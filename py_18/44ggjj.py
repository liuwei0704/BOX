# -*- coding: utf-8 -*-
import json, re, sys, base64, hashlib, os, time
from urllib.parse import quote, unquote

sys.path.append('..')
from base.spider import Spider as BaseSpider


# ========== ENC2 解密（XOR + FNV-1a）==========

def _b64_decode(s):
    s = str(s or '').strip().replace(' ', '').replace('-', '+').replace('_', '/')
    pad = (4 - len(s) % 4) % 4
    return base64.b64decode(s + '=' * pad)


def _fnv1a(data):
    h = 2166136261
    for b in data:
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _xorshift(s):
    s = s & 0xFFFFFFFF
    s ^= (s << 13) & 0xFFFFFFFF
    s ^= (s >> 17) & 0xFFFFFFFF
    s ^= (s << 5) & 0xFFFFFFFF
    return s & 0xFFFFFFFF


def _vf_decrypt(ct_bytes, iv_str, key_str):
    seed = _fnv1a(f'{key_str}|{iv_str}'.encode()) or 2166136261
    out = bytearray(len(ct_bytes))
    r = 0
    for a in range(len(ct_bytes)):
        if a & 3 == 0:
            seed = _xorshift(seed)
            r = seed
        out[a] = ct_bytes[a] ^ ((r >> (8 * (a & 3))) & 255)
    return bytes(out)


def _dec_enc2(enc_str, key='Mumu2026#'):
    if not isinstance(enc_str, str) or not enc_str.startswith('ENC2.'):
        return enc_str
    parts = enc_str.split('.')
    if len(parts) != 3:
        return enc_str
    iv = parts[1]
    ct = _b64_decode(parts[2])
    dec = _vf_decrypt(ct, iv, key)
    return dec.decode('utf-8', errors='replace')


def _dec_obj(obj, key='Mumu2026#'):
    if isinstance(obj, str):
        if obj.startswith('ENC2.'):
            try:
                return json.loads(_dec_enc2(obj, key))
            except:
                return _dec_enc2(obj, key)
        return obj
    if isinstance(obj, list):
        return [_dec_obj(x, key) for x in obj]
    if isinstance(obj, dict):
        return {k: _dec_obj(v, key) for k, v in obj.items()}
    return obj


class Spider(BaseSpider):
    def __init__(self):
        self.name = '44ggjj'
        self.host = 'https://www.44ggjj.com'
        self.api_base = 'https://kkavhd.xffll.com/api'
        self.enc_key = 'Mumu2026#'
        # 图片CDN：sq.2277ww.com 502，用 ddd.aisheji8.com/data/ 替代
        self.pic_cdn = 'https://ddd.aisheji8.com/data'
        # m3u8 CDN：相对路径时拼接此前缀
        self.m3u8_cdn = 'https://h1.ychbkj168.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            'Referer': self.host + '/',
            'Origin': self.host,
        }
        self.page_size = 24
        self._tags_cache = None
        self._tags_ts = 0

    def init(self, extend=''):
        try:
            if extend:
                ext = json.loads(extend)
                if isinstance(ext, dict):
                    self.api_base = ext.get('apiBase', self.api_base)
                    self.enc_key = ext.get('encKey', self.enc_key)
                    self.pic_cdn = ext.get('picCdn', self.pic_cdn)
        except:
            pass
        return None

    def getName(self):
        return self.name

    def isVideoFormat(self, url):
        if not url:
            return False
        if url.startswith(('novel://', 'text://', 'pics://')):
            return False
        return '.m3u8' in url or '.mp4' in url or '.ts' in url

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    # ========== 首页 ==========

    def homeContent(self, filter):
        try:
            return self._homeContent_inner(filter)
        except Exception as e:
            self.log(f'homeContent error: {e}')
            return {'class': [], 'filters': {}, 'list': []}

    def _homeContent_inner(self, filter):
        tags_data = self._get_tags()
        classes = []
        filters = {}
        for cat in tags_data:
            for tag in cat.get('tags', []):
                tid = str(tag.get('id', ''))
                name = tag.get('name', '')
                tag_type = str(tag.get('type', '')).strip()
                if tid and name:
                    # image 和 novel 类型用特殊前缀标识
                    if tag_type == 'image' or tid.startswith('image_'):
                        classes.append({'type_id': tid, 'type_name': f'🖼{name}'})
                    elif tag_type == 'novel' or tid.startswith('novel_'):
                        classes.append({'type_id': tid, 'type_name': f'📖{name}'})
                    else:
                        classes.append({'type_id': tid, 'type_name': name})
        return {'class': classes, 'filters': filters, 'list': []}

    def homeVideoContent(self):
        try:
            return self._homeVideoContent_inner()
        except Exception as e:
            self.log(f'homeVideoContent error: {e}')
            return {'list': []}

    def _homeVideoContent_inner(self):
        resp = self._api(f'/movie/home_sections?pageSize={self.page_size}')
        if not resp or resp.get('code') != 0:
            return {'list': []}
        items = []
        for section in resp.get('data', []):
            for m in section.get('movies', []):
                vod = self._map_vod_movie(m)
                if vod:
                    items.append(vod)
        return {'list': items}

    # ========== 分类 ==========

    def categoryContent(self, tid, pg, filter, extend):
        try:
            return self._categoryContent_inner(tid, pg, filter, extend)
        except Exception as e:
            self.log(f'categoryContent error: {e}')
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 0, 'total': 0}

    def _categoryContent_inner(self, tid, pg, filter, extend):
        page = int(pg)
        tid_str = str(tid)

        # 根据类型选择API
        if tid_str.startswith('image_'):
            return self._category_image(tid_str, page)
        elif tid_str.startswith('novel_'):
            return self._category_novel(tid_str, page)
        else:
            return self._category_movie(tid_str, page)

    def _category_movie(self, tid, page):
        url = f'/movie/list?page={page}&pageSize={self.page_size}&tagid={tid}'
        resp = self._api(url)
        if not resp or resp.get('code') != 0:
            return {'list': [], 'page': page, 'pagecount': 1, 'limit': self.page_size, 'total': 0}
        items = [self._map_vod_movie(m) for m in resp.get('data', []) if m]
        total = resp.get('total', 0) or 0
        pagecount = max(1, (total + self.page_size - 1) // self.page_size) if total else 999
        return {
            'page': page,
            'pagecount': pagecount,
            'limit': self.page_size,
            'total': total,
            'list': items,
        }

    def _category_image(self, tid, page):
        url = f'/image/list?page={page}&pageSize={self.page_size}&tagid={tid}'
        resp = self._api(url)
        if not resp or resp.get('code') != 0:
            return {'list': [], 'page': page, 'pagecount': 1, 'limit': self.page_size, 'total': 0}
        items = []
        for m in resp.get('data', []):
            vod = self._map_vod_image(m)
            if vod:
                items.append(vod)
        total = resp.get('total', 0) or 0
        pagecount = max(1, (total + self.page_size - 1) // self.page_size) if total else 999
        return {
            'page': page,
            'pagecount': pagecount,
            'limit': self.page_size,
            'total': total,
            'list': items,
        }

    def _category_novel(self, tid, page):
        url = f'/novel/list?page={page}&pageSize={self.page_size}&tagid={tid}'
        resp = self._api(url)
        if not resp or resp.get('code') != 0:
            return {'list': [], 'page': page, 'pagecount': 1, 'limit': self.page_size, 'total': 0}
        items = []
        for m in resp.get('data', []):
            vod = self._map_vod_novel(m)
            if vod:
                items.append(vod)
        total = resp.get('total', 0) or 0
        pagecount = max(1, (total + self.page_size - 1) // self.page_size) if total else 999
        return {
            'page': page,
            'pagecount': pagecount,
            'limit': self.page_size,
            'total': total,
            'list': items,
        }

    # ========== 详情 ==========

    def detailContent(self, ids):
        try:
            return self._detailContent_inner(ids)
        except Exception as e:
            self.log(f'detailContent error: {e}')
            return {'list': []}

    def _detailContent_inner(self, ids):
        vod_id = str(ids[0])

        # 判断类型：image_ 前缀 → 图文，novel_ 前缀 → 小说，其他 → 视频
        if vod_id.startswith('image_'):
            real_id = vod_id[6:]
            return self._detail_image(real_id)
        elif vod_id.startswith('novel_'):
            real_id = vod_id[6:]
            return self._detail_novel(real_id)
        else:
            return self._detail_movie(vod_id)

    def _detail_movie(self, vod_id):
        resp = self._api(f'/movie/{vod_id}')
        if not resp or resp.get('code') != 0 or not resp.get('data'):
            return {'list': []}
        data = resp['data']
        movieid = str(data.get('movieid', vod_id))
        title = data.get('Topic', '')
        pic = self._fix_pic_url(data.get('smallpic', ''))
        tagname = data.get('tagname', '')
        timesize = data.get('timesize', '0')
        update = data.get('UpdateTime', '')
        formatted_time = data.get('formatted_timesize', '')

        play_from = []
        play_url = []

        # H264 线路1
        h264_m3u8 = self._fix_m3u8_url(data.get('h264m3u8url', ''))
        h264_mp4 = self._fix_m3u8_url(data.get('h264mp4url', ''))
        if h264_m3u8 or h264_mp4:
            url = h264_m3u8 or h264_mp4
            play_from.append('H264')
            play_url.append(f'正片${url}')

        # H264 线路2
        h264_m3u8_2 = self._fix_m3u8_url(data.get('h264m3u8url2', ''))
        h264_mp4_2 = self._fix_m3u8_url(data.get('h264mp4url2', ''))
        if h264_m3u8_2 or h264_mp4_2:
            url = h264_m3u8_2 or h264_mp4_2
            play_from.append('H264-2')
            play_url.append(f'正片${url}')

        # H265 线路
        h265_m3u8 = self._fix_m3u8_url(data.get('h265m3u8url', ''))
        h265_mp4 = self._fix_m3u8_url(data.get('h265mp4url', ''))
        if h265_m3u8 or h265_mp4:
            url = h265_m3u8 or h265_mp4
            play_from.append('H265')
            play_url.append(f'正片${url}')

        remarks = formatted_time or self._format_duration(timesize)

        vod = {
            'vod_id': movieid,
            'vod_name': title,
            'vod_pic': pic,
            'vod_remarks': remarks,
            'vod_content': f'分类: {tagname}',
            'vod_year': update[:10] if update else '',
            'vod_area': '',
            'vod_class': tagname,
            'vod_director': '',
            'vod_actor': '',
            'vod_play_from': '$$$'.join(play_from),
            'vod_play_url': '$$$'.join(play_url),
        }
        return {'list': [vod]}

    def _detail_image(self, vod_id):
        resp = self._api(f'/image/details?id={vod_id}')
        if not resp or resp.get('code') != 0 or not resp.get('data'):
            return {'list': []}
        data = resp['data']
        title = data.get('topic', '')
        classname = data.get('Classname', '')
        content_html = data.get('Content1', '')

        # 提取图片URL列表
        img_urls = self._extract_image_urls(content_html)
        if not img_urls:
            return {'list': []}

        # 用 pics:// 协议
        pics = '&&'.join(img_urls)

        vod = {
            'vod_id': f'image_{vod_id}',
            'vod_name': title,
            'vod_pic': img_urls[0] if img_urls else '',
            'vod_remarks': f'{len(img_urls)}P',
            'vod_content': title,
            'vod_class': classname,
            'vod_tag': 'image',
            'vod_player': '画',
            'vod_play_from': '图集',
            'vod_play_url': f'图片$pics://{pics}',
        }
        return {'list': [vod]}

    def _detail_novel(self, vod_id):
        resp = self._api(f'/novel/{vod_id}')
        if not resp or resp.get('code') != 0 or not resp.get('data'):
            return {'list': []}
        data = resp['data']
        title = data.get('topic', '')
        classname = data.get('Classname', '')
        content_html = data.get('Content1', '')
        source_url = data.get('Url', '')

        # 提取纯文本
        content_text = self._html_to_text(content_html)

        vod = {
            'vod_id': f'novel_{vod_id}',
            'vod_name': title,
            'vod_pic': '',
            'vod_remarks': classname,
            'vod_content': content_text[:200],
            'vod_class': classname,
            'vod_tag': 'text',
            'vod_player': '书',
            'vod_play_from': '正文',
            'vod_play_url': f'阅读$novel_{vod_id}',
        }
        return {'list': [vod]}

    # ========== 搜索 ==========

    def searchContent(self, key, quick, pg='1'):
        try:
            return self._searchContent_inner(key, quick, pg)
        except Exception as e:
            self.log(f'searchContent error: {e}')
            return {'list': [], 'page': int(pg)}

    def _searchContent_inner(self, key, quick, pg):
        page = int(pg)
        url = f'/movie/list?page={page}&pageSize={self.page_size}&keyword={quote(key)}'
        resp = self._api(url)
        if not resp or resp.get('code') != 0:
            return {'list': [], 'page': page}
        items = [self._map_vod_movie(m) for m in resp.get('data', []) if m]
        if quick:
            items = items[:10]
        return {'page': page, 'list': items}

    # ========== 播放 ==========

    def playerContent(self, flag, id, vipFlags):
        try:
            return self._playerContent_inner(flag, id, vipFlags)
        except Exception as e:
            self.log(f'playerContent error: {e}')
            return {'parse': 1, 'url': id, 'header': self.headers}

    def _playerContent_inner(self, flag, id, vipFlags):
        # 小说协议
        if id.startswith('novel_'):
            novel_id = id[6:]
            resp = self._api(f'/novel/{novel_id}')
            if resp and resp.get('code') == 0 and resp.get('data'):
                content_html = resp['data'].get('Content1', '')
                title = resp['data'].get('topic', '')
                content_text = self._html_to_text(content_html)
                novel_json = json.dumps({'title': title, 'content': content_text}, ensure_ascii=False)
                return {'parse': 0, 'url': f'novel://{novel_json}', 'header': ''}
            return {'parse': 0, 'url': 'novel://{"title":"加载失败","content":"无法获取内容"}', 'header': ''}

        # 视频
        url = self._fix_m3u8_url(id)
        header = {'User-Agent': self.headers['User-Agent'], 'Referer': self.host + '/'}
        if '.m3u8' in url or '.mp4' in url:
            return {'parse': 0, 'url': url, 'header': header, 'jx': 0}
        return {'parse': 1, 'url': url, 'header': header}

    # ========== 工具方法 ==========

    def _api(self, path, timeout=15):
        url = self.api_base + path
        try:
            rsp = self.fetch(url, headers=self.headers, timeout=timeout, verify=False)
            text = rsp.text or ''
            if not text or text.startswith('<!--'):
                return None
            data = json.loads(text)
            return _dec_obj(data, self.enc_key)
        except Exception as e:
            self.log(f'API error [{path}]: {e}')
            return None

    def _get_tags(self, force=False):
        now = time.time()
        if not force and self._tags_cache and now - self._tags_ts < 3600:
            return self._tags_cache
        resp = self._api('/movie/tags')
        if resp and resp.get('code') == 0:
            self._tags_cache = resp.get('data', [])
            self._tags_ts = now
            return self._tags_cache
        return self._tags_cache or []

    def _fix_pic_url(self, url):
        """修复封面图URL：sq.2277ww.com 502，替换为可用CDN"""
        raw = str(url or '').strip()
        if not raw:
            return ''
        # sq.2277ww.com/cover/ → ddd.aisheji8.com/data/cover/
        raw = raw.replace('sq.2277ww.com/cover/', 'ddd.aisheji8.com/data/cover/')
        # 其他域名的 /cover/ 也尝试修复
        if not raw.startswith('http'):
            if raw.startswith('//'):
                return 'https:' + raw
            if raw.startswith('/'):
                return self.pic_cdn + raw
            return self.pic_cdn + '/' + raw
        return raw

    def _fix_img_url(self, url):
        """修复图片内容URL：相对路径转绝对路径"""
        raw = str(url or '').strip()
        if not raw:
            return ''
        if raw.startswith('http'):
            # 修复已知问题域名
            raw = raw.replace('sq.2277ww.com/', 'ddd.aisheji8.com/data/')
            return raw
        # 相对路径 → 拼接 pic_cdn
        if raw.startswith('/'):
            return self.pic_cdn + raw
        return self.pic_cdn + '/' + raw

    def _map_vod_movie(self, m):
        if not m:
            return None
        movieid = str(m.get('movieid', ''))
        title = m.get('Topic', '')
        pic = self._fix_pic_url(m.get('smallpic', ''))
        formatted_time = m.get('formatted_timesize', '')
        timesize = str(m.get('timesize', '0'))
        remarks = formatted_time or self._format_duration(timesize)
        if not movieid or not title:
            return None
        return {
            'vod_id': movieid,
            'vod_name': title,
            'vod_pic': pic,
            'vod_remarks': remarks,
        }

    def _map_vod_image(self, m):
        if not m:
            return None
        picid = str(m.get('picid', ''))
        title = m.get('title', '')
        picurl_html = m.get('picurl', '')
        # 提取第一张图作为封面
        imgs = re.findall(r'src="([^"]+)"', picurl_html)
        pic = self._fix_img_url(imgs[0]) if imgs else ''
        count = len(imgs)
        if not picid or not title:
            return None
        return {
            'vod_id': f'image_{picid}',
            'vod_name': title,
            'vod_pic': pic,
            'vod_remarks': f'{count}P' if count else '',
        }

    def _map_vod_novel(self, m):
        if not m:
            return None
        novelid = str(m.get('novelid', ''))
        title = m.get('title', '')
        if not novelid or not title:
            return None
        return {
            'vod_id': f'novel_{novelid}',
            'vod_name': title,
            'vod_pic': '',
            'vod_remarks': '小说',
        }

    def _extract_image_urls(self, html):
        """从 HTML 中提取图片 URL 并修复路径"""
        urls = []
        for src in re.findall(r'src="([^"]+)"', str(html or '')):
            fixed = self._fix_img_url(src)
            if fixed:
                urls.append(fixed)
        return urls

    def _html_to_text(self, html):
        """HTML 转纯文本"""
        text = str(html or '')
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'</p>\s*<p[^>]*>', '\n\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _format_duration(self, seconds_str):
        try:
            secs = int(seconds_str)
            if secs <= 0:
                return ''
            mins = secs // 60
            s = secs % 60
            return f'{mins:02d}:{s:02d}'
        except:
            return ''

    def _fix_m3u8_url(self, url):
        """修复 m3u8 相对路径：/data/... → https://cdn/data/..."""
        raw = str(url or '').strip()
        if not raw:
            return ''
        if raw.startswith('http'):
            return raw
        if raw.startswith('/data/'):
            return self.m3u8_cdn + raw
        return raw

    def _full_url(self, path):
        raw = str(path or '').strip()
        if not raw:
            return ''
        if raw.startswith('http'):
            return raw
        if raw.startswith('//'):
            return 'https:' + raw
        if raw.startswith('/'):
            return self.host + raw
        return self.host + '/' + raw

    def localProxy(self, param):
        return [404, 'text/plain', b'']
