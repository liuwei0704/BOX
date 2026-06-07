#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "冰雪世界"
    
    def init(self, extend=""):
        self.host = "https://bxsj3.top"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Chrome/120.0.0.0) Safari/537.36',
            'Referer': self.host,
        }
    
    def getDependence(self):
        return ["bs4"]
    
    def isVideoFormat(self, url):
        return False
    
    def manualVideoCheck(self):
        pass
    
    def localProxy(self, param):
        return None
    
    def destroy(self):
        pass
    
    def build_full_url(self, url):
        if not url:
            return ''
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        return self.host + '/' + url
    
    def extract_videos(self, soup):
        """从 BeautifulSoup 对象中提取视频列表"""
        videos = []
        items = soup.select('.movie-item')
        if not items:
            items = soup.select('.item')
        
        for item in items:
            link_tag = item.select_one('a[href*="vod-detail-id"]')
            if not link_tag:
                continue
            
            href = link_tag.get('href')
            title = link_tag.get('title', '') or link_tag.text.strip()
            if not title:
                h1_link = item.select_one('h1 a')
                if h1_link:
                    title = h1_link.get('title', '') or h1_link.text.strip()
            
            img_tag = item.select_one('img')
            pic = img_tag.get('data-original', '') if img_tag else ''
            
            if href and title:
                videos.append({
                    "vod_id": href,
                    "vod_name": title,
                    "vod_pic": self.build_full_url(pic) if pic else ''
                })
        return videos
    
    def homeContent(self, filter):
        result = {}
        classes = [
            {"type_id": "16", "type_name": "中文字幕"}, {"type_id": "17", "type_name": "日韩无码"},
            {"type_id": "18", "type_name": "国产精品"}, {"type_id": "19", "type_name": "日韩精品"},
            {"type_id": "20", "type_name": "欧美精品"}, {"type_id": "21", "type_name": "动漫精品"},
            {"type_id": "22", "type_name": "自拍偷拍"}, {"type_id": "23", "type_name": "伦理影片"},
            {"type_id": "24", "type_name": "人妻系列"}, {"type_id": "25", "type_name": "制服诱惑"},
            {"type_id": "26", "type_name": "强奸乱伦"}, {"type_id": "27", "type_name": "AV明星"},
            {"type_id": "28", "type_name": "SM重味"}, {"type_id": "29", "type_name": "巨乳系列"},
            {"type_id": "30", "type_name": "颜射系列"}, {"type_id": "31", "type_name": "口交视频"},
            {"type_id": "32", "type_name": "自慰系列"}, {"type_id": "33", "type_name": "教师学生"},
            {"type_id": "34", "type_name": "大秀视频"}, {"type_id": "35", "type_name": "明星换脸"},
            {"type_id": "36", "type_name": "AV解说"}, {"type_id": "37", "type_name": "黑料网曝"},
            {"type_id": "38", "type_name": "精品探花"}, {"type_id": "39", "type_name": "精品网红"},
            {"type_id": "40", "type_name": "反差母狗"}, {"type_id": "41", "type_name": "颜值正义"},
            {"type_id": "42", "type_name": "熟女少妇"}, {"type_id": "43", "type_name": "人兽乱交"},
            {"type_id": "44", "type_name": "国产传媒"}, {"type_id": "45", "type_name": "激情动漫"},
            {"type_id": "46", "type_name": "三级伦理"}, {"type_id": "47", "type_name": "清纯美女"},
            {"type_id": "48", "type_name": "网红头条"}
        ]
        result["class"] = classes
        result["filters"] = {}
        
        videos = []
        try:
            rsp = requests.get(self.host, headers=self.headers, timeout=15)
            rsp.encoding = 'utf-8'
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = self.extract_videos(soup)[:20]
        except Exception as e:
            print(f"homeContent error: {e}")
        result["list"] = videos
        return result
    
    def homeVideoContent(self):
        return self.homeContent(False)
    
    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        try:
            if int(pg) == 1:
                url = f"{self.host}/?m=vod-type-id-{tid}.html"
            else:
                url = f"{self.host}/?m=vod-type-id-{tid}-pg-{pg}.html"
            print(f"Fetching category: {url}")
            rsp = requests.get(url, headers=self.headers, timeout=15)
            rsp.encoding = 'utf-8'
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            videos = self.extract_videos(soup)
            
            total_match = re.search(r'共(\d+)条数据.*?当前:\d+/(\d+)页', rsp.text)
            total_pages = int(total_match.group(2)) if total_match else 1
            
            result = {"list": videos, "pagecount": total_pages, "page": int(pg), "limit": len(videos), "total": 0}
        except Exception as e:
            print(f"categoryContent error: {e}")
            result = {"list": [], "pagecount": 1, "page": int(pg), "limit": 0, "total": 0}
        return result
    
    def detailContent(self, ids):
        result = {}
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            url = self.build_full_url(vid)
            rsp = requests.get(url, headers=self.headers, timeout=15)
            rsp.encoding = 'utf-8'
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            # 提取片名
            title = "未知"
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.text
                title = re.sub(r'[-_]\s*(日本|韩国|高清|免费|电影|电视剧|动漫|短剧|在线观看).*$', '', title)
                title = title.strip()
            if not title or title == "未知":
                h1_tag = soup.select_one('h1, .title, strong')
                if h1_tag:
                    title = h1_tag.text.strip()
            
            # 提取封面
            pic = ''
            img_tag = soup.select_one('.film_info dt img, dt img, .card-image img')
            if img_tag:
                pic = img_tag.get('src', '')
            
            # ========== 提取所有播放线路 ==========
            play_froms = []   # 线路名称列表
            play_urls = []    # 线路播放地址列表
            
            # 查找所有播放链接（通常在线路选择区域）
            # 方法1: 从 .btn-detail 或 .card-content 区域查找
            play_containers = soup.select('.btn-detail, .card-content, .film_bar')
            for container in play_containers:
                links = container.select('a[href*="vod-play-id"]')
                for link in links:
                    href = link.get('href', '')
                    name = link.text.strip()
                    if href and 'vod-play-id' in href:
                        if name:
                            play_froms.append(name)
                        else:
                            play_froms.append(f"线路{len(play_froms)+1}")
                        # 每个线路只有一集（正片）
                        play_urls.append(f"正片${self.build_full_url(href)}")
            
            # 方法2: 如果没找到，直接查找页面中所有播放链接
            if not play_froms:
                all_play_links = soup.select('a[href*="vod-play-id"]')
                for link in all_play_links:
                    href = link.get('href', '')
                    name = link.text.strip()
                    if href and 'vod-play-id' in href:
                        if name:
                            play_froms.append(name)
                        else:
                            play_froms.append(f"线路{len(play_froms)+1}")
                        play_urls.append(f"正片${self.build_full_url(href)}")
            
            # 去重（保留顺序）
            seen = set()
            unique_froms = []
            unique_urls = []
            for f, u in zip(play_froms, play_urls):
                if u not in seen:
                    seen.add(u)
                    unique_froms.append(f)
                    unique_urls.append(u)
            
            vod = {
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": self.build_full_url(pic) if pic else '',
                "vod_play_from": '$$$'.join(unique_froms) if unique_froms else "默认源",
                "vod_play_url": '$$$'.join(unique_urls) if unique_urls else ""
            }
            result["list"] = [vod]
        except Exception as e:
            print(f"detailContent error: {e}")
            result["list"] = []
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {}
        try:
            play_url = id if id.startswith("http") else self.build_full_url(id)
            rsp = requests.get(play_url, headers=self.headers, timeout=15)
            rsp.encoding = 'utf-8'
            if rsp:
                # 提取 m3u8 直链
                m3u8_match = re.search(r'"url":"([^"]+\.m3u8)"', rsp.text)
                if m3u8_match:
                    video_url = m3u8_match.group(1).replace("\\/", "/")
                    result = {"parse": 0, "playUrl": "", "url": video_url, "header": ""}
                    return result
                
                # 从 mac_url 提取
                m3u8_match = re.search(r'mac_url=unescape\([\'"]([^\'"]+)[\'"]\)', rsp.text)
                if m3u8_match:
                    decoded = urllib.parse.unquote(m3u8_match.group(1))
                    parts = decoded.split('$', 1)
                    if len(parts) == 2 and parts[1].startswith('http'):
                        result = {"parse": 0, "playUrl": "", "url": parts[1], "header": ""}
                        return result
            
            result = {"parse": 1, "playUrl": "", "url": play_url, "header": ""}
        except Exception as e:
            print(f"playerContent error: {e}")
            result = {"parse": 1, "playUrl": "", "url": id if id else "", "header": ""}
        return result
    
    def searchContent(self, key, quick, pg=1):
        result = {"list": []}
        try:
            search_url = f"{self.host}/index.php?m=vod-search"
            rsp = requests.post(search_url, data={'wd': key}, headers=self.headers, timeout=15)
            rsp.encoding = 'utf-8'
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = self.extract_videos(soup)
            result = {"list": videos, "page": int(pg), "pagecount": 1, "limit": len(videos), "total": len(videos)}
        except Exception as e:
            print(f"searchContent error: {e}")
        return result