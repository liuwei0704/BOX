import sys
import re
import requests
import json
from bs4 import BeautifulSoup

class Spider:
    def __init__(self):
        self.siteUrl = "https://baoziduanju.com"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://baoziduanju.com/"
        }

    def getName(self): return "包子短剧"
    def getDependence(self): return []
    def init(self, extend): pass

    def homeContent(self, filter):
        classes = [{"type_id": "系统觉醒", "type_name": "系统觉醒"},{"type_id": "穿越重生", "type_name": "穿越重生"},{"type_id": "都市逆袭", "type_name": "都市逆袭"},{"type_id": "古风权谋", "type_name": "古风权谋"},{"type_id": "总裁娇妻", "type_name": "总裁娇妻"},{"type_id": "玄幻仙侠", "type_name": "玄幻仙侠"}]
        return {"class": classes, "list": self.get_list(f"{self.siteUrl}/index.html")}

    def homeVideoContent(self):
        return {"list": self.get_list(f"{self.siteUrl}/index.html")}

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.siteUrl}/category/{tid}.html" if str(pg) == "1" else f"{self.siteUrl}/page/{pg}.html"
        return {"page": pg, "pagecount": 99, "list": self.get_list(url)}

    def detailContent(self, ids):
        id_path = ids[0]
        res = requests.get(self.siteUrl + id_path, headers=self.header, timeout=10)
        res.encoding = 'utf-8'
        html = res.text
        
        # 1. 提取基础信息
        title = "短剧"
        t_match = re.search(r'<h1.*?>(.*?)</h1>', html)
        if t_match: title = t_match.group(1).split('-')[0].strip()
        
        # 2. 强力抓取播放列表 (全能扫描模式)
        play_list = []
        # A. 搜索 JS 变量 (支持更多变体)
        var_patterns = [r"vodPlayUrl\s*=\s*['\"](.*?)['\"]", r"playlist\s*:\s*\[(.*?)\]", r"urls\s*:\s*\[(.*?)\]"]
        for p in var_patterns:
            m = re.search(p, html, re.S)
            if m and len(m.group(1)) > 20:
                content = m.group(1).replace('\/', '/')
                if '#' in content: # 格式: 1$url#2$url
                    play_list = content.split('#')
                    break
        
        # B. 如果 A 失败，扫描所有类似 /watch/ 或 /video/ 的集数链接
        if not play_list:
            cid_match = re.search(r'/video/(\d+)', id_path)
            if cid_match:
                cid = cid_match.group(1)
                # 寻找所有 _数字.html
                eps = re.findall(rf'/{cid}_(\d+)\.html', html)
                if not eps: # 尝试不带前缀的匹配
                    eps = re.findall(r'_(\d+)\.html', html)
                
                if eps:
                    unique_eps = sorted(list(set(map(int, eps))))
                    for ep in unique_eps:
                        play_list.append(f"第{ep}集${self.siteUrl}/video/{cid}_{ep}.html")

        # C. 兜底方案：如果还是只有一集，检查是否有“选集”按钮区域
        if not play_list:
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.select('.episode-list a, .playlist a, .anthology-list a'):
                play_list.append(f"{a.get_text().strip()}${self.siteUrl}{a.get('href')}")

        vod = {
            "vod_id": id_path,
            "vod_name": self.clean_name(title),
            "vod_pic": "", 
            "vod_remarks": f"更新至{len(play_list)}集" if len(play_list) > 1 else "全一集",
            "vod_content": "精彩短剧，尽在包子。",
            "vod_play_from": "包子专线",
            "vod_play_url": "#".join(play_list) if play_list else f"正片${self.siteUrl}{id_path}"
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        res = requests.get(id, headers=self.header, timeout=10)
        html = res.text
        # 寻找 hls.js 可能会加载的 m3u8 地址
        m = re.search(r'url:[\'"](.*?\.m3u8.*?)[\'"]', html)
        if not m: m = re.search(r'video_url\s*=\s*[\'"](.*?)[\'"]', html)
        if not m: m = re.search(r'source\s*:\s*[\'"](.*?\.m3u8.*?)[\'"]', html)
        
        url = m.group(1).replace("\/", "/") if m else id
        return {"parse": 0, "url": url, "header": self.header}

    def get_list(self, url):
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = []
            for a in soup.select("div.video-grid a"):
                img = a.find("img")
                if img:
                    videos.append({
                        "vod_id": a.get("href"),
                        "vod_name": self.clean_name(img.get("alt", "")),
                        "vod_pic": img.get("src"),
                        "vod_remarks": a.find("span").get_text() if a.find("span") else ""
                    })
            return videos
        except: return []

    def clean_name(self, name):
        return re.sub(r'\(.*?\)|（.*?）|【.*?】|\[.*?\]|全集|高清', '', name).strip()