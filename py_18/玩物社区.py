# -*- coding: utf-8 -*-
# 玩物社区 - 使用 getProxyUrl() 方式

import json
import re
import urllib.parse
import requests
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def getName(self):
        return "玩物社区"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.host = "https://thu.hejpugurn.cc"
        self.default_pic = "https://via.placeholder.com/400x225?text=Video"
        
        self.classes = [
            {"type_id": "zhibo-huifang", "type_name": "直播回放"},
            {"type_id": "guochan-sm", "type_name": "国产sm"},
            {"type_id": "rihan-sm", "type_name": "日韩sm"},
            {"type_id": "oumei-sm", "type_name": "欧美sm"},
            {"type_id": "dongman-sm", "type_name": "动漫sm"},
            {"type_id": "tiaojiao-av", "type_name": "调教av"},
            {"type_id": "ai-all", "type_name": "AI短剧-全部"},
            {"type_id": "ai-duanju", "type_name": "AI成人短剧"},
            {"type_id": "ai-meinv", "type_name": "AI美女"},
            {"type_id": "ai-huanlian", "type_name": "AI换脸"},
            {"type_id": "ai-manju", "type_name": "AI漫剧"},
        ]
        
        self.filters = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _fix_url(self, url):
        if not url:
            return ""
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.host + url
        return url

    def _pic(self, url):
        """使用 getProxyUrl() 生成图片代理URL，参考好色先生.py"""
        if not url:
            return self.default_pic
        # 如果已经是代理URL，直接返回
        if url.startswith("proxy://") or "127.0.0.1:9978" in url:
            return url
        return self.getProxyUrl() + '&url=' + urllib.parse.quote(url)

    def _fetch_html(self, url):
        try:
            resp = self.session.get(url, timeout=15)
            return resp.text if resp.status_code == 200 else ""
        except:
            return ""

    def _extract_vid(self, url):
        match = re.search(r'/vd-([a-zA-Z0-9]+)-', url)
        return match.group(1) if match else ""

    def _extract_embed_id(self, embed_url):
        if not embed_url:
            return ""
        match = re.search(r'[?&]id=([^&]+)', embed_url)
        return match.group(1) if match else ""

    def _extract_total_count(self, html):
        match = re.search(r'"numberOfItems"\s*:\s*(\d+)', html)
        return int(match.group(1)) if match else 0

    def _extract_jsonld_items(self, html):
        items = []
        pattern = r'<script type="application/ld\+json">(.*?)</script>'
        for match in re.findall(pattern, html, re.DOTALL):
            try:
                data = json.loads(match)
                if data.get("@type") == "CollectionPage":
                    main = data.get("mainEntity", {})
                    if main.get("@type") == "ItemList":
                        for entry in main.get("itemListElement", []):
                            item = entry.get("item", {})
                            if item.get("@type") == "VideoObject":
                                url = item.get("url", "")
                                vid = self._extract_vid(url)
                                vod_name = item.get("name", "")
                                
                                thumb = item.get("thumbnailUrl", [])
                                if isinstance(thumb, list) and thumb:
                                    vod_pic = self._fix_url(thumb[0])
                                elif isinstance(thumb, str):
                                    vod_pic = self._fix_url(thumb)
                                else:
                                    vod_pic = ""
                                
                                # 使用 _pic 生成代理URL
                                proxy_pic = self._pic(vod_pic) if vod_pic else self.default_pic
                                
                                duration = item.get("duration", "")
                                if duration:
                                    duration = duration.replace("PT", "").replace("H", ":").replace("M", ":").replace("S", "")
                                
                                embed_id = self._extract_embed_id(item.get("embedUrl", ""))
                                
                                items.append({
                                    "vod_id": f"{vid}|$|{vod_name}|$|{proxy_pic}|$|{duration}|$|{embed_id}",
                                    "vod_name": vod_name,
                                    "vod_pic": proxy_pic,
                                    "vod_remarks": duration
                                })
            except:
                continue
        return items

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            data = self._fetch_category("guochan-sm", 1)
            return {"list": data.get("list", [])[:10]}
        except:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if pg else 1
        if tid.startswith("ai-"):
            return self._fetch_category_ai(tid, pg)
        return self._fetch_category(tid, pg)

    def _fetch_category(self, slug, pg):
        url = f"{self.host}/videos/{slug}/" if pg == 1 else f"{self.host}/videos/{slug}/page/{pg}/"
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1, "total": 0}
        items = self._extract_jsonld_items(html)
        total = self._extract_total_count(html)
        return {
            "list": items,
            "page": pg,
            "pagecount": max(1, (total + 19) // 20) if total > 0 else 1,
            "total": total if total > 0 else len(items)
        }

    def _fetch_category_ai(self, tid, pg):
        url = f"{self.host}/ai/{tid}/" if pg == 1 else f"{self.host}/ai/{tid}/page/{pg}/"
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1, "total": 0}
        items = self._extract_jsonld_items(html)
        total = self._extract_total_count(html)
        return {
            "list": items,
            "page": pg,
            "pagecount": max(1, (total + 19) // 20) if total > 0 else 1,
            "total": total if total > 0 else len(items)
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        parts = ids[0].split('|$|')
        vid = parts[0] if len(parts) > 0 else ""
        vod_name = parts[1] if len(parts) > 1 else ""
        vod_pic = parts[2] if len(parts) > 2 else self.default_pic
        vod_remark = parts[3] if len(parts) > 3 else ""
        embed_id = parts[4] if len(parts) > 4 else vid
        
        play_url = self._get_play_url(embed_id)
        return {"list": [{
            "vod_id": vid,
            "vod_name": vod_name,
            "vod_pic": vod_pic,
            "vod_remarks": vod_remark,
            "vod_content": vod_remark,
            "vod_play_from": "玩物",
            "vod_play_url": f"播放${play_url}" if play_url else ""
        }]}

    def _get_play_url(self, embed_id):
        if not embed_id:
            return ""
        html = self._fetch_html(f"{self.host}/videos/embed?id={embed_id}")
        if not html:
            return ""
        match = re.search(r'<source[^>]*src="([^"]+\.m3u8[^"]*)"', html)
        if match:
            return match.group(1)
        match = re.search(r'<video[^>]*>.*?<source[^>]*src="([^"]+)"', html, re.DOTALL)
        return match.group(1) if match else ""

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": ""}
        if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
            return {"parse": 0, "url": id, "header": self.headers}
        play_url = self._get_play_url(id)
        if play_url:
            return {"parse": 0, "url": play_url, "header": self.headers}
        return {"parse": 1, "url": id}

    def searchContent(self, key, quick, pg):
        if not key:
            return {"list": [], "page": 1, "pagecount": 1, "total": 0}
        pg = int(pg) if pg else 1
        url = f"{self.host}/videos/search/{urllib.parse.quote(key)}" if pg == 1 else f"{self.host}/videos/search/{urllib.parse.quote(key)}/page/{pg}/"
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1, "total": 0}
        items = self._extract_jsonld_items(html)
        total = self._extract_total_count(html)
        return {
            "list": items,
            "page": pg,
            "pagecount": max(1, (total + 19) // 20) if total > 0 else 1,
            "total": total if total > 0 else len(items)
        }

    def localProxy(self, params):
        """本地代理 - 处理图片请求"""
        try:
            url = params.get('url', '')
            if not url:
                return [404, 'text/plain', b'']
            
            # 请求图片
            headers = {
                "User-Agent": self.headers.get("User-Agent", "Mozilla/5.0"),
                "Referer": self.host + "/",
            }
            resp = self.session.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 200 and len(resp.content) > 0:
                content = resp.content
                # 判断图片类型
                if content.startswith(b'\xff\xd8'):
                    mime = "image/jpeg"
                elif content.startswith(b'\x89PNG'):
                    mime = "image/png"
                elif content.startswith(b'GIF8'):
                    mime = "image/gif"
                else:
                    mime = "image/jpeg"
                return [200, mime, content]
            else:
                return [404, 'text/plain', b'Image not found']
        except Exception as e:
            return [500, 'text/plain', str(e).encode('utf-8')]

    def destroy(self):
        try:
            self.session.close()
        except:
            pass