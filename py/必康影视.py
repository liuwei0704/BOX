import sys
import requests
import re
import json
import html

class Spider():
    def getName(self):
        return "必康影视"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.host = "https://www.xabicon.com"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host
        }

    def check_init(self):
        if not hasattr(self, 'host'):
            self.init()

    def homeContent(self, filter):
        self.check_init()
        result = {}
        cateManual = {"短劇": "20","电影": "1", "电视剧": "2", "综艺": "3", "动漫": "4"}
        result["class"] = [{"type_name": k, "type_id": v} for k, v in cateManual.items()]
        try:
            res = requests.get(self.host, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            result["list"] = self.parse_list(res.text)
        except:
            result["list"] = []
        return result

    def homeVideoContent(self):
        return self.homeContent(False)

    def parse_list(self, raw_html):
        videos = []
        # 修正正则，同时抓取图片下方的备注标签（如有）
        items = re.findall(r'<a href="(/bicon/\d+\.html)".*?title="(.*?)".*?data-original="(.*?)".*?>(.*?)</a>', raw_html, re.S)
        for sid, name, pic, extra in items:
            if pic.startswith("//"): pic = "https:" + pic
            elif pic.startswith("/"): pic = self.host + pic
            
            # --- 角标处理逻辑 ---
            # 提取 <span> 里的内容作为角标，例如 "高清"、"完结"
            remark = self.regStr(extra, r'<span.*?>(.*?)</span>')
            
            videos.append({
                "vod_id": sid,
                "vod_name": html.unescape(name),
                "vod_pic": pic,
                "vod_remarks": remark # 这里的备注会显示在角标位置
            })
        return videos

    def categoryContent(self, tid, pg, filter, extend):
        self.check_init()
        url = f"{self.host}/vodtype/{tid}-{pg}.html"
        res = requests.get(url, headers=self.header, timeout=10)
        res.encoding = 'utf-8'
        return {"list": self.parse_list(res.text), "page": pg, "pagecount": 999}

    def detailContent(self, ids):
        self.check_init()
        tid = ids[0]
        url = self.host + tid if tid.startswith('/') else f"{self.host}/{tid}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            raw_html = res.text
            clean_html = re.sub(r'<(tcenter|fss|tyyt|ssmall|time|areass|sdu|is|font|dfn|sadw|acronym|ecode)[^>]*?>', '', raw_html)
            clean_html = re.sub(r'</(tcenter|fss|tyyt|ssmall|time|areass|sdu|is|font|dfn|sadw|acronym|ecode)>', '', clean_html)

            # 提取备注并清洗，去掉“资源：”前缀，使其在详情页角标更美观
            raw_remark = self.regStr(clean_html, r'资源：</label><span>(.*?)</span>')
            remark = raw_remark.replace("资源：", "").strip()

            vod = {
                "vod_id": tid,
                "vod_name": self.regStr(clean_html, r'<h1.*?>(.*?)</h1>'),
                "vod_pic": self.regStr(clean_html, r'id="movie_thumb".*?data-original="(.*?)"'),
                "type_name": self.regStr(clean_html, r'类型：</label><span>(.*?)</span>'),
                "vod_year": self.regStr(clean_html, r'年份：</label><span>(.*?)</span>'),
                "vod_remarks": remark,
                "vod_actor": self.regStr(clean_html, r'主演：</label><span>(.*?)</span>'),
                "vod_director": self.regStr(clean_html, r'导演：</label><span>(.*?)</span>'),
                "vod_content": self.regStr(clean_html, r'style="text-indent: 28px;margin-top: 10px;">(.*?)</div>')
            }

            froms = re.findall(r'class="tab-nav">(.*?)</a>', clean_html)
            play_urls = []
            blocks = clean_html.split('episodes-list clearfix">')[1:]
            for block in blocks:
                block = block.split('</ul>')[0]
                links = re.findall(r'href="(/bkplay/.*?.html)".*?>(.*?)</a>', block, re.S)
                p_list = [f"{html.unescape(re.sub(r'<.*?>','',l[1])).strip()}${l[0]}" for l in links]
                if p_list: play_urls.append("#".join(p_list))

            if len(froms) < len(play_urls): froms = [f"线路{i+1}" for i in range(len(play_urls))]
            vod["vod_play_from"] = "$$$".join(froms)
            vod["vod_play_url"] = "$$$".join(play_urls)
            return {"list": [vod]}
        except:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        self.check_init()
        url = f"{self.host}/vodsearch/-------------.html?wd={key}&page={pg}"
        res = requests.get(url, headers=self.header, timeout=10)
        res.encoding = 'utf-8'
        return {"list": self.parse_list(res.text)}

    def playerContent(self, flag, id, vipFlags):
        self.check_init()
        url = self.host + id if id.startswith('/') else f"{self.host}/{id}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            player_data = re.search(r'var player_aaaa\s*=\s*(\{.*?\});', res.text)
            if player_data:
                config = json.loads(player_data.group(1))
                video_url = config.get('url', '')
                is_video = '.m3u8' in video_url or '.mp4' in video_url
                return {"parse": 0 if is_video else 1, "url": video_url, "header": self.header}
            return {"parse": 1, "url": url, "header": self.header}
        except:
            return {"parse": 1, "url": url, "header": self.header}

    def regStr(self, txt, mark):
        try:
            result = re.search(mark, txt, re.S)
            return html.unescape(result.group(1).strip()) if result else ""
        except:
            return ""

    def isVideoCanWin(self, url): return True
    def action(self, action): return ""
    def destroy(self): pass