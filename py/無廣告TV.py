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
        return "无广告TV"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    # ------------------------- 网站配置 -------------------------
    host = 'https://www.5ggtv.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://www.5ggtv.com/'
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
        """从列表项提取视频基本信息 - 适配分类页/首页的.poster-item"""
        try:
            link = item('a').attr('href')
            if not link:
                return None
            link = self._normalize_url(link)
            
            title = item('.module-poster-item-title').text().strip()
            if not title:
                title = item('img').attr('alt', '').strip()
            
            img = item('img').attr('data-original') or item('img').attr('src')
            img = self._normalize_url(img)
            
            remarks = item('.module-item-note').text().strip()
            
            if not title or not link:
                return None
                
            return {
                'vod_id': link,
                'vod_name': title,
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

            nav_items = data('.navbar-items .navbar-item')
            for item in nav_items.items():
                link = item('a').attr('href')
                name = item('a span').text().strip()
                if link and name and name not in ['首页', '热榜', '今日更新', '永久网址', '影视导航'] and not link.startswith('http'):
                    if '/vodtype/' in link:
                        type_id = re.search(r'/vodtype/(\d+)', link)
                        if type_id:
                            link = f"/vodshow/{type_id.group(1)}--------1---.html"
                    classes.append({
                        'type_name': name,
                        'type_id': self._normalize_url(link)
                    })

            videos = self._get_home_list(data)
            return {'class': classes, 'list': videos[:20]}
        except Exception as e:
            return {'class': [], 'list': []}

    def _get_home_list(self, data):
        """首页推荐列表"""
        videos = []
        
        slide_items = data('.sm-swiper .swiper-slide')
        for item in slide_items.items():
            video_info = self._extract_slide_item(item)
            if video_info:
                videos.append(video_info)
        
        items = data('.module-items .module-poster-item')
        for item in items.items():
            if len(videos) >= 30:
                break
            video_info = self._extract_video_basic(item)
            if video_info and not any(v['vod_id'] == video_info['vod_id'] for v in videos):
                videos.append(video_info)
                
        return videos

    def _extract_slide_item(self, item):
        """提取轮播图项"""
        try:
            link = self._normalize_url(item('a').attr('href'))
            title = item('.title a').text().strip() or item('img').attr('alt', '')
            img = self._normalize_url(item('img').attr('src') or item('img').attr('data-original'))
            remarks = item('.ins p').first().text().strip()
            
            if not title or not link:
                return None
                
            return {
                'vod_id': link,
                'vod_name': title,
                'vod_pic': img or '',
                'vod_remarks': remarks or '',
                'vod_year': ''
            }
        except:
            return None

    def categoryContent(self, tid, pg, filter, extend):
        """分类页内容"""
        try:
            if 'vodshow' in tid:
                if pg == '1':
                    url = tid
                else:
                    url = re.sub(r'--------\d+---\.html', f'--------{pg}---.html', tid)
            elif 'vodtype' in tid:
                match = re.search(r'/vodtype/(\d+)', tid)
                if match:
                    type_id = match.group(1)
                    url = f"{self.host}/vodshow/{type_id}--------{pg}---.html"
                else:
                    url = tid
            else:
                url = tid
                
            data = self.getpq(self.fetch(url, headers=self.headers).text)
            videos = self._get_video_list(data)
            
            total_pages = 9999
            page_links = data('#page .page-number')
            for link in page_links.items():
                text = link.text().strip()
                if text.isdigit() and int(text) > total_pages and int(text) < 1000:
                    total_pages = int(text)
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': total_pages,
                'limit': 30,
                'total': total_pages * 30
            }
        except Exception as e:
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}

    def _get_video_list(self, data):
        """提取列表页视频 - 用于分类页"""
        videos = []
        items = data('.module-items .module-poster-item')
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

            # 标题
            vod_name = data('.module-info-heading h1').text().strip() or data('h1').text().strip()
            if not vod_name:
                vod_name = data('title').text().strip().replace('详情介绍-', '').replace(' - 无广告TV', '')
            
            # 海报
            poster = data('.module-info-poster img').attr('data-original') or \
                     data('.module-info-poster img').attr('src') or \
                     data('.module-item-pic img').attr('data-original')
            
            # 简介
            content = data('.module-info-introduction-content p').text().strip() or \
                      data('.module-info-introduction-content').text().strip()
            
            # 解析详情信息
            actor = ''
            director = ''
            area = ''
            year = ''
            remarks = ''
            
            info_items = data('.module-info-items .module-info-item')
            for item in info_items.items():
                label = item('.module-info-item-title').text().strip()
                value = item('.module-info-item-content').text().strip()
                
                if '导演' in label:
                    director = value.replace('/', ' ').strip()
                elif '演员' in label or '主演' in label:
                    actor = value.replace('/', ' ').strip()
                elif '地区' in label:
                    area = value
                elif '年份' in label:
                    year = value
                elif '集数' in label or '更新' in label:
                    remarks = value
            
            if not remarks:
                remarks = data('.module-info-tag .module-info-tag-link a').first().text().strip()
            
            vod = {
                'vod_id': first_id,
                'vod_name': vod_name,
                'vod_pic': self._normalize_url(poster or ''),
                'vod_content': content or '暂无简介',
                'vod_year': year,
                'vod_area': area,
                'vod_remarks': remarks,
                'vod_actor': actor,
                'vod_director': director
            }

            # 播放列表
            play_links = []
            play_from = []
            
            tab_items = data('.module-tab-item')
            source_names = []
            for item in tab_items.items():
                name = item.text().strip()
                name = re.sub(r'\d+$', '', name).strip()
                if name:
                    source_names.append(name)
            
            play_lists = data('.module-play-list')
            
            if len(source_names) < play_lists.length:
                for i in range(play_lists.length - len(source_names)):
                    source_names.append(f'播放源{len(source_names)+1}')
            
            for idx, play_list in enumerate(play_lists.items()):
                source_name = source_names[idx] if idx < len(source_names) else '默认播放源'
                play_from.append(source_name)
                
                links = []
                items = play_list('.module-play-list-content a')
                for item in items.items():
                    title = item.text().strip()
                    link = self._normalize_url(item.attr('href'))
                    if link:
                        links.append(f"{title}${link}")
                
                if links:
                    play_links.append('#'.join(links))
            
            if not play_links:
                direct_link = data('video source').attr('src') or data('video').attr('src') or data('iframe').attr('src')
                if direct_link:
                    play_links.append(f"播放${self._normalize_url(direct_link)}")
                    play_from.append('默认播放源')
                else:
                    play_links.append(f"播放${first_id}")
                    play_from.append('默认播放源')
            
            vod['vod_play_from'] = '$$$'.join(play_from) if play_from else '默认播放源'
            vod['vod_play_url'] = '$$$'.join(play_links) if play_links else ''

            return {'list': [vod]}
        except Exception as e:
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        """搜索功能 - 已禁用，返回空列表"""
        return {'list': [], 'page': int(pg)}

    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        try:
            if id.startswith('http'):
                if any(ext in id.lower() for ext in ['.mp4', '.m3u8', '.flv', '.mkv', '.avi', '.mov']):
                    return {'parse': 0, 'url': id, 'header': self.headers}
                
                data = self.getpq(self.fetch(id, headers=self.headers).text)
                
                iframe = data('iframe').attr('src')
                if iframe:
                    return {'parse': 1, 'url': self._normalize_url(iframe), 'header': self.headers}
                
                video_src = data('video source').attr('src') or data('video').attr('src')
                if video_src:
                    return {'parse': 0, 'url': self._normalize_url(video_src), 'header': self.headers}
            
            return {'parse': 1, 'url': id, 'header': self.headers}
        except Exception as e:
            return {'parse': 1, 'url': id, 'header': self.headers}

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        pass