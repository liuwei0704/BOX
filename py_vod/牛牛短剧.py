# coding: utf-8
"""
牛牛视频 - TVBox/FongMi 爬虫源
站点: https://niuniuf.com/
播放策略: 使用 CDN 域名 d32bg2g0w9aqg4.cloudfront.net 请求 m3u8
作者: AI Assistant
日期: 2026-07-24
"""
import re
import json
from urllib.parse import quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://niuniuf.com"
        self.cdn_host = "https://d32bg2g0w9aqg4.cloudfront.net"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://niuniuf.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.cookies = {}
        self.cookie_str = ""
        # 分类列表 - 只保留短剧相关分类
        self.classes = [
            {"type_id": "cate5", "type_name": "🔥擦边短剧"},
            {"type_id": "cate17", "type_name": "乱伦之爱"},
            {"type_id": "cate29", "type_name": "一手原创"},
            {"type_id": "cate37", "type_name": "独家热播"},
        ]
        self.filters = {}

    def getName(self):
        return "牛牛视频"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        url = self.host + "/"
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        items = self._parse_video_list(html)
        return {"list": items}

    def categoryContent(self, tid, pg, filter=False, extend=""):
        # 支持直接传入 cateX 或数字
        if not tid.startswith("cate"):
            tid = "cate" + str(tid)
        pg = str(pg) if pg else "1"
        if pg == "1":
            url = self.host + "/category/" + tid + "/"
        else:
            url = self.host + "/category/" + tid + "/" + pg + "/"

        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}

        items = self._parse_video_list(html)
        pagecount = self._parse_page_count(html)

        return {
            "list": items,
            "page": int(pg),
            "pagecount": pagecount if pagecount > 0 else 50,
            "limit": 20,
            "total": 0,
        }

    def detailContent(self, ids):
        if not ids or len(ids) == 0:
            return {"list": []}

        vid = ids[0]
        if "/video/" in vid:
            vid = vid.split("/video/")[-1].rstrip("/")

        detail_url = self.host + "/video/" + str(vid) + "/"
        html = self._fetch_html(detail_url)
        if not html:
            return {"list": []}

        title = self._extract_title(html)
        pic = self._extract_pic(html)
        desc = self._extract_desc(html)

        vod = {
            "vod_id": str(vid),
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": desc,
            "vod_content": desc,
            "vod_play_from": "播放",
            "vod_play_url": "播放$" + str(vid),
        }

        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}

        keyword = key.strip()
        pg = str(pg) if pg else "1"
        url = self.host + "/search/" + quote(keyword) + "/"
        if pg != "1":
            url = self.host + "/search/" + quote(keyword) + "/" + pg + "/"

        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": int(pg)}

        items = self._parse_video_list(html)
        pagecount = self._parse_page_count(html)

        return {
            "list": items,
            "page": int(pg),
            "pagecount": pagecount if pagecount > 0 else 20,
        }

    def playerContent(self, flag, vid, vipFlags):
        # 确保 vid 是字符串
        vid = str(vid) if vid is not None else ""
        
        cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
        play_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://niuniuf.com/",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Origin": "https://niuniuf.com",
        }
        if cookie_str:
            play_headers["Cookie"] = cookie_str

        if vid and (vid.endswith(".m3u8") or vid.endswith(".mp4")):
            vid = self._fix_cdn_url(vid)
            return {"parse": 0, "url": vid, "header": play_headers}

        if vid and vid.startswith("http"):
            match = re.search(r'/video/(\d+)/', vid)
            if match:
                vid = match.group(1)
            else:
                return {"parse": 1, "url": vid, "header": play_headers}

        detail_url = self.host + "/video/" + str(vid) + "/"
        html = self._fetch_html(detail_url)
        if html:
            archive_data = self._extract_archive_player(html)
            if archive_data:
                raw_path = archive_data.get("rawPath", "")
                cdn_line = archive_data.get("cdnLine", self.cdn_host)
                if raw_path:
                    if raw_path.startswith("/"):
                        m3u8_url = cdn_line.rstrip("/") + raw_path
                    else:
                        m3u8_url = cdn_line.rstrip("/") + "/" + raw_path.lstrip("/")
                    m3u8_url = self._fix_cdn_url(m3u8_url)
                    if cookie_str:
                        play_headers["Cookie"] = cookie_str
                    return {"parse": 0, "url": m3u8_url, "header": play_headers}

        return {"parse": 1, "url": detail_url, "header": play_headers}

    def recommendContent(self, ids, pg=1):
        return {"list": []}

    def localProxy(self, params):
        return [404, "text/plain", "Not Found", {}]

    def destroy(self):
        pass

    def _fix_cdn_url(self, url):
        replacements = [
            ("niuniuf.com", "d32bg2g0w9aqg4.cloudfront.net"),
            ("gr32fe.sxwph.com", "d32bg2g0w9aqg4.cloudfront.net"),
            ("wefs3.sxwph.com", "d32bg2g0w9aqg4.cloudfront.net"),
            ("sdsdsd.sxwph.com", "d32bg2g0w9aqg4.cloudfront.net"),
            ("d2k58elwv8me3x.cloudfront.net", "d32bg2g0w9aqg4.cloudfront.net"),
        ]
        for old, new in replacements:
            if old in url:
                url = url.replace(old, new)
        return url

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if resp and hasattr(resp, "text"):
                try:
                    if hasattr(resp, "cookies"):
                        self.cookies.update(resp.cookies)
                except Exception:
                    pass
                return resp.text
            return None
        except Exception as e:
            self.log({"action": "fetch_error", "url": url, "error": str(e)})
            return None

    def _parse_video_list(self, html):
        items = []
        li_pattern = r'<li[^>]*class="[^"]*section-content__item[^"]*"[^>]*>.*?<a[^>]*href="/video/(\d+)/"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<span[^>]*class="eye"[^>]*>(.*?)</span>'
        matches = re.findall(li_pattern, html, re.DOTALL)

        def fix_pic_url(pic):
            if "wefs3.sxwph.com" in pic:
                pic = pic.replace("wefs3.sxwph.com", "d32bg2g0w9aqg4.cloudfront.net")
            elif "sdsdsd.sxwph.com" in pic:
                pic = pic.replace("sdsdsd.sxwph.com", "d32bg2g0w9aqg4.cloudfront.net")
            return pic

        if not matches:
            li_pattern2 = r'<a[^>]*href="/video/(\d+)/"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>'
            matches2 = re.findall(li_pattern2, html, re.DOTALL)
            for match in matches2:
                if len(match) >= 3:
                    vid = match[0]
                    pic = fix_pic_url(match[1])
                    title = re.sub(r'<[^>]+>', '', match[2].strip())
                    if vid and title:
                        items.append({
                            "vod_id": vid,
                            "vod_name": title,
                            "vod_pic": pic if pic.startswith("http") else self.host + pic,
                            "vod_remarks": "",
                        })
        else:
            for match in matches:
                if len(match) >= 4:
                    vid = match[0]
                    pic = fix_pic_url(match[1])
                    title = re.sub(r'<[^>]+>', '', match[2].strip())
                    remark = match[3].strip() if len(match) > 3 else ""
                    if vid and title:
                        items.append({
                            "vod_id": vid,
                            "vod_name": title,
                            "vod_pic": pic if pic.startswith("http") else self.host + pic,
                            "vod_remarks": remark,
                        })

        seen = set()
        unique_items = []
        for item in items:
            key = item["vod_id"]
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        return unique_items[:50]

    def _parse_page_count(self, html):
        pages = re.findall(r'<a[^>]*href="[^"]*/(\d+)/"[^>]*>\d+</a>', html)
        if pages:
            return max([int(p) for p in pages if p.isdigit()])
        return 1

    def _extract_title(self, html):
        match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
        if match:
            return match.group(1).strip()
        match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
        if match:
            return re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return ""

    def _extract_pic(self, html):
        archive_data = self._extract_archive_player(html)
        if archive_data:
            poster = archive_data.get("posterImg", "")
            if poster:
                return poster
        match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if match:
            pic = match.group(1)
            if pic.startswith("/"):
                pic = self.host + pic
            return pic
        match = re.search(r'<img[^>]*data-src="([^"]+)"[^>]*class="[^"]*cover[^"]*"', html)
        if match:
            pic = match.group(1)
            if "/system/" not in pic:
                return pic if pic.startswith("http") else self.host + pic
        return ""

    def _extract_desc(self, html):
        match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        if match:
            return match.group(1)[:200]
        return ""

    def _extract_archive_player(self, html):
        start_pattern = r'__ARCHIVE_PLAYER__\s*=\s*(\{)'
        match = re.search(start_pattern, html)
        if not match:
            return None

        start_idx = match.start(1)
        stack = []
        in_string = False
        escape_next = False
        end_idx = None

        for i in range(start_idx, len(html)):
            char = html[i]
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == '{':
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        end_idx = i + 1
                        break

        if end_idx is None:
            return None

        json_str = html[start_idx:end_idx]
        try:
            return json.loads(json_str)
        except:
            return None