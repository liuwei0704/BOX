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
        return "极速看剧"
    
    def init(self, extend=""):
        self.host = "https://jddy.tv"
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
            {"type_name": "电视剧", "type_id": "2"},
            {"type_name": "综艺", "type_id": "3"},
            {"type_name": "动漫", "type_id": "4"},
            {"type_name": "短劇", "type_id": "5"}
        ]
        result["class"] = classes
        return result
    
    def homeVideoContent(self):
        """首页推荐视频"""
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 首页有多个区块：电影、电视剧、动漫
            # 获取所有区块的视频
            sections = root.select('.index-tj .index-tj-l ul')
            
            for section in sections:
                items = section.find_all('li', class_='p2')
                
                for item in items:
                    try:
                        a = item.find('a', class_='link-hover')
                        if not a:
                            continue
                        
                        vod_id = a.get('href', '')
                        if vod_id and not vod_id.startswith('http'):
                            vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                        
                        # 获取标题
                        vod_name = ""
                        name_elem = a.find('p', class_='name')
                        if name_elem:
                            vod_name = name_elem.text.strip()
                        
                        # 获取封面图
                        vod_pic = ""
                        img = a.find('img')
                        if img:
                            vod_pic = img.get('src', '') or img.get('data-src', '')
                            if vod_pic:
                                if vod_pic.startswith('//'):
                                    vod_pic = 'https:' + vod_pic
                                elif not vod_pic.startswith('http'):
                                    vod_pic = self.host + vod_pic if vod_pic.startswith('/') else vod_pic
                        
                        # 获取备注（更新状态）
                        vod_remarks = ""
                        remark_elem = a.find('p', class_='other')
                        if remark_elem:
                            vod_remarks = remark_elem.text.strip()
                        
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
            
            return {"list": videos[:60]}  # 限制返回数量
        except Exception as e:
            print(f"首页视频解析错误: {e}")
            return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类页面内容 - 修复分頁版"""
        try:
            # 根据实际HTML，分类页面URL格式：
            # 第一页：/vodshow/1--------1---.html
            # 第二页：/vodshow/1--------2---.html
            # 以此类推
            
            url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            
            print(f"访问分类URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            
            if rsp.status_code != 200:
                print(f"页面访问失败，状态码: {rsp.status_code}")
                return {
                    "list": [],
                    "page": int(pg),
                    "pagecount": 1,
                    "limit": 30,
                    "total": 0
                }
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 视频项在 div.public-list-box 中
            video_items = root.select('.public-list-box')
            
            print(f"找到 {len(video_items)} 个视频项")
            
            for item in video_items:
                try:
                    a = item.find('a', class_='public-list-exp')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    
                    # 获取标题 - 从title属性获取
                    vod_name = a.get('title', '')
                    
                    # 获取封面图 (懒加载)
                    vod_pic = ""
                    img = a.find('img', class_='lazy')
                    if img:
                        vod_pic = img.get('data-src', '')
                        if not vod_pic:
                            vod_pic = img.get('src', '')
                        
                        if vod_pic:
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            elif vod_pic.startswith('/'):
                                vod_pic = self.host + vod_pic
                    
                    # 获取备注
                    vod_remarks = ""
                    remark_span = item.find('span', class_='public-list-prb')
                    if remark_span:
                        vod_remarks = remark_span.text.strip()
                    
                    if vod_name and vod_id:
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": vod_name,
                            "vod_pic": vod_pic,
                            "vod_remarks": vod_remarks
                        })
                    
                except Exception as e:
                    print(f"分类解析单个视频时出错: {e}")
                    continue
            
            # 修復點：正確的分頁信息提取 - 增強版
            pagecount = 1
            
            # 方法1：從頁面中的總頁數文本提取
            pagination = root.find('div', class_='pages')
            if pagination:
                page_info = pagination.find('div', class_='page-info')
                if page_info:
                    page_text = page_info.text
                    print(f"分頁文本: {page_text}")
                    
                    # 匹配 "/ 1040页" 格式
                    match = re.search(r'/\s*(\d+)\s*页', page_text)
                    if match:
                        pagecount = int(match.group(1))
                        print(f"從文本提取到總頁數: {pagecount}")
            
            # 方法2：如果方法1失敗，從頁碼鏈接中提取最大頁碼
            if pagecount <= 1:
                page_links = root.find_all('a', href=re.compile(r'/vodshow/' + str(tid) + r'--------\d+---\.html'))
                max_page = 0
                for link in page_links:
                    href = link.get('href', '')
                    match = re.search(r'--------(\d+)---\.html', href)
                    if match:
                        try:
                            page_num = int(match.group(1))
                            if page_num > max_page:
                                max_page = page_num
                        except:
                            pass
                
                if max_page > 0:
                    pagecount = max_page
                    print(f"從鏈接提取到最大頁碼: {pagecount}")
            
            # 方法3：如果還是只有1頁但視頻數量很多，保守估計
            if pagecount <= 1 and len(videos) >= 30:
                # 如果視頻數量達到30條，說明至少還有下一頁
                # 保守估計10頁，讓用戶可以繼續點擊
                pagecount = 10
                print(f"保守估計頁數: {pagecount}")
            
            print(f"返回 {len(videos)} 個視頻，總頁數: {pagecount}")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 30,
                "total": pagecount * 30
            }
            
        except Exception as e:
            print(f"分類頁面解析錯誤: {e}")
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
        """视频详情页 - 修复版"""
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                url = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
            else:
                url = vod_id
            
            print(f"访问详情页URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 1. 解析视频标题
            vod_name = ""
            title_elem = root.select_one('.slide-desc-title')
            if title_elem:
                vod_name = title_elem.text.strip()
            
            # 2. 解析封面图 (从background-image中提取)
            vod_pic = ""
            pic_bj = root.select_one('.this-pic-bj')
            if pic_bj:
                style = pic_bj.get('style', '')
                match = re.search(r'url\([\'"]?([^\'"]+)[\'"]?\)', style)
                if match:
                    vod_pic = match.group(1)
                    if vod_pic.startswith('//'):
                        vod_pic = 'https:' + vod_pic
            
            # 3. 解析剧情描述
            vod_content = ""
            desc_elem = root.select_one('#height_limit')
            if desc_elem:
                vod_content = desc_elem.text.strip()
                # 移除开头的"描述:"字样
                if vod_content.startswith('描述:'):
                    vod_content = vod_content[3:].strip()
            
            # 4. 解析基本信息 (年份、地区、状态)
            vod_year = ""
            vod_area = ""
            vod_remarks = ""
            
            info_spans = root.select('.this-desc-info span')
            for span in info_spans:
                text = span.text.strip()
                # 匹配年份 (4位数字)
                if re.match(r'^\d{4}$', text):
                    vod_year = text
                # 匹配地区 (包含"中国"、"大陆"、"香港"、"台湾"等)
                elif re.search(r'[中国港澳台韩美日英法德]', text):
                    vod_area = text
                # 匹配状态 (包含"集"、"期"、"完结"等)
                elif re.search(r'[集期完结]', text):
                    vod_remarks = text
            
            # 5. 解析导演和演员
            vod_director = ""
            vod_actor = ""
            
            # 从 .this-info 中提取
            info_divs = root.select('.this-info')
            for div in info_divs:
                strong = div.find('strong')
                if strong:
                    label = strong.text.strip()
                    if '导演' in label:
                        # 提取导演名字
                        director_links = div.find_all('a')
                        directors = [a.text.strip() for a in director_links if a.text.strip()]
                        vod_director = ','.join(directors)
                    elif '演员' in label:
                        # 提取演员名字
                        actor_links = div.find_all('a')
                        actors = [a.text.strip() for a in actor_links if a.text.strip()]
                        vod_actor = ','.join(actors)
            
            # 6. 解析播放源和剧集
            play_from_list = []
            play_url_list = []
            
            # 获取播放源列表
            source_tab = root.select_one('.anthology-tab')
            if source_tab:
                source_links = source_tab.find_all('a')
                source_names = []
                for link in source_links:
                    name = link.text.strip()
                    # 清理名称，去除图标文字
                    name = re.sub(r'[]', '', name).strip()
                    if name:
                        source_names.append(name)
                
                # 获取对应的剧集列表
                playlist_boxes = root.select('.anthology-list .anthology-list-box')
                
                for i, source_name in enumerate(source_names):
                    if i < len(playlist_boxes):
                        playlist_box = playlist_boxes[i]
                        episodes = []
                        
                        # 查找所有剧集链接
                        episode_links = playlist_box.find_all('a', href=True)
                        for link in episode_links:
                            ep_title = link.text.strip()
                            ep_url = link.get('href', '')
                            
                            if ep_title and ep_url:
                                # 处理URL
                                if ep_url.startswith('//'):
                                    ep_url = 'https:' + ep_url
                                elif ep_url.startswith('/'):
                                    ep_url = self.host + ep_url
                                episodes.append(f"{ep_title}${ep_url}")
                        
                        if episodes:
                            play_from_list.append(source_name)
                            play_url_list.append("#".join(episodes))
            
            # 如果上面的方法没找到，尝试备用方法
            if not play_from_list:
                # 查找所有vodplay链接
                play_links = root.find_all('a', href=re.compile(r'/vodplay/'))
                if play_links:
                    episodes = []
                    for link in play_links:
                        ep_title = link.text.strip()
                        ep_url = link.get('href', '')
                        
                        if ep_title and ep_url:
                            if ep_url.startswith('//'):
                                ep_url = 'https:' + ep_url
                            elif ep_url.startswith('/'):
                                ep_url = self.host + ep_url
                            episodes.append(f"{ep_title}${ep_url}")
                    
                    if episodes:
                        play_from_list = ["播放源"]
                        play_url_list = ["#".join(episodes)]
            
            # 如果仍然没有找到，使用vod_id作为播放地址
            if not play_from_list:
                play_from_list = ["默认播放源"]
                play_url_list = [f"第1集${vod_id}"]
            
            # 7. 从底部的参数区域获取更多信息（备用）
            param_div = root.select_one('.info-parameter')
            if param_div and (not vod_year or not vod_area):
                param_text = param_div.text
                # 提取年份
                year_match = re.search(r'年份[：:]\s*(\d{4})', param_text)
                if year_match and not vod_year:
                    vod_year = year_match.group(1)
                # 提取地区
                area_match = re.search(r'地区[：:]\s*([^<>\n]+)', param_text)
                if area_match and not vod_area:
                    vod_area = area_match.group(1).strip()
            
            # 构建结果
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
            
            print(f"详情页解析完成: {vod_name}")
            print(f"播放源: {play_from_list}")
            print(f"播放地址数量: {len(play_url_list[0].split('#')) if play_url_list else 0}")
            
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
    
    def searchContent(self, key, quick, pg=1):
        """搜索功能"""
        try:
            encoded_key = urllib.parse.quote(key)
            # 搜索URL格式
            search_url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            
            print(f"搜索URL: {search_url}")
            rsp = self.fetch(search_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 搜索结果的视频项应该和分类页类似
            video_items = root.select('.public-list-box')
            
            if not video_items:
                video_items = root.find_all('li', class_=re.compile(r'p[0-9]'))
            
            for item in video_items:
                try:
                    a = item.find('a', class_='public-list-exp')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    
                    # 标题
                    vod_name = a.get('title', '')
                    
                    # 封面
                    vod_pic = ""
                    img = a.find('img', class_='lazy')
                    if img:
                        vod_pic = img.get('data-src', '') or img.get('src', '')
                        if vod_pic:
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            elif vod_pic.startswith('/'):
                                vod_pic = self.host + vod_pic
                    
                    # 备注
                    vod_remarks = ""
                    remark_span = item.find('span', class_='public-list-prb')
                    if remark_span:
                        vod_remarks = remark_span.text.strip()
                    
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
            pagination = root.find('div', class_='pages')
            if pagination:
                page_info = pagination.find('div', class_='page-info')
                if page_info:
                    page_text = page_info.text
                    match = re.search(r'/\s*(\d+)\s*页', page_text)
                    if match:
                        pagecount = int(match.group(1))
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 30,
                "total": len(videos) * pagecount
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
            
            print(f"解析播放地址: {play_url}")
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
            
            # 3. 查找script中的播放地址
            if not video_url:
                script_tags = root.find_all('script')
                for script in script_tags:
                    if script.string:
                        # 尝试匹配m3u8或mp4地址
                        patterns = [
                            r'["\'](https?://[^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'url:\s*["\']([^"\']+)["\']',
                            r'src:\s*["\']([^"\']+)["\']',
                            r'file:\s*["\']([^"\']+)["\']'
                        ]
                        for pattern in patterns:
                            matches = re.findall(pattern, script.string)
                            for match in matches:
                                url = match[0] if isinstance(match, tuple) else match
                                if self.isVideoFormat(url):
                                    video_url = url
                                    break
                            if video_url:
                                break
            
            if video_url and self.isVideoFormat(video_url):
                result["parse"] = 0
                result["url"] = video_url
                print(f"找到直接播放地址: {video_url}")
            else:
                # 如果找不到直接播放地址，让TVBox解析
                result["parse"] = 1
                result["url"] = play_url
                print(f"使用代理解析播放地址: {play_url}")
            
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