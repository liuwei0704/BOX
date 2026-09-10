# coding: utf-8
"""
站点: 4k网av
域名: e_pe_p.4kwanavs4k.sbs
类型: MacCMS 影视站（成人内容）
特点: 图片流伪装 m3u8（分片后缀 .jpg）
验证时间: 2026-09-06
"""
import json
import re
import urllib.parse
import html as html_parser
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://e_pe_p.4kwanavs4k.sbs"
        self.site_name = "4k网av"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        # 分类硬编码（从首页提取）
        self.classes = [
            {"type_id": "5", "type_name": "麻豆视频"},
            {"type_id": "6", "type_name": "变态重口"},
            {"type_id": "7", "type_name": "海外明星"},
            {"type_id": "8", "type_name": "素人"},
            {"type_id": "9", "type_name": "学生系列"},
            {"type_id": "10", "type_name": "偷拍自拍"},
            {"type_id": "11", "type_name": "极品少妇"},
            {"type_id": "12", "type_name": "网红黑料"},
            {"type_id": "22", "type_name": "国产裸聊"},
            {"type_id": "23", "type_name": "国产自拍"},
            {"type_id": "24", "type_name": "国产盗摄"},
            {"type_id": "25", "type_name": "伦理三级"},
            {"type_id": "26", "type_name": "女同性恋"},
            {"type_id": "27", "type_name": "少女萝莉"},
            {"type_id": "28", "type_name": "人妖系列"},
            {"type_id": "29", "type_name": "熟女人妻"},
            {"type_id": "30", "type_name": "制服丝袜"},
            {"type_id": "31", "type_name": "强奸乱伦"},
            {"type_id": "32", "type_name": "无码专区"},
            {"type_id": "33", "type_name": "有码视频"},
            {"type_id": "34", "type_name": "卡漫画"},
            {"type_id": "35", "type_name": "中文字幕"},
            {"type_id": "36", "type_name": "AV解说"},
            {"type_id": "37", "type_name": "巨乳美乳"},
        ]
        self.filters = {}
        self.NEED_CLEAN = True  # 图片流伪装站需要走代理
        self._fetch_kwargs = {"verify": False}  # 禁用 SSL 验证

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
        """首页推荐 - 从首页抓取视频列表"""
        try:
            url = self.host + "/"
            resp = self.fetch(url, headers=self.headers, timeout=15, verify=False)
            if not resp or resp.status_code != 200:
                return {"list": []}
            html = resp.text
            videos = []
            items = re.findall(r'<div class="col-md-3 portfolio-item new-video">(.*?)</div>\s*</div>', html, re.S)
            for item in items[:20]:
                title_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*title="([^"]*)"', item)
                if not title_match:
                    continue
                link = title_match.group(1)
                title = html_parser.unescape(title_match.group(2) or "未知标题")
                pic_match = re.search(r'data-original="([^"]+)"', item)
                pic = pic_match.group(1) if pic_match else ""
                remark_match = re.search(r'<div class="uptime">(.*?)</div>', item, re.S)
                remark = html_parser.unescape(remark_match.group(1).strip()) if remark_match else ""
                videos.append({
                    "vod_id": str(link),
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
            return {"list": videos}
        except Exception as e:
            self.log({"homeVideoContent": "error", "error": str(e)})
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        """分类列表 - 支持分页"""
        try:
            # TVBox 传入的 tid 可能是索引（int）也可能是 type_id（str）
            if isinstance(tid, int) and 0 <= tid < len(self.classes):
                type_id = self.classes[tid]["type_id"]
            else:
                type_id = str(tid)
                valid_ids = [c["type_id"] for c in self.classes]
                if type_id not in valid_ids:
                    try:
                        idx = int(tid)
                        if 0 <= idx < len(self.classes):
                            type_id = self.classes[idx]["type_id"]
                        else:
                            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}
                    except:
                        return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

            page = pg or 1
            if page == 1:
                url = f"{self.host}/index.php/vod/type/id/{type_id}.html"
            else:
                url = f"{self.host}/index.php/vod/type/id/{type_id}/page/{page}.html"
            resp = self.fetch(url, headers=self.headers, timeout=15, verify=False)
            if not resp or resp.status_code != 200:
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}
            html = resp.text
            videos = []
            items = re.findall(r'<div class="col-md-3 portfolio-item new-video">(.*?)</div>\s*</div>', html, re.S)
            for item in items:
                title_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*title="([^"]*)"', item)
                if not title_match:
                    continue
                link = title_match.group(1)
                title = html_parser.unescape(title_match.group(2) or "未知标题")
                pic_match = re.search(r'data-original="([^"]+)"', item)
                pic = pic_match.group(1) if pic_match else ""
                remark_match = re.search(r'<div class="uptime">(.*?)</div>', item, re.S)
                remark = html_parser.unescape(remark_match.group(1).strip()) if remark_match else ""
                videos.append({
                    "vod_id": str(link),
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
            pagecount = 1
            total_match = re.search(r'共(\d+)页', html)
            if total_match:
                pagecount = int(total_match.group(1))
            else:
                page_links = re.findall(r'<a[^>]+href="[^"]*page/(\d+)\.html[^"]*"[^>]*>(\d+)</a>', html)
                if page_links:
                    max_page = max(int(p[1]) for p in page_links)
                    pagecount = max(pagecount, max_page)
            return {
                "list": videos,
                "page": int(page),
                "pagecount": pagecount,
                "limit": 20,
                "total": pagecount * 20
            }
        except Exception as e:
            self.log({"categoryContent": "error", "tid": tid, "pg": pg, "error": str(e)})
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

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

        if vid.startswith("http"):
            detail_url = vid
        else:
            id_match = re.search(r'id/(\d+)', vid)
            if id_match:
                vid_num = id_match.group(1)
                detail_url = f"{self.host}/index.php/vod/detail/id/{vid_num}.html"
            else:
                detail_url = f"{self.host}/index.php/vod/detail/id/{vid}.html"

        try:
            resp = self.fetch(detail_url, headers=self.headers, timeout=15, verify=False)
            if not resp or resp.status_code != 200 or len(resp.text) < 500:
                return self._skeleton(vid)
            html = resp.text

            title_match = re.search(r'<title>(.*?)(?:_|</title>)', html)
            title = html_parser.unescape(title_match.group(1).strip()) if title_match else ""

            pic_match = re.search(r'data-original="([^"]+)"', html)
            pic = pic_match.group(1) if pic_match else ""

            play_links = []
            for m in re.finditer(r'<a[^>]+href="([^"]*index\.php/vod/play/[^"]+)"[^>]*class="[^"]*btn-danger[^"]*"[^>]*>.*?</a>', html, re.S):
                link = m.group(1)
                if link and "/play/" in link and link not in play_links:
                    play_links.append(link)

            if not play_links:
                for m in re.finditer(r'href="([^"]*index\.php/vod/play/[^"]+)"', html):
                    link = m.group(1)
                    if link and link not in play_links:
                        play_links.append(link)

            if not play_links:
                player_match = re.search(r'var player_aaaa=(\{[^}]+})', html)
                if player_match:
                    try:
                        data_str = player_match.group(1).replace("\\/", "/")
                        data = json.loads(data_str)
                        play_url = data.get("link", "")
                        if play_url:
                            play_links.append(play_url)
                    except Exception:
                        pass

            if play_links:
                play_from = "播放"
                play_url_parts = []
                for i, link in enumerate(play_links[:10]):
                    ep_num = i + 1
                    play_url_parts.append(f"第{ep_num}集${link}")
                play_url_str = "#".join(play_url_parts)

                return {"list": [{
                    "vod_id": vid,
                    "vod_name": title or "未知标题",
                    "vod_pic": pic or "",
                    "vod_remarks": "",
                    "vod_content": "",
                    "vod_play_from": play_from,
                    "vod_play_url": play_url_str
                }]}

            return self._skeleton(vid, title, pic)

        except Exception as e:
            self.log({"detailContent": "error", "vid": vid, "error": str(e)})
            return self._skeleton(vid)

    def searchContent(self, key, quick, pg="1"):
        try:
            url = f"{self.host}/index.php/vod/search.html?wd={urllib.parse.quote(key)}"
            resp = self.fetch(url, headers=self.headers, timeout=15, verify=False)
            if not resp or resp.status_code != 200:
                return {"list": []}
            html = resp.text
            videos = []
            items = re.findall(r'<div class="col-md-3 portfolio-item new-video">(.*?)</div>\s*</div>', html, re.S)
            for item in items:
                title_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*title="([^"]*)"', item)
                if not title_match:
                    continue
                link = title_match.group(1)
                title = html_parser.unescape(title_match.group(2) or "未知标题")
                pic_match = re.search(r'data-original="([^"]+)"', item)
                pic = pic_match.group(1) if pic_match else ""
                videos.append({
                    "vod_id": str(link),
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": ""
                })
            return {"list": videos, "page": int(pg)}
        except Exception as e:
            self.log({"searchContent": "error", "key": key, "error": str(e)})
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        ua = self.headers.get("User-Agent", "")
        if not id:
            return {"parse": 1, "url": "", "header": {"User-Agent": ua}}

        if id.startswith("http"):
            play_page_url = id
        else:
            if "index.php/vod/play" in id:
                play_page_url = self.host + id if id.startswith("/") else id
            else:
                play_page_url = self.host + "/index.php/vod/play/id/" + str(id).split("/")[-1] + "/sid/1/nid/1.html"

        try:
            resp = self.fetch(play_page_url, headers=self.headers, timeout=15, verify=False)
            if not resp or resp.status_code != 200:
                return {"parse": 1, "url": play_page_url, "header": self.headers}

            html = resp.text

            player_match = re.search(r'var player_aaaa=(\{[^}]+})', html)
            if player_match:
                try:
                    data_str = player_match.group(1).replace("\\/", "/")
                    data = json.loads(data_str)
                    play_url = data.get("url", "")
                    if play_url and play_url.startswith("http"):
                        if self.NEED_CLEAN and ".m3u8" in play_url.lower():
                            return {"parse": 0, "url": self._m3u8_proxy_url(play_url), "header": {"User-Agent": ua}}
                        return {"parse": 0, "url": play_url, "header": {"User-Agent": ua}}
                except Exception as e:
                    self.log({"playerContent": "json_error", "error": str(e)})

            m3u8_matches = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
            if m3u8_matches:
                play_url = m3u8_matches[0]
                if self.NEED_CLEAN:
                    return {"parse": 0, "url": self._m3u8_proxy_url(play_url), "header": {"User-Agent": ua}}
                return {"parse": 0, "url": play_url, "header": {"User-Agent": ua}}

            return {"parse": 1, "url": play_page_url, "header": self.headers}

        except Exception as e:
            self.log({"playerContent": "error", "id": id, "error": str(e)})
            return {"parse": 1, "url": play_page_url if 'play_page_url' in locals() else id, "header": self.headers}

    def _m3u8_proxy_url(self, url):
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
            if not target or not target.startswith("http"):
                return [400, "text/plain", b"invalid url"]

            resp = self.fetch(target, headers=self.headers, timeout=20, verify=False)
            if not resp:
                return [502, "text/plain", b"fetch failed"]
            content = getattr(resp, "content", b"") or b""
            if not content and getattr(resp, "text", ""):
                content = resp.text.encode("utf-8", errors="ignore")
            if not content:
                return [502, "text/plain", b"empty content"]

            if b"#EXTM3U" not in content[:512]:
                return [200, "application/octet-stream", content]

            text = content.decode("utf-8", errors="ignore")
            cleaned = self._clean_m3u8(text, target)
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

        except Exception as e:
            self.log({"localProxy": "error", "error": str(e)})
            return [500, "text/plain", f"localProxy error: {e}".encode("utf-8", errors="ignore")]

    def _clean_m3u8(self, text, source_url):
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        is_img = self._is_fake_image_stream(text, source_url)
        if is_img:
            self.log({"stage": "clean", "fake_image_stream": True, "action": "keep_suffix_as_is"})

        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urllib.parse.urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"

        main_dir = self._resolve_main_dir(lines, source_url, is_image_stream=is_img)
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)

        if removed > 0 and (kept == 0 or removed > kept):
            self.log({"stage": "clean", "fallback": "no_filter", "removed": removed, "kept": kept})
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
            if not key_uri.startswith("http"):
                key_uri = urllib.parse.urljoin(source_url, key_uri)
            key_dir = posixpath.dirname(urllib.parse.urlparse(key_uri).path)
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
        PROTECTED = ("#EXT-X-KEY", "#EXT-X-MAP", "#EXT-X-SESSION-KEY")
        if line.startswith(PROTECTED):
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

    def recommendContent(self, ids, pg):
        return {"list": []}

    def destroy(self):
        pass