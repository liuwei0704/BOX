# coding: utf-8
import json
import re
from urllib.parse import quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://5lxtv.com"
        self.play_host = "https://5x.avtube.xyz"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.58 Mobile Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json"
        }
        self.classes = [
            {"type_id": "18", "type_name": "破坏馆"},
            {"type_id": "20", "type_name": "黑料"},
            {"type_id": "22", "type_name": "绿帽NTR"},
            {"type_id": "25", "type_name": "魔剧AI"},
            {"type_id": "21", "type_name": "Fc2"},
            {"type_id": "1", "type_name": "无码"},
            {"type_id": "2", "type_name": "欧美"},
            {"type_id": "3", "type_name": "有码"},
            {"type_id": "4", "type_name": "动画"},
            {"type_id": "5", "type_name": "自拍"},
            {"type_id": "7", "type_name": "有码中文"},
            {"type_id": "10", "type_name": "素人"},
            {"type_id": "11", "type_name": "无码中文"},
        ]
        self.video_cache = {}
        self.filters = {}

    def getName(self):
        return "51xtv"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _fetch_classes(self):
        try:
            url = f"{self.host}/movies/channel"
            resp = self.fetch(url, headers=self.headers)
            if resp and resp.status_code == 200:
                data = resp.json()
                self.classes = []
                for item in data:
                    self.classes.append({
                        "type_id": str(item.get("ID", "")),
                        "type_name": item.get("Name", "")
                    })
                return True
        except Exception as e:
            self.log({"action": "fetch_classes_fail", "error": str(e)})
        return False

    def _fetch_tags(self):
        try:
            url = f"{self.host}/movies/class"
            resp = self.post(url, json={"page": 1}, headers=self.headers)
            if resp and resp.status_code == 200:
                data = resp.json()
                tags = data.get("Class", [])
                self.filters = {}
                tag_options = [{"n": "全部", "v": ""}]
                for tag in tags:
                    tag_options.append({"n": tag.get("name", ""), "v": tag.get("id", "")})
                self.filters = {
                    "1": [{"key": "tag", "name": "标签", "value": tag_options}]
                }
                return True
        except Exception as e:
            self.log({"action": "fetch_tags_fail", "error": str(e)})
        return False

    def homeContent(self, filter=False):
        if not self.classes:
            self._fetch_classes()
        if filter and not self.filters:
            self._fetch_tags()
        return {
            "class": self.classes,
            "filters": self.filters if filter else {}
        }

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        return self.categoryContent(tid="-1", pg="1", filter=False, extend={})

    def categoryContent(self, tid, pg, filter=False, extend={}):
        if not self.classes:
            self._fetch_classes()

        page = int(pg) if pg else 1
        extend_dict = self._parse_extend(extend)
        
        payload = {
            "page": page,
            "type": 1,
            "id": [int(tid)] if tid and tid != "-1" else [0]
        }
        
        if extend_dict.get("tag"):
            payload["tag"] = int(extend_dict["tag"])

        try:
            url = f"{self.host}/movies/lists"
            resp = self.post(url, json=payload, headers=self.headers)
            if resp and resp.status_code == 200:
                data = resp.json()
                movies = data.get("Movies", [])
                total = data.get("Total", 0)
                page_count = data.get("PageCount", 1)
                
                video_list = []
                for item in movies:
                    vid = str(item.get("id", ""))
                    if not vid:
                        continue
                    self.video_cache[vid] = item
                    video_list.append({
                        "vod_id": vid,
                        "vod_name": item.get("title", ""),
                        "vod_pic": item.get("backdrop_path", item.get("poster_path", "")),
                        "vod_remarks": item.get("creater_date", "")
                    })
                
                return {
                    "list": video_list,
                    "page": page,
                    "pagecount": page_count if page_count > 0 else 1,
                    "limit": len(video_list),
                    "total": total
                }
        except Exception as e:
            self.log({"action": "category_fail", "error": str(e)})
        
        return {"list": [], "page": page, "pagecount": 1, "limit": 0, "total": 0}

    def _parse_extend(self, extend):
        if not extend:
            return {}
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            extend = extend.strip()
            if extend.startswith("{") and "=" in extend:
                result = {}
                content = extend[1:-1]
                for part in content.split(","):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        result[k.strip()] = v.strip()
                return result
            if extend.startswith("{") and ":" in extend:
                try:
                    return json.loads(extend)
                except:
                    pass
            result = {}
            for part in extend.split(","):
                if "=" in part:
                    k, v = part.split("=", 1)
                    result[k.strip()] = v.strip()
            return result
        return {}

    def _extract_code(self, text):
        """从文本中提取影片编号"""
        patterns = [
            r'([A-Z]{2,5}[-]?[0-9]{2,5})',
            r'([A-Z]{2,5}\s*[0-9]{2,5})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text.upper())
            if match:
                return match.group(1).replace(" ", "-")
        return None

    def _get_code_from_preview(self, preview_url):
        """从preview URL中提取影片编号和路径"""
        if not preview_url:
            return None, None
        
        # 提取编号
        code_match = re.search(r'([A-Z]{2,5}[-]?[0-9]{2,5})', preview_url)
        code = code_match.group(1) if code_match else None
        
        # 提取路径: /2026/3/0719/SDAB-352/
        path_match = re.search(r'/(2026/\d{1,2}/\d{4}/[A-Z0-9-]+)/', preview_url)
        path = path_match.group(1) if path_match else None
        
        return code, path

    def _build_play_url_from_preview(self, preview_url):
        """从preview URL直接构建播放地址"""
        code, path = self._get_code_from_preview(preview_url)
        if path:
            # 路径已包含年/月/日+编号
            # 直接用这个路径构建播放地址
            return f"{self.play_host}/video/{path}/r/playlist.m3u8"
        return None

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        
        vid = str(ids[0])
        item = self.video_cache.get(vid)
        if not item:
            self._fetch_all_videos()
            item = self.video_cache.get(vid)
        
        if not item:
            return {"list": []}
        
        title = item.get("title", "")
        preview_url = item.get("preview", "")
        
        # 从preview URL构建播放地址
        play_url = self._build_play_url_from_preview(preview_url)
        
        # 如果构建失败，尝试从标题提取编号再构建
        if not play_url:
            code = self._extract_code(title)
            if code:
                date = item.get("creater_date", "")
                if date:
                    parts = date.split("/")
                    if len(parts) == 3:
                        year = parts[0]
                        month = str(int(parts[1]))
                        day = parts[2]
                        date_path = f"{year}/{month}/{day}{month}{day}"
                        play_url = f"{self.play_host}/video/{date_path}/{code}/r/playlist.m3u8"
        
        # 最终降级：使用preview
        if not play_url:
            play_url = preview_url
        
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": item.get("backdrop_path", item.get("poster_path", "")),
            "vod_remarks": item.get("creater_date", ""),
            "vod_content": item.get("overview", ""),
            "vod_play_from": "直链",
            "vod_play_url": f"播放${play_url}" if play_url else ""
        }
        return {"list": [vod]}

    def _fetch_all_videos(self, tid="-1", pages=2):
        for page in range(1, pages + 1):
            payload = {
                "page": page,
                "type": 1,
                "id": [int(tid)] if tid and tid != "-1" else [0]
            }
            try:
                url = f"{self.host}/movies/lists"
                resp = self.post(url, json=payload, headers=self.headers)
                if resp and resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("Movies", []):
                        vid = str(item.get("id", ""))
                        if vid:
                            self.video_cache[vid] = item
            except:
                pass

    def searchContent(self, key, quick=False, pg="1"):
        page = int(pg) if pg else 1
        payload = {
            "page": page,
            "type": 1,
            "id": [0],
            "keyword": key
        }
        
        try:
            url = f"{self.host}/movies/lists"
            resp = self.post(url, json=payload, headers=self.headers)
            if resp and resp.status_code == 200:
                data = resp.json()
                movies = data.get("Movies", [])
                total = data.get("Total", 0)
                page_count = data.get("PageCount", 1)
                
                video_list = []
                for item in movies:
                    vid = str(item.get("id", ""))
                    if not vid:
                        continue
                    self.video_cache[vid] = item
                    video_list.append({
                        "vod_id": vid,
                        "vod_name": item.get("title", ""),
                        "vod_pic": item.get("backdrop_path", item.get("poster_path", "")),
                        "vod_remarks": item.get("creater_date", "")
                    })
                
                return {
                    "list": video_list,
                    "page": page,
                    "pagecount": page_count if page_count > 0 else 1,
                    "limit": len(video_list),
                    "total": total
                }
        except Exception as e:
            self.log({"action": "search_fail", "error": str(e)})
        
        return {"list": [], "page": page, "pagecount": 1, "limit": 0, "total": 0}

    def playerContent(self, flag, id, vipFlags=""):
        """播放 - 直接播放传入的URL"""
        if not id:
            return {"parse": 1, "url": ""}
        
        # 如果已经是完整URL（m3u8/mp4），直接返回
        if id.startswith("http://") or id.startswith("https://"):
            if ".m3u8" in id or ".mp4" in id:
                return {"parse": 0, "url": id, "header": {"Referer": self.host + "/"}}
            return {"parse": 1, "url": id}
        
        # 其他情况，尝试从缓存获取
        item = self.video_cache.get(str(id))
        if item:
            preview_url = item.get("preview", "")
            if preview_url:
                return {"parse": 1, "url": preview_url}
        
        return {"parse": 1, "url": id}

    def localProxy(self, param):
        return [404, "text/plain", "Not Found"]

    def destroy(self):
        self.video_cache.clear()