# coding: utf-8
import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://atc.xdrk2.mom"
        self.base_path = "/cn/home/web"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + self.base_path + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.classes = [
            {"type_id": "20", "type_name": "绝美少女"},
            {"type_id": "21", "type_name": "激情口交"},
            {"type_id": "22", "type_name": "同性专区"},
            {"type_id": "23", "type_name": "人妖激情"},
            {"type_id": "24", "type_name": "重咸口味"},
            {"type_id": "25", "type_name": "国产专区"},
            {"type_id": "26", "type_name": "日韩专区"},
            {"type_id": "27", "type_name": "欧美专区"},
            {"type_id": "28", "type_name": "卡通动漫"},
            {"type_id": "29", "type_name": "三级伦理"},
        ]
        self.filters = {k: [] for k in ["20", "21", "22", "23", "24", "25", "26", "27", "28", "29"]}

    def getName(self):
        return "性都入口"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        # 复用分类页数据作为首页推荐（使用第一个分类"绝美少女"）
        try:
            result = self.categoryContent("20", "1", False, {})
            items = result.get("list", [])[:20]
            return {"list": items}
        except Exception as e:
            return {"list": []}
    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = self.host + self.base_path + f"/index.php/vod/type/id/{tid}/page/{page}.html"
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if not resp or resp.status_code != 200:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            html = resp.text
            items = []
            # 匹配分类列表中的视频 - PC模板结构
            # <li class="ng-scope"> 包含 a 标签和 p.title
            li_pattern = r'<li class="ng-scope">.*?<a href="([^"]+)".*?<img[^>]*data-original="([^"]+)".*?</a>.*?<p class="title[^"]*"[^>]*title="([^"]+)".*?</p>.*?<span class="pink-txt[^"]*">上架日期[^:]*:([^<]+)</span>'
            matches = re.findall(li_pattern, html, re.DOTALL)
            for match in matches:
                link, pic, title, remark = match
                vod_id = self._extract_vod_id(link)
                if vod_id:
                    items.append({
                        "vod_id": vod_id,
                        "vod_name": title.strip(),
                        "vod_pic": pic,
                        "vod_remarks": remark.strip(),
                    })
            # 提取总页数
            pagecount = 1
            # 从分页信息中提取: "共45704条数据 当前:1/2177页"
            page_info_match = re.search(r'当前:(\d+)/(\d+)页', html)
            if page_info_match:
                pagecount = int(page_info_match.group(2))
            return {
                "list": items,
                "page": int(page),
                "pagecount": pagecount,
                "limit": 20,
                "total": pagecount * 20,
            }
        except Exception as e:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vod_id = str(ids[0])
        url = self.host + self.base_path + f"/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if not resp or resp.status_code != 200:
                return {"list": []}
            html = resp.text
            # 提取标题
            title_match = re.search(r'<title>(.*?)</title>', html)
            title = "未知"
            if title_match:
                raw_title = title_match.group(1)
                # 清理标题
                title = re.sub(r'\s*-\s*在线播放.*$', '', raw_title)
                title = re.sub(r'\s*-\s*.*性都入口.*$', '', title)
            # 提取播放地址
            player_data_match = re.search(r'var player_data=({[^}]+})', html)
            play_url = ""
            if player_data_match:
                try:
                    data = json.loads(player_data_match.group(1))
                    play_url = data.get("url", "")
                except:
                    pass
            # 提取选集列表
            vod_play_url = ""
            vod_play_from = "直链"
            if play_url and ".m3u8" in play_url:
                vod_play_url = "第1集$" + play_url
            else:
                # 如果没有m3u8，使用播放页地址
                vod_play_url = "第1集$" + url
                vod_play_from = "播放页"
            # 提取封面
            pic_match = re.search(r'<img[^>]*data-original="([^"]+)"', html)
            pic = pic_match.group(1) if pic_match else ""
            vod = {
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": "最新",
                "vod_content": "",
                "vod_play_from": vod_play_from,
                "vod_play_url": vod_play_url,
            }
            return {"list": [vod]}
        except Exception as e:
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        url = self.host + self.base_path + f"/index.php/vod/search.html?wd={urllib.parse.quote(key)}"
        if str(pg) != "1":
            url += f"&pg={pg}"
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if not resp or resp.status_code != 200:
                return {"list": [], "page": int(pg)}
            html = resp.text
            items = []
            # 匹配搜索列表中的视频 - 与分类页相同的PC模板结构
            li_pattern = r'<li class="ng-scope">.*?<a href="([^"]+)".*?<img[^>]*data-original="([^"]+)".*?</a>.*?<p class="title[^"]*"[^>]*title="([^"]+)".*?</p>.*?<span class="pink-txt[^"]*">上架日期[^:]*:([^<]+)</span>'
            matches = re.findall(li_pattern, html, re.DOTALL)
            for match in matches:
                link, pic, title, remark = match
                vod_id = self._extract_vod_id(link)
                if vod_id:
                    items.append({
                        "vod_id": vod_id,
                        "vod_name": title.strip(),
                        "vod_pic": pic,
                        "vod_remarks": remark.strip(),
                    })
            return {"list": items, "page": int(pg)}
        except Exception as e:
            return {"list": [], "page": int(pg)}
    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        play_url = str(id).strip()
        if "vod/play/id/" in play_url:
            try:
                resp = self.fetch(play_url, headers=self.headers, timeout=15)
                if resp and resp.status_code == 200:
                    player_data_match = re.search(r'var player_data=({[^}]+})', resp.text)
                    if player_data_match:
                        try:
                            data = json.loads(player_data_match.group(1))
                            m3u8_url = data.get("url", "")
                            if m3u8_url and ".m3u8" in m3u8_url:
                                return {
                                    "parse": 0,
                                    "url": self._m3u8_proxy_url(m3u8_url),
                                    "header": self.headers,
                                }
                        except:
                            pass
            except:
                pass
            return {"parse": 1, "url": play_url, "header": self.headers}
        if ".m3u8" in play_url:
            return {
                "parse": 0,
                "url": self._m3u8_proxy_url(play_url),
                "header": self.headers,
            }
        return {"parse": 0, "url": play_url, "header": self.headers}

    def _m3u8_proxy_url(self, url):
        proxy_url = self.getProxyUrl()
        if "?" in proxy_url:
            return proxy_url + "&url=" + urllib.parse.quote(str(url or ""), safe="")
        return proxy_url + "?url=" + urllib.parse.quote(str(url or ""), safe="")

    def localProxy(self, param):
        target = ""
        if isinstance(param, dict):
            target = param.get("url", "") or param.get("source", "")
        elif isinstance(param, str):
            target = param
        if target and target.startswith("url="):
            target = target[4:]
        if target and "url=" in target:
            parsed = urllib.parse.urlparse(target)
            qs = urllib.parse.parse_qs(parsed.query)
            if "url" in qs:
                target = qs["url"][0]
        target = urllib.parse.unquote(str(target or ""))
        if not target or not re.match(r"^https?://", target, re.I):
            return [400, "text/plain", b"invalid url"]
        try:
            resp = self.fetch(target, headers=self.headers, timeout=20)
            if not resp:
                return [502, "text/plain", b"fetch failed"]
            content = getattr(resp, "content", b"") or b""
            if not content and hasattr(resp, "text") and resp.text:
                content = resp.text.encode("utf-8", errors="ignore")
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
            return [200, content_type, content]
        except Exception as e:
            return [500, "text/plain", str(e).encode("utf-8", errors="ignore")]

    def _clean_m3u8(self, text, source_url):
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"
        is_multi = any(line.startswith("#EXT-X-STREAM-INF") for line in lines)
        if is_multi:
            return self._clean_m3u8_multi(lines, source_url)
        return self._clean_m3u8_single(lines, source_url)

    def _clean_m3u8_multi(self, lines, source_url):
        out = []
        for line in lines:
            if line.startswith("#"):
                out.append(line)
            else:
                child_url = urllib.parse.urljoin(source_url, line)
                out.append(self._m3u8_proxy_url(child_url))
        return "\n".join(out) + "\n"

    def _clean_m3u8_single(self, lines, source_url):
        parsed = urllib.parse.urlparse(source_url)
        dir_path = parsed.path[:parsed.path.rfind('/')+1] if '/' in parsed.path else "/"

        def is_valid_segment(url):
            parsed_url = urllib.parse.urlparse(url)
            return parsed_url.path.startswith(dir_path)

        result = []
        pending_extinf = []
        removed = 0
        kept = 0
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
                        if is_valid_segment(media_url):
                            if media_url.endswith('.jpg'):
                                media_url = media_url[:-4] + '.ts'
                            result.extend(pending_extinf)
                            result.append(media_url)
                            kept += 1
                        else:
                            removed += 1
                        i += 1
                        break
                continue
            result.append(line)
            i += 1
        if removed:
            self.log(f"m3u8已过滤广告分片: {removed}个，保留正片: {kept}个")
        return "\n".join(result) + "\n"

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

    def _extract_vod_id(self, link):
        match = re.search(r'/play/id/(\d+)/', link)
        return match.group(1) if match else None

    def destroy(self):
        pass