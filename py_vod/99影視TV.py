# -*- coding: utf-8 -*-
# 99影視TV - https://99itv.cc
import re
import json
import gzip
import zlib
import ssl
import time
import random
import urllib.parse
import urllib.request
from base.spider import Spider

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass


class Spider(Spider):
    def __init__(self):
        self.host = 'https://99itv.cc'
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        self.headers = {
            'User-Agent': self.ua,
            'Referer': self.host + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
        }
        self.timeout = 15
        self.last = 0
        self.classes = [
            {'type_id': 'movie', 'type_name': '電影'},
            {'type_id': 'drama', 'type_name': '電視劇'},
            {'type_id': 'variety', 'type_name': '綜藝'},
            {'type_id': 'anime', 'type_name': '動漫'},
        ]

    def getName(self):
        return '99影視TV'

    def init(self, extend=''):
        pass

    def getDependence(self):
        return []

    def destroy(self):
        pass

    def _log(self, msg):
        try:
            print('[99影視TV] ' + str(msg))
        except Exception:
            pass

    def _clean(self, s):
        if not s:
            return ''
        s = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', '', str(s), flags=re.I)
        s = re.sub(r'<[^>]+>', ' ', s)
        try:
            import html
            s = html.unescape(s)
        except Exception:
            pass
        return re.sub(r'\s+', ' ', s).strip()

    def _fix(self, url):
        if not url:
            return ''
        url = str(url).strip().replace('&amp;', '&')
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        if not re.match(r'https?://', url, re.I):
            return self.host + '/' + url.lstrip('/')
        return url

    def _anti(self, html):
        return bool(html and any(x in html for x in ['請不要頻繁操作', '搜索時間間隔', '系統提示', '等待時間']))

    def _get(self, url, referer=None, retry=3):
        url = self._fix(url)
        for i in range(retry):
            try:
                # 轻限速，避免站点频率限制
                wait = 0.45 - (time.time() - self.last)
                if wait > 0:
                    time.sleep(wait + random.uniform(0.05, 0.2))
                h = dict(self.headers)
                if referer:
                    h['Referer'] = referer
                req = urllib.request.Request(url, headers=h)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as r:
                    raw = r.read()
                    enc = (r.info().get('Content-Encoding') or '').lower()
                    if enc == 'gzip':
                        raw = gzip.decompress(raw)
                    elif enc == 'deflate':
                        try:
                            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                        except Exception:
                            raw = zlib.decompress(raw)
                    self.last = time.time()
                    text = raw.decode('utf-8', errors='ignore')
                    if self._anti(text):
                        self._log('触发频率限制: ' + url)
                        time.sleep(1.5 + i)
                        continue
                    return text
            except Exception as e:
                self._log('请求失败(%s/%s): %s %s' % (i + 1, retry, url, e))
                time.sleep(0.8 + i)
        return ''

    def _vid_from_href(self, href):
        href = href or ''
        m = re.search(r'/detail/([^"/]+?)\.html', href)
        return m.group(1) if m else ''

    def _parse_items(self, html):
        arr, seen = [], set()
        if not html:
            return arr
        blocks = re.findall(r'<a[^>]+href="[^"]*/detail/[^"]+\.html"[\s\S]*?</a>', html, re.I)
        if not blocks:
            blocks = re.findall(r'<div[^>]+class="[^"]*module-(?:poster|card)-item[^"]*"[\s\S]*?</div>', html, re.I)
        for it in blocks:
            try:
                hm = re.search(r'href="([^"]*/detail/[^"]+\.html)"', it, re.I)
                if not hm:
                    continue
                vid = self._vid_from_href(hm.group(1))
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                title = ''
                for p in [r'title="([^"]+)"', r'alt="([^"]+)"', r'<strong[^>]*>([\s\S]*?)</strong>', r'class="[^"]*title[^"]*"[^>]*>([\s\S]*?)<']:
                    m = re.search(p, it, re.I)
                    if m:
                        title = self._clean(m.group(1)); break
                if not title:
                    title = self._clean(it)
                pic = ''
                pm = re.search(r'(?:data-original|data-src|src)="([^"]+)"', it, re.I)
                if pm:
                    pic = self._fix(pm.group(1))
                remark = ''
                rm = re.search(r'class="[^"]*module-item-note[^"]*"[^>]*>([\s\S]*?)</', it, re.I)
                if rm:
                    remark = self._clean(rm.group(1))
                if title:
                    arr.append({'vod_id': vid, 'vod_name': title, 'vod_pic': pic, 'vod_remarks': remark})
            except Exception as e:
                self._log('列表单条解析失败: ' + str(e))
        return arr

    def homeContent(self, filter=False):
        res = {'class': self.classes, 'list': []}
        if filter:
            res['filters'] = {}
        html = self._get(self.host + '/')
        res['list'] = self._parse_items(html)[:30]
        return res

    def homeVideoContent(self):
        return {'list': self.homeContent(False).get('list', [])[:20]}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        try:
            page = max(1, int(pg or 1))
        except Exception:
            page = 1
        url = '/type/%s.html' % tid if page == 1 else '/type/%s-%s.html' % (tid, page)
        html = self._get(url)
        items = self._parse_items(html)
        pagecount = page + 1 if items else page
        return {'list': items, 'page': page, 'pagecount': pagecount, 'limit': 24, 'total': pagecount * 24}

    def searchContent(self, key, quick=False, pg=None):
        if not key:
            return {'list': []}
        try:
            page = max(1, int(pg or 1))
        except Exception:
            page = 1
        wd = urllib.parse.quote(str(key).strip())
        urls = ['/search.html?wd=%s' % wd, '/search/wd/%s.html' % wd]
        if page > 1:
            urls.insert(0, '/search/page/%s/wd/%s.html' % (page, wd))
        items = []
        for u in urls:
            html = self._get(u)
            items = self._parse_items(html)
            if items:
                break
        return {'list': items, 'page': page, 'pagecount': page + 1 if items else 1, 'limit': 20, 'total': len(items)}

    def detailContent(self, ids):
        res = {'list': []}
        if not ids:
            return res
        vid = str(ids[0])
        html = self._get('/detail/%s.html' % vid)
        if not html:
            return res
        vod = {'vod_id': vid, 'vod_name': '', 'vod_pic': '', 'vod_content': '', 'vod_director': '', 'vod_actor': '', 'vod_remarks': '', 'vod_play_from': '', 'vod_play_url': ''}
        m = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', html, re.I)
        if m:
            vod['vod_name'] = self._clean(m.group(1))
        pm = re.search(r'class="[^"]*module-info-poster[^"]*"[\s\S]*?<img[^>]+(?:data-original|data-src|src)="([^"]+)"', html, re.I)
        if not pm:
            pm = re.search(r'property="og:image"\s+content="([^"]+)"', html, re.I)
        if pm:
            vod['vod_pic'] = self._fix(pm.group(1))
        dm = re.search(r'class="[^"]*module-info-introduction-content[^"]*"[^>]*>([\s\S]*?)</div>', html, re.I)
        if dm:
            vod['vod_content'] = self._clean(dm.group(1))
        for key, field in [('導演', 'vod_director'), ('主演', 'vod_actor'), ('備註', 'vod_remarks')]:
            mm = re.search(key + r'[：:]?[\s\S]{0,80}?class="[^"]*module-info-item-content[^"]*"[^>]*>([\s\S]*?)</div>', html, re.I)
            if mm:
                vod[field] = self._clean(mm.group(1)).replace(' / ', ',')

        tabs = re.findall(r'class="[^"]*module-tab-item[^"]*"[^>]*data-dropdown-value="([^"]+)"[\s\S]*?<span[^>]*>([\s\S]*?)</span>', html, re.I)
        names = [self._clean(b) or self._clean(a) for a, b in tabs]
        blocks = re.findall(r'<div[^>]+class="[^"]*module-play-list-content[^"]*"[^>]*>([\s\S]*?)</div>', html, re.I)
        play_from, play_url = [], []
        for i, block in enumerate(blocks):
            eps, seen = [], set()
            for href, name in re.findall(r'<a[^>]+href="([^"]*?/userpy/[^"]+\.html)"[\s\S]*?<span[^>]*>([\s\S]*?)</span>', block, re.I):
                try:
                    purl = self._fix(href)
                    if purl in seen:
                        continue
                    seen.add(purl)
                    eps.append('%s$%s' % (self._clean(name) or ('第%s集' % (len(eps) + 1)), purl))
                except Exception:
                    continue
            if eps:
                play_from.append(names[i] if i < len(names) and names[i] else '线路%s' % (i + 1))
                play_url.append('#'.join(eps))
        if not play_url:
            eps, seen = [], set()
            for href, name in re.findall(r'<a[^>]+href="([^"]*?/userpy/[^"]+\.html)"[\s\S]*?<span[^>]*>([\s\S]*?)</span>', html, re.I):
                purl = self._fix(href)
                if purl not in seen:
                    seen.add(purl); eps.append('%s$%s' % (self._clean(name), purl))
            if eps:
                play_from = ['默認']; play_url = ['#'.join(eps)]
        vod['vod_play_from'] = '$$$'.join(play_from)
        vod['vod_play_url'] = '$$$'.join(play_url)
        res['list'].append(vod)
        return res

    def _decode_player_url(self, data):
        url = data.get('url') or ''
        enc = str(data.get('encrypt', '0'))
        try:
            if enc == '1':
                url = urllib.parse.unquote(url)
            elif enc == '2':
                import base64
                url = base64.b64decode(urllib.parse.unquote(url)).decode('utf-8', errors='ignore')
            else:
                url = urllib.parse.unquote(url)
        except Exception as e:
            self._log('播放地址解码异常: ' + str(e))
        return self._fix(url)

    def _media_header(self, referer):
        return json.dumps({'User-Agent': self.ua, 'Referer': referer or self.host + '/', 'Origin': self.host}, ensure_ascii=False)

    def playerContent(self, flag, id, vipFlags=None):
        ret = {'parse': 1, 'playUrl': '', 'url': id or '', 'header': ''}
        if not id:
            return ret
        full = self._fix(id)
        if re.search(r'\.(m3u8|mp4|flv)(\?|$)', full, re.I):
            return {'parse': 0, 'playUrl': '', 'url': full, 'header': self._media_header(self.host + '/')}
        html = self._get(full, self.host + '/')
        if html:
            m = re.search(r'var\s+player_aaaa\s*=\s*(\{[\s\S]*?\})\s*</script>', html, re.I)
            if not m:
                m = re.search(r'var\s+player_\w+\s*=\s*(\{[\s\S]*?\})\s*;', html, re.I)
            if m:
                try:
                    data = json.loads(m.group(1))
                    purl = self._decode_player_url(data)
                    if purl and re.search(r'\.(m3u8|mp4|flv)(\?|$)', purl, re.I):
                        return {'parse': 0, 'playUrl': '', 'url': purl, 'header': self._media_header(full)}
                    if purl:
                        return {'parse': 1, 'playUrl': '', 'url': purl, 'header': self._media_header(full)}
                except Exception as e:
                    self._log('player_aaaa解析失败: ' + str(e))
            im = re.search(r'<iframe[^>]+src="([^"]+)"', html, re.I)
            if im:
                return self.playerContent(flag, self._fix(im.group(1)), vipFlags)
            mm = re.search(r'(https?://[^\s"\']+?\.(?:m3u8|mp4|flv)[^\s"\']*)', html, re.I)
            if mm:
                return {'parse': 0, 'playUrl': '', 'url': mm.group(1).replace('\\/', '/'), 'header': self._media_header(full)}
        ret['url'] = full
        ret['header'] = self._media_header(full)
        return ret

    def localProxy(self, params=None):
        return None
