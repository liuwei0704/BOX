# coding: utf-8
import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://c-you.hair"
        self.classes = [
            {"type_id": "6", "type_name": "国产精品"},
            {"type_id": "7", "type_name": "中文字幕"},
            {"type_id": "8", "type_name": "伦理影片"},
            {"type_id": "9", "type_name": "自拍偷拍"},
            {"type_id": "10", "type_name": "口交视频"},
            {"type_id": "11", "type_name": "日韩无码"},
            {"type_id": "12", "type_name": "制服诱惑"},
            {"type_id": "13", "type_name": "国产色情"},
        ]
        self.filters = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        self.NEED_CLEAN = True

    def _fetch_with_retry(self, url, headers=None, timeout=20):
        """带重试和SSL绕过"""
        headers = headers or self.headers
        try:
            # 尝试使用 verify=False（如果支持）
            try:
                return self.fetch(url, headers=headers, timeout=timeout, verify=False)
            except TypeError:
                # verify 参数不支持，使用默认
                return self.fetch(url, headers=headers, timeout=timeout)
        except Exception as e:
            self.log({"_fetch_retry": "ssl_error", "url": url, "error": str(e)})
            # 如果是SSL错误，尝试用更宽松的配置
            try:
                return self.fetch(url, headers=headers, timeout=timeout)
            except Exception as e2:
                self.log({"_fetch_retry": "second_attempt_failed", "error": str(e2)})
                return None

    def getName(self):
        return "豹纹黑丝"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            r = self._fetch_with_retry(self.host + "/")
            html = r.text if r else ""
            items = self._parse_list(html, self.host + "/")
            return {"list": items[:20]}
        except Exception as e:
            self.log({"homeVideo": "error", "error": str(e)})
            return {"list": []}

    def _parse_list(self, html, page_url):
        items = []
        pattern = r'<div[^>]*class="[^"]*resent-grid[^"]*"[^>]*>.*?<a[^>]*href="(/voddetail/[^"]+)"[^>]*>.*?<img[^>]*data-original="([^"]+)"[^>]*>.*?<p[^>]*class="[^"]*duration-time[^"]*"[^>]*>([^<]+)</p>.*?<h5[^>]*>.*?<a[^>]*href="[^"]+"[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</a>'
        for m in re.finditer(pattern, html, re.S):
            link = m.group(1).strip()
            pic = m.group(2).strip()
            duration = m.group(3).strip()
            title = m.group(4).strip()
            if not link or not title:
                continue
            vid = link.split("/")[-1].replace(".html", "")
            vod_id = f"{vid}|$|{title}|$|{pic}|$|{duration}|$|{link}"
            items.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": duration,
            })
        if not items:
            pattern2 = r'<a[^>]*href="(/voddetail/[^"]+)"[^>]*>.*?<img[^>]*data-original="([^"]+)"[^>]*>.*?<p[^>]*class="[^"]*duration-time[^"]*"[^>]*>([^<]+)</p>.*?<a[^>]*href="[^"]+"[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</a>'
            for m in re.finditer(pattern2, html, re.S):
                link = m.group(1).strip()
                pic = m.group(2).strip()
                duration = m.group(3).strip()
                title = m.group(4).strip()
                if not link or not title:
                    continue
                vid = link.split("/")[-1].replace(".html", "")
                vod_id = f"{vid}|$|{title}|$|{pic}|$|{duration}|$|{link}"
                items.append({
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": duration,
                })
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/vodtype/{tid}-{page}.html"
        try:
            r = self._fetch_with_retry(url)
            html = r.text if r else ""
            items = self._parse_list(html, url)
            pagecount = 81
            for m in re.finditer(r'<a[^>]*href="[^"]*"[^>]*>(\d+)</a>', html):
                try:
                    p = int(m.group(1))
                    if p > pagecount:
                        pagecount = p
                except:
                    pass
            return {
                "list": items,
                "page": int(page),
                "pagecount": pagecount,
                "limit": 20,
                "total": pagecount * 20
            }
        except Exception as e:
            self.log({"category": "error", "tid": tid, "pg": page, "error": str(e)})
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

    @staticmethod
    def _norm_ids(ids):
        if ids is None:
            return ""
        if isinstance(ids, (list, tuple)):
            if not ids:
                return ""
            ids = ids[0]
        if isinstance(ids, bytes):
            ids = ids.decode("utf-8", errors="ignore")
        return str(ids).strip()

    def _skeleton(self, vid, title="", pic=""):
        pid = str(vid).split("|$|")[0].replace("$", "|")
        return {"list": [{
            "vod_id": vid,
            "vod_name": title or "未知标题",
            "vod_pic": pic or "",
            "vod_remarks": "解析中",
            "vod_content": "",
            "vod_play_from": "播放",
            "vod_play_url": "播放$" + pid,
        }]}

    def detailContent(self, ids):
        vid = self._norm_ids(ids)
        if not vid:
            return {"list": []}

        if "|$|" in vid:
            parts = vid.split("|$|")
            if len(parts) >= 5 and parts[4]:
                play_page = parts[4]
                if "/voddetail/" in play_page:
                    vid_raw = parts[0]
                    play_page = f"/vodplay/{vid_raw}-1-1.html"
                return {"list": [{
                    "vod_id": vid,
                    "vod_name": parts[1] if len(parts) > 1 else "未知标题",
                    "vod_pic": parts[2] if len(parts) > 2 else "",
                    "vod_remarks": parts[3] if len(parts) > 3 else "",
                    "vod_content": parts[3] if len(parts) > 3 else "",
                    "vod_play_from": "播放",
                    "vod_play_url": f"播放${urllib.parse.urljoin(self.host, play_page)}",
                }]}

        title = pic = play_url = ""
        try:
            vid_raw = vid.split("|$|")[0] if "|$|" in vid else vid
            detail_url = f"{self.host}/voddetail/{vid_raw}.html"
            r = self._fetch_with_retry(detail_url)
            if not r or r.status_code != 200 or len(r.text) < 500:
                return self._skeleton(vid)

            html = r.text
            title_match = re.search(r'<h3[^>]*class="[^"]*text-center[^"]*"[^>]*>([^<]+)</h3>', html)
            if title_match:
                title = title_match.group(1).strip()
            pic_match = re.search(r'<img[^>]*class="[^"]*detail-img[^"]*"[^>]*src="([^"]+)"', html)
            if pic_match:
                pic = pic_match.group(1).strip()
            play_match = re.search(r'<a[^>]*href="(/vodplay/[^"]+)"[^>]*>[^<]*播放[^<]*</a>', html)
            if play_match:
                play_url = play_match.group(1).strip()
            else:
                play_url = f"/vodplay/{vid_raw}-1-1.html"

            froms = ["播放"]
            urls = [f"播放${urllib.parse.urljoin(self.host, play_url)}"]
            from_str, url_str = self._align(froms, urls)
            if not url_str:
                return self._skeleton(vid, title, pic)

            return {"list": [{
                "vod_id": vid,
                "vod_name": title or "未知标题",
                "vod_pic": pic or "",
                "vod_remarks": "",
                "vod_content": "",
                "vod_play_from": from_str,
                "vod_play_url": url_str,
            }]}
        except Exception as e:
            self.log({"detail": "exception", "vid": vid, "error": str(e)})
            return self._skeleton(vid, title, pic)

    @staticmethod
    def _align(froms, urls):
        pairs = [(f, u) for f, u in zip(froms, urls) if f and u and u.strip()]
        if not pairs:
            return "", ""
        return "$$$".join(p[0] for p in pairs), "$$$".join(p[1] for p in pairs)

    def searchContent(self, key, quick, pg="1"):
        try:
            data = f"wd={urllib.parse.quote(key)}"
            r = self.post(f"{self.host}/vodsearch/-------------.html", data=data, headers=self.headers, timeout=15)
            html = r.text if r else ""
            items = self._parse_list(html, self.host + "/")
            return {"list": items, "page": int(pg)}
        except Exception as e:
            self.log({"search": "error", "key": key, "error": str(e)})
            return {"list": [], "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        ua = self.headers.get("User-Agent", "")
        if not id:
            return {"parse": 1, "url": "", "header": {"User-Agent": ua}}

        if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
            if self.NEED_CLEAN and ".m3u8" in id:
                return {"parse": 0, "url": self._m3u8_proxy_url(id), "header": {"User-Agent": ua}}
            return {"parse": 0, "url": id, "header": {"User-Agent": ua}}

        if not id.startswith("http"):
            id = urllib.parse.urljoin(self.host, id)

        html = ""
        try:
            r = self._fetch_with_retry(id)
            if r and r.status_code == 200:
                html = r.text
                self.log({"player": "fetch_success", "html_len": len(html)})
        except Exception as e:
            self.log({"player": "fetch_error", "error": str(e)})

        if not html or len(html) < 500:
            alt_headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "Referer": self.host + "/"
            }
            try:
                r = self._fetch_with_retry(id, headers=alt_headers)
                if r and r.status_code == 200:
                    html = r.text
                    self.log({"player": "fetch_alt_success", "html_len": len(html)})
            except Exception as e:
                self.log({"player": "fetch_alt_error", "error": str(e)})

        if not html or len(html) < 500:
            self.log({"player": "html_too_short", "len": len(html) if html else 0})
            return {"parse": 1, "url": id, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

        patterns = [
            r'var\s+player_aaaa\s*=\s*({[^;]+});',
            r'player_aaaa\s*=\s*({[^;]+});',
            r'var\s+player_aaaa\s*=\s*({[^}]+})',
        ]
        for pat in patterns:
            m = re.search(pat, html, re.S)
            if m:
                try:
                    data = json.loads(m.group(1))
                    url = data.get("url", "")
                    if url and ("m3u8" in url or "mp4" in url):
                        url = url.replace("\\/", "/")
                        self.log({"player": "extracted_m3u8", "url": url})
                        if self.NEED_CLEAN and ".m3u8" in url:
                            return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}
                        return {"parse": 0, "url": url, "header": {"User-Agent": ua}}
                except json.JSONDecodeError as e:
                    self.log({"player": "json_parse_fail", "pattern": pat, "error": str(e)})
                    url_match = re.search(r'"url"\s*:\s*"([^"]+)"', m.group(1))
                    if url_match:
                        url = url_match.group(1).replace("\\/", "/")
                        if url and ("m3u8" in url or "mp4" in url):
                            self.log({"player": "extracted_url_from_raw", "url": url})
                            if self.NEED_CLEAN and ".m3u8" in url:
                                return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}
                            return {"parse": 0, "url": url, "header": {"User-Agent": ua}}

        m = re.search(r'MacPlayer\s*\.\s*PlayUrl\s*=\s*["\']([^"\']+)["\']', html)
        if m:
            url = m.group(1).replace("\\/", "/")
            if url and ("m3u8" in url or "mp4" in url):
                self.log({"player": "macplayer_playurl", "url": url})
                if self.NEED_CLEAN and ".m3u8" in url:
                    return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}
                return {"parse": 0, "url": url, "header": {"User-Agent": ua}}

        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
        if iframe_match:
            iframe_url = urllib.parse.urljoin(id, iframe_match.group(1))
            self.log({"player": "iframe_found", "iframe_url": iframe_url})
            try:
                r = self._fetch_with_retry(iframe_url)
                if r and r.status_code == 200:
                    iframe_html = r.text
                    m = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', iframe_html)
                    if m:
                        url = m.group(1).replace("\\/", "/")
                        self.log({"player": "iframe_m3u8_found", "url": url})
                        if self.NEED_CLEAN:
                            return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}
                        return {"parse": 0, "url": url, "header": {"User-Agent": ua}}
            except Exception as e:
                self.log({"player": "iframe_fetch_error", "error": str(e)})

        m = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html)
        if m:
            url = m.group(1).replace("\\/", "/")
            self.log({"player": "regex_found", "url": url})
            if self.NEED_CLEAN:
                return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}
            return {"parse": 0, "url": url, "header": {"User-Agent": ua}}

        self.log({"player": "all_layers_miss", "page": id})
        return {"parse": 1, "url": id, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

    def _m3u8_proxy_url(self, url):
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

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

        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            return self._clean_m3u8_multi(lines, source_url)

        main_dir = self._resolve_main_dir(lines, source_url)
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)

        if removed > 0 and (kept == 0 or removed > kept):
            self.log({"stage": "clean", "fallback": "no_filter", "removed": removed, "kept": kept, "anchor": main_dir})
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        if removed:
            self.log({"stage": "clean", "removed": removed, "kept": kept, "anchor": main_dir})

        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

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

    def _resolve_main_dir(self, lines, source_url):
        import posixpath
        base_dir = posixpath.dirname(urllib.parse.urlparse(source_url).path)
        if not base_dir.endswith("/"):
            base_dir += "/"
        for line in lines:
            if not line.startswith("#EXT-X-KEY") or "URI=" not in line:
                continue
            m = re.search(r'URI="([^"]+)"', line)
            if not m:
                continue
            key_uri = m.group(1)
            key_path = urllib.parse.urlparse(
                key_uri if key_uri.startswith("http") else urllib.parse.urljoin(source_url, key_uri)
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

    def recommendContent(self, ids, pg):
        return {"list": []}

    def destroy(self):
        pass