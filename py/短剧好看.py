# coding=utf-8
import re, sys, requests, json
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self): return "短剧网"

    def init(self, extend=""):
        self.host = "https://www.duanjuhk.com"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    def homeContent(self, filter):
        if not hasattr(self, 'host'): self.init()
        # 别名和数字 ID 双重保障
        result = {'class': [
            {"type_name": "都市", "type_id": "dushi"},
            {"type_name": "穿越", "type_id": "chuanyue"},
            {"type_name": "古代", "type_id": "gudai"},
            {"type_name": "福利", "type_id": "fuliduanju"}
        ]}
        result['list'] = self.get_list(self.host)
        return result

    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'host'): self.init()
        p = int(pg)
    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'host'): self.init()
        p = int(pg)
        if p <= 1:
            url = f"{self.host}/vodtype/{tid}.html"
        else:
            url = f"{self.host}/vodtype/{tid}-{p}.html"
        vids = self.get_list(url, is_page=True)
        vids = self.get_list(url, is_page=True)
        return {"list": vids, "page": p, "pagecount": 99, "limit": 20, "total": 999}

    def get_list(self, url, is_page=False):
        vids = []
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 重点：HL 模板分类列表通常在 hl-vod-list 中
            container = soup.select_one('.hl-vod-list')
            if not container:
                # 兼容模式：如果没有找到主列表容器，则寻找所有 item 但排除掉置顶推荐区域
                items = [i for i in soup.select('.hl-list-item') if not i.find_parent(class_='hl-br-list')]
            else:
                items = container.select('.hl-list-item')

            for item in items:
                a = item.select_one('.hl-item-thumb, .hl-item-content a')
                if not a: continue
                vids.append({
                    "vod_id": a['href'],
                    "vod_name": a.get('title') or item.select_one('.hl-item-title').text.strip(),
                    "vod_pic": self.host + a['data-original'] if a.get('data-original','').startswith('/') else a.get('data-original',''),
                    "vod_remarks": item.select_one('.hl-lc-1').text.strip() if item.select_one('.hl-lc-1') else ""
                })
        except: pass
        return vids

    def detailContent(self, ids):
        if not hasattr(self, 'host'): self.init()
        try:
            r = requests.get(self.host + ids[0], headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            vod = {
                "vod_id": ids[0],
                "vod_name": soup.select_one('.hl-dc-title').text.strip(),
                "vod_pic": self.host + soup.select_one('.hl-item-thumb')['data-original'] if soup.select_one('.hl-item-thumb') else "",
                "vod_play_from": "$$$".join([t.text.strip() for t in soup.select('.hl-tabs-btn')]),
                "vod_play_url": "$$$".join(["#".join([f"{a.text}${a['href']}" for a in pl.find_all('a')]) for pl in soup.select('.hl-plays-list')])
            }
            return {"list": [vod]}
        except: return {"list": []}

    def searchContent(self, key, quick, pg=1):
        if not hasattr(self, 'host'): self.init()
        # 搜索路径尝试
        url = f"{self.host}/index.php/vod/search/wd/{key}/page/{pg}.html"
        return {"list": self.get_list(url)}

    def playerContent(self, flag, id, vipFlags):
        if not hasattr(self, 'host'): self.init()
        try:
            r = requests.get(self.host + id, headers=self.headers, timeout=10)
            match = re.search(r'player_aaaa=(.*?)</script>', r.text)
            if match: return {"parse": 0, "playUrl": "", "url": json.loads(match.group(1))['url']}
        except: pass
        return {"parse": 1, "playUrl": "", "url": self.host + id}