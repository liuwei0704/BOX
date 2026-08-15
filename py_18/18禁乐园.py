# coding=utf-8
# 站点: 18禁乐园 (https://18jin1426.sbs)
# 说明: 支持 m3u8 广告过滤 (v3.0)

import re
import json
import posixpath
import urllib.parse
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://18jin1426.sbs"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host + '/'
        }
        self.classes = [
            {"type_id": "1", "type_name": "国产自拍"},
            {"type_id": "2", "type_name": "主播诱惑"},
            {"type_id": "3", "type_name": "探花约炮"},
            {"type_id": "4", "type_name": "偷拍偷窥"},
            {"type_id": "5", "type_name": "网曝吃瓜"},
            {"type_id": "6", "type_name": "抖阴短片"},
            {"type_id": "7", "type_name": "传媒剧情"},
            {"type_id": "8", "type_name": "日韩无码"},
            {"type_id": "9", "type_name": "中文字幕"},
            {"type_id": "10", "type_name": "换脸明星"},
        ]
        self.filters = {}

    def getName(self):
        return "18禁乐园"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def _fetch_html(self, url):
        try:
            res = self.fetch(url, headers=self.headers, timeout=15)
            if res is None:
                return ""
            if hasattr(res, "text") and res.text:
                return res.text
            if hasattr(res, "content") and res.content:
                try:
                    return res.content.decode('utf-8', errors='ignore')
                except Exception:
                    pass
            return ""
        except Exception:
            return ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html(self.host + "/")
        items = self._parse_list(html)
        return {"list": items[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        html = self._fetch_html(url)
        items = self._parse_list(html)
        pagecount = self._get_pagecount(html)
        return {
            "list": items,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 20,
            "total": pagecount * 20
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vod_id = str(ids[0])
        if not vod_id.startswith("http"):
            vod_id = f"{self.host}/index.php/vod/detail/id/{vod_id}.html"
        html = self._fetch_html(vod_id)
        return self._parse_detail(html, vod_id)

    def searchContent(self, key, quick, pg="1"):
        if not key or key.strip() == "":
            return {"list": [], "page": 1}
        page = pg or "1"
        url = f"{self.host}/index.php/vod/search/page/{page}/wd/{urllib.parse.quote(key)}.html"
        html = self._fetch_html(url)
        items = self._parse_list(html)
        return {"list": items, "page": int(page)}

    def playerContent(self, flag, id, vipFlags):
        try:
            play_url = id if id.startswith("http") else f"{self.host}{id if id.startswith('/') else '/' + id}"
            html = self._fetch_html(play_url)
            if not html:
                return {"parse": 1, "url": play_url}

            real_url = ""

            # 方法1: 搜索转义后的 m3u8 地址
            match = re.search(r'https?:\\/\\/[^"\'\s]+\.m3u8[^"\'\s]*', html)
            if match:
                real_url = match.group(0).replace('\\/', '/')

            # 方法2: 搜索标准 m3u8 地址
            if not real_url:
                match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
                if match:
                    real_url = match.group(1)

            # 方法3: 搜索 mp4 地址
            if not real_url:
                match = re.search(r'https?://[^\s"\']+\.mp4[^\s"\']*', html)
                if match:
                    real_url = match.group(0).replace('\\/', '/')

            if real_url:
                real_url = real_url.replace("\\/", "/").strip()
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(real_url),
                    "header": self.headers
                }

            # 降级：返回 iframe 嗅探
            iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', html)
            if iframe_match:
                iframe_url = iframe_match.group(1)
                if iframe_url.startswith('/'):
                    iframe_url = self.host + iframe_url
                return {"parse": 1, "url": iframe_url}

            return {"parse": 1, "url": play_url}

        except Exception as e:
            return {"parse": 1, "url": id}

    def localProxy(self, param):
        """m3u8 本地代理 + 广告分片过滤 (v3.0)"""
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

            res = self.fetch(target, headers={"User-Agent": self.headers.get("User-Agent", "")}, timeout=15)
            if not res:
                return [502, "text/plain", b"fetch failed"]

            content = getattr(res, "content", b"") or b""
            if not content and hasattr(res, "text") and res.text:
                content = res.text.encode("utf-8", errors="ignore")

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
        """清洗 m3u8：过滤广告分片 (基于 #EXT-X-KEY 目录匹配)"""
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

    def _parse_list(self, html):
        items = []
        if not html:
            return items

        blocks = re.findall(r'<div[^>]*class="[^"]*video[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        if not blocks:
            blocks = re.findall(r'<div[^>]*class="[^"]*(?:video-item|thumb|item|col-video)[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)

        for block in blocks:
            link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>', block)
            if not link_match:
                continue
            href = link_match.group(1)
            if '/vod/detail/' not in href and '/vod/' not in href:
                continue

            title_match = re.search(r'<a[^>]*title="([^"]*)"', block)
            title = title_match.group(1) if title_match else ""
            if not title:
                title_match = re.search(r'<a[^>]*>([^<]+)</a>', block)
                title = title_match.group(1).strip() if title_match else ""
            title = re.sub(r'\s+', ' ', title).strip()

            img_match = re.search(r'<img[^>]*(?:data-src|src)="([^"]+)"', block)
            pic = img_match.group(1) if img_match else ""

            remark_match = re.search(r'<span[^>]*class="[^"]*(?:overlay|views|duration|meta|badge)[^"]*"[^>]*>([^<]*)</span>', block)
            remark = remark_match.group(1).strip() if remark_match else ""

            if title:
                full_url = href if href.startswith("http") else self.host + href
                items.append({
                    "vod_id": full_url,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })

        return items

    def _parse_detail(self, html, vod_id):
        if not html:
            return {"list": []}

        # 标题：从 h1.panel-title 提取
        title_match = re.search(r'<h1[^>]*class="[^"]*panel-title[^"]*"[^>]*>([^<]*)</h1>', html)
        title = title_match.group(1).strip() if title_match else ""

        if not title:
            title_match = re.search(r'<h3[^>]*class="[^"]*title[^"]*"[^>]*>([^<]*)</h3>', html)
            title = title_match.group(1).strip() if title_match else ""

        if not title:
            title_match = re.search(r'<div[^>]*class="[^"]*panel-heading[^"]*"[^>]*>\s*<h[1-6][^>]*>([^<]*)</h[1-6]>', html, re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()

        if not title:
            title_match = re.search(r'<title>([^<]*)</title>', html)
            if title_match:
                title = title_match.group(1).strip()
                title = re.sub(r'\s*[-–]\s*18禁乐园$', '', title)

        img_match = re.search(r'<img[^>]*(?:data-src|src)="([^"]+)"[^>]*class="[^"]*(?:video-pic|thumb)[^"]*"', html)
        pic = img_match.group(1) if img_match else ""

        content_match = re.search(r'<div[^>]*class="[^"]*(?:panel-body|description|video-description)[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        content = content_match.group(1).strip() if content_match else ""

        play_from = []
        play_url = []

        play_btns = re.findall(r'<a[^>]*href="([^"]*index.php/vod/play/[^"]*)"[^>]*>([^<]*)</a>', html)
        for href, name in play_btns:
            line_name = name.strip() or "线路"
            play_from.append(line_name)
            full_url = href if href.startswith("http") else self.host + href
            play_url.append(full_url)

        if not play_from:
            vid_match = re.search(r'/id/(\d+)', vod_id)
            if vid_match:
                vid = vid_match.group(1)
                play_from.append("默认线路")
                play_url.append(f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html")

        return {
            "list": [{
                "vod_id": vod_id,
                "vod_name": title or "未知标题",
                "vod_pic": pic,
                "vod_content": content,
                "vod_play_from": "$$$".join(play_from) if play_from else "18禁乐园",
                "vod_play_url": "$$$".join(play_url) if play_url else vod_id
            }]
        }

    def _get_pagecount(self, html):
        if not html:
            return 1
        page_match = re.search(r'共(\d+)頁', html)
        if not page_match:
            page_match = re.search(r'共(\d+)页', html)
        if page_match:
            return int(page_match.group(1))
        return 99

    def destroy(self):
        pass