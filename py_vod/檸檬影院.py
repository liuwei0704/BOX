# coding: utf-8
# 柠檬影院 - https://m.ydfdj.com
# 站点类型: 苹果CMS HTML站
# 分类: 电影(含子分类)、电视剧、综艺、动漫、短剧
# 分页: /show/{sid}--------{pg}---.html

import re
import json
from urllib.parse import urljoin, quote

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.site_url = "https://m.ydfdj.com"
        self.ua = "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.headers = {
            "User-Agent": self.ua,
            "Referer": self.site_url + "/"
        }
        
        # 主分类（首页显示的分类）
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "36", "type_name": "短剧"},
        ]
        
        # 主分类 → 子分类ID映射（用于分页）
        # /show/{sid} 支持分页，/type/ 不支持分页
        self.show_id_map = {
            "1": "6",   # 电影 → 动作片（默认子分类）
            "2": "13",  # 电视剧
            "3": "17",  # 综艺
            "4": "20",  # 动漫
            "36": "37", # 短剧
        }
        
        # 电影子分类（用于筛选）
        self.filters = {
            "1": [
                {
                    "key": "sub_category",
                    "name": "类型",
                    "value": [
                        {"n": "动作片", "v": "6"},
                        {"n": "喜剧片", "v": "7"},
                        {"n": "爱情片", "v": "8"},
                        {"n": "科幻片", "v": "9"},
                        {"n": "恐怖片", "v": "10"},
                        {"n": "剧情片", "v": "11"},
                        {"n": "战争片", "v": "12"},
                        {"n": "动画片", "v": "24"},
                    ]
                }
            ],
            "2": [],
            "3": [],
            "4": [],
            "36": [],
        }

    def getName(self):
        return "柠檬影院"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _fetch(self, url):
        """使用 self.fetch() 获取页面内容"""
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if resp and hasattr(resp, 'text') and resp.text:
                return resp.text
            if resp and hasattr(resp, 'content'):
                try:
                    return resp.content.decode('utf-8', errors='ignore')
                except:
                    pass
        except Exception as e:
            pass
        return ""

    def _parse_extend(self, extend):
        if not extend:
            return {}
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            try:
                return json.loads(extend)
            except:
                clean = extend.strip().strip('{}')
                result = {}
                if clean:
                    for part in clean.split(','):
                        if '=' in part:
                            key, val = part.split('=', 1)
                            result[key.strip()] = val.strip()
                return result
        return {}

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐 - 使用电影分类"""
        return self.categoryContent("1", "1", False, {})

    def categoryContent(self, tid, pg="1", filter=False, extend=None):
        page = str(pg or "1")
        tid = str(tid)
        
        # 解析extend参数，获取子分类ID
        extend_dict = self._parse_extend(extend)
        sub_category = extend_dict.get("sub_category", "")
        
        # 确定使用哪个分类ID进行分页
        # 如果有子分类，使用子分类ID；否则使用默认映射
        if sub_category and sub_category in self.show_id_map.values():
            show_id = sub_category
        elif tid in self.show_id_map:
            show_id = self.show_id_map[tid]
        else:
            show_id = tid
        
        # 构建分页URL
        # 格式: /show/{sid}--------{pg}---.html
        url = f"{self.site_url}/show/{show_id}--------{page}---.html"
        
        html = self._fetch(url)
        if not html:
            return {"list": [], "page": int(page), "pagecount": 1, "total": 0}

        videos = []
        # 匹配视频列表项
        li_pattern = r'<li class="col-md-6 col-sm-4 col-xs-3">.*?<a class="stui-vodlist__thumb[^"]*" href="(/det/\d+\.html)"[^>]*data-original="([^"]+)"[^>]*>.*?<span class="pic-text text-right">([^<]+)</span>.*?<p class="title text-overflow h4_add"><a[^>]*>([^<]+)</a>'
        
        for match in re.finditer(li_pattern, html, re.S):
            vod_url, pic, status, title = match.groups()
            if title and title.strip():
                # 修复相对路径图片
                if pic and pic.startswith("/"):
                    pic = self.site_url + pic
                videos.append({
                    "vod_id": vod_url,
                    "vod_name": title.strip(),
                    "vod_pic": pic,
                    "vod_remarks": status.strip(),
                })

        # 提取分页信息
        pagecount = 1
        
        # 方式1: 提取"共X页"
        page_match = re.search(r'共(\d+)页', html)
        if page_match:
            pagecount = int(page_match.group(1))
        else:
            # 方式2: 从分页链接中提取最大页码
            page_links = re.findall(r'/show/\d+--------(\d+)---\.html', html)
            if page_links:
                page_nums = [int(p) for p in page_links if p.isdigit()]
                if page_nums:
                    pagecount = max(page_nums)
            else:
                # 方式3: 查找尾页
                last_match = re.search(r'<a[^>]*href="[^"]*?/show/\d+--------(\d+)---\.html"[^>]*>尾页</a>', html)
                if last_match:
                    pagecount = int(last_match.group(1))

        return {
            "list": videos,
            "page": int(page),
            "pagecount": pagecount if pagecount > 0 else 1,
            "limit": 20,
            "total": len(videos) * pagecount if pagecount > 1 else len(videos)
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vod_id = str(ids[0]) if isinstance(ids, list) else str(ids)
        url = f"{self.site_url}{vod_id}"
        html = self._fetch(url)
        if not html:
            return {"list": []}

        vod = {}

        # 标题
        title_match = re.search(r'<h1 class="title">(.*?)</h1>', html)
        if title_match:
            vod["vod_name"] = title_match.group(1).strip()

        # 图片
        pic_match = re.search(r'<a class="stui-vodlist__thumb picture v-thumb"[^>]*>.*?<img class="lazyload"[^>]*data-original="(.*?)"', html, re.S)
        if pic_match:
            pic = pic_match.group(1)
            if pic and pic.startswith("/"):
                pic = self.site_url + pic
            vod["vod_pic"] = pic

        # 简介
        desc_match = re.search(r'<span class="detail-content".*?>(.*?)</span>', html, re.S)
        if desc_match:
            desc = desc_match.group(1).strip()
            desc = re.sub(r'<[^>]+>', '', desc)
            vod["vod_content"] = desc.strip()
        else:
            vod["vod_content"] = ""

        # 播放列表
        play_from_list = []
        play_url_list = []

        # 尝试标准tab结构
        tab_pattern = r'<ul class="nav nav-tabs active">(.*?)</ul>'
        tab_match = re.search(tab_pattern, html, re.S)
        if tab_match:
            tab_html = tab_match.group(1)
            from_matches = re.findall(r'<li.*?><a href="#playlist(\d+)"[^>]*>(.*?)</a></li>', tab_html)
            for tab_id, from_name in from_matches:
                playlist_pattern = rf'<div id="playlist{tab_id}" class="tab-pane[^"]*">.*?<ul class="stui-content__playlist clearfix column8">(.*?)</ul>'
                playlist_match = re.search(playlist_pattern, html, re.S)
                if playlist_match:
                    playlist_html = playlist_match.group(1)
                    ep_matches = re.findall(r'<li><a class="btn[^"]*" href="([^"]+)"[^>]*>(.*?)</a></li>', playlist_html)
                    if ep_matches:
                        play_from_list.append(from_name.strip())
                        ep_urls = [f"{name.strip()}${url}" for url, name in ep_matches]
                        play_url_list.append("$$$".join(ep_urls))

        # 如果没有找到线路，尝试备用模式
        if not play_from_list:
            all_ep_pattern = r'<li><a class="btn[^"]*" href="(/[^"]+)"[^>]*>(.*?)</a></li>'
            all_ep_matches = re.findall(all_ep_pattern, html)
            if all_ep_matches:
                play_from_list = ["线路1"]
                ep_urls = [f"{name.strip()}${url}" for url, name in all_ep_matches]
                play_url_list = ["$$$".join(ep_urls)]

        if play_from_list:
            vod["vod_play_from"] = "$$$".join(play_from_list)
            vod["vod_play_url"] = "$$$".join(play_url_list)
        else:
            vod["vod_play_from"] = ""
            vod["vod_play_url"] = ""

        # 补充默认值
        vod.setdefault("vod_id", vod_id)
        vod.setdefault("vod_name", "未知")
        vod.setdefault("vod_pic", "")
        vod.setdefault("vod_remarks", "")
        vod.setdefault("vod_content", "")

        return {"list": [vod]}

    def searchContent(self, key, quick=False, pg="1"):
        if not key or len(key.strip()) < 1:
            return {"list": [], "page": 1}
        keyword = key.strip()
        page = str(pg or "1")
        url = f"{self.site_url}/search/-------------.html?wd={keyword}&page={page}"
        html = self._fetch(url)
        if not html:
            return {"list": [], "page": int(page)}

        videos = []

        # 搜索页使用 stui-vodlist__media 结构
        patterns = [
            r'<a class="v-thumb stui-vodlist__thumb lazyload" href="(/det/\d+\.html)"[^>]*data-original="([^"]+)".*?<span class="pic-text text-right">([^<]+)</span>.*?<h3 class="title"><a[^>]*>([^<]+)</a>',
            r'<li class="col-md-6 col-sm-4 col-xs-3">.*?<a class="stui-vodlist__thumb.*?" href="(/det/\d+\.html)".*?data-original="(.*?)".*?<span class="pic-text text-right">(.*?)</span>.*?<p class="title text-overflow h4_add"><a[^>]*>(.*?)</a>',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.S)
            if matches:
                for match in matches:
                    vod_url, pic, status, title = match
                    if title and title.strip():
                        if pic and pic.startswith("/"):
                            pic = self.site_url + pic
                        videos.append({
                            "vod_id": vod_url,
                            "vod_name": title.strip(),
                            "vod_pic": pic,
                            "vod_remarks": status.strip(),
                        })
                break

        pagecount = 1
        page_match = re.search(r'共(\d+)页', html)
        if page_match:
            pagecount = int(page_match.group(1))

        return {"list": videos, "page": int(page), "pagecount": pagecount}

    def playerContent(self, flag, id, vipFlags=None):
        # 如果是完整URL，直接返回
        if id.startswith("http://") or id.startswith("https://"):
            return {"parse": 0, "url": id, "header": self.headers}

        # 构建播放页URL
        if id.startswith("/"):
            play_url = f"{self.site_url}{id}"
        else:
            play_url = f"{self.site_url}/{id}"

        html = self._fetch(play_url)
        if not html:
            return {"parse": 1, "url": play_url, "header": self.headers}

        # 1. 尝试从 player_aaaa 变量提取
        player_pattern = r'var player_aaaa\s*=\s*({.*?});'
        player_match = re.search(player_pattern, html, re.S)
        if player_match:
            try:
                player_json = player_match.group(1)
                url_match = re.search(r'"url"\s*:\s*"(.*?)"', player_json)
                if url_match:
                    video_url = url_match.group(1).replace('\\/', '/')
                    if video_url.startswith("http"):
                        return {"parse": 0, "url": video_url, "header": self.headers}
            except:
                pass

        # 2. 尝试其他播放器格式
        alt_patterns = [
            r'player\s*=\s*({[^}]*"url"\s*:\s*"[^"]+"[^}]*})',
            r'video\s*:\s*{[^}]*url\s*:\s*"([^"]+)"',
            r'src\s*:\s*"([^"]+\.m3u8[^"]*)"',
            r'url\s*:\s*"([^"]+\.m3u8[^"]*)"',
        ]
        for pattern in alt_patterns:
            match = re.search(pattern, html, re.S)
            if match:
                video_url = match.group(1)
                if video_url.startswith("http"):
                    return {"parse": 0, "url": video_url, "header": self.headers}

        # 3. 直接搜索m3u8链接
        m3u8_pattern = r'(https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*)'
        m3u8_matches = re.findall(m3u8_pattern, html)
        if m3u8_matches:
            return {"parse": 0, "url": m3u8_matches[0], "header": self.headers}

        # 4. 降级嗅探
        return {"parse": 1, "url": play_url, "header": self.headers}

    def getProxyUrl(self):
        return ""

    def destroy(self):
        pass


# 兼容性函数
def getSpider():
    return Spider()

def getHomeContent():
    return Spider().homeContent()

def getHomeVideoContent():
    return Spider().homeVideoContent()

def getCategoryContent(tid, pg=1, filter=False, extend=None):
    return Spider().categoryContent(tid, pg, filter, extend)

def getDetailContent(ids):
    return Spider().detailContent(ids)

def getSearchContent(key, quick=False, pg=1):
    return Spider().searchContent(key, quick, pg)

def getPlayerContent(flag, id, vipFlags=None):
    return Spider().playerContent(flag, id, vipFlags)

def getDependence():
    return Spider().getDependence()

def destroy():
    return Spider().destroy()