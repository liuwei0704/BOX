# coding=utf-8
import sys
import re
import requests
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "HomeJav"

    def init(self, extend=""):
        self.host = "https://www.homejav.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }

    def homeContent(self, filter):
        if not hasattr(self, 'host'): self.init()
        result = {"class": [], "list": []}
        result["class"] = [
            {"type_id": "/cn/videos/japanese", "type_name": "首页推荐"},
            {"type_id": "/cn/videos/japanese?o=bw", "type_name": "正在观看"},
            {"type_id": "/cn/videos/uncensored-leak", "type_name": "无码流出"},
            {"type_id": "/cn/videos/uncensored", "type_name": "无码高清"}
        ]
        try:
            res = requests.get(f"{self.host}/cn/videos/japanese", headers=self.headers, timeout=10)
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
            name = soup.find('h1').get_text(strip=True) if soup.find('h1') else "未知视频"
            pic = ""
            meta_pic = soup.find('meta', property="og:image")
            if meta_pic: pic = meta_pic['content']
            vod = {
                "vod_id": vod_id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_play_from": "HomeJav",
                "vod_play_url": f"播放${vod_id}",
                "vod_content": name
            }
            result["list"].append(vod)
        except: pass
        return result

    def searchContent(self, key, quick, pg=1):
        if not hasattr(self, 'host'): self.init()
        result = {"list": []}
        # 修正为 RESTful 路径格式
        url = f"{self.host}/cn/search/{key}?page={pg}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            result["list"] = self.parseList(res.text)
        except: pass
        return result

    def playerContent(self, flag, id, vipFlags):
        # 确保播放逻辑独立且缩进正确
        return {"parse": 1, "playUrl": "", "url": id}

    def parseList(self, html):
        lst = []
        soup = BeautifulSoup(html, 'html.parser')
        for a_tag in soup.find_all('a', href=re.compile(r'/cn/video/[0-9a-z]+')):
            img = a_tag.find('img')
            if not img: continue
            
            href = a_tag['href']
            if not href.startswith('http'): href = self.host + href
            if any(x['vod_id'] == href for x in lst): continue

            pic = img.get('data-src') or img.get('srcset') or img.get('src', '')
            if 'base64' in pic: pic = img.get('data-src', '')

            remarks = ""
            parent = a_tag.find_parent()
            full_text = parent.get_text(" ", strip=True) if parent else a_tag.get_text(" ", strip=True)
            duration = re.search(r'\d+:\d+(:\d+)?', full_text)
            if duration: remarks = duration.group()
            
            name = a_tag.get('title', '').strip() or img.get('alt', '').strip()
            if not name:
                name = full_text.replace(remarks, "").strip()
            if len(name) < 5 and parent:
                title_node = parent.find(['h3', 'p', 'div'], class_=re.compile(r'title|text'))
                if title_node: name = title_node.get_text(strip=True)

            lst.append({
                "vod_id": href,
                "vod_name": name if name else "视频",
                "vod_pic": pic,
                "vod_remarks": remarks
            })
        return lst

    def getDependence(self):
        return ["requests", "beautifulsoup4"]