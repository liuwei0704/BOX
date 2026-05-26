# coding=utf-8
import re
import json
import urllib.request
import urllib.parse
from base.spider import Spider

BASE = "https://missavt.com"

class Spider(Spider):
    def getName(self):
        return "MissAVt"

    def init(self, extend=""):
        self.site_url = BASE
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": BASE + "/"
        }

    def getDependence(self):
        return []

    def header(self):
        return self.headers

    def _get(self, url):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except:
            return None

    def _fix(self, u):
        if not u:
            return ""
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return BASE + u
        return u

    def _parse_list(self, html):
        if not html:
            return []
        results = []
        items = re.findall(r'<li>\s*<div[^>]*class="video-item"[^>]*>(.*?)</div>\s*<a[^>]*class="[^"]*my-1[^"]*"[^>]*href="[^"]*"[^>]*>([^<]+)</a>', html, re.DOTALL)
        for item_html, title in items:
            m = re.search(r'href=["\']/watch/([^"\']+)/?["\']', item_html)
            if not m:
                continue
            vod_id = m.group(1)
            m2 = re.search(r'data-src=["\']([^"\']+)["\']', item_html)
            pic = m2.group(1) if m2 else ""
            results.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": self._fix(pic)
            })
        return results

    def homeVideoContent(self):
        return self.homeContent(False)

    def homeContent(self, filter):
        html = self._get(BASE + "/")
        video_list = self._parse_list(html) if html else []
        return {
            "class": [
                {"type_id": "1", "type_name": "推荐视频"},
                {"type_id": "2", "type_name": "热门视频"},
                {"type_id": "3", "type_name": "无码破解"},
                {"type_id": "4", "type_name": "中文字幕"},
                {"type_id": "5", "type_name": "素人"},
            ],
            "list": video_list[:24],
            "filters": {}
        }

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        type_map = {
            "1": "",
            "2": "/sort/month_hot/",
            "3": "/category/reducing-mosaic/",
            "4": "/category/chinese-subtitle/",
            "5": "/category/amateur/",
        }
        path = type_map.get(tid, "")
        if page > 1:
            url = f"{BASE}{path}?page={page}"
        else:
            url = f"{BASE}{path}"
        html = self._get(url)
        video_list = self._parse_list(html) if html else []
        return {
            "page": page,
            "pagecount": 50,
            "limit": 36,
            "total": 999,
            "list": video_list
        }

    def detailContent(self, ids):
        result = {"list": []}
        for vod_id in ids:
            try:
                url = f"{BASE}/watch/{vod_id}/"
                html = self._get(url)
                if not html:
                    continue
                title = ""
                m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
                if m:
                    title = m.group(1).strip()
                pic = ""
                m = re.search(r'<div[^>]*class=["\'][^"\']*poster[^"\']*["\'][^>]*>.*?<img[^>]*(?:data-src|src)=["\']([^"\']+)["\']', html, re.DOTALL)
                if m:
                    pic = self._fix(m.group(1))
                play_url = ""
                m = re.search(r'<div[^>]*class=["\'][^"\']*poster[^"\']*["\'][^>]*data-url=["\']([^"\']+)["\']', html)
                if m:
                    play_url = self._fix(m.group(1))
                if not play_url:
                    m = re.search(r'<video[^>]*src=["\']([^"\']+\.m3u8[^"\']*)["\']', html)
                    if m:
                        play_url = self._fix(m.group(1))
                result["list"].append({
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_play_from": "默认",
                    "vod_play_url": f"播放${play_url}" if play_url else ""
                })
            except:
                continue
        return result

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        url = f"{BASE}/search/{urllib.parse.quote(key)}/"
        if page > 1:
            url = f"{BASE}/search/{urllib.parse.quote(key)}/?page={page}"
        html = self._get(url)
        video_list = self._parse_list(html) if html else []
        return {
            "list": video_list,
            "page": page,
            "pagecount": 20
        }

    def playerContent(self, flag, id, vipFlags):
        # 构建播放页URL
        if id.startswith('http'):
            play_url = id
        else:
            play_url = BASE + '/watch/' + id + '/'
        # 实时抓取播放页，提取最新的m3u8链接
        html = self._get(play_url)
        if html:
            # 从 poster 的 data-url 提取
            m = re.search(r'<div[^>]*class=["\'][^"\']*poster[^"\']*["\'][^>]*data-url=["\']([^"\']+)"', html)
            if m:
                m3u8_url = self._fix(m.group(1))
                return {
                    "parse": 0,
                    "url": m3u8_url,
                    "header": json.dumps(self.headers)
                }
            # 从 video 标签提取
            m = re.search(r'<video[^>]*src=["\']([^"\']+\.m3u8[^"\']*)"', html)
            if m:
                m3u8_url = self._fix(m.group(1))
                return {
                    "parse": 0,
                    "url": m3u8_url,
                    "header": json.dumps(self.headers)
                }
        # 降级：返回播放页让客户端解析
        return {
            "parse": 1,
            "url": play_url,
            "header": json.dumps(self.headers)
        }

    def destroy(self):
        pass