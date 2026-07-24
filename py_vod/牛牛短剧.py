# coding: utf-8
"""
牛牛视频 - TVBox/FongMi 爬虫源
站点: https://niuniuf.com/
播放策略: 使用 CDN 域名 gr32fe.sxwph.com 请求 m3u8
作者: AI Assistant
日期: 2026-07-24
"""
import re
import json
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://niuniuf.com"
        self.cdn_host = "https://gr32fe.sxwph.com"  # CDN 域名
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://niuniuf.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.cookies = {}
        
        self.classes = [
            {"type_id": "cate5", "type_name": "擦边短剧"}
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
        """
        播放地址解析 - 使用 CDN 域名 gr32fe.sxwph.com 请求 m3u8
        """
        # 如果传入的是m3u8/mp4直链，直接返回
        if vid and (vid.endswith(".m3u8") or vid.endswith(".mp4")):
            # 如果是 niuniuf.com 的 m3u8，替换为 CDN 域名
            if "niuniuf.com" in vid:
                vid = vid.replace("niuniuf.com", "gr32fe.sxwph.com")
            return {"parse": 0, "url": vid, "header": self.headers}

        # 如果是完整的播放页URL，提取视频ID
        if vid and vid.startswith("http"):
            # 从URL中提取视频ID
            match = re.search(r'/video/(\d+)/', vid)
            if match:
                vid = match.group(1)
            else:
                return {"parse": 1, "url": vid, "header": self.headers}

        # 获取详情页HTML，提取 rawPath
        detail_url = self.host + "/video/" + str(vid) + "/"
        html = self._fetch_html(detail_url)
        if html:
            # 提取 __ARCHIVE_PLAYER__.rawPath
            archive_data = self._extract_archive_player(html)
            if archive_data:
                raw_path = archive_data.get("rawPath", "")
                if raw_path:
                    # 替换域名为 CDN 域名
                    if raw_path.startswith("/"):
                        m3u8_url = self.cdn_host + raw_path
                    else:
                        m3u8_url = raw_path.replace("niuniuf.com", "gr32fe.sxwph.com")
                    return {"parse": 0, "url": m3u8_url, "header": self.headers}

        # 降级：使用 parse:1 嗅探
        return {"parse": 1, "url": detail_url, "header": self.headers}

    def localProxy(self, params):
        return [404, "text/plain", "Not Found", {}]

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if resp and hasattr(resp, "text"):
                if hasattr(resp, "cookies"):
                    self.cookies.update(resp.cookies)
                return resp.text
            return None
        except Exception as e:
            self.log({"action": "fetch_error", "url": url, "error": str(e)})
            return None

    def _parse_video_list(self, html):
        items = []
        card_pattern = r'<li[^>]*class="[^"]*section-content__item[^"]*(?!module-two)"[^>]*>.*?<a[^>]*href="(/video/(\d+)/)"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<span[^>]*class="eye"[^>]*>(.*?)</span>'
        matches = re.findall(card_pattern, html, re.DOTALL)

        if not matches:
            card_pattern2 = r'<a[^>]*href="(/video/(\d+)/)"[^>]*>.*?data-src="([^"]+)".*?text-truncate[^>]*>(.*?)</h3>'
            matches = re.findall(card_pattern2, html, re.DOTALL)

        for match in matches:
            if len(match) >= 4:
                href = match[0]
                vid = match[1]
                pic = match[2]
                title = re.sub(r'<[^>]+>', '', match[3].strip())
                remark = match[4] if len(match) > 4 else ""

                if href and vid and title:
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
        """
        从页面中提取 __ARCHIVE_PLAYER__ JSON 对象
        使用栈匹配处理嵌套的 {} 和 []
        """
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