# -*- coding: utf-8 -*-
"""
快活空间 - 爬虫源
https://www.buhuibania.cfd/
站点类型: MacCMS 成人影视站
支持 m3u8 广告过滤 (localProxy)
"""
import re
import sys
import json
import urllib.parse
import posixpath
from html import unescape
from urllib.parse import quote

sys.path.append("..")
try:
    from base.spider import Spider as BaseSpider
except Exception:
    class BaseSpider:
        def __init__(self):
            pass


class Spider(BaseSpider):
    host = "https://www.buhuibania.cfd"
    timeout = 20

    def __init__(self):
        try:
            super().__init__()
        except Exception:
            pass
        self.classes = [
            {"type_id": "1", "type_name": "麻豆传媒"},
            {"type_id": "2", "type_name": "欧美盛宴"},
            {"type_id": "3", "type_name": "明星系列"},
            {"type_id": "4", "type_name": "国产精品"},
            {"type_id": "7", "type_name": "三级电影"},
            {"type_id": "8", "type_name": "少女萝莉"},
            {"type_id": "9", "type_name": "高清无码"},
            {"type_id": "10", "type_name": "动漫系列"},
            {"type_id": "11", "type_name": "网红事件"},
            {"type_id": "12", "type_name": "国产主播"},
        ]
        self.filters = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    def getName(self):
        return "快活空间"

    def init(self, extend=""):
        extend = (extend or "").strip()
        if extend.startswith("http"):
            self.host = extend.rstrip("/")
        return True

    def destroy(self):
        pass

    def getProxyUrl(self):
        """获取本地代理地址"""
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        """生成m3u8代理地址"""
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html(self.host + "/")
        items = self._parse_video_list(html)
        return {"list": items[:20]}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        page = int(pg) if str(pg).isdigit() else 1
        tid = str(tid or "1")
        url = f"{self.host}/index.php/vod/type/id/{tid}.html"
        if page > 1:
            url += f"?page={page}"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        pagecount = self._parse_page_count(html) or (page + 1)
        return {
            "list": items,
            "page": page,
            "pagecount": pagecount,
            "limit": 20,
            "total": pagecount * 20,
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0] if isinstance(ids, list) else ids).strip()
        id_match = re.search(r'/(\d+)\.html$', vid)
        if id_match:
            pure_id = id_match.group(1)
        else:
            pure_id = vid
        play_url = f"/index.php/vod/play/id/{pure_id}/sid/1/nid/1.html"
        detail_html = self._fetch_html(self.host + "/index.php/vod/detail/id/" + pure_id + ".html")
        title, cover, content = self._parse_detail_info(detail_html)
        return {
            "list": [{
                "vod_id": pure_id,
                "vod_name": title or f"视频{pure_id}",
                "vod_pic": self._fix_url(cover),
                "vod_content": content,
                "vod_play_from": "播放",
                "vod_play_url": f"播放${play_url}",
            }]
        }

    def searchContent(self, key, quick, pg="1"):
        key = (key or "").strip()
        if not key:
            return {"list": []}
        page = int(pg) if str(pg).isdigit() else 1
        url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}"
        if page > 1:
            url += f"&page={page}"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        return {"list": items, "page": page}

    def playerContent(self, flag, id, vipFlags=None):
        url = (id or "").strip().replace("\\/", "/")
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Origin": self.host,
            "Accept": "*/*",
        }
        if url.startswith("http") and ".m3u8" in url:
            return {
                "parse": 0,
                "jx": 0,
                "url": self._m3u8_proxy_url(url),
                "header": header
            }
        if url.startswith("/"):
            html = self._fetch_html(self.host + url)
            m3u8_url = self._extract_m3u8_from_html(html)
            if m3u8_url:
                return {
                    "parse": 0,
                    "jx": 0,
                    "url": self._m3u8_proxy_url(m3u8_url),
                    "header": header
                }
            detail_url = re.sub(r'/play/id/(\d+)/.*', r'/detail/id/\1.html', url)
            if detail_url != url:
                html2 = self._fetch_html(self.host + detail_url)
                m3u8_url2 = self._extract_m3u8_from_html(html2)
                if m3u8_url2:
                    return {
                        "parse": 0,
                        "jx": 0,
                        "url": self._m3u8_proxy_url(m3u8_url2),
                        "header": header
                    }
            return {"parse": 1, "jx": 0, "url": url, "header": header}
        return {"parse": 1, "jx": 0, "url": url, "header": header}

    def recommendContent(self, ids, pg="1"):
        html = self._fetch_html(self.host + "/")
        items = self._parse_video_list(html)
        return {"list": items[:10]}

    def localProxy(self, param):
        """
        m3u8本地代理 - 广告分片过滤
        参考 m3u8_ad_filter.md v3.0
        """
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

            resp = self.fetch(target, headers={"User-Agent": self.headers.get("User-Agent", "")}, timeout=15)
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
        """清洗m3u8 - 过滤广告分片"""
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
        """重写m3u8标签中的URI"""
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

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, timeout=self.timeout)
            if resp and hasattr(resp, "status_code") and resp.status_code == 200:
                return resp.text
            if resp and hasattr(resp, "text"):
                return resp.text
        except Exception as e:
            print("[快活空间] fetch error:", e)
        return ""

    def _parse_video_list(self, html):
        items = []
        if not html:
            return items
        pattern = r'<li>\s*<a class="thumbnail"\s+href="([^"]+)"[^>]*>\s*<img\s+src="([^"]+)"\s+alt="([^"]*)"'
        matches = re.findall(pattern, html, re.I | re.S)
        if not matches:
            pattern2 = r'<a class="thumbnail"\s+href="([^"]+)"[^>]*>\s*<img[^>]+src="([^"]+)"[^>]+alt="([^"]*)"'
            matches = re.findall(pattern2, html, re.I | re.S)
        seen = set()
        for href, pic, title in matches:
            if href in seen:
                continue
            seen.add(href)
            name = unescape(title).strip() or "未知视频"
            items.append({
                "vod_id": href,
                "vod_name": name,
                "vod_pic": self._fix_url(pic),
                "vod_remarks": "最新"
            })
        return items

    def _parse_page_count(self, html):
        if not html:
            return 1
        pattern = r'<a[^>]*>(\d+)</a>\s*</div>\s*<a[^>]*>下一页'
        m = re.search(pattern, html)
        if m:
            return int(m.group(1)) + 1
        pattern2 = r'<a[^>]*data-num="[^"]*"[^>]*>(\d+)</a>'
        matches = re.findall(pattern2, html)
        if matches:
            return int(matches[-1])
        return 1

    def _parse_detail_info(self, html):
        title = ""
        cover = ""
        content = ""
        if not html:
            return title, cover, content
        m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if m:
            title = unescape(m.group(1)).strip()
        if not title:
            m = re.search(r'<title>([^<]+)</title>', html)
            if m:
                title = unescape(m.group(1)).split("_")[0].strip()
        m = re.search(r'<img[^>]+class="[^"]*vod_img[^"]*"[^>]+src="([^"]+)"', html)
        if m:
            cover = m.group(1)
        if not cover:
            m = re.search(r'<img[^>]+src="([^"]+)"[^>]+alt="[^"]*"', html)
            if m:
                cover = m.group(1)
        m = re.search(r'<div[^>]*class="[^"]*desc[^"]*"[^>]*>([\s\S]*?)</div>', html)
        if m:
            content = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        return title, cover, content

    def _extract_m3u8_from_html(self, html):
        if not html:
            return None
        pattern = r'var\s+player_aaaa\s*=\s*(\{[^;]+\});'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                url = data.get("url", "")
                if url and url.startswith("http"):
                    return url.replace("\\/", "/")
            except Exception:
                pass
        pattern2 = r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"'
        match2 = re.search(pattern2, html)
        if match2:
            url = match2.group(1)
            if url and url.startswith("http"):
                return url.replace("\\/", "/")
        pattern3 = r'https?://[^"\']+\.m3u8[^"\']*'
        match3 = re.search(pattern3, html)
        if match3:
            return match3.group(0)
        return None

    def _fix_url(self, url):
        if not url:
            return ""
        if url.startswith("//"):
            return "https:" + url
        if not url.startswith("http"):
            return self.host.rstrip("/") + (url if url.startswith("/") else "/" + url)
        return url