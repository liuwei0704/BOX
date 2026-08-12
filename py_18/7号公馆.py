# -*- coding: utf-8 -*-
import re
import json
import base64
import urllib.parse
import posixpath
from urllib.parse import urljoin, quote, unquote, urlparse
from bs4 import BeautifulSoup

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://lu.7hggtret.cfd"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.host + '/'
        }
        self.classes = [
            {"type_id": "66", "type_name": "偷拍"},
            {"type_id": "67", "type_name": "无码"},
            {"type_id": "50", "type_name": "中文"},
            {"type_id": "51", "type_name": "多人"},
            {"type_id": "68", "type_name": "巨乳"},
            {"type_id": "69", "type_name": "制服"},
            {"type_id": "54", "type_name": "伦理"},
            {"type_id": "55", "type_name": "亚洲"}
        ]
        self.filters = {}

    def getName(self):
        return "7号公馆"

    def getDependence(self):
        return ['bs4']

    def init(self, extend=""):
        pass

    def destroy(self):
        pass

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        if not url:
            return ""
        url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + quote(str(url), safe="")

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
        m = re.search(r'/detail/id/(\d+)\.html', url)
        if m:
            return m.group(1)
        return url

    def _parse_video_items(self, items, limit=999):
        videos = []
        for item in items:
            a = item.find('a', class_='stui-vodlist__thumb')
            if not a:
                continue
            href = a.get('href', '')
            vid = self._extract_vod_id(href)
            title = a.get('title', '')
            if not title:
                title_a = item.find('h4', class_='stui-vodlist__title')
                if title_a:
                    title = title_a.text.strip()
            pic = a.get('data-original', '')
            if pic:
                pic = self.fix_url(pic)
            remark = ''
            span = a.find('span', class_='pic-text')
            if span:
                remark = span.text.strip()
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

    def homeContent(self, filter=False):
        return {'class': self.classes, 'filters': self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html(self.host + '/')
        if not html:
            return {'list': []}
        doc = BeautifulSoup(html, 'html.parser')
        items = doc.find_all('li', class_='stui-vodlist__item')
        videos = self._parse_video_items(items, 15)
        return {'list': videos}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        pg = int(pg) if pg else 1
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
        html = self._fetch_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 20, 'total': 0}
        doc = BeautifulSoup(html, 'html.parser')
        items = doc.find_all('li', class_='stui-vodlist__item')
        videos = self._parse_video_items(items)

        pagecount = 1
        pagination = doc.find('ul', class_='stui-page')
        if pagination:
            for a in pagination.find_all('a'):
                if a.text.strip().isdigit():
                    num = int(a.text.strip())
                    if num > pagecount:
                        pagecount = num
            last = pagination.find('a', string='尾页')
            if last:
                m = re.search(r'/page/(\d+)\.html', last.get('href', ''))
                if m:
                    pagecount = int(m.group(1))
            active_span = pagination.find('span', class_='num')
            if active_span:
                m = re.search(r'(\d+)/(\d+)', active_span.text)
                if m:
                    pagecount = int(m.group(2))

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
        if isinstance(ids, int):
            vid = str(ids)
        elif isinstance(ids, list) and ids:
            vid = str(ids[0])
        elif isinstance(ids, str):
            vid = ids
        else:
            return {'list': []}
        url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
        html = self._fetch_html(url)
        if not html:
            return {'list': []}
        doc = BeautifulSoup(html, 'html.parser')

        title = ''
        title_h3 = doc.find('h3', class_='title')
        if title_h3:
            title = title_h3.text.strip()

        pic = ''
        img = doc.find('img', class_='img-responsive lazyload')
        if img:
            pic = img.get('data-original', '')
            if pic:
                pic = self.fix_url(pic)

        desc = ''
        desc_div = doc.find('div', class_='stui-content__desc')
        if desc_div:
            desc = desc_div.text.strip()

        category = ''
        type_a = doc.find('a', href=re.compile(r'/vod/type/id/\d+\.html'))
        if type_a:
            category = type_a.text.strip()

        playlist_ul = doc.find('ul', class_='stui-content__playlist')
        play_urls = []
        if playlist_ul:
            for li in playlist_ul.find_all('li'):
                a = li.find('a')
                if a:
                    href = a.get('href', '')
                    name = a.text.strip()
                    m = re.search(r'/play/id/(\d+)/sid/(\d+)/nid/(\d+)\.html', href)
                    if m:
                        play_id = f"{m.group(1)}|sid|{m.group(2)}|nid|{m.group(3)}"
                    else:
                        play_id = href
                    if name and play_id:
                        play_urls.append(f"{name}${play_id}")

        if play_urls:
            play_from = "默认线路"
            play_url_str = '#'.join(play_urls)
        else:
            play_from = ""
            play_url_str = ""

        data = {
            'vod_id': vid,
            'vod_name': title or '未知标题',
            'vod_pic': pic,
            'vod_content': desc,
            'vod_actor': '',
            'vod_remarks': category,
            'vod_play_from': play_from,
            'vod_play_url': play_url_str,
        }
        return {'list': [data]}

    def searchContent(self, key, quick=False, pg='1'):
        if not key:
            return {'list': [], 'page': 1, 'pagecount': 1, 'total': 0}
        pg = int(pg) if pg else 1
        encoded_key = quote(key)
        url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{encoded_key}.html"
        html = self._fetch_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}
        doc = BeautifulSoup(html, 'html.parser')
        items = doc.find_all('li', class_='stui-vodlist__item')
        videos = self._parse_video_items(items)

        pagecount = 1
        pagination = doc.find('ul', class_='stui-page')
        if pagination:
            active_span = pagination.find('span', class_='num')
            if active_span:
                m = re.search(r'(\d+)/(\d+)', active_span.text)
                if m:
                    pagecount = int(m.group(2))
            last = pagination.find('a', string='尾页')
            if last:
                m = re.search(r'/page/(\d+)/', last.get('href', ''))
                if m:
                    pagecount = int(m.group(1))

        return {
            'list': videos,
            'page': pg,
            'pagecount': pagecount,
            'total': pagecount * 20
        }

    def playerContent(self, flag, id, vipFlags=None):
        if not id:
            return {'parse': 1, 'url': ''}

        # 如果是直链，走代理
        if id.startswith('http') and ('.m3u8' in id or '.mp4' in id):
            return {
                'parse': 0,
                'url': self._m3u8_proxy_url(id),
                'header': {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': self.host + '/'
                }
            }

        # 解析播放页获取m3u8
        if '|sid|' in id and '|nid|' in id:
            parts = id.split('|')
            vid = parts[0]
            sid = parts[2]
            nid = parts[4]
            play_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/{sid}/nid/{nid}.html"
        elif id.startswith('/'):
            play_url = self.fix_url(id)
        elif id.startswith('http'):
            play_url = id
        else:
            play_url = f"{self.host}/index.php/vod/play/id/{id}/sid/1/nid/1.html"

        html = self._fetch_html(play_url)
        if not html:
            return {'parse': 1, 'url': play_url, 'header': self.headers}

        # 提取player_aaaa中的url
        m = re.search(r'var\s+player_aaaa\s*=\s*({[^}]+})', html)
        if m:
            try:
                player_data = json.loads(m.group(1))
                real_url = player_data.get('url', '')
                if real_url:
                    if real_url.startswith('//'):
                        real_url = 'https:' + real_url
                    if real_url.startswith('/'):
                        real_url = self.fix_url(real_url)
                    if '.m3u8' in real_url or '.mp4' in real_url:
                        return {
                            'parse': 0,
                            'url': self._m3u8_proxy_url(real_url),
                            'header': {
                                'User-Agent': self.headers['User-Agent'],
                                'Referer': self.host + '/'
                            }
                        }
            except:
                pass

        # 尝试直接搜索m3u8
        m = re.search(r'https?://[^"\']+\.m3u8[^"\']*', html)
        if m:
            return {
                'parse': 0,
                'url': self._m3u8_proxy_url(m.group(0)),
                'header': {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': self.host + '/'
                }
            }

        return {'parse': 1, 'url': play_url, 'header': self.headers}

    def _fetch_html(self, url, params=None):
        """统一获取HTML内容"""
        full_url = url
        if params:
            if "?" in url:
                full_url = url + "&" + urllib.parse.urlencode(params)
            else:
                full_url = url + "?" + urllib.parse.urlencode(params)
        try:
            resp = self.fetch(full_url, headers=self.headers, timeout=15)
            if resp and hasattr(resp, "status_code") and resp.status_code == 200:
                return resp.text
            if resp and hasattr(resp, "text"):
                return resp.text
        except:
            pass
        return ""

    def localProxy(self, param):
        """
        TVBox/FongMi 本地代理接口
        """
        try:
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")

            if "url=" in target:
                parsed = urlparse(target)
                query = urllib.parse.parse_qs(parsed.query)
                if "url" in query:
                    target = query["url"][0]
                elif "source" in query:
                    target = query["source"][0]

            target = unquote(target)

            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            # 非m3u8直接透传
            if not target.endswith(".m3u8") and "m3u8" not in target.lower():
                resp = self.fetch(target, headers=self.headers, timeout=10)
                if resp and hasattr(resp, "status_code") and resp.status_code == 200:
                    return [200, resp.headers.get("Content-Type", "application/octet-stream"), resp.content]
                return [404, "text/plain", b"not found"]

            # 请求m3u8 - 增加超时和重试
            headers = {
                "User-Agent": self.headers.get("User-Agent", ""),
                "Referer": self.host + "/"
            }
            resp = self.fetch(target, headers=headers, timeout=20)
            if not resp or not hasattr(resp, "status_code") or resp.status_code != 200:
                return [502, "text/plain", b"fetch failed"]

            content = resp.text if hasattr(resp, "text") else resp.content.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in content:
                return [502, "text/plain", b"invalid m3u8"]

            cleaned = self._clean_m3u8(content, target)
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

        except Exception as e:
            return [500, "text/plain", f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")]

    def _clean_m3u8(self, text, source_url):
        """清洗m3u8 - 过滤广告分片"""
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"

        parsed = urlparse(source_url)
        source_dir = posixpath.dirname(parsed.path)
        if not source_dir.endswith("/"):
            source_dir += "/"

        main_dir = source_dir
        for line in lines:
            if line.startswith("#EXT-X-KEY") and "URI=" in line:
                uri_match = re.search(r'URI="([^"]+)"', line)
                if uri_match:
                    key_path = uri_match.group(1)
                    if not key_path.startswith("http"):
                        key_dir = posixpath.dirname(key_path)
                        if key_dir and key_dir != "/":
                            main_dir = key_dir + "/"
                            break

        segments = []
        pending = []

        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media_url = urljoin(source_url, line)
                media_parsed = urlparse(media_url)
                is_ad = not media_parsed.path.startswith(main_dir)
                if not is_ad:
                    segments.extend(pending)
                    segments.append(media_url)
                pending = []
                continue

            if not line.startswith("#"):
                segments.append(urljoin(source_url, line))
            else:
                segments.append(line)

        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in ("#EXT-X-KEY:METHOD=NONE", "#EXT-X-DISCONTINUITY"):
                if not out or out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
                    continue
            out.append(line)

        while len(out) > 1 and out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
            out.pop()

        return "\n".join(out) + "\n"

    def _rewrite_m3u8_tag(self, line, source_url):
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(match):
                uri = match.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)

        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urljoin(source_url, line)

        return line