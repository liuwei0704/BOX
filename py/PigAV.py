import json
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "PigAV_Stable"

    def init(self, extend=""):
        self.base_url = "https://pigav.ws"
        self.api_url = "https://pigav.ws/api/v1"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://pigav.ws",
            "Referer": "https://pigav.ws/"
        }
        self.page_size = 24

    def homeContent(self, filter):
        if not hasattr(self, 'api_url'): self.init()
        result = {"class": []}
        result["class"] = [
            {"type_id": "publishedAt", "type_name": "最新"},
            {"type_id": "hot", "type_name": "热门"},
            {"type_id": "views", "type_name": "排行"},
            {"type_id": "20", "type_name": "日韩"},
            {"type_id": "21", "type_name": "亚洲"},
            {"type_id": "22", "type_name": "自拍"},
            {"type_id": "23", "type_name": "欧美"},
            {"type_id": "24", "type_name": "动漫"}
        ]
        result["list"] = self.get_videos(f"{self.api_url}/videos?sort=-publishedAt&count={self.page_size}&start=0")
        return result

    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'api_url'): self.init()
        p = int(pg)
        start = (max(1, p) - 1) * self.page_size
    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'api_url'): self.init()
        
        # 確保 pg 是整數，並計算偏移量
        try:
            p = int(pg)
        except:
            p = 1
        
        # 上滑加載核心：計算起始位置
        start_index = (max(1, p) - 1) * self.page_size
        tid_str = str(tid)
        
        # 構造請求參數
        params = {
            "count": self.page_size,
            "start": start_index,
            "sort": "-publishedAt" # 默認按最新排序
        }
        
        if tid_str.isdigit():
            # 頻道分類請求
            headers = self.headers.copy()
            headers["Referer"] = f"{self.base_url}/videos/browse?categoryOneOf={tid_str}"
            url = f"{self.api_url}/videos?categoryOneOf={tid_str}&sort={params['sort']}&count={params['count']}&start={params['start']}"
            return {"list": self.get_videos(url, headers)}
        else:
            # 排序標籤請求 (最新/熱門/排行)
            sort_map = {"publishedAt": "-publishedAt", "hot": "-hot", "views": "-views"}
            params["sort"] = sort_map.get(tid_str, "-publishedAt")
            url = f"{self.api_url}/videos?sort={params['sort']}&count={params['count']}&start={params['start']}"
            return {"list": self.get_videos(url)}
        try:
            res = self.fetch(url, headers=self.headers, timeout=10)
            data = json.loads(res.text if hasattr(res, 'text') else res)
            vod = {
                "vod_id": vid,
                "vod_name": data.get("name", ""),
                "vod_pic": self.fix_url(data.get("thumbnailPath", "")),
                "vod_remarks": self.format_time(data.get("duration", 0)),
                "vod_actor": data.get("channel", {}).get("displayName", ""),
                "vod_content": data.get("description", ""),
                "vod_play_from": "PigAV",
                "vod_play_url": f"播放正片${vid}"
            }
            return {"list": [vod]}
        except:
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        if not hasattr(self, 'api_url'): self.init()
        p = int(pg)
        start = (max(1, p) - 1) * self.page_size
        url = f"{self.api_url}/search/videos?search={key}&count={self.page_size}&start={start}"
        return {"list": self.get_videos(url)}

    def playerContent(self, flag, id, vipFlags):
        url = f"{self.api_url}/videos/{id}"
        play_headers = {
            "User-Agent": self.headers["User-Agent"],
            "Referer": f"https://pigav.ws/videos/{id}",
            "Origin": "https://pigav.ws",
            "Range": "bytes=0-",
            "Connection": "keep-alive"
        }
        try:
            res = self.fetch(url, headers=self.headers, timeout=12)
            data = json.loads(res.text if hasattr(res, 'text') else res)
            play_url = ""
            streaming = data.get("streamingPlaylists", [])
            if streaming:
                idx = max(0, len(streaming) - 2)
                play_url = streaming[idx].get("playlistUrl")
            if not play_url:
                files = data.get("files", [])
                if files:
                    suitable_files = [f for f in files if f.get("resolution", {}).get("height", 0) <= 720]
                    best_file = suitable_files[-1] if suitable_files else files[0]
                    play_url = best_file.get("fileUrl") or best_file.get("fileDownloadUrl")
            if play_url:
                return {"parse": 0, "url": self.fix_url(play_url), "header": play_headers, "timeout": 60}
        except: pass
        return {"parse": 0, "url": ""}

    def get_videos(self, url, headers=None):
        videos = []
        try:
            res = self.fetch(url, headers=headers if headers else self.headers, timeout=10)
            content = res.text if hasattr(res, 'text') else res
            data = json.loads(content)
            items = data.get("data", []) if isinstance(data, dict) else data
            for item in items:
                videos.append({
                    "vod_id": item.get("shortUUID") or item.get("uuid"),
                    "vod_name": item.get("name", ""),
                    "vod_pic": self.fix_url(item.get("thumbnailPath", "")),
                    "vod_remarks": self.format_time(item.get("duration", 0))
                })
        except: pass
        return videos

    def fix_url(self, path):
        if not path: return ""
        if path.startswith("http"): return path
        return self.base_url + path

    def format_time(self, seconds):
        try:
            sec = int(seconds)
            m, s = divmod(sec, 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
        except: return ""