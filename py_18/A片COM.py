# coding: utf-8
"""
站点信息
主域名: https://xn--a-pt1c.com/
备用域名: 暂无
发布页: 无
内容类型: 成人AV影视
特殊说明: MacCMS系统，播放地址在页面JS中嵌入
最后验证时间: 2026-08-31
来源: 用户提供
m3u8结构摘要: 多码率主表 + AES-128加密，正片目录含日期路径，KEY URI目录优先锚点
"""
import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://xn--a-pt1c.com"
        self.classes = [
            {"type_id": "1", "type_name": "日韓有碼"},
            {"type_id": "2", "type_name": "國產AV"},
            {"type_id": "5", "type_name": "日韓無碼"},
            {"type_id": "6", "type_name": "強姦亂倫"},
            {"type_id": "7", "type_name": "巨乳美乳"},
            {"type_id": "9", "type_name": "制服誘惑"},
            {"type_id": "10", "type_name": "人妻熟女"},
            {"type_id": "11", "type_name": "調教"},
            {"type_id": "13", "type_name": "中文字幕"},
            {"type_id": "17", "type_name": "國產精品"},
            {"type_id": "30", "type_name": "歐美"},
            {"type_id": "35", "type_name": "FC2系列"},
            {"type_id": "36", "type_name": "探花"},
            {"type_id": "38", "type_name": "麻豆傳媒"},
            {"type_id": "44", "type_name": "童顏巨乳"},
            {"type_id": "45", "type_name": "明星淫夢"},
            {"type_id": "48", "type_name": "國產自拍"},
            {"type_id": "51", "type_name": "有碼精品"},
            {"type_id": "53", "type_name": "絕美少女"},
        ]
        self.filters = {
            "1": [],
            "2": [],
            "5": [],
            "6": [],
            "7": [],
            "9": [],
            "10": [],
            "11": [],
            "13": [],
            "17": [],
            "30": [],
            "35": [],
            "36": [],
            "38": [],
            "44": [],
            "45": [],
            "48": [],
            "51": [],
            "53": [],
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
        }

    def getName(self):
        return "A片.com"

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
            resp = self.fetch(self.host, headers=self.headers, timeout=10)
            if not resp or resp.status_code != 200:
                return {"list": []}
            html = resp.text
            items = []
            pattern = r'<div class="col-6 col-sm-4 col-lg-3">.*?<a href="/([^"]+)".*?data-src="([^"]+)".*?alt="([^"]+)".*?<h4 class="title"><a[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches[:20]:
                url_part, pic, alt, title = match
                if url_part:
                    items.append({
                        "vod_id": url_part.replace(".html", ""),
                        "vod_name": title or alt,
                        "vod_pic": urllib.parse.urljoin(self.host, pic) if pic and not pic.startswith("http") else pic,
                        "vod_remarks": "",
                    })
            return {"list": items}
        except Exception as e:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = pg or "1"
            url = f"{self.host}/vodtype/{tid}-{page}.html"
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if not resp or resp.status_code != 200:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            html = resp.text
            items = []
            
            # 使用简单的字符串分割方法提取卡片
            # 先找到所有卡片的开始位置
            start_marker = '<div class="video-img-box mb-e-20">'
            pos = 0
            count = 0
            while True:
                start = html.find(start_marker, pos)
                if start == -1 or count >= 20:
                    break
                # 找卡片结束：下一个卡片开始或 </div></div> 的结束
                end = html.find(start_marker, start + 1)
                if end == -1:
                    end = html.find('</div></div>', start + 1)
                    if end == -1:
                        end = html.find('</div>', start + 1)
                        if end == -1:
                            end = len(html)
                    else:
                        end = end + 13  # 包含 </div></div>
                card_html = html[start:end]
                
                # 提取链接
                href_pos = card_html.find('href="/v/')
                if href_pos == -1:
                    pos = end
                    continue
                href_end = card_html.find('.html', href_pos)
                if href_end == -1:
                    pos = end
                    continue
                vid = card_html[href_pos + 9:href_end]  # 'href="/v/' 后开始
                
                # 提取图片
                ds_pos = card_html.find('data-src="')
                if ds_pos != -1:
                    ds_end = card_html.find('"', ds_pos + 11)
                    pic = card_html[ds_pos + 11:ds_end] if ds_end != -1 else ''
                else:
                    pic = ''
                
                # 提取标题
                title_pos = card_html.find('<h4 class="title">')
                if title_pos != -1:
                    a_pos = card_html.find('<a', title_pos)
                    if a_pos != -1:
                        a_end = card_html.find('</a>', a_pos)
                        if a_end != -1:
                            gt_pos = card_html.find('>', a_pos)
                            if gt_pos != -1 and gt_pos < a_end:
                                title = card_html[gt_pos + 1:a_end].strip()
                            else:
                                title = ''
                        else:
                            title = ''
                    else:
                        title = ''
                else:
                    title = ''
                
                if vid and title:
                    items.append({
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": urllib.parse.urljoin(self.host, pic) if pic and not pic.startswith("http") else pic,
                        "vod_remarks": "",
                    })
                pos = end
                count += 1
            
            # 提取总页数
            pagecount = 1
            last_marker = '最後一頁 »'
            last_pos = html.find(last_marker)
            if last_pos != -1:
                # 往前找 href
                href_pos = html.rfind('href="', 0, last_pos)
                if href_pos != -1:
                    href_end = html.find('"', href_pos + 6)
                    if href_end != -1:
                        href = html[href_pos + 6:href_end]
                        import re
                        match = re.search(r'/vodtype/' + tid + r'-(\d+)\.html', href)
                        if match:
                            pagecount = int(match.group(1))
            
            return {
                "list": items,
                "page": int(page),
                "pagecount": pagecount if pagecount > 1 else 1,
                "limit": 20,
                "total": pagecount * 20
            }
        except Exception as e:
            return {"list": [], "page": int(page or 1), "pagecount": 1, "limit": 20, "total": 0}
    def detailContent(self, ids):
        try:
            vod_id = ids[0] if ids else ""
            if not vod_id:
                return {"list": []}
            url = f"{self.host}/v/{vod_id}.html"
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if not resp or resp.status_code != 200:
                return {"list": []}
            html = resp.text
            # 提取标题
            title_match = re.search(r'<h1>([^<]+)</h1>', html)
            title = title_match.group(1) if title_match else ""
            # 提取图片
            pic_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            pic = pic_match.group(1) if pic_match else ""
            # 提取播放地址
            play_match = re.search(r'var player_aaaa=\{"flag":"play","encrypt":0,"trysee":0,"points":0,"link":"[^"]*","link_next":"[^"]*","link_pre":"[^"]*","url":"([^"]+)","url_next":"","from":"([^"]+)","server":"[^"]*","note":"","id":"[^"]*","sid":\d+,"nid":\d+\}', html)
            play_url = play_match.group(1) if play_match else ""
            play_from = play_match.group(2) if play_match else "播放"
            if not play_url:
                return {"list": []}
            # 构造多线路（此站只有一条线路，仍按标准格式）
            vod = {
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": "",
                "vod_content": "",
                "vod_play_from": play_from,
                "vod_play_url": f"正片${play_url}",
            }
            return {"list": [vod]}
        except Exception as e:
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        try:
            import time
            # 模拟人类操作间隔
            url = f"{self.host}/s.html?wd={urllib.parse.quote(key)}"
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if not resp or resp.status_code != 200:
                return {"list": [], "page": int(pg)}
            
            html = resp.text
            # 检测是否触发了频率限制
            if "請不要頻繁操作" in html or "搜索時間間隔為5秒" in html:
                return {"list": [], "page": int(pg)}
            
            items = []
            # 使用与 categoryContent 相同的提取逻辑
            start_marker = '<div class="video-img-box mb-e-20">'
            pos = 0
            count = 0
            while True:
                start = html.find(start_marker, pos)
                if start == -1 or count >= 20:
                    break
                end = html.find(start_marker, start + 1)
                if end == -1:
                    end = html.find('</div></div>', start + 1)
                    if end == -1:
                        end = html.find('</div>', start + 1)
                        if end == -1:
                            end = len(html)
                        else:
                            end = end + 6
                    else:
                        end = end + 13
                card_html = html[start:end]
                
                href_pos = card_html.find('href="/v/')
                if href_pos == -1:
                    pos = end
                    continue
                href_end = card_html.find('.html', href_pos)
                if href_end == -1:
                    pos = end
                    continue
                vid = card_html[href_pos + 9:href_end]
                
                ds_pos = card_html.find('data-src="')
                if ds_pos != -1:
                    ds_end = card_html.find('"', ds_pos + 11)
                    pic = card_html[ds_pos + 11:ds_end] if ds_end != -1 else ''
                else:
                    pic = ''
                
                title_pos = card_html.find('<h4 class="title">')
                if title_pos != -1:
                    a_pos = card_html.find('<a', title_pos)
                    if a_pos != -1:
                        a_end = card_html.find('</a>', a_pos)
                        if a_end != -1:
                            gt_pos = card_html.find('>', a_pos)
                            if gt_pos != -1 and gt_pos < a_end:
                                title = card_html[gt_pos + 1:a_end].strip()
                            else:
                                title = ''
                        else:
                            title = ''
                    else:
                        title = ''
                else:
                    title = ''
                
                if vid and title:
                    items.append({
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": urllib.parse.urljoin(self.host, pic) if pic and not pic.startswith("http") else pic,
                        "vod_remarks": "",
                    })
                pos = end
                count += 1
            
            return {"list": items, "page": int(pg)}
        except Exception as e:
            return {"list": [], "page": int(pg)}
    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        play_url = str(id).strip()
        if play_url.startswith("http") and ".m3u8" in play_url:
            # 走代理过滤广告
            return {
                "parse": 0,
                "url": self._m3u8_proxy_url(play_url),
                "header": {"User-Agent": self.headers.get("User-Agent", "")},
            }
        return {"parse": 1, "url": play_url, "header": self.headers}

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

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

    def _is_fake_image_stream(self, text, source_url):
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
        import posixpath
        parsed = urllib.parse.urlparse(source_url)
        main_dir = posixpath.dirname(parsed.path)
        if not main_dir.endswith("/"):
            main_dir += "/"
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
        return main_dir

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

    def _clean_m3u8_multi(self, lines, source_url):
        out = []
        for line in lines:
            if line.startswith("#"):
                out.append(line)
                continue
            child = urllib.parse.urljoin(source_url, line)
            if ".m3u8" in child.lower():
                out.append(self._m3u8_proxy_url(child))
            else:
                out.append(child)
        return "\n".join(out) + "\n"

    def _clean_m3u8(self, text, source_url):
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"
        if self._is_fake_image_stream(text, source_url):
            restored = text
            for ext in (".png", ".jpeg", ".jpg", ".webp"):
                restored = restored.replace(ext, ".ts")
            return restored
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            return self._clean_m3u8_multi(lines, source_url)
        main_dir = self._resolve_main_dir(lines, source_url)
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)
        if kept == 0 and removed > 0:
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"
        if removed:
            pass
        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

    def recommendContent(self, ids, pg):
        return {"list": []}

    def destroy(self):
        pass