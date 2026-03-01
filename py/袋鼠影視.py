# -*- coding: utf-8 -*-
"""
袋鼠影视爬虫 - 基于成功模板重构（移除搜索功能）
"""
import requests
import re
from urllib.parse import urljoin

class Spider:
    """
    袋鼠影视爬虫主类
    """
    
    def __init__(self):
        """初始化爬虫配置"""
        # 网站主域名
        self.host = 'https://daishuys.com'
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.host
        }
        
        # 分类映射
        self.type_map = {
            '1': '电影',
            '2': '电视剧',
            '3': '综艺',
            '4': '动漫',
            '5': '动作片',
            '6': '爱情片',
            '7': '科幻片',
            '8': '恐怖片',
            '9': '战争片',
            '10': '喜剧片',
            '11': '纪录片',
            '12': '剧情片',
            '16': '日韩剧',
            '39': '微电影',
            '41': '动画片'
        }
        
        # URL模式配置
        self.url_patterns = {
            'home': '/',
            'category': '/search.php?searchtype=5&tid={tid}&page={pg}',
            'detail': '/movie/{id}.html',
            'play': '/play/{id}-{sid}-{nid}.html'
        }
        
        # 选择器配置（正则表达式）
        self.selectors = {
            # 首页/分类页视频列表项
            'video_item': r'<li class="col-md-2 col-sm-3 col-xs-4">.*?<a class="videopic lazy" href="([^"]+)" title="([^"]+)" data-original="([^"]+)".*?<span class="note textbg">([^<]+)</span>',
            
            # 分页信息
            'page_info': r'<span class="num">(\d+)/(\d+)</span>',
            
            # 详情页标题
            'detail_title': r'<h1[^>]*>([^<]+)</h1>',
            
            # 详情页封面
            'detail_pic': r'<img[^>]+src="([^"]+)"[^>]+class="[^"]*img-responsive[^"]*"',
            
            # 详情页导演
            'detail_director': r'导演[：:]\s*<a[^>]*>([^<]+)</a>',
            
            # 详情页演员
            'detail_actor': r'主演[：:]\s*([^<]+)',
            
            # 详情页简介
            'detail_content': r'<div class="plot">([^<]+)</div>',
            
            # 播放线路块
            'source_block': r'<div class="panel clearfix">.*?<a class="option"[^>]+title="([^"]+)"[^>]*>.*?<ul class="[^"]*">(.*?)</ul>',
            
            # 剧集链接
            'episode_link': r'<li[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>',
            
            # iframe链接
            'iframe_link': r'<iframe[^>]+src="([^"]+)"'
        }
    
    def getDependence(self):
        """返回依赖列表"""
        return []
    
    def init(self, extend=""):
        """初始化方法"""
        return {}
    
    def getName(self):
        """返回爬虫名称"""
        return "袋鼠影视"
    
    def _build_url(self, pattern_key, **kwargs):
        """构建URL的辅助方法"""
        pattern = self.url_patterns.get(pattern_key, '')
        url = pattern.format(**kwargs)
        if not url.startswith('http'):
            url = self.host + url
        return url
    
    def _extract_videos(self, html, selector_key, max_count=0):
        """
        从HTML中提取视频列表的辅助方法
        """
        videos = []
        pattern = self.selectors.get(selector_key, '')
        if not pattern:
            return videos
        
        items = re.findall(pattern, html, re.DOTALL)
        
        for item in items:
            if selector_key == 'video_item':
                # 格式: (href, title, pic, remark)
                href, title, pic, remark = item
            else:
                continue
            
            full_url = urljoin(self.host, href)
            videos.append({
                'vod_id': full_url,
                'vod_name': title.strip(),
                'vod_pic': pic.strip('\'"'),
                'vod_remarks': remark.strip()
            })
            
            if max_count and len(videos) >= max_count:
                break
        
        return videos
    
    def homeContent(self, filter):
        """获取首页分类和推荐"""
        result = {}
        
        # 构建分类列表
        classes = []
        for tid, name in self.type_map.items():
            classes.append({
                'type_id': tid,
                'type_name': name
            })
        result['class'] = classes
        
        try:
            url = self._build_url('home')
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            html = r.text
            
            videos = self._extract_videos(html, 'video_item', 30)
            result['list'] = videos
            
        except Exception as e:
            print(f"homeContent error: {e}")
            result['list'] = []
        
        return result
    
    def homeVideoContent(self):
        return self.homeContent(True)
    
    def categoryContent(self, tid, pg, filter, extend):
        """获取分类页内容"""
        result = {}
        page = int(pg) if pg else 1
        
        try:
            url = self._build_url('category', tid=tid, pg=page)
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            html = r.text
            
            videos = self._extract_videos(html, 'video_item')
            
            # 解析总页数
            page_info = re.search(self.selectors['page_info'], html)
            max_page = 1
            if page_info:
                max_page = int(page_info.group(2))
            
            result['page'] = page
            result['pagecount'] = max_page
            result['limit'] = len(videos)
            result['total'] = max_page * 30
            result['list'] = videos
            
        except Exception as e:
            print(f"categoryContent error: {e}")
            result['list'] = []
            result['page'] = page
            result['pagecount'] = 1
            result['limit'] = 0
            result['total'] = 0
        
        return result
    
    def detailContent(self, ids):
        """获取详情页内容"""
        result = {}
        
        try:
            if isinstance(ids, list) and len(ids) > 0:
                vod_id = ids[0]
            else:
                vod_id = ids
            
            r = requests.get(vod_id, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            html = r.text
            
            vod = {
                'vod_id': vod_id,
                'vod_name': '',
                'vod_pic': '',
                'vod_actor': '',
                'vod_director': '',
                'vod_content': '',
                'vod_play_from': '',
                'vod_play_url': ''
            }
            
            # 提取标题
            title_match = re.search(self.selectors['detail_title'], html)
            if title_match:
                vod['vod_name'] = title_match.group(1).strip()
            
            # 提取封面
            pic_match = re.search(self.selectors['detail_pic'], html)
            if pic_match:
                vod['vod_pic'] = pic_match.group(1)
            
            # 提取导演
            director_match = re.search(self.selectors['detail_director'], html)
            if director_match:
                vod['vod_director'] = director_match.group(1).strip()
            
            # 提取演员
            actor_match = re.search(self.selectors['detail_actor'], html)
            if actor_match:
                actor_text = actor_match.group(1)
                # 提取所有a标签内的演员名
                actor_names = re.findall(r'<a[^>]*>([^<]+)</a>', actor_text)
                if actor_names:
                    vod['vod_actor'] = ','.join([name.strip() for name in actor_names])
                else:
                    vod['vod_actor'] = actor_text.strip()
            
            # 提取简介
            content_match = re.search(self.selectors['detail_content'], html)
            if content_match:
                vod['vod_content'] = content_match.group(1).strip()
            
            # 提取播放列表
            playlist_sources = []
            playlist_urls = []
            
            # 查找所有播放线路块
            source_blocks = re.findall(self.selectors['source_block'], html, re.DOTALL)
            
            for source_name, episode_html in source_blocks:
                source_name = source_name.strip()
                
                # 提取该线路下的所有剧集
                episodes = re.findall(self.selectors['episode_link'], episode_html, re.DOTALL)
                
                if episodes:
                    source_urls = []
                    for href, name in episodes:
                        full_url = urljoin(vod_id, href)
                        source_urls.append(f"{name.strip()}${full_url}")
                    
                    playlist_sources.append(source_name)
                    playlist_urls.append('#'.join(source_urls))
            
            if playlist_sources and playlist_urls:
                vod['vod_play_from'] = '$$$'.join(playlist_sources)
                vod['vod_play_url'] = '$$$'.join(playlist_urls)
            
            result['list'] = [vod]
            
        except Exception as e:
            print(f"detailContent error: {e}")
            result['list'] = []
        
        return result
    
    def playerContent(self, flag, id, vipFlags):
        """获取播放地址"""
        result = {}
        
        try:
            r = requests.get(id, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            html = r.text
            
            # 查找iframe
            iframe_match = re.search(self.selectors['iframe_link'], html)
            if iframe_match:
                result['url'] = iframe_match.group(1)
                result['parse'] = 0
                return result
            
            # 如果没有找到，返回原URL
            result['url'] = id
            result['parse'] = 1
            
        except Exception as e:
            print(f"playerContent error: {e}")
            result['url'] = id
            result['parse'] = 1
        
        return result

# 必须的入口函数
def getDependence():
    return Spider().getDependence()

def init(extend):
    return Spider().init(extend)

def getName():
    return Spider().getName()

def homeContent(filter):
    return Spider().homeContent(filter)

def homeVideoContent():
    return Spider().homeVideoContent()

def categoryContent(tid, pg, filter, extend):
    return Spider().categoryContent(tid, pg, filter, extend)

def detailContent(ids):
    return Spider().detailContent(ids)

def playerContent(flag, id, vipFlags):
    return Spider().playerContent(flag, id, vipFlags)