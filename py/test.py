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
        return "百思派电影网"
    
    def init(self, extend=""):
        self.host = "https://www.bestpipe.cn"
        pass
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }
    
    def homeContent(self, filter):
        """返回分类列表"""
        result = {}
        classes = [
            {"type_name": "电影", "type_id": "20"},
            {"type_name": "剧集", "type_id": "21"},
            {"type_name": "短剧", "type_id": "24"},
            {"type_name": "动漫", "type_id": "22"},
            {"type_name": "综艺", "type_id": "23"}
        ]
        result["class"] = classes
        return result
    
    def homeVideoContent(self):
        """首页推荐视频"""
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 解析热播推荐部分
            items = root.select('.stui-vodlist li')
            
            for item in items:
                try:
                    a = item.find('a', class_='stui-vodlist__thumb')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
                    
                    # 获取标题
                    vod_name = a.get('title', '')
                    if not vod_name:
                        title_elem = item.find('h4', class_='title')
                        if title_elem:
                            vod_name = title_elem.text.strip()
                    
                    # 获取封面图
                    vod_pic = ""
                    if a.get('data-original'):
                        vod_pic = a['data-original']
                    elif a.get('style'):
                        # 从style中提取背景图片
                        match = re.search(r'url\((.*?)\)', a['style'])
                        if match:
                            vod_pic = match.group(1).strip('"\'')

                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
                    
                    # 获取备注（更新状态）
                    vod_remarks = ""
                    remark_elem = item.find('span', class_='pic-text')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
                    # 获取演员信息
                    vod_actor = ""
                    actor_elem = item.find('p', class_='text')
                    if actor_elem:
                        vod_actor = actor_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception as e:
                    print(f"解析单个视频时出错: {e}")
                    continue
            
            return {"list": videos[:12]}  # 只返回前12个
        except Exception as e:
            print(f"首页视频解析错误: {e}")
            return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类页面内容"""
        try:
            # 构建分类URL
            if int(pg) > 1:
                url = f"{self.host}/vodshow/{tid}-----------{pg}.html"
            else:
                url = f"{self.host}/vodshow/{tid}-----------.html"
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 解析视频列表
            items = root.select('.stui-vodlist li')
            
            for item in items:
                try:
                    a = item.find('a', class_='stui-vodlist__thumb')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
                    
                    # 获取标题
                    vod_name = a.get('title', '')
                    if not vod_name:
                        title_elem = item.find('h4', class_='title')
                        if title_elem:
                            vod_name = title_elem.text.strip()
                    
                    # 获取封面图
                    vod_pic = ""
                    if a.get('data-original'):
                        vod_pic = a['data-original']
                    elif a.get('style'):
                        match = re.search(r'url\((.*?)\)', a['style'])
                        if match:
                            vod_pic = match.group(1).strip('"\'')

                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
                    
                    # 获取备注
                    vod_remarks = ""
                    remark_elem = item.find('span', class_='pic-text')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
                    # 获取演员信息
                    vod_actor = ""
                    actor_elem = item.find('p', class_='text')
                    if actor_elem:
                        vod_actor = actor_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception as e:
                    print(f"分类解析单个视频时出错: {e}")
                    continue
            
            # 分页信息
            pagecount = 1
            pagination = root.find('div', class_='stui-pagination')
            if not pagination:
                pagination = root.find('ul', class_='pagination')
            
            if pagination:
                page_links = pagination.find_all('a')
                page_numbers = []
                for link in page_links:
                    try:
                        text = link.text.strip()
                        if text.isdigit():
                            num = int(text)
                            page_numbers.append(num)
                    except:
                        pass
                if page_numbers:
                    pagecount = max(page_numbers)
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount if pagecount > 0 else 1,
                "limit": 20,
                "total": len(videos) * (pagecount if pagecount > 0 else 1)
            }
        except Exception as e:
            print(f"分类页面解析错误: {e}")
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }
    
    def detailContent(self, ids):
        """视频详情页"""
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                url = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
            else:
                url = vod_id
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 解析基本信息
            vod_name = ""
            title_elem = root.find('h1') or root.find('h2')
            if title_elem:
                vod_name = title_elem.text.strip()
            
            # 封面图
            vod_pic = ""
            cover_img = root.find('img', class_=re.compile('thumb|cover|poster'))
            if cover_img and cover_img.get('src'):
                vod_pic = cover_img['src']
            elif cover_img and cover_img.get('data-original'):
                vod_pic = cover_img['data-original']
            
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
            
            # 描述
            vod_content = ""
            desc_elem = root.find('div', class_=re.compile('content|intro|description'))
            if desc_elem:
                vod_content = desc_elem.text.strip()
            
            # 播放列表解析
            play_from_list = []
            play_url_list = []
            
            # 查找播放列表
            play_sections = root.find_all('div', class_=re.compile('play|episode'))
            
            if not play_sections:
                # 备用方法：查找所有包含播放链接的div
                play_sections = root.find_all('div', id=re.compile('play'))
            
            for section in play_sections:
                # 播放源名称
                source_name = "默认播放源"
                source_title = section.find('h3') or section.find('h4') or section.find('span', class_=re.compile('title'))
                if source_title:
                    source_name = source_title.text.strip()
                
                # 播放列表
                episodes = []
                play_links = section.find_all('a', href=re.compile(r'vodplay|play|watch'))
                
                if not play_links:
                    # 查找所有a标签
                    play_links = section.find_all('a', href=True)
                
                for link in play_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    # 过滤掉非播放链接
                    if 'vodplay' in href or 'play' in href or 'watch' in href or 'detail' not in href:
                        ep_title = link.text.strip()
                        if not ep_title:
                            ep_title = f"第{len(episodes)+1}集"
                        
                        if href and not href.startswith('http'):
                            href = self.host + href if href.startswith('/') else self.host + '/' + href
                        
                        if ep_title and href:
                            episodes.append(f"{ep_title}${href}")
                
                if episodes:
                    play_from_list.append(source_name)
                    play_url_list.append("#".join(episodes))
            
            # 如果没找到播放列表，尝试直接使用详情页链接
            if not play_from_list:
                episodes = [f"播放${url}"]
                play_from_list = ["默认"]
                play_url_list = ["#".join(episodes)]
            
            # 构建结果
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }
            
            return {"list": [video]}
            
        except Exception as e:
            print(f"详情页解析错误: {e}")
            import traceback
            traceback.print_exc()
            
            video = {
                "vod_id": ids[0],
                "vod_name": "加载失败",
                "vod_pic": "",
                "vod_content": "",
                "vod_play_from": "默认",
                "vod_play_url": f"播放${self.host}"
            }
            return {"list": [video]}
    
    def searchContent(self, key, quick, pg=1):
        """搜索功能"""
        try:
            encoded_key = urllib.parse.quote(key)
            search_url = f"{self.host}/vodsearch/{encoded_key}-------------.html"
            
            if int(pg) > 1:
                search_url = f"{self.host}/vodsearch/{encoded_key}-------------{pg}.html"
            
            rsp = self.fetch(search_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 解析搜索结果
            result_items = root.select('.stui-vodlist li')
            
            for item in result_items:
                try:
                    a = item.find('a', class_='stui-vodlist__thumb')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
                    
                    # 标题
                    vod_name = a.get('title', '')
                    if not vod_name:
                        title_elem = item.find('h4', class_='title')
                        if title_elem:
                            vod_name = title_elem.text.strip()
                    
                    # 封面
                    vod_pic = ""
                    if a.get('data-original'):
                        vod_pic = a['data-original']
                    elif a.get('style'):
                        match = re.search(r'url\((.*?)\)', a['style'])
                        if match:
                            vod_pic = match.group(1).strip('"\'')
                    
                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
                    
                    # 备注
                    vod_remarks = ""
                    remark_elem = item.find('span', class_='pic-text')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception as e:
                    print(f"搜索解析单个结果时出错: {e}")
                    continue
            
            # 分页信息
            pagecount = 1
            pagination = root.find('div', class_='stui-pagination')
            if not pagination:
                pagination = root.find('ul', class_='pagination')
            
            if pagination:
                page_links = pagination.find_all('a')
                page_numbers = []
                for link in page_links:
                    try:
                        text = link.text.strip()
                        if text.isdigit():
                            num = int(text)
                            page_numbers.append(num)
                    except:
                        pass
                if page_numbers:
                    pagecount = max(page_numbers)
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount if pagecount > 0 else 1,
                "limit": 20,
                "total": len(videos) * (pagecount if pagecount > 0 else 1)
            }
            
        except Exception as e:
            print(f"搜索解析错误: {e}")
            return {"list": []}
    
    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        result = {}
        
        try:
            if not id.startswith('http'):
                play_url = self.host + id if id.startswith('/') else self.host + '/' + id
            else:
                play_url = id
            
            rsp = self.fetch(play_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 尝试解析播放地址
            video_url = None
            
            # 1. 查找iframe
            iframe = root.find('iframe')
            if iframe and iframe.get('src'):
                video_url = iframe['src']
            
            # 2. 查找video标签
            if not video_url:
                video_tag = root.find('video')
                if video_tag and video_tag.get('src'):
                    video_url = video_tag['src']
            
            # 3. 查找source标签
            if not video_url:
                source_tag = root.find('source')
                if source_tag and source_tag.get('src'):
                    video_url = source_tag['src']
            
            # 4. 查找javascript中的播放地址
            if not video_url:
                script_tags = root.find_all('script')
                for script in script_tags:
                    if script.string:
                        # 尝试匹配各种视频地址格式
                        patterns = [
                            r'url:\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'src:\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'file:\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'player_data[\s\S]*?url[\s\S]*?["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']'
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, script.string)
                            if match:
                                video_url = match.group(1)
                                break
            
            if video_url:
                result["parse"] = 0
                result["url"] = video_url
                result["header"] = self.header()
            else:
                # 如果找不到直接播放地址，让TVBox解析
                result["parse"] = 1
                result["url"] = play_url
                result["header"] = self.header()
            
        except Exception as e:
            print(f"播放地址解析错误: {e}")
            result["parse"] = 1
            result["url"] = id
            result["header"] = self.header()
        
        return result
    
    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        video_formats = ['.m3u8', '.mp4', '.avi', '.mkv', '.flv', '.ts', '.webm']
        return any(fmt in url.lower() for fmt in video_formats)
    
    def localProxy(self, params):
        """本地代理"""
        return [200, "video/MP2T", ""]
