# -*- coding: utf-8 -*-
# 针对 https://minidrama.contentchina.com/category/list 的爬虫
import base64
import binascii
import json
import random
import sys
import time
import uuid
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Hash import MD5
from Crypto.Util.Padding import unpad, pad

sys.path.append('..')
from base.spider import Spider


class MiniDramaSpider(Spider):

    def init(self, extend=""):
        """
        初始化函数
        """
        self.host = 'https://minidrama.contentchina.com'
        self.did = self.random_str(16)  # 设备ID
        self.uid = self.random_str(24)  # 用户ID
        self.token = None
        self.session_id = str(int(time.time() * 1000))
        
        # 尝试获取token（如果需要的话）
        self.get_initial_token()
        
    def getName(self):
        """
        返回爬虫名称
        """
        return "迷你短剧"
    
    def isVideoFormat(self, url):
        """
        判断是否为视频格式
        """
        video_ext = ['.mp4', '.m3u8', '.flv', '.avi', '.mov', '.mkv']
        return any(ext in url.lower() for ext in video_ext)
    
    def manualVideoCheck(self):
        """
        手动视频检查
        """
        pass
    
    def destroy(self):
        """
        销毁函数
        """
        pass
    
    def random_str(self, length=16):
        """
        生成随机字符串
        """
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join(random.choice(chars) for _ in range(length))
    
    def get_initial_token(self):
        """
        获取初始token（如果需要认证）
        """
        try:
            # 如果网站需要token，可以在这里实现获取逻辑
            # 目前假设不需要认证
            self.token = self.random_str(32)
            return True
        except Exception as e:
            print(f"获取token失败: {e}")
            self.token = self.random_str(32)
            return False
    
    def md5(self, text):
        """
        MD5加密
        """
        h = MD5.new()
        h.update(text.encode('utf-8'))
        return h.hexdigest()
    
    def build_headers(self):
        """
        构建请求头
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': f'{self.host}/',
            'Origin': self.host,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            headers['X-Session-Id'] = self.session_id
            headers['X-Device-Id'] = self.did
            headers['X-User-Id'] = self.uid
        
        return headers
    
    def parse_category_list(self, html_content):
        """
        解析分类列表页面
        """
        categories = []
        
        try:
            # 这里需要根据实际页面结构进行解析
            # 假设页面是JSON格式
            data = json.loads(html_content)
            
            if isinstance(data, dict) and 'data' in data:
                items = data['data']
                if isinstance(items, list):
                    for item in items:
                        category = {
                            'type_id': item.get('id', ''),
                            'type_name': item.get('name', ''),
                            'type_pic': item.get('cover', ''),
                            'type_desc': item.get('description', ''),
                            'video_count': item.get('video_count', 0)
                        }
                        categories.append(category)
        except json.JSONDecodeError:
            # 如果不是JSON，可能是HTML，需要用其他方式解析
            # 这里简化处理，实际需要根据页面结构调整
            pass
        
        return categories
    
    def homeContent(self, filter):
        """
        首页内容
        """
        result = {}
        
        try:
            # 获取分类列表
            headers = self.build_headers()
            response = self.fetch(f'{self.host}/category/list', headers=headers)
            
            if response and response.text:
                categories = self.parse_category_list(response.text)
                
                # 构建分类数据
                classes = []
                for cat in categories:
                    classes.append({
                        'type_id': cat['type_id'],
                        'type_name': cat['type_name']
                    })
                
                # 如果没有获取到分类，使用默认分类
                if not classes:
                    classes = [
                        {'type_id': '1', 'type_name': '热门短剧'},
                        {'type_id': '2', 'type_name': '最新更新'},
                        {'type_id': '3', 'type_name': '古装剧场'},
                        {'type_id': '4', 'type_name': '现代都市'},
                        {'type_id': '5', 'type_name': '爱情剧场'},
                        {'type_id': '6', 'type_name': '悬疑惊悚'},
                    ]
                
                result['class'] = classes
                
                # 构建筛选器
                filters = {}
                for cat in classes[:3]:  # 只给前3个分类添加筛选器
                    type_id = cat['type_id']
                    filters[type_id] = [
                        {
                            'key': 'sort',
                            'name': '排序',
                            'value': [
                                {'n': '最新', 'v': 'newest'},
                                {'n': '最热', 'v': 'hotest'},
                                {'n': '评分', 'v': 'rating'}
                            ]
                        },
                        {
                            'key': 'year',
                            'name': '年份',
                            'value': [
                                {'n': '全部', 'v': 'all'},
                                {'n': '2024', 'v': '2024'},
                                {'n': '2023', 'v': '2023'},
                                {'n': '2022', 'v': '2022'}
                            ]
                        }
                    ]
                
                result['filters'] = filters
                
            else:
                # 如果请求失败，返回默认数据
                result['class'] = [
                    {'type_id': 'all', 'type_name': '全部'},
                    {'type_id': 'hot', 'type_name': '热门'},
                    {'type_id': 'new', 'type_name': '最新'}
                ]
                result['filters'] = {}
                
        except Exception as e:
            print(f"首页内容获取失败: {e}")
            result['class'] = [
                {'type_id': 'all', 'type_name': '全部'},
                {'type_id': 'hot', 'type_name': '热门'},
                {'type_id': 'new', 'type_name': '最新'}
            ]
            result['filters'] = {}
        
        return result
    
    def homeVideoContent(self):
        """
        首页视频推荐
        """
        try:
            headers = self.build_headers()
            # 获取推荐视频
            params = {
                'page': 1,
                'limit': 12,
                'sort': 'recommend'
            }
            
            response = self.fetch(f'{self.host}/api/video/recommend', headers=headers, params=params)
            
            videos = []
            if response and response.text:
                data = json.loads(response.text)
                if data.get('code') == 0 and 'data' in data:
                    for item in data['data']:
                        video = {
                            'vod_id': item.get('id', ''),
                            'vod_name': item.get('title', ''),
                            'vod_pic': item.get('cover', ''),
                            'vod_remarks': item.get('duration', ''),
                            'vod_year': item.get('year', ''),
                            'vod_score': item.get('score', '')
                        }
                        videos.append(video)
            
            return {'list': videos}
            
        except Exception as e:
            print(f"首页视频获取失败: {e}")
            return {'list': []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """
        分类内容
        """
        result = {
            'list': [],
            'page': int(pg),
            'pagecount': 999,
            'limit': 20,
            'total': 9999
        }
        
        try:
            headers = self.build_headers()
            
            # 构建请求参数
            params = {
                'page': pg,
                'limit': 20,
                'category_id': tid if tid != 'all' else ''
            }
            
            # 添加筛选条件
            if extend:
                if 'sort' in extend:
                    params['sort'] = extend['sort']
                if 'year' in extend and extend['year'] != 'all':
                    params['year'] = extend['year']
            
            # 根据分类ID选择不同的API
            if tid == 'hot':
                url = f'{self.host}/api/video/hot'
            elif tid == 'new':
                url = f'{self.host}/api/video/latest'
            else:
                url = f'{self.host}/api/video/category'
            
            response = self.fetch(url, headers=headers, params=params)
            
            if response and response.text:
                data = json.loads(response.text)
                
                if data.get('code') == 0 and 'data' in data:
                    items = data['data']
                    if 'list' in items:
                        items = items['list']
                    
                    for item in items:
                        video = {
                            'vod_id': item.get('id', ''),
                            'vod_name': item.get('title', ''),
                            'vod_pic': item.get('cover', ''),
                            'vod_remarks': item.get('episodes', '') + '集',
                            'vod_year': item.get('year', ''),
                            'vod_score': item.get('score', ''),
                            'vod_content': item.get('description', '')
                        }
                        result['list'].append(video)
            
        except Exception as e:
            print(f"分类内容获取失败: {e}")
        
        return result
    
    def detailContent(self, ids):
        """
        详情页面
        """
        vod_id = ids[0]
        result = {'list': []}
        
        try:
            headers = self.build_headers()
            response = self.fetch(f'{self.host}/api/video/detail/{vod_id}', headers=headers)
            
            if response and response.text:
                data = json.loads(response.text)
                
                if data.get('code') == 0 and 'data' in data:
                    item = data['data']
                    
                    # 解析播放列表
                    play_list = []
                    if 'episodes' in item and isinstance(item['episodes'], list):
                        for idx, ep in enumerate(item['episodes'], 1):
                            play_url = ep.get('url', '')
                            if play_url:
                                play_list.append(f'第{idx}集${play_url}')
                    
                    vod = {
                        'vod_id': item.get('id', ''),
                        'vod_name': item.get('title', ''),
                        'vod_pic': item.get('cover', ''),
                        'vod_year': item.get('year', ''),
                        'vod_area': item.get('area', ''),
                        'vod_remarks': item.get('episode_count', '') + '集全',
                        'vod_actor': item.get('actors', ''),
                        'vod_director': item.get('director', ''),
                        'vod_content': item.get('description', ''),
                        'vod_play_from': '迷你短剧',
                        'vod_play_url': '#'.join(play_list) if play_list else ''
                    }
                    
                    result['list'].append(vod)
            
        except Exception as e:
            print(f"详情内容获取失败: {e}")
        
        return result
    
    def searchContent(self, key, quick, pg="1"):
        """
        搜索内容
        """
        result = {
            'list': [],
            'page': int(pg),
            'pagecount': 10,
            'limit': 20,
            'total': 200
        }
        
        try:
            headers = self.build_headers()
            params = {
                'keyword': key,
                'page': pg,
                'limit': 20
            }
            
            response = self.fetch(f'{self.host}/api/video/search', headers=headers, params=params)
            
            if response and response.text:
                data = json.loads(response.text)
                
                if data.get('code') == 0 and 'data' in data:
                    items = data['data']
                    if 'list' in items:
                        items = items['list']
                    
                    for item in items:
                        video = {
                            'vod_id': item.get('id', ''),
                            'vod_name': item.get('title', ''),
                            'vod_pic': item.get('cover', ''),
                            'vod_remarks': item.get('episodes', '') + '集',
                            'vod_year': item.get('year', ''),
                            'vod_content': item.get('description', '')[:50] + '...'
                        }
                        result['list'].append(video)
            
        except Exception as e:
            print(f"搜索内容获取失败: {e}")
        
        return result
    
    def playerContent(self, flag, id, vipFlags):
        """
        播放器内容
        """
        result = {
            'parse': 0,  # 0表示直接播放，1表示需要解析
            'url': id,
            'header': self.build_headers()
        }
        
        # 如果需要解析，可以在这里添加解析逻辑
        if flag == '解析':
            result['parse'] = 1
            result['jx'] = 1
        
        return result
    
    def localProxy(self, param):
        """
        本地代理，用于图片解密等
        """
        # 这里可以根据需要实现图片解密等功能
        # 暂时直接返回原数据
        return {
            'code': 200,
            'header': {
                'Content-Type': 'image/jpeg',
                'Cache-Control': 'max-age=86400'
            },
            'body': b''
        }


# 注册爬虫
if __name__ == '__main__':
    spider = MiniDramaSpider()