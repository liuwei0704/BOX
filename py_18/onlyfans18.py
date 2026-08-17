# coding: utf-8
# onlyfans18.vip 影视爬虫 - MacCMS 标准站
# 站点: https://onlyfans18.vip/
# 类型: 成人视频聚合站

import re
import json
import urllib.parse
import posixpath
from urllib.parse import quote, urljoin, unquote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://onlyfans18.vip"
        self.site_name = "onlyfans18"
        self.classes = [
            {"type_id": "4", "type_name": "自拍"},
            {"type_id": "1", "type_name": "onlyfans"},
            {"type_id": "2", "type_name": "网黄"},
            {"type_id": "3", "type_name": "品牌"},
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            "Referer": self.host + "/",
        }

    def getName(self):
        return "onlyfans18"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html(self.host + "/")
        items = self._parse_video_list(html)
        return {"list": items[:12]}

    def categoryContent(self, tid, pg, filter, extend):
        pg = str(pg) if pg else "1"
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        page_count = self._parse_page_count(html)
        return {
            "list": items,
            "page": int(pg),
            "pagecount": page_count,
            "limit": 20,
            "total": page_count * 20,
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        if isinstance(ids, list):
            vid = str(ids[0])
        else:
            vid = str(ids)

        play_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        html = self._fetch_html(play_url)
        
        title = self._extract_title(html)
        tags = self._extract_tags(html)
        pic = self._extract_cover(html)
        
        # 提取播放地址
        m3u8_url = self._extract_m3u8_from_html(html)
        
        if m3u8_url:
            vod = {
                "vod_id": vid,
                "vod_name": title or f"视频{vid}",
                "vod_pic": pic or "",
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": tags,
                "vod_play_from": "播放",
                "vod_play_url": f"播放${m3u8_url}",
            }
        else:
            vod = {
                "vod_id": vid,
                "vod_name": title or f"视频{vid}",
                "vod_pic": pic or "",
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": tags,
                "vod_play_from": "播放",
                "vod_play_url": f"播放${play_url}",
            }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        pg = str(pg) if pg else "1"
        url = f"{self.host}/index.php/vod/search/wd/{quote(key)}.html"
        if pg != "1":
            url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{quote(key)}.html"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        return {"list": items, "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        # 统一转为字符串
        id_str = str(id) if id is not None else ""
        
        # 如果id是m3u8/mp4链接，直接返回
        if id_str.startswith("http"):
            if ".m3u8" in id_str.lower():
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(id_str),
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }
            if ".mp4" in id_str.lower():
                return {
                    "parse": 0,
                    "url": id_str,
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }

        # 如果id是播放页URL，提取m3u8
        if id_str.startswith("http") and "play/id" in id_str:
            html = self._fetch_html(id_str)
            m3u8_url = self._extract_m3u8_from_html(html)
            if m3u8_url:
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(m3u8_url),
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }
            return {"parse": 1, "url": id_str, "header": self.headers}

        # 如果id是数字（vod_id），构造播放页URL提取
        if id_str.isdigit():
            detail_url = f"{self.host}/index.php/vod/play/id/{id_str}/sid/1/nid/1.html"
            html = self._fetch_html(detail_url)
            m3u8_url = self._extract_m3u8_from_html(html)
            if m3u8_url:
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(m3u8_url),
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }
            return {"parse": 1, "url": detail_url, "header": self.headers}

        # 其他情况，尝试作为URL处理
        if id_str:
            return {"parse": 1, "url": id_str, "header": self.headers}
        
        return {"parse": 1, "url": "", "header": self.headers}

    def recommendContent(self, ids, pg):
        try:
            if not ids or len(ids) == 0:
                return {"list": []}
            vid = str(ids[0])
            if vid.startswith("rp_"):
                vid = vid.replace("rp_", "")
            detail_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
            html = self._fetch_html(detail_url)
            items = self._parse_recommend_list(html)
            return {"list": items[:12]}
        except Exception as e:
            return {"list": []}

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def localProxy(self, param):
        try:
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")

            if target.startswith("url="):
                target = target[4:]
            target = urllib.parse.unquote(str(target or ""))

            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            resp = self.fetch(target, headers=self.headers, timeout=15)
            if not resp:
                return [502, "text/plain", b"fetch failed"]

            content = getattr(resp, "content", b"") or b""
            if not content and hasattr(resp, "text") and resp.text:
                content = resp.text.encode("utf-8", errors="ignore")

            if not content:
                return [502, "text/plain", b"empty content"]

            text = content.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]

            cleaned = self._clean_m3u8(text, target)
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

        except Exception as e:
            error_msg = f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")
            return [500, "text/plain", error_msg]

    def _clean_m3u8(self, text, source_url):
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urllib.parse.urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"

        parsed = urllib.parse.urlparse(source_url)
        source_dir = posixpath.dirname(parsed.path)
        if not source_dir.endswith("/"):
            source_dir += "/"

        main_dir = source_dir
        for line in lines:
            if line.startswith("#EXT-X-KEY") and "URI=" in line:
                uri_match = re.search(r'URI="([^"]+)"', line)
                if uri_match:
                    key_path = uri_match.group(1)
                    if not key_path.startswith("http"):
                        key_dir = posixpath.dirname(key_path)
                        if key_dir and key_dir != "/":
                            main_dir = key_dir + "/"
                            break

        segments = []
        pending = []

        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media_url = urllib.parse.urljoin(source_url, line)
                media_parsed = urllib.parse.urlparse(media_url)
                is_ad = not media_parsed.path.startswith(main_dir)
                if not is_ad:
                    segments.extend(pending)
                    segments.append(media_url)
                pending = []
                continue

            if not line.startswith("#"):
                segments.append(urllib.parse.urljoin(source_url, line))
            else:
                segments.append(line)

        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in ("#EXT-X-KEY:METHOD=NONE", "#EXT-X-DISCONTINUITY"):
                if not out or out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
                    continue
            out.append(line)

        while len(out) > 1 and out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
            out.pop()

        return "\n".join(out) + "\n"

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

    def _fetch_html(self, url, params=None):
        full_url = url
        if params:
            if "?" in url:
                full_url = url + "&" + urllib.parse.urlencode(params)
            else:
                full_url = url + "?" + urllib.parse.urlencode(params)
        try:
            resp = self.fetch(full_url, headers=self.headers, timeout=15)
            if resp and hasattr(resp, "status_code") and resp.status_code == 200:
                return resp.text
            if resp and hasattr(resp, "text"):
                return resp.text
        except Exception as e:
            pass
        return ""

    def _parse_video_list(self, html):
        items = []
        if not html:
            return items

        # 匹配视频卡片 - 从col-style中提取
        pattern = r'<div[^>]*class="[^"]*col-style[^"]*"[^>]*>.*?<a[^>]*href="(/index\.php/vod/play/id/(\d+)/[^"]+)"[^>]*>.*?<div[^>]*class="[^"]*videoBox-cover[^"]*"[^>]*style="[^"]*background-image:\s*url\(([^)]+)\)[^"]*"[^>]*>.*?<span[^>]*class="[^"]*videoBox-time[^"]*"[^>]*>([^<]*)</span>.*?<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>'
        matches = re.findall(pattern, html, re.DOTALL)

        for match in matches:
            link, vid, pic, duration, title = match
            # 清理图片URL：移除多余的引号和空格
            pic = pic.strip().strip("'\"")
            # 如果URL中包含 &quot; 实体，解码
            pic = pic.replace("&quot;", "").replace('"', '').strip()
            # 构建完整URL
            if pic and not pic.startswith("http"):
                if pic.startswith("/"):
                    pic = self.host + pic
                else:
                    pic = urljoin(self.host, pic)
            # 清理可能残留的引号
            pic = pic.strip('"').strip("'")
            items.append({
                "vod_id": vid.strip(),
                "vod_name": title.strip(),
                "vod_pic": pic,
                "vod_remarks": duration.strip(),
            })

        # 如果上面的正则失败，使用简化匹配
        if not items:
            pattern2 = r'<a[^>]*href="(/index\.php/vod/play/id/(\d+)/[^"]+)"[^>]*>.*?<div[^>]*class="[^"]*videoBox-cover[^"]*"[^>]*style="[^"]*background-image:\s*url\(([^)]+)\)[^"]*"[^>]*>.*?<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>'
            matches2 = re.findall(pattern2, html, re.DOTALL)
            for match in matches2:
                link, vid, pic, title = match
                pic = pic.strip().strip("'\"")
                pic = pic.replace("&quot;", "").replace('"', '').strip()
                if pic and not pic.startswith("http"):
                    if pic.startswith("/"):
                        pic = self.host + pic
                    else:
                        pic = urljoin(self.host, pic)
                pic = pic.strip('"').strip("'")
                items.append({
                    "vod_id": vid.strip(),
                    "vod_name": title.strip(),
                    "vod_pic": pic,
                    "vod_remarks": "",
                })

        return items
    def _parse_page_count(self, html):
        if not html:
            return 1
        # 提取分页中的最大页码
        pattern = r'<a[^>]*href="[^"]*page/(\d+)[^"]*"[^>]*>(\d+)</a>'
        matches = re.findall(pattern, html)
        if matches:
            nums = [int(m[1]) for m in matches if m[1].isdigit()]
            if nums:
                return max(nums)
        return 1

    def _extract_m3u8_from_html(self, html):
        if not html:
            return None

        # 方法1: 从 player_data 中提取
        # 匹配 var player_data={...} 或 var player_data = {...}
        pattern = r'var\s+player_data\s*=\s*(\{[^}]*\})'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                data_str = match.group(1)
                # 尝试解析JSON
                data = json.loads(data_str)
                url = data.get("url", "")
                if url:
                    if url.startswith("http"):
                        return url
                    if url.startswith("/"):
                        return self.host + url
                    # 处理相对路径
                    if not url.startswith("/") and not url.startswith("http"):
                        return self.host + "/" + url
                    return url
            except Exception as e:
                # JSON解析失败，尝试用正则提取url
                url_match = re.search(r'"url"\s*:\s*"([^"]+)"', data_str)
                if url_match:
                    url = url_match.group(1)
                    if url.startswith("http"):
                        return url
                    if url.startswith("/"):
                        return self.host + url
                    if url:
                        return self.host + "/" + url

        # 方法2: 直接查找任何以 /upload/vod_file/ 开头的mp4或m3u8链接
        # 这是该站点的视频文件存放路径模式
        pattern2 = r'"/upload/vod_file/[^"]+\.(mp4|m3u8)[^"]*"'
        match2 = re.search(pattern2, html)
        if match2:
            url = match2.group(0).strip('"')
            if url:
                return self.host + url

        # 方法3: 查找任何m3u8链接
        pattern3 = r'https?://[^"\']+\.m3u8[^"\']*'
        match3 = re.search(pattern3, html)
        if match3:
            return match3.group(0)

        # 方法4: 查找mp4直链
        pattern4 = r'https?://[^"\']+\.mp4[^"\']*'
        match4 = re.search(pattern4, html)
        if match4:
            return match4.group(0)

        return None
    def _extract_title(self, html):
        if not html:
            return ""
        pattern = r'<h1[^>]*class="[^"]*video-title[^"]*"[^>]*>([^<]+)</h1>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            return match.group(1).strip()
        pattern2 = r'<title>([^<]+)</title>'
        match2 = re.search(pattern2, html)
        if match2:
            title = match2.group(1).strip()
            title = title.replace(" - 高清视频在线观看", "").replace(" - 亚洲高质量A片、网红泄露、反差婊在线观看 - onlyfans18", "")
            return title
        return ""

    def _extract_tags(self, html):
        if not html:
            return ""
        pattern = r'<span[^>]*class="[^"]*tags[^"]*"[^>]*>(.*?)</span>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            tags_html = match.group(1)
            tags = re.findall(r'<a[^>]*>([^<]+)</a>', tags_html)
            return "，".join(tags)
        return ""

    def _extract_cover(self, html):
        if not html:
            return ""
        pattern = r'background-image:\s*url\(([^)]+)\)'
        match = re.search(pattern, html)
        if match:
            pic = match.group(1).strip().strip("'\"")
            if pic and not pic.startswith("http"):
                pic = urljoin(self.host, pic)
            return pic
        return ""

    def _parse_recommend_list(self, html):
        items = []
        if not html:
            return items

        pattern = r'<a[^>]*href="(/index\.php/vod/play/id/(\d+)/sid/1/nid/1\.html)"[^>]*>.*?<div[^>]*class="[^"]*videoBox-cover[^"]*"[^>]*style="[^"]*background-image:\s*url\(([^)]+)\)[^"]*"[^>]*>.*?<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>'
        matches = re.findall(pattern, html, re.DOTALL)

        for match in matches:
            link, vid, pic, title = match
            # 清理图片URL：移除多余的引号和空格
            pic = pic.strip().strip("'\"")
            pic = pic.replace("&quot;", "").replace('"', '').strip()
            if pic and not pic.startswith("http"):
                if pic.startswith("/"):
                    pic = self.host + pic
                else:
                    pic = urljoin(self.host, pic)
            pic = pic.strip('"').strip("'")
            items.append({
                "vod_id": vid.strip(),
                "vod_name": title.strip(),
                "vod_pic": pic,
                "vod_remarks": "",
            })

        return items
    def destroy(self):
        pass