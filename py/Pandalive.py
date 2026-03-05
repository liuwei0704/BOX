# -*- coding: utf-8 -*-
import requests
import urllib.parse

class Spider:
    def init(self, extend=""):
        self.host = "https://5721004.xyz"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }
        print("爬蟲初始化成功")

    def getName(self):
        return "M3U8直播"

    def getDependence(self):
        """返回依賴庫"""
        return []

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def localProxy(self, param):
        return None

    def homeContent(self, filter):
        """首頁 - 返回分類和推薦列表"""
        try:
            # 分類
            classes = [
                {'type_id': 'live', 'type_name': '📺 直播頻道'}
            ]
            
            # 獲取直播列表
            live_list = self._get_live_list()
            
            return {
                'class': classes,
                'list': live_list[:20],
                'filters': {}
            }
        except Exception as e:
            print(f"homeContent錯誤: {e}")
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        """首頁視頻推薦"""
        try:
            live_list = self._get_live_list()
            return {'list': live_list[:20]}
        except:
            return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        """分類頁"""
        try:
            if tid == 'live':
                videos = self._get_live_list()
            else:
                videos = []
            
            # 分頁
            page_size = 30
            start = (int(pg) - 1) * page_size
            end = start + page_size
            page_videos = videos[start:end] if start < len(videos) else []
            
            return {
                'list': page_videos,
                'page': int(pg),
                'pagecount': (len(videos) + page_size - 1) // page_size if videos else 1,
                'limit': page_size,
                'total': len(videos)
            }
        except Exception as e:
            print(f"categoryContent錯誤: {e}")
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}

    def _get_live_list(self):
        """從list.m3u獲取直播列表"""
        try:
            url = f"{self.host}/player/list.m3u"
            print(f"請求: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            print(f"響應狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                lines = response.text.split('\n')
                streams = []
                i = 0
                
                while i < len(lines):
                    line = lines[i].strip()
                    
                    if line.startswith('#EXTINF:'):
                        # 解析: #EXTINF:0,主播ID,主播名稱
                        parts = line.split(',', 2)
                        if len(parts) >= 3:
                            name = parts[1].strip()      # 主播ID
                            nameinfo = parts[2].strip()  # 主播名稱
                        else:
                            name = parts[1].strip() if len(parts) > 1 else "未知"
                            nameinfo = name
                        
                        # 下一行是URL
                        if i + 1 < len(lines):
                            url_line = lines[i + 1].strip()
                            if url_line.startswith('http'):
                                # 編碼URL作為ID
                                encoded_url = urllib.parse.quote(url_line, safe='')
                                
                                streams.append({
                                    'vod_id': f"live_{name}_{encoded_url}",
                                    'vod_name': f"📺 {nameinfo}",
                                    'vod_pic': 'https://tupian.li/images/2024/03/30/660769b1ba623.png',
                                    'vod_remarks': '🔴 直播',
                                    'vod_actor': name
                                })
                            i += 1
                    i += 1
                
                print(f"總共找到 {len(streams)} 個直播")
                return streams
            
            return []
            
        except Exception as e:
            print(f"獲取直播列表異常: {e}")
            return []

    def detailContent(self, ids):
        """詳情頁"""
        try:
            if isinstance(ids, list):
                first_id = ids[0]
            else:
                first_id = ids
            
            if first_id.startswith("live_"):
                parts = first_id.split('_', 2)
                if len(parts) == 3:
                    name = parts[1]
                    encoded_url = parts[2]
                    
                    try:
                        stream_url = urllib.parse.unquote(encoded_url)
                    except:
                        stream_url = encoded_url
                    
                    # 代理服務器
                    proxies = [
                        "https://uae2.515355.xyz/proxy/",
                        "https://pol.515355.xyz/proxy/",
                        "https://hubu.515355.xyz/proxy/?",
                        "https://f00.515355.xyz/proxy/",
                        "https://flank.515355.xyz/proxy/",
                        "https://ce2.515355.xyz/proxy/?",
                    ]
                    
                    play_links = []
                    for i, proxy in enumerate(proxies, 1):
                        play_links.append(f"代理{i}${proxy + stream_url}")
                    play_links.append(f"直連${stream_url}")
                    
                    vod = {
                        'vod_id': first_id,
                        'vod_name': f"📺 {name}",
                        'vod_pic': 'https://tupian.li/images/2024/03/30/660769b1ba623.png',
                        'vod_content': f'主播: {name}',
                        'vod_actor': name,
                        'vod_remarks': '🔴 直播',
                        'vod_play_from': '直播源',
                        'vod_play_url': '#'.join(play_links)
                    }
                    return {'list': [vod]}
            
            return {'list': []}
            
        except Exception as e:
            print(f"detailContent錯誤: {e}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        """搜索"""
        try:
            videos = self._get_live_list()
            results = []
            key_lower = key.lower()
            for v in videos:
                if key_lower in v.get('vod_name', '').lower():
                    results.append(v)
            return {'list': results[:50], 'page': int(pg)}
        except:
            return {'list': [], 'page': int(pg)}

    def playerContent(self, flag, id, vipFlags):
        """播放"""
        return {
            'parse': 0,
            'url': id,
            'header': self.headers
        }