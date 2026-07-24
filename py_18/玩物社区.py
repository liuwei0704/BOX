# coding=utf-8
# 玩物社区 - TVBox爬虫源（最终稳定版）
# 站点: https://9iio.zgdnbjh.com/
# 特性: 图片AES解密 + data:image显示 + 详情页片名提取 + 播放直链提取

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
        self.host = "https://9iio.zgdnbjh.com"
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
        
        soups = doc.find_all('ul', class_="video-items")
        if not soups:
            soups = doc.find_all('div', class_=re.compile(r'video|item|card'))
        
        for soup in soups:
            items = soup.find_all('li') if soup.name == 'ul' else soup.find_all('div', class_=re.compile(r'item|card|video'))
            for item in items:
                img = item.find('img')
                if not img:
                    continue
                
                pic_url = img.get('data-src') or img.get('src')
                if not pic_url:
                    continue
                
                pic = self.process_encrypted_image(pic_url)
                if not pic:
                    pic = "https://via.placeholder.com/400x225?text=Video"
                
                name = img.get('alt', '')
                if not name:
                    title_tag = item.find('a', class_=re.compile(r'title|name'))
                    if title_tag:
                        name = title_tag.text.strip()
                
                link = item.find('a', href=True)
                vod_id = link.get('href') if link else ""
                
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
        
        # 提取片名
        name = ""
        title_tag = doc.find('h1')
        if title_tag:
            name = title_tag.text.strip()
        if not name:
            og_title = doc.find('meta', property="og:title")
            if og_title:
                name = og_title.get('content', '').strip()
        if not name:
            name = "视频详情"
        
        # 提取封面
        pic = ""
        og_image = doc.find('meta', property="og:image")
        if og_image:
            pic = og_image.get('content', '')
        if not pic and 'thumbnailUrl' in html:
            match = re.search(r'"thumbnailUrl"\s*:\s*\["([^"]+)"\]', html)
            if match:
                pic = self.process_encrypted_image(match.group(1))
        if not pic:
            pic = "https://via.placeholder.com/400x225?text=Video"
        
        # 提取描述
        desc = ""
        og_desc = doc.find('meta', property="og:description")
        if og_desc:
            desc = og_desc.get('content', '')
        if not desc:
            meta_desc = doc.find('meta', attrs={"name": "description"})
            if meta_desc:
                desc = meta_desc.get('content', '')
        
        # 提取播放地址 - 从 embed 页面提取
        play_url = ""
        embed_url = ""
        script_match = re.search(r'"embedUrl":\s*"([^"]+)"', html)
        if script_match:
            embed_url = script_match.group(1)
        else:
            embed_meta = doc.find('meta', property="og:video")
            if embed_meta:
                embed_url = embed_meta.get('content', '')
        
        if embed_url:
            if embed_url.startswith('/'):
                embed_url = self.host + embed_url
            embed_html = self.fetch_html(embed_url)
            if embed_html:
                embed_doc = BeautifulSoup(embed_html, "lxml")
                embed_source = embed_doc.find('source')
                if embed_source:
                    play_url = embed_source.get('src', '')
                if not play_url:
                    video_tag = embed_doc.find('video')
                    if video_tag:
                        play_url = video_tag.get('src', '')
        
        return {"list": [{
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": pic,
            "vod_content": desc,
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