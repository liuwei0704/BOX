# -*- coding: utf-8 -*-
import re
import sys
import json
import base64
import urllib.parse
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):

    def init(self, extend=""):
        pass

    def getName(self):
        return "奴娜TV"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    # ------------------------- 網站配置 -------------------------
    host = 'https://www.nntv.in'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'https://www.nntv.in',
    }

    # ------------------------- 通用工具方法 -------------------------
    def _normalize_url(self, url):
        """標準化URL：處理相對路徑、協議缺失等"""
        if not url:
            return url
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{self.host}{url}"
        return url

    def _extract_video_basic(self, item):
        """從列表項提取視頻基本信息 - 適配奴娜TV搜索結果"""
        try:
            # 提取鏈接
            link = self._normalize_url(item('a.public-list-exp').attr('href') or item('a').attr('href'))
            if not link:
                return None

            # 提取標題 - 搜索結果頁使用 .time-title
            title = item('.time-title').text().strip()
            if not title:
                title = item('a.public-list-exp').attr('title') or '未知標題'
            
            # 提取海報 - 優先取data-src懶加載
            img = ''
            img_elem = item('img.lazy')
            if img_elem:
                img = self._normalize_url(img_elem.attr('data-src') or img_elem.attr('src'))
            
            # 提取備註/更新信息
            remarks = item('.public-list-prb').text().strip()
            
            # 提取評分
            score = item('.public-prt').text().strip()

            return {
                'vod_id': link,
                'vod_name': title,
                'vod_pic': img or '',
                'vod_remarks': remarks,
                'vod_year': '',
                'vod_score': score
            }
        except Exception as e:
            return None

    def getpq(self, text):
        """創建PyQuery對象"""
        try:
            return pq(text)
        except:
            try:
                return pq(text.encode('utf-8'))
            except:
                return pq('')

    # ------------------------- 首頁 -------------------------
    def homeContent(self, filter):
        """首頁：分類 + 推薦列表"""
        try:
            data = self.getpq(self.fetch(self.host, headers=self.headers).text)
            classes = []
            
            nav_items = data('.head-nav ul li, .this-wap ul li')
            for item in nav_items.items():
                a_tag = item('a')
                link = a_tag.attr('href')
                name = a_tag.text().strip()
                if link and name and name not in ['推薦', '更多', '我的', '客戶端', '观看记录']:
                    if '/vod/type/id/' in link or '/vod/show/' in link:
                        classes.append({'type_name': name, 'type_id': link})
            
            # 去重
            unique_classes = []
            seen = set()
            for c in classes:
                if c['type_id'] not in seen:
                    seen.add(c['type_id'])
                    unique_classes.append(c)
            
            recommend_list = self._get_home_recommend_list(data)
            
            return {'class': unique_classes, 'list': recommend_list}
        except Exception as e:
            return {'class': [], 'list': []}

    def _get_home_recommend_list(self, data):
        """首頁推薦列表"""
        videos = []
        seen_ids = set()
        
        slide_items = data('.slide-time-bj')
        for item in slide_items.items():
            video_info = self._extract_slide_video(item)
            if video_info and video_info['vod_id'] not in seen_ids:
                seen_ids.add(video_info['vod_id'])
                videos.append(video_info)
        
        hot_items = data('.public-list-box.public-pic-b')
        for item in hot_items.items():
            video_info = self._extract_video_basic(item)
            if video_info and video_info['vod_id'] not in seen_ids:
                seen_ids.add(video_info['vod_id'])
                videos.append(video_info)
        
        return videos[:24]

    def _extract_slide_video(self, item):
        """提取輪播區視頻"""
        try:
            link = self._normalize_url(item('a').attr('href'))
            title = item('.this-desc-title').text().strip()
            img = item('.slide-time-img3').attr('style')
            if img:
                match = re.search(r"url\('?([^'\)]+)'?\)", img)
                if match:
                    img = self._normalize_url(match.group(1))
            remarks = item('.this-desc-info span:last-child').text().strip()
            year = item('.this-desc-info span:nth-child(2)').text().strip()
            area = item('.this-desc-info span:nth-child(3)').text().strip()
            score = item('.this-desc-score').text().strip().replace('', '')
            
            return {
                'vod_id': link,
                'vod_name': title,
                'vod_pic': img or '',
                'vod_remarks': remarks,
                'vod_year': year,
                'vod_area': area,
                'vod_score': score
            }
        except:
            return None

    # ------------------------- 分類頁 -------------------------
    def categoryContent(self, tid, pg, filter, extend):
        """分類頁內容"""
        try:
            if tid.startswith('http'):
                base_url = tid
            elif tid.startswith('/'):
                base_url = f"{self.host}{tid}"
            else:
                base_url = tid

            if pg == '1':
                url = base_url
            else:
                if base_url.endswith('.html'):
                    url = base_url.replace('.html', f'/page/{pg}.html')
                elif '/page/' in base_url:
                    url = re.sub(r'/page/\d+\.html', f'/page/{pg}.html', base_url)
                else:
                    url = f"{base_url}/page/{pg}.html" if base_url.endswith('/') else f"{base_url}/page/{pg}.html"
            
            data = self.getpq(self.fetch(url, headers=self.headers).text)
            videos = self._get_category_video_list(data)
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': 9999,
                'limit': 30,
                'total': 999999
            }
        except Exception as e:
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}

    def _get_category_video_list(self, data):
        """提取分類列表頁視頻"""
        videos = []
        items = data('.public-list-box.public-pic-b')
        for item in items.items():
            video_info = self._extract_video_basic(item)
            if video_info:
                videos.append(video_info)
        return videos

    # ------------------------- 詳情頁 -------------------------
    def detailContent(self, ids):
        """詳情頁：提取視頻詳情、播放列表"""
        try:
            first_id = next(iter(ids)) if hasattr(ids, '__iter__') and not isinstance(ids, str) else ids
            url = self._normalize_url(first_id)
            data = self.getpq(self.fetch(url, headers=self.headers).text)
            
            # 標題
            vod_name = data('.this-desc-title').text().strip()
            if not vod_name:
                vod_name = data('h1').text().strip() or data('.title-h1').text().strip()
            
            # 海報
            vod_pic = ''
            bg_style = data('.this-pic-bj').attr('style')
            if bg_style:
                match = re.search(r"url\('?([^'\)]+)'?\)", bg_style)
                if match:
                    vod_pic = self._normalize_url(match.group(1))
            
            # 簡介
            vod_content = data('.this-desc .text').text().strip()
            if not vod_content:
                vod_content = data('.this-desc').text().replace('描述:', '').strip()
            
            # 詳細信息
            vod_year = ''
            vod_area = ''
            vod_remarks = ''
            vod_actor = ''
            vod_director = ''
            
            info_spans = data('.this-desc-info span')
            for i, span in enumerate(info_spans.items()):
                text = span.text().strip()
                if i == 1:
                    vod_year = text
                elif i == 2:
                    vod_area = text
                elif i == 3:
                    vod_remarks = text
            
            director_text = data('.this-info:contains("导演")').text()
            if director_text:
                vod_director = director_text.replace('导演:', '').replace('，', ' ').strip()
            
            actor_text = data('.this-info:contains("演员")').text()
            if actor_text:
                vod_actor = actor_text.replace('演员:', '').replace('，', ' ').strip()
            
            vod = {
                'vod_id': first_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_content': vod_content,
                'vod_year': vod_year,
                'vod_area': vod_area,
                'vod_remarks': vod_remarks,
                'vod_actor': vod_actor,
                'vod_director': vod_director
            }
            
            # 提取播放列表
            play_links = self._extract_play_urls(data)
            
            if play_links:
                source_names = []
                source_tabs = data('.anthology-tab a')
                for tab in source_tabs.items():
                    name = tab.text().strip()
                    if name:
                        name = re.sub(r'[]', '', name).strip()
                        source_names.append(name)
                
                if len(source_names) > 1:
                    vod['vod_play_from'] = '$$$'.join(source_names)
                    all_links = []
                    for i, links in enumerate(play_links):
                        if i > 0:
                            all_links.append('$$$')
                        all_links.append('#'.join(links))
                    vod['vod_play_url'] = ''.join(all_links)
                else:
                    vod['vod_play_from'] = source_names[0] if source_names else '奴娜線路'
                    vod['vod_play_url'] = '#'.join(play_links[0] if play_links else [])
            else:
                vod['vod_play_from'] = '播放地址'
                vod['vod_play_url'] = f'播放${first_id}'
            
            return {'list': [vod]}
        except Exception as e:
            return {'list': []}

    def _extract_play_urls(self, data):
        """提取播放鏈接"""
        play_lists = []
        
        source_boxes = data('.anthology-list-box')
        for box in source_boxes.items():
            episodes = []
            ep_links = box('li a')
            for link in ep_links.items():
                title = link.text().strip()
                url = self._normalize_url(link.attr('href'))
                if url and title:
                    episodes.append(f"{title}${url}")
            if episodes:
                play_lists.append(episodes)
        
        if not play_lists:
            all_links = data('.anthology-list-play li a')
            if all_links:
                episodes = []
                for link in all_links.items():
                    title = link.text().strip()
                    url = self._normalize_url(link.attr('href'))
                    if url and title:
                        episodes.append(f"{title}${url}")
                if episodes:
                    play_lists.append(episodes)
        
        return play_lists

    # ------------------------- 搜索功能（已修復）-------------------------
    def searchContent(self, key, quick, pg="1"):
        """搜索功能 - 適配奴娜TV搜索結果頁"""
        try:
            # 正確的搜索URL格式
            search_url = f"{self.host}/index.php/vod/search.html?wd={urllib.parse.quote(key)}"
            
            # 處理分頁：搜索頁分頁格式為 /index.php/vod/search/page/2/wd/關鍵字.html
            if pg != "1":
                search_url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{urllib.parse.quote(key)}.html"
            
            print(f"搜索URL: {search_url}")  # 調試用
            
            data = self.getpq(self.fetch(search_url, headers=self.headers).text)
            
            # 提取搜索結果列表 - 搜索結果頁使用 .public-list-box.public-pic-b
            results = []
            items = data('.public-list-box.public-pic-b')
            
            for item in items.items():
                video_info = self._extract_video_basic(item)
                if video_info:
                    # 不需要額外過濾，因為搜索結果已經是匹配的
                    results.append(video_info)
            
            # 獲取總頁數（從分頁器提取）
            pagecount = 1
            page_links = data('.pages .page-link')
            for link in page_links.items():
                text = link.text().strip()
                if text.isdigit():
                    page_num = int(text)
                    if page_num > pagecount:
                        pagecount = page_num
            
            return {
                'list': results,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 24,
                'total': pagecount * 24
            }
        except Exception as e:
            print(f"搜索錯誤: {str(e)}")
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 24, 'total': 0}

    # ------------------------- 播放解析 -------------------------
    def playerContent(self, flag, id, vipFlags):
        """解析播放地址 - 適配奴娜TV加密播放器"""
        try:
            url = self._normalize_url(id)
            data = self.getpq(self.fetch(url, headers=self.headers).text)
            
            # 方法1: 從 player_aaaa 變量提取加密URL
            scripts = data('script').text()
            
            player_match = re.search(r'var player_aaaa\s*=\s*({.*?});', scripts, re.DOTALL)
            if player_match:
                try:
                    player_json = player_match.group(1)
                    player_json = re.sub(r'(\w+):', r'"\1":', player_json)
                    player_json = player_json.replace("'", '"')
                    player_data = json.loads(player_json)
                    
                    encrypted_url = player_data.get('url', '')
                    if encrypted_url:
                        decrypted_url = self._decrypt_url(encrypted_url)
                        if decrypted_url:
                            return {'parse': 0, 'url': decrypted_url, 'header': self.headers}
                    
                    url_next = player_data.get('url_next', '')
                    if url_next and not encrypted_url:
                        decrypted_next = self._decrypt_url(url_next)
                        if decrypted_next:
                            return {'parse': 0, 'url': decrypted_next, 'header': self.headers}
                except:
                    pass
            
            # 方法2: 提取iframe嵌入地址
            iframe = data('iframe#playIframe, .play-content iframe, iframe[src*="m3u8"], iframe[src*="mp4"]').attr('src')
            if iframe:
                return {'parse': 1, 'url': self._normalize_url(iframe), 'header': self.headers}
            
            # 方法3: 提取video標籤
            video_src = data('video source').attr('src')
            if video_src:
                return {'parse': 0, 'url': self._normalize_url(video_src), 'header': self.headers}
            
            # 方法4: 提取其他JS變量中的URL
            m3u8_match = re.search(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', scripts)
            if m3u8_match:
                return {'parse': 0, 'url': m3u8_match.group(1), 'header': self.headers}
            
            mp4_match = re.search(r'(https?://[^"\'\s]+\.mp4[^"\'\s]*)', scripts)
            if mp4_match:
                return {'parse': 0, 'url': mp4_match.group(1), 'header': self.headers}
            
            return {'parse': 1, 'url': url, 'header': self.headers}
        except Exception as e:
            return {'parse': 1, 'url': id, 'header': self.headers}

    def _decrypt_url(self, encrypted_str):
        """解密奴娜TV的加密URL"""
        try:
            decoded = urllib.parse.unquote(encrypted_str)
            
            try:
                padding = 4 - (len(decoded) % 4)
                if padding != 4:
                    decoded += '=' * padding
                
                decoded_bytes = base64.b64decode(decoded)
                decoded_str = decoded_bytes.decode('utf-8')
                
                url_match = re.search(r'(https?://[^\s]+)', decoded_str)
                if url_match:
                    return url_match.group(1)
                
                return decoded_str
            except:
                return decoded
        except:
            return None

    def _legacy_decrypt(self, encrypted_str):
        """備用解密方法"""
        try:
            if encrypted_str.startswith('oZGqtPGOeRyJ') or encrypted_str.startswith('pMGutabcfh6J'):
                real_encrypted = encrypted_str[16:]
                return self._decrypt_url(real_encrypted)
            return self._decrypt_url(encrypted_str)
        except:
            return None

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        pass