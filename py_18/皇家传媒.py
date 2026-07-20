import sys, re, json, urllib.parse

try:
    from spider import Spider
except ImportError:
    class Spider:
        def __init__(self): 
            self.site_url = ""
            import requests
            self.sess = requests.Session()
        def fetch(self, url, headers=None, **kwargs):
            try:
                res = self.sess.get(url, headers=headers, verify=False, timeout=15)
                return res
            except: return None

class Spider(Spider):
    def getDependence(self):
        return ['requests']

    def getName(self):
        return "皇家传媒"

    def init(self, extend=""):
        self.site_url = "https://hua00.sbs"
        if not hasattr(self, 'sess'):
            import requests
            self.sess = requests.Session()

    def getHeaders(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": self.site_url
        }

    def homeContent(self, filter):
        if not hasattr(self, 'site_url') or not self.site_url: self.init()
        res = self.fetch(self.site_url, headers=self.getHeaders())
        classes = []
        if res:
            html = res.text if hasattr(res, 'text') else ""
            matches = re.finditer(r'href="/vodtype/(\d+)\.html"[^>]*>([^<]+)</a>', html)
            seen = set()
            for m in matches:
                tid, name = m.group(1), m.group(2).strip()
                if tid not in seen and len(name) < 10 and name not in ['首页', '留言']:
                    classes.append({"type_id": tid, "type_name": name})
                    seen.add(tid)
        return {"class": classes}

    # --- 修复 Fongmi 报错的关键：首页推荐视频 ---
    def homeVideoContent(self):
        if not hasattr(self, 'site_url') or not self.site_url: self.init()
        res = self.fetch(self.site_url, headers=self.getHeaders())
        video_list = []
        if res:
            html = res.text if hasattr(res, 'text') else ""
            matches = re.finditer(r'href="(/voddetail/(\d+)\.html)".*?title="([^"]+)"', html, re.S)
            for m in matches[:30] if isinstance(matches, list) else matches: # 抓取前30个作为推荐
                ctx = html[max(0, m.start()-1200):m.end()]
                img = re.search(r'(?:data-realsrc|data-src|src)="([^"]+)"', ctx)
                pic = img.group(1) if img else ""
                if pic.startswith("//"): pic = "https:" + pic
                elif pic.startswith("/"): pic = self.site_url + pic
                video_list.append({"vod_id": m.group(2), "vod_name": m.group(3), "vod_pic": pic, "vod_remarks": "最新"})
                if len(video_list) >= 30: break
        return {"list": video_list}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if str(pg).isdigit() else 1
        url = f"{self.site_url}/vodtype/{tid}-{pg}.html"
        res = self.fetch(url, headers=self.getHeaders())
        video_list = []
        if res:
            html = res.text if hasattr(res, 'text') else ""
            matches = re.finditer(r'href="(/voddetail/(\d+)\.html)".*?title="([^"]+)"', html, re.S)
            for m in matches:
                ctx = html[max(0, m.start()-1200):m.end()]
                img = re.search(r'(?:data-realsrc|data-src|src)="([^"]+)"', ctx)
                pic = img.group(1) if img else ""
                if pic.startswith("//"): pic = "https:" + pic
                elif pic.startswith("/"): pic = self.site_url + pic
                video_list.append({"vod_id": m.group(2), "vod_name": m.group(3), "vod_pic": pic, "vod_remarks": ""})
        return {"list": video_list, "page": pg, "pagecount": 999, "limit": 20, "total": 9999}

    def detailContent(self, ids):
        res = self.fetch(f"{self.site_url}/voddetail/{ids[0]}.html", headers=self.getHeaders())
        if not res: return {}
        html = res.text if hasattr(res, 'text') else ""
        name_m = re.search(r'<title>(.*?)剧情介绍', html) or re.search(r'<h1>(.*?)</h1>', html)
        pic_m = re.search(r'class="stui-content__thumb".*?src="([^"]+)"', html, re.S)
        pic = pic_m.group(1) if pic_m else ""
        if pic and not pic.startswith("http"): pic = self.site_url + pic
        play_list = []
        for m in re.finditer(r'href="(/vodplay/[^"]+)"[^>]*>(.*?)</a>', html):
            v_url, v_name = m.group(1), re.sub(r'<.*?>', '', m.group(2)).strip()
            if "vodplay" in v_url and v_name: play_list.append(f"{v_name}${v_url}")
        vod = {"vod_id": ids[0], "vod_name": name_m.group(1).strip() if name_m else "未知", "vod_pic": pic, "vod_play_from": "皇家专线", "vod_play_url": "#".join(play_list)}
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        pg = int(pg) if str(pg).isdigit() else 1
        url = f"{self.site_url}/vodsearch/{urllib.parse.quote(key)}----------{pg}---.html"
        res = self.fetch(url, headers=self.getHeaders())
        video_list = []
        if res:
            html = res.text if hasattr(res, 'text') else ""
            for m in re.finditer(r'href="(/voddetail/(\d+)\.html)".*?title="([^"]+)"', html, re.S):
                ctx = html[max(0, m.start()-1200):m.end()]
                img = re.search(r'(?:data-realsrc|data-src|src)="([^"]+)"', ctx)
                pic = img.group(1) if img else ""
                if pic.startswith("//"): pic = "https:" + pic
                elif pic.startswith("/"): pic = self.site_url + pic
                video_list.append({"vod_id": m.group(2), "vod_name": m.group(3), "vod_pic": pic, "vod_remarks": ""})
        return {"list": video_list, "page": pg}

    def playerContent(self, flag, id, vipFlags):
        url = self.site_url + id if id.startswith("/") else id
        res = self.fetch(url, headers=self.getHeaders())
        if not res: return {}
        html = res.text if hasattr(res, 'text') else ""
        m = re.search(r'var\s+(?:player_aaaa|maccms_player)\s*=\s*(\{.*?\});', html) or re.search(r'mac_url\s*=\s*\'([^\']+)\'', html)
        if m:
            try:
                c = m.group(1)
                u = (json.loads(c) if c.startswith('{') else {"url": c}).get("url", "")
                if u: return {"parse": 0, "url": urllib.parse.unquote(u), "header": self.getHeaders()}
            except: pass
        return {"parse": 1, "url": url}

    def localProxy(self, ob):
        return [200, "video/MP2T", b""]