# coding=utf-8
import sys
import os
import re
import json
import base64
import urllib.parse
from bs4 import BeautifulSoup

class Spider:
    """JAVEWE 爬虫 - 影视/综艺/动漫等"""
    
    def getName(self):
        return "JAVEWE"
    
    def getDependence(self):
        return ["bs4", "requests"]
    
    def init(self, extend=""):
        self.host = "https://javewe.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': self.host + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        # 分类列表
        self.categories = [
            {"type_id": "popular-today", "type_name": "今日热门"},
            {"type_id": "popular-week", "type_name": "本周热门"},
            {"type_id": "popular-month", "type_name": "本月热门"},
            {"type_id": "genre/jav-sub", "type_name": "JAV Sub"},
            {"type_id": "genre/uncensored-jav", "type_name": "无码"},
            {"type_id": "genre/amateur", "type_name": "素人"},
            {"type_id": "channel/fc2ppv", "type_name": "Fc2ppv"}
        ]
    
    def fetch(self, url):
        """发送HTTP请求"""
        try:
            import requests
            r = requests.get(url, headers=self.headers, timeout=15)
            r.encoding = 'utf-8'
            return r.text
        except Exception as e:
            print(f"请求失败: {url}, 错误: {e}")
            return None
    
    def build_full_url(self, url):
        if not url or not isinstance(url, str):
            return ''
        url = url.strip()
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        return self.host + '/' + url
    
    def parse_video_list(self, html):
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        videos = []
        items = soup.select('.article_standard_view .item')
        for item in items:
            try:
                title_elem = item.select_one('.item_content h3 a')
                if not title_elem:
                    continue
                href = title_elem.get('href', '')
                vod_id = href.strip('/') if href else ''
                vod_name = title_elem.get_text().strip()
                
                img_elem = item.select_one('.item_header a img')
                vod_pic = img_elem.get('src') if img_elem else ''
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = self.build_full_url(vod_pic)
                
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_remarks': ''
                })
            except:
                continue
        return videos
    
    def homeContent(self, filter):
        result = {"class": self.categories, "list": [], "filters": {}}
        try:
            html = self.fetch(self.host)
            if html:
                videos = self.parse_video_list(html)
                result["list"] = videos[:24]
        except Exception as e:
            print(f"homeContent error: {e}")
        return result
    
    def homeVideoContent(self):
        return self.homeContent(False)
    
    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        if page == 1:
            url = f"{self.host}/{tid}"
        else:
            url = f"{self.host}/{tid}/{page}"
        
        html = self.fetch(url)
        videos = self.parse_video_list(html) if html else []
        return {
            "list": videos,
            "page": page,
            "pagecount": 50,
            "limit": len(videos),
            "total": 1000
        }
    
    def detailContent(self, ids):
        result = {"list": []}
        try:
            if isinstance(ids, list):
                vid = ids[0]
            else:
                vid = ids
            
            url = f"{self.host}/{vid}"
            html = self.fetch(url)
            if not html:
                return result
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取标题
            vod_name = ""
            title_elem = soup.select_one('.post_header h4')
            if title_elem:
                vod_name = title_elem.get_text().strip()
            
            # 提取图片
            vod_pic = ""
            img_elem = soup.select_one('.images a img')
            if img_elem and img_elem.get('src'):
                vod_pic = self.build_full_url(img_elem.get('src'))
            
            # 提取演员等信息
            vod_actor = ""
            meta = soup.select_one('.product_meta')
            if meta:
                starring_links = meta.select('span:has(.fa-user) a')
                if starring_links:
                    vod_actor = ', '.join([a.get_text().strip() for a in starring_links])
            
            # 提取播放链接 - 关键修改：直接返回中间页URL，让playerContent处理
            play_url = ""
            links_input = soup.find('input', id='links')
            if links_input and links_input.get('value'):
                encoded = links_input.get('value')
                try:
                    decoded = base64.b64decode(encoded).decode('utf-8')
                    play_list = [url.strip() for url in decoded.split(',,,') if url and url.strip()]
                    if play_list:
                        # 使用第一个播放链接
                        first_url = play_list[0]
                        if not first_url.startswith('http'):
                            first_url = 'https://' + first_url
                        play_url = first_url
                except Exception as e:
                    print(f"解码播放地址失败: {e}")
            
            if not play_url:
                iframe = soup.find('iframe', id='iframe-link')
                if iframe and iframe.get('src'):
                    play_url = iframe.get('src')
                    if not play_url.startswith('http'):
                        play_url = 'https://' + play_url
            
            result["list"] = [{
                "vod_id": vid,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_actor": vod_actor,
                "vod_play_from": "默认线路",
                "vod_play_url": play_url if play_url else url
            }]
        except Exception as e:
            print(f"detailContent error: {e}")
        return result
    
    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        import urllib.parse
        if page == 1:
            url = f"{self.host}/search?s={urllib.parse.quote(key)}"
        else:
            url = f"{self.host}/search?page={page}&s={urllib.parse.quote(key)}"
        
        html = self.fetch(url)
        videos = self.parse_video_list(html) if html else []
        return {
            "list": videos,
            "page": page,
            "pagecount": 1,
            "limit": len(videos),
            "total": len(videos)
        }
    
    def playerContent(self, flag, id, vipFlags):
        """
        播放器接口 - 与 mjv012.py 相同的成功模式
        返回 parse=1 让客户端加载中间页，由客户端 WebView 处理 JS 加密
        """
        if id and id.startswith('http'):
            # 返回 parse=1，让客户端直接加载URL
            # 客户端会处理页面中的 JS 加密和播放器加载
            return {"parse": 1, "playUrl": "", "url": id, "header": self.headers}
        return {"parse": 1, "playUrl": "", "url": "", "header": self.headers}
    
    def destroy(self):
        pass