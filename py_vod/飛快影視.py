# coding=utf-8
import sys
import os
import re
import json
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    
    def getName(self):
        return "飞快TV"
    
    def getDependence(self):
        return ["bs4"]
    
    def init(self, extend=""):
        self.site_url = "https://feikuai.in"
        self.limit = 24
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.site_url,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.categories = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "剧集"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
        ]
        self.filters = {}
    
    def header(self):
        return self.headers
    
    def isVideoFormat(self, url):
        if not url:
            return False
        video_exts = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.wmv', '.mov']
        return any(ext in url.lower() for ext in video_exts)
    
    def manualVideoCheck(self):
        pass
    
    def localProxy(self, param):
        return None
    
    def destroy(self):
        pass
    
    def build_full_url(self, url):
        if not url or not isinstance(url, str):
            return ''
        url = url.strip()
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if url in ['null', 'undefined', '']:
            return ''
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.site_url + url
        if url.startswith('./'):
            return self.site_url + url[1:]
        return self.site_url + '/' + url
    
    def extract_pic(self, element):
        pic = ''
        img = element.find('img') if hasattr(element, 'find') else None
        if img:
            pic = img.get('data-original', '') or img.get('data-src', '') or img.get('src', '')
        if not pic:
            pic = element.get('data-original', '') or element.get('data-src', '') or element.get('src', '')
        if not pic:
            style = element.get('style', '')
            match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
            if match:
                pic = match.group(1)
        return self.build_full_url(pic) if pic else ''
    
    def extract_remark(self, element):
        remark = ''
        remark_span = element.find('span', class_='pic-text') if hasattr(element, 'find') else None
        if remark_span:
            remark = remark_span.text.strip()
        if not remark:
            note = element.find('div', class_='module-item-note') or element.find('div', class_='module-poster-item-note')
            if note:
                remark = note.text.strip()
        return remark
    
    def parse_video_card(self, card):
        # 提取链接和ID
        link_elem = card.select_one('a') or card
        href = link_elem.get('href', '')
        match = re.search(r'/voddetail/(\d+)\.html', href)
        if not match:
            onclick = card.get('onclick', '')
            match = re.search(r'/voddetail/(\d+)\.html', onclick)
            if not match:
                return None
        vod_id = match.group(1)
        
        # 提取标题
        vod_name = ''
        # 1. 优先从 .module-card-item-title a strong 或 a 获取（搜索页面）
        title_elem = card.select_one('.module-card-item-title a strong')
        if title_elem:
            vod_name = title_elem.get_text(strip=True)
        if not vod_name:
            title_elem = card.select_one('.module-card-item-title a')
            if title_elem:
                vod_name = title_elem.get_text(strip=True)
        # 2. 从 title 属性获取
        if not vod_name:
            vod_name = link_elem.get('title', '')
        # 3. 从 .module-poster-item-title 获取（首页/分类页）
        if not vod_name:
            title_elem = card.select_one('.module-poster-item-title') or card.select_one('.module-item-title')
            if title_elem:
                vod_name = title_elem.get_text(strip=True)
        # 4. 最后从链接文本获取，但过滤状态词
        if not vod_name:
            raw_text = link_elem.get_text(strip=True)
            status_words = ['更新至', '全', '集', 'HD', 'TC', '国语', '中字', '正片', '预告', '抢先版']
            if not any(word in raw_text for word in status_words):
                vod_name = raw_text
        
        # 提取图片
        vod_pic = self.extract_pic(card)
        
        # 提取备注（集数/状态）
        vod_remarks = self.extract_remark(card)
        if not vod_remarks:
            remark_elem = card.select_one('.module-item-note') or card.select_one('.module-card-item-note')
            if remark_elem:
                vod_remarks = remark_elem.get_text(strip=True)
        
        return {"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic, "vod_remarks": vod_remarks}
    
    def homeContent(self, filter):
        result = {}
        result["class"] = self.categories
        result["filters"] = self.filters
        videos = []
        try:
            rsp = self.fetch(self.site_url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            cards = soup.select('.module-items .module-item') or soup.select('.module-items a.module-poster-item')
            for card in cards[:self.limit]:
                item = self.parse_video_card(card)
                if item:
                    videos.append(item)
            result["list"] = videos
        except Exception as e:
            print(f"homeContent error: {e}")
            result["list"] = []
        return result
    
    def homeVideoContent(self):
        return self.homeContent(False)
    
    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        try:
            page = int(pg) if pg else 1
            url = f"{self.site_url}/vodshow/{tid}--------{page}---.html"
            print(f"Fetching category: {url}")
            rsp = self.fetch(url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            cards = soup.select('.module-items .module-item') or soup.select('.module-items a.module-poster-item')
            for card in cards:
                item = self.parse_video_card(card)
                if item:
                    videos.append(item)
            result["list"] = videos
            pagecount = 1
            for a in soup.select('.page-link') or soup.select('.pagination a'):
                txt = a.get_text(strip=True)
                if txt.isdigit():
                    pagecount = max(pagecount, int(txt))
                href = a.get('href', '')
                match = re.search(r'--------(\d+)---', href)
                if match:
                    pagecount = max(pagecount, int(match.group(1)))
            result["pagecount"] = pagecount
            result["page"] = page
            result["limit"] = len(videos)
            result["total"] = pagecount * 30
        except Exception as e:
            print(f"categoryContent error: {e}")
            result = {"list": [], "pagecount": 1, "page": pg, "limit": 0, "total": 0}
        return result
    
    def detailContent(self, ids):
        result = {}
        try:
            if isinstance(ids, list):
                vod_id = ids[0]
            else:
                vod_id = ids
            url = self.build_full_url(f"/voddetail/{vod_id}.html")
            rsp = self.fetch(url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            vod = {
                "vod_id": vod_id,
                "vod_name": "",
                "vod_pic": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_area": "",
                "vod_year": "",
                "vod_remarks": "",
                "vod_play_from": "",
                "vod_play_url": ""
            }
            title_elem = soup.select_one('.module-info-heading h1') or soup.select_one('h1')
            if title_elem:
                vod["vod_name"] = title_elem.get_text(strip=True)
            vod["vod_pic"] = self.extract_pic(soup)
            desc_elem = soup.select_one('.module-info-introduction-content p')
            if desc_elem:
                vod["vod_content"] = desc_elem.get_text(strip=True)
            for item in soup.select('.module-info-item'):
                ts = item.select_one('.module-info-item-title')
                cd = item.select_one('.module-info-item-content')
                if not ts or not cd:
                    continue
                label = ts.get_text(strip=True)
                if '导演' in label:
                    vod["vod_director"] = cd.get_text(strip=True)
                if '主演' in label:
                    vod["vod_actor"] = cd.get_text(strip=True)
                if '地区' in label:
                    vod["vod_area"] = cd.get_text(strip=True)
                if '年份' in label:
                    vod["vod_year"] = cd.get_text(strip=True)
            play_from_list = []
            play_url_list = []
            tab_items = soup.select('.module-tab-item')
            play_containers = soup.select('.module-list.sort-list.tab-list')
            if tab_items and play_containers and len(tab_items) == len(play_containers):
                for idx, tab in enumerate(tab_items):
                    source_name = tab.get('data-dropdown-value', '') or tab.get_text(strip=True)
                    episodes = []
                    for a in play_containers[idx].select('a.module-play-list-link'):
                        href = a.get('href', '')
                        if href:
                            episodes.append(f"{a.get_text(strip=True)}${self.build_full_url(href)}")
                    if episodes:
                        play_from_list.append(source_name)
                        play_url_list.append('#'.join(episodes))
            else:
                all_items = soup.select('.module-play-list-content a.module-play-list-link')
                if all_items:
                    episodes = []
                    for a in all_items:
                        href = a.get('href', '')
                        if href:
                            episodes.append(f"{a.get_text(strip=True)}${self.build_full_url(href)}")
                    if episodes:
                        play_from_list.append('默认线路')
                        play_url_list.append('#'.join(episodes))
            vod["vod_play_from"] = '$$$'.join(play_from_list)
            vod["vod_play_url"] = '$$$'.join(play_url_list)
            result["list"] = [vod]
        except Exception as e:
            print(f"detailContent error: {e}")
            result["list"] = []
        return result
    
    def searchContent(self, key, quick, pg="1"):
        return self._do_search(key, pg)
    
    def search(self, key):
        return self._do_search(key, 1)
    
    def find(self, key):
        return self._do_search(key, 1)
    
    def query(self, key):
        return self._do_search(key, 1)
    
    def searchPage(self, key, pg):
        return self._do_search(key, pg)
    
    def _do_search(self, key, pg=1):
        result = {}
        try:
            page = int(pg) if pg else 1
            encoded_key = urllib.parse.quote(key)
            if page == 1:
                url = f"{self.site_url}/vodsearch/{encoded_key}-------------.html"
            else:
                url = f"{self.site_url}/vodsearch/{encoded_key}----------{page}---.html"
            print(f"Search URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 搜索页面使用 .module-card-item 选择器
            cards = soup.select('.module-card-item')
            for card in cards:
                # 提取ID
                link = card.select_one('a[href*="/voddetail/"]')
                if not link:
                    continue
                href = link.get('href', '')
                match = re.search(r'/voddetail/(\d+)\.html', href)
                if not match:
                    continue
                vod_id = match.group(1)
                
                # 提取标题 - 从 .module-card-item-title a strong 或 a
                title = ''
                title_elem = card.select_one('.module-card-item-title a strong')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                if not title:
                    title_elem = card.select_one('.module-card-item-title a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                if not title:
                    title = link.get('title', '')
                
                if not title:
                    continue
                
                # 提取图片
                pic = ''
                img = card.select_one('.module-item-pic img')
                if img:
                    pic = img.get('data-original', '') or img.get('data-src', '') or img.get('src', '')
                if pic and not pic.startswith('http'):
                    pic = self.site_url + pic
                
                # 提取备注（集数/状态）
                remark = ''
                note_elem = card.select_one('.module-item-note')
                if note_elem:
                    remark = note_elem.get_text(strip=True)
                
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
            
            result["list"] = videos
            result["pagecount"] = 1
            result["page"] = page
            result["limit"] = len(videos)
            result["total"] = len(videos)
            print(f"Search found {len(videos)} results")
        except Exception as e:
            print(f"searchContent error: {e}")
            result = {"list": [], "pagecount": 1, "page": pg, "limit": 0, "total": 0}
        return result
    
    def playerContent(self, flag, id, vipFlags):
        result = {}
        try:
            play_url = id if id.startswith('http') else self.build_full_url(id)
            print(f"播放請求 - URL: {play_url}, Flag: {flag}")
            
            player_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.site_url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }
            
            try:
                rsp = self.fetch(play_url, headers=player_headers)
                if rsp and rsp.text:
                    m3u8_pattern = r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)'
                    match = re.search(m3u8_pattern, rsp.text)
                    if match:
                        direct_url = match.group(1)
                        print(f"从页面提取到 m3u8: {direct_url[:80]}...")
                        result["parse"] = 0
                        result["playUrl"] = ""
                        result["url"] = direct_url
                        result["header"] = json.dumps(player_headers)
                        return result
            except Exception as e:
                print(f"提取 m3u8 失败: {e}")
            
            result["parse"] = 1
            result["playUrl"] = ""
            result["url"] = play_url
            result["header"] = json.dumps(player_headers)
            
        except Exception as e:
            print(f"playerContent error: {e}")
            result = {"parse": 1, "playUrl": "", "url": id if id else "", "header": json.dumps(self.header())}
        return result