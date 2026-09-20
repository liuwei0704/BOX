# coding: utf-8
import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://www.estek.sbs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "1", "type_name": "视频一区"},
            {"type_id": "2", "type_name": "视频二区"},
            {"type_id": "3", "type_name": "视频三区"}
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}
        self.NEED_CLEAN = True
        self.timeout = 15

    def getName(self):
        return "78草小妹"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def destroy(self):
        pass

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            r = self.fetch(f"{self.host}/vod/type/id/1.html", headers=self.headers, timeout=self.timeout)
            if not r or r.status_code != 200:
                return {"list": []}
            items = self._parse_list(r.text, f"{self.host}/vod/type/id/1.html")
            return {"list": items[:20]}
        except Exception:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/vod/type/id/{tid}/page/{page}.html"
        try:
            r = self.fetch(url, headers=self.headers, timeout=self.timeout)
            if not r or r.status_code != 200:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            items = self._parse_list(r.text, url)
            total_pages = self._parse_total_pages(r.text)
            return {
                "list": items,
                "page": int(page),
                "pagecount": total_pages,
                "limit": 20,
                "total": len(items)
            }
        except Exception:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

    def _parse_total_pages(self, html):
        # 尝试匹配 "共 N 页" 格式
        m = re.search(r'共\s*(\d+)\s*页', html)
        if m:
            return int(m.group(1))
        # 尝试匹配分页链接中的最后一个页码
        matches = re.findall(r'<a[^>]+href="[^"]*page/(\d+)"[^>]*>', html)
        if matches:
            nums = [int(x) for x in matches if x.isdigit()]
            if nums:
                return max(nums)
        # 尝试匹配 "1/N" 格式（如 1/80339）
        m = re.search(r'(\d+)\s*/\s*(\d+)', html)
        if m:
            return int(m.group(2))
        return 1
    def _parse_list(self, html, page_url):
        items = []
        pattern = r'<li[^>]*class="[^"]*fed-list-item[^"]*"[^>]*>.*?<a[^>]*class="[^"]*fed-list-pics[^"]*"[^>]*href="([^"]+)"[^>]*data-original="([^"]+)"[^>]*>.*?</a>.*?<a[^>]*class="[^"]*fed-list-title[^"]*"[^>]*href="[^"]*"[^>]*>([^<]+)</a>'
        for m in re.finditer(pattern, html, re.S):
            link, pic, name = m.groups()
            vid = link.strip("/").split("/")[-1].replace(".html", "")
            if vid:
                items.append({
                    "vod_id": vid,
                    "vod_name": name.strip(),
                    "vod_pic": pic.strip() if pic.startswith("http") else "https:" + pic.strip() if pic.startswith("//") else pic.strip(),
                    "vod_remarks": ""
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

    def _skeleton(self, vid, title="", pic=""):
        pid = str(vid).split("|$|")[0].replace("$", "|")
        return {"list": [{
            "vod_id": vid,
            "vod_name": title or "未知标题",
            "vod_pic": pic or "",
            "vod_remarks": "解析中",
            "vod_content": "",
            "vod_play_from": "播放",
            "vod_play_url": f"播放${pid}"
        }]}

    def detailContent(self, ids):
        vid = self._norm_ids(ids)
        if not vid:
            return {"list": []}

        title = ""
        pic = ""
        try:
            url = f"{self.host}/vod/detail/id/{vid}.html"
            r = self.fetch(url, headers=self.headers, timeout=self.timeout)
            if r and r.status_code == 200 and len(r.text) > 500:
                html = r.text
                # 标题：取 fed-detail-text 容器内全部文本
                m = re.search(r'<h3[^>]*class="[^"]*fed-detail-text[^"]*"[^>]*>(.*?)</h3>', html, re.S)
                if m:
                    title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if not title:
                    m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html)
                    if m:
                        title = m.group(1).strip()
                        title = re.sub(r'\s*[-|_–]\s*[^-|_–]{2,20}$', '', title)
                if not title:
                    m = re.search(r'<title>([^<]+)</title>', html)
                    if m:
                        title = m.group(1).strip()
                        title = re.sub(r'\s*[-|_–]\s*[^-|_–]{2,20}$', '', title)
                # 封面
                m = re.search(r'<a[^>]*class="[^"]*fed-list-pics[^"]*"[^>]*data-original="([^"]+)"', html)
                if m:
                    pic = m.group(1)
                    if not pic.startswith("http"):
                        pic = urllib.parse.urljoin(self.host, pic)
        except Exception:
            pass

        play_url = f"{self.host}/vod/play/id/{vid}/sid/1/nid/1.html"
        vod = {
            "vod_id": vid,
            "vod_name": title or "未知标题",
            "vod_pic": pic or "",
            "vod_remarks": "",
            "vod_content": "",
            "vod_play_from": "播放",
            "vod_play_url": f"播放${play_url}"
        }
        return {"list": [vod]}
    def _extract_play_from_detail(self, html):
        m = re.search(r'var\s+player_aaaa\s*=\s*(\{[^}]*\})', html)
        if m:
            try:
                data = json.loads(m.group(1))
                url = data.get("url", "")
                if url:
                    return urllib.parse.unquote(url)
            except Exception:
                pass
        m = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
        if m:
            return m.group(1)
        return ""

    def searchContent(self, key, quick, pg="1"):
        try:
            url = f"{self.host}/vod/search.html?wd={urllib.parse.quote(key)}"
            r = self.fetch(url, headers=self.headers, timeout=self.timeout)
            if not r or r.status_code != 200:
                return {"list": [], "page": int(pg)}
            items = self._parse_search_list(r.text)
            return {"list": items, "page": int(pg)}
        except Exception:
            return {"list": [], "page": int(pg)}

    def _parse_search_list(self, html):
        items = []
        # 搜索页使用 fed-list-vods，结构：dl.fed-list-vods > dt > a 取封面，dd > h3 > a 取标题和链接
        pattern = r'<dl[^>]*class="[^"]*fed-list-vods[^"]*"[^>]*>.*?<a[^>]*class="[^"]*fed-list-pics[^"]*"[^>]*href="([^"]+)"[^>]*data-original="([^"]+)"[^>]*>.*?</a>.*?<h3>.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        for m in re.finditer(pattern, html, re.S):
            play_link, pic, detail_link, name = m.groups()
            # 从 detail_link 或 play_link 提取 vod_id
            vid = detail_link.strip("/").split("/")[-1].replace(".html", "")
            if not vid:
                vid = play_link.strip("/").split("/")[-1].replace(".html", "")
            if vid:
                items.append({
                    "vod_id": vid,
                    "vod_name": name.strip(),
                    "vod_pic": pic.strip() if pic.startswith("http") else "https:" + pic.strip() if pic.startswith("//") else pic.strip(),
                    "vod_remarks": ""
                })
        # 如果正则没匹配到，尝试更宽松的方式
        if not items:
            pattern2 = r'<dl[^>]*class="[^"]*fed-list-vods[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>.*?<img[^>]+data-original="([^"]+)"[^>]*>.*?<h3>.*?<a[^>]+>([^<]+)</a>'
            for m in re.finditer(pattern2, html, re.S):
                link, pic, name = m.groups()
                vid = link.strip("/").split("/")[-1].replace(".html", "")
                if vid:
                    items.append({
                        "vod_id": vid,
                        "vod_name": name.strip(),
                        "vod_pic": pic.strip() if pic.startswith("http") else "https:" + pic.strip() if pic.startswith("//") else pic.strip(),
                        "vod_remarks": ""
                    })
        return items
    def playerContent(self, flag, id, vipFlags):
        play_url = str(id or "").strip()
        ua = self.headers.get("User-Agent", "")

        if not play_url:
            return {"parse": 0, "url": "", "header": {"User-Agent": ua}}

        # 如果是 "名称$地址" 格式，提取地址
        if "$" in play_url:
            parts = play_url.split("$", 1)
            if len(parts) == 2:
                play_url = parts[1]

        # 补协议
        if play_url and not play_url.startswith("http"):
            if not play_url.startswith("//"):
                play_url = "https://" + play_url
            else:
                play_url = "https:" + play_url

        if not play_url.startswith("http"):
            return {"parse": 0, "url": "", "header": {"User-Agent": ua}}

        # 判断是否是 m3u8 直链
        if ".m3u8" in play_url.lower():
            if self.NEED_CLEAN:
                return {"parse": 0, "url": self._m3u8_proxy_url(play_url), "header": {"User-Agent": ua}}
            return {"parse": 0, "url": play_url, "header": {"User-Agent": ua}}

        if ".mp4" in play_url.lower():
            return {"parse": 0, "url": play_url, "header": {"User-Agent": ua}}

        # 否则请求播放页提取 m3u8
        try:
            r = self.fetch(play_url, headers=self.headers, timeout=self.timeout)
            if not r or r.status_code != 200:
                return {"parse": 1, "url": play_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

            html = r.text
            # 提取 player_aaaa 中的 url
            m = re.search(r'var\s+player_aaaa\s*=\s*(\{[^}]*\})', html, re.S)
            if m:
                try:
                    data = json.loads(m.group(1))
                    url = data.get("url", "")
                    if url:
                        # 还原 JSON 转义的反斜杠
                        url = url.replace("\\/", "/")
                        # 再 unquote
                        url = urllib.parse.unquote(url)
                        if ".m3u8" in url.lower():
                            if self.NEED_CLEAN:
                                return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}
                            return {"parse": 0, "url": url, "header": {"User-Agent": ua}}
                        return {"parse": 0, "url": url, "header": {"User-Agent": ua}}
                except Exception:
                    pass

            # 正则兜底
            m = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
            if m:
                url = m.group(1).replace("\\/", "/")
                url = urllib.parse.unquote(url)
                if self.NEED_CLEAN:
                    return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}
                return {"parse": 0, "url": url, "header": {"User-Agent": ua}}

        except Exception:
            pass

        return {"parse": 1, "url": play_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}
    def _m3u8_proxy_url(self, url):
        return f"http://127.0.0.1:9978/proxy?do=py&url={urllib.parse.quote(str(url or ''), safe='')}"

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

        # 取 KEY URI 目录作锚点
        main_dir = self._resolve_main_dir(lines, source_url)

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
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        out = []
        noise = ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE")
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in noise:
                if not out or out[-1] in noise:
                    continue
            out.append(line)
        while len(out) > 1 and out[-1] in noise:
            out.pop()
        return "\n".join(out) + "\n"

    def _resolve_main_dir(self, lines, source_url):
        import posixpath
        from collections import Counter

        # 收集所有分片路径的目录
        dir_counter = Counter()
        for line in lines:
            if not line or line.startswith("#"):
                continue
            media_url = urllib.parse.urljoin(source_url, line)
            path = urllib.parse.urlparse(media_url).path
            d = posixpath.dirname(path)
            if d and d != "/":
                dir_counter[d + "/"] += 1

        # 如果分片目录众数存在且占比显著，使用它作为锚点
        if dir_counter:
            most_common_dir, most_common_count = dir_counter.most_common(1)[0]
            total_segments = sum(dir_counter.values())
            # 如果众数占比 > 50%，说明这是正片目录
            if most_common_count > total_segments * 0.5:
                return most_common_dir

        # 否则尝试 KEY URI 目录
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
            if not key_uri.startswith("http"):
                key_uri = urllib.parse.urljoin(source_url, key_uri)
            key_path = urllib.parse.urlparse(key_uri).path
            key_dir = posixpath.dirname(key_path)
            if key_dir and key_dir != "/":
                return key_dir + "/"

        # 如果 KEY 目录没有命中，且分片众数存在但占比不够，使用众数（宁可多保留）
        if dir_counter:
            return most_common_dir

        return base_dir
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
        # 根据视频 ID 获取分类，然后从该分类取推荐
        vid = self._norm_ids(ids)
        if not vid:
            return {"list": []}

        tid = "1"
        try:
            url = f"{self.host}/vod/detail/id/{vid}.html"
            r = self.fetch(url, headers=self.headers, timeout=self.timeout)
            if r and r.status_code == 200 and len(r.text) > 500:
                html = r.text
                # 提取分类 ID
                m = re.search(r'<a[^>]+href="/vod/type/id/(\d+)"[^>]*>', html)
                if m:
                    tid = m.group(1)
        except Exception:
            pass

        # 从该分类取推荐列表
        try:
            url = f"{self.host}/vod/type/id/{tid}/page/1.html"
            r = self.fetch(url, headers=self.headers, timeout=self.timeout)
            if not r or r.status_code != 200:
                return {"list": []}
            items = self._parse_list(r.text, url)
            # 排除当前视频
            items = [it for it in items if it.get("vod_id") != vid]
            return {"list": items[:12]}
        except Exception:
            return {"list": []}
