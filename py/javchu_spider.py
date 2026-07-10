# coding=utf-8
"""
Javchu.com 爬虫源
网站: https://javchu.com/
类型: 影视/成人
版本: 1.3 - 修复视频提取
"""
import re
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional


class Spider:
    """Javchu 爬虫主类"""

    def __init__(self):
        self.extend = ""
        self.base_url = "https://javchu.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Referer': 'https://javchu.com/'
        }
        self.timeout = 15

    def getDependence(self):
        return []

    def _fetch_html(self, url: str) -> str:
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"[ERROR] 获取页面失败: {url}, {e}")
            return ""

    def _extract_videos(self, html: str) -> List[Dict]:
        """从HTML中提取视频列表 - 使用更健壮的方式"""
        videos = []
        if not html:
            return videos

        # 方法1: 直接匹配每个 video-item-container 块
        # 使用更精确的匹配，不依赖 .*? 跨行匹配
        blocks = re.findall(
            r'<div[^>]*class="video-item-container"[^>]*>.*?</div>\s*</div>\s*</div>',
            html,
            re.DOTALL
        )

        for block in blocks:
            try:
                # 提取标题（从 title 属性）
                title_match = re.search(r'title="([^"]*)"', block)
                title = title_match.group(1) if title_match else ""

                # 提取链接
                href_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*class="video-link"', block)
                if not href_match:
                    href_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>', block)
                href = href_match.group(1) if href_match else ""

                # 提取视频ID
                vid_match = re.search(r'v=(\d+)', href) if href else None

                # 提取图片
                img_match = re.search(r'<img[^>]*class="main-thumb"[^>]*src="([^"]+)"', block)
                pic = img_match.group(1) if img_match else ""

                # 提取时长
                dur_match = re.search(r'<div[^>]*class="duration"[^>]*>([^<]*)</div>', block)
                duration = dur_match.group(1).strip() if dur_match else ""

                # 提取标题（从 title div）
                if not title:
                    title_div = re.search(r'<div[^>]*class="title"[^>]*>([^<]*)</div>', block)
                    title = title_div.group(1).strip() if title_div else ""

                if vid_match and title:
                    videos.append({
                        'vod_id': vid_match.group(1),
                        'vod_name': title.strip(),
                        'vod_pic': pic,
                        'vod_remarks': duration
                    })
            except Exception as e:
                print(f"[DEBUG] 解析视频块失败: {e}")
                continue

        # 方法2: 如果方法1没找到，尝试用更宽松的正则
        if not videos:
            pattern = r'<div[^>]*class="video-item-container"[^>]*title="([^"]*)"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*class="main-thumb"[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="duration"[^>]*>([^<]*)</div>.*?<div[^>]*class="title"[^>]*>([^<]*)</div>'
            matches = re.findall(pattern, html, re.DOTALL)
            for title_attr, href, pic, duration, title_text in matches:
                vid_match = re.search(r'v=(\d+)', href)
                if vid_match:
                    name = title_attr.strip() or title_text.strip()
                    videos.append({
                        'vod_id': vid_match.group(1),
                        'vod_name': name,
                        'vod_pic': pic,
                        'vod_remarks': duration.strip()
                    })

        # 方法3: 最简单的方式 - 逐个查找
        if not videos:
            # 找所有 video-item-container
            raw_blocks = re.findall(r'<div[^>]*class="video-item-container"[^>]*>', html)
            for raw in raw_blocks:
                # 找对应的闭合
                start_idx = html.find(raw)
                if start_idx == -1:
                    continue
                # 找到3个闭合的 </div>
                end_idx = start_idx
                div_count = 0
                for i in range(start_idx, len(html)):
                    if html[i:i+6] == '</div>':
                        div_count += 1
                        if div_count >= 3:
                            end_idx = i + 6
                            break
                if end_idx > start_idx:
                    block = html[start_idx:end_idx]
                    title_match = re.search(r'title="([^"]*)"', block)
                    title = title_match.group(1) if title_match else ""
                    href_match = re.search(r'href="([^"]+)"', block)
                    href = href_match.group(1) if href_match else ""
                    vid_match = re.search(r'v=(\d+)', href) if href else None
                    img_match = re.search(r'src="([^"]+)"', block)
                    pic = img_match.group(1) if img_match else ""
                    dur_match = re.search(r'<div[^>]*class="duration"[^>]*>([^<]*)</div>', block)
                    duration = dur_match.group(1).strip() if dur_match else ""
                    if vid_match and title:
                        videos.append({
                            'vod_id': vid_match.group(1),
                            'vod_name': title.strip(),
                            'vod_pic': pic,
                            'vod_remarks': duration
                        })

        return videos

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
                if config.get('headers'):
                    self.headers.update(config['headers'])
            elif self.extend.startswith('http'):
                self.base_url = self.extend
        except Exception as e:
            print(f"[ERROR] 初始化失败: {e}")

    def homeContent(self, filter: bool) -> Dict:
        result = {'class': [], 'filters': {}, 'list': []}
        try:
            html = self._fetch_html(self.base_url)
            if not html:
                return result

            # 提取分类
            nav_pattern = r'<a[^>]*class="nav-item[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            for match in re.finditer(nav_pattern, html):
                href = match.group(1)
                name = match.group(2).strip()
                if name and 'search' in href:
                    tid = None
                    if 'genre=' in href:
                        tid = re.search(r'genre=([^&]+)', href)
                    elif 'tags[]=' in href:
                        tid = re.search(r'tags\[\]=([^&]+)', href)
                    if tid and name not in ['全部类型', '标签', '排序方式', '发布日期', '時長']:
                        result['class'].append({'type_id': tid.group(1), 'type_name': name})

            if not result['class']:
                result['class'] = [
                    {'type_id': '全部', 'type_name': '全部'},
                    {'type_id': '日本AV', 'type_name': '日本AV'},
                    {'type_id': '中文字幕', 'type_name': '中文字幕'},
                    {'type_id': '素人業餘', 'type_name': '素人業餘'},
                    {'type_id': '高清無碼', 'type_name': '高清無碼'},
                    {'type_id': 'AI解碼', 'type_name': 'AI解碼'},
                    {'type_id': '國產AV', 'type_name': '國產AV'},
                    {'type_id': '國產素人', 'type_name': '國產素人'},
                    {'type_id': 'H動漫', 'type_name': 'H動漫'}
                ]

            result['list'] = self._extract_videos(html)[:20]
            return result
        except Exception as e:
            print(f"[ERROR] homeContent失败: {e}")
            return result

    def homeVideoContent(self) -> Dict:
        return self.homeContent(False)

    def categoryContent(self, tid: str, pg: str, filter: bool, extend: Dict) -> Dict:
        result = {'list': [], 'page': int(pg) if pg else 1, 'pagecount': 1, 'limit': 20, 'total': 0, 'code': 0, 'msg': ''}
        try:
            page = int(pg) if pg else 1
            url = f"{self.base_url}/search?genre={urllib.parse.quote(tid)}"
            if page > 1:
                url += f"&page={page}"

            html = self._fetch_html(url)
            if not html:
                return result

            result['list'] = self._extract_videos(html)

            page_nums = re.findall(r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>', html)
            if page_nums:
                try:
                    result['pagecount'] = max([int(n) for n in page_nums])
                except:
                    pass

            return result
        except Exception as e:
            print(f"[ERROR] categoryContent失败: {e}")
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

            desc_match = re.search(r'<div[^>]*class="video-caption-text"[^>]*>([^<]*)</div>', html)
            description = desc_match.group(1).strip() if desc_match else ""

            views_match = re.search(r'觀看次數[：:]\s*([^<&]+)', html)
            views = views_match.group(1).strip() if views_match else ""

            vod = {
                'vod_id': vid,
                'vod_name': title,
                'vod_pic': poster,
                'vod_content': description or title,
                'vod_play_from': 'Javchu',
                'vod_play_url': f'播放$' + play_url if play_url else ''
            }
            if views:
                vod['vod_remarks'] = views

            result['list'] = [vod]
            return result
        except Exception as e:
            print(f"[ERROR] detailContent失败: {e}")
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
            if not html:
                return result

            result['list'] = self._extract_videos(html)

            page_nums = re.findall(r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>', html)
            if page_nums:
                try:
                    result['pagecount'] = max([int(n) for n in page_nums])
                except:
                    pass

            return result
        except Exception as e:
            print(f"[ERROR] searchContent失败: {e}")
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
            print(f"[ERROR] playerContent失败: {e}")
            return result

    def localProxy(self, param: Optional[Dict]) -> Optional[List]:
        return None

    def isVideoFormat(self, url: str) -> bool:
        if not url:
            return False
        video_extensions = ['.m3u8', '.mp4', '.ts', '.mkv', '.webm']
        return any(url.lower().endswith(ext) for ext in video_extensions) or 'm3u8' in url.lower()

    def manualVideoCheck(self) -> bool:
        return False

    def destroy(self) -> None:
        pass