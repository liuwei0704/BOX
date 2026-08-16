# -*- coding: utf-8 -*-
import re
import sys
import json
from pyquery import PyQuery as pq
import urllib.parse

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):

    def init(self, extend=""):
        pass

    def getName(self):
        return "飞流视频"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    # ------------------------- 网站配置 -------------------------
    host = 'https://www.flixflop.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
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
            # 提取标题和链接
            link_tag = item('h3.xtczxMk a')
            if link_tag:
                link = self._normalize_url(link_tag.attr('href'))
                title = link_tag.text().strip()
                
                # 提取图片
                img_tag = item('img')
                img = self._normalize_url(img_tag.attr('src') or img_tag.attr('data-src'))
                
                # 提取备注和年份
                remarks = item('.xLSs05H').text().strip()
                year = item('.xH2UQqh').text().strip()
                
                # 提取演员
                actors = item('.xF4MEWI').text().strip()

                return {
                    'vod_id': link,
                    'vod_name': title,
                    'vod_pic': img or '',
                    'vod_remarks': remarks,
                    'vod_year': year,
                    'vod_actor': actors
                }
            return None
        except Exception as e:
            return None

    def _extract_search_item(self, item):
        """从搜索结果页提取信息 - 简化版"""
        try:
            # 提取链接 - 搜索頁面使用 a.xeerELw
            link_tag = item('a.xeerELw')
            if not link_tag:
                return None
                
            link = self._normalize_url(link_tag.attr('href'))
            
            # 提取图片
            img_tag = link_tag('img')
            img = self._normalize_url(img_tag.attr('src') or '')
            
            # 提取标题 - 搜索頁面使用 a.xrIoPJE
            title_tag = item('a.xrIoPJE')
            title = title_tag.text().strip() if title_tag else ''
            
            # 提取年份和备注
            year = item('.xH2UQqh').text().strip()
            remarks = item('.xLSs05H').text().strip()
            
            # 提取演员
            actors = ''
            actor_tag = item('.x5A9jrT')
            if actor_tag:
                actors = actor_tag.text().strip()

            if title:
                return {
                    'vod_id': link,
                    'vod_name': title,
                    'vod_pic': img or '',
                    'vod_remarks': remarks,
                    'vod_year': year,
                    'vod_actor': actors
                }
            return None
        except Exception as e:
            print(f"Error in _extract_search_item: {e}")
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

    # ------------------------- 主要功能方法 -------------------------
    def homeContent(self, filter):
        """首页：分类 + 推荐列表"""
        try:
            response_text = self.fetch(self.host, headers=self.headers).text
            data = self.getpq(response_text)

            classes = []
            # 从 __NEXT_DATA__ 中提取分类
            try:
                next_data_script = data('script#__NEXT_DATA__')
                if next_data_script:
                    json_str = next_data_script.text()
                    json_data = json.loads(json_str)
                    categories = json_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['data']
                    for cat in categories:
                        classes.append({
                            'type_name': cat['name'],
                            'type_id': f"{self.host}/explore/{cat['category_id']}?page=1"
                        })
            except Exception as e:
                print(f"Error extracting categories from JSON: {e}")
                # 备用：从导航栏提取
                nav_items = data('.MuiTabs-flexContainer a.MuiTab-root')
                for item in nav_items.items():
                    link = item.attr('href')
                    name = item.text().strip()
                    if link and name and name not in ['首页', 'Home']:
                        classes.append({'type_name': name, 'type_id': self._normalize_url(link)})

            # 获取首页推荐列表
            videos = []
            items = data('div.xy8LLgj div.xdxy5lq > div, div.xpHiS84 > div')
            for item in items.items():
                video_info = self._extract_video_basic(item)
                if video_info:
                    videos.append(video_info)

            return {'class': classes, 'list': videos}
        except Exception as e:
            print(f"Error in homeContent: {e}")
            return {'class': [], 'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        """分类页内容"""
        try:
            print(f"Debug - Original tid: {tid}")
            print(f"Debug - Requested page: {pg}")
            
            # 構建分頁URL
            if '?' in tid:
                base_url = tid.split('?')[0]
                url = f"{base_url}?page={pg}"
            else:
                url = f"{tid}?page={pg}"
            
            print(f"Debug - Final URL: {url}")
            
            response_text = self.fetch(url, headers=self.headers).text
            data = self.getpq(response_text)

            # 提取视频列表
            videos = self._get_video_list(data)
            print(f"Debug - Found {len(videos)} videos")

            # 提取总页数
            total_pages = self._extract_total_pages(data)
            print(f"Debug - Total pages: {total_pages}")

            return {
                'list': videos,
                'page': int(pg),
                'pagecount': total_pages,
                'limit': 30,
                'total': 999999
            }
        except Exception as e:
            print(f"Error in categoryContent: {e}")
            import traceback
            traceback.print_exc()
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}

    def _get_video_list(self, data):
        """提取分类页视频列表"""
        videos = []
        items = data('div.xgah6c7 > div')
        for item in items.items():
            video_info = self._extract_video_basic(item)
            if video_info:
                videos.append(video_info)
        return videos

    def _extract_total_pages(self, data):
        """从分页导航提取总页数"""
        try:
            max_page = 1
            
            # 從所有分頁連結中找出最大頁碼
            page_links = data('nav[aria-label="pagination"] ul li a')
            for link in page_links.items():
                href = link.attr('href')
                if href:
                    match = re.search(r'[?&]page=(\d+)', href)
                    if match:
                        page_num = int(match.group(1))
                        if page_num > max_page:
                            max_page = page_num
                            
                link_text = link.text().strip()
                if link_text.isdigit():
                    page_num = int(link_text)
                    if page_num > max_page:
                        max_page = page_num
            
            # 檢查省略號後的最後一頁
            ellipsis_items = data('nav[aria-label="pagination"] ul li .MuiPaginationItem-ellipsis')
            for item in ellipsis_items.items():
                next_li = item.parent().next()
                if next_li:
                    last_link = next_li.find('a')
                    if last_link:
                        last_text = last_link.text().strip()
                        if last_text.isdigit():
                            last_page = int(last_text)
                            if last_page > max_page:
                                max_page = last_page
            
            return max_page if max_page > 1 else 9999
        except Exception as e:
            print(f"Error extracting total pages: {e}")
            return 9999

    def detailContent(self, ids):
        """详情页：提取视频详情、播放列表"""
        try:
            first_id = next(iter(ids)) if hasattr(ids, '__iter__') and not isinstance(ids, str) else ids
            print(f"Debug - Fetching detail: {first_id}")
            
            response_text = self.fetch(first_id, headers=self.headers).text
            data = self.getpq(response_text)

            # 從 __NEXT_DATA__ 提取詳細信息
            video_info = {}
            sources_data = []
            
            next_data_script = data('script#__NEXT_DATA__')
            if next_data_script:
                try:
                    json_str = next_data_script.text()
                    json_data = json.loads(json_str)
                    
                    # 遍歷所有查詢以獲取視頻信息和播放源
                    for query in json_data['props']['pageProps']['dehydratedState']['queries']:
                        query_key = str(query.get('queryKey', ''))
                        if 'metadata' in query_key and 'state' in query:
                            video_info = query['state']['data']['data']
                        elif 'sources' in query_key and 'state' in query:
                            sources_data = query['state']['data']['data']
                except Exception as e:
                    print(f"Error parsing JSON: {e}")

            # 構建影片基本信息
            vod = {
                'vod_id': first_id,
                'vod_name': video_info.get('title', '') or data('h1').text().strip() or '未知片名',
                'vod_pic': video_info.get('cover_image', '') or self._normalize_url(data('meta[property="og:image"]').attr('content') or ''),
                'vod_content': video_info.get('description', '') or data('meta[name="description"]').attr('content') or '',
                'vod_year': str(video_info.get('published_year', '')) or '',
                'vod_area': video_info.get('area', '') or '',
                'vod_remarks': video_info.get('remarks', '') or '',
                'vod_actor': ', '.join([actor.get('name', '') for actor in video_info.get('actors', [])]) if video_info.get('actors') else '',
                'vod_director': ', '.join([director.get('name', '') for director in video_info.get('directors', [])]) if video_info.get('directors') else ''
            }

            # 構建播放列表
            play_from = []
            play_url = []
            
            if sources_data:
                for source in sources_data:
                    source_name = source.get('name', '未知源')
                    play_from.append(source_name)
                    
                    # 解析播放URL
                    url_string = source.get('url', '')
                    episodes = url_string.split('#')
                    episode_links = []
                    for episode in episodes:
                        if '$' in episode:
                            title, link = episode.split('$', 1)
                            if link and not link.startswith('http'):
                                link = f"https:{link}" if link.startswith('//') else link
                            episode_links.append(f"{title}${link}")
                    
                    if episode_links:
                        play_url.append('#'.join(episode_links))
            
            if play_from and play_url:
                vod['vod_play_from'] = '$$$'.join(play_from)
                vod['vod_play_url'] = '$$$'.join(play_url)
            else:
                vod['vod_play_from'] = '飞流视频'
                vod['vod_play_url'] = f"播放${first_id}"

            print(f"Debug - Found {len(play_from)} play sources")
            return {'list': [vod]}
            
        except Exception as e:
            print(f"Error in detailContent: {e}")
            import traceback
            traceback.print_exc()
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        """搜索功能 - 简化版"""
        try:
            encoded_key = urllib.parse.quote(key)
            search_url = f"{self.host}/results?q={encoded_key}"
            if pg != "1":
                search_url += f"&page={pg}"
            
            print(f"Debug - Search URL: {search_url}")
            
            response_text = self.fetch(search_url, headers=self.headers).text
            data = self.getpq(response_text)

            results = []
            
            # 直接提取所有可能包含搜索结果的容器
            # 方法1: 使用通用的选择器
            items = data('div.flex.gap-4')
            print(f"Debug - Found {len(items)} flex.gap-4 items")
            
            for item in items.items():
                video_info = self._extract_search_item(item)
                if video_info and video_info.get('vod_name'):
                    results.append(video_info)
            
            # 如果沒找到，嘗試其他選擇器
            if not results:
                items = data('div[class*="flex"]')
                print(f"Debug - Trying fallback, found {len(items)} flex items")
                for item in items.items():
                    video_info = self._extract_search_item(item)
                    if video_info and video_info.get('vod_name'):
                        results.append(video_info)

            print(f"Debug - Total found {len(results)} search results")
            
            # 過濾結果
            filtered = []
            key_lower = key.lower()
            for r in results:
                if key_lower in r.get('vod_name', '').lower():
                    filtered.append(r)
            
            return {'list': filtered, 'page': int(pg)}
            
        except Exception as e:
            print(f"Error in searchContent: {e}")
            import traceback
            traceback.print_exc()
            return {'list': [], 'page': int(pg)}

    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        try:
            print(f"Debug - PlayerContent - flag: {flag}, id: {id}")
            
            if id.startswith('http') and ('.m3u8' in id or '.mp4' in id):
                return {'parse': 0, 'url': id, 'header': self.headers}
            
            if id.startswith('//'):
                return {'parse': 0, 'url': f"https:{id}", 'header': self.headers}
            
            return {'parse': 1, 'url': id, 'header': self.headers}
            
        except Exception as e:
            print(f"Error in playerContent: {e}")
            return {'parse': 1, 'url': id, 'header': self.headers}

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        pass