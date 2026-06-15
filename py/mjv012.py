#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import requests
from lxml import etree

class Spider:
    def getName(self):
        return "AV影院"

    def getDependence(self):
        return ["requests", "lxml"]

    def init(self, extend=""):
        self.host = "https://mjv012.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': self.host + '/zh/',
            'Cookie': 'YES_Eighteen=IamOverEighteenYearsOld; PHPSESSID=uodipq0vp2qc326cvvmjb1sgo0'
        }
        self.categories = [
            {"type_id": "chinese", "type_name": "中文字幕AV"},
            {"type_id": "censored", "type_name": "有碼AV"},
            {"type_id": "reducing-mosaic", "type_name": "無碼破解"},
            {"type_id": "amateurjav", "type_name": "素人AV"},
            {"type_id": "uncensored", "type_name": "無碼AV"}
        ]
        self.video_map = {}

    def _get(self, url):
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            r.encoding = 'utf-8'
            return r.text
        except:
            return None

    def _fix(self, u):
        if not u:
            return ""
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return self.host + u
        return u

    def _parse_list(self, html):
        if not html:
            return []
        tree = etree.HTML(html)
        results = []
        items = tree.xpath('//div[contains(@class, "post video_9s")]')
        for item in items:
            try:
                a = item.xpath('.//h3/a')[0]
                href = a.get("href", "")
                match = re.search(r'/(\d+)/([^/]+)\.html', href)
                if not match:
                    continue
                vid = match.group(1)
                code = match.group(2)
                name = "".join(a.xpath('.//text()')).strip()
                img = item.xpath('.//img')
                pic = ""
                if img:
                    pic = img[0].get("data-src") or img[0].get("src", "")
                    pic = self._fix(pic)
                self.video_map[vid] = code
                results.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": pic,
                })
            except:
                continue
        return results

    def homeContent(self, filter):
        return {"class": self.categories, "list": [], "filters": {}}

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        url = f"{self.host}/zh/{tid}_random/all/index.html?page={page}"
        html = self._get(url)
        return {
            "page": page,
            "pagecount": 50,
            "list": self._parse_list(html) if html else []
        }

    def detailContent(self, ids):
        result = {"list": []}
        for vid in ids:
            code = self.video_map.get(vid, '')
            if not code:
                continue
            
            detail_page_url = f"{self.host}/zh/chinese_content/{vid}/{code}.html"
            html = self._get(detail_page_url)
            if not html:
                continue
            
            tree = etree.HTML(html)
            name = ""
            title_elem = tree.xpath('//div[contains(@class,"archive-title")]//h1/b/text()')
            if title_elem:
                name = title_elem[0].strip()
            if not name:
                title_elem = tree.xpath('//div[contains(@class,"con")]//h1/text()')
                if title_elem:
                    name = title_elem[0].strip()
            if not name:
                title_elem = tree.xpath('//h1/text()')
                if title_elem:
                    name = title_elem[0].strip()
            
            pic = ""
            img_elem = tree.xpath('//div[contains(@class,"thumb")]//img')
            if img_elem:
                pic = img_elem[0].get("data-src") or img_elem[0].get("src", "")
                pic = self._fix(pic)
            
            play_url = ''
            match = re.search(r"mvarr\['\d+_\d+'\]\s*=\s*\[\[[^\]]*,'([^']*play\.php[^']*)'", html)
            if match:
                play_url = self._fix(match.group(1))
            
            if play_url and 'id=' in play_url and play_url.split('id=')[1]:
                final_url = play_url
            else:
                final_url = detail_page_url
            
            result["list"].append({
                "vod_id": vid,
                "vod_name": name if name else code,
                "vod_pic": pic,
                "vod_play_from": "默认线路",
                "vod_play_url": final_url
            })
        return result

    def searchContent(self, key, quick, pg="1"):
        import urllib.parse
        page = int(pg) if pg else 1
        # 使用 fc_search（全部影片搜索）
        encoded_key = urllib.parse.quote(key)
        url = f"{self.host}/zh/fc_search/all/{encoded_key}/{page}.html"
        html = self._get(url)
        if not html:
            return {"list": [], "page": page, "pagecount": 1}
        
        # 解析搜索结果
        tree = etree.HTML(html)
        results = []
        items = tree.xpath('//div[contains(@class, "post video_9s")]')
        for item in items:
            try:
                a = item.xpath('.//h3/a')[0]
                href = a.get("href", "")
                match = re.search(r'/(\d+)/([^/]+)\.html', href)
                if not match:
                    continue
                vid = match.group(1)
                code = match.group(2)
                name = "".join(a.xpath('.//text()')).strip()
                img = item.xpath('.//img')
                pic = ""
                if img:
                    pic = img[0].get("data-src") or img[0].get("src", "")
                    pic = self._fix(pic)
                self.video_map[vid] = code
                results.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": pic,
                })
            except:
                continue
        return {"list": results, "page": page, "pagecount": 1}

    def playerContent(self, flag, id, vipFlags):
        return {"parse": 1, "url": id, "header": self.headers}