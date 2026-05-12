import re, json, urllib.parse
try: import requests; from bs4 import BeautifulSoup
except: pass

BASE = "https://58btv.net"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": BASE + "/"}
def _get(url):
    try: r = requests.get(url, headers=UA, timeout=15); r.encoding = "utf-8"; return r.text
    except: return None
def _fix(u):
    if not u: return ""
    if u.startswith("http"): return u
    if u.startswith("//"): return "https:" + u
    return BASE + u

class Spider:
    def init(self, extend=""):
        self.site_url = BASE
        self.headers = UA

    def homeContent(self, filter):
        html = _get(BASE + "/")
        result = {"class": [
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
        ], "list": [], "filters": {}}
        if not html: return result
        soup = BeautifulSoup(html, "html.parser")
        items = []
        for a in soup.select(".x-thumbnail-wrap.x-thumbnail-play"):
            try:
                href = a.get("href", "")
                m = re.search(r"/film-(\d+)", href)
                if not m: continue
                vid = m.group(1)
                img = a.select_one("img")
                pic = ""
                if img: pic = _fix(img.get("data-original") or img.get("src", ""))
                title = a.get("title", "")
                remarks = ""
                grade_span = a.select_one(".video-grade-right")
                if grade_span: remarks = grade_span.get_text(strip=True)
                info_div = a.find_next_sibling("div", class_="video-info")
                if info_div:
                    h5 = info_div.select_one("h5 a")
                    if h5: title = h5.get("title", "") or title
                items.append({"vod_id": vid, "vod_name": title, "vod_pic": pic, "vod_remarks": remarks})
            except: continue
        result["list"] = items[:30]
        return result

    def getDependence(self):
        return []
        
    def homeVideoContent(self):
        return self.homeContent(False)
        
    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        url = BASE + "/" + tid + "/"
        if page > 1: url = BASE + "/" + tid + "/?page=" + str(page)
        html = _get(url)
        result = {"page": page, "pagecount": 99, "limit": 24, "total": 0, "list": []}
        if not html: return result
        soup = BeautifulSoup(html, "html.parser")
        items = []
        for a in soup.select(".x-thumbnail-wrap.x-thumbnail-play"):
            try:
                href = a.get("href", "")
                m = re.search(r"/film-(\d+)", href)
                if not m: continue
                vid = m.group(1)
                img = a.select_one("img")
                pic = ""
                if img: pic = _fix(img.get("data-original") or img.get("src", ""))
                title = a.get("title", "")
                remarks = ""
                grade_span = a.select_one(".video-grade-right")
                if grade_span: remarks = grade_span.get_text(strip=True)
                info_div = a.find_next_sibling("div", class_="video-info")
                if info_div:
                    h5 = info_div.select_one("h5 a")
                    if h5: title = h5.get("title", "") or title
                items.append({"vod_id": vid, "vod_name": title, "vod_pic": pic, "vod_remarks": remarks})
            except: continue
        result["list"] = items
        return result

    def detailContent(self, ids):
        result = {"list": []}
        if not ids: return result
        vid = ids[0]
        html = _get(BASE + "/film-" + vid + ".html")
        if not html: return result
        try:
            soup = BeautifulSoup(html, "html.parser")
            h1 = soup.select_one(".detail-header-2 h1, .detail-header-2 .h2")
            name = h1.get_text(strip=True).replace("線上看", "").strip() if h1 else ""
            h3 = soup.select_one(".detail-header-2 h3")
            sub_title = h3.get_text(strip=True) if h3 else ""
            img = soup.select_one(".detail-poster-2 img")
            pic = _fix(img.get("src", "")) if img else ""
            bread = soup.select(".breadcrumb-item")
            type_name = bread[-2].get_text(strip=True) if len(bread) >= 2 else ""
            desc_elem = soup.select_one(".detail-intro")
            desc = desc_elem.get_text(strip=True).replace("劇情介紹：", "").strip() if desc_elem else ""
            sources, episodes = [], []
            for tab_ul in soup.select(".detail-content.tab-content"):
                panes = tab_ul.select(".tab-pane")
                for pane in panes:
                    links = pane.select("a")
                    if not links: continue
                    ep_list = []
                    src_name = "在線播放"
                    for a in links:
                        a_text = a.get_text(strip=True)
                        a_href = a.get("href", "")
                        ep_list.append(a_text + "$" + a_href)
                    if ep_list:
                        sources.append(src_name)
                        episodes.append("#".join(ep_list))
            if not sources:
                links = soup.select(".detail-play-list a")
                if links:
                    ep_list = [a.get_text(strip=True) + "$" + a.get("href","") for a in links]
                    sources.append("在線播放")
                    episodes.append("#".join(ep_list))
            info_items = soup.select(".detail-info-2 li")
            director = actor = area = year = ""
            for li in info_items:
                label = li.select_one("label")
                if not label: continue
                lbl = label.get_text(strip=True)
                if "導演" in lbl:
                    spans = li.select("span")
                    director = ",".join(s.get_text(strip=True) for s in spans)
                if "主演" in lbl:
                    spans = li.select("span")
                    actor = ",".join(s.get_text(strip=True) for s in spans)
                if "地區" in lbl:
                    spans = li.select("span")
                    area = ",".join(s.get_text(strip=True) for s in spans)
                if "年份" in lbl:
                    spans = li.select("span")
                    year = ",".join(s.get_text(strip=True) for s in spans)
            result["list"].append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "type_name": type_name,
                "vod_content": desc,
                "vod_director": director,
                "vod_actor": actor,
                "vod_area": area,
                "vod_year": year,
                "vod_play_from": "$$$".join(sources),
                "vod_play_url": "$$$".join(episodes),
            })
        except: pass
        return result

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        url = BASE + "/search?q=" + urllib.parse.quote(key)
        if page > 1: url += "&page=" + str(page)
        html = _get(url)
        result = {"list": []}
        if not html: return result
        soup = BeautifulSoup(html, "html.parser")
        items = []
        for a in soup.select(".x-thumbnail-wrap.x-thumbnail-play"):
            try:
                href = a.get("href", "")
                m = re.search(r"/film-(\d+)", href)
                if not m: continue
                vid = m.group(1)
                img = a.select_one("img")
                pic = ""
                if img: pic = _fix(img.get("data-original") or img.get("src", ""))
                title = a.get("title", "")
                remarks = ""
                grade_span = a.select_one(".video-grade-right")
                if grade_span: remarks = grade_span.get_text(strip=True)
                items.append({"vod_id": vid, "vod_name": title, "vod_pic": pic, "vod_remarks": remarks})
            except: continue
        result["list"] = items
        return result

    def playerContent(self, flag, id, vipFlags):
        url = id if id.startswith("http") else _fix(id)
        return {"parse": 1, "url": url, "header": UA}