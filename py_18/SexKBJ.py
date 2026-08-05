#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import json
import urllib.parse
from bs4 import BeautifulSoup

class Spider:
    def getName(self):
        return "SexKBJ"

    def getDependence(self):
        return ["bs4"]

    def init(self, extend=""):
        self.base_url = "https://sexkbj.com"
        self.embed_url = "https://sexkbj.top/embed"
        self.limit = 24
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.base_url,
        }
        self.categories = [
            {"type_id": "korean-bj", "type_name": "KOREAN BJ"},
            {"type_id": "premium", "type_name": "PREMIUM"},
            {"type_id": "afreecatv", "type_name": "AFREECATV"},
            {"type_id": "korean-amateur", "type_name": "KOREAN AMATEUR"},
        ]
        self.filters = {}

    def _fetch(self, url, headers=None):
        try:
            import requests
            if headers is None:
                headers = self.headers
            r = requests.get(url, headers=headers, timeout=15)
            r.encoding = 'utf-8'
            return r.text
        except Exception as e:
            print(f"fetch error: {e}")
            return ""

    def _fix(self, u):
        if not u:
            return ""
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return self.base_url + u
        return u

    def _parse_list(self, html):
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        for article in soup.select('article.loop-video')[:self.limit]:
            try:
                a = article.find('a')
                if not a:
                    continue
                href = a.get('href', '')
                if href and not href.startswith('http'):
                    href = self.base_url + href
                vod_id = href
                
                title = article.select_one('.entry-header span')
                name = title.text.strip() if title else ''
                
                img = article.select_one('.post-thumbnail-container img')
                pic = ''
                if img:
                    pic = img.get('src') or img.get('data-src') or ''
                    pic = self._fix(pic)
                
                dur = article.select_one('.duration')
                remark = dur.text.strip() if dur else ''
                
                views = article.select_one('.views')
                if views:
                    vt = views.text.strip()
                    if vt:
                        remark = f"{vt} {remark}".strip()
                
                results.append({
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
            except:
                continue
        return results

    def homeContent(self, filter):
        html = self._fetch(self.base_url)
        return {"class": self.categories, "list": self._parse_list(html), "filters": self.filters}

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        cat_map = {
            'korean-bj': '/category/korean-bj/',
            'premium': '/category/premium/',
            'afreecatv': '/category/afreecatv/',
            'korean-amateur': '/category/korean-amateur/',
        }
        path = cat_map.get(tid, f'/category/{tid}/')
        url = self.base_url + path
        if page > 1:
            url = self.base_url + path + f'page/{page}/'
        html = self._fetch(url)
        video_list = self._parse_list(html)
        pagecount = page
        if html:
            for a in re.findall(r'href="[^"]*/page/(\d+)/"', html):
                p = int(a)
                if p > pagecount:
                    pagecount = p
        return {"list": video_list, "page": page, "pagecount": pagecount, "limit": self.limit, "total": 0}

    def detailContent(self, ids):
        result = {"list": []}
        for vid in ids:
            url = vid if vid.startswith('http') else self.base_url + vid
            html = self._fetch(url)
            if not html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            
            title = soup.select_one('h1.entry-title')
            name = title.text.strip() if title else ''
            
            img = soup.select_one('.video-player .post-thumbnail-container img')
            pic = ''
            if img:
                pic = img.get('src') or img.get('data-src') or ''
                pic = self._fix(pic)
            
            desc = soup.select_one('.video-description')
            content = desc.text.strip() if desc else ''
            
            actor = ''
            ae = soup.select_one('#video-actors')
            if ae:
                actor = ' / '.join([a.text.strip() for a in ae.select('a')])
            
            iframe = soup.select_one('.responsive-player iframe')
            iframe_src = iframe.get('src', '') if iframe else ''
            
            vod_id = self._vid(url)
            if not vod_id and iframe_src:
                m = re.search(r'/embed/([^/?]+)', iframe_src)
                if m:
                    vod_id = m.group(1)
            if not vod_id:
                vod_id = vid
            
            play_url = iframe_src if iframe_src else ''
            if not play_url and vod_id:
                play_url = f'{self.embed_url}/{vod_id}'
            
            result["list"].append({
                "vod_id": vod_id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_content": content,
                "vod_actor": actor,
                "vod_play_from": "SexKBJ",
                "vod_play_url": f"SexKBJ${play_url}"
            })
        return result

    def _vid(self, url):
        m = re.search(r'/(kbj[\d_]+|ka[\d_]+|[a-z]+[\d_]+)', url, re.I)
        return m.group(1) if m else None

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        url = f'{self.base_url}/?s={urllib.parse.quote(key)}'
        if page > 1:
            url = f'{self.base_url}/page/{page}/?s={urllib.parse.quote(key)}'
        html = self._fetch(url)
        return {"list": self._parse_list(html), "page": page, "pagecount": 1}

    def _extract_m3u8(self, embed_url):
        """从 embed 页面提取 m3u8 直链"""
        headers = self.headers.copy()
        headers['Referer'] = 'https://sexkbj.com/'
        html = self._fetch(embed_url, headers)
        if not html:
            return None
        
        # 方法1: JWPlayer setup 中的 file
        m = re.search(r'file\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', html)
        if m:
            return m.group(1)
        
        # 方法2: 任意 m3u8 URL
        m = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if m:
            return m.group(0)
        
        # 方法3: cdn.acek.online 地址 (带 token)
        m = re.search(r'cdn\.[^\s"\']+\.online[^\s"\']+\.m3u8', html)
        if m:
            return 'https://' + m.group(0)
        
        # 方法4: sexkbj.top/stream/ 地址 (从日志中看到的实际流地址)
        m = re.search(r'sexkbj\.top/stream/[^\s"\']+\.m3u8', html)
        if m:
            return 'https://' + m.group(0)
        
        return None

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": ""}
        
        # 如果已经是直链 m3u8
        if '.m3u8' in id and id.startswith('http'):
            return {"parse": 0, "url": id, "header": json.dumps(self.headers)}
        
        # 尝试从 embed 页面提取 m3u8
        m3u8 = self._extract_m3u8(id)
        if m3u8:
            print(f"提取到直链 m3u8: {m3u8}")
            return {"parse": 0, "url": m3u8, "header": json.dumps(self.headers)}
        
        # 如果提取失败，返回 parse=1 让客户端 iframe 解析
        print(f"未提取到 m3u8，使用 iframe 解析: {id}")
        return {"parse": 1, "url": id, "header": json.dumps(self.headers)}