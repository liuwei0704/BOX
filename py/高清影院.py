# -*- coding: utf-8 -*-
import requests
import re
import html

class Spider:
    def __init__(self):
        self.host = 'https://www.moozcloud.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def getDependence(self):
        return []
    
    def init(self, extend=""):
        return {}
    
    def homeContent(self, filter):
        try:
            r = requests.get(self.host, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            classes = [
                {'type_id': '1', 'type_name': '电影'},
                {'type_id': '2', 'type_name': '电视剧'},
                {'type_id': '3', 'type_name': '动漫'},
                {'type_id': '4', 'type_name': '综艺'},
                {'type_id': '27', 'type_name': '短剧'}
            ]
            
            videos = []
            pattern = r'<ul id="home1"[^>]*>(.*?)</ul>'
            match = re.search(pattern, r.text, re.S)
            
            if match:
                ul_content = match.group(1)
                item_pattern = r'<a[^>]+href="/movie/(\d+)\.html"[^>]+title="([^"]+)"[^>]+data-original="([^"]+)"[^>]*>.*?<span class="pic-text">([^<]+)</span>'
                items = re.findall(item_pattern, ul_content, re.S)
                
                for item in items[:20]:
                    videos.append({
                        'vod_id': item[0],
                        'vod_name': html.unescape(item[1]),
                        'vod_pic': item[2],
                        'vod_remarks': item[3].strip()
                    })
            
            return {'class': classes, 'list': videos}
        except Exception as e:
            print(f"homeContent error: {e}")
            return {'class': [], 'list': []}
    
    def homeVideoContent(self):
        result = self.homeContent(True)
        return {'list': result.get('list', [])}
    
    def categoryContent(self, tid, pg, filter, extend):
        try:
            # 修正：使用正确的URL格式 /class/{tid}-{pg}.html（短横线）
            if pg == '1' or not pg:
                url = f'{self.host}/class/{tid}.html'
            else:
                url = f'{self.host}/class/{tid}-{pg}.html'  # 关键修复：下划线改为短横线
            
            print(f"正在请求分类页: {url}")
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            videos = []
            
            # 查找视频列表容器
            ul_pattern = r'<ul[^>]*class="[^"]*vodlist[^"]*"[^>]*>(.*?)</ul>'
            ul_match = re.search(ul_pattern, r.text, re.S)
            
            if ul_match:
                ul_content = ul_match.group(1)
                # 提取所有li项
                li_pattern = r'<li[^>]*class="[^"]*vodlist__item[^"]*"[^>]*>(.*?)</li>'
                li_items = re.findall(li_pattern, ul_content, re.S)
                
                for li in li_items:
                    # 提取视频信息
                    a_match = re.search(r'<a[^>]+href="/movie/(\d+)\.html"[^>]+title="([^"]+)"[^>]+(?:data-original|src)="([^"]+)"[^>]*>', li, re.S)
                    if not a_match:
                        continue
                    
                    vid, title, pic = a_match.groups()
                    
                    # 提取备注
                    remark_match = re.search(r'<span class="pic-text">([^<]+)</span>', li, re.S)
                    remark = remark_match.group(1).strip() if remark_match else ''
                    
                    videos.append({
                        'vod_id': vid,
                        'vod_name': html.unescape(title),
                        'vod_pic': pic,
                        'vod_remarks': remark
                    })
            
            # 去重
            seen = set()
            unique_videos = []
            for v in videos:
                if v['vod_id'] not in seen:
                    seen.add(v['vod_id'])
                    unique_videos.append(v)
            
            # 获取分页信息 - 根据真实页面结构调整
            # 分页容器: ul.text-center.clearfix
            page_pattern = r'<a[^>]+href="/class/\d+-(\d+)\.html"'  # 匹配短横线格式的分页链接
            pages = re.findall(page_pattern, r.text)
            pagecount = 1
            if pages:
                page_numbers = [int(p) for p in pages]
                if page_numbers:
                    pagecount = max(page_numbers)
            
            # 如果没找到分页链接，检查总页数显示（如"共6页"）
            if pagecount == 1:
                total_pages_match = re.search(r'共(\d+)页', r.text)
                if total_pages_match:
                    pagecount = int(total_pages_match.group(1))
            
            # 确保pagecount至少等于当前页
            current_page = int(pg)
            if pagecount < current_page:
                pagecount = current_page
            
            return {
                'page': current_page,
                'pagecount': pagecount,
                'limit': 30,
                'total': len(unique_videos),
                'list': unique_videos
            }
        except Exception as e:
            print(f"categoryContent error: {e}")
            return {'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0, 'list': []}
    
    def clean_text(self, text):
        if not text:
            return ''
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def detailContent(self, ids):
        try:
            vid = ids[0]
            url = f'{self.host}/movie/{vid}.html'
            
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', r.text)
            title = title_match.group(1).strip() if title_match else ''
            
            pic_match = re.search(r'<img[^>]+src="([^"]+)"[^>]+class="lazyload"', r.text)
            if not pic_match:
                pic_match = re.search(r'<img[^>]+data-original="([^"]+)"', r.text)
            pic = pic_match.group(1) if pic_match else ''
            
            info = {}
            info_pattern = r'<li[^>]*>([^:]+):\s*([^<]+)</li>'
            info_items = re.findall(info_pattern, r.text)
            for k, v in info_items:
                info[k.strip()] = v.strip()
            
            type_name = info.get('类型', '')
            area = info.get('地区', '')
            year = info.get('年份', '')
            remark = info.get('状态', '')
            actor = info.get('主演', '')
            director = info.get('导演', '')
            
            desc_match = re.search(r'<p[^>]*class="desc"[^>]*>([^<]+)</p>', r.text)
            if not desc_match:
                desc_match = re.search(r'简介[：:]([^<]+)', r.text)
            desc = desc_match.group(1).strip() if desc_match else ''
            
            vod_items = []
            
            # 解析播放列表
            source_pattern = r'<div[^>]+class="source-list[^"]*"[^>]*data-id="([^"]+)"[^>]*>.*?<div[^>]+class="episode-list[^"]*"[^>]*data-id="([^"]+)"[^>]*>(.*?)</div>'
            sources = re.findall(source_pattern, r.text, re.S)
            
            if sources:
                for source_id, episode_id, episode_html in sources:
                    # 提取集数链接
                    ep_pattern = r'<a[^>]+href="([^"]+)"[^>]+>([^<]+)</a>'
                    eps = re.findall(ep_pattern, episode_html)
                    
                    for ep_url, ep_name in eps:
                        vod_items.append(f"{ep_name}${ep_url}")
            else:
                # 备用解析
                ep_pattern = r'<a[^>]+href="(/play/\d+-\d+-\d+)\.html"[^>]+>([^<]+)</a>'
                eps = re.findall(ep_pattern, r.text)
                
                for ep_url, ep_name in eps:
                    full_url = self.host + ep_url
                    vod_items.append(f"{ep_name}${full_url}")
            
            vod = {
                'vod_id': vid,
                'vod_name': title,
                'vod_pic': pic,
                'type_name': type_name,
                'vod_year': year,
                'vod_area': area,
                'vod_remarks': remark,
                'vod_actor': actor,
                'vod_director': director,
                'vod_content': desc,
                'vod_play_from': '高清影院',
                'vod_play_url': '#'.join(vod_items) if vod_items else ''
            }
            
            return {'list': [vod]}
        except Exception as e:
            print(f"detailContent error: {e}")
            return {'list': []}
    
    def searchContent(self, key, quick):
        try:
            url = f'{self.host}/search?wd={key}'
            
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            videos = []
            
            li_pattern = r'<li[^>]*class="[^"]*vodlist__item[^"]*"[^>]*>(.*?)</li>'
            li_items = re.findall(li_pattern, r.text, re.S)
            
            for li in li_items:
                a_match = re.search(r'<a[^>]+href="/movie/(\d+)\.html"[^>]+title="([^"]+)"[^>]+(?:data-original|src)="([^"]+)"[^>]*>', li, re.S)
                if not a_match:
                    continue
                
                vid, title, pic = a_match.groups()
                
                remark_match = re.search(r'<span class="pic-text">([^<]+)</span>', li, re.S)
                remark = remark_match.group(1).strip() if remark_match else ''
                
                videos.append({
                    'vod_id': vid,
                    'vod_name': html.unescape(title),
                    'vod_pic': pic,
                    'vod_remarks': remark
                })
            
            return {'list': videos}
        except Exception as e:
            print(f"searchContent error: {e}")
            return {'list': []}
    
    def playerContent(self, flag, id, vipFlags):
        try:
            url = id
            if not url.startswith('http'):
                url = self.host + url
            
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            
            # 查找播放地址
            url_match = re.search(r'<iframe[^>]+src="([^"]+)"', r.text)
            if not url_match:
                url_match = re.search(r'<video[^>]+src="([^"]+)"', r.text)
            if not url_match:
                url_match = re.search(r'url\s*[:=]\s*["\']([^"\']+)["\']', r.text)
            
            if url_match:
                play_url = url_match.group(1)
                if not play_url.startswith('http'):
                    play_url = self.host + play_url
                
                return {
                    'parse': 0,
                    'playUrl': '',
                    'url': play_url,
                    'header': ''
                }
            
            return {'parse': 0, 'playUrl': '', 'url': id, 'header': ''}
        except Exception as e:
            print(f"playerContent error: {e}")
            return {'parse': 0, 'playUrl': '', 'url': id, 'header': ''}