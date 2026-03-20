import requests
import re
import json
from bs4 import BeautifulSoup

class Spider():
    host = "https://www.rewardreels.com"

    def getName(self): return "快看短剧"
    def getDependence(self): return ['requests', 'bs4']
    def isSearchable(self): return True
    def isFilterable(self): return False
    def init(self, extend=""): pass

    def homeContent(self, filter):
        return {'class': [{"type_id": "2", "type_name": "中文短剧"},{"type_id": "3", "type_name": "Short Drama"},{"type_id": "15", "type_name": "擦边短剧"}]}

    def homeVideoContent(self):
        videos = []
        try:
            r = requests.get(self.host, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(r.text, 'html.parser')
            for item in soup.select('.hl-list-item')[:20]:
                t, a = item.select_one('.hl-item-title'), item.select_one('.hl-item-thumb')
                if t and a:
                    pic = a.get('data-original', '')
                    videos.append({"vod_id": a.get('href', ''), "vod_name": t.text.strip(), "vod_pic": self.host + pic if pic.startswith('/') else pic, "vod_remarks": item.select_one('.hl-lc-1').text.strip() if item.select_one('.hl-lc-1') else ""})
        except: pass
        return {"list": videos}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg)
        res = {'list': [], 'page': pg, 'pagecount': pg + 1, 'limit': 20, 'total': 9999}
        try:
            url = f"{self.host}/index.php/vod/show/id/{tid}/page/{pg}.html"
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': f"{self.host}/index.php/vod/show/id/{tid}.html"}
            r = requests.get(url, timeout=10, headers=headers)
            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.select('.hl-list-item')
            if not items:
                res['pagecount'] = pg
                return res
            for item in items:
                a = item.select_one('.hl-item-thumb')
                if a:
                    pic = a.get('data-original', '')
                    res['list'].append({'vod_id': a.get('href', ''), 'vod_name': a.get('title') or item.select_one('.hl-item-title').text.strip(), 'vod_pic': self.host + pic if pic.startswith('/') else pic, 'vod_remarks': item.select_one('.hl-lc-1').text.strip() if item.select_one('.hl-lc-1') else ""})
            res['pagecount'] = pg + 1
        except: pass
        return res

    def detailContent(self, ids):
        res = {'list': []}
        try:
            url = self.host + ids[0] if ids[0].startswith('/') else ids[0]
            r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(r.text, 'html.parser')
            n, p = (soup.select_one('.hl-dc-title') or soup.select_one('h1')), soup.select_one('.hl-dc-pic img')
            pic = p.get('data-original') or p.get('src') or "" if p else ""
            vod = {"vod_id": ids[0], "vod_name": n.text.strip() if n else "未知", "vod_pic": self.host + pic if pic.startswith('/') else pic, "type_name": "短剧", "vod_content": soup.select_one('.hl-content-text').text.strip() if soup.select_one('.hl-content-text') else ""}
            play_from, play_url = [], []
            tabs, lists = soup.select('.hl-plays-from a'), soup.select('.hl-plays-list')
            for i in range(len(tabs)):
                play_from.append(tabs[i].text.strip())
                items = lists[i].select('a') if i < len(lists) else []
                play_url.append("#".join([f"{it.text.strip()}${it.get('href', '')}" for it in items if it.get('href')]))
            vod.update({"vod_play_from": "$$$".join(play_from), "vod_play_url": "$$$".join(play_url)})
            res['list'].append(vod)
        except: pass
        return res

    def searchContent(self, key, quick, pg=1):
        pg = int(pg)
        # 🔥 搜索翻页诱导逻辑：初始让 pagecount 始终比当前页大 1
        res = {'list': [], 'page': pg, 'pagecount': pg + 1, 'limit': 20, 'total': 9999}
        try:
            # 修正搜索分页 URL，部分站点需要 urlencode 关键词，这里 requests 会自动处理
            url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{key}.html"
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': self.host}
            r = requests.get(url, timeout=10, headers=headers)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            items = soup.select('.hl-list-item')
            if not items:
                # 真的搜不到了，熔断翻页
                res['pagecount'] = pg
                return res
                
            for item in items:
                a = item.select_one('.hl-item-thumb')
                if a:
                    pic = a.get('data-original', '')
                    res['list'].append({
                        'vod_id': a.get('href', ''),
                        'vod_name': item.select_one('.hl-item-title').text.strip(),
                        'vod_pic': self.host + pic if pic.startswith('/') else pic,
                        'vod_remarks': item.select_one('.hl-lc-1').text.strip() if item.select_one('.hl-lc-1') else ""
                    })
            
            # 只要有数据，就保持翻页动力
            res['pagecount'] = pg + 1
        except: pass
        return res

    def playerContent(self, flag, id, vipFlags):
        url = self.host + id if id.startswith('/') else id
        js = "var checkUrl = setInterval(function(){ if(player_aaaa.url && player_aaaa.url.indexOf('http')>=0){ clearInterval(checkUrl); window.location.href = player_aaaa.url; } }, 500);"
        return {
            "parse": 1,
            "url": url,
            "js": js,
            "header": {"User-Agent": "Mozilla/5.0", "Referer": self.host}
        }

    def localProxy(self, param): pass