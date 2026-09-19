# coding: utf-8
"""
站点: 忘不了爽剧
主域名: https://www.wangbuliaoshuangju.com
备用域名: 暂无
发布页: 无
内容类型: 影视视频站（短剧/爽剧）
特殊说明: 标准HTML站，播放地址在flashvars.video_url或videoObject.video.url中
验证时间: 2026-09-05
来源: AI Agent 分析
"""
import json
import re
from urllib.parse import urljoin, quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://www.wangbuliaoshuangju.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        # 分类列表 - 包含主分类和子分类（与超好看影视风格一致）
        self.classes = [
            {"type_id": "latest-videos", "type_name": "最新电影"},
            {"type_id": "serials-videos", "type_name": "电视剧"},
            {"type_id": "lunlidianying", "type_name": "伦理片"},
            {"type_id": "quanjiduanju", "type_name": "全短剧"},
            {"type_id": "fenjiduanju", "type_name": "短剧集"},
            {"type_id": "hanju", "type_name": "韩剧"}
        ]
        # 子分类映射：type_id -> (分类类型, 显示名称)
        self.category_map = {
            "lunlidianying": {"type": "videos", "name": "伦理片"},
            "quanjiduanju": {"type": "videos", "name": "全短剧"},
            "fenjiduanju": {"type": "serials_videos", "name": "短剧集"},
            "hanju": {"type": "serials_videos", "name": "韩剧"}
        }
        self.filters = {}
        self._session = None

    def getName(self):
        return "忘不了爽剧"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""
        if self._session is None:
            self._session = self.fetch

    def destroy(self):
        if self._session:
            self._session = None

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐视频"""
        resp = self.fetch(self.host + "/", headers=self.headers, timeout=10)
        if resp.status_code != 200:
            return {"list": []}
        html = resp.text
        items = []
        # 使用 a 标签的 title 属性提取标题，更通用
        pattern = r'<div class="item">\s*<a href="([^"]+)"[^>]*title="([^"]+)".*?<picture>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div class="wrap">([^<]+)</div>'
        matches = re.findall(pattern, html, re.DOTALL)
        seen = set()
        for match in matches:
            link, title, pic, wrap = match
            if link in seen:
                continue
            seen.add(link)
            vod_id = link.strip("/").split("/")[-1] if link else ""
            if not vod_id:
                continue
            views = ""
            if "次播放" in wrap:
                views = wrap.split("次播放")[0].strip()
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, pic.strip()) if pic else "",
                "vod_remarks": views
            })
            if len(items) >= 20:
                break
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        """分类列表"""
        page = int(pg) if pg and str(pg).isdigit() else 1
        if page < 1:
            page = 1

        # 判断分类类型
        if tid == "latest-videos":
            url = f"{self.host}/latest-videos/{page}/"
        elif tid == "serials-videos":
            url = f"{self.host}/serials-videos/{page}/"
        elif tid in self.category_map:
            cat_info = self.category_map[tid]
            url = f"{self.host}/{cat_info['type']}/categories/{tid}/{page}/"
        else:
            url = f"{self.host}/videos/categories/{tid}/{page}/"

        resp = self.fetch(url, headers=self.headers, timeout=10)
        if resp.status_code != 200:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        html = resp.text
        items = []
        
        # 使用更可靠的正则：从 a 标签提取 title 和 href，从 img 提取 src，从 wrap 提取播放次数
        pattern = r'<div class="item">.*?<a href="([^"]+)"[^>]*title="([^"]+)".*?<img[^>]*src="([^"]+)".*?<div class="wrap">([^<]+)</div>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for match in matches:
            link, title, pic, wrap = match
            vod_id = link.strip("/").split("/")[-1] if link else ""
            if not vod_id or not title:
                continue
            views = ""
            if "次播放" in wrap:
                views = wrap.split("次播放")[0].strip()
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, pic) if pic else "",
                "vod_remarks": views
            })

        # 解析分页信息
        pagecount = 1
        last_pattern = r'<li class="last"><a href="[^"]*/(\d+)/"'
        last_match = re.search(last_pattern, html)
        if last_match:
            pagecount = int(last_match.group(1))
        else:
            page_links = re.findall(r'<li class="page"><a href="[^"]*/(\d+)/"', html)
            if page_links:
                pagecount = max(int(p) for p in page_links)

        return {
            "list": items,
            "page": page,
            "pagecount": pagecount,
            "limit": 20,
            "total": len(items) * pagecount if items else 0
        }

    def detailContent(self, ids):
        """详情页 - 提取剧集列表"""
        if not ids:
            return {"list": []}
        vod_id = str(ids[0])
        # 优先尝试电视剧路径，再尝试电影路径
        url = f"{self.host}/serials-video/{vod_id}/"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if resp.status_code != 200:
            url = f"{self.host}/video/{vod_id}/"
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return {"list": []}
            is_serials = False
        else:
            is_serials = True
        html = resp.text

        # 提取标题
        title_match = re.search(r'<h1[^>]*class="videoinfo-title"[^>]*>([^<]+)</h1>', html)
        if not title_match:
            title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        title = title_match.group(1).strip() if title_match else ""

        # 提取封面 - 从页面中实际提取
        pic = ""
        pic_match = re.search(r'<picture>.*?<img[^>]*src="([^"]+)"', html, re.DOTALL)
        if pic_match:
            pic = urljoin(self.host, pic_match.group(1))
        if not pic:
            pic_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            if pic_match:
                pic = pic_match.group(1)

        # 提取描述
        desc = ""
        desc_match = re.search(r'<meta name="description" content="([^"]+)"', html)
        if desc_match:
            desc = desc_match.group(1).strip()
        if not desc:
            desc_match = re.search(r'<div class="videoinfo-title">([^<]+)</div>', html)
            if desc_match:
                desc = desc_match.group(1).strip()

        if is_serials:
            # 电视剧：提取选集列表
            play_from = "播放"
            play_url_parts = []
            
            # 直接匹配所有 episode_item
            episode_items = re.findall(r'<div class="episode_item">(.*?)</div>', html, re.DOTALL)
            for item in episode_items:
                ep_num = ""
                ep_url = ""
                span_match = re.search(r'<span[^>]*>(\d+)</span>', item)
                if span_match:
                    ep_num = span_match.group(1)
                    ep_url = self._extract_play_url(html)
                    if ep_url:
                        play_url_parts.append(f"第{ep_num}集${ep_url}")
                    continue
                a_match = re.search(r'<a href="([^"]+)">(\d+)</a>', item)
                if a_match:
                    ep_url = a_match.group(1)
                    ep_num = a_match.group(2)
                    play_url_parts.append(f"第{ep_num}集${ep_url}")
                    continue
            
            if not play_url_parts:
                play_url = self._extract_play_url(html)
                if play_url:
                    play_url_parts.append(f"第1集${play_url}")
            
            vod_play_url = "#".join(play_url_parts) if play_url_parts else ""
            vod_play_from = play_from
        else:
            # 电影：直接提取播放地址
            play_url = self._extract_play_url(html)
            vod_play_from = "播放"
            vod_play_url = f"播放${play_url}" if play_url else ""

        vod = {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": "",
            "vod_content": desc,
            "vod_play_from": vod_play_from,
            "vod_play_url": vod_play_url
        }
        return {"list": [vod]}

    def _extract_play_url(self, html):
        """从HTML中提取播放地址"""
        play_url = ""
        flash_match = re.search(r"video_url\s*:\s*['\"]([^'\"]+)['\"]", html)
        if flash_match:
            play_url = flash_match.group(1)
        if not play_url:
            url_match = re.search(r"video\s*:\s*\{\s*[^}]*url\s*:\s*['\"]([^'\"]+)['\"]", html, re.DOTALL)
            if url_match:
                play_url = url_match.group(1)
        if not play_url:
            url_match = re.search(r"url\s*:\s*['\"]([^'\"]+\.m3u8)['\"]", html)
            if url_match:
                play_url = url_match.group(1)
        return play_url

    def searchContent(self, key, quick, pg="1"):
        """搜索"""
        if not key:
            return {"list": [], "page": 1}
        page = int(pg) if str(pg).isdigit() else 1
        url = f"{self.host}/search/?q={quote(key)}"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if resp.status_code != 200:
            return {"list": [], "page": page}
        html = resp.text
        items = []
        # 使用 a 标签的 title 属性提取标题
        pattern = r'<div class="item">\s*<a href="([^"]+)"[^>]*title="([^"]+)".*?<picture>.*?<img[^>]*src="([^"]+)"[^>]*>'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            link, title, pic = match
            vod_id = link.strip("/").split("/")[-1] if link else ""
            if not vod_id:
                continue
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, pic.strip()) if pic else "",
                "vod_remarks": ""
            })
        return {"list": items, "page": page}

    def playerContent(self, flag, id, vipFlags):
        """播放器"""
        id = str(id) if id is not None else ""
        if not id:
            return {"parse": 0, "url": "", "header": self.headers}
        # 如果 id 是完整的 URL 且是 m3u8/mp4 直链，直接返回，不走代理
        if id.startswith("http") and (".m3u8" in id.lower() or ".mp4" in id.lower()):
            return {"parse": 0, "url": id, "header": self.headers}
        # 如果 id 是剧集页面链接 (完整URL或相对路径)
        if id.startswith("/serials-video/") or id.startswith("https://www.wangbuliaoshuangju.com/serials-video/") or id.startswith("/video/"):
            if not id.startswith("http"):
                url = urljoin(self.host, id)
            else:
                url = id
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                html = resp.text
                play_url = self._extract_play_url(html)
                if play_url:
                    return {"parse": 0, "url": play_url, "header": self.headers}
        # 如果 id 是 vod_id，尝试从详情页获取播放地址
        url = f"{self.host}/video/{id}/"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if resp.status_code != 200:
            url = f"{self.host}/serials-video/{id}/"
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return {"parse": 0, "url": "", "header": self.headers}
        html = resp.text
        play_url = self._extract_play_url(html)
        if play_url:
            return {"parse": 0, "url": play_url, "header": self.headers}
        return {"parse": 1, "url": url, "header": self.headers}

    def localProxy(self, params):
        """m3u8 代理"""
        if not params:
            return [404, "text/plain", b"not found"]
        target = params.get("url", "")
        if not target or not target.startswith("http"):
            return [400, "text/plain", b"invalid url"]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.host + "/"
        }
        try:
            resp = self.fetch(target, headers=headers, timeout=15)
            if resp.status_code != 200:
                return [502, "text/plain", b"m3u8 fetch failed"]
            content = resp.content
            text = content.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]
            lines = text.splitlines()
            out_lines = []
            base_url = target.rsplit("/", 1)[0] + "/"
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
                        def repl(m):
                            uri = m.group(1)
                            if not uri.startswith("http"):
                                uri = urljoin(base_url, uri)
                            return f'URI="{uri}"'
                        line = re.sub(r'URI="([^"]+)"', repl, line)
                    out_lines.append(line)
                else:
                    if not line.startswith("http"):
                        line = urljoin(base_url, line)
                    out_lines.append(line)
            result = "\n".join(out_lines)
            return [200, "application/vnd.apple.mpegurl", result.encode("utf-8")]
        except Exception as e:
            return [500, "text/plain", b"proxy error"]

    def recommendContent(self, ids, pg):
        """相关推荐"""
        return {"list": []}