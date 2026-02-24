# -*- coding: utf-8 -*-
import requests
import re
import html

class Spider:
    def __init__(self):
        self.host = 'https://www.moozcloud.com'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    def getDependence(self):
        return []
    
    def init(self, extend=""):
        return {}
    
    def homeContent(self, filter):
        try:
            r = requests.get(self.host, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            classes = [
                {'type_id': '1', 'type_name': '电影'},
                {'type_id': '2', 'type_name': '电视剧'},
                {'type_id': '3', 'type_name': '动漫'},
                {'type_id': '4', 'type_name': '综艺'},
                {'type_id': '27', 'type_name': '短剧'}
            ]
            
            videos = []
            pattern = r'<ul id="home1"[^>]*>(.*?)</ul>'
            match = re.search(pattern, r.text, re.S)
            
            if match:
                ul_content = match.group(1)
                item_pattern = r'<a[^>]+href="/movie/(\d+)\.html"[^>]+title="([^"]+)"[^>]+data-original="([^"]+)"[^>]*>.*?<span class="pic-text">([^<]+)</span>'
                items = re.findall(item_pattern, ul_content, re.S)
                
                for item in items[:20]:
                    videos.append({
                        'vod_id': item[0],
                        'vod_name': item[1],
                        'vod_pic': item[2],
                        'vod_remarks': item[3].strip()
                    })
            
            return {'class': classes, 'list': videos}
        except Exception as e:
            print(f"homeContent error: {e}")
            return {'class': [], 'list': []}
    
    def homeVideoContent(self):
        result = self.homeContent(True)
        return {'list': result.get('list', [])}
    
    def categoryContent(self, tid, pg, filter, extend):
        try:
            if pg == '1':
                url = f'{self.host}/class/{tid}.html'
            else:
                url = f'{self.host}/class/{tid}_{pg}.html'
            
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            videos = []
            
            li_pattern = r'<li[^>]*class="[^"]*vodlist__item[^"]*"[^>]*>(.*?)</li>'
            li_items = re.findall(li_pattern, r.text, re.S)
            
            if li_items:
                for li in li_items:
                    a_match = re.search(r'<a[^>]+href="/movie/(\d+)\.html"[^>]+title="([^"]+)"[^>]+data-original="([^"]+)"[^>]*>', li, re.S)
                    if not a_match:
                        continue
                    
                    vid, title, pic = a_match.groups()
                    
                    remark_match = re.search(r'<span class="pic-text">([^<]+)</span>', li, re.S)
                    remark = remark_match.group(1).strip() if remark_match else ''
                    
                    videos.append({
                        'vod_id': vid,
                        'vod_name': title,
                        'vod_pic': pic,
                        'vod_remarks': remark
                    })
            else:
                a_pattern = r'<a[^>]+href="/movie/(\d+)\.html"[^>]+title="([^"]+)"[^>]+data-original="([^"]+)"[^>]*>'
                a_items = re.findall(a_pattern, r.text, re.S)
                
                for item in a_items:
                    vid, title, pic = item
                    
                    remark = ''
                    pos = r.text.find(f'/movie/{vid}.html')
                    if pos > 0:
                        nearby = r.text[pos:pos+500]
                        remark_match = re.search(r'<span class="pic-text">([^<]+)</span>', nearby, re.S)
                        if remark_match:
                            remark = remark_match.group(1).strip()
                    
                    videos.append({
                        'vod_id': vid,
                        'vod_name': title,
                        'vod_pic': pic,
                        'vod_remarks': remark
                    })
            
            seen = set()
            unique_videos = []
            for v in videos:
                if v['vod_id'] not in seen:
                    seen.add(v['vod_id'])
                    unique_videos.append(v)
            
            page_pattern = r'<a[^>]+href="/class/\d+_(\d+)\.html"'
            pages = re.findall(page_pattern, r.text)
            pagecount = 1
            if pages:
                pagecount = max([int(p) for p in pages])
            
            return {
                'page': pg,
                'pagecount': pagecount,
                'limit': 30,
                'total': len(unique_videos),
                'list': unique_videos
            }
        except Exception as e:
            print(f"categoryContent error: {e}")
            return {'page': pg, 'pagecount': 1, 'limit': 30, 'total': 0, 'list': []}
    
    def clean_text(self, text):
        if not text:
            return ''
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_title(self, html_content):
        """從HTML中提取影片標題，忽略APP播放"""
        # 方法1: 從 <h1> 標籤
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
        if h1_match:
            title = self.clean_text(h1_match.group(1))
            if title and 'APP' not in title:
                return title
        
        # 方法2: 從 <h1> 標籤內的 <span> 之前
        h1_span_match = re.search(r'<h1[^>]*>([^<]+)<span', html_content)
        if h1_span_match:
            title = self.clean_text(h1_span_match.group(1))
            if title and 'APP' not in title:
                return title
        
        # 方法3: 從 meta property="og:title"
        meta_match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html_content)
        if meta_match:
            title = self.clean_text(meta_match.group(1))
            if title and 'APP' not in title:
                return title
        
        # 方法4: 從 <title> 標籤
        title_match = re.search(r'<title>([^<]+)</title>', html_content)
        if title_match:
            title = self.clean_text(title_match.group(1))
            # 清理常見的後綴
            title = re.sub(r'_[^_]+$|高清影院|免費在線觀看|全集|在线观看', '', title)
            if title and 'APP' not in title:
                return title
        
        return ''
    
    def detailContent(self, ids):
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            url = f'{self.host}/movie/{vid}.html'
            
            print(f"獲取詳情: {url}")
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            # ===== 提取標題 - 使用專門的方法 =====
            title = self.extract_title(r.text)
            print(f"提取到標題: {title}")
            
            # 圖片
            img_match = re.search(r'<img[^>]+data-original="([^"]+)"', r.text)
            if not img_match:
                img_match = re.search(r'<img[^>]+src="([^"]+)"', r.text)
            img = img_match.group(1) if img_match else ''
            
            # 簡介
            desc_match = re.search(r'<div[^>]+class="[^"]*content__desc[^"]*"[^>]*>(.*?)</div>', r.text, re.S)
            if not desc_match:
                desc_match = re.search(r'<div[^>]+class="[^"]*info-content[^"]*"[^>]*>(.*?)</div>', r.text, re.S)
            description = self.clean_text(desc_match.group(1)) if desc_match else ''
            
            # 演員
            actor_match = re.search(r'主演：</span>(.*?)</p>', r.text)
            actor = self.clean_text(actor_match.group(1)) if actor_match else ''
            
            # 導演
            director_match = re.search(r'导演：</span>(.*?)</p>', r.text)
            director = self.clean_text(director_match.group(1)) if director_match else ''
            
            # 地區
            area_match = re.search(r'地区：</span><a[^>]*>([^<]+)</a>', r.text)
            area = self.clean_text(area_match.group(1)) if area_match else ''
            
            # 年份
            year_match = re.search(r'年份：</span><a[^>]*>([^<]+)</a>', r.text)
            year = self.clean_text(year_match.group(1)) if year_match else ''
            
            # 備註
            remark_match = re.search(r'<span class="pic-text">([^<]+)</span>', r.text)
            remark = self.clean_text(remark_match.group(1)) if remark_match else ''
            
            # ===== 處理播放線路 =====
            play_urls = []
            play_from = []
            
            source_pattern = r'<div id="playlist(\d+)"[^>]*>.*?<ul[^>]+class="[^"]*playlink[^"]*"[^>]*>(.*?)</ul>'
            source_matches = re.findall(source_pattern, r.text, re.S)
            
            source_names = {
                '1': '新浪',
                '2': '金鷹',
                '3': '光速',
                '4': '紅牛'
            }
            
            for source_id, source_content in source_matches:
                source_name = source_names.get(source_id, f"線路{source_id}")
                
                links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', source_content, re.S)
                
                episode_urls = []
                for href, title_link in links:
                    if 'heji.html' in href or 'APP播放' in title_link or 'APP' in title_link:
                        continue
                    
                    if '/play/' in href:
                        full_url = self.host + href if href.startswith('/') else href
                        clean_title = self.clean_text(title_link)
                        episode_urls.append(f'{clean_title}${full_url}')
                
                if episode_urls:
                    play_from.append(source_name)
                    play_urls.append('#'.join(episode_urls))
            
            vod_info = {
                'vod_id': vid,
                'vod_name': title,
                'vod_pic': img,
                'vod_content': description,
                'vod_actor': actor,
                'vod_director': director,
                'vod_area': area,
                'vod_lang': '',
                'vod_year': year,
                'vod_remarks': remark,
                'vod_play_from': '$$$'.join(play_from) if play_from else 'm3u8',
                'vod_play_url': '$$$'.join(play_urls) if play_urls else ''
            }
            
            print(f"詳情解析成功: {vod_info['vod_name']}")
            return {'list': [vod_info]}
            
        except Exception as e:
            print(f"detailContent error: {e}")
            import traceback
            traceback.print_exc()
            return {'list': []}
    
    def searchContent(self, keyword, pg):
        print(f"搜索功能已禁用: {keyword}")
        return {'list': []}
    
    def playerContent(self, flag, id, vipFlags):
        try:
            if id.startswith('/play/'):
                url = f'{self.host}{id}'
            elif id.startswith('http'):
                url = id
            else:
                url = f'{self.host}/play/{id}'
            
            if 'heji.html' in url:
                return {'parse': 0, 'playUrl': '', 'url': ''}
            
            headers = self.headers.copy()
            headers['Referer'] = self.host
            
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = 'utf-8'
            
            m3u8_url = None
            
            pattern1 = r'(https?://cdn\.yddsha2\.com[^"\']+\.m3u8[^"\']*)'
            match1 = re.search(pattern1, r.text)
            if match1:
                m3u8_url = match1.group(1)
            
            if not m3u8_url:
                pattern2 = r'(https?://[^"\']+\.m3u8[^"\']*)'
                match2 = re.search(pattern2, r.text)
                if match2:
                    m3u8_url = match2.group(1)
            
            if not m3u8_url:
                pattern3 = r'<iframe[^>]+src="[^"]*\?[^,]+,[^,]+,([^",]+)"'
                match3 = re.search(pattern3, r.text)
                if match3:
                    m3u8_url = match3.group(1).strip()
            
            if m3u8_url:
                m3u8_url = m3u8_url.rstrip(',')
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