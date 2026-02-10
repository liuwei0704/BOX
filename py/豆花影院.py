# -*- coding: utf-8 -*-
import re
import sys
import json
import urllib.parse
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):

    def init(self, extend=""):
        pass

    def getName(self):
        return "豆花影院"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    # ------------------------- 网站配置 -------------------------
    host = 'https://www.widiz.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.widiz.com/',
        'Connection': 'keep-alive',
    }

    # ------------------------- 通用工具方法 -------------------------
    def _normalize_url(self, url):
        """标准化URL：处理相对路径、协议缺失等"""
        if not url:
            return url
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{self.host}{url}"
        return url

    def _extract_video_basic(self, item):
        """从列表项提取视频基本信息"""
        try:
            # 查找视频链接
            detail_link = None
            
            # 1. 查找详情页链接（通常是h4.title下的a标签）
            title_link = item('h4.title a')
            if title_link:
                detail_link = title_link.attr('href')
            
            # 2. 如果没有找到，查找thumb-link
            if not detail_link:
                thumb_link = item('a.thumb-link')
                if thumb_link:
                    detail_link = thumb_link.attr('href')
            
            # 3. 如果没有找到，查找其他可能的链接
            if not detail_link:
                all_links = item('a')
                for link in all_links.items():
                    href = link.attr('href')
                    if href and ('/remen/' in href or '/vod/' in href or 'widiz.com' in href):
                        detail_link = href
                        break
            
            if not detail_link:
                # 尝试父元素查找
                parent = item.parents('li')
                if parent:
                    parent_link = parent('h4.title a') or parent('a.thumb-link')
                    if parent_link:
                        detail_link = parent_link.attr('href')
            
            if not detail_link:
                return None
            
            detail_link = self._normalize_url(detail_link)
            
            # 提取标题
            title = ''
            # 1. 从h4.title提取
            title_elem = item('h4.title a')
            if title_elem:
                title = title_elem.attr('title') or title_elem.text().strip()
            
            # 2. 从缩略图提取
            if not title:
                thumb_elem = item('.ewave-vodlist__thumb')
                if thumb_elem:
                    title = thumb_elem.attr('title') or thumb_elem.attr('alt') or ''
            
            # 3. 从父元素提取
            if not title:
                parent = item.parents('li')
                if parent:
                    parent_title = parent('h4.title a')
                    if parent_title:
                        title = parent_title.attr('title') or parent_title.text().strip()
            
            if not title:
                return None
            
            # 提取图片
            img = ''
            thumb_elem = item('.ewave-vodlist__thumb')
            if thumb_elem:
                img = thumb_elem.attr('data-original') or thumb_elem.attr('src')
                if not img:
                    img = thumb_elem.attr('data-src')
            
            if img:
                img = self._normalize_url(img)
            
            # 提取备注/状态
            remarks = ''
            remark_elem = item('.pic-text')
            if remark_elem:
                remarks = remark_elem.text().strip()
            
            # 提取评分
            score = ''
            score_elem = item('.pic-tag-h')
            if score_elem:
                score = score_elem.text().strip()
            
            # 提取演员信息
            actor = ''
            actor_elem = item('.text-actor')
            if actor_elem:
                actor_text = actor_elem.text().strip()
                # 清理演员文本
                if actor_text and actor_text != '&nbsp;':
                    actor = actor_text.replace('&nbsp;', '').strip()
            elif item.parents('li'):
                # 从父元素查找演员信息
                parent = item.parents('li')
                parent_actor = parent('.text-actor')
                if parent_actor:
                    actor_text = parent_actor.text().strip()
                    if actor_text and actor_text != '&nbsp;':
                        actor = actor_text.replace('&nbsp;', '').strip()

            return {
                'vod_id': detail_link,
                'vod_name': title,
                'vod_pic': img,
                'vod_remarks': remarks,
                'vod_actor': actor,
                'vod_year': '',
                'vod_score': score
            }
        except Exception as e:
            return None

    def _extract_search_result(self, item):
        """从搜索结果项提取视频信息"""
        try:
            # 查找详情页链接
            detail_link = item('h3.title a').attr('href')
            if not detail_link:
                detail_link = item('a.v-thumb').attr('href')
            
            if not detail_link:
                return None
            
            detail_link = self._normalize_url(detail_link)
            
            # 提取标题
            title = item('h3.title a').text().strip()
            if not title:
                title = item('a.v-thumb').attr('title') or ''
            
            if not title:
                return None
            
            # 提取图片
            img = item('a.v-thumb').attr('data-original') or item('a.v-thumb').attr('src')
            if img:
                img = self._normalize_url(img)
            
            # 提取备注/状态
            remarks = item('.pic-text').text().strip()
            
            # 提取演员信息
            actor = ''
            actor_elem = item('p:contains("主演：")')
            if actor_elem:
                actor_text = actor_elem.text().replace('主演：', '').strip()
                if actor_text:
                    actor = actor_text
            
            # 提取导演信息
            director = ''
            director_elem = item('p:contains("导演：")')
            if director_elem:
                director_text = director_elem.text().replace('导演：', '').strip()
                if director_text:
                    director = director_text
            
            return {
                'vod_id': detail_link,
                'vod_name': title,
                'vod_pic': img or '',
                'vod_remarks': remarks,
                'vod_actor': actor,
                'vod_year': '',
                'vod_score': '',
                'vod_director': director
            }
        except Exception as e:
            print(f"提取搜索结果错误: {e}")
            return None

    def getpq(self, text):
        """创建PyQuery对象，处理编码问题"""
        try:
            return pq(text)
        except:
            try:
                return pq(text.encode('utf-8'))
            except:
                return pq('')

    # ------------------------- 分类系统 -------------------------
    def _get_categories(self):
        """获取网站分类"""
        categories = []
        
        # 主分类
        main_categories = [
            {'name': '电影', 'url': 'https://www.widiz.com/show/1--------1---.html'},
            {'name': '电视剧', 'url': 'https://www.widiz.com/show/2--------1---.html'},
            {'name': '综艺', 'url': 'https://www.widiz.com/show/3--------1---.html'},
            {'name': '动漫', 'url': 'https://www.widiz.com/show/4--------1---.html'},
            {'name': '短剧片', 'url': 'https://www.widiz.com/show/30--------1---.html'},
        ]
        
        for cat in main_categories:
            categories.append({
                'type_name': cat['name'],
                'type_id': cat['url']
            })
        
        return categories

    # ------------------------- 主要功能方法 -------------------------
    def homeContent(self, filter):
        """首页：分类 + 推荐列表"""
        try:
            # 获取分类
            categories = self._get_categories()
            
            # 获取首页内容（显示电影分类的第一页）
            home_url = 'https://www.widiz.com/show/1--------1---.html'
            
            response = self.fetch(home_url, headers=self.headers)
            if not response or not response.text:
                return {'class': categories, 'list': []}
            
            data = self.getpq(response.text)
            
            # 获取首页视频列表
            videos = []
            
            # 方法1：直接查找视频列表项
            video_items = data('li .ewave-vodlist__box')
            if not video_items:
                # 方法2：查找所有视频项
                video_items = data('.ewave-vodlist__box')
            
            if not video_items:
                # 方法3：查找列表项
                video_items = data('li.col-md-6.col-sm-4.col-xs-3')
            
            for item in video_items.items():
                video_info = self._extract_video_basic(item)
                if video_info:
                    videos.append(video_info)
            
            return {
                'class': categories,
                'list': videos
            }
        except Exception as e:
            print(f"首页错误: {e}")
            return {'class': [], 'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        """分类页内容"""
        try:
            print(f"分类请求: tid={tid}, pg={pg}")
            
            # 处理分页
            url = tid
            
            # 如果URL中包含页码占位符，替换它
            if '--------' in tid:
                # 构建新的URL，替换页码部分
                # 查找并替换页码
                match = re.search(r'--------(\d+)---', tid)
                if match:
                    url = tid.replace(match.group(0), f'--------{pg}---')
                else:
                    # 如果没有页码，添加页码
                    if tid.endswith('.html'):
                        base_url = tid[:-5]  # 去掉.html
                        url = f"{base_url}--------{pg}---.html"
            else:
                # 对于其他格式的URL，直接添加页码参数
                if '?' in url:
                    url = f"{url}&page={pg}"
                else:
                    url = f"{url}?page={pg}"
            
            print(f"分类页URL: {url}")
            
            # 获取分类页内容
            response = self.fetch(url, headers=self.headers)
            if not response or not response.text:
                return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}
            
            html_content = response.text
            data = self.getpq(html_content)
            
            # 提取视频列表 - 多种选择器尝试
            videos = []
            
            # 方法1：标准选择器
            video_items = data('li .ewave-vodlist__box')
            
            # 方法2：如果没找到，尝试其他选择器
            if not video_items:
                video_items = data('.ewave-vodlist__box')
            
            # 方法3：查找列表项
            if not video_items:
                video_items = data('li.col-md-6.col-sm-4.col-xs-3')
            
            # 方法4：查找所有可能的视频项
            if not video_items:
                video_items = data('.vodlist li, .item, .movie-item, .video-item')
            
            print(f"找到 {len(video_items)} 个视频项")
            
            for item in video_items.items():
                video_info = self._extract_video_basic(item)
                if video_info:
                    videos.append(video_info)
            
            print(f"成功提取 {len(videos)} 个视频")
            
            # 提取分页信息
            pagecount = int(pg)
            
            # 查找分页元素
            page_elements = data('.ewave-page a, .pagination a, .page a')
            
            # 查找最大页码
            max_page = int(pg)
            for page_elem in page_elements.items():
                href = page_elem.attr('href')
                if href:
                    # 尝试提取页码
                    patterns = [
                        r'--------(\d+)---',
                        r'page=(\d+)',
                        r'p=(\d+)',
                        r'/page/(\d+)',
                        r'-(\d+)\.html$'
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
            
            # 检查尾页
            last_page_elem = data('a:contains("尾页")')
            if last_page_elem:
                href = last_page_elem.attr('href')
                if href:
                    match = re.search(r'--------(\d+)---', href)
                    if match:
                        try:
                            pagecount = int(match.group(1))
                        except:
                            pagecount = max_page
            
            # 如果没有找到尾页，使用最大页码
            if pagecount <= int(pg):
                pagecount = max_page
            
            # 确保至少有一页
            if pagecount < int(pg):
                pagecount = int(pg)
            
            # 如果没有找到任何分页信息，设置一个默认值
            if pagecount <= int(pg):
                pagecount = int(pg) + 1
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 30,
                'total': 999999
            }
        except Exception as e:
            print(f"分类页错误: {e}")
            import traceback
            traceback.print_exc()
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}

    def detailContent(self, ids):
        """详情页：提取视频详情、播放列表"""
        try:
            if not ids:
                return {'list': []}
            
            # 获取详情页ID
            if isinstance(ids, list):
                vod_id = ids[0]
            elif isinstance(ids, dict):
                vod_id = list(ids.keys())[0] if ids else ''
            else:
                vod_id = str(ids)
            
            # 确保URL完整
            if not vod_id.startswith('http'):
                vod_id = self._normalize_url(vod_id)
            
            print(f"详情页ID: {vod_id}")
            
            # 获取详情页内容
            response = self.fetch(vod_id, headers=self.headers)
            if not response or not response.text:
                print("获取详情页内容失败")
                return {'list': []}
            
            data = self.getpq(response.text)
            
            # 提取基本信息 - 根据提供的HTML结构
            # 1. 标题
            title = ''
            title_elem = data('h1.title span')
            if title_elem:
                title = title_elem.text().strip()
            
            if not title:
                # 尝试其他选择器
                title_elem = data('h1')
                if title_elem:
                    title = title_elem.text().strip()
            
            print(f"提取到标题: {title}")
            
            # 2. 封面图片
            img = ''
            img_elem = data('.ewave-content__thumb img')
            if img_elem:
                img = img_elem.attr('data-original') or img_elem.attr('src')
            
            if not img:
                img_elem = data('.v-thumb img, .poster img')
                if img_elem:
                    img = img_elem.attr('src')
            
            if img:
                img = self._normalize_url(img)
            
            print(f"提取到封面: {img}")
            
            # 3. 描述内容
            content = ''
            content_elem = data('#desc .ewave-pannel_bd p')
            if content_elem:
                content = content_elem.text().strip()
            
            if not content:
                # 尝试简介区域
                content_elem = data('.desc')
                if content_elem:
                    content = content_elem.text().strip()
            
            # 4. 提取详细信息
            year = ''
            area = ''
            actor = ''
            director = ''
            remarks = ''
            
            # 查找详细信息区域
            info_items = data('.ewave-content__detail .data')
            for info_item in info_items.items():
                text = info_item.text()
                
                # 地区
                if '地区：' in text or '地区:' in text:
                    area_match = re.search(r'地区[：:]\s*([^\s]+)', text)
                    if area_match:
                        area = area_match.group(1)
                
                # 演员
                if '主演：' in text or '主演:' in text:
                    # 提取演员信息
                    actor_text = text.replace('主演：', '').replace('主演:', '').strip()
                    if actor_text:
                        actor = actor_text
            
            # 5. 状态/备注
            remarks_elem = data('.pic-text')
            if remarks_elem:
                remarks = remarks_elem.text().strip()
            
            # 6. 导演信息
            director_elem = data('.data:contains("导演："), .data:contains("导演:")')
            if director_elem:
                director_text = director_elem.text().replace('导演：', '').replace('导演:', '').strip()
                if director_text:
                    director = director_text
            
            print(f"提取信息: 地区={area}, 演员={actor}, 导演={director}")
            
            # 构建视频信息
            vod = {
                'vod_id': vod_id,
                'vod_name': title or '未知标题',
                'vod_pic': img or '',
                'vod_content': content or '',
                'vod_year': year or '',
                'vod_area': area or '',
                'vod_remarks': remarks or '',
                'vod_actor': actor or '',
                'vod_director': director or '',
                'vod_play_from': '',
                'vod_play_url': ''
            }
            
            print(f"视频信息构建完成: {vod['vod_name']}")
            
            # 提取播放列表 - 根据提供的HTML结构
            # 首先获取所有播放源名称
            play_sources = {}
            
            # 查找播放源标签
            source_tabs = data('.playlist-slide a')
            for tab in source_tabs.items():
                source_id = tab.attr('href').replace('#', '')
                source_name = tab.text().strip()
                play_sources[source_id] = source_name
            
            print(f"找到播放源: {play_sources}")
            
            # 提取每个播放源的播放列表
            all_play_links = {}
            
            # 遍历每个播放源
            for source_id, source_name in play_sources.items():
                source_playlist = data(f'#{source_id} .ewave-content__playlist a')
                source_links = []
                
                for item in source_playlist.items():
                    play_title = item.text().strip()
                    play_url = item.attr('href')
                    
                    if play_url:
                        play_url = self._normalize_url(play_url)
                        source_links.append(f"{play_title}${play_url}")
                        print(f"源[{source_name}] 提取播放链接: {play_title} -> {play_url}")
                
                if source_links:
                    all_play_links[source_name] = source_links
            
            print(f"总共找到 {len(all_play_links)} 个播放源的播放列表")
            
            # 格式化播放列表
            if all_play_links:
                # 创建播放源名称列表
                source_names = list(all_play_links.keys())
                vod['vod_play_from'] = '$$$'.join(source_names)
                
                # 创建播放链接列表
                play_urls = []
                for source_name, links in all_play_links.items():
                    play_urls.append('#'.join(links))
                
                vod['vod_play_url'] = '$$$'.join(play_urls)
                print(f"播放信息格式化: 来源={vod['vod_play_from']}, 链接数={len(play_urls)}")
            else:
                # 如果没有找到播放列表，查找立即播放按钮
                play_btn = data('.play-btn a')
                if play_btn:
                    play_url = play_btn.attr('href')
                    if play_url:
                        play_url = self._normalize_url(play_url)
                        vod['vod_play_from'] = '立即播放'
                        vod['vod_play_url'] = f"立即播放${play_url}"
                        print(f"使用立即播放链接: {play_url}")
            
            return {'list': [vod]}
        except Exception as e:
            print(f"详情页错误: {e}")
            import traceback
            traceback.print_exc()
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        """搜索功能 - 根据搜索页HTML结构重写"""
        try:
            print(f"搜索请求: key={key}, pg={pg}")
            
            # 编码搜索关键词
            encoded_key = urllib.parse.quote(key)
            
            # 构建搜索URL - 根据提供的HTML结构
            search_url = f"{self.host}/search/{encoded_key}----------{pg}---.html"
            
            print(f"搜索URL: {search_url}")
            
            # 获取搜索结果
            response = self.fetch(search_url, headers=self.headers)
            if not response or not response.text:
                print("搜索请求失败")
                return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}
            
            html_content = response.text
            data = self.getpq(html_content)
            
            # 提取视频列表 - 根据搜索页面的HTML结构
            videos = []
            
            # 查找搜索结果项
            search_items = data('.ewave-vodlist__media li')
            
            # 如果没有找到，尝试其他选择器
            if not search_items:
                search_items = data('li.active')
            
            print(f"找到 {len(search_items)} 个搜索结果项")
            
            for item in search_items.items():
                video_info = self._extract_search_result(item)
                if video_info:
                    # 检查标题是否包含搜索关键词
                    title = video_info.get('vod_name', '').lower()
                    if key.lower() in title:
                        videos.append(video_info)
                        print(f"提取搜索结果: {video_info['vod_name']}")
            
            # 如果使用新方法没找到，尝试旧方法
            if not videos:
                print("使用备用方法提取搜索结果")
                video_items = data('.ewave-vodlist__box')
                if not video_items:
                    video_items = data('.vodlist li, .search-item, .item')
                
                for item in video_items.items():
                    video_info = self._extract_video_basic(item)
                    if video_info:
                        title = video_info.get('vod_name', '').lower()
                        if key.lower() in title:
                            videos.append(video_info)
            
            print(f"总共提取到 {len(videos)} 个搜索结果")
            
            # 提取分页信息
            pagecount = int(pg)
            
            # 查找分页元素
            page_elements = data('.ewave-page a, .pagination a, .page a')
            
            # 查找尾页链接
            last_page_elem = data('a:contains("尾页")')
            if last_page_elem:
                href = last_page_elem.attr('href')
                if href:
                    # 尝试从尾页URL提取最大页码
                    match = re.search(r'----------(\d+)---\.html', href)
                    if match:
                        try:
                            pagecount = int(match.group(1))
                            print(f"从尾页提取到总页数: {pagecount}")
                        except:
                            pass
            
            # 如果没有找到尾页，检查其他页码链接
            if pagecount <= int(pg):
                max_page = int(pg)
                for page_elem in page_elements.items():
                    href = page_elem.attr('href')
                    if href:
                        # 尝试提取页码
                        match = re.search(r'----------(\d+)---\.html', href)
                        if match:
                            try:
                                page_num = int(match.group(1))
                                if page_num > max_page:
                                    max_page = page_num
                            except:
                                pass
                
                pagecount = max_page
            
            # 如果没有找到任何分页信息，设置一个默认值
            if pagecount <= int(pg):
                pagecount = int(pg) + 1
            
            print(f"搜索完成: 关键词={key}, 结果数={len(videos)}, 总页数={pagecount}")
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 30,
                'total': 999999
            }
        except Exception as e:
            print(f"搜索错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                'list': [],
                'page': int(pg),
                'pagecount': 1,
                'limit': 30,
                'total': 0
            }

    def playerContent(self, flag, id, vipFlags):
        """解析播放地址 - 根据播放页HTML结构"""
        try:
            print(f"播放解析请求: flag={flag}, id={id}")
            
            # 确保URL完整
            if not id.startswith('http'):
                id = self._normalize_url(id)
            
            print(f"播放页完整URL: {id}")
            
            # 获取播放页内容
            response = self.fetch(id, headers=self.headers)
            if not response or not response.text:
                print("获取播放页内容失败")
                return {'parse': 1, 'url': id, 'header': self.headers}
            
            html_content = response.text
            print(f"获取到播放页内容，长度: {len(html_content)}")
            
            # 从HTML中提取player_aaaa对象
            # 查找var player_aaaa = {...} 格式
            player_pattern = r'var\s+player_aaaa\s*=\s*({[^}]+(?:\{[^{}]*\}[^}]*)*})'
            match = re.search(player_pattern, html_content, re.DOTALL)
            
            if match:
                try:
                    # 尝试解析JSON
                    player_json_str = match.group(1)
                    print(f"找到player_aaaa对象: {player_json_str[:200]}...")
                    
                    # 清理JSON字符串
                    player_json_str = player_json_str.replace('\\/', '/')
                    
                    player_data = json.loads(player_json_str)
                    
                    # 提取播放地址
                    video_url = player_data.get('url', '')
                    
                    if video_url:
                        print(f"从player_aaaa提取到播放地址: {video_url}")
                        return {
                            'parse': 0,  # 0表示直接播放，1表示需要解析
                            'url': self._normalize_url(video_url),
                            'header': self.headers
                        }
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    # 尝试手动提取URL
                    url_pattern = r'"url"\s*:\s*"([^"]+)"'
                    url_match = re.search(url_pattern, html_content)
                    if url_match:
                        video_url = url_match.group(1).replace('\\/', '/')
                        print(f"手动提取到播放地址: {video_url}")
                        return {
                            'parse': 0,
                            'url': self._normalize_url(video_url),
                            'header': self.headers
                        }
            
            # 如果没找到player_aaaa，尝试其他方法
            data = self.getpq(html_content)
            
            # 1. 查找iframe播放器
            iframe = data('iframe').attr('src')
            if iframe:
                print(f"找到iframe播放器: {iframe}")
                return {
                    'parse': 1,
                    'url': self._normalize_url(iframe),
                    'header': self.headers
                }
            
            # 2. 查找视频直链
            video_src = data('video source').attr('src')
            if video_src:
                print(f"找到视频直链: {video_src}")
                return {
                    'parse': 0,
                    'url': self._normalize_url(video_src),
                    'header': self.headers
                }
            
            # 3. 从script中提取视频地址
            script_text = data('script').text()
            
            # 查找m3u8地址
            m3u8_patterns = [
                r'["\'](http[^"\']+\.m3u8[^"\']*)["\']',
                r'url["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                r'm3u8["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'player\.url\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']'
            ]
            
            for pattern in m3u8_patterns:
                matches = re.findall(pattern, script_text, re.IGNORECASE)
                if matches:
                    m3u8_url = matches[0]
                    print(f"找到m3u8地址: {m3u8_url}")
                    return {
                        'parse': 0,
                        'url': self._normalize_url(m3u8_url),
                        'header': self.headers
                    }
            
            # 4. 查找其他视频格式
            video_patterns = [
                r'["\'](http[^"\']+\.mp4[^"\']*)["\']',
                r'["\'](http[^"\']+\.flv[^"\']*)["\']',
                r'video_url["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'playurl["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'player\.url\s*=\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, script_text, re.IGNORECASE)
                if matches:
                    video_url = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    print(f"找到视频地址: {video_url}")
                    return {
                        'parse': 0,
                        'url': self._normalize_url(video_url),
                        'header': self.headers
                    }
            
            # 5. 查找iframe的src
            iframe_src_pattern = r'iframe\.src\s*=\s*["\']([^"\']+)["\']'
            iframe_match = re.search(iframe_src_pattern, script_text)
            if iframe_match:
                iframe_url = iframe_match.group(1)
                print(f"找到iframe src: {iframe_url}")
                return {
                    'parse': 1,
                    'url': self._normalize_url(iframe_url),
                    'header': self.headers
                }
            
            print("未找到播放地址，使用原始URL")
            return {
                'parse': 1,
                'url': id,
                'header': self.headers
            }
        except Exception as e:
            print(f"播放解析错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                'parse': 1,
                'url': id,
                'header': self.headers
            }

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        pass