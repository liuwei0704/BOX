# coding: utf-8
# 站点信息沉淀（法则24）
# 主域名: https://www.caosesp.sbs/
# 备用域名: www.caosesp.cam (maccms 配置中)
# 发布页: 无
# 内容类型: 影视 (成人)
# 特殊说明: MacCMS 标准站，player_aaaa 直链，无广告特征，无需 localProxy
# 最后验证时间: 2026-09-05
# 来源: 用户提供

import json
import re
from urllib.parse import urljoin, quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        # __init__ 零网络依赖，只做本地初始化
        self.host = "https://www.caosesp.sbs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        # 分类硬编码（法则16/17）
        self.classes = [
            {"type_id": "20", "type_name": "热门福利"},
            {"type_id": "1", "type_name": "国产精品"},
            {"type_id": "2", "type_name": "精品传媒"},
            {"type_id": "3", "type_name": "精选网红"},
            {"type_id": "4", "type_name": "偷拍自拍"},
            {"type_id": "5", "type_name": "精品探花"},
            {"type_id": "6", "type_name": "大秀视频"},
            {"type_id": "7", "type_name": "自慰系列"},
            {"type_id": "8", "type_name": "颜值正义"},
            {"type_id": "9", "type_name": "中文字幕"},
            {"type_id": "10", "type_name": "熟女少妇"},
            {"type_id": "11", "type_name": "制服诱惑"},
            {"type_id": "12", "type_name": "教师师生"},
            {"type_id": "13", "type_name": "精选日韩"},
            {"type_id": "14", "type_name": "欧美JAV"},
            {"type_id": "15", "type_name": "动漫专区"},
            {"type_id": "16", "type_name": "AI明星换脸"},
            {"type_id": "17", "type_name": "反差母狗"},
        ]
        # filters 结构（空，站点无筛选）
        self.filters = {str(cls["type_id"]): [] for cls in self.classes}
        # m3u8 分析结论：无广告特征，不需要清洗
        self.NEED_CLEAN = False

    def getName(self):
        return "草色福利视频"

    def getDependence(self):
        return []

    def init(self, extend=""):
        """init 零网络依赖"""
        self.extend = extend or ""
        pass

    def homeContent(self, filter):
        """homeContent 零网络依赖，快速返回分类"""
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐：从首页抓取视频列表"""
        url = self.host + "/"
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if resp.status_code != 200:
                return {"list": []}
        except Exception:
            return {"list": []}

        html = resp.text
        items = []

        # 使用更安全的正则，避免灾难性回溯
        # 匹配 .module-item 容器
        pattern = r'<a[^>]*href="(/index\.php/vod/detail/id/\d+\.html)"[^>]*title="([^"]*)"[^>]*>'
        matches = re.findall(pattern, html, re.S)
        
        for link, title in matches[:20]:
            if not title:
                continue
            vod_id = link.split("/")[-1].replace(".html", "")
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": "",
                "vod_remarks": ""
            })

        # 尝试提取图片
        img_pattern = r'<img[^>]*data-src="([^"]+)"[^>]*>'
        imgs = re.findall(img_pattern, html, re.S)
        for i, item in enumerate(items):
            if i < len(imgs):
                item["vod_pic"] = urljoin(self.host, imgs[i])

        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        """分类列表：使用实测的分页 URL 格式"""
        page = pg or "1"
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        # 如果 page=1，也可以使用不带 page 的 URL，但带 page 也能正常工作
        # 为了统一，全部使用带 page 的格式

        resp = self.fetch(url, headers=self.headers, timeout=15)
        if resp.status_code != 200:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

        html = resp.text
        items = []

        # 提取所有详情链接和标题
        pattern = r'<a[^>]*href="(/index\.php/vod/detail/id/\d+\.html)"[^>]*title="([^"]*)"[^>]*>'
        matches = re.findall(pattern, html)

        # 提取图片
        img_pattern = r'<img[^>]*data-src="([^"]+)"[^>]*>'
        imgs = re.findall(img_pattern, html)

        seen = set()
        for i, (link, title) in enumerate(matches):
            if not title or link in seen:
                continue
            seen.add(link)
            vod_id = link.split("/")[-1].replace(".html", "")
            pic = imgs[i] if i < len(imgs) else ""
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, pic) if pic else "",
                "vod_remarks": ""
            })
            if len(items) >= 30:
                break

        # 提取总页数：查找 "尾页" 链接
        pagecount = 1
        last_page_pattern = r'<a[^>]*href="[^"]*page/(\d+)\.html"[^>]*class="[^"]*page-last[^"]*"[^>]*>尾页</a>'
        last_match = re.search(last_page_pattern, html)
        if last_match:
            pagecount = int(last_match.group(1))
        else:
            # 如果没有 "尾页"，尝试查找 "下一页" 链接，然后加 1
            next_pattern = r'<a[^>]*href="[^"]*page/(\d+)\.html"[^>]*class="[^"]*page-next[^"]*"[^>]*>下一页</a>'
            next_match = re.search(next_pattern, html)
            if next_match:
                # 当前页 = 下一页页码 - 1，总页数至少是下一页页码
                next_page = int(next_match.group(1))
                if next_page > 1:
                    pagecount = next_page  # 至少有这么多的页

        return {
            "list": items,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 20,
            "total": len(items) * pagecount
        }

    def detailContent(self, ids):
        """详情页：多线路提取"""
        vod_id = str(ids[0]).strip()
        url = f"{self.host}/index.php/vod/detail/id/{vod_id}.html"

        resp = self.fetch(url, headers=self.headers, timeout=10)
        if resp.status_code != 200:
            return {"list": []}

        html = resp.text

        # 提取标题
        title_match = re.search(r'<h1[^>]*class="[^"]*page-title[^"]*"[^>]*>(.*?)</h1>', html, re.S)
        title = title_match.group(1).strip() if title_match else ""

        # 提取封面
        pic_match = re.search(r'<img[^>]*data-src="([^"]+)"[^>]*class="[^"]*lazyload[^"]*"[^>]*>', html, re.S)
        pic = urljoin(self.host, pic_match.group(1)) if pic_match else ""

        # 提取简介
        content_match = re.search(r'<span[^>]*class="[^"]*video-desc[^"]*"[^>]*>(.*?)</span>', html, re.S)
        content = content_match.group(1).strip() if content_match else ""

        # 提取线路和选集
        # MacCMS 站点通常在详情页有线路 tab，但此处播放链接在播放页
        # 直接构造播放链接
        play_url = f"{self.host}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"

        vod = {
            "vod_id": vod_id,
            "vod_name": title or "视频",
            "vod_pic": pic,
            "vod_remarks": "",
            "vod_content": content,
            "vod_play_from": "播放",
            "vod_play_url": f"第1集${play_url}"
        }

        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        """搜索：从搜索页提取视频列表"""
        if not key:
            return {"list": [], "page": 1}

        url = f"{self.host}/index.php/vod/search.html"
        params = {"wd": key}
        resp = self.fetch(url, params=params, headers=self.headers, timeout=15)

        if resp.status_code != 200:
            return {"list": [], "page": 1}

        html = resp.text
        items = []

        # 提取所有详情链接和标题
        pattern = r'<a[^>]*href="(/index\.php/vod/detail/id/\d+\.html)"[^>]*title="([^"]*)"[^>]*>'
        matches = re.findall(pattern, html)

        # 提取图片
        img_pattern = r'<img[^>]*data-src="([^"]+)"[^>]*>'
        imgs = re.findall(img_pattern, html)

        seen = set()
        for i, (link, title) in enumerate(matches):
            if not title or link in seen:
                continue
            seen.add(link)
            vod_id = link.split("/")[-1].replace(".html", "")
            pic = imgs[i] if i < len(imgs) else ""
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, pic) if pic else "",
                "vod_remarks": ""
            })
            if len(items) >= 30:
                break

        return {"list": items, "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        """播放：从 player_aaaa 提取 m3u8 直链"""
        if not id:
            return {"parse": 1, "url": "", "header": {}}

        play_url = id if id.startswith("http") else urljoin(self.host, id)
        resp = self.fetch(play_url, headers=self.headers, timeout=15)

        if resp.status_code != 200:
            return {"parse": 1, "url": play_url, "header": self.headers}

        html = resp.text

        # L2: 提取 player_aaaa 对象 - 使用平衡括号匹配
        # 先找到 var player_aaaa= 的位置
        start_pattern = r'var\s+player_aaaa\s*=\s*'
        start_match = re.search(start_pattern, html)
        if start_match:
            start_idx = start_match.end()
            # 从 start_idx 开始查找第一个 '{'
            brace_idx = html.find("{", start_idx)
            if brace_idx != -1:
                # 使用平衡括号匹配提取完整的 JSON
                raw = self._grab_json_object(html, brace_idx)
                if raw:
                    try:
                        # 处理转义字符
                        raw = raw.replace("\\/", "/")
                        raw = raw.replace("\\n", "").replace("\\r", "")
                        player_data = json.loads(raw)
                        m3u8_url = player_data.get("url", "")
                        if m3u8_url and ".m3u8" in m3u8_url.lower() and m3u8_url.startswith("http"):
                            return {
                                "parse": 0,
                                "url": m3u8_url,
                                "header": {"User-Agent": self.headers["User-Agent"]}
                            }
                    except json.JSONDecodeError:
                        # 如果 JSON 解析失败，尝试用正则提取 URL
                        url_pattern = r'"url":"([^"]+\.m3u8[^"]*)"'
                        url_match = re.search(url_pattern, raw)
                        if url_match:
                            m3u8_url = url_match.group(1).replace("\\/", "/")
                            if m3u8_url.startswith("http"):
                                return {
                                    "parse": 0,
                                    "url": m3u8_url,
                                    "header": {"User-Agent": self.headers["User-Agent"]}
                                }

        # L5: 全文正则兜底 - 只匹配 .m3u8 地址
        pattern2 = r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*'
        match2 = re.search(pattern2, html)
        if match2:
            m3u8_url = match2.group(0)
            if "安全中心" not in m3u8_url and "search" not in m3u8_url:
                return {
                    "parse": 0,
                    "url": m3u8_url,
                    "header": {"User-Agent": self.headers["User-Agent"]}
                }

        # 降级：parse:1 嗅探
        return {
            "parse": 1,
            "url": play_url,
            "header": self.headers
        }

    def _grab_json_object(self, text, start_idx):
        """从指定位置开始，使用平衡括号匹配提取完整的 JSON 对象"""
        if start_idx < 0 or start_idx >= len(text) or text[start_idx] != "{":
            return ""
        depth = 0
        in_str = False
        escape = False
        for i in range(start_idx, len(text)):
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]
        return ""

    def recommendContent(self, ids, pg):
        """相关推荐"""
        # 简化实现：从首页获取推荐
        return self.homeVideoContent()

    def destroy(self):
        """释放资源"""
        pass