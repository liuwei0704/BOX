# coding: utf-8
# 338TV 影视爬虫 - 基于 MacCMS
# 站点: https://338tv1.xyz/
# 特征: 标准 MacCMS，视频列表 + DPlayer 播放器 m3u8 直链

import re
import json
from urllib.parse import quote, urlencode

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://338tv1.xyz"
        self.classes = [
            {"type_id": "28", "type_name": "短视频"},
            {"type_id": "25", "type_name": "黑料"},
            {"type_id": "29", "type_name": "综艺"},
            {"type_id": "41", "type_name": "人兽"},
            {"type_id": "42", "type_name": "二次元"},
            {"type_id": "37", "type_name": "av解说"},
            {"type_id": "43", "type_name": "同性恋"},
            {"type_id": "14", "type_name": "猎奇"},
            {"type_id": "24", "type_name": "338原创"},
            {"type_id": "31", "type_name": "欧美"},
            {"type_id": "39", "type_name": "日韩"},
            {"type_id": "26", "type_name": "国产"},
            {"type_id": "27", "type_name": "偷拍"},
            {"type_id": "30", "type_name": "动漫"},
            {"type_id": "34", "type_name": "经典三级"},
            {"type_id": "35", "type_name": "制片厂"},
            {"type_id": "36", "type_name": "明星淫梦"},
            {"type_id": "38", "type_name": "强奸乱伦"},
            {"type_id": "32", "type_name": "福利姬"},
            {"type_id": "13", "type_name": "制服诱惑"},
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.host + "/",
        }

    def getName(self):
        return "338TV"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        return self.categoryContent("28", "1", None, None)

    def categoryContent(self, tid, pg, filter, extend):
        pg = str(pg) if pg else "1"
        url = f"{self.host}/index.php/vodtype/{tid}-{pg}.html"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        page_count = self._parse_page_count(html)
        return {
            "list": items,
            "page": int(pg),
            "pagecount": page_count,
            "limit": 20,
            "total": page_count * 20,
        }

    def detailContent(self, ids):
        raw = str(ids[0])
        parts = raw.split("|$|")
        vid = parts[0]
        title = parts[1] if len(parts) > 1 else "视频"
        pic = parts[2] if len(parts) > 2 else ""
        remark = parts[3] if len(parts) > 3 else ""
        play_url = f"{self.host}/index.php/vodplay/{vid}-1-1.html"

        if len(parts) == 1:
            detail_html = self._fetch_html(play_url)
            title, pic, remark = self._parse_detail_meta(detail_html)

        vod = {
            "vod_id": raw,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": remark,
            "vod_content": remark,
            "vod_play_from": "播放",
            "vod_play_url": f"播放${play_url}",
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        pg = str(pg) if pg else "1"
        url = f"{self.host}/index.php/vodsearch/-------------.html?wd={quote(key)}"
        html = self._fetch_html(url)
        items = self._parse_video_list(html)
        return {"list": items, "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        if id.startswith("http"):
            play_url = id
        else:
            play_url = f"{self.host}/index.php/vodplay/{id}-1-1.html" if "-" not in id else id

        html = self._fetch_html(play_url)
        m3u8_match = re.search(r'<video[^>]*src="([^"]+\.m3u8[^"]*)"', html, re.IGNORECASE)
        if m3u8_match:
            m3u8_url = m3u8_match.group(1)
            if m3u8_url.startswith("//"):
                m3u8_url = "https:" + m3u8_url
            elif m3u8_url.startswith("/"):
                m3u8_url = self.host + m3u8_url
            return {"parse": 0, "url": m3u8_url, "header": self.headers}

        player_match = re.search(r'player_aaaa\s*=\s*({[^}]+})', html)
        if player_match:
            try:
                data = json.loads(player_match.group(1))
                if data.get("encrypt") == 0 and data.get("url"):
                    return {"parse": 0, "url": data["url"], "header": self.headers}
            except:
                pass

        return {"parse": 1, "url": id, "header": self.headers}

    def localProxy(self, param):
        return [404, "text/plain", "Not Found"]

    def _fetch_html(self, url, params=None):
        full_url = url
        if params:
            if "?" in url:
                full_url = url + "&" + urlencode(params)
            else:
                full_url = url + "?" + urlencode(params)
        resp = self.fetch(full_url, headers=self.headers)
        if resp and resp.status_code == 200:
            return resp.text
        return ""

    def _parse_video_list(self, html):
        """解析视频列表 - 直接从HTML提取视频信息"""
        items = []
        if not html:
            return items

        # 方法1: 直接从HTML中提取所有视频链接
        # 匹配格式: /index.php/vodplay/数字-1-1.html
        # 同时提取标题、封面、时长
        pattern = r'<a[^>]*href="(/index.php/vodplay/(\d+)-[^"]+)"[^>]*>.*?</a>'
        links = re.findall(pattern, html, re.DOTALL)

        # 提取所有封面图
        pic_pattern = r'<img[^>]*(?:data-original|src)="([^"]+)"[^>]*>'
        pics = re.findall(pic_pattern, html)

        # 提取所有时长
        dur_pattern = r'<span class="vod-duration">([^<]+)</span>'
        durations = re.findall(dur_pattern, html)

        # 提取所有标题
        title_pattern = r'<a[^>]*class="[^"]*vod-title[^"]*"[^>]*>([^<]+)</a>'
        titles = re.findall(title_pattern, html)

        # 如果标题提取不到，尝试从链接周围提取
        if not titles:
            title_pattern2 = r'<a[^>]*href="/index.php/vodplay/\d+-[^"]+"[^>]*>([^<]+)</a>'
            titles = re.findall(title_pattern2, html)

        # 构建视频条目
        # 使用列表索引匹配，但要注意广告会干扰，需要过滤
        vid_set = set()
        for i, (link, vid) in enumerate(links):
            if vid in vid_set:
                continue
            # 跳过广告链接（外部链接）
            if link.startswith("http") and "338tv" not in link:
                continue
            # 获取对应的标题
            title = ""
            if i < len(titles):
                title = titles[i].strip()
            # 如果标题包含广告关键词，跳过
            if any(k in title for k in ["同城约炮", "金桃直播", "糖果直播", "顶级主播"]):
                continue
            if not title:
                continue

            pic = ""
            if i < len(pics):
                pic = pics[i]
            duration = ""
            if i < len(durations):
                duration = durations[i]

            item = {
                "vod_id": f"{vid}|$|{title}|$|{pic}|$|{duration}",
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": duration,
            }
            items.append(item)
            vid_set.add(vid)

        # 如果方法1没提取到，使用块匹配
        if not items:
            # 匹配 list-grid 区域
            list_area = re.search(r'<div class="list-grid vod-list">(.*?)</div>\s*</div>', html, re.DOTALL)
            if list_area:
                list_html = list_area.group(1)
            else:
                list_html = html

            # 匹配每个 vod-item 块
            blocks = re.findall(r'<div class="[^"]*vod-item[^"]*">(.*?)</div>\s*(?:</div>|</a>)', list_html, re.DOTALL)
            for block in blocks:
                # 跳过广告
                if 'downurl' in block and any(k in block for k in ["同城约炮", "金桃直播", "糖果直播"]):
                    continue

                pic = ""
                pic_match = re.search(r'<img[^>]*(?:data-original|src)="([^"]+)"', block)
                if pic_match:
                    pic = pic_match.group(1)

                duration = ""
                dur_match = re.search(r'<span class="vod-duration">([^<]+)</span>', block)
                if dur_match:
                    duration = dur_match.group(1)

                title = ""
                title_match = re.search(r'<a[^>]*class="[^"]*vod-title[^"]*"[^>]*>([^<]+)</a>', block)
                if not title_match:
                    title_match = re.search(r'<a[^>]*href="/index.php/vodplay/[^"]+"[^>]*>([^<]+)</a>', block)
                if title_match:
                    title = title_match.group(1).strip()

                link = ""
                link_match = re.search(r'<a[^>]*href="(/index.php/vodplay/\d+-[^"]+)"[^>]*>', block)
                if link_match:
                    link = link_match.group(1)

                vid = ""
                if link:
                    vid_match = re.search(r'/vodplay/(\d+)-', link)
                    if vid_match:
                        vid = vid_match.group(1)

                if vid and title and len(title) > 1 and not any(k in title for k in ["同城约炮", "金桃直播", "糖果直播"]):
                    items.append({
                        "vod_id": f"{vid}|$|{title}|$|{pic}|$|{duration}",
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": duration,
                    })

        return items

    def _parse_page_count(self, html):
        if not html:
            return 1
        match = re.search(r'当前\d+/(\d+)页', html)
        if match:
            return int(match.group(1))
        links = re.findall(r'/index.php/vodtype/\d+-(\d+)\.html', html)
        if links:
            return max(int(x) for x in links)
        return 1

    def _parse_detail_meta(self, html):
        title = "视频"
        pic = ""
        remark = ""
        if not html:
            return title, pic, remark
        title_match = re.search(r'<h1>([^<]+)</h1>', html)
        if title_match:
            title = title_match.group(1).strip()
        poster_match = re.search(r'<video[^>]*poster="([^"]+)"', html)
        if poster_match:
            pic = poster_match.group(1)
        desc_match = re.search(r'<p>([^<]+)</p>', html)
        if desc_match:
            remark = desc_match.group(1).strip()[:50]
        return title, pic, remark