# -*- coding: utf-8 -*-
import sys
import requests
import urllib.parse
import urllib.request
import ssl
import re
import json
import base64
from lxml import etree
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    def getName(self):
        return "Rou"

    def init(self, extend):
        self.home_url = 'https://rouva4.xyz'
        self.real_home = 'https://rouva4.xyz/home'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.build_id = "S87AMM5U2FXdSraJ7I_Wz"

    def getDependence(self):
        return []

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def _get(self, url, headers=None):
        if headers is None:
            headers = self.headers.copy()
        else:
            merged = self.headers.copy()
            merged.update(headers)
            headers = merged
        try:
            res = requests.get(url, headers=headers, timeout=15)
            return res
        except:
            return None

    def _get_raw(self, url):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
            req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
            req.add_header("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
                return response.read().decode('utf-8', errors='ignore')
        except:
            return None

    def _parse_video_item(self, item):
        hrefs = item.xpath('./@href')
        if not hrefs:
            return None
        href = hrefs[0]
        if '/v/' not in href:
            return None
        imgs = item.xpath('.//img/@src')
        pic = imgs[0] if imgs else ''
        alts = item.xpath('.//img/@alt')
        title = ''
        for alt in reversed(alts):
            if alt and alt.strip():
                title = alt.strip()
                break
        if not title:
            texts = item.xpath('.//text()')
            title = ' '.join(t.strip() for t in texts if t.strip() and len(t.strip()) > 2)
            if len(title) > 100:
                title = title[:100]
        remark = ''
        all_text = ' '.join(item.xpath('.//text()')).strip()
        quality = re.search(r'(\d{3,4}P|4K|HD)', all_text, re.IGNORECASE)
        if quality:
            remark = quality.group(1)
        time_match = re.search(r'(\d+分\d+秒|\d+:\d+:\d+|\d+:\d+)', all_text)
        if time_match:
            remark = f"{remark} {time_match.group(1)}".strip()
        return {
            'vod_id': href,
            'vod_name': title if title else '未知',
            'vod_pic': pic,
            'vod_remarks': remark,
            'vod_year': '',
            'style': {"type": "rect", "ratio": 1.5}
        }

    def homeContent(self, filter):
        cat_map = {
            "國產AV": "gcAV",
            "麻豆傳媒": "madouAV",
            "探花": "v91",
            "OnlyFans": "onlyfans"
        }
        result = {
            'class': [
                {"type_name": "國產AV", "type_id": "/t/國產AV"},
                {"type_name": "麻豆傳媒", "type_id": "/t/麻豆傳媒"},
                {"type_name": "OnlyFans", "type_id": "/t/OnlyFans"},
                {"type_name": "探花", "type_id": "/t/探花"},
                {"type_name": "自拍流出", "type_id": "/t/自拍流出"},
                {"type_name": "日本", "type_id": "/t/日本"},
            ]
        }
        if filter:
            res = self._get(f'{self.home_url}/cat')
            if res and res.status_code == 200:
                nd = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', res.text, re.DOTALL)
                if nd:
                    data = json.loads(nd.group(1))
                    pp = data.get('props', {}).get('pageProps', {})
                    filters = {}
                    for big_name, key in cat_map.items():
                        subs = pp.get(key, [])
                        if subs:
                            values = [{"n": "全部", "v": ""}]
                            for sub in subs:
                                values.append({"n": f"{sub['id']}({sub['count']})", "v": sub['id']})
                            filters[f'/t/{big_name}'] = [{"key": "tag", "name": "分类", "value": values}]
                    result['filters'] = filters
        return result

    def homeVideoContent(self):
        return self._get_video_list(self.real_home)

    def categoryContent(self, cid, page, filter, ext):
        tag = ext.get('tag', '') if ext else ''
        if tag:
            url = f'{self.home_url}/t/{urllib.parse.quote(tag)}'
        else:
            url = f'{self.home_url}{cid}'
        if page and page != '1':
            url += f'?page={page}' if '?' not in url else f'&page={page}'
        return self._get_video_list(url)

    def _get_video_list(self, url):
        try:
            res = self._get(url)
            if not res or res.status_code != 200:
                return {'list': [], 'parse': 0, 'jx': 0, 'msg': '请求失败'}
            root = etree.HTML(res.text)
            items = root.xpath('//a[contains(@href, "/v/")]')
            if not items:
                return {'list': [], 'parse': 0, 'jx': 0, 'msg': '未找到视频'}
            videos = []
            seen = set()
            for item in items:
                info = self._parse_video_item(item)
                if info and info['vod_id'] not in seen:
                    seen.add(info['vod_id'])
                    videos.append(info)
            return {'list': videos, 'parse': 0, 'jx': 0}
        except:
            return {'list': [], 'parse': 0, 'jx': 0, 'msg': '解析失败'}

    def detailContent(self, did):
        if isinstance(did, list):
            video_id = did[0]
        else:
            video_id = did
        vid = video_id.split('/')[-1] if '/' in video_id else video_id

        vd = {}
        vid_tag = ''
        play_url = ''

        api_url = f'{self.home_url}/_next/data/{self.build_id}/v/{vid}.json'
        api_res = self._get(api_url, {'Accept': 'application/json'})
        if api_res and api_res.status_code == 200:
            data = api_res.json()
            vd = data.get('pageProps', {}).get('video', {})
            ref_url = vd.get('ref', '')
            vid_tag = vd.get('vid', '')
            
            if ref_url:
                play_url = self._extract_play_url(ref_url)
            
            if not play_url:
                ev = data.get('pageProps', {}).get('ev', {})
                if ev and ev.get('d'):
                    try:
                        decoded = base64.b64decode(ev['d']).decode('latin-1')
                        result = ''.join(chr(ord(c) - ev['k']) for c in decoded)
                        ev_data = json.loads(result)
                        if ev_data.get('videoUrl'):
                            play_url = ev_data['videoUrl'].replace('/index.jpg', '/index.m3u8')
                    except:
                        pass

            if play_url and play_url.startswith('http'):
                return self._build_detail_response(video_id, vd, play_url)

        if not vd:
            video_url = f'{self.home_url}/v/{vid}'
            res = self._get(video_url)
            if res and res.status_code == 200:
                nd = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', res.text, re.DOTALL)
                if nd:
                    data = json.loads(nd.group(1))
                    vd = data.get('props', {}).get('pageProps', {}).get('video', {})
                    ref_url = vd.get('ref', '')
                    vid_tag = vd.get('vid', '')
                    
                    if ref_url:
                        play_url = self._extract_play_url(ref_url)
                    
                    if not play_url:
                        ev = data.get('pageProps', {}).get('ev', {})
                        if ev and ev.get('d'):
                            try:
                                decoded = base64.b64decode(ev['d']).decode('latin-1')
                                result = ''.join(chr(ord(c) - ev['k']) for c in decoded)
                                ev_data = json.loads(result)
                                if ev_data.get('videoUrl'):
                                    play_url = ev_data['videoUrl'].replace('/index.jpg', '/index.m3u8')
                            except:
                                pass

                    if play_url and play_url.startswith('http'):
                        return self._build_detail_response(video_id, vd, play_url)

        if not play_url and vid_tag:
            play_url = self._get_missav_url(vid_tag)
            if play_url:
                return self._build_detail_response(video_id, vd, play_url)

        return {'list': [], 'parse': 1, 'jx': 0, 'msg': '未找到播放地址'}

    def _get_missav_url(self, vid_tag):
        code = vid_tag.lower().replace(' ', '-')
        for alt_url in [
            f'https://missav.run/videos/{code}',
            f'http://missav.run/videos/{code}',
        ]:
            html = self._get_raw(alt_url)
            if not html:
                res = self._get(alt_url)
                if res and res.status_code == 200:
                    html = res.text
            if html:
                m3u8 = re.findall(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', html)
                for url in m3u8:
                    if 'preview' not in url and 'thumb' not in url:
                        return url
                break
        return None

    def _build_detail_response(self, video_id, vd, play_url):
        tags = vd.get('tags', [])
        vod_content = ''
        if tags:
            tag_links = []
            for tag in tags:
                tag_links.append(f'[a=cr:{{"id":"/t/{urllib.parse.quote(tag)}","name":"{tag}"}}/]{tag}[/a]')
            vod_content = ' '.join(tag_links)
        
        return {
            'list': [{
                'vod_id': video_id,
                'vod_name': vd.get('name', '') or vd.get('nameZh', ''),
                'vod_pic': vd.get('coverImageUrl', ''),
                'type_name': 'Rou',
                'vod_remarks': '',
                'vod_year': vd.get('createdAt', '')[:4] if vd.get('createdAt') else '',
                'vod_area': '',
                'vod_actor': '',
                'vod_director': '',
                'vod_content': vod_content,
                'vod_play_from': 'Rou',
                'vod_play_url': f'正片${play_url}',
            }],
            'parse': 1,
            'jx': 0
        }

    def _extract_play_url(self, ref_url):
        try:
            if ref_url.startswith('/'):
                ref_url = f'{self.home_url}{ref_url}'

            need_raw = any(d in ref_url for d in ['xchina.co', '91pinse.com', 'missav.ws'])
            if need_raw:
                html = self._get_raw(ref_url)
                if not html:
                    return None
                class FakeResponse:
                    def __init__(self, text):
                        self.text = text
                        self.status_code = 200
                res = FakeResponse(html)
            else:
                res = self._get(ref_url)

            if not res or res.status_code != 200:
                return None

            if '91pinse.com' in ref_url:
                all_strings = re.findall(r"'([^']{50,})'", res.text)
                for s in all_strings:
                    s_clean = s.replace('\\u003D', '=')
                    try:
                        decoded = base64.b64decode(s_clean).decode('utf-8', errors='ignore')
                        if '.m3u8' in decoded or '.mp4' in decoded:
                            return decoded
                    except:
                        continue

            stream = re.search(r"var stream = '(https?://[^']+)'", res.text)
            if stream:
                return stream.group(1)

            m3u8 = re.findall(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', res.text)
            for url in m3u8:
                if 'preview' not in url and 'thumb' not in url:
                    return url

            return None
        except:
            return None

    def searchContent(self, key, quick, page='1'):
        url = f'{self.home_url}/search?q={urllib.parse.quote(key)}'
        if page and page != '1':
            url += f'&page={page}'
        return self._get_video_list(url)

    def playerContent(self, flag, pid, vipFlags):
        return {
            'parse': 1,
            'url': pid,
            'header': {
                'Referer': 'https://xchina.co/',
                'Origin': 'https://xchina.co',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }

    def localProxy(self, params):
        pass

    def destroy(self):
        return '正在Destroy'