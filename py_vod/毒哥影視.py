import sys
import re
import json
import requests
import base64
import urllib.parse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from base.spider import Spider

requests.packages.urllib3.disable_warnings()

class Spider(Spider):
    site_url = "https://dgtv.cc"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://dgtv.cc"
    }

    def getName(self):
        return "毒哥影視"

    def init(self, extend=""):
        super().init(extend)
        self.sess = requests.Session()
        self.sess.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1)))

    def fetch(self, url, timeout=10):
        try:
            if not hasattr(self, 'sess'):
                self.sess = requests.Session()
            res = self.sess.get(url, headers=self.headers, timeout=timeout, verify=False)
            res.encoding = "utf-8"
            return res
        except:
            return None

    def homeContent(self, filter):
        # 根據你提供的 HTML 完整映射分類 ID
        cate_list = [
            {"type_name": "動作片", "type_id": "6"},
            {"type_name": "喜劇片", "type_id": "7"},
            {"type_name": "愛情片", "type_id": "8"},
            {"type_name": "科幻片", "type_id": "9"},
            {"type_name": "恐怖片", "type_id": "10"},
            {"type_name": "劇情片", "type_id": "11"},
            {"type_name": "紀錄片", "type_id": "13"},
            {"type_name": "動畫片", "type_id": "14"},
            {"type_name": "國產劇", "type_id": "15"},
            {"type_name": "港台劇", "type_id": "16"},
            {"type_name": "日韓劇", "type_id": "17"},
            {"type_name": "歐美劇", "type_id": "18"},
            {"type_name": "Netflix", "type_id": "20"},
            {"type_name": "日韓動漫", "type_id": "22"},
            {"type_name": "反轉爽劇", "type_id": "27"},
            {"type_name": "古裝仙俠", "type_id": "28"},
            {"type_name": "年代穿越", "type_id": "29"},
            {"type_name": "現代都市", "type_id": "31"},
            {"type_name": "短劇", "type_id": "4"}
        ]
        return {"class": cate_list}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if str(pg).isdigit() else 1
        list_url = f"{self.site_url}/class/{tid}-{pg}.html"
        res = self.fetch(list_url)
        video_list = []
        if res and res.ok:
            pattern = r'myui-vodlist__thumb.*?href="(.*?)".*?title="(.*?)".*?data-original="(.*?)"'
            matches = re.findall(pattern, res.text, re.S)
            for path, name, pic in matches:
                vod_id = path.split('/')[-1].split('.')[0]
                if not vod_id or "play" in path: continue
                video_list.append({
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": pic if pic.startswith("http") else self.site_url + pic,
                    "vod_remarks": ""
                })
        return {"list": video_list, "page": pg, "pagecount": pg + 1, "limit": 20, "total": 999}

    def detailContent(self, ids):
        vod_id = ids[0]
        url = f"{self.site_url}/movie/{vod_id}.html"
        res = self.fetch(url)
        if not res or not res.ok:
            return {"list": []}
        html = res.text
        name_match = re.search(r'<h1.*?>(.*?)</h1>', html, re.S)
        name = re.sub(r'<.*?>', '', name_match.group(1)).strip() if name_match else "未知影片"
        pic_match = re.search(r'data-original="(.*?)"', html)
        pic = pic_match.group(1) if pic_match else ""
        from_list = re.findall(r'data-toggle="tab" href="#playlist\d+">(.*?)</a>', html)
        url_list = []
        tabs = re.findall(r'id="playlist\d+" class="tab-pane fade.*?>(.*?)</ul>', html, re.S)
        for tab in tabs:
            links = re.findall(r'href="(.*?)".*?>(.*?)</a>', tab)
            urls = []
            for link_url, link_name in links:
                clean_name = re.sub(r'<.*?>', '', link_name).strip()
                urls.append(f"{clean_name}${link_url}")
            url_list.append("#".join(urls))
        vod = {
            "vod_id": vod_id, "vod_name": name, "vod_pic": pic if pic.startswith("http") else self.site_url + pic,
            "vod_play_from": "$$$".join(from_list) if from_list else "毒哥雲播",
            "vod_play_url": "$$$".join(url_list) if url_list else ""
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        play_url = self.site_url + id if id.startswith("/") else id
        res = self.fetch(play_url)
        if not res or not res.ok:
            return {"parse": 1, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.site_url + "/"}}
        html = res.text
        content = ""
        for key in ["player_aaaa", "player_data", "player_info"]:
            if key + "=" in html:
                try:
                    content = html.split(key + "=")[1].split("</script>")[0].strip()
                    if content.endswith(";"): content = content[:-1]
                    break
                except: continue
        if content:
            try:
                data = json.loads(content)
                url = data.get('url', '')
                if url and not url.startswith('http') and not url.startswith('/'):
                    try:
                        url = base64.b64decode(url).decode('utf-8')
                        url = urllib.parse.unquote(url)
                    except: pass
                if url:
                    if "url=" in url:
                        url = url.split("url=")[-1]
                        url = urllib.parse.unquote(url)
                    is_video = any(ext in url.lower() for ext in [".m3u8", ".mp4", ".flv", ".avi"])
                    return {
                        "parse": 0 if is_video else 1,
                        "url": url,
                        "header": {"User-Agent": self.headers["User-Agent"], "Referer": play_url}
                    }
            except: pass
        return {"parse": 1, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.site_url + "/"}}

    def searchContent(self, keyword, quick, pg=1):
        url = f"{self.site_url}/search.php?searchword={keyword}"
        res = self.fetch(url)
        video_list = []
        if res and res.ok:
            pattern = r'myui-vodlist__thumb.*?href="(.*?)".*?title="(.*?)".*?data-original="(.*?)"'
            matches = re.findall(pattern, res.text, re.S)
            for path, name, pic in matches:
                vod_id = path.split('/')[-1].split('.')[0]
                if not vod_id or "play" in path: continue
                video_list.append({
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": pic if pic.startswith("http") else self.site_url + pic
                })
        return {"list": video_list}