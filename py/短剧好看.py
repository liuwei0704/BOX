# coding=utf-8
import re
import sys
import requests
import json
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "短剧好看"

    def init(self, extend=""):
        self.host = "https://www.duanjuhk.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }

    def homeContent(self, filter):
        if not hasattr(self, 'host'):
            self.init()
        result = {}
        result['class'] = [
            {"type_name": "精选", "type_id": "jingxuanduanju"},
            {"type_name": "都市", "type_id": "dushi"},
            {"type_name": "穿越", "type_id": "chuanyue"},
            {"type_name": "古代", "type_id": "gudai"},
            {"type_name": "福利", "type_id": "fuliduanju"}
        ]
        result['list'] = self.get_list(self.host)
        return result

    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'host'):
            self.init()
        url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
        return {
            "list": self.get_list(url),
            "page": int(pg),
            "pagecount": 99,
            "limit": 20,
            "total": 999
        }

    def detailContent(self, ids):
        if not hasattr(self, 'host'):
            self.init()
        url = self.host + ids[0]
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            # 适配 HL 模板详情页
            name = soup.select_one('.hl-dc-title').text.strip() if soup.select_one('.hl-dc-title') else "未知"
            pic = soup.select_one('.hl-item-thumb')['data-original'] if soup.select_one('.hl-item-thumb') else ""
            
            # 播放列表解析
            play_lists = soup.select('.hl-plays-list')
            tabs = soup.select('.hl-tabs-btn')
            
            play_from = []
            play_url = []
            
            for i, pl in enumerate(play_lists):
                source_name = tabs[i].text.strip() if i < len(tabs) else f"线路{i+1}"
                play_from.append(source_name)
                links = []
                for a in pl.find_all('a'):
                    links.append(f"{a.text}${a['href']}")
                play_url.append("#".join(links))

            vod = {
                "vod_id": ids[0],
                "vod_name": name,
                "vod_pic": self.host + pic if pic and pic.startswith('/') else pic,
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_url)
            }
            return {"list": [vod]}
        except:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        if not hasattr(self, 'host'):
            self.init()
        url = f"{self.host}/vodsearch/{key}----------{pg}---.html"
        return {"list": self.get_list(url)}

    def playerContent(self, flag, id, vipFlags):
        if not hasattr(self, 'host'):
            self.init()
        url = self.host + id
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            match = re.search(r'player_aaaa=(.*?)</script>', r.text)
            if match:
                config = json.loads(match.group(1))
                return {"parse": 0, "playUrl": "", "url": config['url']}
        except:
            pass
        return {"parse": 1, "playUrl": "", "url": url}

    def get_list(self, url):
        vids = []
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.select('.hl-list-item')
            for item in items:
                a = item.select_one('.hl-item-thumb, .hl-item-content a')
                if not a: continue
                name = a.get('title') or (item.select_one('.hl-item-title').text.strip() if item.select_one('.hl-item-title') else "未知")
                pic = a.get('data-original') or a.get('data-src')
                
                vids.append({
                    "vod_id": a['href'],
                    "vod_name": name,
                    "vod_pic": self.host + pic if pic and pic.startswith('/') else pic,
                    "vod_remarks": item.select_one('.hl-lc-1, .remarks').text.strip() if item.select_one('.hl-lc-1, .remarks') else ""
                })
        except:
            pass
        return vids