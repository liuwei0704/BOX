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
        return "传奇影院"
    
    def init(self, extend=""):
        self.host = "https://www.aqsfybjy.com"
        # 调试模式，True时输出详细信息，False时静默运行
        self.debug_mode = False
        pass
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }
    
    def _debug_print(self, message):
        """调试信息输出"""
        if self.debug_mode:
            print(f"[DEBUG] {message}")
    
    def homeContent(self, filter):
        """返回分类列表"""
        result = {}
        classes = [
            {"type_name": "电影", "type_id": "1"},
            {"type_name": "电视剧", "type_id": "2"},
            {"type_name": "综艺", "type_id": "3"},
            {"type_name": "动漫", "type_id": "4"},
            {"type_name": "动画片", "type_id": "35"},
            {"type_name": "短剧", "type_id": "36"}
        ]
        result["class"] = classes
        return result
    
    def homeVideoContent(self):
        """首页推荐视频"""
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 提取首页所有视频项
            items = root.select('.vod-item')
            
            # 备用选择器
            if not items:
                items = root.select('[class*="vod"][class*="item"]')
            
            for item in items:
                try:
                    # 获取链接
                    a_tag = item.find('a', class_='vod-item-img')
                    if not a_tag:
                        a_tag = item.find('a', href=re.compile(r'/voddetail/'))
                    
                    if not a_tag:
                        continue
                    
                    vod_id = a_tag.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取标题
                    vod_name = ""
                    title_elem = item.find('h3', class_='vod-item-title')
                    if title_elem:
                        title_link = title_elem.find('a')
                        if title_link:
                            vod_name = title_link.get_text(strip=True)
                    
                    # 备用获取标题
                    if not vod_name:
                        vod_name = a_tag.get('title', '')
                        if not vod_name:
                            vod_name = a_tag.get_text(strip=True)
                    
                    # 获取封面图
                    vod_pic = self.extract_image_url(item)
                    
                    # 获取备注
                    vod_remarks = ""
                    remark_elem = item.find('span', class_='vod-item-status')
                    if remark_elem:
                        vod_remarks = remark_elem.get_text(strip=True)
                    
                    # 获取评分
                    score_elem = item.find('span', class_='vod-item-score')
                    if score_elem and score_elem.get_text(strip=True):
                        score = score_elem.get_text(strip=True)
                        vod_remarks = f"{vod_remarks} 评分:{score}" if vod_remarks else f"评分:{score}"
                    
                    # 只添加有标题的视频
                    if vod_name and vod_id:
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": vod_name,
                            "vod_pic": vod_pic,
                            "vod_remarks": vod_remarks
                        })
                        
                except Exception as e:
                    continue
            
            return {"list": videos}
        except Exception as e:
            self._debug_print(f"首页视频加载异常: {e}")
            return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类页面内容 - 增强版"""
        try:
            # 尝试多种URL格式
            url_formats = [
                # 格式1: /vodshow/类型-页码.html
                f"{self.host}/vodshow/{tid}--------{pg if int(pg) > 1 else ''}---.html",
                # 格式2: /vodshow/类型.html?page=页码
                f"{self.host}/vodshow/{tid}.html?page={pg}",
                # 格式3: /vodshow/类型-页码.html
                f"{self.host}/vodshow/{tid}-{pg}.html",
                # 格式4: /list/类型/页码.html
                f"{self.host}/list/{tid}/{pg}.html",
                # 格式5: 首页样式
                f"{self.host}/?type={tid}&page={pg}",
                # 格式6: /index.php/vod/show/类型/页码
                f"{self.host}/index.php/vod/show/id/{tid}/page/{pg}.html"
            ]
            
            rsp = None
            final_url = ""
            
            for url in url_formats:
                try:
                    self._debug_print(f"尝试分类URL: {url}")
                    rsp = self.fetch(url, headers=self.header())
                    if rsp.status_code == 200 and len(rsp.text) > 500:
                        final_url = url
                        self._debug_print(f"成功使用URL: {url}")
                        break
                except Exception as e:
                    self._debug_print(f"URL {url} 失败: {e}")
                    continue
            
            if not rsp or rsp.status_code != 200:
                self._debug_print("所有分类URL格式都失败")
                return {
                    "list": [],
                    "page": int(pg),
                    "pagecount": 1,
                    "limit": 20,
                    "total": 0
                }
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 方法1: 尝试多种选择器
            selectors = [
                '.vod-item',
                '.module-item',
                '.video-item',
                '.movie-item',
                '.film-item',
                '.stui-vodlist li',
                '.stui-vodlist__box',
                '.module-card-item',
                '.module-list-item',
                '.col-lg-2',
                '.col-md-3',
                '.col-sm-4',
                '.col-xs-6',
                '[class*="vod"][class*="item"]',
                '[class*="video"][class*="item"]',
                'div[class*="vod"]',
                'div[class*="item"]'
            ]
            
            items = []
            for selector in selectors:
                found = root.select(selector)
                if found and len(found) > 3:  # 确保找到足够多的项目
                    self._debug_print(f"使用选择器 '{selector}' 找到 {len(found)} 个项目")
                    items = found
                    break
            
            # 方法2: 如果没有找到，尝试通过class名查找
            if not items:
                all_divs = root.find_all('div', class_=True)
                for div in all_divs:
                    classes = ' '.join(div.get('class', [])).lower()
                    if ('vod' in classes or 'video' in classes) and ('item' in classes or 'box' in classes):
                        items.append(div)
                self._debug_print(f"通过class名找到 {len(items)} 个项目")
            
            # 方法3: 查找所有包含视频详情的链接
            if len(items) < 5:  # 如果找到的项目太少
                all_links = root.find_all('a', href=re.compile(r'/voddetail/|/detail/'))
                for link in all_links:
                    parent = link.parent
                    if parent and parent not in items:
                        items.append(parent)
                self._debug_print(f"通过voddetail链接找到 {len(items)} 个项目")
            
            # 处理找到的项目
            processed_urls = set()
            
            for item in items[:40]:  # 限制最多处理40个
                try:
                    # 获取链接 - 多种方式
                    a_tag = None
                    
                    # 方式1: 查找vod-item-img类
                    a_tag = item.find('a', class_='vod-item-img')
                    
                    # 方式2: 查找任何包含voddetail的链接
                    if not a_tag:
                        a_tags = item.find_all('a', href=re.compile(r'/voddetail/|/detail/'))
                        if a_tags:
                            a_tag = a_tags[0]
                    
                    # 方式3: 查找任何有href的a标签
                    if not a_tag:
                        a_tag = item.find('a', href=True)
                    
                    if not a_tag:
                        continue
                    
                    vod_id = a_tag.get('href', '')
                    if not vod_id:
                        continue
                    
                    # 检查是否已处理过
                    if vod_id in processed_urls:
                        continue
                    
                    # 规范化URL
                    if not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取标题 - 多种方式
                    vod_name = ""
                    
                    # 方式1: 从a标签的title属性
                    vod_name = a_tag.get('title', '')
                    
                    # 方式2: 查找标题元素
                    if not vod_name:
                        for tag_name in ['h3', 'h4', 'h5', 'strong', 'p']:
                            title_elem = item.find(tag_name)
                            if title_elem:
                                vod_name = title_elem.get_text(strip=True)
                                if vod_name:
                                    break
                    
                    # 方式3: 从a标签文本
                    if not vod_name:
                        vod_name = a_tag.get_text(strip=True)
                    
                    # 方式4: 查找任何文本内容
                    if not vod_name or len(vod_name) < 2:
                        all_text = item.get_text(' ', strip=True)
                        text_parts = all_text.split()
                        for text in text_parts:
                            if 2 < len(text) < 30:
                                vod_name = text
                                break
                    
                    # 获取封面图
                    vod_pic = self.extract_image_url(item)
                    
                    # 获取备注
                    vod_remarks = ""
                    for class_name in ['vod-item-status', 'status', 'remark', 'note', 'tag', 'label']:
                        remark_elem = item.find('span', class_=class_name)
                        if not remark_elem:
                            remark_elem = item.find('div', class_=class_name)
                        if remark_elem:
                            vod_remarks = remark_elem.get_text(strip=True)
                            break
                    
                    # 获取评分
                    score_text = ""
                    for class_name in ['vod-item-score', 'score', 'rating', 'douban']:
                        score_elem = item.find('span', class_=class_name)
                        if not score_elem:
                            score_elem = item.find('div', class_=class_name)
                        if score_elem:
                            score_text = score_elem.get_text(strip=True)
                            break
                    
                    # 添加评分到备注
                    if score_text:
                        vod_remarks = f"{vod_remarks} 评分:{score_text}" if vod_remarks else f"评分:{score_text}"
                    
                    # 确保有有效的标题
                    if vod_name and len(vod_name.strip()) > 1 and vod_id:
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": vod_name.strip(),
                            "vod_pic": vod_pic,
                            "vod_remarks": vod_remarks.strip()
                        })
                        processed_urls.add(vod_id)
                        
                except Exception as e:
                    continue
            
            # 如果还是没找到，尝试直接解析页面内容
            if len(videos) < 5:
                self._debug_print("视频数量不足，尝试直接解析页面内容")
                # 查找所有可能的视频区块
                for container in ['div.module-list', 'div.vod-list', 'div.list-wrap', 'ul.vod-list', 'div.module-row', 'div.video-list']:
                    container_elems = root.select(container)
                    for container_elem in container_elems:
                        links = container_elem.find_all('a', href=re.compile(r'/voddetail/|/detail/'))
                        for link in links[:20]:
                            try:
                                vod_id = link.get('href', '')
                                if vod_id and vod_id not in processed_urls:
                                    if not vod_id.startswith('http'):
                                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                                    
                                    vod_name = link.get('title', '')
                                    if not vod_name:
                                        vod_name = link.get_text(strip=True)
                                    
                                    if vod_name and vod_id:
                                        videos.append({
                                            "vod_id": vod_id,
                                            "vod_name": vod_name,
                                            "vod_pic": "",
                                            "vod_remarks": ""
                                        })
                                        processed_urls.add(vod_id)
                            except:
                                continue
            
            self._debug_print(f"最终找到 {len(videos)} 个视频")
            
            # 分页信息
            pagecount = max(int(pg) + 1, 10)  # 默认10页
            
            # 查找分页元素
            for selector in ['ul.pagination', 'div.pagination', 'div.page', 'div.pages', 'div.page-nav', 'div.module-pagination']:
                pagination = root.select_one(selector)
                if pagination:
                    page_numbers = []
                    for link in pagination.find_all('a'):
                        text = link.get_text(strip=True)
                        if text.isdigit():
                            page_numbers.append(int(text))
                    
                    if page_numbers:
                        pagecount = max(page_numbers)
                        self._debug_print(f"从分页找到最大页码: {pagecount}")
                    break
            
            # 如果没有找到分页，根据当前页码估算
            if pagecount <= int(pg):
                pagecount = int(pg) + 5
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 20,
                "total": len(videos) * pagecount if videos else 0
            }
            
        except Exception as e:
            self._debug_print(f"分类页面异常: {e}")
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }
    
    def extract_image_url(self, item):
        """提取图片URL的通用方法 - 增强版"""
        vod_pic = ""
        
        # 方法1: 查找lazyload的div
        img_wrapper = item.find('div', class_=re.compile(r'(lazyload|img-wrapper|vod-pic|thumb|image|pic|cover)'))
        if img_wrapper:
            # 优先使用data-original
            if 'data-original' in img_wrapper.attrs:
                vod_pic = img_wrapper['data-original']
            # 备选：使用data-background
            elif 'data-background' in img_wrapper.attrs:
                vod_pic = img_wrapper['data-background']
            # 备选：使用data-src
            elif 'data-src' in img_wrapper.attrs:
                vod_pic = img_wrapper['data-src']
            # 备选：使用style中的background-image
            elif 'style' in img_wrapper.attrs:
                style = img_wrapper['style']
                patterns = [
                    r'background-image:\s*url\(([^)]+)\)',
                    r'background:\s*url\(([^)]+)\)',
                    r'url\(([^)]+)\)'
                ]
                for pattern in patterns:
                    match = re.search(pattern, style)
                    if match:
                        vod_pic = match.group(1).strip('\'"')
                        break
        
        # 方法2: 如果没有找到，查找img标签
        if not vod_pic:
            img_tag = item.find('img')
            if img_tag:
                # 按优先级获取图片URL
                for attr in ['data-original', 'data-src', 'src', 'data-url', 'data-source']:
                    if attr in img_tag.attrs:
                        vod_pic = img_tag[attr]
                        break
        
        # 方法3: 查找任何有data-original或data-src属性的元素
        if not vod_pic:
            for attr in ['data-original', 'data-src', 'data-url', 'data-image']:
                any_elem = item.find(attrs={attr: True})
                if any_elem:
                    vod_pic = any_elem[attr]
                    break
        
        # 处理图片URL
        if vod_pic:
            # 移除可能的前后引号
            vod_pic = vod_pic.strip('\'"')
            
            if vod_pic.startswith('//'):
                vod_pic = 'https:' + vod_pic
            elif not vod_pic.startswith('http'):
                if vod_pic.startswith('/'):
                    vod_pic = self.host + vod_pic
                else:
                    # 相对路径，尝试拼接基础URL
                    vod_pic = self.host + '/' + vod_pic.lstrip('/')
            
            # 过滤掉非图片的URL
            if not any(ext in vod_pic.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                if '?' in vod_pic:
                    vod_pic = vod_pic.split('?')[0]
        
        return vod_pic
    
    def detailContent(self, ids):
        """视频详情页 - 针对电视剧多集情况优化版"""
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                url = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
            else:
                url = vod_id
            
            self._debug_print(f"详情页URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 解析基本信息
            vod_name = ""
            title_elem = root.select_one('.detail-info-title')
            if title_elem:
                vod_name = title_elem.get_text(strip=True)
            
            # 备用标题获取
            if not vod_name:
                title_elem = root.find('h1')
                if title_elem:
                    vod_name = title_elem.get_text(strip=True)
            
            # 封面图 - 从detail-img获取
            vod_pic = ""
            detail_img = root.select_one('.detail-img img')
            if detail_img and 'data-original' in detail_img.attrs:
                vod_pic = detail_img['data-original']
            elif detail_img and 'src' in detail_img.attrs:
                vod_pic = detail_img['src']
            
            # 处理封面图URL
            if vod_pic:
                vod_pic = vod_pic.strip()
                if vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
                elif not vod_pic.startswith('http'):
                    if vod_pic.startswith('/'):
                        vod_pic = self.host + vod_pic
                    else:
                        vod_pic = self.host + '/' + vod_pic
            
            # 描述
            vod_content = ""
            # 从描述区域获取
            desc_content = root.select_one('.detail-desc-content')
            if desc_content:
                vod_content = desc_content.get_text(strip=True, separator=' ')
            
            # 从meta description获取备用
            if not vod_content:
                meta_desc = root.find('meta', attrs={'name': 'description'})
                if meta_desc and 'content' in meta_desc.attrs:
                    vod_content = meta_desc['content']
            
            # 解析详细信息列表
            vod_year = ""
            vod_actor = ""
            vod_director = ""
            vod_area = ""
            vod_remarks = ""
            
            # 查找所有详情信息项
            desc_items = root.select('.detail-info-desc li')
            for item in desc_items:
                text = item.get_text(strip=True)
                if '年份：' in text:
                    vod_year = text.replace('年份：', '').strip()
                elif '主演：' in text:
                    # 提取演员，去掉a标签
                    actor_text = item.get_text(strip=True, separator=' ')
                    vod_actor = actor_text.replace('主演：', '').strip()
                elif '导演：' in text:
                    director_text = item.get_text(strip=True, separator=' ')
                    vod_director = director_text.replace('导演：', '').strip()
                elif '地区：' in text:
                    vod_area = text.replace('地区：', '').strip()
                elif '状态：' in text:
                    vod_remarks = text.replace('状态：', '').strip()
            
            # 解析播放源 - 针对传奇影院结构优化，支持多集电视剧
            play_from_list = []
            play_url_list = []
            
            # 查找播放列表区域
            playlist_box = root.select_one('.episode-box')
            if playlist_box:
                # 播放源名称
                source_name = "高清云播"
                source_title = root.select_one('.playlist-tab-box .tab-item.active a')
                if source_title:
                    source_name = source_title.get_text(strip=True)
                
                # 播放列表
                episodes = []
                # 查找播放链接
                ep_links = playlist_box.find_all('a', href=True)
                self._debug_print(f"找到 {len(ep_links)} 个剧集链接")
                
                for ep_link in ep_links:
                    ep_title = ep_link.get_text(strip=True)
                    ep_url = ep_link['href']
                    
                    if ep_url and not ep_url.startswith('http'):
                        ep_url = self.host + ep_url if ep_url.startswith('/') else self.host + '/' + ep_url
                    
                    if ep_title and ep_url:
                        # 清理剧集标题
                        ep_title = ep_title.strip()
                        episodes.append(f"{ep_title}${ep_url}")
                
                if episodes:
                    play_from_list.append(source_name)
                    play_url_list.append("#".join(episodes))
                    self._debug_print(f"找到播放源: {source_name}, 共 {len(episodes)} 集")
            
            # 如果没有找到播放列表，尝试查找立即播放按钮
            if not play_from_list:
                play_btn = root.select_one('.detail-info-btn a[href*="/vodplay/"]')
                if play_btn:
                    ep_url = play_btn['href']
                    if not ep_url.startswith('http'):
                        ep_url = self.host + ep_url if ep_url.startswith('/') else ep_url
                    
                    if ep_url:
                        play_from_list = ["默认播放源"]
                        play_url_list = [f"立即播放${ep_url}"]
                        self._debug_print(f"找到立即播放按钮: {ep_url}")
            
            # 构建结果
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name if vod_name else "未知视频",
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": vod_year,
                "vod_actor": vod_actor,
                "vod_director": vod_director,
                "vod_area": vod_area,
                "vod_remarks": vod_remarks,
                "vod_play_from": "$$$".join(play_from_list) if play_from_list else "默认",
                "vod_play_url": "$$$".join(play_url_list) if play_url_list else f"第1集${url}"
            }
            
            # 输出调试信息
            self._debug_print(f"视频详情: {vod_name}")
            self._debug_print(f"封面: {vod_pic}")
            self._debug_print(f"播放源: {play_from_list}")
            self._debug_print(f"剧集数: {len(ep_links) if 'ep_links' in locals() else 0}")
            
            return {"list": [video]}
            
        except Exception as e:
            self._debug_print(f"详情页异常: {e}")
            video = {
                "vod_id": ids[0],
                "vod_name": "加载失败",
                "vod_pic": "",
                "vod_content": str(e),
                "vod_play_from": "默认",
                "vod_play_url": f"第1集${self.host}"
            }
            return {"list": [video]}
    
    def searchContent(self, key, quick, pg=1):
        """搜索功能 - 增强版"""
        try:
            encoded_key = urllib.parse.quote(key)
            
            # 多种搜索URL格式
            if int(pg) == 1:
                search_urls = [
                    f"{self.host}/vodsearch/{encoded_key}-------------.html",
                    f"{self.host}/index.php/vod/search/page/{pg}/wd/{encoded_key}.html",
                    f"{self.host}/search/{encoded_key}/{pg}.html"
                ]
            else:
                search_urls = [
                    f"{self.host}/vodsearch/{encoded_key}-------------{pg}---.html",
                    f"{self.host}/index.php/vod/search/page/{pg}/wd/{encoded_key}.html",
                    f"{self.host}/search/{encoded_key}/{pg}.html"
                ]
            
            rsp = None
            for search_url in search_urls:
                try:
                    self._debug_print(f"尝试搜索URL: {search_url}")
                    rsp = self.fetch(search_url, headers=self.header())
                    if rsp.status_code == 200 and len(rsp.text) > 500:
                        self._debug_print(f"使用搜索URL: {search_url}")
                        break
                except:
                    continue
            
            if not rsp or rsp.status_code != 200:
                return {"list": []}
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 解析搜索结果 - 根据你提供的HTML结构修改
            result_items = root.select('.search-item')
            
            # 如果没有找到.search-item，尝试其他选择器
            if not result_items:
                result_items = root.select('.search-list .row')
            
            if not result_items:
                result_items = root.select('.vod-item, .module-search-item, .video-item')
            
            self._debug_print(f"找到 {len(result_items)} 个搜索结果项")
            
            for item in result_items:
                try:
                    # 查找详情链接
                    detail_link = item.find('a', href=re.compile(r'/voddetail/'))
                    if not detail_link:
                        # 查找任何包含voddetail的链接
                        detail_links = item.find_all('a', href=re.compile(r'/voddetail/'))
                        if detail_links:
                            detail_link = detail_links[0]
                    
                    if not detail_link:
                        continue
                    
                    vod_id = detail_link.get('href', '')
                    if not vod_id:
                        continue
                    
                    # 规范化URL
                    if not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取标题
                    vod_name = detail_link.get('title', '')
                    
                    # 如果从title属性没有获取到，尝试从文本内容获取
                    if not vod_name:
                        title_elem = item.select_one('.search-item-title, h2, h3')
                        if title_elem:
                            vod_name = title_elem.get_text(strip=True)
                        else:
                            # 从链接文本获取
                            vod_name = detail_link.get_text(strip=True)
                    
                    # 清理标题
                    vod_name = re.sub(r'[\s\n\r]+', ' ', vod_name).strip()
                    
                    # 获取封面图
                    vod_pic = ""
                    img_wrapper = item.select_one('.img-wrapper.lazyload, .search-item-cover')
                    if img_wrapper and 'data-original' in img_wrapper.attrs:
                        vod_pic = img_wrapper['data-original']
                    
                    # 如果没有找到，查找img标签
                    if not vod_pic:
                        img_tag = item.find('img')
                        if img_tag:
                            for attr in ['data-original', 'src', 'data-src']:
                                if attr in img_tag.attrs:
                                    vod_pic = img_tag[attr]
                                    break
                    
                    # 处理封面图URL
                    if vod_pic:
                        vod_pic = vod_pic.strip()
                        if vod_pic.startswith('//'):
                            vod_pic = 'https:' + vod_pic
                        elif not vod_pic.startswith('http'):
                            if vod_pic.startswith('/'):
                                vod_pic = self.host + vod_pic
                            else:
                                vod_pic = self.host + '/' + vod_pic
                    
                    # 获取描述信息
                    vod_remarks = ""
                    
                    # 尝试从描述信息中提取年份和地区
                    desc_elem = item.select_one('.search-item-desc')
                    if desc_elem:
                        desc_text = desc_elem.get_text(strip=True, separator=' ')
                        # 查找年份信息
                        year_match = re.search(r'(\d{4})\s*[|/]\s*([^/\s]+)', desc_text)
                        if year_match:
                            vod_remarks = f"{year_match.group(1)}/{year_match.group(2)}"
                        
                        # 如果没找到年份，查找状态信息
                        status_match = re.search(r'状态[:：]\s*([^\s]+)', desc_text)
                        if status_match:
                            vod_remarks = status_match.group(1)
                    
                    # 添加结果
                    if vod_name and vod_id:
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": vod_name,
                            "vod_pic": vod_pic,
                            "vod_remarks": vod_remarks
                        })
                        self._debug_print(f"添加搜索结果: {vod_name}")
                        
                except Exception as e:
                    self._debug_print(f"解析搜索结果项异常: {e}")
                    continue
            
            # 如果没有找到结果，尝试备用解析方法
            if not videos:
                self._debug_print("尝试备用解析方法")
                # 查找所有voddetail链接
                all_links = root.find_all('a', href=re.compile(r'/voddetail/'))
                for link in all_links[:20]:  # 限制最多20个
                    try:
                        vod_id = link.get('href', '')
                        if vod_id and not vod_id.startswith('http'):
                            vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                        
                        vod_name = link.get('title', '')
                        if not vod_name:
                            vod_name = link.get_text(strip=True)
                        
                        if vod_name and vod_id:
                            videos.append({
                                "vod_id": vod_id,
                                "vod_name": vod_name,
                                "vod_pic": "",
                                "vod_remarks": ""
                            })
                    except:
                        continue
            
            # 分页信息
            pagecount = int(pg)
            
            # 查找分页元素
            pagination = root.select_one('.ewave-page, ul.pagination, div.pagination, div.page, div.pages')
            if pagination:
                page_links = pagination.find_all('a')
                max_page = int(pg)
                for link in page_links:
                    text = link.get_text(strip=True)
                    if text.isdigit():
                        page_num = int(text)
                        if page_num > max_page:
                            max_page = page_num
                
                # 如果没有找到数字页码，尝试从省略号后的链接获取
                if max_page == int(pg):
                    last_link = page_links[-1] if page_links else None
                    if last_link and 'href' in last_link.attrs:
                        href = last_link['href']
                        # 从URL中提取页码
                        page_match = re.search(r'(\d+)(?:---\.html|/page/\d+\.html|\.html\?page=\d+)', href)
                        if page_match:
                            max_page = int(page_match.group(1))
                
                if max_page > pagecount:
                    pagecount = max_page
            
            # 如果仍然只有当前页，根据总结果数估算
            if pagecount == int(pg):
                # 尝试从页面文本中获取总页数
                total_text = root.find(string=re.compile(r'共\d+条'))
                if total_text:
                    total_match = re.search(r'共(\d+)条', total_text)
                    if total_match:
                        total_count = int(total_match.group(1))
                        pagecount = (total_count + 19) // 20  # 每页20条
            
            self._debug_print(f"搜索 '{key}' 第 {pg} 页，找到 {len(videos)} 个结果，共 {pagecount} 页")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": max(pagecount, int(pg) + 1),
                "limit": 20,
                "total": len(videos) * pagecount if videos else 0
            }
            
        except Exception as e:
            self._debug_print(f"搜索异常: {e}")
            return {"list": []}
    
    def playerContent(self, flag, id, vipFlags):
        """解析播放地址 - 针对传奇影院播放页面优化版"""
        result = {}
        
        try:
            if not id.startswith('http'):
                play_url = self.host + id if id.startswith('/') else self.host + '/' + id
            else:
                play_url = id
            
            self._debug_print(f"播放页URL: {play_url}")
            rsp = self.fetch(play_url, headers=self.header())
            html_content = rsp.text
            
            # 从HTML中直接提取播放地址
            video_url = None
            
            # 方法1: 从JavaScript变量中提取播放地址
            # 在HTML中搜索 player_aaaa 对象
            player_patterns = [
                # 直接匹配 player_aaaa 对象
                r'var player_aaaa\s*=\s*({[^}]+});',
                r'player_aaaa\s*=\s*({[^}]+});',
                r'var player_aaaa\s*=\s*({[^}]+})',
                # 匹配包含url的JSON对象
                r'"url"\s*:\s*"([^"]+)"',
                r"'url'\s*:\s*'([^']+)'",
                # 匹配m3u8地址
                r'https?://[^\s"\']+\.m3u8[^\s"\']*',
                r'https?://[^\s"\']+\.mp4[^\s"\']*',
                # 匹配unescape编码的地址
                r'unescape\(\s*["\']([^"\']+)["\']',
                # 匹配playurl
                r'playurl\s*=\s*["\']([^"\']+)["\']',
                r'url\s*=\s*["\']([^"\']+)["\']',
                r'file\s*=\s*["\']([^"\']+)["\']',
                r'src\s*=\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in player_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, str):
                        # 如果是完整的player_aaaa对象
                        if match.startswith('{'):
                            try:
                                # 解析JSON对象
                                player_data = json.loads(match.replace("'", '"'))
                                if 'url' in player_data:
                                    video_url = player_data['url']
                                    self._debug_print(f"从player_aaaa对象找到URL: {video_url}")
                                    break
                            except:
                                # 如果不是合法的JSON，继续尝试其他模式
                                continue
                        # 如果是直接的URL
                        elif 'http' in match and any(ext in match for ext in ['.m3u8', '.mp4', '.flv', '.ts']):
                            video_url = match
                            self._debug_print(f"从正则匹配找到URL: {video_url}")
                            break
            
            # 方法2: 如果没有找到，尝试BeautifulSoup解析
            if not video_url:
                root = BeautifulSoup(html_content, 'html.parser')
                
                # 查找script标签中的播放地址
                script_tags = root.find_all('script')
                for script in script_tags:
                    if script.string:
                        content = script.string
                        # 尝试匹配各种播放地址格式
                        url_patterns = [
                            r'"url"\s*:\s*"([^"]+\.(m3u8|mp4)[^"]*)"',
                            r"'url'\s*:\s*'([^']+\.(m3u8|mp4)[^']*)'",
                            r'url\s*=\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'file\s*=\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'src\s*=\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'player_aaaa\s*=\s*{.*?"url"\s*:\s*"([^"]+)"',
                            r"player_aaaa\s*=\s*{.*?'url'\s*:\s*'([^']+)'"
                        ]
                        
                        for pattern in url_patterns:
                            url_match = re.search(pattern, content, re.DOTALL)
                            if url_match:
                                video_url = url_match.group(1)
                                self._debug_print(f"从script标签找到URL: {video_url}")
                                break
                        if video_url:
                            break
            
            # 方法3: 查找iframe
            if not video_url:
                root = BeautifulSoup(html_content, 'html.parser')
                iframe = root.find('iframe', src=True)
                if iframe:
                    video_url = iframe['src']
                    self._debug_print(f"找到iframe: {video_url}")
            
            # 方法4: 查找video标签
            if not video_url:
                root = BeautifulSoup(html_content, 'html.parser')
                video_tag = root.find('video')
                if video_tag and video_tag.get('src'):
                    video_url = video_tag['src']
                    self._debug_print(f"找到video标签: {video_url}")
            
            # 方法5: 查找source标签
            if not video_url:
                root = BeautifulSoup(html_content, 'html.parser')
                source_tag = root.find('source', src=True)
                if source_tag:
                    video_url = source_tag['src']
                    self._debug_print(f"找到source标签: {video_url}")
            
            # 处理找到的视频URL
            if video_url:
                # 处理相对路径
                if not video_url.startswith('http'):
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    elif video_url.startswith('/'):
                        video_url = self.host + video_url
                    else:
                        # 相对路径
                        base_url = play_url.rsplit('/', 1)[0]
                        video_url = base_url + '/' + video_url
                
                # 解码可能的URL编码
                try:
                    video_url = urllib.parse.unquote(video_url)
                except:
                    pass
                
                result["parse"] = 0
                result["url"] = video_url
                result["header"] = self.header()
                self._debug_print(f"最终播放地址: {video_url}")
                
                # 如果是m3u8地址，添加特定的header
                if '.m3u8' in video_url:
                    result["header"]["User-Agent"] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    result["header"]["Referer"] = self.host
            else:
                # 如果找不到直接播放地址，让TVBox解析
                self._debug_print("未找到直接播放地址，启用解析")
                result["parse"] = 1
                result["url"] = play_url
                result["header"] = self.header()
            
        except Exception as e:
            self._debug_print(f"播放地址解析异常: {e}")
            result["parse"] = 1
            result["url"] = id
            result["header"] = self.header()
        
        return result
    
    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        video_formats = ['.m3u8', '.mp4', '.avi', '.mkv', '.flv', '.ts', '.webm', '.mpeg', '.mov']
        return any(fmt in url.lower() for fmt in video_formats)
    
    def localProxy(self, params):
        """本地代理"""
        return [200, "video/MP2T", ""]