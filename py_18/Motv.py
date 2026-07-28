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
            {"type_name": "最新", "type_id": "new"},
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
            {"type_name": "三級電影", "type_id": "53"},
            {"type_name": "鹹濕電台", "type_id": "169"}
        ]
        try:
            res = self.fetch(self.host, headers={"User-Agent": self.m_ua})
            return {'class': classes, 'list': self.parse_list(res.text).get('list', []), 'filters': {}}
        except:
            return {'class': classes, 'list': [], 'filters': {}}

    def categoryContent(self, tid, pg, filter, extend):
        self.prepare()
        pg = int(pg)
        # 修正分頁邏輯
        url = f"{self.host}/vodshow/{tid}--------{pg}---/" if pg > 1 else f"{self.host}/vodtype/{tid}/"
        res = self.fetch(url, headers={"User-Agent": self.m_ua, "Referer": self.host})
        return self.parse_list(res.text)

    def parse_list(self, html):
        videos = []
        seen_ids = set()
        html = html.replace('\/', '/')
        # 兼容多種列表模式
        items = re.findall(r'class=[\'\"](?:movie-list-item|vod-search-list|list-item|video-item).*?</a>', html, re.S)
        
        for item in items:
            link_m = re.search(r'href=[\'\"](/vod(?:play|detail)/(\d+)-.*?)[\'\"]', item)
            if not link_m: continue
            v_id = link_m.group(2)
            if v_id in seen_ids: continue
            seen_ids.add(v_id)

            name = ""
            title_m = re.search(r'title=[\'\"](.*?)[\'\"]', item)
            if title_m: name = title_m.group(1)
            if not name or name.lower() == "video":
                alt_m = re.search(r'alt=[\'\"](.*?)[\'\"]', item)
                if alt_m: name = alt_m.group(1)
            
            # 清洗名稱
            for junk in ['gt;', '&gt;', 'π', '影片信息', '&quot;']:
                name = name.replace(junk, '')
            name = re.sub(r'^[^\w\u4e00-\u9fa5]+', '', name).strip()
            if not name: name = "Video"

            pic = ""
            pic_m = re.search(r'(?:data-original|data-src|src|data-lazyload|data-backup)=[\'\"](.*?)[\'\"]', item)
            if not pic_m:
                pic_m = re.search(r'url\([\'\"]?(.*?)[\'\"]?\)', item)
            
            if pic_m:
                pic = pic_m.group(1).strip()
                if not pic.startswith('http'):
                    pic = self.host + pic
                pic = f"{pic}@Referer={self.host}@User-Agent={self.m_ua}"
            
            videos.append({"vod_id": v_id, "vod_name": name, "vod_pic": pic, "vod_remarks": ""})
        return {"list": videos}

    def detailContent(self, ids):
        self.prepare()
        v_id = ids[0]
        url = f"{self.host}/voddetail/{v_id}/"
        res = self.fetch(url, headers={"User-Agent": self.m_ua, "Referer": self.host})
        html = res.text
        
        title = "Video"
        h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
        if h1_m:
            title = re.sub(r'<.*?>', '', h1_m.group(1)).strip()
        
        title = title.replace('&gt;', '').replace('π', '')
        
        pic = ""
        pic_m = re.search(r'(?:data-original|src)=[\'\"](.*?)[\'\"]', html)
        if pic_m:
            pic = pic_m.group(1).replace('\/', '/')
            if not pic.startswith('http'): pic = self.host + pic
        if pic: pic = f"{pic}@Referer={self.host}@User-Agent={self.m_ua}"

        vod = {
            "vod_id": v_id, "vod_name": title, "vod_pic": pic,
            "vod_play_from": "MOTV",
            "vod_play_url": f"播放$/vodplay/{v_id}-1-1/"
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg=1):
        self.prepare()
        url = f"{self.host}/vodsearch/-------------/?wd={key}"
        res = self.fetch(url, headers={"User-Agent": self.m_ua, "Referer": self.host})
        return self.parse_list(res.text)

    def playerContent(self, flag, id, vipFlags):
        self.prepare()
        import base64
        import urllib.parse
        play_url = self.host + id if id.startswith('/') else f"{self.host}/{id}"
        headers = {"User-Agent": self.m_ua, "Referer": self.host}
        res = self.fetch(play_url, headers=headers)
        html = res.text
        
        # 1. 尝试解析苹果CMS核心变量 player_aaaa
        player_data = re.search(r'var\s+player_aaaa\s*=\s*(\{.*?\})', html)
        if player_data:
            try:
                data = json.loads(player_data.group(1))
                v_url = data.get('url', '')
                
                # 处理 Base64 编码
                if v_url and not v_url.startswith('http') and not v_url.startswith('/'):
                    try:
                        v_url = base64.b64decode(v_url).decode('utf-8')
                    except:
                        pass
                
                v_url = urllib.parse.unquote(v_url).replace('\\/', '/')
                
                # 如果获取到了有效的 URL
                if v_url and len(v_url) > 10:
                    if 'url=' in v_url:
                        v_url = v_url.split('url=')[-1]
                    
                    ext = v_url.split('?')[0].split('.')[-1].lower()
                    if ext in ['m3u8', 'mp4', 'flv']:
                        return {"parse": 0, "url": v_url, "header": headers}
                    else:
                        return {"parse": 1, "url": v_url, "header": headers}
            except:
                pass

        # 2. 暴力提取：如果 player_aaaa 里没 url，则扫描全页面的 m3u8 特征
        # 排除掉 js 文件，寻找可能是视频流的地址
        raw_urls = re.findall(r'[\'\"](https?[:\\\/]+[^\'\" ]+?\.m3u8[^\'\" ]*)[\'\"]', html)
        for r_url in raw_urls:
            r_url = r_url.replace('\\/', '/')
            if 'index.m3u8' in r_url or '.m3u8' in r_url:
                return {"parse": 0, "url": r_url, "header": headers}

        # 2. 增强型正则匹配（兼容转义斜杠）
        matches = re.findall(r'[\'\"](https?[:\\\/]+[^\'\" ]+?\.m3u8[^\'\" ]*)[\'\"]', html)
        for m in matches:
            final_url = m.replace('\\/', '/').replace('&amp;', '&')
            return {"parse": 0, "url": final_url, "header": headers}

        # 3. 兜底方案：交给 APP 原生嗅探
        return {"parse": 1, "url": play_url, "header": headers}