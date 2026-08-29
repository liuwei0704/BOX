# coding: utf-8
# 站点: 记得我视频
# 域名: https://pym.jdwsp2.pics/jdwsp/
# 类型: MacCMS 成人影视站
# 最后验证: 2026-08-29

import re
import json
import base64
import urllib.parse
from bs4 import BeautifulSoup
import requests


class Spider:
    def __init__(self):
        self.host = "https://pym.jdwsp2.pics"
        self.base_path = "/cn/home/web"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.host + '/',
        }
        self.classes = [
            {"type_id": "1", "type_name": "乱伦"},
            {"type_id": "2", "type_name": "出轨"},
            {"type_id": "3", "type_name": "制服"},
            {"type_id": "4", "type_name": "自慰"},
            {"type_id": "5", "type_name": "偷拍"},
            {"type_id": "20", "type_name": "自拍"},
            {"type_id": "21", "type_name": "国产"},
            {"type_id": "22", "type_name": "同性"},
            {"type_id": "23", "type_name": "日韩"},
            {"type_id": "24", "type_name": "欧美"},
            {"type_id": "25", "type_name": "三级"},
            {"type_id": "26", "type_name": "动漫"},
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
            return self.host + url
        return self.host + '/' + url.lstrip('/')

    def _make_proxy_url(self, pic_url):
        if not pic_url:
            return ''
        encoded = base64.b64encode(pic_url.encode()).decode()
        return f'proxy://do=py&site=记得我视频&type=img&url={encoded}'

    def _parse_list_items(self, html, limit=999):
        doc = BeautifulSoup(html, 'html.parser')
        videos = []
        for li in doc.select('ul.img-list li'):
            a = li.find('a', href=True)
            if not a:
                continue
            href = a.get('href', '')
            if '/vod/play/id/' not in href:
                continue
            vid = self._extract_vod_id(href)
            if not vid:
                continue
            title = ''
            h2 = a.find('h2')
            if h2:
                title = h2.text.strip()
            if not title:
                title = a.get('title', '') or a.text.strip()
            # 尝试多种方式获取图片
            img = li.find('img')
            pic = ''
            if img:
                pic = img.get('src') or img.get('data-src') or img.get('data-original', '')
            # 如果 li 中没有 img，尝试从 a 中找
            if not pic:
                img = a.find('img')
                if img:
                    pic = img.get('src') or img.get('data-src') or img.get('data-original', '')
            pic = self.fix_url(pic)
            if pic:
                pic = self._make_proxy_url(pic)
            remark = ''
            i_tag = li.find('i')
            if i_tag:
                remark = i_tag.text.strip()
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
    def _extract_vod_id(self, url):
        if not url:
            return ''
        m = re.search(r'/vod/play/id/(\d+)', url)
        if m:
            return m.group(1)
        return ''

    def _parse_play_url(self, html):
        """从详情页HTML中提取播放地址"""
        # 尝试从 player_data 变量提取
        m = re.search(r'var\s+player_data\s*=\s*({[^}]+})', html)
        if m:
            try:
                data = json.loads(m.group(1))
                if data.get('url'):
                    return data['url']
            except:
                pass
        # 备用：直接搜索 m3u8 链接
        m = re.search(r'["\'](https?://[^"\']+\.m3u8)["\']', html)
        if m:
            return m.group(1)
        return ''

    def homeContent(self, filter=False):
        return {'class': self.classes, 'filters': self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐 - 从首页提取最近热播"""
        url = self.host + self.base_path + '/'
        html = self.get_html(url)
        if not html:
            return {'list': []}
        videos = self._parse_list_items(html, 20)
        return {'list': videos}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        pg = int(pg) if pg else 1
        url = f"{self.host}{self.base_path}/index.php/vod/type/id/{tid}.html"
        if pg > 1:
            url = f"{self.host}{self.base_path}/index.php/vod/type/id/{tid}/page/{pg}.html"
        html = self.get_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}
        videos = self._parse_list_items(html)
        # 提取总页数
        pagecount = 1
        total = 0
        page_info = re.search(r'共(\d+)条数据,当前(\d+)/(\d+)页', html)
        if page_info:
            total = int(page_info.group(1))
            pagecount = int(page_info.group(3))
        return {
            'list': videos,
            'page': pg,
            'pagecount': pagecount,
            'limit': 20,
            'total': total
        }

    def detailContent(self, ids):
        if not ids:
            return {'list': []}
        vid = ids[0]
        url = f"{self.host}{self.base_path}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        html = self.get_html(url)
        if not html:
            return {'list': []}

        doc = BeautifulSoup(html, 'html.parser')

        # 提取标题
        title = ''
        t = doc.find('h1')
        if t:
            title = t.text.strip()
        if not title:
            title_match = re.search(r'<title>(.+?)</title>', html)
            if title_match:
                title = title_match.group(1).replace(' - 记得我视频', '').replace('在线播放', '').strip()

        # 提取封面 - 多种方式尝试
        pic = ''
        # 方式1: 从播放器区域找封面
        for img in doc.select('#detail-box img, .ui-box img, .video-box img'):
            pic = img.get('src') or img.get('data-src', '')
            if pic and 'placeholder' not in pic and 'loading' not in pic:
                break
        # 方式2: 从 player_data 中找封面
        if not pic:
            m = re.search(r'var\s+player_data\s*=\s*({[^}]+})', html)
            if m:
                try:
                    data = json.loads(m.group(1))
                    if data.get('pic'):
                        pic = data['pic']
                except:
                    pass
        # 方式3: 从页面任意 img 中找
        if not pic:
            for img in doc.find_all('img'):
                src = img.get('src') or img.get('data-src', '')
                if src and 'placeholder' not in src and 'loading' not in src and 'logo' not in src:
                    pic = src
                    break
        pic = self.fix_url(pic)
        if pic:
            pic = self._make_proxy_url(pic)

        # 提取播放地址
        play_url = self._parse_play_url(html)

        # 提取集数列表
        episodes = []
        for a in doc.select('.video_list a'):
            href = a.get('href', '')
            ep_title = a.text.strip()
            if href and '/vod/play/id/' in href:
                m = re.search(r'/vod/play/id/(\d+)/sid/\d+/nid/(\d+)\.html', href)
                if m:
                    ep_id = m.group(2)
                    episodes.append(f"{ep_title}${vid}|{ep_id}")

        if episodes:
            play_from = '播放线路'
            play_url_str = '#'.join(episodes)
        elif play_url:
            play_from = '播放线路'
            play_url_str = f'播放${play_url}'
        else:
            play_from = ''
            play_url_str = ''

        data = {
            'vod_id': vid,
            'vod_name': title or '未知标题',
            'vod_pic': pic,
            'vod_content': '',
            'vod_play_from': play_from,
            'vod_play_url': play_url_str,
        }
        return {'list': [data]}
    def searchContent(self, key, quick=False, pg='1'):
        if not key:
            return {'list': [], 'page': 1, 'pagecount': 1, 'total': 0}
        pg = int(pg) if pg else 1
        encoded_key = urllib.parse.quote(key)
        url = f"{self.host}{self.base_path}/index.php/vod/search/wd/{encoded_key}.html"
        if pg > 1:
            url = f"{self.host}{self.base_path}/index.php/vod/search/page/{pg}/wd/{encoded_key}.html"
        html = self.get_html(url)
        if not html:
            return {'list': [], 'page': pg, 'pagecount': 1, 'total': 0}
        videos = self._parse_list_items(html)
        total = 0
        total_match = re.search(r'共(\d+)条数据', html)
        if total_match:
            total = int(total_match.group(1))
        return {'list': videos, 'page': pg, 'pagecount': 999, 'total': total}

    def playerContent(self, flag, id, vipFlags=None):
        if not id:
            return {'parse': 1, 'url': ''}

        # 处理 pics:// 协议
        if id.startswith('pics://'):
            return {'parse': 1, 'url': id}

        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': self.host + '/',
        }

        # 处理格式: vid|epid
        if '|' in id:
            parts = id.split('|')
            if len(parts) == 2:
                vid, epid = parts
                url = f"{self.host}{self.base_path}/index.php/vod/play/id/{vid}/sid/1/nid/{epid}.html"
                html = self.get_html(url)
                if html:
                    play_url = self._parse_play_url(html)
                    if play_url:
                        if play_url.endswith('.m3u8') or '.m3u8?' in play_url:
                            return {'parse': 0, 'url': self._m3u8_proxy_url(play_url), 'header': headers}
                        if play_url.endswith('.mp4'):
                            return {'parse': 0, 'url': play_url, 'header': headers}
                        if play_url.startswith('/'):
                            play_url = self.host + play_url
                            if play_url.endswith('.m3u8') or '.m3u8?' in play_url:
                                return {'parse': 0, 'url': self._m3u8_proxy_url(play_url), 'header': headers}
                            return {'parse': 0, 'url': play_url, 'header': headers}

        # 直接处理播放链接
        if id.startswith('http'):
            if id.endswith('.m3u8') or '.m3u8?' in id:
                return {'parse': 0, 'url': self._m3u8_proxy_url(id), 'header': headers}
            if id.endswith('.mp4'):
                return {'parse': 0, 'url': id, 'header': headers}
            html = self.get_html(id)
            if html:
                play_url = self._parse_play_url(html)
                if play_url:
                    if play_url.endswith('.m3u8') or '.m3u8?' in play_url:
                        return {'parse': 0, 'url': self._m3u8_proxy_url(play_url), 'header': headers}
                    if play_url.endswith('.mp4'):
                        return {'parse': 0, 'url': play_url, 'header': headers}

        # 降级嗅探
        return {'parse': 1, 'url': id, 'header': headers}
    def _m3u8_proxy_url(self, url):
        """生成 m3u8 代理地址"""
        if not url:
            return ''
        # 使用 proxy:// 协议，让壳端调用 localProxy
        return f"proxy://do=py&site=记得我视频&type=m3u8&url={urllib.parse.quote(str(url), safe='')}"
    def localProxy(self, param):
        """localProxy - 支持图片代理和 m3u8 代理"""
        print(f"localProxy 收到参数: {param}")
        print(f"参数类型: {type(param)}")
        
        target = ""
        if isinstance(param, dict):
            print(f"参数字典内容: {param}")
            target = param.get("url", "") or param.get("source", "")
            # 图片代理
            if param.get('type') == 'img':
                try:
                    encoded_url = param.get('url', '')
                    if encoded_url:
                        pic_url = base64.b64decode(encoded_url).decode()
                        print("图片代理解码:", pic_url)
                        resp = requests.get(pic_url, headers=self.headers, timeout=30, verify=False)
                        if resp.status_code == 200:
                            content = resp.content
                            content_type = resp.headers.get('Content-Type', 'image/jpeg')
                            if content.startswith(b'\xff\xd8\xff'):
                                content_type = 'image/jpeg'
                            elif content.startswith(b'\x89PNG'):
                                content_type = 'image/png'
                            return [200, content_type, content]
                        print(f"图片获取失败: {resp.status_code}")
                        return [resp.status_code, 'text/plain', b'Image fetch failed']
                except Exception as e:
                    print('localProxy img error:', e)
                    return [500, 'text/plain', b'Image proxy error']
        elif isinstance(param, str):
            print(f"参数字符串: {param}")
            target = param
        else:
            print(f"未知参数类型: {type(param)}")
            return [400, "text/plain", b"invalid param type"]

        # 剥离前缀 url= 并解码
        if target and target.startswith("url="):
            target = target[4:]
        if target and "url=" in target:
            parsed = urllib.parse.urlparse(target)
            qs = urllib.parse.parse_qs(parsed.query)
            print(f"解析 query string: {qs}")
            if "url" in qs:
                target = qs["url"][0]
        target = urllib.parse.unquote(str(target or ""))

        if not target or not re.match(r"^https?://", target, re.I):
            print(f"无效目标 URL: {target}")
            return [400, "text/plain", b"invalid url"]

        try:
            print(f"localProxy 请求 m3u8: {target}")
            resp = requests.get(target, headers=self.headers, timeout=20, verify=False)
            if resp is None:
                return [502, "text/plain", b"fetch failed"]
            if resp.status_code != 200:
                print(f"m3u8 请求失败: {resp.status_code}")
                return [resp.status_code, "text/plain", f"fetch failed: {resp.status_code}".encode()]
            content = resp.content or b""
            if not content:
                return [502, "text/plain", b"empty content"]

            if b"#EXTM3U" in content[:256]:
                print("检测到 m3u8，开始过滤")
                text = content.decode("utf-8", errors="ignore")
                cleaned = self._clean_m3u8(text, target)
                print(f"过滤完成，长度: {len(cleaned)}")
                return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

            print("非 m3u8 内容，直接返回")
            content_type = "application/octet-stream"
            if target.endswith(".ts"):
                content_type = "video/mp2t"
            elif target.endswith(".m3u8"):
                content_type = "application/vnd.apple.mpegurl"
            elif target.endswith(".jpg") or target.endswith(".png"):
                content_type = "image/jpeg"
            elif target.endswith(".mp4"):
                content_type = "video/mp4"
            return [200, content_type, content]
        except Exception as e:
            print(f'localProxy error: {e}')
            import traceback
            traceback.print_exc()
            return [500, "text/plain", str(e).encode("utf-8", errors="ignore")]
    def _clean_m3u8(self, text, source_url):
        """清洗 m3u8：过滤广告分片（基于目录前缀匹配）"""
        import posixpath

        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 多码率处理 - 将子流 URL 转为完整 URL
        # 多码率处理 - 将子流 URL 转为 proxy:// 格式，让子流也走代理
        # 多码率处理 - 直接透传，不进行代理转换
        # 多码率 m3u8 的广告过滤较复杂，透传后由壳端原生播放器处理
        # 多码率处理 - 直接获取子流内容并过滤
        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            # 找到第一个子流 URL
            child_url = None
            for line in lines:
                if not line.startswith("#") and '.m3u8' in line:
                    child_url = urllib.parse.urljoin(source_url, line)
                    break
            
            if child_url:
                try:
                    # 获取子流内容
                    resp = requests.get(child_url, headers=self.headers, timeout=20)
                    if resp and resp.status_code == 200:
                        child_content = resp.content or b""
                        if child_content and b"#EXTM3U" in child_content[:256]:
                            child_text = child_content.decode("utf-8", errors="ignore")
                            # 递归调用过滤子流
                            filtered_child = self._clean_m3u8(child_text, child_url)
                            # 返回过滤后的子流内容（直接返回，不再返回主 m3u8）
                            return filtered_child
                except Exception as e:
                    print(f"多码率子流获取失败: {e}")
            
            # 如果获取失败，直接透传主 m3u8
            return "\n".join(lines) + "\n"

        # 单码率处理 - 目录前缀匹配法
        parsed = urllib.parse.urlparse(source_url)
        dir_path = posixpath.dirname(parsed.path)
        if not dir_path.endswith('/'):
            dir_path += '/'

        def is_valid_segment(url):
            parsed_url = urllib.parse.urlparse(url)
            return parsed_url.path.startswith(dir_path)

        result = []
        pending_extinf = []
        removed = 0
        kept = 0
        i = 0

        while i < len(lines):
            line = lines[i]

            # 处理 KEY 标签 - 补全 URI
            if line.startswith("#EXT-X-KEY") and "URI=" in line:
                line = self._rewrite_m3u8_tag(line, source_url)
                result.append(line)
                i += 1
                continue

            if line.startswith("#EXTINF"):
                pending_extinf = [line]
                i += 1
                # 收集后续的注释行
                while i < len(lines) and lines[i].startswith("#"):
                    pending_extinf.append(lines[i])
                    i += 1
                # 处理分片 URL
                if i < len(lines):
                    next_line = lines[i]
                    media_url = urllib.parse.urljoin(source_url, next_line)
                    if is_valid_segment(media_url):
                        result.extend(pending_extinf)
                        result.append(media_url)
                        kept += 1
                    else:
                        removed += 1
                    i += 1
                continue

            # 跳过 DISCONTINUITY（广告分割标记）
            if line == "#EXT-X-DISCONTINUITY":
                i += 1
                continue

            # 跳过广告 KEY:NONE
            if line == "#EXT-X-KEY:METHOD=NONE":
                i += 1
                continue

            # 非 EXTINF 的标签直接保留
            result.append(line)
            i += 1

        if removed:
            print(f"m3u8已过滤广告分片: {removed}个，保留正片: {kept}个")
        return "\n".join(result) + "\n"
    def _rewrite_m3u8_tag(self, line, source_url):
        """重写 m3u8 标签中的 URI（补全绝对地址）"""
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

    def recommendContent(self, ids, pg):
        """推荐接口"""
        return {"list": []}

    def init(self, extend=''):
        pass

    def destroy(self):
        pass

    def getDependence(self):
        return ['requests', 'bs4']

    def getName(self):
        return '记得我视频'

    def getProxyUrl(self):
        """获取本地代理地址"""
        return "http://127.0.0.1:9978/proxy"
