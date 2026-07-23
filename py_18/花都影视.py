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
            {"type_id": "2", "type_name": "无字幕"},
            {"type_id": "3", "type_name": "国产"},
            {"type_id": "5", "type_name": "动漫"},
            {"type_id": "4", "type_name": "欧美"},
        ]

    def getName(self):
        return "花都影视"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _get_html(self, url):
        """获取页面HTML"""
        try:
            resp = self.fetch(url, headers=self.headers)
            if resp and resp.status_code == 200:
                return resp.text
        except Exception as e:
            self.log({"action": "fetch_fail", "url": url, "error": str(e)})
        return ""

    def _parse_video_list(self, html):
        """解析视频列表"""
        if not html:
            return []
        
        results = []
        
        # 匹配视频卡片
        # 格式: <li class="col-md-6 col-sm-3 col-xs-2 "> ... </li>
        pattern = r'<li[^>]*class="[^"]*col-[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*title="([^"]*)"[^>]*>.*?<img[^>]+data-original="([^"]+)"[^>]*>.*?</li>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for match in matches:
            url, title, pic = match
            vid = url.split("/")[-1].replace(".html", "")
            # 处理相对路径
            if pic.startswith("/"):
                pic = self.host + pic
            if url.startswith("/"):
                url = self.host + url
            
            results.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": ""
            })
        
        return results

    def _parse_play_url(self, html):
        """从播放页解析视频源"""
        if not html:
            return None
        
        # 1. 查找 iframe 中的 src
        # 常见格式: <iframe src="https://xxx.com/xxx" ...>
        pattern = r'<iframe[^>]+src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(pattern, html)
        for match in matches:
            if match and not match.startswith("javascript:"):
                # 可能是视频源地址
                if ".m3u8" in match or ".mp4" in match or "/vodplay/" in match:
                    return match
        
        # 2. 查找 video 标签中的 src
        pattern = r'<video[^>]*src=["\']([^"\']+)["\'][^>]*>'
        match = re.search(pattern, html)
        if match:
            return match.group(1)
        
        # 3. 查找 player_aaaa 变量（FeiFeiCMS 常用）
        pattern = r'player_aaaa\s*=\s*({[^}]+})'
        match = re.search(pattern, html)
        if match:
            try:
                data = json.loads(match.group(1))
                if "url" in data:
                    return data["url"]
            except:
                pass
        
        # 4. 查找播放器嵌入的 JS 变量
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
        """首页推荐 - 使用第一个分类"""
        return self.categoryContent(tid="1", pg="1", filter=False, extend={})

    def categoryContent(self, tid, pg, filter=False, extend={}):
        page = int(pg) if pg else 1
        url = f"{self.host}/index.php/vodtype/{tid}.html"
        if page > 1:
            url = f"{self.host}/index.php/vodtype/{tid}-{page}.html"
        
        html = self._get_html(url)
        video_list = self._parse_video_list(html)
        
        # 获取总页数
        pagecount = 100
        if html:
            pattern = r'<span[^>]*class="[^"]*pageinfo[^"]*"[^>]*>.*?/(\d+)\s*页</span>'
            match = re.search(pattern, html)
            if match:
                try:
                    pagecount = int(match.group(1))
                except:
                    pass
            # 另一种分页格式
            pattern = r'<li[^>]*class="[^"]*active[^"]*"[^>]*>.*?<span[^>]*>(\d+)</span>.*?</li>.*?<span[^>]*>共(\d+)页</span>'
            match = re.search(pattern, html)
            if match:
                try:
                    pagecount = int(match.group(2))
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
        
        # 提取标题
        title = vid
        pattern = r'<a[^>]+href="[^"]*/voddetail/[^"]*"[^>]*title="([^"]*)"'
        match = re.search(pattern, html)
        if match:
            title = match.group(1)
        
        # 提取封面
        pic = ""
        pattern = r'<img[^>]+class="[^"]*stui-vodlist__thumb[^"]*"[^>]+data-original="([^"]+)"'
        match = re.search(pattern, html)
        if match:
            pic = match.group(1)
            if pic.startswith("/"):
                pic = self.host + pic
        
        # 提取描述
        desc = ""
        pattern = r'<div[^>]*class="[^"]*vod_content[^"]*"[^>]*>([\s\S]*?)</div>'
        match = re.search(pattern, html)
        if match:
            desc = match.group(1).strip()
            desc = re.sub(r'<[^>]+>', '', desc)
        
        # 提取播放地址 - 从播放按钮链接构建
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
        """播放 - 从播放页解析视频源"""
        if not id:
            return {"parse": 1, "url": ""}
        
        # 如果是完整的播放页 URL
        if id.startswith(self.host) and "/vodplay/" in id:
            html = self._get_html(id)
            play_url = self._parse_play_url(html)
            if play_url:
                if play_url.startswith("/"):
                    play_url = self.host + play_url
                return {"parse": 0, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"]}}
        
        # 如果已经是直接的视频源
        if id.startswith("http://") or id.startswith("https://"):
            if ".m3u8" in id or ".mp4" in id:
                return {"parse": 0, "url": id, "header": {"User-Agent": self.headers["User-Agent"]}}
            # 可能是播放页 URL，尝试解析
            html = self._get_html(id)
            play_url = self._parse_play_url(html)
            if play_url:
                if play_url.startswith("/"):
                    play_url = self.host + play_url
                return {"parse": 0, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"]}}
        
        # 降级：使用 WebView 嗅探
        return {"parse": 1, "url": id}

    def localProxy(self, param):
        return [404, "text/plain", "Not Found"]

    def destroy(self):
        pass