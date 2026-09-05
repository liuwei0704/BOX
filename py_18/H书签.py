# coding: utf-8
"""
站点: H书签
主域名: https://z_ml_s.jyspsgdf.sbs/
备用域名: 无
内容类型: 成人影视
特殊说明: 图片流伪装（分片为.jpg），有开头广告，需m3u8清洗
最后验证: 2026-09-05
来源: AI Agent 自动生成
"""
import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://z_ml_s.jyspsgdf.sbs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "1", "type_name": "国产传媒"},
            {"type_id": "2", "type_name": "国产视频"},
            {"type_id": "3", "type_name": "国产二区"},
            {"type_id": "4", "type_name": "日本视频"},
            {"type_id": "5", "type_name": "视频五区"}
        ]
        self.filters = {}
        # 启用m3u8清洗（有开头广告）
        self.NEED_CLEAN = True
        self.verify_ssl = False

    def getName(self):
        return "H书签"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def _fetch(self, url, headers=None, timeout=10):
        try:
            return self.fetch(url, headers=headers or self.headers, timeout=timeout, verify=self.verify_ssl)
        except Exception as e:
            self.log({"_fetch_error": str(e)})
            return None

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            res = self._fetch(self.host + "/")
            if res and res.status_code == 200:
                return self._parse_list(res.text, self.host + "/")
        except Exception as e:
            self.log({"homeVideo_error": str(e)})
        return {"list": []}

    def categoryContent(self, tid, pg, filter=False, extend=""):
        try:
            page = str(pg or "1")
            url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
            res = self._fetch(url)
            if res and res.status_code == 200:
                return self._parse_list(res.text, url)
        except Exception as e:
            self.log({"category_error": str(e)})
        return {"list": [], "page": int(pg or 1), "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        try:
            raw = str(ids[0])
            parts = raw.split('|$|')
            if len(parts) >= 5:
                return {
                    "list": [{
                        "vod_id": parts[0],
                        "vod_name": parts[1],
                        "vod_pic": parts[2],
                        "vod_remarks": parts[3],
                        "vod_content": parts[3],
                        "vod_play_from": "直链",
                        "vod_play_url": f"播放${parts[4]}"
                    }]
                }
        except Exception as e:
            self.log({"detail_error": str(e)})
        return {"list": []}

    def searchContent(self, key, quick=False, pg="1"):
        try:
            encoded = urllib.parse.quote(str(key).encode("utf-8"))
            url = f"{self.host}/index.php/vod/search.html?wd={encoded}"
            res = self._fetch(url)
            if res and res.status_code == 200:
                return self._parse_list(res.text, url)
        except Exception as e:
            self.log({"search_error": str(e)})
        return {"list": [], "page": 1}

    def playerContent(self, flag, id, vipFlags=""):
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        
        ua = self.headers.get("User-Agent", "")
        raw_id = str(id).strip()
        
        if raw_id.startswith("http"):
            # 归一化：替换反斜杠转义
            raw_id = raw_id.replace("\\/", "/")
            if ".m3u8" in raw_id.lower() or ".mp4" in raw_id.lower():
                if self.NEED_CLEAN and ".m3u8" in raw_id.lower():
                    proxy_url = self._m3u8_proxy_url(raw_id)
                    return {"parse": 0, "url": proxy_url, "header": {"User-Agent": ua}}
                return {"parse": 0, "url": raw_id, "header": {"User-Agent": ua}}
        
        if raw_id.startswith("http"):
            page_url = raw_id
        else:
            page_url = urllib.parse.urljoin(self.host, raw_id)
        
        try:
            res = self._fetch(page_url)
            if res and res.status_code == 200:
                m = re.search(r'var\s+player_aaaa\s*=\s*({[^}]+})', res.text)
                if m:
                    try:
                        data = json.loads(m.group(1))
                        url = data.get("url", "")
                        if url:
                            url = url.replace("\\/", "/")
                        if url and ".m3u8" in url.lower():
                            if self.NEED_CLEAN:
                                return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}
                            return {"parse": 0, "url": url, "header": {"User-Agent": ua}}
                    except:
                        pass
                m = re.search(r'"url":"([^"]+\.m3u8[^"]*)"', res.text)
                if m:
                    url = m.group(1).replace("\\/", "/")
                    if self.NEED_CLEAN:
                        return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}
                    return {"parse": 0, "url": url, "header": {"User-Agent": ua}}
        except Exception as e:
            self.log({"player_error": str(e)})
        
        return {"parse": 1, "url": page_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

    def recommendContent(self, ids, pg=""):
        return {"list": []}

    def destroy(self):
        pass

    def _parse_list(self, html, base_url):
        items = []
        pattern = r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?<span[^>]*class="views"[^>]*>.*?([0-9]+)'
        for m in re.finditer(pattern, html, re.S):
            href = m.group(1)
            title = m.group(2).strip()
            pic = m.group(3)
            views = m.group(4)
            if not href or not title:
                continue
            vid_match = re.search(r'/id/(\d+)/', href)
            if not vid_match:
                continue
            vod_id = vid_match.group(1)
            play_url = urllib.parse.urljoin(base_url, href)
            items.append({
                "vod_id": f"{vod_id}|$|{title}|$|{pic}|$|{views}人观看|$|{play_url}",
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": f"{views}人观看"
            })
        return {
            "list": items,
            "page": 1,
            "pagecount": 99,
            "limit": 20,
            "total": len(items)
        }

    # ========== m3u8 清洗 ==========
    def _m3u8_proxy_url(self, url):
        # 先归一化URL（替换反斜杠转义）
        url = str(url or "").replace("\\/", "/")
        return "http://127.0.0.1:9978/proxy?do=py&url=" + urllib.parse.quote(url, safe="")

    def _is_fake_image_stream(self, text):
        has_video = False
        has_image = False
        for line in str(text or "").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            path = line.split("?")[0].split("#")[0].lower()
            if path.endswith((".ts", ".m4s", ".mp4")):
                has_video = True
            elif path.endswith((".jpg", ".jpeg", ".png", ".webp")):
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
                key_uri if key_uri.startswith("http") else urllib.parse.urljoin(source_url, key_uri)
            ).path
            key_dir = posixpath.dirname(key_path)
            if key_dir and key_dir != "/":
                return key_dir + "/"
        return base_dir

    def _rewrite_tag(self, line, source_url):
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(m):
                uri = m.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urllib.parse.urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)
        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urllib.parse.urljoin(source_url, line)
        return line

    def _clean_m3u8(self, text, source_url):
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"
        
        is_img = self._is_fake_image_stream(text)
        if is_img:
            self.log({"clean": "fake_image_stream", "action": "keep_suffix"})
        
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
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
        
        main_dir = self._resolve_main_dir(lines, source_url, is_image_stream=is_img)
        
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
        
        if removed > 0 and (kept == 0 or removed > kept):
            self.log({"clean": "fallback_no_filter", "removed": removed, "kept": kept, "anchor": main_dir})
            out = [self._rewrite_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"
        
        if removed:
            self.log({"clean": "filtered", "removed": removed, "kept": kept, "anchor": main_dir})
        
        noise = ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE")
        out = []
        for line in segments:
            line = self._rewrite_tag(line, source_url)
            if line in noise:
                if not out or out[-1] in noise:
                    continue
            out.append(line)
        while len(out) > 1 and out[-1] in noise:
            out.pop()
        
        return "\n".join(out) + "\n"

    def localProxy(self, param):
        try:
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")
            
            # 多种方式提取URL
            if target.startswith("url="):
                target = target[4:]
            elif "url=" in target:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(target).query)
                target = qs.get("url", [""])[0]
            
            # 解码并归一化（替换反斜杠转义）
            target = urllib.parse.unquote(str(target or ""))
            target = target.replace("\\/", "/")
            
            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url: " + str(target).encode()]
            
            resp = self.fetch(target, headers=self.headers, timeout=20, verify=self.verify_ssl)
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
            import traceback
            err = traceback.format_exc()
            return [500, "text/plain", f"localProxy error: {e}\n{err}".encode("utf-8", errors="ignore")]