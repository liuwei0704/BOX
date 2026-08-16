# -*- coding: utf-8 -*-
import re
import requests

class Spider:
    host = 'https://www.djfen.cc'
    
    def getDependence(self):
        return ['requests']
    
    def init(self, extend):
        pass
    
    def getName(self):
        return "短剧粉"
    
    def homeContent(self, filter):
        return {'class': [
            {'type_id': '21', 'type_name': '现代都市'},
            {'type_id': '2', 'type_name': '女频恋爱'},
            {'type_id': '3', 'type_name': '反转爽剧'},
            {'type_id': '5', 'type_name': '年代穿越'},
            {'type_id': '4', 'type_name': '脑洞悬疑'},
            {'type_id': '20', 'type_name': '古装仙侠'}
        ]}
    
    def homeVideoContent(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(self.host, headers=headers, timeout=10)
            html = r.text
            videos = []
            seen = set()
            pattern = r'<li[^>]*class="col-4[^"]*"[^>]*>.*?<a[^>]+href="/duanju/(\d+)/"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<h4[^>]*>.*?<a[^>]+>([^<]+)</a>'
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
    
    def categoryContent(self, tid, pg, filter, extend):
        try:
            url = f'{self.host}/list/{tid}/' if int(pg) == 1 else f'{self.host}/list/{tid}-{pg}/'
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            html = r.text
            videos = []
            seen = set()
            pattern = r'<li[^>]*class="col-4[^"]*"[^>]*>.*?<a[^>]+href="/duanju/(\d+)/"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<h4[^>]*>.*?<a[^>]+>([^<]+)</a>'
            matches = re.findall(pattern, html, re.S)
            for match in matches:
                if len(match) >= 3:
                    vod_id, vod_pic, vod_name = match[0], match[1], match[2].strip()
                    if 'logo' not in vod_pic and vod_id not in seen:
                        seen.add(vod_id)
                        videos.append({'vod_id': vod_id, 'vod_name': vod_name, 'vod_pic': vod_pic, 'vod_remarks': '短剧'})
            page_matches = re.findall(r'href="/list/\d+-(\d+)/"', html)
            pagecount = max([int(p) for p in page_matches]) if page_matches else 1
            return {'list': videos, 'page': int(pg), 'pagecount': pagecount, 'limit': 30, 'total': len(videos)}
        except:
            return {'list': [], 'page': int(pg), 'pagecount': 0, 'limit': 30, 'total': 0}
    
    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            url = f'{self.host}/duanju/{vod_id}/'
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
            
            play_url = f'{self.host}/play/{vod_id}-1-1/'
            
            return {'list': [{
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_remarks': vod_remarks,
                'vod_content': vod_content,
                'vod_play_from': '短剧粉',
                'vod_play_url': f'播放${play_url}'
            }]}
        except:
            return {'list': []}
    
    def searchContent(self, key, quick, pg=1):
        try:
            url = f'{self.host}/search/{key}--/page/{pg}/'
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            html = r.text
            
            videos = []
            seen = set()
            
            pattern = r'<li[^>]*class="col-4[^"]*"[^>]*>.*?<a[^>]+href="/duanju/(\d+)/"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<h4[^>]*>.*?<a[^>]+>([^<]+)</a>.*?<p[^>]*>.*?<span[^>]*>([^<]+)</span>.*?(\d{4})/([^<]+)'
            matches = re.findall(pattern, html, re.S)
            
            for match in matches:
                if len(match) >= 6:
                    vod_id = match[0]
                    vod_pic = match[1]
                    vod_name = match[2].strip()
                    score = match[3]
                    year = match[4]
                    
                    if vod_id not in seen:
                        seen.add(vod_id)
                        videos.append({
                            'vod_id': vod_id,
                            'vod_name': vod_name,
                            'vod_pic': vod_pic,
                            'vod_remarks': f'{year} {score}分'
                        })
            
            page_matches = re.findall(r'href="/search/[^"]+/page/(\d+)/"', html)
            pagecount = max([int(p) for p in page_matches]) if page_matches else 1
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 30,
                'total': len(videos)
            }
        except:
            return {'list': [], 'page': int(pg), 'pagecount': 0, 'limit': 30, 'total': 0}
    
    def playerContent(self, flag, id, vipFlags):
        return {'parse': 1, 'url': id, 'header': {'User-Agent': 'Mozilla/5.0', 'Referer': self.host}}
    
    def isVideoFormat(self, url):
        return False
    
    def localProxy(self, params):
        return []