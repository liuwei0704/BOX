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
        """返回分類列表 + 首頁推薦影片 + 篩選器"""
        result = {
            "class": [{"type_id": k, "type_name": v} for k, v in self.type_map.items()],
            "list": [],
            "filters": {
                # 短劇分類的篩選器
                "KCCCCCCK": [
                    {
                        "key": "剧情",
                        "name": "剧情",
                        "value": [
                            {"n": "全部", "v": ""},
                            {"n": "都市", "v": "都市"},
                            {"n": "赘婿", "v": "赘婿"},
                            {"n": "战神", "v": "战神"},
                            {"n": "古代言情", "v": "古代言情"},
                            {"n": "现代言情", "v": "现代言情"},
                            {"n": "历史", "v": "历史"},
                            {"n": "脑洞", "v": "脑洞"},
                            {"n": "玄幻", "v": "玄幻"},
                            {"n": "电视节目", "v": "电视节目"},
                            {"n": "搞笑", "v": "搞笑"},
                            {"n": "网剧", "v": "网剧"},
                            {"n": "喜剧", "v": "喜剧"},
                            {"n": "萌宝", "v": "萌宝"},
                            {"n": "神豪", "v": "神豪"},
                            {"n": "致富", "v": "致富"},
                            {"n": "奇幻脑洞", "v": "奇幻脑洞"},
                            {"n": "超能", "v": "超能"},
                            {"n": "强者回归", "v": "强者回归"},
                            {"n": "甜宠", "v": "甜宠"},
                            {"n": "励志", "v": "励志"},
                            {"n": "豪门恩怨", "v": "豪门恩怨"},
                            {"n": "复仇", "v": "复仇"},
                            {"n": "长生", "v": "长生"},
                            {"n": "神医", "v": "神医"},
                            {"n": "马甲", "v": "马甲"},
                            {"n": "亲情", "v": "亲情"},
                            {"n": "小人物", "v": "小人物"},
                            {"n": "奇幻", "v": "奇幻"},
                            {"n": "无敌", "v": "无敌"},
                            {"n": "现实", "v": "现实"},
                            {"n": "重生", "v": "重生"},
                            {"n": "闪婚", "v": "闪婚"},
                            {"n": "职场商战", "v": "职场商战"},
                            {"n": "穿越", "v": "穿越"},
                            {"n": "年代", "v": "年代"},
                            {"n": "权谋", "v": "权谋"},
                            {"n": "高手下山", "v": "高手下山"},
                            {"n": "悬疑", "v": "悬疑"},
                            {"n": "家国情仇", "v": "家国情仇"},
                            {"n": "虐恋", "v": "虐恋"},
                            {"n": "古装", "v": "古装"},
                            {"n": "时空之旅", "v": "时空之旅"},
                            {"n": "玄幻仙侠", "v": "玄幻仙侠"},
                            {"n": "欢喜冤家", "v": "欢喜冤家"},
                            {"n": "传承觉醒", "v": "传承觉醒"},
                            {"n": "情感", "v": "情感"},
                            {"n": "逆袭", "v": "逆袭"},
                            {"n": "家庭", "v": "家庭"}
                        ]
                    },
                    {
                        "key": "年份",
                        "name": "年份",
                        "value": [
                            {"n": "全部", "v": ""},
                            {"n": "2026", "v": "2026"},
                            {"n": "2025", "v": "2025"},
                            {"n": "2024", "v": "2024"},
                            {"n": "2023", "v": "2023"},
                            {"n": "2022", "v": "2022"},
                            {"n": "2021", "v": "2021"},
                            {"n": "2020", "v": "2020"}
                        ]
                    },
                    {
                        "key": "排序",
                        "name": "排序",
                        "value": [
                            {"n": "时间", "v": "time"},
                            {"n": "人气", "v": "hits"},
                            {"n": "评分", "v": "score"}
                        ]
                    }
                ]
            }
        }
        
        # 抓取首頁獲取推薦影片
        res = self.fetch(self.site_url)
        if res:
            html = res.text
            # 從 sm-swiper 中提取推薦影片
            slides = re.findall(
                r'<div class="swiper-slide">.*?<div class="pic">.*?<a href="(/voddetail/[^"]+)".*?<img[^>]+alt="([^"]+)".*?</div>.*?<div class="ins">.*?<p>(.*?)</p>',
                html, re.S
            )
            
            for slide in slides:
                vod_id, name, remark = slide
                img_match = re.search(
                    r'<a href="' + re.escape(vod_id) + r'"[^>]*>.*?<img[^>]+src="([^"]+)"',
                    html, re.S
                )
                pic = img_match.group(1) if img_match else ""
                
                result["list"].append({
                    "vod_id": vod_id,
                    "vod_name": name.strip(),
                    "vod_pic": pic if pic.startswith('http') else self.site_url + pic,
                    "vod_remarks": remark.strip()
                })
                        
        return result

    def categoryContent(self, tid, pg, filter, extend):
        """
        獲取分類列表，支持篩選
        extend 格式: {"剧情": "都市", "年份": "2026", "排序": "time"}
        """
        pg = int(pg) if str(pg).isdigit() else 1
        
        # 提取篩選參數
        class_val = extend.get('剧情', '') if extend else ''
        year_val = extend.get('年份', '') if extend else ''
        sort_val = extend.get('排序', '') if extend else ''
        
        # 構造 URL
        # 格式: /vodshow/{tid}--{排序}---{劇情}-----{頁碼}---{年份}.html
        if sort_val:
            url_path = f"/vodshow/{tid}--{sort_val}---{class_val}-----{pg}---{year_val}.html"
        else:
            url_path = f"/vodshow/{tid}---{class_val}-----{pg}---{year_val}.html"
        
        url = self.site_url + url_path
        res = self.fetch(url)
        video_list = []
        max_page = pg
        
        if res:
            html = res.text
            # 匹配影片列表
            blocks = re.findall(r'<a href="(/voddetail/[^"]+)".*?<img[^>]+data-original="([^"]+)".*?alt="([^"]+)".*?<div class="module-item-note">(.*?)</div>', html, re.S)
            
            for v_url, v_pic, v_name, v_remk in blocks:
                video_list.append({
                    "vod_id": v_url,
                    "vod_name": v_name.strip(),
                    "vod_pic": v_pic if v_pic.startswith('http') else self.site_url + v_pic,
                    "vod_remarks": v_remk.strip()
                })
            
            # 如果上面的匹配沒抓到，用更寬鬆的方式
            if not video_list:
                blocks2 = re.findall(r'(<a[^>]+href="/voddetail/[^"]+"[^>]*>.*?</a>)', html, re.S)
                for block in blocks2:
                    v_url = re.search(r'href="(/voddetail/[^"]+)"', block)
                    v_pic = re.search(r'data-original="([^"]+)"', block)
                    v_name = re.search(r'alt="([^"]+)"', block)
                    v_remk = re.search(r'class="module-item-note">(.*?)</div>', block, re.S)
                    
                    if v_url and v_pic:
                        video_list.append({
                            "vod_id": v_url.group(1),
                            "vod_name": v_name.group(1).strip() if v_name else "未知",
                            "vod_pic": v_pic.group(1) if v_pic.group(1).startswith('http') else self.site_url + v_pic.group(1),
                            "vod_remarks": v_remk.group(1).strip() if v_remk else ""
                        })
            
            # 解析總頁數
            page_links = re.findall(r'<a[^>]+href="[^"]*---(\d+)---[^"]*"[^>]*>', html)
            if page_links:
                max_page = max([int(x) for x in page_links])
            
        return {"list": video_list, "page": pg, "pagecount": max_page, "limit": 20, "total": max_page*20}

    def detailContent(self, ids):
        vod_id = ids[0] if isinstance(ids, list) else ids
        url = self.site_url + vod_id if not vod_id.startswith('http') else vod_id
        res = self.fetch(url)
        if not res: return {"list": []}
        
        html = res.text
        
        name_match = re.search(r'<h1>(.*?)</h1>', html)
        if name_match:
            name = name_match.group(1).strip()
        else:
            title_match = re.search(r'<title>(.*?)</title>', html)
            if title_match:
                name = title_match.group(1).split('-')[0].strip()
            else:
                name = "未知影片"
        
        pic_match = re.search(r'data-original="([^"]+)"', html)
        pic = pic_match.group(1) if pic_match else ""
        
        desc_match = re.search(r'<div class="module-info-introduction-content">(.*?)</div>', html, re.S)
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
        else:
            desc = "暫無簡介"
        
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
        url = self.site_url + id if id.startswith('/') else id
        res = self.fetch(url)
        if not res:
            return {"parse": 0, "url": ""}
        
        html = res.text
        
        match = re.search(r'player_aaaa\s*=\s*({[^}]+})', html, re.S)
        if match:
            try:
                data_str = match.group(1).replace("'", '"')
                data = json.loads(data_str)
                encrypted_url = data.get('url', '')
                encrypt_level = data.get('encrypt', 0)
                
                if encrypt_level == 2 and encrypted_url:
                    decoded_base64 = base64.b64decode(encrypted_url).decode('utf-8')
                    play_url = unquote(decoded_base64)
                    if play_url.startswith('http'):
                        return {"parse": 0, "url": play_url, "header": self.headers}
                        
            except Exception as e:
                print(f"[ERROR] 解密播放地址失敗: {e}")
        
        return {"parse": 1, "url": url, "header": self.headers}