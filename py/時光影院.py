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
        return "时光影院"
    
    def init(self, extend=""):
        self.host = "https://www.cinemirrox.com"
        # 如果需要登录或其他初始化，在这里处理
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
            {"type_name": "电影", "type_id": "1"},
            {"type_name": "连续剧", "type_id": "2"},
            {"type_name": "动漫", "type_id": "3"},
            {"type_name": "综艺", "type_id": "4"},
            {"type_name": "体育", "type_id": "32"}
        ]
        result["class"] = classes
        return result
    
    def homeVideoContent(self):
        """首页推荐视频 - 使用分类页面替代"""
        try:
            # 使用电影分类第一页作为首页推荐
            return self.categoryContent("1", "1", None, None)
        except Exception as e:
            print(f"首页视频解析错误: {e}")
            return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类页面内容"""
        try:
            # 构建分类URL
            url = f"{self.host}/vod/show/id/{tid}.html"
            if int(pg) > 1:
                url = f"{self.host}/vod/show/id/{tid}/page/{pg}.html"
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 根据实际结构选择元素
            items = root.select('.module-item')
            
            for item in items:
                try:
                    a = item.find('a', href=re.compile(r'/vod/detail/'))
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取标题
                    vod_name = ""
                    title_elem = item.select_one('.module-item-title')
                    if title_elem:
                        vod_name = title_elem.text.strip()
                    elif a.get('title'):
                        vod_name = a.get('title').strip()
                    
                    # 获取封面图
                    vod_pic = ""
                    img = item.find('img')
                    if img:
                        img_src = img.get('data-src') or img.get('src')
                        if img_src:
                            vod_pic = img_src
                            if vod_pic and not vod_pic.startswith('http'):
                                vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
                    
                    # 获取备注（清晰度/更新状态）
                    vod_remarks = ""
                    remark_elem = item.select_one('.module-item-text')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
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
            pagination = root.find('div', id='page')
            if pagination:
                page_links = pagination.find_all('a', class_='page-number')
                page_numbers = []
                for link in page_links:
                    try:
                        if 'display' in link.get('class', []):
                            num = int(link.text.strip())
                            page_numbers.append(num)
                    except:
                        pass
                if page_numbers:
                    pagecount = max(page_numbers)
                else:
                    # 尝试解析最后一页
                    last_page = pagination.find('a', class_='page-next', string='尾页')
                    if last_page and last_page.get('href'):
                        href = last_page['href']
                        match = re.search(r'/page/(\d+)\.html', href)
                        if match:
                            pagecount = int(match.group(1))
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 20,
                "total": len(videos) * pagecount
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
        """视频详情页 - 根据新的HTML结构更新"""
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
            title_elem = root.find('h1', class_='page-title')
            if title_elem:
                vod_name = title_elem.text.strip()
            else:
                # 备选方案
                title_elem = root.find('h1')
                if title_elem:
                    vod_name = title_elem.text.strip()
            
            # 封面图
            vod_pic = ""
            cover_img = root.find('img', class_='lazyload')
            if cover_img:
                img_src = cover_img.get('data-src') or cover_img.get('src')
                if img_src:
                    vod_pic = img_src
                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
            
            # 描述 - 从相关元素中提取
            vod_content = ""
            # 尝试多个可能的描述元素
            desc_selectors = ['.video-text', '.video-info-content', '.vod_content', '.module-item-style.video-text']
            for selector in desc_selectors:
                desc_elem = root.select_one(selector)
                if desc_elem:
                    vod_content = desc_elem.text.strip()
                    # 清理可能的描述文本
                    vod_content = vod_content.replace('　　半年间，SNK剧变，总监余英飞离职、门外汉古肇华空降。张家妍虽掌权却难服众。刘艳的公开平台崛起，动摇传统媒体地位，连已入官场的许诗晴亦被卷入新旧媒体的角力。文慧心于此时复出，昭告世人：新闻女王的地位永远不可撼动！', '').strip()
                    if vod_content:
                        break
            
            # 解析年份、地区、类型
            info_dict = {}
            
            # 从video-info-aux中提取信息
            video_info_aux = root.find('div', class_='video-info-aux')
            if video_info_aux:
                # 年份
                year_links = video_info_aux.find_all('a', href=re.compile(r'/vod/show/id/.*/year/'))
                if year_links:
                    info_dict['年份'] = year_links[0].text.strip()
                
                # 地区
                area_links = video_info_aux.find_all('a', href=re.compile(r'/vod/show/area/'))
                if area_links:
                    info_dict['地区'] = area_links[0].text.strip()
                
                # 类型/分类
                type_links = video_info_aux.find_all('a', href=re.compile(r'/vod/type/'))
                if type_links:
                    info_dict['类型'] = type_links[0].text.strip()
            
            # 从meta描述中提取信息作为备用
            meta_desc = root.find('meta', {'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content = meta_desc['content']
                # 尝试从描述中提取年份
                year_match = re.search(r'(\d{4})年', content)
                if year_match and '年份' not in info_dict:
                    info_dict['年份'] = year_match.group(1)
            
            # 解析演员和导演 - 从相关模块中提取
            actor_text = ""
            # 查找相关视频模块中的演员信息
            related_items = root.select('.module-item')
            if related_items:
                # 取第一个相关视频的演员信息
                first_item = related_items[0]
                actor_elem = first_item.select_one('.video-tag')
                if actor_elem:
                    actor_links = actor_elem.find_all('a')
                    actors = []
                    for link in actor_links:
                        actor_name = link.text.strip()
                        if actor_name:
                            actors.append(actor_name)
                    if actors:
                        info_dict['演员'] = ' '.join(actors[:10])  # 限制前10个演员
            
            # 从script标签中尝试提取演员信息
            script_tags = root.find_all('script')
            for script in script_tags:
                if script.string and 'vod_actor' in script.string:
                    # 尝试匹配演员信息
                    match = re.search(r'vod_actor":"([^"]+)"', script.string)
                    if match:
                        actors = match.group(1).split(',')
                        if actors:
                            info_dict['演员'] = ' '.join(actors[:10])
                        break
            
            # 从script标签中尝试提取导演信息
            for script in script_tags:
                if script.string and 'vod_director' in script.string:
                    match = re.search(r'vod_director":"([^"]+)"', script.string)
                    if match:
                        directors = match.group(1).split(',')
                        if directors:
                            info_dict['导演'] = ' '.join(directors)
                        break
            
            # 解析播放列表 - 根据HTML结构
            play_from_list = []
            play_url_list = []
            
            # 查找播放节点标签
            tab_items = root.select('.module-tab-item')
            if tab_items:
                for i, tab_item in enumerate(tab_items):
                    tab_name = tab_item.find('span')
                    if tab_name:
                        source_name = tab_name.text.strip()
                        
                        # 查找对应的播放列表
                        # 根据HTML结构，有两个播放列表区域
                        playlist_divs = root.select('.module-player-list')
                        if playlist_divs and i < len(playlist_divs):
                            playlist_div = playlist_divs[i]
                            episodes = []
                            # 查找所有播放链接
                            play_links = playlist_div.find_all('a', href=re.compile(r'/vod/play/'))
                            for link in play_links:
                                play_href = link.get('href', '')
                                play_title = link.get('title', '')
                                
                                if not play_title:
                                    # 尝试从span获取标题
                                    span = link.find('span')
                                    if span:
                                        play_title = span.text.strip()
                                
                                if not play_title:
                                    # 尝试从链接文本获取
                                    play_title = link.text.strip()
                                
                                if play_href and not play_href.startswith('http'):
                                    play_href = self.host + play_href if play_href.startswith('/') else play_href
                                
                                if play_title and play_href:
                                    # 清理标题
                                    play_title = play_title.replace('播放', '').replace('新闻女王2粤语', '').strip()
                                    episodes.append(f"{play_title}${play_href}")
                            
                            if episodes:
                                play_from_list.append(source_name)
                                play_url_list.append("#".join(episodes))
            
            # 如果上述方法失败，使用备用方法
            if not play_from_list:
                # 查找所有的播放链接区域
                playlist_areas = root.find_all('div', class_='module-blocklist')
                if playlist_areas:
                    for area in playlist_areas:
                        episodes = []
                        play_links = area.find_all('a', href=re.compile(r'/vod/play/'))
                        for link in play_links:
                            play_href = link.get('href', '')
                            play_title = link.get('title', '')
                            
                            if not play_title:
                                span = link.find('span')
                                if span:
                                    play_title = span.text.strip()
                            
                            if not play_title:
                                play_title = link.text.strip()
                            
                            if play_href and not play_href.startswith('http'):
                                play_href = self.host + play_href if play_href.startswith('/') else play_href
                            
                            if play_title and play_href:
                                play_title = play_title.replace('播放', '').strip()
                                episodes.append(f"{play_title}${play_href}")
                        
                        if episodes:
                            play_from_list.append("线路" + str(len(play_from_list) + 1))
                            play_url_list.append("#".join(episodes))
            
            # 如果没有播放列表，使用详情页URL作为播放源
            if not play_from_list:
                play_from_list = ["默认"]
                play_url_list = [f"第1集${url}"]
            
            # 构建结果
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": info_dict.get('年份', ''),
                "vod_actor": info_dict.get('演员', ''),
                "vod_director": info_dict.get('导演', ''),
                "vod_area": info_dict.get('地区', ''),
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
                "vod_play_url": f"第1集${self.host}"
            }
            return {"list": [video]}
    
    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        result = {}
        
        try:
            print(f"开始解析播放地址: {id}")
            
            # 如果传入的是详情页URL，需要先获取播放页URL
            if '/vod/detail/' in id:
                # 提取视频ID
                match = re.search(r'/vod/detail/id/(\d+)', id)
                if match:
                    video_id = match.group(1)
                    # 构建播放页URL
                    # 从详情页中提取sid和nid
                    rsp = self.fetch(id, headers=self.header())
                    root = BeautifulSoup(rsp.text, 'html.parser')
                    
                    # 查找第一个播放链接
                    first_play_link = root.find('a', href=re.compile(r'/vod/play/'))
                    if first_play_link and first_play_link.get('href'):
                        play_href = first_play_link['href']
                        if not play_href.startswith('http'):
                            play_href = self.host + play_href if play_href.startswith('/') else play_href
                        id = play_href
                    else:
                        # 默认使用第一集
                        id = f"{self.host}/vod/play/id/{video_id}/sid/1/nid/1.html"
            
            # 确保URL完整
            if not id.startswith('http'):
                id = self.host + id if id.startswith('/') else self.host + '/' + id
            
            print(f"解析播放页: {id}")
            rsp = self.fetch(id, headers=self.header())
            html_content = rsp.text
            
            # 方法1: 从JavaScript变量中提取m3u8地址
            m3u8_url = None
            
            # 查找player_aaaa变量
            player_pattern = r'var player_aaaa\s*=\s*({[^}]+})'
            player_match = re.search(player_pattern, html_content)
            
            if player_match:
                try:
                    player_data = player_match.group(1)
                    # 提取url字段
                    url_pattern = r'"url":"([^"]+)"'
                    url_match = re.search(url_pattern, player_data)
                    if url_match:
                        m3u8_url = url_match.group(1)
                        print(f"从player_aaaa找到m3u8地址: {m3u8_url}")
                except Exception as e:
                    print(f"解析player_aaaa失败: {e}")
            
            # 方法2: 直接搜索m3u8链接
            if not m3u8_url:
                m3u8_patterns = [
                    r'https?://[^"\']+\.m3u8[^"\']*',
                    r'url\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                    r'src\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                    r'file\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']'
                ]
                
                for pattern in m3u8_patterns:
                    matches = re.findall(pattern, html_content)
                    for match in matches:
                        if isinstance(match, tuple):
                            m3u8_url = match[0]
                        else:
                            m3u8_url = match
                        
                        if m3u8_url and '.m3u8' in m3u8_url:
                            print(f"从正则匹配找到m3u8地址: {m3u8_url}")
                            break
                    if m3u8_url:
                        break
            
            # 方法3: 查找隐藏的播放地址
            if not m3u8_url:
                root = BeautifulSoup(html_content, 'html.parser')
                hidden_url = root.find('a', id='bfurl')
                if hidden_url and hidden_url.get('href'):
                    m3u8_url = hidden_url['href']
                    print(f"从隐藏链接找到m3u8地址: {m3u8_url}")
            
            # 方法4: 查找video-source标签
            if not m3u8_url:
                source_tag = root.find('source', {'id': 'video-source'})
                if source_tag and source_tag.get('src'):
                    m3u8_url = source_tag['src']
                    print(f"从video-source找到m3u8地址: {m3u8_url}")
            
            # 如果找到m3u8地址
            if m3u8_url:
                # 确保URL完整
                if m3u8_url.startswith('//'):
                    m3u8_url = 'https:' + m3u8_url
                elif not m3u8_url.startswith('http'):
                    m3u8_url = self.host + m3u8_url if m3u8_url.startswith('/') else m3u8_url
                
                # 检查是否需要添加Referer
                headers = self.header()
                if 'lzcdn' in m3u8_url or 'cinemirra' in m3u8_url:
                    headers['Referer'] = id
                
                result["parse"] = 0  # 直接播放
                result["url"] = m3u8_url
                result["header"] = headers
                print(f"返回播放地址: {m3u8_url}")
            else:
                # 如果没有找到m3u8，返回播放页URL让TVBox解析
                result["parse"] = 1  # 需要解析
                result["url"] = id
                result["header"] = self.header()
                print(f"未找到m3u8地址，返回播放页: {id}")
            
            return result
            
        except Exception as e:
            print(f"播放地址解析错误: {e}")
            import traceback
            traceback.print_exc()
            
            # 出错时返回原始URL
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