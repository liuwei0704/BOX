#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup

class Spider:
    def getName(self):
        return "夜趣福利"

    def getDependence(self):
        return ["bs4", "requests"]

    def init(self, extend=""):
        self.site_url = "https://yqfl9.cfd"
        self.limit = 24
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.site_url,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate'
        }
        self.categories = [
            {"type_id": "28", "type_name": "国产自拍"},
            {"type_id": "29", "type_name": "主播诱惑"},
            {"type_id": "30", "type_name": "探花约炮"},
            {"type_id": "31", "type_name": "偷拍偷窥"},
            {"type_id": "32", "type_name": "网曝吃瓜"},
            {"type_id": "33", "type_name": "抖阴短片"},
            {"type_id": "34", "type_name": "传媒剧情"},
            {"type_id": "35", "type_name": "日韩主播"},
            {"type_id": "36", "type_name": "日韩无码"},
            {"type_id": "37", "type_name": "中文字幕"},
            {"type_id": "38", "type_name": "AV解说"},
            {"type_id": "39", "type_name": "换脸明星"},
            {"type_id": "40", "type_name": "强奸乱伦"},
            {"type_id": "41", "type_name": "女优明星"},
            {"type_id": "42", "type_name": "欧美激情"}
        ]
        self.filters = {}

    def _ensure_init(self):
        if not hasattr(self, 'site_url'):
            self.init()

    def fetch(self, url):
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            r.encoding = 'utf-8'
            return r
        except Exception as e:
            print(f"请求失败: {url}, 错误: {e}")
            return None

    def _parse_video_card(self, card):
        """解析视频卡片（分类页用）"""
        href = card.get('href', '')
        match = re.search(r'/movie/index(\d+)\.html', href)
        if not match:
            return None
        vod_id = match.group(1)
        
        vod_name = card.get('title', '')
        if not vod_name:
            img = card.find('img')
            if img:
                vod_name = img.get('alt', '')
        if not vod_name:
            vod_name = card.get_text(strip=True)
        
        vod_pic = card.get('data-original', '')
        if not vod_pic:
            img = card.find('img')
            if img:
                vod_pic = img.get('data-original', '') or img.get('src', '')
        if vod_pic and vod_pic.startswith('//'):
            vod_pic = 'https:' + vod_pic
        elif vod_pic and vod_pic.startswith('/'):
            vod_pic = self.site_url + vod_pic
        
        return {"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic}

    def homeContent(self, filter):
        self._ensure_init()
        return {"class": self.categories, "list": [], "filters": self.filters}

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        self._ensure_init()
        page = int(pg) if pg else 1
        if page == 1:
            url = f"{self.site_url}/frim/index{tid}.html"
        else:
            url = f"{self.site_url}/frim/index{tid}-{page}.html"
        
        resp = self.fetch(url)
        if not resp:
            return {"list": [], "page": page, "pagecount": 1, "limit": self.limit, "total": 0}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        video_list = []
        cards = soup.select('a.stui-vodlist__thumb')
        for card in cards:
            item = self._parse_video_card(card)
            if item:
                video_list.append(item)
        
        pagecount = page
        for a in soup.select('.stui-page a'):
            href = a.get('href', '')
            match = re.search(r'/frim/index\d+-(\d+)\.html', href)
            if match:
                p = int(match.group(1))
                if p > pagecount:
                    pagecount = p
        
        if pagecount < page:
            pagecount = page + 1
        
        return {"list": video_list, "page": page, "pagecount": pagecount, "limit": self.limit, "total": 0}

    def detailContent(self, ids):
        self._ensure_init()
        if not ids:
            return {"list": []}
        vod_id = ids[0]
        url = f"{self.site_url}/movie/index{vod_id}.html"
        resp = self.fetch(url)
        if not resp:
            return {"list": []}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        title_elem = soup.select_one('h3.title')
        if not title_elem:
            title_elem = soup.select_one('h1')
        vod_name = title_elem.get_text(strip=True) if title_elem else ''
        
        img_elem = soup.select_one('a.stui-vodlist__thumb')
        vod_pic = ''
        if img_elem:
            vod_pic = img_elem.get('data-original', '') or img_elem.get('src', '')
            if vod_pic and vod_pic.startswith('//'):
                vod_pic = 'https:' + vod_pic
            elif vod_pic and vod_pic.startswith('/'):
                vod_pic = self.site_url + vod_pic
        
        play_from_list = []
        play_url_list = []
        episodes = []
        for a in soup.select('ul.stui-content__playlist a'):
            href = a.get('href', '')
            if not href:
                continue
            text = a.get_text(strip=True)
            episodes.append(f"{text}${href}")
        
        if episodes:
            play_from_list.append('云播')
            play_url_list.append('#'.join(episodes))
        
        return {"list": [{
            "vod_id": vod_id, 
            "vod_name": vod_name, 
            "vod_pic": vod_pic,
            "vod_play_from": '$$$'.join(play_from_list), 
            "vod_play_url": '$$$'.join(play_url_list)
        }]}

    def searchContent(self, key, quick, pg="1"):
        self._ensure_init()
        page = int(pg) if pg else 1
        url = f"{self.site_url}/search.php"
        data = {"searchword": key}
        try:
            r = requests.post(url, data=data, headers=self.headers, timeout=15)
            r.encoding = 'utf-8'
        except:
            return {"list": [], "page": page, "pagecount": 1}
        
        soup = BeautifulSoup(r.text, 'html.parser')
        video_list = []
        # 搜索页使用 ul.stui-vodlist__media li a
        for a in soup.select('ul.stui-vodlist__media li a.stui-vodlist__thumb'):
            href = a.get('href', '')
            # 搜索页的链接是 /play/xxx-0-0.html，需要转换为 /movie/indexxxx.html
            match = re.search(r'/play/(\d+)-\d+-\d+\.html', href)
            if match:
                vod_id = match.group(1)
                vod_name = a.get('title', '')
                vod_pic = a.get('data-original', '')
                if vod_pic and vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
                elif vod_pic and vod_pic.startswith('/'):
                    vod_pic = self.site_url + vod_pic
                video_list.append({"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic})
        
        return {"list": video_list, "page": page, "pagecount": 1}

    def playerContent(self, flag, id, vipFlags):
        self._ensure_init()
        if id.startswith('http'):
            play_url = id
        else:
            play_url = self.site_url + id
        
        resp = self.fetch(play_url)
        if not resp:
            return {"parse": 1, "url": play_url, "header": self.headers}
        
        html = resp.text
        m3u8_match = re.search(r'var\s+now\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html)
        if m3u8_match:
            direct_url = m3u8_match.group(1)
            if direct_url.startswith('//'):
                direct_url = 'https:' + direct_url
            return {"parse": 0, "url": direct_url, "header": self.headers}
        
        m3u8_match2 = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if m3u8_match2:
            direct_url = m3u8_match2.group(0)
            return {"parse": 0, "url": direct_url, "header": self.headers}
        
        return {"parse": 1, "url": play_url, "header": self.headers}