import requests
import re
import json

class Spider():
    def getName(self):
        return "KT剧集"

    def init(self, extend=""):
        self.siteUrl = "https://www.bradfordstone.com"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.siteUrl
        }

    def getDependence(self): 
        return []

    def homeVideoContent(self):
        try:
            res = requests.get(self.siteUrl, headers=self.header, timeout=10)
            res.encoding = "utf-8"
            html = res.text
            if "今日热播" in html:
                html = html.split("今日热播")[1].split("最新电影")[0]
            return {"list": self.parseList(html)}
        except:
            return {"list": []}

    def homeContent(self, filter):
        classes = [
            {"type_name": "短剧", "type_id": "3"},
            {"type_name": "电影", "type_id": "1"},
            {"type_name": "电视剧", "type_id": "2"},
            {"type_name": "动漫", "type_id": "4"},
            {"type_name": "综艺", "type_id": "5"}
        ]
        return {"class": classes}

    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'siteUrl'): self.init()
        url = f"{self.siteUrl}/webtv/{tid}/page/{pg}.html" if str(pg) != "1" else f"{self.siteUrl}/webtv/{tid}.html"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = "utf-8"
            return {"list": self.parseList(res.text), "page": pg, "pagecount": 99}
        except:
            return {"list": [], "page": pg, "pagecount": 0}

    def parseList(self, html):
        videos = []
        # ✅ 增强正则：同时匹配 href, id, title, pic 和 角标(vtitle)
        # 考虑到源码结构，先匹配每个 li 块再细分提取
        items = re.findall(r'<li class="col-xs-4.*?">.*?</li>', html, re.S)
        
        for item in items:
            try:
                # 提取链接、ID和标题
                m = re.search(r'href="(/movie/(\d+)\.html)" title="(.*?)"', item)
                # 提取图片
                p = re.search(r'data-original="(.*?)"', item)
                # ✅ 提取角标（如：全集、更新至12集）
                r = re.search(r'<span class="vtitle[^>]*>(.*?)</span>', item)
                
                if m and p:
                    href, v_id, name = m.groups()
                    pic = p.group(1)
                    remarks = r.group(1).strip() if r else ""
                    
                    # 清洗标题
                    clean_name = re.sub(r'<.*?>', '', name).strip()
                    
                    # 补全图片URL
                    if pic.startswith("//"): pic = "https:" + pic
                    elif pic.startswith("/"): pic = self.siteUrl + pic
                        
                    videos.append({
                        "vod_id": href,
                        "vod_name": clean_name,
                        "vod_pic": pic,
                        "vod_remarks": remarks # ✅ 加入角标显示
                    })
            except:
                continue
        return videos

    def detailContent(self, ids):
        if not hasattr(self, 'siteUrl'): self.init()
        v_id = ids[0]
        try:
            res = requests.get(f"{self.siteUrl}{v_id}", headers=self.header, timeout=10)
            res.encoding = "utf-8"
            html = res.text
            
            # 名称去乱码
            raw_name = re.search(r'<h1>(.*?)</h1>', html).group(1)
            name = re.sub(r'<.*?>', '', raw_name).strip()
            
            pic = re.search(r'data-original="(.*?)"', html).group(1)
            if pic.startswith("/"): pic = self.siteUrl + pic

            # 匹配播放列表
            play_matches = re.findall(r'href="(/video/\d+/\d+/\d+\.html)"[^>]*>(.*?)</a>', html)
            url_dict = {}
            for p_href, p_name in play_matches:
                p_name_clean = re.sub(r'<.*?>', '', p_name).strip()
                # 屏蔽干扰项
                if any(x in p_name_clean for x in ["立即播放", "下载", "APP"]): 
                    continue
                
                line_id = p_href.split('/')[3]
                if line_id not in url_dict: url_dict[line_id] = []
                
                display_name = p_name_clean.replace('完结', '').strip()
                url_dict[line_id].append(f"{display_name}${p_href}")

            sorted_lines = sorted(url_dict.items(), key=lambda x: len(x[1]), reverse=True)
            final_from, final_url = [], []
            for i, (l_id, urls) in enumerate(sorted_lines[:2]):
                final_from.append(f"线路{i+1}")
                final_url.append("#".join(urls))

            return {"list": [{
                "vod_id": v_id, 
                "vod_name": name, 
                "vod_pic": pic,
                "vod_play_from": "$$$".join(final_from),
                "vod_play_url": "$$$".join(final_url)
            }]}
        except:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        try:
            res = requests.get(f"{self.siteUrl}{id}", headers=self.header, timeout=10)
            player_json = re.search(r'player_aaaa\s*=\s*(\{.*?\})', res.text)
            if player_json:
                data = json.loads(player_json.group(1))
                return {"parse": 0, "url": data['url'].replace('\/', '/'), "header": ""}
            return {"parse": 1, "url": f"{self.siteUrl}{id}"}
        except:
            return {"parse": 1, "url": f"{self.siteUrl}{id}"}

    def searchContent(self, key, quick,pg="1"):
        if not hasattr(self, 'siteUrl'): self.init()
        url = f"{self.siteUrl}/search.html?wd={key}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = "utf-8"
            return {"list": self.parseList(res.text)}
        except:
            return {"list": []}