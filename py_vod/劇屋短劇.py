# coding: utf-8
# 剧屋 - https://m.juwu.tv
# 站点类型: 苹果CMS HTML站
# 分类: 短剧(1)、电影(2)
# 播放: 直接从video标签提取m3u8直链，parse=0
# 无筛选功能

import re
import json
import urllib.request
import urllib.parse
import gzip
import zlib
from urllib.parse import urljoin, urlparse, quote

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.site_url = "https://m.juwu.tv"
        self.play_domain = "https://play.juwu.tv"
        self.ua = "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.classes = [
            {"type_id": "1", "type_name": "短剧"},
            {"type_id": "2", "type_name": "电影"},
        ]
        self.filters = {}  # 无筛选功能
        self.headers = {
            "User-Agent": self.ua,
            "Referer": self.site_url + "/"
        }

    def getName(self):
        return "剧屋"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        return self.categoryContent("1", "1", False, {})

    def _fetch(self, url):
        """优先使用 self.fetch()，备用 urllib.request"""
        headers = {
            "User-Agent": self.ua,
            "Referer": self.site_url + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        try:
            resp = self.fetch(url, headers=headers, timeout=15)
            if resp and hasattr(resp, 'text') and resp.text:
                return resp.text
        except Exception as e:
            pass
        try:
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=15)
            data = response.read()
            encoding = response.headers.get('Content-Encoding', '')
            if 'gzip' in encoding:
                data = gzip.decompress(data)
            elif 'deflate' in encoding:
                data = zlib.decompress(data, -zlib.MAX_WBITS)
            charset = 'utf-8'
            content_type = response.headers.get('Content-Type', '')
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[-1].strip()
            return data.decode(charset, errors='ignore')
        except Exception as e:
            pass
        return ""

    def _parse_extend(self, extend):
        if not extend:
            return {}
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            try:
                return json.loads(extend)
            except:
                clean = extend.strip().strip('{}')
                result = {}
                if clean:
                    for part in clean.split(','):
                        if '=' in part:
                            key, val = part.split('=', 1)
                            result[key.strip()] = val.strip()
                return result
        return {}

    def categoryContent(self, tid, pg="1", filter=False, extend=None):
        page = str(pg or "1")
        url = f"{self.site_url}/vod-show/{tid}--------{page}---/"
        
        html = self._fetch(url)
        if not html:
            return {"list": [], "page": int(page), "pagecount": 1, "total": 0}

        videos = []
        blocks = re.findall(r'<a href="/vod/(\d+)/"[^>]*>.*?<div class="module-item-note">([^<]*)</div>.*?<img[^>]*data-original="([^"]+)"[^>]*>.*?<div class="module-poster-item-title">([^<]*)</div>', html, re.S)
        
        for match in blocks:
            vid, note, pic, title = match
            if pic and '43f8a205f442c9676dd5e01514daba6f' in pic:
                continue
            videos.append({
                "vod_id": vid,
                "vod_name": title.strip(),
                "vod_pic": pic,
                "vod_remarks": note.strip(),
            })

        pagecount = 1
        last_match = re.search(r'<a[^>]*href="[^"]*--------(\d+)---/"[^>]*>尾页</a>', html)
        if last_match:
            pagecount = int(last_match.group(1))
        else:
            page_nums = re.findall(r'<a[^>]*href="[^"]*--------(\d+)---/"[^>]*>', html)
            if page_nums:
                pagecount = max([int(n) for n in page_nums if n.isdigit()])
            else:
                page_match = re.search(r'第(\d+)页.*?共(\d+)页', html)
                if page_match:
                    pagecount = int(page_match.group(2))

        return {
            "list": videos,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 20,
            "total": len(videos) * pagecount if pagecount > 1 else len(videos)
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vod_id = str(ids[0]) if isinstance(ids, list) else str(ids)
        url = f"{self.site_url}/vod/{vod_id}/"
        html = self._fetch(url)
        if not html:
            return {"list": []}

        title_match = re.search(r'<h1>([^<]*)</h1>', html)
        title = title_match.group(1).strip() if title_match else ""

        pic_match = re.search(r'<div class="module-item-pic"><img[^>]*src="([^"]+)"', html)
        pic = pic_match.group(1) if pic_match else ""

        remark_match = re.search(r'<div class="module-info-item"><span class="module-info-item-title">备注：</span>\s*<div class="module-info-item-content">([^<]*)</div>', html)
        if not remark_match:
            remark_match = re.search(r'<div class="module-info-item"><span class="module-info-item-title">集数：</span>\s*<div class="module-info-item-content">([^<]*)</div>', html)
        remark = remark_match.group(1).strip() if remark_match else ""

        content_match = re.search(r'<div class="module-info-introduction-content">\s*<p>([^<]*)</p>', html)
        content = content_match.group(1).strip() if content_match else ""

        lines = {}
        
        line_pattern = r'<div class="module-tab-item tab-item[^"]*" data-sid="(\d+)"[^>]*>.*?<span>([^<]*)</span>'
        line_matches = re.findall(line_pattern, html)
        
        if not line_matches:
            line_pattern2 = r'<div[^>]*class="swiper-slide module-tab-item tab-item[^"]*"[^>]*>\s*([^<]*?)<small'
            line_matches2 = re.findall(line_pattern2, html)
            if line_matches2:
                line_matches = [(str(idx+1), name.strip()) for idx, name in enumerate(line_matches2)]

        if not line_matches:
            line_matches = [("1", "线路")]

        for sid, line_name in line_matches:
            pane_pattern = rf'<div class="module-list sort-list tab-list play-tab-list[^"]*" id="pane{sid}">.*?<div class="module-play-list-content[^>]*>(.*?)</div>\s*</div>'
            pane_match = re.search(pane_pattern, html, re.S)
            if pane_match:
                content_html = pane_match.group(1)
                ep_pattern = rf'<a[^>]*href="(/vod-play/\d+-{sid}-\d+/)"[^>]*><span>([^<]*)</span>'
                ep_matches = re.findall(ep_pattern.format(sid=sid), content_html)
                if ep_matches:
                    ep_urls = []
                    for ep_href, ep_name in ep_matches:
                        ep_urls.append(f"{ep_name}${ep_href}")
                    if ep_urls:
                        lines[sid] = {"name": line_name, "urls": "$$$".join(ep_urls)}

        if not lines:
            all_ep_pattern = r'<a[^>]*href="(/vod-play/\d+-\d+-\d+/)"[^>]*><span>([^<]*)</span>'
            all_ep_matches = re.findall(all_ep_pattern, html)
            if all_ep_matches:
                groups = {}
                for ep_href, ep_name in all_ep_matches:
                    sid_match = re.search(r'/vod-play/\d+-(\d+)-\d+/', ep_href)
                    if sid_match:
                        sid = sid_match.group(1)
                        if sid not in groups:
                            groups[sid] = []
                        groups[sid].append(f"{ep_name}${ep_href}")
                for sid, eps in groups.items():
                    lines[sid] = {"name": f"线路{sid}", "urls": "$$$".join(eps)}

        # 线路排序: sid=2优先, sid=3其次, sid=1最后
        priority_order = ["2", "3", "1"]
        sorted_lines = []
        for sid in priority_order:
            if sid in lines:
                sorted_lines.append(lines[sid])
                del lines[sid]
        for sid in sorted(lines.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            sorted_lines.append(lines[sid])

        play_from_list = [line["name"] for line in sorted_lines]
        play_url_list = [line["urls"] for line in sorted_lines]

        vod_play_from = "$$$".join(play_from_list) if play_from_list else ""
        vod_play_url = "$$$".join(play_url_list) if play_url_list else ""

        vod = {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": remark,
            "vod_content": content,
            "vod_play_from": vod_play_from,
            "vod_play_url": vod_play_url,
        }
        return {"list": [vod]}

    def searchContent(self, key, quick=False, pg="1"):
        if not key or len(key.strip()) < 1:
            return {"list": []}
        keyword = key.strip()
        page = str(pg or "1")
        url = f"{self.site_url}/vod-search/-------------/?wd={keyword}&page={page}"
        html = self._fetch(url)
        if not html:
            return {"list": [], "page": int(page)}

        videos = []
        blocks = re.findall(r'<a href="/vod/(\d+)/"[^>]*>.*?<div class="module-item-note">([^<]*)</div>.*?<img[^>]*data-original="([^"]+)"[^>]*>.*?<div class="module-card-item-title">.*?<a[^>]*><strong>([^<]*)</strong>', html, re.S)
        if not blocks:
            blocks = re.findall(r'<a href="/vod/(\d+)/"[^>]*>.*?<div class="module-item-note">([^<]*)</div>.*?<img[^>]*data-original="([^"]+)"[^>]*>.*?<div class="module-poster-item-title">([^<]*)</div>', html, re.S)
        
        for match in blocks:
            if len(match) == 4:
                vid, note, pic, title = match
            else:
                continue
            if pic and '43f8a205f442c9676dd5e01514daba6f' in pic:
                continue
            videos.append({
                "vod_id": vid,
                "vod_name": title.strip(),
                "vod_pic": pic,
                "vod_remarks": note.strip(),
            })

        pagecount = 1
        page_match = re.search(r'共(\d+)页', html)
        if page_match:
            pagecount = int(page_match.group(1))

        return {"list": videos, "page": int(page), "pagecount": pagecount}

    def playerContent(self, flag, id, vipFlags=None):
        if id.startswith("http://") or id.startswith("https://"):
            return {"parse": 0, "url": id, "header": self.headers}

        # 如果id是纯数字，构造完整播放URL（默认线路1，第1集）
        if isinstance(id, str) and id.isdigit():
            play_url = f"{self.site_url}/vod-play/{id}-1-1/"
        elif id.startswith("/"):
            play_url = f"{self.site_url}{id}"
        else:
            play_url = f"{self.site_url}/vod-play/{id}/"

        html = self._fetch(play_url)
        if not html:
            return {"parse": 1, "url": play_url, "header": self.headers}

        video_pattern = r'<video[^>]*src="([^"]+)"[^>]*>'
        video_match = re.search(video_pattern, html)
        if video_match:
            m3u8_url = video_match.group(1)
            if m3u8_url.startswith("http"):
                return {"parse": 0, "url": m3u8_url, "header": self.headers}

        player_pattern = r'player\s*=\s*new\s+DPlayer[^}]*url:\s*"([^"]+)"'
        player_match = re.search(player_pattern, html)
        if player_match:
            m3u8_url = player_match.group(1)
            if m3u8_url.startswith("http"):
                return {"parse": 0, "url": m3u8_url, "header": self.headers}

        return {"parse": 1, "url": play_url, "header": self.headers}

    def getProxyUrl(self):
        return ""

    def destroy(self):
        pass


# 兼容性函数
def getSpider():
    return Spider()

def getHomeContent():
    return Spider().homeContent()

def getHomeVideoContent():
    return Spider().homeVideoContent()

def getCategoryContent(tid, pg=1, filter=False, extend=None):
    return Spider().categoryContent(tid, pg, filter, extend)

def getDetailContent(ids):
    return Spider().detailContent(ids)

def getSearchContent(key, quick=False, pg=1):
    return Spider().searchContent(key, quick, pg)

def getPlayerContent(flag, id, vipFlags=None):
    return Spider().playerContent(flag, id, vipFlags)

def getDependence():
    return Spider().getDependence()

def destroy():
    return Spider().destroy()