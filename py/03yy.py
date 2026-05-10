#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, requests
from bs4 import BeautifulSoup

host = "https://www.03yy.live"
ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": host + "/"}

def _fix(u):
    if not u: return ""
    if u.startswith("//"): return "https:" + u
    if u.startswith("/"): return host + u
    return u

def _get(url, cookies=None):
    try:
        r = requests.get(url, headers=ua, timeout=15, cookies=cookies, allow_redirects=False)
        if r.status_code in (301, 302):
            loc = r.headers.get("Location", "")
            if loc:
                if not loc.startswith("http"):
                    loc = host + loc
                r = requests.get(loc, headers=ua, timeout=15, cookies=cookies)
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except:
        return None

def _post(url, data, cookies=None):
    try:
        r = requests.post(url, data=data, headers=ua, timeout=15, cookies=cookies)
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except:
        return None

def _parse_list(html):
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    results, seen = [], set()
    items = soup.select('.pic-content a[href*="/movie/"] img')
    if not items:
        items = soup.select('a[href*="/movie/"] img')
    for img in items:
        try:
            a = img.find_parent('a')
            if not a: continue
            href = a.get("href", "")
            m = re.search(r"/movie/index(\d+)\.html", href)
            if not m or m.group(1) in seen: continue
            seen.add(m.group(1))
            pic = _fix(img.get("data-original") or img.get("data-src") or img.get("src", ""))
            title = a.get("title", "") or img.get("alt", "").strip()
            remarks = ""
            pc = a.find_parent(class_="pic-content")
            if pc:
                span = pc.select_one('span')
                if span: remarks = span.get_text(strip=True)
            if not title:
                if pc:
                    h4 = pc.select_one("h4 a")
                    title = h4.text.strip() if h4 and h4.text else ""
            if not title:
                title = a.get_text(strip=True)
            results.append({"vod_id": m.group(1), "vod_name": title, "vod_pic": pic, "vod_remarks": remarks})
        except:
            continue
    return results

class Spider:
    def __init__(self):
        self.host = host
        self.headers = ua
        self.cookies = {}
    def getName(self):
        return "03影院"
    def getDependence(self):
        return []
    def init(self, extend=""):
        try:
            r = requests.get(self.host, headers=self.headers, timeout=10, allow_redirects=False)
            self.cookies = r.cookies.get_dict()
        except:
            pass
    def homeContent(self, filter):
        categories = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "11", "type_name": "纪录"},
            {"type_id": "64", "type_name": "少儿"},
            {"type_id": "48", "type_name": "短剧"},
        ]
        area_f = {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "大陆", "v": "&area=大陆"}, {"n": "香港", "v": "&area=香港"}, {"n": "台湾", "v": "&area=台湾"}, {"n": "美国", "v": "&area=美国"}, {"n": "韩国", "v": "&area=韩国"}, {"n": "日本", "v": "&area=日本"}, {"n": "英国", "v": "&area=英国"}, {"n": "法国", "v": "&area=法国"}, {"n": "泰国", "v": "&area=泰国"}, {"n": "其它", "v": "&area=其它"}]}
        year_f = {"key": "year", "name": "年代", "value": [{"n": "全部", "v": ""}, {"n": "2026", "v": "&year=2026"}, {"n": "2025", "v": "&year=2025"}, {"n": "2024", "v": "&year=2024"}, {"n": "2023", "v": "&year=2023"}, {"n": "2022", "v": "&year=2022"}, {"n": "2021", "v": "&year=2021"}, {"n": "2020", "v": "&year=2020"}, {"n": "2019", "v": "&year=2019"}, {"n": "2018", "v": "&year=2018"}, {"n": "2017", "v": "&year=2017"}, {"n": "2016", "v": "&year=2016"}, {"n": "2015", "v": "&year=2015"}, {"n": "更早", "v": "&year=2014"}]}
        order_f = {"key": "order", "name": "排序", "value": [{"n": "时间", "v": "&order=time"}, {"n": "人气", "v": "&order=hit"}, {"n": "评分", "v": "&order=score"}]}
        filters = {}
        for c in categories:
            filters[c["type_id"]] = [area_f, year_f, order_f]
        html = _get(host + "/", self.cookies)
        if not html:
            return {"class": categories, "list": [], "filters": filters}
        return {"class": categories, "list": _parse_list(html), "filters": filters}
    def homeVideoContent(self):
        return self.homeContent(False)
    def categoryContent(self, tid, pg, filter, extend):
        area = extend.get("area", "") if extend else ""
        year = extend.get("year", "") if extend else ""
        order = extend.get("order", "time") if extend else "time"
        url = f"{host}/search.php?searchtype=5&tid={tid}&page={pg}&order={order}"
        if area: url += f"&area={area}"
        if year: url += f"&year={year}"
        html = _get(url, self.cookies)
        if not html:
            return {"page": int(pg), "pagecount": 99, "limit": 36, "total": 999, "list": []}
        return {"page": int(pg), "pagecount": 99, "limit": 36, "total": 999, "list": _parse_list(html)}
    def detailContent(self, ids):
        result = {"list": []}
        for vid in ids:
            try:
                html = _get(f"{host}/movie/index{vid}.html", self.cookies)
                if not html: continue
                soup = BeautifulSoup(html, "html.parser")
                name_tag = soup.select_one("h1")
                name = name_tag.text.strip() if name_tag else ""
                if not name:
                    name_tag = soup.select_one('.m-content h1')
                    name = name_tag.text.strip() if name_tag else ""
                pic_tag = soup.select_one('.MoviePic img') or soup.select_one('.m-pic img')
                pic = _fix(pic_tag.get("src", "")) if pic_tag else ""
                sources, episodes = [], []
                tabs = soup.select('#playlist li')
                panels = soup.select('.play-box div[id^="stab8"]')
                for i, p in enumerate(panels):
                    src_name = tabs[i].text.strip() if i < len(tabs) and tabs[i].text else f"线路{i+1}"
                    eps = p.select('#episodeList a')
                    ep_list = [f'{a.get_text(strip=True)}${_fix(a.get("href",""))}' for a in eps if a.get("href")]
                    if ep_list:
                        sources.append(src_name)
                        episodes.append("#".join(ep_list))
                result["list"].append({"vod_id": vid, "vod_name": name, "vod_pic": pic, "vod_play_from": "$$$".join(sources), "vod_play_url": "$$$".join(episodes)})
            except:
                continue
        return result
    def searchContent(self, key, quick, pg="1"):
        html = _post(host + "/search.php", {"searchword": key}, self.cookies)
        if not html:
            return {"list": [], "page": int(pg)}
        return {"list": _parse_list(html), "page": int(pg)}
    def playerContent(self, flag, id, vipFlags):
        url = id if id.startswith("http") else _fix(id)
        return {"parse": 1, "url": url, "header": ua}