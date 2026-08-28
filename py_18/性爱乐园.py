# coding: utf-8
import re
import json
from urllib.parse import urljoin, quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = "https://dunet.cfd"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        self.classes = [
            {"type_id": "31", "type_name": "明星"},
            {"type_id": "32", "type_name": "抖音"},
            {"type_id": "6", "type_name": "精品"},
            {"type_id": "14", "type_name": "国产"},
            {"type_id": "8", "type_name": "伦理"}
        ]
        self.filters = {}

    def getName(self):
        return "性爱乐园"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers)
            if resp is None:
                return ""
            if hasattr(resp, 'text'):
                return resp.text
            if hasattr(resp, 'content'):
                try:
                    return resp.content.decode('utf-8', errors='ignore')
                except:
                    return str(resp.content)
            return str(resp)
        except Exception as e:
            return ""

    def _fetch_post(self, url, data):
        try:
            resp = self.post(url, data=data, headers=self.headers)
            if resp is None:
                return ""
            if hasattr(resp, 'text'):
                return resp.text
            if hasattr(resp, 'content'):
                try:
                    return resp.content.decode('utf-8', errors='ignore')
                except:
                    return str(resp.content)
            return str(resp)
        except Exception as e:
            return ""

    def _parse_video_list(self, html):
        items = []
        if not html:
            return items
        block_pattern = r'<div class="item">\s*<a href="([^"]+)" title="([^"]*)">\s*<div class="img">\s*<img[^>]*data-original="([^"]+)"[^>]*>\s*<span[^>]*></span>\s*<span class="is-hd"></span>\s*</div>\s*<strong class="title">\s*([^<]*)</strong>\s*<div class="wrap">\s*<div class="duration">([^<]*)</div>\s*<div class="rating[^>]*>\s*([^<]*)</div>\s*</div>\s*<div class="wrap">\s*<div class="added"><em>([^<]*)</em></div>\s*<div class="views">([^<]*)</div>\s*</div>\s*</a>\s*</div>'
        matches = re.findall(block_pattern, html, re.DOTALL)
        for match in matches:
            link, title_full, pic, title, duration, rating, added, views = match
            vid_match = re.search(r'/id/(\d+)', link)
            if not vid_match:
                continue
            vod_id = vid_match.group(1)
            clean_title = title.strip() or title_full.strip()
            items.append({
                "vod_id": vod_id,
                "vod_name": clean_title,
                "vod_pic": pic.strip(),
                "vod_remarks": duration.strip()
            })
        if not items:
            item_pattern = r'<div class="item">.*?<a href="([^"]+)".*?title="([^"]*)".*?data-original="([^"]+)".*?<strong class="title">([^<]*)</strong>.*?<div class="duration">([^<]*)</div>'
            matches2 = re.findall(item_pattern, html, re.DOTALL)
            for match in matches2:
                link, title_full, pic, title, duration = match
                vid_match = re.search(r'/id/(\d+)', link)
                if vid_match:
                    items.append({
                        "vod_id": vid_match.group(1),
                        "vod_name": title.strip() or title_full.strip(),
                        "vod_pic": pic.strip(),
                        "vod_remarks": duration.strip()
                    })
        return items

    def _get_page_count(self, html):
        last_match = re.search(r'<a href="[^"]*page/(\d+)\.html"[^>]*>尾页</a>', html)
        if last_match:
            return int(last_match.group(1))
        page_matches = re.findall(r'<a href="[^"]*page/(\d+)\.html"', html)
        if page_matches:
            return max([int(p) for p in page_matches])
        total_match = re.search(r'共(\d+)页', html)
        if total_match:
            return int(total_match.group(1))
        return 1

    def _extract_player_url(self, html):
        """从播放页HTML中提取播放直链"""
        if not html:
            return None
        # 方法1: 直接搜索 "url":"https://...m3u8"
        m3u8_match = re.search(r'"url"\s*:\s*"(https?://[^"]+\.m3u8[^"]*)"', html)
        if m3u8_match:
            return m3u8_match.group(1)
        # 方法2: 提取 player_aaaa 中的 url 字段
        player_match = re.search(r'var player_aaaa\s*=\s*{[^}]*"url"\s*:\s*"([^"]+)"', html)
        if player_match:
            return player_match.group(1)
        # 方法3: 直接搜索 m3u8 地址
        m3u8_match2 = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if m3u8_match2:
            return m3u8_match2.group(0)
        return None

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html(self.host)
        if not html:
            return {"list": []}
        items = self._parse_video_list(html)
        return {"list": items[:20]}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        page = pg or "1"
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
        items = self._parse_video_list(html)
        pagecount = self._get_page_count(html)
        return {
            "list": items,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 20,
            "total": len(items)
        }

    def detailContent(self, ids):
        """详情页 - 提取信息 + 直接获取播放直链"""
        vod_id = ids[0] if ids else ""
        detail_url = f"{self.host}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        html = self._fetch_html(detail_url)

        vod_name = ""
        vod_pic = ""
        vod_remarks = ""
        vod_content = ""
        play_url = None

        if html:
            # 标题
            title_match = re.search(r'<h1>([^<]+)</h1>', html)
            if title_match:
                vod_name = title_match.group(1).strip()
            # 封面图
            pic_match = re.search(r'<img[^>]*data-original="([^"]+)"[^>]*alt="[^"]*"', html)
            if not pic_match:
                pic_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*class="thumb"', html)
            if pic_match:
                vod_pic = pic_match.group(1)
            # 时长
            duration_match = re.search(r'时长:\s*<em>([^<]*)</em>', html)
            if duration_match:
                vod_remarks = duration_match.group(1)
            # 描述
            desc_match = re.search(r'描述:\s*<em>([^<]*)</em>', html)
            if desc_match:
                vod_content = desc_match.group(1)
            else:
                vod_content = vod_name
            # 提取播放直链
            play_url = self._extract_player_url(html)

        # 如果提取到播放地址，直接返回直链
        if play_url:
            vod_play_url = f"播放${play_url}"
            vod_play_from = "直链"
        else:
            # 如果没有提取到，传递 vod_id 让 playerContent 再尝试
            vod_play_url = f"播放${vod_id}"
            vod_play_from = "播放"

        vod = {
            "vod_id": vod_id,
            "vod_name": vod_name or "视频",
            "vod_pic": vod_pic or "",
            "vod_remarks": vod_remarks or "",
            "vod_content": vod_content or vod_name or "",
            "vod_play_from": vod_play_from,
            "vod_play_url": vod_play_url
        }
        return {"list": [vod]}

    def searchContent(self, key, quick=False, pg="1"):
        if not key or not key.strip():
            return {"list": [], "page": 1}
        page = pg or "1"
        search_url = f"{self.host}/index.php/vod/search.html"
        html = self._fetch_post(search_url, {"wd": key.strip()})
        if not html:
            get_url = f"{self.host}/search/{quote(key.strip())}/"
            html = self._fetch_html(get_url)
        if not html:
            return {"list": [], "page": int(page)}
        items = self._parse_video_list(html)
        return {"list": items, "page": int(page)}

    def playerContent(self, flag, id, vipFlags):
        """播放直链提取 - 尽量返回 parse:0 直链"""
        # 如果 id 已经是直链地址
        if id and any(ext in id for ext in [".m3u8", ".mp4", ".ts"]):
            return {"parse": 0, "url": id, "header": self.headers}

        # 如果 id 是详情页URL，提取直链
        if id and id.startswith("http") and "dunet.cfd" in id:
            html = self._fetch_html(id)
            play_url = self._extract_player_url(html)
            if play_url:
                return {"parse": 0, "url": play_url, "header": self.headers}

        # 如果 id 是 vod_id（纯数字），请求详情页提取直链
        if id and re.match(r'^\d+$', str(id)):
            detail_url = f"{self.host}/index.php/vod/play/id/{id}/sid/1/nid/1.html"
            html = self._fetch_html(detail_url)
            play_url = self._extract_player_url(html)
            if play_url:
                return {"parse": 0, "url": play_url, "header": self.headers}

        # 如果 id 包含 $ 分隔符，提取后面的部分
        if id and "$" in str(id):
            parts = str(id).split("$")
            if len(parts) >= 2:
                vid_or_url = parts[-1]
                if any(ext in vid_or_url for ext in [".m3u8", ".mp4", ".ts"]):
                    return {"parse": 0, "url": vid_or_url, "header": self.headers}
                if re.match(r'^\d+$', vid_or_url):
                    detail_url = f"{self.host}/index.php/vod/play/id/{vid_or_url}/sid/1/nid/1.html"
                    html = self._fetch_html(detail_url)
                    play_url = self._extract_player_url(html)
                    if play_url:
                        return {"parse": 0, "url": play_url, "header": self.headers}

        # 最后降级：让 TVBox 嗅探
        return {"parse": 1, "url": id or "", "header": self.headers}

    def localProxy(self, param):
        return [404, "text/plain", "Not Found", {}]

    def isVideoFormat(self, url):
        return url and any(ext in url for ext in [".m3u8", ".mp4", ".flv", ".avi", ".mkv", ".ts"])

    def destroy(self):
        pass