# coding: utf-8
"""
站点信息：
主域名：https://www.buhuibania.cfd/
备用域名：https://www.houruxueyun.shop/ (发布页)
内容类型：成人影视聚合站
特殊说明：MacCMS风格，首页分类静态定义，详情页含多线路，m3u8含前置广告（7个分片）
最后验证时间：2026-08-31
来源：https://www.buhuibania.cfd/

m3u8结构摘要：
- 锚点方式：KEY URI 目录优先
- 正片目录：https://tsbfask.com:65/20260713/QoqStegm/2000kb/hls/
- 广告目录：/20260830/i2vAQKIt/1000kb/hls/ (7个分片)
- 广告特征：目录不同 + DISCONTINUITY 标记
"""

import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://www.buhuibania.cfd"
        self.classes = [
            {"type_id": "1", "type_name": "麻豆传媒"},
            {"type_id": "2", "type_name": "欧美盛宴"},
            {"type_id": "3", "type_name": "明星系列"},
            {"type_id": "4", "type_name": "国产精品"},
            {"type_id": "7", "type_name": "三级电影"},
            {"type_id": "8", "type_name": "少女萝莉"},
            {"type_id": "9", "type_name": "高清无码"},
            {"type_id": "10", "type_name": "动漫系列"},
            {"type_id": "11", "type_name": "网红事件"},
            {"type_id": "12", "type_name": "国产主播"},
        ]
        self.filters = {
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "7": [],
            "8": [],
            "9": [],
            "10": [],
            "11": [],
            "12": [],
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
        }

    def getName(self):
        return "快活空间"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """从首页提取推荐列表"""
        url = self.host + "/"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if not resp or resp.status_code != 200:
            return {"list": []}
        html = resp.text
        items = []
        # 首页推荐视频结构：<li><a class="thumbnail" href="/index.php/vod/detail/id/xxx.html">
        pattern = r'<a class="thumbnail" href="([^"]+?)".*?<img src="([^"]+?)".*?alt="([^"]+?)"'
        matches = re.findall(pattern, html, re.DOTALL)
        for href, pic, title in matches:
            vid = self._extract_id_from_url(href)
            if vid:
                items.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": pic.strip(),
                    "vod_remarks": "",
                })
            if len(items) >= 20:
                break
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if not resp or resp.status_code != 200:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
        html = resp.text
        items = []
        # 列表页结构
        pattern = r'<a class="thumbnail" href="([^"]+?)".*?<img src="([^"]+?)".*?alt="([^"]+?)"'
        matches = re.findall(pattern, html, re.DOTALL)
        for href, pic, title in matches:
            vid = self._extract_id_from_url(href)
            if vid:
                # 提取备注（如"麻豆传媒 - 2026-07-30"）
                remark = ""
                remark_pattern = r'<p>([^<]+)</p>'
                # 简化处理：从上下文提取
                items.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": pic.strip(),
                    "vod_remarks": remark,
                })
        # 提取分页信息
        pagecount = 1
        total = 0
        # 从"共X条数据,当前Y/Z页"提取
        page_info = re.search(r'共(\d+)条数据,当前(\d+)/(\d+)页', html)
        if page_info:
            total = int(page_info.group(1))
            pagecount = int(page_info.group(3))
        return {
            "list": items,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 20,
            "total": total,
        }

    def detailContent(self, ids):
        import html
        vid = str(ids[0]) if ids else ""
        if not vid:
            return {"list": []}
        url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if not resp or resp.status_code != 200:
            return {"list": []}
        html_content = resp.text
        # 提取标题 - 多种方式兜底
        title = ""
        # 方式1：从 <title> 提取，去掉站点后缀
        title_match = re.search(r'<title>([^<]+)</title>', html_content)
        if title_match:
            raw_title = title_match.group(1).strip()
            # 去掉 "快活空间" 相关后缀
            title = re.sub(r'[_-]快活空间.*$', '', raw_title).strip()
        # 方式2：从 <h1> 或 detail-title 类提取
        if not title:
            h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
            if h1_match:
                title = h1_match.group(1).strip()
        # 方式3：从 breadcrumbs 或页面中提取
        if not title:
            crumb_match = re.search(r'<span[^>]*>([^<]+)</span>', html_content)
            if crumb_match:
                title = crumb_match.group(1).strip()
        title = html.unescape(title)
        # 提取封面
        pic = ""
        pic_match = re.search(r'<img[^>]+src="([^"]+)"[^>]*alt="[^"]*"', html_content)
        if pic_match:
            pic = pic_match.group(1)
        # 提取描述（HTML实体解码）
        content = ""
        content_match = re.search(r'<meta name="description" content="([^"]+)"', html_content)
        if content_match:
            content = html.unescape(content_match.group(1))
        # 提取播放地址 - 从 player_aaaa 变量获取
        play_from = ""
        play_url = ""
        player_match = re.search(r'var player_aaaa=\s*({[^}]+})', html_content)
        if player_match:
            try:
                data = json.loads(player_match.group(1))
                if data.get("url"):
                    play_from = "播放"
                    play_url = f"第1集${vid}|1|1"
            except:
                pass
        # 如果没找到player_aaaa，尝试从播放列表提取
        if not play_url:
            play_list_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
            play_matches = re.findall(play_list_pattern, html_content)
            urls = []
            for href, label in play_matches:
                if "vod/play" in href:
                    play_id = self._extract_play_id_from_url(href)
                    if play_id:
                        urls.append(f"线路${play_id}")
            if urls:
                play_from = "播放"
                play_url = "#".join(urls)
        # 如果仍无播放地址，尝试从页面中直接提取 m3u8
        if not play_url:
            m3u8_match = re.search(r'url":"(https?://[^"]+\.m3u8[^"]*)"', html_content)
            if m3u8_match:
                play_from = "播放"
                play_url = f"直链${vid}|0|0"
        # 如果标题仍为空，从描述中截取
        if not title and content:
            title = content[:30]
        vod = {
            "vod_id": vid,
            "vod_name": title or "视频",
            "vod_pic": pic,
            "vod_remarks": "",
            "vod_content": content,
            "vod_actor": "",
            "vod_director": "",
            "vod_play_from": play_from,
            "vod_play_url": play_url,
        }
        return {"list": [vod]}
    def searchContent(self, key, quick, pg="1"):
        url = f"{self.host}/index.php/vod/search.html?wd={urllib.parse.quote(str(key))}&page={pg}"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if not resp or resp.status_code != 200:
            return {"list": [], "page": int(pg)}
        html = resp.text
        items = []
        pattern = r'<a class="thumbnail" href="([^"]+?)".*?<img src="([^"]+?)".*?alt="([^"]+?)"'
        matches = re.findall(pattern, html, re.DOTALL)
        for href, pic, title in matches:
            vid = self._extract_id_from_url(href)
            if vid:
                items.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": pic.strip(),
                    "vod_remarks": "",
                })
        return {"list": items, "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        play_id = str(id).strip()
        # 如果播放ID包含 | 分隔符，解析为 vid|sid|nid 或 vid|0|0（直链）
        if "|" in play_id:
            parts = play_id.split("|")
            if len(parts) >= 2:
                vid = parts[0]
                sid = parts[1] if len(parts) >= 2 else "1"
                nid = parts[2] if len(parts) >= 3 else "1"
                # 如果是直链模式 (sid=0, nid=0)，尝试直接获取 m3u8
                if sid == "0" and nid == "0":
                    # 从详情页直接提取 m3u8
                    detail_url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
                    resp = self.fetch(detail_url, headers=self.headers, timeout=10)
                    if resp and resp.status_code == 200:
                        html = resp.text
                        m3u8_match = re.search(r'url":"(https?://[^"]+\.m3u8[^"]*)"', html)
                        if m3u8_match:
                            m3u8_url = m3u8_match.group(1)
                            return {
                                "parse": 0,
                                "url": self._m3u8_proxy_url(m3u8_url),
                                "header": {"User-Agent": self.headers.get("User-Agent", "")},
                            }
                # 正常播放模式：构造播放页URL
                play_url = f"/index.php/vod/play/id/{vid}/sid/{sid}/nid/{nid}.html"
                full_url = self.host + play_url
                resp = self.fetch(full_url, headers=self.headers, timeout=10)
                if resp and resp.status_code == 200:
                    html = resp.text
                    player_match = re.search(r'var player_aaaa=\s*({[^}]+})', html)
                    if player_match:
                        try:
                            data = json.loads(player_match.group(1))
                            m3u8_url = data.get("url", "")
                            if m3u8_url and m3u8_url.startswith("http") and ".m3u8" in m3u8_url:
                                return {
                                    "parse": 0,
                                    "url": self._m3u8_proxy_url(m3u8_url),
                                    "header": {"User-Agent": self.headers.get("User-Agent", "")},
                                }
                        except:
                            pass
                return {"parse": 1, "url": full_url, "header": self.headers}
        # 如果是直接m3u8地址
        if play_id.startswith("http") and ".m3u8" in play_id:
            return {
                "parse": 0,
                "url": self._m3u8_proxy_url(play_id),
                "header": {"User-Agent": self.headers.get("User-Agent", "")},
            }
        # 如果id中只包含数字（纯vid），尝试获取直链
        if play_id.isdigit():
            detail_url = f"{self.host}/index.php/vod/detail/id/{play_id}.html"
            resp = self.fetch(detail_url, headers=self.headers, timeout=10)
            if resp and resp.status_code == 200:
                html = resp.text
                m3u8_match = re.search(r'url":"(https?://[^"]+\.m3u8[^"]*)"', html)
                if m3u8_match:
                    m3u8_url = m3u8_match.group(1)
                    return {
                        "parse": 0,
                        "url": self._m3u8_proxy_url(m3u8_url),
                        "header": {"User-Agent": self.headers.get("User-Agent", "")},
                    }
        # 降级嗅探
        return {"parse": 1, "url": play_id, "header": self.headers}
    def _m3u8_proxy_url(self, url):
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def localProxy(self, param):
        """m3u8 本地代理 + 广告分片过滤（五层管线）"""
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

            # 非 m3u8 直接透传
            return [200, "application/octet-stream", content]
        except Exception as e:
            return [500, "text/plain", f"localProxy error: {e}".encode("utf-8", errors="ignore")]

    def _clean_m3u8(self, text, source_url):
        """清洗 m3u8：五层管线"""
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 第1层：图片流伪装检测
        if self._is_fake_image_stream(text, source_url):
            restored = text
            for ext in (".png", ".jpeg", ".jpg", ".webp"):
                restored = restored.replace(ext, ".ts")
            self.log("检测到图片流伪装，已还原扩展名 -> .ts，跳过广告过滤")
            return restored

        # 第2层：多码率主表处理
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            return self._clean_m3u8_multi(lines, source_url)

        # 第3层：正片目录锚点
        main_dir = self._resolve_main_dir(lines, source_url)

        # 第4层：分片过滤
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)

        # 第5层：全滤兜底
        if kept == 0 and removed > 0:
            self.log(f"广告过滤命中全部分片({removed}个)，判定锚点失效，回退为不过滤模式")
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        if removed:
            self.log(f"m3u8已过滤广告分片: {removed}个，保留正片: {kept}个")

        # 第5层：冗余标签清理
        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

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

    def _clean_m3u8_multi(self, lines, source_url):
        """多码率主表透传"""
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

    def _resolve_main_dir(self, lines, source_url):
        """确定正片目录锚点：KEY URI 目录优先"""
        import posixpath
        parsed = urllib.parse.urlparse(source_url)
        main_dir = posixpath.dirname(parsed.path)
        if not main_dir.endswith("/"):
            main_dir += "/"
        # 优先以 KEY URI 目录为锚点
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
        """分片过滤：保留正片目录前缀匹配的分片"""
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
        """冗余标签清理 + URI补全"""
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
        """重写 m3u8 标签中的 URI 和分片地址"""
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

    def _extract_id_from_url(self, url):
        """从详情链接中提取视频ID"""
        match = re.search(r'/vod/detail/id/(\d+)\.html', url)
        if match:
            return match.group(1)
        return None

    def _extract_play_id_from_url(self, url):
        """从播放链接中提取播放ID"""
        match = re.search(r'/vod/play/id/(\d+)/sid/(\d+)/nid/(\d+)\.html', url)
        if match:
            return f"{match.group(1)}|{match.group(2)}|{match.group(3)}"
        return url

    def recommendContent(self, ids, pg):
        """相关推荐"""
        return {"list": []}

    def destroy(self):
        pass