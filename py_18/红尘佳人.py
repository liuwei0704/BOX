# coding: utf-8
# 站点: 红尘佳人 (7799vip.top)
# CMS: MacCMS
# 类型: 成人影视
# 特点: 服务端渲染 HTML，player_aaaa 变量包含播放地址，encrypt:0 直链

import re
import json
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://7799vip.top"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
            "Referer": self.host + "/"
        }
        # 8个分类
        self.classes = [
            {"type_id": "6", "type_name": "国产主播"},
            {"type_id": "13", "type_name": "萝莉少女"},
            {"type_id": "7", "type_name": "自拍偷拍"},
            {"type_id": "8", "type_name": "日本无码"},
            {"type_id": "9", "type_name": "欧美激情"},
            {"type_id": "10", "type_name": "强奸乱伦"},
            {"type_id": "11", "type_name": "女优明星"},
            {"type_id": "12", "type_name": "抖音传媒"}
        ]
        # 无筛选功能
        self.filters = {c["type_id"]: [] for c in self.classes}

    def getName(self):
        return "红尘佳人"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐"""
        try:
            res = self.fetch(self.host + "/", headers=self.headers)
            if res.status_code != 200:
                return {"list": []}
            html = res.text
            items = self._parse_video_list(html)
            return {"list": items}
        except Exception:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        pg = pg or "1"
        try:
            if pg == "1":
                url = f"{self.host}/vodtype/{tid}.html"
            else:
                url = f"{self.host}/vodtype/{tid}-{pg}.html"
            res = self.fetch(url, headers=self.headers)
            if res.status_code != 200:
                return {"list": [], "page": int(pg), "pagecount": 0, "limit": 20, "total": 0}
            html = res.text
            items = self._parse_video_list(html)
            # 提取总页数
            pagecount = self._parse_page_count(html)
            return {
                "list": items,
                "page": int(pg),
                "pagecount": pagecount or 50,
                "limit": 20,
                "total": 0
            }
        except Exception:
            return {"list": [], "page": int(pg), "pagecount": 0, "limit": 20, "total": 0}

    def detailContent(self, ids):
        try:
            vid = str(ids[0])
            url = f"{self.host}/voddetail/{vid}.html"
            res = self.fetch(url, headers=self.headers)
            if res.status_code != 200:
                return {"list": []}
            html = res.text
            # 提取标题
            title_match = re.search(r'<h3[^>]*>(.*?)</h3>', html, re.S)
            title = title_match.group(1).strip() if title_match else "视频"
            # 提取封面
            pic_match = re.search(r'<img[^>]*class="detail-img"[^>]*src="([^"]+)"', html)
            pic = pic_match.group(1) if pic_match else ""
            # 提取时长
            duration_match = re.search(r'视频时长：<span>([^<]+)</span>', html)
            duration = duration_match.group(1).strip() if duration_match else ""
            # 提取分类标签
            tags = []
            tag_matches = re.findall(r'<a href="/vodsearch/----([^"]+)---------.html"[^>]*>([^<]+)</a>', html)
            for _, tag_name in tag_matches:
                tags.append(tag_name)
            tag_str = ",".join(tags) if tags else ""
            # 构造播放URL
            play_url = f"{self.host}/vodplay/{vid}-1-1.html"
            vod = {
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": duration,
                "vod_content": f"分类: {tag_str}",
                "vod_play_from": "播放",
                "vod_play_url": f"播放${play_url}"
            }
            return {"list": [vod]}
        except Exception:
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        try:
            data = {"wd": key}
            # 注意: 搜索需要携带 Referer
            headers = self.headers.copy()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            res = self.post(f"{self.host}/vodsearch/-------------.html", data=data, headers=headers)
            if res.status_code != 200:
                return {"list": []}
            html = res.text
            items = self._parse_video_list(html)
            return {"list": items, "page": int(pg)}
        except Exception:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        """播放地址解析"""
        try:
            # 如果已经是 m3u8 直链
            if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
                return {"parse": 0, "url": id, "header": self.headers}
            # 播放页面地址
            if not id.startswith("http"):
                url = id if id.startswith("http") else self.host + id
            else:
                url = id
            res = self.fetch(url, headers=self.headers)
            if res.status_code != 200:
                return {"parse": 1, "url": id, "header": self.headers}
            html = res.text
            # 提取 player_aaaa
            match = re.search(r'var\s+player_aaaa\s*=\s*(\{[^;]+\});', html, re.S)
            if match:
                try:
                    player_data = json.loads(match.group(1))
                    if player_data.get("encrypt") == 0 and player_data.get("url"):
                        m3u8_url = player_data["url"]
                        return {"parse": 0, "url": m3u8_url, "header": self.headers}
                except:
                    pass
            # 降级嗅探
            return {"parse": 1, "url": id, "header": self.headers}
        except Exception:
            return {"parse": 1, "url": id, "header": self.headers}

    def _parse_video_list(self, html):
        """解析视频列表"""
        items = []
        # 匹配卡片块
        block_pattern = r'<div class="col-md-3 resent-grid recommended-grid[^"]*">(.*?)</div>\s*</div>\s*</div>'
        blocks = re.findall(block_pattern, html, re.S)
        for block in blocks:
            try:
                # 详情链接
                link_match = re.search(r'<a href="([^"]+)"', block)
                if not link_match:
                    continue
                link = link_match.group(1)
                # 提取视频ID
                vid_match = re.search(r'/voddetail/(\d+)\.html', link)
                if not vid_match:
                    continue
                vid = vid_match.group(1)
                # 封面图
                pic_match = re.search(r'data-original="([^"]+)"', block)
                pic = pic_match.group(1) if pic_match else ""
                # 标题
                title_match = re.search(r'<a[^>]*class="title"[^>]*>([^<]+)</a>', block)
                title = title_match.group(1).strip() if title_match else "视频"
                # 时长
                duration_match = re.search(r'<p class="duration-time">([^<]+)</p>', block)
                duration = duration_match.group(1).strip() if duration_match else ""
                # 观看数
                views_match = re.search(r'<span>(\d+)</span>观看', block)
                views = views_match.group(1) if views_match else "0"
                items.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": f"{duration} | {views}观看"
                })
            except:
                continue
        return items

    def _parse_page_count(self, html):
        """解析总页数"""
        match = re.search(r'class="page"[^>]*>.*?(\d+)</a>\s*</li>\s*<li[^>]*class="active"', html, re.S)
        if match:
            return int(match.group(1))
        match = re.search(r'共(\d+)页', html)
        if match:
            return int(match.group(1))
        return None

    def destroy(self):
        pass