# -*- coding: utf-8 -*-
# AV猴影视 TVBox 爬虫 - 最终完美版

import re
import json
import urllib.parse
import urllib.request
import ssl

# 忽略SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context

class Spider:
    """AV猴TVBox爬虫 - 最终完美版"""
    
    def __init__(self):
        self.siteUrl = "https://avmonkey.tv"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.siteUrl
        }
        self.cateManual = {
            '国产自拍': '国产自拍-1',
            '日韩精品': '日韩精品-2',
            'onlyfans精选': 'onlyfans精选-3',
            '卡通动漫': '卡通动漫-4',
            '欧美视频': '欧美视频-5',
            '优质传媒': '优质传媒-6',
            '精品探花': '精品探花-7',
        }
        
    def getDependence(self, *args, **kwargs):
        return []
        
    def init(self, *args, **kwargs):
        pass
        
    def homeContent(self, *args, **kwargs):
        """获取首页内容"""
        result = {'class': [], 'list': []}
        
        try:
            # 添加分类
            for name, tid in self.cateManual.items():
                result['class'].append({
                    'type_id': tid,
                    'type_name': name
                })
            
            # 获取最新视频
            html = self.fetch(self.siteUrl)
            if html:
                videos = self._parse_video_list(html)
                result['list'] = videos[:20]
        except Exception as e:
            print(f"homeContent error: {e}")
            
        return result
        
    def homeVideoContent(self, *args, **kwargs):
        """获取首页视频"""
        try:
            html = self.fetch(self.siteUrl)
            if html:
                videos = self._parse_video_list(html)
                return {'list': videos[:20]}
        except:
            pass
        return {'list': []}
        
    def categoryContent(self, tid, pg=1, filter=False, ext=None, *args, **kwargs):
        """获取分类内容"""
        result = {
            'list': [],
            'page': int(pg),
            'pagecount': 1,
            'limit': 20,
            'total': 0
        }
        
        try:
            if tid in self.cateManual.values():
                cat_name = tid.split('-')[0]
                cat_id = tid.split('-')[1]
                url = f"{self.siteUrl}/categories/{urllib.parse.quote(cat_name)}-{cat_id}"
            else:
                url = f"{self.siteUrl}/categories/{urllib.parse.quote(tid)}"
            
            if int(pg) > 1:
                url = f"{url}?page={pg}"
            
            html = self.fetch(url)
            if html:
                videos = self._parse_video_list(html)
                result['list'] = videos
                
                # 获取总页数
                page_pattern = r'<a[^>]*href="[^"]*[?&]page=(\d+)"[^>]*>(\d+)</a>'
                pages = re.findall(page_pattern, html)
                if pages:
                    max_page = max([int(p[1]) for p in pages])
                    result['pagecount'] = max_page
        except Exception as e:
            print(f"categoryContent error: {e}")
            
        return result
        
    def detailContent(self, ids, *args, **kwargs):
        """获取详情内容"""
        vod_list = []
        
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            
            if vid.startswith('http'):
                url = vid
            else:
                url = f"{self.siteUrl}/video/{vid}"
            
            html = self.fetch(url)
            if html:
                vod = self._parse_detail(html, vid)
                if vod:
                    vod_list.append(vod)
        except Exception as e:
            print(f"detailContent error: {e}")
            
        return {'list': vod_list}
        
    def searchContent(self, key, quick=False, *args, **kwargs):
        """搜索内容"""
        vod_list = []
        
        try:
            encoded_key = urllib.parse.quote(key)
            url = f"{self.siteUrl}/Search/{encoded_key}"
            
            html = self.fetch(url)
            if html:
                videos = self._parse_video_list(html)
                vod_list = videos[:20]
        except Exception as e:
            print(f"searchContent error: {e}")
            
        return {'list': vod_list}
        
    def playerContent(self, flag, id, vipFlags=None, *args, **kwargs):
        """获取播放地址 - 修复版本"""
        result = {}
        
        try:
            if id.startswith('http'):
                play_url = id
            else:
                # 获取详情页HTML
                url = f"{self.siteUrl}/video/{id}"
                html = self.fetch(url)
                
                # 使用修复后的提取方法
                play_url = self._extract_play_url_fixed(html) if html else url
                
            result['url'] = play_url
            result['parse'] = 0
            result['header'] = json.dumps({
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.siteUrl
            })
        except Exception as e:
            print(f"playerContent error: {e}")
            result['url'] = id
            
        return result
        
    def _extract_play_url_fixed(self, html):
        """修复版的播放地址提取 - 优先从JSON-LD获取完整视频"""
        play_url = None
        
        # 1. 从JSON-LD提取完整视频地址
        jsonld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        jsonld_match = re.search(jsonld_pattern, html, re.DOTALL)
        if jsonld_match:
            try:
                data = json.loads(jsonld_match.group(1))
                if isinstance(data, dict):
                    # 直接获取contentUrl
                    if 'contentUrl' in data:
                        play_url = data['contentUrl']
                        return play_url
                    # 从video对象获取
                    elif 'video' in data and isinstance(data['video'], dict):
                        if 'contentUrl' in data['video']:
                            play_url = data['video']['contentUrl']
                            return play_url
            except:
                pass
        
        # 2. 如果没找到，回退到原方法
        if not play_url:
            # 查找M3U8链接
            m3u8_pattern = r'(https?://[^"\']+\.m3u8[^"\']*)'
            m3u8_match = re.search(m3u8_pattern, html)
            if m3u8_match:
                play_url = m3u8_match.group(1)
            
            # 查找API链接
            if not play_url:
                api_pattern = r'(/api/[^"\']*\.m3u8[^"\']*)'
                api_match = re.search(api_pattern, html)
                if api_match:
                    play_url = urllib.parse.urljoin(self.siteUrl, api_match.group(1))
        
        return play_url
        
    def _parse_video_list(self, html):
        """解析视频列表"""
        videos = []
        
        # 查找视频卡片
        pattern = r'<a[^>]*href="([^"]*/(?:video|archives)/([^"/?]+))"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>.*?<p[^>]*>([^<]*)</p>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for match in matches:
            try:
                url = match[0]
                vid = match[1]
                img = match[2]
                title = match[3].strip()
                
                title = re.sub(r'<[^>]+>', '', title)
                if not title or len(title) < 2:
                    continue
                    
                if not url.startswith('http'):
                    url = urllib.parse.urljoin(self.siteUrl, url)
                if not img.startswith('http'):
                    img = urllib.parse.urljoin(self.siteUrl, img)
                
                # 提取时长
                remarks = ''
                dur_match = re.search(r'(\d+:\d+)', html[html.find(title):html.find(title)+300])
                if dur_match:
                    remarks = dur_match.group(1)
                
                video = {
                    'vod_id': vid,
                    'vod_name': title[:100],
                    'vod_pic': img,
                    'vod_remarks': remarks,
                    'vod_content': title
                }
                videos.append(video)
            except:
                continue
                
        return videos
        
    def _parse_detail(self, html, vid):
        """解析详情页"""
        vod = {
            'vod_id': vid,
            'vod_name': '',
            'vod_pic': '',
            'vod_actor': '',
            'vod_director': '',
            'vod_content': '',
            'vod_play_from': 'AV猴',
            'vod_play_url': '',
            'vod_year': '',
            'vod_area': '',
            'vod_remarks': ''
        }
        
        try:
            # 提取标题
            title_match = re.search(r'<title>([^<]+)</title>', html)
            if title_match:
                title = title_match.group(1).split('|')[0].strip()
                vod['vod_name'] = title
            
            # 提取缩略图
            img_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]*)"', html)
            if not img_match:
                img_match = re.search(r'<img[^>]*src="([^"]*)"[^>]*class="[^"]*thumbnail[^"]*"', html)
            if img_match:
                vod['vod_pic'] = img_match.group(1)
            
            # 提取描述
            desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
            if desc_match:
                vod['vod_content'] = desc_match.group(1)
            
            # 获取播放地址
            play_url = self._extract_play_url_fixed(html)
            if play_url:
                vod['vod_play_url'] = f"播放地址${play_url}"
            else:
                vod['vod_play_url'] = f"播放地址${self.siteUrl}/video/{vid}"
            
            # 提取观看数
            views_match = re.search(r'([\d.]+[千万]?)[^0-9]*?播放', html)
            if views_match:
                vod['vod_remarks'] = f"{views_match.group(1)}次播放"
                
        except Exception as e:
            print(f"_parse_detail error: {e}")
            
        return vod
        
    def localProxy(self, param, *args, **kwargs):
        return None
        
    def fetch(self, url):
        """发送HTTP请求"""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                return html
        except Exception as e:
            print(f"fetch error {url}: {e}")
            return None