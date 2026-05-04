#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, json, requests
from urllib.parse import quote
from lxml import etree
from base.spider import Spider

class Spider(Spider):
    def getName(self): return "ESJAV"
    def init(self, extend=""):
        self.host = "https://esjav.com"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": self.host + "/"})
        self.session.get(self.host + "/cn", timeout=15)
        self.categories = [
            {"type_id": "japanese", "type_name": "日本AV"},
            {"type_id": "uncensored-leak", "type_name": "无码流出"},
            {"type_id": "uncensored", "type_name": "无码"},
            {"type_id": "amateur", "type_name": "素人"},
        ]
    def _get(self, url):
        try: r = self.session.get(url, timeout=15); r.encoding = "utf-8"; return r.text
        except: return None
    def _fix(self, u): return "https:" + u if u and u.startswith("//") else self.host + u if u and u.startswith("/") else u or ""

    def _parse_list(self, html):
        if not html: return []
        results, seen = [], set()
        for m in re.finditer(r'<a[^>]*?href="[^"]*?/video/([a-f0-9]+)/([^"]+)"[^>]*?\stitle="([^"]*)"', html):
            hid, slug, title = m.group(1), m.group(2), m.group(3)
            vid = hid + "|" + slug
            if vid in seen: continue
            seen.add(vid)
            results.append({"vod_id": vid, "vod_name": title, "vod_pic": ""})
        for m in re.finditer(r'<img[^>]*?\sdata-src="(https?://img\.esjav\.com/[^"]+?/default\.jpg)"[^>]*?\salt="([^"]*)"', html):
            pic, alt = m.group(1), m.group(2)
            hm = re.search(r'/video/([a-f0-9]+)/([^"]+)', html[m.start()-3000:m.start()] if m.start() > 3000 else html[:m.start()+1000])
            if hm:
                vid = hm.group(1) + "|" + hm.group(2)
                for r in results:
                    if r["vod_id"] == vid:
                        if not r["vod_pic"]: r["vod_pic"] = pic
                        if not r["vod_name"]: r["vod_name"] = alt
                        break
        if results: return results
        for m in re.finditer(r'<img[^>]*?\sdata-src="(https?://img\.esjav\.com/[^"]+?/default\.jpg)"[^>]*?\salt="([^"]*)"', html):
            pic, alt = m.group(1), m.group(2)
            hm = re.search(r'/video/([a-f0-9]+)/([^"]+)', html[m.start()-3000:m.start()] if m.start() > 3000 else html[:m.start()+1000])
            if hm:
                vid = hm.group(1) + "|" + hm.group(2)
                if vid not in seen:
                    seen.add(vid)
                    results.append({"vod_id": vid, "vod_name": alt, "vod_pic": pic})
        if results: return results
        tree = etree.HTML(html)
        for item in tree.xpath('//div[contains(@class,"thumbnail")]'):
            try:
                a = item.xpath('.//a[contains(@href,"/video/")]')
                if not a: continue
                href = a[0].get("href", "")
                m = re.search(r'/video/([a-f0-9]+)/([^/]+)', href)
                if not m: continue
                vid = m.group(1) + "|" + m.group(2)
                if vid in seen: continue
                seen.add(vid)
                title = a[0].get("title", "") or "".join(a[0].xpath('.//text()')).strip()
                img = item.xpath('.//img[@data-src] | .//img[@src]')
                pic = ""
                if img: pic = img[0].get("data-src") or img[0].get("src", "")
                if not title:
                    imgs = item.xpath('.//img[@alt]')
                    if imgs: title = imgs[0].get("alt", "")
                results.append({"vod_id": vid, "vod_name": title, "vod_pic": pic})
            except: continue
        return results

    def homeContent(self, filter):
        html = self._get(self.host + "/cn")
        return {"class": self.categories, "list": self._parse_list(html) if html else [], "filters": {}}

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.host}/cn/videos/{tid}?page={pg}"
        html = self._get(url)
        return {"page": int(pg), "pagecount": 99, "limit": 36, "total": 999, "list": self._parse_list(html) if html else []}

    def detailContent(self, ids):
        result = {"list": []}
        for vid in ids:
            try:
                parts = vid.split("|", 1)
                hid = parts[0]; slug = parts[1] if len(parts) > 1 else ""
                url = f"{self.host}/cn/video/{hid}/{slug}" if slug else f"{self.host}/cn/video/{hid}"
                html = self._get(url)
                name = slug.upper() if slug else hid
                if html:
                    m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
                    if m: name = m.group(1).strip()
                    else:
                        m = re.search(r'<title>([^<]+)</title>', html)
                        if m: name = m.group(1).strip()
                play_url = f"{self.host}/media/videos/v_{hid}.m3u8"
                result["list"].append({"vod_id": vid, "vod_name": name, "vod_pic": "", "vod_play_from": "默认", "vod_play_url": f"完整版${play_url}"})
            except: continue
        return result

    def searchContent(self, key, quick, pg="1"):
        url = f"{self.host}/cn/videos/search?keyword={quote(key)}&page={pg}"
        html = self._get(url)
        return {"list": self._parse_list(html) if html else [], "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        url = self._fix(id)
        if not url.startswith("http"):
            m = re.search(r'([a-f0-9]{20,})', id)
            if m: url = f"{self.host}/media/videos/v_{m.group(1)}.m3u8"
        return {"parse": 0, "url": url, "header": json.dumps(dict(self.session.headers))}
