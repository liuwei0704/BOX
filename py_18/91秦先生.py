# -*- coding: utf-8 -*-
# 站点: 91秦先生
# 说明: 无广告过滤版本

import re
import json
import urllib.parse
from urllib.parse import quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://69vip.cfd"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.host + '/'
        }
        self.classes = [
            {"type_id": "1", "type_name": "视频一区"},
            {"type_id": "6", "type_name": "国产"},
            {"type_id": "7", "type_name": "偷拍"},
            {"type_id": "8", "type_name": "巨乳"},
            {"type_id": "9", "type_name": "中文"},
            {"type_id": "10", "type_name": "欧美"},
            {"type_id": "11", "type_name": "动漫"},
            {"type_id": "12", "type_name": "制服"},
            {"type_id": "2", "type_name": "视频二区"},
            {"type_id": "13", "type_name": "无码"},
            {"type_id": "14", "type_name": "人妻"},
            {"type_id": "15", "type_name": "另类"},
            {"type_id": "16", "type_name": "学生"},
            {"type_id": "17", "type_name": "伦理"},
            {"type_id": "18", "type_name": "探花"},
            {"type_id": "20", "type_name": "少妇"},
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}

    def getName(self):
        return "91秦先生"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html(self.host + "/")
        items = self._parse_video_list(html)
        return {"list": items[:20]}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        pg = str(pg) if pg else "1"
        if pg == "1":
            url = self.host + f'/index.php/vod/type/id/{tid}.html'
        else:
            url = self.host + f'/index.php/vod/type/id/{tid}/page/{pg}.html'
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        page_count = self._parse_page_count(html)
        return {
            "list": items,
            "page": int(pg),
            "pagecount": page_count,
            "limit": 20,
            "total": page_count * 20
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0])
        url = self.host + f'/index.php/vod/detail/id/{vid}.html'
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        title = ''
        m = re.search(r'<div[^>]*class="breadcrumbs"[^>]*>.*?<span>([^<]+)</span>', html, re.DOTALL)
        if m:
            title = m.group(1).strip()
        if not title:
            m = re.search(r'<h3[^>]*class="appel-title"[^>]*>([^<]+)</h3>', html)
            if m:
                title = m.group(1).strip()
        if not title:
            m = re.search(r'<title>([^<]+)</title>', html)
            if m:
                title = m.group(1).replace('剧情介绍--91秦先生', '').strip()
        pic = ''
        m = re.search(r'<a[^>]*class="thumbnail"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>', html, re.DOTALL)
        if m:
            pic = self._fix_url(m.group(1))
        update_time = ''
        m = re.search(r'<li><label>更新：</label>([^<]+)</li>', html)
        if m:
            update_time = m.group(1).strip()
        play_from = "91秦先生"
        play_urls = []
        play_pattern = r'<a[^>]*href="(/index.php/vod/play/id/\d+/sid/\d+/nid/\d+\.html)"[^>]*>([^<]*)</a>'
        matches = re.findall(play_pattern, html)
        for href, label in matches:
            label_clean = label.strip()
            if label_clean and '分享' not in label_clean and '正在播放' not in label_clean:
                full_url = self._fix_url(href)
                play_urls.append(full_url)
        if not play_urls:
            m = re.search(r'<a[^>]*href="(/index.php/vod/play/id/\d+/sid/\d+/nid/\d+\.html)"[^>]*>正在播放</a>', html)
            if m:
                full_url = self._fix_url(m.group(1))
                play_urls.append(full_url)
        if play_urls:
            play_url_str = '#'.join(play_urls)
        else:
            play_url_str = ''
        data = {
            'vod_id': vid,
            'vod_name': title or '未知标题',
            'vod_pic': pic,
            'vod_remarks': update_time,
            'vod_content': '',
            'vod_actor': '',
            'vod_director': '',
            'vod_play_from': play_from,
            'vod_play_url': play_url_str
        }
        return {"list": [data]}

    def searchContent(self, key, quick=False, pg='1'):
        if not key:
            return {"list": [], "page": 1, "pagecount": 1, "total": 0}
        pg = str(pg) if pg else "1"
        url = self.host + f'/index.php/vod/search/page/{pg}/wd/{quote(key)}.html'
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        page_count = self._parse_page_count(html)
        return {
            "list": items,
            "page": int(pg),
            "pagecount": page_count if page_count > 1 else 1,
            "total": page_count * 20
        }

    def playerContent(self, flag, id, vipFlags=None):
        id = str(id) if id is not None else ''
        if not id:
            return {"parse": 1, "url": ""}
        url_match = re.search(r'(https?://[^\s]+)', id)
        if url_match:
            id = url_match.group(1)
        if id.startswith('http'):
            if '.m3u8' in id or '.mp4' in id:
                return {
                    "parse": 0,
                    "url": id,
                    "header": {
                        "User-Agent": self.headers.get('User-Agent', ''),
                        "Referer": self.host + '/'
                    }
                }
            return self._extract_play_url(id)
        if id.startswith('/'):
            full_url = self._fix_url(id)
            return self._extract_play_url(full_url)
        if id.isdigit():
            full_url = self.host + f'/index.php/vod/play/id/{id}/sid/1/nid/1.html'
            return self._extract_play_url(full_url)
        return {
            "parse": 1,
            "url": id,
            "header": {
                "User-Agent": self.headers.get('User-Agent', ''),
                "Referer": self.host + '/'
            }
        }

    def _extract_play_url(self, url):
        html = self._fetch_html(url)
        if not html:
            return {"parse": 1, "url": url, "header": self.headers}
        m = re.search(r'player_aaaa\s*=\s*({[^}]+})', html)
        if m:
            try:
                data = json.loads(m.group(1))
                play_url = data.get('url', '')
                if play_url:
                    play_url = self._fix_url(play_url)
                    if '.m3u8' in play_url or '.mp4' in play_url:
                        return {
                            "parse": 0,
                            "url": play_url,
                            "header": {
                                "User-Agent": self.headers['User-Agent'],
                                "Referer": self.host + '/'
                            }
                        }
            except:
                pass
        m = re.search(r'["\']([^"\']+\.m3u8[^"\']*)["\']', html)
        if m:
            play_url = self._fix_url(m.group(1))
            if play_url:
                return {
                    "parse": 0,
                    "url": play_url,
                    "header": {
                        "User-Agent": self.headers['User-Agent'],
                        "Referer": self.host + '/'
                    }
                }
        return {
            "parse": 1,
            "url": url,
            "header": {
                "User-Agent": self.headers['User-Agent'],
                "Referer": self.host + '/'
            }
        }

    def _fix_url(self, url):
        if not url:
            return ''
        url = url.strip()
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host.rstrip('/') + url
        return self.host.rstrip('/') + '/' + url.lstrip('/')

    def _parse_video_list(self, html):
        items = []
        if not html:
            return items
        pattern = r'<li>.*?<a[^>]*class="thumbnail"[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>.*?<h5><a[^>]*title="([^"]*)"[^>]*>([^<]*)</a></h5>'
        matches = re.findall(pattern, html, re.DOTALL)
        for href, img_src, img_alt, title_attr, title_text in matches:
            vid = self._extract_vod_id(href)
            name = title_text or title_attr or img_alt
            pic = self._fix_url(img_src)
            if vid and name:
                items.append({
                    'vod_id': vid,
                    'vod_name': name.strip(),
                    'vod_pic': pic,
                    'vod_remarks': ''
                })
        return items

    def _extract_vod_id(self, url):
        if not url:
            return ''
        m = re.search(r'/vod/detail/id/(\d+)\.html', url)
        if m:
            return m.group(1)
        m = re.search(r'/vod/play/id/(\d+)/', url)
        if m:
            return m.group(1)
        return url

    def _parse_page_count(self, html):
        if not html:
            return 1
        m = re.search(r'当前\S+/(\d+)页', html)
        if m:
            return int(m.group(1))
        return 1

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if resp and hasattr(resp, 'text'):
                return resp.text
            return None
        except Exception:
            return None

    def recommendContent(self, ids, pg=1):
        if not ids:
            return {"list": []}
        vid = str(ids[0])
        url = self.host + f'/index.php/vod/detail/id/{vid}.html'
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        videos = []
        pattern = r'<h3[^>]*class="appel-title"[^>]*>猜你喜欢</h3>(.*?)</ul>'
        m = re.search(pattern, html, re.DOTALL)
        if m:
            section = m.group(1)
            li_pattern = r'<li>.*?<a[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>.*?<h5><a[^>]*title="([^"]*)"[^>]*>([^<]*)</a></h5>'
            matches = re.findall(li_pattern, section, re.DOTALL)
            for match in matches:
                href, img_src, img_alt, title_attr, title_text = match
                vid_id = self._extract_vod_id(href)
                name = title_text or title_attr or img_alt
                pic = self._fix_url(img_src)
                if vid_id and name:
                    videos.append({
                        'vod_id': vid_id,
                        'vod_name': name.strip(),
                        'vod_pic': pic,
                        'vod_remarks': ''
                    })
        if not videos:
            return self.homeVideoContent()
        return {"list": videos}

    def destroy(self):
        pass