# coding: utf-8
import re
import json
from urllib.request import urlopen, Request
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://porncloud.tv"
        self.classes = [
            {"type_id": "jav", "type_name": "JAV视频"},
            {"type_id": "global", "type_name": "全球资源"},
            {"type_id": "domestic", "type_name": "国产资源"},
            {"type_id": "domestic-spy", "type_name": "国产偷拍"},
            {"type_id": "influencer", "type_name": "网红福利姬"},
            {"type_id": "photo-sets", "type_name": "写真套图"},
            {"type_id": "onlyfans", "type_name": "OnlyFans"},
            {"type_id": "black-stockings", "type_name": "黑丝"},
            {"type_id": "coser", "type_name": "Coser"},
            {"type_id": "private-video", "type_name": "私拍"},
            {"type_id": "one-to-one", "type_name": "1对1"},
        ]
        self.filters = {c["type_id"]: [] for c in self.classes}
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def init(self, extend):
        pass

    def _fetch(self, url, headers=None):
        try:
            req = Request(url, headers=headers or {"User-Agent": self.ua})
            with urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except:
            return ""

    def _fix_url(self, url):
        if not url: return ""
        if url.startswith("//"): return "https:" + url
        if url.startswith("/"): return self.host + url
        if not url.startswith("http"): return self.host + "/" + url
        return url

    def _parse_pay_status_from_nuxt(self, html, target_id=None):
        """从 __NUXT_DATA__ 中提取视频的付费状态"""
        pay_map = {}
        try:
            nuxt_match = re.search(r'<script[^>]+id="__NUXT_DATA__"[^>]*>([^<]+)</script>', html)
            if nuxt_match:
                data_str = nuxt_match.group(1)
                nuxt_data = json.loads(data_str)
                def find_items(obj):
                    if isinstance(obj, dict):
                        if "items" in obj and isinstance(obj["items"], list):
                            return obj["items"]
                        for v in obj.values():
                            result = find_items(v)
                            if result:
                                return result
                    elif isinstance(obj, list):
                        for item in obj:
                            result = find_items(item)
                            if result:
                                return result
                    return None
                
                items = find_items(nuxt_data)
                if items and isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            vid = item.get("id")
                            is_free = item.get("isFree")
                            if vid and is_free is not None:
                                pay_map["/media/" + vid] = is_free
                                pay_map["/play/" + vid] = is_free
                                # 如果指定了target_id，直接返回该视频的状态
                                if target_id and vid == target_id:
                                    return not is_free
        except:
            pass
        return pay_map

    def _parse_videos(self, html):
        """解析视频列表，付费视频在备注中显示角标"""
        videos = []
        
        # 从 __NUXT_DATA__ 提取付费状态
        pay_map = self._parse_pay_status_from_nuxt(html)
        
        # 从 HTML 中检测付费标签
        pattern = r'<a[^>]+href="(/(?:play|media)/[^"]+)"[^>]*>'
        for match in re.finditer(pattern, html):
            href = match.group(1)
            if not href or href == "/play/" or href == "/media/":
                continue
            if "/category/" in href or "/tag/" in href:
                continue
            
            block_start = max(0, match.start() - 1000)
            block_end = min(len(html), match.end() + 1000)
            block = html[block_start:block_end]
            
            # 提取标题
            title = ""
            alt_match = re.search(r'alt="([^"]+)"', block)
            if alt_match:
                title = alt_match.group(1)
            if not title:
                text_match = re.search(r'>([^<]+)<', match.group(0))
                if text_match:
                    title = text_match.group(1).strip()
            if not title:
                title = href.split("/")[-1]
            
            # 提取图片
            pic = ""
            img_patterns = [
                r'<img[^>]+src="([^"]+)"',
                r'<img[^>]+data-src="([^"]+)"',
                r'<img[^>]+data-original="([^"]+)"',
            ]
            for p in img_patterns:
                img_match = re.search(p, block, re.I)
                if img_match:
                    pic = img_match.group(1).strip('"\'')
                    if pic and not pic.startswith("data:"):
                        break
            
            # 判断是否为付费视频
            is_pay = False
            
            # 从 JSON 数据中检查
            if href in pay_map:
                is_pay = not pay_map[href]
            
            # 从 HTML 标签中检查（兜底）
            if not is_pay:
                if '付费会员' in block or 'lock-badge' in block or '登录查看' in block:
                    is_pay = True
            
            # 设置备注角标
            remark = "🔒 VIP付费" if is_pay else "免费"
            
            if title:
                videos.append({
                    "vod_id": href,
                    "vod_name": title.strip(),
                    "vod_pic": self._fix_url(pic),
                    "vod_remarks": remark
                })
        
        # 去重
        seen = set()
        result = []
        for v in videos:
            if v["vod_id"] not in seen:
                seen.add(v["vod_id"])
                result.append(v)
        return result

    def homeVideoContent(self):
        """首页视频推荐，TVBox加载必需"""
        html = self._fetch(self.host)
        videos = self._parse_videos(html)
        return {"list": videos[:40]}

    def homeContent(self, filter=False):
        html = self._fetch(self.host)
        videos = self._parse_videos(html)
        return {"class": self.classes, "filters": self.filters, "list": videos[:40]}

    def categoryContent(self, tid, pg, filter=False, extend={}):
        pg = int(pg) if str(pg).isdigit() else 1
        url_map = {
            "jav": "/jav-list",
            "global": "/media",
            "domestic": "/media/category/domestic",
            "domestic-spy": "/media/category/domestic-spy",
            "influencer": "/media/category/influencer",
            "photo-sets": "/media/category/photo-sets",
            "onlyfans": "/media/tag/onlyfans",
            "black-stockings": "/media/tag/black-stockings",
            "coser": "/media/tag/coser",
            "private-video": "/media/tag/private-video",
            "one-to-one": "/media/tag/one-to-one",
        }
        path = url_map.get(tid, "/media")
        url = self.host + path + "?page=" + str(pg)
        html = self._fetch(url)
        videos = self._parse_videos(html)
        return {"list": videos, "page": pg, "pagecount": 100, "limit": 20, "total": len(videos)}

    def detailContent(self, ids):
        result = []
        if isinstance(ids, str):
            ids = [ids]
        for vid in ids:
            if not vid.startswith("/"):
                vid = "/" + vid
            url = self._fix_url(vid)
            html = self._fetch(url)
            title = ""
            desc = ""
            pic = ""
            play_url = ""
            remark = ""
            
            # 从 __NUXT_DATA__ 提取当前视频的付费状态
            current_id = vid.split("/")[-1]
            is_pay = False
            try:
                nuxt_match = re.search(r'<script[^>]+id="__NUXT_DATA__"[^>]*>([^<]+)</script>', html)
                if nuxt_match:
                    data_str = nuxt_match.group(1)
                    nuxt_data = json.loads(data_str)
                    def find_video(obj, target_id):
                        if isinstance(obj, dict):
                            if "id" in obj and str(obj.get("id")) == str(target_id):
                                return obj
                            for v in obj.values():
                                result = find_video(v, target_id)
                                if result:
                                    return result
                        elif isinstance(obj, list):
                            for item in obj:
                                result = find_video(item, target_id)
                                if result:
                                    return result
                        return None
                    
                    video_data = find_video(nuxt_data, current_id)
                    if video_data and isinstance(video_data, dict):
                        is_free = video_data.get("isFree")
                        if is_free is not None:
                            is_pay = not is_free
            except:
                pass
            
            # 从 JSON-LD 提取
            ld_pattern = r'<script type="application/ld\+json">([^<]+)</script>'
            for match in re.finditer(ld_pattern, html):
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, dict):
                        if data.get("@type") == "VideoObject":
                            play_url = data.get("contentUrl") or ""
                            if not pic:
                                thumbs = data.get("thumbnailUrl")
                                if thumbs and isinstance(thumbs, list) and thumbs:
                                    pic = thumbs[0]
                            if not title:
                                title = data.get("name") or ""
                            if not desc:
                                desc = data.get("description") or ""
                except:
                    pass
            
            # 从 OG 标签提取
            if not play_url:
                og_match = re.search(r'<meta[^>]+property="og:video"[^>]+content="([^"]+)"', html)
                if og_match:
                    play_url = og_match.group(1)
            if not title:
                h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
                if h1_match:
                    title = h1_match.group(1).strip()
            if not title:
                title_match = re.search(r'<title>色情云 PornCloud - ([^<]+)</title>', html)
                if title_match:
                    title = title_match.group(1).strip()
            if not pic:
                og_img = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
                if og_img:
                    pic = og_img.group(1)
            if not desc:
                desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
                if desc_match:
                    desc = desc_match.group(1)
            if not play_url:
                m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
                if m3u8_match:
                    play_url = m3u8_match.group(0)
            
            # 设置角标
            remark = "🔒 VIP付费" if is_pay else "免费"
            
            display_title = title or vid.split("/")[-1]
            
            result.append({
                "vod_id": vid,
                "vod_name": display_title,
                "vod_pic": self._fix_url(pic),
                "vod_content": desc or "",
                "vod_remarks": remark,
                "vod_play_from": "PornCloud",
                "vod_play_url": "播放$" + play_url if play_url else "播放$" + vid
            })
        return {"list": result}

    def searchContent(self, key, quick=False, pg="1"):
        pg = int(pg) if str(pg).isdigit() else 1
        search_url = self.host + "/search/" + key.replace(" ", "+")
        if pg > 1:
            search_url += "?page=" + str(pg)
        html = self._fetch(search_url)
        videos = self._parse_videos(html)
        total = len(videos)
        pagecount = 1
        page_match = re.search(r'pagecount["\']?\s*[:=]\s*(\d+)', html)
        if page_match:
            pagecount = int(page_match.group(1))
        return {"list": videos, "page": pg, "pagecount": pagecount, "limit": 20, "total": total}

    def playerContent(self, flag, id, vipFlags=None):
        """播放地址解析 - 优先直链，降级嗅探"""
        if id.startswith("http"):
            return {
                "parse": 0,
                "url": id,
                "header": {
                    "User-Agent": self.ua,
                    "Referer": self.host + "/"
                }
            }
        
        vid = id.split("/")[-1]
        play_page_url = self.host + "/play/" + vid
        
        html = self._fetch(play_page_url)
        play_url = ""
        
        # 从 JSON-LD 提取
        ld_pattern = r'<script type="application/ld\+json">([^<]+)</script>'
        for match in re.finditer(ld_pattern, html):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict) and data.get("@type") == "VideoObject":
                    play_url = data.get("contentUrl") or ""
                    break
            except:
                pass
        
        # 从 HTML 中提取 m3u8 链接
        if not play_url:
            m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
            if m3u8_match:
                play_url = m3u8_match.group(0)
        
        if play_url:
            return {
                "parse": 0,
                "url": play_url,
                "header": {
                    "User-Agent": self.ua,
                    "Referer": self.host + "/"
                }
            }
        
        return {
            "parse": 1,
            "url": play_page_url,
            "header": {
                "User-Agent": self.ua,
                "Referer": self.host + "/"
            }
        }

    def localProxy(self, params):
        if not params:
            return None
        url = params.get("url") or params.get("src") or ""
        if not url or ".m3u8" not in url:
            return None
        try:
            req = Request(url, headers={"User-Agent": self.ua, "Referer": self.host + "/"})
            with urlopen(req, timeout=15) as resp:
                content = resp.read().decode('utf-8')
            base_url = url.rsplit("/", 1)[0] + "/"
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith("#EXT-X-MAP:URI="):
                    match = re.search(r'URI="([^"]+)"', line)
                    if match:
                        init_url = match.group(1)
                        if not init_url.startswith("http"):
                            init_url = base_url + init_url
                        new_lines.append('#EXT-X-MAP:URI="' + init_url + '"')
                    else:
                        new_lines.append(line)
                elif line and not line.startswith("#") and not line.startswith("http"):
                    new_lines.append(base_url + line)
                else:
                    new_lines.append(line)
            return [200, "application/vnd.apple.mpegurl", ("\n".join(new_lines) + "\n").encode("utf-8")]
        except Exception as e:
            return None

    def getDependence(self):
        return []

    def destroy(self):
        pass