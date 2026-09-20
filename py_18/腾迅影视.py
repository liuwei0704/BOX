# coding: utf-8
"""
站点: 腾迅影视
域名: dm3gcwsu8.tengxunyingshi.sbs
主域名: https://dm3gcwsu8.tengxunyingshi.sbs
备用域名: 暂无
类型: 成人影视站 (MacCMS风格)
特征: 标准HTML影视站, 多码率m3u8带广告目录
验证时间: 2026-09-05
来源: 用户提供
m3u8结构: 多码率流, KEY URI目录锚点, 广告目录 /20260904/seBMuJoW/, /20260718/Qu1lDiqe/
"""
import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://dm3gcwsu8.tengxunyingshi.sbs"
        self.classes = [
            {"type_id": "1", "type_name": "国产视频"},
            {"type_id": "6", "type_name": "国产传媒"},
            {"type_id": "2", "type_name": "国产探花"},
            {"type_id": "7", "type_name": "极品学生"},
            {"type_id": "8", "type_name": "野战户外"},
            {"type_id": "9", "type_name": "网曝黑料"},
            {"type_id": "10", "type_name": "日本有码"},
        ]
        self.filters = {
            "1": [],
            "6": [],
            "2": [],
            "7": [],
            "8": [],
            "9": [],
            "10": [],
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        self.NEED_CLEAN = True

    def getName(self):
        return "腾迅影视"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            res = self.fetch(self.host + "/")
            if not res or res.status_code != 200:
                return {"list": []}
            html = res.text
            items = []
            # 同时捕获 href 和内容
            video_blocks = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*video-item[^"]*"[^>]*>(.*?)</a>', html, re.S)
            for href_raw, block in video_blocks:
                href = urllib.parse.urljoin(self.host, href_raw.strip())
                pic_match = re.search(r'url\(([^)]+)\)', block)
                pic = pic_match.group(1).strip().strip("'").strip('"') if pic_match else ""
                if pic and not pic.startswith("http"):
                    pic = urllib.parse.urljoin(self.host, pic)
                badge_match = re.search(r'<div[^>]*class="[^"]*video-badge[^"]*"[^>]*>([^<]*)</div>', block)
                badge = badge_match.group(1).strip() if badge_match else ""
                title_match = re.search(r'<div[^>]*class="[^"]*video-title[^"]*"[^>]*>([^<]*)</div>', block)
                title = title_match.group(1).strip() if title_match else ""
                info_match = re.search(r'<div[^>]*class="[^"]*video-info[^"]*"[^>]*>([^<]*)</div>', block)
                info = info_match.group(1).strip() if info_match else ""
                if href and title:
                    items.append({
                        "vod_id": href,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": badge or info
                    })
            return {"list": items[:20]}
        except Exception as e:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        if tid in ["1", "6", "2", "7", "8", "9", "10"]:
            url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        else:
            url = f"{self.host}/index.php/vod/type/id/1/page/{page}.html"
        try:
            res = self.fetch(url, headers=self.headers)
            if not res or res.status_code != 200:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            html = res.text
            items = []
            # 同时捕获 href 和内容
            video_blocks = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*video-item[^"]*"[^>]*>(.*?)</a>', html, re.S)
            for href_raw, block in video_blocks:
                href = urllib.parse.urljoin(self.host, href_raw.strip())
                pic_match = re.search(r'url\(([^)]+)\)', block)
                pic = pic_match.group(1).strip().strip("'").strip('"') if pic_match else ""
                if pic and not pic.startswith("http"):
                    pic = urllib.parse.urljoin(self.host, pic)
                badge_match = re.search(r'<div[^>]*class="[^"]*video-badge[^"]*"[^>]*>([^<]*)</div>', block)
                badge = badge_match.group(1).strip() if badge_match else ""
                title_match = re.search(r'<div[^>]*class="[^"]*video-title[^"]*"[^>]*>([^<]*)</div>', block)
                title = title_match.group(1).strip() if title_match else ""
                info_match = re.search(r'<div[^>]*class="[^"]*video-info[^"]*"[^>]*>([^<]*)</div>', block)
                info = info_match.group(1).strip() if info_match else ""
                if href and title:
                    items.append({
                        "vod_id": href,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": badge or info
                    })
            total_pages = 5
            try:
                page_match = re.search(r'第(\d+)页', html)
                current = int(page_match.group(1)) if page_match else int(page)
            except:
                current = int(page)
            return {
                "list": items,
                "page": current,
                "pagecount": total_pages,
                "limit": 20,
                "total": total_pages * 20
            }
        except Exception as e:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        try:
            url = ids[0]
            if not url.startswith("http"):
                url = urllib.parse.urljoin(self.host, url)
            res = self.fetch(url, headers=self.headers)
            if not res or res.status_code != 200:
                return {"list": []}
            html = res.text
            
            title_match = re.search(r'<title>([^<]*)</title>', html)
            title = title_match.group(1).strip() if title_match else "未知"
            title = re.sub(r'\s*[-|].*$', '', title)
            
            pic = ""
            pic_match = re.search(r'url\(([^)]+)\)', html)
            if pic_match:
                pic = pic_match.group(1).strip().strip("'").strip('"')
                if pic and not pic.startswith("http"):
                    pic = urllib.parse.urljoin(self.host, pic)
            
            desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', html)
            desc = desc_match.group(1).strip() if desc_match else ""
            
            play_url = ""
            url_field_match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
            if url_field_match:
                play_url = url_field_match.group(1).replace("\\/", "/")
            
            if not play_url:
                player_match = re.search(r'var player_aaaa\s*=\s*({[^;]+});', html, re.S)
                if player_match:
                    url_match = re.search(r'"url"\s*:\s*"([^"]+)"', player_match.group(1))
                    if url_match:
                        play_url = url_match.group(1).replace("\\/", "/")
            
            if not play_url:
                m3u8_pattern = r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)'
                m3u8_match = re.search(m3u8_pattern, html)
                if m3u8_match:
                    play_url = m3u8_match.group(1)
            
            vod_play_from = ""
            vod_play_url = ""
            if play_url:
                vod_play_from = "高清"
                vod_play_url = f"高清${play_url}"
            
            return {
                "list": [{
                    "vod_id": url,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": "",
                    "vod_content": desc,
                    "vod_play_from": vod_play_from,
                    "vod_play_url": vod_play_url
                }]
            }
        except Exception as e:
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        return {"list": [], "page": 1}

    def playerContent(self, flag, id, vipFlags):
        ua = self.headers.get("User-Agent", "")
        if not id:
            return {"parse": 1, "url": "", "header": {"User-Agent": ua}}

        if self._is_media_url(id):
            return self._wrap_play(id, ua)

        if not id.startswith("http"):
            id = urllib.parse.urljoin(self.host, id)

        try:
            res = self.fetch(id, headers=self.headers)
            if res and res.status_code == 200:
                html = res.text
                player_match = re.search(r'var player_aaaa\s*=\s*({[^;]*?});', html, re.S)
                if player_match:
                    try:
                        import json
                        player_data = json.loads(player_match.group(1))
                        play_url = player_data.get("url", "")
                        if play_url:
                            play_url = play_url.replace("\\/", "/")
                            if self._is_media_url(play_url):
                                return self._wrap_play(play_url, ua)
                    except:
                        url_match = re.search(r'"url"\s*:\s*"([^"]+)"', player_match.group(1))
                        if url_match:
                            play_url = url_match.group(1).replace("\\/", "/")
                            if self._is_media_url(play_url):
                                return self._wrap_play(play_url, ua)
                
                url_pattern = r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"'
                url_match = re.search(url_pattern, html)
                if url_match:
                    play_url = url_match.group(1).replace("\\/", "/")
                    if self._is_media_url(play_url):
                        return self._wrap_play(play_url, ua)
                
                m3u8_pattern = r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)'
                m3u8_match = re.search(m3u8_pattern, html)
                if m3u8_match:
                    play_url = m3u8_match.group(1)
                    if self._is_media_url(play_url):
                        return self._wrap_play(play_url, ua)
                        
                iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
                if iframe_match:
                    iframe_url = urllib.parse.urljoin(id, iframe_match.group(1))
                    sub_res = self.fetch(iframe_url, headers=self.headers)
                    if sub_res and sub_res.status_code == 200:
                        sub_html = sub_res.text
                        sub_pattern = r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)'
                        sub_match = re.search(sub_pattern, sub_html)
                        if sub_match:
                            play_url = sub_match.group(1)
                            if self._is_media_url(play_url):
                                return self._wrap_play(play_url, ua)
        except:
            pass

        return {"parse": 1, "url": id, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

    def _is_media_url(self, url):
        if not url or not str(url).startswith(("http://", "https://")):
            return False
        media_ext = (".m3u8", ".mp4", ".mkv", ".flv", ".avi", ".m4v", ".mov", ".ts")
        path = str(url).split("?")[0].split("#")[0].lower()
        if path.endswith(media_ext):
            return True
        return ".m3u8" in str(url).lower() or "playlist.m3u8" in str(url).lower()

    def _wrap_play(self, url, ua):
        header = {"User-Agent": ua}
        if self.NEED_CLEAN and ".m3u8" in url.lower():
            return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": header}
        return {"parse": 0, "url": url, "header": header}

    def _m3u8_proxy_url(self, url):
        if url:
            url = url.replace("\\/", "/")
        return "http://127.0.0.1:9978/proxy?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

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
            return [500, "text/plain", f"localProxy error: {e}".encode("utf-8", errors="ignore")]

    def _clean_m3u8(self, text, source_url):
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        is_img = self._is_fake_image_stream(text, source_url)
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            return self._clean_m3u8_multi(lines, source_url)

        main_dir = self._resolve_main_dir(lines, source_url, is_image_stream=is_img)
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)

        if removed > 0 and (kept == 0 or removed > kept):
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

    def _is_fake_image_stream(self, text, source_url):
        image_ext = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
        video_ext = (".ts", ".m4s", ".mp4", ".aac", ".m4a")
        has_video = False
        has_image = False
        for line in str(text or "").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            path = line.split("?")[0].split("#")[0].lower()
            if path.endswith(video_ext):
                has_video = True
            elif path.endswith(image_ext):
                has_image = True
        return has_image and not has_video

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
                key_uri if key_uri.startswith(("http://", "https://"))
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
        noise = ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE")
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in noise:
                if not out or out[-1] in noise:
                    continue
            out.append(line)
        while len(out) > 1 and out[-1] in noise:
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

    def _clean_m3u8_multi(self, lines, source_url):
        out = []
        for line in lines:
            if line.startswith("#"):
                out.append(line)
            else:
                child = urllib.parse.urljoin(source_url, line)
                if ".m3u8" in child.lower():
                    out.append(self._m3u8_proxy_url(child))
                else:
                    out.append(child)
        return "\n".join(out) + "\n"

    def recommendContent(self, ids, flag=None):
        return {"list": []}

    def destroy(self):
        pass