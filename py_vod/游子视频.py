import json
import requests
import re
from bs4 import BeautifulSoup

class Spider():
    host = "https://www.youzisp.tv"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.youzisp.tv/"
    }

    type_map = {
        "dianying": ("1", "电影"),
        "dianshiju": ("2", "电视剧"),
        "zongyi": ("3", "综艺"),
        "dongman": ("4", "动漫"),
        "jilupian": ("5", "纪录片"),
        "wuyejuchang": ("6", "午夜剧场"),
    }

    def getName(self):
        return "游子视频"

    def init(self, extend=""):
        pass

    def getDependence(self):
        return []

    def _parse_list(self, soup):
        vod_list = []
        items = soup.select('a.module-poster-item')
        for item in items:
            vod_id = item.get('href', '').replace('/voddetail/', '').replace('.html', '')
            vod_name = item.get('title', '未知')
            img = item.select_one('img')
            vod_pic = img.get('data-original') or img.get('src', '') if img else ''
            if vod_pic.startswith('/'):
                vod_pic = self.host + vod_pic
            elif vod_pic and not vod_pic.startswith('http'):
                vod_pic = self.host + '/' + vod_pic
            note = item.select_one('.module-item-note')
            vod_remarks = note.text.strip() if note else ''
            if vod_id:
                vod_list.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })
        return vod_list

    def homeContent(self, filter):
        result = {"class": [], "list": []}
        for slug, (tid, tname) in self.type_map.items():
            result["class"].append({"type_id": tid, "type_name": tname})
        try:
            res = requests.get(self.host, headers=self.header, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            result["list"] = self._parse_list(soup)[:20]
        except Exception as e:
            print(f"homeContent error: {e}")
        return result

    def homeVideoContent(self):
        try:
            res = requests.get(self.host, headers=self.header, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            return {"list": self._parse_list(soup)[:20]}
        except Exception as e:
            print(f"homeVideoContent error: {e}")
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        slug = None
        for s, (t, _) in self.type_map.items():
            if t == str(tid):
                slug = s
                break
        if not slug:
            return {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}
        url = f"{self.host}/vodshow/{slug}-----------.html?page={pg}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            vod_list = self._parse_list(soup)
            return {
                "list": vod_list,
                "page": int(pg),
                "pagecount": 999,
                "limit": len(vod_list),
                "total": len(vod_list) * 999
            }
        except Exception as e:
            print(f"categoryContent error: {e}")
            return {"list": [], "page": int(pg), "pagecount": 1, "limit": 0, "total": 0}

    def detailContent(self, ids):
        vid = ids[0]
        url = f"{self.host}/voddetail/{vid}.html"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            html = res.text
            soup = BeautifulSoup(html, 'html.parser')
            vod_name = "未知"
            h_tag = soup.select_one('h1') or soup.select_one('.module-info-title h2')
            if h_tag:
                vod_name = h_tag.text.strip()
            play_from = []
            tab_items = soup.select('.module-tab-item[data-dropdown-value]')
            for tab in tab_items:
                dv = tab.get('data-dropdown-value', '')
                if dv:
                    play_from.append(dv)
            if not play_from:
                play_from = ["默认线路"]
            play_blocks = soup.select('.module-play-list')
            play_url = []
            for block in play_blocks:
                links = block.select('a.module-play-list-link')
                eps_parts = []
                for a in links:
                    href = a.get('href', '')
                    span = a.select_one('span')
                    name = span.text.strip() if span else '未知'
                    if href:
                        eps_parts.append(f"{name}${href}")
                if eps_parts:
                    play_url.append("#".join(eps_parts))
            if not play_url:
                play_url = [""]
            play_from = play_from[:len(play_url)]
            return {"list": [{
                "vod_id": vid,
                "vod_name": vod_name,
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_url)
            }]}
        except Exception as e:
            print(f"detailContent error: {e}")
            return {"list": [{"vod_id": vid, "vod_name": "未知", "vod_play_from": "默认线路", "vod_play_url": ""}]}

    def searchContent(self, key, quick, pg=1):
        try:
            res = requests.get(
                f"{self.host}/index.php/ajax/suggest?mid=1&wd={key}&page={pg}",
                headers=self.header, timeout=10
            )
            data = res.json()
            vod_list = []
            for item in data.get("list", []):
                vod_pic = item.get("pic", "")
                if vod_pic.startswith('/'):
                    vod_pic = self.host + vod_pic
                elif vod_pic and not vod_pic.startswith('http'):
                    vod_pic = self.host + '/' + vod_pic
                vod_list.append({
                    "vod_id": str(item.get("id", "")),
                    "vod_name": item.get("name", "未知"),
                    "vod_pic": vod_pic,
                    "vod_remarks": item.get("remarks", "")
                })
            return {"list": vod_list}
        except Exception as e:
            print(f"searchContent error: {e}")
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        p_url = self.host + id if id.startswith('/') else id
        return {
            "parse": 1,
            "url": p_url,
            "header": {
                "Referer": self.host,
                "User-Agent": self.header["User-Agent"]
            }
        }