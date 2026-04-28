import re
import json
import urllib.request
import urllib.parse
import ssl

class Spider():
    vod_cache = {}

    def getName(self):
        return "第一AV_全兼容穩定版"

    def init(self, extend=""):
        self.host = "https://chenjiuq.cfd"
        self.ctx = ssl._create_unverified_context()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": self.host
        }

    # --- 框架必需方法補齊 ---
    def getDependence(self): return []
    def homeVideoContent(self): return {"list": []}
    def isVideoCanPlay(self): return True
    # ----------------------

    def fetch(self, url, ref=""):
        try:
            headers = self.headers.copy()
            if ref: headers["Referer"] = ref
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=self.ctx, timeout=10) as response:
                return response.read().decode('utf-8', errors='ignore')
        except: return ""

    def homeContent(self, filter):
        return {
            "class": [
                {"type_name": "视频一区", "type_id": "1"}, 
                {"type_name": "中文字幕", "type_id": "7"}, 
                {"type_name": "麻豆传媒", "type_id": "21"},
                {"type_name": "日韩电影", "type_id": "6"}
            ]
        }

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
        html = self.fetch(url, self.host)
        videos = []
        items = re.findall(r'<dl>.*?href="([^"]+)" title="([^"]+)" target="_blank">.*?data-src="([^"]+)"', html, re.S)
        for link, name, pic in items:
            vid_match = re.search(r'/id/(\d+)', link)
            if vid_match:
                vid = vid_match.group(1)
                img = pic if pic.startswith("http") else self.host + pic
                Spider.vod_cache[vid] = {"name": name, "pic": img}
                videos.append({"vod_id": vid, "vod_name": name, "vod_pic": img})
        return {"list": videos, "page": pg, "pagecount": 99}

    def detailContent(self, ids):
        vid = ids[0]
        cache = Spider.vod_cache.get(vid, {})
        name = cache.get("name", "")
        pic = cache.get("pic", "")

        if not name:
            url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
            html = self.fetch(url, self.host)
            title_m = re.search(r'<title>(.*?)</title>', html, re.S)
            if title_m: name = title_m.group(1).split('-')[0].strip()
            pic_m = re.search(r'data-src="(.*?)"', html)
            if pic_m: pic = pic_m.group(1) if pic_m.group(1).startswith("http") else self.host + pic_m.group(1)

        vod = {
            "vod_id": vid,
            "vod_name": name if name else f"影片:{vid}",
            "vod_pic": pic,
            "type_name": "影片",
            "vod_remarks": "高清",
            "vod_play_from": "默认线路",
            "vod_play_url": f"播放${vid}"
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        url = f"{self.host}/index.php/vod/play/id/{id}/sid/1/nid/1.html"
        html = self.fetch(url, f"{self.host}/index.php/vod/detail/id/{id}.html")
        match = re.search(r'var player_aaaa=({.*?})', html)
        if match:
            try:
                data = json.loads(match.group(1))
                return {"parse": 0, "url": data.get("url"), "header": self.headers}
            except: pass
        return {"parse": 1, "url": url}

    def searchContent(self, key, quick, pg="1"):
        url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{urllib.parse.quote(key)}.html"
        html = self.fetch(url, self.host)
        videos = []
        items = re.findall(r'<dl>.*?href="([^"]+)" title="([^"]+)" target="_blank">.*?data-src="([^"]+)"', html, re.S)
        for link, name, pic in items:
            vid_match = re.search(r'/id/(\d+)', link)
            if vid_match:
                vid = vid_match.group(1)
                img = pic if pic.startswith("http") else self.host + pic
                Spider.vod_cache[vid] = {"name": name, "pic": img}
                videos.append({"vod_id": vid, "vod_name": name, "vod_pic": img})
        return {"list": videos}