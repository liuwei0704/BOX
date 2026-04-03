import sys
import re
import requests
import time
import random
from bs4 import BeautifulSoup

class Spider():
    def getDependence(self):
        return ["requests", "beautifulsoup4"]

    def getName(self):
        return "爾絲短劇(過檢測版)"

    def init(self, extend=""):
        self.host = "https://www.ersidj.cc"
        # 使用 Session 自動管理 Cookies
        self.session = requests.Session()
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ]

    def get_headers(self):
        return {
            "User-Agent": random.choice(self.ua_list),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": self.host + "/",
            "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

    def homeContent(self, filter):
        result = {'class': [
            {"type_name": "全部", "type_id": "uu"},
            {"type_name": "婚姻", "type_id": "HxxhSb"},
            {"type_name": "擦邊", "type_id": "SkwGG1"},
            {"type_name": "重生", "type_id": "RvCRkA"},
            {"type_name": "宮廷", "type_id": "9jPYk"},
            {"type_name": "權謀", "type_id": "xTPSjV"},
            {"type_name": "奇幻", "type_id": "5k18R7"},
            {"type_name": "總裁", "type_id": "NkSrxN"},
            {"type_name": "都市", "type_id": "GXYuRA"},
            {"type_name": "復仇", "type_id": "CJyBHx"}
        ]}

        filters = {}
        filter_config = [
            {"key": "tag", "name": "標籤", "value": [{"n": "全部", "v": "S"}, {"n": "逆襲", "v": "900688nqS"}, {"n": "都市", "v": "90sq5r02S"}]},
            {"key": "channel", "name": "頻道", "value": [{"n": "全部", "v": "uu"}, {"n": "男頻", "v": "male"}, {"n": "女頻", "v": "female"}]},
            {"key": "sort", "name": "排序", "value": [{"n": "最新", "v": "0"}, {"n": "推薦", "v": "1"}, {"n": "點擊量", "v": "6"}]}
        ]
        for item in result['class']:
            filters[item['type_id']] = filter_config
        result['filters'] = filters
        return result

    def homeVideoContent(self):
        return self.categoryContent("uu", 1, False, {})

    def categoryContent(self, tid, pg, filter, extend):
        # 增加隨機休眠，減少被標記風險
        time.sleep(random.uniform(0.5, 1.5))
        
        result = {}
        tag = extend.get('tag', 'S')
        cate = tid
        channel = extend.get('channel', 'uu')
        year = extend.get('year', '')
        state = extend.get('state', '0')
        sort = extend.get('sort', '0')
        
        url = f"{self.host}/shuku/{tag},{cate},{channel},{year},{state},{sort},{pg}.html"
        
        try:
            res = self.session.get(url, headers=self.get_headers(), timeout=15)
            # 如果還是被封，嘗試訪問首頁拿 Cookie 再回來
            if res.status_code == 403:
                self.session.get(self.host, headers=self.get_headers())
                res = self.session.get(url, headers=self.get_headers(), timeout=15)
            
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            result['list'] = self.parse_vod_list(soup)
            result['page'] = pg
            result['pagecount'] = 10  # 降低分頁數，避免自動加載過快
        except:
            result['list'] = []
        return result

    def parse_vod_list(self, soup):
        vod_list = []
        items = soup.find_all('a', href=re.compile(r'/content/[a-zA-Z0-9]+\.html'))
        for item in items:
            href = item.get('href', '')
            vod_id = href.replace('/content/', '').replace('.html', '')
            img_el = item.find('img')
            name_el = item.select_one('.font-bold')
            name = name_el.get_text(strip=True) if name_el else (img_el.get('alt', '') if img_el else "")
            if not name: continue
            pic = img_el.get('data-lazy') or img_el.get('src') or ""
            if pic.startswith('/'): pic = self.host + pic
            remark = item.select_one('.bg-surface').get_text(strip=True) if item.select_one('.bg-surface') else ""
            vod_list.append({"vod_id": vod_id, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
        
        unique_list = []
        seen = set()
        for v in vod_list:
            if v['vod_id'] not in seen:
                unique_list.append(v)
                seen.add(v['vod_id'])
        return unique_list

    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            url = f"{self.host}/content/{vod_id}.html"
            res = self.session.get(url, headers=self.get_headers(), timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            title = soup.select_one('h2.font-bold').get_text(strip=True) if soup.select_one('h2.font-bold') else "短劇"
            img_el = soup.select_one('img[data-lazy]')
            pic = img_el['data-lazy'] if img_el else ""
            if pic.startswith('/'): pic = self.host + pic

            def get_playlist(line):
                return "#".join([f"第{i}集$/play/{vod_id}/{i}?line={line}" for i in range(1, 101)])

            play_from = ["線路1", "線路2", "線路3"]
            play_url = [get_playlist(1), get_playlist(2), get_playlist(3)]

            return {"list": [{
                "vod_id": vod_id, "vod_name": title, "vod_pic": pic, "type_name": "短劇",
                "vod_play_from": "$$$".join(play_from), "vod_play_url": "$$$".join(play_url)
            }]}
        except:
            return {"list": []}

    def searchContent(self, key, quick):
        time.sleep(2) # 搜尋強烈建議延遲
        search_url = f"{self.host}/searchlist/"
        try:
            payload = {'keyword': key, 'pg': 1}
            # 搜尋通常檢查更嚴格，使用 POST 時必須帶上完整的 Referer
            h = self.get_headers()
            h["Origin"] = self.host
            res = self.session.post(search_url, headers=h, data=payload, timeout=15)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            return {'list': self.parse_vod_list(soup)}
        except:
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        play_url = self.host + id if id.startswith('/') else id
        return {
            "parse": 1,
            "url": play_url,
            "header": {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                "Referer": self.host + "/",
                "Origin": self.host
            }
        }