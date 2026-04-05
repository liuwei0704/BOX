import sys
import re
import requests
from bs4 import BeautifulSoup

class Spider():
    def getDependence(self):
        return ["requests", "beautifulsoup4"]

    def getName(self):
        return "爾絲短劇"

    def init(self, extend=""):
        self.host = "https://www.ersidj.cc"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Referer": self.host
        }

    def homeContent(self, filter):
        # 完整分類列表 (包含更多隱藏分類)
        result = {'class': [
            {"type_name": "全部", "type_id": "uu"},
            {"type_name": "婚姻", "type_id": "HxxhSb"},
            {"type_name": "擦邊", "type_id": "SkwGG1"},
            {"type_name": "重生", "type_id": "RvCRkA"},
            {"type_name": "宮廷", "type_id": "9jPYk"},
            {"type_name": "權謀", "type_id": "xTPSjV"},
            {"type_name": "奇幻", "type_id": "5k18R7"},
            {"type_name": "總裁", "type_id": "NkSrxN"},
            {"type_name": "戰爭", "type_id": "1NNbCJ"},
            {"type_name": "懸疑", "type_id": "xWNBTh"},
            {"type_name": "搞笑", "type_id": "5Ap1kr"},
            {"type_name": "豪門", "type_id": "VT177I"},
            {"type_name": "家庭", "type_id": "bQ5N5M"},
            {"type_name": "勵志", "type_id": "yPGIBa"},
            {"type_name": "甜寵", "type_id": "rxypaw"},
            {"type_name": "恐怖", "type_id": "TNbA55"},
            {"type_name": "熱血", "type_id": "TRUUND"},
            {"type_name": "都市", "type_id": "GXYuRA"},
            {"type_name": "復仇", "type_id": "CJyBHx"},
            {"type_name": "穿越", "type_id": "rV8818"},
            {"type_name": "情感", "type_id": "9x718j"}
        ]}

        # 完整篩選配置 (對應 URL: /shuku/標籤,分類,頻道,年代,狀態,排序,頁碼.html)
        filters = {}
        filter_config = [
            {"key": "tag", "name": "標籤", "value": [
                {"n": "全部", "v": "S"}, {"n": "逆襲", "v": "900688nqS"}, {"n": "都市", "v": "90sq5r02S"}, 
                {"n": "甜寵", "v": "751p5on0S"}, {"n": "愛情", "v": "723160p5S"}, {"n": "情感", "v": "60p5611sS"},
                {"n": "復仇", "v": "590q4rp7S"}, {"n": "豪門", "v": "8p6n95r8S"}, {"n": "家庭", "v": "5oo65rnqS"}
            ]},
            {"key": "channel", "name": "頻道", "value": [{"n": "全部", "v": "uu"}, {"n": "男頻", "v": "male"}, {"n": "女頻", "v": "female"}]},
            {"key": "year", "name": "年代", "value": [{"n": "全部", "v": ""}, {"n": "古代", "v": "1"}, {"n": "現代", "v": "2"}]},
            {"key": "state", "name": "狀態", "value": [{"n": "全部", "v": "0"}, {"n": "完結", "v": "2"}, {"n": "連載", "v": "1"}]},
            {"key": "sort", "name": "排序", "value": [
                {"n": "最新", "v": "0"}, {"n": "推薦", "v": "1"}, {"n": "最近更新", "v": "2"}, 
                {"n": "周點擊", "v": "3"}, {"n": "月點擊", "v": "4"}, {"n": "點擊量", "v": "6"}
            ]}
        ]
        
        for item in result['class']:
            filters[item['type_id']] = filter_config
            
        result['filters'] = filters
        return result

    def homeVideoContent(self):
        return self.categoryContent("uu", 1, False, {})

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        # 獲取篩選參數
        tag = extend.get('tag', 'S')
        cate = tid
        channel = extend.get('channel', 'uu')
        year = extend.get('year', '')
        state = extend.get('state', '0')
        sort = extend.get('sort', '0')
        
        # 構造 URL
        url = f"{self.host}/shuku/{tag},{cate},{channel},{year},{state},{sort},{pg}.html"
        
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            result['list'] = self.parse_vod_list(soup)
            result['page'] = pg
            result['pagecount'] = 20
        except:
            result['list'] = []
        return result

    def parse_vod_list(self, soup):
        vod_list = []
        # 尋找所有劇集連結
        items = soup.find_all('a', href=re.compile(r'/content/[a-zA-Z0-9]+\.html'))
        for item in items:
            href = item.get('href', '')
            vod_id = href.replace('/content/', '').replace('.html', '')
            
            # 優先從圖片 alt 或 font-bold 找標題
            img_el = item.find('img')
            name_el = item.select_one('.font-bold')
            name = name_el.get_text(strip=True) if name_el else (img_el.get('alt', '') if img_el else "")
            
            if not name: continue
            
            pic = img_el.get('data-lazy') or img_el.get('src') or ""
            if pic.startswith('/'): pic = self.host + pic
            
            remark = item.select_one('.bg-surface').get_text(strip=True) if item.select_one('.bg-surface') else ""
            
            vod_list.append({
                "vod_id": vod_id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        
        # 簡單去重
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
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            title = soup.select_one('h2.font-bold').get_text(strip=True) if soup.select_one('h2.font-bold') else "短劇播放"
            img_el = soup.select_one('img[data-lazy]')
            pic = img_el['data-lazy'] if img_el else ""
            if pic.startswith('/'): pic = self.host + pic

            def get_playlist(line):
                eps = [f"第{i}集$/play/{vod_id}/{i}?line={line}" for i in range(1, 101)]
                return "#".join(eps)

            play_from = ["線路1", "線路2", "線路3"]
            play_url = [get_playlist(1), get_playlist(2), get_playlist(3)]

            vod = {
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "type_name": "短劇",
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_url)
            }
            return {"list": [vod]}
        except:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        result = {'list': []}
        # 使用你測試 OK 的 POST 與 pg=1 邏輯
        search_url = f"{self.host}/searchlist/"
        try:
            payload = {'keyword': key, 'pg': 1}
            res = requests.post(search_url, headers=self.headers, data=payload, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            result['list'] = self.parse_vod_list(soup)
        except:
            pass
        return result

    def playerContent(self, flag, id, vipFlags):
        # 移除可能存在的 line 重複拼接，確保 URL 格式正確
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