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
        return "星辰影院"

    def init(self, extend=""):
        self.host = "https://www.hffswz.com"
        pass

    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
            'Referer': self.host
        }

    def homeContent(self, filter):
        result = {}
        classes = [
            {"type_name": "电影", "type_id": "/vodtype/1.html"},
            {"type_name": "电视剧", "type_id": "/vodtype/2.html"},
            {"type_name": "综艺", "type_id": "/vodtype/3.html"},
            {"type_name": "动漫", "type_id": "/vodtype/4.html"},
            {"type_name": "短剧", "type_id": "/vodtype/36.html"},
            {"type_name": "最近更新", "type_id": "/label/new.html"},
            {"type_name": "排行榜", "type_id": "/label/ranking.html"}
        ]
        result["class"] = classes
        return result

    def homeVideoContent(self):
        rsp = self.fetch(self.host, headers=self.header())
        root = BeautifulSoup(rsp.text, 'html.parser')
        videos = []
        
        # 查找热播推荐
        hot_items = root.select('ul.video-small-list li')
        for item in hot_items:
            a = item.find('a', class_='video-link')
            if not a:
                continue
                
            vod_id = a.get('href', '')
            if vod_id and not vod_id.startswith('http'):
                vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
            
            # 获取图片
            vod_pic = ""
            img_div = item.find('div', class_='item-pic')
            if img_div and img_div.get('data-original'):
                vod_pic = img_div['data-original']
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
            
            # 获取标题
            vod_name = ""
            h2 = item.find('h2', class_='video-con-tit')
            if h2:
                vod_name = h2.text.strip()
            
            # 获取备注
            vod_remarks = ""
            duration_div = item.find('div', class_='video-duration')
            if duration_div:
                vod_remarks = duration_div.text.strip()
            
            if vod_name and vod_id:
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })
        
        return {"list": videos}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            # 从tid中提取分类ID（如/vodtype/1.html -> 1）
            class_id_match = re.search(r'/vodtype/(\d+)\.html', tid)
            if class_id_match:
                class_id = class_id_match.group(1)
            else:
                # 如果是其他分类，如/label/new.html
                class_id_match = re.search(r'/(\w+)/(\w+)\.html', tid)
                if class_id_match:
                    class_id = class_id_match.group(2)
                else:
                    class_id = "1"  # 默认值
            
            # 构建分类页URL - 从HTML中可以看到格式是 /vodtype/6-2.html
            if int(pg) > 1:
                # 第2页及以后：/vodtype/6-2.html
                url = f"{self.host}/vodtype/{class_id}-{pg}.html"
            else:
                # 第1页：/vodtype/6.html 或保持原始tid
                url = self.host + tid
            
            print(f"分类页URL: {url}")
            
            rsp = self.fetch(url, headers=self.header())
            if rsp.status_code != 200:
                print(f"URL {url} 返回状态码: {rsp.status_code}")
                return {
                    "list": [],
                    "page": int(pg),
                    "pagecount": 1,
                    "limit": 20,
                    "total": 0
                }
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 方法1：查找轮播图形式的短剧列表
            video_slide_list = root.find('div', class_='video-slide-list')
            if video_slide_list:
                print("找到轮播图形式的短剧列表")
                slide_items = video_slide_list.find_all('li', class_='swiper-slide')
                for item in slide_items:
                    a = item.find('a', class_='video-link')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    vod_pic = ""
                    img_div = item.find('div', class_='item-pic')
                    if img_div and img_div.get('data-background'):
                        vod_pic = img_div['data-background']
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
                    
                    vod_name = ""
                    h2 = item.find('h2', class_='video-con-tit')
                    if h2:
                        vod_name = h2.text.strip()
                    
                    vod_remarks = ""
                    duration_div = item.find('div', class_='video-duration')
                    if duration_div:
                        vod_remarks = duration_div.text.strip()
                    
                    if vod_name and vod_id:
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": vod_name,
                            "vod_pic": vod_pic,
                            "vod_remarks": vod_remarks
                        })
            
            # 方法2：查找常规视频列表 - 主要视频列表
            print("尝试查找常规视频列表")
            video_items = root.select('ul.video-film-list li .video-item')
            if not video_items:
                video_items = root.select('ul.video-list li .video-item')
            
            for item in video_items:
                a = item.find('a', class_='video-link')
                if not a:
                    continue
                
                vod_id = a.get('href', '')
                if vod_id and not vod_id.startswith('http'):
                    vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                
                vod_pic = ""
                img_div = item.find('div', class_='item-pic')
                if img_div:
                    if img_div.get('data-original'):
                        vod_pic = img_div['data-original']
                    elif img_div.get('data-background'):
                        vod_pic = img_div['data-background']
                    elif img_div.find('img') and img_div.find('img').get('src'):
                        vod_pic = img_div.find('img')['src']
                    elif img_div.find('img') and img_div.find('img').get('data-src'):
                        vod_pic = img_div.find('img')['data-src']
                
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
                
                vod_name = ""
                h2 = item.find('h2', class_='video-con-tit')
                if h2:
                    vod_name = h2.text.strip()
                
                vod_remarks = ""
                duration_div = item.find('div', class_='video-duration')
                if duration_div:
                    vod_remarks = duration_div.text.strip()
                
                if vod_name and vod_id:
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
            
            # 去重
            unique_videos = []
            seen_ids = set()
            for video in videos:
                if video['vod_id'] not in seen_ids:
                    seen_ids.add(video['vod_id'])
                    unique_videos.append(video)
            
            videos = unique_videos
            
            # 尝试获取总页数
            pagecount = 1
            
            # 查找分页元素 - 从HTML中可以看到有<ul class="ewave-page">
            page_div = root.find('ul', class_='ewave-page')
            if page_div:
                print("找到ewave-page分页")
                
                # 方法1：从分页文本中提取（如"2/181"）
                page_text_elem = page_div.find('li', class_='hidden-md hidden-lg hidden-xl hidden-xxl active')
                if page_text_elem:
                    page_text = page_text_elem.find('span', class_='num')
                    if page_text:
                        page_match = re.search(r'(\d+)/(\d+)', page_text.text.strip())
                        if page_match:
                            pagecount = int(page_match.group(2))
                            print(f"从分页文本找到总页数: {pagecount}")
                
                # 方法2：如果没有找到文本，从分页链接中提取
                if pagecount == 1:
                    page_links = page_div.find_all('a')
                    max_page = 1
                    for link in page_links:
                        href = link.get('href', '')
                        text = link.text.strip()
                        
                        if href:
                            # 从URL中提取页码
                            patterns = [
                                r'/vodtype/\d+-(\d+)\.html$',
                                r'[-_](\d+)\.html$',
                                r'[?&]page=(\d+)',
                                r'[-/]page/(\d+)',
                                r'[-/](\d+)/?$'
                            ]
                            for pattern in patterns:
                                match = re.search(pattern, href)
                                if match:
                                    try:
                                        page_num = int(match.group(1))
                                        if page_num > max_page:
                                            max_page = page_num
                                    except:
                                        pass
                        
                        if text and text.isdigit():
                            try:
                                page_num = int(text)
                                if page_num > max_page:
                                    max_page = page_num
                            except:
                                pass
                    
                    if max_page > 1:
                        pagecount = max_page
                        print(f"从分页链接找到最大页数: {pagecount}")
            
            # 方法3：从script标签中获取总数量
            if pagecount == 1:
                scripts = root.find_all('script')
                for script in scripts:
                    if script.string and 'ewave-total' in script.string:
                        total_match = re.search(r'ewave-total["\']?[^}]*?(\d+)', script.string)
                        if total_match:
                            total = int(total_match.group(1))
                            # 假设每页24个结果（从HTML中可以看到每页24个）
                            pagecount = (total + 23) // 24
                            print(f"从script中找到总记录数 {total}，计算页数: {pagecount}")
                            break
            
            # 如果没有找到分页信息，但有数据，尝试设置合理的页数
            if videos and pagecount == 1 and int(pg) == 1:
                # 检查是否有"下一页"链接
                next_link = root.find('a', text=re.compile(r'下一页|下一頁|>|»'))
                if next_link or len(videos) >= 20:
                    pagecount = 999
                else:
                    pagecount = 1
            
            print(f"分类页解析结果: 找到 {len(videos)} 个视频，当前第 {pg} 页，共 {pagecount} 页")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 20,
                "total": 9999 if pagecount == 999 else pagecount * 20
            }
            
        except Exception as e:
            print(f"分类页面解析错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }

    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                url = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
            else:
                url = vod_id
            
            print(f"详情页URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 获取影片名称
            vod_name = "未知"
            h1_tag = root.find('h1', class_='media-title')
            if h1_tag:
                vod_name = h1_tag.text.strip()
            
            # 获取影片图片
            vod_pic = ""
            img_tag = root.find('div', class_='detail-img')
            if img_tag:
                img = img_tag.find('img')
                if img and img.get('src'):
                    vod_pic = img['src']
                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else self.host + vod_pic
            
            # 获取影片描述
            vod_content = ""
            
            # 获取影片信息（年份、演员、导演、地区）
            vod_year = ""
            vod_actor = ""
            vod_director = ""
            vod_area = ""
            vod_remarks = ""
            
            # 从详情页的desc列表中获取信息
            desc_items = root.find_all('li', class_=re.compile(r'^col-xs-'))
            for item in desc_items:
                text = item.text.strip()
                icon = item.find('i')
                if icon:
                    icon_class = icon.get('class', [])
                    
                    if 'fa-user-o' in ' '.join(icon_class) and '主演' in text:
                        vod_actor = text.replace('主演：', '').replace('未知', '').strip()
                    elif 'fa-user-o' in ' '.join(icon_class) and '导演' in text:
                        vod_director = text.replace('导演：', '').replace('未知', '').strip()
                    elif 'fa-calendar' in ' '.join(icon_class):
                        vod_year = text.replace('年份：', '').strip()
                    elif 'fa-map-marker' in ' '.join(icon_class):
                        vod_area = text.replace('地区：', '').strip()
                    elif 'fa-dedent' in ' '.join(icon_class):
                        vod_remarks = text.replace('状态：', '').strip()
            
            # 解析播放源和播放列表
            play_from_list = []
            play_url_list = []
            
            # 查找片源选择部分
            player_from_box = root.find('div', class_='player-from-box')
            if player_from_box:
                source_tabs = player_from_box.find_all('li', class_='ewave-tab')
                for tab in source_tabs:
                    if tab.get('data-target'):
                        play_source_name = tab.text.strip()
                        
                        target_id = tab['data-target'].replace('#', '')
                        playlist_div = root.find('div', id=target_id)
                        if playlist_div:
                            episode_links = []
                            play_items = playlist_div.find_all('li', class_='ewave-playlist-item')
                            for item in play_items:
                                a_tag = item.find('a')
                                if a_tag:
                                    href = a_tag.get('href', '')
                                    title = a_tag.text.strip()
                                    
                                    if href and title:
                                        if not href.startswith('http'):
                                            if href.startswith('/'):
                                                href = self.host + href
                                            else:
                                                href = self.host + '/' + href
                                        
                                        title = title.replace('$', '').replace('#', '')
                                        episode_links.append(f"{title}${href}")
                            
                            if episode_links:
                                play_from_list.append(play_source_name)
                                play_url_list.append("#".join(episode_links))
            
            # 如果没有找到播放源，尝试直接查找播放列表
            if not play_from_list:
                playlist_div = root.find('div', class_='ep-list-box')
                if playlist_div:
                    episode_links = []
                    play_items = playlist_div.find_all('a', href=re.compile(r'/vodplay/'))
                    for a_tag in play_items:
                        href = a_tag.get('href', '')
                        title = a_tag.text.strip()
                        
                        if href and title:
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = self.host + href
                                else:
                                    href = self.host + '/' + href
                            
                            title = title.replace('$', '').replace('#', '')
                            episode_links.append(f"{title}${href}")
                    
                    if episode_links:
                        play_from_list = ["高清资源"]
                        play_url_list = ["#".join(episode_links)]
            
            # 如果还是没有找到，使用备用方案
            if not play_from_list:
                play_from_list = ["默认线路"]
                play_url_list = [f"第1集${url}"]
            
            # 构建完整的影片信息
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": vod_year,
                "vod_actor": vod_actor,
                "vod_director": vod_director,
                "vod_area": vod_area,
                "vod_remarks": vod_remarks,
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }
            
            print(f"播放线路: {play_from_list}")
            print(f"找到 {len(play_url_list[0].split('#')) if play_url_list else 0} 个播放链接")
            return {"list": [video]}
            
        except Exception as e:
            print(f"详情页解析错误: {e}")
            import traceback
            traceback.print_exc()
            video = {
                "vod_id": ids[0],
                "vod_name": "影片详情加载失败",
                "vod_pic": "",
                "vod_content": "",
                "vod_play_from": "默认线路",
                "vod_play_url": f"第1集${self.host}"
            }
            return {"list": [video]}

    def searchContent(self, key, quick, pg=1):
        try:
            # 编码搜索关键词
            encoded_key = urllib.parse.quote(key)
            
            # 构建搜索URL - 根据提供的HTML，搜索URL格式为：
            # /vodsearch/我----------1---.html (第1页)
            # /vodsearch/我----------2---.html (第2页)
            # URL中的模式似乎是：/vodsearch/{关键词}----------{页码}---.html
            
            # 首先尝试原始格式
            search_url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            
            # 备用格式：使用参数形式
            backup_url = f"{self.host}/vodsearch/-------------.html?wd={encoded_key}"
            if int(pg) > 1:
                backup_url += f"&page={pg}"
            
            print(f"搜索URL尝试1: {search_url}")
            print(f"搜索URL备用: {backup_url}")
            
            # 首先尝试第一种格式
            rsp = self.fetch(search_url, headers=self.header())
            
            # 检查是否有效
            if rsp.status_code != 200 or "搜索结果" not in rsp.text:
                print("第一种URL格式无效，尝试备用格式")
                rsp = self.fetch(backup_url, headers=self.header())
                search_url = backup_url
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 方法1：查找搜索结果的detail-search格式（从提供的HTML看）
            detail_search = root.find('div', class_='detail-search')
            if detail_search:
                print("找到detail-search格式的搜索结果")
                detail_wraps = detail_search.find_all('div', class_='detail-wrap')
                
                for detail_wrap in detail_wraps:
                    # 获取链接
                    detail_img_link = detail_wrap.find('a', class_='detail-img-link')
                    if not detail_img_link:
                        continue
                    
                    vod_id = detail_img_link.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取图片
                    vod_pic = ""
                    detail_img = detail_wrap.find('div', class_='detail-img')
                    if detail_img and detail_img.get('data-original'):
                        vod_pic = detail_img['data-original']
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
                    
                    # 获取标题
                    vod_name = ""
                    media_title = detail_wrap.find('h2', class_='media-title')
                    if media_title:
                        vod_name = media_title.text.strip()
                    
                    # 获取年份和地区信息
                    vod_year = ""
                    vod_area = ""
                    vod_actor = ""
                    
                    desc_list = detail_wrap.find('ul', class_='desc')
                    if desc_list:
                        desc_items = desc_list.find_all('li')
                        if len(desc_items) > 0:
                            # 第一个li通常是"年份 / 地区"
                            year_area = desc_items[0].text.strip()
                            if '/' in year_area:
                                parts = year_area.split('/')
                                if len(parts) >= 2:
                                    vod_year = parts[0].strip()
                                    vod_area = parts[1].strip()
                        
                        if len(desc_items) > 1:
                            # 第二个li可能是主演信息
                            actor_text = desc_items[1].text.strip()
                            if '主演：' in actor_text:
                                vod_actor = actor_text.replace('主演：', '').strip()
                            elif actor_text and actor_text != '未知':
                                vod_actor = actor_text
                    
                    # 获取备注信息（可能从简介中提取）
                    vod_remarks = ""
                    
                    if vod_name and vod_id:
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": vod_name,
                            "vod_pic": vod_pic,
                            "vod_remarks": vod_remarks,
                            "vod_year": vod_year,
                            "vod_area": vod_area,
                            "vod_actor": vod_actor
                        })
            
            # 方法2：如果没有找到detail-search，尝试常规视频列表
            if not videos:
                print("尝试查找常规视频列表格式")
                list_selectors = [
                    'ul.video-film-list li',
                    'ul.video-small-list li',
                    'ul.video-list li',
                    'div.video-item'
                ]
                
                for selector in list_selectors:
                    items = root.select(selector)
                    if items:
                        print(f"使用选择器 '{selector}' 找到 {len(items)} 个项目")
                        for item in items:
                            a = item.find('a', class_='video-link')
                            if not a:
                                continue
                            
                            vod_id = a.get('href', '')
                            if vod_id and not vod_id.startswith('http'):
                                vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                            
                            vod_pic = ""
                            img_div = item.find('div', class_='item-pic')
                            if img_div:
                                if img_div.get('data-original'):
                                    vod_pic = img_div['data-original']
                                elif img_div.get('data-background'):
                                    vod_pic = img_div['data-background']
                                elif img_div.find('img') and img_div.find('img').get('src'):
                                    vod_pic = img_div.find('img')['src']
                            
                            if vod_pic and not vod_pic.startswith('http'):
                                vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
                            
                            vod_name = ""
                            h2 = item.find('h2', class_='video-con-tit')
                            if h2:
                                vod_name = h2.text.strip()
                            
                            vod_remarks = ""
                            duration_div = item.find('div', class_='video-duration')
                            if duration_div:
                                vod_remarks = duration_div.text.strip()
                            
                            if vod_name and vod_id:
                                videos.append({
                                    "vod_id": vod_id,
                                    "vod_name": vod_name,
                                    "vod_pic": vod_pic,
                                    "vod_remarks": vod_remarks
                                })
                        break
            
            # 尝试获取总页数
            pagecount = 1
            
            # 查找分页信息 - 搜索页有特殊的ewave-page类
            page_div = root.find('ul', class_='ewave-page')
            if page_div:
                print("找到ewave-page分页")
                # 从HTML中可以看到有"2/988"这样的文本
                page_text = page_div.text.strip()
                page_match = re.search(r'(\d+)/(\d+)', page_text)
                if page_match:
                    pagecount = int(page_match.group(2))
                    print(f"从分页文本找到总页数: {pagecount}")
                else:
                    # 查找所有分页链接
                    page_links = page_div.find_all('a')
                    max_page = 1
                    for link in page_links:
                        href = link.get('href', '')
                        text = link.text.strip()
                        
                        if href:
                            # 从URL中提取页码
                            patterns = [
                                r'----------(\d+)---\.html$',
                                r'[?&]page=(\d+)',
                                r'[-/](\d+)\.html$'
                            ]
                            for pattern in patterns:
                                match = re.search(pattern, href)
                                if match:
                                    try:
                                        page_num = int(match.group(1))
                                        if page_num > max_page:
                                            max_page = page_num
                                    except:
                                        pass
                        
                        if text and text.isdigit():
                            try:
                                page_num = int(text)
                                if page_num > max_page:
                                    max_page = page_num
                            except:
                                pass
                    
                    if max_page > 1:
                        pagecount = max_page
            
            # 如果还是没有找到分页信息，检查script中的总页数
            if pagecount == 1:
                scripts = root.find_all('script')
                for script in scripts:
                    if script.string and 'ewave-total' in script.string:
                        # 查找总记录数，然后计算页数
                        total_match = re.search(r'ewave-total["\']?[^}]*?(\d+)', script.string)
                        if total_match:
                            total = int(total_match.group(1))
                            # 假设每页10个结果
                            pagecount = (total + 9) // 10
                            print(f"从script中找到总记录数 {total}，计算页数: {pagecount}")
                            break
            
            # 如果还是没有找到，但有数据，假设至少有当前页
            if videos and pagecount == 1:
                pagecount = 999
            
            print(f"搜索解析结果: 关键词 '{key}'，找到 {len(videos)} 个结果，第 {pg} 页，共 {pagecount} 页")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 10,
                "total": pagecount * 10
            }
            
        except Exception as e:
            print(f"搜索页面解析错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 10,
                "total": 0
            }

    def playerContent(self, flag, id, vipFlags):
        result = {}
        
        try:
            if not id.startswith('http'):
                if id.startswith('/'):
                    play_url = self.host + id
                else:
                    play_url = self.host + '/' + id
            else:
                play_url = id
            
            print(f"播放页面URL: {play_url}")
            rsp = self.fetch(play_url, headers=self.header())
            html_content = rsp.text
            
            # 方法1：查找player_aaaa JSON对象
            pattern1 = r'var player_aaaa\s*=\s*({[^}]+})'
            match1 = re.search(pattern1, html_content)
            
            if match1:
                try:
                    json_str = match1.group(1)
                    json_str = json_str.replace('\\/', '/')
                    player_data = json.loads(json_str)
                    
                    if 'url' in player_data and player_data['url']:
                        video_url = player_data['url']
                        print(f"从player_aaaa找到视频地址: {video_url}")
                        
                        result["parse"] = 0
                        result["url"] = video_url
                        result["header"] = self.header()
                        return result
                except Exception as e:
                    print(f"解析player_aaaa JSON失败: {e}")
            
            # 方法2：查找url字段
            pattern2 = r'"url"\s*:\s*"([^"]+)"'
            matches2 = re.findall(pattern2, html_content)
            for url in matches2:
                if self.isVideoFormat(url):
                    url = url.replace('\\/', '/')
                    print(f"从url字段找到视频地址: {url}")
                    
                    result["parse"] = 0
                    result["url"] = url
                    result["header"] = self.header()
                    return result
            
            # 方法3：查找script标签中的m3u8地址
            pattern3 = r'https?://[^"\']+\.(m3u8|mp4|flv|ts)[^"\']*'
            matches3 = re.findall(pattern3, html_content, re.IGNORECASE)
            for match in matches3:
                if isinstance(match, tuple):
                    url = match[0]
                else:
                    url = match
                
                if self.isVideoFormat(url):
                    print(f"从正则匹配找到视频地址: {url}")
                    
                    result["parse"] = 0
                    result["url"] = url
                    result["header"] = self.header()
                    return result
            
            # 方法4：解析HTML查找iframe
            root = BeautifulSoup(html_content, 'html.parser')
            iframe = root.find('iframe')
            if iframe and iframe.get('src'):
                iframe_src = iframe['src']
                if iframe_src:
                    print(f"找到iframe地址: {iframe_src}")
                    
                    result["parse"] = 0
                    result["url"] = iframe_src
                    result["header"] = self.header()
                    return result
            
            # 如果没有找到直接播放地址，使用内置解析
            print("未找到直接播放地址，使用内置解析")
            result["parse"] = 1
            result["url"] = play_url
            result["header"] = self.header()
            result["ua"] = "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"
            
        except Exception as e:
            print(f"播放页面解析错误: {e}")
            import traceback
            traceback.print_exc()
            result["parse"] = 1
            result["url"] = id
            result["header"] = self.header()
        
        return result

    def isVideoFormat(self, url):
        video_formats = ['.m3u8', '.mp4', '.avi', '.mkv', '.flv', '.ts', '.webm']
        url_lower = url.lower()
        for fmt in video_formats:
            if fmt in url_lower:
                return True
        return False

    def localProxy(self, params):
        return [200, "video/MP2T", ""]