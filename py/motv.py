import sys
import re
import json
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "MOTV"

    def init(self, extend=""):
        self.host = "https://motv.app"

    def prepare(self):
        if not hasattr(self, 'host'):
            self.host = "https://motv.app"
        self.host = self.host.strip()
        self.m_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    def isVideoStatus(self, url):
        return True

    def homeContent(self, filter):
        self.prepare()
        # 根據導航列完整補齊所有分類
        classes = [
            {"type_name": "HD日本", "type_id": "51"},
            {"type_name": "HD歐美", "type_id": "52"},
            {"type_name": "日本有碼", "type_id": "20"},
            {"type_name": "日本無碼", "type_id": "50"},
            {"type_name": "歐美風情", "type_id": "25"},
            {"type_name": "國產原創", "type_id": "41"},
            {"type_name": "成人動畫", "type_id": "29"},
            {"type_name": "水果AV", "type_id": "35"},
            {"type_name": "色情情燴", "type_id": "30"},
            {"type_name": "經典四級", "type_id": "47"},
            {"type_name": "鹹濕電台", "type_id": "169"}
        ]
        try:
            res = self.fetch(self.host, headers={"User-Agent": self.m_ua})
            return {'class': classes, 'list': self.parse_list(res.text).get('list', []), 'filters': {}}
        except: return {'class': classes, 'list': [], 'filters': {}}

    def categoryContent(self, tid, pg, filter, extend):
        self.prepare()
        pg = int(pg)
        # 處理分類路由，支持分頁
        url = f"{self.host}/vodshow/{tid}--------{pg}---/" if pg > 1 else f"{self.host}/vodtype/{tid}/"
        res = self.fetch(url, headers={"User-Agent": self.m_ua, "Referer": self.host})
        return self.parse_list(res.text)

    def parse_list(self, html):
        videos = []
        seen_ids = set()
        html = html.replace('\/', '/')
        
        # 1. 抓取包含連結的區塊
        items = re.findall(r'<(?:div|a)[^>]*?href=[\'\"](/vod(?:play|detail)/(\d+)-.*?)[\'\"][^>]*?>.*?</(?:div|a)>', html, re.S)
        if not items:
            items = re.findall(r'href=[\'\"](/vod(?:play|detail)/(\d+)-.*?)[\'\"]', html)
        
        for match in items:
            if isinstance(match, tuple):
                link, v_id = match[0], match[1]
            else: continue
                
            if v_id in seen_ids: continue
            seen_ids.add(v_id)

            # 定位上下文捕捉圖片與名稱
            pos = html.find(link)
            context = html[max(0, pos-250):pos+650]

            # 名稱清洗邏輯
            name = ""
            name_m = re.search(r'title=[\'\"](.*?)[\'\"]', context)
            if name_m: name = name_m.group(1)
            if not name or name.lower() == "video":
                alt_m = re.search(r'alt=[\'\"](.*?)[\'\"]', context)
                if alt_m: name = alt_m.group(1)
            
            for junk in ['gt;', '&gt;', 'π', '影片信息', '&quot;']:
                name = name.replace(junk, '')
            name = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', name).strip()
            if not name: name = f"影片{v_id}"

            # 圖片解析 (Lazyload 強化)
            pic = ""
            pic_m = re.search(r'(?:data-original|data-src|src|data-lazyload)=[\'\"](.*?)[\'\"]', context)
            if pic_m:
                pic = pic_m.group(1).strip()
                if pic.startswith('//'): pic = "https:" + pic
                elif not pic.startswith('http'): pic = self.host + (pic if pic.startswith('/') else '/' + pic)
                pic = f"{pic}@Referer={self.host}"
            
            videos.append({"vod_id": v_id, "vod_name": name, "vod_pic": pic, "vod_remarks": ""})
            
        return {"list": videos}

    def detailContent(self, ids):
        self.prepare()
        v_id = ids[0]
        url = f"{self.host}/voddetail/{v_id}/"
        html = self.fetch(url, headers={"User-Agent": self.m_ua, "Referer": self.host}).text
        
        title = ""
        h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
        if h1_m: title = re.sub(r'<.*?>', '', h1_m.group(1)).strip()
        title = title.replace('gt;', '').replace('&gt;', '').replace('π', '')
        title = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', title).strip()
        
        pic = ""
        pic_m = re.search(r'(?:data-original|src)=[\'\"](.*?)[\'\"]', html)
        if pic_m:
            pic = pic_m.group(1).replace('\/', '/')
            if not pic.startswith('http'): pic = self.host + pic
            pic = f"{pic}@Referer={self.host}"

        vod = {
            "vod_id": v_id, "vod_name": title, "vod_pic": pic,
            "vod_play_from": "MOTV",
            "vod_play_url": f"立即播放$/vodplay/{v_id}-1-1/"
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg=1):
        self.prepare()
        url = f"{self.host}/vodsearch/-------------/?wd={key}"
        res = self.fetch(url, headers={"User-Agent": self.m_ua, "Referer": self.host})
        return self.parse_list(res.text)

    def playerContent(self, flag, id, vipFlags):
        self.prepare()
        play_url = self.host + id if id.startswith('/') else f"{self.host}/{id}"
        headers = {"User-Agent": self.m_ua, "Referer": self.host}
        res = self.fetch(play_url, headers=headers)
        html = res.text
        
        # 暴力破解 m3u8 位址 (含 multicdn.top)
        matches = re.findall(r'[\'\"](https?[:\/]+[^\'\" ]+?\.m3u8[^\'\" ]*)[\'\"]', html)
        for m in matches:
            return {"parse": 0, "url": m.replace('\/', '/').replace('&amp;', '&'), "header": headers}
        
        # 備用 JSON 提取
        url_raw = re.search(r'[\'\"]url[\'\"]\s*:\s*[\'\"](.*?)[\'\"]', html)
        if url_raw:
            return {"parse": 0, "url": url_raw.group(1).replace('\/', '/'), "header": headers}

        return {"parse": 1, "url": play_url}