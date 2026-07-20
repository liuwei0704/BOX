import sys, requests, re, json, urllib.parse
from bs4 import BeautifulSoup

class Spider():
    def __init__(self):
        self.host = "https://ainivod.com"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': self.host,
        }

    def getName(self): return "爱你影视"
    def getDependence(self): return []

    def init(self, extend=""):
        try: self.session.get(self.host, headers=self.headers, timeout=5)
        except: pass

    def _fix(self, u):
        if not u: return ""
        if u.startswith("http"): return u
        if u.startswith("//"): return "https:" + u
        return self.host + u

    def parseList(self, html):
        video_list = []
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('.hl-list-item')
        for item in items:
            try:
                a = item.select_one('a.hl-item-thumb') or item.select_one('a')
                if not a: continue
                href = a.get('href', '')
                m = re.search(r'/voddetail/(\d+)\.html', href)
                if not m: continue
                vod_id = m.group(1)
                title_elem = item.select_one('.hl-item-title a') or item.select_one('.hl-item-title')
                vod_name = title_elem.get_text(strip=True) if title_elem else ''
                img = a.select_one('img') or a
                vod_pic = self._fix(img.get('data-original', '') or img.get('data-src', '') or img.get('src', '')) if img else ''
                tag = item.select_one('.remarks') or item.select_one('.hl-pic-text .remarks')
                vod_remarks = tag.get_text(strip=True) if tag else ''
                if vod_id and vod_name:
                    video_list.append({"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic, "vod_remarks": vod_remarks})
            except: continue
        res_list, seen = [], set()
        for v in video_list:
            if v['vod_id'] not in seen:
                res_list.append(v)
                seen.add(v['vod_id'])
        return res_list

    def homeContent(self, filter):
        result = {'class': [
            {"type_name": "电影", "type_id": "1"},
            {"type_name": "连续剧", "type_id": "2"},
            {"type_name": "动漫", "type_id": "4"},
            {"type_name": "短剧", "type_id": "20"},
            {"type_name": "综艺", "type_id": "3"},
            {"type_name": "记录片", "type_id": "43"},
        ]}
        try:
            res = self.session.get(self.host + "/", headers=self.headers)
            res.encoding = 'utf-8'
            result['list'] = self.parseList(res.text)
        except: result['list'] = []
        return result

    def homeVideoContent(self): return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        if page == 1: url = f"{self.host}/vodtype/{tid}.html"
        else: url = f"{self.host}/vodtype/{tid}-{page}.html"
        try:
            res = self.session.get(url, headers=self.headers)
            res.encoding = 'utf-8'
            v_list = self.parseList(res.text)
            pagecount = 99
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.select('.page-link') or soup.select('.pagination a'):
                t = a.get_text(strip=True)
                if t.isdigit(): pagecount = max(pagecount, int(t))
            return {"list": v_list, "page": page, "pagecount": pagecount, "limit": 24, "total": 999}
        except: return {"list": [], "page": page, "pagecount": 1}

    def detailContent(self, ids):
        if not ids: return {"list": []}
        vid = ids[0] if isinstance(ids, list) else ids
        url = f"{self.host}/voddetail/{vid}.html"
        try:
            res = self.session.get(url, headers=self.headers)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            name_el = soup.select_one('.hl-dc-title')
            vod_name = name_el.get_text(strip=True) if name_el else ''
            img = soup.select_one('.hl-dc-pic .hl-item-thumb') or soup.select_one('.hl-item-thumb')
            vod_pic = self._fix(img.get('data-original', '') or img.get('src', '')) if img else ''
            from_list, url_list = [], []
            tabs = soup.select('.hl-plays-from .hl-tabs-btn')
            boxes = soup.select('.hl-tabs-box')
            for i, box in enumerate(boxes):
                links = [f"{a.get_text(strip=True)}${a.get('href', '')}" for a in box.select('a') if a.get('href', '') and '/vodplay/' in a.get('href', '') and 'javascript:' not in a.get('href', '')]
                if links:
                    name = tabs[i].get_text(strip=True) if i < len(tabs) else f"线路{i+1}"
                    from_list.append(name)
                    url_list.append("#".join(links))
            return {"list": [{"vod_id": str(vid), "vod_name": vod_name, "vod_pic": vod_pic, "vod_play_from": "$$$".join(from_list), "vod_play_url": "$$$".join(url_list)}]}
        except: return {"list": []}

    def searchContent(self, key, quick, pg=1):
        page = int(pg) if pg else 1
        if page == 1: url = f"{self.host}/vodsearch/{urllib.parse.quote(key)}-------------.html"
        else: url = f"{self.host}/vodsearch/{urllib.parse.quote(key)}----------{page}---.html"
        try:
            res = self.session.get(url, headers=self.headers)
            res.encoding = 'utf-8'
            return {"list": self.parseList(res.text), "page": page}
        except: return {"list": [], "page": page}

    def playerContent(self, flag, id, vipFlags):
        url = id if id.startswith('http') else self.host + id
        try:
            self.headers['Referer'] = url
            res = self.session.get(url, headers=self.headers)
            html = res.text
            m3u8 = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
            if m3u8:
                return {"parse": 0, "url": m3u8.group(1).replace('\\/', '/'), "header": self.headers}
            match = re.search(r'player_aaaa\s*=\s*(\{.*?\})', html)
            if match:
                v_url = json.loads(match.group(1)).get('url', '')
                return {"parse": 0 if '.m3u8' in v_url.lower() or '.mp4' in v_url.lower() else 1, "url": v_url, "header": self.headers}
        except: pass
        return {"parse": 1, "url": url, "header": self.headers}