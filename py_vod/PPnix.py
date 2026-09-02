# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

class Spider():
    def __init__(self):
        self.host = "https://www.ppnix.com"
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        self.headers = {'User-Agent': self.ua, 'Referer': self.host + '/', 'Origin': self.host}

    def getName(self): return "PPnix(繁)全功能角標版"
    def getDependence(self): return []
    def init(self, extend=""): pass

    def homeContent(self, filter):
        filters = {
            "movie": [
                {"key": "class", "name": "類型", "value": [{"n": "全部", "v": ""}, {"n": "劇情", "v": "劇情"}, {"n": "喜劇", "v": "喜劇"}, {"n": "動作", "v": "動作"}, {"n": "愛情", "v": "愛情"}, {"n": "科幻", "v": "科幻"}, {"n": "動畫", "v": "動畫"}, {"n": "懸疑", "v": "懸疑"}, {"n": "驚悚", "v": "驚悚"}, {"n": "恐怖", "v": "恐怖"}, {"n": "犯罪", "v": "犯罪"}]},
                {"key": "area", "name": "地區", "value": [{"n": "全部", "v": ""}, {"n": "中國大陸", "v": "中國大陸"}, {"n": "美國", "v": "美國"}, {"n": "香港", "v": "香港"}, {"n": "台灣", "v": "台灣"}, {"n": "日本", "v": "日本"}, {"n": "韓國", "v": "韓國"}]},
                {"key": "year", "name": "年份", "value": [{"n": "全部", "v": ""}, {"n": "2026", "v": "2026"}, {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"}, {"n": "2023", "v": "2023"}, {"n": "2022", "v": "2022"}]}
            ],
            "tv": [
                {"key": "class", "name": "類型", "value": [{"n": "全部", "v": ""}, {"n": "劇情", "v": "劇情"}, {"n": "喜劇", "v": "喜劇"}, {"n": "愛情", "v": "愛情"}, {"n": "古裝", "v": "古裝"}, {"n": "懸疑", "v": "懸疑"}, {"n": "犯罪", "v": "犯罪"}, {"n": "科幻", "v": "科幻"}]},
                {"key": "area", "name": "地區", "value": [{"n": "全部", "v": ""}, {"n": "中國大陸", "v": "中國大陸"}, {"n": "美國", "v": "美國"}, {"n": "香港", "v": "香港"}, {"n": "台灣", "v": "台灣"}, {"n": "日本", "v": "日本"}, {"n": "韓國", "v": "韓國"}]},
                {"key": "year", "name": "年份", "value": [{"n": "全部", "v": ""}, {"n": "2026", "v": "2026"}, {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"}, {"n": "2023", "v": "2023"}]}
            ]
        }
        return {
            'class': [{"type_name": "電影", "type_id": "movie"}, {"type_name": "電視劇", "type_id": "tv"}],
            'filters': filters
        }

    def homeVideoContent(self):
        return self.categoryContent("movie", 1, False, {})

    def categoryContent(self, tid, pg, filter, extend):
        cls = extend.get("class", "")
        area = extend.get("area", "")
        year = extend.get("year", "")
        url = f"{self.host}/tw/{tid}/{cls}-{area}-{year}-{pg}-.html"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = []
            for item in soup.select('.lists-content ul li'):
                a = item.select_one('h2 a') or item.select_one('a.thumbnail')
                if not a: continue
                img = item.select_one('img')
                name = a.get_text(strip=True)
                pic = img.get('data-original') or img.get('src') if img else ""
                
                # --- 提取角標資訊 (vod_remarks) ---
                # 優先抓取評分或更新集數
                remark = ""
                rate = item.select_one('.rate')
                if rate:
                    remark = rate.get_text(strip=True)
                else:
                    # 如果沒評分，找是否有顯示更新至第幾集
                    footer_span = item.select_one('footer span')
                    if footer_span: remark = footer_span.get_text(strip=True)
                
                full_pic = urljoin(self.host, pic) + f"@Referer={self.host}/#.webp"
                videos.append({
                    "vod_id": a['href'], 
                    "vod_name": name, 
                    "vod_pic": full_pic,
                    "vod_remarks": remark # 這裡就是顯示在右上角的角標
                })
            return {"list": videos, "page": int(pg), "pagecount": 99}
        except: return {"list": []}

    def detailContent(self, ids):
        url = urljoin(self.host, ids[0])
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            html = res.text
            soup = BeautifulSoup(html, 'html.parser')
            play_list = []
            m3u8_match = re.search(r"m3u8=\[(.*?)\]", html)
            if m3u8_match:
                eps = m3u8_match.group(1).replace("'", "").split(',')
                for ep in eps:
                    ep = ep.strip()
                    if ep: play_list.append(f"第{ep}集${ids[0]}?ep={ep}")
            if not play_list:
                links = soup.select('.playlist ul li a') or soup.select('a[href*="/play/"]')
                for a in links:
                    play_list.append(f"{a.get_text(strip=True)}${a['href']}")
            vod = {
                "vod_id": ids[0],
                "vod_name": soup.select_one('h1').get_text(strip=True) if soup.select_one('h1') else "影片詳情",
                "vod_play_from": "PPnix-穩播",
                "vod_play_url": "#".join(play_list) if play_list else f"正片${ids[0]}"
            }
            return {"list": [vod]}
        except: return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        target_url = urljoin(self.host, id.split('?')[0]) 
        return {
            "url": target_url, "header": self.headers,
            "parse": 1, "ua": self.ua, "referer": self.host + "/"
        }

    def searchContent(self, key, quick, pg=1):
        url = f"{self.host}/tw/search/-------------.html?wd={key}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = []
            for a in soup.select('.lists-content ul li h2 a'):
                videos.append({"vod_id": a['href'], "vod_name": a.get_text(strip=True)})
            return {"list": videos}
        except: return {"list": []}