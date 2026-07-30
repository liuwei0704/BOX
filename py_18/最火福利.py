# coding: utf-8
"""
TVBox/FongMi 爬虫源 - 最火福利
站点: https://www.suoyoude.shop/
CMS: 苹果 CMS (MacCMS) HTML 站
分类数: 15
图片: 直链 JPEG (无需解密)
播放: encrypt=0 直链 m3u8
"""

import re
import json
from urllib.parse import urljoin
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://www.suoyoude.shop"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        self.classes = [
            {"type_id": "1", "type_name": "火爆影视"},
            {"type_id": "2", "type_name": "国产传媒"},
            {"type_id": "3", "type_name": "国产视频"},
            {"type_id": "4", "type_name": "欧美精选"},
            {"type_id": "6", "type_name": "国产主播"},
            {"type_id": "7", "type_name": "人妻少妇"},
            {"type_id": "8", "type_name": "教师学生"},
            {"type_id": "9", "type_name": "91大神"},
            {"type_id": "10", "type_name": "制服诱惑"},
            {"type_id": "11", "type_name": "强奸乱伦"},
            {"type_id": "12", "type_name": "日韩无码"},
            {"type_id": "13", "type_name": "巨乳系列"},
            {"type_id": "14", "type_name": "三级伦理"},
            {"type_id": "15", "type_name": "精品动漫"},
        ]
        self.filters = {}

    def getName(self):
        return "最火福利"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            resp = self.fetch(self.host + "/", headers=self.headers, timeout=10)
            html = resp.content.decode('utf-8', errors='ignore')
            videos = self._parse_video_list(html)
            return {"list": videos[:20] if videos else []}
        except Exception as e:
            self.log({"action": "homeVideoContent", "error": str(e)})
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        try:
            resp = self.fetch(url, headers=self.headers, timeout=10)
            html = resp.content.decode('utf-8', errors='ignore')
            videos = self._parse_video_list(html)
            total_pages = self._parse_total_pages(html)
            return {
                "list": videos,
                "page": int(page),
                "pagecount": total_pages or 99,
                "limit": 20,
                "total": 999
            }
        except Exception as e:
            self.log({"action": "categoryContent", "tid": tid, "pg": pg, "error": str(e)})
            return {"list": [], "page": int(page), "pagecount": 0, "limit": 20, "total": 0}

    def detailContent(self, ids):
        vod_id = str(ids[0])
        if '|$|' in vod_id:
            parts = vod_id.split('|$|')
            vid = parts[0]
            name = parts[1] if len(parts) > 1 else ""
            pic = parts[2] if len(parts) > 2 else ""
            remark = parts[3] if len(parts) > 3 else ""
        else:
            vid = vod_id
            name = ""
            pic = ""
            remark = ""

        if not name or not pic:
            try:
                url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
                resp = self.fetch(url, headers=self.headers, timeout=10)
                html = resp.content.decode('utf-8', errors='ignore')
                name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
                if name_match:
                    name = name_match.group(1).strip()
                pic_match = re.search(r'<img[^>]+src="([^"]+)"', html)
                if pic_match:
                    pic = pic_match.group(1)
                    if not pic.startswith("http"):
                        pic = urljoin(self.host, pic)
            except Exception as e:
                self.log({"action": "detailContent", "vid": vid, "error": str(e)})

        play_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        vod = {
            "vod_id": vid,
            "vod_name": name or "视频",
            "vod_pic": pic,
            "vod_remarks": remark,
            "vod_content": remark,
            "vod_play_from": "线路1",
            "vod_play_url": f"线路1${play_url}"
        }

        try:
            detail_url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
            resp = self.fetch(detail_url, headers=self.headers, timeout=10)
            detail_html = resp.content.decode('utf-8', errors='ignore')
            lines = self._parse_play_lines(detail_html)
            if lines:
                vod["vod_play_from"] = "$$$".join([l["name"] for l in lines])
                vod["vod_play_url"] = "$$$".join([f"{l['name']}${l['url']}" for l in lines])
        except Exception as e:
            self.log({"action": "detailContent_lines", "vid": vid, "error": str(e)})

        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        page = pg or "1"
        try:
            url = f"{self.host}/index.php/vod/search.html"
            data = {"wd": key}
            resp = self.post(url, data=data, headers=self.headers, timeout=10)
            html = resp.content.decode('utf-8', errors='ignore')
            videos = self._parse_video_list(html)
            return {"list": videos, "page": int(page)}
        except Exception as e:
            self.log({"action": "searchContent", "key": key, "error": str(e)})
            return {"list": []}

    def playerContent(self, flag, play_id, vipFlags):
        if play_id.endswith((".m3u8", ".mp4")):
            return {"parse": 0, "url": play_id, "header": self._make_play_header(play_id)}

        try:
            if not play_id.startswith("http"):
                play_url = urljoin(self.host, play_id)
            else:
                play_url = play_id

            resp = self.fetch(play_url, headers=self.headers, timeout=15)
            html = resp.content.decode('utf-8', errors='ignore')

            m3u8_url = self._extract_player_aaaa(html)
            if m3u8_url:
                if not m3u8_url.startswith("http"):
                    m3u8_url = urljoin(self.host, m3u8_url)
                return {"parse": 0, "url": m3u8_url, "header": self._make_play_header(m3u8_url)}

            m3u8_url = self._extract_macplayer(html)
            if m3u8_url:
                if not m3u8_url.startswith("http"):
                    m3u8_url = urljoin(self.host, m3u8_url)
                return {"parse": 0, "url": m3u8_url, "header": self._make_play_header(m3u8_url)}

            m3u8_match = re.search(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', html)
            if m3u8_match:
                return {"parse": 0, "url": m3u8_match.group(0), "header": self._make_play_header(m3u8_match.group(0))}

            return {"parse": 1, "url": play_url, "header": self.headers}

        except Exception as e:
            self.log({"action": "playerContent", "play_id": play_id, "error": str(e)})
            return {"parse": 1, "url": play_id, "header": self.headers}

    def localProxy(self, param):
        target = param.get("target", "")
        if target:
            try:
                resp = self.fetch(target, headers=self.headers, timeout=10)
                content = resp.content if hasattr(resp, 'content') else resp.text
                return [200, "image/jpeg", content, {}]
            except Exception:
                pass
        return [404, "text/plain", "Not Found", {}]

    def _parse_video_list(self, html):
        videos = []
        pattern = r'<li[^>]*class="[^"]*content-item[^"]*"[^>]*>.*?<a[^>]*href="[^"]*detail/id/(\d+)\.html"[^>]*title="([^"]*)"'
        items = re.findall(pattern, html, re.DOTALL)
        if not items:
            pattern2 = r'href="[^"]*detail/id/(\d+)\.html"[^>]*title="([^"]+)"'
            items = re.findall(pattern2, html)

        for vid, title in items[:30]:
            pic = ""
            pic_match = re.search(r'<img[^>]+src="([^"]+)"', html[html.find(f'detail/id/{vid}'):html.find(f'detail/id/{vid}') + 1000] if f'detail/id/{vid}' in html else html)
            if pic_match:
                pic = pic_match.group(1)
                if not pic.startswith("http"):
                    pic = urljoin(self.host, pic)

            remark = ""
            note_pattern = r'<span[^>]*class="[^"]*note[^"]*"[^>]*>([^<]+)</span>'
            note_match = re.search(note_pattern, html[html.find(f'detail/id/{vid}'):html.find(f'detail/id/{vid}') + 1000] if f'detail/id/{vid}' in html else html)
            if note_match:
                remark = note_match.group(1).strip()

            videos.append({
                "vod_id": f"{vid}|$|{title}|$|{pic}|$|{remark}",
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        return videos

    def _parse_total_pages(self, html):
        match = re.search(r'共(\d+)页', html)
        if match:
            return int(match.group(1))
        match = re.search(r'pagecount=(\d+)', html)
        if match:
            return int(match.group(1))
        pages = re.findall(r'/page/(\d+)\.html', html)
        if pages:
            return max([int(p) for p in pages])
        return 10

    def _parse_play_lines(self, html):
        lines = []
        tab_pattern = r'<div[^>]*class="[^"]*play-btn-group[^"]*"[^>]*>(.*?)</div>'
        tab_match = re.search(tab_pattern, html, re.DOTALL)
        if not tab_match:
            return lines
        tab_html = tab_match.group(1)
        line_pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
        for match in re.finditer(line_pattern, tab_html):
            href = match.group(1)
            name = match.group(2).strip()
            if not href.startswith("http"):
                href = urljoin(self.host, href)
            lines.append({"name": name, "url": href})
        seen = set()
        unique = []
        for line in lines:
            if line["url"] not in seen:
                seen.add(line["url"])
                unique.append(line)
        return unique

    def _extract_player_aaaa(self, html):
        start = html.find("var player_aaaa=")
        if start == -1:
            start = html.find("var player_aaaa =")
        if start != -1:
            segment = html[start:start + 2000]
            url_match = re.search(r'"url"\s*:\s*"([^"]+)"', segment)
            if url_match:
                m3u8 = url_match.group(1).replace('\\/', '/')
                if 'test.cn' not in m3u8 and 'example' not in m3u8:
                    return m3u8
        return None

    def _extract_macplayer(self, html):
        pattern = r'MacPlayer\.PlayUrl\s*=\s*"([^"]+)"'
        match = re.search(pattern, html)
        if match:
            return match.group(1).replace('\\/', '/')
        pattern2 = r'MacPlayer\s*=\s*{[^}]*PlayUrl\s*:\s*"([^"]+)"'
        match = re.search(pattern2, html)
        if match:
            return match.group(1).replace('\\/', '/')
        return None

    def _make_play_header(self, url):
        h = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36"
        }
        if self.host in url:
            h["Referer"] = self.host + "/"
        return h