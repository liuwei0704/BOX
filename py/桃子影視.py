# coding=utf-8
import sys
import os
import re
import json
import urllib.parse
import base64
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    def getName(self):
        return "桃子影视"
    
    def init(self, extend=""):
        # 使用正確的域名
        self.host = "https://www.taozi008.com"
        print(f"桃子影視爬蟲初始化: {self.host}")
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
    
    def homeContent(self, filter):
        """返回分類列表"""
        result = {}
        classes = [
            {"type_name": "電影", "type_id": "229"},
            {"type_name": "電視劇", "type_id": "230"},
            {"type_name": "綜藝", "type_id": "231"},
            {"type_name": "動漫", "type_id": "232"}
        ]
        result["class"] = classes
        result["filters"] = self._get_filters()
        return result
    
    def _get_filters(self):
        """返回篩選條件（可選）"""
        return {}
    
    def homeVideoContent(self):
        """首頁推薦視頻 - 直接返回空"""
        return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分類頁面內容"""
        try:
            # 構建分類URL
            url = f"{self.host}/vod/index.html?type_id={tid}"
            
            # 添加分頁
            if int(pg) > 1:
                url += f"&page={pg}"
            
            print(f"正在抓取分類頁面: tid={tid}, page={pg}, url={url}")
            rsp = self.fetch(url, headers=self.header())
            
            if rsp.status_code != 200:
                print(f"請求失敗，狀態碼: {rsp.status_code}")
                return self._get_empty_data(pg)
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 查找視頻列表項
            items = root.select('.lists-content ul li')
            
            if not items:
                items = root.select('.lists.lists-thumb-top .lists-content ul li')
            
            if not items:
                print("未找到視頻列表")
                return self._get_empty_data(pg)
            
            for item in items[:20]:
                try:
                    a = item.find('a', class_='thumbnail')
                    if not a:
                        a = item.find('a', href=True)
                    if not a:
                        continue
                    
                    href = a.get('href', '')
                    if not href:
                        continue
                    
                    vod_id = self.host + href if href.startswith('/') else href
                    
                    # 獲取標題
                    vod_name = ""
                    h2 = item.find('h2')
                    if h2:
                        vod_name = h2.text.strip()
                    if not vod_name:
                        vod_name = a.get('title', '').strip()
                    if not vod_name:
                        vod_name = a.text.strip()
                    
                    # 獲取封面
                    vod_pic = ""
                    img = a.find('img')
                    if img and img.get('src'):
                        vod_pic = img['src']
                        if vod_pic.startswith('//'):
                            vod_pic = 'https:' + vod_pic
                        elif vod_pic.startswith('/'):
                            vod_pic = self.host + vod_pic
                    
                    # 獲取備註
                    vod_remarks = []
                    note_elem = a.find(class_='note')
                    if note_elem:
                        vod_remarks.append(note_elem.text.strip())
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": " | ".join(vod_remarks) if vod_remarks else ""
                    })
                    
                except Exception as e:
                    continue
            
            # 獲取總頁數
            pagecount = int(pg)
            pagination = root.find('ul', class_='myci-page')
            if pagination:
                last_page = pagination.find('a', string='尾頁')
                if last_page:
                    href = last_page.get('href', '')
                    if href:
                        match = re.search(r'page=(\d+)', href)
                        if match:
                            pagecount = int(match.group(1))
            
            print(f"成功抓取 {len(videos)} 個視頻，當前頁: {pg}, 總頁數: {pagecount}")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": max(pagecount, int(pg)),
                "limit": 20,
                "total": len(videos) * max(pagecount, 1)
            }
            
        except Exception as e:
            print(f"分類頁面抓取出錯: {str(e)}")
            return self._get_empty_data(pg)
    
    def _get_empty_data(self, pg):
        """返回空數據"""
        return {
            "list": [],
            "page": int(pg),
            "pagecount": int(pg),
            "limit": 20,
            "total": 0
        }
    
    def detailContent(self, ids):
        """視頻詳情頁"""
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                url = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
            else:
                url = vod_id
            
            print(f"正在獲取詳情頁: {url}")
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 獲取標題
            vod_name = "未知"
            title_elem = root.find('h1', class_='product-title')
            if not title_elem:
                title_elem = root.find('h1')
            if title_elem:
                vod_name = title_elem.text.strip()
            
            # 獲取封面
            vod_pic = ""
            img_selectors = ['img.thumb', '.thumbnail img', 'img.cover']
            for selector in img_selectors:
                img_elem = root.select_one(selector)
                if img_elem and img_elem.get('src'):
                    vod_pic = img_elem['src']
                    break
            
            if vod_pic:
                if vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
                elif vod_pic.startswith('/'):
                    vod_pic = self.host + vod_pic
            
            # 獲取年份
            vod_year = ""
            year_match = re.search(r'\((\d{4})\)', vod_name)
            if year_match:
                vod_year = year_match.group(1)
            
            # 獲取導演、演員、地區、簡介
            vod_director = ""
            vod_actor = ""
            vod_area = ""
            vod_content = ""
            
            # 從 product-excerpt 中提取信息
            excerpts = root.find_all('div', class_='product-excerpt')
            for excerpt in excerpts:
                text = excerpt.get_text(strip=True)
                if '導演：' in text:
                    vod_director = text.replace('導演：', '').strip()
                elif '主演：' in text:
                    vod_actor = text.replace('主演：', '').strip()
                elif '製片國家/地區：' in text:
                    vod_area = text.replace('製片國家/地區：', '').strip()
                elif '劇情簡介' in text:
                    span = excerpt.find('span')
                    if span:
                        vod_content = span.get_text(strip=True)
            
            # 如果沒找到簡介，嘗試從 meta 獲取
            if not vod_content:
                meta_desc = root.find('meta', {'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    vod_content = meta_desc['content']
            
            # 解析播放列表
            episodes = []
            
            # 查找劇集列表
            episode_containers = root.select('.playEpisodes ul, #playlist ul, .episode-list ul')
            for container in episode_containers:
                links = container.find_all('a', href=True)
                for link in links:
                    episode_name = link.text.strip()
                    episode_url = link.get('href', '')
                    if episode_url and episode_name:
                        if not episode_url.startswith('http'):
                            episode_url = self.host + episode_url if episode_url.startswith('/') else episode_url
                        episodes.append(f"{episode_name}${episode_url}")
            
            # 如果沒解析到劇集，使用詳情頁鏈接
            if not episodes:
                episodes.append(f"第1集${url}")
            
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": vod_year,
                "vod_actor": vod_actor,
                "vod_director": vod_director,
                "vod_area": vod_area,
                "vod_play_from": "線路1",
                "vod_play_url": "#".join(episodes)
            }
            
            print(f"詳情頁解析完成: {vod_name}, 共{len(episodes)}集")
            return {"list": [video]}
            
        except Exception as e:
            print(f"詳情頁獲取失敗: {str(e)}")
            video = {
                "vod_id": ids[0],
                "vod_name": "視頻詳情",
                "vod_pic": "",
                "vod_content": "詳情加載中...",
                "vod_play_from": "默認",
                "vod_play_url": f"第1集${ids[0]}"
            }
            return {"list": [video]}
    
    def searchContent(self, key, quick, pg=1):
        """搜索功能 - 完全修復版本"""
        try:
            encoded_key = urllib.parse.quote(key)
            
            # ✅ 修正：直接使用標準搜索頁面，不使用 Ajax 接口
            url = f"{self.host}/search/index.html?keyword={encoded_key}"
            
            if int(pg) > 1:
                url += f"&page={pg}"
            
            print(f"搜索 URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            
            if rsp.status_code != 200:
                print(f"搜索請求失敗，狀態碼: {rsp.status_code}")
                return {"list": []}
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # ✅ 檢查是否有搜索結果
            no_result = root.find('p', string=re.compile('未搜索到相關內容|沒有找到'))
            if no_result:
                print(f"未搜索到相關內容: {key}")
                return {"list": []}
            
            # ✅ 精準定位搜索結果列表
            items = root.select('.lists-content ul li')
            
            if not items:
                # 備用選擇器
                items = root.select('.lists ul li')
            
            print(f"找到 {len(items)} 個搜索結果項")
            
            for item in items:
                try:
                    # 查找鏈接
                    a = None
                    for selector in ['a.thumbnail', 'a', '.thumbnail a']:
                        a = item.select_one(selector)
                        if a:
                            break
                    
                    if not a:
                        a = item.find('a', href=True)
                    
                    if not a:
                        continue
                    
                    href = a.get('href', '')
                    if not href or href == '#':
                        continue
                    
                    # 處理視頻ID
                    vod_id = self.host + href if href.startswith('/') else href
                    
                    # 獲取標題 - 多種方式
                    vod_name = ""
                    
                    # 1. 從 h2 獲取
                    h2 = item.find('h2')
                    if h2:
                        vod_name = h2.text.strip()
                    
                    # 2. 從 title 屬性
                    if not vod_name:
                        vod_name = a.get('title', '').strip()
                    
                    # 3. 從文本
                    if not vod_name:
                        vod_name = a.text.strip()
                    
                    # 4. 從 alt 屬性
                    if not vod_name:
                        img = a.find('img')
                        if img and img.get('alt'):
                            vod_name = img['alt'].strip()
                    
                    if not vod_name:
                        continue
                    
                    # 清理標題
                    vod_name = re.sub(r'\s+', ' ', vod_name).strip()
                    
                    # 獲取封面
                    vod_pic = ""
                    img = a.find('img')
                    if img and img.get('src'):
                        vod_pic = img['src']
                        if vod_pic.startswith('//'):
                            vod_pic = 'https:' + vod_pic
                        elif vod_pic.startswith('/'):
                            vod_pic = self.host + vod_pic
                    
                    # 獲取備註
                    vod_remarks = ""
                    note_elem = a.find(class_='note')
                    if note_elem:
                        vod_remarks = note_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                    
                except Exception as e:
                    print(f"解析搜索結果項時出錯: {str(e)}")
                    continue
            
            print(f"搜索到 {len(videos)} 個結果")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": 1,  # 簡化處理，只返回第一頁
                "limit": 20,
                "total": len(videos)
            }
            
        except Exception as e:
            print(f"搜索失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"list": []}
    
    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        try:
            print(f"正在解析播放地址: {id}")
            
            rsp = self.fetch(id, headers=self.header())
            html_content = rsp.text
            
            m3u8_url = ""
            
            # 方法1：查找 base64 編碼的 m3u8
            base64_patterns = [
                r'"file":"([A-Za-z0-9+/=]{50,})"',
                r'file["\']?\s*:\s*["\']([A-Za-z0-9+/=]{50,})["\']',
                r'url["\']?\s*:\s*["\']([A-Za-z0-9+/=]{50,})["\']',
                r'src["\']?\s*:\s*["\']([A-Za-z0-9+/=]{50,})["\']'
            ]
            
            for pattern in base64_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    try:
                        # 處理特殊前綴
                        if len(match) > 3 and match[:3] in ['KhY', 'XPQ', 'd4g', 'yYQ', 'frX', '7eR', 'U0j', '898', 'oLX', 'jwR']:
                            encrypted = match[3:]
                        else:
                            encrypted = match
                        
                        # base64 解碼
                        decoded_bytes = base64.b64decode(encrypted)
                        decoded_str = decoded_bytes.decode('utf-8')
                        
                        # URL 解碼
                        m3u8_url = urllib.parse.unquote(decoded_str)
                        
                        if 'm3u8' in m3u8_url.lower() and m3u8_url.startswith('http'):
                            print(f"成功解析 m3u8 地址")
                            break
                    except:
                        continue
                if m3u8_url:
                    break
            
            # 方法2：直接查找 m3u8 鏈接
            if not m3u8_url:
                m3u8_pattern = r'https?://[^\s"\']+\.m3u8[^\s"\']*'
                m3u8_matches = re.findall(m3u8_pattern, html_content, re.IGNORECASE)
                if m3u8_matches:
                    m3u8_url = m3u8_matches[0]
                    print(f"直接找到 m3u8 地址")
            
            if m3u8_url:
                # 清理 URL
                m3u8_url = m3u8_url.strip()
                m3u8_url = m3u8_url.strip('"\'')
                
                if m3u8_url.startswith('//'):
                    m3u8_url = 'https:' + m3u8_url
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': id,
                    'Origin': 'https://www.taozi008.com'
                }
                
                return {
                    "parse": 0,
                    "url": m3u8_url,
                    "header": json.dumps(headers)
                }
            else:
                print("未找到 m3u8 地址，返回原始鏈接")
                headers = self.header()
                headers['Referer'] = id
                
                return {
                    "parse": 1,
                    "url": id,
                    "header": json.dumps(headers)
                }
                
        except Exception as e:
            print(f"播放地址解析失敗: {str(e)}")
            headers = self.header()
            headers['Referer'] = id
            
            return {
                "parse": 1,
                "url": id,
                "header": json.dumps(headers)
            }
    
    def isVideoFormat(self, url):
        """判斷是否為視頻格式"""
        video_formats = ['.m3u8', '.mp4', '.avi', '.mkv', '.flv', '.ts', '.webm']
        return any(fmt in url.lower() for fmt in video_formats)
    
    def localProxy(self, params):
        """本地代理"""
        return [200, "video/MP2T", ""]