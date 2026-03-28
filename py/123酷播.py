import sys
import requests
import re
import json
import base64
from bs4 import BeautifulSoup

class Spider():
    def __init__(self):
        self.host = "https://123kubo.tv"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': self.host,
        }

    def getName(self):
        return "123酷播"

    def getDependence(self):
        return []

    def init(self, extend=""):
        try:
            self.session.get(self.host, headers=self.headers, timeout=10)
        except:
            pass

    def homeContent(self, filter):
        result = {'class': [
            {"type_name": "電影", "type_id": "1"},
            {"type_name": "連續劇", "type_id": "2"},
            {"type_name": "綜藝", "type_id": "3"},
            {"type_name": "動漫", "type_id": "4"}
        ]}
        result['filters'] = {
            "1": [{"key": "tid", "name": "類型", "value": [{"n": "全部", "v": "1"}, {"n": "動作片", "v": "6"}, {"n": "喜劇片", "v": "7"}, {"n": "愛情片", "v": "8"}, {"n": "科幻片", "v": "9"}, {"n": "恐怖片", "v": "10"}, {"n": "劇情片", "v": "11"}, {"n": "戰爭片", "v": "12"}, {"n": "紀錄片", "v": "20"}, {"n": "微電影", "v": "21"}, {"n": "動漫片", "v": "22"}, {"n": "倫理片", "v": "23"}]}],
            "2": [{"key": "tid", "name": "類型", "value": [{"n": "全部", "v": "2"}, {"n": "陸劇", "v": "13"}, {"n": "港劇", "v": "14"}, {"n": "台劇", "v": "15"}, {"n": "日劇", "v": "16"}, {"n": "韓劇", "v": "24"}, {"n": "美劇", "v": "25"}, {"n": "泰劇", "v": "26"}, {"n": "海外劇", "v": "27"}]}],
            "3": [{"key": "tid", "name": "類型", "value": [{"n": "全部", "v": "3"}, {"n": "內地綜藝", "v": "28"}, {"n": "日韓綜藝", "v": "29"}, {"n": "港台綜藝", "v": "30"}, {"n": "歐美綜藝", "v": "31"}]}],
            "4": [{"key": "tid", "name": "類型", "value": [{"n": "全部", "v": "4"}, {"n": "國產動漫", "v": "32"}, {"n": "日韓動漫", "v": "33"}, {"n": "港台動漫", "v": "34"}, {"n": "歐美動漫", "v": "35"}, {"n": "海外動漫", "v": "36"}]}]
        }
        try:
            res = self.session.get(self.host, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            result["list"] = self.parseList(res.text)
        except:
            result['list'] = []
        return result

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        target_tid = extend.get("tid", tid)
        url = f"{self.host}/show/{target_tid}/page/{pg}.html"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            v_list = self.parseList(res.text)
            return {"list": v_list, "page": int(pg), "pagecount": 99, "limit": len(v_list), "total": 999}
        except:
            return {"list": [], "page": int(pg)}

    def parseList(self, html):
        video_list = []
        soup = BeautifulSoup(html, 'parser.html' if 'parser.html' in sys.modules else 'html.parser')
        items = soup.select('.hl-list-item, .hl-item-pic, .hl-vod-list li, .hl-item-thumb, .conch-list-item')
        if not items:
            items = soup.find_all('a', href=re.compile(r'/detail/|/play/|/eps/'))
        
        blacklist = ["線上看", "首頁", "專題", "留言", "排行", "最近更新", "推薦", "APP", "公告"]
        
        for item in items:
            try:
                a = item if item.name == 'a' else item.find('a')
                if not a: continue
                href = a.get('href', '')
                if not href or "/play/" in href: continue # 排除直接播放鏈接
                
                name = a.get('title') or (a.find('img').get('alt') if a.find('img') else "")
                if not name:
                    name_el = item.select_one('.hl-item-title, .hl-item-name, .title, .name')
                    name = name_el.text.strip() if name_el else a.text.strip()
                
                if not name or len(name) < 2 or len(name) > 40: continue
                if any(word == name for word in blacklist): continue

                # 【標題清洗修復】切除：線上看、電影線上看、高清線上看及其前綴標點
                name = re.sub(r'(-|\||_)?(電影|劇集|動漫|綜藝|免費|高清)?線上看.*', '', name).strip()
                name = name.replace("123酷播", "").strip()
                
                pic = a.get('data-original') or a.get('src') or ""
                img = a.find('img')
                if not pic and img:
                    pic = img.get('data-original') or img.get('src') or ""
                
                rem_el = item.select_one('.hl-item-remarks, .remarks, .state')
                remarks = rem_el.text.strip() if rem_el else ""
                
                video_list.append({
                    "vod_id": href, 
                    "vod_name": name, 
                    "vod_pic": pic if pic.startswith("http") else self.host + pic, 
                    "vod_remarks": remarks
                })
            except:
                continue
        
        res_list, seen = [], set()
        for v in video_list:
            if v['vod_id'] not in seen:
                res_list.append(v)
                seen.add(v['vod_id'])
        return res_list

    def detailContent(self, ids):
        id = ids[0]
        url = f"{self.host}{id}" if id.startswith("/") else id
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            # 詳情頁標題也做同樣的清洗
            raw_title = soup.title.text.split('-')[0].strip()
            title = re.sub(r'(-|\||_)?(電影|劇集|動漫|綜藝|免費|高清)?線上看.*', '', raw_title).strip()
            
            vod = {"vod_id": id, "vod_name": title, "vod_pic": "", "vod_play_from": "", "vod_play_url": ""}
            from_list, url_list = [], []
            play_tabs = soup.select('.hl-tabs-btn, .hl-plays-from a')
            play_uls = soup.find_all('ul', class_=re.compile(r'hl-plays-list'))
            for i, ul in enumerate(play_uls):
                name = play_tabs[i].text.strip() if i < len(play_tabs) else f"線路{i+1}"
                from_list.append(name)
                links = [f"{a.text.strip()}${a.get('href')}" for a in ul.find_all('a') if a.get('href')]
                url_list.append("#".join(links))
            vod['vod_play_from'] = "$$$".join(from_list)
            vod['vod_play_url'] = "$$$".join(url_list)
            return {"list": [vod]}
        except:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        url = f"{self.host}/search/page/{pg}/wd/{key}.html"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            return {"list": self.parseList(res.text)}
        except:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        url = f"{self.host}{id}" if id.startswith("/") else id
        try:
            self.headers['Referer'] = url
            res = self.session.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            html = res.text
            jisu = re.search(r'(https?:\\?/\\?/[^"\']+\.m3u8[^"\']*)', html)
            if jisu:
                return {"parse": 0, "url": jisu.group(1).replace('\\/', '/'), "header": self.headers}
            match = re.search(r'player_aaaa\s*=\s*(\{.*?\})', html)
            if match:
                config = json.loads(match.group(1))
                v_url = config.get('url', '').replace('\\/', '/')
                if v_url:
                    if not any(x in v_url.lower() for x in ['.m3u8', '.mp4', 'http']) and len(v_url) > 20:
                        try:
                            v_url = base64.b64decode(v_url).decode('utf-8')
                        except:
                            pass
                    parse = 0 if '.m3u8' in v_url.lower() or '.mp4' in v_url.lower() else 1
                    return {"parse": parse, "url": v_url, "header": self.headers}
            soup = BeautifulSoup(html, 'html.parser')
            ifr = soup.select_one('.hl-player-box iframe') or soup.find('iframe')
            if ifr and ifr.get('src'):
                return {"parse": 1, "url": ifr.get('src').replace('\\/', '/'), "header": self.headers}
        except:
            pass
        return {"parse": 1, "url": url, "header": self.headers}
