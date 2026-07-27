# coding: utf-8
# 私欲阁 - ninimen.sbs

import re
import json
import urllib.parse

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from base.spider import Spider as BaseSpider

def _fix_url(url):
    if not url:
        return ''
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return 'https://ninimen.sbs' + url
    return url

class Spider(BaseSpider):
    def __init__(self):
        self.host = 'https://ninimen.sbs'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host + '/'
        }
        self.classes = [
            {'type_id': '6', 'type_name': '中文字幕'},
            {'type_id': '7', 'type_name': '无码专区'},
            {'type_id': '8', 'type_name': '欧美大全'},
            {'type_id': '9', 'type_name': '国产高清'},
            {'type_id': '10', 'type_name': '日韩视频'},
            {'type_id': '11', 'type_name': '香港三级'},
            {'type_id': '12', 'type_name': '动漫精品'},
            {'type_id': '13', 'type_name': '素人合集'}
        ]
        self.filters = {}

    def getName(self):
        return '私欲阁'

    def getDependence(self):
        return []

    def init(self, extend=''):
        pass

    def homeContent(self, filter=False):
        return {'class': self.classes, 'filters': self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        if BeautifulSoup is None:
            return {'list': []}
        try:
            html = self.fetch(self.host, headers=self.headers).text
            soup = BeautifulSoup(html, 'html.parser')
            items = []
            for card in soup.select('div.col-md-3.resent-grid.recommended-grid'):
                a = card.select_one('a')
                img = card.select_one('img.lazy')
                title_el = card.select_one('h5 a.title')
                duration_el = card.select_one('p.duration-time')
                if a and img and title_el:
                    vid = a.get('href', '').replace('/voddetail/', '').replace('.html', '')
                    if vid:
                        items.append({
                            'vod_id': vid,
                            'vod_name': title_el.text.strip(),
                            'vod_pic': img.get('data-original') or img.get('src', ''),
                            'vod_remarks': duration_el.text.strip() if duration_el else ''
                        })
            return {'list': items[:20]}
        except Exception as e:
            return {'list': []}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        if BeautifulSoup is None:
            return {'list': [], 'page': 1, 'pagecount': 1, 'limit': 20, 'total': 0}
        page = int(pg) if pg else 1
        url = f"{self.host}/vodtype/{tid}.html" if page == 1 else f"{self.host}/vodtype/{tid}-{page}.html"
        try:
            html = self.fetch(url, headers=self.headers).text
            soup = BeautifulSoup(html, 'html.parser')
            items = []
            for card in soup.select('div.col-md-3.resent-grid.recommended-grid'):
                a = card.select_one('a')
                img = card.select_one('img.lazy')
                title_el = card.select_one('h5 a.title')
                duration_el = card.select_one('p.duration-time')
                if a and img and title_el:
                    vid = a.get('href', '').replace('/voddetail/', '').replace('.html', '')
                    if vid:
                        items.append({
                            'vod_id': vid,
                            'vod_name': title_el.text.strip(),
                            'vod_pic': img.get('data-original') or img.get('src', ''),
                            'vod_remarks': duration_el.text.strip() if duration_el else ''
                        })
            pagecount = 10
            pagination = soup.select('.pagination a, .page a, a[href*="-"]')
            max_pg = 1
            for link in pagination:
                href = link.get('href', '')
                m = re.search(r'-(\d+)\.html$', href)
                if m:
                    pg_num = int(m.group(1))
                    if pg_num > max_pg:
                        max_pg = pg_num
            if max_pg > 1:
                pagecount = max_pg
            return {
                'list': items,
                'page': page,
                'pagecount': pagecount,
                'limit': 20,
                'total': pagecount * 20
            }
        except Exception as e:
            return {'list': [], 'page': page, 'pagecount': 1, 'limit': 20, 'total': 0}

    def detailContent(self, ids):
        if not ids:
            return {'list': []}
        vid = str(ids[0])
        name = ''
        pic = ''
        remark = ''
        play_page = f'/vodplay/{vid}-1-1.html'
        if '|$|' in vid:
            parts = vid.split('|$|')
            vid = parts[0]
            name = parts[1] if len(parts) > 1 else ''
            pic = parts[2] if len(parts) > 2 else ''
            remark = parts[3] if len(parts) > 3 else ''
            play_page = parts[4] if len(parts) > 4 else f'/vodplay/{vid}-1-1.html'
        if BeautifulSoup is not None:
            try:
                html = self.fetch(_fix_url(f'/voddetail/{vid}.html'), headers=self.headers).text
                soup = BeautifulSoup(html, 'html.parser')
                title_el = soup.select_one('h3.text-center')
                if title_el and not name:
                    name = title_el.text.strip()
                img_el = soup.select_one('img.detail-img')
                if img_el and not pic:
                    pic = img_el.get('src', '')
                remark_el = soup.select_one('p span')
                if remark_el and not remark:
                    remark = remark_el.text.strip()
            except:
                pass
        vod = {
            'vod_id': vid,
            'vod_name': name or '视频',
            'vod_pic': pic,
            'vod_remarks': remark,
            'vod_content': remark,
            'vod_play_from': '播放',
            'vod_play_url': f'播放${play_page}'
        }
        return {'list': [vod]}

    def searchContent(self, key, quick, pg='1'):
        if BeautifulSoup is None:
            return {'list': []}
        try:
            data = {'wd': key, 'submit': ''}
            html = self.post(f'{self.host}/vodsearch/-------------.html', data=data, headers=self.headers).text
            soup = BeautifulSoup(html, 'html.parser')
            items = []
            for card in soup.select('div.col-md-3.resent-grid.recommended-grid'):
                a = card.select_one('a')
                img = card.select_one('img.lazy')
                title_el = card.select_one('h5 a.title')
                if a and img and title_el:
                    vid = a.get('href', '').replace('/voddetail/', '').replace('.html', '')
                    if vid:
                        items.append({
                            'vod_id': vid,
                            'vod_name': title_el.text.strip(),
                            'vod_pic': img.get('data-original') or img.get('src', ''),
                            'vod_remarks': ''
                        })
            return {'list': items, 'page': 1}
        except Exception as e:
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        # 构建播放页URL
        if id.startswith('http'):
            play_url = id
        elif id.startswith('/'):
            play_url = self.host + id
        else:
            play_url = self.host + f'/vodplay/{id}-1-1.html'

        try:
            html = self.fetch(play_url, headers=self.headers).text

            # 方式1: player_aaaa 变量 (encrypt=0 直链) - 参考18AV模式
            # 用正则直接提取url字段，避免JSON解析转义问题
            m = re.search(r'player_aaaa\s*=\s*\{[^}]*"url"\s*:\s*"([^"]+)"', html)
            if m:
                url = m.group(1).replace('\\/', '/')
                if url and ('.m3u8' in url or '.mp4' in url):
                    return {'parse': 0, 'url': url, 'header': self.headers}

            # 方式2: MacPlayer.PlayUrl
            m = re.search(r'MacPlayer\s*\.\s*PlayUrl\s*=\s*["\']([^"\']+)["\']', html)
            if m:
                url = m.group(1)
                if url and ('.m3u8' in url or '.mp4' in url):
                    return {'parse': 0, 'url': url, 'header': self.headers}

            # 方式3: var now
            m = re.search(r'var\s+now\s*=\s*["\']([^"\']+)["\']', html)
            if m:
                url = m.group(1)
                if url and ('.m3u8' in url or '.mp4' in url):
                    return {'parse': 0, 'url': url, 'header': self.headers}

            # 方式4: iframe 嵌套
            m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
            if m:
                iframe_url = m.group(1)
                if 'm3u8' in iframe_url or 'mp4' in iframe_url:
                    return {'parse': 0, 'url': iframe_url, 'header': self.headers}
                if 'aojiexi' in iframe_url:
                    m2 = re.search(r'url=([^&]+)', iframe_url)
                    if m2:
                        real_url = urllib.parse.unquote(m2.group(1))
                        if real_url:
                            return {'parse': 0, 'url': real_url, 'header': self.headers}

            # 方式5: 直接匹配 m3u8 链接
            m = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
            if m:
                return {'parse': 0, 'url': m.group(1), 'header': self.headers}

        except Exception as e:
            pass

        # 无法提取直链，降级嗅探
        return {'parse': 1, 'url': play_url, 'header': self.headers}

    def localProxy(self, param):
        return []

    def isVideoFormat(self, url):
        return bool(re.search(r'\.(m3u8|mp4|ts)(\?|$)', url, re.I))