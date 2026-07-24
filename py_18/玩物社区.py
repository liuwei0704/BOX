# -*- coding: utf-8 -*-
# 玩物社区 - 照搬朋友代码的图片解密方式

import re
import base64
import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def getName(self):
        return "玩物社区"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.host = "https://thu.hejpugurn.cc"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "/videos/zhibo-huifang/", "type_name": "直播回放"},
            {"type_id": "/videos/guochan-sm/", "type_name": "国产sm"},
            {"type_id": "/videos/rihan-sm/", "type_name": "日韩sm"},
            {"type_id": "/videos/oumei-sm/", "type_name": "欧美sm"},
            {"type_id": "/videos/dongman-sm/", "type_name": "动漫sm"},
            {"type_id": "/videos/tiaojiao-av/", "type_name": "调教av"},
            {"type_id": "/ai/all/", "type_name": "AI短剧-全部"},
            {"type_id": "/ai/ai-duanju/", "type_name": "AI成人短剧"},
            {"type_id": "/ai/ai-meinv/", "type_name": "AI美女"},
            {"type_id": "/ai/ai-huanlian/", "type_name": "AI换脸"},
            {"type_id": "/ai/ai-manju/", "type_name": "AI漫剧"},
        ]
        self.filters = {}

    def decrypt_image(self, encrypted_bytes):
        try:
            key = b"f5d965df75336270"
            iv = b"97b60394abc2fbe1"
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
            return decrypted
        except:
            return None

    def process_encrypted_image(self, pic_url):
        if not pic_url:
            return ""
        try:
            resp = requests.get(pic_url, headers=self.headers, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 0:
                decrypted = self.decrypt_image(resp.content)
                if decrypted:
                    b64 = base64.b64encode(decrypted).decode()
                    return f"data:image/jpeg;base64,{b64}"
        except:
            pass
        return ""

    def fetch_html(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            return resp.text if resp.status_code == 200 else ""
        except:
            return ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            data = self.categoryContent("/videos/guochan-sm/", 1, None, None)
            return {"list": data.get("list", [])[:10]}
        except:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if pg else 1
        url = f"{self.host}{tid}" if tid.endswith("/") else f"{self.host}{tid}/"
        if pg > 1:
            url = f"{url}page/{pg}/"
        
        html = self.fetch_html(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1, "total": 0}
        
        doc = BeautifulSoup(html, "lxml")
        videos = []
        
        # 查找视频列表 - 按朋友代码的方式
        soups = doc.find_all('ul', class_="video-items")
        if not soups:
            soups = doc.find_all('div', class_=re.compile(r'video|item|card'))
        
        for soup in soups:
            items = soup.find_all('li') if soup.name == 'ul' else soup.find_all('div', class_=re.compile(r'item|card|video'))
            for item in items:
                # 提取图片
                img = item.find('img')
                if not img:
                    continue
                
                pic_url = img.get('data-src') or img.get('src')
                if not pic_url:
                    continue
                
                # 解密图片
                pic = self.process_encrypted_image(pic_url)
                if not pic:
                    pic = "https://via.placeholder.com/400x225?text=Video"
                
                # 提取标题
                name = img.get('alt', '')
                if not name:
                    title_tag = item.find('a', class_=re.compile(r'title|name'))
                    if title_tag:
                        name = title_tag.text.strip()
                
                # 提取链接
                link = item.find('a', href=True)
                vod_id = link.get('href') if link else ""
                
                # 提取备注
                remark = ""
                remark_tag = item.find('div', class_=re.compile(r'truncate|remark|time|duration'))
                if remark_tag:
                    remark = remark_tag.text.strip()
                
                if vod_id and name:
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": name,
                        "vod_pic": pic,
                        "vod_remarks": remark
                    })
        
        return {
            "list": videos,
            "page": pg,
            "pagecount": 9999,
            "limit": 90,
            "total": 999999
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        
        vid = ids[0]
        if not vid.startswith("http"):
            vid = self.host + vid
        
        html = self.fetch_html(vid)
        if not html:
            return {"list": []}
        
        doc = BeautifulSoup(html, "lxml")
        
        # 提取播放地址
        play_url = ""
        source = doc.find('source')
        if source:
            play_url = source.get('src', '')
        
        if not play_url:
            # 尝试从 script 中提取
            scripts = doc.find_all('script')
            for script in scripts:
                if script.string and 'embedUrl' in script.string:
                    match = re.search(r'"embedUrl":\s*"([^"]+)"', script.string)
                    if match:
                        embed_url = match.group(1)
                        embed_html = self.fetch_html(embed_url)
                        if embed_html:
                            embed_doc = BeautifulSoup(embed_html, "lxml")
                            embed_source = embed_doc.find('source')
                            if embed_source:
                                play_url = embed_source.get('src', '')
                                break
        
        return {"list": [{
            "vod_id": vid,
            "vod_name": "视频详情",
            "vod_pic": "",
            "vod_content": "",
            "vod_play_from": "玩物",
            "vod_play_url": f"播放${play_url}" if play_url else ""
        }]}

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": ""}
        if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
            return {"parse": 0, "url": id, "header": self.headers}
        return {"parse": 1, "url": id}

    def searchContent(self, key, quick, pg):
        if not key:
            return {"list": [], "page": 1, "pagecount": 1, "total": 0}
        
        pg = int(pg) if pg else 1
        url = f"{self.host}/videos/search/{key}/"
        if pg > 1:
            url = f"{url}page/{pg}/"
        
        html = self.fetch_html(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1, "total": 0}
        
        doc = BeautifulSoup(html, "lxml")
        videos = []
        
        soups = doc.find_all('ul', class_="video-items")
        for soup in soups:
            items = soup.find_all('li')
            for item in items:
                img = item.find('img')
                if not img:
                    continue
                
                pic_url = img.get('data-src') or img.get('src')
                pic = self.process_encrypted_image(pic_url) if pic_url else ""
                
                name = img.get('alt', '')
                link = item.find('a', href=True)
                vod_id = link.get('href') if link else ""
                
                if vod_id and name:
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": name,
                        "vod_pic": pic,
                        "vod_remarks": ""
                    })
        
        return {"list": videos, "page": pg, "pagecount": 9999, "limit": 90, "total": 999999}

    def destroy(self):
        pass