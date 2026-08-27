# coding: utf-8
"""
站点: 心动短剧
域名: https://xindongduanju.com
"""
import json
import re
from urllib.parse import quote

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://xindongduanju.com"
        self.api_host = "https://xindongduanju.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "recommend", "type_name": "为你推荐"},
            {"type_id": "all", "type_name": "全部"},
            {"type_id": "重生", "type_name": "重生"},
            {"type_id": "甜宠", "type_name": "甜宠"},
            {"type_id": "都市", "type_name": "都市"},
            {"type_id": "古装", "type_name": "古装"},
            {"type_id": "喜剧", "type_name": "喜剧"},
            {"type_id": "家庭", "type_name": "家庭"}
        ]
        self.filters = {k: [] for k in ["recommend", "all", "重生", "甜宠", "都市", "古装", "喜剧", "家庭"]}

    def getName(self):
        return "心动短剧"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, verify=False)
            if resp and resp.status_code == 200:
                return resp.text
            return ""
        except:
            return ""

    def _fetch_json(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, verify=False)
            if resp and resp.status_code == 200:
                return json.loads(resp.text)
            return None
        except:
            return None

    def _clean_pic(self, url):
        return url if url else ""

    def _parse_card_items(self, html):
        items = []
        if not html:
            return items
        pattern = r'<a[^>]*href="(/play/[^"]+)"[^>]*>(.*?)</a>'
        for match in re.findall(pattern, html, re.DOTALL):
            href, content = match
            if not href or '/play/' not in href:
                continue
            vid = href.replace('/play/', '').split('-')[0]
            title_match = re.search(r'<h[23][^>]*>(.*?)</h[23]>', content, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_match.group(1).strip()) if title_match else ''
            if not title:
                continue
            img_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*>', content, re.DOTALL)
            pic = img_match.group(1) if img_match else ''
            # 补全图片URL
            if pic and pic.startswith("/"):
                pic = self.host + pic
            if pic and "?lsj-fallback=" in pic:
                pic = pic.split("?lsj-fallback=")[0]
            # 如果没有图片，使用默认占位图
            if not pic:
                pic = self.host + "/logo-192.png"
            remark_match = re.search(r'<span[^>]*>(\d+[亿万]?\s*热度|\d+\s*集)</span>', content, re.DOTALL)
            remark = remark_match.group(1).strip() if remark_match else ''
            items.append({"vod_id": vid, "vod_name": title, "vod_pic": pic, "vod_remarks": remark})
        return items
    def _parse_api_items(self, items):
        result = []
        for it in items or []:
            vid = it.get("sourceId") or it.get("lsj_id") or str(it.get("id", ""))
            if vid:
                pic = it.get("cover", "")
                # 如果是相对路径，补全为完整URL
                if pic and pic.startswith("/"):
                    pic = self.host + pic
                # 如果已经是完整URL，但包含lsj-fallback参数，移除
                elif pic and "?lsj-fallback=" in pic:
                    pic = pic.split("?lsj-fallback=")[0]
                # 如果图片地址为空或无效，使用默认占位图
                if not pic:
                    pic = self.host + "/logo-192.png"
                result.append({
                    "vod_id": vid,
                    "vod_name": it.get("title", ""),
                    "vod_pic": pic,
                    "vod_remarks": it.get("viewCountDisplay", "") or f"{it.get('episodeCount', 0)}集"
                })
        return result
    def _fetch_api_dramas(self, offset=0, limit=20):
        url = f"{self.api_host}/api/dramas?offset={offset}&limit={limit}"
        data = self._fetch_json(url)
        if data:
            if "items" in data:
                return data["items"]
            if "list" in data:
                return data["list"]
            if "data" in data:
                if isinstance(data["data"], list):
                    return data["data"]
                if "items" in data["data"]:
                    return data["data"]["items"]
            if isinstance(data, list):
                return data
        return None

    def homeVideoContent(self):
        api_items = self._fetch_api_dramas(0, 30)
        if api_items:
            items = self._parse_api_items(api_items)
            return {"list": items[:50]}
        html = self._fetch_html(self.host + "/")
        if not html:
            return {"list": []}
        items = self._parse_card_items(html)
        return {"list": items[:50]}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except:
            page = 1
        if page < 1:
            page = 1
        offset = (page - 1) * 20
        if tid in ["recommend", "all"]:
            api_items = self._fetch_api_dramas(offset, 20)
            if api_items is not None:
                items = self._parse_api_items(api_items)
                total = 12599
                try:
                    url = f"{self.api_host}/api/dramas?offset=0&limit=1"
                    resp = self.fetch(url, headers=self.headers, verify=False)
                    if resp and resp.status_code == 200:
                        data = json.loads(resp.text)
                        if "total" in data:
                            total = data["total"]
                except:
                    pass
                return {"list": items, "page": page, "pagecount": (total + 19) // 20, "limit": 20, "total": total}
        search_url = f"{self.host}/search?q={quote(tid)}"
        html = self._fetch_html(search_url)
        if not html:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}
        items = self._parse_card_items(html)
        return {"list": items, "page": page, "pagecount": 1, "limit": 20, "total": len(items)}
    def detailContent(self, ids):
        # 兼容多种传入格式：字符串、列表、元组、整数
        if isinstance(ids, (list, tuple)):
            vid = str(ids[0]) if ids else ""
        else:
            vid = str(ids)
        if not vid:
            return {"list": []}
        
        # 如果是数字ID，先通过API获取真实sourceId和剧集信息
        source_id = vid
        title = ""
        cover = ""
        total_episodes = 0
        
        if vid.isdigit():
            api_url = f"{self.api_host}/api/dramas/{vid}"
            data = self._fetch_json(api_url)
            if data:
                source_id = data.get("lsj_id", vid)
                title = data.get("title", "")
                cover = data.get("cover", "")
                # 补全图片URL并移除lsj-fallback参数
                if cover and cover.startswith("/"):
                    cover = self.host + cover
                if cover and "?lsj-fallback=" in cover:
                    cover = cover.split("?lsj-fallback=")[0]
                total_episodes = data.get("total_episodes", 0)
        
        # 尝试从剧集列表API获取总集数
        if total_episodes == 0:
            list_url = f"{self.api_host}/api/dramas?offset=0&limit=100"
            list_data = self._fetch_json(list_url)
            if list_data and list_data.get("items"):
                for item in list_data["items"]:
                    if str(item.get("id")) == vid or item.get("lsj_id") == source_id:
                        total_episodes = item.get("episodeCount", 0)
                        if not title:
                            title = item.get("title", "")
                        if not cover:
                            cover = item.get("cover", "")
                            if cover and cover.startswith("/"):
                                cover = self.host + cover
                            if cover and "?lsj-fallback=" in cover:
                                cover = cover.split("?lsj-fallback=")[0]
                        break
        
        # 如果总集数为0，默认设为1
        if total_episodes == 0:
            total_episodes = 1
        
        # 如果封面还是空，使用默认图片
        if not cover:
            cover = self.host + "/logo-192.png"
        
        # 构建播放列表 - 使用播放页面URL
        play_parts = []
        for i in range(1, total_episodes + 1):
            ep_title = f"第{i}集"
            play_url = f"{self.host}/play/lsj/{source_id}-{i}"
            play_parts.append(f"{ep_title}${play_url}")
        
        if not play_parts:
            play_url = f"{self.host}/play/lsj/{source_id}-1"
            play_parts.append(f"第1集${play_url}")
        
        vod = {
            "vod_id": vid,
            "vod_name": title or "心动短剧",
            "vod_pic": cover,
            "vod_remarks": f"{total_episodes}集" if total_episodes else "",
            "vod_actor": "",
            "vod_director": "",
            "vod_content": "",
            "vod_play_from": "在线播放",
            "vod_play_url": "#".join(play_parts) if play_parts else ""
        }
        return {"list": [vod]}
    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        search_url = f"{self.host}/search?q={quote(key)}"
        html = self._fetch_html(search_url)
        if not html:
            return {"list": [], "page": 1}
        items = self._parse_card_items(html)
        return {"list": items, "page": 1}

    def playerContent(self, flag, id, vipFlags):
        import time
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        if id.startswith("/"):
            id = self.host + id
        
        # 如果id是播放页面URL，需要提取真正的播放地址
        if "/play/lsj/" in id:
            # 从播放页面提取token
            html = self._fetch_html(id)
            if html:
                token_match = re.search(r'/api/playback/hls\?s=([^"\'&\s<>]+)', html)
                if token_match:
                    token = token_match.group(1)
                    play_url = f"{self.api_host}/api/playback/hls?s={token}&_t={int(time.time()*1000)}"
                    # 提取集数用于Referer
                    episode = 1
                    match = re.search(r'-(\d+)', id)
                    if match:
                        episode = int(match.group(1))
                    referer = id
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Referer": referer,
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                        "Origin": self.host,
                        "Connection": "keep-alive",
                        "Sec-Fetch-Dest": "empty",
                        "Sec-Fetch-Mode": "cors",
                        "Sec-Fetch-Site": "same-origin",
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0",
                        "X-Episode": str(episode)
                    }
                    return {"parse": 0, "url": play_url, "header": headers}
        
        # 如果已经是播放地址，直接返回
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": self.host,
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        return {"parse": 0, "url": id, "header": headers}
    def localProxy(self, param):
        return [404, "text/plain", b""]