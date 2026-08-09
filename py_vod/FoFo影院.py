#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, json
from urllib.parse import quote
from urllib.request import urlopen, Request

BASE = "https://fofoyy.com"
UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": BASE + "/"
}

CAT_MOVIE = [{"n":"全部","v":"0"},{"n":"剧情","v":"1"},{"n":"喜剧","v":"2"},{"n":"动作","v":"3"},{"n":"爱情","v":"4"},{"n":"科幻","v":"5"},{"n":"悬疑","v":"6"},{"n":"惊悚","v":"7"},{"n":"恐怖","v":"8"},{"n":"犯罪","v":"9"},{"n":"同性","v":"10"},{"n":"音乐","v":"11"},{"n":"歌舞","v":"12"},{"n":"传记","v":"13"},{"n":"历史","v":"14"},{"n":"战争","v":"15"},{"n":"西部","v":"16"},{"n":"奇幻","v":"17"},{"n":"冒险","v":"18"},{"n":"灾难","v":"19"},{"n":"武侠","v":"20"},{"n":"伦理","v":"21"}]
CAT_VARIETY = [{"n":"全部","v":"0"},{"n":"真人秀","v":"1"},{"n":"脱口秀","v":"2"},{"n":"纪录片","v":"3"},{"n":"传记","v":"4"},{"n":"歌舞","v":"5"}]
CAT_ANIME = [{"n":"全部","v":"0"},{"n":"剧情","v":"1"},{"n":"喜剧","v":"2"},{"n":"动作","v":"3"},{"n":"爱情","v":"4"},{"n":"科幻","v":"5"},{"n":"悬疑","v":"6"},{"n":"惊悚","v":"7"},{"n":"恐怖","v":"8"},{"n":"犯罪","v":"9"},{"n":"同性","v":"10"},{"n":"音乐","v":"11"},{"n":"歌舞","v":"12"},{"n":"传记","v":"13"},{"n":"历史","v":"14"},{"n":"战争","v":"15"},{"n":"西部","v":"16"},{"n":"奇幻","v":"17"},{"n":"冒险","v":"18"},{"n":"灾难","v":"19"},{"n":"武侠","v":"20"},{"n":"伦理","v":"21"}]
AREA_MOVIE = [{"n":"全部","v":"0"},{"n":"中国大陆","v":"1"},{"n":"美国","v":"2"},{"n":"香港","v":"3"},{"n":"台湾","v":"4"},{"n":"日本","v":"5"},{"n":"韩国","v":"6"},{"n":"英国","v":"7"},{"n":"法国","v":"8"},{"n":"德国","v":"9"},{"n":"意大利","v":"10"},{"n":"西班牙","v":"11"},{"n":"印度","v":"12"},{"n":"泰国","v":"13"},{"n":"俄罗斯","v":"14"},{"n":"伊朗","v":"15"},{"n":"加拿大","v":"16"},{"n":"澳大利亚","v":"17"},{"n":"爱尔兰","v":"18"},{"n":"瑞典","v":"19"},{"n":"巴西","v":"20"},{"n":"丹麦","v":"21"}]
AREA_VARIETY = [{"n":"全部","v":"0"},{"n":"中国大陆","v":"1"},{"n":"美国","v":"2"},{"n":"香港","v":"3"},{"n":"台湾","v":"4"},{"n":"日本","v":"5"},{"n":"韩国","v":"6"}]
AREA_ANIME = [{"n":"全部","v":"0"},{"n":"中国大陆","v":"1"},{"n":"美国","v":"2"},{"n":"日本","v":"5"},{"n":"韩国","v":"6"}]
YEAR_FILTER = [{"n":"全部","v":"0"},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"},{"n":"2009","v":"2009"},{"n":"2008","v":"2008"},{"n":"2007","v":"2007"},{"n":"2006","v":"2006"},{"n":"2005","v":"2005"},{"n":"其他","v":"1"}]
SORT_FILTER = [{"n":"时间","v":"0"},{"n":"人气","v":"1"},{"n":"评分","v":"2"}]

FILTERS = {
    "dianying": [
        {"key":"class","name":"类型","value":CAT_MOVIE},
        {"key":"area","name":"地区","value":AREA_MOVIE},
        {"key":"year","name":"年代","value":YEAR_FILTER},
        {"key":"sort","name":"排序","value":SORT_FILTER}
    ],
    "dianshiju": [
        {"key":"class","name":"类型","value":CAT_MOVIE},
        {"key":"area","name":"地区","value":AREA_MOVIE},
        {"key":"year","name":"年代","value":YEAR_FILTER},
        {"key":"sort","name":"排序","value":SORT_FILTER}
    ],
    "zongyi": [
        {"key":"class","name":"类型","value":CAT_VARIETY},
        {"key":"area","name":"地区","value":AREA_VARIETY},
        {"key":"year","name":"年代","value":YEAR_FILTER},
        {"key":"sort","name":"排序","value":SORT_FILTER}
    ],
    "dongman": [
        {"key":"class","name":"类型","value":CAT_ANIME},
        {"key":"area","name":"地区","value":AREA_ANIME},
        {"key":"year","name":"年代","value":YEAR_FILTER},
        {"key":"sort","name":"排序","value":SORT_FILTER}
    ]
}

def _fetch(url, post_data=None):
    try:
        if post_data:
            data = "&".join(f"{k}={v}" for k, v in post_data.items()).encode()
            req = Request(url, data=data, headers=UA_HEADERS)
        else:
            req = Request(url, headers=UA_HEADERS)
        with urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
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

def _decrypt_char_shift(s):
    return "".join(chr(ord(c) - 1) for c in s)

def _decrypt_val(v):
    if isinstance(v, dict):
        return _decrypt_dict(v)
    if isinstance(v, list):
        return [_decrypt_val(i) for i in v]
    if isinstance(v, str):
        try:
            t = _decrypt_char_shift(v)
            return json.loads(t)
        except:
            return v
    return v

def _decrypt_dict(d):
    result = {}
    if not isinstance(d, dict):
        return d
    for k, v in d.items():
        nk = _decrypt_char_shift(k)
        result[nk] = _decrypt_val(v)
    return result

def _extract_list(html):
    if not html:
        return []
    items = []
    blocks = re.findall(r'<li>(.*?)</li>', html, re.DOTALL)
    for block in blocks:
        href_m = re.search(r'href="([^"]*)"', block)
        if not href_m:
            continue
        href = href_m.group(1)
        vid = href.strip("/").split("/")[-1]
        if not vid.isdigit():
            continue
        img_m = re.search(r'<img[^>]*?src="([^"]*)"', block)
        pic = img_m.group(1) if img_m else ""
        alt_m = re.search(r'alt="([^"]*)"', block)
        h2_m = re.search(r'<h2>.*?<a[^>]*>([^<]*)</a>', block)
        title = h2_m.group(1).strip() if h2_m else (alt_m.group(1).strip() if alt_m else "")
        if not title:
            continue
        note_m = re.search(r'<span[^>]*>(.*?)</span>', block)
        remarks = note_m.group(1).strip() if note_m else ""
        items.append({"vod_id": vid, "vod_name": title, "vod_pic": _fix(pic), "vod_remarks": remarks})
    return items

class Spider:
    def getName(self):
        return "FoFo影院"

    def init(self, extend=""):
        self.site_url = BASE

    def getDependence(self):
        return []

    def destroy(self):
        pass

    def homeVideoContent(self):
        return self.homeContent(True)

    def homeContent(self, filter):
        html = _fetch(BASE + "/")
        result = {"class": [], "list": [], "filters": {}}
        if not html:
            return result
        nav_cats = [("dianying", "电影"), ("dianshiju", "电视剧"), ("zongyi", "综艺"), ("dongman", "动漫")]
        result["class"] = [{"type_id": t, "type_name": n} for t, n in nav_cats]
        result["filters"] = FILTERS
        result["list"] = _extract_list(html)[:24]
        return result

    def categoryContent(self, tid, pg, filter, extend):
        cid, area, year, order = "0", "0", "0", "0"
        if extend and isinstance(extend, str) and extend.strip():
            try:
                ext = json.loads(extend) if extend.strip().startswith("{") else {}
                cid = str(ext.get("class", ext.get("分类", "0")))
                area = str(ext.get("area", ext.get("地区", "0")))
                year = str(ext.get("year", ext.get("年代", "0")))
                order = str(ext.get("sort", ext.get("排序", "0")))
            except:
                pass
        url = f"{BASE}/{tid}/{cid}-{area}-{year}-{order}?page={pg}"
        html = _fetch(url)
        result = {"page": int(pg), "pagecount": 99, "limit": 24, "count": 0, "list": []}
        if html:
            result["list"] = _extract_list(html)
        return result

    def detailContent(self, ids):
        result = {"list": []}
        for vid in ids:
            try:
                cat_paths = ["dianying", "dianshiju", "zongyi", "dongman"]
                html = None
                for cp in cat_paths:
                    html = _fetch(f"{BASE}/{cp}/{vid}")
                    if html and "product-title" in html:
                        break
                if not html:
                    continue
                name_m = re.search(r'product-title[^>]*>([^<]+)', html)
                name = name_m.group(1).strip() if name_m else ""
                if name:
                    name = re.sub(r'<[^>]+>', '', name).strip()
                pic_m = re.search(r'class="thumb"\s+src="([^"]*)"', html)
                if not pic_m:
                    pic_m = re.search(r'src="([^"]*)"[^>]*class="thumb"', html)
                pic = _fix(pic_m.group(1)) if pic_m else ""
                sources, episodes = [], []
                decrypt_m = re.search(r'urlList\s*=\s*decryptDict\((\{.*?\})\)', html, re.DOTALL)
                if decrypt_m:
                    try:
                        js_obj = decrypt_m.group(1)
                        js_obj = re.sub(r"'", '"', js_obj)
                        raw = json.loads(js_obj)
                        data = _decrypt_dict(raw)
                        src_names = data.get("source", [])
                        url_lists = data.get("url_list", [])
                        for idx, src in enumerate(src_names):
                            ep_list = []
                            if idx < len(url_lists):
                                for ep in url_lists[idx]:
                                    sid = ep.get("sid", "") if isinstance(ep, dict) else ""
                                    t = ep.get("title", "") if isinstance(ep, dict) else ""
                                    if not t and isinstance(ep, dict):
                                        nm = ep.get("name", "")
                                        t = _decrypt_char_shift(nm) if isinstance(nm, str) else str(nm)
                                    if not t:
                                        t = "HD"
                                    ep_list.append(f"{t}${sid}")
                            if ep_list:
                                sources.append(src)
                                episodes.append("#".join(ep_list))
                    except:
                        pass
                if not sources:
                    src_blocks = re.findall(r'<dt[^>]*>(.*?)</dt>', html)
                    dl_blocks = re.findall(r'<div class="playlist clearfix">(.*?)</div>', html, re.DOTALL)
                    for i, sb in enumerate(src_blocks):
                        ep_list = []
                        if i < len(dl_blocks):
                            for a_m in re.finditer(r'<a[^>]*onclick="play\((\d+)\)"[^>]*>(.*?)</a>', dl_blocks[i]):
                                ep_list.append(f"{a_m.group(2).strip()}${a_m.group(1)}")
                        if ep_list:
                            sources.append(sb.strip())
                            episodes.append("#".join(ep_list))
                result["list"].append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_play_from": "$$$".join(sources) if sources else "默认",
                    "vod_play_url": "$$$".join(episodes) if episodes else ""
                })
            except:
                continue
        return result

    def searchContent(self, key, quick, pg="1"):
        url = f"{BASE}/search?q={quote(key)}&page={pg}"
        html = _fetch(url)
        result = {"list": [], "page": int(pg)}
        if html:
            result["list"] = _extract_list(html)
        return result

    def playerContent(self, flag, id, vipFlags):
        raw = _fetch(BASE + "/source/", {"id": id})
        url = raw.strip() if raw else ""
        if not url:
            return {"parse": 0, "url": _fix(id), "header": json.dumps(UA_HEADERS)}
        if url.startswith("/"):
            url = BASE + url
        return {"parse": 0, "url": url, "header": json.dumps(UA_HEADERS)}