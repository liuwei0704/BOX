import sys
import requests
import re
import json
import html

class Spider():
    def getName(self):
        return "必康影視"

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
        # 這裡將「短劇」作為一個大類，利用篩選器切換 50, 51 等子 ID
        result["class"] = [
            {"type_name": "短劇", "type_id": "20"},
            {"type_name": "電影", "type_id": "1"},
            {"type_name": "電視劇", "type_id": "2"},
            {"type_name": "綜藝", "type_id": "3"},
            {"type_name": "動漫", "type_id": "4"}
        ]
        
        # 篩選器配置
        result["filters"] = {
            "20": [
                {
                    "key": "tid",
                    "name": "分類",
                    "value": [
                        {"n": "全部", "v": "20"},
                        {"n": "穿越短劇", "v": "50"},
                        {"n": "愛情短劇", "v": "51"},
                        {"n": "懸疑短劇", "v": "52"},
                        {"n": "仙俠短劇", "v": "53"},
                        {"n": "都市短劇", "v": "54"},
                        {"n": "短劇列表", "v": "55"}
                    ]
                },
                {
                    "key": "by",
                    "name": "排序",
                    "value": [
                        {"n": "按更新", "v": "time"},
                        {"n": "按熱度", "v": "hits"},
                        {"n": "按評分", "v": "score"}
                    ]
                },
                {
                    "key": "letter",
                    "name": "字母",
                    "value": [{"n": "全部", "v": ""}] + [{"n": chr(i), "v": chr(i)} for i in range(65, 91)] + [{"n": "0-9", "v": "0-9"}]
                }
            ]
        }
        
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
        # 強力匹配：抓取圖片、標題和狀態角標
        items = re.findall(r'href="(/bicon/\d+\.html)".*?title="(.*?)".*?data-original="(.*?)".*?>(.*?)</a>', raw_html, re.S)
        for sid, name, pic, extra in items:
            if pic.startswith("//"): pic = "https:" + pic
            elif pic.startswith("/"): pic = self.host + pic
            
            # 提取 <span class="state">更新全集</span>
            remark = self.regStr(extra, r'<span.*?>(.*?)</span>')
            
            videos.append({
                "vod_id": sid,
                "vod_name": html.unescape(name),
                "vod_pic": pic,
                "vod_remarks": remark
            })
        return videos

    def categoryContent(self, tid, pg, filter, extend):
        self.check_init()
        
        # 關鍵修改：如果篩選器選了子分類，則覆蓋原始 tid
        curr_tid = extend.get("tid", tid)
        by = extend.get("by", "time")
        letter = extend.get("letter", "")
        
        # 構建 MacCMS vodshow URL
        # 結構: {tid}--{by}---{letter}---{pg}---.html
        url = f"{self.host}/vodshow/{curr_tid}--{by}---{letter}---{pg}---.html"
        
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            video_list = self.parse_list(res.text)
            return {"list": video_list, "page": pg, "pagecount": 999}
        except:
            return {"list": [], "page": pg, "pagecount": 0}

    def detailContent(self, ids):
        self.check_init()
        tid = ids[0]
        url = self.host + tid if tid.startswith('/') else f"{self.host}/{tid}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            raw_html = res.text

            # 物理清洗標籤
            clean_html = re.sub(r'<(tcenter|fss|tyyt|ssmall|time|areass|sdu|is|font|dfn|sadw|acronym|ecode)[^>]*?>', '', raw_html)
            clean_html = re.sub(r'</(tcenter|fss|tyyt|ssmall|time|areass|sdu|is|font|dfn|sadw|acronym|ecode)>', '', clean_html)

            raw_remark = self.regStr(clean_html, r'資源：</label><span>(.*?)</span>')
            remark = raw_remark.replace("資源：", "").strip()

            vod = {
                "vod_id": tid,
                "vod_name": self.regStr(clean_html, r'<h1.*?>(.*?)</h1>'),
                "vod_pic": self.regStr(clean_html, r'id="movie_thumb".*?data-original="(.*?)"'),
                "type_name": self.regStr(clean_html, r'類型：</label><span>(.*?)</span>'),
                "vod_year": self.regStr(clean_html, r'年份：</label><span>(.*?)</span>'),
                "vod_remarks": remark,
                "vod_actor": self.regStr(clean_html, r'主演：</label><span>(.*?)</span>'),
                "vod_director": self.regStr(clean_html, r'導演：</label><span>(.*?)</span>'),
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

            vod["vod_play_from"] = "$$$".join(froms[:len(play_urls)])
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
                return {"parse": 0 if ('.m3u8' in config['url'] or '.mp4' in config['url']) else 1, "url": config['url'], "header": self.header}
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