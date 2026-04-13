import json
import re
import requests
from urllib.parse import quote
from lxml import etree

class Spider():
    def getName(self):
        return "果果短剧"

    def init(self, extend=""):
        self.siteUrl = "https://www.ggduanju.com"

    def getDependence(self):
        return []

    def isVideoCanPlay(self):
        return ""

    def isVideoStatus(self, vod_id, name, cnt):
        return True

    def homeContent(self, filter):
        res = requests.get(self.siteUrl, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        html = etree.HTML(res.text)
        classes = []
        nodes = html.xpath('//ul[contains(@class, "hl-nav")]/li/a[contains(@href, ".html") or contains(@href, "/duanju/")]')
        for node in nodes:
            try:
                name = node.xpath("./text()")[0]
                if name in ["首页", "留言"]: continue
                tid = node.xpath("./@href")[0].split("/")[-1].split(".")[0]
                classes.append({"type_name": name, "type_id": tid})
            except: continue
        return {"class": classes}

    def homeVideoContent(self):
        try:
            res = requests.get(self.siteUrl, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
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
        clean_tid = tid[1:] if tid.startswith('l') and tid != "lduanju" else tid
        if curr_pg == 1:
            url = f"{self.siteUrl}/{tid}/" if tid == "duanju" else f"{self.siteUrl}/{tid}.html"
        else:
            url = f"{self.siteUrl}/Category{clean_tid}-{'_' * 7}{curr_pg}___.html"
        try:
            res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            html = etree.HTML(res.text)
            vod_list = []
            nodes = html.xpath('//ul[contains(@class, "hl-vod-list")]/li | //div[contains(@class, "hl-list-item")]')
            for node in nodes:
                try:
                    name = node.xpath('.//a/@title')[0]
                    pic = node.xpath('.//a/@data-original')[0]
                    id = node.xpath('.//a/@href')[0]
                    remark_node = node.xpath('.//span[contains(@class, "remarks")]/text()')
                    remark = remark_node[0] if remark_node else ""
                    vod_list.append({"vod_id": id, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
                except: continue
            last_page = curr_pg + 1 if len(vod_list) >= 10 else curr_pg
            return {"list": vod_list, "page": curr_pg, "pagecount": last_page, "limit": 20, "total": last_page * 20}
        except: return {"list": []}

    def detailContent(self, ids):
        id = ids[0]
        url = f"{self.siteUrl}{id}"
        try:
            res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            html = etree.HTML(res.text)
            
            # 基础信息解析
            name = html.xpath('//h2[contains(@class, "hl-dc-title")]/text()')[0]
            pic = html.xpath('//div[contains(@class, "hl-dc-pic")]//span/@data-original')[0]
            
            # 详情列表解析
            info_list = html.xpath('//div[contains(@class, "hl-full-box")]//li')
            type_name = ""
            remarks = ""
            content = ""
            for info in info_list:
                text = "".join(info.xpath(".//text()")).replace("\xa0", "")
                if "类型：" in text: type_name = text.replace("类型：", "")
                if "状态：" in text: remarks = text.replace("状态：", "")
                if "简介：" in text: content = text.replace("简介：", "").strip()

            vod = {
                "vod_id": id,
                "vod_name": name,
                "vod_pic": pic,
                "type_name": type_name,
                "vod_remarks": remarks,
                "vod_content": content
            }

            # 播放源解析 (Conch 模板特有结构)
            source_names = html.xpath('//div[contains(@class, "hl-plays-from")]//a/text()')
            source_lists = html.xpath('//ul[contains(@class, "hl-plays-list")]')
            
            play_from = []
            play_url = []
            
            for i in range(min(len(source_names), len(source_lists))):
                s_name = source_names[i].strip()
                if not s_name: continue
                
                links = source_lists[i].xpath('.//li/a')
                urls = []
                for link in links:
                    p_name = link.xpath('./text()')[0]
                    p_url = link.xpath('./@href')[0]
                    urls.append(f"{p_name}${p_url}")
                
                if urls:
                    play_from.append(s_name)
                    play_url.append("#".join(urls))

            vod["vod_play_from"] = "$$$".join(play_from)
            vod["vod_play_url"] = "$$$".join(play_url)
            return {"list": [vod]}
        except Exception as e:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        return {"parse": 1, "url": f"{self.siteUrl}{id}", "header": ""}

    def searchContent(self, key, quick, pg="1"):
        curr_pg = int(pg)
        url = f"{self.siteUrl}/so-{quote(key)}-{curr_pg}.html"
        try:
            res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            html = etree.HTML(res.text)
            vod_list = []
            nodes = html.xpath('//ul[contains(@class, "hl-one-list")]/li | //ul[contains(@class, "hl-vod-list")]/li')
            for node in nodes:
                try:
                    name = node.xpath('.//a[contains(@class, "hl-item-thumb")]/@title')[0]
                    pic = node.xpath('.//a[contains(@class, "hl-item-thumb")]/@data-original')[0]
                    id = node.xpath('.//a[contains(@class, "hl-item-thumb")]/@href')[0]
                    remark_node = node.xpath('.//span[contains(@class, "remarks")]/text()')
                    remark = remark_node[0] if remark_node else ""
                    vod_list.append({"vod_id": id, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
                except: continue
            return {"list": vod_list}
        except: return {"list": []}