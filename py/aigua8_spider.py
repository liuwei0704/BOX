# coding=utf-8
import re
import json
import base64
import urllib.parse
import requests
from bs4 import BeautifulSoup

class Spider():
    """爱瓜TV 爬虫"""

    def __init__(self):
        self.host = "http://m.aigua8.com"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': self.host,
        }

    def getName(self):
        return "爱瓜TV"

    def getDependence(self):
        return []

    def init(self, extend=""):
        try: self.session.get(self.host, headers=self.headers, timeout=5)
        except: pass

    def homeVideoContent(self):
        return self.homeContent(False)

    def _fetch(self, url, params=None):
        try:
            full_url = url
            if params:
                full_url = url + '?' + urllib.parse.urlencode(params)
            r = self.session.get(full_url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            return r.text
        except Exception as e:
            print(f"请求失败: {url} - {e}")
            return ""

    def _fetch_json(self, url, params=None):
        try:
            full_url = url
            if params:
                full_url = url + '?' + urllib.parse.urlencode(params)
            r = self.session.get(full_url, headers=self.headers, timeout=10)
            return r.json()
        except Exception as e:
            print(f"JSON请求失败: {url} - {e}")
            return {}

    def _make_pic_url(self, url):
        if not url:
            return ""
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        return self.host + url

    def homeContent(self, filter):
        result = {"class": [], "list": []}
        html = self._fetch(self.host + '/')
        if not html:
            return result
        soup = BeautifulSoup(html, 'html.parser')
        nav = soup.select('#topNav .swiper-slide-li a')
        for a in nav:
            href = a.get('href', '')
            match = re.search(r'channel_id=(\d+)', href)
            if match:
                cid = match.group(1)
                name = a.get_text(strip=True)
                if cid != '0':
                    result["class"].append({"type_id": cid, "type_name": name})
        banner_items = soup.select('#video-list-banner .swiper-slide')
        for item in banner_items:
            try:
                data_link = item.get('data-link', '')
                vid_match = re.search(r'video_id=(\d+)', data_link)
                title_el = item.select_one('.video-banner-title .title')
                pic_el = item.select_one('.piclist-link')
                style = pic_el.get('style', '') if pic_el else ''
                pic_match = re.search(r'url\(([^)]+)\)', style)
                vod_id = vid_match.group(1) if vid_match else ''
                vod_name = title_el.get_text(strip=True) if title_el else ''
                vod_pic = pic_match.group(1) if pic_match else ''
                if vod_id and vod_name:
                    result["list"].append({"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic, "vod_remarks": "推荐"})
            except Exception:
                continue
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 12, "total": 0}
        params = {"channel_id": tid, "page": pg}
        if extend:
            try:
                ext = json.loads(extend) if isinstance(extend, str) else extend
                for key in ['tag', 'area', 'year', 'sort']:
                    if key in ext and ext[key]:
                        params[key] = ext[key]
            except:
                pass
        data = self._fetch_json(self.host + '/video/refresh-cates', params)
        if data.get('errno') == 0:
            d = data.get('data', {})
            result["pagecount"] = int(d.get('total_page', 1))
            result["total"] = int(d.get('total_count', 0))
            for item in d.get('list', []):
                vod_id = str(item.get('video_id', ''))
                vod_name = item.get('video_name', '')
                vod_pic = self._make_pic_url(item.get('cover', ''))
                vod_remarks = item.get('score', '')
                if vod_id and vod_name:
                    result["list"].append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
        return result

    def searchContent(self, key, quick, pg=1):
        result = {"list": []}
        html = self._fetch(self.host + '/video/search', {"keyword": key})
        if not html:
            return result
        soup = BeautifulSoup(html, 'html.parser')
        video_items = soup.select('.video-item')
        if not video_items:
            video_items = soup.select('a[href*="video_id"]')
        for item in video_items:
            try:
                if item.name == 'a':
                    link = item
                else:
                    link = item.select_one('a[href*="video_id"]')
                if not link:
                    continue
                href = link.get('href', '')
                vid_match = re.search(r'video_id=(\d+)', href)
                if not vid_match:
                    continue
                vod_id = vid_match.group(1)
                img = item.select_one('img')
                vod_pic = img.get('originalsrc') or img.get('data-src') or img.get('src') or '' if img else ''
                vod_pic = self._make_pic_url(vod_pic)
                name_el = item.select_one('.video-item-name') or item.select_one('.title') or item.select_one('p')
                vod_name = name_el.get_text(strip=True) if name_el else (img.get('alt', '') if img else '')
                remarks_el = item.select_one('.video-item-remarks') or item.select_one('.remarks')
                vod_remarks = remarks_el.get_text(strip=True) if remarks_el else ''
                if vod_id and vod_name:
                    result["list"].append({"vod_id": vod_id, "vod_name": vod_name, "vod_pic": vod_pic, "vod_remarks": vod_remarks})
            except Exception:
                continue
        return result

    def detailContent(self, ids):
        result = {"list": []}
        vid = str(ids[0]).strip() if isinstance(ids, list) else str(ids).strip()
        html = self._fetch(self.host + '/video/detail', {"video_id": vid})
        if not html:
            return result
        soup = BeautifulSoup(html, 'html.parser')
        vod_info = {
            "vod_id": vid, "vod_name": "", "vod_pic": "", "type_name": "",
            "vod_year": "", "vod_area": "", "vod_remarks": "",
            "vod_actor": "", "vod_director": "", "vod_content": "",
            "vod_play_from": "", "vod_play_url": ""
        }
        title_el = soup.select_one('.video-title') or soup.select_one('title')
        if title_el:
            vod_info["vod_name"] = title_el.get_text(strip=True).split('-')[0].strip()
        api_data = self._fetch_json(self.host + '/video/refresh-cates',
                                     {"channel_id": "", "page": 1, "video_id": vid})
        if api_data.get('errno') == 0 and api_data.get('data', {}).get('list'):
            item = api_data['data']['list'][0]
            if not vod_info["vod_name"]:
                vod_info["vod_name"] = item.get('video_name', '')
            vod_info["vod_pic"] = self._make_pic_url(item.get('cover', ''))
            vod_info["vod_remarks"] = item.get('score', '')
            vod_info["vod_actor"] = item.get('artist', '')
            vod_info["vod_director"] = item.get('director', '')
            vod_info["vod_content"] = item.get('intro', '')
            cat = item.get('category', '')
            if cat:
                vod_info["type_name"] = cat.replace(' ', '/')
        script_text = ''
        for s in soup.select('script'):
            if s.string:
                script_text += s.string + '\n'
        chapter_id = ''
        cm = re.search(r"'chapterId'\s*:\s*'(\d+)'", script_text)
        if not cm:
            cm = re.search(r'"chapterId"\s*:\s*"(\d+)"', script_text)
        if cm:
            chapter_id = cm.group(1)
        if chapter_id:
            source_map = {'1': '普快线路', '2': '超快线路'}
            from_list = []
            url_parts = []
            ep_items = soup.select('.video-detail-series-bottom li a')
            for sid in ['1', '2']:
                sname = source_map.get(sid, f'线路{sid}')
                from_list.append(sname)
                if ep_items:
                    seen = set()
                    ep_list = []
                    for ep in ep_items:
                        ep_text = ep.get_text(strip=True)
                        if ep_text not in seen:
                            seen.add(ep_text)
                            ep_list.append(f"{ep_text}${vid}|{chapter_id}|{sid}")
                    url_parts.append("#".join(ep_list) if ep_list else f"正片${vid}|{chapter_id}|{sid}")
                else:
                    url_parts.append(f"正片${vid}|{chapter_id}|{sid}")
            vod_info["vod_play_from"] = "$$$".join(from_list)
            vod_info["vod_play_url"] = "$$$".join(url_parts)
        cover_el = soup.select_one('.video-detail-cover img') or soup.select_one('.video-play-left img')
        if cover_el and not vod_info["vod_pic"]:
            vod_info["vod_pic"] = self._make_pic_url(cover_el.get('src') or cover_el.get('data-src') or '')
        result["list"].append(vod_info)
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {"parse": 1, "playUrl": "", "url": ""}
        sid = str(id).strip()
        if sid.startswith('http'):
            result["url"] = sid
            result["header"] = dict(self.headers)
            result["parse"] = 0 if '.m3u8' in sid else 1
            return result
        parts = sid.split('|')
        video_id = parts[0] if len(parts) > 0 else sid
        chapter_id = parts[1] if len(parts) > 1 else ''
        source_id = parts[2] if len(parts) > 2 else '1'
        self.headers['Referer'] = self.host + '/video/detail?video_id=' + video_id
        data = self._fetch_json(self.host + '/video/play-url', {
            "citycode": "SIN", "page": "detail",
            "chapterId": chapter_id, "videoId": video_id, "sourceId": source_id
        })
        if data.get('errno') == 0:
            urlinfo = data.get('data', {}).get('urlinfo', {})
            play_url = urlinfo.get('resource_url', '')
            if isinstance(play_url, dict):
                # 优先选非 yfvodcdn 的域名
                for k in [source_id, '16', '21', '1']:
                    u = play_url.get(k, '')
                    if u and 'yfvodcdn' not in u:
                        play_url = u
                        break
                if isinstance(play_url, dict):
                    play_url = list(play_url.values())[0] if play_url else ''
            if play_url:
                result["url"] = play_url
                result["header"] = dict(self.headers)
                result["parse"] = 0 if '.m3u8' in play_url else 1
                return result
        html = self._fetch(self.host + '/video/detail', {"video_id": video_id})
        if html:
            m3u8 = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
            if m3u8:
                result["url"] = m3u8.group(1).replace('\\/', '/')
                result["header"] = dict(self.headers)
                result["parse"] = 0
                return result
        return result