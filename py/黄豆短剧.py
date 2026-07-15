# coding: utf-8
# 黄豆短剧 https://www.hdmgdj.com/
# React SPA + /api AES-GCM(ECDH/HKDF) + 加密封面(.bng AES-CBC-CBC变体)
from base.spider import Spider
import json, re, time, os, base64, hashlib, random, urllib.parse, warnings
try:
    import urllib3
    urllib3.disable_warnings()
except Exception:
    pass

try:
    from Crypto.Cipher import AES
except Exception:
    AES = None

class Spider(Spider):
    def getName(self):
        return '黄豆短剧'

    def __init__(self):
        self.host = 'https://www.hdmgdj.com'
        self.api = self.host + '/api'
        self.ua = 'Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36'
        self.sid = ''
        self.k = None
        self.exp = 0
        self._home_cache = None
        self._home_cache_time = 0
        self._detail_cache = {}
        self._m3u8_cache = {}
        self.classes = [
            {'type_id': 'all', 'type_name': '全部'},
            {'type_id': 'recommend', 'type_name': '推荐'},
            {'type_id': '都市', 'type_name': '都市'},
            {'type_id': '古装', 'type_name': '古装'},
            {'type_id': '悬疑', 'type_name': '悬疑'},
            {'type_id': '逆袭', 'type_name': '逆袭'},
            {'type_id': '穿越', 'type_name': '穿越'},
            {'type_id': '奇幻', 'type_name': '奇幻'},
            {'type_id': '甜宠', 'type_name': '甜宠'},
            {'type_id': '玄幻', 'type_name': '玄幻'},
            {'type_id': '大女主', 'type_name': '大女主'},
            {'type_id': '复仇', 'type_name': '复仇'},
            {'type_id': '科幻', 'type_name': '科幻'},
            {'type_id': 'AI漫剧', 'type_name': 'AI漫剧'},
            {'type_id': '规则怪谈', 'type_name': '规则怪谈'},
            {'type_id': '异能', 'type_name': '异能'},
            {'type_id': '恐怖', 'type_name': '恐怖'},
            {'type_id': '动漫同人', 'type_name': '动漫同人'},
            {'type_id': '漫改', 'type_name': '漫改'},
            {'type_id': '国漫', 'type_name': '国漫'},
            {'type_id': '大神原创', 'type_name': '大神原创'},
            {'type_id': '魔改短剧', 'type_name': '魔改短剧'},
            {'type_id': '精品', 'type_name': '精品'},
        ]
        tag_vals = [{'n': '全部', 'v': ''}] + [{'n': c['type_name'], 'v': c['type_id']} for c in self.classes if c['type_id'] not in ['all','recommend']]
        self.filters = {'all': [
            {'key': 'genre', 'name': '题材', 'value': tag_vals},
            {'key': 'order', 'name': '排序', 'value': [{'n':'默认','v':''},{'n':'最新','v':'new'},{'n':'最热','v':'hot'}]}
        ]}
        for c in self.classes:
            if c['type_id'] not in self.filters:
                self.filters[c['type_id']] = [{'key':'order','name':'排序','value':[{'n':'默认','v':''},{'n':'最新','v':'new'},{'n':'最热','v':'hot'}]}]

    def init(self, extend):
        pass

    def getDependence(self):
        return []

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    def homeContent(self, filter):
        return {'class': self.classes, 'filters': self.filters}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            data = self._home() or {}
            arr = []
            for k in ['feature', 'guess', 'latest', 'hot']:
                arr += data.get(k) or []
            return {'list': self._vod_list(arr[:30])}
        except Exception as e:
            self._log('首页推荐失败: %s' % e)
            return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._int(pg, 1)
        ext = self._extend(extend)
        try:
            if isinstance(tid, dict):
                tid = tid.get('id') or tid.get('name') or ''
            tid = urllib.parse.unquote(str(tid or 'all'))
            if tid.startswith('search:'):
                return self._page('/search', {'kw': tid[7:], 'page': page, 'size': 24}, page)
            if tid.startswith('tag:'):
                return self._tag_page(tid[4:], page)
            elif tid == 'all':
                tag = ext.get('genre') or ''
            elif tid == 'recommend':
                data = self._home() or {}
                return self._result(self._vod_list((data.get('feature') or []) + (data.get('guess') or [])), page)
            else:
                tag = tid
            params = {'page': page, 'size': 24}
            if tag:
                params['kw'] = tag
            if ext.get('order'):
                params['sort'] = ext.get('order')
            return self._page('/dramas', params, page)
        except Exception as e:
            self._log('分类失败 tid=%s pg=%s err=%s' % (tid, page, e))
            return self._result([], page)

    def searchContent(self, key, quick=False, pg='1'):
        page = self._int(pg, 1)
        try:
            return {'list': self._vod_list((self._api_get('/search', {'kw': key, 'page': page, 'size': 30}) or {}).get('list') or [])}
        except Exception as e:
            self._log('搜索失败: %s' % e)
            return {'list': []}

    def detailContent(self, ids):
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            data = self._api_get('/dramas/%s' % vid) or {}
            vod = self._vod(data)
            vod.update({
                'vod_id': str(data.get('id') or vid),
                'vod_name': data.get('t') or data.get('title') or '',
                'vod_pic': self._pic(data.get('cover') or ''),
                'type_name': ' '.join(data.get('tags') or []) or data.get('sub') or '',
                'vod_year': '',
                'vod_area': '',
                'vod_remarks': data.get('serial') or (('%s集' % data.get('eps')) if data.get('eps') else ''),
                'vod_actor': '',
                'vod_director': '',
                'vod_content': self._content(data),
            })
            eps = data.get('episodes') or []
            play = []
            for ep in eps:
                try:
                    epno = ep.get('ep') or ep.get('index') or len(play)+1
                    name = ep.get('title') or ('第%s集' % epno)
                    url = ep.get('playUrl') or ep.get('url') or ''
                    if not url:
                        continue
                    pid = self._b64(json.dumps({'dramaId': str(vid), 'ep': epno, 'url': url}, ensure_ascii=False, separators=(',', ':')))
                    play.append('%s$%s' % (name, pid))
                except Exception:
                    continue
            if play:
                vod['vod_play_from'] = '黄豆直链'
                vod['vod_play_url'] = '#'.join(play)
            return {'list': [vod]}
        except Exception as e:
            self._log('详情失败: %s' % e)
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            raw = self._unb64(str(id))
            info = json.loads(raw) if raw.startswith('{') else {'url': id}
            url = info.get('url') or id
            # 原站 m3u8 内使用 custom://key，EXO 无法识别；改走本地代理重写 key URI
            if '.m3u8' in url:
                url = self.getProxyUrl() + '&mode=m3u8&url=' + urllib.parse.quote(url)
            header = {'User-Agent': self.ua, 'Referer': self.host + '/', 'Origin': self.host}
            return {'parse': 0, 'playUrl': '', 'url': url, 'header': header}
        except Exception as e:
            self._log('播放失败: %s' % e)
            return {'parse': 1, 'url': id}

    def localProxy(self, param):
        try:
            mode = ''
            url = ''
            if isinstance(param, dict):
                mode = str(param.get('mode') or '')
                url = param.get('url') or param.get('src') or ''
                hval = param.get('hash') or ''
                ver = param.get('version') or 'v1'
            elif isinstance(param, list) and param:
                url = param[0]; hval = ''; ver = 'v1'
            else:
                hval = ''; ver = 'v1'
            url = urllib.parse.unquote(str(url or ''))
            if mode == 'key':
                key = hashlib.md5(('xnaichanping' + str(hval).lower() + str(ver)).encode()).digest()
                return [200, 'application/octet-stream', key]
            if not url:
                return [404, 'text/plain', b'']
            if mode == 'm3u8' or '.m3u8' in url:
                return self._proxy_m3u8(url)
            data = self._fetch_bytes(url)
            if '.bng' in url or self._magic(data) == 'bin':
                data = self._decrypt_bng(data, url)
            mime = self._mime(data)
            return [200, mime, data]
        except Exception as e:
            self._log('本地代理失败: %s' % e)
            return [500, 'text/plain', str(e).encode('utf-8')]
    def _home(self):
        if self._home_cache and time.time() - self._home_cache_time < 180:
            return self._home_cache
        data = self._api_get('/home') or {}
        self._home_cache = data
        self._home_cache_time = time.time()
        return data

    def _tag_page(self, tag, page):
        tag = str(tag or '').strip()
        if not tag:
            return self._result([], page)
        arr = []
        # 站点没有独立标签接口，富文本点击用搜索 + 列表扫描兜底，确保点击不空。
        for path, params in [
            ('/search', {'kw': tag, 'page': page, 'size': 24}),
            ('/dramas', {'kw': tag, 'page': page, 'size': 24}),
        ]:
            data = self._api_get(path, params) or {}
            items = data.get('list') if isinstance(data, dict) else data
            for it in items or []:
                if tag in (it.get('tags') or []) or tag in (it.get('sub') or '') or tag in (it.get('t') or ''):
                    arr.append(it)
            if arr:
                return self._result(self._vod_list(arr), page)
        # 标签搜索为空时，从全量最新列表抽样过滤，避免详情富文本点击空白。
        for p in range(1, 4):
            data = self._api_get('/dramas', {'sort': '最新', 'page': p, 'size': 24}) or {}
            for it in (data.get('list') if isinstance(data, dict) else data) or []:
                if tag in (it.get('tags') or []) or tag in (it.get('sub') or ''):
                    arr.append(it)
            if len(arr) >= 24:
                break
        return self._result(self._vod_list(arr), page)

    def _proxy_m3u8(self, url):
        text = self.fetch(url, headers={'User-Agent': self.ua, 'Referer': self.host + '/', 'Origin': self.host}, timeout=15, verify=False).text
        h = ''
        m = re.search(r'/hls/([0-9a-fA-F]{64})/', url)
        if m:
            h = m.group(1).lower()
        ver = 'v1'
        mv = re.search(r'[?&]version=([^&#]+)', url)
        if mv:
            ver = urllib.parse.unquote(mv.group(1))
        key_url = self.getProxyUrl() + '&mode=key&hash=' + h + '&version=' + urllib.parse.quote(ver)
        text = re.sub(r'URI="custom://key\?version=[^"]*"', 'URI="%s"' % key_url, text)
        base = url.rsplit('/', 1)[0] + '/'
        out = []
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith('#') and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', s):
                out.append(urllib.parse.urljoin(base, s))
            else:
                out.append(line)
        return [200, 'application/vnd.apple.mpegurl', ('\n'.join(out) + '\n').encode('utf-8')]


    def _api_get(self, path, params=None):
        self._ensure_session()
        url = self.api + path
        p = {'platform': 'mobile'}
        if params: p.update(params)
        headers = self._headers()
        headers['X-Sid'] = self.sid
        r = self.fetch(url, params=p, headers=headers, timeout=15, verify=False)
        data = r.json()
        data = self._dec_payload(data)
        if isinstance(data, dict) and data.get('code') == 0:
            return data.get('data')
        self._log('API异常 %s -> %s' % (path, data))
        return data.get('data') if isinstance(data, dict) else data

    def _ensure_session(self):
        if self.sid and self.k and self.exp > time.time():
            return
        if AES is None:
            raise Exception('缺少 Crypto.Cipher.AES')
        # P-256 参数
        p = int('ffffffff00000001000000000000000000000000ffffffffffffffffffffffff', 16)
        a = int('ffffffff00000001000000000000000000000000fffffffffffffffffffffffc', 16)
        b = int('5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b', 16)
        gx = int('6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296', 16)
        gy = int('4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5', 16)
        n = int('ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551', 16)
        sx = int('cfd1448eb340b7c5276e0fba9a69c63eda4e9a772314afc2ad007e667d56d94', 16)
        sy = int('ddaf05723a69f6a7d68aa2e680071dca73241442debd9a63c1cc9401ba9b4752', 16)
        d = random.SystemRandom().randrange(1, n-1)
        qx, qy = self._ec_mul(d, gx, gy, p, a)
        ssx, ssy = self._ec_mul(d, sx, sy, p, a)
        shared = ssx.to_bytes(32, 'big')
        self.k = self._hkdf(shared, b'app-data-h5')
        client_pub = self._spki(qx, qy)
        body = {'clientPub': base64.b64encode(client_pub).decode(), 'keyId': 'h5-2026-07', 'clientType': 'h5'}
        url = self.api + '/handshake?platform=mobile'
        r = self.post(url, headers=self._headers(), data=json.dumps(body), timeout=15)
        j = r.json()
        self.sid = ((j.get('data') or {}).get('sid') if isinstance(j, dict) else '') or ''
        if not self.sid:
            raise Exception('handshake failed: %s' % j)
        self.exp = time.time() + 20 * 60

    def _dec_payload(self, obj):
        if isinstance(obj, dict) and 'iv' in obj and 'data' in obj:
            iv = base64.b64decode(obj.get('iv'))
            raw = base64.b64decode(obj.get('data'))
            plain = AES.new(self.k, AES.MODE_GCM, nonce=iv).decrypt(raw[:-16])
            # PyCryptodome 上面未校验 tag；若环境支持可 decrypt_and_verify
            try:
                plain = AES.new(self.k, AES.MODE_GCM, nonce=iv).decrypt_and_verify(raw[:-16], raw[-16:])
            except Exception:
                pass
            return json.loads(plain.decode('utf-8')).get('payload')
        return obj

    def _headers(self):
        return {'User-Agent': self.ua, 'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json', 'Origin': self.host, 'Referer': self.host + '/'}

    def _page(self, path, params, page):
        data = self._api_get(path, params) or {}
        arr = data.get('list') if isinstance(data, dict) else data
        return self._result(self._vod_list(arr or []), page, data if isinstance(data, dict) else {})

    def _result(self, arr, page, data=None):
        total = self._int((data or {}).get('total') or (data or {}).get('count') or 9999, 9999)
        return {'list': arr, 'page': int(page), 'pagecount': max(int(page)+1, (total + 23)//24), 'limit': 24, 'total': total}

    def _vod_list(self, arr):
        res, seen = [], set()
        for it in arr or []:
            try:
                v = self._vod(it)
                if v['vod_id'] and v['vod_id'] not in seen:
                    seen.add(v['vod_id']); res.append(v)
            except Exception:
                continue
        return res

    def _vod(self, it):
        vid = str(it.get('id') or it.get('vod_id') or '')
        return {'vod_id': vid, 'vod_name': it.get('t') or it.get('title') or it.get('name') or '', 'vod_pic': self._pic(it.get('cover') or it.get('pic') or ''), 'vod_remarks': it.get('serial') or it.get('sub') or (('%s集' % it.get('eps')) if it.get('eps') else '')}

    def _content(self, data):
        tags = data.get('tags') or []
        links = []
        for t in tags:
            payload = json.dumps({'id': 'tag:' + str(t), 'name': str(t)}, ensure_ascii=False, separators=(',', ':'))
            links.append('[a=cr:%s/]%s[/a]' % (payload, t))
        parts = []
        if data.get('summary'): parts.append(data.get('summary'))
        if links: parts.append('标签：' + ' '.join(links))
        if data.get('plays'): parts.append('播放：' + str(data.get('plays')))
        if data.get('likes') is not None: parts.append('点赞：' + str(data.get('likes')))
        return '\n'.join(parts)

    def _pic(self, url):
        url = str(url or '')
        if not url: return ''
        if '.bng' in url:
            return self.getProxyUrl() + '&url=' + urllib.parse.quote(url)
        return url

    def _fetch_bytes(self, url):
        r = self.fetch(url, headers={'User-Agent': self.ua, 'Referer': self.host + '/'}, timeout=20, verify=False)
        return r.content

    def _decrypt_bng(self, data, url):
        if AES is None: return data
        m = re.search(r'[0-9a-fA-F]{64}', url)
        if not m: return data
        ver = 'v1'
        mv = re.search(r'[?&]version=([^&#]+)', url)
        if mv: ver = urllib.parse.unquote(mv.group(1))
        key = hashlib.md5(('xnaichanping' + m.group(0).lower() + ver).encode()).digest()
        iv = bytes(16)
        if len(data) % 16 != 0 or len(data) < 16: return data
        last = data[-16:]
        pad_block = bytes([x ^ 16 for x in last])
        extra = AES.new(key, AES.MODE_CBC, iv).encrypt(pad_block)[:16]
        dec = AES.new(key, AES.MODE_CBC, iv).decrypt(data + extra)
        out = bytearray(len(dec))
        out[:16] = dec[:16]
        blocks = len(data) // 16
        for i in range(1, blocks):
            for j in range(16):
                out[i*16+j] = dec[i*16+j] ^ data[(i-1)*16+j]
        pad = out[len(data)-1]
        return bytes(out[:len(data) - (pad if 0 < pad <= 16 else 0)])

    def _mime(self, b):
        if b.startswith(b'\xff\xd8\xff'): return 'image/jpeg'
        if b.startswith(b'\x89PNG'): return 'image/png'
        if b.startswith(b'GIF'): return 'image/gif'
        if b[:4] == b'RIFF' and b[8:12] == b'WEBP': return 'image/webp'
        return 'application/octet-stream'

    def _magic(self, b):
        return self._mime(b) if b else 'bin'

    def _extend(self, e):
        if isinstance(e, dict): return e
        try: return json.loads(e) if e else {}
        except Exception: return {}

    def _int(self, v, d=0):
        try: return int(v)
        except Exception: return d

    def _b64(self, s):
        return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')

    def _unb64(self, s):
        try:
            return base64.urlsafe_b64decode(s + '=' * ((4 - len(s) % 4) % 4)).decode()
        except Exception:
            return s

    def _log(self, msg):
        try: self.log('[黄豆短剧] ' + str(msg))
        except Exception: pass

    # ---- P-256 / HKDF / SPKI，无 cryptography 依赖 ----
    def _inv(self, x, p):
        return pow(x, p-2, p)

    def _ec_add(self, P, Q, p, a):
        if P is None: return Q
        if Q is None: return P
        x1,y1=P; x2,y2=Q
        if x1 == x2 and (y1 + y2) % p == 0: return None
        if P == Q:
            lam = ((3*x1*x1 + a) * self._inv(2*y1 % p, p)) % p
        else:
            lam = ((y2-y1) * self._inv((x2-x1) % p, p)) % p
        x3 = (lam*lam - x1 - x2) % p
        y3 = (lam*(x1-x3) - y1) % p
        return (x3,y3)

    def _ec_mul(self, k, x, y, p, a):
        R = None; P = (x,y)
        while k:
            if k & 1: R = self._ec_add(R, P, p, a)
            P = self._ec_add(P, P, p, a); k >>= 1
        return R

    def _hkdf(self, ikm, info):
        prk = hashlib.pbkdf2_hmac('sha256', ikm, b'', 1, dklen=32)
        # 上面不是标准 HKDF-Extract(salt空)，按 HMAC 实现一次
        import hmac
        prk = hmac.new(bytes(32), ikm, hashlib.sha256).digest()
        t = hmac.new(prk, info + bytes([1]), hashlib.sha256).digest()
        return t[:32]

    def _spki(self, x, y):
        # DER SubjectPublicKeyInfo: ecPublicKey + prime256v1 + uncompressed point
        point = bytes([4]) + x.to_bytes(32,'big') + y.to_bytes(32,'big')
        head = bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d030107034200')
        return head + point