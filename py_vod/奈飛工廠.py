import sys
import json
import re
from base.spider import Spider

class Spider(Spider):
    host = "https://naifei.im"

    def getName(self):
        return "奈飞工廠"

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        result = {}
        classes = [
            {"type_name": "電影", "type_id": "1"},
            {"type_name": "劇集", "type_id": "2"},
            {"type_name": "綜藝", "type_id": "3"},
            {"type_name": "動漫", "type_id": "4"},
            {"type_name": "短劇", "type_id": "5"}
        ]
        result['class'] = classes
        # 自動加載首頁推薦
        home_data = self.homeVideoContent()
        result['list'] = home_data.get('list', [])
        return result

    def homeVideoContent(self):
        res = self.fetch(self.host)
        html = res.text
        vod_list = []
        # 更加寬鬆的匹配首頁卡片
        pattern = r'href="(/voddetail/.*?\.html)".*?title="(.*?)".*?data-original="(.*?)".*?module-item-note">(.*?)</div>'
        matches = re.findall(pattern, html, re.S)
        for match in matches:
            vod_id = match[0].split('/')[-1].split('.')[0]
            vod_list.append({
                "vod_id": vod_id,
                "vod_name": match[1],
                "vod_pic": match[2],
                "vod_remarks": match[3]
            })
        return {"list": vod_list}

    def categoryContent(self, tid, pg, filter, extend):
        # 修正：針對 naifei.im 調整連字號數量 (8個 -)
        url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
        res = self.fetch(url)
        html = res.text
        vod_list = []
        pattern = r'module-item-cover.*?href="(/voddetail/.*?\.html)".*?title="(.*?)".*?data-original="(.*?)".*?module-item-note">(.*?)</div>'
        matches = re.findall(pattern, html, re.S)
        for match in matches:
            vod_id = match[0].split('/')[-1].split('.')[0]
            vod_list.append({
                "vod_id": vod_id,
                "vod_name": match[1],
                "vod_pic": match[2],
                "vod_remarks": match[3]
            })
        return {
            "list": vod_list,
            "page": int(pg),
            "pagecount": 999,
            "limit": 20,
            "total": 9999
        }

    def detailContent(self, array):
        tid = array[0]
        url = f"{self.host}/voddetail/{tid}.html"
        res = self.fetch(url)
        html = res.text
        
        # 獲取標題和圖片
        name = re.search(r'<h1>(.*?)</h1>', html).group(1) if re.search(r'<h1>(.*?)</h1>', html) else ""
        pic = re.search(r'data-original="(.*?)"', html).group(1) if re.search(r'data-original="(.*?)"', html) else ""
        
        # 播放線路標題 (WJ線路, OK線路等)
        raw_froms = re.findall(r'module-tab-item.*?<span>(.*?)</span>', html, re.S)
        
        # 直接定位播放列表區塊
        raw_play_lists = re.findall(r'class="module-play-list-content.*?>(.*?)</div>', html, re.S)
        
        # 組合線路與選集，便於排序
        combined = []
        for i in range(len(raw_froms)):
            if i < len(raw_play_lists):
                pl_html = raw_play_lists[i]
                items = re.findall(r'href="(/vodplay/.*?\.html)".*?<span>(.*?)</span>', pl_html, re.S)
                if not items:
                    items = re.findall(r'href="(/vodplay/.*?\.html)" title="(.*?)"', pl_html, re.S)
                url_str = "#".join([f"{it[1]}${it[0]}" for it in items])
                combined.append({"from": raw_froms[i], "url": url_str})

        # 排序：將含有 "OK" 的線路排到第一位
        combined.sort(key=lambda x: 0 if "OK" in x["from"].upper() else 1)

        final_froms = [c["from"] for c in combined]
        final_urls = [c["url"] for c in combined]
            
        vod = {
            "vod_id": tid,
            "vod_name": name,
            "vod_pic": pic,
            "vod_play_from": "$$$".join(final_froms),
            "vod_play_url": "$$$".join(final_urls)
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        url = f"{self.host}{id}"
        res = self.fetch(url)
        match = re.search(r'var player_aaaa=(.*?)</script>', res.text)
        if match:
            config = json.loads(match.group(1))
            return {"parse": 0, "url": config.get('url', ''), "header": {"User-Agent": "Mozilla/5.0"}}
        return {"parse": 0, "url": ""}

    def searchContent(self, keyword, quick, pg=1):
        url = f"{self.host}/vodsearch/-------------.html?wd={keyword}"
        res = self.fetch(url)
        # 簡單適配搜索
        matches = re.findall(r'href="(/voddetail/.*?\.html)".*?title="(.*?)"', res.text, re.S)
        vod_list = []
        for match in matches:
            vod_list.append({"vod_id": match[0].split('/')[-1].split('.')[0], "vod_name": match[1], "vod_pic": "", "vod_remarks": ""})
        return {"list": vod_list}