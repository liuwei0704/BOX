import sys, os, json, re, requests, urllib.parse
from base64 import b64decode

class Spider():
    def __init__(self):
        self.host = "https://www.dakays.com"
        self.header = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Referer": "https://www.dakays.com/"
        }

    def getName(self): return "打卡影视"
    def init(self, extend=""): pass
    def getDependence(self): return []
    def isVideoCanPlay(self, url): return True

    def homeContent(self, filter):
        classes = [{"type_id": "1", "type_name": "电影"},{"type_id": "2", "type_name": "电视剧"},{"type_id": "3", "type_name": "动漫"},{"type_id": "4", "type_name": "综艺"},{"type_id": "29", "type_name": "短剧"}]
        return {"class": classes}

    def homeVideoContent(self):
        res = self.categoryContent("1", "1", False, {})
        return {"list": res.get("list", [])[:15]}

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.host}/sort/{tid}.html" if int(pg) <= 1 else f"{self.host}/sort/{tid}-{pg}.html"
        res = self.fetch(url)
        pattern = r'class="stui-vodlist__thumb\s+lazyload"[^>]*?href="(/html/\d+\.html)"[^>]*?title="(.*?)"[^>]*?data-original="(.*?)"[^>]*?>.*?class="pic-text\s+text-right">(.*?)</span>'
        matches = re.findall(pattern, res, re.S)
        vod_list = []
        for href, name, pic, remark in matches:
            vod_list.append({"vod_id": href, "vod_name": name, "vod_pic": pic if pic.startswith("http") else self.host + pic, "vod_remarks": remark.strip()})
        return {"page": pg, "list": vod_list}

    def detailContent(self, ids):
        vod_id = ids[0]
        res = self.fetch(self.host + vod_id)
        name = self.regStr(res, r'<h1 class="title">(.*?)</h1>', "视频")
        pic = self.regStr(res, r'data-original="(.*?)"', "")
        remark = self.regStr(res, r'class="data">类型：.*?</span><span class="data">(.*?)</span>', "")
        
        from_names = re.findall(r'data-toggle="tab"[^>]*>([^<]+)</a>', res)
        if not from_names:
            from_names = re.findall(r'<h3 class="title">([^<]+)</h3>', res)
        
        valid_names = []
        for fn in from_names:
            if any(x in fn for x in ["免费", "官解", "排序", "推荐"]): continue
            valid_names.append(fn.strip())

        playlist_blocks = re.findall(r'<ul[^>]*class="stui-content__playlist[^>]*>(.*?)</ul>', res, re.S)
        
        play_list_data = []
        for i, list_html in enumerate(playlist_blocks):
            links = re.findall(r'href="(/yun/\d+-\d+-\d+\.html)">(.*?)</a>', list_html)
            if links:
                urls = [f"{l[1]}${l[0]}" for l in links]
                f_name = valid_names[i] if i < len(valid_names) else f"线路{i+1}"
                play_list_data.append(f"{f_name}#" + "#".join(urls))
            
        return {"list": [{
            "vod_id": vod_id, "vod_name": name, "vod_pic": pic if pic.startswith("http") else self.host + pic,
            "vod_remarks": remark,
            "vod_play_from": "$$$".join([p.split("#")[0] for p in play_list_data]),
            "vod_play_url": "$$$".join(["#".join(p.split("#")[1:]) for p in play_list_data])
        }]}

    def searchContent(self, key, quick, pg=1):
        res = self.fetch(f"{self.host}/sou/{key}-------------.html")
        pattern = r'href="(/html/\d+\.html)"[^>]*?title="(.*?)"[^>]*?data-original="(.*?)"[^>]*?>.*?class="pic-text\s+text-right">(.*?)</span>'
        matches = re.findall(pattern, res, re.S)
        vod_list = []
        for href, name, pic, remark in matches:
            vod_list.append({"vod_id": href, "vod_name": name, "vod_pic": pic if pic.startswith("http") else self.host + pic, "vod_remarks": remark.strip()})
        if not vod_list:
            try:
                ajax_res = requests.get(f"{self.host}/index.php/ajax/suggest?mid=1&wd={key}", headers=self.header, timeout=10).json()
                for item in ajax_res.get('list', []):
                    vod_list.append({"vod_id": f"/html/{item['id']}.html", "vod_name": item['name'], "vod_pic": item['pic'] if item['pic'].startswith("http") else self.host + item['pic'], "vod_remarks": "Search"})
            except: pass
        return {"list": vod_list}

    def playerContent(self, flag, id, vipFlags):
        res = self.fetch(self.host + id)
        player_match = re.search(r'var\s+(?:player_aaaa|player_data|cms_player|player_ptr)\s*=\s*(\{.*?\})(?:\s*;|\s+<)', res)
        if player_match:
            try:
                json_str = player_match.group(1)
                if "}" in json_str: json_str = json_str[:json_str.rfind("}")+1]
                config = json.loads(json_str)
                play_url = config.get('url', '')
                if not play_url.startswith("http"):
                    try: play_url = b64decode(play_url).decode("utf-8")
                    except: pass
                return {"parse": 1, "url": urllib.parse.unquote(play_url) if "%" in play_url else play_url, "header": self.header}
            except: pass
        return {"parse": 1, "url": self.host + id, "header": self.header}

    def fetch(self, url):
        try:
            r = requests.get(url, headers=self.header, timeout=10)
            r.encoding = 'utf-8'
            return r.text
        except: return ""

    def regStr(self, txt, reg, default):
        m = re.search(reg, txt)
        return m.group(1) if m else default