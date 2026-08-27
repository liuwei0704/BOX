# -*- coding: utf-8 -*-
import requests
import re
from bs4 import BeautifulSoup
import json
import urllib.parse
import base64

class Spider:
    host = "https://ktv183.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': "https://ktv183.com"
    }

    def init(self, extend=""):
        print("KTV183 完美修復版 (含搜尋分頁) 初始化成功")

    def getName(self):
        return "KTV183"

    def getDependence(self):
        return []

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        try:
            classes = [
                {'type_id': '5', 'type_name': '短剧'},
                {'type_id': '2', 'type_name': '连续剧'},
                {'type_id': '1', 'type_name': '电影'},
                {'type_id': '4', 'type_name': '动漫'},
                {'type_id': '3', 'type_name': '综艺'}
            ]
            
            common_years = [{"n": "全部", "v": ""}] + [{"n": str(y), "v": str(y)} for y in range(2026, 2003, -1)]
            common_by = [{"n": "时间", "v": "time"}, {"n": "人气", "v": "hits"}, {"n": "评分", "v": "score"}]

            filters = {
                "5": [
                    {"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}, {"n": "女频恋爱", "v": "36"}, {"n": "古装仙侠", "v": "37"}, {"n": "擦边短剧", "v": "38"}, {"n": "现代都市", "v": "39"}, {"n": "年代穿越", "v": "40"}, {"n": "反转爽剧", "v": "41"}, {"n": "脑洞悬疑", "v": "42"}, {"n": "深夜追剧", "v": "32"}, {"n": "爽文", "v": "33"}]},
                    {"key": "year", "name": "年份", "value": common_years},
                    {"key": "by", "name": "排序", "value": common_by}
                ],
                "2": [
                    {"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}, {"n": "国产剧", "v": "15"}, {"n": "欧美剧", "v": "13"}, {"n": "日剧", "v": "16"}, {"n": "韩剧", "v": "30"}, {"n": "海外剧", "v": "14"}, {"n": "港剧", "v": "31"}]},
                    {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "内地", "v": "内地"}, {"n": "韩国", "v": "韩国"}, {"n": "香港", "v": "香港"}, {"n": "台湾", "v": "台湾"}, {"n": "日本", "v": "日本"}, {"n": "美国", "v": "美国"}]},
                    {"key": "year", "name": "年份", "value": common_years},
                    {"key": "by", "name": "排序", "value": common_by}
                ],
                "1": [
                    {"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}, {"n": "喜剧片", "v": "6"}, {"n": "剧情片", "v": "7"}, {"n": "动作片", "v": "8"}, {"n": "记录片", "v": "9"}, {"n": "战争片", "v": "10"}, {"n": "爱情片", "v": "11"}, {"n": "恐怖片", "v": "12"}, {"n": "科幻片", "v": "21"}]},
                    {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "大陆", "v": "大陆"}, {"n": "美国", "v": "美国"}, {"n": "香港", "v": "香港"}, {"n": "台湾", "v": "台湾"}, {"n": "日本", "v": "日本"}, {"n": "韩国", "v": "韩国"}]},
                    {"key": "year", "name": "年份", "value": common_years},
                    {"key": "by", "name": "排序", "value": common_by}
                ],
                "4": [
                    {"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}, {"n": "国产动漫", "v": "20"}, {"n": "日韩动漫", "v": "22"}, {"n": "欧美动漫", "v": "23"}, {"n": "海外动漫", "v": "24"}]},
                    {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "国产", "v": "国产"}, {"n": "日本", "v": "日本"}, {"n": "欧美", "v": "欧美"}, {"n": "其他", "v": "其他"}]},
                    {"key": "year", "name": "年份", "value": common_years},
                    {"key": "by", "name": "排序", "value": common_by}
                ],
                "3": [
                    {"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}, {"n": "大陆综艺", "v": "25"}, {"n": "欧美综艺", "v": "26"}, {"n": "日韩综艺", "v": "27"}, {"n": "港台综艺", "v": "28"}, {"n": "海外综艺", "v": "29"}]},
                    {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "内地", "v": "内地"}, {"n": "港台", "v": "港台"}, {"n": "日韩", "v": "日韩"}, {"n": "欧美", "v": "欧美"}]},
                    {"key": "year", "name": "年份", "value": common_years},
                    {"key": "by", "name": "排序", "value": common_by}
                ]
            }
            
            res = requests.get(self.host, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = self._parse_vod_list(soup)
            return {'class': classes, 'list': videos, 'filters': filters}
        except: return {'class': [], 'list': []}

    def homeVideoContent(self):
        return self.homeContent(filter=False)

    def categoryContent(self, tid, pg, filter, extend):
        try:
            url = f"{self.host}/index.php/vod/show/id/{tid}/page/{pg}.html"
            for key in ["class", "area", "year", "by"]:
                if extend.get(key):
                    if key == "class":
                        url = url.replace(f"id/{tid}", f"id/{extend[key]}")
                    else:
                        url = url.replace(".html", f"/{key}/{urllib.parse.quote(extend[key])}.html")
            
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            return {'list': self._parse_vod_list(soup), 'page': int(pg), 'pagecount': 99}
        except: return {'list': [], 'page': int(pg)}

    def detailContent(self, ids):
        try:
            vod_id = ids[0] if isinstance(ids, list) else ids
            url = f"{self.host}/index.php/vod/detail/id/{vod_id}.html"
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            name_tag = soup.find('h1') or soup.find('h2') or soup.find(class_=re.compile(r'title'))
            name = name_tag.get_text(strip=True) if name_tag else "未知视频"
            
            play_from, play_url = [], []
            tabs = soup.find_all(['div', 'a', 'span'], class_=re.compile(r'tab-item|module-tab-item'))
            lists = soup.find_all(['div', 'ul'], class_=re.compile(r'play-list|module-play-list'))
            
            valid_tabs = []
            for t in tabs:
                inner_span = t.find('span')
                txt = inner_span.get_text(strip=True) if inner_span else t.get_text(strip=True)
                if txt and "排序" not in txt and txt not in valid_tabs:
                    valid_tabs.append(txt)

            for i in range(min(len(valid_tabs), len(lists))):
                fn = valid_tabs[i]
                links = lists[i].find_all('a', href=re.compile(r'/vod/play/'))
                urls = []
                seen_line_urls = set()
                for l in links:
                    p_name = l.get_text(strip=True)
                    p_url = l.get('href', '')
                    if p_url and p_url not in seen_line_urls:
                        urls.append(f"{p_name}${p_url}")
                        seen_line_urls.add(p_url)
                if urls:
                    play_from.append(fn)
                    play_url.append('#'.join(urls))

            return {'list': [{'vod_id': vod_id, 'vod_name': name, 'vod_play_from': '$$$'.join(play_from), 'vod_play_url': '$$$'.join(play_url)}]}
        except: return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{urllib.parse.quote(key)}.html"
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # --- 分頁提取邏輯 ---
            pagecount = int(pg)
            page_div = soup.find('div', id='page') or soup.find(class_=re.compile(r'pagination|page'))
            if page_div:
                # 尋找最後一個分頁數字，通常是總頁數
                p_links = page_div.find_all('a')
                for pl in p_links:
                    p_match = re.search(r'page/(\d+)', pl.get('href', ''))
                    if p_match:
                        p_val = int(p_match.group(1))
                        if p_val > pagecount: pagecount = p_val

            return {'list': self._parse_search_list(soup), 'page': int(pg), 'pagecount': pagecount}
        except: return {'list': [], 'page': int(pg)}

    def playerContent(self, flag, id, vipFlags):
        try:
            url = self.host + id if id.startswith('/') else id
            res = requests.get(url, headers=self.headers, timeout=10)
            match = re.search(r'var player_aaaa=(.*?)</script>', res.text)
            if match:
                config = json.loads(match.group(1))
                play_url = config.get('url', '')
                if not play_url.startswith('http') and not play_url.endswith('.m3u8'):
                    try:
                        decoded = base64.b64decode(play_url).decode('utf-8')
                        play_url = urllib.parse.unquote(decoded)
                    except: pass
                if play_url.startswith('/') and not play_url.startswith('//'):
                    play_url = self.host + play_url
                return {'parse': 0, 'url': play_url, 'header': self.headers}
            return {'parse': 1, 'url': url, 'header': self.headers}
        except: return {'parse': 1, 'url': id}

    def localProxy(self, param): return None

    def _parse_vod_list(self, soup):
        videos = []
        for item in soup.find_all(['a', 'div'], class_='module-item'):
            try:
                link = item if item.name == 'a' else item.find('a')
                if not link: continue
                id_match = re.search(r'id/(\d+)', link.get('href', ''))
                if not id_match: continue
                img = item.find('img')
                pic = img.get('data-original') or img.get('data-src') or img.get('src') or ""
                if pic and not pic.startswith('http'): pic = self.host + pic
                name = link.get('title') or (item.find('div', class_='module-item-titlebox').text.strip() if item.find('div', class_='module-item-titlebox') else "未知")
                note = item.find('div', class_='module-item-note')
                videos.append({'vod_id': id_match.group(1), 'vod_name': name, 'vod_pic': pic, 'vod_remarks': note.text.strip() if note else ""})
            except: continue
        return videos

    def _parse_search_list(self, soup):
        videos = []
        items = soup.find_all('div', class_='module-card-item')
        for item in items:
            try:
                link = item.find('a', href=re.compile(r'id/(\d+)'))
                if not link: continue
                id_match = re.search(r'id/(\d+)', link['href'])
                title_tag = item.find(class_='module-card-item-title')
                name = title_tag.get_text(strip=True) if title_tag else ""
                if not name:
                    img = item.find('img')
                    name = img.get('alt', '').strip() if img else "未知"
                img_tag = item.find('img')
                pic = img_tag.get('data-original') or img_tag.get('data-src') or img_tag.get('src') or ""
                if pic and not pic.startswith('http'): pic = self.host + pic
                note = item.find(class_=re.compile(r'module-item-note|remarks'))
                videos.append({'vod_id': id_match.group(1), 'vod_name': name, 'vod_pic': pic, 'vod_remarks': note.get_text(strip=True) if note else ""})
            except: continue
        return videos if videos else self._parse_vod_list(soup)