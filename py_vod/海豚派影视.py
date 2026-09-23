# coding: utf-8
# 海豚派影视 (hidekatsu.net) TVBox/FongMi T3 爬虫  type=3
import re
import sys
from urllib.parse import quote, urljoin, unquote, urlparse

sys.setrecursionlimit(10000)

# 第三方视频 CDN 证书常自签/过期，关闭校验并压制告警
try:
    import urllib3
    urllib3.disable_warnings()
except Exception:
    pass

try:
    from base.spider import Spider as BaseSpider
except Exception:
    class BaseSpider(object):
        def log(self, x):
            pass

# ============ 站点信息（换站只改这里） ============
SITE_NAME = "海豚派"
HOST = "https://www.hidekatsu.net"
IMG_HOST = "https://img.hidekatsu.net"
# 顶部主分类（type_id 与 /tv/{tid} 通用）
CATEGORIES = [
    {"type_id": "1", "type_name": "电影"},
    {"type_id": "2", "type_name": "电视剧"},
    {"type_id": "3", "type_name": "短剧"},
    {"type_id": "4", "type_name": "动漫"},
    {"type_id": "5", "type_name": "综艺"},
]
# 电影二级类型（/tv/{tid} 直接翻页）
MOVIE_GENRES = [
    {"n": "全部", "v": "1"}, {"n": "剧情", "v": "6"}, {"n": "动作", "v": "7"},
    {"n": "冒险", "v": "8"}, {"n": "喜剧", "v": "9"}, {"n": "奇幻", "v": "10"},
    {"n": "恐怖", "v": "11"}, {"n": "悬疑", "v": "16"}, {"n": "惊悚", "v": "17"},
    {"n": "灾难", "v": "18"}, {"n": "爱情", "v": "19"}, {"n": "犯罪", "v": "20"},
    {"n": "科幻", "v": "21"}, {"n": "动画电影", "v": "22"}, {"n": "战争", "v": "28"},
    {"n": "经典", "v": "29"},
]


class _R(object):
    """本地代理用的轻量响应对象，兼容 res.status_code / res.content / res.headers.get / res.text"""
    def __init__(self, status_code, content, ctype):
        self.status_code = int(status_code or 200)
        self.content = content or b""
        self.headers = {"Content-Type": ctype or ""}

    @property
    def text(self):
        return self.content.decode("utf-8", "ignore")


class Spider(BaseSpider):

    def __init__(self):
        self.host = HOST
        self.classes = CATEGORIES
        self.filters = {"1": [{"key": "class", "name": "类型", "value": MOVIE_GENRES}]}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Referer": HOST + "/",
        }
        # DoH 解析缓存：host -> [ip,...]，绕过运营商 DNS 污染时复用
        self._doh_cache = {}

    # ---------- 基础 ----------
    def getName(self):
        return SITE_NAME

    def getDependence(self):
        return []

    def init(self, extend=""):
        # 零网络
        self.extend = extend or ""
        return

    def isVideoFormat(self, url):
        u = (url or "").lower()
        return (".m3u8" in u) or (".mp4" in u) or (".flv" in u)

    def manualVideoCheck(self):
        return False

    def destroy(self):
        return

    # ---------- 网络封装 ----------
    def _get(self, url):
        try:
            r = self.fetch(url, headers=self.headers)
            if r and getattr(r, "status_code", 0) == 200:
                try:
                    return r.text
                except Exception:
                    return getattr(r, "content", b"").decode("utf-8", "ignore")
        except Exception as e:
            self.log("GET fail %s : %s" % (url, e))
        return ""

    def _doh_resolve(self, host, timeout=8):
        # 用 DNS-over-HTTPS 解析真实 IP，绕过运营商 DNS 污染/劫持。
        # 结果按 host 缓存，避免海量分片重复解析。
        if not host:
            return []
        cached = self._doh_cache.get(host)
        if cached:
            return cached
        import json as _json
        import ssl
        import urllib.request
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ua = self.headers["User-Agent"]
        for base in (
            "https://1.1.1.1/dns-query",
            "https://8.8.8.8/resolve",
            "https://dns.google/resolve",
            "https://cloudflare-dns.com/dns-query",
        ):
            try:
                u = "%s?name=%s&type=A" % (base, host)
                req = urllib.request.Request(
                    u, headers={"accept": "application/dns-json", "User-Agent": ua})
                r = urllib.request.urlopen(req, timeout=timeout, context=ctx)
                d = _json.loads(r.read().decode("utf-8", "ignore"))
                ips = [a["data"] for a in d.get("Answer", []) if a.get("type") == 1]
                if ips:
                    self._doh_cache[host] = ips
                    return ips
            except Exception:
                continue
        return []

    def _dl_doh(self, url, timeout=20):
        # 经 DoH 解析真实 IP，并以“正确 SNI + 真实 Host 头”直连该 IP，
        # 绕过运营商把 CDN 域名污染到 404 边缘节点的问题；非 2xx 自动换下一个 IP。
        import ssl
        import socket
        import http.client
        from urllib.parse import urlsplit
        u = urlsplit(url)
        host = u.hostname
        if not host:
            return None
        port = u.port or (443 if u.scheme == "https" else 80)
        path = u.path + (("?" + u.query) if u.query else "")
        if not path:
            path = "/"
        ips = self._doh_resolve(host)
        if not ips:
            return None
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        hosthdr = host if port in (80, 443) else "%s:%d" % (host, port)
        hdrs = {
            "User-Agent": self.headers["User-Agent"],
            "Referer": self.host + "/",
            "Accept": "*/*",
            "Connection": "close",
        }
        best = None
        for ip in ips:
            conn = None
            try:
                raw = socket.create_connection((ip, port), timeout=timeout)
                if u.scheme == "https":
                    sock = ctx.wrap_socket(raw, server_hostname=host)  # SNI=真实域名
                else:
                    sock = raw
                conn = http.client.HTTPConnection(ip, port, timeout=timeout)
                conn.sock = sock
                conn.putrequest("GET", path, skip_host=True, skip_accept_encoding=True)
                conn.putheader("Host", hosthdr)
                for k, v in hdrs.items():
                    conn.putheader(k, v)
                conn.endheaders()
                resp = conn.getresponse()
                body = resp.read()
                ct = resp.getheader("Content-Type", "") or ""
                r = _R(resp.status, body, ct)
                try:
                    conn.close()
                except Exception:
                    pass
                if 200 <= resp.status < 400:
                    return r
                best = r  # 记录非 2xx，继续尝试其它边缘 IP
            except Exception:
                try:
                    if conn:
                        conn.close()
                except Exception:
                    pass
                continue
        return best

    def _dl(self, url, timeout=20):
        # 供本地代理使用。设备端(Chaquo) base.fetch 多半不支持 verify 参数，
        # 且运营商可能把第三方 CDN 域名 DNS 污染到返回 404 的边缘节点。
        # 分级策略：
        #   1) 常规 urllib + 关闭 TLS 校验（绕过自签/过期证书）
        #   2) 若异常或返回非 2xx（典型：DNS 污染导致的 404）→ DoH 解析真实 IP 直连
        #   3) 再回退 base.fetch 多签名兼容
        hdr = {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}
        direct = None
        # 1) 常规 urllib + 关闭 TLS 校验
        try:
            import ssl
            import urllib.request
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers=hdr)
            resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            data = resp.read()
            try:
                code = resp.status
            except Exception:
                code = resp.getcode() or 200
            ctype = ""
            try:
                ctype = resp.headers.get("Content-Type", "") or ""
            except Exception:
                pass
            direct = _R(code, data, ctype)
            if 200 <= direct.status_code < 400:
                return direct
            self.log("dl direct status=%s, try DoH: %s" % (direct.status_code, url))
        except Exception as e:
            self.log("dl urllib fail %s : %s" % (url, e))
        # 2) DoH 解析真实 IP + 正确 SNI 直连，绕过运营商 DNS 污染
        try:
            doh = self._dl_doh(url, timeout=timeout)
            if doh is not None and 200 <= doh.status_code < 400:
                self.log("dl DoH ok status=%s: %s" % (doh.status_code, url))
                return doh
        except Exception as e:
            self.log("dl DoH fail %s : %s" % (url, e))
        # 3) 回退 base.fetch（不同签名兼容；部分实现支持 verify）
        attempts = (
            {"headers": hdr, "timeout": timeout, "verify": False},
            {"headers": hdr, "verify": False},
            {"headers": hdr, "timeout": timeout},
            {"headers": hdr},
        )
        last = None
        for kw in attempts:
            try:
                r = self.fetch(url, **kw)
                if r is not None:
                    return r
            except TypeError:
                continue  # 该签名不接受此参数，换下一组
            except Exception as e:
                last = e
                break
        if last is not None:
            self.log("dl fetch fail %s : %s" % (url, last))
        # 4) 都失败时，若常规请求拿到过响应（哪怕 404），透传给上层判断
        return direct


    def _abs(self, u):
        if not u:
            return ""
        u = u.strip()
        if u.startswith("http"):
            return u
        if u.startswith("//"):
            return "https:" + u
        return urljoin(self.host + "/", u)

    @staticmethod
    def _unescape_url(u):
        # 消除 player_aaaa 内 JSON 转义，规避 unicode_escape 的 DeprecationWarning
        if not u:
            return ""
        return (u.replace("\\/", "/")
                 .replace("\\u002f", "/").replace("\\u002F", "/")
                 .replace("\\u003a", ":").replace("\\u003A", ":")
                 .strip())

    # ---------- 列表卡片解析 ----------
    def _parse_vodlist(self, html):
        vods = []
        m = re.search(r'<ul class="shoutu-vodlist">(.*?)</ul>', html, re.S)
        seg = m.group(1) if m else html
        for li in re.findall(r'<li class="col8">(.*?)</li>', seg, re.S):
            am = re.search(r'href="/video/(\d+)\.html"\s+title="([^"]*)"', li)
            if not am:
                continue
            vid = am.group(1)
            name = am.group(2).strip()
            pm = re.search(r'data-original="([^"]+)"', li)
            pic = self._abs(pm.group(1)) if pm else ""
            rm = re.search(r'<p class="text"[^>]*>(.*?)</p>', li, re.S)
            remark = re.sub(r"<[^>]+>", "", rm.group(1)).strip() if rm else ""
            vods.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": remark,
            })
        return vods

    def _pagecount(self, html):
        pgs = re.findall(r'/tv/\d+/page/(\d+)\.html', html)
        if pgs:
            try:
                return max(int(x) for x in pgs)
            except Exception:
                pass
        return 1

    # ---------- 首页 ----------
    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._get(self.host + "/tv/1.html")
        return {"list": self._parse_vodlist(html)}

    # ---------- 分类 ----------
    def categoryContent(self, tid, pg, filter, extend):
        page = 1
        try:
            page = int(pg or 1)
        except Exception:
            page = 1
        extend = extend or {}
        # 电影支持二级类型筛选：extend['class'] 覆盖 tid
        real_tid = str(tid)
        if isinstance(extend, dict):
            cls = extend.get("class", "")
            if cls:
                real_tid = str(cls)
        if page <= 1:
            url = "%s/tv/%s.html" % (self.host, real_tid)
        else:
            url = "%s/tv/%s/page/%d.html" % (self.host, real_tid, page)
        html = self._get(url)
        vods = self._parse_vodlist(html)
        pc = self._pagecount(html)
        if pc < page:
            pc = page
        return {
            "list": vods,
            "page": page,
            "pagecount": pc,
            "limit": len(vods) or 42,
            "total": pc * 42,
        }

    # ---------- 详情 ----------
    @staticmethod
    def _norm_ids(ids):
        if ids is None:
            return ""
        if isinstance(ids, (list, tuple)):
            if not ids:
                return ""
            ids = ids[0]
        if isinstance(ids, bytes):
            ids = ids.decode("utf-8", "ignore")
        return str(ids).strip()

    def detailContent(self, ids):
        vid = self._norm_ids(ids)
        if not vid:
            return {"list": []}
        vid = vid.split("/")[-1].replace(".html", "")
        url = "%s/video/%s.html" % (self.host, vid)
        html = self._get(url)
        if not html:
            return {"list": [{
                "vod_id": vid, "vod_name": "视频", "vod_pic": "",
                "vod_remarks": "", "vod_content": "",
                "vod_play_from": SITE_NAME, "vod_play_url": "正片$" + vid,
            }]}

        nm = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        name = re.sub(r"<[^>]+>", "", nm.group(1)).strip() if nm else "视频"

        pm = re.search(r'cover-img[^>]*>\s*<img[^>]*data-original="([^"]+)"', html, re.S)
        pic = self._abs(pm.group(1)) if pm else ""

        # tag 块：分类 / 年份 / 地区 / 语言
        tag_txt = ""
        tm = re.search(r'<div class="tag">(.*?)</div>', html, re.S)
        if tm:
            parts = [re.sub(r"<[^>]+>", "", p).strip()
                     for p in re.split(r'</a>|<br\s*/?>', tm.group(1))]
            parts = [p for p in parts if p]
            tag_txt = " ".join(parts)

        year = area = actor = director = ""
        ym = re.search(r"(\b(?:19|20)\d{2}\b)", tag_txt)
        if ym:
            year = ym.group(1)
        am_ = re.search(r"(大陆|香港|台湾|韩国|日本|美国|英国|法国|泰国|印度|其他|欧美|内地)", tag_txt)
        if am_:
            area = am_.group(1)
        for pm2 in re.finditer(r'<p class="data[^"]*"[^>]*>(.*?)</p>', html, re.S):
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", pm2.group(1))).strip()
            if "主演" in t:
                actor = t.split("：", 1)[-1].split(":", 1)[-1].strip()
            elif "导演" in t or "導演" in t:
                director = t.split("：", 1)[-1].split(":", 1)[-1].strip()

        # 简介
        content = ""
        sm = re.search(r'detail-sketch[^>]*>(.*?)</', html, re.S)
        if sm:
            content = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", sm.group(1))).strip()

        # 播放线路：每个 shoutu-playlist ul 对应一条线路，线路名取其前最近的 <h3>
        play_from = []
        play_url = []
        for pl in re.finditer(r'<ul class="shoutu-playlist[^"]*"[^>]*>(.*?)</ul>', html, re.S):
            block = pl.group(1)
            # 线路名：ul 之前最近的 h3
            head = html[:pl.start()]
            hs = re.findall(r"<h3[^>]*>(.*?)</h3>", head, re.S)
            line_name = re.sub(r"<[^>]+>", "", hs[-1]).strip() if hs else "线路"
            if not line_name:
                line_name = "线路"
            eps = []
            for em in re.finditer(r'href="(/play/[^"]+)"[^>]*>(.*?)</a>', block, re.S):
                link = em.group(1)
                title = re.sub(r"<[^>]+>", "", em.group(2)).strip()
                if not title:
                    title = "播放"
                eps.append("%s$%s" % (title, link))
            if eps:
                play_from.append(line_name)
                play_url.append("#".join(eps))

        if not play_url:
            play_from = [SITE_NAME]
            play_url = ["正片$" + vid]

        vod = {
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": pic,
            "vod_year": year,
            "vod_area": area,
            "vod_actor": actor,
            "vod_director": director,
            "vod_remarks": tag_txt,
            "vod_content": content or tag_txt,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url),
        }
        return {"list": [vod]}

    # ---------- 搜索 ----------
    def searchContent(self, key, quick, pg="1"):
        url = "%s/search.html?wd=%s" % (self.host, quote(str(key)))
        html = self._get(url)
        return {"list": self._parse_vodlist(html), "page": 1}

    def searchContentPage(self, key, quick, pg="1"):
        return self.searchContent(key, quick, pg)

    # ---------- 播放 ----------
    def playerContent(self, flag, id, vipFlags):
        pid = id or ""
        # 直链
        if pid.startswith("http"):
            return self._wrap_url(pid)
        # 播放页路径 /play/xxx.html
        play_path = pid if pid.startswith("/play/") else ("/play/%s" % pid.lstrip("/"))
        if not play_path.endswith(".html"):
            # 兜底：非播放页 id（如仅 vid），无法直接解析
            return {"parse": 1, "url": self.host + "/video/" + pid.lstrip("/"),
                    "header": self.headers}
        html = self._get(self._abs(play_path))
        real = ""
        m = re.search(r'var player_aaaa\s*=\s*(\{.*?\})</script>', html, re.S)
        if not m:
            m = re.search(r'player_aaaa\s*=\s*(\{.*?\})', html, re.S)
        if m:
            blob = m.group(1)
            um = re.search(r'"url"\s*:\s*"([^"]*)"', blob)
            if um:
                real = self._unescape_url(um.group(1))
        if not real:
            return {"parse": 1, "url": self._abs(play_path), "header": self.headers}
        return self._wrap_url(real)

    def _proxy_url(self, url):
        # 把任意资源（m3u8/分片/key）转为本地代理端点，TLS 校验由代理端关闭
        try:
            base = self.getProxyUrl()
        except Exception:
            base = ""
        if not base:
            return url
        sep = "&" if "?" in base else "?"
        return "%s%surl=%s" % (base, sep, quote(url, safe=""))

    def _wrap_url(self, url):
        url = self._abs(url)
        header = {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}
        if ".m3u8" in url.lower():
            # 走本地代理：关闭 TLS 校验 + 改写为全本地 http，规避设备端证书失败
            return {"parse": 0, "url": self._proxy_url(url), "header": header}
        return {"parse": 0, "url": url, "header": header}

    # ---------- 本地代理 ----------
    # 策略：对 m3u8 逐行把变体/分片/KEY/MAP 的 URI 全部改写回本地代理，
    # 使播放器只与 127.0.0.1 走 http；真实 https 抓取一律由本方法以
    # verify=False 完成，彻底绕过自签/过期证书。非 m3u8（分片/key）原样透传。
    @staticmethod
    def _is_master(text):
        return "#EXT-X-STREAM-INF" in text

    def _pick_variant(self, text, base):
        # 从 master playlist 选取带宽最高的变体，返回其绝对 URL
        best_url = ""
        best_bw = -1
        lines = text.replace("\r", "").split("\n")
        for i, ln in enumerate(lines):
            if ln.startswith("#EXT-X-STREAM-INF"):
                bw = 0
                bm = re.search(r"BANDWIDTH=(\d+)", ln)
                if bm:
                    bw = int(bm.group(1))
                # 变体地址在紧邻的下一行（跳过注释/空行）
                for j in range(i + 1, len(lines)):
                    nxt = lines[j].strip()
                    if not nxt or nxt.startswith("#"):
                        continue
                    if bw >= best_bw:
                        best_bw = bw
                        best_url = urljoin(base, nxt)
                    break
        return best_url

    def localProxy(self, param):
        p = param or {}
        target = unquote(str(p.get("url", "") or ""))
        if not re.match(r"^https?://", target, re.I):
            return [400, "text/plain", b"invalid url"]

        res = self._dl(target)
        if res is None:
            self.log("localProxy 502 (dl None): %s" % target)
            return [502, "text/plain", b"bad gateway"]
        raw = getattr(res, "content", b"") or b""
        status = getattr(res, "status_code", 200) or 200
        ctype = ""
        try:
            ctype = res.headers.get("Content-Type", "") or ""
        except Exception:
            pass

        head = raw[:512].decode("utf-8", "ignore")
        path_only = target.split("?", 1)[0].lower()
        is_m3u8 = ("#EXTM3U" in head) or path_only.endswith(".m3u8") or ("mpegurl" in ctype.lower())
        if not is_m3u8:
            # 分片 / key / 其它二进制：原样透传
            return [status, ctype or "application/octet-stream", raw]

        text = raw.decode("utf-8", "ignore")

        # 服务端跟随 master -> media，最多 3 层，避免播放器侧多级代理往返
        cur = target
        depth = 0
        while self._is_master(text) and depth < 3:
            var = self._pick_variant(text, cur)
            if not var:
                break
            r2 = self._dl(var)
            if r2 is None:
                self.log("localProxy master follow fail: %s" % var)
                break
            cur = var
            text = (getattr(r2, "content", b"") or b"").decode("utf-8", "ignore")
            depth += 1

        # 此时 text 应为 media playlist，segment/KEY/MAP 一律改写回本地代理
        out = []
        for line in text.replace("\r", "").split("\n"):
            s = line.strip()
            if not s:
                out.append(s)
                continue
            if s.startswith("#"):
                if ("URI=" in s) and (s.startswith("#EXT-X-KEY") or s.startswith("#EXT-X-MAP")):
                    def repl(mo):
                        return 'URI="' + self._proxy_url(urljoin(cur, mo.group(1))) + '"'
                    s = re.sub(r'URI="([^"]+)"', repl, s)
                out.append(s)
            else:
                # 分片（或仍残留的变体）：转绝对后交给本地代理
                out.append(self._proxy_url(urljoin(cur, s)))
        self.log("localProxy m3u8 ok depth=%d lines=%d src=%s" % (depth, len(out), cur))
        return [200, "application/vnd.apple.mpegurl", "\n".join(out).encode("utf-8")]
