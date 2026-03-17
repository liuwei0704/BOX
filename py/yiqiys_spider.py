import sys, requests, re, json
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote

try:
    from base.spider import Spider as BaseSpider
except:
    class BaseSpider:
        def __init__(self): pass

class Spider(BaseSpider):
    def getName(self): return "一起影視"
    def init(self, extend=""):
        self.host = "https://www.yiqiys.com"
        self.header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36","Referer":self.host}

    def homeContent(self, is_filter):
        f_common = [
            {"key":"by","name":"排序","value":[{"n":"熱門","v":"hits"},{"n":"時間","v":"time"},{"n":"評分","v":"score"}]},
            {"key":"lang","name":"語言","value":[{"n":"全部","v":""},{"n":"國語","v":"國語"},{"n":"粵語","v":"粵語"},{"n":"英語","v":"英語"},{"n":"韓語","v":"韓語"},{"n":"日語","v":"日語"}]},
            {"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"}]}
        ]
        f_movie = [{"key":"tid","name":"分類","value":[{"n":"電影全部","v":"1"},{"n":"動作片","v":"6"},{"n":"喜劇片","v":"7"},{"n":"愛情片","v":"8"},{"n":"科幻片","v":"9"},{"n":"恐怖片","v":"10"},{"n":"劇情片","v":"11"}]},{"key":"area","name":"地區","value":[{"n":"全部","v":""},{"n":"大陸","v":"大陸"},{"n":"香港","v":"香港"},{"n":"台灣","v":"台灣"},{"n":"美國","v":"美國"},{"n":"韓國","v":"韓國"}]}] + f_common
        f_drama = [{"key":"tid","name":"分類","value":[{"n":"電視劇全部","v":"2"},{"n":"國產劇","v":"12"},{"n":"港台劇","v":"13"},{"n":"歐美劇","n":"14"},{"n":"日韓劇","v":"15"},{"n":"海外劇","v":"16"}]},{"key":"area","name":"地區","value":[{"n":"全部","v":""},{"n":"大陸","v":"大陸"},{"n":"香港","v":"香港"},{"n":"台灣","v":"台灣"},{"n":"韓國","v":"韓國"}]}] + f_common
        return {'class': [{"type_name":"電影","type_id":"1"},{"type_name":"電視劇","type_id":"2"},{"type_name":"綜藝","type_id":"3"},{"type_name":"動漫","type_id":"4"}],'filters': {"1":f_movie, "2":f_drama}}

    def homeVideoContent(self):
        return self.categoryContent("1", "1", False, {})

    def categoryContent(self, tid, pg, is_filter, extend):
        res = {"list": [], "page": int(pg), "pagecount": int(pg)}
        try:
            tid_val = str(extend.get("tid", tid))
            area_val = quote(str(extend.get("area", "")))
            by_val = str(extend.get("by", "hits"))
            lang_val = quote(str(extend.get("lang", "")))
            year_val = str(extend.get("year", ""))
            # URL結構: {tid}-{area}-{by}-{class}-{lang}-{letter}-{level}-{tag}-{page}-{area_id}-{short}-{year}
            p = [tid_val, area_val, by_val, "", lang_val, "", "", "", str(pg), "", "", year_val]
            url = f"{self.host}/show/{'-'.join(p)}.html"
            
            r = requests.get(url, headers=self.header, timeout=10)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 分頁解析 (1/39)
            page_info = soup.select_one('.stui-page__item li.active.num a')
            if page_info:
                res["pagecount"] = int(page_info.text.split('/')[-1])

            items = soup.select('.stui-vodlist li')
            for item in items:
                a = item.find('a', class_='stui-vodlist__thumb')
                if not a: continue
                res['list'].append({
                    "vod_id": a.get('href'),
                    "vod_name": a.get('title') or "未知",
                    "vod_pic": a.get('data-original') or a.get('src') or "",
                    "vod_remarks": item.select_one('.pic-text').text.strip() if item.select_one('.pic-text') else ""
                })
        except: pass
        return res

    def detailContent(self, ids):
        try:
            r = requests.get(f"{self.host}{ids[0]}", headers=self.header, timeout=10)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, 'html.parser')
            vod = {"vod_id": ids[0], "vod_name": soup.find('h1').text.strip() if soup.find('h1') else "未知", "vod_play_from": "", "vod_play_url": ""}
            pic_tag = soup.select_one('.stui-content__thumb img')
            pic = pic_tag.get('data-original') or pic_tag.get('src') if pic_tag else ""
            if pic.startswith('//'): pic = "https:" + pic
            elif pic.startswith('/') and not pic.startswith('//'): pic = self.host + pic
            vod["vod_pic"] = pic
            
            play_lists = []
            uls = soup.select('.stui-content__playlist')
            for ul in uls:
                links = [f"{a.text}${a.get('href')}" for a in ul.select('li a')]
                play_lists.append("#".join(links))
            
            from_names = [a.text.strip() for a in soup.select('.nav-tabs li a')]
            if not from_names: from_names = [f"線路{i+1}" for i in range(len(play_lists))]
            
            vod["vod_play_from"] = "$$$".join(from_names[:len(play_lists)])
            vod["vod_play_url"] = "$$$".join(play_lists)
            return {"list": [vod]}
        except: return {"list": []}

    def searchContent(self, key, quick):
        return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        try:
            url = f"{self.host}{id}"
            import base64
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = "utf-8"
            match = re.search(r'var player_aaaa=(.*?)<', res.text)
            if match:
                config = json.loads(match.group(1))
                play_url = config.get('url', '')
                if not play_url.startswith('http'):
                    try:
                        play_url = unquote(base64.b64decode(play_url).decode('utf-8'))
                    except: pass
                return {"parse": 1, "url": play_url, "header": {"User-Agent": self.header["User-Agent"], "Referer": url}}
            return {"parse": 1, "url": url}
        except: return {"parse": 1, "url": id}

    def localProxy(self, param):
        return [200, "video/MP4", ""]