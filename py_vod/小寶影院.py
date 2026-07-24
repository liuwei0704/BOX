# coding=utf-8
import sys
import os
import re
import json
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    def getName(self):
        return "小宝影院"
    
    def init(self, extend=""):
        self.host = "https://xiaoxintv.cc"
        print(f"Initialized with host: {self.host}")
    
    def getDependence(self):
        return ["bs4"]
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    def build_full_url(self, url):
        """將相對路徑補全為完整URL"""
        if not url or not isinstance(url, str):
            return ''
        
        url = url.strip()
        
        if url.startswith('http://') or url.startswith('https://'):
            return url
            
        if not url or url in ['小宝影院', 'null', 'undefined', '']:
            return ''
        
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        if url.startswith('./'):
            return self.host + url[1:]
        
        return self.host + '/' + url
    
    def homeContent(self, filter):
        """返回分類列表和首頁推薦"""
        result = {}
        classes = [
            {"type_id": "7", "type_name": "電影"},
            {"type_id": "6", "type_name": "電視劇"},
            {"type_id": "5", "type_name": "動漫"},
            {"type_id": "3", "type_name": "綜藝"},
            {"type_id": "21", "type_name": "紀錄片"},
            {"type_id": "64", "type_name": "短劇"},
        ]
        result["class"] = classes
        
        videos = []
        try:
            rsp = self.fetch(self.host, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            # 提取輪播圖推薦
            slide_items = soup.select('#home_slide .carousel-inner .item a')
            for item in slide_items:
                href = item.get('href', '')
                if href:
                    vod_id = self.build_full_url(href)
                    title = item.get('title', '')
                    img = item.find('img')
                    if img:
                        pic = img.get('src', '')
                        if not pic or pic == '':
                            pic = img.get('data-original', '')
                        pic = self.build_full_url(pic)
                    else:
                        pic = ''
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": "輪播推薦"
                    })
            
            # 提取大片推薦區域
            vod_items = soup.select('.myui-vodlist__box')
            for item in vod_items:
                link = item.find('a', class_='myui-vodlist__thumb')
                if link:
                    href = link.get('href', '')
                    if href:
                        vod_id = self.build_full_url(href)
                        title = link.get('title', '')
                        pic = link.get('data-original', '')
                        if not pic:
                            pic = link.get('src', '')
                        pic = self.build_full_url(pic)
                        
                        remark_span = item.find('span', class_='pic-text')
                        remark = remark_span.text.strip() if remark_span else ''
                        
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": title,
                            "vod_pic": pic,
                            "vod_remarks": remark
                        })
            
            seen = set()
            unique_videos = []
            for v in videos:
                if v['vod_id'] not in seen and v['vod_name']:
                    seen.add(v['vod_id'])
                    unique_videos.append(v)
                    if len(unique_videos) >= 20:
                        break
            
            result["list"] = unique_videos
        except Exception as e:
            print(f"homeContent error: {e}")
            result["list"] = []
        
        return result
    
    def homeVideoContent(self):
        """返回首頁推薦視頻"""
        return self.homeContent(False)
    
    def categoryContent(self, tid, pg, filter, extend):
        """返回分類頁內容"""
        result = {}
        try:
            if pg == 1:
                url = f"{self.host}/index.php/vod/type/id/{tid}.html"
            else:
                url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
            
            if extend:
                filter_url = f"{self.host}/index.php/vod/show"
                params = []
                params.append(f"id/{tid}")
                
                if extend.get('class') and extend['class'] != tid:
                    params.append(f"class/{extend['class']}")
                if extend.get('area'):
                    params.append(f"area/{urllib.parse.quote(extend['area'])}")
                if extend.get('year'):
                    params.append(f"year/{extend['year']}")
                if extend.get('lang'):
                    params.append(f"lang/{urllib.parse.quote(extend['lang'])}")
                if extend.get('by'):
                    params.append(f"by/{extend['by']}")
                
                if pg == 1:
                    url = f"{filter_url}/{'/'.join(params)}.html"
                else:
                    url = f"{filter_url}/page/{pg}/{'/'.join(params)}.html"
            
            print(f"Fetching category: {url}")
            rsp = self.fetch(url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            videos = []
            vod_items = soup.select('.myui-vodlist__box')
            for item in vod_items:
                link = item.find('a', class_='myui-vodlist__thumb')
                if link:
                    href = link.get('href', '')
                    if href:
                        vod_id = self.build_full_url(href)
                        title = link.get('title', '')
                        pic = link.get('data-original', '')
                        if not pic:
                            pic = link.get('src', '')
                        pic = self.build_full_url(pic)
                        
                        remark_span = item.find('span', class_='pic-text')
                        remark = remark_span.text.strip() if remark_span else ''
                        
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": title,
                            "vod_pic": pic,
                            "vod_remarks": remark
                        })
            
            result["list"] = videos
            
            page_info = soup.find('ul', class_='myui-page')
            if page_info:
                mobile_span = page_info.find('span', class_='visible-xs')
                if mobile_span:
                    page_text = mobile_span.text.strip()
                    match = re.search(r'/(\d+)', page_text)
                    if match:
                        result["pagecount"] = int(match.group(1))
                    else:
                        result["pagecount"] = 1
                else:
                    page_links = page_info.find_all('a')
                    max_page = 1
                    for link in page_links:
                        href = link.get('href', '')
                        match = re.search(r'(?:/page/|page/)(\d+)', href)
                        if match:
                            page_num = int(match.group(1))
                            if page_num > max_page:
                                max_page = page_num
                    
                    if max_page > 1:
                        result["pagecount"] = max_page
                    else:
                        result["pagecount"] = 1
            else:
                result["pagecount"] = 1
            
            if result.get("pagecount", 0) < 1:
                result["pagecount"] = 1
            
            result["page"] = pg
            result["limit"] = len(videos)
            result["total"] = result["pagecount"] * 20
            
        except Exception as e:
            print(f"categoryContent error: {e}")
            result["list"] = []
            result["pagecount"] = 1
            result["page"] = pg
            result["limit"] = 0
            result["total"] = 0
        
        return result
    
    def detailContent(self, ids):
        """返回詳情頁內容"""
        result = {}
        try:
            if isinstance(ids, list):
                vid = ids[0]
            else:
                vid = ids
            
            vid = self.build_full_url(vid)
            
            print(f"Fetching detail: {vid}")
            rsp = self.fetch(vid, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            vod = {
                "vod_id": vid,
                "vod_name": "",
                "vod_pic": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_area": "",
                "vod_year": "",
                "vod_remarks": "",
                "vod_play_from": "",
                "vod_play_url": ""
            }
            
            # 提取標題
            title_tag = soup.find('h1', class_='title')
            if title_tag:
                vod["vod_name"] = title_tag.text.strip()
            
            # 提取封面
            thumb_div = soup.find('div', class_='myui-content__thumb')
            if thumb_div:
                img = thumb_div.find('img')
                if img:
                    pic = img.get('data-original', '')
                    if not pic:
                        pic = img.get('src', '')
                    vod["vod_pic"] = self.build_full_url(pic)
            
            # 提取分類、地區、年份
            data_ps = soup.find_all('p', class_='data')
            for p in data_ps:
                text = p.text
                if '分類：' in text:
                    area_link = p.find('a')
                    if area_link:
                        vod["type_name"] = area_link.text
                elif '地區：' in text:
                    area_link = p.find('a')
                    if area_link:
                        vod["vod_area"] = area_link.text
                elif '年份：' in text:
                    year_link = p.find('a')
                    if year_link:
                        vod["vod_year"] = year_link.text
                elif '更新：' in text:
                    update_text = p.find('span', class_='text-red')
                    if update_text:
                        vod["vod_remarks"] = update_text.text.strip()
            
            # 提取主演
            for p in soup.find_all('p', class_='data'):
                if '主演：' in p.text:
                    actors = []
                    for a in p.find_all('a'):
                        actors.append(a.text.strip())
                    if actors:
                        vod["vod_actor"] = ','.join(actors)
                    else:
                        vod["vod_actor"] = ''
                    break
            
            # 提取導演
            for p in soup.find_all('p', class_='data'):
                if '導演：' in p.text:
                    directors = []
                    for a in p.find_all('a'):
                        directors.append(a.text.strip())
                    if directors:
                        vod["vod_director"] = ','.join(directors)
                    else:
                        vod["vod_director"] = ''
                    break
            
            # 提取簡介
            desc_div = soup.find('div', class_='text-collapse')
            if desc_div:
                content_span = desc_div.find('span', class_='data')
                if content_span:
                    vod["vod_content"] = content_span.get_text(strip=True)
                else:
                    sketch = desc_div.find('span', class_='sketch')
                    if sketch:
                        vod["vod_content"] = sketch.text.strip()
                    else:
                        vod["vod_content"] = desc_div.get_text(strip=True)
            
            # 提取播放地址
            play_froms = []
            play_urls = []
            
            tab_links = soup.select('.myui-panel__head .nav-tabs li a')
            for tab in tab_links:
                play_froms.append(tab.text.strip())
            
            if not play_froms:
                play_froms = ["小宝影院"]
            
            tab_panes = soup.find_all('div', class_='tab-pane')
            for i, pane in enumerate(tab_panes):
                if i >= len(play_froms):
                    break
                
                episodes = []
                playlist = pane.find('ul', class_='myui-content__list')
                if playlist:
                    links = playlist.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if href and href != 'javascript:;':
                            episode_name = link.text.strip()
                            if episode_name:
                                play_url = self.build_full_url(href)
                                if play_url and play_url != '小宝影院':
                                    episodes.append(f"{episode_name}${play_url}")
                
                if episodes:
                    play_urls.append('#'.join(episodes))
            
            if not play_urls:
                playlist_ul = soup.find('ul', class_='myui-content__list')
                if playlist_ul:
                    episodes = []
                    links = playlist_ul.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if href and href != 'javascript:;':
                            episode_name = link.text.strip()
                            if episode_name:
                                play_url = self.build_full_url(href)
                                if play_url and play_url != '小宝影院':
                                    episodes.append(f"{episode_name}${play_url}")
                    if episodes:
                        play_urls.append('#'.join(episodes))
                        play_froms = ["小宝影院"]
            
            if not play_urls:
                play_btn = soup.find('a', class_='btn btn-warm', href=True)
                if play_btn:
                    href = play_btn.get('href', '')
                    if href and href != 'javascript:;':
                        play_url = self.build_full_url(href)
                        if play_url and play_url != '小宝影院':
                            episodes = [f"播放${play_url}"]
                            play_urls.append('#'.join(episodes))
                            play_froms = ["小宝影院"]
            
            vod["vod_play_from"] = '$$$'.join(play_froms)
            vod["vod_play_url"] = '$$$'.join(play_urls)
            
            result["list"] = [vod]
            
        except Exception as e:
            print(f"detailContent error: {e}")
            result["list"] = []
        
        return result
    
    # ==================== 搜索方法 - 優化圖片提取 ====================
    
    def searchContent(self, key, quick, pg=1):
        """搜索內容 - 優化圖片提取"""
        print("="*50)
        print("【搜索】searchContent 被調用")
        print(f"搜索關鍵字: {key}")
        print(f"quick: {quick}")
        print(f"頁碼: {pg}")
        print("="*50)
        
        result = {}
        videos = []
        try:
            # 構建搜索URL
            if pg == 1:
                search_url = f"{self.host}/index.php/vod/search.html?wd={urllib.parse.quote(key)}"
            else:
                search_url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{urllib.parse.quote(key)}.html"
            
            print(f"搜索URL: {search_url}")
            
            rsp = self.fetch(search_url, headers=self.header())
            print(f"響應狀態碼: {rsp.status if hasattr(rsp, 'status') else 'unknown'}")
            
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            # 根據HTML結構，搜索結果在 id="searchList" 的 ul 中
            search_list = soup.find('ul', id='searchList')
            if search_list:
                print("找到 searchList")
                search_items = search_list.find_all('li', class_='clearfix')
                print(f"找到 {len(search_items)} 個搜索結果")
                
                for item in search_items:
                    # 提取標題和鏈接
                    title_tag = item.find('h4', class_='title')
                    if not title_tag:
                        continue
                        
                    link_tag = title_tag.find('a')
                    if not link_tag:
                        continue
                    
                    href = link_tag.get('href', '')
                    if not href:
                        continue
                    
                    vod_id = self.build_full_url(href)
                    title = link_tag.text.strip()
                    
                    # ===== 優化圖片提取 =====
                    pic = ''
                    thumb_div = item.find('div', class_='thumb')
                    if thumb_div:
                        # 方法1: 找 img 標籤
                        img = thumb_div.find('img')
                        if img:
                            # 優先使用 data-original (懶加載)
                            pic = img.get('data-original', '')
                            if not pic:
                                pic = img.get('src', '')
                            print(f"找到圖片: {pic[:50]}...")
                        
                        # 方法2: 如果沒找到圖片，檢查 a 標籤的 style 屬性
                        if not pic:
                            a_tag = thumb_div.find('a')
                            if a_tag:
                                style = a_tag.get('style', '')
                                if 'background-image' in style:
                                    match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                                    if match:
                                        pic = match.group(1)
                                        print(f"從 style 找到圖片: {pic[:50]}...")
                    
                    # 方法3: 如果還是沒找到，嘗試直接從 a 標籤獲取
                    if not pic:
                        a_tag = item.find('a', class_='myui-vodlist__thumb')
                        if a_tag:
                            pic = a_tag.get('data-original', '')
                            if not pic:
                                pic = a_tag.get('src', '')
                    
                    # 補全圖片URL
                    if pic:
                        pic = self.build_full_url(pic)
                    
                    # 提取備註信息
                    remark = ''
                    pic_text = item.find('span', class_='pic-text')
                    if pic_text:
                        remark = pic_text.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": remark
                    })
                    
                    print(f"添加視頻: {title}, 圖片: {bool(pic)}")
            
            # 如果上面的選擇器沒找到，嘗試備用選擇器
            if not videos:
                print("未找到 searchList，嘗試備用選擇器")
                alt_items = soup.select('.myui-vodlist__media li.clearfix')
                for item in alt_items:
                    link = item.find('a', class_='myui-vodlist__thumb')
                    if link:
                        href = link.get('href', '')
                        if href:
                            vod_id = self.build_full_url(href)
                            title = link.get('title', '')
                            
                            # 提取圖片
                            pic = link.get('data-original', '')
                            if not pic:
                                pic = link.get('src', '')
                            pic = self.build_full_url(pic)
                            
                            remark_span = item.find('span', class_='pic-text')
                            remark = remark_span.text.strip() if remark_span else ''
                            
                            videos.append({
                                "vod_id": vod_id,
                                "vod_name": title,
                                "vod_pic": pic,
                                "vod_remarks": remark
                            })
            
            result["list"] = videos
            print(f"總共提取到 {len(videos)} 個視頻")
            print(f"有圖片的視頻數: {len([v for v in videos if v['vod_pic']])}")
            
            # 提取總頁數
            page_info = soup.find('ul', class_='myui-page')
            if page_info:
                mobile_span = page_info.find('span', class_='visible-xs')
                if mobile_span:
                    page_text = mobile_span.text.strip()
                    match = re.search(r'/(\d+)', page_text)
                    if match:
                        result["pagecount"] = int(match.group(1))
                        print(f"總頁數: {result['pagecount']}")
                    else:
                        result["pagecount"] = 1
                else:
                    result["pagecount"] = 1
            else:
                result["pagecount"] = 1
            
            result["page"] = pg
            result["limit"] = len(videos)
            result["total"] = result["pagecount"] * len(videos) if len(videos) > 0 else 0
            
        except Exception as e:
            print(f"搜索錯誤: {e}")
            import traceback
            traceback.print_exc()
            result["list"] = []
        
        return result
    
    # ==================== 備用搜索方法 ====================
    
    def search(self, key):
        """備用搜索方法"""
        print("【備用搜索】search 被調用")
        return self.searchContent(key, False, 1)
    
    def find(self, key):
        """備用搜索方法"""
        print("【備用搜索】find 被調用")
        return self.searchContent(key, False, 1)
    
    def query(self, key):
        """備用搜索方法"""
        print("【備用搜索】query 被調用")
        return self.searchContent(key, False, 1)
    
    def playerContent(self, ids, flag, ext):
        """返回播放器內容 - 使用嗅探模式"""
        result = {}
        try:
            play_url = ids
            print(f"播放請求 - ID: {play_url}, Flag: {flag}")
            
            if play_url == "小宝影院" and flag and flag != "小宝影院":
                play_url = flag
                print(f"使用 flag 作為 URL: {play_url}")
            
            if not play_url or play_url == "小宝影院":
                print("警告: 無效的播放URL")
                return {}
            
            result["parse"] = 1
            result["playUrl"] = ""
            result["url"] = play_url
            result["header"] = json.dumps(self.header())
            
            print(f"返回 parse=1 的 URL: {play_url[:50]}...")
            
        except Exception as e:
            print(f"playerContent 錯誤: {e}")
            result["parse"] = 1
            result["playUrl"] = ""
            result["url"] = ids if ids and ids != "小宝影院" else ""
            result["header"] = json.dumps(self.header())
        
        return result
    
    def isVideoFormat(self, url):
        if not url or not isinstance(url, str):
            return False
        video_exts = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.wmv', '.mov']
        url_lower = url.lower()
        for ext in video_exts:
            if ext in url_lower:
                return True
        return False
    
    def localProxy(self, param):
        return None