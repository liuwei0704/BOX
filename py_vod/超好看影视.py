# coding: utf-8
"""
站点: 超好看影视
主域名: https://xn--94qq85au3qv4v.chaohaokanyingshi1.click/
备用域名: 暂无
发布页: 无
内容类型: 影视视频站
特殊说明: 标准HTML站，播放地址在videoObject.url中，直链m3u8无广告
验证时间: 2026-09-05
来源: AI Agent 分析
"""
import json
import re
from urllib.parse import urljoin, quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://xn--94qq85au3qv4v.chaohaokanyingshi1.click"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        # 子分类扁平化：直接列出所有可点击的分类
        self.classes = [
            {"type_id": "dongzuopian", "type_name": "动作片"},
            {"type_id": "aiqingpian", "type_name": "爱情片"},
            {"type_id": "kehuanpian", "type_name": "科幻片"},
            {"type_id": "kongbupian", "type_name": "恐怖片"},
            {"type_id": "xijupian", "type_name": "喜剧片"},
            {"type_id": "juqingpian", "type_name": "剧情片"},
            {"type_id": "zhanzhengpian", "type_name": "战争片"},
            {"type_id": "jingsongpian", "type_name": "惊悚片"},
            {"type_id": "lunlidianying", "type_name": "伦理片"},
            {"type_id": "chongshengmingguoduanju", "type_name": "重生民国"},
            {"type_id": "chuanyuexiandaiduanju", "type_name": "穿越现代"},
            {"type_id": "fanzhuanshuangjuduanju", "type_name": "反转爽剧"},
            {"type_id": "yanqingzongcaiduanju", "type_name": "言情总裁"},
            {"type_id": "xiandaidoushiduanju", "type_name": "现代都市"},
            {"type_id": "guzhuangxianxiaduanju", "type_name": "古装仙侠"},
            {"type_id": "xuanyishaonaoduanju", "type_name": "悬疑烧脑"},
            {"type_id": "chinajuchang", "type_name": "大陆剧"},
            {"type_id": "chinaxianggang", "type_name": "香港剧"},
            {"type_id": "hanju", "type_name": "韩剧"},
            {"type_id": "oumeidianshiju", "type_name": "欧美剧"},
            {"type_id": "japanju", "type_name": "日本剧"},
            {"type_id": "taiju", "type_name": "泰国剧"},
            {"type_id": "chtaiwan", "type_name": "台湾剧"},
            {"type_id": "fenjiduanju", "type_name": "短剧集"},
            {"type_id": "othersju", "type_name": "其它剧"}
        ]
        self.filters = {}
        self._session = None

    def getName(self):
        return "超好看影视"

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
        # 解析"正在热播"和"最新上线视频"中的视频
        # 使用正则提取视频块
        pattern = r'<a href="([^"]+)" title="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<strong class="title">(.*?)</strong>'
        matches = re.findall(pattern, html, re.DOTALL)
        seen = set()
        for match in matches:
            link, title, pic, name = match
            if link in seen:
                continue
            seen.add(link)
            vod_id = link.strip("/").split("/")[-1] if link else ""
            if not vod_id:
                continue
            items.append({
                "vod_id": vod_id,
                "vod_name": name.strip() or title.strip(),
                "vod_pic": urljoin(self.host, pic.strip()) if pic else "",
                "vod_remarks": ""
            })
            if len(items) >= 20:
                break
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        """分类列表"""
        page = int(pg) if pg and str(pg).isdigit() else 1
        if page < 1:
            page = 1

        # tid 是拼音，直接构建URL
        # 判断是电影还是电视剧：在 self.classes 中查找
        is_serials = tid in ["chinajuchang", "chinaxianggang", "hanju", "oumeidianshiju", "japanju", "taiju", "chtaiwan", "fenjiduanju", "othersju"]
        if is_serials:
            url = f"{self.host}/serials_videos/categories/{tid}/{page}/"
        else:
            url = f"{self.host}/videos/categories/{tid}/{page}/"

        resp = self.fetch(url, headers=self.headers, timeout=10)
        if resp.status_code != 200:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        html = resp.text
        items = []
        # 解析视频列表项
        pattern = r'<div class="item">.*?<a href="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<strong class="title">(.*?)</strong>.*?<div class="added"><em>(.*?)</em></div>.*?<div class="views">(.*?)</div>'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            link, pic, title, added, views = match
            vod_id = link.strip("/").split("/")[-1] if link else ""
            if not vod_id:
                continue
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, pic.strip()) if pic else "",
                "vod_remarks": views.strip() if views else added.strip() if added else ""
            })

        # 解析分页信息 - 从"最后"链接提取总页数
        pagecount = 1
        last_pattern = r'<li class="last"><a href="[^"]*/categories/[^/]+/(\d+)/"'
        last_match = re.search(last_pattern, html)
        if last_match:
            pagecount = int(last_match.group(1))
        else:
            # 尝试从分页链接中提取最大页数
            page_links = re.findall(r'<li class="page"><a href="[^"]*/categories/[^/]+/(\d+)/"', html)
            if page_links:
                pagecount = max(int(p) for p in page_links)
            # 检查是否有"更多"链接
            more_pattern = r'<a[^>]*href="[^"]*/categories/[^/]+/(\d+)/"[^>]*>.*?</a>'
            more_matches = re.findall(more_pattern, html)
            if more_matches:
                pagecount = max(int(p) for p in more_matches)

        return {
            "list": items,
            "page": page,
            "pagecount": pagecount,
            "limit": 20,
            "total": len(items) * pagecount if items else 0
        }

    def detailContent(self, ids):
        """详情页"""
        if not ids:
            return {"list": []}
        vod_id = str(ids[0])
        # 如果 ids[0] 包含管道符，解析出真实的 vod_id
        if '|' in vod_id:
            parts = vod_id.split('|')
            vod_id = parts[0]
        url = f"{self.host}/video/{vod_id}/"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if resp.status_code != 200:
            return {"list": []}
        html = resp.text

        # 提取标题
        title_match = re.search(r'<h1>(.*?)</h1>', html)
        title = title_match.group(1).strip() if title_match else ""

        # 提取封面
        pic_match = re.search(r'<img[^>]*class="thumb"[^>]*src="([^"]+)"', html)
        pic = urljoin(self.host, pic_match.group(1)) if pic_match else ""

        # 提取播放地址 - 优先 flashvars
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

        # 构建详情数据
        vod = {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": "",
            "vod_content": "",
            "vod_play_from": "播放",
            "vod_play_url": f"播放${play_url}" if play_url else ""
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        """搜索"""
        if not key:
            return {"list": [], "page": 1}
        page = int(pg) if str(pg).isdigit() else 1
        url = f"{self.host}/search/?q={quote(key)}&page={page}"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if resp.status_code != 200:
            return {"list": [], "page": page}
        html = resp.text
        items = []
        # 解析搜索结果
        pattern = r'<div class="item">.*?<a href="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<strong class="title">(.*?)</strong>.*?<div class="added"><em>(.*?)</em></div>.*?<div class="views">(.*?)</div>'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            link, pic, title, added, views = match
            vod_id = link.strip("/").split("/")[-1] if link else ""
            if not vod_id:
                continue
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, pic.strip()) if pic else "",
                "vod_remarks": views.strip() if views else added.strip() if added else ""
            })
        return {"list": items, "page": page}

    def playerContent(self, flag, id, vipFlags):
        """播放器"""
        id = str(id) if id is not None else ""
        if not id:
            return {"parse": 0, "url": "", "header": self.headers}
        # 如果 id 是完整的 URL 或 m3u8 地址
        if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
            # 走代理解决防盗链和相对路径问题
            proxy_url = self.getProxyUrl() + "&url=" + quote(id, safe="")
            return {"parse": 0, "url": proxy_url, "header": {}}
        # 如果 id 是 vod_id，尝试从详情页获取播放地址
        url = f"{self.host}/video/{id}/"
        resp = self.fetch(url, headers=self.headers, timeout=10)
        if resp.status_code != 200:
            return {"parse": 0, "url": "", "header": self.headers}
        html = resp.text
        play_url = ""
        # 优先从 flashvars.video_url 提取（支持单引号和双引号）
        flash_match = re.search(r"video_url\s*:\s*['\"]([^'\"]+)['\"]", html)
        if flash_match:
            play_url = flash_match.group(1)
        if not play_url:
            # 从 videoObject.video.url 提取
            url_match = re.search(r"video\s*:\s*\{\s*[^}]*url\s*:\s*['\"]([^'\"]+)['\"]", html, re.DOTALL)
            if url_match:
                play_url = url_match.group(1)
        if not play_url:
            # 从 videoObject 中提取更广泛的模式
            url_match = re.search(r"url\s*:\s*['\"]([^'\"]+\.m3u8)['\"]", html)
            if url_match:
                play_url = url_match.group(1)
        if play_url:
            # 走代理
            proxy_url = self.getProxyUrl() + "&url=" + quote(play_url, safe="")
            return {"parse": 0, "url": proxy_url, "header": {}}
        # 降级嗅探
        return {"parse": 1, "url": url, "header": self.headers}

    def recommendContent(self, ids, pg):
        """相关推荐"""
        # 简单实现：返回空列表
        return {"list": []}

    def localProxy(self, params):
        """m3u8 代理 - 解决防盗链和相对路径问题"""
        if not params:
            return [404, "text/plain", b"not found"]
        target = params.get("url", "")
        if not target or not target.startswith("http"):
            return [400, "text/plain", b"invalid url"]
        # 防盗链头
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
            # 改写分片地址为绝对地址
            lines = text.splitlines()
            out_lines = []
            base_url = target.rsplit("/", 1)[0] + "/"
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    # 处理 KEY 和 MAP 的 URI
                    if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
                        def repl(m):
                            uri = m.group(1)
                            if not uri.startswith("http"):
                                uri = urljoin(base_url, uri)
                            return f'URI="{uri}"'
                        line = re.sub(r'URI="([^"]+)"', repl, line)
                    out_lines.append(line)
                else:
                    # 分片地址 - 改写为绝对地址
                    if not line.startswith("http"):
                        line = urljoin(base_url, line)
                    out_lines.append(line)
            result = "\n".join(out_lines)
            return [200, "application/vnd.apple.mpegurl", result.encode("utf-8")]
        except Exception as e:
            self.log("localProxy error: " + str(e))
            return [500, "text/plain", b"proxy error"]
