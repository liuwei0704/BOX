# coding: utf-8
"""
TVBox 爬虫源 - 辣妹AV
站点: https://www.hengshuangde.shop/
CMS: 苹果CMS (MacCMS) HTML站
类型: 影视（成人向）
"""

import re
import json
from urllib.parse import urljoin, quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://www.hengshuangde.shop"
        self.fallback_host = "https://www.langren98.cfd"
        
        self.classes = [
            {"type_id": "1", "type_name": "高清无码"},
            {"type_id": "2", "type_name": "动漫剧情"},
            {"type_id": "3", "type_name": "国产精品"},
            {"type_id": "4", "type_name": "女优明星"},
            {"type_id": "6", "type_name": "传媒剧情"},
            {"type_id": "7", "type_name": "国产女星"},
            {"type_id": "8", "type_name": "三级伦理"},
            {"type_id": "9", "type_name": "欧美专区"},
            {"type_id": "10", "type_name": "中文字幕"},
            {"type_id": "11", "type_name": "萝莉少女"},
            {"type_id": "12", "type_name": "日本有码"},
            {"type_id": "13", "type_name": "国产主播"},
            {"type_id": "14", "type_name": "韩国主播"},
            {"type_id": "15", "type_name": "强奸乱伦"},
            {"type_id": "16", "type_name": "网红头条"},
        ]
        
        self.filters = {}
        for cls in self.classes:
            self.filters[cls["type_id"]] = []
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.extend = ""

    def getName(self):
        return "辣妹AV"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _fetch_html(self, url):
        try:
            rsp = self.fetch(url, headers=self.headers)
            status_code = None
            if rsp:
                for attr in ["code", "status_code", "status"]:
                    if hasattr(rsp, attr):
                        val = getattr(rsp, attr)
                        if val is not None:
                            status_code = val
                            break
            
            if rsp and hasattr(rsp, "text"):
                html = rsp.text
                if html and len(html) > 100:
                    if status_code is None or status_code == 200:
                        return html
            return None
        except Exception:
            return None

    def _fix_url(self, url):
        if not url:
            return ""
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.host + url
        if not url.startswith("http"):
            return self.host + "/" + url.lstrip("/")
        return url

    def _parse_video_list(self, html):
        """从分类页 HTML 解析视频列表"""
        videos = []
        if not html:
            return videos
        
        # 匹配 <li> 中的视频卡片
        pattern = r'<li>.*?<a\s+href="[^"]*?/vod/detail/id/(\d+)\.html[^"]*"[^>]*>.*?<img[^>]*src="([^"]*?)"[^>]*>.*?</a>.*?<a\s+href="[^"]*"[^>]*>.*?<h3[^>]*>([^<]*)</h3>'
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        
        for m in matches:
            vid = m[0]
            img = m[1]
            title = m[2].strip()
            if vid and img and title:
                videos.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": self._fix_url(img),
                    "vod_remarks": ""
                })
        
        # 备用匹配
        if not videos:
            pattern2 = r'<a\s+href="[^"]*?/detail/id/(\d+)\.html[^"]*"[^>]*>.*?<img[^>]*src="([^"]*?)"[^>]*>.*?<h3[^>]*>([^<]*)</h3>'
            matches2 = re.findall(pattern2, html, re.IGNORECASE | re.DOTALL)
            for m in matches2:
                vid = m[0]
                img = m[1]
                title = m[2].strip()
                if vid and img and title:
                    videos.append({
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": self._fix_url(img),
                        "vod_remarks": ""
                    })
        
        return videos

    def _parse_page_info(self, html):
        page = 1
        pagecount = 1
        if not html:
            return page, pagecount
        
        page_match = re.search(r'当前(\d+)/(\d+)页', html)
        if page_match:
            return int(page_match.group(1)), int(page_match.group(2))
        
        page_match2 = re.search(r'page[/=](\d+)\.html', html)
        if page_match2:
            page = int(page_match2.group(1))
        
        page_links = re.findall(r'page[/=](\d+)\.html', html)
        if page_links:
            max_page = max([int(p) for p in page_links])
            if max_page > pagecount:
                pagecount = max_page
        
        return page, pagecount

    def homeContent(self, filter=False):
        return {
            "class": self.classes,
            "filters": self.filters if filter else {}
        }

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            html = self._fetch_html(self.host + "/index.php/vod/type/id/3.html")
            if html:
                videos = self._parse_video_list(html)
                return {"list": videos[:20]}
        except Exception:
            pass
        return {"list": []}

    def categoryContent(self, tid, pg, filter=False, extend=""):
        page = pg or "1"
        if int(page) <= 1:
            url = f"{self.host}/index.php/vod/type/id/{tid}.html"
        else:
            url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
        
        videos = self._parse_video_list(html)
        cur_page, total_page = self._parse_page_info(html)
        
        return {
            "list": videos,
            "page": int(page),
            "pagecount": total_page if total_page > 0 else 1,
            "limit": 20,
            "total": len(videos) * (total_page if total_page > 0 else 1)
        }

    def _parse_extend(self, extend):
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            if extend.startswith("{") and extend.endswith("}"):
                try:
                    return json.loads(extend)
                except:
                    pass
            result = {}
            parts = extend.replace("{", "").replace("}", "").split(",")
            for part in parts:
                if "=" in part:
                    k, v = part.split("=", 1)
                    result[k.strip()] = v.strip()
            return result
        return {}

    def detailContent(self, ids):
        vid = ids[0] if ids else ""
        if not vid:
            return {"list": []}
        
        url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
        html = self._fetch_html(url)
        
        if not html:
            return {
                "list": [{
                    "vod_id": vid,
                    "vod_name": f"视频 {vid}",
                    "vod_pic": "",
                    "vod_remarks": "",
                    "vod_content": "",
                    "vod_play_from": "播放",
                    "vod_play_url": f"播放$ {self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
                }]
            }
        
        # 提取标题
        title = ""
        title_match = re.search(r'<h1[^>]*>([^<]*)</h1>', html)
        if title_match:
            title = title_match.group(1).strip()
        if not title:
            title_match2 = re.search(r'<title>([^<]*)</title>', html)
            if title_match2:
                title = title_match2.group(1).strip()
                title = re.sub(r'\s*[-|]\s*辣妹AV.*$', '', title)
                title = re.sub(r'\s*详情介绍.*$', '', title)
                title = re.sub(r'\s*在线观看.*$', '', title)
                title = re.sub(r'\s*迅雷下载.*$', '', title)
        
        # 提取封面图
        pic = ""
        pic_match = re.search(r'<img[^>]*class="[^"]*vod_img[^"]*"[^>]*src="([^"]*)"', html)
        if not pic_match:
            pic_match = re.search(r'<img[^>]*src="([^"]*)"[^>]*class="[^"]*vod_img[^"]*"', html)
        if pic_match:
            pic = self._fix_url(pic_match.group(1))
        if not pic:
            pic_match3 = re.search(r'<img[^>]*data-src="([^"]*)"[^>]*>', html)
            if pic_match3:
                pic = self._fix_url(pic_match3.group(1))
        if not pic:
            pic_match2 = re.search(r'<img[^>]*src="([^"]*)"[^>]*alt="[^"]*"', html)
            if pic_match2:
                pic = self._fix_url(pic_match2.group(1))
        
        # 提取简介
        desc = ""
        desc_match = re.search(r'<div[^>]*class="[^"]*vod_content[^"]*"[^>]*>([^<]*)</div>', html, re.DOTALL)
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
        
        # 提取播放线路
        # 从 play-btn-group 中提取所有线路
        play_btn_group = re.search(r'<div\s+class="play-btn-group"[^>]*>(.*?)</div>', html, re.IGNORECASE | re.DOTALL)
        play_from = ""
        play_url = ""
        
        if play_btn_group:
            group_html = play_btn_group.group(1)
            # 匹配所有线路链接
            line_pattern = r'<a\s+title="([^"]*)"\s+href="([^"]*)"'
            line_matches = re.findall(line_pattern, group_html, re.IGNORECASE)
            
            from_list = []
            url_list = []
            for line_name, line_href in line_matches:
                # 构建完整播放URL
                play_page_url = self._fix_url(line_href)
                from_list.append(line_name.strip())
                url_list.append(play_page_url)
            
            if from_list and url_list:
                play_from = "$$$".join(from_list)
                play_url = "$$$".join(url_list)
        
        # 如果没有提取到线路，使用默认
        if not play_url:
            play_from = "播放"
            play_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        
        vod = {
            "vod_id": vid,
            "vod_name": title or f"视频 {vid}",
            "vod_pic": pic,
            "vod_remarks": "",
            "vod_content": desc,
            "vod_play_from": play_from,
            "vod_play_url": play_url
        }
        
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        page = pg or "1"
        search_url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}"
        if int(page) > 1:
            search_url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}&page={page}"
        
        html = self._fetch_html(search_url)
        if not html:
            return {"list": [], "page": int(page)}
        
        videos = self._parse_video_list(html)
        return {"list": videos, "page": int(page)}

    def playerContent(self, flag, id, vipFlags):
        """解析播放页，提取直链"""
        # 如果已经是直链，直接返回
        if id.startswith("http") and (".m3u8" in id or ".mp4" in id or "m3u8" in id):
            return {"parse": 0, "url": id, "header": self.headers}
        
        # 获取播放页 HTML
        url = self._fix_url(id)
        html = self._fetch_html(url)
        
        if not html:
            return {"parse": 1, "url": id, "header": self.headers}
        
        play_url = ""
        
        # 方法1: 从 player_aaaa 变量提取
        player_match = re.search(r'var\s+player_aaaa\s*=\s*({[^}]+})', html)
        if player_match:
            try:
                player_data = json.loads(player_match.group(1))
                if isinstance(player_data, dict):
                    for key in ["url", "playUrl", "play_url", "m3u8", "m3u8_url", "video"]:
                        if key in player_data and player_data[key]:
                            play_url = player_data[key]
                            break
                    # 如果 url 是对象，继续提取
                    if not play_url and "url" in player_data and isinstance(player_data["url"], dict):
                        for sub_key in ["url", "m3u8", "m3u8_url"]:
                            if sub_key in player_data["url"] and player_data["url"][sub_key]:
                                play_url = player_data["url"][sub_key]
                                break
            except:
                pass
        
        # 方法2: 从 iframe 提取
        if not play_url:
            iframe_match = re.search(r'<iframe[^>]*src="([^"]*)"', html)
            if iframe_match:
                play_url = self._fix_url(iframe_match.group(1))
        
        # 方法3: 从 now 参数提取
        if not play_url:
            now_match = re.search(r'now\s*[=:]\s*["\']([^"\']+)["\']', html)
            if now_match:
                play_url = now_match.group(1)
        
        # 方法4: 从 video 标签提取
        if not play_url:
            video_match = re.search(r'<video[^>]*src="([^"]*)"', html)
            if video_match:
                play_url = video_match.group(1)
        
        # 方法5: 从 JS 中的 m3u8 链接提取
        if not play_url:
            m3u8_match = re.search(r'["\'](https?://[^\s"\']+\.m3u8[^\s"\']*)["\']', html)
            if m3u8_match:
                play_url = m3u8_match.group(1)
        
        if play_url:
            return {"parse": 0, "url": play_url, "header": self.headers}
        
        # 降级到嗅探
        return {"parse": 1, "url": id, "header": self.headers}

    def localProxy(self, params):
        return [404, "text/plain", "Not Found"]

    def isVideoFormat(self, url):
        return bool(re.search(r'\.(m3u8|mp4|flv|mkv|ts)', url, re.I))

    def destroy(self):
        pass