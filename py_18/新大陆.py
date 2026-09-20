# coding: utf-8
import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://cmo.xdl6.yachts"
        self.base_path = "/cn/home/web"
        self.classes = [
            {"type_id": "20", "type_name": "偷拍自拍"},
            {"type_id": "21", "type_name": "人妻熟女"},
            {"type_id": "22", "type_name": "强奸乱伦"},
            {"type_id": "23", "type_name": "制服丝袜"},
            {"type_id": "24", "type_name": "主播名人"},
            {"type_id": "25", "type_name": "自慰同性"},
            {"type_id": "26", "type_name": "变态SM"},
            {"type_id": "27", "type_name": "国产精品"},
            {"type_id": "28", "type_name": "日韩情色"},
            {"type_id": "29", "type_name": "欧美情色"},
            {"type_id": "30", "type_name": "卡通动漫"},
            {"type_id": "31", "type_name": "三级精品"},
        ]
        self.filters = {c["type_id"]: [] for c in self.classes}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        # 广告目录列表
        self.ad_dirs = [
            '5215af9565c8b6ce',
            'UTe7qSJd',
            'UTxI1Mxv',
            'VmnacVi8',
            'a3712cbfc6902686',
            '48a95b6cc2e944fa',
        ]

    def getName(self):
        return "新大陆"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _parse_extend(self, extend):
        if not extend:
            return {}
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            try:
                return json.loads(extend)
            except:
                pass
            result = {}
            for part in extend.split(','):
                if '=' in part:
                    k, v = part.split('=', 1)
                    result[k.strip()] = v.strip()
            return result
        return {}

    def _parse_list_items(self, html, base_url):
        """从HTML解析视频列表"""
        items = []
        # 匹配 .img-list 中的 li
        pattern = r'<li>.*?<a[^>]*href="([^"]+)"[^>]*title="([^"]*)".*?<img[^>]*src="([^"]+)".*?</li>'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            # match 是元组 (url, title, pic)
            url = match[0]
            title = match[1]
            pic = match[2]
            if not url or not title:
                continue
            # 提取vod_id
            vod_id_match = re.search(r'/vod/play/id/(\d+)', url)
            if not vod_id_match:
                continue
            vod_id = vod_id_match.group(1)
            # 从title中去除HTML标签
            title = re.sub(r'<[^>]+>', '', title).strip()
            # 提取角标 (日期) - 从整个匹配中提取
            remark = ""
            full_match = match[0] + match[1] + match[2]
            remark_match = re.search(r'<label[^>]*class="text"[^>]*>([^<]+)</label>', match[3] if len(match) > 3 else "")
            if remark_match:
                remark = remark_match.group(1).strip()
            items.append({
                "vod_id": str(vod_id),
                "vod_name": title,
                "vod_pic": urllib.parse.urljoin(base_url, pic),
                "vod_remarks": remark,
            })
        return items
    def _parse_play_url(self, html):
        """从播放页解析播放地址"""
        # 匹配 player_data.url
        match = re.search(r'player_data\s*=\s*\{[^}]*"url"\s*:\s*"([^"]+)"', html)
        if match:
            url = match.group(1)
            # 移除转义反斜杠（JSON中的 \/ 转义）
            url = url.replace('\\/', '/')
            return url
        return None
    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        # 直接抓取首页推荐
        url = self.host + self.base_path + "/"
        resp = self.fetch(url, headers=self.headers, timeout=15)
        if not resp or resp.status_code != 200:
            return {"list": []}
        html = resp.text
        # 从最近热播和最新上传中提取
        items = []
        # 匹配 img-list 中的 li
        pattern = r'<ul class="img-list">(.*?)</ul>'
        ul_matches = re.findall(pattern, html, re.DOTALL)
        for ul_html in ul_matches:
            items.extend(self._parse_list_items(ul_html, url))
        # 去重
        seen = set()
        unique_items = []
        for item in items:
            if item["vod_id"] not in seen:
                seen.add(item["vod_id"])
                unique_items.append(item)
        return {"list": unique_items[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        page = str(pg or "1")
        if page == "1":
            list_url = f"{self.host}{self.base_path}/index.php/vod/type/id/{tid}.html"
        else:
            list_url = f"{self.host}{self.base_path}/index.php/vod/type/id/{tid}/page/{page}.html"

        resp = self.fetch(list_url, headers=self.headers, timeout=15)
        if not resp or resp.status_code != 200:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

        html = resp.text
        items = []
        # 提取列表
        pattern = r'<ul class="img-list">(.*?)</ul>'
        ul_match = re.search(pattern, html, re.DOTALL)
        if ul_match:
            items = self._parse_list_items(ul_match.group(1), list_url)

        # 提取分页信息
        pagecount = 1
        total = 0
        page_match = re.search(r'共(\d+)条数据,当前(\d+)/(\d+)页', html)
        if page_match:
            total = int(page_match.group(1))
            pagecount = int(page_match.group(3))

        return {
            "list": items,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 20,
            "total": total,
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vod_id = str(ids[0])
        # 直接请求播放页
        url = f"{self.host}{self.base_path}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        resp = self.fetch(url, headers=self.headers, timeout=15)
        if not resp or resp.status_code != 200:
            return {"list": []}
        html = resp.text

        # 提取标题
        title = ""
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            title = title_match.group(1)
            # 去掉后缀
            title = re.sub(r'\s*-\s*在线播放.*', '', title)
            title = re.sub(r'\s*-\s*高清资源.*', '', title)
            title = re.sub(r'\s*-\s*新大陆.*', '', title)

        # 提取封面
        pic = ""
        pic_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*class="[^"]*pic[^"]*"', html)
        if not pic_match:
            pic_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*alt="[^"]*"', html)
        if pic_match:
            pic = urllib.parse.urljoin(url, pic_match.group(1))

        # 提取播放地址
        play_url = self._parse_play_url(html)
        if not play_url:
            return {"list": []}

        # 提取线路名称
        play_from = "ckplayer"
        from_match = re.search(r'"from"\s*:\s*"([^"]+)"', html)
        if from_match:
            play_from = from_match.group(1)

        # 提取集数
        # 检查是否有多个集数
        episodes = []
        ep_pattern = r'<a[^>]*href="[^"]*nid/(\d+).html"[^>]*class="cur"[^>]*>第(\d+)集</a>'
        # 先找当前集
        current_match = re.search(r'<a[^>]*href="[^"]*nid/(\d+).html"[^>]*class="cur"[^>]*>第(\d+)集</a>', html)
        if current_match:
            episodes.append({"nid": current_match.group(1), "title": f"第{current_match.group(2)}集"})
        else:
            episodes.append({"nid": "1", "title": "第1集"})

        # 构建播放URL
        play_urls = []
        for ep in episodes:
            play_urls.append(f"{ep['title']}${play_url}")

        vod = {
            "vod_id": str(vod_id),
            "vod_name": title or "视频",
            "vod_pic": pic or "",
            "vod_remarks": "",
            "vod_content": "",
            "vod_play_from": play_from,
            "vod_play_url": "#".join(play_urls),
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        page = str(pg or "1")
        # 尝试使用 quick 参数
        search_url = f"{self.host}{self.base_path}/index.php/vod/search.html?wd={urllib.parse.quote(key)}"
        if quick:
            search_url += "&quick=1"
        if page != "1":
            search_url += f"&page={page}"

        resp = self.fetch(search_url, headers=self.headers, timeout=15)
        if not resp or resp.status_code != 200:
            return {"list": [], "page": int(page)}

        html = resp.text
        items = []

        # 尝试多种可能的结果列表选择器
        # 1. 标准 .img-list
        pattern = r'<ul class="img-list">(.*?)</ul>'
        ul_match = re.search(pattern, html, re.DOTALL)
        if ul_match:
            items = self._parse_list_items(ul_match.group(1), search_url)
        else:
            # 2. 尝试直接匹配 li 条目
            pattern2 = r'<li>\s*<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]+)".*?</li>'
            matches = re.findall(pattern2, html, re.DOTALL)
            for match in matches:
                url, title, pic = match
                if not url or not title:
                    continue
                vod_id_match = re.search(r'/vod/play/id/(\d+)', url)
                if not vod_id_match:
                    continue
                vod_id = vod_id_match.group(1)
                title = re.sub(r'<[^>]+>', '', title).strip()
                items.append({
                    "vod_id": str(vod_id),
                    "vod_name": title,
                    "vod_pic": urllib.parse.urljoin(search_url, pic),
                    "vod_remarks": "",
                })

        # 如果还是没有结果，尝试从页面提取"没有找到"提示
        if not items and "没有找到" in html or "暂无" in html:
            return {"list": [], "page": int(page)}

        return {"list": items, "page": int(page)}
    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": {}}

        play_url = str(id).strip()
        # 如果已经是m3u8直链
        if play_url.startswith("http") and (".m3u8" in play_url or ".mp4" in play_url):
            if ".m3u8" in play_url:
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(play_url),
                    "header": self.headers,
                }
            return {
                "parse": 0,
                "url": play_url,
                "header": {"User-Agent": self.headers["User-Agent"]},
            }

        # 如果是播放页URL，尝试提取
        if play_url.startswith("/") or not play_url.startswith("http"):
            full_url = urllib.parse.urljoin(self.host, play_url)
            resp = self.fetch(full_url, headers=self.headers, timeout=15)
            if resp and resp.status_code == 200:
                real_url = self._parse_play_url(resp.text)
                if real_url and real_url.startswith("http"):
                    if ".m3u8" in real_url:
                        return {
                            "parse": 0,
                            "url": self._m3u8_proxy_url(real_url),
                            "header": self.headers,
                        }
                    return {
                        "parse": 0,
                        "url": real_url,
                        "header": {"User-Agent": self.headers["User-Agent"]},
                    }

        # 降级
        return {
            "parse": 1,
            "url": play_url,
            "header": {
                "User-Agent": self.headers["User-Agent"],
                "Referer": self.host + "/",
            },
        }

    def _m3u8_proxy_url(self, url):
        # 确保URL被正确编码，避免双重编码
        if not url:
            return ""
        # 如果已经包含代理前缀，直接返回
        if url.startswith("http://127.0.0.1:9978/proxy"):
            return url
        # 使用 urllib.parse.quote 只编码特殊字符
        encoded = urllib.parse.quote(str(url), safe=":/?&=#%")
        return self.getProxyUrl() + "&url=" + encoded
    def _clean_m3u8_single(self, lines, source_url):
        result = []
        pending_extinf = []
        removed = 0

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
                        media_url = urllib.parse.urljoin(source_url, next_line)
                        is_ad = False
                        for ad_dir in self.ad_dirs:
                            if ad_dir in media_url:
                                is_ad = True
                                break
                        if is_ad:
                            removed += 1
                        else:
                            if media_url.endswith('.jpg'):
                                media_url = media_url[:-4] + '.ts'
                            result.extend(pending_extinf)
                            result.append(media_url)
                        i += 1
                        break
                continue

            result.append(line)
            i += 1

        if removed:
            self.log(f"m3u8已过滤广告分片: {removed}个")
        return "\n".join(result) + "\n"

    def _clean_m3u8_multi(self, lines, source_url):
        out = []
        for line in lines:
            if line.startswith("#"):
                out.append(line)
            else:
                child_url = urllib.parse.urljoin(source_url, line)
                out.append(self._m3u8_proxy_url(child_url) if ".m3u8" in child_url.lower() else child_url)
        return "\n".join(out) + "\n"

    def _clean_m3u8(self, text, source_url):
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        is_multi = any(line.startswith("#EXT-X-STREAM-INF") for line in lines)
        if is_multi:
            return self._clean_m3u8_multi(lines, source_url)
        else:
            return self._clean_m3u8_single(lines, source_url)

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

    def localProxy(self, param):
        try:
            target = ""
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            elif isinstance(param, str):
                target = param

            target = urllib.parse.unquote(str(target or ""))

            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": self.host + "/",
                "Accept": "*/*",
            }

            resp = self.fetch(target, headers=headers, timeout=20)
            if not resp:
                return [502, "text/plain", b"fetch failed"]

            content = getattr(resp, "content", b"") or b""
            if not content:
                return [502, "text/plain", b"empty content"]

            if b"#EXTM3U" in content[:256]:
                text = content.decode("utf-8", errors="ignore")
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
            elif target.endswith(".key") or target.endswith(".bin"):
                content_type = "application/octet-stream"

            return [200, content_type, content]

        except Exception as e:
            error_msg = f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")
            return [500, "text/plain", error_msg]

    def recommendContent(self, ids, pg):
        # 从播放页猜你喜欢提取
        if not ids:
            return {"list": []}
        vod_id = str(ids[0])
        url = f"{self.host}{self.base_path}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        resp = self.fetch(url, headers=self.headers, timeout=15)
        if not resp or resp.status_code != 200:
            return {"list": []}
        html = resp.text

        items = []
        # 从 #xihuan 中提取
        pattern = r'<div[^>]*id="xihuan"[^>]*>.*?<ul class="img-list">(.*?)</ul>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            items = self._parse_list_items(match.group(1), url)

        # 如果 #xihuan 没有，尝试从页面其他 img-list 提取
        if not items:
            patterns = [
                r'<ul class="img-list[^"]*">(.*?)</ul>',
                r'<div[^>]*class="[^"]*box_con[^"]*"[^>]*>.*?<ul class="img-list[^"]*">(.*?)</ul>',
            ]
            for pat in patterns:
                matches = re.findall(pat, html, re.DOTALL)
                for match in matches:
                    parsed = self._parse_list_items(match, url)
                    if parsed:
                        items = parsed
                        break
                if items:
                    break

        # 去重，避免与当前视频重复
        if items:
            unique_items = []
            seen = set()
            for item in items:
                if item["vod_id"] != vod_id and item["vod_id"] not in seen:
                    seen.add(item["vod_id"])
                    unique_items.append(item)
            items = unique_items

        return {"list": items[:20]}
    def destroy(self):
        pass