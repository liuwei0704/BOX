import requests
from bs4 import BeautifulSoup
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Spider:
    def __init__(self):
        self.host = "https://www.kukuys.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": self.host
        }

    def getDependence(self): return []
    def init(self, extend=""): pass

    def homeContent(self, filter):
        classes = [
            {"type_name": "電影", "type_id": "1"},
            {"type_name": "電視劇", "type_id": "2"},
            {"type_name": "綜藝", "type_id": "3"},
            {"type_name": "動漫", "type_id": "4"},
            {"type_name": "動作片", "type_id": "5"},
            {"type_name": "喜劇片", "type_id": "6"},
            {"type_name": "愛情片", "type_id": "7"},
            {"type_name": "科幻片", "type_id": "8"},
            {"type_name": "恐怖片", "type_id": "9"},
            {"type_name": "劇情片", "type_id": "10"},
            {"type_name": "戰爭片", "type_id": "11"},
            {"type_name": "國產劇", "type_id": "12"},
            {"type_name": "香港劇", "type_id": "13"},
            {"type_name": "韓國劇", "type_id": "14"},
            {"type_name": "歐美劇", "type_id": "15"},
            {"type_name": "台灣劇", "type_id": "16"},
            {"type_name": "日本劇", "type_id": "17"},
            {"type_name": "海外劇", "type_id": "18"},
            {"type_name": "微電影", "type_id": "19"},
            {"type_name": "🔞福利1", "type_id": "20"},
            {"type_name": "🔞福利2", "type_id": "21"}
           ]
        result = {"class": classes, "list": []}
        try:
            res = requests.get(self.host, headers=self.headers, timeout=10, verify=False)
            res.encoding = 'utf-8'
            result["list"] = self.parse_list(res.text)
        except: pass
        return result

    def homeVideoContent(self): return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg)
        # 修正分页 URL 格式：/p/1-pg-2.html
        url = f"{self.host}/p/{tid}-pg-{pg}.html" if pg > 1 else f"{self.host}/p/{tid}.html"
        result = {"list": [], "page": pg, "pagecount": pg, "limit": 20, "total": 0}
        try:
            res = requests.get(url, headers=self.headers, timeout=10, verify=False)
            res.encoding = 'utf-8'
            html = res.text
            pg_match = re.search(r'-pg-(\d+)\.html\"[^\>]*\>尾页', html)
            if pg_match: result["pagecount"] = int(pg_match.group(1))
            else:
                pg_nums = re.findall(r'-pg-(\d+)\.html', html)
                result["pagecount"] = max([int(n) for n in pg_nums]) if pg_nums else pg + 1
            result["list"] = self.parse_list(html)
        except: pass
        return result

    def parse_list(self, html):
        videos = []
        seen_ids = set()
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/v/(\d+)\.html'))
        
        for a in links:
            vid = re.search(r'/v/(\d+)\.html', a['href']).group(1)
            if vid in seen_ids: continue
            
            img = a.find('img') or a.parent.find('img')
            if not img: continue
            
            # 清理名称中的广告词
            name = (img.get('alt') or a.get('title') or "").split('｜')[-1].strip()
            
            # 角标提取：三层回溯逻辑
            remark = ""
            parent = a.parent
            for _ in range(3):
                if not parent: break
                for tag in parent.find_all(['span', 'em', 'font'], recursive=True):
                    t = tag.get_text(strip=True)
                    if t and len(t) < 12 and any(k in t for k in ['集', '完', 'HD', '蓝光', '期', '更新']):
                        remark = t; break
                if remark: break
                parent = parent.parent

            pic = img.get('data-original') or img.get('src', '')
            if pic.startswith('//'): pic = 'https:' + pic
            elif pic.startswith('/') and not pic.startswith('//'): pic = self.host + pic
            
            seen_ids.add(vid)
            videos.append({"vod_id": vid, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
        return videos

    def detailContent(self, ids):
        vid = ids[0]
        url = f"{self.host}/v/{vid}.html"
        result = {"list": []}
        try:
            res = requests.get(url, headers=self.headers, timeout=10, verify=False)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. 基础信息提取
            h1 = soup.find('h1')
            name = h1.contents[0].strip() if h1 else ""
            img = soup.find('img', class_='lazy')
            pic = img.get('data-original') if img else ""
            
            # 【修复简介提取】
            plot = ""
            for p in soup.find_all('p'):
                txt = p.get_text(strip=True)
                if "剧情简介：" in txt:
                    plot = txt.replace("剧情简介：", "").strip()
                    break

            from_list = []
            url_list = []
            
            # 2. 线路和播放列表：精准对接 .playfrom 和 id^=stab1
            tab_items = soup.select('.playfrom li')
            playlist_divs = soup.select('div[id^="stab1"]')

            for i, div in enumerate(playlist_divs):
                f_name = f"线路 {i+1}"
                if i < len(tab_items):
                    # 获取 em 或直接获取 li 文本并去除末尾数字（线路长度统计）
                    f_name = tab_items[i].get_text(strip=True)
                    f_name = re.sub(r'\d+$', '', f_name)

                # 提取 /play/ 链接
                links = div.find_all('a', href=re.compile(r'/play/'))
                p_urls = [f"{a.get_text(strip=True)}${a['href']}" for a in links if a.get('href')]
                
                if p_urls:
                    from_list.append(f_name)
                    url_list.append("#".join(p_urls))

            result["list"].append({
                "vod_id": vid, 
                "vod_name": name, 
                "vod_pic": pic,
                "vod_play_from": "$$$".join(from_list),
                "vod_play_url": "$$$".join(url_list),
                "vod_content": plot
            })
        except: pass
        return result

    def playerContent(self, flag, id, vipFlags):
        return {"parse": 1, "url": self.host + id if id.startswith('/') else id}

    def searchContent(self, keyword, quick, pg=1): return {"list": []}
    def liveContent(self): return {}
    def destroy(self): pass