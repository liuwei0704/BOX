# coding: utf-8
"""
站点名称: 莉莉絲 (Enjoy Lamb)
站点域名: https://llstv10.sbs/
站点类型: MacCMS 标准 HTML 影视站
内容类型: 视频 (成人内容)
备注: 播放地址为 m3u8 直链 (encrypt:0)，无需解密
支持 m3u8 广告过滤 (通过 localProxy)
"""
import json
import re
import posixpath
import urllib.parse
from urllib.parse import urljoin, quote, unquote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://llstv10.sbs/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.71 Mobile Safari/537.36",
            "Referer": self.host,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }
        self.classes = [
            {"type_id": "1", "type_name": "人人影視"},
            {"type_id": "2", "type_name": "第二次元"},
            {"type_id": "3", "type_name": "日語教學"},
            {"type_id": "4", "type_name": "主播直播"},
            {"type_id": "21", "type_name": "高質影片"},
        ]
        self.filters = {
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "21": [],
        }
        self.site_name = "莉莉絲"

    def getProxyUrl(self):
        """获取本地代理地址"""
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        """生成 m3u8 代理地址"""
        if not url:
            return ""
        # 先替换反斜杠转义
        url = str(url).replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")
    def _unescape(self, text):
        """将 Unicode 转义序列转换为实际字符"""
        if not text or not isinstance(text, str):
            return text
        try:
            if r'\u' in text:
                return text.encode('utf-8').decode('unicode_escape')
            return text
        except:
            return text

    def _unescape_dict(self, data):
        """递归处理字典/列表中的所有字符串，转译 Unicode"""
        if isinstance(data, dict):
            return {k: self._unescape_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._unescape_dict(v) for v in data]
        elif isinstance(data, str):
            return self._unescape(data)
        else:
            return data

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
        try:
            html = self.fetch(self.host, headers=self.headers).text
            items = self._parse_vod_list(html)
            return {"list": self._unescape_dict(items)}
        except Exception as e:
            self.log("homeVideoContent error: " + str(e))
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = pg or "1"
            if page == "1":
                url = f"{self.host}vtype-{tid}.html"
            else:
                url = f"{self.host}vtype-{tid}-{page}.html"

            html = self.fetch(url, headers=self.headers).text
            items = self._parse_vod_list(html)
            page_info = self._parse_page_info(html)

            result = {
                "list": self._unescape_dict(items),
                "page": page_info.get("page", int(page)),
                "pagecount": page_info.get("pagecount", 1),
                "limit": 20,
                "total": page_info.get("total", 0)
            }
            return result
        except Exception as e:
            self.log("categoryContent error: " + str(e))
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        try:
            vid = ids[0] if ids else ""
            if not vid:
                return {"list": []}

            url = f"{self.host}vplay-{vid}/sid/1/nid/1.html"
            html = self.fetch(url, headers=self.headers).text

            play_data = self._extract_player_data(html)
            play_url = play_data.get("url", "")
            from_name = play_data.get("from", "播放")
            title = play_data.get("vod_name", "未知影片")

            if not play_url:
                m3u8_matches = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
                if m3u8_matches:
                    play_url = m3u8_matches[0]

            if not title or title == "未知影片":
                title_match = re.search(r'<h1>([^<]+)</h1>', html)
                if title_match:
                    title = title_match.group(1).strip()

            # 通过代理播放 m3u8（用于广告过滤）
            if play_url:
                play_url = self._m3u8_proxy_url(play_url)

            vod = {
                "vod_id": vid,
                "vod_name": self._unescape(title),
                "vod_pic": "",
                "vod_remarks": "",
                "vod_content": "",
                "vod_play_from": self._unescape(from_name),
                "vod_play_url": f"正片${play_url}" if play_url else f"正片${vid}"
            }

            try:
                lines = self._extract_all_lines(html, vid)
                if lines and len(lines) > 1:
                    play_from_list = []
                    play_url_list = []
                    for line in lines:
                        play_from_list.append(self._unescape(line.get("name", "未知线路")))
                        play_url_list.append(f"{vid}|{line.get('name', '')}")
                    vod["vod_play_from"] = "$$$".join(play_from_list)
                    vod["vod_play_url"] = "$$$".join(play_url_list)
            except Exception as e:
                pass

            return {"list": [vod]}
        except Exception as e:
            self.log("detailContent error: " + str(e))
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = pg or "1"
            if page == "1":
                url = f"{self.host}search.html?wd={quote(key)}"
            else:
                url = f"{self.host}search/page/{page}/wd/{quote(key)}.html"

            html = self.fetch(url, headers=self.headers).text
            items = self._parse_vod_list(html)
            page_info = self._parse_page_info(html)

            result = {
                "list": self._unescape_dict(items),
                "page": page_info.get("page", int(page)),
                "pagecount": page_info.get("pagecount", 1),
                "limit": 20,
                "total": page_info.get("total", 0)
            }
            return result
        except Exception as e:
            self.log("searchContent error: " + str(e))
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def playerContent(self, flag, id, vipFlags):
        try:
            # 如果 id 本身就是 m3u8 链接，直接返回
            if isinstance(id, str) and (id.startswith("http") and ".m3u8" in id):
                return {
                    "parse": 0,
                    "url": id,
                    "header": {
                        "User-Agent": self.headers["User-Agent"],
                        "Referer": self.host
                    }
                }

            if "|" in str(id):
                vid = str(id).split("|", 1)[0]
            else:
                vid = str(id)

            url = f"{self.host}vplay-{vid}/sid/1/nid/1.html"
            resp = self.fetch(url, headers=self.headers)
            if not resp or not resp.text:
                return {"parse": 1, "url": url, "header": self.headers}

            html = resp.text
            m3u8_matches = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
            if m3u8_matches:
                play_url = self._m3u8_proxy_url(m3u8_matches[0])
                return {
                    "parse": 0,
                    "url": play_url,
                    "header": {
                        "User-Agent": self.headers["User-Agent"],
                        "Referer": self.host
                    }
                }

            return {
                "parse": 1,
                "url": f"{self.host}vplay-{vid}/sid/1/nid/1.html",
                "header": self.headers
            }
        except Exception as e:
            self.log("playerContent error: " + str(e))
            return {"parse": 1, "url": "", "header": self.headers}

    def localProxy(self, param):
        """m3u8 本地代理 + 广告分片过滤"""
        try:
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")

            if target.startswith("url="):
                target = target[4:]
            target = unquote(str(target or ""))

            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            # 请求 m3u8 时携带正确的 Referer
            headers = {
                "User-Agent": self.headers.get("User-Agent", ""),
                "Referer": self.host,
                "Accept": "*/*",
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            }
            res = self.fetch(target, headers=headers, timeout=15)
            if not res:
                return [502, "text/plain", b"fetch failed"]

            content = getattr(res, "content", b"") or b""
            if not content and hasattr(res, "text") and res.text:
                content = res.text.encode("utf-8", errors="ignore")

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
        """清洗 m3u8：过滤广告分片，保留正片"""
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 处理多码率 Master Playlist
        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"

        parsed = urllib.parse.urlparse(source_url)
        source_dir = posixpath.dirname(parsed.path)
        if not source_dir.endswith("/"):
            source_dir += "/"

        # 从 #EXT-X-KEY 提取正片目录（更准确）
        main_dir = source_dir
        for line in lines:
            if line.startswith("#EXT-X-KEY") and "URI=" in line:
                uri_match = re.search(r'URI="([^"]+)"', line)
                if uri_match:
                    key_path = uri_match.group(1)
                    if not key_path.startswith("http"):
                        key_dir = posixpath.dirname(key_path)
                        if key_dir and key_dir != "/":
                            main_dir = key_dir + "/"
                            break

        segments = []
        pending = []

        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media_url = urljoin(source_url, line)
                media_parsed = urllib.parse.urlparse(media_url)

                # 过滤逻辑：判断分片路径是否以正片目录开头
                is_ad = not media_parsed.path.startswith(main_dir)

                if not is_ad:
                    segments.extend(pending)
                    segments.append(media_url)
                pending = []
                continue

            if not line.startswith("#"):
                segments.append(urljoin(source_url, line))
            else:
                segments.append(line)

        # 二次清洗：去除孤立/连续的标记
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in ("#EXT-X-KEY:METHOD=NONE", "#EXT-X-DISCONTINUITY"):
                if not out or out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
                    continue
            out.append(line)

        while len(out) > 1 and out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
            out.pop()

        return "\n".join(out) + "\n"

    def _rewrite_m3u8_tag(self, line, source_url):
        """重写 m3u8 标签中的 URI（补全绝对地址）"""
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

    def _parse_vod_list(self, html):
        items = []
        pattern = r'<div class="vod-box">\s*<a class="vod" href="([^"]+)"[^>]*>\s*<div class="vod-thumb">\s*<img[^>]*data-src="([^"]*)"[^>]*>\s*</div>\s*<div class="vod-name">\s*<span>([^<]*)</span>\s*</div>\s*</a>\s*</div>'
        matches = re.findall(pattern, html, re.DOTALL)

        for match in matches:
            href, pic, name = match
            vid_match = re.search(r'/vplay-(\d+)/', href)
            if not vid_match:
                continue
            vid = vid_match.group(1)
            if not vid or not name:
                continue
            if pic and not pic.startswith("http"):
                pic = urljoin(self.host, pic)
            items.append({
                "vod_id": vid,
                "vod_name": name.strip(),
                "vod_pic": pic,
                "vod_remarks": ""
            })

        if not items:
            pattern2 = r'<a class="vod" href="(/vplay-\d+[^"]*)"[^>]*>\s*<div class="vod-thumb">\s*<img[^>]*(?:data-src|src)="([^"]*)"[^>]*>\s*</div>\s*<div class="vod-name">\s*<span>([^<]*)</span>'
            matches2 = re.findall(pattern2, html, re.DOTALL)
            for match in matches2:
                href, pic, name = match
                vid_match = re.search(r'/vplay-(\d+)/', href)
                if not vid_match:
                    continue
                vid = vid_match.group(1)
                if not vid or not name:
                    continue
                if pic and not pic.startswith("http"):
                    pic = urljoin(self.host, pic)
                items.append({
                    "vod_id": vid,
                    "vod_name": name.strip(),
                    "vod_pic": pic,
                    "vod_remarks": ""
                })

        return items

    def _parse_page_info(self, html):
        result = {"page": 1, "pagecount": 1, "total": 0}
        page_match = re.search(r'<log>(\d+)</log>', html)
        if page_match:
            result["pagecount"] = int(page_match.group(1))
            result["total"] = int(page_match.group(1)) * 20
        current_match = re.search(r'<div class="page-num active">\s*<a[^>]*>(\d+)</a>', html)
        if current_match:
            result["page"] = int(current_match.group(1))
        return result

    def _extract_player_data(self, html):
        result = {}
        pattern = r'var player_aaaa\s*=\s*({[\s\S]+?});'
        match = re.search(pattern, html)
        if not match:
            return result

        data_str = match.group(1)

        url_match = re.search(r'"url"\s*:\s*"([^"]+)"', data_str)
        if url_match:
            result["url"] = url_match.group(1)

        from_match = re.search(r'"from"\s*:\s*"([^"]+)"', data_str)
        if from_match:
            result["from"] = from_match.group(1)
        else:
            result["from"] = "播放"

        id_match = re.search(r'"id"\s*:\s*"([^"]+)"', data_str)
        if id_match:
            result["id"] = id_match.group(1)

        name_match = re.search(r'"vod_name"\s*:\s*"([^"]*)"', data_str)
        if name_match:
            result["vod_name"] = name_match.group(1)
        else:
            result["vod_name"] = "未知影片"

        return result

    def _extract_all_lines(self, html, vid):
        lines = []
        pattern = r'<a href="/vplay-' + str(vid) + r'/sid/(\d+)/nid/1\.html"[^>]*>(.*?)</a>'
        matches = re.findall(pattern, html)

        seen = set()
        for sid, name in matches:
            name = name.strip()
            if name in seen:
                continue
            seen.add(name)
            lines.append({
                "name": name,
                "sid": sid,
                "url": f"{vid}|{name}"
            })

        if not lines:
            play_data = self._extract_player_data(html)
            from_name = play_data.get("from", "播放")
            lines.append({
                "name": from_name,
                "sid": "1",
                "url": f"{vid}|{from_name}"
            })

        return lines