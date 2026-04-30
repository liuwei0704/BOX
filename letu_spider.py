# coding=utf-8
import sys
import os
import re
import json
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    def getName(self):
        return "乐兔影视"
    
    def init(self, extend=""):
        self.host = "https://www.letu.me"
        pass
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host,
        }
    
    def homeContent(self, filter):
        result = {}
        classes = [
            {"type_name": "电影", "type_id": "1"},
            {"type_name": "连续剧", "type_id": "2"},
            {"type_name": "综艺", "type_id": "3"},
            {"type_name": "动漫", "type_id": "4"},
            {"type_name": "短剧", "type_id": "5"},
        ]
        result["class"] = classes
        return result
    
    def homeVideoContent(self):
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            items = root.select('.vodlist_item')
            for item in items[:30]:
                a = item.select_one('.vodlist_thumb')
                if not a:
                    continue
                
                vod_id = a.get('href', '')
                vod_name = a.get('title', '')
                
                if not vod_name:
                    title_elem = item.select_one('.vodlist_title a')
                    if title_elem:
                        vod_name = title_elem.text.strip()
                
                vod_pic = a.get('data-original') or a.get('src', '')
                
                remarks = []
                pic_text = a.select_one('.pic_text')
                if pic_text:
                    remarks.append(pic_text.text.strip())
                else:
                    year_elem = a.select_one('.voddate_year')
                    type_elem = a.select_one('.voddate_type')
                    if year_elem:
                        remarks.append(year_elem.text.strip())
                    if type_elem:
                        remarks.append(type_elem.text.strip())
                
                videos.append({
                    "vod_id": self.regUrl(vod_id),
                    "vod_name": vod_name,
                    "vod_pic": self.regUrl(vod_pic),
                    "vod_remarks": " | ".join(remarks)
                })
            
            return {"list": videos}
        except Exception as e:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        pg = int(pg)
        url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            
        try:
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 分类页结构: li.vodlist_item
            items = root.select('.vodlist_item')
            for item in items:
                a = item.select_one('.vodlist_thumb')
                if not a:
                    continue
                vod_id = a.get('href', '')
                vod_name = a.get('title', '')
                if not vod_name:
                    title_elem = item.select_one('.vodlist_title a')
                    if title_elem:
                        vod_name = title_elem.text.strip()
                
                vod_pic = a.get('data-original') or a.get('src', '')
                
                remarks = []
                pic_text = a.select_one('.pic_text')
                if pic_text:
                    remarks.append(pic_text.text.strip())
                
                videos.append({
                    "vod_id": self.regUrl(vod_id),
                    "vod_name": vod_name,
                    "vod_pic": self.regUrl(vod_pic),
                    "vod_remarks": " | ".join(remarks)
                })

            # 分页：查找 ul.page 中的数字链接，取最大值
            page_count = pg
            pagination = root.select_one('ul.page')
            if pagination:
                btns = pagination.find_all('a')
                for btn in btns:
                    btn_text = btn.text.strip()
                    if btn_text.isdigit():
                        page_count = max(page_count, int(btn_text))

            return {
                "list": videos,
                "page": pg,
                "pagecount": page_count,
                "limit": 30,
                "total": 30 * page_count
            }
        except Exception as e:
            return {"list": [], "page": pg, "pagecount": pg}

    def detailContent(self, ids):
        vod_id = ids[0]
        url = self.regUrl(vod_id)
        
        try:
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 标题
            vod_name = ""
            h2 = root.select_one('.content_detail .title')
            if h2:
                vod_name = h2.text.strip()
            if not vod_name:
                h1 = root.find('h1')
                if h1:
                    vod_name = h1.text.strip()
            
            # 简介
            vod_content = ""
            content_div = root.select_one('.content_desc span')
            if content_div:
                vod_content = content_div.text.strip()
            
            play_from = []
            play_urls = []
            
            # 解析播放线路：.play_source_tab a
            source_tabs = root.select('.play_source_tab a')
            # 解析剧集列表：对应的 .play_list_box .content_playlist li a
            play_boxes = root.select('.play_list_box')
            
            for idx, tab in enumerate(source_tabs):
                line_name = tab.text.strip()
                play_from.append(line_name)
                
                episodes = []
                if idx < len(play_boxes):
                    links = play_boxes[idx].select('.content_playlist li a')
                    for link in links:
                        ep_name = link.text.strip()
                        ep_href = link.get('href', '')
                        episodes.append(f"{ep_name}${self.regUrl(ep_href)}")
                
                play_urls.append("#".join(episodes))
            
            video = {
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_urls),
                "vod_content": vod_content
            }
            return {"list": [video]}
        except Exception as e:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        pg = int(pg)
        encoded_key = urllib.parse.quote(key)
        url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            
        try:
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 搜索页结构: li.searchlist_item
            items = root.select('.searchlist_item')
            for item in items:
                a = item.select_one('.searchlist_img a')
                if not a:
                    continue
                vod_id = a.get('href', '')
                vod_name = a.get('title', '')
                if not vod_name:
                    title_elem = item.select_one('.vodlist_title a')
                    if title_elem:
                        vod_name = title_elem.text.strip()
                
                vod_pic = a.get('data-original') or a.get('src', '')
                
                remarks = []
                pic_text = a.select_one('.pic_text')
                if pic_text:
                    remarks.append(pic_text.text.strip())
                
                videos.append({
                    "vod_id": self.regUrl(vod_id),
                    "vod_name": vod_name,
                    "vod_pic": self.regUrl(vod_pic),
                    "vod_remarks": " | ".join(remarks)
                })
            
            # 搜索分页: ul.page
            page_count = pg
            pagination = root.select_one('ul.page')
            if pagination:
                btns = pagination.find_all('a')
                for btn in btns:
                    btn_text = btn.text.strip()
                    if btn_text.isdigit():
                        page_count = max(page_count, int(btn_text))
            
            return {"list": videos, "page": pg, "pagecount": page_count}
        except Exception as e:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        url = self.regUrl(id)
        result = {"parse": 1, "url": url, "header": self.header()}
        
        try:
            rsp = self.fetch(url, headers=self.header())
            m3u8_match = re.search(r'["\']([^"\']+\.m3u8[^"\']*)["\']', rsp.text)
            if not m3u8_match:
                m3u8_match = re.search(r'data-src="([^"]+\.m3u8[^"]*)"', rsp.text)
            if not m3u8_match:
                m3u8_match = re.search(r'url:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', rsp.text)
            if m3u8_match:
                result["parse"] = 0
                result["url"] = m3u8_match.group(1)
        except:
            pass
            
        return result

    def regUrl(self, url):
        if not url:
            return ""
        if url.startswith('//'):
            return "https:" + url
        if url.startswith('/'):
            return self.host + url
        return url