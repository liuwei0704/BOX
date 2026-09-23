# coding: utf-8
# 路飞影视 (www.lufys.com) — TVBox/FongMi T3 爬虫
# 架构：MacCMS theme2，JSON API 已关闭，走 HTML 解析。
# 播放：详情/播放页明文 m3u8 直链，encrypt=0，parse:0 直接播放。
import re
import sys
from urllib.parse import quote, unquote, urljoin, urlsplit

# 第三方视频 CDN 证书常自签/过期，关闭校验并压制告警
try:
    import urllib3
    urllib3.disable_warnings()
except Exception:
    pass

try:
    from base.spider import Spider as BaseSpider
except Exception:  # 本地沙盒自测兜底
    class BaseSpider(object):
        def log(self, *a, **k):
            pass


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

    # ---------------- 站点信息（换站只改这里） ----------------
    SITE_NAME = "路飞影视"
    HOST = "https://www.lufys.com"
    # 导航分类：type slug -> 中文名
    CATEGORIES = [
        ("dianying", "电影"),
        ("dianshiju", "电视剧"),
        ("zongyi", "综艺"),
        ("dongman", "动漫"),
        ("duanju", "短剧"),
    ]

    def __init__(self):
        self.host = self.HOST
        self.classes = [{"type_id": s, "type_name": n} for s, n in self.CATEGORIES]
        # 游客无筛选/无深度分页权限，留空
        self.filters = {}
        self.headers = {
            "User-Agent": ("Mozilla/5.0 (Linux; Android 12; Pixel 6) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Mobile Safari/537.36"),
            "Referer": self.HOST + "/",
        }
        # DoH 解析缓存：host -> [ip,...]，绕过运营商 DNS 污染时复用
        self._doh_cache = {}

    # ---------------- 基础方法 ----------------
    def getName(self):
        return self.SITE_NAME

    def getDependence(self):
        return []

    def init(self, extend=""):
        # 零网络
        self.extend = extend or ""

    def isVideoFormat(self, url):
        u = (url or "").lower()
        return (".m3u8" in u) or (".mp4" in u)

    def manualVideoCheck(self):
        return False

    def destroy(self):
        return

    # ---------------- 网络封装 ----------------
    def _get(self, url):
        """统一 GET，返回 html 文本；判 200 再解析。"""
        try:
            r = self.fetch(url, headers=self.headers)
            if r is None:
                return ""
            code = getattr(r, "status_code", 200)
            if code != 200:
                return ""
            return getattr(r, "text", "") or ""
        except Exception as e:
            self.log("lufys _get error: %s %s" % (url, e))
            return ""

    # ---------------- DoH 抗 DNS 污染下载栈 ----------------
    # 背景：运营商对本站视频 CDN 域名做 DNS 污染，把分片解析到返回 404 的
    # 边缘节点，导致“取链 200 / 拉流 404、换网或 VPN 即恢复”。设备端播放器
    # 与 self.fetch 都吃同一份被污染的 DNS，故播放走 localProxy 把抓取搬到
    # 爬虫侧，并以 DoH 解析真实 IP + 正确 SNI 直连绕过污染。
    def _doh_resolve(self, host, timeout=8):
        # 用 DNS-over-HTTPS 解析真实 IP，绕过运营商 DNS 污染；按 host 缓存。
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
        # 经 DoH 解析真实 IP，以“正确 SNI + 真实 Host 头”直连该 IP，绕过运营商
        # 把 CDN 域名污染到 404 边缘节点的问题；非 2xx 自动换下一个 IP。
        import ssl
        import socket
        import http.client
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
        # 本地代理下载：1) 常规 urllib + 关 TLS 校验 → 2) 非 2xx/异常(典型污染 404)
        # 走 DoH 真实 IP 直连 → 3) 回退 base.fetch 多签名兼容。
        hdr = {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}
        direct = None
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
        try:
            doh = self._dl_doh(url, timeout=timeout)
            if doh is not None and 200 <= doh.status_code < 400:
                self.log("dl DoH ok status=%s: %s" % (doh.status_code, url))
                return doh
        except Exception as e:
            self.log("dl DoH fail %s : %s" % (url, e))
        attempts = (
            {"headers": hdr, "timeout": timeout, "verify": False},
            {"headers": hdr, "verify": False},
            {"headers": hdr, "timeout": timeout},
            {"headers": hdr},
        )
        for kw in attempts:
            try:
                r = self.fetch(url, **kw)
                if r is not None:
                    return r
            except TypeError:
                continue
            except Exception:
                break
        return direct

    def _proxy_url(self, url):
        # 把任意资源（m3u8/分片/key）转为本地代理端点，TLS/DNS 由代理端接管
        try:
            base = self.getProxyUrl()
        except Exception:
            base = ""
        if not base:
            return url
        sep = "&" if "?" in base else "?"
        return "%s%surl=%s" % (base, sep, quote(url, safe=""))

    # ---------------- 首页 ----------------
    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._get(self.host + "/")
        return {"list": self._parse_cards(html)}

    # ---------------- 分类列表 ----------------
    def categoryContent(self, tid, pg, filter, extend):
        # 游客仅可访问首页(第1页)，深页触发会员墙；固定 pagecount=1。
        page = 1
        try:
            page = int(pg or 1)
        except Exception:
            page = 1
        html = self._get("%s/type/%s" % (self.host, tid))
        vlist = self._parse_cards(html) if page == 1 else []
        return {
            "list": vlist,
            "page": page,
            "pagecount": 1,
            "limit": len(vlist) or 90,
            "total": len(vlist),
        }

    # ---------------- 详情 + 多线路 ----------------
    def detailContent(self, ids):
        vid = self._norm_ids(ids)
        if not vid:
            return {"list": []}
        html = self._get("%s/watch/%s" % (self.host, vid))
        if not html:
            return self._skeleton(vid)

        name = self._first(html, [
            r'<h1 class="seo-h1">([^<]+)</h1>',
            r'<title>([^<]+?)\s*-',
        ]) or "路飞影视"
        pic = self._pic_from(html)
        year = self._first(html, [r'/search/year/\d+"[^>]*>([^<]+)</a>'])
        area = self._first(html, [r'/search/area/[^"]+"[^>]*>([^<]+)</a>'])
        vclass = self._first(html, [r'/show/\d+/class/[^"]+"[^>]*>([^<]+)</a>'])
        remarks = self._first(html, [r'备注\s*:\s*</strong>\s*([^<]+)'])
        director = self._collect(html, r'/search/director/[^"]+"[^>]*>([^<]+)</a>')
        actor = self._collect(html, r'/search/actor/[^"]+"[^>]*>([^<]+)</a>')
        content = self._first(html, [r'id="height_limit"[^>]*>\s*(.*?)\s*</div>'])
        content = re.sub(r"<[^>]+>", "", content or "").strip()

        vtype = " ".join([x for x in [year, area, vclass] if x])

        froms, urls = self._parse_play(html, vid)
        if not froms:
            return self._skeleton(vid, name, pic, remarks or "解析中")

        vod = {
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": pic,
            "vod_year": year or "",
            "vod_area": area or "",
            "vod_remarks": remarks or "",
            "vod_actor": actor,
            "vod_director": director,
            "vod_content": content or vtype,
            "type_name": vclass or "",
            "vod_play_from": "$$$".join(froms),
            "vod_play_url": "$$$".join(urls),
        }
        return {"list": [vod]}

    def _parse_play(self, html, vid):
        """返回 (线路名列表, 每线路的集数串列表)，一一对齐。"""
        # 线路名：anthology-tab 里的 swiper-slide a
        tab_area = self._section(html, "anthology-tab", "</div>\n    </div>")
        tab_names = []
        for m in re.finditer(r'<a class="swiper-slide"[^>]*>(.*?)</a>', tab_area, re.S):
            txt = re.sub(r"<[^>]+>", "", m.group(1))
            txt = txt.replace("&nbsp;", "").replace("\xa0", "")
            txt = re.sub(r"\d+$", "", txt).strip()  # 去掉末尾 badge 数字
            tab_names.append(txt or ("线路%d" % (len(tab_names) + 1)))

        # 每个 anthology-list-box 一个线路；线路来源(sid)取自 data-play-sid，
        # 真实可播放地址为三段式 /watch-play/{id}-{nid}-{sid}，
        # 2 段式 href 会退回默认线路，必须补回 sid 才能区分多线路。
        boxes = re.findall(r'<div class="anthology-list-box[^"]*"[^>]*>.*?</ul>', html, re.S)
        froms, urls = [], []
        for i, box in enumerate(boxes):
            bsm = re.search(r'data-play-sid="(\d+)"', box)
            box_sid = bsm.group(1) if bsm else str(i + 1)
            eps = []
            for a in re.finditer(r'<a\b([^>]*)>(.*?)</a>', box, re.S):
                attrs, inner = a.group(1), a.group(2)
                hm = re.search(r'href="/watch-play/(\d+)-(\d+)"', attrs)
                if not hm:
                    continue
                aid, nid = hm.group(1), hm.group(2)
                sm = re.search(r'data-play-sid="(\d+)"', attrs)
                sid = sm.group(1) if sm else box_sid
                epname = re.sub(r"<[^>]+>", "", inner)
                epname = epname.replace("&nbsp;", " ").strip()
                if not epname:
                    epname = "第%s集" % nid
                epname = epname.replace("$", " ").replace("#", " ")
                play_id = "%s-%s-%s" % (aid, nid, sid)
                eps.append("%s$%s" % (epname, play_id))
            if not eps:
                continue
            name = tab_names[i] if i < len(tab_names) else ("线路%d" % (i + 1))
            name = name.replace("$", " ").replace("#", " ")
            froms.append(name)
            urls.append("#".join(eps))
        return froms, urls

    # ---------------- 搜索 ----------------
    def searchContent(self, key, quick, pg="1"):
        html = self._get("%s/search?wd=%s" % (self.host, quote(str(key or ""))))
        return {"list": self._parse_cards(html), "page": 1}

    # ---------------- 推荐 ----------------
    def recommendContent(self, *args):
        return {"list": []}

    # ---------------- 播放 ----------------
    def playerContent(self, flag, id, vipFlags):
        pid = self._norm_ids(id)
        # 已是直链
        if pid.lower().endswith((".m3u8", ".mp4")):
            return self._wrap_play(pid)
        # 拉取播放页解析 player_aaaa.url
        html = self._get("%s/watch-play/%s" % (self.host, pid))
        real = ""
        m = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
        if not m:
            m = re.search(r'"url"\s*:\s*"(https?:[^"]+)"', html)
        if m:
            real = m.group(1).replace("\\/", "/").replace("\\u002f", "/")
        if not real:
            return {"parse": 1, "url": "%s/watch-play/%s" % (self.host, pid),
                    "header": self.headers}
        return self._wrap_play(real)

    def _wrap_play(self, url):
        # m3u8 走本地代理（DoH 抗污染 + 分片改写回代理），mp4 直链回传。
        header = {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}
        if ".m3u8" in url.lower():
            return {"parse": 0, "url": self._proxy_url(url), "header": header}
        return {"parse": 0, "url": url, "header": header}

    # ---------------- m3u8 本地代理（DoH 抗污染 + 分片回代理） ----------------
    @staticmethod
    def _is_master(text):
        return "#EXT-X-STREAM-INF" in text

    def _pick_variant(self, text, base):
        best_url, best_bw = "", -1
        lines = text.replace("\r", "").split("\n")
        for i, ln in enumerate(lines):
            if ln.startswith("#EXT-X-STREAM-INF"):
                bm = re.search(r"BANDWIDTH=(\d+)", ln)
                bw = int(bm.group(1)) if bm else 0
                for j in range(i + 1, len(lines)):
                    nxt = lines[j].strip()
                    if not nxt or nxt.startswith("#"):
                        continue
                    if bw >= best_bw:
                        best_bw, best_url = bw, urljoin(base, nxt)
                    break
        return best_url

    def localProxy(self, param):
        target = unquote(str((param or {}).get("url", "") or ""))
        if not re.match(r"^https?://", target, re.I):
            return [400, "text/plain", b"invalid url"]

        res = self._dl(target)
        if res is None:
            self.log("lufys localProxy 502 (dl None): %s" % target)
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
        cur, depth = target, 0
        while self._is_master(text) and depth < 3:
            var = self._pick_variant(text, cur)
            if not var:
                break
            r2 = self._dl(var)
            if r2 is None:
                self.log("lufys localProxy master follow fail: %s" % var)
                break
            cur = var
            text = (getattr(r2, "content", b"") or b"").decode("utf-8", "ignore")
            depth += 1

        # media playlist：segment/KEY/MAP 一律改写回本地代理
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
                out.append(self._proxy_url(urljoin(cur, s)))
        self.log("lufys localProxy m3u8 ok depth=%d lines=%d src=%s" % (depth, len(out), cur))
        return [200, "application/vnd.apple.mpegurl", "\n".join(out).encode("utf-8")]

    # ---------------- 卡片解析（分类/首页/搜索通用） ----------------
    def _parse_cards(self, html):
        out, seen = [], set()
        if not html:
            return out
        blocks = re.split(r'(?=class="public-list-exp")', html)
        for b in blocks[1:]:
            idm = re.search(r'href="/watch/(\d+)"', b)
            if not idm:
                continue
            vid = idm.group(1)
            head = b[:220]
            # 名称：exp 锚点 title 属性（分类/首页），否则 thumb-txt / time-title
            nm = re.search(r'title="([^"]+)"', head)
            name = nm.group(1).strip() if nm else ""
            if not name:
                hm = re.search(r'thumb-txt.*?<h3>\s*<a[^>]*>\s*([^<]+?)\s*</a>', b, re.S)
                if hm:
                    name = hm.group(1).strip()
            if not name:
                hm = re.search(r'time-title[^>]*>\s*<a[^>]*title="([^"]+)"', b, re.S)
                if hm:
                    name = hm.group(1).strip()
            if not vid or not name or vid in seen:
                continue
            picm = re.search(r'data-src="([^"]+)"', b)
            pic = picm.group(1) if picm else ""
            rm = re.search(r'public-list-prb[^>]*>\s*([^<]+?)\s*<', b, re.S)
            rem = rm.group(1).strip() if rm else ""
            seen.add(vid)
            out.append({"vod_id": vid, "vod_name": name,
                        "vod_pic": pic, "vod_remarks": rem})
        return out

    def _pic_from(self, html):
        m = re.search(r'class="detail-pic">\s*<img[^>]*data-src="([^"]+)"', html, re.S)
        if m:
            return m.group(1)
        m = re.search(r'slide-time-img2">\s*<img[^>]*src="([^"]+)"', html, re.S)
        return m.group(1) if m else ""

    # ---------------- 工具 ----------------
    @staticmethod
    def _norm_ids(ids):
        if ids is None:
            return ""
        if isinstance(ids, (list, tuple)):
            if not ids:
                return ""
            ids = ids[0]
        if isinstance(ids, bytes):
            ids = ids.decode("utf-8", errors="ignore")
        return str(ids).strip()

    @staticmethod
    def _first(html, patterns):
        for p in patterns:
            m = re.search(p, html, re.S)
            if m:
                return m.group(1).strip()
        return ""

    @staticmethod
    def _collect(html, pattern):
        vals = re.findall(pattern, html, re.S)
        seen, out = set(), []
        for v in vals:
            v = v.strip()
            if v and v not in seen:
                seen.add(v)
                out.append(v)
        return " / ".join(out)

    @staticmethod
    def _section(html, start_mark, end_mark):
        i = html.find(start_mark)
        if i < 0:
            return ""
        j = html.find(end_mark, i)
        return html[i:j] if j > i else html[i:i + 4000]

    def _skeleton(self, vid, title="", pic="", remarks="解析中"):
        return {"list": [{
            "vod_id": vid, "vod_name": title or "未知标题", "vod_pic": pic or "",
            "vod_remarks": remarks, "vod_content": "",
            "vod_play_from": "播放", "vod_play_url": "播放$%s-1-1" % vid,
        }]}
