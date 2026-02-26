# 爬虫名称: ur95短剧爬虫
# 目标网站: https://www.ur95.com
# 版本: 最终完美版（所有功能正常）

import re
import json
from base.spider import Spider

class Spider(Spider):
    def init(self, extend):
        self.siteUrl = 'https://www.ur95.com'
        return
        
    def getName(self):
        return '热播短剧网'
        
    def getType(self):
        return 3
        
    def getVersion(self):
        return 1
        
    def homeContent(self, filter):
        result = {'class': [], 'list': []}
        try:
            self.init(None)
            response = self.fetch(self.siteUrl)
            if response and hasattr(response, 'text'):
                html = response.text
                
                # 1. 提取分类列表
                id_pattern = r'<a href="/duan/(\d+)\.html"'
                ids = re.findall(id_pattern, html)
                
                class_names = {
                    '1': '重生', '2': '穿越', '3': '爽剧', '4': '言情',
                    '5': '都市', '6': '古装', '7': '悬疑', '8': '剧情'
                }
                
                seen = set()
                for tid in ids:
                    if tid not in seen and tid in class_names:
                        seen.add(tid)
                        result['class'].append({
                            'type_id': tid, 
                            'type_name': class_names[tid]
                        })
                
                # 2. 提取首页视频列表
                module_pattern = r'<div class="module-item">.*?<a href="/daquan/(\d+)\.html"[^>]*title="([^"]+)".*?<img[^>]*data-src="([^"]+)"[^>]*>'
                items = re.findall(module_pattern, html, re.DOTALL)
                
                for vid, title, pic in items:
                    if len(result['list']) < 20:
                        result['list'].append({
                            'vod_id': vid,
                            'vod_name': title.strip(),
                            'vod_pic': pic,
                            'vod_remarks': ''
                        })
        except Exception as e:
            pass
        return result
    
    def categoryContent(self, tid, pg, filter, extend):
        result = {
            'page': pg,
            'pagecount': 1,
            'limit': 24,
            'total': 0,
            'list': []
        }
        
        try:
            self.init(None)
            if pg == 1 or pg == '1':
                url = f'{self.siteUrl}/duan/{tid}.html'
            else:
                url = f'{self.siteUrl}/duan/{tid}_{pg}.html'
            
            response = self.fetch(url)
            if response and hasattr(response, 'text'):
                html = response.text
                
                # 提取总页数
                last_page_match = re.search(r'<a href="/duan/\d+-(\d+)\.html"[^>]*title="尾页"', html)
                if last_page_match:
                    result['pagecount'] = int(last_page_match.group(1))
                
                # 提取视频列表
                module_pattern = r'<div class="module-item">.*?<a href="/daquan/(\d+)\.html"[^>]*title="([^"]+)".*?<img[^>]*data-src="([^"]+)"[^>]*>'
                items = re.findall(module_pattern, html, re.DOTALL)
                
                for vid, title, pic in items:
                    result['list'].append({
                        'vod_id': vid,
                        'vod_name': title.strip(),
                        'vod_pic': pic,
                        'vod_remarks': ''
                    })
                
                result['total'] = len(result['list'])
        except:
            pass
        
        return result
    
    def detailContent(self, ids):
        vod_id = ids[0]
        result = {'list': []}
        
        try:
            self.init(None)
            url = f'{self.siteUrl}/daquan/{vod_id}.html'
            response = self.fetch(url)
            
            if response and hasattr(response, 'text'):
                html = response.text
                
                vod_info = {
                    'vod_id': vod_id,
                    'vod_name': '',
                    'vod_pic': '',
                    'vod_actor': '',
                    'vod_director': '',
                    'vod_content': '',
                    'vod_year': '',
                    'vod_area': '',
                    'vod_play_from': '',
                    'vod_play_url': ''
                }
                
                # 1. 從 meta 標籤提取基本信息
                title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
                if title_match:
                    vod_info['vod_name'] = title_match.group(1)
                
                pic_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                if pic_match:
                    vod_info['vod_pic'] = pic_match.group(1)
                
                area_match = re.search(r'<meta property="og:video:area" content="([^"]+)"', html)
                if area_match:
                    vod_info['vod_area'] = area_match.group(1)
                
                date_match = re.search(r'<meta property="og:video:update_date" content="([^"]+)"', html)
                if date_match:
                    vod_info['vod_year'] = date_match.group(1)[:4]
                
                director_match = re.search(r'<meta property="og:video:director" content="([^"]+)"', html)
                if director_match:
                    vod_info['vod_director'] = director_match.group(1)
                
                actor_match = re.search(r'<meta property="og:video:actor" content="([^"]+)"', html)
                if actor_match:
                    vod_info['vod_actor'] = actor_match.group(1)
                
                desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
                if desc_match:
                    vod_info['vod_content'] = desc_match.group(1)
                
                # 2. 從 HTML 提取播放列表
                # 先找播放源標籤
                source_pattern = r'<li><a href="#playlist(\d+)"[^>]*>.*?<i class="icon-play"></i>&nbsp;([^<]+)</a>'
                sources = re.findall(source_pattern, html, re.DOTALL)
                
                play_from = []
                play_url = []
                
                for source_id, source_name in sources:
                    source_name = source_name.strip()
                    play_from.append(source_name)
                    
                    # 查找對應的播放列表
                    playlist_pattern = f'<div id="playlist{source_id}"[^>]*>(.*?)</div>'
                    playlist_match = re.search(playlist_pattern, html, re.DOTALL)
                    
                    if playlist_match:
                        playlist_html = playlist_match.group(1)
                        
                        # 提取劇集
                        episode_pattern = r'<a[^>]*title="([^"]*)"[^>]*href="(/play/[^"]+)"[^>]*>'
                        episodes = re.findall(episode_pattern, playlist_html)
                        
                        episode_list = []
                        for title, path in episodes:
                            if title:  # 只添加有標題的劇集
                                full_url = path
                                if not path.startswith('http'):
                                    if path.startswith('//'):
                                        full_url = 'https:' + path
                                    else:
                                        full_url = self.siteUrl + path
                                episode_list.append(f"{title}${full_url}")
                        
                        if episode_list:
                            play_url.append('$$$'.join(episode_list))
                        else:
                            play_url.append('')
                    else:
                        play_url.append('')
                
                # 如果上面的方式沒找到，直接查找所有播放列表div
                if not play_from:
                    playlist_divs = re.findall(r'<div id="playlist(\d+)"[^>]*>(.*?)</div>', html, re.DOTALL)
                    for i, (pid, content) in enumerate(playlist_divs):
                        source_name = f'線路{i+1}'
                        play_from.append(source_name)
                        
                        # 提取劇集
                        episode_pattern = r'<a[^>]*title="([^"]*)"[^>]*href="(/play/[^"]+)"[^>]*>'
                        episodes = re.findall(episode_pattern, content)
                        
                        episode_list = []
                        for title, path in episodes:
                            if title:
                                full_url = path
                                if not path.startswith('http'):
                                    if path.startswith('//'):
                                        full_url = 'https:' + path
                                    else:
                                        full_url = self.siteUrl + path
                                episode_list.append(f"{title}${full_url}")
                        
                        if episode_list:
                            play_url.append('$$$'.join(episode_list))
                
                if play_from and play_url:
                    vod_info['vod_play_from'] = '$$$'.join(play_from)
                    vod_info['vod_play_url'] = '$$$'.join(play_url)
                
                result['list'] = [vod_info]
        except Exception as e:
            pass
        
        return result
    
    def searchContent(self, key, quick):
        result = {'list': []}
        
        try:
            self.init(None)
            url = f'{self.siteUrl}/search.php?searchword={key}'
            response = self.fetch(url)
            
            if response and hasattr(response, 'text'):
                html = response.text
                
                module_pattern = r'<div class="module-item">.*?<a href="/daquan/(\d+)\.html"[^>]*title="([^"]+)".*?<img[^>]*data-src="([^"]+)"[^>]*>'
                items = re.findall(module_pattern, html, re.DOTALL)
                
                for vid, title, pic in items:
                    if key.lower() in title.lower():
                        result['list'].append({
                            'vod_id': vid,
                            'vod_name': title.strip(),
                            'vod_pic': pic,
                            'vod_remarks': ''
                        })
        except:
            pass
        
        return result
    
    def playerContent(self, flag, id, vipFlags):
        result = {}
        
        try:
            self.init(None)
            if id.startswith('http'):
                url = id
            else:
                url = self.siteUrl + id
            
            response = self.fetch(url)
            if response and hasattr(response, 'text'):
                html = response.text
                
                # 1. 查找 now 變量（播放頁中的視頻地址）
                now_match = re.search(r'var\s+now\s*=\s*[\'"]([^\'"]+\.m3u8[^\'"]*)[\'"]', html)
                if now_match:
                    video_url = now_match.group(1)
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    result['url'] = video_url
                    result['parse'] = 0
                    return result
                
                # 2. 查找直接視頻地址
                direct_match = re.search(r'https?://[^\'"]+\.(?:rsfcxq|yczy|dbzy|byxca|yspinh)[^\'"]+\.m3u8[^\'"]*', html)
                if direct_match:
                    video_url = direct_match.group(0)
                    result['url'] = video_url
                    result['parse'] = 0
                    return result
                
                # 3. 查找任何 m3u8 連結
                m3u8_match = re.search(r'https?://[^\'"]+\.m3u8[^\'"]*', html)
                if m3u8_match:
                    video_url = m3u8_match.group(0)
                    result['url'] = video_url
                    result['parse'] = 0
                    return result
            
            result['url'] = url
            result['parse'] = 1
        except:
            result['url'] = url
            result['parse'] = 1
        
        return result
    
    def localProxy(self, param):
        return None