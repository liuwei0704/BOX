# coding=utf-8
import re
import sys
import requests
import json
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "七七影院"

    def init(self, extend=""):
        self.host = "https://www.77qikan.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }

    def homeContent(self, filter):
        result = {"class": [], "list": []}
        # 1. 设置分类列表
        result["class"] = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "5", "type_name": "短剧"}
        ]
        
        # 2. 抓取首页推荐视频
        try:
            res = requests.get(self.host, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 首页通常抓取前两组排版好的视频列表
            items = soup.select('.stui-vodlist li')
            vod_list = []
            for item in items:
                a = item.select_one('a.stui-vodlist__thumb')
                if not a: continue
                
                name = a.get('title', '').strip()
                pic = a.get('data-original', '')
                remarks = a.select_one('span.pic-text').text.strip() if a.select_one('span.pic-text') else ""
                
                vod_list.append({
                    "vod_id": a['href'],
                    "vod_name": name,
                    "vod_pic": self.get_full_url(pic),
                    "vod_remarks": remarks
                })
            
            # 首页展示去重后的前 30 条数据
            result["list"] = vod_list[:30]
        except:
            pass
            
        return result

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg)
        result = {"list": [], "page": pg, "pagecount": pg, "limit": 20, "total": 0}
        
        # 修正 URL 构造逻辑
        if pg == 1:
            url = f"{self.host}/7qikantp/{tid}.html"
        else:
            url = f"{self.host}/7qikantp/{tid}-{pg}.html"
        
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            items = soup.select('ul.stui-vodlist li')
            for item in items:
                a = item.select_one('a.stui-vodlist__thumb')
                if not a: continue
                
                name = a.get('title', '').strip()
                pic = a.get('data-original', '')
                remarks = a.select_one('span.pic-text').text.strip() if a.select_one('span.pic-text') else ""
                
                result["list"].append({
                    "vod_id": a['href'],
                    "vod_name": name,
                    "vod_pic": self.get_full_url(pic),
                    "vod_remarks": remarks
                })
            
            # --- 翻页判定逻辑 ---
            # 如果当前页抓到了数据，说明可能还有下一页
            # 我们强制设置 pagecount 为 pg + 1，这样 APP 就会显示加载更多
            if len(result["list"]) > 0:
                result["pagecount"] = pg + 1
            else:
                # 抓不到数据了，说明到底了
                result["pagecount"] = pg

        except Exception as e:
            pass
            
        return result

    def detailContent(self, ids):
        self.init()
        baseUrl = self.host
        url = baseUrl + ids[0] if ids[0].startswith('/') else ids[0]
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            vod = {
                "vod_id": ids[0],
                "vod_name": soup.find('h1', class_='title').text if soup.find('h1', class_='title') else "",
                "vod_pic": soup.find('img', class_='lazyload').get('data-original', ''),
                "vod_content": soup.find('span', class_='detail-content').text.strip() if soup.find('span', class_='detail-content') else ""
            }

            # 临时存储所有线路数据的列表
            all_line_data = []
            
            groups = soup.find_all('div', class_='stui-pannel_bd')
            for group in groups:
                playlist = group.find('ul', class_='stui-content__playlist')
                if playlist:
                    parent_pannel = group.find_parent('div', class_='stui-pannel')
                    title_tag = parent_pannel.find('h3', class_='title') if parent_pannel else None
                    name = title_tag.text.strip() if title_tag else f"线路{len(all_line_data)+1}"
                    
                    links = playlist.find_all('a')
                    urls = [f"{l.text}${l['href']}" for l in links]
                    
                    # 将线路名和对应的播放列表打包存入
                    all_line_data.append({
                        "name": name,
                        "urls": "#".join(urls)
                    })

            # --- VIP 线路优先排序逻辑 ---
            # 定义你认为应该是第一位的关键词
            vip_keywords = ["VIP", "蓝光", "极速", "高清", "77"]
            
            def get_priority(line_name):
                # 如果匹配到关键词，优先级设为 0（最小，排在最前），否则设为 1
                for kw in vip_keywords:
                    if kw.upper() in line_name.upper():
                        return 0
                return 1

            # 按优先级排序，优先级相同则保持原序
            all_line_data.sort(key=lambda x: get_priority(x['name']))

            # 重新组合成播放器要求的格式
            play_sources = [item['name'] for item in all_line_data]
            play_urls = [item['urls'] for item in all_line_data]

            vod["vod_play_from"] = "$$$".join(play_sources)
            vod["vod_play_url"] = "$$$".join(play_urls)
            
            return {"list": [vod]}
        except Exception as e:
            # print(f"Error: {e}")
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        # 1. 构造搜索 URL
        # 根据 77.txt，搜索入口是 /7qikansc/-------------.html，参数名是 wd
        # 如果是翻页，可能需要根据站点的翻页规则调整，这里先处理第一页和基础搜索
        search_url = f"{self.host}/7qikansc/{key}----------{pg}---.html"
        
        result = {"list": []}
        try:
            # 2. 发起请求
            res = requests.get(search_url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 3. 解析搜索结果列表 (针对 stui-vodlist__media 结构)
            # 源码中每个搜索结果是一个 li，包含 thumb 和 detail 两部分
            items = soup.select('.stui-vodlist__media li')
            
            vod_list = []
            for item in items:
                # 提取图片节点
                a_thumb = item.select_one('a.v-thumb')
                if not a_thumb:
                    continue
                
                # 获取标题和 ID
                name = a_thumb.get('title', '').strip()
                vod_id = a_thumb['href'] # 例如: /7qikandt/216931.html
                
                # 获取图片 (data-original)
                pic = a_thumb.get('data-original', '')
                
                # 获取备注 (如: 全82集 / 已完结)
                remarks_node = a_thumb.select_one('.pic-text')
                remarks = remarks_node.text.strip() if remarks_node else ""
                
                vod_list.append({
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": self.get_full_url(pic),
                    "vod_remarks": remarks
                })
            
            result["list"] = vod_list
            
        except Exception as e:
            # print(f"Search Error: {e}")
            pass
            
        return result

    def playerContent(self, flag, id, vipFlags):
        url = self.get_full_url(id)
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            match = re.search(r'player_aaaa=(.*?)</script>', res.text)
            if match:
                config = json.loads(match.group(1))
                return {"parse": 1, "url": config.get('url', ''), "header": self.headers}
        except:
            pass
        return {"parse": 1, "url": url, "header": self.headers}

    def get_full_url(self, url):
        if not url: return ""
        if url.startswith('//'): return "https:" + url
        if url.startswith('/'): return self.host + url
        return url