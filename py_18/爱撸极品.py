# -*- coding: utf-8 -*-
# 站点: 爱撸极品
# 域名: https://www.yeyehau.shop/ (备用: www.touyue.cfd)
# 类型: 成人影视聚合站 (MacCMS)
# CMS: MacCMS v8
# 加密: 无
# 版本: v1.2 - 添加 m3u8 广告过滤

import re
import json
from urllib.parse import urljoin, quote, unquote, urlparse
import posixpath

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://www.yeyehau.shop"
        self.backup_host = "https://www.touyue.cfd"
        
        self.classes = [
            {"type_id": "1", "type_name": "波多野结衣"},
            {"type_id": "2", "type_name": "欧美在线"},
            {"type_id": "3", "type_name": "中文字幕"},
            {"type_id": "4", "type_name": "日本无码"},
            {"type_id": "5", "type_name": "制服诱惑"},
            {"type_id": "6", "type_name": "麻豆传媒"},
            {"type_id": "7", "type_name": "国产视频"},
            {"type_id": "8", "type_name": "美女主播"},
            {"type_id": "9", "type_name": "少女萝莉"},
            {"type_id": "10", "type_name": "激情动漫"},
            {"type_id": "11", "type_name": "韩国主播"},
            {"type_id": "12", "type_name": "三级电影"},
            {"type_id": "13", "type_name": "网红头条"},
            {"type_id": "14", "type_name": "人妖做爱"},
            {"type_id": "15", "type_name": "明星流出"},
            {"type_id": "16", "type_name": "强奸乱伦"},
        ]
        
        self.filters = {str(i): [] for i in range(1, 17)}
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        
        self.extend = ""

    def getName(self):
        return "爱撸极品"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def getHost(self):
        return self.host

    def homeContent(self, filter):
        return {
            "class": self.classes,
            "filters": self.filters if filter else {}
        }

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        url = f"{self.getHost()}/"
        try:
            res = self.fetch(url, headers=self.headers)
            if not res or res.status_code != 200:
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}
            html = res.text
            items = self._parse_list_items(html)
            return {
                "list": items,
                "page": 1,
                "pagecount": 1,
                "limit": 20,
                "total": len(items)
            }
        except Exception as e:
            self.log(f"首页抓取失败: {e}")
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.getHost()}/index.php/vod/type/id/{tid}/page/{page}.html"
        return self._fetch_list(url, f"分类_{tid}_第{page}页")

    def searchContent(self, key, quick, pg="1"):
        if not key or len(key.strip()) == 0:
            return {"list": [], "page": 1}
        
        page = pg or "1"
        keyword = key.strip()
        url = f"{self.getHost()}/index.php/vod/search.html?wd={quote(keyword)}&page={page}"
        
        try:
            res = self.fetch(url, headers=self.headers)
            if not res or res.status_code != 200:
                return {"list": [], "page": int(page)}
            
            html = res.text
            items = self._parse_list_items(html)
            
            return {
                "list": items,
                "page": int(page)
            }
        except Exception as e:
            self.log(f"搜索失败: {e}")
            return {"list": [], "page": int(page)}

    def detailContent(self, ids):
        if not ids or len(ids) == 0:
            return {"list": []}
        
        vod_id = str(ids[0])
        if "|$|" in vod_id:
            parts = vod_id.split("|$|")
            vod_id = parts[0]
            vod_name = parts[1] if len(parts) > 1 else ""
            vod_pic = parts[2] if len(parts) > 2 else ""
            vod_remark = parts[3] if len(parts) > 3 else ""
        else:
            vod_name = ""
            vod_pic = ""
            vod_remark = ""
        
        play_url = f"{self.getHost()}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        
        vod = {
            "vod_id": vod_id,
            "vod_name": vod_name or "视频",
            "vod_pic": vod_pic,
            "vod_remarks": vod_remark,
            "vod_content": vod_remark,
            "vod_play_from": "播放",
            "vod_play_url": f"播放${play_url}"
        }
        
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        if id and (id.endswith(".m3u8") or id.endswith(".mp4")):
            if id.endswith(".m3u8"):
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(id),
                    "header": {"User-Agent": self.headers["User-Agent"]}
                }
            return {
                "parse": 0,
                "url": id,
                "header": {"User-Agent": self.headers["User-Agent"]}
            }
        
        try:
            res = self.fetch(id, headers=self.headers)
            if not res or res.status_code != 200:
                return {"parse": 1, "url": id, "header": self.headers}
            
            html = res.text
            
            match = re.search(r'var\s+player_aaaa\s*=\s*({[^;]+})', html)
            if match:
                try:
                    player_data = json.loads(match.group(1))
                    m3u8_url = player_data.get("url", "")
                    if m3u8_url and (m3u8_url.endswith(".m3u8") or m3u8_url.endswith(".mp4")):
                        if m3u8_url.endswith(".m3u8"):
                            return {
                                "parse": 0,
                                "url": self._m3u8_proxy_url(m3u8_url),
                                "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.getHost()}
                            }
                        return {
                            "parse": 0,
                            "url": m3u8_url,
                            "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.getHost()}
                        }
                except:
                    pass
            
            iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"[^>]*>', html)
            if iframe_match:
                iframe_src = iframe_match.group(1)
                if iframe_src and (".m3u8" in iframe_src or ".mp4" in iframe_src):
                    if ".m3u8" in iframe_src:
                        return {
                            "parse": 0,
                            "url": self._m3u8_proxy_url(iframe_src),
                            "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.getHost()}
                        }
                    return {
                        "parse": 0,
                        "url": iframe_src,
                        "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.getHost()}
                    }
                if "?" in iframe_src and "url=" in iframe_src:
                    url_param = re.search(r'[?&]url=([^&]+)', iframe_src)
                    if url_param:
                        decoded = unquote(url_param.group(1))
                        if decoded.endswith(".m3u8") or decoded.endswith(".mp4"):
                            if decoded.endswith(".m3u8"):
                                return {
                                    "parse": 0,
                                    "url": self._m3u8_proxy_url(decoded),
                                    "header": {"User-Agent": self.headers["User-Agent"]}
                                }
                            return {
                                "parse": 0,
                                "url": decoded,
                                "header": {"User-Agent": self.headers["User-Agent"]}
                            }
            
            m3u8_pattern = r'https?://[^\s"\']+\.m3u8[^\s"\']*'
            match = re.search(m3u8_pattern, html)
            if match:
                m3u8_url = match.group(0)
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(m3u8_url),
                    "header": {"User-Agent": self.headers["User-Agent"]}
                }
            
            return {
                "parse": 1,
                "url": id,
                "header": self.headers
            }
            
        except Exception as e:
            self.log(f"playerContent解析失败: {e}")
            return {"parse": 1, "url": id, "header": self.headers}

    def _fetch_list(self, url, log_tag=""):
        try:
            res = self.fetch(url, headers=self.headers)
            if not res or res.status_code != 200:
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}
            
            html = res.text
            items = self._parse_list_items(html)
            page_info = self._parse_pagination(html)
            
            return {
                "list": items,
                "page": page_info.get("page", 1),
                "pagecount": page_info.get("pagecount", 1),
                "limit": 20,
                "total": page_info.get("total", len(items))
            }
        except Exception as e:
            self.log(f"{log_tag} 抓取失败: {e}")
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def _parse_list_items(self, html):
        items = []
        
        li_pattern = r'<li\s+class="col-md-2[^"]*"[^>]*>(.*?)</li>'
        li_matches = re.findall(li_pattern, html, re.DOTALL)
        
        for li_html in li_matches:
            try:
                pic_match = re.search(r'background:\s*url\(([^)]+)\)', li_html)
                pic = pic_match.group(1).strip() if pic_match else ""
                
                link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"', li_html)
                if not link_match:
                    continue
                
                href = link_match.group(1)
                title = link_match.group(2).strip()
                
                if not title or not href:
                    continue
                
                vod_id_match = re.search(r'/vod/play/id/(\d+)', href)
                vod_id = vod_id_match.group(1) if vod_id_match else ""
                
                if not vod_id:
                    continue
                
                tag_parts = re.findall(r'<td[^>]*><div[^>]*>([^<]+)</div></td>', li_html)
                date = tag_parts[0].strip() if tag_parts else ""
                tag = tag_parts[-1].strip() if len(tag_parts) > 1 else ""
                
                composite_id = f"{vod_id}|$|{title}|$|{pic}|$|{date}"
                
                item = {
                    "vod_id": composite_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": f"{date} {tag}".strip()
                }
                items.append(item)
                
            except Exception as e:
                self.log(f"解析列表项出错: {e}")
                continue
        
        return items

    def _parse_pagination(self, html):
        result = {"page": 1, "pagecount": 1, "total": 0}
        
        current_match = re.search(r'<span[^>]*class="current"[^>]*>(\d+)</span>', html)
        if not current_match:
            current_match = re.search(r'<a[^>]*class="active"[^>]*>(\d+)</a>', html)
        
        if current_match:
            result["page"] = int(current_match.group(1))
        
        page_nums = re.findall(r'>(\d+)</a>', html)
        page_nums = [int(n) for n in page_nums if n.isdigit()]
        if page_nums:
            result["pagecount"] = max(page_nums)
        else:
            result["pagecount"] = 1
        
        return result

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

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        return self.getProxyUrl() + "?do=py&url=" + quote(str(url or ""), safe="")

    def localProxy(self, param):
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

            res = self.fetch(target, headers={"User-Agent": self.headers.get("User-Agent", "")}, timeout=15)
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
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"

        parsed = urlparse(source_url)
        source_dir = posixpath.dirname(parsed.path)
        if not source_dir.endswith("/"):
            source_dir += "/"

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
                media_parsed = urlparse(media_url)

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