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

    def clean_text(self, text):
        if not text: return ""
        # 移除混淆標籤
        res = re.sub(r'<[^>]*?>', '', text)
        res = html.unescape(res)
        # 物理切除標題中殘留的符號
        res = res.replace('">', '').replace('"', '').replace('>', '').strip()
        return res

    def homeContent(self, filter):
        result = {"class": [
            {"type_name": "全部短劇", "type_id": "20"},
            {"type_name": "穿越短劇", "type_id": "50"},
            {"type_name": "愛情短劇", "type_id": "51"},
            {"type_name": "懸疑短劇", "type_id": "52"},
            {"type_name": "仙俠短劇", "type_id": "53"},
            {"type_name": "都市短劇", "type_id": "54"},
            {"type_name": "短劇列表", "type_id": "55"},
            {"type_name": "電影", "type_id": "1"},
            {"type_name": "電視劇", "type_id": "2"},
            {"type_name": "綜藝", "type_id": "3"},
            {"type_name": "動漫", "type_id": "4"}
        ]}
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
        items = re.findall(r'href="(/bicon/\d+\.html)"[^>]*?title="(.*?)"', raw_html, re.S)
        
        for sid, name in items:
            start_idx = raw_html.find(sid)
            search_area = raw_html[start_idx:start_idx+500]
            
            pic = ""
            img_match = re.search(r'data-original="(.*?)"', search_area)
            if img_match:
                pic = img_match.group(1)
                if pic.startswith("//"): pic = "https:" + pic
                elif pic.startswith("/"): pic = self.host + pic

            remarks = ""
            rem_match = re.search(r'<span[^>]*?>(.*?)</span>', search_area, re.S)
            if rem_match:
                remarks = self.clean_text(rem_match.group(1))

            videos.append({
                "vod_id": sid,
                "vod_name": self.clean_text(name),
                "vod_pic": pic,
                "vod_remarks": remarks
            })
            
        seen = set()
        unique_videos = []
        for v in videos:
            if v['vod_id'] not in seen:
                unique_videos.append(v)
                seen.add(v['vod_id'])
        return unique_videos

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg)
        
        # 根據你提供的 HTML，短劇子分類使用的是 vodshow 路由
        # 格式：tid-----------pg-.html (11個橫槓，pg在第11位)
        p = [""] * 12
        p[0] = str(tid)
        p[10] = str(pg)
        
        url = f"{self.host}/vodshow/{'-'.join(p)}.html"
        
        # 如果 vodshow 沒數據，則嘗試 vodtype 作為備選
        if pg == 1:
            # 優先嘗試不帶分頁的標準分類路徑
            test_url = f"{self.host}/vodtype/{tid}.html"
        else:
            test_url = f"{self.host}/vodtype/{tid}-{pg}.html"

        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            v_list = self.parse_list(res.text)
            
            # 如果 vodshow 返回空，切換到備選路徑
            if not v_list:
                res = requests.get(test_url, headers=self.header, timeout=10)
                res.encoding = 'utf-8'
                v_list = self.parse_list(res.text)

            # 動態分頁邏輯
            page_count = pg + 1 if len(v_list) >= 12 else pg
            
            return {
                "list": v_list,
                "page": pg,
                "pagecount": page_count,
                "limit": 20
            }
        except:
            return {"list": [], "page": pg, "pagecount": 0}

    def detailContent(self, ids):
        tid = ids[0]
        url = self.host + tid if tid.startswith('/') else f"{self.host}/{tid}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            raw_html = res.text
            
            name = re.search(r'<h1[^>]*?>(.*?)</h1>', raw_html)
            pic = re.search(r'data-original="([^"]*?)"', raw_html)
            
            vod = {
                "vod_id": tid,
                "vod_name": self.clean_text(name.group(1)) if name else "未知",
                "vod_pic": pic.group(1) if pic else "",
                "vod_remarks": self.clean_text(self.regStr(raw_html, r'資源：</label><span>(.*?)</span>')),
                "vod_content": "內容請查看播放列表"
            }
            
            froms = re.findall(r'class="tab-nav">(.*?)</a>', raw_html)
            play_urls = []
            blocks = raw_html.split('episodes-list clearfix">')[1:]
            for block in blocks:
                block = block.split('</ul>')[0]
                links = re.findall(r'href="(/bkplay/.*?.html)".*?>(.*?)</a>', block, re.S)
                p_list = [f"{self.clean_text(l[1])}${l[0]}" for l in links]
                if p_list: play_urls.append("#".join(p_list))

            vod["vod_play_from"] = "$$$".join(froms[:len(play_urls)])
            vod["vod_play_url"] = "$$$".join(play_urls)
            return {"list": [vod]}
        except:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        url = f"{self.host}/vodsearch/-------------.html?wd={key}&page={pg}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            return {"list": self.parse_list(res.text)}
        except:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        url = self.host + id if id.startswith('/') else f"{self.host}/{id}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            player_data = re.search(r'var player_aaaa\s*=\s*(\{.*?\});', res.text)
            if player_data:
                config = json.loads(player_data.group(1))
                return {"parse": 0 if ('.m3u8' in config['url'] or '.mp4' in config['url']) else 1, "url": config['url'], "header": self.header}
            return {"parse": 1, "url": url}
        except:
            return {"parse": 1, "url": url}

    def regStr(self, txt, mark):
        result = re.search(mark, txt, re.S)
        return result.group(1).strip() if result else ""

    def isVideoCanWin(self, url): return True
    def action(self, action): return ""
    def destroy(self): pass