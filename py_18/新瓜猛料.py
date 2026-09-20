# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import re
import json
import base64
import urllib.parse
import posixpath
from bs4 import BeautifulSoup
import requests
import json
import base64
import urllib.parse
from bs4 import BeautifulSoup
import requests

class Spider:
    def __init__(self):
        self.host = "https://www.gouhunba.shop"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.host + '/'
        }
        self.classes = [
            {"type_id": "1", "type_name": "明星脸蛋"},
            {"type_id": "2", "type_name": "国产精品"},
            {"type_id": "3", "type_name": "传媒合集"},
            {"type_id": "4", "type_name": "欧美专区"},
            {"type_id": "6", "type_name": "制服诱惑"},
            {"type_id": "7", "type_name": "萝莉少女"},
            {"type_id": "8", "type_name": "乱伦视频"},
            {"type_id": "9", "type_name": "在线主播"},
            {"type_id": "10", "type_name": "三级电影"},
            {"type_id": "11", "type_name": "女同性恋"},
            {"type_id": "12", "type_name": "中文字幕"},
            {"type_id": "13", "type_name": "日本有码"},
            {"type_id": "14", "type_name": "高清无码"},
            {"type_id": "15", "type_name": "韩国主播"},
            {"type_id": "16", "type_name": "网红性事"},
        ]
        self.filters = {}

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
        m = re.search(r'/voddetail/(\d+)\.html', url)
        if m:
            return m.group(1)
        return ''

    def _parse_videos(self, html, limit=20):
        doc = BeautifulSoup(html, 'html.parser')
        videos = []
        # 查找所有视频卡片
        cards = doc.find_all('div', class_=re.compile(r'card-compact'))
        for card in cards:
            a = card.find('a', href=True)
            if not a:
                continue
            href = a.get('href', '')
            if '/voddetail/' not in href:
                continue
            vid = self._extract_vod_id(href)
            if not vid:
                continue
            # 提取标题
            title = ''
            title_tag = card.find('h2', class_=re.compile(r'card-title'))
            if title_tag:
                title = title_tag.text.strip()
            if not title:
                title = a.get('title', '') or a.text.strip()
            # 提取封面
            pic = ''
            img = card.find('img')
            if img:
                pic = img.get('data-src') or img.get('src', '')
                pic = self.fix_url(pic)
            # 提取角标
            remark = ''
            p_tag = card.find('p')
            if p_tag:
                remark = p_tag.text.strip()
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

    def _parse_page_count(self, html):
        """提取总页数 - 从分页控件或提示文字中提取"""
        if not html:
            return 1
        max_page = 1
        
        # 方法1: 从"共X条数据,当前Y/Z页"中提取总页数
        pattern = r'共\d+条数据,当前\d+/(\d+)页'
        match = re.search(pattern, html)
        if match:
            return int(match.group(1))
        
        # 方法2: 从分页按钮中提取最大数字
        doc = BeautifulSoup(html, 'html.parser')
        for a in doc.find_all('a'):
            text = a.text.strip()
            if text.isdigit():
                num = int(text)
                if num > max_page:
                    max_page = num
        
        # 方法3: 如果有"下一页"链接，从href中提取页码
        for a in doc.find_all('a'):
            text = a.text.strip()
            if '下一页' in text:
                href = a.get('href', '')
                m = re.search(r'/(\d+)\.html', href)
                if m:
                    num = int(m.group(1))
                    if num > max_page:
                        max_page = num
                # 也可能是 page=数字 格式
                m = re.search(r'page[=\/](\d+)', href)
                if m:
                    num = int(m.group(1))
                    if num > max_page:
                        max_page = num
        
        return max_page

    def homeContent(self, filter=False):
        return {'class': self.classes, 'filters': self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐 - 返回传媒合集分类的内容"""
        try:
            result = self.categoryContent('3', 1, False, None)
            return {'list': result.get('list', [])[:16]}
        except Exception as e:
            print('homeVideoContent error:', e)
            return {'list': []}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        pg = int(pg) if pg else 1
        # 分页URL格式: /vodtype/{tid}-{page}.html
        if pg == 1:
            url = self.host + '/vodtype/' + str(tid) + '.html'
        else:
            url = self.host + '/vodtype/' + str(tid) + '-' + str(pg) + '.html'
        html = self.get_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}
        videos = self._parse_videos(html, 20)
        # 提取总页数 - 从"共X条数据,当前Y/Z页"或分页按钮中提取
        pagecount = self._parse_page_count(html)
        return {'list': videos, 'page': pg, 'pagecount': pagecount, 'limit': 20, 'total': pagecount * 20}

    def detailContent(self, ids):
        if not ids:
            return {'list': []}
        vid = str(ids[0])
        url = self.host + '/voddetail/' + vid + '.html'
        html = self.get_html(url)
        if not html:
            return {'list': []}
        doc = BeautifulSoup(html, 'html.parser')
        # 提取标题
        title = ''
        title_tag = doc.find('h2', class_=re.compile(r'card-title'))
        if title_tag:
            title = title_tag.text.strip()
        # 提取封面
        pic = ''
        img = doc.find('figure')
        if img:
            img_tag = img.find('img')
            if img_tag:
                pic = img_tag.get('src', '')
                pic = self.fix_url(pic)
        # 提取类型
        type_name = ''
        for p in doc.find_all('p'):
            if '类型：' in p.text or '类型:' in p.text:
                type_name = p.text.replace('类型：', '').replace('类型:', '').strip()
                break
        # 提取播放链接 - 从card-actions区域内的按钮中提取
        play_url = ''
        card_actions = doc.find('div', class_=re.compile(r'card-actions'))
        if card_actions:
            btn = card_actions.find('button', class_=re.compile(r'btn-primary'))
            if btn:
                onclick = btn.get('onclick', '')
                m = re.search(r"window\.location\.href='([^']+)'", onclick)
                if m:
                    play_url = self.host + m.group(1)
        # 如果没有card-actions，尝试直接查找按钮
        if not play_url:
            for btn in doc.find_all('button', class_=re.compile(r'btn-primary')):
                onclick = btn.get('onclick', '')
                if 'vodplay' in onclick:
                    m = re.search(r"window\.location\.href='([^']+)'", onclick)
                    if m:
                        play_url = self.host + m.group(1)
                        break
        # 如果没有按钮，尝试从页面中提取vodplay链接
        if not play_url:
            for a in doc.find_all('a', href=True):
                href = a.get('href', '')
                if '/vodplay/' in href:
                    play_url = self.host + href
                    break
        if play_url:
            play_from = '默认线路'
            play_url_str = '播放$' + play_url
        else:
            play_from = '默认线路'
            play_url_str = '播放$' + vid
        data = {
            'vod_id': vid,
            'vod_name': title or '未知标题',
            'vod_pic': pic,
            'vod_content': type_name,
            'vod_play_from': play_from,
            'vod_play_url': play_url_str,
        }
        return {'list': [data]}

    def searchContent(self, key, quick=False, pg='1'):
        if not key:
            return {'list': [], 'page': 1, 'pagecount': 1, 'total': 0}
        pg = int(pg) if pg else 1
        encoded_key = urllib.parse.quote(key)
        url = self.host + '/vodsearch/-------------.html?wd=' + encoded_key
        if pg > 1:
            url += '&pg=' + str(pg)
        html = self.get_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}
        videos = self._parse_videos(html, 20)
        return {'list': videos, 'page': pg, 'pagecount': 999, 'total': 9999}

    def playerContent(self, flag, id, vipFlags=None):
        if not id:
            return {'parse': 1, 'url': ''}
        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': self.host + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        # 如果id是播放页链接，去解析真实m3u8
        if id.startswith(self.host) and '/vodplay/' in id:
            html = self.get_html(id, headers)
            if html:
                # 方法1: 从 player_aaaa 对象中提取
                pattern = r'var\s+player_aaaa\s*=\s*(\{[^;]+\});'
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        real_url = data.get("url", "")
                        if real_url and real_url.startswith("http"):
                            real_url = real_url.replace('\\/', '/')
                            if '.m3u8' in real_url:
                                # 走代理过滤广告
                                return {'parse': 0, 'url': self._m3u8_proxy_url(real_url), 'header': headers}
                    except:
                        pass
                # 方法2: 直接提取url字段
                pattern2 = r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"'
                match2 = re.search(pattern2, html)
                if match2:
                    real_url = match2.group(1)
                    real_url = real_url.replace('\\/', '/')
                    if real_url.startswith('http'):
                        return {'parse': 0, 'url': self._m3u8_proxy_url(real_url), 'header': headers}
                # 方法3: 查找任何m3u8链接
                pattern3 = r'https?://[^"\']+\.m3u8[^"\']*'
                match3 = re.search(pattern3, html)
                if match3:
                    real_url = match3.group(0)
                    return {'parse': 0, 'url': self._m3u8_proxy_url(real_url), 'header': headers}
        # 如果id本身是m3u8直链，走代理
        if id.endswith('.m3u8') or '.m3u8' in id or id.endswith('.mp4'):
            return {'parse': 0, 'url': self._m3u8_proxy_url(id), 'header': headers}
        # 否则返回降级嗅探
        return {'parse': 1, 'url': id, 'header': headers}

    def recommendContent(self, ids, pg=1):
        """相关推荐"""
        if not ids:
            return {'list': []}
        vid = str(ids[0])
        url = self.host + '/voddetail/' + vid + '.html'
        html = self.get_html(url)
        if not html:
            return {'list': []}
        doc = BeautifulSoup(html, 'html.parser')
        videos = []
        # 查找相关推荐区域
        rec_div = doc.find('div', class_=re.compile(r'divider-neutral'))
        if rec_div:
            # 找到推荐卡片
            cards = rec_div.find_next_siblings()
            for sibling in cards:
                if 'grid' in sibling.get('class', []):
                    videos = self._parse_videos(str(sibling), 20)
                    break
        return {'list': videos}

    def init(self, extend=''):
        pass

    def destroy(self):
        pass
    def getProxyUrl(self):
        """获取本地代理地址"""
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        """生成m3u8代理地址 - 使用 ?do=py&url= 格式（与壳端标准一致）"""
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def localProxy(self, param):
        """
        m3u8本地代理 - 广告分片过滤
        参考wangshi_ribao.py的localProxy实现方式
        """
        try:
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")

            if target.startswith("url="):
                target = target[4:]
            target = urllib.parse.unquote(str(target or ""))

            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            resp = self.fetch(target, headers=self.headers, timeout=15)
            if not resp:
                return [502, "text/plain", b"fetch failed"]

            content = getattr(resp, "content", b"") or b""
            if not content and hasattr(resp, "text") and resp.text:
                content = resp.text.encode("utf-8", errors="ignore")

            if not content:
                return [502, "text/plain", b"empty content"]

            text = content.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]

            cleaned = self._clean_m3u8(text, target)
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

        except Exception as e:
            error_msg = f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")
            return [500, "text/plain", error_msg]

    def _clean_m3u8(self, text, source_url):
        """清洗m3u8 - 过滤广告分片 (参考wangshi_ribao.py)"""
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 处理多码率 Master Playlist
        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urllib.parse.urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"

        parsed = urllib.parse.urlparse(source_url)
        source_dir = posixpath.dirname(parsed.path)
        if not source_dir.endswith("/"):
            source_dir += "/"

        # 从 #EXT-X-KEY 提取正片目录
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
                media_url = urllib.parse.urljoin(source_url, line)
                media_parsed = urllib.parse.urlparse(media_url)

                is_ad = not media_parsed.path.startswith(main_dir)

                if not is_ad:
                    segments.extend(pending)
                    segments.append(media_url)
                pending = []
                continue

            if not line.startswith("#"):
                segments.append(urllib.parse.urljoin(source_url, line))
            else:
                segments.append(line)

        # 二次清洗
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
        """重写m3u8标签中的URI（补全绝对地址）"""
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(match):
                uri = match.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urllib.parse.urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)

        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urllib.parse.urljoin(source_url, line)

        return line

    def getDependence(self):
        return ['requests', 'bs4']

    def getName(self):
        return '新瓜猛料'