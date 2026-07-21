# -*- coding: utf-8 -*-
import re
import sys
import json
import requests
import urllib.parse
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    host = 'https://www.zzoc.cc'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.zzoc.cc/',
    }

    def getName(self):
        return "枝枝影視[全功能完美版]"

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        result = {'class': [
            {"type_name": u"電影", "type_id": "1"},
            {"type_name": u"電視劇", "type_id": "2"},
            {"type_name": u"綜藝", "type_id": "3"},
            {"type_name": u"動漫", "type_id": "4"},
            {"type_name": u"短劇", "type_id": "20"}
        ]}
        try:
            res = requests.get(self.host, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            result['list'] = self.parseList(res.text)
        except:
            result['list'] = []
        return result

    def categoryContent(self, tid, pg, filter, extend):
        # 分類分頁：8個橫線
        url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            return {
                'list': self.parseList(res.text),
                'page': int(pg),
                'pagecount': 99,
                'limit': 20,
                'total': 999
            }
        except:
            return {'list': [], 'page': int(pg)}

    def searchContent(self, key, quick, pg=1):
        # 【核心修復：搜索 URL 結構】
        # 格式：/vodsearch/關鍵字----------頁碼---.html (10個橫線)
        wd = urllib.parse.quote(key)
        url = f"{self.host}/vodsearch/{wd}----------{pg}---.html"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            return {'list': self.parseList(res.text)}
        except:
            return {'list': []}

    def detailContent(self, ids):
        id = ids[0]
        url = self._normalize_url(id)
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            pic = ""
            meta_img = soup.find('meta', property='og:image') or soup.find('meta', itemprop='image')
            if meta_img: pic = meta_img.get('content', '')
            if not pic:
                img = soup.select_one('.poster img, .vod-pic img, .lazyload')
                if img: pic = img.get('data-original') or img.get('data-src') or img.get('src')

            vod = {
                "vod_id": id,
                "vod_name": soup.find('h1').get_text(strip=True) if soup.find('h1') else "未知",
                "vod_pic": self._normalize_image_url(pic),
                "vod_play_from": "", 
                "vod_play_url": ""
            }

            from_list, url_list = [], []
            play_tabs = soup.select('.player_name a, .nav-tabs li a')
            play_lists = soup.select('.tab-content .tab-pane, .myui-content__list')

            for i, pane in enumerate(play_lists):
                name = play_tabs[i].get_text(strip=True) if i < len(play_tabs) else f"線路{i+1}"
                links = [f"{a.get_text(strip=True)}${a.get('href', '')}" for a in pane.select('a') if 'vodplay' in a.get('href', '')]
                if links:
                    from_list.append(name)
                    url_list.append("#".join(links))

            vod['vod_play_from'] = "$$$".join(from_list)
            vod['vod_play_url'] = "$$$".join(url_list)
            return {"list": [vod]}
        except: return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        url = self._normalize_url(id)
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            match = re.search(r'player_aaaa=(.*?)</script>', res.text)
            if match:
                config = json.loads(match.group(1))
                play_url = config.get('url', '')
                if '%' in play_url: play_url = urllib.parse.unquote(play_url)
                if any(x in play_url.lower() for x in ['.m3u8', '.mp4']):
                    return {"parse": 0, "url": play_url, "header": ""}
            return {"parse": 1, "url": url, "header": ""}
        except: return {"parse": 1, "url": url, "header": ""}

    def parseList(self, html):
        videos = []
        soup = BeautifulSoup(html, 'html.parser')
        # 兼容搜索結果的 module-item 結構和普通列表結構
        items = soup.select('.myui-vodbox-content, .myui-vodlist__box, .myui-vodlist__thumb, li.col-lg-6, .module-item')
        for item in items:
            a = item.select_one('a')
            if not a: continue
            img = item.select_one('img')
            pic = ""
            if img:
                pic = img.get('data-original') or img.get('data-src') or img.get('src')
            if not pic and a.get('style'):
                bg = re.search(r'url\((.*?)\)', a.get('style'))
                if bg: pic = bg.group(1).strip("'\"")

            name_node = item.select_one('.title, .name, .module-item-title, h4')
            name = name_node.get_text(strip=True) if name_node else (img.get('alt', '') if img else "未知")
            
            videos.append({
                "vod_id": a.get('href', ''),
                "vod_name": name,
                "vod_pic": self._normalize_image_url(pic),
                "vod_remarks": item.select_one('.tag, .pic-text, .remarks, .module-item-note').get_text(strip=True) if item.select_one('.tag, .pic-text, .remarks, .module-item-note') else ""
            })
        return videos

    def _normalize_url(self, url):
        if not url: return ""
        url = url.strip()
        if url.startswith('//'): return f"https:{url}"
        if url.startswith('/'): return f"{self.host}{url}"
        return url

    def _normalize_image_url(self, url):
        if not url: return ""
        url = self._normalize_url(url)
        # 保持 Referer 偽裝，確保搜索結果圖片也能顯示
        return f"{url}@Referer={self.host}/@User-Agent={self.headers['User-Agent']}"