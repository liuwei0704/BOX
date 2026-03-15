import sys
import re
import json
import requests
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
        # 設定重試機制增加穩定性
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
        # 修正分類 URL 格式
        url = f"{self.site_url}/vodshow/{tid}--------{pg}---.html"
        res = self.fetch(url)
        video_list = []
        max_page = pg
        
        if res:
            html = res.text
            # 改用更強大的區塊匹配：定位包含 module-item 的 <a> 標籤
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
            
            # 簡單的分頁解析
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
        # 標題與封面
        name_match = re.search(r'<title>(.*?)</title>', html)
        name = name_match.group(1).split('-')[0].strip() if name_match else "未知影片"
        pic_match = re.search(r'data-original="([^"]+)"', html)
        pic = pic_match.group(1) if pic_match else ""
        
        # 簡介
        desc_match = re.search(r'video-info-content.*?>(.*?)</div>', html, re.S)
        desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip() if desc_match else "暫無簡介"
        
        # 播放源解析
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
        # 修正：下飯短劇搜尋必須使用 GET 請求，參數為 wd
        # URL 格式：/vodsearch/-------------.html?wd=xxx
        url = f"{self.site_url}/vodsearch/-------------.html?wd={keyword}"
        res = self.fetch(url)
        video_list = []
        
        if res:
            html = res.text
            # 定位搜尋結果卡片
            blocks = re.findall(r'<div class="module-card-item module-item">(.*?)<div class="module-card-item-footer">', html, re.S)
            
            for block in blocks:
                v_url = re.search(r'href="(/voddetail/[^"]+)"', block)
                v_pic = re.search(r'data-original="([^"]+)"', block)
                # 搜尋頁面的名稱通常在 <strong> 標籤或 alt 屬性中
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
        # 播放地址處理，這裡直接返回 ID 交給內核解析，或拼接完整網址
        url = self.site_url + id if id.startswith('/') else id
        return {"parse": 1, "url": url, "header": self.headers}