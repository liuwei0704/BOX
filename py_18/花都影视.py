# coding: utf-8
import re
import json
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://a.huadudm.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.58 Mobile Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.classes = [
            {"type_id": "1", "type_name": "中文字幕"},
            {"type_id": "6", "type_name": "中字有码"},
            {"type_id": "8", "type_name": "中字无码"},
            {"type_id": "2", "type_name": "无字幕"},
            {"type_id": "7", "type_name": "骑兵有码"},
            {"type_id": "9", "type_name": "步兵无码"},
            {"type_id": "3", "type_name": "国产"},
            {"type_id": "10", "type_name": "国产精品"},
            {"type_id": "11", "type_name": "国产传媒"},
            {"type_id": "13", "type_name": "糖心Vlog"},
            {"type_id": "4", "type_name": "欧美"},
            {"type_id": "12", "type_name": "欧美中字"},
            {"type_id": "5", "type_name": "动漫"},
            {"type_id": "14", "type_name": "中字里番"},
            {"type_id": "15", "type_name": "3D动漫"},
            {"type_id": "16", "type_name": "AI短剧"},
        ]

    def getName(self):
        return "花都影视"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _get_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers)
            if resp and resp.status_code == 200:
                return resp.text
        except Exception as e:
            self.log({"action": "fetch_fail", "url": url, "error": str(e)})
        return ""

    def _parse_video_list(self, html):
        if not html:
            return []
        
        results = []
        pattern = r'<li[^>]*class="[^"]*col-[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*title="([^"]*)"[^>]*>.*?<img[^>]+data-original="([^"]+)"[^>]*>.*?</li>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for match in matches:
            url, title, pic = match
            vid = url.split("/")[-1].replace(".html", "")
            if pic.startswith("/"):
                pic = self.host + pic
            if url.startswith("/"):
                url = self.host + url
            
            duration = ""
            dur_match = re.search(r'<span[^>]*class="[^"]*pic-tag-b[^"]*"[^>]*>([^<]+)</span>', match[2] if len(match) > 2 else "")
            if dur_match:
                duration = dur_match.group(1).strip()
            
            results.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": duration
            })
        
        return results

    def _parse_play_url(self, html):
        if not html:
            return None
        
        pattern = r'<iframe[^>]+src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(pattern, html)
        for match in matches:
            if match and not match.startswith("javascript:"):
                if ".m3u8" in match or ".mp4" in match or "/vodplay/" in match:
                    return match
        
        pattern = r'<video[^>]*src=["\']([^"\']+)["\'][^>]*>'
        match = re.search(pattern, html)
        if match:
            return match.group(1)
        
        pattern = r'player_aaaa\s*=\s*({[^}]+})'
        match = re.search(pattern, html)
        if match:
            try:
                data = json.loads(match.group(1))
                if "url" in data:
                    return data["url"]
            except:
                pass
        
        pattern = r'var\s+[a-zA-Z_]+[\s]*=[\s]*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']'
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            if match and ".m3u8" in match:
                return match
        
        return None

    def homeContent(self, filter=False):
        return {
            "class": self.classes,
            "filters": {}
        }

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        return self.categoryContent(tid="1", pg="1", filter=False, extend={})

    def categoryContent(self, tid, pg, filter=False, extend={}):
        page = int(pg) if pg else 1
        
        if page == 1:
            url = f"{self.host}/index.php/vodtype/{tid}.html"
        else:
            url = f"{self.host}/vodshow/{tid}--------{page}---.html"
        
        html = self._get_html(url)
        video_list = self._parse_video_list(html)
        
        pagecount = 100
        if html:
            pattern = r'<span[^>]*class="num"[^>]*>(\d+)/(\d+)</span>'
            match = re.search(pattern, html)
            if match:
                try:
                    pagecount = int(match.group(2))
                except:
                    pass
            pattern = r'<span[^>]*class="[^"]*pageinfo[^"]*"[^>]*>.*?/(\d+)\s*页</span>'
            match = re.search(pattern, html)
            if match:
                try:
                    pagecount = int(match.group(1))
                except:
                    pass
        
        return {
            "list": video_list,
            "page": page,
            "pagecount": pagecount,
            "limit": len(video_list),
            "total": pagecount * 20
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        
        vid = str(ids[0])
        url = f"{self.host}/index.php/voddetail/{vid}.html"
        html = self._get_html(url)
        
        if not html:
            return {"list": []}
        
        title = vid
        pattern = r'<a[^>]+href="[^"]*/voddetail/[^"]*"[^>]*title="([^"]*)"'
        match = re.search(pattern, html)
        if match:
            title = match.group(1)
        
        pic = ""
        pattern = r'<img[^>]+class="[^"]*stui-vodlist__thumb[^"]*"[^>]+data-original="([^"]+)"'
        match = re.search(pattern, html)
        if match:
            pic = match.group(1)
            if pic.startswith("/"):
                pic = self.host + pic
        
        desc = ""
        pattern = r'<div[^>]*class="[^"]*vod_content[^"]*"[^>]*>([\s\S]*?)</div>'
        match = re.search(pattern, html)
        if match:
            desc = match.group(1).strip()
            desc = re.sub(r'<[^>]+>', '', desc)
        
        play_url = f"{self.host}/index.php/vodplay/{vid}-1-1.html"
        
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": pic,
            "vod_content": desc,
            "vod_remarks": "",
            "vod_play_from": "播放",
            "vod_play_url": f"播放${play_url}"
        }
        return {"list": [vod]}

    def searchContent(self, key, quick=False, pg="1"):
        page = int(pg) if pg else 1
        encoded_key = quote(key)
        url = f"{self.host}/index.php/vodsearch/{encoded_key}-------------.html"
        if page > 1:
            url = f"{self.host}/index.php/vodsearch/{encoded_key}-------------{page}.html"
        
        html = self._get_html(url)
        video_list = self._parse_video_list(html)
        
        return {
            "list": video_list,
            "page": page,
            "pagecount": 20,
            "limit": len(video_list),
            "total": 200
        }

    def playerContent(self, flag, id, vipFlags=""):
        if not id:
            return {"parse": 1, "url": ""}
        
        if id.startswith(self.host) and "/vodplay/" in id:
            html = self._get_html(id)
            play_url = self._parse_play_url(html)
            if play_url:
                if play_url.startswith("/"):
                    play_url = self.host + play_url
                return {"parse": 0, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"]}}
        
        if id.startswith("http://") or id.startswith("https://"):
            if ".m3u8" in id or ".mp4" in id:
                return {"parse": 0, "url": id, "header": {"User-Agent": self.headers["User-Agent"]}}
            html = self._get_html(id)
            play_url = self._parse_play_url(html)
            if play_url:
                if play_url.startswith("/"):
                    play_url = self.host + play_url
                return {"parse": 0, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"]}}
        
        return {"parse": 1, "url": id}

    def localProxy(self, param):
        return [404, "text/plain", "Not Found"]

    def destroy(self):
        pass