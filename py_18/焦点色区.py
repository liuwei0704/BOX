# -*- coding: utf-8 -*-
"""
焦点色区 - TVBox爬虫源
站点: https://xn--0813--ft1hp00a213fpezc.23246.xyz/srym/
"""

import re
import json
from urllib.parse import urljoin, urlparse, quote
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://xn--0813--ft1hp00a213fpezc.23246.xyz"
        self.site_path = "/srym"
        self.base_url = self.host + self.site_path
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Referer": self.base_url + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        # 分类硬编码
        self.classes = [
            {"type_id": "sifangzipai", "type_name": "私房自拍"},
            {"type_id": "ribenwuma", "type_name": "日本无码"},
            {"type_id": "zhongwenzimu", "type_name": "中文字幕"},
            {"type_id": "katongdonghua", "type_name": "卡通动画"},
            {"type_id": "guodongchuanmei", "type_name": "果冻传媒"},
            {"type_id": "tianmeichuanmei", "type_name": "天美传媒"},
            {"type_id": "mitaochuanmei", "type_name": "蜜桃传媒"},
            {"type_id": "xingkongchuanmei", "type_name": "星空传媒"},
            {"type_id": "aidouchuanmei", "type_name": "爱豆传媒"},
            {"type_id": "SAguoji", "type_name": "SA国际"},
            {"type_id": "qitachuanmei", "type_name": "其他传媒"},
            {"type_id": "tuzixiansheng", "type_name": "兔子先生"}
        ]
        # 筛选（站点无筛选，返回空）
        self.filters = {c["type_id"]: [] for c in self.classes}

    def getName(self):
        return "焦点色区"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _fetch_html(self, url, data=None, method="GET"):
        """封装请求，返回HTML文本"""
        try:
            if method.upper() == "POST" and data:
                resp = self.post(url, data=data, headers=self.headers)
            else:
                resp = self.fetch(url, headers=self.headers)
            if resp:
                if hasattr(resp, "status_code") and resp.status_code != 200:
                    return None
                if hasattr(resp, "text"):
                    return resp.text
                if hasattr(resp, "content"):
                    try:
                        return resp.content.decode("utf-8", errors="ignore")
                    except:
                        pass
                if isinstance(resp, str):
                    return resp
            return None
        except Exception as e:
            self.log({"action": "fetch_error", "url": url, "error": str(e)})
            return None

    def _fix_url(self, url):
        """补全绝对路径"""
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.host + url
        return urljoin(self.base_url, url)

    def _parse_list_items(self, html):
        """解析列表页的视频项 - 使用更健壮的方式"""
        items = []
        # 先提取所有 item 块
        item_blocks = re.findall(r'<div\s+class="item">(.*?)</div>\s*</a>\s*</div>', html, re.DOTALL)
        if not item_blocks:
            # 尝试更宽松的匹配
            item_blocks = re.findall(r'<div\s+class="item">.*?<a\s+href="([^"]+)".*?<img[^>]+(?:data-original|src)="([^"]+)".*?<div\s+class="item-title">([^<]+)</div>', html, re.DOTALL)
            for link, pic, title in item_blocks:
                vod_id = self._extract_vod_id(link)
                if vod_id:
                    items.append({
                        "vod_id": vod_id,
                        "vod_name": title.strip(),
                        "vod_pic": self._fix_url(pic),
                        "vod_remarks": ""
                    })
            return items
        for block in item_blocks:
            link_match = re.search(r'<a\s+href="([^"]+)"', block)
            if not link_match:
                continue
            link = link_match.group(1)
            vod_id = self._extract_vod_id(link)
            if not vod_id:
                continue
            pic_match = re.search(r'<img[^>]+(?:data-original|src)="([^"]+)"[^>]*alt="([^"]*)"', block)
            pic = pic_match.group(1) if pic_match else ""
            alt = pic_match.group(2) if pic_match else ""
            title_match = re.search(r'<div\s+class="item-title">([^<]+)</div>', block)
            title = title_match.group(1).strip() if title_match else alt
            items.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": self._fix_url(pic),
                "vod_remarks": ""
            })
        return items

    def _extract_vod_id(self, url):
        """从URL提取视频ID"""
        match = re.search(r'/video/([^/]+)/', url)
        return match.group(1) if match else None

    def homeContent(self, filter):
        """首页分类和筛选"""
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐"""
        result = {"list": []}
        html = self._fetch_html(self.base_url + "/")
        if not html:
            return result
        item_pattern = r'<div\s+class="item">\s*<a\s+href="([^"]+)"[^>]*>.*?<img[^>]+(?:data-original|src)="([^"]+)"[^>]*alt="([^"]*)"[^>]*>.*?<div\s+class="item-title">([^<]+)</div>'
        matches = re.findall(item_pattern, html, re.DOTALL)
        for link, pic, alt, title in matches:
            vod_id = self._extract_vod_id(link)
            if not vod_id:
                continue
            result["list"].append({
                "vod_id": vod_id,
                "vod_name": title.strip() or alt.strip(),
                "vod_pic": self._fix_url(pic),
                "vod_remarks": ""
            })
        return result

    def categoryContent(self, tid, pg, filter, extend):
        """分类列表"""
        pg = pg or "1"
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}
        if pg == "1":
            url = f"{self.base_url}/category/{tid}/"
        else:
            url = f"{self.base_url}/category/{tid}-{pg}/"
        html = self._fetch_html(url)
        if not html:
            return result
        result["list"] = self._parse_list_items(html)
        page_match = re.search(r'<a[^>]+href="[^"]*category/[^"]+-(\d+)/"[^>]*>(\d+)</a>\s*</div>', html)
        if page_match:
            try:
                total_pages = int(page_match.group(1))
                result["pagecount"] = total_pages
            except:
                pass
        if result["pagecount"] == 1:
            nav_match = re.search(r'<span[^>]*>\d+</span>\s*<a[^>]+href="[^"]+-(\d+)/"[^>]*>', html)
            if nav_match:
                try:
                    result["pagecount"] = int(nav_match.group(1))
                except:
                    pass
        return result

    def detailContent(self, ids):
        """详情页"""
        result = {"list": []}
        if not ids:
            return result
        vod_id = ids[0] if isinstance(ids, list) else ids
        url = f"{self.base_url}/video/{vod_id}/"
        html = self._fetch_html(url)
        if not html:
            return result
        title_match = re.search(r'<h1[^>]*class="[^"]*items-title[^"]*"[^>]*>([^<]+)</h1>', html)
        title = title_match.group(1).strip() if title_match else ""
        pic_match = re.search(r'<img[^>]+(?:data-original|src)="([^"]+)"[^>]*alt="[^"]*"[^>]*>', html)
        pic = pic_match.group(1) if pic_match else ""
        desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
        desc = desc_match.group(1) if desc_match else ""
        player_match = re.search(r'var\s+player_aaaa\s*=\s*({[^;]+})', html)
        play_from = "播放"
        play_url = ""
        if player_match:
            try:
                player_data = json.loads(player_match.group(1))
                m3u8_url = player_data.get("url", "")
                if m3u8_url:
                    play_url = f"正片${m3u8_url}"
            except:
                pass
        if not play_url:
            iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', html)
            if iframe_match:
                iframe_src = iframe_match.group(1)
                if iframe_src:
                    play_url = f"正片${iframe_src}"
            else:
                play_url = f"正片${url}"
                play_from = "播放"
        vod_data = {
            "vod_id": vod_id,
            "vod_name": title or "未知标题",
            "vod_pic": self._fix_url(pic),
            "vod_content": desc,
            "vod_actor": "",
            "vod_director": "",
            "vod_play_from": play_from,
            "vod_play_url": play_url
        }
        result["list"] = [vod_data]
        return result

    def searchContent(self, key, quick, pg="1"):
        """搜索"""
        result = {"list": [], "page": int(pg) if pg else 1}
        if not key:
            return result
        try:
            headers = self.headers.copy()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            resp = self.post(
                f"{self.base_url}/vodsearch/-------------/",
                data={"wd": key},
                headers=headers
            )
            if resp:
                html = None
                if hasattr(resp, "text"):
                    html = resp.text
                elif hasattr(resp, "content"):
                    try:
                        html = resp.content.decode("utf-8", errors="ignore")
                    except:
                        pass
                elif isinstance(resp, str):
                    html = resp
                if html:
                    result["list"] = self._parse_list_items(html)
        except Exception as e:
            self.log({"action": "search_error", "key": key, "error": str(e)})
        return result

    def playerContent(self, flag, id, vipFlags):
        """播放"""
        if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
            return {
                "parse": 0,
                "url": id,
                "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.base_url + "/"}
            }
        if id.startswith(self.base_url) and "/video/" in id:
            html = self._fetch_html(id)
            if html:
                player_match = re.search(r'var\s+player_aaaa\s*=\s*({[^;]+})', html)
                if player_match:
                    try:
                        player_data = json.loads(player_match.group(1))
                        m3u8_url = player_data.get("url", "")
                        if m3u8_url and ".m3u8" in m3u8_url:
                            return {
                                "parse": 0,
                                "url": m3u8_url,
                                "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.base_url + "/"}
                            }
                    except:
                        pass
        return {
            "parse": 1,
            "url": id,
            "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.base_url + "/"}
        }

    def recommendContent(self, ids, pg):
        """
        相关推荐接口
        ids: 视频ID列表，如 ['76369-sv1ep1']
        pg: 页码（从1开始）
        返回: {'list': [vod1, vod2, ...]}
        """
        result = {"list": []}
        try:
            current_id = ids[0] if ids and isinstance(ids, list) else None
            if current_id:
                url = f"{self.base_url}/video/{current_id}/"
                html = self._fetch_html(url)
                if html:
                    # 提取右侧 "他们都在看..." 推荐列表
                    recommend_pattern = r'<div\s+class="fright">.*?<div\s+class="items-title[^"]*"[^>]*>他们都在看\.\.\.</div>(.*?)</div>\s*</div>\s*</div>'
                    recommend_html = re.search(recommend_pattern, html, re.DOTALL)
                    if recommend_html:
                        recommend_content = recommend_html.group(1)
                        # 使用专门的推荐解析
                        item_pattern = r'<div\s+class="item">\s*<a\s+href="([^"]+)"[^>]*>.*?<img[^>]+(?:src|data-original)="([^"]+)"[^>]*alt="([^"]*)"[^>]*>.*?<div\s+class="item-title">([^<]+)</div>'
                        matches = re.findall(item_pattern, recommend_content, re.DOTALL)
                        for link, pic, alt, title in matches:
                            vod_id = self._extract_vod_id(link)
                            if not vod_id:
                                continue
                            result["list"].append({
                                "vod_id": vod_id,
                                "vod_name": title.strip() or alt.strip(),
                                "vod_pic": self._fix_url(pic),
                                "vod_remarks": ""
                            })
                        if result["list"]:
                            return result
        except Exception as e:
            self.log({"action": "recommend_error", "ids": ids, "error": str(e)})
        # 兜底：使用首页推荐
        try:
            home_result = self.homeVideoContent()
            if home_result and home_result.get("list"):
                result["list"] = home_result["list"][:12]
        except Exception as e:
            self.log({"action": "recommend_fallback_error", "error": str(e)})
        return result
    def destroy(self):
        """释放资源"""
        pass