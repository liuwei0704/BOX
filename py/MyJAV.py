# -*- coding: utf-8 -*-
import re
import sys
import json
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""):
        pass

    def getName(self):
        return "MyJav"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    # ------------------------- 网站配置 -------------------------
    host = 'https://myjav.tv'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://myjav.tv',
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
            # 获取详情页链接
            link = self._normalize_url(item('a').attr('href'))
            if not link:
                return None

            # 获取标题
            title = item('.video-title').text().strip()
            if not title:
                title = item('img').attr('alt') or '未知标题'

            # 获取图片 - 从style属性中提取background-image的URL
            img = ''
            cover_div = item('.video-cover')
            if cover_div:
                style = cover_div.attr('style')
                if style:
                    # 提取 background-image: url('...')
                    img_match = re.search(r"url\('([^']+)'\)", style)
                    if img_match:
                        img = self._normalize_url(img_match.group(1))

            # 获取番号 (从 .video-vol-tag 中提取)
            vod_id_tag = item('.video-vol-tag').text().strip()
            
            # 获取时长
            duration = item('.video-duration').text().strip()
            
            # 获取属性标签 (中文字幕、无码等)
            tags = []
            tag_elements = item('.video-tags-container .video-attribute-tag')
            for tag in tag_elements.items():
                title_attr = tag.attr('title')
                if title_attr:
                    tags.append(title_attr)

            remarks = duration
            if tags:
                remarks += ' [' + ','.join(tags) + ']'

            return {
                'vod_id': link,
                'vod_name': f"{vod_id_tag} - {title}" if vod_id_tag else title,
                'vod_pic': img or '',
                'vod_remarks': remarks,
                'vod_year': ''
            }
        except Exception as e:
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
            data = self.getpq(self.fetch(self.host, headers=self.headers).text)
            classes = []

            # 提取分类导航 - 从nav-menu中提取
            nav_items = data('.nav-menu .nav-menu-item a')
            for item in nav_items.items():
                link = item.attr('href')
                name = item.text().strip()
                if link and name and name not in ['Home', 'Favorites', 'History']:
                    # 处理特殊分类
                    if name == 'Recent':
                        classes.append({'type_name': '最新更新', 'type_id': self._normalize_url('/videos?x=updated')})
                    elif name == 'Uncensored':
                        classes.append({'type_name': '无码', 'type_id': self._normalize_url('/videos?x=uncensored')})
                    #elif name == 'Tags':
                        classes.append({'type_name': '标签', 'type_id': self._normalize_url('/tags')})
                    #elif name == 'Actors':
                        classes.append({'type_name': '演员', 'type_id': self._normalize_url('/actors')})
                    #elif name == 'Makers':
                        classes.append({'type_name': '制作商', 'type_id': self._normalize_url('/makers')})
                    else:
                        classes.append({'type_name': name, 'type_id': self._normalize_url(link)})

            return {'class': classes, 'list': self._get_home_list(data)}
        except Exception as e:
            return {'class': [], 'list': []}

    def _get_home_list(self, data):
        """首页推荐列表 - 获取特色推荐和最新发布"""
        videos = []
        
        # 获取特色推荐 (video-card-large)
        featured_items = data('.video-card-large')
        for item in featured_items.items():
            video_info = self._extract_video_basic(item)
            if video_info:
                videos.append(video_info)
        
        # 获取最新发布 (regular grid中的video-card)
        regular_items = data('.video-grid.regular .video-card')
        for item in regular_items.items():
            video_info = self._extract_video_basic(item)
            if video_info and len(videos) < 30:  # 限制数量
                videos.append(video_info)
        
        return videos

    def categoryContent(self, tid, pg, filter, extend):
        """分类页内容"""
        try:
            # 处理分页
            url = tid
            if pg != '1':
                if '?' in tid:
                    url = f"{tid}&page={pg}"
                else:
                    url = f"{tid}?page={pg}"
            
            data = self.getpq(self.fetch(url, headers=self.headers).text)
            
            videos = self._get_video_list(data)
            
            # 尝试获取总页数（如果没有则使用默认值）
            pagecount = 9999
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 30,
                'total': 999999
            }
        except Exception as e:
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}

    def _get_video_list(self, data):
        """提取列表页视频"""
        videos = []
        items = data('.video-grid .video-card, .video-card-large')
        for item in items.items():
            video_info = self._extract_video_basic(item)
            if video_info:
                videos.append(video_info)
        return videos

    def detailContent(self, ids):
        """详情页：提取视频详情、播放列表"""
        try:
            first_id = next(iter(ids)) if hasattr(ids, '__iter__') and not isinstance(ids, str) else ids
            data = self.getpq(self.fetch(first_id, headers=self.headers).text)

            # 提取番号
            vod_id_tag = data('.video-vol-tag').text().strip()
            
            # 提取标题
            title = data('h1').text().strip()
            if not title:
                title = data('.video-title').text().strip()
            
            # 提取图片
            img = ''
            cover_div = data('.video-cover')
            if cover_div:
                style = cover_div.attr('style')
                if style:
                    img_match = re.search(r"url\('([^']+)'\)", style)
                    if img_match:
                        img = self._normalize_url(img_match.group(1))
            
            # 提取简介
            content = data('.video-info p, .description').text().strip()
            if not content:
                content = data('.video-title').text().strip()

            vod = {
                'vod_id': first_id,
                'vod_name': f"{vod_id_tag} - {title}" if vod_id_tag else title,
                'vod_pic': img or '',
                'vod_content': content,
                'vod_year': '',
                'vod_area': '日本',
                'vod_remarks': data('.video-duration').text().strip(),
                'vod_actor': '',
                'vod_director': ''
            }

            # 由于这个网站可能没有直接的播放列表，我们需要从页面中提取播放链接
            # 假设播放器在 iframe 中或者是直接视频链接
            play_links = []
            
            # 尝试提取 iframe 播放器
            iframe = data('iframe[src*="video"], iframe[src*="player"]').attr('src')
            if iframe:
                play_links.append(f"播放${self._normalize_url(iframe)}")
            else:
                # 如果没有 iframe，使用详情页本身作为播放地址
                play_links.append(f"播放${first_id}")

            vod['vod_play_from'] = '默认播放源'
            vod['vod_play_url'] = '#'.join(play_links)

            return {'list': [vod]}
        except Exception as e:
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        """搜索功能"""
        try:
            # 这个网站可能使用JavaScript搜索，我们需要猜测搜索URL
            # 常见的搜索URL模式
            search_url = f"{self.host}/search?q={key}"
            if pg != "1":
                search_url += f"&page={pg}"
            
            data = self.getpq(self.fetch(search_url, headers=self.headers).text)
            results = self._get_video_list(data)
            
            # 如果上面的搜索URL无效，尝试其他常见模式
            if not results:
                search_url = f"{self.host}/videos?s={key}"
                data = self.getpq(self.fetch(search_url, headers=self.headers).text)
                results = self._get_video_list(data)
            
            filtered = self._filter_search_results(results, key)
            return {'list': filtered, 'page': int(pg)}
        except Exception as e:
            return {'list': [], 'page': int(pg)}

    def _filter_search_results(self, results, key):
        """过滤和排序搜索结果"""
        if not results or not key:
            return results
        key_lower = key.lower()
        scored = []
        for result in results:
            title = result.get('vod_name', '').lower()
            if key_lower in title:
                scored.append((title.startswith(key_lower), -title.find(key_lower), result))
        scored.sort(reverse=True)
        return [r for _, _, r in scored]

    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        try:
            # 先尝试直接访问页面提取播放器
            data = self.getpq(self.fetch(id, headers=self.headers).text)
            
            # 尝试提取 iframe 播放器
            iframe = data('iframe[src*="video"], iframe[src*="player"], iframe.video-player').attr('src')
            if iframe:
                return {'parse': 1, 'url': self._normalize_url(iframe), 'header': self.headers}

            # 尝试提取 video 标签
            video_src = data('video source').attr('src')
            if video_src:
                return {'parse': 0, 'url': self._normalize_url(video_src), 'header': self.headers}
            
            # 尝试从 script 中提取视频链接
            scripts = data('script').text()
            video_url_patterns = [
                r'video_url["\']\s*:\s*["\']([^"\']+)["\']',
                r'src["\']\s*:\s*["\']([^"\']+\.(?:mp4|m3u8))["\']',
                r'playUrl["\']\s*:\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in video_url_patterns:
                match = re.search(pattern, scripts, re.IGNORECASE)
                if match:
                    return {'parse': 1 if '.m3u8' in match.group(1) else 0, 
                           'url': self._normalize_url(match.group(1)), 
                           'header': self.headers}

            # 回退
            return {'parse': 1, 'url': id, 'header': self.headers}
        except Exception as e:
            return {'parse': 1, 'url': id, 'header': self.headers}

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        pass

    # ------------------------- 扩展功能 -------------------------
    def filterByTag(self, video_list, tag):
        """按标签过滤视频"""
        return [v for v in video_list if tag.lower() in v.get('vod_name', '').lower()]

    def getUncensoredOnly(self, video_list):
        """只获取无码视频"""
        return [v for v in video_list if 'Uncensored' in v.get('vod_remarks', '')]