# -*- coding: utf-8 -*-
import re, json, base64
from urllib.parse import quote, unquote
from base.spider import Spider

class Spider(Spider):
    def getName(self): return "短劇影視屋"
    def init(self, extend=""): pass
    host = 'https://www.djys.tv'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', 'Referer': 'https://www.djys.tv/'}

    def _normalize_url(self, url):
        if not url or 'javascript:' in url: return ''
        url = url.strip()
        if url.startswith('//'): return f"https:{url}"
        elif url.startswith('/'): return f"{self.host}{url}"
        return url

    def homeContent(self, filter):
        try:
            html = self.fetch(self.host, headers=self.headers).text
            classes = []
            type_matches = re.findall(r'href="([^"]*/vod/type/id/[^"]+\.html)"[^>]*>([^<]+)</a>', html)
            for href, name in type_matches:
                if name not in ['首頁', '最新', '排行', 'APP', '留言', '首页', '觀看記錄', '观看记录'] and name not in [c['type_name'] for c in classes]:
                    classes.append({'type_name': name, 'type_id': self._normalize_url(href)})
            
            videos = []
            vod_pattern = re.compile(r'hl-list-item[\s\S]*?href="([^"]+)"[\s\S]*?title="([^"]+)"[\s\S]*?data-original="([^"]+)"[\s\S]*?remarks">([^<]+)</span>', re.S)
            for href, name, pic, remark in vod_pattern.findall(html):
                # 過濾廣告和觀看記錄項
                if name in ["觀看記錄", "观看记录"] or any(ad in name for ad in ["廣告", "官網"]):
                    continue
                videos.append({
                    'vod_id': self._normalize_url(href),
                    'vod_name': name,
                    'vod_pic': self._normalize_url(pic),
                    'vod_remarks': remark.strip()
                })
            
            if not classes:
                classes = [{'type_name': '精選短劇', 'type_id': f'{self.host}/vod/type/id/jingxuanduanju.html'}]
            return {'class': classes, 'list': videos[:30]}
        except: return {'class': [], 'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg)
        url = tid if pg == 1 else tid.replace('.html', f'/page/{pg}.html')
        try:
            html = self.fetch(url, headers=self.headers).text
            videos = []
            vod_pattern = re.compile(r'hl-list-item[\s\S]*?href="([^"]+)"[\s\S]*?title="([^"]+)"[\s\S]*?data-original="([^"]+)"[\s\S]*?remarks">([^<]+)</span>', re.S)
            for href, name, pic, remark in vod_pattern.findall(html):
                if name in ["觀看記錄", "观看记录"]:
                    continue
                videos.append({
                    'vod_id': self._normalize_url(href),
                    'vod_name': name,
                    'vod_pic': self._normalize_url(pic),
                    'vod_remarks': remark.strip()
                })
            return {'list': videos, 'page': pg, 'pagecount': 999}
        except: return {'list': [], 'page': pg}

    def detailContent(self, ids):
        try:
            url = self._normalize_url(ids[0])
            html = self.fetch(url, headers=self.headers).text
            
            # 提取標題 (使用 hl-dc-title)
            name = re.search(r'class="hl-dc-title[^>]*>([^<]+)<', html)
            # 提取圖片 (從 meta 或 detail 區塊提取)
            pic = re.search(r'class="hl-item-thumb hl-lazy"[^>]*data-original="([^"]+)"', html)
            if not pic:
                pic = re.search(r'property="og:image" content="([^"]+)"', html)
                
            # 提取備註 (狀態：全80集)
            remark = re.search(r'<em class="hl-text-muted">狀態：</em><span[^>]*>([^<]+)<', html)
            # 提取簡介
            content = re.search(r'class="hl-content-text"><em>([\s\S]*?)</em>', html)
            
            vod = {
                'vod_id': ids[0],
                'vod_name': name.group(1) if name else '未知',
                'vod_pic': self._normalize_url(pic.group(1)) if pic else '',
                'vod_remarks': remark.group(1).strip() if remark else '',
                'vod_content': content.group(1).strip() if content else '',
                'type_name': ''
            }
            
            # 1. 提取播放源名稱 (如：無盡資源)
            # 根據 HTML：<a class="hl-tabs-btn hl-slide-swiper active" ...><i ...></i>&nbsp;無盡資源</a>
            from_names = re.findall(r'class="hl-tabs-btn[^>]*>[\s\S]*?&nbsp;([^<]+)<', html)
            
            # 2. 提取播放列表區塊
            # 根據 HTML：<ul class="hl-plays-list hl-sort-list clearfix" id="hl-plays-list">...</ul>
            urls_list = []
            play_blocks = re.findall(r'id="hl-plays-list"[^>]*>([\s\S]*?)</ul>', html)
            
            for block in play_blocks:
                # 提取具體集數連結：<a href="/vod/play/id/40852/sid/1/nid/1.html">1-20集</a>
                links = re.findall(r'href="([^"]+)"[^>]*>([^<]+)</a>', block)
                if links:
                    # 格式化為：集數$URL#集數$URL
                    urls_list.append("#".join([f"{l[1]}${self._normalize_url(l[0])}" for l in links]))
            
            vod['vod_play_from'] = "$$$".join(from_names) if from_names else "默認"
            vod['vod_play_url'] = "$$$".join(urls_list)
            
            return {'list': [vod]}
        except Exception as e:
            return {'list': []}

    def searchContent(self, key, quick, pg=1):
        url = f"{self.host}/vod/search/page/{pg}/wd/{quote(key)}.html"
        try:
            html = self.fetch(url, headers=self.headers).text
            videos = []
            vod_pattern = re.compile(r'hl-list-item[\s\S]*?href="([^"]+)"[\s\S]*?title="([^"]+)"[\s\S]*?data-original="([^"]+)"[\s\S]*?remarks">([^<]+)</span>', re.S)
            for href, name, pic, remark in vod_pattern.findall(html):
                if name in ["觀看記錄", "观看记录"]:
                    continue
                videos.append({
                    'vod_id': self._normalize_url(href),
                    'vod_name': name,
                    'vod_pic': self._normalize_url(pic),
                    'vod_remarks': remark.strip()
                })
            return {'list': videos, 'page': pg}
        except: return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            html = self.fetch(id, headers=self.headers).text
            player_json = re.search(r'player_aaaa\s*=\s*(\{.*?\})</script>', html)
            if player_json:
                data = json.loads(player_json.group(1))
                play_url = data.get('url', '')
                if data.get('encrypt') == '1':
                    play_url = unquote(base64.b64decode(play_url).decode('utf-8'))
                elif data.get('encrypt') == '2':
                    play_url = unquote(play_url)
                
                parse = 0 if ('.m3u8' in play_url or '.mp4' in play_url) else 1
                return {'parse': parse, 'url': play_url, 'header': self.headers}
            return {'parse': 1, 'url': id}
        except: return {'parse': 1, 'url': id}