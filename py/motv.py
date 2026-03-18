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
        classes = [
            {"type_name": "HD日本", "type_id": "51"}, {"type_name": "HD歐美", "type_id": "52"},
            {"type_name": "日本有碼", "type_id": "20"}, {"type_name": "日本無碼", "type_id": "50"},
            {"type_name": "國產原創", "type_id": "41"}, {"type_name": "成人動畫", "type_id": "29"}
        ]
        try:
            res = self.fetch(self.host, headers={"User-Agent": self.m_ua})
            return {'class': classes, 'list': self.parse_list(res.text).get('list', []), 'filters': {}}
        except: return {'class': classes, 'list': [], 'filters': {}}

    def categoryContent(self, tid, pg, filter, extend):
        self.prepare()
        pg = int(pg)
        url = f"{self.host}/vodshow/{tid}--------{pg}---/" if pg > 1 else f"{self.host}/vodtype/{tid}/"
        res = self.fetch(url, headers={"User-Agent": self.m_ua, "Referer": self.host})
        return self.parse_list(res.text)

    def parse_list(self, html):
        videos = []
        seen_ids = set()
        html = html.replace('\/', '/')
        items = re.findall(r'class=[\'\"](?:movie-list-item|vod-search-list|list-item|video-item).*?</a>', html, re.S)
        
        for item in items:
            link_m = re.search(r'href=[\'\"](/vod(?:play|detail)/(\d+)-.*?)[\'\"]', item)
            if not link_m: continue
            v_id = link_m.group(2)
            if v_id in seen_ids: continue
            seen_ids.add(v_id)

            # 名稱抓取邏輯 (三級保底)
            name = ""
            title_m = re.search(r'title=[\'\"](.*?)[\'\"]', item)
            if title_m: name = title_m.group(1)
            if not name or name.lower() == "video":
                alt_m = re.search(r'alt=[\'\"](.*?)[\'\"]', item)
                if alt_m: name = alt_m.group(1)
            if not name or name.lower() == "video":
                text_m = re.search(r'>(.*?)</a>', item, re.S)
                if text_m: name = re.sub(r'<.*?>', '', text_m.group(1)).strip()

            # 你的精確名稱清洗邏輯
            for junk in ['gt;', '&gt;', 'π', '影片信息', '&quot;']:
                name = name.replace(junk, '')
            name = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', name).strip()
            if not name: name = "Video"

            # 圖片解析 (針對懶加載強化)
            pic = ""
            pic_m = re.search(r'(?:data-original|data-src|src|data-lazyload|data-backup)=[\'\"](.*?)[\'\"]', item)
            if not pic_m:
                pic_m = re.search(r'url\([\'\"]?(.*?)[\'\"]?\)', item)
            
            if pic_m:
                pic = pic_m.group(1).strip()
                if not pic.startswith('http'):
                    pic = self.host + pic
                # 注入防盜鏈頭部
                pic = f"{pic}@Referer={self.host}@User-Agent={self.m_ua}"
            
            videos.append({"vod_id": v_id, "vod_name": name, "vod_pic": pic, "vod_remarks": ""})
        return {"list": videos}

    def detailContent(self, ids):
        self.prepare()
        v_id = ids[0]
        url = f"{self.host}/voddetail/{v_id}/"
        html = self.fetch(url, headers={"User-Agent": self.m_ua, "Referer": self.host}).text
        
        title = ""
        h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
        if h1_m:
            title = re.sub(r'<.*?>', '', h1_m.group(1)).strip()
        if not title or title.lower() == "video":
            title_m = re.search(r'<title>(.*?) - MOTV', html)
            if title_m: title = title_m.group(1).split('-')[0]

        title = title.replace('gt;', '').replace('&gt;', '').replace('π', '')
        title = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', title).strip()
        if not title: title = "Video"
        
        pic_m = re.search(r'(?:data-original|data-src|src)=[\'\"](.*?)[\'\"]|url\([\'\"]?(.*?)[\'\"]?\)', html)
        pic = (pic_m.group(1) or pic_m.group(2)).strip() if pic_m else ""
        if pic and not pic.startswith('http'): pic = self.host + pic
        if pic: pic = f"{pic}@Referer={self.host}@User-Agent={self.m_ua}"
            
        vod = {
            "vod_id": v_id, "vod_name": title, "vod_pic": pic,
            "vod_play_from": "MOTV", "vod_play_url": f"立即播放$/vodplay/{v_id}-1-1/"
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg=1):
        self.prepare()
        url = f"{self.host}/vodsearch/-------------/?wd={key}"
        html = self.fetch(url, headers={"User-Agent": self.m_ua, "Referer": self.host}).text
        return self.parse_list(html)

    def detailContent(self, ids):
        self.prepare()
        v_id = ids[0]
        url = f"{self.host}/voddetail/{v_id}/"
        html = self.fetch(url, headers={"User-Agent": self.m_ua}).text
        
        # 詳情頁標題與圖片
        title = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S).group(1) if '<h1' in html else "Video"
        title = re.sub(r'<.*?>', '', title).replace('&gt;', '').strip()
        
        pic = ""
        pic_m = re.search(r'(?:data-original|src)=[\'\"](.*?)[\'\"]', html)
        if pic_m:
            pic = pic_m.group(1).replace('\/', '/')
            if not pic.startswith('http'): pic = self.host + pic

        # 回歸單線路，確保穩定播放
        vod = {
            "vod_id": v_id, "vod_name": title, "vod_pic": pic,
            "vod_play_from": "MOTV",
            "vod_play_url": f"播放$/vodplay/{v_id}-1-1/"
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg=1):
        self.prepare()
        url = f"{self.host}/vodsearch/-------------/?wd={key}"
        res = self.fetch(url, headers={"User-Agent": self.m_ua})
        return self.parse_list(res.text)

    def playerContent(self, flag, id, vipFlags):
        self.prepare()
        play_url = self.host + id if id.startswith('/') else f"{self.host}/{id}"
        headers = {"User-Agent": self.m_ua, "Referer": self.host}
        res = self.fetch(play_url, headers=headers)
        html = res.text
        
        # 暴力搜索 m3u8 位址，這能抓到 CLUB-859 的 multicdn 線路
        matches = re.findall(r'[\'\"](https?[:\/]+[^\'\" ]+?\.m3u8[^\'\" ]*)[\'\"]', html)
        for m in matches:
            final_url = m.replace('\/', '/').replace('&amp;', '&')
            return {"parse": 0, "url": final_url, "header": headers}
        
        # 備用方案：JSON 提取
        url_raw = re.search(r'[\'\"]url[\'\"]\s*:\s*[\'\"](.*?)[\'\"]', html)
        if url_raw:
            return {"parse": 0, "url": url_raw.group(1).replace('\/', '/'), "header": headers}

        return {"parse": 1, "url": play_url}