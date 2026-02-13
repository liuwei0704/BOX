# -*- coding: utf-8 -*-
# @Author  : [Lemon]
# @Time    : [2006/02/14]

import sys
import requests
import re
import json
import urllib.parse
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    def getName(self):
        """返回爬蟲名稱"""
        return "开心影院"

    def init(self, extend):
        """初始化爬蟲配置"""
        self.home_url = 'https://www.kxyytv.com'
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        self.error_url = "https://akuzika.com/v/500.m3u8"

    def getDependence(self):
        """返回依賴庫列表"""
        return []

    def isVideoFormat(self, url):
        """判斷是否為視頻格式"""
        return url.endswith(('.m3u8', '.mp4', '.flv', '.mkv'))

    def manualVideoCheck(self):
        """手動視頻檢查"""
        pass

    def homeContent(self, filter):
        """
        獲取首頁分類和篩選條件
        """
        class_list = [
            {'type_id': '1', 'type_name': '电影'},
            {'type_id': '2', 'type_name': '电视剧'},
            {'type_id': '3', 'type_name': '综艺'},
            {'type_id': '4', 'type_name': '动漫'},
            {'type_id': '26', 'type_name': '短剧'},
            {'type_id': '24', 'type_name': '纪录片'}
        ]
        
        filters = {
            '1': self._get_movie_filters(),
            '2': self._get_tv_filters(),
            '3': self._get_variety_filters(),
            '4': self._get_anime_filters(),
            '26': self._get_short_drama_filters(),
            '24': self._get_documentary_filters()
        }
            
        return {
            'class': class_list,
            'filters': filters
        }
    
    def _get_movie_filters(self):
        """电影分类的筛选选项"""
        return [
            {
                'key': 'class',
                'name': '类型',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '科幻', 'v': '科幻'},
                    {'n': '剧情', 'v': '剧情'},
                    {'n': '惊悚', 'v': '惊悚'},
                    {'n': '爱情', 'v': '爱情'},
                    {'n': '古装', 'v': '古装'},
                    {'n': '动作', 'v': '动作'},
                    {'n': '伦理', 'v': '伦理'},
                    {'n': '悬疑', 'v': '悬疑'},
                    {'n': '犯罪', 'v': '犯罪'},
                    {'n': '谍战', 'v': '谍战'},
                    {'n': '历史', 'v': '历史'},
                    {'n': '喜剧', 'v': '喜剧'},
                    {'n': '奇幻', 'v': '奇幻'},
                    {'n': '家庭', 'v': '家庭'},
                    {'n': '青春', 'v': '青春'},
                    {'n': '冒险', 'v': '冒险'},
                    {'n': '纪录', 'v': '纪录'},
                    {'n': '动画', 'v': '动画'},
                    {'n': '人物', 'v': '人物'},
                    {'n': '文化', 'v': '文化'},
                    {'n': '其他', 'v': '其他'}
                ]
            },
            {
                'key': 'area',
                'name': '地区',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '中国大陆', 'v': '中国大陆'},
                    {'n': '中国香港', 'v': '中国香港'},
                    {'n': '中国台湾', 'v': '中国台湾'},
                    {'n': '美国', 'v': '美国'},
                    {'n': '日本', 'v': '日本'},
                    {'n': '韩国', 'v': '韩国'},
                    {'n': '泰国', 'v': '泰国'},
                    {'n': '英国', 'v': '英国'},
                    {'n': '法国', 'v': '法国'},
                    {'n': '德国', 'v': '德国'},
                    {'n': '意大利', 'v': '意大利'}
                ]
            },
            {
                'key': 'year',
                'name': '年份',
                'value': self._get_year_options()
            },
            {
                'key': 'by',
                'name': '排序',
                'value': self._get_sort_options()
            }
        ]
    
    def _get_tv_filters(self):
        """电视剧分类的筛选选项"""
        return [
            {
                'key': 'class',
                'name': '类型',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '爱情', 'v': '爱情'},
                    {'n': '古装', 'v': '古装'},
                    {'n': '悬疑', 'v': '悬疑'},
                    {'n': '都市', 'v': '都市'},
                    {'n': '喜剧', 'v': '喜剧'},
                    {'n': '战争', 'v': '战争'},
                    {'n': '剧情', 'v': '剧情'},
                    {'n': '青春', 'v': '青春'},
                    {'n': '历史', 'v': '历史'},
                    {'n': '网剧', 'v': '网剧'},
                    {'n': '奇幻', 'v': '奇幻'},
                    {'n': '冒险', 'v': '冒险'},
                    {'n': '励志', 'v': '励志'},
                    {'n': '犯罪', 'v': '犯罪'},
                    {'n': '商战', 'v': '商战'},
                    {'n': '恐怖', 'v': '恐怖'},
                    {'n': '穿越', 'v': '穿越'},
                    {'n': '农村', 'v': '农村'},
                    {'n': '人物', 'v': '人物'},
                    {'n': '商业', 'v': '商业'},
                    {'n': '生活', 'v': '生活'},
                    {'n': '其他', 'v': '其他'}
                ]
            },
            {
                'key': 'area',
                'name': '地区',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '中国大陆', 'v': '中国大陆'},
                    {'n': '中国香港', 'v': '中国香港'},
                    {'n': '中国台湾', 'v': '中国台湾'},
                    {'n': '美国', 'v': '美国'},
                    {'n': '日本', 'v': '日本'},
                    {'n': '韩国', 'v': '韩国'},
                    {'n': '泰国', 'v': '泰国'},
                    {'n': '英国', 'v': '英国'},
                    {'n': '法国', 'v': '法国'},
                    {'n': '德国', 'v': '德国'},
                    {'n': '意大利', 'v': '意大利'}
                ]
            },
            {
                'key': 'year',
                'name': '年份',
                'value': self._get_year_options()
            },
            {
                'key': 'by',
                'name': '排序',
                'value': self._get_sort_options()
            }
        ]
    
    def _get_variety_filters(self):
        """综艺分类的筛选选项"""
        return [
            {
                'key': 'class',
                'name': '类型',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '真人秀', 'v': '真人秀'},
                    {'n': '脱口秀', 'v': '脱口秀'},
                    {'n': '喜剧', 'v': '喜剧'},
                    {'n': '音乐', 'v': '音乐'},
                    {'n': '爱情', 'v': '爱情'},
                    {'n': '家庭', 'v': '家庭'},
                    {'n': '歌舞', 'v': '歌舞'}
                ]
            },
            {
                'key': 'area',
                'name': '地区',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '中国大陆', 'v': '中国大陆'},
                    {'n': '港台', 'v': '港台'},
                    {'n': '韩国', 'v': '韩国'},
                    {'n': '欧美', 'v': '欧美'},
                    {'n': '其他', 'v': '其他'}
                ]
            },
            {
                'key': 'year',
                'name': '年份',
                'value': self._get_year_options()
            },
            {
                'key': 'by',
                'name': '排序',
                'value': self._get_sort_options()
            }
        ]
    
    def _get_anime_filters(self):
        """动漫分类的筛选选项"""
        return [
            {
                'key': 'class',
                'name': '类型',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '少年', 'v': '少年'},
                    {'n': '热血', 'v': '热血'},
                    {'n': '科幻', 'v': '科幻'},
                    {'n': '冒险', 'v': '冒险'},
                    {'n': '动画', 'v': '动画'},
                    {'n': '爱情', 'v': '爱情'},
                    {'n': '奇幻', 'v': '奇幻'},
                    {'n': '武侠', 'v': '武侠'},
                    {'n': '悬疑', 'v': '悬疑'},
                    {'n': '惊悚', 'v': '惊悚'},
                    {'n': '剧情', 'v': '剧情'},
                    {'n': '音乐', 'v': '音乐'},
                    {'n': '恐怖', 'v': '恐怖'},
                    {'n': '喜剧', 'v': '喜剧'},
                    {'n': '儿童', 'v': '儿童'}
                ]
            },
            {
                'key': 'area',
                'name': '地区',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '中国大陆', 'v': '中国大陆'},
                    {'n': '日本', 'v': '日本'}
                ]
            },
            {
                'key': 'year',
                'name': '年份',
                'value': self._get_year_options()
            },
            {
                'key': 'by',
                'name': '排序',
                'value': self._get_sort_options()
            }
        ]
    
    def _get_short_drama_filters(self):
        """短剧分类的筛选选项"""
        return [
            {
                'key': 'class',
                'name': '类型',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '短剧', 'v': '短剧'}
                ]
            },
            {
                'key': 'area',
                'name': '地区',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '中国大陆', 'v': '中国大陆'}
                ]
            },
            {
                'key': 'year',
                'name': '年份',
                'value': self._get_year_options()
            },
            {
                'key': 'by',
                'name': '排序',
                'value': self._get_sort_options()
            }
        ]
    
    def _get_documentary_filters(self):
        """纪录片分类的筛选选项"""
        return [
            {
                'key': 'class',
                'name': '类型',
                'value': [
                    {'n': '不限', 'v': ''}
                ]
            },
            {
                'key': 'area',
                'name': '地区',
                'value': [
                    {'n': '不限', 'v': ''}
                ]
            },
            {
                'key': 'year',
                'name': '年份',
                'value': [
                    {'n': '不限', 'v': ''},
                    {'n': '2020', 'v': '2020'},
                    {'n': '2019', 'v': '2019'},
                    {'n': '2018', 'v': '2018'},
                    {'n': '2017', 'v': '2017'},
                    {'n': '2016', 'v': '2016'},
                    {'n': '2015', 'v': '2015'},
                    {'n': '2014', 'v': '2014'},
                    {'n': '2006', 'v': '2006'},
                    {'n': '2005', 'v': '2005'},
                    {'n': '2004', 'v': '2004'},
                    {'n': '2003', 'v': '2003'},
                    {'n': '2002', 'v': '2002'},
                    {'n': '2001', 'v': '2001'},
                    {'n': '2000', 'v': '2000'}
                ]
            },
            {
                'key': 'by',
                'name': '排序',
                'value': self._get_sort_options()
            }
        ]
    
    def _get_year_options(self):
        """年份选项"""
        years = [{'n': '不限', 'v': ''}]
        for year in range(2026, 1999, -1):
            years.append({'n': str(year), 'v': str(year)})
        years.extend([
            {'n': '90年代', 'v': '90年代'},
            {'n': '80年代', 'v': '80年代'},
            {'n': '70年代', 'v': '70年代'},
            {'n': '其他', 'v': '其他'}
        ])
        return years
    
    def _get_sort_options(self):
        """排序选项"""
        return [
            {'n': '更新时间', 'v': 'time'},
            {'n': '近期热门', 'v': 'hits_week'},
            {'n': '豆瓣评分', 'v': 'douban_score'}
        ]

    def homeVideoContent(self):
        """
        獲取首頁推薦視頻列表
        """
        video_list = []
        h = {"User-Agent": self.ua}
        
        try:
            res = requests.get(self.home_url, headers=h, timeout=10)
            html = res.text
            
            pattern = r'<div class="col-4 rows-md-7">.*?<a title="(.*?)" href="(/voddetail/\d+\.html?)".*?<img.*?data-src="(.*?)".*?<span class="badge.*?">(.*?)</span>'
            items = re.findall(pattern, html, re.DOTALL)
            
            seen = set()
            for item in items:
                vod_name = item[0]
                vod_id = item[1].replace('/voddetail/', '')
                vod_pic = item[2]
                vod_remarks = item[3].strip()
                
                if vod_id not in seen:
                    seen.add(vod_id)
                    video_list.append({
                        'vod_id': vod_id,
                        'vod_name': vod_name,
                        'vod_pic': vod_pic,
                        'vod_remarks': vod_remarks
                    })
                    
        except Exception as e:
            print(f"首页解析错误: {e}")
            
        return {'list': video_list, 'parse': 0, 'jx': 0}

    def categoryContent(self, tid, page, filter, extend):
        """
        獲取分類內容
        """
        video_list = []
        h = {"User-Agent": self.ua}
        
        try:
            _class = extend.get('class', '')
            _area = extend.get('area', '')
            _year = extend.get('year', '')
            _by = extend.get('by', 'time')
            
            if _area:
                _area = urllib.parse.quote(_area)
            if _class:
                _class = urllib.parse.quote(_class)
            
            url = f"{self.home_url}/vodshow/{tid}-{_area}-{_by}-{_class}-----{page}---{_year}.html"
            
            print(f"请求分类URL: {url}")
            
            res = requests.get(url, headers=h, timeout=10)
            html = res.text
            
            video_list = self._parse_video_list(html)
            
            page_count = self._get_page_count(html, tid)
            
            print(f"找到 {len(video_list)} 个视频")
                
        except Exception as e:
            print(f"分类页解析错误: {e}")
            return {'list': [], 'msg': str(e)}
            
        return {
            'list': video_list, 
            'parse': 0, 
            'jx': 0, 
            'page': int(page), 
            'pagecount': page_count,
            'limit': len(video_list),
            'total': len(video_list)
        }
    
    def _parse_video_list(self, html):
        """解析视频列表"""
        video_list = []
        
        pattern1 = r'<div class="col-lg-8 col-4">.*?<a target="_blank" href="/voddetail/(.*?)".*?<img src="(.*?)".*?<span class="badge.*?">(.*?)</span>.*?<h3 class="mb-0 card-title text-truncate">(.*?)</h3>'
        items = re.findall(pattern1, html, re.DOTALL)
        for item in items:
            video_list.append({
                'vod_id': item[0],
                'vod_name': item[3].strip(),
                'vod_pic': item[1],
                'vod_remarks': item[2].strip()
            })
        
        if not video_list:
            pattern2 = r'<div class="col-4 rows-md-7">.*?<a title="(.*?)" href="/voddetail/(.*?)".*?<img.*?src="(.*?)".*?<span class="badge.*?">(.*?)</span>'
            items = re.findall(pattern2, html, re.DOTALL)
            for item in items:
                video_list.append({
                    'vod_id': item[1],
                    'vod_name': item[0].strip(),
                    'vod_pic': item[2],
                    'vod_remarks': item[3].strip()
                })
        
        return video_list
    
    def _get_page_count(self, html, tid):
        """获取总页数"""
        page_count = 9999
        page_pattern = r'/vodshow/' + tid + r'--------(\d+)---\.html'
        pages = re.findall(page_pattern, html)
        if pages:
            max_page = max([int(p) for p in pages if p.isdigit()])
            page_count = max_page
        return page_count

    def detailContent(self, did):
        """
        獲取視頻詳情
        """
        ids = did[0]
        if not ids.endswith('.html'):
            ids = ids + '.html'
            
        video_list = []
        h = {"User-Agent": self.ua}
        
        try:
            url = f"{self.home_url}/voddetail/{ids}"
            print(f"请求详情URL: {url}")
            
            res = requests.get(url, headers=h, timeout=10)
            html = res.text
            
            # 提取视频名称
            name_match = re.search(r'<h1[^>]*class="d-none d-md-block"[^>]*>(.*?)</h1>', html)
            if not name_match:
                name_match = re.search(r'<h2[^>]*class="d-sm-block d-md-none"[^>]*>(.*?)</h2>', html)
            
            vod_name_full = ''
            vod_year = ''
            if name_match:
                vod_name_full = name_match.group(1).strip()
                vod_name_full = re.sub(r'&nbsp;', ' ', vod_name_full)
                vod_name_full = re.sub(r'&[a-z]+;', '', vod_name_full)
                
                year_match = re.search(r'\((\d{4})\)', vod_name_full)
                if year_match:
                    vod_name = vod_name_full.replace(f'({year_match.group(1)})', '').strip()
                    vod_year = year_match.group(1)
                else:
                    vod_name = vod_name_full
            else:
                vod_name = ids.replace('.html', '')
            
            # 提取图片
            pic_match = re.search(r'<img[^>]*src="(.*?)"[^>]*onerror="[^"]*"[^>]*>', html)
            if not pic_match:
                pic_match = re.search(r'<img[^>]*src="(.*?)"[^>]*class="[^"]*cover[^"]*"[^>]*>', html)
            vod_pic = pic_match.group(1) if pic_match else ''
            
            # 提取导演
            director_match = re.search(r'导演[：:]\s*</span>\s*<a[^>]*>(.*?)</a>', html)
            if director_match:
                vod_director = director_match.group(1).strip()
            else:
                director_match = re.search(r'导演[：:]\s*([^<]+?)(?:</li>|<br)', html)
                vod_director = director_match.group(1).strip() if director_match else '未知'
            
            # 提取主演
            actor_match = re.search(r'主演[：:]\s*</span>\s*(.*?)</p>', html, re.DOTALL)
            if actor_match:
                actor_html = actor_match.group(1)
                actor_names = re.findall(r'<a[^>]*>([^<]+)</a>', actor_html)
                if actor_names:
                    vod_actor = ' '.join(actor_names)
                else:
                    vod_actor = actor_html.strip()
            else:
                vod_actor = '未知'
            
            # 提取地区
            area_match = re.search(r'制片国家/地区[：:]\s*\[?(.*?)\]?\s*(?:</li>|<br)', html)
            if not area_match:
                area_match = re.search(r'地区[：:]\s*</span>\s*(.*?)\s*</li>', html)
            vod_area = area_match.group(1).strip() if area_match else ''
            
            # 提取类型
            type_match = re.search(r'类型[：:]\s*</span>\s*<a[^>]*>([^<]+?)</a>', html)
            if not type_match:
                type_match = re.search(r'类型[：:]\s*([^<]+?)(?:</li>|<br)', html)
            vod_type = type_match.group(1).strip() if type_match else ''
            
            # 提取备注
            remarks_match = re.search(r'摘要[：:]\s*<span[^>]*class="[^"]*text-orange[^"]*"[^>]*>([^<]+?)</span>', html)
            if not remarks_match:
                remarks_match = re.search(r'<span[^>]*class="badge[^"]*bg-green-lt[^"]*"[^>]*>([^<]+?)</span>', html)
            vod_remarks = remarks_match.group(1).strip() if remarks_match else ''
            
            # 提取简介
            content_match = re.search(r'<div[^>]*class="card-body"[^>]*>(.*?)</div>', html, re.DOTALL)
            if content_match:
                vod_content = content_match.group(1).strip()
                vod_content = re.sub(r'<.*?>', '', vod_content)
                vod_content = re.sub(r'\s+', ' ', vod_content)
            else:
                vod_content = ''
            
            # 解析播放源和剧集
            play_sources = []
            play_urls_dict = {}
            
            # 从nav-tabs中提取播放源
            source_pattern = r'<li[^>]*class="nav-item"[^>]*>.*?<a[^>]*href="#tabs-home-(\d+)"[^>]*>.*?<svg.*?</svg>\s*([^<&]+?)\s*&nbsp;.*?<span[^>]*class="badge"[^>]*>(\d+)</span>'
            sources = re.findall(source_pattern, html, re.DOTALL)
            
            if not sources:
                source_pattern2 = r'<li[^>]*class="nav-item"[^>]*>.*?<a[^>]*href="#tabs-home-(\d+)"[^>]*>([^<]+?)<'
                sources = re.findall(source_pattern2, html, re.DOTALL)
            
            if sources:
                for source in sources:
                    if len(source) >= 2:
                        source_id = source[0]
                        source_name = source[1].strip()
                        source_name = re.sub(r'&nbsp;|\s+', ' ', source_name).strip()
                        play_sources.append(source_name)
                        
                        tab_pattern = f'<div[^>]*class="tab-pane[^"]*"[^>]*id="tabs-home-{source_id}"[^>]*>(.*?)</div>'
                        tab_match = re.search(tab_pattern, html, re.DOTALL)
                        if tab_match:
                            tab_html = tab_match.group(1)
                            ep_pattern = r'<a[^>]*class="btn[^"]*btn-square[^"]*"[^>]*href="(/vodplay/([^"]+))"[^>]*>(\d+)</a>'
                            eps = re.findall(ep_pattern, tab_html, re.DOTALL)
                            
                            source_urls = []
                            for ep in eps:
                                ep_url = ep[0]
                                ep_num = ep[2]
                                if ep_num.isdigit():
                                    ep_num = f'{int(ep_num):02d}'
                                source_urls.append(f"第{ep_num}集${ep_url}")
                            
                            if source_urls:
                                play_urls_dict[source_name] = source_urls
            else:
                ep_pattern = r'<a[^>]*class="btn[^"]*btn-square[^"]*"[^>]*href="(/vodplay/([^"]+))"[^>]*>(\d+)</a>'
                eps = re.findall(ep_pattern, html, re.DOTALL)
                
                if eps:
                    play_sources.append('云播')
                    source_urls = []
                    for ep in eps:
                        ep_url = ep[0]
                        ep_num = ep[2]
                        if ep_num.isdigit():
                            ep_num = f'{int(ep_num):02d}'
                        source_urls.append(f"第{ep_num}集${ep_url}")
                    play_urls_dict['云播'] = source_urls
            
            # 构建vod_play_from和vod_play_url
            if play_sources and play_urls_dict:
                vod_play_from = '$$$'.join(play_sources)
                
                all_play_urls = []
                for source in play_sources:
                    if source in play_urls_dict:
                        all_play_urls.append('#'.join(play_urls_dict[source]))
                vod_play_url = '$$$'.join(all_play_urls)
            else:
                vod_play_from = '云播'
                vod_play_url = '暂无$'
            
            video_info = {
                'vod_id': ids,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_content': vod_content,
                'vod_play_from': vod_play_from,
                'vod_play_url': vod_play_url,
                'vod_actor': vod_actor,
                'vod_director': vod_director,
                'vod_area': vod_area,
                'vod_year': vod_year,
                'vod_remarks': vod_remarks,
                'vod_type': vod_type
            }
            
            video_list.append(video_info)
            print(f"详情页解析成功: {vod_name}")
            print(f"播放源: {play_sources}")
            print(f"剧集数: {sum(len(urls) for urls in play_urls_dict.values()) if play_urls_dict else 0}")
            
        except Exception as e:
            print(f"详情页解析错误: {e}")
            return {'list': [], 'msg': str(e)}
            
        return {"list": video_list, 'parse': 0, 'jx': 0}

    def playerContent(self, flag, pid, vipFlags):
        """
        獲取播放地址
        """
        if not pid.startswith('/vodplay/'):
            if not pid.endswith('.html'):
                if '-' in pid:
                    pid = f"{pid}.html"
                else:
                    pid = f"{pid}-1-1.html"
            pid = f"/vodplay/{pid}"
        
        play_url = f"{self.home_url}{pid}"
        print(f"请求播放页: {play_url}")
        
        h = {"User-Agent": self.ua}
        
        try:
            res = requests.get(play_url, headers=h, timeout=10)
            html = res.text
            
            player_pattern = r'var player_data\s*=\s*({.*?});'
            player_match = re.search(player_pattern, html, re.DOTALL)
            
            if player_match:
                player_json_str = player_match.group(1)
                try:
                    player_data = json.loads(player_json_str)
                    real_url = player_data.get('url', '')
                    if real_url:
                        real_url = real_url.replace('\\/', '/')
                        print(f"找到真实播放地址: {real_url}")
                        header = {
                            "User-Agent": self.ua,
                            "Referer": self.home_url
                        }
                        return {"url": real_url, "header": header, "parse": 0, "jx": 0}
                except:
                    pass
            
            url_pattern = r'"url":"([^"]+)"'
            url_match = re.search(url_pattern, html)
            if url_match:
                real_url = url_match.group(1).replace('\\/', '/')
                print(f"找到真实播放地址: {real_url}")
                header = {
                    "User-Agent": self.ua,
                    "Referer": self.home_url
                }
                return {"url": real_url, "header": header, "parse": 0, "jx": 0}
            
            iframe_pattern = r'<iframe[^>]*src="([^"]+)"[^>]*>'
            iframe_match = re.search(iframe_pattern, html)
            if iframe_match:
                real_url = iframe_match.group(1)
                if not real_url.startswith('http'):
                    if real_url.startswith('/'):
                        real_url = self.home_url + real_url
                    else:
                        real_url = self.home_url + '/' + real_url
                print(f"找到iframe地址: {real_url}")
                header = {
                    "User-Agent": self.ua,
                    "Referer": self.home_url
                }
                return {"url": real_url, "header": header, "parse": 1, "jx": 0}
            
            print("未找到真实播放地址")
            
        except Exception as e:
            print(f"播放页解析错误: {e}")
        
        header = {
            "User-Agent": self.ua,
            "Referer": self.home_url
        }
        return {"url": play_url, "header": header, "parse": 1, "jx": 0}

    def searchContent(self, key, quick, page='1'):
        """
        搜索內容 - 由于安全验证，返回空列表
        """
        print(f"搜索功能已禁用（安全验证）")
        return {'list': [], 'parse': 0, 'jx': 0}

    def localProxy(self, params):
        """本地代理"""
        pass

    def destroy(self):
        """銷毀時的清理操作"""
        return '正在Destroy'