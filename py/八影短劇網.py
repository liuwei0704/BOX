# -*- coding: utf-8 -*-
import re
import sys
import json
import urllib.parse
import random
import time
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):

    def init(self, extend=""):
        pass

    def getName(self):
        return "八影短劇網"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    host = 'https://8movie.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Referer': 'https://8movie.com/'
    }

    CATEGORIES = [
        {'type_name': '穿越古代', 'type_id': '/movies/1'},
        {'type_name': '都市情愛', 'type_id': '/movies/4'},
        {'type_name': '復仇爽劇', 'type_id': '/movies/5'},
        {'type_name': '玄幻武俠', 'type_id': '/movies/2'},
        {'type_name': '奇幻懸疑', 'type_id': '/movies/3'},
        {'type_name': '其他短劇', 'type_id': '/movies/6'},
    ]

    def _normalize_url(self, url):
        if not url:
            return url
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{self.host}{url}"
        return url

    def _extract_video_basic(self, item):
        try:
            link_elem = item('a')
            if not link_elem:
                return None
            link = self._normalize_url(link_elem.attr('href'))
            if not link or '/movies/' not in link:
                return None

            title = link_elem.attr('title') or item('h6').text().strip() or ''
            img = self._normalize_url(item('img').attr('src'))
            remarks = item('eps').text().strip()
            
            if img and title:
                return {
                    'vod_id': link,
                    'vod_name': title,
                    'vod_pic': img,
                    'vod_remarks': remarks,
                    'vod_year': ''
                }
            return None
        except:
            return None

    def getpq(self, text):
        try:
            return pq(text)
        except:
            try:
                return pq(text.encode('utf-8'))
            except:
                return pq('')

    def _get_video_list(self, data):
        videos = []
        items = data('.pagemore .col-4.col-lg-2, .row .col-4, .col-4.p-2')
        for item in items.items():
            video = self._extract_video_basic(item)
            if video:
                if not any(v['vod_id'] == video['vod_id'] for v in videos):
                    videos.append(video)
        return videos

    def homeContent(self, filter):
        classes = []
        for cat in self.CATEGORIES:
            classes.append({
                'type_name': cat['type_name'],
                'type_id': self._normalize_url(cat['type_id'])
            })
        
        recommend = []
        try:
            data = self.getpq(self.fetch(self.host, headers=self.headers).text)
            recommend = self._get_video_list(data)[:30]
        except:
            pass
        
        return {'class': classes, 'list': recommend}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            if pg == '1':
                url = tid.rstrip('/')
                data = self.getpq(self.fetch(url, headers=self.headers).text)
                videos = self._get_video_list(data)
                
                total_batches = 20
                loadmore = data('.loadmore')
                if loadmore:
                    total = loadmore.attr('total')
                    if total:
                        try:
                            total_batches = int(total)
                        except:
                            pass
                
                return {
                    'list': videos[:30],
                    'page': 1,
                    'pagecount': total_batches,
                    'limit': 30,
                    'total': 30 * total_batches
                }
            
            page = int(pg)
            base_url = tid.rstrip('/')
            load_url = f"{base_url}/{page}.html?{random.random()}"
            
            resp = self.fetch(load_url, headers=self.headers)
            data = self.getpq(resp.text)
            videos = self._get_video_list(data)
            
            return {
                'list': videos[:30],
                'page': page,
                'pagecount': 20,
                'limit': 30,
                'total': 600
            }
            
        except Exception as e:
            return {
                'list': [], 
                'page': int(pg), 
                'pagecount': 1, 
                'limit': 30, 
                'total': 0
            }

    def detailContent(self, ids):
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            data = self.getpq(self.fetch(vid, headers=self.headers).text)

            vod_name = data('meta[name="name"]').attr('content') or \
                      data('h1').text().strip() or \
                      data('title').text().strip()
            vod_name = re.sub(r'[-_|]?八影短劇網.*$', '', vod_name).strip()
            
            vod_pic = data('meta[name="pic"]').attr('content') or ''
            if vod_pic:
                vod_pic = self._normalize_url(vod_pic)
            else:
                for sel in ['.item-cover img', '.poster img', '.cover img', '.pic img']:
                    img = data(sel).attr('src')
                    if img:
                        vod_pic = self._normalize_url(img)
                        break
            
            vod_actor = data('meta[name="author"]').attr('content') or ''
            vod_type = data('meta[name="cat"]').attr('content') or ''
            vod_year = data('meta[name="date"]').attr('content') or ''
            if vod_year:
                vod_year = vod_year.split('-')[0]
            
            vod_remarks = data('meta[name="count"]').attr('content') or ''
            if vod_remarks:
                vod_remarks = f"{vod_remarks}集"
            
            vod_content = ''
            
            episodes = []
            episode_items = data('#episodes li a')
            
            for item in episode_items.items():
                ep_url = self._normalize_url(item.attr('href'))
                ep_name = item.text().strip()
                if ep_url and ep_name:
                    episodes.append(f"{ep_name}${ep_url}")
            
            if not episodes:
                episodes = [f"播放${vid}"]
            
            vod = {
                'vod_id': vid,
                'vod_name': vod_name or '未知片名',
                'vod_pic': vod_pic or '',
                'vod_content': vod_content or '暫無簡介',
                'vod_year': vod_year,
                'vod_area': '',
                'vod_remarks': vod_remarks,
                'vod_actor': vod_actor,
                'vod_director': '',
                'vod_type': vod_type
            }

            vod['vod_play_from'] = '八影短劇'
            vod['vod_play_url'] = '#'.join(episodes)

            return {'list': [vod]}
            
        except Exception as e:
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        # 參考包子短劇：直接把播放頁 URL 傳給 TVBox，讓它自己解析
        # 這樣 TVBox 會從頁面中提取 video 標籤的 src 進行播放
        return {
            'parse': 1,
            'playUrl': '',
            'url': id
        }

    def searchContent(self, key, quick, pg="1"):
        try:
            time.sleep(1)
            
            if pg == '1':
                encoded = urllib.parse.quote(key)
                url = f"{self.host}/search/?key={encoded}"
                data = self.getpq(self.fetch(url, headers=self.headers).text)
                
                if 'alert' in data.text() and '請間隔10秒後再搜尋' in data.text():
                    print("搜尋太頻繁，等待10秒...")
                    time.sleep(10)
                    data = self.getpq(self.fetch(url, headers=self.headers).text)
                
                results = self._get_video_list(data)
                return {
                    'list': results[:50],
                    'page': 1,
                    'pagecount': 20,
                    'limit': 30,
                    'total': 600
                }
            
            page = int(pg)
            encoded_key = urllib.parse.quote(key)
            load_url = f"{self.host}/data/search.aspx?key={encoded_key}&page={page}"
            
            resp = self.fetch(load_url, headers=self.headers)
            data = self.getpq(resp.text)
            results = self._get_video_list(data)
            
            return {
                'list': results[:50],
                'page': page,
                'pagecount': 20,
                'limit': 30,
                'total': 600
            }
            
        except Exception as e:
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        pass