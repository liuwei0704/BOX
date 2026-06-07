#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests, re, json
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""):
        self.name = "998号影视"
        self.host = "www.sflm998.top"
        self.headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.sflm998.top"}

    def homeContent(self, filter):
        classes = [
            {"type_id": "1", "type_name": "999号"}, {"type_id": "20", "type_name": "裸体学生"},
            {"type_id": "6", "type_name": "国产乱伦"}, {"type_id": "7", "type_name": "黑料吃瓜"},
            {"type_id": "8", "type_name": "国产精品"}, {"type_id": "9", "type_name": "人兽杂交"},
            {"type_id": "10", "type_name": "吃瓜乱伦"}, {"type_id": "11", "type_name": "国产萝莉"},
            {"type_id": "12", "type_name": "新瓜猛料"}, {"type_id": "2", "type_name": "998号"},
            {"type_id": "21", "type_name": "动漫禁漫"}, {"type_id": "22", "type_name": "学生合集"},
            {"type_id": "23", "type_name": "探花约炮"}, {"type_id": "24", "type_name": "欧美大屌"},
            {"type_id": "13", "type_name": "日本有码"}, {"type_id": "14", "type_name": "主播网红"},
            {"type_id": "15", "type_name": "中文字幕"}, {"type_id": "16", "type_name": "国产传媒"},
            {"type_id": "3", "type_name": "997号"}, {"type_id": "25", "type_name": "日本无码"},
            {"type_id": "26", "type_name": "欧美无码"}, {"type_id": "27", "type_name": "强奸乱伦"},
            {"type_id": "28", "type_name": "制服诱惑"}, {"type_id": "29", "type_name": "明星换脸"},
            {"type_id": "30", "type_name": "抖阴视频"}, {"type_id": "31", "type_name": "网曝黑料"},
            {"type_id": "32", "type_name": "女优明星"}, {"type_id": "4", "type_name": "996号"},
            {"type_id": "33", "type_name": "剧情解说"}, {"type_id": "34", "type_name": "性奴调教"},
            {"type_id": "35", "type_name": "极品媚黑"}, {"type_id": "36", "type_name": "女同性恋"},
            {"type_id": "37", "type_name": "网红头条"}, {"type_id": "38", "type_name": "真实自拍"},
            {"type_id": "39", "type_name": "明星黑料"}, {"type_id": "40", "type_name": "双飞姐妹"}
        ]
        recommend = []
        try:
            url = f"https://{self.host}/index.php/vod/type/id/33/page/1.html"
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = "utf-8"
            items = re.findall(r'<a href="/index.php/vod/detail/id/(\d+)\.html"[^>]*>.*?<img src="([^"]+)"[^>]*>.*?<p class="vod-name">([^<]+)</p>', res.text, re.DOTALL)
            for vid, pic, title in items[:12]:
                recommend.append({"vod_id": vid, "vod_name": title, "vod_pic": pic})
        except:
            pass
        return {"class": classes, "filters": {}, "list": recommend}

    def categoryContent(self, tid, pg, filter, extend):
        url = f"https://{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
        res = requests.get(url, headers=self.headers, timeout=10)
        res.encoding = "utf-8"
        
        items = re.findall(r'<a href="/index.php/vod/detail/id/(\d+)\.html"[^>]*>.*?<img src="([^"]+)"[^>]*>.*?<p class="vod-name">([^<]+)</p>', res.text, re.DOTALL)
        videos = []
        seen = set()
        for vid, pic, title in items:
            if vid in seen:
                continue
            seen.add(vid)
            videos.append({"vod_id": vid, "vod_name": title, "vod_pic": pic})
        
        # 提取分页：找所有页码数字的最大值
        page_nums = re.findall(r'<a[^>]+href="/index.php/vod/type/id/' + tid + r'/page/(\d+)\.html"[^>]*>(\d+)</a>', res.text)
        max_page = 1
        for _, page_num in page_nums:
            if page_num.isdigit():
                max_page = max(max_page, int(page_num))
        # 也检查当前激活页
        current_match = re.search(r'<text[^>]*class="[^"]*page-actvie[^"]*"[^>]*>(\d+)</text>', res.text)
        if current_match:
            max_page = max(max_page, int(current_match.group(1)))
        
        return {"list": videos, "page": int(pg), "pagecount": max_page, "limit": 30, "total": len(videos)}

    def detailContent(self, ids):
        vid = ids[0] if isinstance(ids, list) else ids.split(",")[0]
        url = f"https://{self.host}/index.php/vod/detail/id/{vid}.html"
        res = requests.get(url, headers=self.headers, timeout=10)
        res.encoding = "utf-8"
        title_match = re.search(r'<title>(.+?)</title>', res.text)
        vod_name = title_match.group(1).replace("在线播放", "").replace("- 高清资源", "").strip() if title_match else "未知"
        pic_match = re.search(r'<img[^>]+class="detail-vod-pic"[^>]+src="([^"]+)"', res.text)
        vod_pic = pic_match.group(1) if pic_match else ""
        play_match = re.search(r'<a[^>]+href="(/index.php/vod/play/id/[^"]+)"[^>]*>在线播放</a>', res.text)
        play_url = f"https://{self.host}{play_match.group(1)}" if play_match else ""
        return {"list": [{"vod_id": vid, "vod_name": vod_name, "vod_pic": vod_pic, "vod_play_from": "默认源", "vod_play_url": f"在线播放${play_url}" if play_url else ""}]}

    def searchContent(self, key, quick, pg=1):
        url = f"https://{self.host}/index.php/vod/search.html?wd={key}&page={pg}"
        res = requests.get(url, headers=self.headers, timeout=10)
        res.encoding = "utf-8"
        items = re.findall(r'<a href="/index.php/vod/detail/id/(\d+)\.html"[^>]*>.*?<img src="([^"]+)"[^>]*>.*?<p class="vod-name">([^<]+)</p>', res.text, re.DOTALL)
        videos = []
        seen = set()
        for vid, pic, title in items[:50]:
            if vid in seen:
                continue
            seen.add(vid)
            videos.append({"vod_id": vid, "vod_name": title, "vod_pic": pic})
        return {"list": videos, "page": int(pg), "pagecount": 1, "limit": 30, "total": len(videos)}

    def playerContent(self, flag, id, vipFlags):
        if ".m3u8" in id:
            return {"parse": 1, "playUrl": "", "url": id, "header": json.dumps({"Referer": "https://www.sflm998.top"})}
        url = id if id.startswith("http") else f"https://{self.host}{id}"
        res = requests.get(url, headers=self.headers, timeout=10)
        res.encoding = "utf-8"
        match = re.search(r'"url":"([^"]+\.m3u8)"', res.text)
        play_url = match.group(1).replace("\\/", "/") if match else ""
        return {"parse": 1, "playUrl": "", "url": play_url, "header": json.dumps({"Referer": "https://www.sflm998.top"})}
