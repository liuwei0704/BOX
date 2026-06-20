#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests

class Spider:
    def getName(self):
        return "麦田短劇"
    
    def getDependence(self):
        return []
    
    def init(self, extend=""):
        self.api_host = "https://apitw.ryehub.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            "Referer": "https://www.ryehub.com/"
        }
        self.categories = [
            {"type_id": "0", "type_name": "全部"},
            {"type_id": "67", "type_name": "女頻片"},
            {"type_id": "87", "type_name": "男頻片"},
            {"type_id": "91", "type_name": "穿越"},
            {"type_id": "92", "type_name": "重生"},
            {"type_id": "93", "type_name": "心聲"},
            {"type_id": "94", "type_name": "逆襲"},
            {"type_id": "95", "type_name": "修仙"},
            {"type_id": "96", "type_name": "萌娃"},
            {"type_id": "97", "type_name": "動漫"}
        ]
        self.limit = 20
    
    def _api_get(self, path, params=None):
        try:
            if params is None:
                params = {}
            params["__platform"] = "1"
            url = f"{self.api_host}{path}"
            r = requests.get(url, headers=self.headers, params=params, timeout=15)
            return r.json()
        except:
            return None
    
    def _fetch_video(self, vid):
        return self._api_get("/api/video/videodata", {"vid": vid})
    
    def _fetch_list(self, cate_id, page):
        return self._api_get("/api/video/indexList", {"cate_id": cate_id, "page": page, "limit": self.limit})
    
    def _fetch_search(self, keyword, page):
        return self._api_get("/api/video/lists", {"keytext": keyword, "page": page, "limit": self.limit})
    
    def _build_list(self, rows):
        result = []
        for row in rows:
            result.append({
                "vod_id": str(row.get("id", "")),
                "vod_name": row.get("name", ""),
                "vod_pic": row.get("img", ""),
                "vod_remarks": "短剧"
            })
        return result
    
    def homeContent(self, filter):
        data = self._fetch_list(0, 1)
        list_data = self._build_list(data.get("rows", [])) if data else []
        return {
            "class": self.categories,
            "list": list_data,
            "filters": {}
        }
    
    def homeVideoContent(self):
        return self.homeContent(False)
    
    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        cate_id = int(tid) if tid else 0
        data = self._fetch_list(cate_id, page)
        rows = data.get("rows", []) if data else []
        total = data.get("total", 0) if data else 0
        pagecount = (total + self.limit - 1) // self.limit if total > 0 else 1
        return {
            "page": page,
            "pagecount": pagecount,
            "list": self._build_list(rows)
        }
    
    def detailContent(self, ids):
        result_list = []
        for vid in ids:
            data = self._fetch_video(vid)
            if data:
                name = data.get("name", "")
                pic = data.get("img", "")
                video_list = data.get("list", [])
                play_urls = []
                for v in video_list:
                    if v.get("needPay", 1) == 0 and v.get("videourl"):
                        play_urls.append(f"{v.get('name', '')}${v.get('videourl', '')}")
                result_list.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_play_from": "直链",
                    "vod_play_url": "#".join(play_urls) if play_urls else ""
                })
        return {"list": result_list}
    
    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        data = self._fetch_search(key, page)
        rows = data.get("rows", []) if data else []
        total = data.get("total", 0) if data else 0
        pagecount = (total + self.limit - 1) // self.limit if total > 0 else 1
        return {
            "list": self._build_list(rows),
            "page": page,
            "pagecount": pagecount
        }
    
    def playerContent(self, flag, id, vipFlags):
        return {
            "parse": 0,
            "url": id,
            "header": self.headers
        }
    
    def liveContent(self, url):
        return "Error"
    
    def proxy(self, params):
        return [404, "text/plain", None]
    
    def action(self, action):
        return {"msg": "Action not implemented"}
    
    def manualVideoCheck(self):
        return False
    
    def isVideoFormat(self, url):
        return url.lower().endswith((".mp4", ".m3u8", ".flv"))
    
    def destroy(self):
        pass