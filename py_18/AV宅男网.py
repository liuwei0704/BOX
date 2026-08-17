# coding: utf-8
"""
AV宅男网 爬虫源
站点: https://mgllc.zainanwdegh.cfd/
类型: MacCMS 标准影视站 (成人内容)
"""
import re
import json
import urllib.parse
import posixpath
from bs4 import BeautifulSoup
try:
    import requests
except ImportError:
    pass

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://mgllc.zainanwdegh.cfd"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "1", "type_name": "国产自拍"},
            {"type_id": "2", "type_name": "无码专区"},
            {"type_id": "3", "type_name": "麻豆传媒"},
            {"type_id": "4", "type_name": "卡通动画"},
            {"type_id": "5", "type_name": "中文字幕"},
            {"type_id": "6", "type_name": "亚洲情色"},
            {"type_id": "7", "type_name": "制服诱惑"},
            {"type_id": "8", "type_name": "巨乳美乳"},
            {"type_id": "9", "type_name": "熟女人妻"},
            {"type_id": "10", "type_name": "少女萝莉"},
            {"type_id": "11", "type_name": "强奸乱伦"},
            {"type_id": "12", "type_name": "国产主播"},
        ]
        self.filters = {}

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if not url:
            return url
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url), safe="")

    def _rewrite_m3u8_tag(self, line, source_url):
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(match):
                uri = match.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urllib.parse.urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)
        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urllib.parse.urljoin(source_url, line)
        return line

    def _clean_m3u8(self, text, source_url):
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"
        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urllib.parse.urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"
        parsed = urllib.parse.urlparse(source_url)
        source_dir = posixpath.dirname(parsed.path)
        if not source_dir.endswith("/"):
            source_dir += "/"
        main_dir = source_dir
        for line in lines:
            if line.startswith("#EXT-X-KEY") and "URI=" in line:
                uri_match = re.search(r'URI="([^"]+)"', line)
                if uri_match:
                    key_path = uri_match.group(1)
                    if not key_path.startswith("http"):
                        key_dir = posixpath.dirname(key_path)
                        if key_dir and key_dir != "/":
                            main_dir = key_dir + "/"
                            break
        segments = []
        pending = []
        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media_url = urllib.parse.urljoin(source_url, line)
                media_parsed = urllib.parse.urlparse(media_url)
                is_ad = not media_parsed.path.startswith(main_dir)
                if not is_ad:
                    segments.extend(pending)
                    segments.append(media_url)
                pending = []
                continue
            if not line.startswith("#"):
                segments.append(urllib.parse.urljoin(source_url, line))
            else:
                segments.append(line)
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in ("#EXT-X-KEY:METHOD=NONE", "#EXT-X-DISCONTINUITY"):
                if not out or out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
                    continue
            out.append(line)
        while len(out) > 1 and out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
            out.pop()
        return "\n".join(out) + "\n"

    def localProxy(self, params):
        try:
            if isinstance(params, dict):
                target = params.get("url", "") or params.get("source", "")
            else:
                target = str(params or "")
            if target.startswith("url="):
                target = target[4:]
            target = urllib.parse.unquote(str(target or ""))
            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]
            res = self.fetch(target, headers={"User-Agent": self.headers.get("User-Agent", "")}, timeout=15)
            if not res:
                return [502, "text/plain", b"fetch failed"]
            content = getattr(res, "content", b"") or b""
            if not content and hasattr(res, "text") and res.text:
                content = res.text.encode("utf-8", errors="ignore")
            if not content:
                return [502, "text/plain", b"empty content"]
            text = content.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]
            cleaned = self._clean_m3u8(text, target)
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]
        except Exception as e:
            error_msg = f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")
            return [500, "text/plain", error_msg]

    def playerContent(self, flag, id, vipFlags=None):
        if not id:
            return {"parse": 1, "url": ""}
        id = str(id).replace("\\/", "/")
        if id.startswith("http"):
            if ".m3u8" in id or ".mp4" in id:
                if ".m3u8" in id:
                    return {
                        "parse": 0,
                        "url": self._m3u8_proxy_url(id),
                        "header": {"User-Agent": self.headers.get("User-Agent", ""), "Referer": self.host + "/"}
                    }
                return {"parse": 0, "url": id, "header": {"User-Agent": self.headers.get("User-Agent", "")}}
            html = self.get_html(id)
            if html:
                play_url = self._extract_player_url(html)
                if play_url:
                    if ".m3u8" in play_url:
                        return {"parse": 0, "url": self._m3u8_proxy_url(play_url), "header": {"User-Agent": self.headers.get("User-Agent", ""), "Referer": self.host + "/"}}
                    return {"parse": 0, "url": play_url, "header": {"User-Agent": self.headers.get("User-Agent", "")}}
        if id.isdigit():
            play_page_url = f"{self.host}/index.php/vod/play/id/{id}/sid/1/nid/1.html"
            html = self.get_html(play_page_url)
            if html:
                play_url = self._extract_player_url(html)
                if play_url:
                    if ".m3u8" in play_url:
                        return {"parse": 0, "url": self._m3u8_proxy_url(play_url), "header": {"User-Agent": self.headers.get("User-Agent", ""), "Referer": self.host + "/"}}
                    return {"parse": 0, "url": play_url, "header": {"User-Agent": self.headers.get("User-Agent", "")}}
        return {"parse": 1, "url": id, "header": self.headers}

    def getName(self):
        return "AV宅男网"

    def getDependence(self):
        return ["requests", "bs4"]

    def init(self, extend=""):
        pass

    def destroy(self):
        pass

    def fetch(self, url, headers=None, timeout=15):
        try:
            headers = headers or self.headers
            resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
            return resp
        except Exception as e:
            print("fetch error:", e)
            return None

    def get_html(self, url, headers=None):
        resp = self.fetch(url, headers)
        if resp and resp.status_code == 200:
            return resp.text
        return None

    def fix_url(self, url):
        if not url:
            return ""
        url = url.strip()
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.host.rstrip("/") + url
        return self.host.rstrip("/") + "/" + url.lstrip("/")

    def _extract_vod_id(self, href):
        if not href:
            return ""
        m = re.search(r"/id/(\d+)\.html", href)
        if m:
            return m.group(1)
        m = re.search(r"/id/(\d+)/", href)
        if m:
            return m.group(1)
        return ""

    def _parse_list_items(self, items, limit=999):
        videos = []
        for item in items:
            a = item.find("a", href=True)
            if not a:
                continue
            href = a.get("href", "")
            vod_id = self._extract_vod_id(href)
            if not vod_id:
                continue
            title_elem = item.find("h4", class_="title-post")
            if title_elem:
                title = title_elem.text.strip()
            else:
                title = a.get("title", "") or a.text.strip()
            img = item.find("img", class_="thumb_img")
            pic = ""
            if img:
                pic = img.get("data-src") or img.get("src", "")
                pic = self.fix_url(pic)
            remark = ""
            stat = item.find("div", class_="stat")
            if stat:
                spans = stat.find_all("span")
                parts = []
                for span in spans:
                    text = span.text.strip()
                    if text:
                        parts.append(text)
                remark = " ".join(parts)
            if vod_id and title:
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
                if len(videos) >= limit:
                    break
        return videos

    def homeContent(self, filter=False):
        return {
            "class": self.classes,
            "filters": self.filters if filter else {}
        }

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self.get_html(self.host)
        if not html:
            return {"list": []}
        doc = BeautifulSoup(html, "html.parser")
        items = doc.select(".block-post .item")
        videos = self._parse_list_items(items, 20)
        return {"list": videos}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        pg = int(pg) if pg else 1
        if pg == 1:
            url = f"{self.host}/index.php/vod/type/id/{tid}.html"
        else:
            url = f"{self.host}/index.php/vod/type/id/{tid}-{pg}.html"
        html = self.get_html(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1, "limit": 20, "total": 0}
        doc = BeautifulSoup(html, "html.parser")
        items = doc.select(".block-post .item")
        videos = self._parse_list_items(items)
        pagecount = 99
        pagination = doc.find("div", class_=re.compile(r"page|pagination"))
        if pagination:
            links = pagination.find_all("a")
            for a in links:
                text = a.text.strip()
                if text.isdigit():
                    num = int(text)
                    if num > pagecount:
                        pagecount = num
        return {
            "list": videos,
            "page": pg,
            "pagecount": pagecount,
            "limit": 20,
            "total": 999
        }

    def _extract_player_url(self, html):
        if not html:
            return None
        m = re.search(r'var\s+player_aaaa\s*=\s*({[^;]+})', html)
        if m:
            try:
                data = json.loads(m.group(1))
                url = data.get("url", "")
                if url:
                    return url
            except:
                pass
        m = re.search(r'["\']([^"\']+\.m3u8[^"\']*)["\']', html)
        if m:
            return m.group(1)
        return None

    def _build_detail_result(self, vod_id, html, play_url):
        doc = BeautifulSoup(html, "html.parser")
        title = ""
        title_elem = doc.find("h1")
        if title_elem:
            title = title_elem.text.strip()
        if not title:
            title_match = re.search(r"<title>([^<]+)</title>", html)
            if title_match:
                title = title_match.group(1)
                title = re.sub(r"\s*[-–]\s*.*AV宅男网.*$", "", title)
                title = title.replace("在线播放", "").strip()
        pic = ""
        img = doc.find("img", class_="thumb_img")
        if img:
            pic = img.get("data-src") or img.get("src", "")
            pic = self.fix_url(pic)
        content = ""
        desc = doc.find("div", class_="content")
        if desc:
            content = desc.text.strip()
        return {"list": [{
            "vod_id": vod_id,
            "vod_name": title or f"视频{vod_id}",
            "vod_pic": pic,
            "vod_content": content,
            "vod_play_from": "默认线路",
            "vod_play_url": f"播放${play_url}"
        }]}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vod_id = ids[0]
        detail_url = f"{self.host}/index.php/vod/detail/id/{vod_id}.html"
        html = self.get_html(detail_url)
        if html:
            play_url = self._extract_player_url(html)
            if play_url:
                return self._build_detail_result(vod_id, html, play_url)
        play_page_url = f"{self.host}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        play_html = self.get_html(play_page_url)
        if play_html:
            play_url = self._extract_player_url(play_html)
            if play_url:
                return self._build_detail_result(vod_id, play_html, play_url)
        return {"list": [{
            "vod_id": vod_id,
            "vod_name": f"视频{vod_id}",
            "vod_pic": "",
            "vod_content": "",
            "vod_play_from": "默认线路",
            "vod_play_url": f"播放${vod_id}"
        }]}

    def searchContent(self, key, quick=False, pg="1"):
        if not key:
            return {"list": [], "page": 1, "pagecount": 1, "total": 0}
        pg = int(pg) if pg else 1
        url = f"{self.host}/index.php/vod/search.html?wd={urllib.parse.quote(key)}"
        html = self.get_html(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1, "total": 0}
        doc = BeautifulSoup(html, "html.parser")
        items = doc.select(".block-post .item")
        videos = self._parse_list_items(items)
        return {"list": videos, "page": pg, "pagecount": 99, "total": 999}

    def recommendContent(self, ids, pg):
        """
        相关推荐 - 基于当前视频ID获取同类推荐
        参考色猫视频实现
        """
        try:
            if not ids:
                return {"list": []}
            vid = str(ids[0]) if isinstance(ids, list) else str(ids)
            detail_result = self.detailContent([vid])
            detail_list = detail_result.get("list", [])
            if not detail_list:
                return {"list": []}
            vod_name = detail_list[0].get("vod_name", "")
            page = max(1, int(pg or 1))
            limit = 18
            seen = set()
            videos = []
            if vod_name and len(vod_name) > 2:
                keyword = vod_name[:6].strip()
                if keyword and len(keyword) > 1:
                    search_result = self.searchContent(keyword, 0, str(page))
                    search_list = search_result.get("list", [])
                    for item in search_list:
                        item_id = item.get("vod_id", "")
                        if item_id and item_id != vid and item_id not in seen:
                            seen.add(item_id)
                            videos.append(item)
                            if len(videos) >= limit:
                                break
            if len(videos) < 6:
                # 从分类"国产自拍"(tid=1)获取推荐
                category_result = self.categoryContent("1", str(page), {}, {})
                category_list = category_result.get("list", [])
                for item in category_list:
                    item_id = item.get("vod_id", "")
                    if item_id and item_id != vid and item_id not in seen:
                        seen.add(item_id)
                        videos.append(item)
                        if len(videos) >= limit:
                            break
            if len(videos) < 4:
                home_result = self.homeVideoContent()
                home_list = home_result.get("list", [])
                for item in home_list:
                    item_id = item.get("vod_id", "")
                    if item_id and item_id != vid and item_id not in seen:
                        seen.add(item_id)
                        videos.append(item)
                        if len(videos) >= limit:
                            break
            return {"list": videos[:limit]}
        except Exception as e:
            return {"list": []}