# coding: utf-8
# 路飞影视 (www.lufys.com) — TVBox/FongMi T3 爬虫
# 架构：MacCMS theme2，JSON API 已关闭，走 HTML 解析。
# 播放：详情/播放页明文 m3u8 直链，encrypt=0，parse:0 直接播放。
import re
import sys
from urllib.parse import quote, unquote, urljoin

try:
    from base.spider import Spider as BaseSpider
except Exception:  # 本地沙盒自测兜底
    class BaseSpider(object):
        def log(self, *a, **k):
            pass


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
            return {"parse": 0, "url": pid,
                    "header": {"User-Agent": self.headers["User-Agent"]}}
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
        return {"parse": 0, "url": real,
                "header": {"User-Agent": self.headers["User-Agent"]}}

    # ---------------- m3u8 本地代理（可选广告过滤） ----------------
    def localProxy(self, param):
        target = unquote(str((param or {}).get("url", "") or ""))
        if not re.match(r"^https?://", target, re.I):
            return [400, "text/plain", b"invalid url"]
        try:
            r = self.fetch(target, headers={"User-Agent": self.headers["User-Agent"]})
            if not r or getattr(r, "status_code", 0) != 200:
                return [502, "text/plain", b"m3u8 fetch failed"]
            text = getattr(r, "text", "") or ""
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]
            out = []
            for line in text.replace("\r", "").split("\n"):
                if line and not line.startswith("#"):
                    out.append(urljoin(target, line))
                elif line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
                    out.append(re.sub(r'URI="([^"]+)"',
                                      lambda mm: 'URI="%s"' % urljoin(target, mm.group(1)),
                                      line))
                else:
                    out.append(line)
            return [200, "application/vnd.apple.mpegurl", "\n".join(out).encode("utf-8")]
        except Exception as e:
            self.log("lufys localProxy error: %s" % e)
            return [500, "text/plain", b"proxy error"]

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
