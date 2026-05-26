#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import json
import requests
import urllib.parse
from lxml import etree

BASE = "https://missavt.com"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": BASE + "/"
}

def _get(url):
    try:
        r = requests.get(url, headers=UA, timeout=15)
        r.encoding = "utf-8"
        return r.text
    except:
        return None

def _fix(u):
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return BASE + u
    return u

def _parse_list(html):
    if not html:
        return []
    tree = etree.HTML(html)
    results = []
    items = tree.xpath('//ul[contains(@class,"video-items")]/li')
    if not items:
        items = tree.xpath('//div[contains(@class,"video-item")]')
    for item in items:
        try:
            a_tag = item.xpath('.//a')[0] if item.xpath('.//a') else None
            if not a_tag:
                continue
            href = a_tag.get("href", "")
            m = re.search(r'/watch/([^/]+)/?', href)
            if not m:
                continue
            vod_id = m.group(1)
            img_tag = a_tag.xpath('.//img')[0] if a_tag.xpath('.//img') else None
            pic = ""
            if img_tag:
                pic = img_tag.get("data-src") or img_tag.get("src", "")
                pic = _fix(pic)
            title_tag = item.xpath('.//a[contains(@class,"my-1")]')
            title = ""
            if title_tag:
                title = title_tag[0].text.strip() if title_tag[0].text else ""
            if not title:
                title = a_tag.get("title", "")
            if not title and img_tag:
                title = img_tag.get("alt", "")
            if title and vod_id:
                results.append({
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": pic
                })
        except:
            continue
    return results

class Spider:
    def __init__(self):
        self.site_url = BASE
        self.headers = UA
        self.categories = [
            {"type_id": "1", "type_name": "推荐视频"},
            {"type_id": "2", "type_name": "热门视频"},
            {"type_id": "3", "type_name": "无码破解"},
            {"type_id": "4", "type_name": "中文字幕"},
            {"type_id": "5", "type_name": "素人"},
        ]

    def init(self, extend=""):
        self.site_url = BASE
        self.headers = UA

    def homeContent(self, filter):
        html = _get(BASE + "/")
        video_list = _parse_list(html) if html else []
        return {
            "class": self.categories,
            "list": video_list[:24],
            "filters": {}
        }

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        type_map = {
            "1": "",
            "2": "/sort/month_hot/",
            "3": "/category/reducing-mosaic/",
            "4": "/category/chinese-subtitle/",
            "5": "/category/amateur/",
        }
        path = type_map.get(tid, "")
        if page > 1:
            url = f"{BASE}{path}?page={page}"
        else:
            url = f"{BASE}{path}"
        html = _get(url)
        video_list = _parse_list(html) if html else []
        return {
            "page": page,
            "pagecount": 50,
            "limit": 36,
            "total": 999,
            "list": video_list
        }

    def detailContent(self, ids):
        result = {"list": []}
        for vod_id in ids:
            try:
                url = f"{BASE}/watch/{vod_id}/"
                html = _get(url)
                if not html:
                    continue
                tree = etree.HTML(html)
                title = ""
                h1 = tree.xpath('//h1/text()')
                if h1:
                    title = h1[0].strip()
                pic = ""
                img = tree.xpath('//div[contains(@class,"poster")]//img')
                if img:
                    pic = img[0].get("data-src") or img[0].get("src", "")
                    pic = _fix(pic)
                play_url = ""
                poster_div = tree.xpath('//div[contains(@class,"poster")]')
                if poster_div:
                    play_url = poster_div[0].get("data-url", "")
                if not play_url:
                    scripts = tree.xpath('//script/text()')
                    for script in scripts:
                        m = re.search(r'data-url=["\']([^"\']+\.m3u8[^"\']*)', script)
                        if m:
                            play_url = m.group(1)
                            break
                        m2 = re.search(r'url:\s*["\']([^"\']+\.m3u8[^"\']*)', script)
                        if m2:
                            play_url = m2.group(1)
                            break
                if play_url:
                    play_url = _fix(play_url)
                vod_play_from = "直链播放"
                vod_play_url = f"播放${play_url}" if play_url else ""
                result["list"].append({
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_play_from": vod_play_from,
                    "vod_play_url": vod_play_url
                })
            except:
                continue
        return result

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        url = f"{BASE}/search/{urllib.parse.quote(key)}/"
        if page > 1:
            url = f"{BASE}/search/{urllib.parse.quote(key)}/?page={page}"
        html = _get(url)
        video_list = _parse_list(html) if html else []
        return {
            "list": video_list,
            "page": page,
            "pagecount": 20
        }

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": json.dumps(UA)}
        if id.startswith('http'):
            url = id
        elif id.startswith('/'):
            url = BASE + id
        else:
            url = BASE + '/watch/' + id + '/'
        return {
            "parse": 1,
            "url": url,
            "header": json.dumps(UA)
        }