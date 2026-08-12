# coding: utf-8
# 胖次美学 - TVBox/FongMi 爬虫
# 站点: https://www.pangci27.xyz/
# CMS: 苹果CMS (MacCMS)
# 特性: m3u8 本地代理 + 广告分片过滤

import re
import json
import urllib.parse
from urllib.parse import urljoin, quote, unquote, urlparse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://www.pangci27.xyz"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "24", "type_name": "国产"},
            {"type_id": "25", "type_name": "传媒"},
            {"type_id": "26", "type_name": "日韩"},
            {"type_id": "27", "type_name": "欧美"},
            {"type_id": "28", "type_name": "动漫"},
            {"type_id": "29", "type_name": "同性"},
            {"type_id": "30", "type_name": "其他"},
        ]
        self.filters = {}

    def getName(self):
        return "胖次美学"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def _decode_entities(self, text):
        if not text:
            return text
        def replace_num(m):
            return chr(int(m.group(1)))
        text = re.sub(r'&#(\d+);', replace_num, text)
        def replace_hex(m):
            return chr(int(m.group(1), 16))
        text = re.sub(r'&#x([0-9a-fA-F]+);', replace_hex, text)
        return text

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            html = self._fetch_html(self.host + "/")
            videos = self._parse_video_list(html)
            return {"list": videos[:20]}
        except:
            return {"list": []}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        if pg is None or pg == "":
            pg = 1
        pg = int(pg)
        if pg == 1:
            url = f"{self.host}/vodtype/{tid}.html"
        else:
            url = f"{self.host}/vodtype/{tid}.html?page={pg}"
        try:
            html = self._fetch_html(url)
            videos = self._parse_video_list(html)
            return {"list": videos, "page": pg, "pagecount": 99, "limit": 20}
        except:
            return {"list": [], "page": pg, "pagecount": 99, "limit": 20}

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers)
            if resp is None:
                return ""
            if hasattr(resp, "text"):
                return resp.text
            if hasattr(resp, "content"):
                try:
                    return resp.content.decode('utf-8')
                except:
                    return str(resp.content)
            return str(resp)
        except:
            return ""

    def _parse_video_list(self, html):
        videos = []
        if not html:
            return videos
        pattern = r'<article\s+class="pc-tile">.*?<a\s+class="pc-tile-media"\s+href="([^"]+)"[^>]*>.*?<img\s+class="pc-tile-img"\s+src="([^"]+)"[^>]*>.*?<h3\s+class="pc-tile-title">.*?<a\s+href="[^"]*"\s+title="([^"]+)"'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            href = match[0]
            pic = match[1]
            title = self._decode_entities(match[2].strip())
            if not title:
                continue
            vid_match = re.search(r'/vodplay/(\d+)', href)
            if not vid_match:
                continue
            vid = vid_match.group(1)
            cat_match = re.search(r'<span\s+class="pc-tile-cat">([^<]+)</span>', html)
            remark = self._decode_entities(cat_match.group(1)) if cat_match else ""
            videos.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark,
            })
        return videos

    def detailContent(self, ids):
        if not ids or not ids[0]:
            return {"list": []}
        vid = str(ids[0]).strip()
        vid = re.sub(r'[^0-9]', '', vid)
        if not vid:
            return {"list": []}
        url = f"{self.host}/vodplay/{vid}-1-1.html"
        try:
            html = self._fetch_html(url)
            return self._parse_detail(html, vid)
        except:
            return {"list": []}

    def _parse_detail(self, html, vid):
        vod = {
            "vod_id": vid,
            "vod_name": "",
            "vod_pic": "",
            "vod_remarks": "",
            "vod_content": "",
            "vod_play_from": "",
            "vod_play_url": ""
        }

        play_url = None
        is_hash = False
        
        start = html.find('player_aaaa=')
        if start != -1:
            json_start = html.find('{', start)
            if json_start != -1:
                brace_count = 0
                json_end = json_start
                for i in range(json_start, len(html)):
                    ch = html[i]
                    if ch == '{':
                        brace_count += 1
                    elif ch == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                if json_end > json_start:
                    json_str = html[json_start:json_end]
                    try:
                        data = json.loads(json_str)
                        raw_url = data.get("url", "")
                        if raw_url:
                            # 检查是否为32位十六进制哈希值
                            if re.match(r'^[0-9a-f]{32}$', raw_url, re.I):
                                is_hash = True
                                # 构造解析 URL，交给 WebView 播放
                                play_url = f"https://pangci.zhenbukaav.top?url={raw_url}"
                                self.log(f"检测到哈希值播放地址: {raw_url}, 使用 WebView 解析服务")
                            else:
                                raw_url = raw_url.replace('\\/', '/')
                                if '.m3u8' in raw_url or '.mp4' in raw_url:
                                    play_url = raw_url
                        # 提取视频名称
                        vod_name = data.get("vod_data", {}).get("vod_name", "")
                        if vod_name:
                            vod["vod_name"] = self._decode_entities(vod_name)
                        vod_class = data.get("vod_data", {}).get("vod_class", "")
                        if vod_class:
                            vod["vod_class"] = self._decode_entities(vod_class)
                    except:
                        pass

        # 如果没有从 player_aaaa 提取到播放地址，尝试从 HTML 中直接提取 m3u8
        if not play_url:
            m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
            if m3u8_match:
                play_url = m3u8_match.group(1)

        if not vod["vod_name"]:
            title_match = re.search(r'<h1\s+class="pc-theater-title">([^<]+)</h1>', html)
            if title_match:
                vod["vod_name"] = self._decode_entities(title_match.group(1).strip())

        pic_match = re.search(r'data-jps-player-poster="([^"]+)"', html)
        if pic_match:
            vod["vod_pic"] = pic_match.group(1)

        desc_match = re.search(r'<div\s+class="pc-story-content">\s*(.*?)\s*</div>', html, re.DOTALL)
        if desc_match:
            vod["vod_content"] = self._decode_entities(desc_match.group(1).strip())

        if play_url:
            if ".m3u8" in play_url or ".mp4" in play_url:
                vod["vod_play_url"] = f"播放${play_url}"
                vod["vod_play_from"] = "直链"
            elif is_hash:
                # 哈希值使用 WebView 解析服务
                vod["vod_play_url"] = f"播放${play_url}"
                vod["vod_play_from"] = "webview"
            else:
                vod["vod_play_url"] = f"播放${play_url}"
                vod["vod_play_from"] = "直链"
        else:
            vod["vod_play_url"] = f"播放$"
            vod["vod_play_from"] = ""

        return {"list": [vod]}
    def searchContent(self, key, quick, pg="1"):
        if not key or not key.strip():
            return {"list": [], "page": 1}
        keyword = key.strip()
        pg = int(pg) if pg else 1
        if pg == 1:
            url = f"{self.host}/vodsearch/{quote(keyword)}-------------.html"
        else:
            url = f"{self.host}/vodsearch/{quote(keyword)}-------------.html?page={pg}"
        try:
            html = self._fetch_html(url)
            videos = self._parse_video_list(html)
            return {"list": videos, "page": pg}
        except:
            return {"list": [], "page": pg}

    # ========== 播放逻辑 ==========

    def _m3u8_proxy_url(self, url):
        return self.getProxyUrl() + "&url=" + quote(str(url or ""), safe="")

    def playerContent(self, flag, id, vipFlags=None):
        try:
            if not id:
                return {"parse": 1, "url": ""}

            # 如果 flag 是 webview 或解析，强制使用 WebView
            if flag in ("webview", "解析"):
                self.log(f"playerContent: flag={flag}, 强制使用 WebView: {id}")
                return {"parse": 1, "url": id, "header": self.headers}

            # 如果 id 是 m3u8/mp4 直链，直接返回走代理
            if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
                if ".m3u8" in id:
                    # 检查是否是真正的 m3u8 内容
                    resp = self.fetch(id, headers=self.headers, timeout=5)
                    if resp and hasattr(resp, "text") and "#EXTM3U" in resp.text:
                        return {"parse": 0, "url": self._m3u8_proxy_url(id), "header": self.headers}
                    # 如果返回的不是 m3u8，交给系统处理
                    return {"parse": 1, "url": id, "header": self.headers}
                return {"parse": 0, "url": id, "header": self.headers}

            # 如果是解析服务 URL，交给 WebView 处理
            if id.startswith("https://pangci.zhenbukaav.top?url="):
                self.log(f"playerContent: 解析服务地址，交给 WebView: {id}")
                return {"parse": 1, "url": id, "header": self.headers}

            # 构造播放页 URL（哈希值或相对路径）
            if id.startswith("/"):
                play_url = urljoin(self.host, id)
            elif re.match(r'^[0-9a-f]{32}$', id, re.I):
                # 哈希值 → 交给 WebView
                play_url = f"{self.host}/vodplay/{id}.html"
                self.log(f"playerContent: hash value, 交给 WebView: {play_url}")
                return {"parse": 1, "url": play_url, "header": self.headers}
            else:
                play_url = self.host + "/" + id if not id.startswith("http") else id

            # 获取播放页 HTML，尝试提取 m3u8 直链
            html = self._fetch_html(play_url)
            if not html:
                return {"parse": 1, "url": play_url, "header": self.headers}

            m3u8_url = ""

            # 提取 player_aaaa JSON
            start = html.find('player_aaaa=')
            if start != -1:
                json_start = html.find('{', start)
                if json_start != -1:
                    brace_count = 0
                    json_end = json_start
                    for i in range(json_start, len(html)):
                        ch = html[i]
                        if ch == '{':
                            brace_count += 1
                        elif ch == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    if json_end > json_start:
                        json_str = html[json_start:json_end]
                        try:
                            data = json.loads(json_str)
                            raw_url = data.get("url", "")
                            if raw_url:
                                raw_url = raw_url.replace('\\/', '/')
                                if '.m3u8' in raw_url or '.mp4' in raw_url:
                                    m3u8_url = raw_url
                                elif re.match(r'^[0-9a-f]{32}$', raw_url, re.I):
                                    # 哈希值：交给 WebView
                                    parse_url = f"https://pangci.zhenbukaav.top?url={raw_url}"
                                    self.log(f"检测到哈希值，交给 WebView: {parse_url}")
                                    return {"parse": 1, "url": parse_url, "header": self.headers}
                        except:
                            pass

            # 直接抓取 URL
            if not m3u8_url:
                urls = re.findall(r'(https?://[^\s"\'<>]+?\.(?:m3u8|mp4)[^\s"\'<>]*)', html, re.IGNORECASE)
                if urls:
                    m3u8_url = urls[0].replace('\\/', '/')

            if m3u8_url:
                # 验证是否是有效的 m3u8
                resp = self.fetch(m3u8_url, headers=self.headers, timeout=5)
                if resp and hasattr(resp, "text") and "#EXTM3U" in resp.text:
                    return {
                        "parse": 0,
                        "url": self._m3u8_proxy_url(m3u8_url),
                        "header": self.headers
                    }
                else:
                    # 不是有效的 m3u8，交给 WebView
                    return {"parse": 1, "url": m3u8_url, "header": self.headers}

            # 兜底：让系统嗅探
            return {"parse": 1, "url": play_url, "header": self.headers}

        except Exception as e:
            self.log(f"playerContent error: {e}")
            return {"parse": 1, "url": id, "header": self.headers}
    def localProxy(self, param):
        """m3u8 本地代理 + 广告分片过滤"""
        target = unquote(str((param or {}).get("url", "") or ""))
        if not target:
            return [400, "text/plain", b"invalid url"]
        try:
            res = self.fetch(target, headers=self.headers, timeout=15)
            if not res or getattr(res, "status_code", 0) != 200:
                return [502, "text/plain", b"m3u8 fetch failed"]
            raw = getattr(res, "content", b"") or b""
            text = raw.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]
            cleaned = self._clean_m3u8(text, target)
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]
        except Exception as e:
            self.log("m3u8广告过滤失败: " + str(e))
            return [500, "text/plain", b"m3u8 proxy error"]

    def _clean_m3u8(self, text, source_url):
        """清洗 m3u8：过滤广告分片，保留正片"""
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 主清单：子清单补成绝对地址并代理
        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"

        # 分片清单：提取正片资源目录
        source_path = urlparse(source_url).path
        source_parts = [p for p in source_path.split("/") if p]
        content_root = "/" + "/".join(source_parts[:2]) + "/" if len(source_parts) >= 2 else ""
        segments = []
        pending = []
        removed = 0
        
        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media = urljoin(source_url, line)
                if content_root and content_root not in urlparse(media).path:
                    removed += 1
                else:
                    segments.extend(pending)
                    segments.append(media)
                pending = []
                continue
            segments.append(self._rewrite_m3u8_tag(line, source_url))

        # 清理无效标记
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line == "#EXT-X-KEY:METHOD=NONE" or line == "#EXT-X-DISCONTINUITY":
                if not out or out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
                    continue
            out.append(line)
        while len(out) > 1 and out[-2] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
            out.pop(-2)
        if removed:
            self.log("m3u8已过滤广告分片: %d" % removed)
        return "\n".join(out) + "\n"

    def _rewrite_m3u8_tag(self, line, source_url):
        """重写 m3u8 标签中的 URI（补全绝对地址）"""
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(match):
                return 'URI="' + urljoin(source_url, match.group(1)) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)
        if line and not line.startswith("#"):
            return urljoin(source_url, line)
        return line

    def isVideoFormat(self, url):
        return bool(re.search(r'\.(m3u8|mp4|ts)(\?|$)', url, re.I))