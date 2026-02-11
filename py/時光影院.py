# -*- coding: utf-8 -*-
import sys
import re
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""): pass
    def getName(self): return "时光影院"
    def isVideoFormat(self, url): pass
    def manualVideoCheck(self): pass
    def destroy(self): pass

    host = 'https://www.cinemirro.com'
    
    # 添加请求头
    def get_header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': self.host
        }

    def homeContent(self, filter):
        # 固定分类 - 根据HTML中的导航栏
        classes = [
            {'type_id': '1', 'type_name': '电影'},
            {'type_id': '2', 'type_name': '连续剧'},
            {'type_id': '3', 'type_name': '动漫'},
            {'type_id': '4', 'type_name': '综艺'},
            {'type_id': '22', 'type_name': '短劇'},
            {'type_id': '32', 'type_name': '体育'},
            {'type_id': 'live', 'type_name': '电视'},
        ]
        return {'class': classes, 'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            print(f"DEBUG: categoryContent called - tid={tid}, pg={pg}")
            
            # 构建分类URL - 根据HTML中的链接格式
            if tid == 'live':
                # 电视直播特殊处理
                url = f"{self.host}/label/live.html"
            elif tid in ['1', '2', '3', '4', '32']:
                # 主分类: /vod/type/id/1.html
                if pg == '1':
                    url = f"{self.host}/vod/type/id/{tid}.html"
                else:
                    url = f"{self.host}/vod/type/id/{tid}/page/{pg}.html"
            else:
                # 尝试其他格式
                if pg == '1':
                    url = f"{self.host}/vod/show/id/{tid}.html"
                else:
                    url = f"{self.host}/vod/show/id/{tid}/page/{pg}.html"
            
            print(f"DEBUG: Fetching URL: {url}")
            
            # 获取页面内容
            response = self.fetch(url, headers=self.get_header())
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response length: {len(response.text)}")
            
            if response.status_code != 200:
                print(f"DEBUG: Failed to fetch page, status: {response.status_code}")
                return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 20, 'total': 0}
            
            # 解析HTML
            data = pq(response.text)
            
            videos = []
            
            # 使用更通用的选择器
            items = data('.module-item')
            print(f"DEBUG: Found {len(items)} items with .module-item selector")
            
            if len(items) == 0:
                # 备用选择器
                items = data('.module-items .module-item-elem')
                print(f"DEBUG: Found {len(items)} items with backup selector")
            
            for item in items.items():
                try:
                    # 提取链接
                    link_elem = item.find('a[href*="/vod/detail/"]')
                    if not link_elem:
                        continue
                    
                    link = link_elem.attr('href')
                    if not link:
                        continue
                    
                    # 提取标题
                    title_elem = item.find('.module-item-title, .video-name')
                    if title_elem:
                        title = title_elem.text().strip()
                    else:
                        title = link_elem.attr('title') or item.find('img').attr('alt') or '未知标题'
                    
                    # 提取图片
                    img_elem = item.find('img.lazyload')
                    if img_elem:
                        img = img_elem.attr('data-src')
                        if not img:
                            img = img_elem.attr('src')
                    else:
                        img = item.find('img').attr('src')
                    
                    # 提取备注
                    remarks_elem = item.find('.module-item-text')
                    remarks = remarks_elem.text().strip() if remarks_elem else ''
                    
                    # 提取内容信息
                    caption_elem = item.find('.module-item-caption')
                    caption = ''
                    if caption_elem:
                        spans = caption_elem.find('span')
                        info_parts = []
                        for span in spans.items():
                            span_text = span.text().strip()
                            if span_text:
                                info_parts.append(span_text)
                        caption = ' '.join(info_parts)
                    
                    # 构建视频信息
                    video_info = {
                        'vod_id': self._normalize_url(link),
                        'vod_name': title,
                        'vod_pic': self._normalize_url(img) if img else '',
                        'vod_remarks': remarks,
                        'vod_content': caption
                    }
                    
                    videos.append(video_info)
                    
                except Exception as e:
                    print(f"DEBUG: Error parsing item: {str(e)}")
                    continue
            
            print(f"DEBUG: Total videos found: {len(videos)}")
            
            # 获取总页数
            pagecount = 1
            page_links = data('#page a')
            if page_links:
                max_page = 1
                for page in page_links.items():
                    page_text = page.text().strip()
                    if page_text.isdigit():
                        page_num = int(page_text)
                        if page_num > max_page:
                            max_page = page_num
                if max_page > 1:
                    pagecount = max_page
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 20,
                'total': len(videos) * pagecount
            }
            
        except Exception as e:
            print(f"DEBUG: categoryContent error: {str(e)}")
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 20, 'total': 0}

    def _normalize_url(self, url):
        """URL标准化"""
        if not url:
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        return url

    def detailContent(self, ids):
        try:
            url = ids[0] if isinstance(ids, list) else ids
            print(f"DEBUG: detailContent called - url={url}")
            
            response = self.fetch(url, headers=self.get_header())
            if response.status_code != 200:
                print(f"DEBUG: Failed to fetch detail page, status: {response.status_code}")
                return {'list': []}
            
            html_content = response.text
            data = pq(html_content)
            
            # 调试：打印页面标题
            print(f"DEBUG: Page title: {data('title').text()[:50]}")
            
            # 方法1：尝试直接提取所有信息
            vod_info = {}
            
            # 提取标题
            vod_name = data('h1.page-title, .video-info-header h1').text().strip()
            if not vod_name:
                # 从title中提取
                title = data('title').text()
                if '《' in title and '》' in title:
                    vod_name = title.split('《')[1].split('》')[0]
                else:
                    vod_name = title.split('_')[0] if '_' in title else title
            vod_info['vod_name'] = vod_name
            
            # 提取图片
            vod_pic = data('.video-cover img.lazyload').attr('data-src')
            if not vod_pic:
                vod_pic = data('.module-item-pic img.lazyload').attr('data-src')
            if not vod_pic:
                vod_pic = data('meta[property="og:image"]').attr('content')
            vod_info['vod_pic'] = self._normalize_url(vod_pic) if vod_pic else ''
            
            # 提取剧情简介
            vod_content = data('.video-info-content.vod_content').text().strip()
            if not vod_content:
                vod_content = data('.video-info-content').text().strip()
            if not vod_content:
                vod_content = data('meta[name="description"]').attr('content') or ''
            vod_info['vod_content'] = vod_content
            
            # 提取导演
            director_text = ''
            for elem in data('.video-info-items').items():
                if '导演' in elem.text():
                    director_links = elem.find('a')
                    directors = []
                    for link in director_links.items():
                        directors.append(link.text().strip())
                    director_text = ' / '.join(directors) if directors else elem.find('.video-info-item').text().strip()
                    break
            vod_info['vod_director'] = director_text
            
            # 提取主演
            actor_text = ''
            for elem in data('.video-info-items').items():
                if '主演' in elem.text():
                    actor_links = elem.find('a')
                    actors = []
                    for link in actor_links.items():
                        actors.append(link.text().strip())
                    actor_text = ' / '.join(actors) if actors else elem.find('.video-info-item').text().strip()
                    break
            vod_info['vod_actor'] = actor_text
            
            # 提取年份
            year_text = ''
            for elem in data('.video-info-items').items():
                if '上映' in elem.text() or '年份' in elem.text():
                    year_text = elem.find('.video-info-item').text().strip()
                    break
            vod_info['vod_year'] = year_text
            
            # 提取地区
            area_text = ''
            area_elem = data('.video-info-aux a[href*="/vod/show/area/"]')
            if area_elem:
                area_text = area_elem.text().strip()
            vod_info['vod_area'] = area_text
            
            # 提取类型
            type_text = ''
            type_elem = data('.video-info-aux a[href*="/vod/type/"]')
            if type_elem:
                type_text = type_elem.text().strip()
            vod_info['type_name'] = type_text
            
            # 提取状态/集数
            remarks_text = ''
            for elem in data('.video-info-items').items():
                if '集数' in elem.text() or '状态' in elem.text():
                    remarks_text = elem.find('.video-info-item').text().strip()
                    break
            vod_info['vod_remarks'] = remarks_text
            
            # 提取播放列表
            play_list = {}
            
            # 查找所有播放节点
            play_nodes = data('.module-player-tab .module-tab-item')
            print(f"DEBUG: Found {len(play_nodes)} play nodes")
            
            if len(play_nodes) > 0:
                for i, node in enumerate(play_nodes.items()):
                    node_name = node.find('span').text().strip()
                    if not node_name:
                        continue
                    
                    # 查找对应的播放列表
                    play_div = data(f'#glist-{i+1}')
                    if not play_div:
                        continue
                    
                    play_links = play_div.find('a[href*="/vod/play/"]')
                    play_urls = []
                    
                    for link in play_links.items():
                        play_url = link.attr('href')
                        play_name_elem = link.find('span')
                        if play_name_elem:
                            play_name = play_name_elem.text().strip()
                        else:
                            play_name = link.text().strip()
                        
                        if play_url:
                            play_urls.append(f"{play_name}${self._normalize_url(play_url)}")
                    
                    if play_urls:
                        play_list[node_name] = '#'.join(play_urls)
                        print(f"DEBUG: Added play node: {node_name} with {len(play_urls)} episodes")
            
            # 如果没找到播放节点，尝试直接查找播放链接
            if not play_list:
                print("DEBUG: No play nodes found, trying direct links")
                play_links = data('a[href*="/vod/play/"]')
                if len(play_links) > 0:
                    play_urls = []
                    for link in play_links.items():
                        play_url = link.attr('href')
                        play_name = link.find('span').text().strip() or link.text().strip()
                        if play_url:
                            play_urls.append(f"{play_name}${self._normalize_url(play_url)}")
                    
                    if play_urls:
                        play_list['播放'] = '#'.join(play_urls)
                        print(f"DEBUG: Added direct play links: {len(play_urls)} episodes")
            
            # 设置视频ID
            vod_info['vod_id'] = url
            
            # 如果有播放列表，添加到视频信息中
            if play_list:
                vod_info['vod_play_from'] = '$$$'.join(play_list.keys())
                vod_info['vod_play_url'] = '$$$'.join(play_list.values())
                print(f"DEBUG: Play list: {list(play_list.keys())}")
            else:
                print(f"DEBUG: No play list found!")
                # 如果没有播放列表，返回空列表
                return {'list': []}
            
            print(f"DEBUG: Successfully parsed video: {vod_name}")
            return {'list': [vod_info]}
            
        except Exception as e:
            print(f"DEBUG: detailContent error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'list': []}

    def searchContent(self, key, quick):
        # 清除搜索功能，直接返回空结果
        print(f"DEBUG: searchContent disabled - key={key}")
        return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        print(f"DEBUG: playerContent called - flag={flag}, id={id}")
        return {
            'parse': 1,  # 启用解析
            'url': id,
            'header': self.get_header()
        }

    def localProxy(self, param): pass
    def liveContent(self, url): pass