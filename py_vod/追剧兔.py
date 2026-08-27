#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import urllib.parse
from bs4 import BeautifulSoup

class Spider:
    def getName(self):
        return "追剧兔"

    def getDependence(self):
        return ["bs4"]

    def init(self, extend=""):
        self.site_url = "https://zhuijutu.com"
        self.limit = 24
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.site_url
        }
        self.categories = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "综艺"}
        ]
        self.filters = {}

    def _ensure_init(self):
        if not hasattr(self, 'site_url'):
            self.init()

    def _parse_video_card(self, card):
        self._ensure_init()
        href = card.get('href', '')
        match = re.search(r'/voddetail/(\d+)\.html', href)
        if not match:
            return None
        vod_id = match.group(1)
        
        vod_name = card.get('title', '') or card.get_text(strip=True)
        
        vod_pic = card.get('data-original', '')
        if not vod_pic:
            style = card.get('style', '')
            if style:
                bg_match = re.search(r'background-image:\s*url\([\'"]?([^\'"]+)[\'"]?\)', style)
                if bg_match:
                    vod_pic = bg_match.group(1)
        if vod_pic and not vod_pic.startswith('http'):
            if vod_pic.startswith('//'):
                vod_pic = 'https:' + vod_pic
            elif vod_pic.startswith('/'):
                vod_pic = self.site_url + vod_pic
        
        vod_remarks = ''
        remarks_elem = card.select_one('.hl-pic-text .remarks')
        if remarks_elem:
            vod_remarks = remarks_elem.get_text(strip=True)
        if not vod_remarks:
            state_elem = card.select_one('.state')
            if state_elem:
                vod_remarks = state_elem.get_text(strip=True)
        if not vod_remarks:
            pic_text = card.select_one('.hl-pic-text')
            if pic_text:
                vod_remarks = pic_text.get_text(strip=True)
        
        return {"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic, "vod_remarks": vod_remarks}

    def fetch(self, url, headers):
        try:
            import requests
            r = requests.get(url, headers=headers, timeout=15)
            r.encoding = r.apparent_encoding or 'utf-8'
            return r
        except:
            return None

    def homeContent(self, filter):
        self._ensure_init()
        url = f"{self.site_url}/"
        resp = self.fetch(url, headers=self.headers)
        video_list = []
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.select('a.hl-item-thumb')
            for card in cards[:self.limit]:
                item = self._parse_video_card(card)
                if item:
                    video_list.append(item)
        return {"class": self.categories, "list": video_list, "filters": self.filters}

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        self._ensure_init()
        page = int(pg) if pg else 1
        url = f"{self.site_url}/vodshow/{tid}--------{page}---.html"
        resp = self.fetch(url, headers=self.headers)
        if not resp:
            return {"list": [], "page": page, "pagecount": 1, "limit": self.limit, "total": 0}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        video_list = []
        cards = soup.select('a.hl-item-thumb')
        for card in cards:
            item = self._parse_video_card(card)
            if item:
                video_list.append(item)
        
        # 提取最大页码
        pagecount = page
        for a in soup.select('a'):
            href = a.get('href', '')
            match = re.search(r'/vodshow/\d+--------(\d+)---\.html', href)
            if match:
                p = int(match.group(1))
                if p > pagecount:
                    pagecount = p
        
        return {"list": video_list, "page": page, "pagecount": pagecount, "limit": self.limit, "total": 0}

    def detailContent(self, ids):
        self._ensure_init()
        if not ids:
            return {"list": []}
        vod_id = ids[0]
        url = f"{self.site_url}/voddetail/{vod_id}.html"
        resp = self.fetch(url, headers=self.headers)
        if not resp:
            return {"list": []}
        soup = BeautifulSoup(resp.text, 'html.parser')
        vod_name = ''
        title_elem = soup.select_one('.module-info-heading h1') or soup.select_one('.hl-detail-title h1')
        if title_elem:
            vod_name = title_elem.get_text(strip=True)
        img_elem = soup.select_one('.module-info-poster img') or soup.select_one('.hl-detail-pic img')
        vod_pic = ''
        if img_elem:
            vod_pic = img_elem.get('data-original', '') or img_elem.get('data-src', '') or img_elem.get('src', '')
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = self.site_url + vod_pic
        desc_elem = soup.select_one('.module-info-introduction-content p') or soup.select_one('.hl-content-rt p')
        vod_content = desc_elem.get_text(strip=True) if desc_elem else ''
        vod_director = ''
        vod_actor = ''
        info_items = soup.select('.module-info-item') or soup.select('.hl-detail-content .hl-info-item')
        for item in info_items:
            title_elem = item.select_one('.module-info-item-title') or item.select_one('.hl-info-label')
            content_elem = item.select_one('.module-info-item-content') or item.select_one('.hl-info-value')
            if not title_elem or not content_elem:
                continue
            label = title_elem.get_text(strip=True)
            value = content_elem.get_text(strip=True)
            if '导演' in label:
                vod_director = value
            if '主演' in label:
                vod_actor = value
        play_from_list = []
        play_url_list = []
        tab_items = soup.select('.module-tab-item') or soup.select('.hl-tabs-btn')
        play_containers = soup.select('.module-list.sort-list.tab-list') or soup.select('.hl-plays-from')
        if tab_items and play_containers and len(tab_items) == len(play_containers):
            for idx, tab in enumerate(tab_items):
                source_name = tab.get('data-dropdown-value', '') or tab.get_text(strip=True)
                episodes = []
                for a in play_containers[idx].select('a.module-play-list-link') or play_containers[idx].select('a.hl-play-link'):
                    href = a.get('href', '')
                    if not href:
                        continue
                    text = a.get_text(strip=True)
                    episodes.append(f"{text}${href}")
                if episodes:
                    play_from_list.append(source_name)
                    play_url_list.append('#'.join(episodes))
        if not play_from_list:
            all_items = soup.select('.module-play-list-content a.module-play-list-link') or soup.select('.hl-plays-list a')
            if all_items:
                episodes = []
                for a in all_items:
                    href = a.get('href', '')
                    if not href:
                        continue
                    text = a.get_text(strip=True)
                    episodes.append(f"{text}${href}")
                if episodes:
                    play_from_list.append('默认线路')
                    play_url_list.append('#'.join(episodes))
        return {"list": [{"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic, "vod_content": vod_content, "vod_director": vod_director, "vod_actor": vod_actor, "vod_play_from": '$$$'.join(play_from_list), "vod_play_url": '$$$'.join(play_url_list)}]}

    def searchContent(self, key, quick, pg="1"):
        self._ensure_init()
        page = int(pg) if pg else 1
        url = f"{self.site_url}/vodsearch/{urllib.parse.quote(key)}-------------.html"
        if page > 1:
            url = f"{self.site_url}/vodsearch/{urllib.parse.quote(key)}----------{page}---.html"
        resp = self.fetch(url, headers=self.headers)
        if not resp:
            return {"list": [], "page": page, "pagecount": 1}
        soup = BeautifulSoup(resp.text, 'html.parser')
        video_list = []
        cards = soup.select('a.hl-item-thumb')
        for card in cards:
            item = self._parse_video_card(card)
            if item:
                video_list.append(item)
        return {"list": video_list, "page": page, "pagecount": 1}

    def playerContent(self, flag, id, vipFlags):
        self._ensure_init()
        play_url = id if id.startswith('http') else self.site_url + id
        
        resp = self.fetch(play_url, headers=self.headers)
        if not resp:
            return {"parse": 1, "url": play_url, "header": self.headers}
        
        html = resp.text
        # 从 player_aaaa 对象中提取直链
        m3u8_match = re.search(r'player_aaaa\s*=\s*\{[^}]*"url":"([^"]+\.m3u8[^"]*)"', html)
        if m3u8_match:
            direct_url = m3u8_match.group(1)
            if direct_url.startswith('//'):
                direct_url = 'https:' + direct_url
            return {"parse": 0, "url": direct_url, "header": self.headers}
        
        # 从其他模式提取
        m3u8_match2 = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if m3u8_match2:
            direct_url = m3u8_match2.group(0)
            return {"parse": 0, "url": direct_url, "header": self.headers}
        
        return {"parse": 1, "url": play_url, "header": self.headers}