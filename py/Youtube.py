# coding=utf-8
import sys
import re
import requests
import urllib.parse
import html

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "YouTube_Final"

    def init(self, extend=""):
        self.host = "https://www.youtube.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }

    def checkInit(self):
        if not hasattr(self, 'host'):
            self.init()

    def homeContent(self, filter):
        self.checkInit()
        return {
            "class": [
                {"type_id": "trending", "type_name": "🔥 实时热门"},
                {"type_id": "live", "type_name": "📺 直播中"},
                {"type_id": "@阿星推文", "type_name": "🪅 阿星推文"},
                {"type_id": "@DawnAnimeClub", "type_name": "👆七號動漫館"},
                {"type_id": "@JayChou", "type_name": "🎵 周杰倫"},
                {"type_id": "@CtiTv", "type_name": "📡 中天新聞"}
            ],
            "list": []
        }

    def categoryContent(self, tid, pg, filter, extend):
        self.checkInit()
        pg = int(pg)
        
        # 热门分类的分页：通过不同的排序过滤来实现物理翻页
        if tid == "trending":
            sps = ["EgIIAQ%3D%3D", "EgQIAhAB", "EgQIAxAB", "EgQIBBAB"]
            idx = (pg - 1) % len(sps)
            # 热门直接搜索 'trending' 并应用排序
            url = f"{self.host}/results?search_query=trending&sp={sps[idx]}"
            return self.parse_data(url)
            
        search_key = f"from:{tid}" if (tid.startswith('@') or tid.startswith('UC')) else tid
        return self.searchContent(search_key, False, pg)

    def parse_data(self, url, limit=30):
        result = {"list": []}
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            text = res.text
            vids = re.findall(r'"videoId":"([^"]{11})"', text)
            seen = set()
            for vid in vids:
                if vid in seen: continue
                seen.add(vid)
                pos = text.find(vid)
                chunk = text[pos:pos+1500]
                
                title = ""
                t_m = re.search(r'"title":\{"runs":\[\{"text":"([^"]+)"\}', chunk)
                if t_m: title = t_m.group(1)
                else:
                    t_m = re.search(r'"title":\{"simpleText":"([^"]+)"\}', chunk)
                    if t_m: title = t_m.group(1)
                
                if not title: continue
                title = html.unescape(title)
                
                result["list"].append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                    "vod_remarks": "🔴 直播" if "LIVE" in chunk else "1080P"
                })
                if len(result["list"]) >= limit: break
        except: pass
        return result

    def detailContent(self, ids):
        vid = ids[0]
        return {"list": [{
            "vod_id": vid, "vod_name": "YouTube 视频",
            "vod_pic": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "vod_play_from": "YouTube", "vod_play_url": f"播放${vid}"
        }]}

    def searchContent(self, key, quick, pg=1):
        self.checkInit()
        pg = int(pg)
        # 翻页核心逻辑：通过 SP 令牌切换实现
        sp_list = ["EgIQAQ%3D%3D", "CAI%3D", "EgIIAQ%3D%3D", "EgIQAw%3D%3D"]
        sp = sp_list[(pg-1) % len(sp_list)]
        
        url = f"{self.host}/results?search_query={urllib.parse.quote(key)}&sp={sp}"
        return self.parse_data(url)

    def playerContent(self, flag, id, vipFlags):
        # 恢复为你测试正常的嗅探模式
        return {"parse": 1, "playUrl": "", "url": f"https://www.youtube.com/watch?v={id}"}

    def getDependence(self):
        return ["requests"]
        