# -*- coding: utf-8 -*-
import re
import json
from urllib.parse import urljoin, quote, unquote, urlparse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.extend = ""
        self.host = "https://hec.zxc9.motorcycles"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cookie": "ageVerified=true"
        }
        self.classes = [
            {"type_id": "1", "type_name": "国产自拍"},
            {"type_id": "20", "type_name": "制服丝袜"},
            {"type_id": "21", "type_name": "强奸乱伦"},
            {"type_id": "22", "type_name": "人妻熟女"},
            {"type_id": "23", "type_name": "主播自拍"},
            {"type_id": "24", "type_name": "日韩精品"},
            {"type_id": "25", "type_name": "欧美风情"},
            {"type_id": "26", "type_name": "卡通动漫"},
            {"type_id": "27", "type_name": "经典伦理"}
        ]
        self.filters = {}

    def getName(self):
        return "知秀场"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if resp and resp.status_code == 200:
                return resp.text
            return None
        except Exception as e:
            self.log({"action": "fetch_error", "url": url, "error": str(e)})
            return None

    def _extract_vod_id(self, url):
        m = re.search(r'/id/(\d+)', url)
        return m.group(1) if m else ""

    def _fix_url(self, url):
        if not url:
            return ""
        url = url.strip()
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.host + url
        return self.host + "/" + url.lstrip("/")

    def _parse_list_items(self, html):
        videos = []
        if not html:
            return videos
        pattern = r'<a\s+class="link-hover"\s+href="([^"]+)"\s+title="([^"]*)".*?<img[^>]*(?:data-original|src)="([^"]*)"[^>]*>.*?<p\s+class="name">([^<]*)</p>.*?<p\s+class="actor">([^<]*)</p>.*?<p\s+class="actor">([^<]*)</p>'
        for m in re.finditer(pattern, html, re.DOTALL):
            href = m.group(1)
            title = m.group(2) or m.group(4)
            pic = m.group(3)
            actor = m.group(5)
            vid = self._extract_vod_id(href)
            if vid and title:
                videos.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": self._fix_url(pic),
                    "vod_remarks": actor.strip() if actor else ""
                })
        return videos

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        url = self.host + "/cn/home/web/"
        html = self._fetch_html(url)
        videos = self._parse_list_items(html)
        return {"list": videos[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        url = f"{self.host}/cn/home/web/index.php/vod/type/id/{tid}/page/{page}.html"
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        videos = self._parse_list_items(html)

        total = 0
        pagecount = 1
        m = re.search(r'共(\d+)条数据', html)
        if m:
            total = int(m.group(1))
        m = re.search(r'当前(\d+)/(\d+)页', html)
        if m:
            page = int(m.group(1))
            pagecount = int(m.group(2))

        return {"list": videos, "page": page, "pagecount": pagecount, "limit": 20, "total": total}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0])
        url = f"{self.host}/cn/home/web/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        html = self._fetch_html(url)
        if not html:
            return {"list": []}

        title = ""
        m = re.search(r'<h1[^>]*class="title"[^>]*>([^<]*)</h1>', html)
        if m:
            title = m.group(1).strip()
        if not title:
            m = re.search(r'<title>([^<]*)</title>', html)
            if m:
                title = m.group(1).strip()
                title = re.sub(r'[-–—]\s*知秀场$', '', title).strip()

        pic = ""
        m = re.search(r'<img[^>]*class="lazy"[^>]*data-original="([^"]+)"', html)
        if m:
            pic = self._fix_url(m.group(1))

        play_from = "推荐线路"
        play_url_str = ""
        player_data = re.search(r'var player_data=({[^}]+})', html)
        if player_data:
            try:
                data = json.loads(player_data.group(1))
                url_raw = data.get("url", "")
                if url_raw:
                    play_url_str = f"播放${url_raw}"
                else:
                    play_url_str = f"播放${vid}"
            except:
                play_url_str = f"播放${vid}"
        else:
            play_url_str = f"播放${vid}"

        data = {
            "vod_id": vid,
            "vod_name": title or "未知标题",
            "vod_pic": pic,
            "vod_content": "",
            "vod_play_from": play_from,
            "vod_play_url": play_url_str
        }
        return {"list": [data]}

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        page = int(pg) if pg else 1
        url = f"{self.host}/cn/home/web/index.php/vod/search.html?wd={quote(key)}"
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": page}
        videos = self._parse_list_items(html)
        return {"list": videos, "page": page}

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 1, "url": ""}

        headers = {
            "User-Agent": self.headers["User-Agent"],
            "Referer": self.host + "/"
        }

        if id.startswith("http"):
            if ".m3u8" in id or ".mp4" in id:
                # m3u8 走代理过滤广告
                if ".m3u8" in id:
                    return {"parse": 0, "url": self._m3u8_proxy_url(id), "header": headers}
                return {"parse": 0, "url": id, "header": headers}
            if "/vod/play/" in id or id.isdigit():
                detail_url = f"{self.host}/cn/home/web/index.php/vod/play/id/{id}/sid/1/nid/1.html"
                html = self._fetch_html(detail_url)
                if html:
                    player_data = re.search(r'var player_data=({[^}]+})', html)
                    if player_data:
                        try:
                            data = json.loads(player_data.group(1))
                            url_raw = data.get("url", "")
                            if url_raw and (".m3u8" in url_raw or ".mp4" in url_raw):
                                if ".m3u8" in url_raw:
                                    return {"parse": 0, "url": self._m3u8_proxy_url(url_raw), "header": headers}
                                return {"parse": 0, "url": url_raw, "header": headers}
                        except:
                            pass

        return {"parse": 1, "url": str(id), "header": headers}

    def recommendContent(self, ids, pg):
        if not ids:
            return {"list": []}
        vid = str(ids[0])
        url = f"{self.host}/cn/home/web/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        html = self._fetch_html(url)
        if not html:
            return {"list": []}

        videos = []
        pattern = r'<div[^>]*class="index-area[^"]*clearfix[^"]*interest"[^>]*>.*?<ul>(.*?)</ul>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            ul_content = match.group(1)
            item_pattern = r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>.*?<img[^>]*(?:data-original|src)="([^"]+)"[^>]*>.*?<p[^>]*class="name">([^<]*)</p>'
            for m in re.finditer(item_pattern, ul_content, re.DOTALL):
                href = m.group(1)
                vid = self._extract_vod_id(href)
                title = m.group(2) or m.group(4)
                pic = m.group(3)
                if vid and title:
                    videos.append({
                        "vod_id": vid,
                        "vod_name": title.strip(),
                        "vod_pic": self._fix_url(pic)
                    })
        return {"list": videos[:12]}

    def destroy(self):
        pass

    def _m3u8_proxy_url(self, url):
        """生成 m3u8 代理地址"""
        if not url:
            return ""
        url = url.replace("\\/", "/")
        return "http://127.0.0.1:9978/proxy?do=py&url=" + quote(str(url or ""), safe="")

    def localProxy(self, params):
        """m3u8 本地代理 + 广告分片过滤"""
        try:
            if isinstance(params, dict):
                target = params.get("url", "") or params.get("source", "")
            else:
                target = str(params or "")
            if target.startswith("url="):
                target = target[4:]
            elif "url=" in target:
                from urllib.parse import parse_qs
                qs = parse_qs(urlparse(target).query)
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
            self.log({"action": "localProxy_error", "error": str(e)})
            return [500, "text/plain", f"localProxy error: {e}".encode("utf-8", errors="ignore")]

    def _is_fake_image_stream(self, text, source_url):
        """检测是否为图片流伪装"""
        low_url = (source_url or "").lower()
        for sig in ("doyinapi", "svip", "imgcdn", "photo"):
            if sig in low_url:
                return True
        for line in str(text or "").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            low = line.lower().split("?")[0]
            if low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                return True
        return False

    def _resolve_main_dir(self, lines, source_url):
        """确定正片目录锚点（优先使用 KEY URI 目录）"""
        parsed = urlparse(source_url)
        main_dir = parsed.path.rsplit("/", 1)[0] + "/" if "/" in parsed.path else "/"
        for line in lines:
            if not line.startswith("#EXT-X-KEY") or "URI=" not in line:
                continue
            m = re.search(r'URI="([^"]+)"', line)
            if not m:
                continue
            key_uri = m.group(1)
            key_path = urlparse(key_uri if key_uri.startswith("http") else urljoin(source_url, key_uri)).path
            key_dir = key_path.rsplit("/", 1)[0] + "/" if "/" in key_path else "/"
            if key_dir and key_dir != "/":
                return key_dir
        return main_dir

    def _clean_m3u8(self, text, source_url):
        """清洗 m3u8：过滤广告分片，保留正片"""
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 第1层：图片流伪装检测
        if self._is_fake_image_stream(text, source_url):
            restored = text
            for ext in (".png", ".jpeg", ".jpg", ".webp"):
                restored = restored.replace(ext, ".ts")
            self.log({"action": "fake_image_stream", "msg": "检测到图片流伪装，已还原扩展名 -> .ts，跳过广告过滤"})
            return restored

        # 第2层：多码率主表
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urljoin(source_url, line)
                    if ".m3u8" in child.lower():
                        out.append(self._m3u8_proxy_url(child))
                    else:
                        out.append(child)
            return "\n".join(out) + "\n"

        # 第3层：正片目录锚点
        main_dir = self._resolve_main_dir(lines, source_url)

        # 第4层：分片过滤
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
                media_url = urljoin(source_url, line)
                media_path = urlparse(media_url).path
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
                segments.append(urljoin(source_url, line))

        # 第5层：全滤兜底
        if kept == 0 and removed > 0:
            self.log({"action": "m3u8_filter_fallback", "msg": "广告过滤命中全部分片，回退为不过滤模式"})
            out = []
            for line in lines:
                if line and not line.startswith("#"):
                    out.append(urljoin(source_url, line))
                else:
                    out.append(line)
            return "\n".join(out) + "\n"

        if removed:
            self.log({"action": "m3u8_filter", "removed": removed, "kept": kept})

        # 冗余标签清理
        noise = ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE")
        out = []
        for line in segments:
            if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
                def repl(match):
                    uri = match.group(1)
                    return 'URI="' + (uri if uri.startswith(("http://", "https://")) else urljoin(source_url, uri)) + '"'
                line = re.sub(r'URI="([^"]+)"', repl, line)
            if line in noise:
                if not out or out[-1] in noise:
                    continue
            out.append(line)
        while len(out) > 1 and out[-1] in noise:
            out.pop()

        return "\n".join(out) + "\n"