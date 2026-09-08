import json
import re
from urllib.parse import parse_qsl, urlencode, unquote, urljoin, urlparse

from lxml import etree
from base.spider import Spider


class Spider(Spider):
    def __init__(self):
        self.ext = ''
        self.host = 'https://123av.com'
        self.locale = '/cn'
        self.ua = 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/126.0.0.0 Mobile Safari/537.36'
        self.headers = {'User-Agent': self.ua, 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.7'}
        self.classes = [
            {'type_id': 'new', 'type_name': '新'},
            {'type_id': 'hot', 'type_name': '热门'},
            {'type_id': 'recent', 'type_name': '最近'},
            {'type_id': 'trend_group', 'type_name': '趋势'},
            {'type_id': 'type_group', 'type_name': '类型'},
            {'type_id': 'collection_group', 'type_name': '集合'},
            {'type_id': 'amateur_group', 'type_name': '业余'},
            {'type_id': 'uncensored_group', 'type_name': '无码'},
        ]
        years = [{'n': '全部', 'v': ''}] + [{'n': str(y), 'v': str(y)} for y in range(2026, 1999, -1)]
        sort_values = [
            {'n': '发布日期', 'v': 'release_date'}, {'n': '最近添加', 'v': 'recent'},
            {'n': '热门', 'v': 'hot'}, {'n': '今日观看', 'v': 'today'},
            {'n': '每周观看', 'v': 'week'}, {'n': '每月观看', 'v': 'month'},
            {'n': '最受欢迎', 'v': 'views'}, {'n': '最多关注', 'v': 'follows'},
            {'n': '最长', 'v': 'longest'}]
        common = [
            {'key': 'year', 'name': '年份', 'value': years},
            {'key': 'actress', 'name': '演员数', 'value': [
                {'n': '全部', 'v': ''}, {'n': '单人', 'v': 'single'}, {'n': '多人', 'v': 'multi'}]},
            {'key': 'sort', 'name': '排序', 'value': sort_values},
        ]
        self.filters = {x: common for x in ('new', 'hot', 'recent')}
        self.filters['trend_group'] = [
            {'key': 'cate_id', 'name': '趋势', 'value': [
                {'n': '今天', 'v': '/cn/all?sort=today'}, {'n': '本周', 'v': '/cn/all?sort=week'},
                {'n': '本月', 'v': '/cn/all?sort=month'}]}] + common[:2]
        self.filters['type_group'] = [
            {'key': 'cate_id', 'name': '类型', 'value': [
                {'n': '有码', 'v': '/cn/censored'}, {'n': '无码', 'v': '/cn/uncensored'},
                {'n': '无码泄露', 'v': '/cn/uncensored-leaked'}]}] + common
        directory_sort = [{'n': n, 'v': v} for n, v in (
            ('视频数量', 'count'), ('名称 A-Z', 'name'), ('最受欢迎', 'views'),
            ('今日观看', 'today'), ('每周观看', 'week'), ('每月观看', 'month'))]
        heights = [{'n': '任意身高', 'v': ''}] + [
            {'n': '%s-%s厘米' % (x, x + 4), 'v': '%s-%s' % (x, x + 4)} for x in range(130, 195, 5)]
        cups = [{'n': '任意罩杯', 'v': ''}] + [{'n': x + '罩杯', 'v': x} for x in 'ABCDEFGHIJKLMNOPQZ']
        ages = [{'n': '任意年龄', 'v': ''}, {'n': '< 20岁', 'v': '0-19'},
                {'n': '20-24岁', 'v': '20-24'}, {'n': '25-29岁', 'v': '25-29'},
                {'n': '30-34岁', 'v': '30-34'}, {'n': '35-39岁', 'v': '35-39'},
                {'n': '40-44岁', 'v': '40-44'}, {'n': '45-49岁', 'v': '45-49'},
                {'n': '50-54岁', 'v': '50-54'}, {'n': '> 60岁', 'v': '60-99'}]
        self.filters['collection_group'] = [
            {'key': 'cate_id', 'name': '集合', 'value': [
                {'n': '类别', 'v': '/cn/genres'}, {'n': '女演员', 'v': '/cn/actresses'},
                {'n': '制作商', 'v': '/cn/makers'}, {'n': '系列', 'v': '/cn/series'}]},
            {'key': 'height', 'name': '身高·女演员', 'value': heights},
            {'key': 'cup', 'name': '罩杯·女演员', 'value': cups},
            {'key': 'age', 'name': '年龄·女演员', 'value': ages},
            {'key': 'sort', 'name': '目录排序', 'value': directory_sort + [{'n': '关注最多', 'v': 'favorited'}]}]
        self.filters['amateur_group'] = [
            {'key': 'cate_id', 'name': '业余', 'value': [
                {'n': 'SIRO', 'v': '/cn/tags/siro'}, {'n': 'LUXU', 'v': '/cn/tags/259luxu'},
                {'n': '200GANA', 'v': '/cn/tags/200gana'}, {'n': 'PRESTIGE', 'v': '/cn/tags/prestige-premium'},
                {'n': 'ORECO', 'v': '/cn/tags/230oreco'}, {'n': 'S-CUTE', 'v': '/cn/makers/s-cute'},
                {'n': 'ARA', 'v': '/cn/tags/261ara'}, {'n': '390JAC', 'v': '/cn/tags/390jac'}]},
            {'key': 'sort', 'name': '排序', 'value': sort_values}]
        self.filters['uncensored_group'] = [
            {'key': 'cate_id', 'name': '无码', 'value': [
                {'n': 'FC2', 'v': '/cn/makers/fc2'}, {'n': 'HEYZO', 'v': '/cn/makers/heyzo'},
                {'n': '1pondo', 'v': '/cn/makers/1pondo'}, {'n': 'Caribbeancom', 'v': '/cn/makers/caribbeancom'},
                {'n': '10musume', 'v': '/cn/makers/10musume'}, {'n': 'Pacopacomama', 'v': '/cn/makers/pacopacomama'},
                {'n': 'Tokyo Hot', 'v': '/cn/makers/tokyo-hot'}, {'n': 'XXX-AV', 'v': '/cn/makers/xxx-av'}]},
            {'key': 'sort', 'name': '排序', 'value': sort_values}]

    def getName(self):
        return '123AV'

    def getDependence(self):
        return []

    def setExtendInfo(self, extend):
        self.ext = extend or ''
        return None

    def init(self, extend=''):
        self.ext = getattr(self, 'ext', '') or extend or ''

    def homeLayout(self):
        return 0

    def isVideoFormat(self, url):
        return bool(re.search(r'\.(?:m3u8|mp4|flv)(?:$|[?#])', str(url or ''), re.I))

    def manualVideoCheck(self):
        return False

    def homeContent(self, filter=False):
        return {'class': self.classes, 'filters': self.filters}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def _text(self, node):
        if node is None:
            return ''
        return re.sub(r'\s+', ' ', ''.join(node.itertext())).strip()

    def _dom(self, content):
        if content is None or content == b'' or content == '':
            return None
        try:
            parser = etree.HTMLParser(recover=True, encoding='utf-8')
            data = content if isinstance(content, bytes) else str(content).encode('utf-8', errors='ignore')
            return etree.HTML(data, parser=parser)
        except Exception as e:
            self.log('DOM解析失败: %s' % e)
            return None

    def _get(self, url, headers=None, timeout=15):
        try:
            h = dict(self.headers)
            if headers:
                h.update(headers)
            rsp = self.fetch(url, headers=h, timeout=timeout, verify=False)
            if rsp is None:
                self.log('请求无响应: %s' % url)
                return ''
            content = getattr(rsp, 'content', None)
            if content not in (None, b'', ''):
                return content
            return getattr(rsp, 'text', '') or ''
        except Exception as e:
            self.log('请求失败: %s | %s' % (url, e))
            return ''

    def _extend(self, extend):
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str) and extend.strip():
            try:
                obj = json.loads(extend)
                return obj if isinstance(obj, dict) else {}
            except Exception:
                return {}
        return {}

    def _pagecount(self, doc, page, count):
        if doc is None:
            return page if count else 0
        nums = []
        for a in doc.xpath('//a[contains(@class,"pager") or contains(@href,"page=")]/@href'):
            m = re.search(r'[?&]page=(\d+)', a)
            if m:
                nums.append(int(m.group(1)))
        for x in doc.xpath('//input[@name="page"]/@max'):
            if str(x).isdigit():
                nums.append(int(x))
        return max(nums) if nums else (page + 1 if count >= 12 else page)

    def _cards(self, doc):
        if doc is None:
            return []
        result, seen = [], set()
        links = doc.xpath('//a[contains(@class,"card__link") and contains(@href,"/v/")]')
        if not links:
            links = doc.xpath('//div[contains(@class,"card")]//a[contains(@href,"/v/")][normalize-space()]')
        for a in links:
            href = a.get('href') or ''
            if '/v/' not in href:
                continue
            vid = urlparse(urljoin(self.host, href)).path
            if vid in seen:
                continue
            card = a
            while card is not None and 'card' not in (card.get('class') or '').split():
                card = card.getparent()
            if card is None:
                for parent in a.iterancestors():
                    if parent.xpath('.//img[@src or @data-src]'):
                        card = parent
                        break
            name = ''
            if card is not None:
                title_nodes = card.xpath(
                    './/*[contains(@class,"card__title")]'
                    ' | .//h2[normalize-space()] | .//h3[normalize-space()]'
                )
                for node in title_nodes:
                    text = self._text(node)
                    if len(text) > len(name):
                        name = text
            if not name:
                name = self._text(a)
            if not name and card is not None:
                attrs = card.xpath(
                    './/a[contains(@href,"/v/")]/@title'
                    ' | .//img/@alt | .//img/@title'
                )
                name = next((re.sub(r'\s+', ' ', str(x)).strip() for x in attrs if str(x).strip()), '')
            if not name:
                continue
            pic = ''
            remark = ''
            if card is not None:
                pics = card.xpath('.//img/@src | .//img/@data-src')

                pic = urljoin(self.host, pics[0]) if pics else ''
                dur = card.xpath('.//*[contains(@class,"card__dur")]/text()')
                meta = card.xpath('.//*[contains(@class,"card__meta")]//text()[normalize-space()]')
                remark = re.sub(r'\s+', ' ', dur[0]).strip() if dur else ''
                if not remark and meta:
                    remark = re.sub(r'\s+', ' ', ' '.join(meta)).strip()
            seen.add(vid)
            result.append({'vod_id': vid, 'vod_name': name, 'vod_pic': pic, 'vod_remarks': remark})
        return result

    def _directory_cards(self, doc, kind):
        if doc is None:
            return []
        selectors = {
            'genres': '//a[contains(@class,"gchip") and contains(@href,"/genres/")]',
            'actresses': '//div[contains(@class,"actress")][.//a[contains(@href,"/actresses/")]]',
            'makers': '//main//a[contains(@class,"mcard") and contains(@href,"/makers/")]',
            'series': '//a[contains(@class,"srow") and contains(@href,"/series/")]',
        }
        result, seen = [], set()
        for node in doc.xpath(selectors.get(kind, '')):
            links = node.xpath('.//a[contains(@href,"/%s/")]/@href' % kind) if node.tag != 'a' else [node.get('href')]
            href = next((str(x) for x in links if x), '')
            if not href or href in seen:
                continue
            seen.add(href)
            if kind == 'genres':
                names = node.xpath('.//*[contains(@class,"gchip__name")]/text()')
                remarks = node.xpath('.//*[contains(@class,"gchip__count")]/text()')
            elif kind == 'actresses':
                names = node.xpath('.//*[contains(@class,"actress__name")]//text()')
                remarks = node.xpath('.//*[contains(@class,"actress__meta")]//text()')
            elif kind == 'makers':
                names = node.xpath('.//*[contains(@class,"mcard__name")]//text()')
                remarks = node.xpath('.//*[contains(@class,"mcard__meta")]//text()')
            else:
                names = node.xpath('.//*[contains(@class,"srow__name")]//text()')
                remarks = node.xpath('.//*[contains(@class,"srow__meta")]//text()')
            name = re.sub(r'\s+', ' ', ''.join(names)).strip()
            remark = re.sub(r'\s+', ' ', ' '.join(remarks)).strip()
            pic = ''
            styles = node.xpath('.//@style')
            for style in styles:
                m = re.search(r"background-image\s*:\s*url\(['\"]?([^'\")]+)", style)
                if m:
                    pic = urljoin(self.host, m.group(1))
                    break
            if name:
                result.append({'vod_id': 'route:' + href, 'vod_name': name, 'vod_pic': pic,
                               'vod_remarks': remark or '进入目录', 'vod_tag': 'folder'})
        return result

    def homeVideoContent(self):
        doc = self._dom(self._get(self.host + self.locale + '/new'))
        return {'list': self._cards(doc)[:24]}

    def _route(self, tid):
        tid = str(tid or '')
        if tid in ('today', 'week', 'month'):
            return self.locale + '/all', {'sort': tid}
        if tid.startswith('search:'):
            return self.locale + '/search', {'keyword': tid[7:]}
        directories = {
            'genres_dir': self.locale + '/genres', 'actresses_dir': self.locale + '/actresses',
            'makers_dir': self.locale + '/makers', 'series_dir': self.locale + '/series'}
        if tid in directories:
            return directories[tid], {}
        if tid == 'trend_group':
            return self.locale + '/all', {'sort': 'today'}
        if tid == 'type_group':
            return self.locale + '/censored', {}
        if tid == 'collection_group':
            return self.locale + '/genres', {}
        if tid == 'amateur_group':
            return self.locale + '/tags/siro', {}
        if tid == 'uncensored_group':
            return self.locale + '/makers/fc2', {}
        if tid in {x['type_id'] for x in self.classes}:
            return self.locale + '/' + tid, {}
        if tid.startswith('route:'):
            return unquote(tid[6:]), {}
        return self.locale + '/new', {}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        page = max(1, int(pg or 1))
        path, params = self._route(self._normalize_tid(tid))
        ext = self._extend(extend)
        normalized_tid = self._normalize_tid(tid)
        directory_kind = {'genres_dir': 'genres', 'actresses_dir': 'actresses',
                          'makers_dir': 'makers', 'series_dir': 'series'}.get(normalized_tid)
        grouped = ('trend_group', 'type_group', 'collection_group', 'amateur_group', 'uncensored_group')
        if normalized_tid in grouped and ext.get('cate_id'):
            selected = urlparse(str(ext.get('cate_id')))
            path = selected.path
            params.update(dict(parse_qsl(selected.query)))
        if normalized_tid == 'collection_group':
            directory_kind = next((x for x in ('genres', 'actresses', 'makers', 'series')
                                   if path.rstrip('/').endswith('/' + x)), 'genres')
        keys = ('height', 'cup', 'age', 'sort') if directory_kind else ('year', 'actress', 'sort')
        for key in keys:
            val = ext.get(key)
            if val not in (None, ''):
                params[key] = str(val)
        params['page'] = page
        url = urljoin(self.host, path) + '?' + urlencode(params)
        doc = self._dom(self._get(url))
        items = self._directory_cards(doc, directory_kind) if directory_kind else self._cards(doc)
        pagecount = 1 if directory_kind == 'genres' else self._pagecount(doc, page, len(items))
        limit = len(items) if directory_kind else 12
        total = len(items) if directory_kind == 'genres' else (int(pagecount * limit) if pagecount else 0)
        return {'list': items, 'page': page, 'pagecount': int(pagecount), 'limit': int(limit),
                'total': int(total)}

    def _normalize_tid(self, tid):
        if isinstance(tid, dict):
            return str(tid.get('id') or tid.get('name') or '')
        raw = unquote(str(tid or '').strip())
        if raw.startswith('{') and raw.endswith('}'):
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict):
                    raw = str(obj.get('id') or obj.get('name') or '')
            except Exception:
                pass
        return raw

    def _rich(self, name, path):
        name = str(name or '').strip()
        if not name or not path:
            return name
        route_id = path if str(path).startswith('search:') else 'route:' + path
        payload = json.dumps({'id': route_id, 'name': name}, ensure_ascii=False, separators=(',', ':'))
        return '[a=cr:{}/]{}[/a]'.format(payload, name)

    def _detail_pairs(self, doc):
        pairs = {}
        if doc is None:
            return pairs
        for row in doc.xpath('//dl[contains(@class,"watch__info")]/*[self::div or self::li]'):
            dt = row.xpath('./dt')
            dd = row.xpath('./dd')
            if dt and dd:
                pairs[self._text(dt[0]).strip(' ：:')] = self._text(dd[0]).strip()
                continue
            text = self._text(row)
            for key in ('代码', '类型', '发布日期', '时长', '演员', '制作商', '类别', '标签'):
                if text.startswith(key) and len(text) > len(key):
                    pairs.setdefault(key, text[len(key):].strip(' ：:'))
        return pairs

    def _episode_data(self, raw):
        m = re.search(r"player\(JSON\.parse\('(.+?)'\)", raw or '', re.S)
        if not m:
            return []
        text = m.group(1)
        try:
            text = bytes(text, 'utf-8').decode('unicode_escape')
            return json.loads(text)
        except Exception:
            try:
                text = re.sub(r'\\+/', '/', text)
                text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda x: chr(int(x.group(1), 16)), text)
                return json.loads(text)
            except Exception as e:
                self.log('播放入口JSON失败: %s' % e)
                return []

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, list) and ids else ids
        path = self._normalize_tid(raw_id)
        if path.startswith('route:'):
            return {'list': []}
        if not path.startswith('/'):
            path = self.locale + '/v/' + path
        url = urljoin(self.host, path)
        content = self._get(url)
        doc = self._dom(content)
        if doc is None:
            return {'list': []}
        title_nodes = doc.xpath('//h1[contains(@class,"watch__title")] | //h1')
        name = self._text(title_nodes[0]) if title_nodes else path.rsplit('/', 1)[-1]
        pic = ''
        styles = doc.xpath('//*[contains(@class,"player")]/@style')
        if styles:
            m = re.search(r"url\(['\"]?([^'\")]+)", styles[0])
            if m:
                pic = urljoin(url, m.group(1))
        if not pic:
            og = doc.xpath('//meta[@property="og:image"]/@content')
            pic = urljoin(url, og[0]) if og else ''
        pairs = self._detail_pairs(doc)
        actor_links, maker_links, genre_links = [], [], []
        info = doc.xpath('//dl[contains(@class,"watch__info")]')
        panel = info[0] if info else None
        if panel is not None:
            for a in panel.xpath('.//a[contains(@href,"/actresses/")]'):
                actor_links.append(self._rich(self._text(a), a.get('href')))
            for a in panel.xpath('.//a[contains(@href,"/makers/")]'):
                maker_links.append(self._rich(self._text(a), a.get('href')))
            for a in panel.xpath('.//a[contains(@href,"/genres/")] | .//a[contains(@href,"/tags/")]'):
                genre_links.append(self._rich(self._text(a), a.get('href')))
        episodes = self._episode_data(content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else str(content))
        play = []
        for i, ep in enumerate(episodes):
            if not isinstance(ep, dict) or not ep.get('url'):
                continue
            label = str(ep.get('name') or ep.get('number') or i + 1)
            play.append(label + '$' + str(ep['url']).replace('$', '%24'))
        if not play:
            return {'list': []}
        code = pairs.get('代码') or name.split('—', 1)[0].strip()
        code_prefix = re.split(r'[-_\s]', code, 1)[0].casefold()
        genre_links = [x for x in genre_links if re.sub(r'^.*?\]\s*|\[/a\]$', '', x).strip().casefold() != code_prefix]
        code_link = self._rich(code, 'search:' + code)
        content_text = ' '.join(genre_links)
        vod = {
            'vod_id': path, 'vod_name': name, 'vod_pic': pic,
            'vod_remarks': pairs.get('时长', ''), 'vod_year': pairs.get('发布日期', '')[:4],
            'vod_area': pairs.get('类型', ''), 'vod_actor': ' '.join(dict.fromkeys(actor_links)),
            'vod_director': ' '.join(dict.fromkeys(maker_links)),
            'vod_content': ('番号：%s\n%s' % (code_link, content_text)).strip(),
            'vod_play_from': 'JavPlayer', 'vod_play_url': '#'.join(play)
        }
        return {'list': [vod]}

    def searchContent(self, key, quick=False, pg='1'):
        page = max(1, int(pg or 1))
        url = self.host + self.locale + '/search?' + urlencode({'keyword': str(key or ''), 'page': page})
        return {'list': self._cards(self._dom(self._get(url)))}

    def playerContent(self, flag, id, vipFlags=None):
        play_url = unquote(str(id or '').replace('%24', '$'))
        for _ in range(3):
            fixed = play_url.replace('\\/', '/').replace('\\\\', '\\')
            if fixed == play_url:
                break
            play_url = fixed
        if self.isVideoFormat(play_url):
            return {'parse': 0, 'jx': 0, 'url': play_url, 'header': {'User-Agent': self.ua}}
        m = re.search(r'https?://javplayer\.cc/e/([a-z0-9_]+)', play_url, re.I)
        if not m:
            self.log('播放失败: 未识别播放入口 %s' % play_url[:160])
            return {'parse': 1, 'jx': 0, 'url': play_url}
        code = m.group(1)
        api = 'https://javplayer.cc/stream?' + urlencode({'id': code})
        content = self._get(api, {'Referer': 'https://javplayer.cc/e/' + code, 'Origin': 'https://javplayer.cc'})
        try:
            text = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else str(content)
            data = json.loads(text)
            media = data.get('media') if isinstance(data, dict) else None
            stream = media.get('stream') if isinstance(media, dict) else ''
            if stream:
                return {'parse': 0, 'jx': 0, 'url': stream,
                        'header': {'User-Agent': self.ua, 'Referer': 'https://javplayer.cc/'}}
            self.log('播放失败: stream接口无媒体')
        except Exception as e:
            self.log('播放失败: stream接口JSON异常 %s' % e)
        return {'parse': 1, 'jx': 0, 'url': play_url}

    def recommendContent(self, ids, pg=1):
        raw_id = ids[0] if isinstance(ids, list) and ids else ids
        path = self._normalize_tid(raw_id)
        if not path.startswith('/'):
            return {'list': []}
        doc = self._dom(self._get(urljoin(self.host, path)))
        if doc is None:
            return {'list': []}
        result, seen = [], set()
        for a in doc.xpath('//a[contains(@class,"vside") and contains(@href,"/v/")]'):
            href = a.get('href') or ''
            if href in seen or href == path:
                continue
            seen.add(href)
            name_nodes = a.xpath('.//*[contains(@class,"vside__title")]')
            name = self._text(name_nodes[0]) if name_nodes else self._text(a)
            pics = a.xpath('.//img/@src | .//img/@data-src')
            pic = urljoin(self.host, pics[0]) if pics else ''
            if not pic:
                styles = a.xpath('.//*[contains(@class,"vside__thumb")]/@style')
                if styles:
                    m = re.search(r"url\(['\"]?([^'\")]+)", styles[0])
                    pic = urljoin(self.host, m.group(1)) if m else ''
            result.append({'vod_id': href, 'vod_name': name, 'vod_pic': pic, 'vod_remarks': ''})
        return {'list': result}