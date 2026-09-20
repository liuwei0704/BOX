# coding: utf-8
"""
站点：妓yuan视频
域名：https://ck.jiyuansfw.cfd/ (备用: https://d.jiyuanav.cc)
类型：标准影视站 (MacCMS模板)
分类：视频、香港伦理、网曝黑料、日本无码、日本有码、经典少妇、情色动画、经典国产、传媒原创
详情：/index.php/vod/detail/id/{id}.html
播放：/index.php/vod/play/id/{id}/sid/{sid}/nid/{nid}.html
分页：/index.php/vod/type/id/{tid}/page/{page}.html
搜索：/index.php/vod/search.html?wd={keyword}
最后更新：2026-09-06
"""
import re
import json
import html
from urllib.parse import urljoin, quote, unquote, urlparse

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://ck.jiyuansfw.cfd"
        self.backup_hosts = ["https://d.jiyuanav.cc"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "42", "type_name": "视频"},
            {"type_id": "52", "type_name": "香港伦理"},
            {"type_id": "51", "type_name": "网曝黑料"},
            {"type_id": "49", "type_name": "日本无码"},
            {"type_id": "50", "type_name": "日本有码"},
            {"type_id": "47", "type_name": "经典少妇"},
            {"type_id": "46", "type_name": "情色动画"},
            {"type_id": "45", "type_name": "经典国产"},
            {"type_id": "44", "type_name": "传媒原创"},
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}
        self.extend = ""
        self.NEED_CLEAN = True

    def getName(self):
        return "妓yuan视频"

    def getDependence(self):
        return []

    def init(self, extend=""):
        # 强制使用主域名，禁用自动切换
        # 备用域名 d.jiyuanav.cc 在 TVBox 沙盒中无法访问
        self.host = "https://ck.jiyuansfw.cfd"

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            r = self.fetch(self.host + "/", headers=self.headers, timeout=15)
            if not r or r.status_code != 200:
                return {"list": []}
            html_text = r.text
            items = []
            # 提取热门视频列表
            pattern = r'<div class="xb3 xl6 xm4 xs6 ul">\s*<div class="item">\s*<div class="thumb">\s*<a href="([^"]+)"[^>]*>.*?<img[^>]*data-original="([^"]+)"[^>]*alt="([^"]*)"'
            matches = re.findall(pattern, html_text, re.S)
            for href, pic, title in matches[:20]:
                if not href.startswith("http"):
                    href = urljoin(self.host, href)
                items.append({
                    "vod_id": href,
                    "vod_name": html.unescape(title).strip(),
                    "vod_pic": pic,
                    "vod_remarks": ""
                })
            return {"list": items}
        except Exception as e:
            self.log({"homeVideoContent": "error", "msg": str(e)})
            return {"list": []}

    def _fetch_with_fallback(self, url, **kwargs):
        hosts = [self.host] + self.backup_hosts
        for h in hosts:
            try:
                full_url = urljoin(h, url) if not url.startswith("http") else url
                r = self.fetch(full_url, headers=self.headers, timeout=15, **kwargs)
                if r and r.status_code == 200:
                    return r
            except Exception:
                continue
        return None

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
                "Referer": self.host + "/"
            }
            r = self.fetch(url, headers=headers, timeout=15)
            if not r or r.status_code != 200:
                self.log({"category": "fetch_failed", "status": r.status_code if r else None})
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            html_text = r.text
            items = []
            pattern = r'<div class="xb3 xl6 xm4 xs6 ul">\s*<div class="item">\s*<div class="thumb">\s*<a href="([^"]+)"[^>]*>.*?<img[^>]*data-original="([^"]+)"[^>]*alt="([^"]*)"'
            for href, pic, title in re.findall(pattern, html_text, re.S):
                if not href.startswith("http"):
                    href = urljoin(self.host, href)
                items.append({
                    "vod_id": href,
                    "vod_name": html.unescape(title).strip(),
                    "vod_pic": pic,
                    "vod_remarks": ""
                })
            # 提取总页数 - 多种方式
            pagecount = 1
            # 方式1: 共X页
            pager_match = re.search(r'共\s*(\d+)\s*页', html_text)
            if pager_match:
                pagecount = int(pager_match.group(1))
                self.log({"category": "pagecount_method1", "pagecount": pagecount})
            # 方式2: 分页器中的最大数字
            if pagecount == 1:
                nums = re.findall(r'<a[^>]*>(\d+)</a>', html_text)
                if nums:
                    pagecount = max(int(n) for n in nums if n.isdigit())
                    self.log({"category": "pagecount_method2", "pagecount": pagecount, "nums": nums[:10]})
            # 方式3: 查找 /page/ 链接中的最大数字
            if pagecount == 1:
                nums = re.findall(r'/page/(\d+)\.html', html_text)
                if nums:
                    pagecount = max(int(n) for n in nums if n.isdigit())
                    self.log({"category": "pagecount_method3", "pagecount": pagecount, "nums": nums[:10]})
            self.log({"category": "final_pagecount", "pagecount": pagecount})
            return {
                "list": items,
                "page": int(page),
                "pagecount": pagecount,
                "limit": 20,
                "total": pagecount * 20
            }
        except Exception as e:
            self.log({"category": "exception", "msg": str(e)})
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

    def _skeleton(self, vid, title="", pic="", remarks="解析中"):
        pid = str(vid).split("|$|")[0].replace("$", "|")
        return {"list": [{
            "vod_id": vid,
            "vod_name": title or "未知标题",
            "vod_pic": pic or "",
            "vod_remarks": remarks,
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
        elif vid.startswith("/"):
            detail_url = urljoin(self.host, vid)
        else:
            detail_url = f"{self.host}/index.php/vod/detail/id/{vid}.html"

        try:
            r = self.fetch(detail_url, headers=self.headers, timeout=15)
            if not r or r.status_code != 200 or len(r.text) < 500:
                return self._skeleton(vid)

            html_text = r.text

            # 提取标题
            title = ""
            # 提取标题 - 多种方式
            title = ""
            # 方式1: <p>影片名称：xxx</p>
            title_match = re.search(r'<p>影片名称[：:]\s*(.*?)</p>', html_text, re.S)
            if title_match:
                title = html.unescape(title_match.group(1).strip())
            # 方式2: <title>xxx</title>
            if not title:
                title_match = re.search(r'<title>(.*?)</title>', html_text, re.S)
                if title_match:
                    raw = html.unescape(title_match.group(1).strip())
                    # 去掉站名后缀
                    title = re.sub(r'_[^_]+$', '', raw)
            # 方式3: og:title
            if not title:
                title_match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html_text)
                if title_match:
                    title = html.unescape(title_match.group(1).strip())
            title = title.strip() or "未知标题"
            if title_match:
                title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
            else:
                title_match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html_text)
                if title_match:
                    title = html.unescape(title_match.group(1)).strip()
            title = html.unescape(title).strip()

            # 提取封面
            pic = ""
            pic_match = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html_text)
            if pic_match:
                pic = pic_match.group(1).strip()
            else:
                pic_match = re.search(r'<img[^>]+data-original="([^"]+)"[^>]*class="[^"]*thumb[^"]*"', html_text)
                if pic_match:
                    pic = pic_match.group(1).strip()

            # 提取简介
            desc = ""
            desc_match = re.search(r'<div[^>]*class="[^"]*(?:desc|content|plot)[^"]*"[^>]*>(.*?)</div>', html_text, re.S)
            if desc_match:
                desc = re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()
                desc = html.unescape(desc)

            # 提取播放列表链接（剧集）
            play_links = []
            # 方法1：MacCMS 常见剧集列表
            playlist_pattern = r'<div[^>]*class="[^"]*(?:playlist|play_list|play-box)[^"]*"[^>]*>(.*?)</div>'
            blocks = re.findall(playlist_pattern, html_text, re.S)
            for blk in blocks:
                for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S):
                    link = m.group(1).strip()
                    name = re.sub(r"<[^>]+>", "", m.group(2)).strip()
                    if link and not link.startswith("http"):
                        link = urljoin(self.host, link)
                    if link and name and "play" in link:
                        play_links.append((name, link))

            # 方法2：直接提取所有包含"play"的链接
            if not play_links:
                for m in re.finditer(r'<a[^>]*href="([^"]*play[^"]*)"[^>]*>([^<]*)</a>', html_text, re.S):
                    link = m.group(1).strip()
                    name = m.group(2).strip()
                    if link and name:
                        if not link.startswith("http"):
                            link = urljoin(self.host, link)
                        play_links.append((name, link))

            # 去重
            seen = set()
            unique_links = []
            for name, link in play_links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append((name, link))
            play_links = unique_links

            if not play_links:
                return self._skeleton(vid, title, pic)

            play_from = "播放"
            play_url = "#".join([f"{name}${link}" for name, link in play_links])

            return {"list": [{
                "vod_id": vid,
                "vod_name": title or "未知标题",
                "vod_pic": pic or "",
                "vod_remarks": "",
                "vod_content": desc or "",
                "vod_actor": "",
                "vod_director": "",
                "vod_play_from": play_from,
                "vod_play_url": play_url,
            }]}

        except Exception as e:
            self.log({"detailContent": "error", "vid": vid, "msg": str(e)})
            return self._skeleton(vid)

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        try:
            url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
                "Referer": self.host + "/"
            }
            r = self.fetch(url, headers=headers, timeout=15)
            if not r or r.status_code != 200:
                self.log({"search": "fetch_failed", "status": r.status_code if r else None})
                return {"list": [], "page": 1}
            html_text = r.text
            self.log({"search": "html_len", "len": len(html_text)})
            items = []
            # 使用与分类页相同的解析逻辑
            pattern = r'<div class="xb3 xl6 xm4 xs6 ul">\s*<div class="item">\s*<div class="thumb">\s*<a[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*data-original="([^"]+)"[^>]*alt="([^"]*)"'
            matches = re.findall(pattern, html_text, re.S)
            self.log({"search": "matches_found", "count": len(matches)})
            for href, pic, title in matches:
                if not href.startswith("http"):
                    href = urljoin(self.host, href)
                items.append({
                    "vod_id": href,
                    "vod_name": html.unescape(title).strip() or "未知标题",
                    "vod_pic": pic,
                    "vod_remarks": ""
                })
            # 如果上面的方法没有匹配到，尝试更宽松的方式
            if not items:
                # 直接从 .title a 提取标题和链接
                for m in re.finditer(r'<div class="title">\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_text, re.S):
                    href = m.group(1).strip()
                    title = html.unescape(re.sub(r"<[^>]+>", "", m.group(2)).strip())
                    if href and title:
                        if not href.startswith("http"):
                            href = urljoin(self.host, href)
                        # 尝试找对应的封面图
                        pic = ""
                        # 在当前位置附近找 data-original
                        pos = m.start()
                        nearby = html_text[max(0, pos-500):pos+500]
                        pic_match = re.search(r'data-original="([^"]+)"', nearby)
                        if pic_match:
                            pic = pic_match.group(1)
                        items.append({
                            "vod_id": href,
                            "vod_name": title,
                            "vod_pic": pic,
                            "vod_remarks": ""
                        })
            self.log({"search": "items_count", "count": len(items)})
            return {"list": items, "page": int(pg)}
        except Exception as e:
            self.log({"search": "exception", "msg": str(e)})
            return {"list": [], "page": 1}

    def _is_media_url(self, url):
        if not url or not str(url).startswith("http"):
            return False
        path = str(url).split("?")[0].split("#")[0].lower()
        media_ext = (".m3u8", ".mp4", ".mkv", ".flv", ".m4v", ".ts", ".m4s")
        return path.endswith(media_ext)

    def _normalize_url(self, raw):
        if not raw:
            return ""
        s = str(raw).strip().strip('"').strip("'")
        s = s.replace("\\/", "/").replace("\\u002f", "/")
        s = html.unescape(s)
        try:
            s = unquote(s)
        except Exception:
            pass
        return s.strip()

    def _extract_play_candidates(self, html_text, page_url):
        bag = []
        if not html_text:
            return bag

        # L2: 播放器变量
        player_vars = ("player_aaaa", "player_data", "player_conf", "playerData", "MacPlayer")
        for var in player_vars:
            for m in re.finditer(re.escape(var) + r'\s*=\s*', html_text):
                brace = html_text.find("{", m.end())
                if brace < 0 or brace - m.end() > 10:
                    continue
                depth = 0
                in_str = False
                esc = False
                quote = ""
                end = brace
                for i in range(brace, len(html_text)):
                    ch = html_text[i]
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
                            end = i
                            break
                if end > brace:
                    json_str = html_text[brace:end + 1]
                    try:
                        data = json.loads(json_str)
                        self._walk_json(data, bag)
                    except Exception:
                        fixed = json_str.replace("\\/", "/")
                        fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
                        try:
                            data = json.loads(fixed)
                            self._walk_json(data, bag)
                        except Exception:
                            pass

        # L3: 内联JSON
        for m in re.finditer(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html_text, re.S):
            try:
                data = json.loads(m.group(1).strip())
                self._walk_json(data, bag)
            except Exception:
                pass

        # L4: 转义还原
        norm_bag = [self._normalize_url(u) for u in bag if u]
        bag = [u for u in norm_bag if u]

        # L5: 全文正则
        patterns = (
            r'https?://[^\s"\'<>()\\]+?\.m3u8[^\s"\'<>()\\]*',
            r'https?://[^\s"\'<>()\\]+?\.mp4[^\s"\'<>()\\]*',
            r'["\']((?:https?:)?\\?/\\?/[^\s"\'<>]+?\.m3u8[^\s"\'<>]*)["\']',
        )
        for p in patterns:
            for hit in re.findall(p, html_text):
                if isinstance(hit, str):
                    bag.append(self._normalize_url(hit))

        seen = set()
        unique = []
        for u in bag:
            if u and u.startswith("http") and u not in seen:
                seen.add(u)
                unique.append(u)
        return unique

    def _walk_json(self, node, bag, depth=0):
        if depth > 6 or node is None:
            return
        url_keys = ("url", "play_url", "playUrl", "video_url", "videoUrl", "src", "source", "m3u8", "hls", "file", "path")
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str) and v:
                    kl = str(k).lower()
                    if any(key in kl for key in url_keys) or self._looks_like_media(v):
                        bag.append(v)
                else:
                    self._walk_json(v, bag, depth + 1)
        elif isinstance(node, list):
            for v in node:
                if isinstance(v, str) and v:
                    if self._looks_like_media(v):
                        bag.append(v)
                else:
                    self._walk_json(v, bag, depth + 1)

    def _looks_like_media(self, s):
        if not s or not isinstance(s, str):
            return False
        s_low = s.lower()
        return ".m3u8" in s_low or ".mp4" in s_low or "playlist.m3u8" in s_low

    def playerContent(self, flag, id, vipFlags):
        ua = self.headers.get("User-Agent", "")
        raw_id = str(id or "").strip()
        if not raw_id:
            return {"parse": 1, "url": "", "header": {"User-Agent": ua}}

        if self._is_media_url(raw_id):
            if ".m3u8" in raw_id.lower() and self.NEED_CLEAN:
                proxy_url = self._m3u8_proxy_url(raw_id)
                return {"parse": 0, "url": proxy_url, "header": {"User-Agent": ua}}
            return {"parse": 0, "url": raw_id, "header": {"User-Agent": ua}}

        if raw_id.startswith("http"):
            page_url = raw_id
        elif raw_id.startswith("/"):
            page_url = urljoin(self.host, raw_id)
        else:
            if "play" in raw_id:
                page_url = urljoin(self.host, raw_id)
            else:
                page_url = f"{self.host}/index.php/vod/play/id/{raw_id}/sid/1/nid/1.html"

        try:
            r = self.fetch(page_url, headers=self.headers, timeout=15)
            if not r or r.status_code != 200:
                return {"parse": 1, "url": page_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

            html_text = r.text
            candidates = self._extract_play_candidates(html_text, page_url)

            cands = []
            for u in candidates:
                if not u.startswith("http"):
                    continue
                if ".m3u8" in u.lower():
                    cands.insert(0, u)
                elif ".mp4" in u.lower():
                    cands.append(u)

            if cands:
                chosen = cands[0]
                self.log({"playerContent": "hit", "url": chosen})
                if ".m3u8" in chosen.lower() and self.NEED_CLEAN:
                    proxy_url = self._m3u8_proxy_url(chosen)
                    return {"parse": 0, "url": proxy_url, "header": {"User-Agent": ua}}
                return {"parse": 0, "url": chosen, "header": {"User-Agent": ua}}

            self.log({"playerContent": "all_layers_miss", "page": page_url})
            return {"parse": 1, "url": page_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

        except Exception as e:
            self.log({"playerContent": "error", "id": raw_id, "msg": str(e)})
            return {"parse": 1, "url": page_url, "header": {"User-Agent": ua, "Referer": self.host + "/"}}

    def _m3u8_proxy_url(self, url):
        if url:
            url = url.replace("\\/", "/")
        return "http://127.0.0.1:9978/proxy?do=py&url=" + quote(str(url or ""), safe="")

    def localProxy(self, param):
        """m3u8 五层广告过滤管线"""
        try:
            # 解析目标 URL
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")
            if target.startswith("url="):
                target = target[4:]
            elif "url=" in target:
                qs = {}
                for part in target.split("&"):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        qs[k] = v
                if "url" in qs:
                    target = qs["url"]
            target = unquote(str(target or ""))
            if not target or not target.startswith(("http://", "https://")):
                return [400, "text/plain", b"invalid url"]

            resp = self.fetch(target, headers=self.headers, timeout=20)
            if not resp or resp.status_code != 200:
                return [502, "text/plain", b"fetch failed"]
            content = getattr(resp, "content", b"") or b""
            if not content and getattr(resp, "text", ""):
                content = resp.text.encode("utf-8", errors="ignore")
            if not content or b"#EXTM3U" not in content[:256]:
                return [200, "application/octet-stream", content]

            # 解析 m3u8 为行列表
            text = content.decode("utf-8", errors="ignore")
            lines = [l.strip() for l in text.replace("\r", "").split("\n") if l.strip()]
            if not lines:
                return [200, "application/vnd.apple.mpegurl", content]

            # 第1层：图片流检测（只打标记，不 return）
            is_img = self._is_fake_image_stream(lines)

            # 第2层：多码率主表透传
            if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
                return self._handle_multi_bitrate(lines, target)

            # 第3-5层：单码率清洗
            cleaned = self._clean_single_bitrate(lines, target, is_img)
            self.log({"localProxy": "filtered", "source": target[:60], "removed": cleaned.get("removed", 0), "kept": cleaned.get("kept", 0)})
            return [200, "application/vnd.apple.mpegurl", cleaned.get("text", "").encode("utf-8")]

        except Exception as e:
            self.log({"localProxy": "error", "msg": str(e)})
            return [500, "text/plain", b"proxy error"]

    def _is_fake_image_stream(self, lines):
        """检测图片流伪装 - 只检测分片扩展名"""
        has_video = False
        has_image = False
        for line in lines:
            if not line or line.startswith("#"):
                continue
            path = line.split("?")[0].split("#")[0].lower()
            if path.endswith((".ts", ".m4s", ".mp4")):
                has_video = True
            elif path.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                has_image = True
        return has_image and not has_video

    def _handle_multi_bitrate(self, lines, source_url):
        """多码率主表透传：子流地址改代理"""
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
        return [200, "application/vnd.apple.mpegurl", "\n".join(out).encode("utf-8")]

    def _clean_single_bitrate(self, lines, source_url, is_img=False):
        """单码率清洗：锚点解析 + 分片过滤 + 标签清理"""
        from collections import Counter

        # 第3层：确定锚点目录
        main_dir = self._resolve_anchor_dir(lines, source_url, is_img)
        self.log({"localProxy": "anchor", "dir": main_dir, "is_img": is_img})

        segments = []
        pending = []
        removed = 0
        kept = 0

        # 第4层：分片过滤
        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media = urljoin(source_url, line)
                media_path = urlparse(media).path
                if media_path.startswith(main_dir):
                    segments.extend(pending)
                    segments.append(media)
                    kept += 1
                else:
                    removed += 1
                    self.log({"localProxy": "ad_filtered", "path": media_path[:60]})
                pending = []
                continue
            if line.startswith("#"):
                segments.append(line)
            else:
                segments.append(urljoin(source_url, line))

        # 第5层：全滤兜底
        if removed > 0 and (kept == 0 or removed > kept):
            self.log({"localProxy": "fallback_triggered", "removed": removed, "kept": kept})
            out = [self._rewrite_uri(line, source_url) for line in lines]
            return {"text": "\n".join(out) + "\n", "removed": removed, "kept": kept, "fallback": True}

        # 冗余标签清理
        noise_tags = ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE")
        out = []
        for line in segments:
            line = self._rewrite_uri(line, source_url)
            if line in noise_tags:
                if not out or out[-1] in noise_tags:
                    continue
            out.append(line)
        while len(out) > 1 and out[-1] in noise_tags:
            out.pop()

        return {"text": "\n".join(out) + "\n", "removed": removed, "kept": kept, "fallback": False}

    def _resolve_anchor_dir(self, lines, source_url, is_img=False):
        """第3层：确定锚点目录"""
        from posixpath import dirname
        base_dir = dirname(urlparse(source_url).path)
        if not base_dir.endswith("/"):
            base_dir += "/"

        # 图片流：改用分片目录众数
        if is_img:
            counter = Counter()
            for line in lines:
                if not line or line.startswith("#"):
                    continue
                p = urlparse(urljoin(source_url, line)).path
                d = dirname(p)
                if d and d != "/":
                    counter[d + "/"] += 1
            if counter:
                return counter.most_common(1)[0][0]
            return base_dir

        # 普通流：KEY URI 目录优先
        for line in lines:
            if not line.startswith("#EXT-X-KEY") or "URI=" not in line:
                continue
            m = re.search(r'URI="([^"]+)"', line)
            if not m:
                continue
            key_uri = m.group(1)
            if not key_uri.startswith("http"):
                key_uri = urljoin(source_url, key_uri)
            key_path = urlparse(key_uri).path
            key_dir = dirname(key_path)
            if key_dir and key_dir != "/":
                return key_dir + "/"
        return base_dir

    def _rewrite_uri(self, line, source_url):
        """重写 URI 为绝对地址"""
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(m):
                uri = m.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)
        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urljoin(source_url, line)
        return line

    def recommendContent(self, ids, pg):
        return {"list": []}

    def destroy(self):
        pass