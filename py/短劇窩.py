# -*- coding: utf-8 -*-
import re
import requests

class Spider:
    host = 'https://www.idjw.cc'
    
    def getDependence(self):
        return ['requests']
    
    def init(self, extend):
        pass
    
    def getName(self):
        return "短剧窝"
    
    # --- 分类列表 (从导航栏提取) ---
    def homeContent(self, filter):
        # 注意：这里的分类ID和名称需要根据网站实际导航栏确认
        # 以下是一个示例，您可能需要根据实际页面进行调整
        return {'class': [
            {'type_id': '1', 'type_name': '现代都市'},
            {'type_id': '2', 'type_name': '古装仙侠'},
            {'type_id': '3', 'type_name': '脑洞悬疑'},
            {'type_id': '4', 'type_name': '年代穿越'},
            {'type_id': '5', 'type_name': '女频恋爱'},
            {'type_id': '20', 'type_name': '反转爽剧'}
        ]}
    
    # --- 首页推荐视频 ---
    def homeVideoContent(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(self.host, headers=headers, timeout=10)
            html = r.text
            videos = []
            seen = set()
            # 匹配视频项：注意路径是 /vod/数字/
            pattern = r'<li[^>]*class="col-4[^"]*"[^>]*>.*?<a[^>]+href="/vod/(\d+)/"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<h4[^>]*>.*?<a[^>]+>([^<]+)</a>'
            matches = re.findall(pattern, html, re.S)
            for match in matches:
                if len(match) >= 3:
                    vod_id, vod_pic, vod_name = match[0], match[1], match[2].strip()
                    if 'logo' not in vod_pic and vod_id not in seen:
                        seen.add(vod_id)
                        videos.append({'vod_id': vod_id, 'vod_name': vod_name, 'vod_pic': vod_pic, 'vod_remarks': '短剧'})
            return {'list': videos[:50]}
        except:
            return {'list': []}
    
    # --- 分类页视频 (带分页) ---
    def categoryContent(self, tid, pg, filter, extend):
        try:
            # 构建分类页URL，分页格式可能需要根据网站调整，例如 /show/{tid}--------{pg}---.html 或 /list/{tid}-{pg}/
            # 这里先使用一个常见格式，您可能需要根据实际页面调整
            url = f'{self.host}/show/{tid}--------{pg}---.html'
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            html = r.text
            videos = []
            seen = set()
            pattern = r'<li[^>]*class="col-4[^"]*"[^>]*>.*?<a[^>]+href="/vod/(\d+)/"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<h4[^>]*>.*?<a[^>]+>([^<]+)</a>'
            matches = re.findall(pattern, html, re.S)
            for match in matches:
                if len(match) >= 3:
                    vod_id, vod_pic, vod_name = match[0], match[1], match[2].strip()
                    if 'logo' not in vod_pic and vod_id not in seen:
                        seen.add(vod_id)
                        videos.append({'vod_id': vod_id, 'vod_name': vod_name, 'vod_pic': vod_pic, 'vod_remarks': '短剧'})
            # 尝试获取总页数，需要根据实际分页HTML调整
            page_matches = re.findall(r'href=".*?/show/.*?/(\d+)\.html"', html) # 示例正则
            pagecount = max([int(p) for p in page_matches]) if page_matches else 1
            return {'list': videos, 'page': int(pg), 'pagecount': pagecount, 'limit': 30, 'total': len(videos)}
        except:
            return {'list': [], 'page': int(pg), 'pagecount': 0, 'limit': 30, 'total': 0}
    
    # --- 视频详情页 ---
    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            url = f'{self.host}/vod/{vod_id}/'
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            html = r.text
            
            title = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
            vod_name = title.group(1).strip() if title else ''
            
            status = re.search(r'状态[：:]([^<]+)', html)
            vod_remarks = status.group(1).strip() if status else ''
            
            pic = re.search(r'<div[^>]*class="[^"]*vod-pic[^"]*"[^>]*>.*?<img[^>]+src="([^"]+)"', html, re.S)
            if not pic:
                pic = re.search(r'<img[^>]+src="([^"]+)"[^>]*alt="[^"]*"', html)
            vod_pic = pic.group(1) if pic and 'logo' not in pic.group(1) else ''
            
            desc = re.search(r'<div[^>]*class="[^"]*card-body[^"]*"[^>]*>\s*<p[^>]*>([^<]+)</p>', html, re.S)
            vod_content = desc.group(1).strip() if desc else '暂无简介'
            
            # 构建播放页地址，格式通常为 /play/数字-1-1/
            play_url = f'{self.host}/play/{vod_id}-1-1/'
            
            return {'list': [{
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_remarks': vod_remarks,
                'vod_content': vod_content,
                'vod_play_from': '短剧窝',
                'vod_play_url': f'播放${play_url}'
            }]}
        except:
            return {'list': []}
    
    # --- 搜索功能 (URL格式需要根据网站调整) ---
    def searchContent(self, key, quick, pg=1):
        try:
            # 搜索URL可能需要根据网站实际格式调整，例如 /search/{key}----------{pg}---.html
            url = f'{self.host}/search/{key}----------{pg}---.html'
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            html = r.text
            videos = []
            seen = set()
            # 匹配搜索结果中的视频项
            pattern = r'<li[^>]*class="col-4[^"]*"[^>]*>.*?<a[^>]+href="/vod/(\d+)/"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<h4[^>]*>.*?<a[^>]+>([^<]+)</a>'
            matches = re.findall(pattern, html, re.S)
            for match in matches:
                if len(match) >= 3:
                    vod_id, vod_pic, vod_name = match[0], match[1], match[2].strip()
                    if vod_id not in seen:
                        seen.add(vod_id)
                        videos.append({'vod_id': vod_id, 'vod_name': vod_name, 'vod_pic': vod_pic, 'vod_remarks': '短剧'})
            # 尝试获取搜索总页数
            page_matches = re.findall(r'href=".*?/search/.*?/(\d+)\.html"', html)
            pagecount = max([int(p) for p in page_matches]) if page_matches else 1
            return {'list': videos, 'page': int(pg), 'pagecount': pagecount, 'limit': 30, 'total': len(videos)}
        except:
            return {'list': [], 'page': int(pg), 'pagecount': 0, 'limit': 30, 'total': 0}
    
    # --- 播放器 (使用WebView) ---
    def playerContent(self, flag, id, vipFlags):
        return {'parse': 1, 'url': id, 'header': {'User-Agent': 'Mozilla/5.0', 'Referer': self.host}}
    
    def isVideoFormat(self, url):
        return False
    
    def localProxy(self, params):
        return []