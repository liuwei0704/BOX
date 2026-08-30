# coding: utf-8
"""
站点: AI成人短剧 (AI成人短剧)
域名: https://xn--7nrw08b95r.aicrss4.sbs/
备用域名: https://ai.aicrss.cc
类型: MacCMS 标准影视站 (成人内容)
特性: 分类列表、多线路、m3u8广告注入(ppvod-ad-injected)
m3u8结构: 主表→子流→分片，前9个为广告分片，通过 #EXT-X-DISCONTINUITY 分割
锚点方式: KEY URI 目录优先 (有 #EXT-X-KEY 标签)
广告目录特征: 前9个分片路径含 /20260731/UTxI1Mxv/9567kb/hls/，后续分片为相对路径
最后验证: 2026-08-31
来源: 用户提供
"""
import re
import json
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://xn--7nrw08b95r.aicrss4.sbs"
        self.site_name = "AI成人短剧"
        # 分类配置 - 从首页提取
        self.classes = [
            {"type_id": "20", "type_name": "视频资源"},
            {"type_id": "82", "type_name": "AI视频"},
            {"type_id": "23", "type_name": "精品推荐"},
            {"type_id": "24", "type_name": "国产色情"},
            {"type_id": "25", "type_name": "主播直播"},
            {"type_id": "26", "type_name": "亚洲无码"},
            {"type_id": "27", "type_name": "亚洲有码"},
            {"type_id": "28", "type_name": "中文字幕"},
            {"type_id": "29", "type_name": "巨乳美乳"},
            {"type_id": "30", "type_name": "人妻熟女"},
            {"type_id": "31", "type_name": "强奸乱伦"},
            {"type_id": "32", "type_name": "欧美精品"},
            {"type_id": "33", "type_name": "萝莉少女"},
            {"type_id": "34", "type_name": "伦理三级"},
            {"type_id": "35", "type_name": "成人动漫"},
            {"type_id": "36", "type_name": "自拍偷拍"},
            {"type_id": "37", "type_name": "制服丝袜"},
            {"type_id": "38", "type_name": "口交颜射"},
            {"type_id": "39", "type_name": "日本精品"},
            {"type_id": "40", "type_name": "Cosplay"},
            {"type_id": "41", "type_name": "素人自拍"},
            {"type_id": "42", "type_name": "台湾辣妹"},
            {"type_id": "43", "type_name": "韩国御姐"},
            {"type_id": "44", "type_name": "唯美港姐"},
            {"type_id": "45", "type_name": "东南亚AV"},
            {"type_id": "46", "type_name": "欺辱凌辱"},
            {"type_id": "47", "type_name": "剧情介绍"},
            {"type_id": "48", "type_name": "多人多P"},
            {"type_id": "49", "type_name": "91探花"},
            {"type_id": "50", "type_name": "网红流出"},
            {"type_id": "51", "type_name": "野外露出"},
            {"type_id": "52", "type_name": "古装扮演"},
            {"type_id": "53", "type_name": "女优系列"},
            {"type_id": "54", "type_name": "可爱学生"},
            {"type_id": "55", "type_name": "风情旗袍"},
            {"type_id": "56", "type_name": "兽耳系列"},
            {"type_id": "57", "type_name": "瑜伽裤"},
            {"type_id": "58", "type_name": "闷骚护士"},
            {"type_id": "59", "type_name": "网曝门"},
            {"type_id": "60", "type_name": "传媒出品"},
            {"type_id": "61", "type_name": "女同性恋"},
            {"type_id": "62", "type_name": "恋腿狂魔"},
            {"type_id": "77", "type_name": "过膝袜"},
            {"type_id": "78", "type_name": "国产乱伦"},
        ]
        # filters - 简化，无复杂筛选
        self.filters = {str(c["type_id"]): [] for c in self.classes}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }

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
        """首页推荐 - 从首页解析"""
        try:
            html = self.fetch(self.host, headers=self.headers, timeout=10).text
            items = self._parse_vod_list(html, self.host)
            return {"list": items[:20] if items else []}
        except Exception as e:
            self.log({"action": "homeVideoContent_error", "error": str(e)})
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        """分类列表"""
        page = int(pg) if pg else 1
        url = f"{self.host}/index.php/vod/type/id/{tid}.html"
        if page > 1:
            url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        try:
            html = self.fetch(url, headers=self.headers, timeout=10).text
            items = self._parse_vod_list(html, self.host)
            # 提取分页信息
            pagecount = self._parse_pagecount(html) or 50
            total = pagecount * 20
            return {
                "list": items,
                "page": page,
                "pagecount": pagecount,
                "limit": 20,
                "total": total
            }
        except Exception as e:
            self.log({"action": "categoryContent_error", "tid": tid, "pg": page, "error": str(e)})
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        """详情页 - 提取多线路播放地址"""
        vid = str(ids[0]) if ids else ""
        if not vid:
            return {"list": []}
        url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
        try:
            html = self.fetch(url, headers=self.headers, timeout=10).text
            vod = self._parse_detail(html, vid)
            return {"list": [vod] if vod else []}
        except Exception as e:
            self.log({"action": "detailContent_error", "vid": vid, "error": str(e)})
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        """搜索"""
        if not key or not key.strip():
            return {"list": [], "page": 1}
        page = int(pg) if pg else 1
        # MacCMS 搜索 POST
        try:
            data = {"wd": key.strip()}
            url = f"{self.host}/index.php/vod/search.html"
            resp = self.post(url, data=data, headers=self.headers, timeout=10)
            html = resp.text if hasattr(resp, "text") else ""
            items = self._parse_vod_list(html, self.host)
            # 简单分页
            pagecount = self._parse_pagecount(html) or 5
            return {
                "list": items,
                "page": page,
                "pagecount": pagecount,
                "limit": 20,
                "total": pagecount * 20
            }
        except Exception as e:
            self.log({"action": "searchContent_error", "key": key, "error": str(e)})
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def playerContent(self, flag, id, vipFlags):
        """播放地址 - 提取 m3u8 直链"""
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        # id 格式: vid|sid|nid 或 播放页URL
        play_url = str(id).strip()
        if not play_url.startswith("http"):
            # 构建播放页URL
            parts = play_url.split("|")
            if len(parts) >= 3:
                vid, sid, nid = parts[0], parts[1], parts[2]
                play_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/{sid}/nid/{nid}.html"
            else:
                play_url = f"{self.host}/index.php/vod/play/id/{play_url}/sid/1/nid/1.html"
        try:
            html = self.fetch(play_url, headers=self.headers, timeout=10).text
            # 提取 player_aaaa 配置
            m3u8_url = self._extract_m3u8_from_playpage(html)
            if m3u8_url and m3u8_url.startswith("http"):
                # m3u8 走代理过滤广告
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(m3u8_url),
                    "header": {"User-Agent": self.headers["User-Agent"]}
                }
            # 降级嗅探
            return {"parse": 1, "url": play_url, "header": self.headers}
        except Exception as e:
            self.log({"action": "playerContent_error", "id": id, "error": str(e)})
            return {"parse": 1, "url": play_url, "header": self.headers}

    def recommendContent(self, ids, pg="1"):
        """相关推荐"""
        return {"list": []}

    def destroy(self):
        pass

    # ============ 辅助方法 ============

    def _parse_vod_list(self, html, base_url):
        """解析视频列表 - stui-vodlist"""
        items = []
        # 匹配 stui-vodlist__box 结构
        pattern = r'<a[^>]*class="[^"]*stui-vodlist__thumb[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*data-original="([^"]*)"'
        matches = re.findall(pattern, html, re.DOTALL)
        for href, title, pic in matches:
            if not title or not href:
                continue
            vid = self._extract_vid_from_url(href)
            if not vid:
                continue
            # 提取备注 (角标)
            remark = ""
            # 从 pic-text 中提取
            pic_text_pattern = r'<span[^>]*class="[^"]*pic-text[^"]*"[^>]*>.*?<p>播放次数:\s*(\d+)次</p>'
            remark_match = re.search(pic_text_pattern, html[html.find(href):html.find(href)+500] if html.find(href) >= 0 else "")
            if remark_match:
                remark = f"播放 {remark_match.group(1)}次"
            # 也尝试从 pic-text1 提取分类
            items.append({
                "vod_id": vid,
                "vod_name": title.strip(),
                "vod_pic": self._fix_url(pic, base_url),
                "vod_remarks": remark or ""
            })
        # 去重
        seen = set()
        unique = []
        for item in items:
            if item["vod_id"] not in seen:
                seen.add(item["vod_id"])
                unique.append(item)
        return unique[:50]

    def _parse_detail(self, html, vid):
        """解析详情"""
        vod = {
            "vod_id": vid,
            "vod_name": "",
            "vod_pic": "",
            "vod_remarks": "",
            "vod_content": "",
            "vod_play_from": "",
            "vod_play_url": ""
        }
        # 标题
        title_match = re.search(r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>', html)
        if title_match:
            vod["vod_name"] = title_match.group(1).strip()
        # 封面
        pic_match = re.search(r'<img[^>]*class="[^"]*lazyload[^"]*"[^>]*data-original="([^"]+)"', html)
        if pic_match:
            vod["vod_pic"] = self._fix_url(pic_match.group(1), self.host)
        # 简介
        content_match = re.search(r'<span[^>]*class="[^"]*detail-content[^"]*"[^>]*>([^<]*)</span>', html)
        if content_match:
            vod["vod_content"] = content_match.group(1).strip()
        # 多线路提取
        play_from_list = []
        play_url_list = []
        # 匹配线路 tab
        tab_pattern = r'<li><a[^>]*href="#playlist(\d+)"[^>]*>([^<]+)</a></li>'
        tabs = re.findall(tab_pattern, html)
        if not tabs:
            tabs = [("1", "默认")]
        for tab_id, tab_name in tabs:
            playlist_pattern = rf'<div[^>]*id="playlist{tab_id}"[^>]*>.*?<ul[^>]*class="[^"]*stui-content__playlist[^"]*"[^>]*>(.*?)</ul>'
            playlist_match = re.search(playlist_pattern, html, re.DOTALL)
            if playlist_match:
                playlist_html = playlist_match.group(1)
                item_pattern = r'<li[^>]*><a[^>]*href="([^"]+)"[^>]*>([^<]+)</a></li>'
                items = re.findall(item_pattern, playlist_html)
                if items:
                    eps = []
                    for ep_href, ep_name in items:
                        sid_nid = self._extract_sid_nid(ep_href)
                        if sid_nid:
                            # 播放ID包含 vid，确保 playerContent 能获取到 vid
                            eps.append(f"{ep_name.strip()}${vid}|{sid_nid}")
                    if eps:
                        play_from_list.append(tab_name.strip())
                        play_url_list.append("#".join(eps))
        # 如果没提取到，从播放按钮提取
        if not play_url_list:
            play_btn_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>立即播放</a>', html)
            if play_btn_match:
                btn_href = play_btn_match.group(1)
                sid_nid = self._extract_sid_nid(btn_href)
                if sid_nid:
                    play_from_list.append("播放")
                    play_url_list.append(f"播放${vid}|{sid_nid}")
        vod["vod_play_from"] = "$$$".join(play_from_list)
        vod["vod_play_url"] = "$$$".join(play_url_list)
        return vod

    def _extract_m3u8_from_playpage(self, html):
        """从播放页提取 m3u8 URL"""
        # 匹配 player_aaaa 变量
        match = re.search(r'var\s+player_aaaa\s*=\s*({[^}]+})', html)
        if match:
            try:
                data = json.loads(match.group(1))
                return data.get("url", "")
            except:
                pass
        # 也尝试从 iframe 或 script 中提取
        match = re.search(r'url\s*["\']\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html)
        if match:
            return match.group(1)
        return ""

    def _extract_vid_from_url(self, url):
        """从URL提取视频ID"""
        # /index.php/vod/detail/id/123456.html
        match = re.search(r'/id/(\d+)\.html', url)
        if match:
            return match.group(1)
        # /index.php/vod/play/id/123456/sid/1/nid/1.html
        match = re.search(r'/id/(\d+)/', url)
        if match:
            return match.group(1)
        return ""

    def _extract_sid_nid(self, url):
        """提取 sid|nid 格式"""
        match = re.search(r'/sid/(\d+)/nid/(\d+)\.html', url)
        if match:
            return f"{match.group(1)}|{match.group(2)}"
        return ""

    def _parse_pagecount(self, html):
        """解析总页数"""
        # 尝试从分页导航中提取
        # 常见格式: 共X页 或 页数信息在页码列表中
        match = re.search(r'<span[^>]*class="[^"]*pageinfo[^"]*"[^>]*>.*?共(\d+)页', html)
        if match:
            return int(match.group(1))
        match = re.search(r'共(\d+)页', html)
        if match:
            return int(match.group(1))
        # 从页码列表中提取最大页码
        page_numbers = re.findall(r'<a[^>]*href="[^"]*page/(\d+)\.html[^"]*"[^>]*>(\d+)</a>', html)
        if page_numbers:
            max_page = max(int(p) for _, p in page_numbers if p.isdigit())
            return max_page
        # 尝试从 "尾页" 或 "最后一页" 提取
        match = re.search(r'<a[^>]*href="[^"]*page/(\d+)\.html[^"]*"[^>]*>[尾页|最后一页]', html)
        if match:
            return int(match.group(1))
        return 1

    def _fix_url(self, url, base_url):
        """补全 URL"""
        if not url:
            return ""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("//"):
            return "https:" + url
        return urllib.parse.urljoin(base_url, url)

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def localProxy(self, param):
        """m3u8 本地代理 + 五层去广告管线"""
        try:
            # 解析 target
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

            # 检查是否为 m3u8
            if b"#EXTM3U" in content[:256]:
                cleaned = self._clean_m3u8(content.decode("utf-8", errors="ignore"), target)
                return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

            # 非 m3u8 透传
            return [200, "application/octet-stream", content]
        except Exception as e:
            return [500, "text/plain", f"localProxy error: {e}".encode("utf-8", errors="ignore")]

    def _clean_m3u8(self, text, source_url):
        """五层 m3u8 清洗"""
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 第1层: 图片流伪装检测
        if self._is_fake_image_stream(text, source_url):
            restored = text
            for ext in (".png", ".jpeg", ".jpg", ".webp"):
                restored = restored.replace(ext, ".ts")
            self.log("检测到图片流伪装，已还原扩展名 -> .ts，跳过广告过滤")
            return restored

        # 第2层: 多码率主表处理
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            return self._clean_m3u8_multi(lines, source_url)

        # 第3层: 正片目录锚点 (KEY URI 优先)
        main_dir = self._resolve_main_dir(lines, source_url)

        # 第4层: 分片过滤
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)

        # 第5层: 全滤兜底
        if kept == 0 and removed > 0:
            self.log("广告过滤命中全部分片，判定锚点失效，回退为不过滤模式")
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        if removed > 0:
            self.log(f"m3u8已过滤广告分片: {removed}个，保留正片: {kept}个")

        # 第5层: 冗余标签清理
        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

    def _is_fake_image_stream(self, text, source_url):
        """检测图片流伪装"""
        low_url = (source_url or "").lower()
        # 已知图片流服务商特征
        for sig in ("doyinapi", "svip", "imgcdn", "photo", "pic"):
            if sig in low_url:
                return True
        # 分片扩展名检测
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
        """正片目录锚点 - KEY URI 优先"""
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
            key_full = key_uri if key_uri.startswith("http") else urllib.parse.urljoin(source_url, key_uri)
            key_path = urllib.parse.urlparse(key_full).path
            key_dir = posixpath.dirname(key_path)
            if key_dir and key_dir != "/":
                return key_dir + "/"
        return main_dir

    def _filter_segments(self, lines, source_url, main_dir):
        """分片过滤"""
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
        """冗余标签清理"""
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
        """标签 URI 补全"""
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
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