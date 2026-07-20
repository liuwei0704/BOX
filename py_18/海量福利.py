#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, json, urllib.parse
from bs4 import BeautifulSoup
from base.spider import Spider

class Spider(Spider):
    def getName(self): return "海量福利"

    def init(self, extend=""):
        self.site_url = "https://12345-bet.cfd"
        self.limit = 24
        self.headers = {"User-Agent": "Mozilla/5.0", "Referer": self.site_url}
        self.categories = [
            {"type_id": "1", "type_name": "国产电影"}, {"type_id": "6", "type_name": "日韩无码"},
            {"type_id": "2", "type_name": "国产视频"}, {"type_id": "7", "type_name": "SM调教"},
            {"type_id": "3", "type_name": "制服诱惑"}, {"type_id": "8", "type_name": "萝莉少女"},
            {"type_id": "4", "type_name": "女同性恋"}, {"type_id": "13", "type_name": "日本无码"},
            {"type_id": "14", "type_name": "激情动漫"}, {"type_id": "15", "type_name": "网暴黑料"},
            {"type_id": "9", "type_name": "女优明星"}, {"type_id": "16", "type_name": "理伦三级"},
            {"type_id": "10", "type_name": "欧美系列"}, {"type_id": "11", "type_name": "强奸乱伦"},
            {"type_id": "12", "type_name": "明星换脸"},
        ]

    def _parse_video_card(self, card):
        link_elem = card.select_one("a.thumbnail") or card
        href = link_elem.get("href", "")
        m = re.search(r"/vod/detail/id/(\d+)\.html", href)
        if not m: return None
        vod_id = m.group(1)
        title_elem = card.select_one(".video-info h5 a") or card.select_one("a[target='_blank']")
        vod_name = title_elem.get_text(strip=True) if title_elem else ""
        img_elem = card.select_one("img.loadi") or card.select_one("img")
        vod_pic = (img_elem.get("data-original") or img_elem.get("data-src") or img_elem.get("src", "")) if img_elem else ""
        tag_elem = card.select_one(".video-grade") or card.select_one("p")
        vod_remarks = tag_elem.get_text(strip=True) if tag_elem else ""
        return {"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic, "vod_remarks": vod_remarks}

    def homeContent(self, filter):
        resp = self.fetch(self.site_url + "/", headers=self.headers)
        video_list = []
        if resp:
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(".thumbnail-group li") or soup.select(".appel-max li")
            for card in cards[:self.limit]:
                item = self._parse_video_card(card)
                if item: video_list.append(item)
        return {"class": self.categories, "list": video_list, "filters": {}}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        url = f"{self.site_url}/index.php/vod/type/id/{tid}/page/{page}.html"
        resp = self.fetch(url, headers=self.headers)
        if not resp: return {"list": [], "page": page, "pagecount": 1, "limit": self.limit, "total": 0}
        soup = BeautifulSoup(resp.text, "html.parser")
        video_list = [item for card in soup.select(".thumbnail-group li") for item in [self._parse_video_card(card)] if item]
        pagecount = 1
        for a in soup.select(".pagination a") or soup.select(".page-link"):
            txt = a.get_text(strip=True)
            if txt.isdigit(): pagecount = max(pagecount, int(txt))
        return {"list": video_list, "page": page, "pagecount": pagecount, "limit": self.limit, "total": 0}

    def detailContent(self, ids):
        if not ids: return {"list": []}
        vod_id = ids[0]
        url = f"{self.site_url}/index.php/vod/detail/id/{vod_id}.html"
        resp = self.fetch(url, headers=self.headers)
        if not resp: return {"list": []}
        soup = BeautifulSoup(resp.text, "html.parser")
        vod_name = "".join([t.get_text(strip=True) for t in soup.select("title")]) or ""
        if vod_name and "-" in vod_name:
            vod_name = vod_name.rsplit("-", 1)[0].strip()
        if not vod_name:
            bread = soup.select_one(".breadcrumbs span")
            vod_name = bread.get_text(strip=True) if bread else ""
        img_elem = soup.select_one(".detail-poster img")
        vod_pic = (img_elem.get("data-original") or img_elem.get("src", "")) if img_elem else ""
        desc_elems = soup.select(".detail-actor li")
        vod_remarks = ""
        for li in desc_elems:
            label = li.select_one("label")
            if label and "剧集" in label.get_text(): vod_remarks = li.get_text(strip=True).replace("剧集:", "").replace("剧集：", "").strip()
        tab_items = soup.select(".detail-tab-zt li a")
        play_containers = soup.select(".detail-play-list")
        play_from_list, play_url_list = [], []
        if tab_items and play_containers and len(tab_items) == len(play_containers):
            for idx, tab in enumerate(tab_items):
                source_name = tab.get_text(strip=True)
                eps = [f"{a.get_text(strip=True)}${a.get('href','')}" for a in play_containers[idx].select("li a") if a.get("href")]
                if eps: play_from_list.append(source_name); play_url_list.append("#".join(eps))
        else:
            all_eps = soup.select(".detail-play-list li a")
            if all_eps:
                eps = [f"{a.get_text(strip=True)}${a.get('href','')}" for a in all_eps if a.get("href")]
                if eps: play_from_list.append("默认"); play_url_list.append("#".join(eps))
        return {"list": [{"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic, "vod_remarks": vod_remarks, "vod_play_from": "$$$".join(play_from_list), "vod_play_url": "$$$".join(play_url_list)}]}

    def searchContent(self, key, quick, pg="1"):
        return {"list": [], "page": int(pg) if pg else 1, "pagecount": 1}

    def playerContent(self, flag, id, vipFlags):
        url = id if id.startswith("http") else self.site_url + id
        return {"parse": 1, "url": url, "header": self.headers}