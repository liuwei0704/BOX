import sys
import requests
from bs4 import BeautifulSoup
import json
import re

class Spider():
    def __init__(self):
        self.host = "https://6o5n.xxaaddss.com"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://6o5n.xxaaddss.com/"
        }

    def getName(self):
        return "性爱大师"

    def init(self, extend=""):
        pass

    def isVideoCanWin(self, url):
        return False

    def getDependence(self):
        return []

    def localProxy(self, proxy):
        return None

    def homeContent(self, filter):
        result = {}
        classes = [
            {"type_name": "国产自拍", "type_id": "1"},
            {"type_name": "网友自拍", "type_id": "2"},
            {"type_name": "麻豆传媒", "type_id": "3"},
            {"type_name": "探花系列", "type_id": "4"},
            {"type_name": "三级伦理", "type_id": "5"}
        ]
        result['class'] = classes
        try:
            res = requests.get(self.host, headers=self.header, timeout=10)
            result['list'] = self.parseList(res.text)
        except:
            result['list'] = []
        return result

    def homeVideoContent(self):
        try:
            res = requests.get(self.host, headers=self.header, timeout=10)
            return {"list": self.parseList(res.text)}
        except:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            return {
                'list': self.parseList(res.text),
                'page': int(pg),
                'pagecount': 99,
                'limit': 24,
                'total': 999
            }
        except:
            return {'list': [], 'page': int(pg)}

    def detailContent(self, ids):
        vod_id = ids[0]
        url = self.host + vod_id if vod_id.startswith('/') else f"{self.host}/index.php/vod/detail/id/{vod_id}.html"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            vod = {
                "vod_id": vod_id,
                "vod_name": soup.title.text.split('-')[0].strip(),
                "vod_pic": "",
                "vod_play_from": "MasterPlayer",
                "vod_play_url": f"立即播放${vod_id}"
            }
            return {"list": [vod]}
        except:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{key}.html"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            return {"list": self.parseList(res.text)}
        except:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        url = self.host + id if id.startswith('/') else id
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            match = re.search(r'var player_aaaa\s*=\s*(\{.*?\})', res.text)
            if match:
                config = json.loads(match.group(1))
                return {"parse": 0, "url": config.get('url', ''), "header": self.header}
        except:
            pass
        return {"parse": 0, "url": "", "header": self.header}

    def parseList(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        vod_list = []
        items = soup.select('div.block-post > div')
        for item in items:
            a = item.select_one('a')
            img = item.select_one('img')
            remarks = item.select_one('span.atten')
            if a:
                raw_name = a.get_text(strip=True)
                clean_name = re.sub(r'\d{4}-\d{2}-\d{2}.*$', '', raw_name)
                clean_name = re.sub(r'\d+$', '', clean_name).strip()
                vod_list.append({
                    "vod_id": a['href'],
                    "vod_name": clean_name if clean_name else raw_name,
                    "vod_pic": img.get('data-src', '') if img else "",
                    "vod_remarks": remarks.get_text(strip=True) if remarks else ""
                })
        return vod_list

if __name__ == '__main__':
    spider = Spider()
    print(spider.homeContent(False))