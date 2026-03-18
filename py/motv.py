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

    def isVideoStatus(self, url):
        return True

    def homeContent(self, filter):
        self.prepare()
        # 完全依照你提供的 HTML 結構補全與修正
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
            {"type_name": "鹹濕電台", "type_id": "169"},
            {"type_name": "三級倫理", "type_id": "53"}
        ]
        try:
            html = self.fetch(self.host).text
            rec_list = self.parse_list(html).get('list', [])
        except:
            rec_list = []
        return {'class': classes, 'list': rec_list, 'filters': {}}

    def categoryContent(self, tid, pg, filter, extend):
        self.prepare()
        url = f"{self.host}/vodtype/{tid}/page/{pg}/"
        html = self.fetch(url).text
        return self.parse_list(html)

    def parse_list(self, html):
        videos = []
        items = re.findall(r'class="movie-list-item".*?</a>', html, re.S)
        for item in items:
            link_m = re.search(r'href=[\'\"](/vod(?:play|detail)/(\d+)-.*?)[\'\"]', item)
            if not link_m: continue
            v_id = link_m.group(2)

            # 圖片抓取邏輯
            pic = ""
            pic_match = re.search(r'(?:data-original|data-src|src)=[\'\"](.*?)[\'\"]', item)
            if not pic_match:
                pic_match = re.search(r'background-image:\s*url\([\'\"]?(.*?)[\'\"]?\)', item)
            
            if pic_match:
                pic = pic_match.group(1).strip()
            
            # 標題清洗邏輯
            title_m = re.search(r'title=[\'\"](.*?)[\'\"]', item)
            name = title_m.group(1) if title_m else "Video"
            # 徹底移除 gt; &gt; 以及奇怪的開頭符號
            name = name.replace('gt;', '').replace('&gt;', '').replace('&quot;', '"')
            name = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', name).strip()
            
            if v_id and pic:
                vod_pic = pic if pic.startswith('http') else self.host + pic
                # 注入 Referer 破解圖片防盜鏈
                if "imagecdn" in vod_pic:
                    vod_pic = f"{vod_pic}@Referer={self.host}@User-Agent=Mozilla/5.0"
                
                videos.append({
                    "vod_id": v_id,
                    "vod_name": name,
                    "vod_pic": vod_pic,
                    "vod_remarks": ""
                })
        return {"list": videos}

    def detailContent(self, ids):
        self.prepare()
        v_id = ids[0]
        url = f"{self.host}/vodplay/{v_id}-1-1/"
        html = self.fetch(url).text
        
        title = "Video"
        title_m = re.search(r'<title>(.*?) - MOTV', html)
        if title_m: 
            title = title_m.group(1).split('-')[0].replace('gt;', '').replace('&gt;', '')
            title = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', title).strip()
        
        pic_m = re.search(r'(?:data-original|src)=[\'\"](.*?)[\'\"]|url\([\'\"]?(.*?)[\'\"]?\)', html)
        pic = (pic_m.group(1) or pic_m.group(2)).strip() if pic_m else ""
        if pic and "imagecdn" in pic:
            pic = f"{pic}@Referer={self.host}@User-Agent=Mozilla/5.0"
            
        vod = {
            "vod_id": v_id,
            "vod_name": title,
            "vod_pic": pic if pic.startswith('http') else self.host + pic,
            "vod_play_from": "MOTV",
            "vod_play_url": f"立即播放$/vodplay/{v_id}-1-1/"
        }
        return {"list": [vod]}

    def searchContent(self, key, quick):
        self.prepare()
        url = f"{self.host}/vodsearch/wd/{key}/"
        html = self.fetch(url).text
        return self.parse_list(html)

    def playerContent(self, flag, id, vipFlags):
        self.prepare()
        clean_id = id.strip()
        url = self.host + clean_id if clean_id.startswith('/') else f"{self.host}/{clean_id}"
        
        html = self.fetch(url).text
        match = re.search(r'player_aaaa\s*=\s*(.*?)</script>', html)
        if match:
            try:
                config = json.loads(match.group(1))
                play_url = config.get('url', '')
                return {
                    "parse": 0 if ('.m3u8' in play_url or '.mp4' in play_url) else 1,
                    "url": play_url,
                    "header": {
                        "User-Agent": "Mozilla/5.0",
                        "Referer": self.host
                    }
                }
            except: pass
        return {"parse": 1, "url": url}