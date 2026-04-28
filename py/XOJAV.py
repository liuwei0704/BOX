import sys, re, json
import urllib.request
import urllib.parse

class Spider():
    def __init__(self):
        self.host = "https://xojav.tv"

    def getName(self): return "XOJAV"
    def init(self, extend=""): pass
    def getDependence(self): return ['re', 'json']

    def fetch(self, url):
        import urllib.request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': self.host
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as res:
                return res.read().decode('utf-8', errors='ignore')
        except:
            return ""

    def homeContent(self, filter):
        # 已補全網頁端主流分類
        res = {
            'class': [
                {"type_name": "最新影片", "type_id": "latest-updates"},
                {"type_name": "亞洲無碼", "type_id": "uncensored-asia"},
                {"type_name": "亞洲有碼", "type_id": "censored-asia"},
                {"type_name": "台灣自拍", "type_id": "taiwan-av"},
                {"type_name": "成人動漫", "type_id": "anime"},
                {"type_name": "國產精選", "type_id": "chinese-av"},
                {"type_name": "素人/人妻", "type_id": "amateur"}
            ],
            'list': []
        }
        try:
            html = self.fetch(self.host)
            res['list'] = self.parseList(html)
        except:
            pass
        return res

    def homeVideoContent(self):
        return {"list": self.parseList(self.fetch(self.host))}

    def categoryContent(self, tid, pg, filter, extend):
        # XOJAV 的分頁路徑通常為 /category/tid?page=pg 或 /tid?page=pg
        url = f"{self.host}/{tid}?page={pg}"
        return {"list": self.parseList(self.fetch(url))}

    def detailContent(self, ids):
        vid = ids[0]
        html = self.fetch(f"{self.host}/videos/{vid}")
        title = re.search(r'property="og:title"\s+content="([^"]+)"', html)
        pic = re.search(r'property="og:image"\s+content="([^"]+)"', html)
        return {"list": [{
            "vod_id": vid,
            "vod_name": title.group(1).replace(' - XOJAV', '').strip() if title else vid,
            "vod_pic": pic.group(1) if pic else "",
            "vod_play_from": "XO-Stream",
            "vod_play_url": f"播放正片${vid}"
        }]}

    def playerContent(self, flag, id, vipFlags):
        video_page = f"{self.host}/videos/{id}"
        html = self.fetch(video_page)
        # 提取串流地址
        raw_url = re.search(r"var\s+stream\s*=\s*'([^']+)'", html)
        url = raw_url.group(1).replace('\\/', '/') if raw_url else ""
        return {
            "parse": 0,
            "play": 0,
            "url": url,
            "header": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": video_page
            }
        }

    def parseList(self, html):
        videos = []
        if not html: return videos
        # 兼容多種影片方塊結構
        pattern = r'href="[^"]*/videos/([^"/]+)"[^>]*>.*?alt="([^"]+)"'
        for vid, title in re.findall(pattern, html, re.S):
            if vid not in [v['vod_id'] for v in videos]:
                videos.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": f"https://cdn.18jav.tv/storage/{vid}/320_180.jpg"
                })
        return videos

    def searchContent(self, key, quick):
        url = f"{self.host}/search?q={urllib.parse.quote(key)}"
        return {"list": self.parseList(self.fetch(url))}

    def localProxy(self, param):
        return [200, "video/MP2T", b"", ""]
