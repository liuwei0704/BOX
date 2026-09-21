# -*- coding: utf-8 -*-
"""
TVBox 爬虫源 - 11奶 (hc2.34nai.sbs)
站点类型: 成人影视/图片/小说综合站
最后更新: 2026-07-12
接口版本: 严格对齐 SPIDER.md 规范
"""

import re
import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, List, Optional


class Spider:
    """11奶 爬虫源"""

    # ========== 基本配置 ==========
    def __init__(self):
        self.homeUrl = "https://hc2.34nai.sbs"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.homeUrl,
        }
        self.timeout = 10
        self.max_retries = 3
        self._class_cache = []
        self._class_map = {}

    # ========== init 接口 ==========

    def init(self, extend: str = "") -> None:
        if extend:
            try:
                ext_data = json.loads(extend)
                self.timeout = ext_data.get('timeout', self.timeout)
                self.max_retries = ext_data.get('max_retries', self.max_retries)
            except:
                pass

    # ========== 依赖声明 ==========

    def getDependence(self):
        return ['urllib']

    # ========== 核心请求方法 ==========

    def fetch(self, url, headers=None, method='GET', data=None, json_data=None, timeout=None):
        if headers is None:
            headers = {}
        if timeout is None:
            timeout = self.timeout

        req_headers = self.headers.copy()
        req_headers.update(headers)

        post_data = None
        if method.upper() == 'POST':
            if json_data:
                post_data = json.dumps(json_data).encode('utf-8')
                req_headers['Content-Type'] = 'application/json'
            elif data:
                post_data = urllib.parse.urlencode(data).encode('utf-8')
                req_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        try:
            request = urllib.request.Request(url, data=post_data, headers=req_headers, method=method.upper())
            response = urllib.request.urlopen(request, timeout=timeout)

            class Response:
                pass
            resp = Response()
            resp.status_code = response.getcode()
            resp.headers = dict(response.headers)
            resp.text = response.read().decode('utf-8', errors='ignore')
            resp.content = response.read()
            return resp
        except Exception as e:
            print(f"[ERROR] fetch: {e}")
            return None

    def fix_url(self, url, base_url=None):
        if not url:
            return ''
        url = url.strip()
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            base = base_url or self.homeUrl
            base = base.rstrip('/')
            return base + url
        if base_url:
            base = base_url.rsplit('/', 1)[0]
            return base + '/' + url.lstrip('/')
        return self.homeUrl.rstrip('/') + '/' + url.lstrip('/')

    # ========== 解析工具方法 ==========

    def _extract_text(self, html, pattern, default=''):
        match = re.search(pattern, html, re.DOTALL)
        if match:
            return match.group(1).strip()
        return default

    def _extract_vod_id(self, url):
        if url.startswith('/z/'):
            return None
        patterns = [r'/vod/(\d+)', r'/detail/(\d+)', r'/(\d+)\.html']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _extract_episode_id(self, url):
        patterns = [r'/play/(\d+/\d+/\d+)', r'/play/(\d+-\d+-\d+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _parse_video_list(self, html, max_items=20):
        items = []
        pattern = r'<li[^>]*class="[^"]*(?:list_box|box_homecon)[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*timebox[^"]*"[^>]*>([^<]*)</div>.*?</a>.*?<p[^>]*>([^<]+)</p>'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            link, img, date, title = match
            vod_id = self._extract_vod_id(link)
            if vod_id is None:
                continue
            items.append({
                'vod_id': vod_id,
                'vod_name': title.strip(),
                'vod_pic': self.fix_url(img.strip()),
                'vod_remarks': date.strip(),
            })
            if len(items) >= max_items:
                break
        return items

    def _parse_category_classes(self, html):
        classes = []
        filters = {}
        pattern = r'<a[^>]+href="/f/(\d+)/1/"[^>]*>([^<]+)</a>'
        for match in re.finditer(pattern, html):
            cid, name = match.groups()
            name_clean = name.strip()
            if name_clean == '查看更多' or name_clean == '':
                continue
            classes.append({'type_id': cid, 'type_name': name_clean})
        for c in classes:
            filters[c['type_id']] = {}
        return classes, filters

    def _parse_pagination(self, html):
        result = {'page': 1, 'pagecount': 1, 'total': 0}
        match = re.search(r'共(\d+)条数据\s*当前:(\d+)/(\d+)页', html)
        if match:
            total, current, total_pages = match.groups()
            result['total'] = int(total)
            result['page'] = int(current)
            result['pagecount'] = int(total_pages)
        else:
            match2 = re.search(r'当前:(\d+)/(\d+)页', html)
            if match2:
                current, total_pages = match2.groups()
                result['page'] = int(current)
                result['pagecount'] = int(total_pages)
        return result

    # ========== homeContent 接口 ==========

    def homeContent(self, filter: bool = True) -> Dict:
        result = {'class': [], 'filters': {}, 'list': []}
        try:
            resp = self.fetch(self.homeUrl, headers=self.headers, timeout=self.timeout)
            if resp is None:
                return result
            html = resp.text
            classes, filters = self._parse_category_classes(html)
            result['class'] = classes
            if filter:
                result['filters'] = filters
            self._class_cache = classes
            self._class_map = {c['type_id']: c['type_name'] for c in classes}
            video_list = self._parse_video_list(html, max_items=20)
            result['list'] = video_list
        except Exception as e:
            print(f"[ERROR] homeContent: {e}")
        return result

    # ========== homeVideoContent 接口 ==========

    def homeVideoContent(self) -> Dict:
        return self.homeContent(filter=False)

    # ========== categoryContent 接口 ==========

    def categoryContent(self, tid: str, pg: str, filter: bool = True, extend: Dict = None) -> Dict:
        result = {'list': [], 'page': 1, 'pagecount': 1, 'total': 0}

        try:
            if pg is None or pg == '':
                pg = '1'

            url = f"{self.homeUrl}/f/{tid}/{pg}/"

            if extend and isinstance(extend, dict):
                query = urllib.parse.urlencode(extend)
                url = url + '?' + query

            resp = self.fetch(url, headers=self.headers, timeout=self.timeout)
            if resp is None:
                return result
            html = resp.text
            video_list = self._parse_video_list(html, max_items=30)
            result['list'] = video_list
            page_info = self._parse_pagination(html)
            result['page'] = page_info['page']
            result['pagecount'] = page_info['pagecount']
            result['total'] = page_info['total']
        except Exception as e:
            print(f"[ERROR] categoryContent: {e}")
        return result

    # ========== detailContent 接口 ==========

    def detailContent(self, ids: List[str]) -> Dict:
        result = {'list': []}
        try:
            if isinstance(ids, str):
                ids = [ids]
            for vod_id in ids:
                url = f"{self.homeUrl}/vod/{vod_id}/"
                resp = self.fetch(url, headers=self.headers, timeout=self.timeout)
                if resp is None:
                    continue
                html = resp.text

                # 提取标题
                title = self._extract_text(html, r'<div[^>]*class="[^"]*film_title[^"]*"[^>]*>.*?<h4[^>]*>([^<]+)</h4>')
                if not title:
                    title = self._extract_text(html, r'<h4[^>]*>([^<]+)</h4>')
                if not title:
                    title = self._extract_text(html, r'<dd[^>]*class="[^"]*film_title[^"]*"[^>]*>.*?<h4[^>]*>([^<]+)</h4>')
                if not title:
                    title = '未知标题'

                # 提取分类
                category = self._extract_text(html, r'分類[：:]\s*<span[^>]*>([^<]+)</span>')

                # 提取图片
                pic = self._extract_text(html, r'<dt[^>]*>.*?<img[^>]+src="([^"]+)"')
                if not pic:
                    pic = self._extract_text(html, r'<img[^>]+class="[^"]*img_1[^"]*"[^>]+src="([^"]+)"')

                # 线路名称
                play_from = []
                line_match = re.search(r'播放線路[：:]\s*([^<]+)', html)
                if line_match:
                    play_from.append(line_match.group(1).strip())
                else:
                    play_from.append('默认线路')

                # ===== 提取剧集列表 - 支持单引号和双引号 =====
                episode_links = []

                # 方式1: 精确匹配 /play/数字/数字/数字/，支持单引号和双引号
                ep_pattern = r'<a[^>]+href=[\"\'](/play/\d+/\d+/\d+/)[\"\'][^>]*>([^<]+)</a>'
                for match in re.finditer(ep_pattern, html):
                    ep_link = match.group(1)
                    ep_title = match.group(2).strip()
                    if '备用' in ep_title or '永久' in ep_title:
                        continue
                    ep_id = self._extract_episode_id(ep_link)
                    if ep_id:
                        episode_links.append(f"{ep_title}${ep_id}")

                # 方式2: 宽松匹配，支持单引号和双引号
                if not episode_links:
                    ep_pattern2 = r'<a[^>]+href=[\"\'](/play/[^\"\']+)[\"\'][^>]*>([^<]+)</a>'
                    for match in re.finditer(ep_pattern2, html):
                        ep_link = match.group(1)
                        ep_title = match.group(2).strip()
                        if '/play/' in ep_link:
                            if '备用' in ep_title or '永久' in ep_title:
                                continue
                            ep_id = self._extract_episode_id(ep_link)
                            if ep_id:
                                episode_links.append(f"{ep_title}${ep_id}")

                # 去重
                if episode_links:
                    seen = set()
                    unique_links = []
                    for link in episode_links:
                        if link not in seen:
                            seen.add(link)
                            unique_links.append(link)
                    play_url = ['$$$'.join(unique_links)]
                else:
                    play_url = ['']

                result['list'].append({
                    'vod_id': vod_id,
                    'vod_name': title,
                    'vod_pic': self.fix_url(pic) if pic else '',
                    'vod_content': category or '',
                    'vod_play_from': '$$$'.join(play_from),
                    'vod_play_url': '$$$'.join(play_url),
                })
        except Exception as e:
            print(f"[ERROR] detailContent: {e}")
        return result

    # ========== searchContent 接口 ==========

    def searchContent(self, key: str, quick: bool = False, pg: Optional[str] = None) -> Dict:
        result = {'list': []}
        try:
            if not key or key.strip() == '':
                return result

            search_limit = 20 if quick else 30

            url = f"{self.homeUrl}/index.php?m=vod-search"
            data = {'wd': key.strip()}
            if pg and pg != '1':
                data['page'] = pg

            resp = self.fetch(
                url,
                headers={'User-Agent': self.headers['User-Agent'], 'Referer': self.homeUrl},
                method='POST',
                data=data,
                timeout=8
            )
            if resp is None:
                return result
            html = resp.text
            video_list = self._parse_video_list(html, max_items=search_limit)
            result['list'] = video_list
        except Exception as e:
            print(f"[ERROR] searchContent: {e}")
        return result

    # ========== playerContent 接口 ==========

    def playerContent(self, flag: str, id: str, vipFlags: Dict = None) -> Dict:
        # 检测直链
        if id.startswith('http'):
            if any(id.endswith(ext) for ext in ['.m3u8', '.mp4', '.flv', '.m3u']):
                return {"parse": 0, "url": id}

        # 构建播放页 URL
        if id.startswith('/'):
            play_url = self.homeUrl + id
        elif re.match(r'^\d+/\d+/\d+$', id):
            play_url = f"{self.homeUrl}/play/{id}/"
        else:
            play_url = self.fix_url(id)

        try:
            resp = self.fetch(play_url, headers={
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.homeUrl,
            }, timeout=15)
            if resp is None:
                return {"parse": 1, "url": play_url}
            html = resp.text

            # 从 mac_url 变量提取
            mac_url_pattern = r'mac_url\s*=\s*(?:unescape\()?["\']([^"\']+)["\']'
            match = re.search(mac_url_pattern, html)
            if match:
                raw_url = match.group(1)
                try:
                    decoded = re.sub(r'%u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), raw_url)
                    decoded = urllib.parse.unquote(decoded)
                except:
                    decoded = raw_url
                if '$' in decoded:
                    parts = decoded.split('$', 1)
                    video_url = parts[1] if len(parts) > 1 else decoded
                else:
                    video_url = decoded
                if video_url.startswith('http') and any(video_url.endswith(ext) for ext in ['.m3u8', '.mp4', '.flv', '.m3u']):
                    return {"parse": 0, "url": video_url}

            # 从 iframe 提取
            iframe_pattern = r'<iframe[^>]+src="([^"]+)"'
            for match in re.finditer(iframe_pattern, html):
                iframe_url = match.group(1)
                if 'm3u8' in iframe_url or 'v=' in iframe_url:
                    v_match = re.search(r'[?&]v=([^&]+)', iframe_url)
                    if v_match:
                        video_url = urllib.parse.unquote(v_match.group(1))
                        if video_url.startswith('http') and video_url.endswith('.m3u8'):
                            return {"parse": 0, "url": video_url}
                    if iframe_url.endswith('.m3u8'):
                        return {"parse": 0, "url": iframe_url}

            # 其他模式
            other_patterns = [
                r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"',
                r'"src"\s*:\s*"([^"]+\.m3u8[^"]*)"',
                r'videoUrl\s*=\s*"([^"]+\.m3u8[^"]*)"',
                r'now\s*=\s*"([^"]+\.m3u8[^"]*)"',
                r'<source[^>]+src="([^"]+\.m3u8[^"]*)"',
            ]
            for pattern in other_patterns:
                match = re.search(pattern, html)
                if match:
                    video_url = match.group(1)
                    if video_url.startswith('http'):
                        return {"parse": 0, "url": video_url}

            return {"parse": 1, "url": play_url}
        except Exception as e:
            print(f"[ERROR] playerContent: {e}")
            return {"parse": 1, "url": play_url}

    # ========== 其他接口 ==========

    def localProxy(self, param: Dict = None):
        return None

    def isVideoFormat(self, url: str) -> bool:
        if not url:
            return False
        video_exts = ['.m3u8', '.mp4', '.flv', '.m3u', '.ts', '.mkv', '.avi']
        return any(url.lower().endswith(ext) for ext in video_exts)

    def manualVideoCheck(self) -> bool:
        return False

    def destroy(self) -> None:
        self._class_cache = []
        self._class_map = {}