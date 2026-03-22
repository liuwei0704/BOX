import sys
import requests
from bs4 import BeautifulSoup
import re
import json

class Spider():
    def getName(self): return "Cloud影视(TVFans)"
    def getDependence(self): return []
    def init(self, extend=""):
        self.host = "https://www.tvfans.top"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": self.host
        }
        # 预编译正则：1. 匹配豆瓣评分 2. 匹配更新状态和各种括号干扰
        self.db_re = re.compile(r'.*?豆瓣:[\d\.]+分')
        self.cleanup_re = re.compile(r'(已完结|全\d+集|更新至\d+期|更新至\d+集|更新至\d+|\(|\[|\)|\]|【|】|/|;|:|\|)+')

    def check_init(self):
        if not hasattr(self, 'host'): self.init()

    def homeContent(self, filter):
        self.check_init()
        classes = [{"type_name": "电影", "type_id": "1"}, {"type_name": "剧集", "type_id": "2"}, {"type_name": "综艺", "type_id": "3"}, {"type_name": "动漫", "type_id": "4"}, {"type_name": "短剧", "type_id": "30"}]
        return {"class": classes}

    def homeVideoContent(self):
        self.check_init()
        try:
            res = requests.get(self.host, headers=self.header, timeout=10)
            res.encoding = "utf-8"
            return {"list": self.parse_vod_list(res.text, deduplicate=True)}
        except: return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        self.check_init()
        url = f"{self.host}/vod/show/{tid}--------{pg}---/"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = "utf-8"
            return {"page": str(pg), "pagecount": 99, "list": self.parse_vod_list(res.text)}
        except: return {"page": str(pg), "pagecount": 0, "list": []}

    def parse_vod_list(self, html, deduplicate=False):
        soup = BeautifulSoup(html, 'html.parser')
        videos = []
        seen_names = set() 
        
        # 针对 TVFans 的结构，先找所有带详情页链接的 a
        items = soup.find_all('a', href=re.compile(r'/vod/detail/'))
        
        for a in items:
            sid = a.get('href', '')
            if not sid: continue
            
            # 找到父级容器以便提取备注和图片
            parent = a.find_parent(class_=re.compile(r'module-item|item|poster|card')) or a
            
            # --- 核心清洗逻辑 ---
            # 1. 优先获取最可能的名称节点
            name_node = parent.select_one(".module-item-title, .video-name, h3, .module-poster-item-title, .module-card-item-title")
            raw_name = name_node.get_text().strip() if name_node else (a.get('title') or a.get_text().strip())
            
            # 2. 去除“豆瓣:X.X分”及其之前的所有乱七八糟的干扰
            # 例如：“更新至20251125豆瓣:2.0分花儿与少年” -> “花儿与少年”
            name = self.db_re.sub("", raw_name).strip()
            
            # 3. 暴力清理剩下的修饰词（如“已完结”、“更新至”等）
            name = self.cleanup_re.sub("", name).strip()
            
            # 4. 长度保护与废词过滤
            if not name or len(name) < 2 or len(name) > 30 or name in ["详情", "播放", "更多", "搜索结果"]: 
                continue

            # --- 去重逻辑 ---
            if deduplicate and name in seen_names: continue

            # --- 备注提取 ---
            remarks = ""
            rem_node = parent.select_one(".module-item-note, .module-poster-item-note, .video-serial, .module-item-caption, .module-item-text")
            if rem_node:
                remarks = rem_node.get_text().strip()
            elif "更新" in raw_name:
                # 从原始名字里提取更新信息作为备注
                r_match = re.search(r'(更新至\d+(集|期)?)', raw_name)
                if r_match: remarks = r_match.group(1)

            # --- 图片提取 ---
            img_node = parent.find('img')
            img = ""
            if img_node:
                img = img_node.get('data-original') or img_node.get('src') or img_node.get('data-src') or ""
            
            # 过滤没有图片的无效占位符（比如分类导航链接）
            if not img and not deduplicate: continue
            
            if img.startswith("//"): img = "https:" + img
            elif img.startswith("/") and not img.startswith("//"): img = self.host + img
            
            videos.append({
                "vod_id": sid,
                "vod_name": name,
                "vod_pic": img,
                "vod_remarks": remarks
            })
            seen_names.add(name)
            
        return videos

    def detailContent(self, ids):
        self.check_init()
        vod_id = ids[0]
        url = self.host + vod_id if vod_id.startswith("/") else f"{self.host}/{vod_id}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, 'html.parser')
            name = soup.find('h1').get_text().strip() if soup.find('h1') else "未知"
            pic_node = soup.select_one(".module-item-pic img, .video-info-main img, .module-info-poster img")
            pic = pic_node.get('data-original') or pic_node.get('src') or "" if pic_node else ""
            if pic.startswith("//"): pic = "https:" + pic
            elif pic.startswith("/") and not pic.startswith("//"): pic = self.host + pic

            play_from, play_url = [], []
            tabs = soup.select(".module-tab-item, .tab-item, .play_source_tab a")
            lists = soup.select(".module-play-list-content, .module-play-list, .play_list_box, .playlist_full")
            
            for i in range(min(len(tabs), len(lists))):
                f_name = tabs[i].get_text().replace("排序", "").strip()
                links = lists[i].find_all('a')
                if links:
                    p_urls = [f"{l.get_text().strip()}${l['href']}" for l in links]
                    play_from.append(f_name)
                    play_url.append("#".join(p_urls))
            
            for i, f_name in enumerate(play_from):
                if "OK" in f_name.upper():
                    play_from.insert(0, play_from.pop(i))
                    play_url.insert(0, play_url.pop(i))
                    break

            return {"list": [{"vod_id": vod_id, "vod_name": name, "vod_pic": pic, "vod_play_from": "$$$".join(play_from), "vod_play_url": "$$$".join(play_url)}]}
        except: return {"list": []}

    def searchContent(self, key, quick, pg=1):
        self.check_init()
        url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{key}.html"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = "utf-8"
            return {"list": self.parse_vod_list(res.text)}
        except: return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        self.check_init()
        url = self.host + id if id.startswith("/") else id
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            match = re.search(r'player_aaaa=(.*?)</script>', res.text)
            if match:
                config = json.loads(match.group(1))
                return {"parse": 0, "url": config.get('url', ''), "header": self.header}
        except: pass
        return {"parse": 1, "url": url, "header": self.header}

if __name__ == '__main__':
    s = Spider(); s.init()
    print(json.dumps(s.homeVideoContent(), ensure_ascii=False))