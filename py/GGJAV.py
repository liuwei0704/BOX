# coding=utf-8
import sys
import re
import requests
import base64
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "GGJAV"

    def init(self, extend=""):
        self.host = "https://ggjav.tv"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }

    def homeContent(self, filter):
        if not hasattr(self, 'host'): self.init()
        result = {"class": [], "list": []}
        result["class"] = [
            {"type_id": "/main/censored", "type_name": "有码AV"},
            {"type_id": "/main/uncensored", "type_name": "无码高清"},
            {"type_id": "/main/ctg?ctgs=無碼流出", "type_name": "无码流出"},
            {"type_id": "/main/amateur", "type_name": "素人作品"},
            {"type_id": "/main/chinese", "type_name": "华语字幕"},
            {"type_id": "/main/europe", "type_name": "歐美高清"},
            {"type_id": "/main/cartoon", "type_name": "動漫高清"}
        ]
        try:
            res = requests.get(f"{self.host}/main/censored", headers=self.headers, timeout=10)
            result["list"] = self.parseList(res.text)
        except: pass
        return result

    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'host'): self.init()
        result = {"list": [], "page": int(pg), "pagecount": 99, "limit": 20, "total": 0}
        p_sign = "&" if "?" in tid else "?"
        url = f"{self.host}{tid}{p_sign}page={pg}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            result["list"] = self.parseList(res.text)
        except: pass
        return result

    def detailContent(self, ids):
        if not hasattr(self, 'host'): self.init()
        vod_id = ids[0]
        result = {"list": []}
        try:
            res = requests.get(vod_id, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            name = soup.find('meta', property="og:title")['content'].split('|')[0].strip() if soup.find('meta', property="og:title") else "视频"
            pic = soup.find('meta', property="og:image")['content'] if soup.find('meta', property="og:image") else ""
            vod = {
                "vod_id": vod_id, "vod_name": name, "vod_pic": pic,
                "vod_play_from": "GGJAV-Direct", "vod_play_url": f"播放${vod_id}", "vod_content": name
            }
            result["list"].append(vod)
        except: pass
        return result

    def searchContent(self, key, quick, pg=1):
        if not hasattr(self, 'host'): self.init()
        result = {"list": []}
        url = f"{self.host}/main/search/{key}?page={pg}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            result["list"] = self.parseList(res.text)
        except: pass
        return result

    def playerContent(self, flag, id, vipFlags):
        # --- 暴力穿透逻辑 ---
        try:
            res = requests.get(id, headers=self.headers, timeout=10)
            # 匹配 embed 链接中的 u= 参数
            embed_match = re.search(r'embed\?u=([a-zA-Z0-9+/=]+)', res.text)
            if embed_match:
                b64_str = embed_match.group(1)
                # Base64 解码得到原始 MP4 地址
                raw_url = base64.b64decode(b64_str).decode('utf-8')
                return {
                    "parse": 0, # 直接出流，不走解析
                    "url": raw_url,
                    "header": {
                        "User-Agent": self.headers['User-Agent'],
                        "Referer": "https://ggjav.com/", # 必须用 .com 的 Referer
                        "Connection": "keep-alive"
                    }
                }
        except Exception as e:
            pass
        
        # 兜底返回原地址走解析
        return {"parse": 1, "url": id, "header": {"Referer": id}}

    def parseList(self, html):
        lst = []
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('div.columns.large-3, div.columns.small-6')
        for item in items:
            a_tag = item.find('a', href=re.compile(r'/main/video\?id='))
            if not a_tag: continue
            href = a_tag['href']
            if not href.startswith('http'): href = self.host + href
            img = item.find('img')
            pic = img.get('data-src') or img.get('src', '') if img else ""
            raw_text = item.get_text(" ", strip=True)
            name = re.sub(r'\d+%\s*|流暢播放', '', raw_text).strip()
            name = re.sub(r'\s+\d{2,}$', '', name).strip()
            lst.append({"vod_id": href, "vod_name": name, "vod_pic": pic, "vod_remarks": ""})
        return lst

    def getDependence(self):
        return ["requests", "beautifulsoup4"]