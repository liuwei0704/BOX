# coding: utf-8
# 站点: 小螺号
# 域名: https://fci.xlh8.hair
# 类型: MacCMS 成人影视站

import json
import re
from urllib.parse import urljoin, quote, unquote, urlparse

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://fci.xlh8.hair"
        self.classes = [
            {"type_id": "20", "type_name": "偷拍自拍"},
            {"type_id": "21", "type_name": "强奸乱伦"},
            {"type_id": "22", "type_name": "人妻熟女"},
            {"type_id": "23", "type_name": "制服情景"},
            {"type_id": "24", "type_name": "国产情色"},
            {"type_id": "25", "type_name": "亚洲精品"},
            {"type_id": "26", "type_name": "卡通动漫"},
            {"type_id": "27", "type_name": "欧美性爱"},
            {"type_id": "28", "type_name": "精品三级"},
        ]
        self.filters = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
        }

    def getName(self):
        return "小螺号"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        url = self.host + "/cn/home/web/"
        try:
            resp = self.fetch(url, headers=self.headers)
            if not resp:
                return {"list": []}
            html = resp.text if hasattr(resp, "text") else ""
            if not html:
                return {"list": []}
            items = self._parse_list_from_html(html)
            return {"list": items[:20]}
        except Exception:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/cn/home/web/index.php/vod/type/id/{tid}/page/{page}.html"
        try:
            resp = self.fetch(url, headers=self.headers)
            if not resp:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            html = resp.text if hasattr(resp, "text") else ""
            if not html:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            items = self._parse_list_from_html(html)
            total = self._parse_total(html)
            pagecount = self._parse_pagecount(html)
            return {
                "list": items,
                "page": int(page),
                "pagecount": pagecount or 1,
                "limit": 20,
                "total": total or 0,
            }
        except Exception:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vod_id = str(ids[0])
        url = f"{self.host}/cn/home/web/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        try:
            resp = self.fetch(url, headers=self.headers)
            if not resp:
                return {"list": []}
            html = resp.text if hasattr(resp, "text") else ""
            if not html:
                return {"list": []}
            title = self._extract_title(html)
            play_url = self._extract_play_url(html)
            if not title:
                title = "未知视频"
            vod = {
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": "",
                "vod_remarks": "",
                "vod_content": "",
                "vod_play_from": "播放",
                "vod_play_url": f"播放${play_url}" if play_url else "",
            }
            return {"list": [vod]}
        except Exception:
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        url = f"{self.host}/cn/home/web/index.php/vod/search.html"
        data = {"wd": key}
        try:
            resp = self.post(url, data=data, headers=self.headers)
            if not resp:
                return {"list": [], "page": 1}
            html = resp.text if hasattr(resp, "text") else ""
            if not html:
                return {"list": [], "page": 1}
            items = self._parse_list_from_html(html)
            return {"list": items, "page": int(pg)}
        except Exception:
            return {"list": [], "page": 1}

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        play_url = str(id).strip()
        if play_url.startswith("http") and ".m3u8" in play_url:
            # 走代理，让 localProxy 处理图片流转换
            return {
                "parse": 0,
                "url": self._m3u8_proxy_url(play_url),
                "header": self.headers,
            }
        return {"parse": 1, "url": play_url, "header": self.headers}

    def recommendContent(self, ids, pg):
        if not ids or not ids[0]:
            return {"list": []}
        # 获取当前视频ID，需要先获取标题
        vod_id = str(ids[0])
        url = f"{self.host}/cn/home/web/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        try:
            resp = self.fetch(url, headers=self.headers)
            if not resp:
                return {"list": []}
            html = resp.text if hasattr(resp, "text") else ""
            if not html:
                return {"list": []}
            title = self._extract_title(html)
            if not title:
                return {"list": []}
            # 取标题前5个字符作为搜索关键词
            keyword = title[:5].strip()
            if len(keyword) < 2:
                return {"list": []}
            # 调用搜索获取推荐列表
            search_result = self.searchContent(keyword, False, "1")
            items = search_result.get("list", [])
            # 过滤掉当前视频自身（如果有相同ID）
            filtered = [item for item in items if str(item.get("vod_id", "")) != vod_id]
            return {"list": filtered[:12]}
        except Exception:
            return {"list": []}

    def localProxy(self, param):
        target = ""
        if isinstance(param, dict):
            target = param.get("url", "") or param.get("source", "")
        elif isinstance(param, str):
            target = param
        if target and target.startswith("url="):
            target = target[4:]
        if target and "url=" in target:
            parsed = urlparse(target)
            qs = self._parse_qs(parsed.query)
            if "url" in qs:
                target = qs["url"][0]
        target = unquote(str(target or ""))
        if not target or not re.match(r"^https?://", target, re.I):
            return [400, "text/plain", b"invalid url"]
        try:
            resp = self.fetch(target, headers=self.headers, timeout=20)
            if not resp:
                return [502, "text/plain", b"fetch failed"]
            content = getattr(resp, "content", b"") or b""
            if not content and hasattr(resp, "text") and resp.text:
                content = resp.text.encode("utf-8", errors="ignore")
            if not content:
                return [502, "text/plain", b"empty content"]
            if b"#EXTM3U" in content[:256]:
                text = content.decode("utf-8", errors="ignore")
                
                # 检测是否为图片流（PNG伪装）
                is_png_stream = False
                if 'doyinapi' in target.lower() or 'svip' in target.lower():
                    is_png_stream = True
                if not is_png_stream and '.png' in text.lower():
                    is_png_stream = True
                
                if is_png_stream:
                    # 图片流：替换 .png -> .ts，不做广告过滤
                    text = text.replace('.png', '.ts')
                    self.log("小螺号 检测到图片流，已替换 .png -> .ts")
                    return [200, "application/vnd.apple.mpegurl", text.encode("utf-8")]
                
                cleaned = self._clean_m3u8(text, target)
                return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]
            content_type = "application/octet-stream"
            if target.endswith(".ts"):
                content_type = "video/mp2t"
            elif target.endswith(".m3u8"):
                content_type = "application/vnd.apple.mpegurl"
            elif target.endswith(".jpg") or target.endswith(".png"):
                content_type = "image/jpeg"
            elif target.endswith(".mp4"):
                content_type = "video/mp4"
            return [200, content_type, content]
        except Exception as e:
            return [500, "text/plain", str(e).encode("utf-8")]

    def _parse_list_from_html(self, html):
        items = []
        # 匹配 li.video 中的视频条目
        pattern = r'<li class="video[^"]*">.*?<a href="([^"]+)"[^>]*>.*?<div class="thumb">.*?<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            link, pic, title = match
            if not link or not title:
                continue
            vod_id = self._extract_id_from_url(link)
            if not vod_id:
                continue
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, pic) if pic else "",
                "vod_remarks": "",
            })
        return items

    def _extract_id_from_url(self, url):
        match = re.search(r'/play/id/(\d+)/', url)
        return match.group(1) if match else None

    def _extract_title(self, html):
        match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        return match.group(1).strip() if match else None

    def _extract_play_url(self, html):
        match = re.search(r'player_data\s*=\s*\{[^}]*"url"\s*:\s*"([^"]+)"', html)
        if match:
            return match.group(1).replace("\\/", "/")
        return None

    def _parse_total(self, html):
        match = re.search(r'共有视频\s*<span[^>]*>(\d+)</span>', html)
        return int(match.group(1)) if match else 0

    def _parse_pagecount(self, html):
        matches = re.findall(r'/page/(\d+)\.html', html)
        if matches:
            max_page = 0
            for m in matches:
                try:
                    p = int(m)
                    if p > max_page:
                        max_page = p
                except:
                    pass
            if max_page > 0:
                return max_page
        return 1

    def _m3u8_proxy_url(self, url):
        return self.getProxyUrl() + "&url=" + quote(str(url or ""), safe="")

    def _parse_qs(self, qs):
        result = {}
        for part in qs.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                result[k] = [v]
        return result

    def _clean_m3u8(self, text, source_url):
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"
        is_multi = any(line.startswith("#EXT-X-STREAM-INF") for line in lines)
        if is_multi:
            return self._clean_m3u8_multi(lines, source_url)
        return self._clean_m3u8_single(lines, source_url)

    def _clean_m3u8_single(self, lines, source_url):
        parsed = urlparse(source_url)
        dir_path = parsed.path.rsplit("/", 1)[0] + "/" if "/" in parsed.path else "/"

        def is_valid_segment(url):
            parsed_url = urlparse(url)
            return parsed_url.path.startswith(dir_path)

        result = []
        pending_extinf = []
        removed = 0
        kept = 0
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("#EXT-X-KEY") and "URI=" in line:
                line = self._rewrite_m3u8_tag(line, source_url)
                result.append(line)
                i += 1
                continue
            if line.startswith("#EXTINF"):
                pending_extinf = [line]
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith("#"):
                        pending_extinf.append(next_line)
                        i += 1
                    else:
                        media_url = urljoin(source_url, next_line)
                        if is_valid_segment(media_url):
                            result.extend(pending_extinf)
                            result.append(media_url)
                            kept += 1
                        else:
                            removed += 1
                        i += 1
                        break
                continue
            result.append(line)
            i += 1
        return "\n".join(result) + "\n"

    def _clean_m3u8_multi(self, lines, source_url):
        out = []
        for line in lines:
            if line.startswith("#"):
                out.append(line)
            else:
                child_url = urljoin(source_url, line)
                out.append(self._m3u8_proxy_url(child_url))
        return "\n".join(out) + "\n"

    def _rewrite_m3u8_tag(self, line, source_url):
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(match):
                uri = match.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)
        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urljoin(source_url, line)
        return line