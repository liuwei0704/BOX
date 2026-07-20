import sys
import re
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "尤爱视频"

    def init(self, extend=""):
        super().init(extend)
        self.site_url = "https://uaisp.org"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": self.site_url + "/"
        }
        self.sess = requests.Session()
        self.sess.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1)))

    def decode_str(self, text):
        if not text: return ""
        def replace_func(match):
            val = match.group(1)
            try: return chr(int(val, 32))
            except: return val
        return re.sub(r'([a-zA-Z0-9]+)-?', replace_func, text)

    def fetch(self, url):
        try:
            res = self.sess.get(url, headers=self.headers, timeout=10, verify=False)
            return res
        except: return None

    def homeContent(self, filter):
        if not hasattr(self, 'site_url'): self.init()
        res = self.fetch(self.site_url)
        if not res: return {"class": []}
        match = re.search(r'loading\(\s*(\{.*?\})\s*\)', res.text, re.S)
        if not match: return {"class": []}
        data = json.loads(match.group(1))
        cate_list = []
        for item in data.get("category", []):
            tid = str(item.get("id"))
            cate_list.append({"type_name": self.decode_str(item.get("name")), "type_id": tid})
        return {"class": cate_list}

    def detailContent(self, ids):
        if not hasattr(self, 'site_url'): self.init()
        mid = ids[0]
        url = f"{self.site_url}/play/{mid}.html"
        res = self.fetch(url)
        if not res: return {"list": []}
        match = re.search(r'loading\(\s*(\{.*?\})\s*\)', res.text, re.S)
        if not match: return {"list": []}
        root = json.loads(match.group(1))
        item = root.get("self", {})
        config = root.get("config", {})
        img_p = config.get("image", "")
        
        u1 = item.get('url', '')
        i1 = item.get('info', '')
        play_url = f"{u1}{i1}"
        
        play_list = []
        if play_url:
            # 这里的 ID 携带了详情页 URL 用于 playerContent 里的 Referer
            play_list.append(f"线路1(主线)${play_url}|{url}")
            if "api-pstatp.com" in play_url and img_p.startswith("http"):
                u2 = play_url.replace("https://api-pstatp.com", img_p.rstrip("/"))
                play_list.append(f"线路2(直连)${u2}|{url}")

        vod = {
            "vod_id": mid,
            "vod_name": self.decode_str(item.get("name")),
            "vod_pic": img_p + item.get("src", "") if not item.get("src", "").startswith("http") else item.get("src", ""),
            "vod_play_from": "尤爱视频",
            "vod_play_url": "#".join(play_list)
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        if not hasattr(self, 'site_url'): self.init()
        parts = id.split('|')
        p_url = parts[0]
        r_url = parts[1] if len(parts) > 1 else self.site_url + "/"
        
        return {
            "parse": 0,
            "url": p_url,
            "header": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": r_url,
                "Origin": self.site_url,
                "Accept": "*/*",
                "Connection": "keep-alive",
                "Range": "bytes=0-"
            }
        }

    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'site_url'): self.init()
        pg = int(pg) if str(pg).isdigit() else 1
        url = f"{self.site_url}/type/{tid}.html" if pg <= 1 else f"{self.site_url}/type/{tid}-{pg}.html"
        res = self.fetch(url)
        video_list = []
        if res:
            match = re.search(r'loading\(\s*(\{.*?\})\s*\)', res.text, re.S)
            if match:
                root = json.loads(match.group(1))
                img_p = root.get("config", {}).get("image", "")
                archives = root.get("archives", {})
                data_list = archives.get("data", []) if isinstance(archives, dict) else (archives if isinstance(archives, list) else [])
                for v in data_list:
                    src = v.get("src", "")
                    video_list.append({
                        "vod_id": str(v.get("id")),
                        "vod_name": self.decode_str(v.get("name")),
                        "vod_pic": img_p + src if not src.startswith("http") else src,
                        "vod_remarks": ""
                    })
        return {"list": video_list, "page": pg, "pagecount": pg + 1 if len(video_list) >= 10 else pg}

    def searchContent(self, key, quick, pg=1):
        if not hasattr(self, 'site_url'): self.init()
        url = f"{self.site_url}/search/{key}.html"
        res = self.fetch(url)
        video_list = []
        if res:
            match = re.search(r'loading\(\s*(\{.*?\})\s*\)', res.text, re.S)
            if match:
                root = json.loads(match.group(1))
                img_p = root.get("config", {}).get("image", "")
                archives = root.get("archives", {})
                data_list = archives.get("data", []) if isinstance(archives, dict) else []
                for v in data_list:
                    src = v.get("src", "")
                    video_list.append({
                        "vod_id": str(v.get("id")),
                        "vod_name": self.decode_str(v.get("name")),
                        "vod_pic": img_p + src if not src.startswith("http") else src,
                        "vod_remarks": ""
                    })
        return {"list": video_list, "page": pg, "pagecount": pg}