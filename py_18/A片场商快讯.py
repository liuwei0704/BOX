# coding: utf-8
# TVBox/FongMi 爬虫 - A片场商快讯
# 站点: https://214841.apiankx011.top/kuaixun/
# 类型: MacCMS 影视站 (成人内容)
# 最后验证: 2026-09-06

import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://214841.apiankx011.top/kuaixun"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "27", "type_name": "国产乱伦"},
            {"type_id": "28", "type_name": "网曝黑料"},
            {"type_id": "29", "type_name": "自拍偷拍"},
            {"type_id": "30", "type_name": "国产传媒"},
            {"type_id": "31", "type_name": "国产精品"},
            {"type_id": "32", "type_name": "探花精品"},
            {"type_id": "33", "type_name": "网红主播"},
            {"type_id": "34", "type_name": "AI换脸"},
            {"type_id": "35", "type_name": "同性恋"},
            {"type_id": "36", "type_name": "3D动漫"},
            {"type_id": "37", "type_name": "欧美精品"},
            {"type_id": "38", "type_name": "韩国主播"},
            {"type_id": "39", "type_name": "高美传媒"},
            {"type_id": "40", "type_name": "国产人妻"},
            {"type_id": "41", "type_name": "麻豆传媒"},
            {"type_id": "42", "type_name": "国产SM"},
        ]
        self.filters = {}
        for c in self.classes:
            self.filters[c["type_id"]] = []

    def getName(self):
        return "A片场商快讯"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        url = f"{self.host}/"
        try:
            r = self.fetch(url, headers=self.headers, timeout=15)
            if not r or r.status_code != 200:
                return {"list": []}
            html = r.text
            # 匹配视频条目：先找所有 <li> 包含 thumbnail 的条目
            items = re.findall(
                r'<a[^>]*class="thumbnail"[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*data-original="([^"]+)"[^>]*>.*?<h5><a[^>]*href="[^"]*"[^>]*>([^<]+)</a></h5>.*?<p[^>]*class="vodtitle">(.*?)</p>',
                html, re.S
            )
            videos = []
            for href, pic, title, info_html in items:
                if not href:
                    continue
                vid = re.search(r'/id/(\d+)/', href)
                vid = vid.group(1) if vid else ""
                if not vid:
                    continue
                # 从 info_html 中提取纯文本，去除 span 标签
                info = re.sub(r'<[^>]+>', '', info_html).strip()
                parts = info.split(" - ")
                remarks = parts[0].strip() if parts else info
                videos.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": pic.strip(),
                    "vod_remarks": remarks
                })
            return {"list": videos[:30]}
        except Exception as e:
            self.log({"homeVideo": "error", "msg": str(e)})
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or 1
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        try:
            r = self.fetch(url, headers=self.headers, timeout=15)
            if not r or r.status_code != 200:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            html = r.text
            items = re.findall(
                r'<a[^>]*class="thumbnail"[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*data-original="([^"]+)"[^>]*>.*?<h5><a[^>]*href="[^"]*"[^>]*>([^<]+)</a></h5>.*?<p[^>]*class="vodtitle">(.*?)</p>',
                html, re.S
            )
            videos = []
            for href, pic, title, info_html in items:
                if not href:
                    continue
                vid = re.search(r'/id/(\d+)/', href)
                vid = vid.group(1) if vid else ""
                if not vid:
                    continue
                info = re.sub(r'<[^>]+>', '', info_html).strip()
                parts = info.split(" - ")
                remarks = parts[0].strip() if parts else info
                videos.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": pic.strip(),
                    "vod_remarks": remarks
                })
            total_pages = 254
            m = re.search(r'共(\d+)页', html)
            if m:
                total_pages = int(m.group(1))
            return {
                "list": videos,
                "page": int(page),
                "pagecount": total_pages,
                "limit": 20,
                "total": total_pages * 20
            }
        except Exception as e:
            self.log({"category": "error", "tid": tid, "pg": page, "msg": str(e)})
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0]) if isinstance(ids, list) else str(ids)
        url = f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        try:
            r = self.fetch(url, headers=self.headers, timeout=15)
            if not r or r.status_code != 200:
                return {"list": []}
            html = r.text
            title = re.search(r'<title>([^<]+)</title>', html)
            title = title.group(1).replace("在线播放--A片场商快讯", "").strip() if title else "未知"
            pic = ""
            m = re.search(r'data-original="([^"]+)"', html)
            if m:
                pic = m.group(1)
            play_url = ""
            m = re.search(r'"url":"([^"]+)"', html)
            if m:
                play_url = m.group(1).replace("\\/", "/")
            if not play_url:
                m = re.search(r'"url":"([^"]+)"', html)
                if m:
                    play_url = m.group(1).replace("\\/", "/")
            if play_url:
                return {
                    "list": [{
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": "1",
                        "vod_content": "",
                        "vod_play_from": "播放",
                        "vod_play_url": f"播放${play_url}"
                    }]
                }
            return {"list": []}
        except Exception as e:
            self.log({"detail": "error", "vid": vid, "msg": str(e)})
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        page = pg or 1
        url = f"{self.host}/index.php/vod/search.html"
        try:
            r = self.post(url, data={"wd": key}, headers=self.headers, timeout=15)
            if not r or r.status_code != 200:
                return {"list": [], "page": int(page)}
            html = r.text
            items = re.findall(
                r'<a[^>]*class="thumbnail"[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*data-original="([^"]+)"[^>]*>.*?<h5><a[^>]*href="[^"]*"[^>]*>([^<]+)</a></h5>.*?<p[^>]*class="vodtitle">(.*?)</p>',
                html, re.S
            )
            videos = []
            for href, pic, title, info_html in items:
                if not href:
                    continue
                vid = re.search(r'/id/(\d+)/', href)
                vid = vid.group(1) if vid else ""
                if not vid:
                    continue
                info = re.sub(r'<[^>]+>', '', info_html).strip()
                parts = info.split(" - ")
                remarks = parts[0].strip() if parts else info
                videos.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": pic.strip(),
                    "vod_remarks": remarks
                })
            return {"list": videos, "page": int(page)}
        except Exception as e:
            self.log({"search": "error", "key": key, "msg": str(e)})
            return {"list": [], "page": int(page)}

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        play_url = str(id).strip()
        if play_url.startswith("http"):
            if ".m3u8" in play_url:
                # 该站 m3u8 有少量跨目录广告分片，需要过滤
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(play_url),
                    "header": {"User-Agent": self.headers["User-Agent"]}
                }
            return {"parse": 0, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"]}}
        return {"parse": 1, "url": play_url, "header": self.headers}

    def recommendContent(self, ids, pg):
        return {"list": []}

    def destroy(self):
        pass

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if not url:
            return ""
        url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url), safe="")

    def localProxy(self, param):
        try:
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")
            if target.startswith("url="):
                target = target[4:]
            elif "url=" in target:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(target).query)
                if "url" in qs:
                    target = qs["url"][0]
            target = urllib.parse.unquote(str(target or ""))
            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            resp = self.fetch(target, headers=self.headers, timeout=20)
            if not resp:
                return [502, "text/plain", b"fetch failed"]
            content = getattr(resp, "content", b"") or b""
            if not content and getattr(resp, "text", ""):
                content = resp.text.encode("utf-8", errors="ignore")
            if not content:
                return [502, "text/plain", b"empty content"]

            if b"#EXTM3U" in content[:256]:
                cleaned = self._clean_m3u8(content.decode("utf-8", errors="ignore"), target)
                return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]
            return [200, "application/octet-stream", content]
        except Exception as e:
            self.log({"localProxy": "error", "msg": str(e)})
            return [500, "text/plain", b"proxy error"]

    def _clean_m3u8(self, text, source_url):
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 第1层：图片流检测（该站非图片流，但仍保留）
        is_img = self._is_fake_image_stream(text, source_url)
        if is_img:
            self.log({"stage": "clean", "fake_image_stream": True, "action": "keep_suffix_as_is"})

        # 第2层：多码率主表
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            return self._clean_m3u8_multi(lines, source_url)

        # 第3层：正片目录锚点
        main_dir = self._resolve_main_dir(lines, source_url, is_image_stream=is_img)

        # 第4层：分片过滤
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)

        # 第5层：全滤兜底（误杀过半即回退）
        if removed > 0 and (kept == 0 or removed > kept):
            self.log({"stage": "clean", "fallback": "no_filter", "removed": removed, "kept": kept, "anchor": main_dir})
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        if removed:
            self.log({"stage": "clean", "removed": removed, "kept": kept, "anchor": main_dir})

        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

    def _is_fake_image_stream(self, text, source_url):
        IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
        VIDEO_EXT = (".ts", ".m4s", ".mp4", ".aac", ".m4a")
        has_video = False
        has_image = False
        for line in str(text or "").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            path = line.split("?")[0].split("#")[0].lower()
            if path.endswith(VIDEO_EXT):
                has_video = True
            elif path.endswith(IMAGE_EXT):
                has_image = True
        return has_image and not has_video

    def _clean_m3u8_multi(self, lines, source_url):
        out = []
        for line in lines:
            if line.startswith("#"):
                out.append(line)
                continue
            child = urllib.parse.urljoin(source_url, line)
            if ".m3u8" in child.lower():
                out.append(self._m3u8_proxy_url(child))
            else:
                out.append(child)
        return "\n".join(out) + "\n"

    def _resolve_main_dir(self, lines, source_url, is_image_stream=False):
        import posixpath
        base_dir = posixpath.dirname(urllib.parse.urlparse(source_url).path)
        if not base_dir.endswith("/"):
            base_dir += "/"

        if is_image_stream:
            counter = {}
            for line in lines:
                if not line or line.startswith("#"):
                    continue
                p = urllib.parse.urlparse(urllib.parse.urljoin(source_url, line)).path
                d = posixpath.dirname(p)
                if d and d != "/":
                    counter[d + "/"] = counter.get(d + "/", 0) + 1
            if counter:
                return max(counter.items(), key=lambda kv: kv[1])[0]
            return base_dir

        for line in lines:
            if not line.startswith("#EXT-X-KEY") or "URI=" not in line:
                continue
            m = re.search(r'URI="([^"]+)"', line)
            if not m:
                continue
            key_uri = m.group(1)
            key_path = urllib.parse.urlparse(
                key_uri if key_uri.startswith("http")
                else urllib.parse.urljoin(source_url, key_uri)
            ).path
            key_dir = posixpath.dirname(key_path)
            if key_dir and key_dir != "/":
                return key_dir + "/"
        return base_dir

    def _filter_segments(self, lines, source_url, main_dir):
        segments = []
        pending = []
        removed = 0
        kept = 0
        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media_url = urllib.parse.urljoin(source_url, line)
                media_path = urllib.parse.urlparse(media_url).path
                if media_path.startswith(main_dir):
                    segments.extend(pending)
                    segments.append(media_url)
                    kept += 1
                else:
                    removed += 1
                pending = []
                continue
            if line.startswith("#"):
                segments.append(line)
            else:
                segments.append(urllib.parse.urljoin(source_url, line))
        return segments, removed, kept

    def _dedup_tags(self, segments, source_url):
        NOISE = ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE")
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in NOISE:
                if not out or out[-1] in NOISE:
                    continue
            out.append(line)
        while len(out) > 1 and out[-1] in NOISE:
            out.pop()
        return out

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