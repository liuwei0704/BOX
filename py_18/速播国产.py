# coding: utf-8
# TVBox/FongMi 爬虫 - 速播国产 (dingbic.cfd)
# 类型: HTML静态站解析
# 支持: 首页推荐、分类列表、详情页、搜索、播放

import re
import html
from urllib.parse import urljoin, quote
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def getName(self):
        return "速播国产"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.host = "https://www.dingbic.cfd"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.host,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        self.classes = [
            {"type_id": "1", "type_name": "国产主播"},
            {"type_id": "2", "type_name": "国产传媒"},
            {"type_id": "3", "type_name": "韩国主播"},
            {"type_id": "4", "type_name": "国产视频"},
            {"type_id": "7", "type_name": "国产明星"},
            {"type_id": "8", "type_name": "中文字幕"},
            {"type_id": "9", "type_name": "三级电影"},
            {"type_id": "13", "type_name": "强奸乱伦"}
        ]

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers)
            if resp and resp.status_code == 200:
                return resp.text
            return None
        except Exception as e:
            self.log({"action": "fetch_fail", "url": url, "error": str(e)})
            return None

    def _clean_text(self, text):
        """清理文本：去除HTML标签，解码实体，去除空白"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        text = re.sub(r'[\r\n\t]+', ' ', text)
        return text.strip()

    def _parse_video_items(self, html):
        items = []
        if not html:
            return items
        pattern = r'<li>.*?<a class="thumbnail" href="([^"]+)".*?<img src="([^"]+)" alt="([^"]+)".*?<h5><a href="[^"]+" title="[^"]*">([^<]+)</a></h5>.*?<p>([^<]+)</p>'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            link, img, alt, title, info = match
            parts = info.split('-')
            category = parts[0].strip() if len(parts) > 0 else ""
            date = parts[1].strip() if len(parts) > 1 else ""
            category = self._clean_text(category)
            date = self._clean_text(date)
            title_clean = self._clean_text(title)
            vid_match = re.search(r'/vod/detail/id/(\d+)\.html', link)
            vid = vid_match.group(1) if vid_match else ""
            if vid:
                remarks = f"{category} {date}".strip()
                if not remarks:
                    remarks = self._clean_text(info)
                items.append({
                    "vod_id": vid,
                    "vod_name": title_clean,
                    "vod_pic": img,
                    "vod_remarks": remarks
                })
        return items

    def _parse_detail(self, html):
        result = {"title": "", "pic": "", "desc": "", "play_from": "", "play_url": ""}
        if not html:
            return result
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if title_match:
            result["title"] = self._clean_text(title_match.group(1))
        pic_match = re.search(r'<img[^>]+class="[^"]*thumbnail[^"]*"[^>]+src="([^"]+)"', html)
        if not pic_match:
            pic_match = re.search(r'<img[^>]+src="([^"]+\.(?:jpg|png|jpeg|gif))"[^>]*>', html)
        if pic_match:
            result["pic"] = pic_match.group(1)
        desc_match = re.search(r'<div[^>]+class="[^"]*desc[^"]*"[^>]*>([^<]+)</div>', html, re.DOTALL)
        if not desc_match:
            desc_match = re.search(r'<p[^>]+class="[^"]*content[^"]*"[^>]*>([^<]+)</p>', html, re.DOTALL)
        if desc_match:
            result["desc"] = self._clean_text(desc_match.group(1))
        play_urls = []
        iframe_pattern = r'<iframe[^>]+src="([^"]+)"'
        for iframe_url in re.findall(iframe_pattern, html):
            if iframe_url and not iframe_url.startswith('javascript:'):
                play_urls.append(iframe_url)
        if not play_urls:
            video_pattern = r'["\']([^"\']+\.(?:m3u8|mp4|ts))["\']'
            for vurl in re.findall(video_pattern, html):
                if vurl and not vurl.startswith('data:'):
                    play_urls.append(vurl)
        if not play_urls:
            play_match = re.search(r'<a[^>]+href="([^"]*play[^"]*)"', html)
            if play_match:
                play_urls.append(play_match.group(1))
        if play_urls:
            unique_urls = []
            seen = set()
            for url in play_urls:
                full_url = urljoin(self.host, url)
                if full_url not in seen:
                    seen.add(full_url)
                    unique_urls.append(full_url)
            result["play_from"] = "默认线路"
            result["play_url"] = "$$$".join(unique_urls[:20])
            if len(unique_urls) > 1:
                result["play_from"] = "线路1$$$线路2$$$线路3"
        return result

    def homeContent(self, filter):
        class_list = [{"type_id": c["type_id"], "type_name": c["type_name"]} for c in self.classes]
        filters = {}
        if filter:
            for c in self.classes:
                filters[c["type_id"]] = [
                    {"key": "order", "name": "排序", "value": [{"n": "最新", "v": "time"}, {"n": "最热", "v": "hits"}]}
                ]
        return {"class": class_list, "filters": filters}

    def homeVideoContent(self):
        html = self._fetch_html(self.host)
        if not html:
            return {"list": []}
        items = self._parse_video_items(html)
        seen = set()
        unique_items = []
        for item in items:
            if item["vod_id"] not in seen:
                seen.add(item["vod_id"])
                unique_items.append(item)
        return {"list": unique_items[:40]}

    def categoryContent(self, tid, pg, filter, extend):
        pg = pg or "1"
        page = int(pg)
        if tid in ["1", "2", "3", "4", "7", "8", "9", "13"]:
            url = f"{self.host}/index.php/vod/type/id/{tid}.html"
            if page > 1:
                url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        else:
            url = f"{self.host}/index.php/vod/type/id/1.html"
            if page > 1:
                url = f"{self.host}/index.php/vod/type/id/1/page/{page}.html"
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}
        items = self._parse_video_items(html)
        pagecount = 1
        page_match = re.search(r'共\d+条数据,当前\d+/(\d+)页', html)
        if not page_match:
            page_match = re.search(r'共\s*(\d+)\s*页', html)
        if page_match:
            pagecount = int(page_match.group(1))
        return {"list": items, "page": page, "pagecount": pagecount, "limit": 20, "total": pagecount * 20}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = ids[0]
        url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        detail = self._parse_detail(html)
        vod = {
            "vod_id": vid,
            "vod_name": detail["title"] or f"视频{vid}",
            "vod_pic": detail["pic"] or "",
            "vod_content": detail["desc"] or "暂无简介",
            "vod_play_from": detail["play_from"] or "默认",
            "vod_play_url": detail["play_url"] or ""
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        if not key or not key.strip():
            return {"list": []}
        pg = pg or "1"
        page = int(pg)
        if page > 1:
            url = f"{self.host}/index.php/vod/search/{page}.html?wd={quote(key)}"
        else:
            url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}"
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        items = self._parse_video_items(html)
        pagecount = 1
        page_match = re.search(r'共\d+条数据,当前\d+/(\d+)页', html)
        if not page_match:
            page_match = re.search(r'共\s*(\d+)\s*页', html)
        if page_match:
            pagecount = int(page_match.group(1))
        return {"list": items, "page": page, "pagecount": pagecount}

    def playerContent(self, flag, id, vipFlags):
        if id.startswith('http') and ('.m3u8' in id or '.mp4' in id):
            return {"parse": 0, "url": id, "header": self.headers}
        if id.startswith('http'):
            try:
                html = self._fetch_html(id)
                if html:
                    iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', html)
                    if iframe_match:
                        iframe_url = iframe_match.group(1)
                        if iframe_url.startswith('http'):
                            return {"parse": 1, "url": iframe_url, "header": self.headers}
                    video_match = re.search(r'["\']([^"\']+\.(?:m3u8|mp4))["\']', html)
                    if video_match:
                        return {"parse": 0, "url": video_match.group(1), "header": self.headers}
                    js_match = re.search(r'url\s*[:=]\s*["\']([^"\']+)["\']', html)
                    if js_match:
                        return {"parse": 0, "url": js_match.group(1), "header": self.headers}
            except Exception as e:
                self.log({"action": "player_fetch_fail", "url": id, "error": str(e)})
        return {"parse": 1, "url": id, "header": self.headers}

    def localProxy(self, param):
        target = param.get("target", "")
        if not target:
            return [404, "text/plain", "Not Found"]
        if '.m3u8' in target:
            try:
                resp = self.fetch(target, headers=self.headers)
                if resp and resp.status_code == 200:
                    return [200, "application/vnd.apple.mpegurl", resp.text, {"Cache-Control": "no-store"}]
            except:
                pass
        return [404, "text/plain", "Proxy not available"]

    def destroy(self):
        pass