import sys
import re
import json
import base64
import requests
from urllib.parse import unquote
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
requests.packages.urllib3.disable_warnings()

from base.spider import Spider

class Spider(Spider):
    def __init__(self):
        super(Spider, self).__init__()
        # 根據導航欄定義的分類 ID
        self.type_map = {
            "KCCCCCCK": "短劇",
            "KCCCCCCk": "女頻戀愛",
            "KCCCCCCp": "反轉爽劇",
            "KCCCCCCH": "腦洞懸疑",
            "KCCCCCCJ": "年代穿越",
            "KCCCCCCL": "古裝仙俠",
            "KCCCCCCZ": "現代都市"
        }
        self.site_url = "https://www.xfduanju.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": self.site_url,
        }
        self.sess = None

    def getName(self):
        return "下飯短劇"

    def init(self, extend=""):
        super().init(extend)
        self.sess = requests.Session()
        self.sess.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1)))

    def fetch(self, url, post_data=None):
        if not self.sess: self.init()
        try:
            if post_data:
                res = self.sess.post(url, data=post_data, headers=self.headers, timeout=10, verify=False)
            else:
                res = self.sess.get(url, headers=self.headers, timeout=10, verify=False)
            res.encoding = "utf-8"
            return res
        except Exception:
            return None

    def homeContent(self, filter):
        cate_list = [{"type_id": k, "type_name": v} for k, v in self.type_map.items()]
        return {"class": cate_list}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if str(pg).isdigit() else 1
        url = f"{self.site_url}/vodshow/{tid}--------{pg}---.html"
        res = self.fetch(url)
        video_list = []
        max_page = pg
        
        if res:
            html = res.text
            blocks = re.findall(r'(<a[^>]+href="/voddetail/[^"]+"[^>]*>.*?</a>)', html, re.S)
            
            for block in blocks:
                v_url = re.search(r'href="(/voddetail/[^"]+)"', block)
                v_pic = re.search(r'data-original="([^"]+)"', block)
                v_name = re.search(r'title="([^"]+)"', block)
                v_remk = re.search(r'class="module-item-note">(.*?)</div>', block, re.S)
                
                if v_url and v_pic:
                    video_list.append({
                        "vod_id": v_url.group(1),
                        "vod_name": v_name.group(1).strip() if v_name else "未知",
                        "vod_pic": v_pic.group(1) if v_pic.group(1).startswith('http') else self.site_url + v_pic.group(1),
                        "vod_remarks": v_remk.group(1).strip() if v_remk else ""
                    })
            
            p_match = re.findall(r'---(\d+)---\.html', html)
            if p_match:
                max_page = max([int(x) for x in p_match])
            
        return {"list": video_list, "page": pg, "pagecount": max_page, "limit": 20, "total": max_page*20}

    def detailContent(self, ids):
        vod_id = ids[0] if isinstance(ids, list) else ids
        url = self.site_url + vod_id if not vod_id.startswith('http') else vod_id
        res = self.fetch(url)
        if not res: return {"list": []}
        
        html = res.text
        
        # 1. 从 <h1> 标签提取影片名称（最准确）
        name_match = re.search(r'<h1>(.*?)</h1>', html)
        if name_match:
            name = name_match.group(1).strip()
        else:
            # 兜底：从 title 提取
            title_match = re.search(r'<title>(.*?)</title>', html)
            if title_match:
                name = title_match.group(1).split('-')[0].strip()
            else:
                name = "未知影片"
        
        # 2. 封面图片
        pic_match = re.search(r'data-original="([^"]+)"', html)
        pic = pic_match.group(1) if pic_match else ""
        
        # 3. 簡介（从 module-info-introduction-content 提取）
        desc_match = re.search(r'<div class="module-info-introduction-content">(.*?)</div>', html, re.S)
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
        else:
            desc = "暫無簡介"
        
        # 4. 播放源解析
        tabs = re.findall(r'class="module-tab-item[^"]*".*?<span>(.*?)</span>', html, re.S)
        lists = re.findall(r'class="module-play-list-content[^"]*">(.*?)</div>', html, re.S)
        from_list, url_list = [], []
        
        for i in range(len(lists)):
            from_list.append(tabs[i] if i < len(tabs) else f"播放源{i+1}")
            ep_matches = re.findall(r'href="(/vodplay/[^"]+)".*?<span>(.*?)</span>', lists[i], re.S)
            episodes = [f"{e_n.strip()}${e_u}" for e_u, e_n in ep_matches]
            url_list.append("#".join(episodes))

        return {"list": [{
            "vod_id": vod_id, 
            "vod_name": name, 
            "vod_pic": pic if pic.startswith('http') else self.site_url + pic,
            "vod_content": desc, 
            "vod_play_from": "$$$".join(from_list), 
            "vod_play_url": "$$$".join(url_list)
        }]}

    def searchContent(self, keyword, quick, pg=1):
        url = f"{self.site_url}/vodsearch/-------------.html?wd={keyword}"
        res = self.fetch(url)
        video_list = []
        
        if res:
            html = res.text
            blocks = re.findall(r'<div class="module-card-item module-item">(.*?)<div class="module-card-item-footer">', html, re.S)
            
            for block in blocks:
                v_url = re.search(r'href="(/voddetail/[^"]+)"', block)
                v_pic = re.search(r'data-original="([^"]+)"', block)
                v_name = re.search(r'title="([^"]+)"', block) or re.search(r'alt="([^"]+)"', block)
                v_remk = re.search(r'class="module-item-note">(.*?)</div>', block, re.S)
                
                if v_url and v_pic:
                    video_list.append({
                        "vod_id": v_url.group(1),
                        "vod_name": v_name.group(1) if v_name else "搜尋結果",
                        "vod_pic": v_pic.group(1) if v_pic.group(1).startswith('http') else self.site_url + v_pic.group(1),
                        "vod_remarks": v_remk.group(1).strip() if v_remk else ""
                    })
        return {"list": video_list}

    def playerContent(self, flag, id, vipFlags):
        """
        解析播放頁，提取真實 m3u8 播放地址
        支持 encrypt:2 雙重編碼（URL編碼 + Base64）
        """
        url = self.site_url + id if id.startswith('/') else id
        res = self.fetch(url)
        if not res:
            return {"parse": 0, "url": ""}
        
        html = res.text
        
        # 1. 提取 player_aaaa 中的加密 url
        match = re.search(r'player_aaaa\s*=\s*({[^}]+})', html, re.S)
        if match:
            try:
                data_str = match.group(1).replace("'", '"')
                data = json.loads(data_str)
                encrypted_url = data.get('url', '')
                encrypt_level = data.get('encrypt', 0)
                
                # encrypt: 2 表示 URL 編碼 + Base64
                if encrypt_level == 2 and encrypted_url:
                    decoded_base64 = base64.b64decode(encrypted_url).decode('utf-8')
                    play_url = unquote(decoded_base64)
                    if play_url.startswith('http'):
                        return {"parse": 0, "url": play_url, "header": self.headers}
                        
            except Exception as e:
                print(f"[ERROR] 解密播放地址失敗: {e}")
        
        # 2. 嘗試從 iframe 提取
        iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', html)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            if not iframe_url.startswith('http'):
                iframe_url = self.site_url + iframe_url
            res2 = self.fetch(iframe_url)
            if res2:
                html2 = res2.text
                match2 = re.search(r'player_aaaa\s*=\s*({[^}]+})', html2, re.S)
                if match2:
                    try:
                        data2 = json.loads(match2.group(1).replace("'", '"'))
                        encrypted_url2 = data2.get('url', '')
                        encrypt_level2 = data2.get('encrypt', 0)
                        if encrypt_level2 == 2 and encrypted_url2:
                            decoded_base64_2 = base64.b64decode(encrypted_url2).decode('utf-8')
                            play_url2 = unquote(decoded_base64_2)
                            if play_url2.startswith('http'):
                                return {"parse": 0, "url": play_url2, "header": self.headers}
                    except:
                        pass
        
        # 3. 兜底：返回播放頁讓內核解析
        return {"parse": 1, "url": url, "header": self.headers}