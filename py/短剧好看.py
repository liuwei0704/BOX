# coding=utf-8
import re
import sys
import json
import base64
import urllib.parse
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    def getName(self):
        return "短剧好看"

    def init(self, extend=""):
        self.host = "https://www.duanjuhk.com"
        self.ua = "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36"
        self.headers = {
            'User-Agent': self.ua,
            'Referer': self.host + '/'
        }

    def _fetch(self, url, headers=None):
        try:
            import requests
            # 先修复URL再请求
            fixed_url = self._fix_url(url)
            h = headers or self.headers
            r = requests.get(fixed_url, headers=h, timeout=10)
            return r.text
        except Exception as e:
            print(f"fetch error: {e}")
            return ""

    def _fix_url(self, url):
        """补全URL - 彻底修复拼接问题"""
        if not url:
            return ""
        
        # 先进行URL解码
        try:
            url = urllib.parse.unquote(url)
        except:
            pass
        
        url = url.strip()
        
        # 1. 如果是完整URL，直接返回
        if url.startswith("http://") or url.startswith("https://"):
            return url
        
        # 2. 处理反斜杠转义（如 https:\/\/ 格式）
        if url.startswith("https:\\/\\/") or url.startswith("http:\\/\\/"):
            url = url.replace("\\/", "/")
            return url
        
        # 3. 处理双斜杠开头的协议相对URL
        if url.startswith("//"):
            return "https:" + url
        
        # 4. 处理以域名开头的URL（无协议）
        domain_match = re.match(r'^([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,})(/|$)', url)
        if domain_match:
            return "https://" + url
        
        # 5. 处理绝对路径
        if url.startswith("/"):
            return self.host + url
        
        # 6. 处理相对路径
        return self.host + "/" + url

    def _extract_play_url(self, html):
        """从页面中提取播放直链"""
        # 方法1：player_aaaa JSON
        match = re.search(r'player_aaaa\s*=\s*(\{.*?\})', html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                url = data.get('url', '')
                if url:
                    # 处理反斜杠转义
                    url = url.replace('\\/', '/')
                    url = urllib.parse.unquote(url)
                    if url.startswith('../../'):
                        url = url.replace('../../', '/')
                    return self._fix_url(url)
            except:
                pass

        # 方法2：player_data JSON
        match = re.search(r'player_data\s*=\s*(\{.*?\})', html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                url = data.get('url', '')
                if url:
                    url = url.replace('\\/', '/')
                    url = urllib.parse.unquote(url)
                    return self._fix_url(url)
            except:
                pass

        # 方法3：iframe 中的 src
        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
        if iframe_match:
            iframe_url = self._fix_url(iframe_match.group(1))
            if iframe_url and 'player' in iframe_url:
                return iframe_url

        # 方法4：通用播放地址提取
        patterns = [
            r'<source[^>]+src=["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
            r'"url"\s*:\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
            r'"src"\s*:\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
            r'videoUrl\s*=\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
            r'(https?://[^\s"\']+\.(?:m3u8|mp4)[^\s"\']*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                url = match.group(1)
                if url and not url.startswith('data:'):
                    return self._fix_url(url)

        return None

    def _parse_video_list(self, html):
        videos = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select('.hl-list-item')
            for item in items:
                a = item.select_one('a.hl-item-thumb')
                if not a:
                    continue
                href = a.get('href', '')
                title = a.get('title', '')
                if not title:
                    title_el = item.select_one('.hl-item-title')
                    if title_el:
                        title = title_el.text.strip()
                pic = a.get('data-original', '')
                if not pic:
                    img = a.select_one('img')
                    if img:
                        pic = img.get('src', '')
                remark_el = item.select_one('.hl-lc-1')
                remark = remark_el.text.strip() if remark_el else ""
                if href:
                    videos.append({
                        "vod_id": href,
                        "vod_name": title or "未知",
                        "vod_pic": self._fix_url(pic),
                        "vod_remarks": remark
                    })
        except Exception as e:
            print(f"parse list error: {e}")
        return videos

    def homeContent(self, filter=False):
        result = {
            'class': [
                {"type_name": "精選", "type_id": "jingxuanduanju"},
                {"type_name": "都市", "type_id": "dushi"},
                {"type_name": "穿越", "type_id": "chuanyue"},
                {"type_name": "古代", "type_id": "gudai"},
                {"type_name": "福利", "type_id": "fuliduanju"}
            ],
            'list': []
        }
        try:
            html = self._fetch(self.host)
            result['list'] = self._parse_video_list(html)[:40]
        except Exception as e:
            print(f"homeContent error: {e}")
        return result

    def homeVideoContent(self):
        try:
            html = self._fetch(self.host)
            videos = self._parse_video_list(html)[:40]
            return {"list": videos}
        except:
            return {"list": []}

    def categoryContent(self, tid, pg=1, filter=False, extend=None):
        pg = int(pg) if str(pg).isdigit() else 1
        url = f"{self.host}/vodtype/{tid}.html"
        if pg > 1:
            url = f"{self.host}/vodtype/{tid}-{pg}.html"
        try:
            html = self._fetch(url)
            videos = self._parse_video_list(html)
            return {
                "list": videos,
                "page": pg,
                "pagecount": 50,
                "limit": 20,
                "total": len(videos)
            }
        except:
            return {"list": [], "page": pg, "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        if isinstance(ids, str):
            ids = [ids]
        result = []
        for vid in ids:
            if not vid.startswith('/'):
                vid = '/' + vid
            url = self._fix_url(vid)
            try:
                html = self._fetch(url)
                soup = BeautifulSoup(html, 'html.parser')
                
                name = ""
                name_el = soup.select_one('.hl-dc-title')
                if name_el:
                    name = name_el.text.strip()
                if not name:
                    title_tag = soup.find('title')
                    if title_tag:
                        title_text = title_tag.text.strip()
                        match = re.search(r'《([^》]+)》', title_text)
                        if match:
                            name = match.group(1)
                        else:
                            name = title_text.split('-')[0].strip()
                if not name:
                    h1 = soup.find('h1')
                    if h1:
                        name = h1.text.strip()
                if not name:
                    og_title = soup.find('meta', property='og:title')
                    if og_title and og_title.get('content'):
                        name = og_title.get('content').strip()

                pic = ""
                thumb_el = soup.select_one('.hl-item-thumb')
                if thumb_el:
                    pic = thumb_el.get('data-original', '')
                    if not pic:
                        pic = thumb_el.get('src', '')

                play_lists = soup.select('.hl-plays-list')
                tabs = soup.select('.hl-tabs-btn')
                play_from = []
                play_url = []

                for i, pl in enumerate(play_lists):
                    source_name = tabs[i].text.strip() if i < len(tabs) else f"线路{i+1}"
                    play_from.append(source_name)
                    links = []
                    for a in pl.find_all('a'):
                        ep_name = a.text.strip()
                        ep_url = a.get('href', '')
                        if ep_url:
                            links.append(f"{ep_name}${ep_url}")
                    play_url.append('#'.join(links))

                if not play_from:
                    play_url_raw = self._extract_play_url(html)
                    if play_url_raw:
                        play_from = ['直链']
                        play_url = [f"播放${play_url_raw}"]
                    else:
                        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
                        if iframe_match:
                            iframe_url = self._fix_url(iframe_match.group(1))
                            play_from = ['iframe']
                            play_url = [f"播放${iframe_url}"]
                        else:
                            play_from = ['默认线路']
                            play_url = [f"播放${vid}"]

                result.append({
                    "vod_id": vid,
                    "vod_name": name or vid.split("/")[-1],
                    "vod_pic": self._fix_url(pic),
                    "vod_content": "",
                    "vod_play_from": "$$$".join(play_from),
                    "vod_play_url": "$$$".join(play_url)
                })
            except Exception as e:
                print(f"detailContent error: {e}")
        return {"list": result}

    def searchContent(self, key, quick=False, pg=1):
        pg = int(pg) if str(pg).isdigit() else 1
        try:
            encoded_key = urllib.parse.quote(key)
            url = f"{self.host}/index.php/vod/search/wd/{encoded_key}/page/{pg}.html"
            html = self._fetch(url)
            videos = self._parse_video_list(html)
            return {"list": videos, "page": pg, "pagecount": 10, "limit": 20, "total": len(videos)}
        except:
            return {"list": [], "page": pg, "pagecount": 1, "limit": 20, "total": 0}

    def playerContent(self, flag, id, vipFlags=None):
        """获取播放地址 - 优先提取直链"""
        # 处理反斜杠转义
        id = id.replace('\\/', '/')
        
        # 如果已经是直链，直接返回
        if (id.startswith('http://') or id.startswith('https://')) and ('.m3u8' in id or '.mp4' in id or '.flv' in id):
            return {
                "parse": 0,
                "url": id,
                "header": {
                    "User-Agent": self.ua,
                    "Referer": self.host + "/"
                }
            }

        # 补全URL
        play_url = self._fix_url(id)

        try:
            html = self._fetch(play_url)
            direct_url = self._extract_play_url(html)
            if direct_url:
                # 确保直链是完整的
                final_url = self._fix_url(direct_url)
                return {
                    "parse": 0,
                    "url": final_url,
                    "header": {
                        "User-Agent": self.ua,
                        "Referer": play_url
                    }
                }

            iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
            if iframe_match:
                iframe_url = self._fix_url(iframe_match.group(1))
                if iframe_url and iframe_url != play_url:
                    iframe_html = self._fetch(iframe_url)
                    direct_url = self._extract_play_url(iframe_html)
                    if direct_url:
                        final_url = self._fix_url(direct_url)
                        return {
                            "parse": 0,
                            "url": final_url,
                            "header": {
                                "User-Agent": self.ua,
                                "Referer": iframe_url
                            }
                        }
                    return {
                        "parse": 1,
                        "url": iframe_url,
                        "header": {
                            "User-Agent": self.ua,
                            "Referer": play_url
                        }
                    }

        except Exception as e:
            print(f"playerContent error: {e}")

        return {
            "parse": 1,
            "url": play_url,
            "header": {
                "User-Agent": self.ua,
                "Referer": self.host + "/"
            }
        }

    def localProxy(self, params):
        if not params:
            return None

        url = params.get("url") or params.get("src") or ""
        if not url or ".m3u8" not in url:
            return None

        try:
            import requests
            req = requests.get(url, headers=self.headers, timeout=15)
            content = req.text

            base_url = url.rsplit("/", 1)[0] + "/"
            lines = content.split("\n")
            new_lines = []

            for line in lines:
                line = line.strip()
                if line.startswith("#EXT-X-MAP:URI="):
                    match = re.search(r'URI="([^"]+)"', line)
                    if match:
                        map_url = match.group(1)
                        if not map_url.startswith("http"):
                            map_url = base_url + map_url
                        new_lines.append('#EXT-X-MAP:URI="' + map_url + '"')
                    else:
                        new_lines.append(line)
                elif line and not line.startswith("#"):
                    if not line.startswith("http"):
                        line = base_url + line
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            result_content = "\n".join(new_lines) + "\n"
            return [
                200,
                "application/vnd.apple.mpegurl",
                result_content.encode("utf-8")
            ]
        except Exception as e:
            print("localProxy error:", e)
            return None

    def getDependence(self):
        return []

    def destroy(self):
        pass