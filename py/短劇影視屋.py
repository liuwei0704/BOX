# -*- coding: utf-8 -*-
import re
import sys
import json
from urllib.parse import quote

sys.path.append('..')
from base.spider import Spider
from pyquery import PyQuery as pq


class Spider(Spider):
    
    def init(self, extend=""):
        pass
    
    def getName(self):
        return "短剧影视屋"
    
    def isVideoFormat(self, url):
        pass
    
    def manualVideoCheck(self):
        pass
    
    def destroy(self):
        pass
    
    # ------------------------- 網站配置 -------------------------
    host = 'https://www.djys.tv'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G9910) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.djys.tv/',
        'Connection': 'keep-alive',
    }
    
    # ------------------------- 通用工具方法 -------------------------
    def _normalize_url(self, url):
        """標準化 URL：處理相對路徑、協議缺失等"""
        if not url or not isinstance(url, str):
            return ''
        if 'javascript:' in url:
            return ''
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{self.host}{url}"
        return url
    
    def getpq(self, text):
        """創建 PyQuery 對象，處理編碼問題"""
        try:
            return pq(text)
        except:
            try:
                return pq(text.encode('utf-8'))
            except:
                return pq('')
    
    def _extract_video_item(self, item):
        """從 li 元素提取視頻信息 - 通用方法"""
        try:
            # 1. 提取鏈接
            link_tag = item('a.hl-item-thumb, a[href*="/vod/detail/"], a:has(.hl-item-thumb)')
            href = link_tag.attr('href')
            if not href:
                href = item('a').attr('href')
            if not href or 'javascript:' in href:
                return None
            
            vod_id = self._normalize_url(href)
            if not vod_id:
                return None
            
            # 2. 提取標題
            title = (link_tag.attr('title') or 
                    item('.hl-item-title a').text().strip() or 
                    item('a[title]').attr('title') or
                    item('img').attr('alt') or 
                    '未知片名')
            
            # 3. 提取圖片
            img = (item('.hl-item-thumb').attr('data-original') or 
                  item('img').attr('data-original') or
                  item('.hl-item-thumb').attr('src') or 
                  item('img').attr('src') or 
                  '')
            vod_pic = self._normalize_url(img)
            
            # 4. 提取備註/更新狀態
            remarks = (item('.remarks').text().strip() or 
                      item('.hl-pic-text').text().strip() or 
                      '')
            
            # 5. 提取年份/評分
            year = ''
            score = ''
            sub_text = item('.hl-item-sub').text().strip()
            if sub_text:
                year_match = re.search(r'(\d{4})', sub_text)
                if year_match:
                    year = year_match.group(1)
                score_match = re.search(r'(\d+\.\d+)', sub_text)
                if score_match:
                    score = score_match.group(1)
            
            return {
                'vod_id': vod_id,
                'vod_name': title,
                'vod_pic': vod_pic,
                'vod_remarks': remarks,
                'vod_year': year,
                'vod_score': score
            }
        except Exception as e:
            return None
    
    # ------------------------- 首頁 -------------------------
    def homeContent(self, filter):
        """首頁：分類 + 推薦列表"""
        try:
            print(f"🔗 請求首頁: {self.host}")
            html_text = self.fetch(self.host, headers=self.headers).text
            print(f"📄 返回長度: {len(html_text)}")
            
            data = self.getpq(html_text)
            classes = []
            
            # ============= 分類提取 =============
            nav_items = data('.hl-nav li a[href*="/vod/type/id/"]')
            for item in nav_items.items():
                href = item.attr('href')
                name = item.text().strip()
                if href and name and name not in ['首頁', 'APP下載', '留言', '最新', '排行']:
                    classes.append({
                        'type_name': name,
                        'type_id': self._normalize_url(href)
                    })
            
            if len(classes) < 5:
                menu_items = data('.hl-menus li a[href*="/vod/type/id/"]')
                for item in menu_items.items():
                    href = item.attr('href')
                    name = item('span').text().strip() or item.text().strip()
                    if href and name and name not in ['首頁']:
                        exists = any(c['type_name'] == name for c in classes)
                        if not exists:
                            classes.append({
                                'type_name': name,
                                'type_id': self._normalize_url(href)
                            })
            
            # ============= 推薦列表 =============
            videos = []
            
            hot_items = data('.hl-rb-vod:first .hl-vod-list .hl-list-item')
            for item in hot_items.items():
                video = self._extract_video_item(item)
                if video:
                    videos.append(video)
            
            section_items = data('.hl-rb-vod:not(:first) .hl-vod-list .hl-list-item')
            for item in section_items.items():
                if len(videos) >= 30:
                    break
                video = self._extract_video_item(item)
                if video and video not in videos:
                    videos.append(video)
            
            print(f"✅ 分類: {len(classes)} 個, 視頻: {len(videos)} 個")
            return {'class': classes, 'list': videos}
            
        except Exception as e:
            print(f"❌ 首頁錯誤: {str(e)}")
            return {'class': [], 'list': []}
    
    # ------------------------- 分類頁 -------------------------
    def categoryContent(self, tid, pg, filter, extend):
        """分類頁內容"""
        try:
            if pg == '1' or pg == 1:
                url = tid
            else:
                if '/page/' not in tid:
                    base_url = tid.replace('.html', '')
                    url = f"{base_url}/page/{pg}.html"
                else:
                    url = re.sub(r'/page/\d+\.html', f'/page/{pg}.html', tid)
            
            print(f"🔗 分類請求: {url}")
            html_text = self.fetch(url, headers=self.headers).text
            data = self.getpq(html_text)
            
            videos = []
            items = data('.hl-vod-list .hl-list-item, .hl-wide-list .hl-list-item')
            for item in items.items():
                video = self._extract_video_item(item)
                if video:
                    videos.append(video)
            
            total_page = 1
            
            page_links = data('.hl-page-wrap li a[href*="/page/"]')
            for link in page_links.items():
                href = link.attr('href')
                if href:
                    match = re.search(r'/page/(\d+)\.html', href)
                    if match:
                        page_num = int(match.group(1))
                        if page_num > total_page:
                            total_page = page_num
            
            if total_page == 1:
                page_text = data('.hl-page-tips').text()
                match = re.search(r'(\d+)\s*/\s*(\d+)', page_text)
                if match:
                    total_page = int(match.group(2))
            
            if total_page == 1:
                last_link = data('.hl-page-wrap li:last-child a[href*="/page/"]').attr('href')
                if last_link:
                    match = re.search(r'/page/(\d+)\.html', last_link)
                    if match:
                        total_page = int(match.group(1))
            
            print(f"📄 當前第 {pg} 頁, 共 {total_page} 頁, 獲取 {len(videos)} 個視頻")
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': total_page,
                'limit': len(videos),
                'total': total_page * 30
            }
            
        except Exception as e:
            print(f"❌ 分類頁錯誤: {str(e)}")
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}
    
    # ------------------------- 詳情頁 - 多線路完整版 -------------------------
    def detailContent(self, ids):
        """詳情頁：提取視頻詳情、多線路播放列表"""
        try:
            first_id = next(iter(ids)) if hasattr(ids, '__iter__') and not isinstance(ids, str) else ids
            url = self._normalize_url(first_id)
            
            print(f"🔗 詳情請求: {url}")
            html_text = self.fetch(url, headers=self.headers).text
            data = self.getpq(html_text)
            
            # ============= 基本信息提取 =============
            vod_name = (data('.hl-dc-title').text().strip() or 
                       data('h1').text().strip() or 
                       data('.hl-mob-name').text().strip() or 
                       data('title').text().split('_')[0].strip() or 
                       '未知片名')
            
            vod_pic = self._normalize_url(
                data('.hl-dc-pic .hl-item-thumb').attr('data-original') or 
                data('.hl-item-pic .hl-item-thumb').attr('data-original') or
                data('.hl-detail-content .hl-item-thumb').attr('data-original') or
                data('.hl-item-thumb').attr('data-original') or
                ''
            )
            
            vod_content = (data('.hl-content-text').text().strip() or 
                          data('.blurb').text().strip() or 
                          data('.hl-vod-inf-content').text().strip() or 
                          '暫無簡介')
            
            # ============= 詳細信息提取 =============
            vod_year = ''
            vod_area = ''
            vod_remarks = ''
            vod_actor = ''
            vod_director = ''
            
            info_items = data('.hl-full-box li, .hl-vod-data li, .hl-dc-content li, .hl-col-xs-12 li')
            for item in info_items.items():
                text = item.text().strip()
                if '狀態' in text or '状态' in text or '更新' in text:
                    vod_remarks = (text.split('：')[-1].strip() or 
                                  text.split(':')[-1].strip() or 
                                  text.split('】')[-1].strip())
                    if vod_remarks == '未知':
                        vod_remarks = ''
                elif '主演' in text:
                    vod_actor = (text.split('：')[-1].strip() or 
                                text.split(':')[-1].strip())
                    vod_actor = re.sub(r'<[^>]+>', '', vod_actor)  # 移除HTML標籤
                    vod_actor = re.sub(r'<i>/</i>', '/', vod_actor)  # 處理分隔符
                    if vod_actor == '未知':
                        vod_actor = ''
                elif '導演' in text or '导演' in text:
                    vod_director = (text.split('：')[-1].strip() or 
                                   text.split(':')[-1].strip())
                    if vod_director == '未知':
                        vod_director = ''
                elif '年份' in text:
                    year_match = re.search(r'(\d{4})', text)
                    if year_match:
                        vod_year = year_match.group(1)
                elif '地區' in text or '地区' in text:
                    vod_area = (text.split('：')[-1].strip() or 
                               text.split(':')[-1].strip())
                elif '语言' in text:
                    if not vod_area:
                        vod_area = (text.split('：')[-1].strip() or 
                                   text.split(':')[-1].strip())
            
            if not vod_remarks:
                vod_remarks = (data('.hl-text-conch').text().strip() or 
                              data('.remarks').text().strip() or 
                              '全集完结')
            
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
            
            # ============= 多線路播放列表提取 =============
            play_from_list = []  # 線路名稱列表
            play_url_list = []   # 對應的播放URL列表
            
            # 1. 從 .hl-play-source 提取多個線路
            source_wrap = data('.hl-play-source')
            
            if source_wrap:
                # 獲取所有線路標籤
                source_tabs = source_wrap('.hl-plays-from .hl-tabs-btn')
                
                for idx, tab in enumerate(source_tabs.items()):
                    # 線路名稱
                    source_name = tab.text().strip()
                    if not source_name:
                        source_name = f"線路{idx + 1}"
                    
                    # 清理名稱
                    source_name = source_name.replace('立即播放', '').replace('▶', '').strip()
                    
                    # 獲取對應的播放列表容器
                    tab_boxes = source_wrap('.hl-tabs-box')
                    if idx < len(tab_boxes):
                        box = tab_boxes.eq(idx)
                        
                        # 提取該線路的所有播放鏈接
                        play_links = []
                        play_items = box('li a[href*="/vod/play/"]')
                        
                        for item in play_items.items():
                            title = item.text().strip()
                            link = self._normalize_url(item.attr('href'))
                            
                            if link and title and 'javascript:' not in link:
                                if not any(skip in link for skip in ['#', 'javascript', 'void']):
                                    play_links.append(f"{title}${link}")
                        
                        # 如果該線路有播放鏈接，才加入
                        if play_links:
                            play_from_list.append(source_name)
                            play_url_list.append('#'.join(play_links))
            
            # 2. 如果上面的方法沒抓到，從 .hl-from-list 提取
            if not play_from_list:
                from_list = data('.hl-from-list li')
                from_urls = {}
                
                for item in from_list.items():
                    source_name = item('.hl-from-jsm3u8, .hl-from-wwm3u8, span').text().strip()
                    data_href = item.attr('data-href')
                    
                    if source_name and data_href:
                        from_urls[source_name] = self._normalize_url(data_href)
                
                # 為每個來源提取播放列表
                for source_name, play_page_url in from_urls.items():
                    # 這裡可以選擇是否要二次請求獲取完整播放列表
                    # 簡單處理：直接使用播放頁URL
                    play_links = [f"播放${play_page_url}"]
                    play_from_list.append(source_name)
                    play_url_list.append('#'.join(play_links))
            
            # 3. 從播放按鈕提取
            if not play_from_list:
                play_btn = data('.hl-play-btn, .hl-play-wb a[href*="/vod/play/"]')
                href = play_btn.attr('href')
                if href and 'javascript:' not in href:
                    play_from_list.append('默認線路')
                    play_url_list.append(f"播放${self._normalize_url(href)}")
            
            # 4. 最後回退
            if not play_from_list:
                play_from_list.append('默認線路')
                play_url_list.append(f"播放${first_id}")
            
            # 設置多線路
            vod['vod_play_from'] = '$$$'.join(play_from_list)
            vod['vod_play_url'] = '$$$'.join(play_url_list)
            
            print(f"✅ 詳情: {vod_name}")
            print(f"🎬 線路數: {len(play_from_list)} 個")
            for i, name in enumerate(play_from_list):
                link_count = play_url_list[i].count('#') + 1
                print(f"   - {name}: {link_count} 集")
            
            return {'list': [vod]}
            
        except Exception as e:
            print(f"❌ 詳情頁錯誤: {str(e)}")
            return {'list': []}
    
    # ------------------------- 搜索功能 -------------------------
    def searchContent(self, key, quick, pg="1"):
        """搜索功能"""
        try:
            encoded_key = quote(key)
            
            if pg == '1' or pg == 1:
                search_url = f"{self.host}/vod/search/wd/{encoded_key}.html"
            else:
                search_url = f"{self.host}/vod/search/page/{pg}/wd/{encoded_key}.html"
            
            print(f"🔍 搜索請求: {search_url}")
            html_text = self.fetch(search_url, headers=self.headers).text
            data = self.getpq(html_text)
            
            results = []
            items = data('.hl-one-list .hl-list-item')
            
            for item in items.items():
                video = self._extract_search_item(item)
                if video:
                    results.append(video)
            
            if not results:
                items = data('.hl-vod-list .hl-list-item, .hl-results li')
                for item in items.items():
                    video = self._extract_video_item(item)
                    if video:
                        results.append(video)
            
            total_page = 1
            
            page_links = data('.hl-page-wrap li a[href*="/page/"]')
            for link in page_links.items():
                href = link.attr('href')
                if href:
                    match = re.search(r'/page/(\d+)/', href)
                    if not match:
                        match = re.search(r'/page/(\d+)\.html', href)
                    if match:
                        page_num = int(match.group(1))
                        if page_num > total_page:
                            total_page = page_num
            
            if total_page == 1:
                page_text = data('.hl-page-total, .hl-page-tips').text()
                match = re.search(r'(\d+)\s*/\s*(\d+)', page_text)
                if match:
                    total_page = int(match.group(2))
            
            print(f"✅ 搜索到 {len(results)} 個結果, 共 {total_page} 頁")
            
            return {
                'list': results,
                'page': int(pg),
                'pagecount': total_page,
                'limit': len(results),
                'total': total_page * len(results) if results else 0
            }
            
        except Exception as e:
            print(f"❌ 搜索錯誤: {str(e)}")
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 20, 'total': 0}
    
    def _extract_search_item(self, item):
        """從搜索結果頁提取視頻信息"""
        try:
            link_tag = item('.hl-item-thumb, a[href*="/vod/detail/"]')
            href = link_tag.attr('href')
            if not href:
                href = item('a').attr('href')
            if not href or 'javascript:' in href:
                return None
            
            vod_id = self._normalize_url(href)
            
            title = (item('.hl-item-title a').text().strip() or 
                    link_tag.attr('title') or 
                    '未知片名')
            
            img = (item('.hl-item-thumb').attr('data-original') or 
                  item('img').attr('data-original') or
                  item('.hl-item-thumb').attr('src') or 
                  item('img').attr('src') or 
                  '')
            vod_pic = self._normalize_url(img)
            
            remarks = (item('.remarks').text().strip() or 
                      item('.hl-pic-text').text().strip() or 
                      '')
            
            year = ''
            score = ''
            actor = ''
            
            sub_items = item('.hl-item-sub')
            for sub in sub_items.items():
                text = sub.text().strip()
                score_match = re.search(r'(\d+\.\d+)', text)
                if score_match:
                    score = score_match.group(1)
                year_match = re.search(r'(\d{4})', text)
                if year_match:
                    year = year_match.group(1)
                if '/' in text and not score_match and not year_match:
                    actor = text
            
            description = item('.hl-lc-2').text().strip()
            
            return {
                'vod_id': vod_id,
                'vod_name': title,
                'vod_pic': vod_pic,
                'vod_remarks': remarks,
                'vod_year': year,
                'vod_score': score,
                'vod_actor': actor,
                'vod_content': description
            }
        except Exception as e:
            return None
    
    # ------------------------- 播放解析 -------------------------
    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        try:
            url = self._normalize_url(id)
            print(f"🎬 播放解析: {url}")
            
            if url and any(url.endswith(ext) for ext in ['.m3u8', '.mp4', '.flv', '.mkv']):
                print(f"✅ 直鏈視頻")
                return {
                    'parse': 0,
                    'url': url,
                    'header': self.headers
                }
            
            html_text = self.fetch(url, headers=self.headers).text
            data = self.getpq(html_text)
            
            iframe_src = (data('iframe#playiframe').attr('src') or 
                         data('.hl-iframe iframe').attr('src') or 
                         data('.player iframe').attr('src') or
                         data('iframe[src*=".m3u8"]').attr('src') or
                         data('iframe[src*=".mp4"]').attr('src'))
            
            if iframe_src:
                print(f"✅ 找到 iframe 播放器")
                return {
                    'parse': 1,
                    'url': self._normalize_url(iframe_src),
                    'header': self.headers
                }
            
            video_src = (data('video source').attr('src') or 
                        data('video').attr('src'))
            
            if video_src:
                print(f"✅ 找到直鏈視頻")
                return {
                    'parse': 0,
                    'url': self._normalize_url(video_src),
                    'header': self.headers
                }
            
            scripts = data('script').text()
            m3u8_patterns = [
                r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
                r'url["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                r'src["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']'
            ]
            
            for pattern in m3u8_patterns:
                m3u8_match = re.search(pattern, scripts)
                if m3u8_match:
                    print(f"✅ 從 JS 提取到 m3u8")
                    return {
                        'parse': 0,
                        'url': self._normalize_url(m3u8_match.group(1)),
                        'header': self.headers
                    }
            
            print(f"⚠️ 未找到播放地址，返回原 URL")
            return {
                'parse': 1,
                'url': url,
                'header': self.headers
            }
            
        except Exception as e:
            print(f"❌ 播放解析錯誤: {str(e)}")
            return {
                'parse': 1,
                'url': self._normalize_url(id),
                'header': self.headers
            }
    
    # ------------------------- 其他方法 -------------------------
    def localProxy(self, param):
        pass
    
    def liveContent(self, url):
        pass