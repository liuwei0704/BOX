# -*- coding: utf-8 -*-
import re
import sys
import json
import requests
from urllib.parse import urljoin, urlencode


sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""):
        """初始化爬蟲"""
        pass

    def getName(self):
        """返回網站名稱"""
        return "AVJOY"

    def isVideoFormat(self, url):
        """判斷是否為視頻格式"""
        return False

    def manualVideoCheck(self):
        """手動視頻檢查"""
        pass

    def destroy(self):
        """銷毀爬蟲"""
        pass

    # ==================== 配置區域 ====================
    host = 'https://avjoy.me'  # 網站主域名
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
    }
    
    # 分類映射
    default_classes = [
        {'type_name': '最新', 'type_id': 'latest'},
        {'type_name': '最受欢迎', 'type_id': 'popular'},
        {'type_name': '日本AV', 'type_id': 'jav'},
        {'type_name': '中国', 'type_id': 'china'},
        {'type_name': '无码', 'type_id': 'uncensored'},
    ]
    
    # 列表頁選擇器配置
    list_selector = 'div.content-left div.col-6'  # 視頻列表項
    title_selector = 'span.content-title'  # 標題選擇器
    title_attr = ''  # 標題屬性（留空表示取文本）
    
    img_selector = 'img'  # 圖片選擇器
    img_attr = 'src'  # 圖片屬性
    img_attr_backup = 'data-src'  # 備用圖片屬性
    
    remark_selector = 'div.duration'  # 備註選擇器（顯示時長）
    remark_selector_backup = '.pic-text'  # 備用備註選擇器
    
    # 詳情頁選擇器配置
    detail_name_selector = 'h1'  # 標題
    detail_pic_selector = 'div.player img, div.video-cover img'  # 圖片
    detail_desc_selector = 'div.video-description'  # 簡介
    
    # 播放頁選擇器配置
    play_video_selector = 'video source'  # video標籤
    play_iframe_selector = 'iframe#player, div.player iframe'  # iframe標籤
    
    # 分頁配置
    page_param = 'page'  # 分頁參數名
    
    # ==================== 工具函數 ====================
    
    def _normalize_url(self, url):
        """標準化URL"""
        if not url:
            return ''
        url = str(url).strip()
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        if not url.startswith('http'):
            return 'https://' + url
        return url

    def getpq(self, text):
        """安全獲取PyQuery對象"""
        try:
            return pq(text)
        except:
            try:
                return pq(text.encode('utf-8'))
            except:
                return pq('')

    def _extract_video_basic(self, item):
        """從列表項提取視頻基本信息"""
        try:
            # 獲取連結
            links = item('a')
            if len(links) < 1:
                return None
            link = links.eq(0).attr('href')
            if not link or '/video/' not in link:
                return None
            link = self._normalize_url(link)
            
            # 提取視頻ID
            vid = link.split('/video/')[-1].split('/')[0] if '/video/' in link else ''
            
            # 標題
            title_elem = item.find(self.title_selector)
            title = title_elem.text() if title_elem else ''
            title = title.strip() or '未知標題'
            
            # 圖片
            img = ''
            img_elem = item.find(self.img_selector)
            if img_elem:
                img = img_elem.attr(self.img_attr)
                if not img and self.img_attr_backup:
                    img = img_elem.attr(self.img_attr_backup)
            img = self._normalize_url(img) if img else ''
            
            # 備註（時長）
            remark = ''
            remark_elem = item.find(self.remark_selector)
            if remark_elem:
                remark = remark_elem.text()
            if not remark and self.remark_selector_backup:
                remark_elem = item.find(self.remark_selector_backup)
                if remark_elem:
                    remark = remark_elem.text()
            remark = remark.strip()
            
            return {
                'vod_id': vid,
                'vod_name': title,
                'vod_pic': img,
                'vod_remarks': remark,
                'vod_url': link
            }
        except Exception as e:
            print(f'提取視頻信息失敗: {e}')
            return None

    def _fetch_html(self, url):
        """獲取HTML內容"""
        try:
            rsp = requests.get(url, headers=self.headers, timeout=10)
            if rsp.status_code == 200:
                return rsp.text
        except Exception as e:
            print(f'獲取HTML失敗: {e}')
        return ''

    # ==================== 核心方法 ====================
    
    def homeContent(self, filter):
        """獲取首頁內容"""
        result = {}
        videos = []
        try:
            html = self._fetch_html(self.host)
            if not html:
                return result
            
            doc = self.getpq(html)
            
            # 獲取視頻列表
            items = doc(self.list_selector)
            for item in items.items():
                video_info = self._extract_video_basic(item)
                if video_info:
                    videos.append(video_info)
            
            result['list'] = videos
            result['class'] = self.default_classes
        except Exception as e:
            print(f'homeContent錯誤: {e}')
        return result

    def categoryContent(self, tid, pg, filter, extend):
        """獲取分類內容"""
        result = {}
        videos = []
        page = int(pg) if pg else 1
        try:
            # 構建分類URL
            if tid == 'latest':
                url = f'{self.host}/videos?o=mr&page={page}'
            elif tid == 'popular':
                url = f'{self.host}/videos?o=mv&page={page}'
            else:
                url = f'{self.host}/videos/{tid}?page={page}'
            
            html = self._fetch_html(url)
            if not html:
                return result
            
            doc = self.getpq(html)
            
            # 獲取視頻列表
            items = doc(self.list_selector)
            for item in items.items():
                video_info = self._extract_video_basic(item)
                if video_info:
                    videos.append(video_info)
            
            result['list'] = videos
            result['page'] = str(page)
            result['pagecount'] = '9999'
            result['limit'] = '30'
            result['total'] = '99999'
        except Exception as e:
            print(f'categoryContent錯誤: {e}')
        return result

    def detailContent(self, ids):
        """獲取詳情內容"""
        result = {}
        videos = []
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            url = f'{self.host}/video/{vid}'
            
            html = self._fetch_html(url)
            if not html:
                return result
            
            doc = self.getpq(html)
            
            # 標題
            title_elem = doc(self.detail_name_selector)
            title = title_elem.text() if title_elem else ''
            
            # 封面
            pic = ''
            pic_elem = doc(self.detail_pic_selector)
            if pic_elem:
                pic = pic_elem.attr('src')
            pic = self._normalize_url(pic) if pic else ''
            
            # 描述
            description = ''
            desc_elem = doc(self.detail_desc_selector)
            if desc_elem:
                description = desc_elem.text().strip()
            
            # 獲取播放地址
            play_url = ''
            
            # 嘗試查找video標籤
            video = doc(self.play_video_selector)
            if video:
                play_url = video.attr('src')
            
            # 如果沒有video，嘗試iframe
            if not play_url:
                iframe = doc(self.play_iframe_selector)
                if iframe:
                    play_url = iframe.attr('src')
            
            play_url = self._normalize_url(play_url) if play_url else ''
            
            videos.append({
                'vod_id': vid,
                'vod_name': title,
                'vod_pic': pic,
                'vod_content': description,
                'vod_play_from': 'avjoy',
                'vod_play_url': f'{title}${play_url}'
            })
            
            result['list'] = videos
        except Exception as e:
            print(f'detailContent錯誤: {e}')
        return result

    def searchContent(self, keyword, pg):
        """搜索內容"""
        result = {}
        videos = []
        try:
            url = f'{self.host}/search/videos/{keyword}?page={pg}'
            
            html = self._fetch_html(url)
            if not html:
                return result
            
            doc = self.getpq(html)
            
            items = doc(self.list_selector)
            for item in items.items():
                video_info = self._extract_video_basic(item)
                if video_info:
                    videos.append(video_info)
            
            result['list'] = videos
        except Exception as e:
            print(f'searchContent錯誤: {e}')
        return result

    def playerContent(self, flag, id, vipFlags):
        """獲取播放地址"""
        result = {}
        try:
            # 如果 id 已經是完整URL，直接返回
            if id.startswith('http'):
                result['parse'] = 0
                result['url'] = id
                result['header'] = self.headers
            else:
                # 否則從詳情頁獲取播放地址
                detail = self.detailContent([id])
                if detail and detail.get('list'):
                    play_url = detail['list'][0].get('vod_play_url', '')
                    if play_url:
                        result['parse'] = 0
                        result['url'] = play_url.split('$')[-1]
                        result['header'] = self.headers
        except Exception as e:
            print(f'playerContent錯誤: {e}')
        return result
