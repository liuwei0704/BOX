# -*- coding: utf-8 -*-
import re
import sys
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""):
        pass

    def getName(self):
        return "MissAVt"

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    host = 'https://central.znfcqan.cc'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://central.znfcqan.cc'
    }

    def _get_html(self, response):
        if hasattr(response, 'text'):
            return response.text
        return str(response)

    def _normalize_url(self, url):
        if url.startswith('/'):
            return self.host + url
        return url

    def homeContent(self, filter):
        result = {'class': [], 'list': []}
        
        # 分類列表
        result['class'] = [
            {'type_name': '首页', 'type_id': '/'},
            {'type_name': '热门影片', 'type_id': '/sort/month_hot/'},
            {'type_name': '国产AV', 'type_id': '/category/domestic-media/'},
            {'type_name': '有码', 'type_id': '/category/censored/'},
            {'type_name': '无码', 'type_id': '/category/uncensored-leak/'},
            {'type_name': '素人', 'type_id': '/category/amateur/'},
            {'type_name': '中文字幕', 'type_id': '/category/chinese-subtitle/'},
            {'type_name': '无码破解', 'type_id': '/category/reducing-mosaic/'},
            {'type_name': '女优', 'type_id': '/actresses/hot/'},
            {'type_name': '主题', 'type_id': '/tags/'},
        ]
        
        # 獲取首頁HTML
        r = self.fetch(self.host, headers=self.headers)
        if r:
            html = self._get_html(r)
            
            # 找到所有視頻列表區塊
            blocks = re.findall(r'<ul[^>]*class="video-items[^"]*"[^>]*>(.*?)</ul>', html, re.S)
            
            for block in blocks:
                items = re.findall(r'<li>(.*?)</li>', block, re.S)
                for item in items:
                    href_match = re.search(r'href="([^"]+)"', item)
                    if not href_match:
                        continue
                    href = href_match.group(1)
                    
                    pic_match = re.search(r'data-src="([^"]+)"', item)
                    pic = pic_match.group(1) if pic_match else ''
                    
                    title_match = re.search(r'<a[^>]*class="[^"]*my-1[^"]*"[^>]*>(.*?)</a>', item, re.S)
                    if title_match:
                        title = title_match.group(1).strip()
                        title = re.sub(r'^\d+:\d+:\d+\s*', '', title)
                        result['list'].append({
                            'vod_id': href,
                            'vod_name': title,
                            'vod_pic': pic,
                            'vod_remarks': ''
                        })
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {'list': [], 'page': pg, 'pagecount': 1, 'limit': 24, 'total': 0}
        
        # 構建URL
        url = self._normalize_url(tid)
        if pg != '1':
            if url.endswith('/'):
                url = url + pg
            else:
                url = url + '/' + pg

        r = self.fetch(url, headers=self.headers)
        if r:
            html = self._get_html(r)
            
            # 找到視頻列表
            list_match = re.search(r'<ul[^>]*class="video-items[^"]*"[^>]*>(.*?)</ul>', html, re.S)
            if list_match:
                items = re.findall(r'<li>(.*?)</li>', list_match.group(1), re.S)
                
                for item in items:
                    href_match = re.search(r'href="([^"]+)"', item)
                    if not href_match: 
                        continue
                    href = href_match.group(1)
                    
                    pic_match = re.search(r'data-src="([^"]+)"', item)
                    pic = pic_match.group(1) if pic_match else ''
                    
                    title = ''
                    t1 = re.search(r'<a[^>]*class="[^"]*my-1[^"]*"[^>]*>(.*?)</a>', item, re.S)
                    if t1:
                        title = t1.group(1).strip()
                    else:
                        t2 = re.search(r'<img[^>]*alt="([^"]+)"', item)
                        if t2:
                            title = t2.group(1).strip()
                    
                    if title:
                        title = re.sub(r'^\d+:\d+:\d+\s*', '', title)
                        result['list'].append({
                            'vod_id': href,
                            'vod_name': title,
                            'vod_pic': pic,
                            'vod_remarks': ''
                        })
            
            # 解析分頁
            total_match = re.search(r'第1/(\d+) 页', html)
            if total_match:
                result['pagecount'] = int(total_match.group(1))
        
        return result

    def detailContent(self, ids):
        result = {'list': []}
        if not ids: return result
        
        url = self._normalize_url(ids[0])
        r = self.fetch(url, headers=self.headers)
        if r:
            html = self._get_html(r)
            
            # 標題
            title = ''
            t1 = re.search(r'<h1[^>]*>(.*?)</h1>', html)
            if t1: 
                title = t1.group(1).strip()
            else:
                t2 = re.search(r'<title>(.*?) - MissAVt</title>', html)
                if t2: 
                    title = t2.group(1).strip()
            
            # 嘗試提取海報，但不要影響其他功能
            poster = ''
            try:
                p1 = re.search(r'<img[^>]*data-src="([^"]+)"', html)
                if p1:
                    poster = p1.group(1)
                    if poster.startswith('//'):
                        poster = 'https:' + poster
            except:
                pass
            
            # 視頻地址 - 優先從 poster div 的 data-url 提取
            video = ''
            v1 = re.search(r'<div[^>]*class="[^"]*poster[^"]*"[^>]*data-url="([^"]+)"', html)
            if v1:
                video = v1.group(1)
            
            if not video:
                v2 = re.search(r'data-url="([^"]+)"', html)
                if v2:
                    video = v2.group(1)
            
            if not video:
                v3 = re.search(r'<video[^>]*src="([^"]+)"', html)
                if v3:
                    video = v3.group(1)
            
            if not video:
                all_m3u8 = re.findall(r'(https?://[^"\']+\.m3u8[^"\']*)', html)
                for url in all_m3u8:
                    if 'preview' not in url.lower() and '10s' not in url.lower():
                        video = url
                        break
                if not video and all_m3u8:
                    video = all_m3u8[0]
            
            if video:
                video = video.replace('&amp;', '&')
                if video.startswith('//'):
                    video = 'https:' + video
                elif video.startswith('/'):
                    video = self.host + video
            
            vod = {
                'vod_id': ids[0],
                'vod_name': title,
                'vod_pic': poster,  # 如果有就顯示，沒有就空著
                'vod_remarks': '',
                'vod_actor': '',
                'vod_director': '',
                'vod_content': '',
                'vod_play_from': 'MissAVt',
                'vod_play_url': f'{title}${video}' if video else f'{title}$'
            }
            result['list'].append(vod)
        return result

    def searchContent(self, key, quick):
        result = {'list': []}
        url = f'{self.host}/search/{key}/'
        r = self.fetch(url, headers=self.headers)
        if r:
            html = self._get_html(r)
            match = re.search(r'<ul[^>]*class="video-items[^"]*"[^>]*>(.*?)</ul>', html, re.S)
            if match:
                items = re.findall(r'<li>(.*?)</li>', match.group(1), re.S)
                for item in items:
                    href_match = re.search(r'href="([^"]+)"', item)
                    if not href_match: continue
                    href = href_match.group(1)
                    pic_match = re.search(r'data-src="([^"]+)"', item)
                    pic = pic_match.group(1) if pic_match else ''
                    title_match = re.search(r'<a[^>]*class="[^"]*my-1[^"]*"[^>]*>(.*?)</a>', item, re.S)
                    if title_match:
                        title = title_match.group(1).strip()
                        title = re.sub(r'^\d+:\d+:\d+\s*', '', title)
                        result['list'].append({'vod_id': href, 'vod_name': title, 'vod_pic': pic, 'vod_remarks': ''})
        return result

    def playerContent(self, flag, id, vipFlags):
        return {'parse': 0, 'playUrl': '', 'url': id}