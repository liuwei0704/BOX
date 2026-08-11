# coding: utf-8
"""
站点: 良家视频
域名: https://xn--k-ei0bs27bx0a.liangjia.click/
备用域名: www.sq84.com, u.liangjia.one, o.liangjia.xyz
类型: 成人短视频/影视站 (蚂蚁视频CMS)
版本: 1.0
说明: 支持分类浏览、详情、搜索、播放
"""

import re
import json
from urllib.parse import urljoin, quote, unquote

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://xn--k-ei0bs27bx0a.liangjia.click"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        # 分类硬编码 - 从导航栏提取
        self.classes = [
            {"type_id": "yuanchuang", "type_name": "本站原创"},
            {"type_id": "luoli", "type_name": "萝莉少女"},
            {"type_id": "chigua", "type_name": "吃瓜黑料"},
            {"type_id": "tanhua", "type_name": "探花系列"},
            {"type_id": "luanlun", "type_name": "乱伦系列"},
            {"type_id": "guochan", "type_name": "国产自拍"},
            {"type_id": "juru", "type_name": "巨乳熟女"},
            {"type_id": "duanshipin", "type_name": "短视频"}
        ]
        # 筛选 - 站点无筛选功能，返回空
        self.filters = {tid: [] for tid in ["yuanchuang", "luoli", "chigua", "tanhua", "luanlun", "guochan", "juru", "duanshipin"]}

    def getName(self):
        return "良家视频"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐数据"""
        try:
            res = self.fetch(self.host + "/", headers=self.headers)
            if not res or res.status_code != 200:
                return {"list": []}
            html = res.text
            items = self._parse_video_list(html)
            return {"list": items[:20] if len(items) > 20 else items}
        except Exception as e:
            self.log({"action": "homeVideoContent", "error": str(e)})
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/category/{tid}?page={page}"
        try:
            res = self.fetch(url, headers=self.headers)
            if not res or res.status_code != 200:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            html = res.text
            items = self._parse_video_list(html)
            # 提取分页信息
            pagecount = self._parse_page_count(html)
            return {
                "list": items,
                "page": int(page),
                "pagecount": pagecount or 1,
                "limit": 20,
                "total": 0
            }
        except Exception as e:
            self.log({"action": "categoryContent", "tid": tid, "pg": page, "error": str(e)})
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        """详情页 - 提取播放地址"""
        try:
            if isinstance(ids, list) and len(ids) > 0:
                vod_id = str(ids[0])
            elif isinstance(ids, str):
                vod_id = ids
            else:
                vod_id = str(ids)
            
            # 去除可能的前缀
            vod_id = re.sub(r'[^0-9]', '', vod_id)
            if not vod_id:
                return {"list": []}
            
            url = f"{self.host}/video/{vod_id}"
            res = self.fetch(url, headers=self.headers)
            if not res or res.status_code != 200:
                return {"list": []}
            html = res.text
            
            # 提取标题
            title = self._extract_title(html)
            # 提取播放地址
            play_url = self._extract_play_url(html)
            # 提取分类
            category = self._extract_category(html)
            # 提取描述
            desc = self._extract_description(html)
            
            vod = {
                "vod_id": vod_id,
                "vod_name": title or f"视频_{vod_id}",
                "vod_pic": "",
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": desc or "",
                "vod_play_from": "播放",
                "vod_play_url": f"播放${play_url}" if play_url else ""
            }
            return {"list": [vod]}
        except Exception as e:
            self.log({"action": "detailContent", "error": str(e)})
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        """搜索"""
        try:
            url = f"{self.host}/search"
            params = {"q": key}
            # 如果页码大于1，添加page参数
            if int(pg or 1) > 1:
                params["page"] = pg
            res = self.fetch(f"{url}?q={quote(key)}", headers=self.headers)
            if not res or res.status_code != 200:
                return {"list": [], "page": int(pg)}
            html = res.text
            items = self._parse_video_list(html)
            return {"list": items[:50] if len(items) > 50 else items, "page": int(pg)}
        except Exception as e:
            self.log({"action": "searchContent", "key": key, "error": str(e)})
            return {"list": [], "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        """播放"""
        if not id:
            return {"parse": 1, "url": "", "header": self.headers}
        
        # 如果已经是完整URL，直接播放
        if id.startswith("http://") or id.startswith("https://"):
            if id.endswith((".m3u8", ".mp4")):
                return {"parse": 0, "url": id, "header": self.headers}
            # 非媒体URL，尝试通过详情页提取
            return self._fetch_play_from_url(id)
        
        # 如果是ID，构造详情页URL提取
        if re.match(r"^\d+$", id):
            detail_url = f"{self.host}/video/{id}"
            return self._fetch_play_from_url(detail_url)
        
        # 可能是参数格式，尝试解析
        return {"parse": 1, "url": id, "header": self.headers}

    def _fetch_play_from_url(self, url):
        """从详情页提取播放地址"""
        try:
            res = self.fetch(url, headers=self.headers)
            if not res or res.status_code != 200:
                return {"parse": 1, "url": url, "header": self.headers}
            html = res.text
            play_url = self._extract_play_url(html)
            if play_url and play_url.startswith("http"):
                return {"parse": 0, "url": play_url, "header": self.headers}
            return {"parse": 1, "url": url, "header": self.headers}
        except Exception as e:
            self.log({"action": "_fetch_play_from_url", "error": str(e)})
            return {"parse": 1, "url": url, "header": self.headers}

    def _parse_video_list(self, html):
        """解析视频列表"""
        items = []
        # 匹配 a.video-card 结构
        pattern = r'<a[^>]*class="[^"]*video-card[^"]*"[^>]*href="([^"]+)"[^>]*data-preview="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<span[^>]*class="[^"]*duration[^"]*"[^>]*>([^<]*)</span>.*?<h3[^>]*class="[^"]*title[^"]*"[^>]*>([^<]*)</h3>'
        matches = re.findall(pattern, html, re.DOTALL)
        for href, preview, pic, duration, title in matches:
            if not href or not title:
                continue
            # 提取视频ID
            vod_id_match = re.search(r'/video/(\d+)', href)
            vod_id = vod_id_match.group(1) if vod_id_match else href
            # 从data-preview中提取m3u8地址
            play_url = self._extract_m3u8_from_preview(preview)
            items.append({
                "vod_id": str(vod_id),
                "vod_name": title.strip(),
                "vod_pic": pic if pic.startswith("http") else urljoin(self.host, pic) if pic else "",
                "vod_remarks": duration.strip() or ""
            })
        # 如果正则匹配失败，尝试备用模式
        if not items:
            items = self._parse_video_list_fallback(html)
        return items

    def _parse_video_list_fallback(self, html):
        """备用解析"""
        items = []
        # 匹配 a 标签
        a_pattern = r'<a[^>]*href="(/video/\d+)"[^>]*>'
        hrefs = re.findall(a_pattern, html)
        # 匹配标题
        title_pattern = r'<h3[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h3>'
        titles = re.findall(title_pattern, html)
        # 匹配图片
        img_pattern = r'<img[^>]*src="([^"]+)"[^>]*>'
        pics = re.findall(img_pattern, html)
        # 匹配时长
        duration_pattern = r'<span[^>]*class="[^"]*duration[^"]*"[^>]*>([^<]*)</span>'
        durations = re.findall(duration_pattern, html)
        
        # 找到视频卡片起始位置
        card_starts = [m.start() for m in re.finditer(r'<a[^>]*class="[^"]*video-card', html)]
        for i, href in enumerate(hrefs):
            if i >= len(titles):
                break
            vod_id_match = re.search(r'/video/(\d+)', href)
            vod_id = vod_id_match.group(1) if vod_id_match else href
            pic = pics[i] if i < len(pics) else ""
            duration = durations[i] if i < len(durations) else ""
            items.append({
                "vod_id": str(vod_id),
                "vod_name": titles[i].strip(),
                "vod_pic": pic if pic.startswith("http") else urljoin(self.host, pic) if pic else "",
                "vod_remarks": duration.strip() or ""
            })
        return items

    def _extract_m3u8_from_preview(self, preview):
        """从data-preview中提取m3u8地址"""
        if not preview:
            return ""
        # 解析URL参数
        match = re.search(r'url=([^&]+)', preview)
        if match:
            try:
                return unquote(match.group(1))
            except:
                return match.group(1)
        return ""

    def _parse_page_count(self, html):
        """解析总页数"""
        # 从分页中提取最大页数
        pattern = r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>(\d+)</a>'
        matches = re.findall(pattern, html)
        pages = [int(m[1]) for m in matches if m[1].isdigit()]
        if pages:
            return max(pages)
        # 尝试从"共XX页"提取
        page_match = re.search(r'共\s*(\d+)\s*页', html)
        if page_match:
            return int(page_match.group(1))
        return 1

    def _extract_play_url(self, html):
        """提取播放地址"""
        # 方法1: 从 window.__MAYI_PLAY_URL__ 提取
        play_match = re.search(r'window\.__MAYI_PLAY_URL__\s*=\s*"([^"]+)"', html)
        if play_match:
            url = play_match.group(1)
            # 如果是代理地址，提取真实m3u8
            if url.startswith("/hls/proxy"):
                m3u8 = self._extract_m3u8_from_preview(url)
                if m3u8:
                    return m3u8
            return url
        # 方法2: 从 video 标签 src 提取
        video_match = re.search(r'<video[^>]*src="([^"]+)"', html)
        if video_match:
            return video_match.group(1)
        # 方法3: 从 data-preview 属性提取（在列表页使用）
        preview_match = re.search(r'data-preview="([^"]*url=([^&]+)[^"]*)"', html)
        if preview_match:
            try:
                return unquote(preview_match.group(2))
            except:
                return preview_match.group(2)
        # 方法4: 从 iframe src 提取
        iframe_pattern = r'<iframe[^>]*src="([^"]+)"'
        iframes = re.findall(iframe_pattern, html)
        for src in iframes:
            if src.startswith("http") and (".m3u8" in src or "m3u8" in src):
                return src
        # 方法5: 从 script 中的 m3u8 URL 提取
        m3u8_pattern = r'https?://[^\s"\']+\.m3u8[^\s"\']*'
        m3u8_match = re.search(m3u8_pattern, html)
        if m3u8_match:
            return m3u8_match.group(0)
        return ""

    def _extract_title(self, html):
        """提取标题"""
        title_match = re.search(r'<h1[^>]*class="[^"]*play-title[^"]*"[^>]*>([^<]+)</h1>', html)
        if title_match:
            return title_match.group(1).strip()
        # 从title标签提取
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            t = title_match.group(1)
            t = re.sub(r'\s*-\s*良家视频\s*$', '', t)
            return t.strip()
        return ""

    def _extract_category(self, html):
        """提取分类"""
        cat_match = re.search(r'分类：<a[^>]*href="/category/([^"]+)"[^>]*>([^<]+)</a>', html)
        if cat_match:
            return cat_match.group(2).strip()
        return ""

    def _extract_description(self, html):
        """提取描述"""
        desc_match = re.search(r'<div[^>]*class="[^"]*play-desc[^"]*"[^>]*>([^<]+)</div>', html)
        if desc_match:
            return desc_match.group(1).strip()
        return ""

    def localProxy(self, param):
        """m3u8 本地代理 - 默认不处理"""
        return [400, "text/plain", b"not implemented"]

    def log(self, data):
        """日志记录"""
        try:
            print("[良家视频]", json.dumps(data, ensure_ascii=False))
        except:
            pass