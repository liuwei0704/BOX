import sys
import re
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import quote

class Spider:
    def __init__(self):
        self.siteUrl = "https://baoziduanju.com"
        self.session = requests.Session()
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.siteUrl
        }

    def getName(self): return "包子短剧"
    def getDependence(self): return []
    def init(self, extend): pass

    def homeContent(self, filter):
        classes = [{"type_id": "系统觉醒", "type_name": "系统觉醒"},{"type_id": "穿越重生", "type_name": "穿越重生"},{"type_id": "都市逆袭", "type_name": "都市逆袭"},{"type_id": "古风权谋", "type_name": "古风权谋"},{"type_id": "总裁娇妻", "type_name": "总裁娇妻"}]
        return {"class": classes, "list": self.get_list(self.siteUrl + "/index.html")}

    def homeVideoContent(self):
        return {"list": self.get_list(self.siteUrl + "/index.html")}

    def categoryContent(self, tid, pg, filter, extend):
        e_tid = tid if tid.startswith("%") else quote(tid)
        url = f"{self.siteUrl}/category/{e_tid}.html" if str(pg) == "1" else f"{self.siteUrl}/category/{e_tid}/page/{pg}.html"
        return {"page": pg, "pagecount": 99, "list": self.get_list(url)}

    def detailContent(self, ids):
        id_val = str(ids[0])
        target = self.siteUrl + (id_val if id_val.startswith("/") else "/video/" + id_val + ".html")
        res = self.session.get(target, headers=self.header, timeout=10, verify=False)
        res.encoding = 'utf-8'
        html = res.text
        play_list = []
        v_match = re.search(r"vodPlayUrl\s*=\s*['\"](.*?)['\"]", html)
        if v_match:
            v_raw = v_match.group(1).replace('\/', '/')
            if '#' in v_raw: play_list = v_raw.split('#')
            elif '.m3u8' in v_raw: play_list.append("正片$" + v_raw)
        if not play_list:
            c_m = re.search(r'/(?:video|watch)/(\d+)', id_val)
            if c_m:
                cid = c_m.group(1)
                eps = re.findall(rf'/{cid}_(\d+)\.html', html)
                if eps:
                    for ep in sorted(list(set(map(int, eps)))):
                        play_list.append(f"第{ep}集${self.siteUrl}/watch/{cid}_{ep}.html")
        title = "短剧"
        t_m = re.search(r'<h1.*?>(.*?)</h1>', html)
        if t_m: title = t_m.group(1).split('-')[0].strip()
        vod = {
            "vod_id": id_val,
            "vod_name": self.clean_name(title),
            "vod_remarks": f"更新至{len(play_list)}集" if len(play_list) > 1 else "全一集",
            "vod_play_from": "包子专线",
            "vod_play_url": "#".join(play_list) if play_list else f"正片${target}"
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        api_url = f"{self.siteUrl}/api/videos/search?q={quote(key)}&page=1&limit=20"
        v_list = []
        try:
            r = self.session.get(api_url, headers=self.header, timeout=10, verify=False)
            data = r.json()
            videos = data.get("data", {}).get("videos", [])
            for v in videos:
                vid = str(v.get("vod_id", ""))
                v_list.append({
                    "vod_id": f"/video/{vid}.html" if vid else "",
                    "vod_name": self.clean_name(v.get("vod_name", "短剧")),
                    "vod_pic": v.get("vod_pic", ""),
                    "vod_remarks": v.get("vod_remarks", "")
                })
        except: pass
        if not v_list: v_list = self.get_list(f"{self.siteUrl}/search/{quote(key)}.html")
        return {"list": v_list}

    def playerContent(self, flag, id, vipFlags):
        if ".m3u8" in id: return {"parse": 0, "url": id, "header": self.header}
        res = self.session.get(id, headers=self.header, timeout=10, verify=False)
        m = re.search(r'url:[\'"](.*?\.m3u8.*?)[\'"]', res.text)
        u = m.group(1).replace("\/", "/") if m else id
        return {"parse": 0, "url": u, "header": self.header}

    def get_list(self, url):
        try:
            r = self.session.get(url, headers=self.header, timeout=10, verify=False)
            soup = BeautifulSoup(r.text, "html.parser")
            v_list = []
            for item in soup.select(".video-card, .video-grid a, .module-item"):
                a = item if item.name == 'a' else item.select_one('a')
                img = item.select_one("img")
                if not a or not img: continue
                href = a.get("href", "")
                if "/video/" not in href and "/watch/" not in href: continue
                rem = ""
                rem_node = item.select_one(".video-duration, .module-item-note, .remarks, .label")
                if rem_node: rem = rem_node.get_text().strip()
                v_list.append({
                    "vod_id": href,
                    "vod_name": self.clean_name(img.get("alt", "短剧")),
                    "vod_pic": img.get("src") if img.get("src", "").startswith("http") else self.siteUrl + img.get("src", ""),
                    "vod_remarks": rem
                })
            return v_list
        except: return []

    def clean_name(self, name):
        if not name: return ""
        return re.sub(r"\(.*?\)|（.*?）|【.*?】|\[.*?\]|全集|高清|正片", "", str(name)).strip()