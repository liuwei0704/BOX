# coding: utf-8
"""
勃士 - TVBox爬虫源
站点：https://wrb.boshi4.help
类型：MacCMS标准站（HTML）
功能：m3u8 图片流替换为视频流
"""

import re
import json
import urllib.parse
from urllib.parse import urljoin, quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://wrb.boshi4.help"
        self.base_path = ""
        self.site_name = "勃士"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.classes = [
            {"type_id": "21", "type_name": "女神学生"},
            {"type_id": "22", "type_name": "美女直播"},
            {"type_id": "23", "type_name": "人妻系列"},
            {"type_id": "24", "type_name": "强奸乱伦"},
            {"type_id": "25", "type_name": "自拍偷拍"},
            {"type_id": "26", "type_name": "制服诱惑"},
            {"type_id": "27", "type_name": "巨乳系列"},
            {"type_id": "28", "type_name": "自慰系列"},
            {"type_id": "29", "type_name": "国产视频"},
            {"type_id": "30", "type_name": "无码视频"},
            {"type_id": "31", "type_name": "有码视频"},
            {"type_id": "32", "type_name": "中文字幕"},
            {"type_id": "33", "type_name": "日韩精品"},
            {"type_id": "34", "type_name": "欧美精品"},
            {"type_id": "35", "type_name": "动漫精品"},
            {"type_id": "36", "type_name": "三级伦理"},
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
        if str(page) == "1":
            url = f"{self.host}/cn/home/web/index.php/vod/type/id/{tid}.html"
        else:
            url = f"{self.host}/cn/home/web/index.php/vod/type/id/{tid}/page/{page}.html"
        html = self._fetch_html(url)
        
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

        if '.m3u8' in id and id.startswith('http'):
            return {
                "parse": 0,
                "url": self._m3u8_proxy_url(id),
                "header": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://wrb.boshi4.help/",
                }
            }

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
                    "Referer": "https://wrb.boshi4.help/",
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

    def _is_ad_url(self, url):
        """判断URL是否为广告 - 基于关键词 + 目录特征"""
        if not url:
            return False
        url_lower = url.lower()
        
        # 1. 关键词检测
        ad_keywords = [
            'ad', 'ads', 'preroll', 'midroll', 'postroll',
            'advertisement', '广告', 'sponsor', 'promotion',
            '片头', '片尾', 'ad_', '-ad', '/ad/', '/ads/'
        ]
        for kw in ad_keywords:
            if kw in url_lower:
                return True
        
        # 2. 目录特征检测（针对这个站点的广告目录）
        ad_dirs = [
            'a3712cbfc6902686',
            '48a95b6cc2e944fa',
        ]
        for ad_dir in ad_dirs:
            if ad_dir in url:
                return True
        
        return False
    def localProxy(self, param):
        """
        m3u8本地代理 - 补全相对路径 + 广告分片过滤 + 图片流替换
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

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://wrb.boshi4.help/",
                "Accept": "*/*",
            }

            resp = self.fetch(target, headers=headers, timeout=20)
            if not resp:
                return [502, "text/plain", b"fetch failed"]

            content = getattr(resp, "content", b"") or b""
            if not content and hasattr(resp, "text") and resp.text:
                content = resp.text.encode("utf-8", errors="ignore")

            if not content:
                return [502, "text/plain", b"empty content"]

            if b"#EXTM3U" in content[:256]:
                text = content.decode("utf-8", errors="ignore")
                
                # 检测是否为多码率 Master Playlist
                has_multi = re.search(r'#EXT-X-STREAM-INF', text)
                
                if has_multi:
                    # 多码率：过滤广告子流
                    lines = text.split('\n')
                    new_lines = []
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith('#'):
                            new_lines.append(line)
                        else:
                            if not line.startswith(('http://', 'https://')):
                                parsed = urllib.parse.urlparse(target)
                                if line.startswith('/'):
                                    line = f"{parsed.scheme}://{parsed.netloc}{line}"
                                else:
                                    base_url = target.rsplit('/', 1)[0]
                                    line = base_url + '/' + line
                            if self._is_ad_url(line):
                                continue
                            # 替换 .jpg -> .ts
                            if line.endswith('.jpg'):
                                line = line[:-4] + '.ts'
                            new_lines.append(line)
                    return [200, "application/vnd.apple.mpegurl", '\n'.join(new_lines).encode("utf-8")]
                
                # 单码率：处理分片
                base_url = target.rsplit('/', 1)[0]
                lines = text.split('\n')
                new_lines = []
                removed = 0

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 补全相对路径
                    if not line.startswith('#') and not line.startswith(('http://', 'https://')):
                        if line.startswith('/'):
                            parsed = urllib.parse.urlparse(target)
                            line = f"{parsed.scheme}://{parsed.netloc}{line}"
                        else:
                            line = base_url + '/' + line

                    # 广告检测
                    if self._is_ad_url(line):
                        removed += 1
                        continue

                    # 替换 .jpg -> .ts
                    if line.endswith('.jpg'):
                        line = line[:-4] + '.ts'

                    new_lines.append(line)

                if removed:
                    self.log(f"勃士 m3u8已过滤广告分片: {removed}个")

                return [200, "application/vnd.apple.mpegurl", '\n'.join(new_lines).encode("utf-8")]

            # 非 m3u8 直接返回
            content_type = "application/octet-stream"
            if target.endswith(".ts"):
                content_type = "video/mp2t"
            elif target.endswith(".m3u8"):
                content_type = "application/vnd.apple.mpegurl"
            elif target.endswith(".jpg") or target.endswith(".png"):
                content_type = "image/jpeg"
            elif target.endswith(".mp4"):
                content_type = "video/mp4"
            elif target.endswith(".key") or target.endswith(".bin"):
                content_type = "application/octet-stream"

            return [200, content_type, content]

        except Exception as e:
            error_msg = f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")
            return [500, "text/plain", error_msg]
    def _fetch_html(self, url, method="GET", data=None):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://wrb.boshi4.help/",
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

        pattern = r'<li[^>]*id="video-(\d+)"[^>]*>.*?<a[^>]*href="[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<span[^>]*class="video-title"[^>]*>([^<]+)</span>'
        matches = re.findall(pattern, html, re.DOTALL)

        for vid, pic, title in matches:
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
        match = re.search(r'共(\d+)条数据', html)
        if match:
            total = int(match.group(1))
            return (total + 19) // 20
        matches = re.findall(r'page/(\d+)\.html', html)
        if matches:
            nums = [int(n) for n in matches if n.isdigit()]
            if nums:
                return max(nums)
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
            title = re.sub(r'\s*[-|]\s*勃士\s*$', '', title)
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