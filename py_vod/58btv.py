# coding: utf-8
# 58BTV 影视站爬虫
# 站点: https://58btv.net
# 类型: HTML解析站
# 更新: 2026-08-10

import re
import json
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    """58BTV 影视爬虫"""
    
    def __init__(self):
        self.site_url = "https://58btv.net"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.site_url + "/"
        }
        self._init_classes()
    
    def _init_classes(self):
        self.classes = [
            {"type_id": "list-tv-kr", "type_name": "韓劇"},
            {"type_id": "list-tv-tw", "type_name": "臺劇"},
            {"type_id": "list-tv-cn", "type_name": "陸劇"},
            {"type_id": "list-tv-west", "type_name": "歐美劇"},
            {"type_id": "list-tv-jp", "type_name": "日劇"},
            {"type_id": "list-tv-hk", "type_name": "港劇"},
            {"type_id": "list-anime", "type_name": "動漫"},
            {"type_id": "list-variety", "type_name": "綜藝"},
            {"type_id": "list-movie-action", "type_name": "動作片"},
            {"type_id": "list-movie-comedy", "type_name": "喜劇片"},
            {"type_id": "list-movie-romance", "type_name": "愛情片"},
            {"type_id": "list-movie-scifi", "type_name": "科幻片"},
            {"type_id": "list-movie-horror", "type_name": "恐怖片"},
            {"type_id": "list-movie-feature", "type_name": "劇情片"},
            {"type_id": "list-movie-war", "type_name": "戰爭片"},
            {"type_id": "list-doc", "type_name": "記錄片"},
        ]
        self.filters = {c["type_id"]: [] for c in self.classes}
    
    def getName(self):
        return "58BTV"
    
    def getDependence(self):
        return []
    
    def init(self, extend=""):
        self.site_url = "https://58btv.net"
        self.headers["Referer"] = self.site_url + "/"
    
    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}
    
    def getHomeContent(self, filter):
        return self.homeContent(filter)
    
    def homeVideoContent(self):
        html = self._fetch_html(self.site_url + "/")
        if not html:
            return {"list": []}
        return {"list": self._parse_video_items(html)[:30]}
    
    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        url = self.site_url + "/" + tid + "/"
        if page > 1:
            url += "?page=" + str(page)
        html = self._fetch_html(url)
        if not html:
            return {"page": page, "pagecount": 99, "limit": 24, "total": 0, "list": []}
        return {"page": page, "pagecount": 99, "limit": 24, "total": 0, "list": self._parse_video_items(html)}
    
    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        if isinstance(ids, (int, str)):
            ids = [str(ids)]
        elif isinstance(ids, list) and ids and not isinstance(ids[0], str):
            ids = [str(ids[0])]
        vid = str(ids[0])
        html = self._fetch_html(self.site_url + "/film-" + vid + ".html")
        if not html:
            return {"list": []}
        return {"list": [self._parse_detail(html, vid)]}
    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        url = self.site_url + "/search?q=" + urllib.parse.quote(key)
        if page > 1:
            url += "&page=" + str(page)
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        return {"list": self._parse_video_items(html)}
    
    def playerContent(self, flag, id, vipFlags):
        # 如果 id 已经是完整 URL，直接返回
        if id.startswith("http"):
            return {"parse": 0, "url": id, "header": self.headers}
        
        # 尝试从播放页提取 m3u8 URL
        url = self.site_url + id if id.startswith("/") else id
        html = self._fetch_html(url)
        if html:
            # 尝试从 select 下拉框提取
            m3u8_url = self._extract_m3u8(html)
            if m3u8_url and m3u8_url.startswith("http"):
                return {"parse": 0, "url": m3u8_url, "header": self.headers}
            
            # 尝试从 video 标签的 data-setup 或 src 中提取
            video_match = re.search(r'<video[^>]*src="([^"]+)"', html)
            if video_match:
                src = video_match.group(1)
                if src.startswith("https://") and ".m3u8" in src:
                    return {"parse": 0, "url": src, "header": self.headers}
        
        # 降级：交给壳端 WebView 嗅探
        # 提供完整的 header 以确保 WebView 能正常加载播放页
        play_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.site_url + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive"
        }
        return {"parse": 1, "url": url, "header": play_headers}
    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if resp and resp.status_code == 200:
                return resp.text
        except:
            pass
        return None
    
    def _parse_video_items(self, html):
        items = []
        pattern = r'<a[^>]*class="[^"]*x-thumbnail-wrap[^"]*x-thumbnail-play[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]*)"'
        for match in re.finditer(pattern, html):
            try:
                href = match.group(1)
                title = match.group(2)
                vid_match = re.search(r"/film-(\d+)", href)
                if not vid_match:
                    continue
                vid = vid_match.group(1)
                # 提取封面图 - 扩大搜索范围到整个 li 区域
                li_start = html.rfind('<li', 0, match.start())
                li_end = html.find('</li>', match.end())
                if li_end == -1:
                    li_end = match.end() + 500
                li_html = html[li_start:li_end] if li_start != -1 else html[match.start():match.end()+800]
                
                pic = ""
                img_match = re.search(r'<img[^>]*data-original="([^"]+)"', li_html)
                if img_match:
                    pic = self._fix_url(img_match.group(1))
                else:
                    img_match = re.search(r'<img[^>]*src="([^"]+)"', li_html)
                    if img_match:
                        pic = self._fix_url(img_match.group(1))
                
                # 提取角标 - 从整个 li 区域中搜索
                remarks = ""
                # 优先取 video-grade-right（评分）
                grade_match = re.search(r'<span[^>]*class="[^"]*video-grade-right[^"]*"[^>]*>([^<]+)</span>', li_html)
                if grade_match:
                    remarks = grade_match.group(1).strip()
                else:
                    # 降级取 video-grade-left（年份）
                    grade_match = re.search(r'<span[^>]*class="[^"]*video-grade-left[^"]*"[^>]*>([^<]+)</span>', li_html)
                    if grade_match:
                        remarks = grade_match.group(1).strip()
                
                items.append({"vod_id": vid, "vod_name": title, "vod_pic": pic, "vod_remarks": remarks})
            except:
                continue
        return items
    def _parse_detail(self, html, vid):
        name = ""
        h1_match = re.search(r'<h1[^>]*class="[^"]*h2[^"]*"[^>]*>([^<]+)</h1>', html)
        if h1_match:
            name = h1_match.group(1).replace("線上看", "").strip()
        pic = ""
        img_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*alt="[^"]*"', html)
        if img_match:
            pic = self._fix_url(img_match.group(1))
        type_name = ""
        breads = re.findall(r'<li[^>]*class="[^"]*breadcrumb-item[^"]*"[^>]*>(?:<a[^>]*href="[^"]*"[^>]*>)?([^<]+)(?:</a>)?</li>', html)
        if len(breads) >= 2:
            type_name = breads[-2].strip()
        desc = ""
        intro_match = re.search(r'<p[^>]*class="[^"]*detail-intro[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
        if intro_match:
            desc = re.sub(r'<[^>]+>', '', intro_match.group(1)).strip()
            desc = re.sub(r'劇情介紹：', '', desc).strip()
        director = ""
        director_match = re.search(r'<label>導演：</label>\s*<span[^>]*>([^<]+)</span>', html)
        if director_match:
            director = director_match.group(1).strip()
        actor = ""
        actor_match = re.search(r'<label>主演：</label>(.*?)</li>', html, re.DOTALL)
        if actor_match:
            spans = re.findall(r'<span[^>]*>([^<]+)</span>', actor_match.group(1))
            actor = ",".join([s.strip() for s in spans])
        area = ""
        area_match = re.search(r'<label>類別：</label>\s*<a[^>]*href="[^"]*"[^>]*>([^<]+)</a>', html)
        if area_match:
            area = area_match.group(1).strip()
        year = ""
        year_match = re.search(r'<label>發行年份：</label>\s*<span[^>]*>([^<]+)</span>', html)
        if not year_match:
            year_match = re.search(r'<label><span[^>]*>發行</span>年份：</label>\s*<span[^>]*>([^<]+)</span>', html)
        if year_match:
            year = year_match.group(1).strip()
        play_from = []
        play_url = []
        ul_match = re.search(r'<ul[^>]*class="[^"]*detail-play-list[^"]*"[^>]*>(.*?)</ul>', html, re.DOTALL)
        if ul_match:
            lis = re.findall(r'<li[^>]*>(.*?)</li>', ul_match.group(1), re.DOTALL)
            ep_list = []
            for li in lis:
                a_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', li)
                if a_match:
                    ep_name = a_match.group(2).strip()
                    ep_url = a_match.group(1).strip()
                    if ep_name and ep_url:
                        ep_list.append({"name": ep_name, "url": ep_url})
            # 按集数排序（从第1集开始）
            if ep_list:
                ep_list.sort(key=lambda x: self._extract_episode_num(x["name"]))
                play_from.append("在線播放")
                play_url.append("#".join([e["name"] + "$" + e["url"] for e in ep_list]))
        if not play_from:
            a_list = re.findall(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>([^<]+)</a>', html)
            ep_list = []
            for href, title, text in a_list:
                if "/watching-" in href and not href.endswith(".html"):
                    ep_name = text.strip()
                    ep_url = href.strip()
                    if ep_name and ep_url:
                        ep_list.append({"name": ep_name, "url": ep_url})
            if ep_list:
                ep_list.sort(key=lambda x: self._extract_episode_num(x["name"]))
                play_from.append("在線播放")
                play_url.append("#".join([e["name"] + "$" + e["url"] for e in ep_list]))
        return {
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": pic,
            "type_name": type_name,
            "vod_content": desc,
            "vod_director": director,
            "vod_actor": actor,
            "vod_area": area,
            "vod_year": year,
            "vod_play_from": "$$$".join(play_from) if play_from else "",
            "vod_play_url": "$$$".join(play_url) if play_url else ""
        }
    
    def _extract_episode_num(self, name):
        """从剧集名称中提取集数用于排序"""
        # 匹配 "第X集" 或 "EP X" 或 "X"
        match = re.search(r'第(\d+)集', name)
        if match:
            return int(match.group(1))
        match = re.search(r'EP\s*(\d+)', name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)', name)
        if match:
            return int(match.group(1))
        return 9999  # 无法提取时放在最后
    def _extract_m3u8(self, html):
        # 优先从 select 下拉框获取
        select_match = re.search(r'<select[^>]*id="[^"]*x-select[^"]*"[^>]*>(.*?)</select>', html, re.DOTALL)
        if select_match:
            options = re.findall(r'<option[^>]*value="([^"]+)"', select_match.group(1))
            for opt in options:
                if opt and ".m3u8" in opt:
                    return opt
        # 从 script 中提取 m3u8 URL（包括 XHR 请求的 URL）
        m3u8_match = re.search(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
        if m3u8_match:
            return m3u8_match.group(0)
        # 从 XHR 请求日志中提取（通过 fetch 拦截方式）
        # 这里不处理，由 playerContent 中的 fetch 日志捕获
        return None
    def _fix_url(self, url):
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.site_url + url
        return self.site_url + "/" + url
    
    def localProxy(self, param):
        target = param.get("url") or param.get("target") or ""
        if not target:
            return [400, "text/plain", b"missing url"]
        try:
            resp = self.fetch(target, headers=self.headers, timeout=30)
            if resp and resp.status_code == 200:
                return [200, resp.headers.get("Content-Type", "video/mp2t"), resp.content]
            return [502, "text/plain", b"fetch failed"]
        except Exception as e:
            return [500, "text/plain", str(e).encode()]