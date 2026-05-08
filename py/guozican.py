#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, json
from urllib.parse import quote
try:
    import requests
except:
    requests = None
try:
    from urllib.request import Request, urlopen
except:
    Request, urlopen = None, None

class Spider:
    host = "https://guozican-q.cyou"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://guozican-q.cyou/"}
    categories = [
        {"type_id": "1", "type_name": "在线视频"}, {"type_id": "6", "type_name": "中文字幕"},
        {"type_id": "7", "type_name": "亚洲视频"}, {"type_id": "8", "type_name": "欧美大片"},
        {"type_id": "9", "type_name": "自拍偷拍"}, {"type_id": "10", "type_name": "熟女人妻"},
        {"type_id": "11", "type_name": "强奸伦理"}, {"type_id": "12", "type_name": "卡通动漫"},
        {"type_id": "20", "type_name": "三级伦理"}
    ]
    def init(self, extend=""): pass
    def getDependence(self): return []

    def homeVideoContent(self):
        return self.homeContent(False)

    def _get(self, url):
        if requests:
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                r.encoding = "utf-8"
                return r.text
            except: pass
        if Request and urlopen:
            try:
                req = Request(url, headers=self.headers)
                with urlopen(req, timeout=15) as resp:
                    return resp.read().decode("utf-8", errors="ignore")
            except: pass
        return None

    def _fix(self, u):
        if not u: return ""
        u = u.strip()
        if u.startswith("http"): return u
        if u.startswith("//"): return "https:" + u
        if u.startswith("/"): return self.host + u
        return u

    def _parse_list(self, html):
        if not html: return []
        results, seen = [], set()
        blocks = re.findall(r'<li[^>]*>.*?<a[^>]*href="/index\.php/vod/detail/id/\d+\.html".*?</li>', html, re.S)
        for block in blocks:
            try:
                m = re.search(r'href="(/index\.php/vod/detail/id/(\d+)\.html)"', block)
                if not m or m.group(2) in seen: continue
                img_m = re.search(r'<img[^>]*src="([^"]+)"', block)
                pic = self._fix(img_m.group(1)) if img_m else ""
                alt_m = re.search(r'alt="([^"]+)"', block)
                title_m = re.search(r'title="([^"]+)"', block)
                name = (alt_m.group(1) if alt_m else (title_m.group(1) if title_m else "未知")).strip()
                if name in ("广告", "点击查看", ""): continue
                grade_m = re.search(r'<span[^>]*class="video-grade"[^>]*>([^<]+)', block)
                remarks = grade_m.group(1).strip() if grade_m else ""
                if not pic or "ads" in pic.lower(): continue
                seen.add(m.group(2))
                results.append({"vod_id": m.group(2), "vod_name": name, "vod_pic": pic, "vod_remarks": remarks})
            except: continue
        return results

    def _parse_detail(self, html, vid):
        name_m = re.search(r'<li>片名：(.*?)</li>', html)
        name = name_m.group(1).strip() if name_m else "未知"
        img_m = re.search(r'<div[^>]*class="detail-poster"[^>]*>.*?<img[^>]*src="([^"]+)"', html, re.S)
        pic = self._fix(img_m.group(1)) if img_m else ""
        sources, episodes = [], []
        tab_m = re.search(r'<ul[^>]*id="detail-tab"[^>]*>(.*?)</ul>', html, re.S)
        panes = re.findall(r'<ul[^>]*class="[^"]*tab-pane[^"]*"[^>]*>(.*?)</ul>', html, re.S)
        if tab_m and panes:
            tabs = re.findall(r'<a[^>]*>([^<]+)</a>', tab_m.group(1))
            if len(tabs) == len(panes):
                for i, src in enumerate(tabs):
                    eps = re.findall(r'<a[^>]*href="(/index\.php/vod/play/id/\d+/sid/\d+/nid/\d+\.html)"[^>]*>([^<]*)</a>', panes[i])
                    el = [f"{t.strip()}${self.host + u}" for u, t in eps if "/vod/play/" in u]
                    if el: sources.append(src.strip()); episodes.append("#".join(el))
        if not sources:
            all_eps = re.findall(r'<a[^>]*href="(/index\.php/vod/play/id/\d+/sid/\d+/nid/\d+\.html)"[^>]*>([^<]*)</a>', html)
            el = [f"{t.strip()}${self.host + u}" for u, t in all_eps if "/vod/play/" in u]
            if el: sources.append("默认"); episodes.append("#".join(el))
        return {"vod_id": vid, "vod_name": name, "vod_pic": pic, "vod_play_from": "$$$".join(sources), "vod_play_url": "$$$".join(episodes)}

    def homeContent(self, filter):
        html = self._get(self.host + "/")
        return {"class": self.categories, "list": self._parse_list(html) if html else [], "filters": {}}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        html = self._get(url)
        if not html: return {"list": [], "page": page, "pagecount": 1, "limit": 12, "total": 0}
        return {"list": self._parse_list(html), "page": page, "pagecount": 99, "limit": 12, "total": 0}

    def detailContent(self, ids):
        result = {"list": []}
        for vid in ids:
            try:
                html = self._get(f"{self.host}/index.php/vod/detail/id/{vid}.html")
                if html and "detail-poster" in html:
                    result["list"].append(self._parse_detail(html, vid))
            except: continue
        return result

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}&page={page}"
        html = self._get(url)
        return {"list": self._parse_list(html) if html else [], "page": page}

    def playerContent(self, flag, id, vipFlags):
        url = id if id.startswith("http") else self._fix(id)
        return {"parse": 1, "url": url, "header": self.headers}