# coding: utf-8
"""
橙子18 - TVBox爬虫源
站点：https://cat.cz184.autos
类型：MacCMS标准站（HTML）
功能：完整 m3u8 广告分片自动过滤
"""

import re
import json
import urllib.parse
import posixpath
from urllib.parse import urljoin, quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://cat.cz184.autos"
        self.base_path = ""
        self.site_name = "橙子18"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.classes = [
            {"type_id": "20", "type_name": "自拍偷拍"},
            {"type_id": "21", "type_name": "巨乳波霸"},
            {"type_id": "22", "type_name": "强奸乱伦"},
            {"type_id": "23", "type_name": "人妻熟女"},
            {"type_id": "24", "type_name": "制服丝袜"},
            {"type_id": "25", "type_name": "花季少女"},
            {"type_id": "26", "type_name": "无码露毛"},
            {"type_id": "27", "type_name": "群P多人"},
            {"type_id": "28", "type_name": "人兽人妖"},
            {"type_id": "29", "type_name": "男同女同"},
            {"type_id": "30", "type_name": "韩日专区"},
            {"type_id": "31", "type_name": "欧美色情"},
            {"type_id": "32", "type_name": "成人动漫"},
            {"type_id": "33", "type_name": "三级剧情"},
        ]
        self.filters = {c["type_id"]: [] for c in self.classes}
        self._cached_host = None

    def getName(self):
        return self.site_name

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        url = f"{self.host}/cn/home/web/"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        return {"list": items[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/cn/home/web/index.php/vod/type/id/{tid}/page/{page}.html"
        html = self._fetch_html(url)
        if html:
            self.log(f"categoryContent html length: {len(html)}, preview: {html[:200]}")
        else:
            self.log(f"categoryContent html empty for url: {url}")
        items = self._parse_video_list(html)
        page_count = self._parse_page_count(html)
        return {
            "list": items,
            "page": int(page),
            "pagecount": page_count if page_count > 0 else 1,
            "limit": 20,
            "total": page_count * 20 if page_count > 0 else 0,
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0])
        url = f"{self.host}/cn/home/web/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        html = self._fetch_html(url)

        title = self._extract_title(html)
        play_url = self._extract_play_url(html)

        if title and ("404" in title or "页面迷路了" in title):
            title = f"视频{vid}"

        vod = {
            "vod_id": vid,
            "vod_name": title or f"视频{vid}",
            "vod_pic": "",
            "vod_remarks": "",
            "vod_content": "",
            "vod_play_from": "播放",
            "vod_play_url": f"播放${play_url}" if play_url else f"播放${url}",
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        url = f"{self.host}/cn/home/web/index.php/vod/search.html"
        data = {"wd": key}
        html = self._fetch_html(url, method="POST", data=data)
        items = self._parse_video_list(html)
        return {"list": items, "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": {}}

        id = str(id).strip()

        # 如果已经是 m3u8 直链，走代理过滤广告
        if '.m3u8' in id and id.startswith('http'):
            return {
                "parse": 0,
                "url": self._m3u8_proxy_url(id),
                "header": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://cat.cz184.autos/",
                }
            }

        # 如果 id 是详情页 URL，提取 m3u8
        if id.startswith('http'):
            vid_match = re.search(r'/id/(\d+)/', id)
            if vid_match:
                vid = vid_match.group(1)
            else:
                num_match = re.search(r'/(\d+)(?:\.html)?$', id)
                vid = num_match.group(1) if num_match else id
            url = id
        else:
            vid = id
            url = f"{self.host}/cn/home/web/index.php/vod/play/id/{vid}/sid/1/nid/1.html"

        html = self._fetch_html(url)
        play_url = self._extract_play_url(html)

        if play_url:
            return {
                "parse": 0,
                "url": self._m3u8_proxy_url(play_url),
                "header": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://cat.cz184.autos/",
                }
            }
        else:
            return {"parse": 1, "url": url, "header": self.headers}
    def recommendContent(self, ids, pg):
        if not ids:
            return {"list": []}
        vid = str(ids[0])
        url = f"{self.host}/cn/home/web/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        html = self._fetch_html(url)

        pattern = r'<div[^>]*class="video-related"[^>]*>.*?<div[^>]*class="video-list"[^>]*>(.*?)</div>\s*</div>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            items = self._parse_video_list(match.group(1))
            return {"list": items[:12]}
        return {"list": []}

    def destroy(self):
        pass

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def localProxy(self, param):
        """
        m3u8本地代理 - 广告分片自动过滤
        """
        try:
            target = ""
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "") or param.get("do", "")
            elif isinstance(param, str):
                target = param
            else:
                target = str(param or "")

            if target.startswith("url="):
                target = target[4:]
            elif target.startswith("do=py&url="):
                target = target[9:]

            target = urllib.parse.unquote(str(target or ""))

            if not target and isinstance(param, dict):
                for key in ["url", "source", "u", "target"]:
                    if key in param and param[key]:
                        target = urllib.parse.unquote(str(param[key]))
                        break

            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            # 使用站点域名作为 Referer，增强防盗链兼容性
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cat.cz184.autos/",
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
            }

            resp = self.fetch(target, headers=headers, timeout=20)
            if not resp:
                return [502, "text/plain", b"fetch failed"]

            content = getattr(resp, "content", b"") or b""
            if not content and hasattr(resp, "text") and resp.text:
                content = resp.text.encode("utf-8", errors="ignore")

            if not content:
                return [502, "text/plain", b"empty content"]

            # 检测 m3u8 并自动过滤广告
            if b"#EXTM3U" in content[:256]:
                text = content.decode("utf-8", errors="ignore")
                cleaned = self._clean_m3u8(text, target)
                return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

            # 非 m3u8 直接返回
            content_type = "application/octet-stream"
            if target.endswith(".ts"):
                content_type = "video/mp2t"
            elif target.endswith(".m3u8"):
                content_type = "application/vnd.apple.mpegurl"
            elif target.endswith(".png") or target.endswith(".jpg"):
                content_type = "image/jpeg"
            elif target.endswith(".mp4"):
                content_type = "video/mp4"
            elif target.endswith(".key"):
                content_type = "application/octet-stream"

            return [200, content_type, content]

        except Exception as e:
            error_msg = f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")
            return [500, "text/plain", error_msg]
    def _is_ad_url(self, url):
        if not url:
            return False
        url_lower = url.lower()
        ad_keywords = [
            'ad', 'ads', 'preroll', 'midroll', 'postroll',
            'advertisement', '广告', 'sponsor', 'promotion',
            '片头', '片尾', 'ad_', '-ad', '/ad/', '/ads/'
        ]
        for kw in ad_keywords:
            if kw in url_lower:
                return True
        return False

    def _clean_m3u8(self, text, source_url):
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        is_multi = any(line.startswith("#EXT-X-STREAM-INF") for line in lines)

        if is_multi:
            return self._clean_m3u8_multi(lines, source_url)
        else:
            return self._clean_m3u8_single(lines, source_url)

    def _clean_m3u8_multi(self, lines, source_url):
        """多码率播放列表 - 完全透传，不做修改（子流会再次进入localProxy过滤）"""
        out = []
        for line in lines:
            if line.startswith("#"):
                out.append(line)
            else:
                child_url = urllib.parse.urljoin(source_url, line)
                out.append(self._m3u8_proxy_url(child_url))
        return "\n".join(out) + "\n"
    def _clean_m3u8_single(self, lines, source_url):
        """单码率播放列表过滤 - 目录列表 + 补全 KEY URI"""
        result = []
        pending_extinf = []
        removed = 0

        # 先从 m3u8 中提取所有目录用于调试
        all_dirs = set()
        for line in lines:
            if '.ts' in line or '.jpg' in line or '.m3u8' in line:
                if '/' in line:
                    parts = line.split('/')
                    for part in parts:
                        if len(part) >= 8 and '.' not in part and '?' not in part:
                            all_dirs.add(part)

        self.log(f"橙子18 检测到目录: {list(all_dirs)}")

        # 广告目录列表（只放广告目录，正片目录不要放进去）
        ad_dirs = [
            'VmnacVi8',          # 橙子18 广告目录
            '5215af9565c8b6ce',  # 新狼AV 广告目录
            'UTe7qSJd',          # 大嘴AV 广告目录
            'UTxI1Mxv',          # 新狼AV 广告目录
            'a3712cbfc6902686',  # 勃士 广告目录
            '48a95b6cc2e944fa',  # 勃士 广告目录
        ]

        i = 0
        while i < len(lines):
            line = lines[i]

            # 补全 #EXT-X-KEY 的 URI
            if line.startswith("#EXT-X-KEY") and "URI=" in line:
                line = self._rewrite_m3u8_tag(line, source_url)
                result.append(line)
                i += 1
                continue

            if line.startswith("#EXTINF"):
                pending_extinf = [line]
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith("#"):
                        pending_extinf.append(next_line)
                        i += 1
                    else:
                        media_url = urllib.parse.urljoin(source_url, next_line)
                        is_ad = False
                        for ad_dir in ad_dirs:
                            if ad_dir in media_url:
                                is_ad = True
                                break
                        if is_ad:
                            removed += 1
                        else:
                            if media_url.endswith('.jpg'):
                                media_url = media_url[:-4] + '.ts'
                            result.extend(pending_extinf)
                            result.append(media_url)
                        i += 1
                        break
                continue

            result.append(line)
            i += 1

        if removed:
            self.log(f"橙子18 m3u8已过滤广告分片: {removed}个")

        return "\n".join(result) + "\n"
    def _rewrite_m3u8_tag(self, line, source_url):
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(match):
                uri = match.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urllib.parse.urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)

        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urllib.parse.urljoin(source_url, line)

        return line

    def _fetch_html(self, url, method="GET", data=None):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cat.cz184.autos/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
            }
            if method.upper() == "POST" and data:
                resp = self.post(url, data=data, headers=headers, timeout=15)
            else:
                resp = self.fetch(url, headers=headers, timeout=15)

            if resp is None:
                return ""

            if hasattr(resp, "text"):
                return resp.text
            elif hasattr(resp, "content"):
                return resp.content.decode("utf-8", errors="ignore")
            return ""
        except Exception:
            return ""

    def _parse_video_list(self, html):
        items = []
        if not html:
            return items

        pattern = r'<div[^>]*class="video-play[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<p[^>]*class="title-p"[^>]*><a[^>]*href="[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html, re.DOTALL)

        for link, pic, title in matches:
            vid_match = re.search(r'/id/(\d+)/', link)
            if vid_match:
                vid = vid_match.group(1)
                items.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": pic,
                    "vod_remarks": ""
                })
        return items

    def _parse_page_count(self, html):
        if not html:
            return 1
        match = re.search(r'(\d+)\s*/\s*(\d+)', html)
        if match:
            return int(match.group(2))
        return 1

    def _extract_title(self, html):
        if not html:
            return ""
        match = re.search(r'<div[^>]*class="playName"[^>]*>.*?<p[^>]*class="name"[^>]*>([^<]+)</p>', html, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r'<title>([^<]+)</title>', html)
        if match:
            title = match.group(1)
            title = re.sub(r'\s*[-|]\s*橙子18\s*$', '', title)
            return title.strip()
        return ""

    def _extract_play_url(self, html):
        if not html:
            return None

        match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
        if match:
            url = match.group(1)
            url = url.replace("\\/", "/")
            if url.startswith("http"):
                return url

        match = re.search(r'var\s+player_data\s*=\s*({[^;]+});', html, re.DOTALL)
        if match:
            try:
                js_obj = match.group(1)
                js_obj = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', js_obj)
                data = json.loads(js_obj)
                url = data.get("url", "")
                if url:
                    url = url.replace("\\/", "/")
                if url and url.startswith("http") and ".m3u8" in url:
                    return url
            except Exception:
                pass

        match = re.search(r'https?://[^"\']+\.m3u8[^"\']*', html)
        if match:
            url = match.group(0)
            url = url.replace("\\/", "/")
            return url

        return None