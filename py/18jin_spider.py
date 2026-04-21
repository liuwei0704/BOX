# coding=utf-8
import sys
import re
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "18禁乐园"

    def init(self, extend=""):
        self.host = "https://18jin1426.sbs"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }

    def homeContent(self, filter):
        if not hasattr(self, 'host'): self.init()
        result = {"class": [], "list": []}
        
        result["class"] = [
            {"type_id": "1", "type_name": "国产自拍"},
            {"type_id": "2", "type_name": "主播诱惑"},
            {"type_id": "3", "type_name": "探花约炮"},
            {"type_id": "4", "type_name": "偷拍偷窥"},
            {"type_id": "5", "type_name": "网曝吃瓜"},
            {"type_id": "6", "type_name": "抖阴短片"},
            {"type_id": "7", "type_name": "传媒剧情"},
            {"type_id": "8", "type_name": "日韩无码"},
            {"type_id": "9", "type_name": "中文字幕"},
            {"type_id": "10", "type_name": "换脸明星"},
        ]
        
        try:
            res = requests.get(self.host, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            result["list"] = self.parseList(res.text)
        except:
            result["list"] = []
        return result

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'host'): self.init()
        result = {"list": [], "page": int(pg), "pagecount": 99, "limit": 20, "total": 0}
        
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            result["list"] = self.parseList(res.text)
        except:
            pass
        return result

    def detailContent(self, ids):
        if not hasattr(self, 'host'): self.init()
        vod_id = ids[0]
        result = {"list": []}
        
        try:
            res = requests.get(vod_id, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            title_elem = soup.select_one('.panel-heading h3, h3.title, .video-title')
            vod_name = title_elem.text.strip() if title_elem else "未知标题"
            
            img = soup.select_one('.video-pic img, .thumb img, .panel-body img')
            vod_pic = img.get('src') or img.get('data-src') or ''
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = urljoin(self.host, vod_pic)
            
            desc_elem = soup.select_one('.panel-body p, .description, .video-description')
            vod_content = desc_elem.text.strip() if desc_elem else ""
            
            play_from = []
            play_url = []
            
            play_btns = soup.select('.play-btn, .btn-group a, .playlist a')
            if play_btns:
                for btn in play_btns:
                    href = btn.get('href', '')
                    if '/index.php/vod/play/' in href:
                        line_name = btn.text.strip() or "线路"
                        play_from.append(line_name)
                        play_url.append(href if href.startswith('http') else urljoin(self.host, href))
            
            if not play_from:
                id_match = re.search(r'/id/(\d+)', vod_id)
                if id_match:
                    vid = id_match.group(1)
                    play_from.append("默认线路")
                    play_url.append(f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html")
            
            vod = {
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_play_from": "$$$".join(play_from) if play_from else "18禁乐园",
                "vod_play_url": "$$$".join(play_url) if play_url else vod_id,
                "vod_actor": "",
                "vod_director": "",
                "vod_remarks": ""
            }
            result["list"].append(vod)
        except:
            pass
        return result

    def searchContent(self, key, quick, pg=1):
        if not hasattr(self, 'host'): self.init()
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}
        
        url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{quote(key)}.html"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            result["list"] = self.parseList(res.text)
        except:
            pass
        return result

    def playerContent(self, flag, id, vipFlags):
        try:
            play_url = id if id.startswith('http') else urljoin(self.host, id)
            
            # 设置正确的 Referer
            headers = self.headers.copy()
            headers['Referer'] = play_url
            
            res = requests.get(play_url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            html = res.text
            
            # 方法1: 直接搜索转义后的m3u8地址（最关键！）
            match = re.search(r'https?:\/\/[^"\'\s]+\.m3u8[^"\'\s]*', html)
            if match:
                video_url = match.group(0).replace('\/', '/')
                return {"parse": 0, "url": video_url, "header": self.headers}
            
            # 方法2: 搜索mp4地址
            match = re.search(r'https?:\/\/[^"\'\s]+\.mp4[^"\'\s]*', html)
            if match:
                video_url = match.group(0).replace('\/', '/')
                return {"parse": 0, "url": video_url, "header": self.headers}
            
            # 方法3: 查找 player_aaaa 变量
            match = re.search(r'player_aaaa\s*=\s*["\']([^"\']+)["\']', html)
            if match:
                player_config = match.group(1)
                if player_config.startswith('http'):
                    return {"parse": 0, "url": player_config, "header": self.headers}
            
            # 方法4: 查找标准m3u8地址
            match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', html)
            if match:
                return {"parse": 0, "url": match.group(1), "header": self.headers}
            
            # 方法5: 查找iframe
            iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', html)
            if iframe_match:
                iframe_url = iframe_match.group(1)
                if iframe_url.startswith('/'):
                    iframe_url = urljoin(self.host, iframe_url)
                return {"parse": 1, "url": iframe_url}
            
        except Exception as e:
            pass
        
        return {"parse": 0, "url": ""}

    def parseList(self, html):
        video_list = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            items = soup.select('div.video')
            if not items:
                items = soup.select('.video-item, .thumb, .item, .col-video')
            
            for item in items:
                try:
                    a = item.find('a', href=True)
                    if not a:
                        continue
                    
                    href = a['href']
                    if not ('/vod/detail/' in href or '/vod/' in href or '/video/' in href):
                        continue
                    
                    title = a.get('title', '')
                    if not title:
                        title_elem = item.select_one('.video-title, .title, h5, h6, p, span')
                        title = title_elem.text.strip() if title_elem else ''
                    if not title:
                        title = a.text.strip()
                    
                    title = re.sub(r'\s+', ' ', title).strip()
                    
                    img = item.find('img')
                    pic = ''
                    if img:
                        pic = img.get('data-src') or img.get('src') or ''
                        if pic and not pic.startswith('http'):
                            pic = urljoin(self.host, pic)
                    
                    remarks = ''
                    remarks_elem = item.select_one('.video-overlay, .views, .duration, .meta, .badge')
                    if remarks_elem:
                        remarks = remarks_elem.text.strip()
                    
                    full_url = href if href.startswith('http') else urljoin(self.host, href)
                    
                    if title and full_url:
                        video_list.append({
                            "vod_id": full_url,
                            "vod_name": title,
                            "vod_pic": pic,
                            "vod_remarks": remarks
                        })
                except:
                    continue
            
            seen = set()
            unique_list = []
            for v in video_list:
                if v['vod_id'] not in seen:
                    unique_list.append(v)
                    seen.add(v['vod_id'])
            
            return unique_list
        except:
            return []