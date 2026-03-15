# coding=utf-8
import re, sys, requests, json, base64, urllib.parse
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self): return "短剧网"

    def init(self, extend=""):
        self.host = "https://www.duanjuhk.com"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36'}

    def homeContent(self, filter):
        if not hasattr(self, 'host'): self.init()
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
        url = f"{self.host}/vodtype/{tid}.html" if p <= 1 else f"{self.host}/vodtype/{tid}-{p}.html"
        vids = self.get_list(url, is_page=True)
        return {"list": vids, "page": p, "pagecount": 99, "limit": 20, "total": 999}

    def get_list(self, url, is_page=False):
        vids = []
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            container = soup.select_one('.hl-vod-list')
            items = container.select('.hl-list-item') if container else soup.select('.hl-list-item')
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
        url = f"{self.host}/index.php/vod/search/wd/{key}/page/{pg}.html"
        return {"list": self.get_list(url)}

    def playerContent(self, flag, id, vipFlags):
        if not hasattr(self, 'host'): self.init()
        # 还原最简单的逻辑：直接返回播放页 URL，让壳子内置的解析/嗅探去工作
        p_url = self.host + id if id.startswith('/') else id
        return {
            "parse": 1,
            "url": p_url,
            "header": {"User-Agent": self.headers['User-Agent']}
        }
        if not hasattr(self, 'host'): self.init()
        p_url = self.host + id if id.startswith('/') else id
        try:
            r = requests.get(p_url, headers=self.headers, timeout=10)
            # 尝试找 player_aaaa 里的直链
            match = re.search(r'player_aaaa\s*=\s*(\{.*?\})', r.text)
            if match:
                data = json.loads(match.group(1))
                v_url = urllib.parse.unquote(data.get('url', ''))
                # 如果是直链且非网页
                if v_url.startswith('http') and ('.m3u8' in v_url or '.mp4' in v_url or '.flv' in v_url):
                    return {"parse": 0, "playUrl": "", "url": v_url, "header": self.headers}
        except: pass
        # 兜底方案：给网页链接，但注入 UA 诱导壳子进行嗅探
        return {
            "parse": 1,
            "url": p_url,
            "header": self.headers
        }