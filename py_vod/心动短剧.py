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
            "X-Requested-With": "XMLHttpRequest"
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
            remark_match = re.search(r'<span[^>]*>(\d+[亿万]?\s*热度|\d+\s*集)</span>', content, re.DOTALL)
            remark = remark_match.group(1).strip() if remark_match else ''
            items.append({"vod_id": vid, "vod_name": title, "vod_pic": pic, "vod_remarks": remark})
        return items

    def _parse_api_items(self, items):
        result = []
        for it in items or []:
            vid = it.get("sourceId") or it.get("lsj_id") or str(it.get("id", ""))
            if vid:
                result.append({
                    "vod_id": vid,
                    "vod_name": it.get("title", ""),
                    "vod_pic": it.get("cover", ""),
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
        vid = str(ids[0]) if ids else ""
        if not vid:
            return {"list": []}
        if vid.startswith("lsj/"):
            url = f"{self.host}/play/{vid}-1"
        elif vid.startswith("lsj_"):
            url = f"{self.host}/play/lsj/{vid.replace('lsj_', '')}-1"
        else:
            url = f"{self.host}/play/lsj/{vid}-1"
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        title_match = re.search(r'<title>(.*?)</title>', html)
        title = title_match.group(1).replace("第1集在线观看 - 心动短剧", "").strip() if title_match else ""
        cover_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        cover = cover_match.group(1) if cover_match else ""
        ep_count_match = re.search(r'共\s*(\d+)\s*集', html)
        ep_count = ep_count_match.group(1) if ep_count_match else "0"
        video_urls = []
        next_data_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if next_data_match:
            try:
                data = json.loads(next_data_match.group(1))
                props = data.get("props", {}).get("pageProps", data.get("pageProps", {}))
                if "allEpisodes" in props:
                    for ep in props["allEpisodes"]:
                        if "video_url" in ep:
                            video_urls.append(ep["video_url"])
                elif "episode" in props and "video_url" in props["episode"]:
                    video_urls.append(props["episode"]["video_url"])
            except:
                pass
        if not video_urls:
            video_urls = re.findall(r'"video_url"\s*:\s*"([^"]+)"', html)
        if not video_urls:
            video_urls = re.findall(r'(/api/playback/hls\?[^"\'<>]+)', html)
        if not video_urls:
            return {"list": []}
        seen = set()
        unique_urls = []
        for u in video_urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)
        play_parts = []
        for i, vurl in enumerate(unique_urls):
            ep_num = i + 1
            ep_title = f"第{ep_num}集"
            if vurl.startswith("/"):
                vurl = self.host + vurl
            play_parts.append(f"{ep_title}${vurl}")
        vod = {
            "vod_id": vid,
            "vod_name": title or "视频",
            "vod_pic": cover,
            "vod_remarks": f"{ep_count}集" if ep_count else "",
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
        if not id:
            return {"parse": 1, "url": "", "header": {}}
        if id.startswith("/"):
            id = self.host + id
        
        # 尝试从URL中提取集数信息
        import re
        episode = 1
        # 检查URL中是否有集数信息
        ep_match = re.search(r'-(\\d+)(?=&|$|#)', id)
        if ep_match:
            episode = int(ep_match.group(1))
        
        # 从detailContent传入的id中提取drama_id
        # 如果id中包含drama_id参数
        drama_match = re.search(r'drama_id=([^&]+)', id)
        drama_id = drama_match.group(1) if drama_match else ''
        
        # 添加额外参数
        if '?' in id:
            id = id + f"&ep={episode}&episode={episode}"
        else:
            id = id + f"?ep={episode}&episode={episode}"
        
        # 如果有drama_id，也加上
        if drama_id:
            id = id + f"&drama_id={drama_id}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.host + "/",
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": self.host,
            "Connection": "keep-alive",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        }
        
        return {"parse": 0, "url": id, "header": headers}
    def localProxy(self, param):
        return [404, "text/plain", b""]