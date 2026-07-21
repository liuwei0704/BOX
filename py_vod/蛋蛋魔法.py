import re
import requests
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    host = "https://ddmf.net"
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://ddmf.net/'
    }

    def getName(self):
        return "蛋蛋魔法"

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        result = {
            "class": [
                {"type_id": "1", "type_name": "电影"},
                {"type_id": "2", "type_name": "电视剧"},
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "4", "type_name": "动漫"},
                {"type_id": "63", "type_name": "短劇"},
                {"type_id": "5", "type_name": "福利"}
            ],
            "list": []
        }
        try:
            res = requests.get(self.host, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            result["list"] = self.parseList(res.text)
        except: pass
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {"list": [], "page": int(pg), "pagecount": 999, "limit": 20, "total": 999}
        # 双路径探测：vodshow (筛选版) 和 vodtype (分类版)
        urls = [f"{self.host}/vodshow/{tid}-----------{pg}---.html", f"{self.host}/vodtype/{tid}-{pg}.html"]
        for url in urls:
            try:
                res = requests.get(url, headers=self.header, timeout=10)
                res.encoding = 'utf-8'
                v_list = self.parseList(res.text)
                if v_list:
                    result["list"] = v_list
                    break
            except: pass
        return result

    def searchContent(self, key, quick, pg=1):
        result = {"list": []}
        url = f"{self.host}/vodsearch/-------------.html?wd={key}"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            result["list"] = self.parseList(res.text)
        except: pass
        return result

    def parseList(self, html):
        vod_list = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # 锁定 mxone 模板的通用容器
            items = soup.find_all('div', class_=re.compile(r'module-item'))
            seen_ids = set()
            for item in items:
                link = item.find('a', href=re.compile(r'/voddetail/'))
                img = item.find('img')
                if not link or not img: continue
                
                v_id = re.search(r'/(\d+)\.html', link['href']).group(1)
                if v_id in seen_ids: continue
                
                # 修复图片：mxone 核心就是 data-original
                v_pic = img.get('data-original') or img.get('data-src') or img.get('src') or ""
                if v_pic.startswith('/'): v_pic = self.host + v_pic
                
                v_name = img.get('alt') or link.get('title') or ""
                v_name = re.sub(r'《|》', '', v_name).strip()
                if not v_name: continue

                # 精准锁定备注
                rem_div = item.find('div', class_=re.compile(r'module-item-(note|text)'))
                v_remarks = rem_div.text.strip() if rem_div else ""

                vod_list.append({
                    "vod_id": v_id,
                    "vod_name": v_name,
                    "vod_pic": v_pic,
                    "vod_remarks": v_remarks
                })
                seen_ids.add(v_id)
        except: pass
        return vod_list

    def detailContent(self, ids):
        url = f"{self.host}/voddetail/{ids[0]}.html"
    def detailContent(self, ids):
        url = f"{self.host}/voddetail/{ids[0]}.html"
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            name_tag = soup.find('h1') or soup.find('h2')
            name = name_tag.text.strip() if name_tag else "未知"
            
            # 1. 提取线路名称
            tabs = soup.find_all('div', class_=re.compile(r'module-tab-item|tab-item'))
            tab_names = [t.get_text().strip() for t in tabs if "排序" not in t.get_text()]

            # 2. 提取播放列表容器 (排除掉移动端覆盖层)
            play_containers = soup.find_all('div', class_=re.compile(r'module-play-list|play-list'))
            
            from_list = []
            url_list = []
            global_seen = set()
            
            for i, container in enumerate(play_containers):
                # 过滤掉冗余的移动端容器
                if container.find_parent('div', class_='shortcuts-mobile-overlay'): continue
                
                links = container.find_all('a', href=re.compile(r'/vodplay/'))
                episodes = []
                for a in links:
                    v_name = a.get_text().strip()
                    if not v_name or v_name in ["立即播放", "排序", "倒序"]: continue
                    
                    v_id = a.get('href').split('/')[-1].replace('.html', '')
                    if v_id not in global_seen:
                        episodes.append(f"{v_name}${v_id}")
                        global_seen.add(v_id)
                
                if episodes:
                    s_name = tab_names[i] if i < len(tab_names) else f"线路{i+1}"
                    from_list.append(s_name)
                    url_list.append("#".join(episodes))

            # 3. 兜底逻辑
            if not url_list:
                all_links = soup.find_all('a', href=re.compile(r'/vodplay/'))
                temp = {}
                for a in all_links:
                    vid = a.get('href').split('/')[-1].replace('.html', '')
                    if vid in global_seen: continue
                    line_key = vid.split('-')[1] if '-' in vid else "1"
                    if line_key not in temp: temp[line_key] = []
                    vname = a.get_text().strip()
                    if vname and vname not in ["立即播放"]:
                        temp[line_key].append(f"{vname}${vid}")
                        global_seen.add(vid)
                for k in sorted(temp.keys()):
                    from_list.append(f"线路 {k}")
                    url_list.append("#".join(temp[k]))

            return {"list": [{
                "vod_id": ids[0],
                "vod_name": name,
                "vod_play_from": "$$$".join(from_list),
                "vod_play_url": "$$$".join(url_list)
            }]}
        except: return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        return {
            "parse": 1,
            "url": f"{self.host}/vodplay/{id}.html",
            "header": {
                "User-Agent": self.header['User-Agent'],
                "Referer": self.host
            }
        }
