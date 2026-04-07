import sys
import re
import requests
from bs4 import BeautifulSoup

class Spider():
    def getDependence(self):
        return ["requests", "beautifulsoup4"]

    def getName(self):
        return "巨魚短劇[適配爾絲解析]"

    def init(self, extend=""):
        self.host = "https://hk.juyu.org"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
            "Referer": self.host + "/",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8"
        }

    def homeContent(self, filter):
        # 定義完整的分類數據
        cate_list = [
            {"n": "全部", "v": "0"}, {"n": "權謀", "v": "r9JP"}, {"n": "穿越", "v": "D6MG"},
            {"n": "愛情", "v": "zRPx"}, {"n": "都市", "v": "ER2"}, {"n": "婚姻", "v": "QG64"},
            {"n": "勵志", "v": "QG14"}, {"n": "逆襲", "v": "ZMO"}, {"n": "玄幻", "v": "VmR"},
            {"n": "奇幻", "v": "63V"}, {"n": "戰爭", "v": "wXLO"}, {"n": "搞笑", "v": "eM6"},
            {"n": "重生", "v": "ZGLb"}, {"n": "總裁", "v": "OjAB"}, {"n": "家庭", "v": "wXel"},
            {"n": "宮廷", "v": "QG4e"}, {"n": "冒險", "v": "r9K2"}, {"n": "恐怖", "v": "QGpV"},
            {"n": "情感", "v": "kKqE"}, {"n": "擦邊", "v": "4OJN"}, {"n": "熱血", "v": "bKbm"}
        ]
        order_list = [
            {"n": "最新", "v": "0"}, {"n": "推薦", "v": "1"}, {"n": "周點擊", "v": "2"},
            {"n": "最多訂閱", "v": "3"}, {"n": "年點擊", "v": "4"}, {"n": "日點擊", "v": "5"},
            {"n": "隨機", "v": "6"}, {"n": "點擊量", "v": "7"}, {"n": "最近更新", "v": "8"}, {"n": "月點擊", "v": "9"}
        ]

        result = {
            'class': [
                {"type_name": "全部", "type_id": "and"},
                {"type_name": "男頻", "type_id": "male"},
                {"type_name": "女頻", "type_id": "female"}
            ],
            'filters': {
                "and": [{"key": "cate", "name": "分類", "value": cate_list}, {"key": "order", "name": "排序", "value": order_list}],
                "male": [{"key": "cate", "name": "分類", "value": cate_list}, {"key": "order", "name": "排序", "value": order_list}],
                "female": [{"key": "cate", "name": "分類", "value": cate_list}, {"key": "order", "name": "排序", "value": order_list}]
            }
        }
        return result

    def homeVideoContent(self):
        return self.categoryContent("and", 1, False, {})

    def categoryContent(self, tid, pg, filter, extend):
        # 依照規則拼接 URL
        cate = extend.get('cate', '0')
        order = extend.get('order', '0')
        channel = tid  # and, male, 或 female
        year = extend.get('year', '0')
        state = extend.get('state', '0')
        tag = "N"
        
        url = f"{self.host}/category/{cate},{order},{channel},{year},{state},{tag},{pg}.html"
        
        result = {'list': [], 'page': pg, 'pagecount': 99}
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            result['list'] = self.parse_vod_list(soup)
        except:
            pass
        return result

    def parse_vod_list(self, soup):
        vod_list = []
        items = soup.select('div.inline-flex')
        for item in items:
            a_tag = item.select_one('a[href^="/content/"]')
            if not a_tag: continue
            href = a_tag.get('href', '')
            vod_id = href.replace('/content/', '').replace('.html', '')
            img_el = item.select_one('img')
            name = img_el.get('alt', '') if img_el else "未知"
            pic = img_el.get('data-lazy') or img_el.get('src') or ""
            if pic.startswith('/'): pic = self.host + pic
            remark_el = item.select_one('.bg-surface')
            remark = remark_el.get_text(strip=True) if remark_el else ""
            vod_list.append({"vod_id": vod_id, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
        return vod_list

    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            url = f"{self.host}/content/{vod_id}.html"
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            title = soup.select_one('h2.font-bold').get_text(strip=True) if soup.select_one('h2.font-bold') else "短劇播放"
            img_el = soup.select_one('img[data-lazy]')
            pic = img_el['data-lazy'] if img_el else ""
            if pic.startswith('/'): pic = self.host + pic

            def get_playlist(line):
                # 爾絲短劇播放路由通常為 /play/{id}/{episode}?line={line}
                eps = [f"第{i}集$/play/{vod_id}/{i}?line={line}" for i in range(1, 101)]
                return "#".join(eps)

            play_from = ["官方線路1", "備用線路2", "備用線路3"]
            play_url = [get_playlist("g0"), get_playlist("g1"), get_playlist("g2")]

            vod = {
                "vod_id": vod_id, "vod_name": title, "vod_pic": pic, "type_name": "短劇",
                "vod_play_from": "$$$".join(play_from), "vod_play_url": "$$$".join(play_url)
            }
            return {"list": [vod]}
        except:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        result = {'list': []}
        search_url = f"{self.host}/findvods/"
        try:
            payload = {'keyword': key}
            res = requests.post(search_url, headers=self.headers, data=payload, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            result['list'] = self.parse_vod_list(soup)
        except:
            pass
        return result

    def playerContent(self, flag, id, vipFlags):
        # 1. 確保播放頁 URL 完整且帶有 source 參數 (對應爾絲的 line)
        play_url = self.host + id if id.startswith('/') else id
        if 'source=' not in play_url:
            play_url += ('&' if '?' in play_url else '?') + "source=1"

        # 2. 使用 parse: 1 調用 APP 的 Webview 解析
        return {
            "parse": 1,
            "url": play_url,
            "header": {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
                "Referer": self.host + "/",
                "Origin": self.host,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8"
            }
        }