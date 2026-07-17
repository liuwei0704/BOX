# -*- coding: utf-8 -*-
import re
import urllib.parse
from urllib.request import urlopen, Request
import json
import gzip

class Spider:
    def __init__(self):
        self.base = 'https://hel.heilrj6.sbs'
        self.path = '/hl'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.base + self.path + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.classes = [
            {'type_id': '241', 'type_name': '无码专区'},
            {'type_id': '256', 'type_name': '侵犯专区'},
            {'type_id': '265', 'type_name': '约炮探花'},
            {'type_id': '269', 'type_name': '人妻极品'},
            {'type_id': '234', 'type_name': '国产视频'},
            {'type_id': '268', 'type_name': '强奸极品'},
            {'type_id': '259', 'type_name': '女同专区'},
            {'type_id': '254', 'type_name': '明星换脸'},
            {'type_id': '248', 'type_name': '欧美专区'},
            {'type_id': '247', 'type_name': 'AV解说'},
            {'type_id': '266', 'type_name': '极品学妹'},
            {'type_id': '240', 'type_name': '中文字幕'},
            {'type_id': '258', 'type_name': 'SM专区'},
            {'type_id': '245', 'type_name': '日韩专区'},
            {'type_id': '267', 'type_name': '乱伦极品'},
            {'type_id': '257', 'type_name': '家庭伦伦'},
            {'type_id': '271', 'type_name': '独家调教'},
            {'type_id': '249', 'type_name': '网曝门事件'},
            {'type_id': '270', 'type_name': '制服极品'},
            {'type_id': '246', 'type_name': '精品动漫'},
            {'type_id': '238', 'type_name': '性感主播'},
            {'type_id': '237', 'type_name': '国产乱伦'},
            {'type_id': '236', 'type_name': '传媒视频'},
            {'type_id': '239', 'type_name': '伦理三级'},
            {'type_id': '242', 'type_name': 'VR专区'},
            {'type_id': '244', 'type_name': '明星淫梦'},
            {'type_id': '253', 'type_name': '强奸乱伦'},
        ]
        # 空筛选器
        self.filters = {}

    def fetch(self, url):
        try:
            req = Request(url, headers=self.headers)
            response = urlopen(req, timeout=15)
            data = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                data = gzip.decompress(data)
            return data.decode('utf-8', errors='ignore')
        except:
            return None

    def fix(self, u):
        if not u:
            return ''
        if u.startswith('//'):
            return 'https:' + u
        if u.startswith('/'):
            return self.base + u
        if not u.startswith('http'):
            return self.base + self.path + '/' + u.lstrip('/')
        return u

    def parse_videos(self, html):
        res = []
        start = 0
        while True:
            idx = html.find('stui-vodlist__box', start)
            if idx == -1:
                break
            div_start = html.rfind('<div', 0, idx)
            if div_start == -1:
                start = idx + 1
                continue
            div_end = html.find('</div>', idx)
            if div_end == -1:
                break
            box = html[div_start:div_end + 6]
            start = div_end + 1
            
            href_start = box.find('href="')
            if href_start == -1:
                href_start = box.find("href='")
                if href_start == -1:
                    continue
                href_start += 6
                href_end = box.find("'", href_start)
            else:
                href_start += 6
                href_end = box.find('"', href_start)
            if href_end == -1:
                continue
            link = box[href_start:href_end]
            
            title_start = box.find('title="')
            if title_start == -1:
                title_start = box.find("title='")
                if title_start == -1:
                    continue
                title_start += 7
                title_end = box.find("'", title_start)
            else:
                title_start += 7
                title_end = box.find('"', title_start)
            if title_end == -1:
                continue
            title = box[title_start:title_end]
            
            pic = ''
            pic_start = box.find('data-original="')
            if pic_start == -1:
                pic_start = box.find("data-original='")
                if pic_start != -1:
                    pic_start += 15
                    pic_end = box.find("'", pic_start)
                    if pic_end != -1:
                        pic = box[pic_start:pic_end]
            else:
                pic_start += 15
                pic_end = box.find('"', pic_start)
                if pic_end != -1:
                    pic = box[pic_start:pic_end]
            
            remark = ''
            span_start = box.find('pic-text')
            if span_start != -1:
                gt = box.find('>', span_start)
                if gt != -1:
                    span_end = box.find('</span>', gt)
                    if span_end != -1:
                        remark = box[gt+1:span_end].strip()
            
            vid = re.search(r'/vod/(?:detail|play)/id/(\d+)', link)
            if vid:
                res.append({
                    'vod_id': vid.group(1),
                    'vod_name': title.strip(),
                    'vod_pic': self.fix(pic),
                    'vod_remarks': remark
                })
        return res

    def get_pagecount(self, html):
        m = re.search(r'(\d+)/(\d+)', html)
        if m:
            return int(m.group(2))
        m = re.search(r'共(\d+)页', html)
        if m:
            return int(m.group(1))
        return 1

    def init(self, extend=None):
        pass

    def getDependence(self):
        return []

    def destroy(self):
        pass

    # 标准 homeContent 接口
    def homeContent(self, filter=False):
        return {'class': self.classes, 'filters': self.filters}

    # 兼容别名（某些 APP 可能需要）
    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self.fetch(self.base + self.path + '/')
        if not html:
            return {'list': []}
        return {'list': self.parse_videos(html)[:20]}

    def categoryContent(self, tid, pg=1, filter=False, extend=None):
        tid = str(tid)
        pg = int(pg)
        if pg == 1:
            url = f'{self.base}{self.path}/index.php/vod/type/id/{tid}.html'
        else:
            url = f'{self.base}{self.path}/index.php/vod/type/id/{tid}/page/{pg}.html'
        html = self.fetch(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 20, 'total': 0}
        return {
            'list': self.parse_videos(html),
            'page': pg,
            'pagecount': self.get_pagecount(html),
            'limit': 20,
            'total': 0
        }

    def detailContent(self, ids):
        if not ids:
            return {'list': []}
        vod_id = str(ids[0])
        
        url = f'{self.base}{self.path}/index.php/vod/detail/id/{vod_id}.html'
        html = self.fetch(url)
        
        r = {
            'vod_id': vod_id,
            'vod_name': '',
            'vod_pic': '',
            'vod_content': '',
            'vod_play_from': '线路',
            'vod_play_url': ''
        }
        
        if html:
            m = re.search(r'<h1[^>]*?class="title"[^>]*?>([^<]+)</h1>', html)
            if m:
                r['vod_name'] = m.group(1).strip()
            
            m = re.search(r'data-original="([^"]+)"', html)
            if m:
                r['vod_pic'] = self.fix(m.group(1))
            
            m = re.search(r'简介：\s*([^<]+)', html)
            if m:
                r['vod_content'] = m.group(1).strip()
        
        play_url = f'{self.base}{self.path}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html'
        r['vod_play_url'] = play_url
        
        return {'list': [r]}

    def searchContent(self, key, quick=False, pg=1):
        if not key:
            return {'list': [], 'pagecount': 0}
        key = urllib.parse.quote(key)
        url = f'{self.base}{self.path}/index.php/vod/search.html?wd={key}'
        if int(pg) > 1:
            url += f'&page={pg}'
        html = self.fetch(url)
        if not html:
            return {'list': [], 'pagecount': 0}
        return {'list': self.parse_videos(html), 'pagecount': self.get_pagecount(html)}

    def playerContent(self, flag, id, vipFlags=None):
        if not id:
            return {'parse': 1, 'url': ''}
        
        media_header = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': self.base + self.path + '/'
        }
        
        if id.startswith('http') and ('.m3u8' in id or '.mp4' in id):
            return {'parse': 0, 'url': id, 'header': json.dumps(media_header)}
        
        return {'parse': 1, 'url': id, 'header': json.dumps(media_header)}

    def localProxy(self, params):
        pass