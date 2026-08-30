# coding: utf-8
# TVBox/FongMi 爬虫源 - zxavmb.sbs
# 站点: http://o2bi40og.zxavmb1.sbs/

import re
import json
import urllib.request
import urllib.parse

try:
    from base.spider import Spider as BaseSpider
except ImportError:
    class BaseSpider:
        pass


class Spider(BaseSpider):
    def __init__(self):
        self.host = "http://o2bi40og.zxavmb1.sbs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "精品推荐"},
            {"type_id": "2", "type_name": "主播秀色"},
            {"type_id": "3", "type_name": "日本有码"},
            {"type_id": "4", "type_name": "日本无码"},
            {"type_id": "5", "type_name": "中文字幕"},
            {"type_id": "6", "type_name": "童颜巨乳"},
            {"type_id": "7", "type_name": "性感人妻"},
            {"type_id": "8", "type_name": "强奸乱伦"},
            {"type_id": "9", "type_name": "欧美情色"},
            {"type_id": "10", "type_name": "三级伦理"},
            {"type_id": "11", "type_name": "卡通动漫"},
            {"type_id": "12", "type_name": "丝袜OL"},
            {"type_id": "13", "type_name": "自拍偷拍"},
            {"type_id": "14", "type_name": "日本片商"},
            {"type_id": "15", "type_name": "剧情介绍"},
            {"type_id": "16", "type_name": "网曝系列"},
            {"type_id": "17", "type_name": "同性恋"},
            {"type_id": "18", "type_name": "探花嫖娼"},
            {"type_id": "19", "type_name": "国产人妻"},
            {"type_id": "20", "type_name": "国产SM"},
            {"type_id": "21", "type_name": "国产丝袜"},
            {"type_id": "22", "type_name": "麻豆传媒"},
            {"type_id": "23", "type_name": "国产乱伦"},
            {"type_id": "24", "type_name": "明星换脸"},
            {"type_id": "25", "type_name": "主奴调教"},
            {"type_id": "26", "type_name": "凌辱快感"},
            {"type_id": "27", "type_name": "多人群交"},
            {"type_id": "28", "type_name": "角色剧情"},
            {"type_id": "29", "type_name": "港台辣妹"},
            {"type_id": "30", "type_name": "重口性癖"},
            {"type_id": "31", "type_name": "变性伪娘"},
            {"type_id": "32", "type_name": "VR视角"},
        ]
        self.filters = {}
        for c in self.classes:
            self.filters[c["type_id"]] = []

    def getName(self):
        return "精品在线"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _fetch(self, url):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception:
            return ""

    def _fix_url(self, url):
        if not url:
            return ""
        url = url.strip()
        if url.startswith("//"):
            return "http:" + url
        if url.startswith("/"):
            return self.host + url
        if not url.startswith("http"):
            return self.host + "/" + url
        return url

    def _parse_videos(self, html, default_tid="1"):
        """解析视频列表，vod_id 编码为 vid|tid"""
        videos = []
        if not html:
            return videos
        # 匹配每个视频块
        pattern = r'<div[^>]*class="[^"]*thumbnail[^"]*"[^>]*>.*?<a[^>]*href="[^"]*video_detail/(\d+)/(\d+)/[^"]*"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*title[^"]*"[^>]*>([^<]*)</div>'
        matches = re.findall(pattern, html, re.DOTALL)
        for vid, tid, pic, title in matches:
            combined_id = f"{vid}|{tid}"
            videos.append({
                "vod_id": combined_id,
                "vod_name": title.strip(),
                "vod_pic": self._fix_url(pic),
                "vod_remarks": "",
            })
        # 如果上面没匹配到，回退到只匹配 vid
        if not videos:
            pattern2 = r'<div[^>]*class="[^"]*thumbnail[^"]*"[^>]*>.*?<a[^>]*href="[^"]*video_detail/(\d+)/[^"]*"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*title[^"]*"[^>]*>([^<]*)</div>'
            matches2 = re.findall(pattern2, html, re.DOTALL)
            for vid, pic, title in matches2:
                combined_id = f"{vid}|{default_tid}"
                videos.append({
                    "vod_id": combined_id,
                    "vod_name": title.strip(),
                    "vod_pic": self._fix_url(pic),
                    "vod_remarks": "",
                })
        return videos

    def _get_play_url(self, html):
        if not html:
            return ""
        match = re.search(r'<iframe[^>]+src="[^"]*Play=([^&]+)', html)
        if match:
            return urllib.parse.unquote(match.group(1))
        match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
        if match:
            return match.group(1)
        return ""

    def homeContent(self, filter=False):
        html = self._fetch(self.host + "/")
        if not html:
            return {"class": self.classes, "list": []}
        videos = self._parse_videos(html, default_tid="1")
        result = {"class": self.classes, "list": videos}
        if filter:
            result["filters"] = self.filters
        return result

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        return self.homeContent(filter=False)

    def categoryContent(self, tid, pg=1, filter=False, extend=None):
        if not tid:
            return {"list": [], "page": 1, "pagecount": 1}
        try:
            pg = int(pg)
        except:
            pg = 1
        if pg < 1:
            pg = 1
        url = f"{self.host}/video_list/{tid}/{pg}/index.html"
        html = self._fetch(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1}
        videos = self._parse_videos(html, default_tid=tid)
        total_pg = pg
        page_matches = re.findall(r'/video_list/[^/]+/(\d+)/index\.html', html)
        for p in page_matches:
            try:
                if int(p) > total_pg:
                    total_pg = int(p)
            except:
                pass
        if total_pg == pg and len(videos) > 0:
            total_pg = 10
        return {
            "list": videos,
            "page": pg,
            "pagecount": total_pg,
            "limit": 20,
            "total": len(videos) * (total_pg - pg + 1) if total_pg > pg else len(videos),
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        combined = ids[0] if isinstance(ids, list) else ids
        # 解析 vid|tid
        if '|' in combined:
            parts = combined.split('|', 1)
            vid = parts[0]
            tid = parts[1] if len(parts) > 1 else "1"
        else:
            vid = combined
            tid = "1"
        url = f"{self.host}/video_detail/{vid}/{tid}/index.html"
        html = self._fetch(url)
        if not html:
            return {"list": []}
        title = ""
        title_match = re.search(r'<div[^>]*class="[^"]*break-all[^"]*"[^>]*>([^<]+)</div>', html)
        if title_match:
            title = title_match.group(1).strip()
        pic = ""
        img_match = re.search(r'<img[^>]*class="[^"]*shadow-lg[^"]*"[^>]*(?:data-src|src)="([^"]+)"', html)
        if img_match:
            pic = self._fix_url(img_match.group(1))
        play_url = ""
        play_link = re.search(r'<a[^>]*class="[^"]*play-url[^"]*"[^>]*href="([^"]+)"', html)
        if play_link:
            play_page_url = self._fix_url(play_link.group(1))
            play_html = self._fetch(play_page_url)
            play_url = self._get_play_url(play_html)
        if not play_url:
            iframe_match = re.search(r'<iframe[^>]+src="[^"]*Play=([^&]+)', html)
            if iframe_match:
                play_url = urllib.parse.unquote(iframe_match.group(1))
        vod = {
            "vod_id": combined,
            "vod_name": title,
            "vod_pic": pic,
            "type_name": "",
            "vod_actor": "",
            "vod_director": "",
            "vod_content": "",
            "vod_play_from": "m3u8",
            "vod_play_url": f"线路1${play_url}" if play_url else "",
        }
        return {"list": [vod]}

    def searchContent(self, key, quick=False, pg=1):
        if not key:
            return {"list": [], "page": 1, "pagecount": 1}
        try:
            pg = int(pg)
        except:
            pg = 1
        if pg < 1:
            pg = 1
        url = f"{self.host}/?search={urllib.parse.quote(key)}"
        if pg > 1:
            url += f"&pg={pg}"
        html = self._fetch(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1}
        videos = self._parse_videos(html, default_tid="1")
        return {
            "list": videos,
            "page": pg,
            "pagecount": 1,
            "limit": 20,
            "total": len(videos),
        }

    def playerContent(self, flag, id, vipFlags=None):
        if id and '$' in id:
            parts = id.split('$', 1)
            if len(parts) == 2 and parts[1].startswith('http'):
                id = parts[1]
        if id and id.startswith('http') and '.m3u8' in id:
            return {"parse": 0, "playUrl": "", "url": id}
        if id:
            play_url = self._fix_url(id)
            html = self._fetch(play_url)
            m3u8 = self._get_play_url(html)
            if m3u8:
                return {"parse": 0, "playUrl": "", "url": m3u8}
        return {"parse": 1, "playUrl": "", "url": ""}

    def destroy(self):
        pass