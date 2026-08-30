# coding: utf-8
# LOLD · 视频库 爬虫
# 站点: https://v.cuct.ccwu.cc/
# 架构: SPA + API 接口

import json
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://v.cuct.ccwu.cc"
        self.site_name = "LOLD视频库"
        self.classes = [
            {"type_id": "66", "type_name": "17岁"},
            {"type_id": "65", "type_name": "热播"},
            {"type_id": "88", "type_name": "萝莉"},
            {"type_id": "67", "type_name": "伦理"},
            {"type_id": "69", "type_name": "国产"},
            {"type_id": "77", "type_name": "禁漫"},
            {"type_id": "74", "type_name": "网黄"},
            {"type_id": "73", "type_name": "福利姬"},
            {"type_id": "81", "type_name": "P站"},
            {"type_id": "68", "type_name": "暗黑"},
            {"type_id": "72", "type_name": "AV"},
            {"type_id": "75", "type_name": "传媒"},
            {"type_id": "86", "type_name": "暗黑萝莉"},
            {"type_id": "83", "type_name": "暴力喋血"},
            {"type_id": "87", "type_name": "恐怖惊悚"},
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "application/json, text/plain, */*",
        }

    def getName(self):
        return "LOLD视频库"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐 - 默认加载'17岁'分类"""
        try:
            result = self.categoryContent("66", "1", False, None)
            return {"list": result.get("list", [])[:12]}
        except Exception as e:
            print("homeVideoContent error:", e)
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        pg = str(pg) if pg else "1"
        url = f"{self.host}/list?classId={tid}&page={pg}"
        resp = self.fetch(url, headers=self.headers, timeout=15)
        if not resp:
            return {"list": [], "page": int(pg), "pagecount": 1, "total": 0}
        
        try:
            data = json.loads(resp.text)
        except:
            return {"list": [], "page": int(pg), "pagecount": 1, "total": 0}
        
        items = data.get("items", [])
        parsed = []
        for item in items:
            if not item.get("id") or not item.get("name"):
                continue
            parsed.append({
                "vod_id": str(item["id"]),
                "vod_name": item["name"],
                "vod_pic": item.get("pic", ""),
                "vod_remarks": item.get("remarks", ""),
            })
        
        return {
            "list": parsed,
            "page": int(pg),
            "pagecount": 999,
            "limit": 20,
            "total": 9999,
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0])
        url = f"{self.host}/play?id={vid}"
        resp = self.fetch(url, headers=self.headers, timeout=15)
        if not resp:
            return {"list": []}
        
        try:
            data = json.loads(resp.text)
        except:
            return {"list": []}
        
        name = data.get("name", f"视频{vid}")
        urls = data.get("urls", [])
        
        if urls:
            play_url = urls[0]
            vod = {
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": "",
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_play_from": "播放",
                "vod_play_url": f"播放${play_url}",
            }
        else:
            vod = {
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": "",
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_play_from": "播放",
                "vod_play_url": "",
            }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        # 站点不支持搜索功能
        return {"list": [], "page": 1}

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 1, "url": ""}
        
        # 如果是 m3u8 直链，直接返回
        if id.startswith("http") and ".m3u8" in id.lower():
            return {
                "parse": 0,
                "url": id,
                "header": {
                    "User-Agent": self.headers["User-Agent"],
                    "Referer": self.host + "/",
                }
            }
        
        # 如果是详情页 URL，尝试提取 m3u8
        if id.startswith("http"):
            return {"parse": 1, "url": id, "header": self.headers}
        
        # 如果是 vod_id，尝试获取播放链接
        url = f"{self.host}/play?id={id}"
        resp = self.fetch(url, headers=self.headers, timeout=15)
        if resp:
            try:
                data = json.loads(resp.text)
                urls = data.get("urls", [])
                if urls and urls[0].startswith("http") and ".m3u8" in urls[0].lower():
                    return {
                        "parse": 0,
                        "url": urls[0],
                        "header": {
                            "User-Agent": self.headers["User-Agent"],
                            "Referer": self.host + "/",
                        }
                    }
            except:
                pass
        
        return {"parse": 1, "url": id, "header": self.headers}

    def localProxy(self, param):
        # 本站点无需 localProxy（播放链接为直接可访问的 m3u8）
        return [404, "text/plain", b"Not Found"]

    def destroy(self):
        pass