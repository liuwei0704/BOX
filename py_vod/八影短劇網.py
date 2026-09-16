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
        # 如果是图片URL且包含 /p/ 路径，确保使用完整域名
        if '/p/' in url and not url.startswith('http'):
            return f"{self.host}{url if url.startswith('/') else '/' + url}"
        return url
    
    def _fix_image_url(self, url):
        """修复图片URL，添加防盗链参数"""
        if not url:
            return url
        # 8movie的图片可能需要添加参数绕过防盗链
        if '8movie.com' in url and '/p/' in url:
            # 添加随机参数防止缓存问题
            if '?' not in url:
                url = url + '?v=' + str(int(time.time()))
        return url

    def _extract_video_basic(self, item):
        try:
            # 尝试多种方式获取链接
            link_elem = item('a') if item('a') else item.find('a')
            if not link_elem:
                return None
                
            link = self._normalize_url(link_elem.attr('href'))
            if not link or '/movies/' not in link:
                return None

            title = link_elem.attr('title') or item('h6').text().strip() or item.text().strip()
            title = re.sub(r'\s+', ' ', title).strip()
            if not title:
                return None
                
            # 修复图片提取：支持多种懒加载属性
            img_elem = item('img')
            if not img_elem:
                img_elem = item.find('img')
            
            img = ''
            if img_elem:
                # 优先取 data-src，再取 data-original，最后取 src
                img = img_elem.attr('data-src') or img_elem.attr('data-original') or img_elem.attr('src') or ''
                # 如果 src 是占位图，尝试从 data-src 再取一次
                if img and 'cover-placeholder' in img:
                    img = img_elem.attr('data-src') or img_elem.attr('data-original') or ''
            
            # 如果 img 为空或占位图，尝试从父级或其他属性获取
            if not img or 'cover-placeholder' in img:
                # 尝试从 style 中的 background-image 提取
                style = item.attr('style') or ''
                bg_match = re.search(r'url\([\'"]?([^\'"()]+)[\'"]?\)', style)
                if bg_match:
                    img = bg_match.group(1)
            
            img = self._normalize_url(img)
            
            remarks = item('eps').text().strip() or item('.eps').text().strip() or ''
            
            return {
                'vod_id': link,
                'vod_name': title,
                'vod_pic': img,
                'vod_remarks': remarks,
                'vod_year': ''
            }
        except Exception as e:
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
        
        selectors = [
            '.col-4',
            '.col-4.p-2',
            '.row .col-4',
            '.pagemore .col-4.col-lg-2',
            '.video-item',
            '.movie-item',
            '.item',
        ]
        
        items = None
        for sel in selectors:
            temp = data(sel)
            if temp and len(temp) > 0:
                items = temp
                break
        
        if not items or len(items) == 0:
            links = data('a[href*="/movies/"]')
            if links and len(links) > 0:
                parent_items = []
                for link in links.items():
                    parent = link.closest('.col-4, .item, .video-item, .movie-item')
                    if parent and len(parent) > 0:
                        parent_items.append(parent)
                if parent_items:
                    items = parent_items[0]
        
        if items:
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
            resp = self.fetch(self.host, headers=self.headers)
            data = self.getpq(resp.text)
            
            # 直接提取最新更新区域的所有视频卡片
            # 页面结构: .card.mt-3.bg-black.bordersm 包含最新更新
            # 每个视频卡片在 .col-4.col-sm-4.col-md-4.col-lg-2.p-2 内
            latest_items = data('.card.mt-3.bg-black.bordersm .col-4.col-sm-4.col-md-4.col-lg-2.p-2')
            
            if not latest_items or len(latest_items) == 0:
                # 备用选择器
                latest_items = data('.row .col-4.p-2')
            
            if latest_items and len(latest_items) > 0:
                for item in latest_items.items():
                    video = self._extract_video_basic(item)
                    if video:
                        recommend.append(video)
            else:
                # 如果还是没有，尝试全页面提取
                recommend = self._get_video_list(data)
            
            recommend = recommend[:30]
        except Exception as e:
            print(f"homeContent 提取失敗: {e}")
        
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
                    img_elem = data(sel)
                    img = img_elem.attr('data-src') or img_elem.attr('src')
                    if img:
                        vod_pic = self._normalize_url(img)
                        break
            
            # 参考 encrypted_image_example.md 的处理方式
            # 下载图片并转为 data:image 格式，绕过防盗链
            if vod_pic and '8movie.com/p/' in vod_pic:
                try:
                    import base64
                    # 携带 Referer 下载图片
                    img_resp = self.fetch(vod_pic, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://8movie.com/',
                        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
                    })
                    if img_resp and img_resp.content:
                        # 检查是否是有效的图片数据（不是 HTML）
                        content = img_resp.content
                        # JPEG: FFD8FF, PNG: 89504E47, GIF: 47494638
                        is_image = (content[:2] == b'\xff\xd8' or 
                                   content[:4] == b'\x89PNG' or 
                                   content[:3] == b'GIF')
                        if is_image:
                            img_data = base64.b64encode(content).decode('utf-8')
                            # 检测图片类型
                            if content[:4] == b'\x89PNG':
                                mime = 'image/png'
                            elif content[:2] == b'\xff\xd8':
                                mime = 'image/jpeg'
                            elif content[:3] == b'GIF':
                                mime = 'image/gif'
                            else:
                                mime = 'image/jpeg'
                            vod_pic = f"data:{mime};base64,{img_data}"
                            print(f"详情页封面转Base64成功")
                        else:
                            print(f"详情页封面不是图片数据，可能是防盗链页面")
                except Exception as e:
                    print(f"详情页封面转Base64失败: {e}")
                    # 失败时保留原始URL
            
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
            print(f"detailContent 错误: {e}")
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
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