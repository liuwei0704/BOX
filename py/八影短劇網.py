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

    # ------------------------- 網站配置 -------------------------
    host = 'https://8movie.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G9910) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Referer': 'https://8movie.com',
        'X-Requested-With': 'XMLHttpRequest'
    }

    # ------------------------- 分類列表（硬編碼保證首頁顯示）-------------------------
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
        """從列表項提取影片信息"""
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
        """提取影片列表（用於分類頁和搜索頁）"""
        videos = []
        items = data('.pagemore .col-4.col-lg-2, .row .col-4, .col-4.p-2')
        for item in items.items():
            video = self._extract_video_basic(item)
            if video:
                # 去重
                if not any(v['vod_id'] == video['vod_id'] for v in videos):
                    videos.append(video)
        return videos

    def homeContent(self, filter):
        """首頁：分類 + 推薦"""
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
        """分類頁 - 支援滾動加載分頁"""
        try:
            # 第1頁：直接訪問分類URL
            if pg == '1':
                url = tid.rstrip('/')
                data = self.getpq(self.fetch(url, headers=self.headers).text)
                videos = self._get_video_list(data)
                
                # 獲取總批數
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
            
            # ============= 第2頁及以後：使用真正的加載接口 =============
            # 接口規則：當前頁面URL + "/" + 批次號 + ".html?" + 隨機數
            page = int(pg)
            base_url = tid.rstrip('/')
            load_url = f"{base_url}/{page}.html?{random.random()}"
            
            resp = self.fetch(load_url, headers=self.headers)
            html_content = resp.text
            data = self.getpq(html_content)
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
        """
        詳情頁 - 完整提取影片資訊和分集列表！
        從你給的HTML可以看到完整的110集
        """
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            data = self.getpq(self.fetch(vid, headers=self.headers).text)

            # ============ 1. 從 meta 標籤提取完整資訊 ============
            # 影片名稱
            vod_name = data('meta[name="name"]').attr('content') or \
                      data('h1').text().strip() or \
                      data('title').text().strip()
            vod_name = re.sub(r'[-_|]?八影短劇網.*$', '', vod_name).strip()
            
            # 封面圖片
            vod_pic = data('meta[name="pic"]').attr('content') or ''
            if vod_pic:
                vod_pic = self._normalize_url(vod_pic)
            else:
                for sel in ['.item-cover img', '.poster img', '.cover img', '.pic img']:
                    img = data(sel).attr('src')
                    if img:
                        vod_pic = self._normalize_url(img)
                        break
            
            # 演員/作者
            vod_actor = data('meta[name="author"]').attr('content') or ''
            
            # 分類
            vod_type = data('meta[name="cat"]').attr('content') or ''
            
            # 年份
            vod_year = data('meta[name="date"]').attr('content') or ''
            if vod_year:
                vod_year = vod_year.split('-')[0]
            
            # 總集數
            vod_remarks = data('meta[name="count"]').attr('content') or ''
            if vod_remarks:
                vod_remarks = f"{vod_remarks}集"
            
            # 簡介（HTML中沒有，留空）
            vod_content = ''
            
            # ============ 2. 提取完整分集列表 ============
            episodes = []
            episode_items = data('#episodes li a')
            
            for item in episode_items.items():
                ep_url = self._normalize_url(item.attr('href'))
                ep_name = item.text().strip()
                if ep_url and ep_name:
                    episodes.append(f"{ep_name}${ep_url}")
            
            # 如果沒有分集，使用默認播放
            if not episodes:
                episodes = [f"播放${vid}"]
            
            # ============ 3. 組裝返回數據 ============
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
        """
        播放頁 - 解析真實視頻地址
        格式: /play/10993/1
        """
        try:
            # 直接訪問播放頁
            play_url = self._normalize_url(id)
            
            data = self.getpq(self.fetch(play_url, headers=self.headers).text)
            
            # ============ 1. 提取 video 標籤 ============
            video_src = data('video').attr('src') or \
                       data('video source').attr('src') or \
                       data('source').attr('src')
            
            if video_src:
                real_url = self._normalize_url(video_src)
                return {
                    'parse': 0,
                    'url': real_url,
                    'header': self.headers
                }
            
            # ============ 2. 提取 iframe ============
            iframe_src = data('iframe').attr('src')
            if iframe_src:
                real_url = self._normalize_url(iframe_src)
                return {
                    'parse': 1,
                    'url': real_url,
                    'header': self.headers
                }
            
            # ============ 3. 從 script 中提取視頻地址 ============
            scripts = data('script').text()
            
            # 嘗試匹配常見的視頻地址模式
            patterns = [
                r'["\'](https?://[^"\']+\.(?:mp4|m3u8|flv|mkv|avi))["\']',
                r'url["\']?\s*:\s*["\']([^"\']+)["\']',
                r'src["\']?\s*:\s*["\']([^"\']+)["\']',
                r'video[_-]url["\']?\s*:\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, scripts, re.I)
                for match in matches:
                    if match and 'http' in match:
                        real_url = self._normalize_url(match)
                        return {
                            'parse': 0,
                            'url': real_url,
                            'header': self.headers
                        }
            
            # ============ 4. 回退 ============
            return {
                'parse': 1,
                'url': play_url,
                'header': self.headers
            }
            
        except Exception as e:
            return {
                'parse': 1,
                'url': id,
                'header': self.headers
            }

    def searchContent(self, key, quick, pg="1"):
        """
        搜索功能 - 支援分頁，加入延遲避免被封
        """
        try:
            # 加入延遲，避免搜尋太頻繁
            time.sleep(1)
            
            # 第1頁
            if pg == '1':
                encoded = urllib.parse.quote(key)
                url = f"{self.host}/search/?key={encoded}"
                data = self.getpq(self.fetch(url, headers=self.headers).text)
                
                # 檢查是否被封
                if 'alert' in data.text() and '請間隔10秒後再搜尋' in data.text():
                    print("搜尋太頻繁，等待10秒...")
                    time.sleep(10)
                    # 重試一次
                    data = self.getpq(self.fetch(url, headers=self.headers).text)
                
                results = self._get_video_list(data)
                return {
                    'list': results[:50],
                    'page': 1,
                    'pagecount': 20,
                    'limit': 30,
                    'total': 600
                }
            
            # 第2頁及以後
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