# -*- coding: utf-8 -*-
"""
兴趣院 - TVBox爬虫源
基于 FongMi 官方 Spider 文档
"""

import re
import urllib.parse
from base.spider import Spider


class Spider(Spider):
    def getName(self):
        return "兴趣院"

    def init(self, context=None, extend=""):
        """官方签名：init(Context context, String extend)"""
        self.context = context
        self.host = "https://m.xxxdd1.top"
        self.ua = "Mozilla/5.0 (Linux; Android 14; 22127RK46C Build/UKQ1.230804.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36"
        self.headers = {
            "User-Agent": self.ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "视频"},
            {"type_id": "5", "type_name": "小说"},
            {"type_id": "6", "type_name": "女主播"},
            {"type_id": "7", "type_name": "AI换脸"},
            {"type_id": "8", "type_name": "日韩视频"},
            {"type_id": "9", "type_name": "国产视频"},
            {"type_id": "10", "type_name": "国产精品"},
            {"type_id": "11", "type_name": "中文字幕"},
            {"type_id": "12", "type_name": "强奸乱伦"},
            {"type_id": "20", "type_name": "无码专区"},
            {"type_id": "38", "type_name": "欧美性爱"},
            {"type_id": "40", "type_name": "熟女人妻"},
            {"type_id": "41", "type_name": "女同性恋"},
            {"type_id": "42", "type_name": "卡通动漫"},
            {"type_id": "43", "type_name": "少女萝莉"},
            {"type_id": "44", "type_name": "制服丝袜"},
            {"type_id": "45", "type_name": "三级伦理"},
            {"type_id": "46", "type_name": "巨乳美乳"},
            {"type_id": "47", "type_name": "精品综合"},
            {"type_id": "48", "type_name": "VR视角"},
        ]
        self.filters = {}
        for c in self.classes:
            self.filters[c["type_id"]] = []

    def getDependence(self):
        return []

    def _fix_url(self, url):
        if not url:
            return ""
        url = str(url).replace("\\/", "/").strip()
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("http"):
            return url
        if url.startswith("/"):
            return self.host + url
        return self.host + "/" + url

    def _fetch_text(self, url):
        """根据官方文档使用 self.fetch"""
        full = self._fix_url(url)
        try:
            r = self.fetch(full, headers=self.headers, timeout=15)
            # 尝试多种方式提取文本
            if r is None:
                return ""
            if hasattr(r, 'text'):
                return r.text
            if hasattr(r, 'content'):
                return r.content.decode('utf-8', errors='ignore')
            if hasattr(r, 'body'):
                return str(r.body)
            if hasattr(r, 'toString'):
                return r.toString()
            # 如果是 Java 的 String
            if isinstance(r, str):
                return r
            return str(r)
        except Exception as e:
            return ""

    def _parse_videos(self, html):
        result = []
        if not html:
            return result
        pattern = r'<a[^>]*href="(/voddetail/(\d+)\.html)"[^>]*title="([^"]*)"[^>]*(?:data-original|src)="([^"]*)"'
        matches = re.findall(pattern, html)
        seen = set()
        for href, vid, title, pic in matches:
            if vid and vid not in seen:
                seen.add(vid)
                result.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": self._fix_url(pic),
                    "vod_remarks": "",
                })
        return result

    def _parse_paging(self, html):
        result = {"page": 1, "pagecount": 1}
        if not html:
            return result
        m = re.search(r'<a[^>]*class="[^"]*btn-warm[^"]*"[^>]*>(\d+)/(\d+)</a>', html)
        if m:
            result["page"] = int(m.group(1))
            result["pagecount"] = int(m.group(2))
        return result

    def homeContent(self, filter=False):
        """首页分类 - 零网络，纯本地返回"""
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐"""
        html = self._fetch_text(self.host + "/")
        return {"list": self._parse_videos(html)[:20]}

    def categoryContent(self, tid, pg="1", filter=False, extend=None):
        """分类列表"""
        pg = str(pg or "1")
        if pg == "1":
            url = self.host + f"/vodtype/{tid}.html"
        else:
            url = self.host + f"/vodtype/{tid}-{pg}.html"
        html = self._fetch_text(url)
        result = {"list": self._parse_videos(html), "page": 1, "pagecount": 1, "total": 0}
        paging = self._parse_paging(html)
        result["page"] = paging.get("page", int(pg))
        result["pagecount"] = paging.get("pagecount", 1)
        return result

    def detailContent(self, ids):
        """详情"""
        result = {"list": []}
        if not ids:
            return result
        vid = str(ids[0])
        html = self._fetch_text(self.host + f"/voddetail/{vid}.html")
        if not html:
            return result
        title = ""
        m = re.search(r'<span[^>]*class="[^"]*vod-title[^"]*"[^>]*data-origin="([^"]*)"', html)
        if m:
            title = m.group(1)
        else:
            m = re.search(r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>', html)
            if m:
                title = m.group(1).strip()
        pic = ""
        m = re.search(r'<img[^>]*class="[^"]*lazyload[^"]*"[^>]*data-original="([^"]+)"', html)
        if m:
            pic = m.group(1)
        else:
            m = re.search(r'<img[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*src="([^"]+)"', html)
            if m:
                pic = m.group(1)
        desc = ""
        m = re.search(r'<span[^>]*class="[^"]*sketch[^"]*"[^>]*>([^<]+)</span>', html)
        if m:
            desc = m.group(1).strip()
        play_url = ""
        m = re.search(r'<a[^>]*class="[^"]*btn-warm[^"]*"[^>]*href="([^"]+)"', html)
        if m:
            play_url = m.group(1)
        if not play_url:
            play_url = f"/vodplay/{vid}-1-1.html"
        result["list"].append({
            "vod_id": vid,
            "vod_name": title or "未知",
            "vod_pic": self._fix_url(pic),
            "vod_content": desc,
            "vod_play_from": "极速A线",
            "vod_play_url": f"极速A线${play_url}",
        })
        return result

    def searchContent(self, key, quick=False, pg="1"):
        """搜索"""
        result = {"list": [], "page": 1, "pagecount": 1}
        if not key:
            return result
        pg = str(pg or "1")
        enc = urllib.parse.quote(key)
        if pg == "1":
            url = self.host + f"/vodsearch/-------------.html?wd={enc}"
        else:
            url = self.host + f"/vodsearch/-------------.html?wd={enc}&page={pg}"
        html = self._fetch_text(url)
        result["list"] = self._parse_videos(html)
        paging = self._parse_paging(html)
        result["page"] = paging.get("page", int(pg))
        result["pagecount"] = paging.get("pagecount", 1)
        return result

    def playerContent(self, flag, id, vipFlags=None):
        """播放"""
        if not id:
            return {"parse": 1, "url": ""}
        if id.startswith("http") and (id.endswith(".m3u8") or id.endswith(".mp4")):
            return {"parse": 0, "url": id, "header": self.headers}
        play_url = self._fix_url(id)
        html = self._fetch_text(play_url)
        if not html:
            return {"parse": 1, "url": play_url}
        m = re.search(r'<iframe[^>]*src="([^"]+)"', html)
        if m:
            src = m.group(1)
            m2 = re.search(r'[?&]url=([^&"\']+)', src)
            if m2:
                video = urllib.parse.unquote(m2.group(1))
                if video.endswith(".m3u8") or video.endswith(".mp4"):
                    return {"parse": 0, "url": video, "header": self.headers}
        patterns = [
            r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"',
            r'"src"\s*:\s*"([^"]+\.m3u8[^"]*)"',
        ]
        for p in patterns:
            m = re.search(p, html, re.IGNORECASE)
            if m:
                video = m.group(1)
                if video.startswith("http") or video.startswith("//"):
                    return {"parse": 0, "url": self._fix_url(video), "header": self.headers}
        return {"parse": 1, "url": play_url}

    def destroy(self):
        pass