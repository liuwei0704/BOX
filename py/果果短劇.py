import json
import re
import requests
from urllib.parse import quote, unquote
from lxml import etree

class Spider():
    def getName(self):
        return "果果短剧"

    def init(self, extend=""):
        self.siteUrl = "https://www.ggduanju.com"
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def getDependence(self):
        return []

    def isVideoCanPlay(self):
        return ""

    def isVideoStatus(self, vod_id, name, cnt):
        return True

    def homeContent(self, filter):
        try:
            res = requests.get(self.siteUrl, timeout=10, headers=self.header)
            html = etree.HTML(res.text)
            classes = []
            # 抓取導航
            nodes = html.xpath('//ul[contains(@class, "hl-nav")]/li/a[contains(@href, ".html")]')
            for node in nodes:
                try:
                    name = node.xpath("./text()")[0]
                    if name in ["首页", "留言", "新短剧"]: continue
                    tid = node.xpath("./@href")[0].split("/")[-1].split(".")[0]
                    classes.append({"type_name": name, "type_id": tid})
                except: continue
            return {"class": classes}
        except: return {"class": []}

    def homeVideoContent(self):
        try:
            res = requests.get(self.siteUrl, timeout=10, headers=self.header)
            html = etree.HTML(res.text)
            vod_list = []
            nodes = html.xpath('//ul[contains(@class, "hl-vod-list")]/li')
            for node in nodes:
                try:
                    name = node.xpath('.//a/@title')[0]
                    pic = node.xpath('.//a/@data-original')[0]
                    id = node.xpath('.//a/@href')[0]
                    remark_node = node.xpath('.//span[contains(@class, "remarks")]/text()')
                    remark = remark_node[0] if remark_node else ""
                    vod_list.append({"vod_id": id, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
                except: continue
            return {"list": vod_list}
        except: return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        curr_pg = int(pg)
        vod_list = []
        
        # 常規分類處理
        clean_tid = tid[1:] if tid.startswith('l') else tid
        if curr_pg == 1:
            url = f"{self.siteUrl}/{tid}.html"
        else:
            url = f"{self.siteUrl}/Category{clean_tid}-{'_' * 7}{curr_pg}___.html"
        
        try:
            res = requests.get(url, timeout=10, headers=self.header)
            res.encoding = 'utf-8'
            html = etree.HTML(res.text)
            
            nodes = html.xpath('//ul[contains(@class, "hl-vod-list")]/li')
            for node in nodes:
                try:
                    name = node.xpath('.//a/@title')[0].strip()
                    pic = node.xpath('.//a/@data-original')[0]
                    id = node.xpath('.//a/@href')[0]
                    remark = "".join(node.xpath('.//span[contains(@class, "remarks")]/text()')).strip()
                    vod_list.append({"vod_id": id, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
                except: continue
            
            return {"list": vod_list, "page": curr_pg, "pagecount": curr_pg + 1 if len(vod_list) >= 10 else curr_pg}
        except: return {"list": []}

    def detailContent(self, ids):
        tid = ids[0]
        url = f"{self.siteUrl}{tid}" if not tid.startswith("http") else tid
        try:
            res = requests.get(url, timeout=10, headers=self.header)
            res.encoding = 'utf-8'
            html = etree.HTML(res.text)
            
            name_node = html.xpath('//h2[contains(@class, "hl-dc-title")]/text()')
            name = name_node[0] if name_node else "未知"
            
            pic_node = html.xpath('//div[contains(@class, "hl-dc-pic")]//span/@data-original')
            pic = pic_node[0] if pic_node else ""
            
            content = "".join(html.xpath('//span[contains(@class, "detail-content")]/text()')).strip()
            
            vod = {
                "vod_id": tid, 
                "vod_name": name, 
                "vod_pic": pic, 
                "type_name": "短剧", 
                "vod_remarks": "", 
                "vod_content": content
            }
            
            source_names = html.xpath('//div[contains(@class, "hl-plays-from")]//a/text()')
            source_lists = html.xpath('//ul[contains(@class, "hl-plays-list")]')
            
            play_from, play_url = [], []
            for i in range(min(len(source_names), len(source_lists))):
                s_name = source_names[i].strip()
                links = source_lists[i].xpath('.//li/a')
                urls = [f"{link.xpath('./text()')[0]}${link.xpath('./@href')[0]}" for link in links]
                if urls:
                    # 判斷是否為「幼稚線路」，如果是則插入到列表最前面
                    if "幼稚" in s_name:
                        play_from.insert(0, s_name)
                        play_url.insert(0, "#".join(urls))
                    else:
                        play_from.append(s_name)
                        play_url.append("#".join(urls))
            
            vod["vod_play_from"] = "$$$".join(play_from) if play_from else "直連"
            vod["vod_play_url"] = "$$$".join(play_url) if play_url else f"播放$ {tid}"
            
            return {"list": [vod]}
        except: return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        # 處理播放地址，有些站點需要補全域名
        playUrl = id
        if not id.startswith('http'):
            playUrl = f"{self.siteUrl}{id}"
        return {"parse": 1, "url": playUrl, "header": ""}

    def searchContent(self, key, quick, pg="1"):
        curr_pg = int(pg)
        url = f"{self.siteUrl}/so-{quote(key)}-{curr_pg}.html"
        try:
            res = requests.get(url, timeout=10, headers=self.header)
            html = etree.HTML(res.text)
            vod_list = []
            nodes = html.xpath('//ul[contains(@class, "hl-one-list")]/li | //ul[contains(@class, "hl-vod-list")]/li')
            for node in nodes:
                try:
                    name = node.xpath('.//a[contains(@class, "hl-item-thumb")]/@title')[0]
                    pic = node.xpath('.//a[contains(@class, "hl-item-thumb")]/@data-original')[0]
                    id = node.xpath('.//a[contains(@class, "hl-item-thumb")]/@href')[0]
                    remark = "".join(node.xpath('.//span[contains(@class, "remarks")]/text()'))
                    vod_list.append({"vod_id": id, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
                except: continue
            return {"list": vod_list}
        except: return {"list": []}