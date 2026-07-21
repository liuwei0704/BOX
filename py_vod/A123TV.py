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
        return "A123TV"
    
    def init(self, extend=""):
        self.host = "https://a123tv.com"
        pass
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    def homeContent(self, filter):
        """返回分类列表"""
        result = {}
        classes = [
            {"type_name": "电影", "type_id": "10"},
            {"type_name": "连续剧", "type_id": "11"},
            {"type_name": "综艺", "type_id": "12"},
            {"type_name": "动漫", "type_id": "13"},
            {"type_name": "福利", "type_id": "15"},
        ]
        result["class"] = classes
        return result
    
    def homeVideoContent(self):
        """首页推荐视频"""
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 首页视频列表选择器
            items = root.select('.w4-item-wrap') or root.select('.w4-item')
            
            for item in items[:30]:
                try:
                    a = item.find('a', class_='w4-item')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取标题
                    vod_name = ""
                    title_elem = a.find('div', class_='t') or a.find('.t')
                    if title_elem:
                        vod_name = title_elem.get('title', title_elem.text.strip())
                    
                    # 获取封面图
                    vod_pic = ""
                    img = a.find('img')
                    if img:
                        vod_pic = img.get('data-src') or img.get('src', '')
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
                    
                    # 获取备注信息
                    vod_remarks = ""
                    
                    # 清晰度标签
                    quality_elem = a.find('div', class_='r')
                    if quality_elem:
                        quality_text = quality_elem.text.strip()
                        vod_remarks = quality_text
                    
                    # 线路数量
                    lines_elem = a.find('div', class_='s')
                    if lines_elem:
                        lines_text = lines_elem.text.strip()
                        if vod_remarks:
                            vod_remarks += " | " + lines_text
                        else:
                            vod_remarks = lines_text
                    
                    # 年份和类型
                    info_elem = a.find('div', class_='i')
                    if info_elem:
                        info_text = info_elem.text.strip()
                        if vod_remarks:
                            vod_remarks += " | " + info_text
                        else:
                            vod_remarks = info_text
                    
                    if vod_name and vod_id:
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": vod_name,
                            "vod_pic": vod_pic,
                            "vod_remarks": vod_remarks
                        })
                except Exception as e:
                    print(f"首页解析单个视频时出错: {e}")
                    continue
            
            return {"list": videos}
        except Exception as e:
            print(f"首页视频解析错误: {e}")
            return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类页面内容 - 已修复分页问题"""
        try:
            # 构建分类URL
            if int(pg) > 1:
                url = f"{self.host}/t/{tid}/p{pg}.html"
            else:
                url = f"{self.host}/t/{tid}.html"
            
            print(f"分类页面URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 分类页视频列表
            items = root.select('.w4-item-wrap')
            
            for item in items:
                try:
                    a = item.find('a', class_='w4-item')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取标题
                    vod_name = ""
                    title_elem = a.find('div', class_='t')
                    if title_elem:
                        vod_name = title_elem.get('title', '') or title_elem.text.strip()
                    
                    if not vod_name:
                        continue
                    
                    # 获取封面图
                    vod_pic = ""
                    img = a.find('img')
                    if img:
                        vod_pic = img.get('data-src') or img.get('src', '')
                        if vod_pic:
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            elif not vod_pic.startswith('http'):
                                vod_pic = self.host + vod_pic if vod_pic.startswith('/') else vod_pic
                    
                    # 获取备注信息
                    vod_remarks = ""
                    
                    # 清晰度
                    quality_elem = a.find('div', class_='r')
                    if quality_elem:
                        quality_text = quality_elem.text.strip()
                        vod_remarks = quality_text
                    
                    # 线路数量
                    lines_elem = a.find('div', class_='s')
                    if lines_elem:
                        lines_text = lines_elem.text.strip()
                        if vod_remarks:
                            vod_remarks += " | " + lines_text
                        else:
                            vod_remarks = lines_text
                    
                    # 年份和类型
                    info_elem = a.find('div', class_='i')
                    if info_elem:
                        info_text = info_elem.text.strip()
                        if vod_remarks:
                            vod_remarks += " | " + info_text
                        else:
                            vod_remarks = info_text
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception as e:
                    print(f"分类解析单个视频时出错: {e}")
                    continue
            
            # 修复分页信息解析
            pagecount = int(pg)
            
            # 查找分页容器
            pagination = root.find('div', class_='w4-page')
            if not pagination:
                # 尝试其他可能的类名
                pagination = root.find('div', class_='pagination')
            
            if pagination:
                # 查找所有分页链接
                page_links = pagination.find_all('a', href=True)
                if page_links:
                    page_numbers = []
                    for link in page_links:
                        href = link.get('href', '')
                        text = link.text.strip()
                        
                        if href:
                            # 从URL中提取页码
                            match = re.search(r'/p(\d+)\.html', href)
                            if match:
                                try:
                                    page_numbers.append(int(match.group(1)))
                                except:
                                    pass
                        elif text.isdigit():
                            # 从文本中提取页码
                            try:
                                page_numbers.append(int(text))
                            except:
                                pass
                    
                    if page_numbers:
                        pagecount = max(page_numbers)
                        print(f"从分页链接解析到最大页码: {pagecount}")
                    else:
                        # 检查是否有"末页"或"最后页"链接
                        last_page = pagination.find('a', text=re.compile(r'末页|最后页|尾页|last', re.I))
                        if last_page and last_page.get('href'):
                            href = last_page.get('href')
                            match = re.search(r'/p(\d+)\.html', href)
                            if match:
                                try:
                                    pagecount = int(match.group(1))
                                except:
                                    pagecount = int(pg) + 1
                        else:
                            # 如果没有找到具体的页码，但当前不是第一页，至少显示当前页+1
                            if int(pg) > 1:
                                pagecount = max(pagecount, int(pg) + 1)
            
            print(f"分类解析完成: 第 {pg} 页，共 {pagecount} 页，找到 {len(videos)} 个视频")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 30,
                "total": len(videos) * pagecount
            }
        except Exception as e:
            print(f"分类页面解析错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 30,
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
            title_elem = root.find('h1') or root.find('title')
            if title_elem:
                vod_name = title_elem.text.strip()
                vod_name = re.sub(r'\s*-\s*A123TV.*', '', vod_name)
                vod_name = vod_name.replace('《', '').replace('》', '')
            
            # 从meta description中提取详细信息
            description = root.find('meta', {'name': 'description'})
            if description:
                desc_content = description.get('content', '')
                
                info_dict = {}
                if desc_content:
                    # 提取地区
                    area_match = re.search(r'地区：(.+?)。', desc_content)
                    if area_match:
                        info_dict['地区'] = area_match.group(1)
                    
                    # 提取演员
                    actor_match = re.search(r'演员：(.+?)。', desc_content)
                    if actor_match:
                        info_dict['演员'] = actor_match.group(1)
                    
                    # 提取导演
                    director_match = re.search(r'导演：(.+?)。', desc_content)
                    if director_match:
                        info_dict['导演'] = director_match.group(1)
                    
                    # 提取年份
                    year_match = re.search(r'(\d{4})年', desc_content)
                    if year_match:
                        info_dict['年份'] = year_match.group(1)
                    
                    # 提取剧情描述
                    plot_match = re.search(r'剧情：(.+)', desc_content)
                    if plot_match:
                        vod_content = plot_match.group(1)
                    else:
                        vod_content = desc_content
                else:
                    vod_content = ""
            else:
                vod_content = ""
                info_dict = {}
            
            # 封面图
            vod_pic = ""
            # 从meta og:image中获取
            og_image = root.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                vod_pic = og_image['content']
                if vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
            
            # 从页面中直接查找图片
            if not vod_pic:
                cover_img = root.find('img', {'class': re.compile(r'cover|poster|thumb')})
                if cover_img and (cover_img.get('src') or cover_img.get('data-src')):
                    vod_pic = cover_img.get('src') or cover_img.get('data-src', '')
                    if vod_pic.startswith('//'):
                        vod_pic = 'https:' + vod_pic
            
            # 解析播放源和剧集
            play_from_list = []
            play_url_list = []
            
            # 1. 解析JavaScript中的播放数据
            script_data = None
            scripts = root.find_all('script')
            for script in scripts:
                if script.string and 'var pp=' in script.string:
                    match = re.search(r'var pp=(\{.*?\});', script.string, re.DOTALL)
                    if match:
                        try:
                            script_data = json.loads(match.group(1))
                        except:
                            try:
                                json_str = match.group(1)
                                json_str = re.sub(r',\s*}', '}', json_str)
                                json_str = re.sub(r',\s*]', ']', json_str)
                                script_data = json.loads(json_str)
                            except:
                                pass
            
            # 2. 解析线路
            if script_data and 'la' in script_data:
                for line in script_data['la']:
                    if len(line) >= 5:
                        line_id = line[0]
                        line_name = line[1]
                        total_episodes = line[2]
                        current_ep_index = line[3]
                        m3u8_url = line[4]
                        
                        episodes = []
                        
                        # 从页面中解析剧集链接
                        episode_container = root.find('div', class_='w4-episode-list')
                        if episode_container:
                            episode_links = episode_container.find_all('a', href=True)
                            for i, ep_link in enumerate(episode_links):
                                ep_href = ep_link.get('href', '')
                                ep_title = ep_link.get('title', '') or ep_link.text.strip()
                                
                                if ep_href:
                                    if not ep_href.startswith('http'):
                                        ep_href = self.host + ep_href if ep_href.startswith('/') else ep_href
                                    
                                    # 替换线路ID
                                    ep_href = re.sub(r'/([a-z0-9]+z\d+)\.html$', f'/{line_id}z{i}.html', ep_href)
                                    
                                    episodes.append(f"{ep_title}${ep_href}")
                        
                        # 如果没有解析到剧集链接，使用默认方式
                        if not episodes and total_episodes > 0:
                            for i in range(total_episodes):
                                episode_url = f"{self.host}/v/{script_data['no']}/{line_id}z{i}.html"
                                episodes.append(f"第{i+1}集${episode_url}")
                        
                        if episodes:
                            play_from_list.append(line_name)
                            play_url_list.append("#".join(episodes))
            
            # 3. 如果没有从JavaScript解析到，从页面线路列表中解析
            if not play_from_list:
                line_items = root.find_all('a', class_='w4-line-item')
                if line_items:
                    for line_item in line_items:
                        line_href = line_item.get('href', '')
                        line_title = line_item.get('title', '') or "线路"
                        
                        if line_href:
                            episodes = []
                            episode_container = root.find('div', class_='w4-episode-list')
                            if episode_container:
                                episode_links = episode_container.find_all('a', href=True)
                                for i, ep_link in enumerate(episode_links):
                                    ep_href = ep_link.get('href', '')
                                    ep_title = ep_link.get('title', '') or ep_link.text.strip()
                                    
                                    if ep_href:
                                        if not ep_href.startswith('http'):
                                            ep_href = self.host + ep_href if ep_href.startswith('/') else ep_href
                                        
                                        episodes.append(f"{ep_title}${ep_href}")
                            
                            if episodes:
                                play_from_list.append(line_title)
                                play_url_list.append("#".join(episodes))
            
            # 4. 最后尝试，如果没有线路，只显示当前页面的剧集
            if not play_from_list:
                episode_container = root.find('div', class_='w4-episode-list')
                if episode_container:
                    episodes = []
                    episode_links = episode_container.find_all('a', href=True)
                    for ep_link in episode_links:
                        ep_href = ep_link.get('href', '')
                        ep_title = ep_link.get('title', '') or ep_link.text.strip()
                        
                        if ep_href:
                            if not ep_href.startswith('http'):
                                ep_href = self.host + ep_href if ep_href.startswith('/') else ep_href
                            
                            episodes.append(f"{ep_title}${ep_href}")
                    
                    if episodes:
                        play_from_list.append("默认线路")
                        play_url_list.append("#".join(episodes))
            
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
                "vod_play_from": "$$$".join(play_from_list) if play_from_list else "默认线路",
                "vod_play_url": "$$$".join(play_url_list) if play_url_list else f"第1集${url}"
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
                "vod_play_url": f"第1集${ids[0]}"
            }
            return {"list": [video]}
    
    def searchContent(self, key, quick, pg=1):
        """搜索功能 - 已根据搜索结果页HTML优化"""
        try:
            encoded_key = urllib.parse.quote(key)
            search_url = f"{self.host}/s/{encoded_key}.html"
            
            # 如果有分页，处理分页
            if int(pg) > 1:
                # 搜索结果页的分页URL格式可能是 /s/关键词/p2.html
                search_url = f"{self.host}/s/{encoded_key}/p{pg}.html"
            
            print(f"搜索URL: {search_url}")
            rsp = self.fetch(search_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 解析搜索结果 - 搜索结果页结构与分类页相同
            result_items = root.select('.w4-item-wrap')
            
            for item in result_items:
                try:
                    a = item.find('a', class_='w4-item')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 标题
                    vod_name = ""
                    title_elem = a.find('div', class_='t')
                    if title_elem:
                        vod_name = title_elem.get('title', '') or title_elem.text.strip()
                    
                    if not vod_name:
                        continue
                    
                    # 封面
                    vod_pic = ""
                    img = a.find('img')
                    if img:
                        vod_pic = img.get('data-src') or img.get('src', '')
                        if vod_pic:
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            elif not vod_pic.startswith('http'):
                                vod_pic = self.host + vod_pic if vod_pic.startswith('/') else vod_pic
                    
                    # 备注信息
                    vod_remarks = ""
                    
                    # 清晰度
                    quality_elem = a.find('div', class_='r')
                    if quality_elem:
                        quality_text = quality_elem.text.strip()
                        vod_remarks = quality_text
                    
                    # 线路数量
                    lines_elem = a.find('div', class_='s')
                    if lines_elem:
                        lines_text = lines_elem.text.strip()
                        if vod_remarks:
                            vod_remarks += " | " + lines_text
                        else:
                            vod_remarks = lines_text
                    
                    # 年份和类型
                    info_elem = a.find('div', class_='i')
                    if info_elem:
                        info_text = info_elem.text.strip()
                        if vod_remarks:
                            vod_remarks += " | " + info_text
                        else:
                            vod_remarks = info_text
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception as e:
                    print(f"搜索解析单个结果时出错: {e}")
                    continue
            
            # 分页信息 - 搜索结果页可能有分页
            pagecount = int(pg)
            pagination = root.find('div', class_='w4-page')
            if pagination:
                page_links = pagination.find_all('a')
                if page_links:
                    page_numbers = []
                    for link in page_links:
                        href = link.get('href', '')
                        text = link.text.strip()
                        if href:
                            # 尝试从URL中提取页码
                            match = re.search(r'/p(\d+)\.html', href)
                            if match:
                                try:
                                    page_numbers.append(int(match.group(1)))
                                except:
                                    pass
                        elif text.isdigit():
                            try:
                                page_numbers.append(int(text))
                            except:
                                pass
                    
                    if page_numbers:
                        pagecount = max(page_numbers)
                    else:
                        # 如果没有找到分页链接，检查是否有下一页
                        next_link = pagination.find('a', text=re.compile(r'下页|下一页|next', re.I))
                        if next_link:
                            # 如果存在下一页，假设总页数至少比当前页多1
                            pagecount = max(pagecount, int(pg) + 1)
            
            print(f"搜索到 {len(videos)} 个结果，第 {pg} 页，共 {pagecount} 页")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 30,
                "total": len(videos) * pagecount
            }
            
        except Exception as e:
            print(f"搜索解析错误: {e}")
            import traceback
            traceback.print_exc()
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
            
            # 1. 首先尝试从JavaScript变量中获取m3u8地址
            video_url = None
            scripts = root.find_all('script')
            
            for script in scripts:
                if script.string:
                    # 查找JavaScript中的播放器配置
                    if 'var pp=' in script.string:
                        match = re.search(r'var pp=(\{.*?\});', script.string, re.DOTALL)
                        if match:
                            try:
                                script_data = json.loads(match.group(1))
                                if 'la' in script_data and script_data['la']:
                                    # 取第一个线路的m3u8地址
                                    for line in script_data['la']:
                                        if len(line) >= 5:
                                            video_url = line[4]
                                            if video_url:
                                                break
                            except:
                                pass
                    
                    # 查找直接播放器div中的data-src
                    if not video_url:
                        match = re.search(r'data-src="([^"]+\.m3u8[^"]*)"', script.string)
                        if match:
                            video_url = match.group(1)
            
            # 2. 查找页面中的播放器div
            if not video_url:
                player_div = root.find('div', id='awp1') or root.find('div', {'data-src': re.compile(r'\.m3u8')})
                if player_div and player_div.get('data-src'):
                    video_url = player_div['data-src']
            
            # 3. 查找video标签
            if not video_url:
                video_tag = root.find('video')
                if video_tag:
                    video_url = video_tag.get('src') or video_tag.get('data-src')
            
            if video_url:
                result["parse"] = 0  # 直接播放
                result["url"] = video_url
                result["header"] = {
                    'User-Agent': self.header()['User-Agent'],
                    'Referer': play_url,
                    'Origin': 'https://a123tv.com'
                }
            else:
                # 如果找不到直接播放地址，让TVBox解析
                result["parse"] = 1  # 需要解析
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