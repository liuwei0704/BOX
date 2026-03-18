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
            html = self.fetch(self.host, headers={"User-Agent": "Mozilla/5.0"}).text
            rec_list = self.parse_list(html).get('list', [])
        except:
            rec_list = []
        return {'class': classes, 'list': rec_list, 'filters': {}}

    def categoryContent(self, tid, pg, filter, extend):
        self.prepare()
        pg = int(pg)
        
        # 優先使用實測有效的橫槓篩選路徑
        if pg <= 1:
            url = f"{self.host}/vodtype/{tid}/"
            headers = {"User-Agent": "Mozilla/5.0"}
        else:
            # 精確對齊用戶提供的路徑：/vodshow/tid--------pg---/
            url = f"{self.host}/vodshow/{tid}--------{pg}---/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": f"{self.host}/vodtype/{tid}/"
            }

        res = self.fetch(url, headers=headers)
        html = res.text
        
        # 如果橫槓路徑沒拿到數據，則回退到你原本的 AJAX 探測邏輯
        if "movie-list-item" not in html and pg > 1:
            ajax_url = f"{self.host}/index.php/ajax/data.html?mid=1&tid={tid}&page={pg}&limit=20"
            ajax_headers = headers.copy()
            ajax_headers.update({
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01"
            })
            ajax_res = self.fetch(ajax_url, headers=ajax_headers)
            content = ajax_res.text
            if content.strip().startswith('{'):
                try:
                    data = json.loads(content)
                    html = data.get('html', data.get('data', content))
                except:
                    html = content
            else:
                html = content

        # 最後保底：嘗試帶參數的動態路徑
        if "movie-list-item" not in html and pg > 1:
            url_alt = f"{self.host}/vodtype/{tid}/?page={pg}"
            html = self.fetch(url_alt, headers={"User-Agent": "Mozilla/5.0"}).text
                
        return self.parse_list(html)

    def parse_list(self, html):
        videos = []
        seen_ids = set()
        # 修正 Regex：兼容單引號或雙引號，並處理可能存在的 JSON 轉義
        html = html.replace('\/', '/')
        items = re.findall(r'class=[\'\"]movie-list-item.*?</a>', html, re.S)
        for item in items:
            link_m = re.search(r'href=[\'\"](/vod(?:play|detail)/(\d+)-.*?)[\'\"]', item)
            if not link_m: continue
            v_id = link_m.group(2)
            if v_id in seen_ids: continue
            seen_ids.add(v_id)

            pic = ""
            pic_match = re.search(r'(?:data-original|data-src|src)=[\'\"](.*?)[\'\"]', item)
            if not pic_match:
                pic_match = re.search(r'background-image:\s*url\([\'\"]?(.*?)[\'\"]?\)', item)
            
            if pic_match:
                pic = pic_match.group(1).strip()
            
            title_m = re.search(r'title=[\'\"](.*?)[\'\"]', item)
            name = title_m.group(1) if title_m else "Video"
            for junk in ['gt;', '&gt;', 'π', '影片信息', '&quot;']:
                name = name.replace(junk, '')
            name = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', name).strip()
            
            if v_id and pic:
                vod_pic = pic if pic.startswith('http') else self.host + pic
                if "imagecdn" in vod_pic:
                    # 注入防盜鏈參數
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
        html = self.fetch(url, headers={"User-Agent": "Mozilla/5.0"}).text
        
        title = "Video"
        title_m = re.search(r'<title>(.*?) - MOTV', html)
        if title_m: 
            title = title_m.group(1).split('-')[0].replace('gt;', '').replace('&gt;', '')
            title = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', title).strip()
        
        pic_m = re.search(r'(?:data-original|src)=[\'\"](.*?)[\'\"]|url\([\'\"]?(.*?)[\'\"]?\)', html)
        pic = (pic_m.group(1) or pic_m.group(2)).strip() if pic_m else ""
        if pic and not pic.startswith('http'): pic = self.host + pic
        if pic and "imagecdn" in pic:
            pic = f"{pic}@Referer={self.host}@User-Agent=Mozilla/5.0"
            
        vod = {
            "vod_id": v_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_play_from": "MOTV",
            "vod_play_url": f"立即播放$/vodplay/{v_id}-1-1/"
        }
        return {"list": [vod]}

    def searchContent(self, key, quick):
        self.prepare()
        url = f"{self.host}/vodsearch/wd/{key}/"
        html = self.fetch(url, headers={"User-Agent": "Mozilla/5.0"}).text
        return self.parse_list(html)

    def playerContent(self, flag, id, vipFlags):
        self.prepare()
        clean_id = id.strip()
        url = self.host + clean_id if clean_id.startswith('/') else f"{self.host}/{clean_id}"
        
        html = self.fetch(url, headers={"User-Agent": "Mozilla/5.0", "Referer": self.host}).text
        match = re.search(r'player_aaaa\s*=\s*(.*?)</script>', html)
        if match:
            try:
                config = json.loads(match.group(1))
                play_url = config.get('url', '')
                return {
                    "parse": 0 if ('.m3u8' in play_url or '.mp4' in play_url) else 1,
                    "url": play_url,
                    "header": {"User-Agent": "Mozilla/5.0", "Referer": self.host}
                }
            except: pass
        return {"parse": 1, "url": url}