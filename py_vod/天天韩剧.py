# coding=utf-8
import sys
import re
import requests
import json
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    host = "https://www.tthj.cc"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': "https://www.tthj.cc/",
    }

    def getName(self):
        return ""

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        result = {}
        #  Unicode /
        result['class'] = [
            {"type_name": u"\u97e9\u5267", "type_id": "1"},
            {"type_name": u"\u6cf0\u5267", "type_id": "3"},
            {"type_name": u"\u65e5\u5267", "type_id": "18"},
            {"type_name": u"\u7535\u5f71", "type_id": "2"}
        ]
        try:
            res = requests.get(self.host, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            result['list'] = self.parseList(res.text)
        except:
            result['list'] = []
        return result

    def categoryContent(self, tid, pg, filter, extend):
        p_pg = str(pg)
        p_tid = str(tid)
        # /search/{pg}-5-time-{tid}---------.html
        url = f"{self.host}/search/{p_pg}-5-time-{p_tid}---------.html"
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

    def detailContent(self, ids):
        id = ids[0]
        url = f"{self.host}{id}" if id.startswith("/") else f"{self.host}/jumv/{id}.html"
        res = requests.get(url, headers=self.headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        title_node = soup.find('h1', class_='title')
        vod = {
            "vod_id": id,
            "vod_name": title_node.text.strip() if title_node else "",
            "vod_pic": self.extractPic(soup.find('img', class_='lazyload')),
            "vod_content": soup.find('span', class_='data').text.strip() if soup.find('span', class_='data') else "",
            "vod_play_from": "", "vod_play_url": ""
        }

        from_list, url_list = [], []
        play_tabs = soup.find_all('a', attrs={"data-toggle": "tab", "href": re.compile(r"#playlist")})
        play_lists = soup.find_all('ul', class_='myui-content__list')

        for i, ul in enumerate(play_lists):
            tab_name = play_tabs[i].text.strip() if i < len(play_tabs) else f"{i+1}"
            from_list.append(tab_name)
            # 1, 2, 3...
            links = [f"{a.text.strip()}${a['href']}" for a in ul.find_all('a')]
            links.reverse() 
            url_list.append("#".join(links))

        vod['vod_play_from'] = "$$$".join(from_list)
        vod['vod_play_url'] = "$$$".join(url_list)
        return {"list": [vod]}

    def searchContent(self, key, quick, pg=1):
        # searchword
        url = f"{self.host}/search.html?searchword={key}&page={pg}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            return {"list": self.parseList(res.text)}
        except:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        url = f"{self.host}{id}"
        res = requests.get(url, headers=self.headers, timeout=10)
        match = re.search(r'player_aaaa=(.*?)</script>', res.text)
        if match:
            try:
                config = json.loads(match.group(1))
                return {"parse": 1, "url": config.get('url', ''), "header": ""}
            except: pass
        return {"parse": 1, "url": url, "header": ""}

    def parseList(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        vods = []
        # 
        items = soup.select('.myui-vodlist__box, .myui-vodlist__item, .myui-vodlist li, li.col-lg-6, .myui-panel_bd li, .myui-vodlist__media li')
        for item in items:
            a = item.find('a', href=re.compile(r'/jumv/|/juid/'))
            if not a: continue
            
            pic = self.extractPic(a) or self.extractPic(item.find('img'))
            name_node = item.find(['h4', 'p', 'h3'], class_=re.compile(r'title|name'))
            name = name_node.text.strip() if name_node else (a.get('title') or a.text.strip())
            name = re.sub(r'\s+', ' ', name).strip()
            
            tag = item.find('span', class_='pic-tag')
            vods.append({
                "vod_id": a['href'],
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": tag.text if tag else ""
            })
        
        res_list, ids = [], []
        for v in vods:
            if v['vod_id'] not in ids:
                res_list.append(v)
                ids.append(v['vod_id'])
        return res_list

    def extractPic(self, tag):
        if not tag: return ""
        pic = tag.get('data-original') or tag.get('src') or ""
        if not pic and tag.get('style'):
            match = re.search(r'url\((.*?)\)', tag.get('style'))
            if match: pic = match.group(1).strip("'\"")
        if pic.startswith('//'): pic = "https:" + pic
        elif pic.startswith('/') and not pic.startswith('//'): pic = self.host + pic
        return pic