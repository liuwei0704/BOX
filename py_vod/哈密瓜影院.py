# -*- coding: utf-8 -*-
# 哈密瓜影院 - TVBox/FongMi 爬虫
# 站点: https://hmgyy.com
import re
import sys
import json
import requests
import urllib.parse
from bs4 import BeautifulSoup

# 禁用SSL证书验证警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "哈密瓜影院"

    def init(self, extend=""):
        self.host = "https://hmgyy.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update(self.headers)
        # 类型映射
        self.type_map = {"dy": "1", "dsj": "2", "zy": "3", "dj": "4", "dm": "5"}

    def fetch(self, url, timeout=15):
        try:
            response = self.session.get(url, timeout=timeout, verify=False)
            response.encoding = response.apparent_encoding or 'utf-8'
            return response
        except Exception as e:
            return None

    def homeContent(self, filter):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {
            "class": [
                {"type_id": "1", "type_name": "電影"},
                {"type_id": "2", "type_name": "劇集"},
                {"type_id": "3", "type_name": "綜藝"},
                {"type_id": "4", "type_name": "短劇"},
                {"type_id": "5", "type_name": "動漫"},
            ],
            "filters": self._get_filters(),
            "list": []
        }
        try:
            res = self.fetch(self.host)
            if res and res.status_code == 200:
                result['list'] = self._parse_videos(res.text, limit=24)
        except Exception as e:
            pass
        return result

    def getHomeContent(self):
        """TVBox/FongMi 兼容方法"""
        return self.homeContent(False)

    def homeVideoContent(self):
        result = {"list": []}
        try:
            res = self.fetch(self.host)
            if res and res.status_code == 200:
                result['list'] = self._parse_videos(res.text)
        except Exception as e:
            pass
        return result

    def categoryContent(self, tid, pg, filter, extend):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {"list": [], "page": int(pg), "pagecount": 999, "limit": 20, "total": 999}
        try:
            page_num = int(pg) if pg else 1
            # 查找类型路径
            type_path = "dy"
            for k, v in self.type_map.items():
                if v == str(tid):
                    type_path = k
                    break

            if page_num > 1:
                url = f"{self.host}/type/{type_path}?page={page_num}"
            else:
                url = f"{self.host}/type/{type_path}"

            res = self.fetch(url)
            if res and res.status_code == 200:
                result['list'] = self._parse_videos(res.text)
        except Exception as e:
            pass
        return result

    def searchContent(self, key, quick, pg=1):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {"list": []}
        try:
            page_num = int(pg) if pg else 1
            search_key = urllib.parse.quote(key)
            if page_num > 1:
                url = f"{self.host}/search?kw={search_key}&page={page_num}"
            else:
                url = f"{self.host}/search?kw={search_key}"
            res = self.fetch(url)
            if res and res.status_code == 200:
                result['list'] = self._parse_videos(res.text)
        except Exception as e:
            pass
        return result

    def detailContent(self, ids):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {"list": []}
        try:
            vod_id = ids[0] if ids else ""
            if not vod_id:
                return result

            url = f"{self.host}/details/{vod_id}"
            res = self.fetch(url)
            if not res or res.status_code != 200:
                return result

            soup = BeautifulSoup(res.text, 'html.parser')

            # 获取标题
            vod_name = ""
            h1 = soup.select_one('.details h1')
            if h1:
                vod_name = h1.get_text(strip=True)

            # 获取图片
            vod_pic = ""
            img = soup.select_one('.details-img')
            if img:
                vod_pic = img.get('src', '') or img.get('data-original', '')
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = self.host + vod_pic

            # 获取简介和其他信息
            vod_content = ""
            vod_remarks = ""
            for item in soup.select('.info'):
                text = item.get_text(strip=True)
                if '简介' in text or '介绍' in text:
                    vod_content = text.split('：', 1)[-1].strip() if '：' in text else text
                elif '状态' in text:
                    vod_remarks = text.split('：', 1)[-1].strip() if '：' in text else text

            # 提取播放数据
            play_from = []
            play_url = []

            # 尝试解析 episodesData
            match = re.search(r'episodesData\s*=\s*(\{.*?\});', res.text, re.S | re.I)
            if match:
                try:
                    data_str = match.group(1)
                    data_str = re.sub(r'//[^\n]*', '', data_str)
                    data_str = data_str.replace('\\/', '/')
                    data_str = re.sub(r'([\{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', data_str)
                    data_str = re.sub(r',\s*\}', '}', data_str)
                    data_str = re.sub(r',\s*\]', ']', data_str)
                    ep_data = json.loads(data_str)

                    # 将线路按名称排序（线路一、线路二、线路三）
                    sorted_items = sorted(ep_data.items(), key=lambda x: x[0])
                    for line_name, episodes in sorted_items:
                        if not episodes:
                            continue
                        play_from.append(line_name)
                        parts = []
                        # 反转剧集列表，让第1集在最前面
                        for ep in reversed(episodes):
                            ep_name = ep.get('name', '')
                            ep_path = ep.get('path', '')
                            id_match = re.search(r'/player/(\d+)/(\d+)', ep_path)
                            if id_match:
                                parts.append(f"{ep_name}${id_match.group(1)}-{id_match.group(2)}")
                        if parts:
                            play_url.append("#".join(parts))
                except Exception as e:
                    pass

            # 如果没有提取到线路，尝试从HTML中提取播放链接
            if not play_from:
                play_links = soup.select('a[href*="/player/"]')
                if play_links:
                    play_from.append("默认线路")
                    parts = []
                    # 反转剧集列表
                    for a in reversed(play_links):
                        href = a.get('href', '')
                        text = a.get_text(strip=True) or a.get('title', '')
                        id_match = re.search(r'/player/(\d+)/(\d+)', href)
                        if id_match:
                            parts.append(f"{text}${id_match.group(1)}-{id_match.group(2)}")
                    if parts:
                        play_url.append("#".join(parts))

            # 如果还是没有，使用默认
            if not play_from:
                play_from.append("线路1")
                play_url.append(f"正片${vod_id}-1")

            vod = {
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_remarks": vod_remarks,
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_url)
            }
            result['list'] = [vod]
        except Exception as e:
            pass
        return result
    def playerContent(self, flag, id, vipFlags):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {"parse": 1, "playUrl": "", "url": ""}
        try:
            # 处理 id 格式：可能是 "vod_id" 或 "vod_id-episode"
            parts = id.split('-')
            vod_id = parts[0]
            ep = parts[1] if len(parts) > 1 else "1"

            url = f"{self.host}/player/{vod_id}/{ep}"
            res = self.fetch(url)
            if not res or res.status_code != 200:
                result["url"] = url
                return result

            html = res.text

            # 尝试提取m3u8
            m3u8_match = re.search(r'["\'](https?://[^"\']*\.m3u8[^"\']*)', html, re.S | re.I)
            if m3u8_match:
                result["parse"] = 0
                result["url"] = m3u8_match.group(1)
                result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
                return result

            # 尝试提取mp4
            mp4_match = re.search(r'["\'](https?://[^"\']*\.mp4[^"\']*)', html, re.S | re.I)
            if mp4_match:
                result["parse"] = 0
                result["url"] = mp4_match.group(1)
                result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
                return result

            # 尝试提取iframe
            iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.S | re.I)
            if iframe_match:
                src = iframe_match.group(1)
                if '.m3u8' in src or '.mp4' in src:
                    result["parse"] = 0
                    result["url"] = src
                    result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
                    return result
                result["parse"] = 1
                result["url"] = src
                result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
                return result

            # 尝试提取video标签
            video_match = re.search(r'<video[^>]*src=["\']([^"\']+)["\']', html, re.S | re.I)
            if video_match:
                result["parse"] = 0
                result["url"] = video_match.group(1)
                result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
                return result

            # 降级到WebView嗅探
            result["parse"] = 1
            result["url"] = url
            result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
        except Exception as e:
            result["parse"] = 1
            result["url"] = f"{self.host}/player/{id}"
            result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
        return result
    def _get_filters(self):
        return {
            "1": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}],
            "2": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}],
            "3": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}],
            "4": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}],
            "5": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}]
        }

    def _parse_videos(self, html, limit=0):
        videos = []
        soup = BeautifulSoup(html, 'html.parser')

        # 尝试多种选择器
        items = soup.select('a.video')
        if not items:
            items = soup.select('.video-item, .module-item, .vod-item')

        for item in items:
            # 获取链接和ID
            a = item if item.name == 'a' else item.select_one('a')
            if not a:
                continue

            href = a.get('href', '')
            vod_id = ""
            if '/details/' in href:
                vod_id = href.replace('/details/', '').strip('/')
            if not vod_id:
                id_match = re.search(r'/details/(\d+)', href)
                if id_match:
                    vod_id = id_match.group(1)
            if not vod_id:
                continue

            # 获取图片
            vod_pic = ""
            img_box = item.select_one('.img-box')
            if img_box:
                vod_pic = img_box.get('data', '')
                if not vod_pic:
                    style = img_box.get('style', '')
                    style_match = re.search(r'url\(["\']?([^"\')\s]+)', style)
                    if style_match:
                        vod_pic = style_match.group(1)
            if not vod_pic:
                img = item.select_one('img')
                if img:
                    vod_pic = img.get('data-original') or img.get('data-src') or img.get('src')
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = self.host + vod_pic

            # 获取标题
            vod_name = ""
            title_el = item.select_one('.title p, .title, .name')
            if title_el:
                vod_name = title_el.get_text(strip=True)
            if not vod_name:
                vod_name = a.get('title', '')

            # 获取备注
            vod_remarks = ""
            desc_el = item.select_one('.desc .desc, .desc, .remarks, .note')
            if desc_el:
                vod_remarks = desc_el.get_text(strip=True)
            if not vod_remarks:
                note_el = item.select_one('.module-item-note, .tag')
                if note_el:
                    vod_remarks = note_el.get_text(strip=True)

            if vod_id and vod_name:
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })

        if limit and len(videos) > limit:
            return videos[:limit]
        return videos