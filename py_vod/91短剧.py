import sys, requests, re, json
from bs4 import BeautifulSoup

class Spider():
    def __init__(self):
        self.host = "https://wiki.ifwtjhzu.com"
        self.session = requests.Session()
        self.headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://wiki.ifwtjhzu.com/'}

    def getName(self):
        return "91CG"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        classes = [{"type_name": "短劇", "type_id": "dydj"}]
        return {'class': classes}

    def homeVideoContent(self):
        return self.categoryContent('dydj', 1, False, {})

    def categoryContent(self, tid, pg, filter, extend):
        p = int(pg)
        if tid == 'search': return {"list": [], "page": p}
        
        url = self.host + "/category/" + tid + "/" if p == 1 else self.host + "/category/" + tid + "/" + str(p) + "/"
        
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            v_list = []
            for item in soup.select('article, .post-card-container'):
                a = item.find('a')
                if not a or not a.get('href'): continue
                if "/archives/" not in a['href']: continue
                
                name_tag = item.select_one('h2, h3, .post-card-title') or a
                name = name_tag.text.strip()
                
                # --- 核心改进：过滤掉名字为空的项目 ---
                if not name:
                    continue

                img = item.find('img')
                pic = ""
                if img: pic = img.get('data-src') or img.get('src') or ""
                if pic and not pic.startswith('http'): pic = self.host + pic
                if pic: pic = pic + "@Referer=" + self.host + "/"

                v_list.append({"vod_id": a['href'], "vod_name": name, "vod_pic": pic, "vod_remarks": ""})
            
            return {"list": v_list, "page": p, "pagecount": p + 1}
        except:
            return {"list": [], "page": p, "pagecount": p}

    def detailContent(self, ids):
        url = ids[0] if ids[0].startswith('http') else self.host + ids[0]
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            name = soup.find('h1').text.strip() if soup.find('h1') else "Video"
            p_list = []
            btns = soup.select('.entry-content a[href*="video"], .entry-content a[href*="play"]')
            for b in btns: p_list.append(b.text.strip() + "$" + b['href'])
            if not p_list: p_list.append("Play$" + url)
            return {"list": [{"vod_id": ids[0], "vod_name": name, "vod_pic": "", "vod_play_from": "Default", "vod_play_url": "#".join(p_list)}]}
        except: return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        return {"parse": 1, "url": id, "header": json.dumps(self.headers)}

    def searchContent(self, key, quick, pg=1):
        return self.categoryContent('search', pg, False, {})