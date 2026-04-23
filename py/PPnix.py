# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

class Spider():
    def __init__(self):
        self.host = "https://www.ppnix.com"
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        self.headers = {
            'User-Agent': self.ua,
            'Referer': self.host + '/',
            'Origin': self.host
        }

    def getName(self): return "PPnix(繁)穩播分集版"
    def getDependence(self): return []
    def init(self, extend=""): pass
    def homeContent(self, filter): return {'class': [{"type_name": "電影", "type_id": "movie"}, {"type_name": "電視劇", "type_id": "tv"}]}
    def homeVideoContent(self): return self.categoryContent("movie", 1, False, "")

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.host}/tw/{tid}/---{pg}-.html"
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
                full_pic = urljoin(self.host, pic) + f"@Referer={self.host}/#.webp"
                videos.append({"vod_id": a['href'], "vod_name": name, "vod_pic": full_pic})
            return {"list": videos, "page": int(pg), "pagecount": 99}
        except: return {"list": []}

    def detailContent(self, ids):
        url = urljoin(self.host, ids[0])
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            html = res.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # --- 核心修復：同時抓取網頁連結與 JS 分集 ---
            play_list = []
            
            # 方法 A: 抓取 JS 裡的 m3u8 數組 (針對《蜜語紀》這類新劇)
            m3u8_match = re.search(r"m3u8=\[(.*?)\]", html)
            if m3u8_match:
                eps = m3u8_match.group(1).replace("'", "").split(',')
                for ep in eps:
                    ep = ep.strip()
                    if ep:
                        # 這裡的 vod_id 必須指向原始播放網頁，才能保證能播
                        # 假設播放網頁格式為 /tw/tv/ID-EP.html 或類似，
                        # 但最穩的是直接用原本的 ID，讓 playerContent 去嗅探
                        play_list.append(f"第{ep}集${ids[0]}?ep={ep}")

            # 方法 B: 傳統標籤抓取 (作為備援)
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
        except:
            return {"list": [{"vod_id": ids[0], "vod_name": "解析失敗", "vod_play_from": "None", "vod_play_url": "正片$" + ids[0]}]}

    def playerContent(self, flag, id, vipFlags):
        # 恢復到最穩定的「網頁原始嗅探」邏輯
        # 移除所有手動構造的 M3U8 路徑，交給 App 內核
        target_url = urljoin(self.host, id.split('?')[0]) 
        return {
            "url": target_url,
            "header": self.headers,
            "parse": 1,
            "ua": self.ua,
            "referer": self.host + "/"
        }

    def searchContent(self, key, quick, pg=1):
        url = f"{self.host}/tw/search/-------------.html?wd={key}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = [{"vod_id": a['href'], "vod_name": a.get_text(strip=True)} for a in soup.select('.lists-content ul li h2 a')]
            return {"list": videos}
        except: return {"list": []}