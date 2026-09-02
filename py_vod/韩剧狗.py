# coding: utf-8
# 韩剧狗 - TVBox/FongMi 爬虫
# 站点: https://www.hanjugo.com
# 类型: MacCMS 标准影视站
# 特点: 无加密、无广告m3u8、静态HTML
# 验证时间: 2026-09-03

import re
import json
from urllib.parse import quote, urljoin, urlparse

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://www.hanjugo.com"
        self.site_name = "韩剧狗"
        self.classes = [
            {"type_id": "dianying", "type_name": "电影"},
            {"type_id": "lianxuju", "type_name": "连续剧"},
            {"type_id": "zongyi", "type_name": "综艺"},
            {"type_id": "dongman", "type_name": "动漫"},
            {"type_id": "duanju", "type_name": "短剧"},
            {"type_id": "aimanju", "type_name": "AI漫剧"},
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
        }

    def getName(self):
        return "韩剧狗"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐 - 从'韩剧狗推荐'区域取前12条"""
        html = self._fetch_html(self.host + "/")
        items = self._parse_home_recommend(html)
        return {"list": items[:12]}

    def categoryContent(self, tid, pg, filter, extend):
        pg = str(pg) if pg else "1"
        url = f"{self.host}/list/{tid}-{pg}.html"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        # 分页: 从页面分页器提取总页数
        total_pages = self._parse_total_pages(html)
        if total_pages < 1:
            total_pages = 1
        return {
            "list": items,
            "page": int(pg),
            "pagecount": total_pages,
            "limit": 20,
            "total": total_pages * 20,
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0]) if isinstance(ids, list) else str(ids)
        url = f"{self.host}/k/{vid}.html"
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        return self._parse_detail(html, vid)

    def searchContent(self, key, quick, pg="1"):
        pg = str(pg) if pg else "1"
        url = f"{self.host}/s/{quote(key)}-------------.html"
        html = self._fetch_html(url)
        items = self._parse_search_results(html)
        return {"list": items, "page": int(pg)}
    def playerContent(self, flag, id, vipFlags):
        """
        播放地址解析 - 从 player_data 提取 m3u8 直链
        """
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        
        # 如果已是直链
        if id.startswith("http") and ".m3u8" in id.lower():
            return {
                "parse": 0,
                "url": id,
                "header": {"User-Agent": self.headers.get("User-Agent", "")}
            }
        
        # 补全播放页完整 URL
        if not id.startswith("http"):
            full_url = urljoin(self.host, id)
        else:
            full_url = id
        
        # 请求播放页
        html = self._fetch_html(full_url, timeout=10)
        if html:
            m3u8_url = self._extract_m3u8_from_player(html, full_url)
            if m3u8_url:
                return {
                    "parse": 0,
                    "url": m3u8_url,
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }
        
        # 如果 id 是 vod_id（数字），尝试从详情页获取播放链接
        if str(id).isdigit():
            detail_url = f"{self.host}/k/{id}.html"
            html = self._fetch_html(detail_url)
            if html:
                ep_links = re.findall(r'<a[^>]*class="btn[^"]*"[^>]*href="([^"]+)"[^>]*>', html)
                for link in ep_links:
                    if "/b/" in link:
                        play_url = urljoin(self.host, link)
                        play_html = self._fetch_html(play_url, timeout=10)
                        if play_html:
                            m3u8_url = self._extract_m3u8_from_player(play_html, play_url)
                            if m3u8_url:
                                return {
                                    "parse": 0,
                                    "url": m3u8_url,
                                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                                }
        
        # 降级嗅探
        return {"parse": 1, "url": id, "header": self.headers}
    def recommendContent(self, ids, pg):
        """相关推荐 - 取详情页'猜你喜欢'区域"""
        if not ids:
            return {"list": []}
        vid = str(ids[0]) if isinstance(ids, list) else str(ids)
        url = f"{self.host}/k/{vid}.html"
        html = self._fetch_html(url)
        items = self._parse_recommend(html)
        return {"list": items}

    def destroy(self):
        """释放资源"""
        pass

    # ==================== 内部辅助方法 ====================

    def _fetch_html(self, url, timeout=15):
        try:
            resp = self.fetch(url, headers=self.headers, timeout=timeout)
            if resp and hasattr(resp, "status_code") and resp.status_code == 200:
                return resp.text
            if resp and hasattr(resp, "text"):
                return resp.text
        except Exception as e:
            pass
        return ""

    def _parse_video_list(self, html):
        """解析视频列表 - 适用于 categoryContent 和 searchContent"""
        items = []
        if not html:
            return items
        
        # 匹配每个视频项
        pattern = r'<li[^>]*class="[^"]*col-lg-[^"]*"[^>]*>.*?<a[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*data-original="([^"]*)"[^>]*>.*?<span[^>]*class="pic-text[^"]*"[^>]*>([^<]*)</span>.*?</a>.*?<div[^>]*class="myui-vodlist__detail"[^>]*>.*?<h4[^>]*class="title[^"]*"[^>]*>.*?<a[^>]*href="[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for link, title_attr, pic, status, title in matches:
            # 提取 vod_id
            vid_match = re.search(r'/k/(\d+)\.html', link)
            if not vid_match:
                continue
            vod_id = vid_match.group(1)
            vod_name = title.strip() or title_attr.strip()
            items.append({
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": pic,
                "vod_remarks": status.strip(),
            })
        return items

    def _parse_home_recommend(self, html):
        """解析首页'韩剧狗推荐'区域"""
        items = []
        if not html:
            return items
        # 定位推荐区域
        pattern = r'<h3[^>]*class="title"[^>]*>韩剧狗推荐</h3>.*?<ul[^>]*class="myui-vodlist[^"]*"[^>]*>(.*?)</ul>'
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            return items
        block = match.group(1)
        # 解析每个视频
        item_pattern = r'<li[^>]*class="[^"]*col-lg-[^"]*"[^>]*>.*?<a[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*data-original="([^"]*)"[^>]*>.*?<span[^>]*class="pic-text[^"]*"[^>]*>([^<]*)</span>'
        matches = re.findall(item_pattern, block, re.DOTALL)
        for link, title, pic, status in matches:
            vid_match = re.search(r'/k/(\d+)\.html', link)
            if vid_match:
                items.append({
                    "vod_id": vid_match.group(1),
                    "vod_name": title.strip(),
                    "vod_pic": pic,
                    "vod_remarks": status.strip(),
                })
        return items

    def _parse_search_results(self, html):
        """解析搜索结果 - 专门处理 myui-vodlist__media 结构"""
        items = []
        if not html:
            return items
        
        # 搜索页结构: <ul class="myui-vodlist__media" id="searchList">
        # 每个 li 包含 thumb 和 detail
        pattern = r'<li[^>]*class="clearfix"[^>]*>.*?<a[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*data-original="([^"]*)"[^>]*>.*?<span[^>]*class="pic-text[^"]*"[^>]*>([^<]*)</span>.*?</a>.*?<div[^>]*class="detail"[^>]*>.*?<h4[^>]*class="title"[^>]*>.*?<a[^>]*href="[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for link, title_attr, pic, status, title in matches:
            vid_match = re.search(r'/k/(\d+)\.html', link)
            if not vid_match:
                continue
            vod_id = vid_match.group(1)
            vod_name = title.strip() or title_attr.strip()
            items.append({
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": pic,
                "vod_remarks": status.strip(),
            })
        return items
    def _parse_detail(self, html, vid):
        """解析详情页"""
        vod = {
            "vod_id": vid,
            "vod_name": "",
            "vod_pic": "",
            "vod_remarks": "",
            "vod_actor": "",
            "vod_director": "",
            "vod_content": "",
            "vod_play_from": "",
            "vod_play_url": "",
        }
        
        # 标题
        title_match = re.search(r'<h1[^>]*class="title"[^>]*>([^<]+)</h1>', html)
        if title_match:
            vod["vod_name"] = title_match.group(1).strip()
        
        # 封面
        pic_match = re.search(r'<img[^>]*class="[^"]*lazyload[^"]*"[^>]*data-original="([^"]+)"', html)
        if pic_match:
            vod["vod_pic"] = pic_match.group(1)
        
        # 分类/地区/年份
        data_pattern = r'<p[^>]*class="data"[^>]*>.*?分类：([^<]+)</span>.*?地区：([^<]+)</span>.*?年份：([^<]+)</span>'
        data_match = re.search(data_pattern, html, re.DOTALL)
        if data_match:
            vod["vod_remarks"] = f"{data_match.group(1).strip()} | {data_match.group(2).strip()} | {data_match.group(3).strip()}"
        
        # 主演
        actor_match = re.search(r'<p[^>]*class="data"[^>]*>.*?主演：([^<]+)</p>', html, re.DOTALL)
        if actor_match:
            vod["vod_actor"] = actor_match.group(1).strip()
        
        # 导演
        director_match = re.search(r'<p[^>]*class="data"[^>]*>.*?导演：([^<]+)</p>', html, re.DOTALL)
        if director_match:
            vod["vod_director"] = director_match.group(1).strip()
        
        # 简介
        content_match = re.search(r'<span[^>]*class="sketch content"[^>]*>([^<]*)</span>', html, re.DOTALL)
        if content_match:
            vod["vod_content"] = content_match.group(1).strip()
        
        # 播放地址 - 提取所有线路
        play_from_list = []
        play_url_list = []
        
        # 线路名称
        tab_pattern = r'<ul[^>]*class="nav nav-tabs[^"]*"[^>]*>.*?<a[^>]*href="#playlist(\d+)"[^>]*>([^<]+)</a>'
        tabs = re.findall(tab_pattern, html, re.DOTALL)
        
        # 剧集链接
        ep_pattern = r'<ul[^>]*class="myui-content__list[^"]*"[^>]*>.*?<a[^>]*class="btn[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        eps = re.findall(ep_pattern, html, re.DOTALL)
        
        if tabs and eps:
            # 有线路分组
            for tab_idx, (tab_id, tab_name) in enumerate(tabs):
                play_from_list.append(tab_name.strip())
                # 匹配该线路下的剧集
                pattern = rf'<div[^>]*id="playlist{tab_id}"[^>]*>.*?<ul[^>]*class="myui-content__list[^"]*"[^>]*>(.*?)</ul>'
                block_match = re.search(pattern, html, re.DOTALL)
                if block_match:
                    block = block_match.group(1)
                    ep_matches = re.findall(r'<a[^>]*class="btn[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', block, re.DOTALL)
                    if ep_matches:
                        episodes = []
                        for ep_link, ep_name in ep_matches:
                            episodes.append(f"{ep_name.strip()}${urljoin(self.host, ep_link)}")
                        play_url_list.append("#".join(episodes))
                    else:
                        play_url_list.append("")
                else:
                    play_url_list.append("")
        else:
            # 无线路分组，直接取所有剧集
            if eps:
                play_from_list.append("播放")
                episodes = []
                for ep_link, ep_name in eps:
                    episodes.append(f"{ep_name.strip()}${urljoin(self.host, ep_link)}")
                play_url_list.append("#".join(episodes))
        
        if play_from_list and play_url_list:
            vod["vod_play_from"] = "$$$".join(play_from_list)
            vod["vod_play_url"] = "$$$".join(play_url_list)
        
        return {"list": [vod]}

    def _parse_total_pages(self, html):
        """解析总页数"""
        if not html:
            return 1
        # 匹配分页器中的最大页码
        pattern = r'<a[^>]*href="[^"]*-\d+\.html"[^>]*>(\d+)</a>'
        matches = re.findall(pattern, html)
        if matches:
            return int(matches[-1])
        # 尝试匹配 "1/N" 格式
        pattern2 = r'(\d+)\s*/\s*(\d+)'
        match2 = re.search(pattern2, html)
        if match2:
            return int(match2.group(2))
        return 1

    def _extract_m3u8_from_player(self, html, page_url=None):
        """从播放页提取 m3u8 地址"""
        if not html:
            return None
        
        # 方法1: 从 player_data 中提取 url 字段
        # 匹配 "url":"https:\/\/xxx.m3u8" 或 "url":"http:\/\/xxx.m3u8"
        url_pattern = r'"url"\s*:\s*"(https?:\\/\\/[^"]+\.m3u8[^"]*)"'
        url_match = re.search(url_pattern, html)
        if url_match:
            m3u8_url = url_match.group(1).replace('\\/', '/')
            if m3u8_url.startswith("http") and ".m3u8" in m3u8_url:
                return m3u8_url
        
        # 方法2: 使用 player_data 变量解析（备用）
        player_pattern = r'var\s+player_data\s*=\s*(\{[^;]+\});'
        player_match = re.search(player_pattern, html, re.DOTALL)
        if player_match:
            try:
                json_str = player_match.group(1).replace('\\/', '/')
                data = json.loads(json_str)
                url = data.get("url", "")
                if url and url.startswith("http") and ".m3u8" in url:
                    return url
            except Exception:
                pass
        
        # 方法3: 从 iframe 中提取
        iframe_pattern = r'<iframe[^>]*src="([^"]+)"[^>]*>'
        iframe_matches = re.findall(iframe_pattern, html)
        for src in iframe_matches:
            if "url=" in src:
                m3u8_match = re.search(r'[?&]url=([^&]+)', src)
                if m3u8_match:
                    from urllib.parse import unquote
                    m3u8_url = unquote(m3u8_match.group(1))
                    if ".m3u8" in m3u8_url:
                        return m3u8_url
            if ".m3u8" in src:
                return src
        
        # 方法4: 直接找任何 m3u8 链接（含转义）
        m3u8_pattern = r'https?:\\?/\\?/[^"\']+\.m3u8[^"\']*'
        m3u8_match = re.search(m3u8_pattern, html)
        if m3u8_match:
            return m3u8_match.group(0).replace('\\/', '/')
        
        return None
    def _parse_recommend(self, html):
        """解析详情页'猜你喜欢'推荐"""
        items = []
        if not html:
            return items
        
        # 定位"猜你喜欢"区域 - 取第一个tab（同类型）
        pattern = r'<h3[^>]*class="title"[^>]*>猜你喜欢</h3>.*?<ul[^>]*id="type"[^>]*class="[^"]*myui-vodlist__bd[^"]*"[^>]*>(.*?)</ul>'
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            return items
        block = match.group(1)
        
        item_pattern = r'<li[^>]*class="[^"]*col-lg-[^"]*"[^>]*>.*?<a[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*data-original="([^"]*)"[^>]*>.*?<span[^>]*class="pic-text[^"]*"[^>]*>([^<]*)</span>'
        matches = re.findall(item_pattern, block, re.DOTALL)
        for link, title, pic, status in matches:
            vid_match = re.search(r'/k/(\d+)\.html', link)
            if vid_match:
                items.append({
                    "vod_id": vid_match.group(1),
                    "vod_name": title.strip(),
                    "vod_pic": pic,
                    "vod_remarks": status.strip(),
                })
        return items