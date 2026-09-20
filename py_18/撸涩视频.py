# coding: utf-8
# 站点: 撸涩视频 (https://axo.lusesp.sbs/)
# 类型: MacCMS影视站，详情页直接跳转播放页
# 特征: 多码率m3u8，含跨目录广告分片，需清洗
# 最后更新: 2026-09-06

import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://axo.lusesp.sbs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        # NEED_CLEAN: m3u8_analyzer取证结论：有跨目录广告分片，需要清洗
        self.NEED_CLEAN = True
        # 分类结构（硬编码，零网络）
        self.classes = [
            {"type_id": "39", "type_name": "卡通动漫"},
            {"type_id": "1", "type_name": "视频一区"},
            {"type_id": "2", "type_name": "视频二区"},
            {"type_id": "3", "type_name": "视频三区"},
            {"type_id": "4", "type_name": "中文字幕"},
            {"type_id": "6", "type_name": "国产视频"},
            {"type_id": "8", "type_name": "抖阴视频"},
            {"type_id": "27", "type_name": "国产少妇"},
            {"type_id": "36", "type_name": "中文字幕"},
            {"type_id": "33", "type_name": "毁三观"},
            {"type_id": "35", "type_name": "无毛合集"},
            {"type_id": "34", "type_name": "乡下妹"},
            {"type_id": "7", "type_name": "国产传媒"},
            {"type_id": "26", "type_name": "日本田野"},
            {"type_id": "13", "type_name": "巨乳美乳"},
            {"type_id": "14", "type_name": "熟女少妇"},
            {"type_id": "15", "type_name": "户外"},
            {"type_id": "10", "type_name": "日本无码"},
            {"type_id": "29", "type_name": "强奸乱伦"},
            {"type_id": "12", "type_name": "萝莉少女"}
        ]
        self.filters = {}

    def getName(self):
        return "撸涩视频"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐：直接取分类列表第1页的前12条"""
        res = self.fetch(f"{self.host}/index.php/vod/type/id/1.html", headers=self.headers)
        if not res or res.status_code != 200:
            return {"list": []}
        html = res.text
        return {"list": self._parse_list(html, self.host + "/index.php/vod/type/id/1.html")}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        res = self.fetch(url, headers=self.headers)
        if not res or res.status_code != 200:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
        html = res.text
        items = self._parse_list(html, url)
        # 从分页器提取总页数
        pagecount = self._get_pagecount(html)
        return {"list": items, "page": int(page), "pagecount": pagecount, "limit": 20, "total": pagecount * 20}

    def detailContent(self, ids):
        """详情页直接跳转播放页，从播放页提取标题、封面，播放ID交给playerContent"""
        vid = self._norm_ids(ids)
        if not vid:
            return {"list": []}
        # 构造播放页URL
        play_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        res = self.fetch(play_url, headers=self.headers)
        if not res or res.status_code != 200:
            return self._skeleton(vid)
        html = res.text
        # 提取标题
        title = self._extract_title(html, vid)
        # 提取封面
        pic = self._extract_pic(html)
        # 直接返回单集播放，让playerContent去提取m3u8
        # 播放ID用播放页URL，playerContent会从该页提取player_aaaa中的m3u8
        vod = {
            "vod_id": vid,
            "vod_name": title or "未知标题",
            "vod_pic": pic or "",
            "vod_remarks": "",
            "vod_content": "",
            "vod_play_from": "播放",
            "vod_play_url": f"第1集${play_url}"
        }
        return {"list": [vod]}
    def searchContent(self, key, quick, pg="1"):
        url = f"{self.host}/index.php/vod/search.html"
        res = self.fetch(url, headers=self.headers, params={"wd": key})
        if not res or res.status_code != 200:
            return {"list": [], "page": 1}
        html = res.text
        items = self._parse_list(html, url)
        return {"list": items, "page": 1}

    def playerContent(self, flag, id, vipFlags):
        ua = self.headers.get("User-Agent", "")
        if not id:
            return {"parse": 1, "url": "", "header": {"User-Agent": ua}}
        raw_id = str(id).strip()
        # L1 直链识别
        if self._is_media_url(raw_id):
            return self._wrap_play(raw_id, ua)
        # 非直链：获取播放页HTML
        page_url = raw_id if raw_id.startswith("http") else urllib.parse.urljoin(self.host, raw_id)
        res = self.fetch(page_url, headers=self.headers)
        if not res or res.status_code != 200:
            return {"parse": 1, "url": page_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}
        html = res.text
        # L2-L6 提取管线
        bag = self._extract_play_candidates(html, page_url)
        cands = self._pick_playable(bag)
        if cands:
            self.log({"stage": "extract", "result": "hit", "count": len(cands), "pick": cands[0]})
            return self._wrap_play(cands[0], ua, referer=page_url)
        self.log({"stage": "extract", "result": "all_layers_miss", "page": page_url})
        return {"parse": 1, "url": page_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

    def recommendContent(self, ids, pg):
        return {"list": []}

    def destroy(self):
        pass

    # ========== 工具方法 ==========

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
        pid = str(vid).split("|$|")[0].replace("$", "|")
        return {"list": [{
            "vod_id": vid,
            "vod_name": title or "未知标题",
            "vod_pic": pic or "",
            "vod_remarks": remarks,
            "vod_content": "",
            "vod_play_from": "播放",
            "vod_play_url": f"播放${pid}"
        }]}

    def _parse_list(self, html, page_url):
        """解析视频列表：.vod_box 容器"""
        items = []
        # 多级兜底：主 .vod_box，备用 [class*="vod_box"]
        pattern = r'<div[^>]*class="[^"]*vod_box[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>.*?<div[^>]*class="[^"]*vod_img[^"]*"[^>]*style="background-image:url\(([^)]+)\)"[^>]*>.*?<span[^>]*class="[^"]*vod_tab[^"]*"[^>]*>(.*?)</span>.*?<div[^>]*class="[^"]*vod_title[^"]*"[^>]*>.*?<h4[^>]*class="[^"]*text-overflow[^"]*"[^>]*>(.*?)</h4>'
        for m in re.finditer(pattern, html, re.S):
            link = m.group(1).strip()
            title = m.group(2).strip()
            pic = m.group(3).strip()
            remark = m.group(4).strip()
            if not link or not title:
                continue
            if not link.startswith("http"):
                link = urllib.parse.urljoin(page_url, link)
            # 提取vod_id
            vid_match = re.search(r'/id/(\d+)', link)
            vod_id = vid_match.group(1) if vid_match else link
            items.append({
                "vod_id": str(vod_id),
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        return items

    def _get_pagecount(self, html):
        """提取总页数，带兜底"""
        # 优先从分页器文本提取 "共72页"
        m = re.search(r'共(\d+)页', html)
        if m:
            return int(m.group(1))
        # 从分页链接提取最大页码
        pages = re.findall(r'/(?:page|p)/(\d+)\.html', html)
        if pages:
            max_page = max(int(p) for p in pages)
            # 如果最大页码只有5，但存在"下一页"链接，说明实际页数更多
            if max_page <= 5 and '下一页' in html:
                # 尝试从"1/29830"格式提取
                m2 = re.search(r'(\d+)/(\d+)', html)
                if m2:
                    return int(m2.group(2))
                # 兜底：返回一个较大的值
                return 100
            return max_page
        pages = re.findall(r'[?&]page=(\d+)', html)
        if pages:
            max_page = max(int(p) for p in pages)
            if max_page <= 5 and '下一页' in html:
                m2 = re.search(r'(\d+)/(\d+)', html)
                if m2:
                    return int(m2.group(2))
                return 100
            return max_page
        # 从 "1/29830" 格式提取
        m = re.search(r'(\d+)/(\d+)', html)
        if m:
            return int(m.group(2))
        return 1
    def _extract_title(self, html, vid):
        """多级兜底提取标题"""
        patterns = [
            r'<h1[^>]*>(.*?)</h1>',
            r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',
            r'<title>([^<]+)</title>',
        ]
        for p in patterns:
            m = re.search(p, html, re.S)
            if m:
                title = m.group(1).strip()
                if title:
                    # 清洗后缀
                    title = re.sub(r'\s*[-|_–]\s*[^-|_–]{2,20}$', '', title)
                    return title
        return "视频_" + str(vid)

    def _extract_pic(self, html):
        """提取封面"""
        patterns = [
            r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
            r'<div[^>]*class="[^"]*(?:lazy|pic|cover|thumb)[^"]*"[^>]*data-original="([^"]+)"',
            r'<div[^>]*class="[^"]*(?:lazy|pic|cover|thumb)[^"]*"[^>]*src="([^"]+)"',
            r'background(?:-image)?:\s*url\(([^)]+)\)',
        ]
        for p in patterns:
            m = re.search(p, html, re.S)
            if m:
                pic = m.group(1).strip()
                if pic and not pic.startswith("http"):
                    pic = urllib.parse.urljoin(self.host, pic)
                return pic
        return ""

    def _extract_routes(self, html, page_url):
        """提取线路与剧集"""
        froms, urls = [], []
        # 找线路名
        tab_pattern = r'<(?:a|li|span)[^>]*class="[^"]*(?:tab|nav-item|playlist-tab|play_tab)[^"]*"[^>]*>(.*?)</(?:a|li|span)>'
        tab_names = re.findall(tab_pattern, html, re.S)
        tab_names = [re.sub(r"<[^>]+>", "", t).strip() for t in tab_names if t.strip()]
        # 找剧集容器
        block_pattern = r'<(?:ul|div)[^>]*class="[^"]*(?:play[_-]?list|playlist|episode|vod_play_list)[^"]*"[^>]*>(.*?)</(?:ul|div)>'
        blocks = re.findall(block_pattern, html, re.S)
        if not blocks:
            # 尝试抓所有a标签
            ep_pattern = r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
            eps = []
            for m in re.finditer(ep_pattern, html, re.S):
                link = m.group(1).strip()
                name = re.sub(r"<[^>]+>", "", m.group(2)).strip()
                if not link or "javascript" in link.lower():
                    continue
                if not link.startswith("http"):
                    link = urllib.parse.urljoin(page_url, link)
                eps.append(f"{name or f'第{len(eps)+1}集'}${link}")
            if eps:
                froms.append("播放")
                urls.append("#".join(eps))
            return froms, urls
        for i, blk in enumerate(blocks):
            eps = []
            seen = set()
            for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S):
                link = m.group(1).strip()
                name = re.sub(r"<[^>]+>", "", m.group(2)).strip()
                if not link or link in seen or "javascript" in link.lower():
                    continue
                seen.add(link)
                if not link.startswith("http"):
                    link = urllib.parse.urljoin(page_url, link)
                eps.append(f"{name or f'第{len(eps)+1}集'}${link}")
            if eps:
                froms.append(tab_names[i] if i < len(tab_names) else f"线路{i+1}")
                urls.append("#".join(eps))
        return froms, urls

    def _align(self, froms, urls):
        """对齐并丢弃空组"""
        pairs = [(f, u) for f, u in zip(froms, urls) if f and u and u.strip()]
        if not pairs:
            return "", ""
        return "$$$".join(p[0] for p in pairs), "$$$".join(p[1] for p in pairs)

    def _sniff_media(self, html):
        """从播放页内嵌JSON提取直链"""
        # L2 播放器变量
        for var in ("player_aaaa", "player_data", "playerData"):
            m = re.search(r'(?:var|let|const)?\s*' + re.escape(var) + r'\s*=\s*\{', html)
            if m:
                brace = html.find("{", m.end())
                if brace > 0:
                    raw = self._grab_json_object(html, brace)
                    if raw:
                        obj = self._loose_json(raw)
                        if obj and isinstance(obj, dict):
                            for k in ("url", "play_url", "src", "link", "m3u8"):
                                v = obj.get(k)
                                if v and isinstance(v, str) and self._is_media_url(v):
                                    return self._normalize_url(v)
        # L5 全文正则
        patterns = (
            r'(https?://[^\s"\'<>()\\]+?\.m3u8[^\s"\'<>()\\]*)',
            r'(https?://[^\s"\'<>()\\]+?\.mp4[^\s"\'<>()\\]*)',
        )
        for p in patterns:
            m = re.search(p, html)
            if m:
                return self._normalize_url(m.group(1))
        return ""

    def _grab_json_object(self, html, start_idx):
        if start_idx < 0 or start_idx >= len(html) or html[start_idx] != "{":
            return ""
        depth, in_str, esc, quote = 0, False, False, ""
        for i in range(start_idx, len(html)):
            ch = html[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == quote:
                    in_str = False
                continue
            if ch in ('"', "'"):
                in_str, quote = True, ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return html[start_idx:i + 1]
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

    def _extract_play_candidates(self, html, page_url, depth=0):
        """9层管线 L2-L6"""
        bag = []
        if not html:
            return bag
        # L2 播放器变量
        for var in ("player_aaaa", "player_data", "playerConf", "playerData"):
            for m in re.finditer(re.escape(var) + r'\s*=\s*', html):
                brace = html.find("{", m.end())
                if brace < 0 or brace - m.end() > 8:
                    continue
                raw = self._grab_json_object(html, brace)
                obj = self._loose_json(raw)
                if obj is not None:
                    self._walk_json(obj, bag)
                elif raw:
                    for p in self.FALLBACK_PATTERNS:
                        bag.extend(re.findall(p, raw))
        # L3 内联JSON
        for m in re.finditer(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html, re.S):
            obj = self._loose_json(m.group(1).strip())
            if obj is not None:
                self._walk_json(obj, bag)
        # L5 全文正则
        for p in self.FALLBACK_PATTERNS:
            for hit in re.findall(p, html):
                bag.append(hit if isinstance(hit, str) else hit[0])
        # L6 iframe递归（限深2）
        if depth < 2 and not self._has_strong_candidate(bag):
            for src in re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)[:3]:
                sub_url = urllib.parse.urljoin(page_url, self._normalize_url(src))
                if not sub_url.startswith("http"):
                    continue
                try:
                    res = self.fetch(sub_url, headers=self.headers, timeout=10)
                    if res and res.status_code == 200:
                        sub_html = res.text
                        bag.extend(self._extract_play_candidates(sub_html, sub_url, depth + 1))
                except Exception:
                    continue
        return bag

    FALLBACK_PATTERNS = (
        r'https?://[^\s"\'<>()\\]+?\.m3u8[^\s"\'<>()\\]*',
        r'https?://[^\s"\'<>()\\]+?\.mp4[^\s"\'<>()\\]*',
        r'https?://[^\s"\'<>()\\]+?/index\.m3u8[^\s"\'<>()\\]*',
        r'["\']((?:https?:)?\\?/\\?/[^\s"\'<>]+?\.m3u8[^\s"\'<>]*)["\']',
    )

    def _has_strong_candidate(self, bag):
        for raw in bag:
            u = self._normalize_url(raw)
            if u.startswith("http") and (".m3u8" in u.lower() or ".mp4" in u.lower()):
                return True
        return False

    def _walk_json(self, node, bag, depth=0):
        if depth > 6 or node is None:
            return
        URL_KEYS = ("url", "play_url", "playUrl", "video_url", "videoUrl", "src", "source", "m3u8", "hls", "file", "purl", "vurl")
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str):
                    kl = str(k).lower()
                    if kl in URL_KEYS or self._looks_like_media(v):
                        bag.append(v)
                else:
                    self._walk_json(v, bag, depth + 1)
        elif isinstance(node, list):
            for v in node:
                if isinstance(v, str) and self._looks_like_media(v):
                    bag.append(v)
                else:
                    self._walk_json(v, bag, depth + 1)

    def _looks_like_media(self, s):
        if not isinstance(s, str):
            return False
        low = s.lower()
        return ".m3u8" in low or ".mp4" in low or ".mkv" in low or ".flv" in low

    def _normalize_url(self, raw):
        if not raw:
            return ""
        s = str(raw).strip().strip('"').strip("'")
        s = s.replace("\\/", "/").replace("\\u002f", "/").replace("\\u002F", "/")
        s = s.replace('" + "', "").replace("' + '", "")
        # HTML实体
        try:
            s = html.unescape(s) if hasattr(html, 'unescape') else s
        except Exception:
            pass
        # URL编码（双层）
        for _ in range(2):
            if "%3A%2F%2F" in s or "%3a%2f%2f" in s:
                try:
                    s = urllib.parse.unquote(s)
                except Exception:
                    break
            else:
                break
        return s.strip()

    def _pick_playable(self, bag):
        seen, cands = set(), []
        for raw in bag:
            u = self._normalize_url(raw)
            if not u or not u.startswith("http") or u in seen:
                continue
            seen.add(u)
            cands.append(u)
        def score(u):
            low = u.lower()
            s = 0
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

    def _is_media_url(self, url):
        if not url or not str(url).startswith("http"):
            return False
        path = str(url).split("?")[0].split("#")[0].lower()
        media_ext = (".m3u8", ".mp4", ".mkv", ".flv", ".avi", ".m4v", ".mov", ".ts")
        if path.endswith(media_ext):
            return True
        low = str(url).lower()
        return "/hls/" in low and "m3u8" in low

    def _wrap_play(self, url, ua, referer=""):
        header = {"User-Agent": ua}
        if referer:
            header["Referer"] = referer
        if self.NEED_CLEAN and ".m3u8" in url.lower():
            return {"parse": 0, "url": self._m3u8_proxy_url(url), "header": header}
        return {"parse": 0, "url": url, "header": header}

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def localProxy(self, param):
        """m3u8本地代理 + 五层广告过滤"""
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
            if not resp or resp.status_code != 200:
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
            self.log("localProxy error: " + str(e))
            return [500, "text/plain", f"localProxy error: {e}".encode("utf-8", errors="ignore")]

    def _clean_m3u8(self, text, source_url):
        """五层广告过滤管线"""
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 第1层：图片流检测（只打标记，不return，不改后缀）
        is_img = self._is_fake_image_stream(text, source_url)
        if is_img:
            self.log({"stage": "clean", "fake_image_stream": True, "action": "keep_suffix_as_is"})

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

        # 第3层：正片目录锚点（图片流改用分片目录众数）
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

        # 第5层：冗余标签清理
        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

    def _is_fake_image_stream(self, text, source_url):
        """检测图片流伪装：只依据分片扩展名"""
        IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
        VIDEO_EXT = (".ts", ".m4s", ".mp4", ".aac", ".m4a")
        has_video, has_image = False, False
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

        # 图片流：用分片目录众数
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
                key_uri if key_uri.startswith("http") else urllib.parse.urljoin(source_url, key_uri)
            ).path
            key_dir = posixpath.dirname(key_path)
            if key_dir and key_dir != "/":
                return key_dir + "/"
        return base_dir

    def _filter_segments(self, lines, source_url, main_dir):
        segments, pending, removed, kept = [], [], 0, 0
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