# coding=utf-8
"""
Javchu.com 爬虫源
网站: https://javchu.com/
版本: 2.2 - 移除 H動漫 分类
"""
import re
import json
import urllib.parse
from typing import Dict, List, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request


class Spider:
    def __init__(self):
        self.extend = ""
        self.base_url = "https://javchu.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Referer': 'https://javchu.com/',
        }
        self.timeout = 15

    def getDependence(self):
        return []

    def _fetch_html(self, url: str) -> str:
        try:
            if HAS_REQUESTS:
                resp = requests.get(url, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.text
            else:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"[ERROR] 获取页面失败: {e}")
        return ""

    def _extract_videos(self, html: str) -> List[Dict]:
        videos = []
        if not html or len(html) < 500:
            return videos

        blocks = re.findall(r'<div[^>]*class="video-item-container"[^>]*>.*?</div>\s*</div>\s*</div>', html, re.DOTALL)

        for block in blocks[:30]:
            try:
                title_match = re.search(r'title="([^"]*)"', block)
                title = title_match.group(1) if title_match else ""

                href_match = re.search(r'href="([^"]+)"', block)
                href = href_match.group(1) if href_match else ""

                img_match = re.search(r'<img[^>]*class="main-thumb"[^>]*src="([^"]+)"', block)
                pic = img_match.group(1) if img_match else ""

                if not pic:
                    img_match2 = re.search(r'<img[^>]*src="([^"]+)"', block)
                    pic = img_match2.group(1) if img_match2 else ""

                dur_match = re.search(r'<div[^>]*class="duration"[^>]*>([^<]*)</div>', block)
                duration = dur_match.group(1).strip() if dur_match else ""

                if not title:
                    title_div = re.search(r'<div[^>]*class="title"[^>]*>([^<]*)</div>', block)
                    title = title_div.group(1).strip() if title_div else ""

                vid = re.search(r'v=(\d+)', href) if href else None
                if vid and title:
                    videos.append({
                        'vod_id': vid.group(1),
                        'vod_name': title.strip(),
                        'vod_pic': pic,
                        'vod_remarks': duration
                    })
            except Exception:
                continue

        if not videos:
            pattern = r'<div[^>]*class="video-item-container"[^>]*title="([^"]*)"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*class="main-thumb"[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="duration"[^>]*>([^<]*)</div>'
            matches = re.findall(pattern, html, re.DOTALL)
            for title, href, pic, duration in matches[:30]:
                vid = re.search(r'v=(\d+)', href)
                if vid:
                    videos.append({
                        'vod_id': vid.group(1),
                        'vod_name': title.strip(),
                        'vod_pic': pic,
                        'vod_remarks': duration.strip()
                    })

        return videos

    def _get_category_url(self, tid: str, page: int) -> str:
        """构建分类URL"""
        if tid == '全部':
            url = f"{self.base_url}/search"
            if page > 1:
                url += f"?page={page}"
        elif tid == '中文字幕':
            url = f"{self.base_url}/search?tags[]={urllib.parse.quote(tid)}"
            if page > 1:
                url += f"&page={page}"
        else:
            url = f"{self.base_url}/search?genre={urllib.parse.quote(tid)}"
            if page > 1:
                url += f"&page={page}"
        return url

    def init(self, extend: str = "") -> None:
        if isinstance(extend, list) and len(extend) > 0:
            self.extend = str(extend[0])
        else:
            self.extend = str(extend)
        try:
            if self.extend.startswith('{'):
                config = json.loads(self.extend)
                if config.get('base_url'):
                    self.base_url = config['base_url']
            elif self.extend.startswith('http'):
                self.base_url = self.extend
        except Exception:
            pass

    def homeContent(self, filter: bool) -> Dict:
        result = {
            'class': [
                {'type_id': '全部', 'type_name': '全部'},
                {'type_id': '日本AV', 'type_name': '日本AV'},
                {'type_id': '中文字幕', 'type_name': '中文字幕'},
                {'type_id': '素人業餘', 'type_name': '素人業餘'},
                {'type_id': '高清無碼', 'type_name': '高清無碼'},
                {'type_id': 'AI解碼', 'type_name': 'AI解碼'},
                {'type_id': '國產AV', 'type_name': '國產AV'},
                {'type_id': '國產素人', 'type_name': '國產素人'},
            ],
            'filters': {},
            'list': []
        }
        try:
            html = self._fetch_html(self.base_url)
            if html:
                result['list'] = self._extract_videos(html)[:20]
            return result
        except Exception as e:
            print(f"[ERROR] homeContent: {e}")
            return result

    def homeVideoContent(self) -> Dict:
        return self.homeContent(False)

    def categoryContent(self, tid: str, pg: str, filter: bool, extend: Dict) -> Dict:
        result = {'list': [], 'page': int(pg) if pg else 1, 'pagecount': 1, 'limit': 20, 'total': 0, 'code': 0, 'msg': ''}
        try:
            page = int(pg) if pg else 1
            url = self._get_category_url(tid, page)

            html = self._fetch_html(url)
            if html:
                result['list'] = self._extract_videos(html)

                page_nums = re.findall(r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>', html)
                if page_nums:
                    try:
                        result['pagecount'] = max([int(n) for n in page_nums])
                    except:
                        pass

            return result
        except Exception as e:
            print(f"[ERROR] categoryContent: {e}")
            result['code'] = -1
            result['msg'] = str(e)
            return result

    def detailContent(self, ids: List[str]) -> Dict:
        result = {'list': [], 'code': 0, 'msg': ''}
        try:
            if not ids:
                return result
            vid = ids[0]
            url = f"{self.base_url}/watch?v={vid}"
            html = self._fetch_html(url)
            if not html:
                return result

            title_match = re.search(r'<h3[^>]*class="video-details-wrapper"[^>]*>([^<]+)</h3>', html)
            title = title_match.group(1).strip() if title_match else ""

            poster_match = re.search(r'<video[^>]*poster="([^"]+)"', html)
            poster = poster_match.group(1) if poster_match else ""

            play_url = ""
            preload_match = re.search(r'<link[^>]*rel="preload"[^>]*as="video"[^>]*href="([^"]+)"', html)
            if preload_match:
                play_url = preload_match.group(1)
            else:
                js_match = re.search(r"const\s+source\s*=\s*'([^']+)'", html)
                if js_match:
                    play_url = js_match.group(1)

            vod = {
                'vod_id': vid,
                'vod_name': title,
                'vod_pic': poster,
                'vod_content': title,
                'vod_play_from': 'Javchu',
                'vod_play_url': f'播放$' + play_url if play_url else ''
            }

            result['list'] = [vod]
            return result
        except Exception as e:
            print(f"[ERROR] detailContent: {e}")
            result['code'] = -1
            result['msg'] = str(e)
            return result

    def searchContent(self, key: str, quick: bool, pg: Optional[str] = None) -> Dict:
        result = {'list': [], 'page': int(pg) if pg else 1, 'pagecount': 1, 'limit': 20, 'total': 0, 'code': 0, 'msg': ''}
        try:
            page = int(pg) if pg else 1
            url = f"{self.base_url}/search?query={urllib.parse.quote(key)}"
            if page > 1:
                url += f"&page={page}"

            html = self._fetch_html(url)
            if html:
                result['list'] = self._extract_videos(html)

                page_nums = re.findall(r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>', html)
                if page_nums:
                    try:
                        result['pagecount'] = max([int(n) for n in page_nums])
                    except:
                        pass

            return result
        except Exception as e:
            print(f"[ERROR] searchContent: {e}")
            result['code'] = -1
            result['msg'] = str(e)
            return result

    def playerContent(self, flag: str, id: str, vipFlags: Optional[Dict] = None) -> Dict:
        result = {'parse': 0, 'playUrl': '', 'url': id, 'header': json.dumps(self.headers)}
        try:
            if id.startswith('http'):
                result['url'] = id
                return result

            url = f"{self.base_url}/watch?v={id}"
            html = self._fetch_html(url)
            if html:
                preload_match = re.search(r'<link[^>]*rel="preload"[^>]*as="video"[^>]*href="([^"]+)"', html)
                if preload_match:
                    result['url'] = preload_match.group(1)
                    return result
                js_match = re.search(r"const\s+source\s*=\s*'([^']+)'", html)
                if js_match:
                    result['url'] = js_match.group(1)
                    return result
            result['url'] = id
            return result
        except Exception as e:
            print(f"[ERROR] playerContent: {e}")
            return result

    def localProxy(self, param: Optional[Dict]) -> Optional[List]:
        return None

    def isVideoFormat(self, url: str) -> bool:
        if not url:
            return False
        return any(url.lower().endswith(ext) for ext in ['.m3u8', '.mp4', '.ts']) or 'm3u8' in url.lower()

    def manualVideoCheck(self) -> bool:
        return False

    def destroy(self) -> None:
        pass