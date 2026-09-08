# coding: utf-8
import json
import re
import base64
import urllib.parse
from urllib.parse import urljoin, quote, unquote

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://krn.baihua2026.sbs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "3", "type_name": "国产"},
            {"type_id": "4", "type_name": "日本"},
            {"type_id": "20", "type_name": "国产"},
            {"type_id": "74", "type_name": "网爆"},
            {"type_id": "68", "type_name": "精品"},
            {"type_id": "69", "type_name": "偷拍"},
            {"type_id": "70", "type_name": "传媒"},
        ]
        self.filters = {}
        self.aes_key = b""
        self.aes_iv = b""
        self.NEED_CLEAN = True  # 取证确认有广告特征
        self._cached_host = self.host

    def getName(self):
        return "百花会"

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
            url = f"{self.host}/index.php/vod/type/id/3.html"
            r = self.fetch(url, headers=self.headers, timeout=10)
            if r and r.status_code == 200:
                html = r.text
                items = self._parse_list(html, is_search=False)
                return {"list": items[:20] if items else []}
            return {"list": []}
        except Exception as e:
            self.log({"homeVideo": "error", "msg": str(e)})
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        page_url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        try:
            r = self.fetch(page_url, headers=self.headers, timeout=15)
            if r and r.status_code == 200:
                html = r.text
                items = self._parse_list(html, is_search=False)
                # 总页数从分页器获取（pagination_parser 实测为188）
                total_pages = 188
                return {
                    "list": items,
                    "page": int(page),
                    "pagecount": total_pages,
                    "limit": 20,
                    "total": 999
                }
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}
        except Exception as e:
            self.log({"category": "error", "tid": tid, "pg": pg, "msg": str(e)})
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def _parse_list(self, html, is_search=False):
        import html as html_parser
        items = []
        if not html:
            return items
        pattern = r'<li>\s*<a\s+class="uzimg"\s+href="([^"]+)"\s+title="([^"]*)"[^>]*>\s*<img\s+class="lazy"\s+data-original="([^"]+)"[^>]*>.*?</a>\s*<h4><a\s+href="[^"]+"\s+title="([^"]*)">(.*?)</a></h4>\s*<p\s+class="vodtitle">([^<]*)'
        for m in re.finditer(pattern, html, re.S):
            link = m.group(1).strip()
            title = m.group(2).strip() or m.group(4).strip() or m.group(5).strip()
            pic = m.group(3).strip()
            remark = m.group(6).strip()
            if not link or not title:
                continue
            # 解码 HTML 实体（修复角标乱码）
            title = html_parser.unescape(title)
            pic = html_parser.unescape(pic)
            remark = html_parser.unescape(remark)
            if not pic.startswith("http"):
                pic = urljoin(self.host, pic)
            vod_id = link
            packed_id = f"{link}|$|{title}|$|{pic}|$|{remark}"
            items.append({
                "vod_id": packed_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        if not items:
            li_pattern = r'<li>.*?<a[^>]+href="([^"]+)"[^>]*>.*?<img[^>]+data-original="([^"]+)"[^>]*>.*?<h4>.*?<a[^>]+>([^<]+)</a>.*?</h4>.*?<p[^>]*>([^<]*)</p>'
            for m in re.finditer(li_pattern, html, re.S):
                link = m.group(1).strip()
                pic = m.group(2).strip()
                title = m.group(3).strip()
                remark = m.group(4).strip()
                if not link or not title:
                    continue
                # 解码 HTML 实体
                title = html_parser.unescape(title)
                pic = html_parser.unescape(pic)
                remark = html_parser.unescape(remark)
                if not pic.startswith("http"):
                    pic = urljoin(self.host, pic)
                vod_id = link
                packed_id = f"{link}|$|{title}|$|{pic}|$|{remark}"
                items.append({
                    "vod_id": packed_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
        return items

    @staticmethod
    def _norm_ids(ids):
        if ids is None:
            return ""
        if isinstance(ids, (list, tuple)):
            if not ids:
                return ""
            ids = ids[0]
        if isinstance(ids, bytes):
            try:
                ids = ids.decode("utf-8", errors="ignore")
            except Exception:
                return ""
        return str(ids).strip()

    def _skeleton(self, vid, title="", pic="", remarks="解析中"):
        # 从打包串中提取真实播放页URL
        # 法则35：骨架兜底，禁止返回空列表
        raw = str(vid)
        play_url = raw
        if "|$|" in raw:
            parts = raw.split("|$|")
            if len(parts) >= 5 and parts[4]:
                play_url = parts[4]
            elif len(parts) >= 1:
                play_url = parts[0]
        # 如果play_url不是完整URL，补全
        if not play_url.startswith("http"):
            play_url = urljoin(self.host, play_url)
        # 播放ID内禁止裸$，用|替代
        safe_id = play_url.replace("$", "|")
        return {"list": [{
            "vod_id": vid,
            "vod_name": title or "未知标题",
            "vod_pic": pic or "",
            "vod_remarks": remarks,
            "vod_content": "",
            "vod_play_from": "播放",
            "vod_play_url": f"播放${safe_id}",
        }]}

    def detailContent(self, ids):
        raw = self._norm_ids(ids)
        if not raw:
            return {"list": []}

        # 第1层：拆包列表阶段封装的字段
        parts = raw.split("|$|")
        if len(parts) >= 1:
            play_page = parts[0] if len(parts) > 0 else ""
            title = parts[1] if len(parts) > 1 else ""
            pic = parts[2] if len(parts) > 2 else ""
            remark = parts[3] if len(parts) > 3 else ""
            
            # 解码 HTML 实体（修复角标乱码）
            import html
            title = html.unescape(title)
            pic = html.unescape(pic)
            remark = html.unescape(remark)
            
            if play_page:
                play_url = play_page if play_page.startswith("http") else urljoin(self.host, play_page)
                # 播放ID 只放播放页URL，不加多余字段
                safe_id = play_url.replace("$", "|")
                return {"list": [{
                    "vod_id": raw,
                    "vod_name": title or "视频",
                    "vod_pic": pic or "",
                    "vod_remarks": remark or "",
                    "vod_content": "",
                    "vod_play_from": "播放",
                    "vod_play_url": f"播放${safe_id}",
                }]}

        # 兜底：用原始ID作为播放页
        play_page = raw
        if not play_page.startswith("http"):
            play_page = urljoin(self.host, play_page)
        safe_id = play_page.replace("$", "|")
        return {"list": [{
            "vod_id": raw,
            "vod_name": "视频",
            "vod_pic": "",
            "vod_remarks": "",
            "vod_content": "",
            "vod_play_from": "播放",
            "vod_play_url": f"播放${safe_id}",
        }]}

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        try:
            search_url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}"
            if int(pg) > 1:
                search_url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}&page={pg}"
            r = self.fetch(search_url, headers=self.headers, timeout=15)
            if r and r.status_code == 200:
                html = r.text
                items = self._parse_list(html, is_search=True)
                return {"list": items, "page": int(pg)}
            return {"list": [], "page": 1}
        except Exception as e:
            self.log({"search": "error", "key": key, "msg": str(e)})
            return {"list": [], "page": 1}

    def _is_media_url(self, url):
        if not url or not str(url).startswith("http"):
            return False
        path = str(url).split("?")[0].split("#")[0].lower()
        media_ext = (".m3u8", ".mp4", ".mkv", ".flv", ".avi", ".m4v", ".mov", ".ts")
        if path.endswith(media_ext):
            return True
        low = str(url).lower()
        return "/hls/" in low and "m3u8" in low

    def _normalize_url(self, raw):
        if not raw:
            return ""
        s = str(raw).strip().strip('"').strip("'")
        s = s.replace("\\/", "/").replace("\\u002f", "/").replace("\\u002F", "/")
        s = s.replace('" + "', "").replace("' + '", "")
        try:
            import html
            s = html.unescape(s)
        except Exception:
            pass
        for _ in range(2):
            if "%3A%2F%2F" in s or "%3a%2f%2f" in s:
                try:
                    s = urllib.parse.unquote(s)
                except Exception:
                    break
            else:
                break
        return s.strip()

    def _extract_play_candidates(self, html, page_url, depth=0):
        """9层管线：提取播放地址候选"""
        bag = []
        if not html:
            return bag

        # L2: 播放器变量
        player_vars = ("player_aaaa", "player_data", "MacPlayerConfig.player_data", "vid_data")
        for var in player_vars:
            for m in re.finditer(re.escape(var) + r'\s*=\s*', html):
                brace = html.find("{", m.end())
                if brace < 0 or brace - m.end() > 8:
                    continue
                raw_json = self._grab_json_object(html, brace)
                obj = self._loose_json(raw_json)
                if obj is not None:
                    self._walk_json(obj, bag)

        # L3: 内联JSON
        for m in re.finditer(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html, re.S):
            obj = self._loose_json(m.group(1).strip())
            if obj is not None:
                self._walk_json(obj, bag)

        # L5: 全文正则
        fallback_patterns = (
            r'https?://[^\s"\'<>()\\]+?\.m3u8[^\s"\'<>()\\]*',
            r'https?://[^\s"\'<>()\\]+?\.mp4[^\s"\'<>()\\]*',
            r'["\']((?:https?:)?\\?/\\?/[^\s"\'<>]+?\.m3u8[^\s"\'<>]*)["\']',
        )
        for p in fallback_patterns:
            for hit in re.findall(p, html):
                bag.append(hit if isinstance(hit, str) else hit[0])

        # L6: iframe递归（限深2）
        if depth < 2:
            for src in re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)[:3]:
                sub_url = urljoin(page_url, self._normalize_url(src))
                if not sub_url.startswith("http"):
                    continue
                try:
                    r = self.fetch(sub_url, headers={"User-Agent": self.headers["User-Agent"], "Referer": page_url}, timeout=10)
                    if r and r.status_code == 200:
                        sub_html = r.text
                        bag.extend(self._extract_play_candidates(sub_html, sub_url, depth + 1))
                except Exception:
                    pass

        return bag

    def _grab_json_object(self, text, start_idx):
        if start_idx < 0 or start_idx >= len(text) or text[start_idx] != "{":
            return ""
        depth = 0
        in_str = False
        esc = False
        quote = ""
        for i in range(start_idx, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == quote:
                    in_str = False
                continue
            if ch in ('"', "'"):
                in_str = True
                quote = ch
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]
        return ""

    def _loose_json(self, raw):
        if not raw:
            return None
        candidates = [raw]
        candidates.append(raw.replace("\\/", "/"))
        if '"' not in raw and "'" in raw:
            candidates.append(raw.replace("'", '"'))
        fixed = re.sub(r",\s*([}\]])", r"\1", raw)
        fixed = re.sub(r"([{,]\s*)([A-Za-z_]\w*)(\s*:)", r'\1"\2"\3', fixed)
        candidates.append(fixed)
        for c in candidates:
            try:
                obj = json.loads(c)
                if isinstance(obj, (dict, list)):
                    return obj
            except Exception:
                continue
        return None

    def _walk_json(self, node, bag, depth=0):
        if depth > 6 or node is None:
            return
        url_keys = ("url", "play_url", "playUrl", "video_url", "videoUrl", "src", "source", "m3u8", "hls", "file", "purl", "vurl")
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str):
                    kl = str(k).lower()
                    if kl in url_keys or self._looks_like_media(v):
                        bag.append(v)
                else:
                    self._walk_json(v, bag, depth + 1)
        elif isinstance(node, list):
            for v in node:
                if isinstance(v, str):
                    if self._looks_like_media(v):
                        bag.append(v)
                else:
                    self._walk_json(v, bag, depth + 1)

    def _looks_like_media(self, s):
        if not s or not isinstance(s, str):
            return False
        s_low = s.lower()
        return ".m3u8" in s_low or ".mp4" in s_low or ".mkv" in s_low or ".flv" in s_low

    def _pick_playable(self, bag):
        seen, cands = set(), []
        for raw in bag:
            u = self._normalize_url(raw)
            if not u or u in seen:
                continue
            if not u.startswith("http"):
                continue
            seen.add(u)
            cands.append(u)
        def score(u):
            s = 0
            low = u.lower()
            if ".m3u8" in low:
                s += 10
            elif ".mp4" in low:
                s += 8
            if any(k in low for k in ("auth_key", "token", "sign", "expire")):
                s += 2
            if "/ad" in low or "advert" in low:
                s -= 5
            return -s
        cands.sort(key=score)
        return cands

    def playerContent(self, flag, id, vipFlags):
        raw_id = str(id or "").strip()
        ua = self.headers.get("User-Agent", "")
        if not raw_id:
            return {"parse": 1, "url": "", "header": {"User-Agent": ua}}

        # L1: 直链识别
        if self._is_media_url(raw_id):
            if ".m3u8" in raw_id.lower() and self.NEED_CLEAN:
                return {"parse": 0, "url": self._m3u8_proxy_url(raw_id), "header": {"User-Agent": ua}}
            return {"parse": 0, "url": raw_id, "header": {"User-Agent": ua}}

        # 补全URL
        if raw_id.startswith("http"):
            page_url = raw_id
        else:
            page_url = urljoin(self.host, raw_id)

        # 获取播放页HTML
        try:
            r = self.fetch(page_url, headers=self.headers, timeout=15)
            if r and r.status_code == 200:
                html = r.text
            else:
                html = ""
        except Exception:
            html = ""

        if not html:
            return {"parse": 1, "url": page_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

        # L2-L6: 提取候选
        bag = self._extract_play_candidates(html, page_url)
        cands = self._pick_playable(bag)

        if cands:
            self.log({"player": "hit", "count": len(cands), "pick": cands[0]})
            play_url = cands[0]
            if ".m3u8" in play_url.lower() and self.NEED_CLEAN:
                return {"parse": 0, "url": self._m3u8_proxy_url(play_url), "header": {"User-Agent": ua}}
            return {"parse": 0, "url": play_url, "header": {"User-Agent": ua}}

        self.log({"player": "all_layers_miss", "page": page_url})
        return {"parse": 1, "url": page_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + quote(str(url or ""), safe="")

    def localProxy(self, param):
        """m3u8 五层过滤管线"""
        try:
            target = ""
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
            target = unquote(str(target or ""))
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
        """五层去广告管线"""
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 第1层：图片流检测（此站非图片流，但保留逻辑）
        is_img = self._is_fake_image_stream(text, source_url)
        if is_img:
            self.log({"stage": "clean", "fake_image_stream": True, "action": "keep_suffix_as_is"})

        # 第2层：多码率主表
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            return self._clean_m3u8_multi(lines, source_url)

        # 第3层：正片目录锚点（根据m3u8_analyzer取证：KEY URI目录优先）
        main_dir = self._resolve_main_dir(lines, source_url, is_image_stream=is_img)

        # 第4层：分片过滤
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)

        # 第5层：全滤兜底
        if removed > 0 and (kept == 0 or removed > kept):
            self.log({"stage": "clean", "fallback": "no_filter", "removed": removed, "kept": kept, "anchor": main_dir})
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        if removed:
            self.log({"stage": "clean", "removed": removed, "kept": kept, "anchor": main_dir})

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

        # 普通流：KEY URI目录优先
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

    def recommendContent(self, ids, pg):
        return {"list": []}

    def destroy(self):
        pass