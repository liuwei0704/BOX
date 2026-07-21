import re
import requests
import json

class Spider:
    def __init__(self):
        self.base_url = 'https://m.ydfdj.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G9910) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Referer': 'https://m.ydfdj.com'
        }

    def init(self, name=None):
        self.base_url = 'https://m.ydfdj.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G9910) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Referer': 'https://m.ydfdj.com'
        }
        if name:
            self.name = name
        return self

    def getDependence(self):
        return []

    def homeContent(self, filter=True):
        result = {'class': [], 'list': []}
        try:
            url = self.base_url + '/'
            r = requests.get(url, headers=self.headers, timeout=10)
            html = r.text

            # 分类
            classes = []
            class_pattern = r'<li> <a href="/type/(\d+)\.html">(.*?)</a> </li>'
            for match in re.finditer(class_pattern, html, re.S):
                class_id = match.group(1)
                class_name = match.group(2).strip()
                if class_name and class_name not in ['柠檬影视', '排行榜']:
                    classes.append({'type_id': class_id, 'type_name': class_name})
            
            if not classes:
                classes = [
                    {'type_id': '1', 'type_name': '电影'},
                    {'type_id': '2', 'type_name': '电视剧'},
                    {'type_id': '3', 'type_name': '综艺'},
                    {'type_id': '4', 'type_name': '动漫'},
                    {'type_id': '36', 'type_name': '短剧'}
                ]
            result['class'] = classes

            # 首页推荐
            vod_items = []
            li_pattern = r'<li class="col-md-6 col-sm-4 col-xs-3">.*?<a class="stui-vodlist__thumb.*?" href="(/det/\d+\.html)".*?data-original="(.*?)".*?<span class="pic-text text-right">(.*?)</span>.*?<a.*?href="/det/\d+\.html".*?>(.*?)</a>'
            li_matches = re.finditer(li_pattern, html, re.S)
            
            for li_match in li_matches:
                vod_url = li_match.group(1)
                pic = li_match.group(2)
                status = li_match.group(3).strip()
                title = re.sub(r'<[^>]+>', '', li_match.group(4)).strip()
                
                if title:
                    vod_items.append({
                        'vod_id': vod_url,
                        'vod_name': title,
                        'vod_pic': pic,
                        'vod_remarks': status
                    })
            
            if vod_items:
                seen = set()
                unique_items = []
                for item in vod_items:
                    if item['vod_id'] not in seen:
                        seen.add(item['vod_id'])
                        unique_items.append(item)
                result['list'] = [{'type_id': '0', 'list': unique_items[:20]}]
            
            return result
        except Exception as e:
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        return self.homeContent()

    def categoryContent(self, tid, pg, filter, extend):
        result = {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 0, 'total': 0}
        try:
            url = f'{self.base_url}/type/{tid}-{pg}.html'
            r = requests.get(url, headers=self.headers, timeout=10)
            html = r.text
            
            vod_list = []
            li_pattern = r'<li class="col-md-6 col-sm-4 col-xs-3">.*?<a class="stui-vodlist__thumb.*?" href="(/det/\d+\.html)".*?data-original="(.*?)".*?<span class="pic-text text-right">(.*?)</span>.*?<p class="title text-overflow h4_add"><a[^>]*>(.*?)</a>'
            li_matches = re.finditer(li_pattern, html, re.S)
            
            for li_match in li_matches:
                vod_url = li_match.group(1)
                pic = li_match.group(2)
                status = li_match.group(3).strip()
                title = li_match.group(4).strip()
                
                if title:
                    vod_list.append({
                        'vod_id': vod_url,
                        'vod_name': title,
                        'vod_pic': pic,
                        'vod_remarks': status
                    })
            
            # 分页
            pagecount = 1
            page_pattern = rf'<a href="/type/{tid}-(\d+)\.html"[^>]*>(\d+)</a>'
            page_matches = re.findall(page_pattern, html)
            if page_matches:
                pages = [int(p[1]) for p in page_matches]
                pagecount = max(pages) if pages else 1
            
            result['list'] = vod_list
            result['pagecount'] = pagecount
            result['limit'] = len(vod_list)
            result['total'] = pagecount * len(vod_list) if pagecount > 1 else len(vod_list)
            
            return result
        except Exception as e:
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 0, 'total': 0}

    def detailContent(self, ids):
        result = {'list': []}
        try:
            vid = ids[0]
            url = f'{self.base_url}{vid}'
            r = requests.get(url, headers=self.headers, timeout=10)
            html = r.text
            
            vod_info = {}
            
            # 标题
            title_match = re.search(r'<h1 class="title">(.*?)</h1>', html)
            if title_match:
                vod_info['vod_name'] = title_match.group(1).strip()
            
            # 图片
            pic_match = re.search(r'<a class="stui-vodlist__thumb picture v-thumb"[^>]*>.*?<img class="lazyload"[^>]*data-original="(.*?)"', html, re.S)
            if pic_match:
                vod_info['vod_pic'] = pic_match.group(1)
            
            # 简介
            desc_match = re.search(r'<span class="detail-content".*?>(.*?)</span>', html, re.S)
            if desc_match:
                desc = desc_match.group(1).strip()
                desc = re.sub(r'<[^>]+>', '', desc)
                vod_info['vod_content'] = desc.strip()
            
            # 播放列表
            play_from_list = []
            play_url_list = []
            
            tab_pattern = r'<ul class="nav nav-tabs active">(.*?)</ul>'
            tab_match = re.search(tab_pattern, html, re.S)
            if tab_match:
                tab_html = tab_match.group(1)
                from_matches = re.findall(r'<li.*?><a href="#playlist(\d+)" data-toggle="tab"[^>]*>(.*?)</a></li>', tab_html)
                
                for from_match in from_matches:
                    tab_id = from_match[0]
                    from_name = from_match[1].strip()
                    
                    playlist_pattern = rf'<div id="playlist{tab_id}" class="tab-pane fade in clearfix">.*?<ul class="stui-content__playlist clearfix column8">(.*?)</ul>'
                    playlist_match = re.search(playlist_pattern, html, re.S)
                    
                    if playlist_match:
                        playlist_html = playlist_match.group(1)
                        play_matches = re.findall(r'<li><a class="btn[^"]*" href="([^"]+)"[^>]*>(.*?)</a></li>', playlist_html)
                        
                        if play_matches:
                            play_from_list.append(from_name)
                            play_urls = []
                            for play_match in play_matches:
                                play_page_url = play_match[0]
                                play_name = play_match[1].strip()
                                play_urls.append(f'{play_name}${play_page_url}')
                            play_url_list.append('#'.join(play_urls))
            
            if play_from_list:
                vod_info['vod_play_from'] = '$$$'.join(play_from_list)
                vod_info['vod_play_url'] = '$$$'.join(play_url_list)
            
            if vod_info:
                result['list'] = [vod_info]
            return result
        except Exception as e:
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        result = {}
        try:
            play_url = f'{self.base_url}{id}'
            r = requests.get(play_url, headers=self.headers, timeout=10)
            html = r.text
            
            player_pattern = r'var player_aaaa\s*=\s*({.*?});'
            player_match = re.search(player_pattern, html, re.S)
            
            if player_match:
                try:
                    player_json = player_match.group(1)
                    url_match = re.search(r'"url"\s*:\s*"(.*?)"', player_json)
                    if url_match:
                        video_url = url_match.group(1).replace('\\/', '/')
                        result['url'] = video_url
                        result['parse'] = 0
                        result['header'] = {
                            'User-Agent': self.headers['User-Agent'],
                            'Referer': self.base_url
                        }
                        return result
                except:
                    pass
            
            m3u8_pattern = r'(https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*)'
            m3u8_matches = re.findall(m3u8_pattern, html)
            if m3u8_matches:
                result['url'] = m3u8_matches[0]
                result['parse'] = 0
                result['header'] = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': self.base_url
                }
                return result
            
            return {}
        except Exception as e:
            return {}

    # 搜索功能已移除 - 返回空列表
    def searchContent(self, key, quick):
        return {'list': []}