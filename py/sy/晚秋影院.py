import requests
from base.spider import Spider
import json
import re

class Spider(Spider):
    host = "https://www.jjcsyl.com"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.jjcsyl.com/"
    }

    def getName(self): return "晚秋影院"
    def init(self, extend=""): pass

    def homeContent(self, filter):
        # 修正分类 ID，确保与站点 API 对应
        classes = [{"type_name": "电影", "type_id": "1"}, {"type_name": "电视剧", "type_id": "2"}, {"type_name": "综艺", "type_id": "3"}, {"type_name": "动漫", "type_id": "4"}, {"type_name": "短剧", "type_id": "36"}]
        return {"class": classes}

    def homeVideoContent(self):
        # 重点：定义首页推荐，展示最新更新的视频
        return self.categoryContent(tid="", pg=1, filter=False, extend={})

    def categoryContent(self, tid, pg, filter, extend):
        # 核心：AJAX API。如果没有 tid 则获取全站最新更新
        tid_str = f"&tid={tid}" if tid else ""
        api_url = f"{self.host}/index.php/ajax/data?mid=1{tid_str}&page={pg}&limit=30"
        try:
            r = requests.get(api_url, headers=self.header, timeout=10)
            data = r.json()
            vod_list = []
            for item in data.get('list', []):
                pic = item.get('vod_pic', '')
                if pic.startswith('//'): pic = "https:" + pic
                elif pic.startswith('/'): pic = self.host + pic
                
                vod_list.append({
                    "vod_id": str(item.get('vod_id')),
                    "vod_name": item.get('vod_name'),
                    "vod_pic": pic,
                    "vod_remarks": item.get('vod_remarks', '') # 完美的角标
                })
            return {"page": pg, "pagecount": data.get('pagecount', 1), "limit": 30, "total": data.get('total'), "list": vod_list}
        except: return {"list": []}

    def detailContent(self, ids):
        # 详情页逻辑保持暴力容错，确保播放通畅
        from lxml import etree
        url = f"{self.host}/voddetail/{ids[0]}.html"
        r = requests.get(url, headers=self.header, timeout=10); r.encoding = 'utf-8'
        html = etree.HTML(r.text)
        
        title_nodes = html.xpath("//title/text()")
        title = title_nodes[0].split('免费')[0].strip('《》') if title_nodes else "未知"
        
        # 详情页图片优先级
        pic = html.xpath("//div[contains(@class,'post')]//img/@src | //img[contains(@class,'lazyload')]/@data-src | //img[contains(@src,'upload')]/@src")[0]
        if pic.startswith("/"): pic = self.host + pic
        
        vod = {
            "vod_id": ids[0], "vod_name": title, "vod_pic": pic,
            "vod_content": "".join(html.xpath("//div[contains(@id,'desc') or contains(@class,'content')]//text()")).strip()[:100]
        }
        
        play_from, play_url = [], []
        froms = html.xpath("//div[contains(@class,'playlist-top')]//li/a/text() | //div[contains(@class,'playlist-top')]//span/text()")
        urls_divs = html.xpath("//ul[contains(@class,'playlist-content')]")
        for i, ul in enumerate(urls_divs):
            source_name = froms[i] if i < len(froms) else f"线路{i+1}"
            links = [f"{a.xpath('./text()')[0]}${a.xpath('./@href')[0]}" for a in ul.xpath(".//a")]
            if links:
                play_from.append(source_name)
                play_url.append("#".join(links))
        
        vod["vod_play_from"] = "$$$".join(play_from)
        vod["vod_play_url"] = "$$$".join(play_url)
        return {"list": [vod]}

    def searchContent(self, key, quick, pg=1):
        # 搜索页同样可以利用 API (mid=1 为视频)
        api_url = f"{self.host}/index.php/ajax/data?mid=1&wd={key}&page={pg}&limit=30"
        try:
            r = requests.get(api_url, headers=self.header, timeout=10)
            data = r.json()
            vod_list = []
            for item in data.get('list', []):
                vod_list.append({
                    "vod_id": str(item.get('vod_id')),
                    "vod_name": item.get('vod_name'),
                    "vod_pic": item.get('vod_pic'),
                    "vod_remarks": item.get('vod_remarks', '')
                })
            return {"list": vod_list}
        except: return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        r = requests.get(f"{self.host}{id}", headers=self.header, timeout=10)
        match = re.search(r'var player_aaaa=(.*?)</script>', r.text)
        if match:
            config = json.loads(match.group(1))
            return {"parse": 1, "url": config['url']}
        return {"parse": 1, "url": ""}