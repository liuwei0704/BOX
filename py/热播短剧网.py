# -*- coding: utf-8 -*-
"""
热播短剧网 - TVBox 爬蟲 (最終完美版)
適用於 https://www.gzlap.com
"""
import requests
import re
import urllib.parse

class Spider:
    def __init__(self):
        self.host = 'https://www.gzlap.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.host
        }
        
        # 分類映射
        self.type_map = {
            '1': '重生', '2': '穿越', '3': '爽剧', '4': '言情',
            '5': '都市', '6': '古装', '7': '悬疑', '8': '剧情'
        }
        
        # URL 格式
        self.url_patterns = {
            'home': '/',
            'category_first': '/csdj/{tid}.html',
            'category_page': '/csdj/{tid}-{pg}.html',
            'detail': '/chongshengduanju/{id}.html',
            'play': '/play/{id}-{sid}-{nid}.html',
            'search': '/search.php?searchword={key}&page={pg}'
        }
    
    def getDependence(self): return []
    def init(self, extend=""): return {}
    def getName(self): return "热播短剧网"
    
    def _build_url(self, pattern_key, **kwargs):
        pattern = self.url_patterns.get(pattern_key, '')
        url = pattern.format(**kwargs)
        return self.host + url if not url.startswith('http') else url
    
    def _extract_videos(self, html, max_count=0):
        videos = []
        items = html.split('<div class="module-item">')
        for item in items[1:]:
            if max_count > 0 and len(videos) >= max_count:
                break
            id_match = re.search(r'href="/chongshengduanju/(\d+)\.html"', item)
            title_match = re.search(r'title="([^"]+)"', item)
            pic_match = re.search(r'data-src="([^"]+)"', item)
            remark_match = re.search(r'<div class="module-item-text">([^<]+)</div>', item)
            if id_match and title_match and pic_match:
                videos.append({
                    'vod_id': id_match.group(1),
                    'vod_name': title_match.group(1).strip(),
                    'vod_pic': pic_match.group(1),
                    'vod_remarks': remark_match.group(1) if remark_match else ''
                })
        return videos
    
    def _extract_page_count(self, html):
        try:
            total_match = re.search(r'<a href="/csdj/\d+-(\d+)\.html" class="page-number page-next"[^>]*>尾页</a>', html)
            if total_match:
                return int(total_match.group(1))
            page_numbers = re.findall(r'<a href="/csdj/\d+-(\d+)\.html" class="page-number display"', html)
            if page_numbers:
                numbers = [int(num) for num in page_numbers if num.isdigit()]
                if numbers:
                    return max(numbers)
            return 100
        except:
            return 100
    
    def homeContent(self, filter):
        try:
            classes = [{'type_id': tid, 'type_name': name} for tid, name in self.type_map.items()]
            url = self._build_url('home')
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            videos = self._extract_videos(r.text, max_count=20)
            return {'class': classes, 'list': videos}
        except:
            return {'class': [], 'list': []}
    
    def homeVideoContent(self):
        result = self.homeContent(True)
        return {'list': result.get('list', [])}
    
    def categoryContent(self, tid, pg, filter, extend):
        try:
            url = self._build_url('category_first' if pg == 1 else 'category_page', tid=tid, pg=pg)
            r = requests.get(url, headers=self.headers, timeout=15)
            r.encoding = 'utf-8'
            videos = self._extract_videos(r.text)
            pagecount = self._extract_page_count(r.text)
            return {
                'list': videos,
                'page': pg,
                'pagecount': pagecount,
                'limit': 30,
                'total': len(videos)
            }
        except:
            return {'list': [], 'page': pg, 'pagecount': 100, 'limit': 30, 'total': 0}
    
    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            url = self._build_url('detail', id=vod_id)
            r = requests.get(url, headers=self.headers, timeout=15)
            r.encoding = 'utf-8'
            html = r.text
            
            # 基本信息
            title = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
            title = title.group(1) if title else ''
            
            pic = re.search(r'data-src="([^"]+)"', html)
            pic = pic.group(1) if pic else ''
            
            # 從meta標籤提取
            actor = re.search(r'<meta property="og:video:actor" content="([^"]+)"', html)
            actor = actor.group(1) if actor else '内详'
            
            director = re.search(r'<meta property="og:video:director" content="([^"]+)"', html)
            director = director.group(1) if director else '内详'
            
            area = re.search(r'<meta property="og:video:area" content="([^"]+)"', html)
            area = area.group(1) if area else '中国大陆'
            
            year = re.search(r'<a href="[^"]*year=(\d{4})"', html)
            year = year.group(1) if year else '2026'
            
            # 播放列表 - 正確提取線路名稱
            play_from = []
            play_url = []
            
            # 提取線路名稱 (如「红豆剧场」)
            source_names = re.findall(r'<i class="icon-play"></i>&nbsp;([^<]+)</a>', html)
            
            # 提取播放列表內容
            playlist_blocks = re.findall(r'<div id="playlist\d+" class="tab-pane fade in[^"]* clearfix">(.*?)</div>', html, re.S)
            
            if playlist_blocks and source_names:
                for idx, block in enumerate(playlist_blocks):
                    if idx < len(source_names):
                        play_from.append(source_names[idx].strip())
                        
                        episodes = []
                        ep_links = re.findall(r'<a[^>]+href="(/play/\d+-\d+-\d+\.html)"[^>]*>([^<]+)</a>', block)
                        for href, name in ep_links:
                            if name and name.strip():
                                episodes.append(f"{name}${self.host + href}")
                        
                        if episodes:
                            play_url.append('#'.join(episodes))
            
            # 默認播放地址
            if not play_url:
                play_from = source_names if source_names else ['红豆剧场']
                play_url = [f"全集完结${self.host}/play/{vod_id}-0-0.html"]
            
            vod = {
                'vod_id': vod_id,
                'vod_name': title,
                'vod_pic': pic,
                'vod_content': '暂无简介',
                'vod_actor': actor,
                'vod_director': director,
                'vod_year': year,
                'vod_area': area,
                'type_name': '重生',
                'vod_play_from': '$$$'.join(play_from),
                'vod_play_url': '$$$'.join(play_url)
            }
            return {'list': [vod]}
        except:
            return {'list': []}
    
    def searchContent(self, key, quick, pg=1):
        try:
            encoded_key = urllib.parse.quote(key)
            url = self._build_url('search', key=encoded_key, pg=pg)
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            videos = self._extract_videos(r.text)
            return {'list': videos, 'page': pg, 'pagecount': 1, 'limit': 20, 'total': len(videos)}
        except:
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 20, 'total': 0}
    
    def playerContent(self, flag, id, vipFlags):
        try:
            play_url = id if id.startswith('http') else self.host + id
            r = requests.get(play_url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            html = r.text
            
            # 從 var now 提取真實m3u8地址
            now_match = re.search(r'var now="([^"]+)"', html)
            if now_match:
                return {'parse': 0, 'playUrl': '', 'url': now_match.group(1)}
            
            video_match = re.search(r'(https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)', html)
            if video_match:
                return {'parse': 0, 'playUrl': '', 'url': video_match.group(1)}
            
            return {'parse': 1, 'playUrl': '', 'url': play_url}
        except:
            return {'parse': 0, 'playUrl': '', 'url': id}
    
    def isVideoFormat(self, url):
        return any(fmt in url.lower() for fmt in ['.mp4', '.m3u8', '.flv', '.mkv'])
    
    def localProxy(self, params):
        return []