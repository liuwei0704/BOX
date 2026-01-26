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
        return "追劇網修復版"
    
    def init(self, extend=""):
        self.host = "https://ztv.tw"
        pass
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
            'Referer': self.host
        }
    
    def homeContent(self, filter):
        result = {}
        classes = [
            {"type_name": "電影", "type_id": "1"},
            {"type_name": "劇集", "type_id": "2"},
            {"type_name": "綜藝", "type_id": "3"},
            {"type_name": "動漫", "type_id": "4"}
        ]
        result["class"] = classes
        
        # 移除篩選功能
        result["filters"] = {}
        return result
    
    def homeVideoContent(self):
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 解析首頁推薦視頻
            items = root.select('.vodlist_item')
            for item in items:
                try:
                    a_tag = item.find('a', class_='vodlist_thumb')
                    if not a_tag or not a_tag.get('href'):
                        continue
                    
                    vod_id = a_tag['href']
                    
                    # 獲取圖片
                    vod_pic = ""
                    if 'data-original' in a_tag.attrs:
                        vod_pic = a_tag['data-original']
                    
                    if vod_pic and not vod_pic.startswith('http'):
                        if vod_pic.startswith('//'):
                            vod_pic = 'https:' + vod_pic
                        elif vod_pic.startswith('/'):
                            vod_pic = self.host + vod_pic
                    
                    # 獲取標題
                    title_div = item.find('div', class_='vodlist_titbox')
                    vod_name = ""
                    if title_div:
                        title_a = title_div.find('a')
                        if title_a:
                            vod_name = title_a.text.strip()
                        else:
                            title_p = title_div.find('p', class_='vodlist_title')
                            if title_p:
                                vod_name = title_p.text.strip()
                    
                    # 獲取備註信息
                    vod_remarks = ""
                    pic_text = item.find('span', class_='pic_text')
                    if pic_text:
                        vod_remarks = pic_text.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                    
                except Exception as e:
                    print(f"解析單個視頻錯誤: {e}")
                    continue
            
            videos = videos[:30]
            return {"list": videos}
            
        except Exception as e:
            print(f"首頁視頻解析錯誤: {e}")
            return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        try:
            print(f"分類ID: {tid}, 頁碼: {pg}")
            
            category_id = tid
            
            # 構建URL
            if int(pg) > 1:
                url = f"{self.host}/vodtype/{category_id}-{pg}.html"
            else:
                url = f"{self.host}/vodtype/{category_id}.html"
            
            print(f"請求URL: {url}")
            
            rsp = self.fetch(url, headers=self.header())
            
            if rsp.status_code != 200:
                print(f"請求失敗: {rsp.status_code}")
                return {
                    "list": [],
                    "page": int(pg),
                    "pagecount": 1,
                    "limit": 20,
                    "total": 0
                }
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            items = root.select('.vodlist_item')
            if not items:
                items = root.select('li.vodlist_item')
            
            print(f"找到 {len(items)} 個視頻項目")
            
            for item in items:
                try:
                    a_tag = item.find('a', class_='vodlist_thumb')
                    if not a_tag:
                        a_tag = item.find('a')
                    
                    if not a_tag or not a_tag.get('href'):
                        continue
                    
                    vod_id = a_tag['href']
                    
                    if not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
                    
                    # 獲取圖片
                    vod_pic = ""
                    if 'data-original' in a_tag.attrs:
                        vod_pic = a_tag['data-original']
                    
                    if vod_pic and not vod_pic.startswith('http'):
                        if vod_pic.startswith('//'):
                            vod_pic = 'https:' + vod_pic
                        elif vod_pic.startswith('/'):
                            vod_pic = self.host + vod_pic
                    
                    # 獲取標題
                    vod_name = ""
                    title_elem = item.find('p', class_='vodlist_title')
                    if title_elem:
                        title_link = title_elem.find('a')
                        if title_link:
                            vod_name = title_link.text.strip()
                        else:
                            vod_name = title_elem.text.strip()
                    
                    if not vod_name:
                        vod_name = "未知影片"
                    
                    # 獲取備註信息
                    vod_remarks = ""
                    pic_text = item.find('span', class_='pic_text')
                    if pic_text:
                        vod_remarks = pic_text.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                    
                except Exception as e:
                    print(f"解析項目錯誤: {e}")
                    continue
            
            # 簡單分頁處理
            pagecount = 1
            try:
                page_links = root.select('.page a')
                max_page = 1
                
                for link in page_links:
                    href = link.get('href', '')
                    if href and f"/vodtype/{category_id}-" in href:
                        match = re.search(rf'/vodtype/{category_id}-(\d+)\.html', href)
                        if match:
                            page_num = int(match.group(1))
                            if page_num > max_page:
                                max_page = page_num
                
                if max_page > 1:
                    pagecount = max_page
                else:
                    pagecount = 1
                    
            except Exception as e:
                print(f"分頁解析錯誤: {e}")
                pagecount = 1
            
            print(f"解析完成，找到 {len(videos)} 個視頻，總頁數: {pagecount}")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 20,
                "total": 999999
            }
            
        except Exception as e:
            print(f"分類頁面解析錯誤: {e}")
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }
    
    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            print(f"原始ID: {vod_id}")
            
            # ==================== 關鍵修復：智能URL處理 ====================
            play_url = None
            detail_url = None
            
            # 判斷URL類型並提取ID
            if '/vodplay/' in vod_id:
                print("檢測到播放頁面URL")
                play_url = vod_id
                # 從播放頁面提取影片ID和線路ID
                match = re.search(r'/vodplay/(\d+)-(\d+)-\d+\.html', vod_id)
                if match:
                    detail_id = match.group(1)
                    line_id = match.group(2)
                    detail_url = f"/vod/detail/{detail_id}.html"
                    print(f"提取到影片ID: {detail_id}, 線路ID: {line_id}")
            elif '/detail/' in vod_id or '/vod/detail/' in vod_id:
                print("檢測到詳情頁面URL")
                detail_url = vod_id
                # 從詳情頁提取影片ID
                match = re.search(r'/detail/(\d+)\.html', vod_id)
                if not match:
                    match = re.search(r'/vod/detail/(\d+)\.html', vod_id)
                if match:
                    detail_id = match.group(1)
                    # 默認使用線路1
                    play_url = f"/vodplay/{detail_id}-1-1.html"
            else:
                print("未知URL格式，直接訪問")
                detail_url = vod_id
            
            # 構建完整URL
            def build_full_url(url):
                if not url or not isinstance(url, str):
                    return None
                if not url.startswith('http'):
                    if url.startswith('/'):
                        return self.host + url
                    else:
                        return self.host + '/' + url
                return url
            
            # 首先獲取詳情信息
            vod_info = {}
            if detail_url:
                detail_url = build_full_url(detail_url)
                print(f"詳情頁URL: {detail_url}")
                try:
                    rsp = self.fetch(detail_url, headers=self.header())
                    if rsp.status_code == 200:
                        html_content = rsp.text
                        root = BeautifulSoup(html_content, 'html.parser')
                        
                        # 獲取影片名稱
                        vod_name = "未知"
                        h1_tag = root.find('h1')
                        if h1_tag:
                            vod_name = h1_tag.text.strip()
                        
                        if vod_name == "未知":
                            title_tag = root.find('title')
                            if title_tag:
                                vod_name = title_tag.text.strip()
                                if ' - ' in vod_name:
                                    vod_name = vod_name.split(' - ')[0]
                                if '|' in vod_name:
                                    vod_name = vod_name.split('|')[0]
                        
                        # 獲取影片圖片
                        vod_pic = ""
                        img_tag = root.find('img', class_='lazyload')
                        if img_tag and 'data-original' in img_tag.attrs:
                            vod_pic = img_tag['data-original']
                        
                        if vod_pic and not vod_pic.startswith('http'):
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            elif vod_pic.startswith('/'):
                                vod_pic = self.host + vod_pic
                        
                        # 獲取影片描述
                        vod_content = ""
                        play_content = root.find('div', class_='play_content')
                        if play_content:
                            p_tags = play_content.find_all('p')
                            for p in p_tags:
                                text = p.get_text(strip=True)
                                if text and len(text) > 20:
                                    vod_content = text
                                    break
                        
                        vod_info = {
                            "vod_name": vod_name,
                            "vod_pic": vod_pic,
                            "vod_content": vod_content,
                            "vod_year": "",
                            "vod_area": "",
                            "vod_lang": "",
                            "vod_actor": "",
                            "vod_director": "",
                            "vod_remarks": ""
                        }
                        
                        # 嘗試在詳情頁面查找立即播放按鈕
                        play_buttons = root.select('a[href*="vodplay"], a.play-btn, a[href*="/play/"]')
                        if play_buttons:
                            for btn in play_buttons:
                                href = btn.get('href', '')
                                if href and 'vodplay' in href:
                                    if not play_url:
                                        play_url = href
                                    break
                except Exception as e:
                    print(f"詳情頁解析錯誤: {e}")
            
            # ==================== 關鍵：從播放器頁面獲取線路和劇集 ====================
            play_from_list = []
            play_url_list = []
            
            # 如果沒有播放頁面URL，嘗試構建一個
            if not play_url:
                # 從詳情頁URL提取ID
                match = re.search(r'/detail/(\d+)\.html', detail_url) if detail_url else None
                if not match:
                    match = re.search(r'/vod/detail/(\d+)\.html', detail_url) if detail_url else None
                if match:
                    detail_id = match.group(1)
                    play_url = f"/vodplay/{detail_id}-1-1.html"
            
            if play_url:
                play_url = build_full_url(play_url)
                print(f"播放器頁面URL: {play_url}")
                
                try:
                    rsp = self.fetch(play_url, headers=self.header())
                    if rsp.status_code == 200:
                        html_content = rsp.text
                        root = BeautifulSoup(html_content, 'html.parser')
                        
                        # ==================== 修復線路解析邏輯 ====================
                        print("開始解析播放線路和劇集...")
                        
                        # 方法1: 查找線路選擇標籤 - 修正選擇器
                        line_tabs = []
                        seen_line_ids = set()  # 避免重複
                        
                        # 優先查找標準的線路選擇器
                        tab_selectors = [
                            '#NumTab a',  # 最常見的選擇器
                            '.tabs a',
                            '.tab a',
                            '.play-source-tab a',
                            '.play_tab a',
                            '.source-tab a'
                        ]
                        
                        for selector in tab_selectors:
                            tabs = root.select(selector)
                            if tabs:
                                print(f"使用選擇器找到線路: {selector}, 數量: {len(tabs)}")
                                for tab in tabs:
                                    line_name = tab.get_text(strip=True)
                                    if line_name and len(line_name) < 20:
                                        # 獲取線路ID
                                        line_id = None
                                        href = tab.get('href', '')
                                        
                                        # 從href提取線路ID
                                        if href:
                                            match = re.search(r'/vodplay/\d+-(\d+)-\d+\.html', href)
                                            if match:
                                                line_id = match.group(1)
                                            else:
                                                # 檢查是否有data屬性
                                                line_id = tab.get('data-id') or tab.get('data-sid')
                                        
                                        # 如果還是沒有，從onclick提取
                                        if not line_id:
                                            onclick = tab.get('onclick', '')
                                            if onclick:
                                                match = re.search(r'changePlay\(\s*["\']?(\d+)["\']?\s*\)', onclick)
                                                if not match:
                                                    match = re.search(r'switchPlay\(\s*["\']?(\d+)["\']?\s*\)', onclick)
                                                if not match:
                                                    match = re.search(r'play\(\s*["\']?(\d+)["\']?\s*\)', onclick)
                                                if match:
                                                    line_id = match.group(1)
                                        
                                        # 如果還是沒有，使用順序ID
                                        if not line_id:
                                            line_id = str(len(line_tabs) + 1)
                                        
                                        # 避免重複線路
                                        if line_id not in seen_line_ids:
                                            seen_line_ids.add(line_id)
                                            line_tabs.append({
                                                'name': line_name,
                                                'id': line_id,
                                                'element': tab
                                            })
                                            print(f"找到線路: {line_name} (ID: {line_id})")
                                break  # 找到就停止
                        
                        # 方法2: 如果沒有找到標準選擇器，查找所有可能是線路的元素
                        if not line_tabs:
                            print("未找到標準線路選擇器，嘗試查找所有可能線路...")
                            possible_lines = root.select('a[href*="vodplay"], span[onclick*="play"], span[onclick*="change"], span[onclick*="switch"]')
                            
                            for elem in possible_lines:
                                line_name = elem.get_text(strip=True)
                                if line_name and len(line_name) < 20 and line_name not in ['立即播放', '播放', '全集']:
                                    line_id = None
                                    
                                    # 嘗試獲取線路ID
                                    href = elem.get('href', '')
                                    if href:
                                        match = re.search(r'/vodplay/\d+-(\d+)-\d+\.html', href)
                                        if match:
                                            line_id = match.group(1)
                                    
                                    onclick = elem.get('onclick', '')
                                    if onclick and not line_id:
                                        match = re.search(r'changePlay\(\s*["\']?(\d+)["\']?\s*\)', onclick)
                                        if not match:
                                            match = re.search(r'switchPlay\(\s*["\']?(\d+)["\']?\s*\)', onclick)
                                        if not match:
                                            match = re.search(r'play\(\s*["\']?(\d+)["\']?\s*\)', onclick)
                                        if match:
                                            line_id = match.group(1)
                                    
                                    if line_id and line_id not in seen_line_ids:
                                        seen_line_ids.add(line_id)
                                        line_tabs.append({
                                            'name': line_name,
                                            'id': line_id,
                                            'element': elem
                                        })
                                        print(f"找到線路: {line_name} (ID: {line_id})")
                        
                        # 方法3: 從JavaScript中解析線路
                        if not line_tabs:
                            print("嘗試從JavaScript解析線路...")
                            script_pattern = r'var\s+player_aaaa\s*=\s*({.*?});'
                            script_match = re.search(script_pattern, html_content, re.DOTALL)
                            if script_match:
                                try:
                                    player_data = json.loads(script_match.group(1))
                                    if 'from' in player_data:
                                        from_list = player_data['from'].split('$$$')
                                        for i, line_name in enumerate(from_list):
                                            line_id = str(i + 1)
                                            if line_id not in seen_line_ids:
                                                seen_line_ids.add(line_id)
                                                line_tabs.append({
                                                    'name': line_name,
                                                    'id': line_id,
                                                    'element': None
                                                })
                                                print(f"從JS找到線路: {line_name} (ID: {line_id})")
                                except Exception as e:
                                    print(f"JS解析錯誤: {e}")
                        
                        # 如果還是沒有線路，創建默認線路
                        if not line_tabs:
                            print("創建默認線路")
                            line_tabs.append({
                                'name': '默認線路',
                                'id': '1',
                                'element': None
                            })
                        
                        print(f"總共找到 {len(line_tabs)} 個不重複的線路")
                        
                        # ==================== 為每個線路解析劇集 ====================
                        for line_info in line_tabs:
                            line_name = line_info['name']
                            line_id = line_info['id']
                            
                            print(f"解析線路: {line_name} (ID: {line_id})")
                            
                            # 方法A: 查找對應該線路的劇集容器
                            episode_links = []
                            
                            # 優先查找對應該線路的播放列表
                            container_selectors = [
                                f'#playlist_{line_id}',
                                f'.playlist_{line_id}',
                                f'div[data-id="{line_id}"]',
                                f'div[data-sid="{line_id}"]',
                                f'ul[data-id="{line_id}"]'
                            ]
                            
                            target_container = None
                            for selector in container_selectors:
                                containers = root.select(selector)
                                if containers:
                                    target_container = containers[0]
                                    print(f"找到線路 {line_id} 的播放列表容器")
                                    break
                            
                            # 如果沒有找到特定容器，嘗試查找所有播放列表
                            if not target_container:
                                all_containers = root.select('.play_list_box, .playlist-box, #playlist, .playlist')
                                if all_containers:
                                    # 根據線路索引選擇容器
                                    line_index = line_tabs.index(line_info)
                                    if line_index < len(all_containers):
                                        target_container = all_containers[line_index]
                                        print(f"根據索引選擇容器 {line_index}")
                            
                            # 從容器中提取劇集
                            if target_container:
                                episodes = target_container.select('a[href*="vodplay"]')
                                if not episodes:
                                    episodes = target_container.select('a')
                                
                                for episode in episodes:
                                    episode_url = episode.get('href', '')
                                    episode_title = episode.get_text(strip=True)
                                    
                                    if episode_url and 'vodplay' in episode_url:
                                        # 處理URL
                                        if not episode_url.startswith('http'):
                                            if episode_url.startswith('//'):
                                                episode_url = 'https:' + episode_url
                                            elif episode_url.startswith('/'):
                                                episode_url = self.host + episode_url
                                            else:
                                                episode_url = self.host + '/' + episode_url
                                        
                                        # 處理標題
                                        if not episode_title or episode_title in ['立即播放', '播放']:
                                            # 從URL提取集數
                                            match = re.search(r'/vodplay/\d+-\d+-(\d+)\.html', episode_url)
                                            if match:
                                                episode_title = f"第{match.group(1)}集"
                                            else:
                                                episode_title = f"第{len(episode_links)+1}集"
                                        
                                        # 清理標題
                                        episode_title = episode_title.replace('$', '').replace('#', '')
                                        
                                        episode_links.append(f"{episode_title}${episode_url}")
                            
                            # 方法B: 如果沒有容器，查找所有對應線路的劇集連結
                            if not episode_links:
                                all_vodplay = root.find_all('a', href=re.compile(rf'/vodplay/\d+-{line_id}-\d+\.html'))
                                for link in all_vodplay:
                                    episode_url = link.get('href', '')
                                    episode_title = link.get_text(strip=True)
                                    
                                    if episode_url:
                                        # 處理URL
                                        if not episode_url.startswith('http'):
                                            if episode_url.startswith('//'):
                                                episode_url = 'https:' + episode_url
                                            elif episode_url.startswith('/'):
                                                episode_url = self.host + episode_url
                                            else:
                                                episode_url = self.host + '/' + episode_url
                                        
                                        # 處理標題
                                        if not episode_title:
                                            match = re.search(r'/vodplay/\d+-\d+-(\d+)\.html', episode_url)
                                            if match:
                                                episode_title = f"第{match.group(1)}集"
                                            else:
                                                episode_title = f"第{len(episode_links)+1}集"
                                        
                                        episode_title = episode_title.replace('$', '').replace('#', '')
                                        
                                        episode_links.append(f"{episode_title}${episode_url}")
                            
                            # 方法C: 如果還是沒有，嘗試從頁面中提取劇集總數並生成
                            if not episode_links:
                                # 查找劇集總數
                                total_episodes = 1
                                
                                # 從頁面文本中查找
                                if '全' in html_content and '集' in html_content:
                                    match = re.search(r'全(\d+)集', html_content)
                                    if match:
                                        total_episodes = int(match.group(1))
                                        print(f"從頁面找到總集數: {total_episodes}")
                                
                                # 生成劇集連結
                                if total_episodes > 1:
                                    # 提取影片ID
                                    match = re.search(r'/vodplay/(\d+)-\d+-\d+\.html', play_url)
                                    if match:
                                        vod_id_num = match.group(1)
                                        for i in range(1, min(total_episodes, 100) + 1):
                                            ep_url = f"{self.host}/vodplay/{vod_id_num}-{line_id}-{i}.html"
                                            episode_links.append(f"第{i}集${ep_url}")
                                    
                                if not episode_links:
                                    # 至少有一個劇集
                                    episode_links.append(f"第1集${play_url}")
                            
                            # 對劇集進行排序
                            if episode_links:
                                # 按集數排序
                                def get_episode_num(item):
                                    match = re.search(r'第(\d+)集', item.split('$')[0])
                                    if match:
                                        return int(match.group(1))
                                    return 999999
                                
                                episode_links.sort(key=get_episode_num)
                                
                                # 添加到播放列表
                                play_from_list.append(line_name)
                                play_url_list.append("#".join(episode_links))
                                
                                print(f"線路 {line_name}: 找到 {len(episode_links)} 個劇集")
                                
                    else:
                        print(f"播放器頁面請求失敗: {rsp.status_code}")
                except Exception as e:
                    print(f"播放器頁面解析錯誤: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 如果還是沒有找到劇集，使用默認
            if not play_from_list:
                print("使用默認播放列表")
                play_from_list = ["追劇網線路"]
                if play_url:
                    play_url_list = [f"第1集${play_url}"]
                else:
                    play_url_list = [f"第1集${self.host}"]
            
            # 構建完整的影片信息
            video = {
                "vod_id": ids[0],
                "vod_name": vod_info.get("vod_name", "未知影片"),
                "vod_pic": vod_info.get("vod_pic", ""),
                "vod_content": vod_info.get("vod_content", ""),
                "vod_year": vod_info.get("vod_year", ""),
                "vod_area": vod_info.get("vod_area", ""),
                "vod_lang": vod_info.get("vod_lang", ""),
                "vod_actor": vod_info.get("vod_actor", ""),
                "vod_director": vod_info.get("vod_director", ""),
                "vod_remarks": vod_info.get("vod_remarks", ""),
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }
            
            print(f"解析完成，找到 {len(play_from_list)} 個播放線路")
            for i, source in enumerate(play_from_list):
                if i < len(play_url_list):
                    episodes = play_url_list[i].split('#')
                    print(f"線路 {i+1}: {source} - {len(episodes)} 個劇集")
                    if len(episodes) <= 3:
                        for j, ep in enumerate(episodes):
                            ep_title = ep.split('$')[0] if '$' in ep else ep
                            print(f"  劇集 {j+1}: {ep_title}")
            
            return {"list": [video]}
            
        except Exception as e:
            print(f"詳情頁解析錯誤: {e}")
            import traceback
            traceback.print_exc()
            
            # 返回錯誤信息但仍提供基本播放
            video = {
                "vod_id": ids[0],
                "vod_name": "影片詳情解析失敗",
                "vod_pic": "",
                "vod_content": "",
                "vod_play_from": "追劇網線路",
                "vod_play_url": f"第1集${self.host}"
            }
            return {"list": [video]}
    
    # searchContent, playerContent 等方法保持不變
    def searchContent(self, key, quick, pg=1):
        try:
            encoded_key = urllib.parse.quote(key)
            search_url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            
            print(f"搜索URL: {search_url}")
            rsp = self.fetch(search_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            items = root.select('.searchlist_item')
            for item in items:
                try:
                    img_div = item.find('div', class_='searchlist_img')
                    a_tag = img_div.find('a', class_='vodlist_thumb') if img_div else None
                    
                    if not a_tag or not a_tag.get('href'):
                        continue
                    
                    vod_id = a_tag['href']
                    
                    if not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
                    
                    vod_pic = ""
                    if 'data-original' in a_tag.attrs:
                        vod_pic = a_tag['data-original']
                    
                    if vod_pic and not vod_pic.startswith('http'):
                        if vod_pic.startswith('//'):
                            vod_pic = 'https:' + vod_pic
                        elif vod_pic.startswith('/'):
                            vod_pic = self.host + vod_pic
                    
                    title_div = item.find('div', class_='searchlist_titbox')
                    vod_name = ""
                    vod_type = ""
                    
                    if title_div:
                        title_a = title_div.find('h4', class_='vodlist_title').find('a')
                        if title_a:
                            title_text = title_a.get_text(strip=True)
                            info_right = title_a.find('span', class_='info_right')
                            if info_right:
                                vod_type = info_right.text.strip()
                                title_text = title_text.replace(vod_type, '').strip()
                            vod_name = title_text
                    
                    vod_remarks = ""
                    pic_text = a_tag.find('span', class_='pic_text')
                    if pic_text:
                        vod_remarks = pic_text.text.strip()
                    
                    vod_actor = ""
                    actor_p = item.find('p', class_='vodlist_sub')
                    if actor_p and '演員：' in actor_p.text:
                        vod_actor = actor_p.text.replace('演員：', '').strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks,
                        "vod_type": vod_type,
                        "vod_actor": vod_actor
                    })
                    
                except Exception as e:
                    print(f"搜索結果解析單個項目錯誤: {e}")
                    continue
            
            pagecount = 1
            total = 0
            
            try:
                page_text = root.get_text()
                
                total_match = re.search(r'相關的<em[^>]*>(\d+)</em>條結果', page_text)
                if total_match:
                    total = int(total_match.group(1))
                
                page_match = re.search(r'總共\s*(\d+)\s*頁', page_text)
                if page_match:
                    pagecount = int(page_match.group(1))
                else:
                    page_links = root.find_all('a', href=True)
                    max_page = 1
                    for link in page_links:
                        href = link['href']
                        if '/vodsearch/' in href and '---' in href:
                            try:
                                parts = href.split('---')
                                if len(parts) >= 2:
                                    page_num = int(parts[-2])
                                    if page_num > max_page:
                                        max_page = page_num
                            except:
                                pass
                    pagecount = max_page if max_page > 1 else 1
                    
            except Exception as e:
                print(f"搜索分頁解析錯誤: {e}")
                pagecount = 1
                total = len(videos) * pagecount
            
            print(f"搜索到 {len(videos)} 個結果，共 {pagecount} 頁，總數 {total}")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 20,
                "total": total
            }
            
        except Exception as e:
            print(f"搜索頁面解析錯誤: {e}")
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }
    
    def playerContent(self, flag, id, vipFlags):
        result = {}
        
        try:
            if not id.startswith('http'):
                if id.startswith('/'):
                    play_url = self.host + id
                else:
                    play_url = self.host + '/' + id
            else:
                play_url = id
            
            print(f"播放頁面URL: {play_url}")
            rsp = self.fetch(play_url, headers=self.header())
            
            script_pattern = r'var\s+player_aaaa\s*=\s*({.*?});'
            script_match = re.search(script_pattern, rsp.text, re.DOTALL)
            
            if script_match:
                try:
                    player_data = json.loads(script_match.group(1))
                    
                    if 'url' in player_data and player_data['url']:
                        real_url = player_data['url']
                        real_url = real_url.replace('\\/', '/')
                        
                        result["parse"] = 0
                        result["url"] = real_url
                        result["header"] = self.header()
                        print(f"找到真實播放地址: {real_url}")
                        return result
                except json.JSONDecodeError:
                    print("JSON解析失敗，嘗試其他方法")
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            iframe = root.find('iframe')
            if iframe and iframe.get('src'):
                iframe_src = iframe['src']
                if iframe_src:
                    if not iframe_src.startswith('http'):
                        if iframe_src.startswith('//'):
                            iframe_src = 'https:' + iframe_src
                        elif iframe_src.startswith('/'):
                            iframe_src = self.host + iframe_src
                    
                    result["parse"] = 0
                    result["url"] = iframe_src
                    result["header"] = self.header()
                    return result
            
            video_tag = root.find('video')
            if video_tag and video_tag.get('src'):
                video_src = video_tag['src']
                if not video_src.startswith('http'):
                    if video_src.startswith('//'):
                        video_src = 'https:' + video_src
                    elif video_src.startswith('/'):
                        video_src = self.host + video_src
                
                result["parse"] = 0
                result["url"] = video_src
                result["header"] = self.header()
                return result
            
            if '.m3u8' in rsp.text:
                m3u8_pattern = r'https?://[^\s"\']+\.m3u8[^\s"\']*'
                m3u8_matches = re.findall(m3u8_pattern, rsp.text)
                if m3u8_matches:
                    result["parse"] = 0
                    result["url"] = m3u8_matches[0]
                    result["header"] = self.header()
                    return result
            
            result["parse"] = 1
            result["url"] = play_url
            result["header"] = self.header()
            result["ua"] = "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"
            
        except Exception as e:
            print(f"播放頁面解析錯誤: {e}")
            result["parse"] = 1
            result["url"] = id
            result["header"] = self.header()
        
        return result
    
    def isVideoFormat(self, url):
        video_formats = ['.m3u8', '.mp4', '.avi', '.mkv', '.flv', '.ts', '.webm']
        for fmt in video_formats:
            if fmt in url.lower():
                return True
        return False
    
    def localProxy(self, params):
        return [200, "video/MP2T", ""]