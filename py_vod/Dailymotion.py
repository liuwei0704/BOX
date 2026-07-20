import requests
import re
from base.spider import Spider

class Spider(Spider):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.dailymotion.com"
    }

    def getName(self):
        return "Dailymotion (RSS-Full-Pagination)"

    def init(self, extend=""):
        super().init(extend)

    def homeContent(self, filter):
        cate_list = [
            {"type_name": "短劇: 一期一会 ", "type_id": "user/narumi4001"},
            {"type_name": "短劇: 七月短剧天下 ", "type_id": "user/dm_9ea4e8672798025a29d1d2812d"},
            {"type_name": "短劇: DailyCDrama ", "type_id": "user/DailyCDrama"},
            {"type_name": "短劇: zenostar ", "type_id": "user/zenostar"},
            {"type_name": "短劇: 短剧全合集", "type_id": "user/huinan520-349"},
            {"type_name": "短劇: sstt", "type_id": "user/stupiddm250"},
            {"type_name": "短劇: drkr004", "type_id": "user/drkr004"},
            {"type_name": "短劇: yi.tong292", "type_id": "user/yi.tong292"},
            {"type_name": "短劇: xin xin ", "type_id": "user/kchow125"},
            {"type_name": "短劇: HIGEGE ", "type_id": "user/HIGEGE"},
            {"type_name": "短劇: 愛看短劇 ", "type_id": "user/91dj"}
        ]
        return {"class": cate_list}

    def categoryContent(self, tid, pg, filter, extend):
        url = f"https://www.dailymotion.com/rss/{tid}?page={pg}"
        video_list = []
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res and res.ok:
                items = re.findall(r'<item>.*?</item>', res.text, re.S)
                for item in items:
                    v_id = re.search(r'video/([a-zA-Z0-9]+)', item)
                    v_title = re.search(r'<title>(.*?)</title>', item)
                    v_pic = re.search(r'media:thumbnail url="(.*?)"', item)
                    if v_id and v_title:
                        video_list.append({
                            "vod_id": v_id.group(1),
                            "vod_name": v_title.group(1).replace('<![CDATA[', '').replace(']]>', ''),
                            "vod_pic": v_pic.group(1) if v_pic else "",
                            "vod_remarks": f"P{pg} RSS更新"
                        })
        except:
            pass
        return {"list": video_list, "page": pg, "pagecount": 99}

    def detailContent(self, ids):
        id = ids[0]
        url = f"https://www.dailymotion.com/player/metadata/video/{id}"
        vod = {"vod_id": id, "vod_name": "Dailymotion 視頻", "vod_play_from": "Dailymotion", "vod_play_url": f"播放${id}"}
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res and res.ok:
                data = res.json()
                vod["vod_name"] = data.get("title") or vod["vod_name"]
                vod["vod_pic"] = data.get("poster_url") or data.get("thumbnail_720_url") or ""
                vod["vod_content"] = data.get("description") or "無簡介"
        except: pass
        return {"list": [vod]}

    def searchContent(self, key, quick, pg=1):
        # 搜索完美继承分页 pg 参数
        return self.categoryContent(f"search/{key}", pg, {}, {})

    def playerContent(self, flag, id, vipFlags):
        url = f"https://www.dailymotion.com/player/metadata/video/{id}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res and res.ok:
                m3u8 = res.json().get("qualities", {}).get("auto", [{}])[0].get("url")
                if m3u8:
                    return {"parse": 0, "playUrl": m3u8, "header": {"User-Agent": self.headers["User-Agent"]}}
        except: pass
        return {"parse": 0, "playUrl": "", "header": ""}

    def destroy(self) -> None:
        pass
