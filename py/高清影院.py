# -*- coding: utf-8 -*-
import requests
import re
import json
from bs4 import BeautifulSoup

class Spider:
    def __init__(self):
        self.host = 'https://cn.bitcoincams.xxx'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.session = requests.Session()
    
    def getDependence(self):
        return []
    
    def init(self, extend=""):
        return {}
    
    def homeContent(self, filter):
        """獲取首頁分類和直播列表"""
        try:
            url = f'{self.host}/'
            r = self.session.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 提取分類
            classes = []
            # 根據實際頁面結構提取分類
            
            # 提取直播列表
            videos = []
            # 根據實際頁面結構提取直播
            
            return {'class': classes, 'list': videos}
        except Exception as e:
            print(f"homeContent error: {e}")
            return {'class': [], 'list': []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """獲取分類頁內容"""
        try:
            url = f'{self.host}/category/{tid}'
            if pg != '1':
                url += f'?page={pg}'
            
            r = self.session.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            videos = []
            # 根據實際頁面結構提取
            
            return {
                'page': pg,
                'pagecount': 1,
                'limit': 30,
                'total': len(videos),
                'list': videos
            }
        except Exception as e:
            print(f"categoryContent error: {e}")
            return {'page': pg, 'pagecount': 1, 'limit': 30, 'total': 0, 'list': []}
    
    def detailContent(self, ids):
        """獲取直播詳情"""
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            url = f'{self.host}/model/{vid}'
            
            r = self.session.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            # 提取直播信息
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 從頁面中提取直播流地址
            # 可能需要從 JavaScript 變量或 iframe 中提取
            
            vod_info = {
                'vod_id': vid,
                'vod_name': '',  # 主播名稱
                'vod_pic': '',   # 預覽圖
                'vod_content': '', # 簡介
                'vod_actor': '',  # 主播信息
                'vod_area': '',   # 地區
                'vod_lang': '',   # 語言
                'vod_play_from': 'live',
                'vod_play_url': '' # 直播流地址
            }
            
            return {'list': [vod_info]}
        except Exception as e:
            print(f"detailContent error: {e}")
            return {'list': []}
    
    def searchContent(self, keyword, pg):
        """搜索功能"""
        try:
            url = f'{self.host}/search'
            params = {'q': keyword, 'page': pg}
            
            r = self.session.get(url, headers=self.headers, params=params, timeout=10)
            r.encoding = 'utf-8'
            
            videos = []
            # 根據實際頁面結構提取搜索結果
            
            return {
                'page': pg,
                'pagecount': 1,
                'limit': 30,
                'total': len(videos),
                'list': videos
            }
        except Exception as e:
            print(f"searchContent error: {e}")
            return {'list': []}
    
    def playerContent(self, flag, id, vipFlags):
        """獲取播放地址"""
        try:
            # 如果是直播流，直接返回
            if id.startswith('http'):
                return {
                    'parse': 0,
                    'playUrl': '',
                    'url': id,
                    'header': {
                        'Referer': self.host,
                        'User-Agent': self.headers['User-Agent']
                    }
                }
            
            # 如果是頁面 URL，需要解析直播流地址
            url = f'{self.host}{id}' if id.startswith('/') else id
            r = self.session.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            # 從頁面中提取直播流地址
            # 常見的直播流格式：.m3u8, .flv, rtmp://
            
            m3u8_url = None
            # 提取 m3u8 地址
            m3u8_pattern = r'(https?://[^"\']+\.m3u8[^"\']*)'
            m3u8_match = re.search(m3u8_pattern, r.text)
            if m3u8_match:
                m3u8_url = m3u8_match.group(1)
            
            if m3u8_url:
                return {
                    'parse': 0,
                    'playUrl': '',
                    'url': m3u8_url,
                    'header': {
                        'Referer': self.host,
                        'User-Agent': self.headers['User-Agent']
                    }
                }
            
            return {'parse': 0, 'playUrl': '', 'url': ''}
        except Exception as e:
            print(f"playerContent error: {e}")
            return {'parse': 0, 'playUrl': '', 'url': ''}