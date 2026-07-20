# coding: utf-8
# 大片工程 - TVBox爬虫源
# 站点: https://pog.dpgc4.beauty/cn/home/web/
# 版本: v3.2 - 移除gzip压缩，简化请求

from base.spider import Spider
import re
import json
import urllib.request
import urllib.parse
import ssl


class Spider(Spider):
    def getName(self):
        return '大片工程'

    def __init__(self):
        self.base = "https://pog.dpgc4.beauty"
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.classes = [
            {"type_id": "20", "type_name": "国产自拍"},
            {"type_id": "21", "type_name": "强奸乱伦"},
            {"type_id": "22", "type_name": "男同女同"},
            {"type_id": "23", "type_name": "重口味"},
            {"type_id": "24", "type_name": "日本AV"},
            {"type_id": "25", "type_name": "无码视频"},
            {"type_id": "26", "type_name": "有码视频"},
            {"type_id": "27", "type_name": "中文字幕"},
            {"type_id": "28", "type_name": "欧美极品"},
            {"type_id": "29", "type_name": "三级伦理"},
            {"type_id": "30", "type_name": "动漫精品"}
        ]
        self.filters = {c["type_id"]: [] for c in self.classes}
        self.headers = {
            'User-Agent': self.ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.base + '/'
        }
        self.cookies = {}

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

    def _fetch(self, url):
        """使用 urllib.request 获取HTML（不压缩）"""
        if not url.startswith('http'):
            url = self.base + url if url.startswith('/') else self.base + '/' + url

        try:
            req = urllib.request.Request(url, headers=self.headers)
            if self.cookies:
                cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
                req.add_header('Cookie', cookie_str)

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=15, context=context) as resp:
                content = resp.read()

                # 保存 Cookie
                cookie_header = resp.info().get('Set-Cookie', '')
                if cookie_header:
                    for cookie in cookie_header.split(','):
                        if '=' in cookie:
                            parts = cookie.strip().split(';')[0].split('=', 1)
                            if len(parts) == 2:
                                self.cookies[parts[0]] = parts[1]

                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            return ''

    def _post(self, url, data):
        """POST请求"""
        if not url.startswith('http'):
            url = self.base + url if url.startswith('/') else self.base + '/' + url

        try:
            post_data = urllib.parse.urlencode(data).encode('utf-8')
            h = dict(self.headers)
            h['Content-Type'] = 'application/x-www-form-urlencoded'
            req = urllib.request.Request(url, data=post_data, headers=h)

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=15, context=context) as resp:
                content = resp.read()
                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            return ''

    def fix_url(self, url):
        if not url:
            return ''
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.base + url
        return self.base + '/' + url

    def _parse_videos(self, html):
        videos = []
        if not html:
            return videos

        items = re.findall(r'<li class="thumb item">(.*?)</li>', html, re.DOTALL)
        for item in items:
            try:
                link_match = re.search(r'<a href="([^"]+)"', item)
                if not link_match:
                    continue
                url = link_match.group(1)

                img_match = re.search(r'<img[^>]+(?:data-original|src)="([^"]+)"', item)
                pic = img_match.group(1) if img_match else ''

                title_match = re.search(r'<span class="title">([^<]+)</span>', item)
                title = title_match.group(1).strip() if title_match else ''

                date_match = re.search(r'<span class="added">([^<]+)</span>', item)
                date = date_match.group(1).strip() if date_match else ''

                if not title:
                    continue

                vod_id = self._extract_vod_id(url)
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': title,
                    'vod_pic': self.fix_url(pic),
                    'vod_remarks': date
                })
            except Exception as e:
                continue

        seen = set()
        result = []
        for v in videos:
            if v['vod_id'] not in seen:
                seen.add(v['vod_id'])
                result.append(v)
        return result

    def _extract_vod_id(self, url):
        match = re.search(r'id/(\d+)/', url)
        if match:
            return match.group(1)
        match = re.search(r'/(\d+)(?:\.html|/)', url)
        return match.group(1) if match else '0'

    def _get_page_count(self, html):
        pattern = r'<span[^>]*>(\d+)\s*/\s*(\d+)</span>'
        match = re.search(pattern, html)
        if match:
            return int(match.group(2))
        pattern = r'<a[^>]*href="[^"]*page/(\d+)\.html"[^>]*>尾页</a>'
        matches = re.findall(pattern, html)
        if matches:
            return int(matches[-1])
        return 1

    def _get_player_url(self, html):
        """
        从 player_data 提取播放地址
        直接用正则提取 url 字段，避免 JSON 解析转义问题
        """
        if not html:
            return None

        # 方法1: 提取 player_data 中的 url
        match = re.search(r'var player_data=({[^;]+});', html)
        if match:
            # 用正则提取 url 字段的值
            url_match = re.search(r'"url":"([^"]+)"', match.group(1))
            if url_match:
                url = url_match.group(1).replace('\\/', '/')
                if url.startswith('http'):
                    return url

        # 方法2: 直接搜索 m3u8 链接
        m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if m3u8_match:
            return m3u8_match.group(0)

        return None

    def _extract_title(self, html):
        pattern = r'<li>([^<]+)</li>'
        matches = re.findall(pattern, html)
        for m in matches:
            m = m.strip()
            if m and 'https://' not in m and '大片工程' not in m and '永久网址' not in m:
                return m
        return ''

    def _extract_pic(self, html):
        pattern = r'<img[^>]+(?:data-original|src)="([^"]+)"[^>]+class="[^"]*lazy[^"]*"'
        matches = re.findall(pattern, html)
        for pic in matches:
            if 'upload/vod' in pic or 'jpg' in pic.lower() or 'png' in pic.lower():
                return self.fix_url(pic)
        return ''

    def _extract_description(self, html):
        pattern = r'<meta name="description" content="([^"]+)"'
        match = re.search(pattern, html)
        return match.group(1) if match else ''

    def homeContent(self, filter=False):
        try:
            html = self._fetch('/cn/home/web/')
            videos = self._parse_videos(html)
            return {"class": self.classes, "filters": self.filters, "list": videos[:40]}
        except Exception as e:
            return {"class": self.classes, "filters": self.filters, "list": []}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            html = self._fetch('/cn/home/web/')
            videos = self._parse_videos(html)
            return {'list': videos[:30]}
        except Exception as e:
            return {'list': []}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        result = {'list': [], 'page': 1, 'pagecount': 1, 'limit': 20, 'total': 0}
        try:
            pg = pg or '1'
            url = f"/cn/home/web/index.php/vod/type/id/{tid}/page/{pg}.html"
            html = self._fetch(url)
            videos = self._parse_videos(html)
            result['list'] = videos
            result['page'] = int(pg)
            result['pagecount'] = self._get_page_count(html)
            result['limit'] = 20
            result['total'] = len(videos)
        except Exception as e:
            pass
        return result

    def detailContent(self, ids):
        result = {'list': []}
        try:
            if isinstance(ids, str):
                ids = [ids]

            for vod_id in ids:
                url = f"/cn/home/web/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
                html = self._fetch(url)

                title = self._extract_title(html) or '未知标题'
                pic = self._extract_pic(html)
                desc = self._extract_description(html) or ''

                play_url = self._get_player_url(html)

                if play_url:
                    play_from = "直链"
                    play_urls = f"{play_from}${play_url}"
                else:
                    play_from = "直链"
                    play_urls = f"{play_from}${vod_id}"

                result['list'].append({
                    'vod_id': vod_id,
                    'vod_name': title,
                    'vod_pic': pic,
                    'vod_content': desc,
                    'vod_play_from': play_from,
                    'vod_play_url': play_urls
                })

        except Exception as e:
            pass
        return result

    def searchContent(self, key, quick=False, pg=None):
        result = {'list': [], 'pagecount': 1}
        try:
            if not key:
                return result
            pg = pg or '1'
            url = f"/cn/home/web/index.php/vod/search.html"
            data = {'wd': key, 'page': pg}
            html = self._post(url, data)
            videos = self._parse_videos(html)
            result['list'] = videos
            result['pagecount'] = self._get_page_count(html) or 1
        except Exception as e:
            pass
        return result

    def playerContent(self, flag, id, vipFlags=None):
        try:
            # 如果 id 是完整 m3u8/mp4 URL，直接返回直链
            if id.startswith('http'):
                if '.m3u8' in id or '.mp4' in id or '.flv' in id:
                    return {
                        'parse': 0,
                        'url': id,
                        'header': {
                            'User-Agent': self.ua,
                            'Referer': self.base + '/'
                        }
                    }

            # 如果 id 是 vod_id，请求播放页提取
            url = f"/cn/home/web/index.php/vod/play/id/{id}/sid/1/nid/1.html"
            html = self._fetch(url)

            if not html:
                return {'parse': 1, 'url': self.base + url}

            play_url = self._get_player_url(html)

            if play_url:
                return {
                    'parse': 0,
                    'url': play_url,
                    'header': {
                        'User-Agent': self.ua,
                        'Referer': self.base + '/'
                    }
                }

            # 降级到 WebView 嗅探
            return {'parse': 1, 'url': self.base + url}

        except Exception as e:
            return {'parse': 1, 'url': id}

    def localProxy(self, params=None):
        pass