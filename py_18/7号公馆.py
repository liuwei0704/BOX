# coding: utf-8
"""
站点：7号公馆
主域名：https://sp.7haosfsg.sbs/
备用域名：7h.7haogg.shop（发布页）
内容类型：成人影视（偷拍/无码/中文/多人/巨乳/制服/伦理/亚洲）
特殊说明：标准MacCMS站，详情页需带Cookie访问，播放地址在player_aaaa中
验证时间：2026-09-05
来源：用户提供
m3u8结构摘要：多码率主表，KEY URI目录锚点，suspicious_ad_dirs包含跨目录分片（/20260830/oV2IGqQV/1000kb/hls/），需走localProxy清洗
"""
import json
import re
import urllib.parse
import posixpath
from base.spider import Spider as BaseSpider
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://sp.7haosfsg.sbs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "66", "type_name": "偷拍"},
            {"type_id": "67", "type_name": "无码"},
            {"type_id": "50", "type_name": "中文"},
            {"type_id": "51", "type_name": "多人"},
            {"type_id": "68", "type_name": "巨乳"},
            {"type_id": "69", "type_name": "制服"},
            {"type_id": "54", "type_name": "伦理"},
            {"type_id": "55", "type_name": "亚洲"}
        ]
        self.filters = {}
        for c in self.classes:
            self.filters[c["type_id"]] = []

    def getName(self):
        return "7号公馆"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        # 首页推荐：取分类列表页第一页
        return self.categoryContent("66", "1", False, {})

    def categoryContent(self, tid, pg, filter, extend):
        page = str(pg or "1")
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        resp = self.fetch(url, headers=self.headers, timeout=15)
        if not resp or resp.status_code != 200:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
        html = resp.text
        list_data = self._parse_list(html)
        # 简单分页信息：从页面提取总页数，默认使用pagination_parser结果
        pagecount = 41
        total = 41 * 24
        return {
            "list": list_data,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 24,
            "total": total
        }

    def _parse_list(self, html):
        import html as html_parser
        results = []
        # 匹配 li.stui-vodlist__item
        pattern = r'<li class="stui-vodlist__item">.*?<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>.*?<span class="pic-text[^"]*">([^<]*)</span>.*?data-original="([^"]+)"'
        for m in re.finditer(pattern, html, re.S):
            link = m.group(1)
            title = html_parser.unescape(m.group(2).strip())
            remark = html_parser.unescape(m.group(3).strip())
            pic = m.group(4).strip()
            if not pic.startswith("http"):
                pic = "https:" + pic if pic.startswith("//") else pic
            vod_id = link.replace("/index.php/vod/detail/id/", "").replace(".html", "")
            results.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        return results

    def detailContent(self, ids):
        # 兼容 ids 为 int、str、list 三种情况
        if ids is None:
            return {"list": []}
        if isinstance(ids, list):
            vid = str(ids[0]) if ids else ""
        else:
            vid = str(ids)
        if not vid:
            return {"list": []}

        url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
        resp = self.fetch(url, headers=self.headers, timeout=15)
        if not resp or resp.status_code != 200:
            return {"list": []}
        html = resp.text
        
        # 解码 HTML 实体（修复乱码）
        import html as html_parser
        
        # 提取标题
        title_match = re.search(r'<h3 class="title">([^<]+)</h3>', html)
        title = html_parser.unescape(title_match.group(1).strip()) if title_match else ""
        
        # 提取封面
        pic_match = re.search(r'data-original="([^"]+)"', html)
        pic = pic_match.group(1) if pic_match else ""
        
        # 提取简介
        desc_match = re.search(r'<div class="stui-content__desc[^"]*">([^<]+)</div>', html)
        desc = html_parser.unescape(desc_match.group(1).strip()) if desc_match else ""
        
        # 提取分类
        type_match = re.search(r'<a href="/index.php/vod/type/id/\d+\.html">([^<]+)</a>', html)
        type_name = html_parser.unescape(type_match.group(1)) if type_match else ""
        
        # 提取播放列表
        play_urls = []
        seen = set()
        # 先尝试匹配播放列表容器
        playlist_match = re.search(r'<ul class="stui-content__playlist clearfix">(.*?)</ul>', html, re.S)
        if playlist_match:
            playlist_html = playlist_match.group(1)
            for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', playlist_html, re.S):
                link = m.group(1).strip()
                name = m.group(2).strip()
                # 解码链接中的中文
                name = html_parser.unescape(name)
                if not link.startswith("/") and not link.startswith("http"):
                    link = "/" + link
                if link not in seen:
                    seen.add(link)
                    play_urls.append((name, link))
        else:
            # 备用：直接查找播放链接
            for m in re.finditer(r'<a[^>]*href="(/index.php/vod/play/[^"]+)"[^>]*>([^<]+)</a>', html, re.S):
                link = m.group(1).strip()
                name = m.group(2).strip()
                name = html_parser.unescape(name)
                if not link.startswith("/") and not link.startswith("http"):
                    link = "/" + link
                if link not in seen:
                    seen.add(link)
                    play_urls.append((name, link))
        
        # 构建播放数据
        vod_play_from = "在线播放2"
        # 修复：使用完整 URL 作为播放 ID，而不是相对路径
        play_items = []
        for name, link in play_urls:
            # 补全为完整 URL，让 playerContent 直接处理
            full_link = link if link.startswith("http") else f"{self.host}{link}"
            play_items.append(f"{name}${full_link}")
        vod_play_url = "#".join(play_items) if play_items else ""
        
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": type_name,
            "vod_content": desc,
            "vod_actor": "",
            "vod_director": "",
            "vod_play_from": vod_play_from,
            "vod_play_url": vod_play_url
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        page = str(pg or "1")
        url = f"{self.host}/index.php/vod/search.html"
        data = {"wd": key, "pg": page}
        resp = self.post(url, data=data, headers=self.headers, timeout=15)
        if not resp or resp.status_code != 200:
            return {"list": [], "page": int(page)}
        html = resp.text
        results = self._parse_list(html)
        return {"list": results, "page": int(page)}

    def playerContent(self, flag, id, vipFlags):
        ua = self.headers.get("User-Agent", "")
        raw_id = str(id or "").strip()
        if not raw_id:
            return {"parse": 1, "url": "", "header": {"User-Agent": ua}}

        # L1: 直链检测
        if raw_id.startswith("http") and (".m3u8" in raw_id or ".mp4" in raw_id):
            return {"parse": 0, "url": raw_id, "header": {"User-Agent": ua}}

        # 播放页URL
        play_url = raw_id if raw_id.startswith("http") else f"{self.host}{raw_id}"
        resp = self.fetch(play_url, headers=self.headers, timeout=15)
        if not resp or resp.status_code != 200:
            return {"parse": 1, "url": play_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

        html = resp.text

        # L2: player_aaaa 变量提取 - 使用平衡括号匹配
        start_pattern = r'var\s+player_aaaa\s*=\s*'
        start_match = re.search(start_pattern, html)
        if start_match:
            start_idx = start_match.end()
            brace_idx = html.find("{", start_idx)
            if brace_idx != -1:
                raw_json = self._grab_json_object(html, brace_idx)
                if raw_json:
                    try:
                        # 处理转义字符
                        raw_json = raw_json.replace("\\/", "/")
                        raw_json = raw_json.replace("\\n", "").replace("\\r", "")
                        data = json.loads(raw_json)
                        url = data.get("url", "")
                        if url and url.startswith("http"):
                            # 走代理清洗
                            return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua, "Referer": self.host + "/", "Origin": self.host}}
                    except json.JSONDecodeError:
                        # JSON 解析失败，尝试正则提取 URL
                        url_match = re.search(r'"url":"([^"]+\.m3u8[^"]*)"', raw_json)
                        if url_match:
                            url = url_match.group(1).replace("\\/", "/")
                            if url.startswith("http"):
                                return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}

        # L5: 全文正则兜底
        m3u8_patterns = [
            r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*',
            r'"url":"([^"]+\.m3u8[^"]*)"',
        ]
        for pat in m3u8_patterns:
            for m in re.finditer(pat, html):
                url = m.group(1) if m.lastindex else m.group(0)
                if url and url.startswith("http") and ".m3u8" in url:
                    return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": {"User-Agent": ua}}

        # 降级
        return {"parse": 1, "url": play_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

    def _grab_json_object(self, text, start_idx):
        """从指定位置开始，使用平衡括号匹配提取完整的 JSON 对象"""
        if start_idx < 0 or start_idx >= len(text) or text[start_idx] != "{":
            return ""
        depth = 0
        in_str = False
        escape = False
        for i in range(start_idx, len(text)):
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]
        return ""

    def _m3u8_proxy_url(self, url):
        # 归一化 URL：去掉反斜杠转义
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def localProxy(self, param):
        """m3u8 清洗：过滤跨目录广告分片"""
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
        target = urllib.parse.unquote(str(target or ""))
        if not target or not re.match(r"^https?://", target, re.I):
            return [400, "text/plain", b"invalid url"]

        resp = self.fetch(target, headers=self.headers, timeout=20)
        if not resp or resp.status_code != 200:
            return [502, "text/plain", b"fetch failed"]
        content = getattr(resp, "content", b"") or b""
        if not content and getattr(resp, "text", ""):
            content = resp.text.encode("utf-8", errors="ignore")
        if not content:
            return [502, "text/plain", b"empty content"]

        if b"#EXTM3U" not in content[:256]:
            return [200, "application/octet-stream", content]

        text = content.decode("utf-8", errors="ignore")
        cleaned = self._clean_m3u8(text, target)
        return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

    def _clean_m3u8(self, text, source_url):
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 第2层：多码率主表透传
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

        # 第3层：锚点目录（KEY URI目录优先）
        main_dir = self._resolve_main_dir(lines, source_url)
        if not main_dir:
            main_dir = urllib.parse.urlparse(source_url).path
            if main_dir and not main_dir.endswith("/"):
                main_dir = main_dir[:main_dir.rfind("/") + 1]

        # 第4层：分片过滤
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)

        # 第5层：全滤兜底
        if removed > 0 and (kept == 0 or removed > kept):
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        # 冗余标签清理
        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

    def _resolve_main_dir(self, lines, source_url):
        import posixpath
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
        base_dir = posixpath.dirname(urllib.parse.urlparse(source_url).path)
        if base_dir and not base_dir.endswith("/"):
            base_dir += "/"
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
        # 简单推荐：返回空列表
        return {"list": []}

    def destroy(self):
        pass