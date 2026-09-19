# coding: utf-8
import json
import re
from urllib.parse import urljoin, quote, unquote

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://www.ksndym.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "20", "type_name": "短剧"},
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "32", "type_name": "纪录片"}
        ]
        self.filters = {
            "20": [],
            "1": [],
            "2": [],
            "4": [],
            "3": [],
            "32": []
        }

    def getName(self):
        return "短剧在线"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            res = self.fetch(self.host, headers=self.headers, timeout=10)
            html = res.text
            items = []
            pattern = r'<a class="stui-vodlist__thumb[^"]*" href="(/post/(\d+)/)" title="([^"]*)" data-original="([^"]*)"[^>]*>.*?<span class="pic-text[^"]*"[^>]*><b>([^<]*)</b></span>'
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                url, vid, title, pic, remark = match
                items.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": urljoin(self.host, pic),
                    "vod_remarks": remark
                })
            return {"list": items}
        except Exception as e:
            self.log("homeVideoContent error: " + str(e))
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        try:
            url = f"{self.host}/category-{tid}-{page}/"
            if page == "1":
                url = f"{self.host}/category-{tid}/"
            res = self.fetch(url, headers=self.headers, timeout=10)
            html = res.text
            items = []
            pattern = r'<a class="stui-vodlist__thumb[^"]*" href="(/post/(\d+)/)" title="([^"]*)" data-original="([^"]*)"[^>]*>.*?<span class="pic-text[^"]*"[^>]*><b>([^<]*)</b></span>'
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                url, vid, title, pic, remark = match
                items.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": urljoin(self.host, pic),
                    "vod_remarks": remark
                })
            page_count = 1
            total = 0
            page_match = re.search(r'(\d+)\s*/\s*(\d+)', html)
            if page_match:
                total_pages = int(page_match.group(2))
                page_count = total_pages
                total = total_pages * 20
            return {
                "list": items,
                "page": int(page),
                "pagecount": page_count,
                "limit": 20,
                "total": total
            }
        except Exception as e:
            self.log("categoryContent error: " + str(e))
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        try:
            vid = str(ids[0])
            url = f"{self.host}/post/{vid}/"
            res = self.fetch(url, headers=self.headers, timeout=10)
            html = res.text

            title = ""
            title_match = re.search(r'<h1 class="title">([^<]*)</h1>', html)
            if title_match:
                title = title_match.group(1).strip()

            pic = ""
            pic_match = re.search(r'<img class="lazyload"[^>]*data-original="([^"]*)"', html)
            if pic_match:
                pic = urljoin(self.host, pic_match.group(1))

            remark = ""
            remark_match = re.search(r'状态：<span[^>]*>([^<]*)</span>', html)
            if remark_match:
                remark = remark_match.group(1).strip()

            content = ""
            content_match = re.search(r'<span class="detail-content"[^>]*>([^<]*)</span>', html)
            if not content_match:
                content_match = re.search(r'<span class="detail-sketch"[^>]*>([^<]*)</span>', html)
            if content_match:
                content = content_match.group(1).strip()

            play_from_list = []
            play_url_list = []
            tab_pattern = r'<li[^>]*><a href="#playlist(\d+)"[^>]*>([^<]*)</a></li>'
            tabs = re.findall(tab_pattern, html)
            for sid, name in tabs:
                list_pattern = r'<div id="playlist' + sid + r'"[^>]*>.*?<ul class="stui-content__playlist[^>]*>(.*?)</ul>'
                list_match = re.search(list_pattern, html, re.DOTALL)
                if list_match:
                    ul_content = list_match.group(1)
                    item_pattern = r'<li[^>]*><a href="(/pl/[^"]+)"[^>]*>([^<]*)</a></li>'
                    items = re.findall(item_pattern, ul_content)
                    if items:
                        play_urls = []
                        for play_url, play_name in items:
                            play_urls.append(f"{play_name}${play_url}")
                        play_from_list.append(name)
                        play_url_list.append("#".join(play_urls))

            vod = {
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark,
                "vod_content": content,
                "vod_play_from": "$$$".join(play_from_list) if play_from_list else "播放",
                "vod_play_url": "$$$".join(play_url_list) if play_url_list else ""
            }
            return {"list": [vod]}
        except Exception as e:
            self.log("detailContent error: " + str(e))
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        try:
            url = f"{self.host}/sch/{key}-------------/"
            res = self.post(url, headers=self.headers, data={"wd": key}, timeout=10)
            html = res.text
            items = []
            pattern = r'<a class="stui-vodlist__thumb[^"]*" href="(/post/(\d+)/)" title="([^"]*)" data-original="([^"]*)"[^>]*>.*?<span class="pic-text[^"]*"[^>]*><b>([^<]*)</b></span>'
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                url, vid, title, pic, remark = match
                items.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": urljoin(self.host, pic),
                    "vod_remarks": remark
                })
            return {"list": items, "page": int(pg)}
        except Exception as e:
            self.log("searchContent error: " + str(e))
            return {"list": [], "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        try:
            play_url = id
            if play_url.startswith("/"):
                play_url = urljoin(self.host, play_url)
            res = self.fetch(play_url, headers=self.headers, timeout=10)
            html = res.text
            pattern = r'var player_aaaa=\{"flag":"play","encrypt":0,"trysee":0,"points":0,"link":"[^"]*","link_next":"","link_pre":"","vod_data":{[^}]*},"url":"([^"]+)","url_next":"","from":"[^"]*","server":"no","note":"","id":"\d+","sid":\d+,"nid":\d+\}'
            match = re.search(pattern, html)
            if match:
                real_url = match.group(1)
                if real_url.endswith(".m3u8"):
                    return {"parse": 0, "url": real_url, "header": {"User-Agent": self.headers["User-Agent"]}}
                return {"parse": 0, "url": real_url, "header": {"User-Agent": self.headers["User-Agent"]}}
            return {"parse": 1, "url": play_url, "header": self.headers}
        except Exception as e:
            self.log("playerContent error: " + str(e))
            return {"parse": 1, "url": id, "header": self.headers}

    def recommendContent(self, ids, pg):
        try:
            vid = str(ids[0]) if ids else ""
            url = f"{self.host}/post/{vid}/"
            res = self.fetch(url, headers=self.headers, timeout=10)
            html = res.text
            items = []
            pattern = r'<a class="stui-vodlist__thumb[^"]*" href="(/post/(\d+)/)" title="([^"]*)" data-original="([^"]*)"[^>]*>.*?<span class="pic-text[^"]*"[^>]*><b>([^<]*)</b></span>'
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches[:20]:
                url, vid, title, pic, remark = match
                items.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": urljoin(self.host, pic),
                    "vod_remarks": remark
                })
            return {"list": items}
        except Exception as e:
            self.log("recommendContent error: " + str(e))
            return {"list": []}

    def destroy(self):
        pass