# -*- coding: utf-8 -*-
# 站点: 91furen (https://91furen.top)
# 说明: 支持 m3u8 广告过滤 (v3.0)

import re
import json
import posixpath
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.site_url = "https://91furen.top"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.site_url + "/"
        }
        self.classes = [
            {"type_id": "1", "type_name": "国产视频"},
            {"type_id": "2", "type_name": "中文字幕"},
            {"type_id": "3", "type_name": "国产主播"},
            {"type_id": "4", "type_name": "激情动漫"},
            {"type_id": "5", "type_name": "伦理三级"},
            {"type_id": "6", "type_name": "制服诱惑"},
            {"type_id": "7", "type_name": "网曝黑料"},
            {"type_id": "8", "type_name": "日本无码"},
            {"type_id": "9", "type_name": "欧美无码"},
            {"type_id": "10", "type_name": "少女萝莉"},
            {"type_id": "11", "type_name": "SM调教"},
            {"type_id": "12", "type_name": "网红头条"},
            {"type_id": "13", "type_name": "国产传媒"},
            {"type_id": "14", "type_name": "抖阴视频"},
            {"type_id": "15", "type_name": "强奸乱伦"},
            {"type_id": "16", "type_name": "韩国主播"},
        ]
        self.filters = {}

    def getName(self):
        return "91furen"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def homeContent(self, filter=False):
        result = {"class": [], "filters": self.filters}
        for c in self.classes:
            result["class"].append({"type_id": c["type_id"], "type_name": c["type_name"]})
        return result

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        return self.categoryContent(tid="1", pg="1", filter=False, extend={})

    def categoryContent(self, tid, pg, filter=False, extend={}):
        url = f"{self.site_url}/vod/type/id/{tid}.html"
        if int(pg) > 1:
            url += f"?page={pg}"
        
        try:
            resp = self.fetch(url, headers=self.headers)
            html = resp.text
            
            items = []
            blocks = re.findall(r'<li[^>]*class="[^"]*content-item[^"]*"[^>]*>(.*?)</li>', html, re.DOTALL)
            
            if not blocks:
                pattern = r'<a href="(/vod/detail/id/(\d+)\.html)"[^>]*>([^<]+)</a>'
                matches = re.findall(pattern, html)
                for detail_url, vid, title in matches:
                    pic = ""
                    img_match = re.search(r'<img[^>]+(?:data-original|src)="([^"]+)"', html)
                    if img_match:
                        pic = img_match.group(1)
                        if pic and not pic.startswith("http"):
                            pic = self.site_url + pic
                    items.append({
                        "vod_id": vid,
                        "vod_name": title.strip(),
                        "vod_pic": pic,
                        "vod_remarks": ""
                    })
            else:
                for block in blocks:
                    link_match = re.search(r'<a href="(/vod/detail/id/(\d+)\.html)"[^>]*>([^<]+)</a>', block)
                    if not link_match:
                        continue
                    detail_url, vid, title = link_match.groups()
                    title = title.strip()
                    if not title or len(title) < 2:
                        continue
                    
                    pic = ""
                    img_match = re.search(r'<img[^>]+(?:data-original|src)="([^"]+)"', block)
                    if img_match:
                        pic = img_match.group(1)
                    if pic and not pic.startswith("http"):
                        pic = self.site_url + pic
                    
                    items.append({
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": ""
                    })
            
            page_count = 1
            page_match = re.search(r'共(\d+)頁', html)
            if not page_match:
                page_match = re.search(r'共(\d+)页', html)
            if page_match:
                page_count = int(page_match.group(1))
            elif re.search(r'下一[頁页]', html):
                page_count = 999
            
            return {
                "list": items,
                "page": int(pg),
                "pagecount": page_count,
                "limit": len(items),
                "total": len(items)
            }
        except Exception as e:
            self.log({"action": "category_fail", "error": str(e)})
            return {"list": [], "page": int(pg), "pagecount": 1, "limit": 0, "total": 0}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        
        vid = str(ids[0])
        url = f"{self.site_url}/vod/detail/id/{vid}.html"
        
        try:
            resp = self.fetch(url, headers=self.headers)
            html = resp.text
            
            title = ""
            title_match = re.search(r'<h5[^>]*class="title"[^>]*>(.*?)</h5>', html, re.DOTALL)
            if title_match:
                title = re.sub(r'[名稱名称]：', '', title_match.group(1).strip())
            
            pic = ""
            pic_match = re.search(r'<img[^>]+src="([^"]+)"[^>]*class="img-responsive"', html)
            if pic_match:
                pic = pic_match.group(1)
                if pic and not pic.startswith("http"):
                    pic = self.site_url + pic
            
            play_url = ""
            play_match = re.search(r'<a[^>]*href="(/vod/play/id/%s/sid/\d+/nid/\d+\.html)"' % vid, html)
            if play_match:
                play_url = self.site_url + play_match.group(1)
            
            return {
                "list": [{
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_play_from": "線路1",
                    "vod_play_url": f"播放${play_url}" if play_url else "",
                    "vod_content": ""
                }]
            }
        except Exception as e:
            self.log({"action": "detail_fail", "error": str(e)})
            return {"list": []}

    def searchContent(self, key, quick=False, pg="1"):
        url = f"{self.site_url}/vod/search.html"
        data = {"wd": key}
        
        try:
            resp = self.post(url, data=data, headers=self.headers)
            html = resp.text
            
            items = []
            blocks = re.findall(r'<li[^>]*class="[^"]*content-item[^"]*"[^>]*>(.*?)</li>', html, re.DOTALL)
            
            if blocks:
                for block in blocks:
                    link_match = re.search(r'<a href="(/vod/detail/id/(\d+)\.html)"[^>]*>([^<]+)</a>', block)
                    if not link_match:
                        continue
                    detail_url, vid, title = link_match.groups()
                    title = title.strip()
                    if not title or len(title) < 2:
                        continue
                    
                    pic = ""
                    img_match = re.search(r'<img[^>]+(?:data-original|src)="([^"]+)"', block)
                    if img_match:
                        pic = img_match.group(1)
                        if pic and not pic.startswith("http"):
                            pic = self.site_url + pic
                    
                    items.append({
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": ""
                    })
            else:
                pattern = r'<a href="(/vod/detail/id/(\d+)\.html)"[^>]*>([^<]+)</a>'
                matches = re.findall(pattern, html)
                seen = set()
                for detail_url, vid, title in matches:
                    if vid in seen:
                        continue
                    seen.add(vid)
                    title = title.strip()
                    if not title:
                        continue
                    pic = ""
                    img_match = re.search(r'<img[^>]+(?:data-original|src)="([^"]+)"', html)
                    if img_match:
                        pic = img_match.group(1)
                        if pic and not pic.startswith("http"):
                            pic = self.site_url + pic
                    items.append({
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": ""
                    })
            
            return {"list": items, "page": int(pg), "pagecount": 1, "limit": len(items), "total": len(items)}
        except Exception as e:
            self.log({"action": "search_fail", "error": str(e)})
            return {"list": [], "page": int(pg), "pagecount": 1, "limit": 0, "total": 0}

    def playerContent(self, flag, id, vipFlags=""):
        if not id:
            return {"parse": 1, "url": ""}
        
        real_url = ""
        try:
            if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
                real_url = id
            else:
                if id.startswith("/"):
                    play_url = self.site_url + id
                elif id.startswith("http"):
                    play_url = id
                else:
                    vid_match = re.search(r'(\d+)', id)
                    vid = vid_match.group(1) if vid_match else id
                    play_url = f"{self.site_url}/vod/play/id/{vid}/sid/1/nid/1.html"
                
                resp = self.fetch(play_url, headers=self.headers, timeout=15)
                html = resp.text
                
                url_match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
                if url_match:
                    real_url = url_match.group(1)
                else:
                    player_match = re.search(r'player_aaaa\s*=\s*({[^;]+});', html, re.DOTALL)
                    if player_match:
                        try:
                            player_data = json.loads(player_match.group(1))
                            real_url = player_data.get("url", "")
                        except json.JSONDecodeError:
                            pass
                
                if not real_url:
                    m3u8_match = re.search(r"setm3u8\s*\(\s*'[^']*'\s*,\s*'([^']+)'\s*,\s*'[^']*'\s*\)", html)
                    if m3u8_match:
                        m3u8_path = m3u8_match.group(1)
                        if m3u8_path and m3u8_path.strip():
                            real_url = self.site_url + "/" + m3u8_path.lstrip("/")
        except Exception as e:
            self.log({"action": "player_extract_fail", "error": str(e)})

        if real_url:
            real_url = real_url.replace("\\/", "/").strip()
            # 包装代理地址，让 localProxy 处理广告过滤
            return {
                "parse": 0,
                "url": self._m3u8_proxy_url(real_url),
                "header": {"Referer": self.site_url + "/", "User-Agent": self.headers["User-Agent"]}
            }
        
        return {"parse": 1, "url": id}

    def localProxy(self, param):
        """m3u8 本地代理 + 广告分片过滤 (v3.0)"""
        try:
            # 兼容 url 和 source 两种参数名
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")

            # 剥离前缀 url= 并解码
            if target.startswith("url="):
                target = target[4:]
            target = urllib.parse.unquote(str(target or ""))

            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            # 发起 HTTP 请求获取 m3u8 内容
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
        """清洗 m3u8：过滤广告分片 (基于 #EXT-X-KEY 目录匹配)"""
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
                    child = urllib.parse.urljoin(source_url, line)
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
                media_url = urllib.parse.urljoin(source_url, line)
                media_parsed = urllib.parse.urlparse(media_url)

                # 过滤逻辑：判断分片路径是否以正片目录开头
                is_ad = not media_parsed.path.startswith(main_dir)

                if not is_ad:
                    segments.extend(pending)
                    segments.append(media_url)
                pending = []
                continue

            if not line.startswith("#"):
                segments.append(urllib.parse.urljoin(source_url, line))
            else:
                segments.append(line)

        # 二次清洗：去除孤立/连续的 #EXT-X-DISCONTINUITY 和 KEY:METHOD=NONE
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in ("#EXT-X-KEY:METHOD=NONE", "#EXT-X-DISCONTINUITY"):
                if not out or out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
                    continue
            out.append(line)

        # 清理尾部多余的标记
        while len(out) > 1 and out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
            out.pop()

        return "\n".join(out) + "\n"

    def _rewrite_m3u8_tag(self, line, source_url):
        """重写相对路径标签 (KEY / MAP / TS)"""
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

    def destroy(self):
        pass