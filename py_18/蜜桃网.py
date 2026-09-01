# -*- coding: utf-8 -*-
import re
import json
import base64
import urllib.parse
from bs4 import BeautifulSoup
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


class Spider:
    def __init__(self):
        self.host = "https://mdw2.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.host + '/',
            'Cookie': 'ageVerified=true',
        }
        # 图片解密密钥 (从 app.config.js 中提取)
        self.image_key = b"f5d965df75336270"
        self.image_iv = b"97b60394abc2fbe1"
        self.classes = [
            {"type_id": "mitaoremen", "type_name": "蜜桃热门"},
            {"type_id": "wanghuang", "type_name": "蜜桃网黄"},
            {"type_id": "cg", "type_name": "原创大片"},
            {"type_id": "gaoqingav", "type_name": "高清AV"},
            {"type_id": "tan-hua-da-shen", "type_name": "探花大神"},
            {"type_id": "ou-mei-xi-lie", "type_name": "欧美系列"},
            {"type_id": "ce-pai-chao-di", "type_name": "厕拍抄底"},
            {"type_id": "jian-kong-po-jie", "type_name": "监控破解"},
        ]
        self.filters = {}

    def fetch(self, url, headers=None, timeout=15):
        try:
            headers = headers or self.headers
            resp = requests.get(url, headers=headers, timeout=timeout)
            return resp
        except Exception as e:
            print('fetch error:', e)
            return None

    def get_html(self, url, headers=None):
        resp = self.fetch(url, headers)
        if resp and resp.status_code == 200:
            return resp.text
        return None

    def fix_url(self, url):
        if not url:
            return ''
        url = url.strip()
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host.rstrip('/') + url
        return self.host.rstrip('/') + '/' + url.lstrip('/')

    def decrypt_image(self, encrypted_data):
        """AES-CBC解密图片"""
        try:
            cipher = AES.new(self.image_key, AES.MODE_CBC, self.image_iv)
            decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            return decrypted
        except Exception as e:
            return None

    def fetch_and_decrypt_image(self, pic_url):
        """下载加密图片 -> 解密 -> 返回 data:image"""
        if not pic_url:
            return ''
        try:
            headers = {
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.host + '/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            }
            resp = requests.get(pic_url, headers=headers, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 0:
                decrypted = self.decrypt_image(resp.content)
                if decrypted:
                    if decrypted.startswith(b'\xff\xd8\xff'):
                        mime = 'image/jpeg'
                    elif decrypted.startswith(b'\x89PNG'):
                        mime = 'image/png'
                    elif decrypted.startswith(b'GIF8'):
                        mime = 'image/gif'
                    else:
                        mime = 'image/jpeg'
                    b64 = base64.b64encode(decrypted).decode()
                    return f'data:{mime};base64,{b64}'
            return ''
        except Exception as e:
            return ''

    def _make_proxy_url(self, pic_url):
        """生成代理图片URL"""
        if not pic_url:
            return ''
        encoded = urllib.parse.quote(pic_url, safe="")
        return f'http://127.0.0.1:9978/proxy?do=py&type=img&url={encoded}'

    def _extract_vod_id(self, url):
        if not url:
            return ''
        m = re.search(r'/archives/(\d+)/', url)
        if m:
            return m.group(1)
        m = re.search(r'/archives/(\d+)', url)
        if m:
            return m.group(1)
        return url

    def _parse_list_items(self, html, limit=999):
        doc = BeautifulSoup(html, 'html.parser')
        videos = []
        for item in doc.find_all('div', class_='xqbj-list-rows'):
            a = item.find('a', href=True)
            if not a:
                continue
            href = a.get('href', '')
            if '/archives/' not in href:
                continue
            vid = self._extract_vod_id(href)

            title = ''
            title_el = item.find('h3', class_='xqbj-list-rows-image-title')
            if title_el:
                title = title_el.text.strip()
            if not title:
                title = a.get('title', '') or a.text.strip()

            pic = ''
            img = item.find('img')
            if img:
                pic = img.get('z-image-loader-url') or img.get('src') or img.get('data-src', '')
                if pic:
                    pic = pic.strip('`')
                    pic = self.fix_url(pic)
                    if pic:
                        # 列表页使用代理URL，由 localProxy 解密
                        pic = self._make_proxy_url(pic)

            remark = ''
            bottom_tags = item.find('div', class_='xqbj-list-rows-bottom-tags')
            if bottom_tags:
                view_el = bottom_tags.find('div', class_='xqbj-icon-view')
                if view_el:
                    parent = view_el.find_parent('a')
                    if parent:
                        text = parent.text.strip()
                        if 'K' in text or '+' in text:
                            remark = text
                if not remark:
                    comm_el = bottom_tags.find('div', class_='xqbj-icon-comm')
                    if comm_el:
                        parent = comm_el.find_parent('a')
                        if parent:
                            text = parent.text.strip()
                            if text.isdigit() or '+' in text:
                                remark = text + '评论'
            if not remark:
                time_el = item.find('div', class_='xqbj-icon-time')
                if time_el:
                    parent = time_el.find_parent('div', class_='xqbj-list-rows-bottom-tags-tag')
                    if parent:
                        text = parent.text.strip()
                        if text:
                            remark = text

            if vid and title:
                videos.append({
                    'vod_id': vid,
                    'vod_name': title,
                    'vod_pic': pic or '',
                    'vod_remarks': remark or ''
                })
                if len(videos) >= limit:
                    break
        return videos
    def _parse_pagecount(self, html):
        doc = BeautifulSoup(html, 'html.parser')
        pagination = doc.find('nav', class_='van-pagination1')
        if pagination:
            max_page = 1
            for a in pagination.find_all('a'):
                text = a.text.strip()
                if text.isdigit():
                    num = int(text)
                    if num > max_page:
                        max_page = num
            for li in pagination.find_all('li', class_='total'):
                a = li.find('a')
                if a:
                    text = a.text.strip()
                    if text.isdigit():
                        num = int(text)
                        if num > max_page:
                            max_page = num
            return max_page
        max_page = 1
        for a in doc.find_all('a', href=True):
            href = a.get('href', '')
            m = re.search(r'/category/[^/]+/(\d+)/', href)
            if m:
                num = int(m.group(1))
                if num > max_page:
                    max_page = num
        return max_page

    def _get_play_url(self, vid):
        """根据视频ID获取最新播放地址"""
        if not vid or not str(vid).isdigit():
            return None
        url = self.host + '/archives/' + str(vid) + '/'
        html = self.get_html(url)
        if not html:
            return None
        player_el = BeautifulSoup(html, 'html.parser').find('div', class_='videoplayer')
        if player_el:
            config_str = player_el.get('data-config', '')
            if config_str:
                try:
                    config = json.loads(config_str)
                    if 'video' in config and 'url' in config['video']:
                        play_url = config['video']['url']
                        if play_url and '.m3u8' in play_url:
                            # 移除 v=3 和 time=0 参数
                            if '&v=3' in play_url:
                                play_url = play_url.split('&v=3')[0]
                            if '&time=' in play_url:
                                play_url = play_url.split('&time=')[0]
                            return play_url
                except:
                    pass
        return None
    def getName(self):
        return '蜜桃网'

    def init(self, extend=''):
        pass

    def destroy(self):
        pass

    def getDependence(self):
        return ['requests', 'bs4', 'Crypto']

    def homeContent(self, filter=False):
        result = {'class': self.classes, 'filters': self.filters if filter else {}}
        html = self.get_html(self.host + '/')
        if html:
            result['list'] = self._parse_list_items(html, 12)
        else:
            result['list'] = []
        return result

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            result = self.categoryContent('mitaoremen', 1, False, None)
            return {'list': result.get('list', [])[:12]}
        except Exception as e:
            print('homeVideoContent error:', e)
            return {'list': []}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        pg = int(pg) if pg else 1
        url = self.host + '/category/' + tid + '/'
        if pg > 1:
            url = self.host + '/category/' + tid + '/' + str(pg) + '/'
        html = self.get_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}
        videos = self._parse_list_items(html)
        pagecount = self._parse_pagecount(html)
        return {
            'list': videos,
            'page': pg,
            'pagecount': pagecount,
            'limit': 20,
            'total': pagecount * 20
        }

    def detailContent(self, ids):
        if not ids:
            return {'list': []}
        vid = str(ids[0])
        url = self.host + '/archives/' + vid + '/'
        html = self.get_html(url)
        if not html:
            return {'list': []}

        doc = BeautifulSoup(html, 'html.parser')

        # 提取标题
        title = ''
        title_el = doc.find('h1', class_='novel-title')
        if title_el:
            title = title_el.text.strip()
        if not title:
            title_el = doc.find('h1')
            if title_el:
                title = title_el.text.strip()

        # 提取描述
        desc = ''
        content_el = doc.find('div', class_='text-content')
        if content_el:
            for p in content_el.find_all('p'):
                text = p.text.strip()
                if text and not text.startswith('关键词：') and not text.startswith('⬇️'):
                    if len(text) > 10:
                        desc += text + '\n'
            desc = desc.strip()

        # 不获取任何图片，vod_pic 留空
        data = {
            'vod_id': vid,
            'vod_name': title or '未知视频',
            'vod_pic': '',  # 不获取图片
            'vod_content': desc or '',
            'vod_play_from': '默认线路',
            'vod_play_url': '默认线路$' + vid,
        }
        return {'list': [data]}
    def searchContent(self, key, quick=False, pg='1'):
        if not key:
            return {'list': [], 'page': 1, 'pagecount': 1, 'total': 0}
        pg = int(pg) if pg else 1
        url = self.host + '/search/' + urllib.parse.quote(key) + '/'
        if pg > 1:
            url = self.host + '/search/' + urllib.parse.quote(key) + '/' + str(pg) + '/'
        html = self.get_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}
        videos = self._parse_list_items(html)
        pagecount = self._parse_pagecount(html)
        return {
            'list': videos,
            'page': pg,
            'pagecount': pagecount,
            'total': pagecount * 20
        }

    def playerContent(self, flag, id, vipFlags=None):
        if not id:
            return {'parse': 1, 'url': ''}

        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': self.host + '/',
        }

        # 解析视频ID
        vid = str(id)
        if '$' in vid:
            parts = vid.split('$')
            if len(parts) >= 2:
                vid = parts[-1]
        if '播放$' in id:
            vid = id.split('播放$')[1]
        elif '默认线路$' in id:
            vid = id.split('默认线路$')[1]

        # 使用 parse:1 让 WebView 加载播放页
        if str(vid).isdigit():
            # 尝试多种 embed 参数，让页面只加载播放器
            play_url = self.host + '/archives/' + str(vid) + '/?embed=1&noheader=1&play=1'
            return {'parse': 1, 'url': play_url, 'header': headers}

        if id.startswith('http'):
            return {'parse': 1, 'url': id, 'header': headers}

        return {'parse': 1, 'url': id, 'header': headers}
    def localProxy(self, params):
        """图片代理 - 解密加密图片"""
        try:
            if isinstance(params, dict):
                url = params.get('url', '')
            else:
                url = str(params or '')
                if 'url=' in url:
                    parsed = urllib.parse.urlparse(url)
                    qs = urllib.parse.parse_qs(parsed.query)
                    url = qs.get('url', [''])[0] if qs.get('url') else ''

            if not url:
                return [400, 'text/plain', b'Missing url']

            url = urllib.parse.unquote(url)

            headers = {
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.host + '/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            }
            resp = requests.get(url, headers=headers, timeout=15)

            if resp.status_code == 200 and len(resp.content) > 0:
                decrypted = self.decrypt_image(resp.content)
                if decrypted:
                    if decrypted.startswith(b'\xff\xd8\xff'):
                        content_type = 'image/jpeg'
                    elif decrypted.startswith(b'\x89PNG'):
                        content_type = 'image/png'
                    elif decrypted.startswith(b'GIF8'):
                        content_type = 'image/gif'
                    else:
                        content_type = 'image/jpeg'
                    return [200, content_type, decrypted]
                else:
                    return [200, 'application/octet-stream', resp.content]
            return [404, 'text/plain', b'Image not found']
        except Exception as e:
            print('localProxy error:', e)
            return [500, 'text/plain', f'Proxy error: {str(e)}'.encode()]