# coding: utf-8
# 蜘蛛精 影视爬虫 - MacCMS 标准站
# 站点: https://ghy.zzj8.help

import re
import json
import urllib.parse
import posixpath

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://ghy.zzj8.help"
        self.site_name = "蜘蛛精"
        self.classes = [
            {"type_id": "1", "type_name": "国产自拍"},
            {"type_id": "20", "type_name": "制服丝袜"},
            {"type_id": "21", "type_name": "强奸乱伦"},
            {"type_id": "22", "type_name": "人妻熟女"},
            {"type_id": "23", "type_name": "主播自拍"},
            {"type_id": "24", "type_name": "日韩精品"},
            {"type_id": "25", "type_name": "欧美风情"},
            {"type_id": "26", "type_name": "卡通动漫"},
            {"type_id": "27", "type_name": "经典伦理"},
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
        }

    def getName(self):
        return "蜘蛛精"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""
        # 初始化时获取Cookie
        self._init_cookies()
    
    def _init_cookies(self):
        """初始化Cookie，访问首页获取session"""
        try:
            resp = self.fetch(self.host + "/cn/home/web/", headers=self.headers, timeout=10)
            if resp and hasattr(resp, "cookies"):
                self.cookies = resp.cookies
            else:
                self.cookies = {}
        except:
            self.cookies = {}

    def destroy(self):
        pass

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html(self.host + "/cn/home/web/")
        items = self._parse_video_list(html)
        return {"list": items[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        pg = str(pg) if pg else "1"
        url = f"{self.host}/cn/home/web/index.php/vod/type/id/{tid}/page/{pg}.html"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        page_count = self._parse_page_count(html)
        return {
            "list": items,
            "page": int(pg),
            "pagecount": page_count,
            "limit": 20,
            "total": page_count * 20,
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        if isinstance(ids, list):
            vid = str(ids[0])
        else:
            vid = str(ids)

        detail_url = f"{self.host}/cn/home/web/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        html = self._fetch_html(detail_url)

        title = self._extract_title(html) or f"视频{vid}"
        pic = self._extract_pic(html) or ""
        play_url = self._extract_m3u8_from_html(html)

        if play_url:
            vod = {
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_play_from": "播放",
                "vod_play_url": f"播放${play_url}",
            }
        else:
            vod = {
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_play_from": "播放",
                "vod_play_url": f"播放${detail_url}",
            }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        pg = str(pg) if pg else "1"
        url = f"{self.host}/cn/home/web/index.php/vod/search.html?wd={urllib.parse.quote(key)}&page={pg}"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        return {"list": items, "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        """播放 - 返回代理地址，由 localProxy 处理 m3u8"""
        if not id:
            return {"parse": 1, "url": ""}

        # 如果是 m3u8 URL，直接走代理（不预验证）
        if id.startswith("http") and ".m3u8" in id:
            proxy_url = self._m3u8_proxy_url(id)
            return {
                "parse": 0,
                "url": proxy_url,
                "header": {"User-Agent": self.headers.get("User-Agent", "")}
            }

        # 如果是 mp4 直链
        if id.startswith("http") and ".mp4" in id:
            return {
                "parse": 0,
                "url": id,
                "header": {
                    "User-Agent": self.headers.get("User-Agent", ""),
                    "Referer": self.host + "/",
                }
            }

        # 如果是 vod_id，从详情页提取 m3u8
        if isinstance(id, str) and id.isdigit():
            detail_url = f"{self.host}/cn/home/web/index.php/vod/play/id/{id}/sid/1/nid/1.html"
            html = self._fetch_html(detail_url)
            play_url = self._extract_m3u8_from_html(html)
            if play_url:
                proxy_url = self._m3u8_proxy_url(play_url)
                return {
                    "parse": 0,
                    "url": proxy_url,
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }

        # 降级到 WebView 嗅探
        fallback_url = id if id.startswith("http") else f"{self.host}/cn/home/web/index.php/vod/play/id/{id}/sid/1/nid/1.html"
        return {
            "parse": 1,
            "url": fallback_url,
            "header": {
                "User-Agent": self.headers.get("User-Agent", ""),
                "Referer": self.host + "/",
            }
        }

    def recommendContent(self, ids, pg):
        if not ids:
            return {"list": []}
        vid = ids[0] if isinstance(ids, list) else ids
        url = f"{self.host}/cn/home/web/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        # 从 "猜你喜欢" 区域提取
        pattern = r'猜你喜欢</h1>\s*<ul>(.*?)</ul>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            items = self._parse_video_list(match.group(1))
            return {"list": items[:10]}
        return {"list": []}

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if url:
            url = str(url).replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def localProxy(self, param):
        try:
            from urllib.parse import unquote
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")

            if target.startswith("url="):
                target = target[4:]
            target = unquote(str(target or ""))

            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            # 直接使用 self.headers，与 AV居委会 一致
            resp = self.fetch(target, headers=self.headers, timeout=15)
            if not resp:
                # 获取失败，返回302让播放器直接尝试（播放器会携带正确的Referer和Cookie）
                return [302, "text/plain", b"", {"Location": target}]

            content = getattr(resp, "content", b"") or b""
            if not content and hasattr(resp, "text") and resp.text:
                content = resp.text.encode("utf-8", errors="ignore")

            if not content:
                return [502, "text/plain", b"empty content"]

            text = content.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]

            cleaned = self._clean_m3u8(text, target)
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

        except Exception as e:
            error_msg = f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")
            return [500, "text/plain", error_msg]

    def _clean_m3u8(self, text, source_url):
        """清洗 m3u8 - 使用m3u8 URL目录作为正片锚点"""
        import re
        from urllib.parse import urljoin, urlparse, quote
        
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # ---- 多码率主表透传 ----
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

        # ---- 正片目录锚点：使用 m3u8 URL 的目录 ----
        parsed = urlparse(source_url)
        main_dir = parsed.path.rsplit("/", 1)[0]
        if not main_dir.endswith("/"):
            main_dir += "/"
        
        self.log(f"蜘蛛精 m3u8正片目录: {main_dir}")

        # ---- 分片过滤（成对处理） ----
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
                # 检查分片路径是否以正片目录开头
                if media_path.startswith(main_dir):
                    segments.extend(pending)
                    segments.append(media_url)
                    kept += 1
                else:
                    removed += 1
                    self.log(f"蜘蛛精 过滤广告分片: {media_path}")
                pending = []
                continue
            if line.startswith("#"):
                segments.append(line)
            else:
                segments.append(urljoin(source_url, line))

        # ---- 全滤兜底 ----
        if kept == 0 and removed > 0:
            self.log(f"蜘蛛精 广告过滤命中全部分片({removed}个)，回退为不过滤模式")
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        if removed > 0:
            self.log(f"蜘蛛精 m3u8已过滤广告分片: {removed}个，保留正片: {kept}个")

        # ---- 冗余标签清理 ----
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

    def _fetch_html(self, url, params=None):
        full_url = url
        if params:
            if "?" in url:
                full_url = url + "&" + urllib.parse.urlencode(params)
            else:
                full_url = url + "?" + urllib.parse.urlencode(params)
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": self.host + "/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Upgrade-Insecure-Requests": "1",
            }
            # 如果有cookies，添加到请求中
            if hasattr(self, 'cookies') and self.cookies:
                # 将cookies转换为字符串格式
                cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
                headers["Cookie"] = cookie_str
            
            resp = self.fetch(full_url, headers=headers, timeout=15)
            if resp and hasattr(resp, "status_code") and resp.status_code == 200:
                return resp.text
            if resp and hasattr(resp, "text"):
                return resp.text
        except:
            pass
        return ""

    def _parse_video_list(self, html):
        items = []
        if not html:
            return items

        # 先找所有视频条目容器
        # 使用更稳健的方式：先找到所有 li.p1，再逐一解析
        import re
        
        # 方法1：直接匹配整个 li 块
        li_pattern = r'<li[^>]*class="[^"]*p1[^"]*"[^>]*>(.*?)</li>'
        li_blocks = re.findall(li_pattern, html, re.DOTALL)

        for block in li_blocks:
            # 提取 vod_id
            id_match = re.search(r'/id/(\d+)/', block)
            if not id_match:
                continue
            vid = id_match.group(1)

            # 提取标题
            title_match = re.search(r'title="([^"]*)"', block)
            title = title_match.group(1).strip() if title_match else "视频"

            # 提取封面图 - 优先 data-original，其次 src
            pic = ""
            img_match = re.search(r'data-original="([^"]+)"', block)
            if img_match:
                pic = img_match.group(1)
            else:
                img_match = re.search(r'src="([^"]+)"', block)
                if img_match:
                    pic = img_match.group(1)

            # 提取备注 - 所有 p.actor
            remarks = []
            for p in re.findall(r'<p[^>]*class="[^"]*actor[^"]*"[^>]*>([^<]*)</p>', block):
                text = p.strip()
                if text and text not in ["播放次", "1970-01-01", ""]:
                    remarks.append(text)
            remark = " ".join(remarks) if remarks else ""

            items.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark,
            })

        if items:
            return items

        # 备用方法
        pattern2 = r'<a[^>]*href="[^"]*/id/(\d+)/[^"]*"[^>]*title="([^"]*)"[^>]*>.*?<img[^>]*(?:data-original="([^"]+)"|src="([^"]+))"'
        matches2 = re.findall(pattern2, html, re.DOTALL)
        for match in matches2:
            vid = match[0]
            title = match[1].strip() if match[1] else "视频"
            pic = match[2] or match[3] or ""
            items.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": "",
            })

        return items

    def _parse_page_count(self, html):
        if not html:
            return 1
        pattern = r'<a[^>]*href="[^"]*/page/(\d+)"[^>]*>'
        matches = re.findall(pattern, html)
        if matches:
            nums = [int(n) for n in matches]
            return max(nums) if nums else 1
        pattern2 = r'共(\d+)条数据'
        match2 = re.search(pattern2, html)
        if match2:
            total = int(match2.group(1))
            return (total + 19) // 20
        return 1

    def _extract_title(self, html):
        if not html:
            return None
        pattern = r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h1>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            title = match.group(1).strip()
            # 去除面包屑
            if "»" in title:
                parts = title.split("»")
                title = parts[-1].strip()
            return title
        return None

    def _extract_pic(self, html):
        if not html:
            return None
        pattern = r'<img[^>]*class="[^"]*video-thumb[^"]*"[^>]*src="([^"]+)"'
        match = re.search(pattern, html)
        if match:
            return match.group(1)
        return None

    def _extract_m3u8_from_html(self, html):
        if not html:
            return None
        # 优先解析 player_data JSON
        pattern = r'var\s+player_data\s*=\s*(\{[^;]+\});'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                url = data.get("url", "")
                if url and url.startswith("http"):
                    # 清理转义字符
                    url = url.replace("\\/", "/")
                    return url
            except:
                pass
        # 备用：直接正则提取 url 字段
        pattern2 = r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"'
        match2 = re.search(pattern2, html)
        if match2:
            url = match2.group(1)
            url = url.replace("\\/", "/")
            if url and url.startswith("http"):
                return url
        # 备用：直接匹配 m3u8 URL
        pattern3 = r'https?://[^"\']+\.m3u8[^"\']*'
        match3 = re.search(pattern3, html)
        if match3:
            url = match3.group(0)
            url = url.replace("\\/", "/")
            if url and url.startswith("http"):
                return url
        return None
