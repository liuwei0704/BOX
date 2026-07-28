# -*- coding: utf-8 -*-
import re
import json
import base64
import urllib.parse
import requests
from bs4 import BeautifulSoup
import time


class Spider:
    def __init__(self):
        self.host = "https://hg0.hghome3.sbs"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.host + '/',
            'Cookie': 'ageVerified=true'
        }
        self.classes = [
            {"type_id": "gc", "type_name": "国产"},
            {"type_id": "gcav", "type_name": "国产AV"},
            {"type_id": "rb", "type_name": "日本"},
            {"type_id": "dh", "type_name": "动画"},
            {"type_id": "om", "type_name": "欧美"},
            {"type_id": "comic", "type_name": "图集"},
        ]
        self.filters = {
            "comic": [
                {"key": "category", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    {"n": "怀旧合集", "v": "gchj"},
                    {"n": "泄密合集", "v": "xmhj"},
                    {"n": "博主合集", "v": "gc"}
                ]},
                {"key": "sort", "name": "排序", "value": [
                    {"n": "更新", "v": "updated"},
                    {"n": "热度", "v": "heat"},
                    {"n": "随机", "v": "random"}
                ]}
            ]
        }

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

    def _extract_vod_id(self, url):
        if not url:
            return ''
        m = re.search(r'/videos/([^.]+)\.html', url)
        if m:
            return m.group(1)
        m = re.search(r'group=([^&]+)', url)
        if m:
            return 'group_' + m.group(1)
        m = re.search(r'/comic/([^.]+)\.html', url)
        if m:
            return 'comic_' + m.group(1)
        return url

    def _is_group(self, vid):
        return vid.startswith('group_')

    def _is_comic(self, vid):
        return vid.startswith('comic_')

    def _get_group_id(self, vid):
        return vid[6:] if vid.startswith('group_') else vid

    def _get_comic_id(self, vid):
        return vid[6:] if vid.startswith('comic_') else vid

    def _clean_play_url(self, url):
        if not url:
            return url
        url = url.replace('\\', '')
        if '/unvip/video//unvip/video/' in url:
            url = url.replace('/unvip/video//unvip/video/', '/unvip/video/')
        if '/unvip/video/unvip/video/' in url:
            url = url.replace('/unvip/video/unvip/video/', '/unvip/video/')
        return url

    def _make_proxy_url(self, pic_url):
        if not pic_url:
            return ''
        encoded = base64.b64encode(pic_url.encode()).decode()
        return f'proxy://do=py&site=海狗TV&type=img&url={encoded}'

    def _extract_title(self, fig, a):
        title = ''
        t = fig.find('div', class_=re.compile(r'line-clamp-2|truncate'))
        if t:
            title = t.text.strip()
        if not title:
            title = a.get('title', '') or a.text.strip()
        if title == '动画：' or title.startswith('动画：'):
            full_title = a.get('title', '')
            if full_title and '动画：' not in full_title:
                title = full_title
            else:
                all_text = fig.get_text(separator=' ', strip=True)
                if '动画：' in all_text:
                    parts = all_text.split('动画：', 1)
                    if len(parts) > 1 and parts[1].strip():
                        title = parts[1].strip()
        return title

    def _parse_items(self, items, limit=999):
        videos = []
        for fig in items:
            a = fig.find('a', href=True)
            if not a:
                continue
            href = a.get('href', '')
            if '/videos/' in href:
                vid = self._extract_vod_id(href)
            elif '/group_detail_v2.html' in href:
                vid = self._extract_vod_id(href)
            elif '/comic/' in href:
                vid = self._extract_vod_id(href)
            else:
                continue
            title = self._extract_title(fig, a)
            img = fig.find('img')
            pic = img.get('src') or img.get('data-src', '') if img else ''
            pic = self.fix_url(pic)
            if pic:
                pic = self._make_proxy_url(pic)
            remark = ''
            s = fig.find('span', class_=re.compile(r'absolute|rounded'))
            if s:
                remark = s.text.strip()
            if not remark:
                status = fig.find('span', class_=re.compile(r'bg-green-500'))
                if status:
                    remark = status.text.strip()
            if vid and title:
                videos.append({
                    'vod_id': vid,
                    'vod_name': title,
                    'vod_pic': pic,
                    'vod_remarks': remark
                })
                if len(videos) >= limit:
                    break
        return videos

    def _parse_videos(self, html, limit=15):
        doc = BeautifulSoup(html, 'html.parser')
        items = doc.find_all('figure')
        return self._parse_items(items, limit)

    def homeContent(self, filter=False):
        result = {'class': self.classes, 'filters': self.filters if filter else {}}
        html = self.get_html(self.host + '/home.html')
        if html:
            result['list'] = self._parse_videos(html, 15)
        else:
            result['list'] = []
        return result

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐 - 返回最新日本分类的内容"""
        try:
            result = self.categoryContent('rb', 1, False, None)
            return {'list': result.get('list', [])[:15]}
        except Exception as e:
            print('homeVideoContent error:', e)
            return {'list': []}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        pg = int(pg) if pg else 1

        if tid == 'comic':
            return self._group_category(pg, extend)

        url = self.host + '/type.html?category=' + tid
        if pg > 1:
            url += '&page=' + str(pg - 1)
        html = self.get_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}
        doc = BeautifulSoup(html, 'html.parser')
        items = doc.find_all('figure') + doc.find_all('div', class_=re.compile(r'group'))
        videos = self._parse_items(items)
        return {'list': videos, 'page': pg, 'pagecount': 999, 'total': 9999}

    def _group_category(self, pg, extend=None):
        url = self.host + '/group.html'
        params = {}

        if isinstance(extend, dict):
            if extend.get('category'):
                params['category'] = extend['category']
            if extend.get('sort'):
                params['sort'] = extend['sort']

        if params:
            url += '?' + urllib.parse.urlencode(params)

        if pg > 1:
            sep = '&' if '?' in url else '?'
            url += f'{sep}page={pg - 1}'

        html = self.get_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}

        doc = BeautifulSoup(html, 'html.parser')
        videos = []

        for group in doc.find_all('div', class_=re.compile(r'group')):
            a = group.find('a', href=True)
            if not a:
                continue
            href = a.get('href', '')
            if '/group_detail_v2.html' not in href:
                continue

            vid = self._extract_vod_id(href)

            title = ''
            t = group.find('div', class_=re.compile(r'line-clamp-2'))
            if t:
                title = t.text.strip()
            if not title:
                title = a.get('title', '') or a.text.strip()

            img = group.find('img', class_=re.compile(r'lazy-image'))
            pic = img.get('src') or img.get('data-src', '') if img else ''
            pic = self.fix_url(pic)
            if pic:
                pic = self._make_proxy_url(pic)

            remark = ''
            if '[' in title and ']' in title:
                m = re.search(r'\[([^\]]+)\]', title)
                if m:
                    remark = m.group(1)

            if vid and title:
                videos.append({
                    'vod_id': vid,
                    'vod_name': title,
                    'vod_pic': pic,
                    'vod_remarks': remark
                })

        pagecount = 999
        pagination = doc.find('div', class_=re.compile(r'flex.*gap-2'))
        if pagination:
            for a in pagination.find_all('a'):
                if a.text.strip().isdigit():
                    pagecount = max(pagecount, int(a.text.strip()))

        return {'list': videos, 'page': pg, 'pagecount': pagecount, 'total': pagecount * 20}

    def detailContent(self, ids):
        if not ids:
            return {'list': []}
        vid = ids[0]
        if self._is_group(vid):
            return self._group_detail(vid)
        if self._is_comic(vid):
            return self._comic_detail(vid)
        return self._video_detail(vid)

    def _video_detail(self, vid):
        url = self.host + '/videos/' + vid + '.html'
        html = self.get_html(url)
        if not html:
            return {'list': []}
        doc = BeautifulSoup(html, 'html.parser')
        title = ''
        t = doc.find('h1', class_=re.compile(r'text-xl'))
        if t:
            title = t.text.strip()
        pic = ''
        img = doc.find('img', class_=re.compile(r'object-cover'))
        if img:
            pic = img.get('src') or img.get('data-src', '')
            pic = self.fix_url(pic)
            if pic:
                pic = self._make_proxy_url(pic)
        desc = ''
        d = doc.find('div', class_=re.compile(r'whitespace-pre-line'))
        if d:
            desc = d.text.strip()
        actors = []
        for a in doc.select('#actor-list a'):
            name = a.find('div', class_=re.compile(r'truncate'))
            actors.append(name.text.strip() if name else a.text.strip())
        tags = []
        for a in doc.select('#class-list a'):
            s = a.find('span')
            tags.append(s.text.strip() if s else a.text.strip())
        play_url = ''
        m = re.search(r'videoSrc\s*=\s*["\']([^"\']+)["\']', html)
        if m:
            play_url = self._clean_play_url(m.group(1))
            if play_url.startswith('/'):
                play_url = self.host + play_url
        if not play_url:
            m = re.search(r'["\']([^"\']+\.m3u8)["\']', html)
            if m:
                play_url = self._clean_play_url(m.group(1))
                if play_url.startswith('/'):
                    play_url = self.host + play_url
        if play_url:
            play_from = '默认线路'
            play_url_str = '播放$' + play_url
        else:
            play_from = '线路1'
            play_url_str = '播放$' + vid
        data = {
            'vod_id': vid,
            'vod_name': title or '未知标题',
            'vod_pic': pic,
            'vod_content': desc,
            'vod_actor': '、'.join(actors) if actors else '',
            'vod_tag': '、'.join(tags) if tags else '',
            'vod_play_from': play_from,
            'vod_play_url': play_url_str,
        }
        return {'list': [data]}

    def _comic_detail(self, vid):
        comic_id = self._get_comic_id(vid)
        url = self.host + '/comic/' + comic_id + '.html'
        html = self.get_html(url)
        if not html:
            return {'list': []}
        doc = BeautifulSoup(html, 'html.parser')

        title = ''
        t = doc.find('h1')
        if t:
            title = t.text.strip()

        pic = ''
        img = doc.find('img', class_=re.compile(r'object-cover'))
        if not img:
            img = doc.find('img', src=re.compile(r'/number/'))
        if img:
            pic = img.get('src') or img.get('data-src', '')
            pic = self.fix_url(pic)
            if pic:
                pic = self._make_proxy_url(pic)

        read_url = self.host + '/comic/read/' + comic_id
        read_html = self.get_html(read_url)
        images = []
        if read_html:
            read_doc = BeautifulSoup(read_html, 'html.parser')
            for img_tag in read_doc.find_all('img'):
                src = img_tag.get('src') or img_tag.get('data-src', '')
                if src and ('/comic/' in src or '/number/' in src):
                    full_url = self.fix_url(src)
                    if full_url and full_url not in images:
                        images.append(full_url)
            if not images:
                for div in read_doc.find_all('div', class_=re.compile(r'page|image|comic')):
                    for img_tag in div.find_all('img'):
                        src = img_tag.get('src') or img_tag.get('data-src', '')
                        if src:
                            full_url = self.fix_url(src)
                            if full_url and full_url not in images:
                                images.append(full_url)

        if not images:
            for img_tag in doc.find_all('img'):
                src = img_tag.get('src') or img_tag.get('data-src', '')
                if src and ('/number/' in src or '/comic/' in src):
                    full_url = self.fix_url(src)
                    if full_url and full_url not in images:
                        images.append(full_url)

        proxy_images = []
        for img_url in images:
            proxy_images.append(self._make_proxy_url(img_url))

        if proxy_images:
            play_from = '漫画阅读'
            play_url_str = 'pics://' + '&&'.join(proxy_images)
        else:
            play_from = '漫画阅读'
            play_url_str = ''

        data = {
            'vod_id': vid,
            'vod_name': title or '未知漫画',
            'vod_pic': pic,
            'vod_content': '',
            'vod_play_from': play_from,
            'vod_play_url': play_url_str,
        }
        return {'list': [data]}

    def _group_detail(self, vid):
        gid = self._get_group_id(vid)
        base_url = self.host + '/group_detail_v2.html?group=' + gid

        first_html = self.get_html(base_url)
        if not first_html:
            return {'list': []}

        doc = BeautifulSoup(first_html, 'html.parser')

        title = ''
        t = doc.find('h1', class_=re.compile(r'text-'))
        if t:
            title = t.text.strip()

        pic = ''
        img = doc.find('img', class_=re.compile(r'object-cover'))
        if img:
            pic = img.get('src') or img.get('data-src', '')
            pic = self.fix_url(pic)
            if pic:
                pic = self._make_proxy_url(pic)

        total_pages = 1
        pagination = doc.find('div', class_=re.compile(r'flex.*gap-2'))
        if pagination:
            for a in pagination.find_all('a'):
                if a.text.strip().isdigit():
                    num = int(a.text.strip())
                    if num > total_pages:
                        total_pages = num
            for a in pagination.find_all('a'):
                if '尾页' in a.text:
                    match = re.search(r'page=(\d+)', a.get('href', ''))
                    if match:
                        total_pages = int(match.group(1)) + 1
                        break

        all_images = []
        all_videos = []
        max_pages = min(total_pages, 30)

        for page in range(max_pages):
            if page == 0:
                html = first_html
            else:
                page_url = base_url + '&page=' + str(page)
                html = self.get_html(page_url)
                if not html:
                    break

            doc_page = BeautifulSoup(html, 'html.parser')
            for trigger in doc_page.find_all('div', class_=re.compile(r'lightbox-trigger')):
                orig = trigger.get('data-original', '')
                if orig:
                    full_url = self.fix_url(orig)
                    # 视频判断：检查是否有视频标识
                    is_video = trigger.find('span', class_=re.compile(r'bg-rose-500'))
                    if is_video:
                        if full_url and full_url not in all_videos:
                            all_videos.append(full_url)
                    else:
                        if full_url and full_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                            if full_url not in all_images:
                                all_images.append(full_url)

            if page >= total_pages - 1:
                break

        play_from = []
        play_url = []

        if all_images:
            proxy_images = []
            for img_url in all_images:
                proxy_images.append(self._make_proxy_url(img_url))
            play_from.append('图片合集')
            play_url.append('pics://' + '&&'.join(proxy_images))

        if all_videos:
            video_play_str = []
            for video_url in all_videos:
                video_play_str.append(f'视频${video_url}')
            play_from.append('视频合集')
            play_url.append('$$$'.join(video_play_str))

        if not play_from:
            play_from.append('图片合集')
            play_url.append('')

        data = {
            'vod_id': vid,
            'vod_name': title or '未知合集',
            'vod_pic': pic,
            'vod_content': '图片 {} 张，视频 {} 个'.format(len(all_images), len(all_videos)),
            'vod_play_from': '$$$'.join(play_from),
            'vod_play_url': '$$$'.join(play_url),
        }
        return {'list': [data]}

    def searchContent(self, key, quick=False, pg='1'):
        if not key:
            return {'list': [], 'page': 1, 'pagecount': 1, 'total': 0}
        pg = int(pg) if pg else 1
        url = self.host + '/type.html?keyword=' + urllib.parse.quote(key)
        if pg > 1:
            url += '&page=' + str(pg - 1)
        html = self.get_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}
        doc = BeautifulSoup(html, 'html.parser')
        items = doc.find_all('figure') + doc.find_all('div', class_=re.compile(r'group'))
        videos = self._parse_items(items)
        return {'list': videos, 'page': pg, 'pagecount': 999, 'total': 9999}

    def playerContent(self, flag, id, vipFlags=None):
        if not id:
            return {'parse': 1, 'url': ''}

        if id.startswith('pics://'):
            return {'parse': 1, 'url': id}

        id = self._clean_play_url(id)
        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': self.host + '/',
            'Cookie': 'ageVerified=true'
        }
        if id.startswith('http'):
            if id.endswith('.m3u8') or id.endswith('.mp4') or '.m3u8?' in id:
                return {'parse': 0, 'url': id, 'header': headers}
            html = self.get_html(id)
            if html:
                m = re.search(r'videoSrc\s*=\s*["\']([^"\']+)["\']', html)
                if m:
                    url = self._clean_play_url(m.group(1))
                    if url.startswith('/'):
                        url = self.host + url
                    if url.endswith('.m3u8') or url.endswith('.mp4'):
                        return {'parse': 0, 'url': url, 'header': headers}
        if not id.startswith('http'):
            url = self.host + '/unvip/video/' + id + '.m3u8'
            return {'parse': 0, 'url': url, 'header': headers}
        return {'parse': 1, 'url': id}

    def localProxy(self, params):
        type_ = params.get('type', '')
        url = params.get('url', '')
        if type_ == 'img' and url:
            try:
                pic_url = base64.b64decode(url).decode()
                resp = requests.get(pic_url, headers=self.headers, timeout=30)
                if resp.status_code == 200:
                    content = resp.content
                    if content.startswith(b'\xff\xd8\xff') or content.startswith(b'\x89PNG') or content.startswith(b'GIF8'):
                        content_type = 'image/jpeg' if content.startswith(b'\xff\xd8\xff') else ('image/png' if content.startswith(b'\x89PNG') else 'image/gif')
                        return [200, content_type, content]
                    content_type = resp.headers.get('Content-Type', 'image/jpeg')
                    return [200, content_type, content]
                else:
                    return [404, 'text/plain', b'Image not found']
            except Exception as e:
                print('localProxy error:', e)
                return [500, 'text/plain', b'Proxy error']
        return [404, 'text/plain', b'Not Found']

    def init(self, extend=''):
        pass

    def destroy(self):
        pass

    def getDependence(self):
        return ['requests', 'bs4']

    def getName(self):
        return '海狗TV'