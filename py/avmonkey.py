# -*- coding: utf-8 -*-
# AV猴影视 TVBox 爬虫
# 最终修复版 - 所有方法都支持额外参数

import re
import json
import urllib.parse
import urllib.request
import ssl
import sys

# 忽略SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context

class Spider:
    """AV猴TVBox爬虫 - 最终修复版"""
    
    def __init__(self):
        self.siteUrl = "https://avmonkey.tv"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.siteUrl
        }
        self.cateManual = {
            '国产自拍': '国产自拍-1',
            '日韩精品': '日韩精品-2',
            'onlyfans精选': 'onlyfans精选-3',
            '卡通动漫': '卡通动漫-4',
            '欧美视频': '欧美视频-5',
            '优质传媒': '优质传媒-6',
            '精品探花': '精品探花-7',
        }
        
    def getDependence(self, *args, **kwargs):
        """返回依赖信息 - TVBox必需方法"""
        return []
        
    def init(self, *args, **kwargs):
        """初始化 - TVBox必需方法，接收任意参数"""
        pass
        
    def homeContent(self, *args, **kwargs):
        """获取首页内容 - 接收任意参数"""
        result = {
            'class': [],
            'list': []
        }
        
        try:
            # 添加分类
            for name, tid in self.cateManual.items():
                result['class'].append({
                    'type_id': tid,
                    'type_name': name
                })
            
            # 获取最新视频
            html = self.fetch(self.siteUrl)
            if html:
                videos = self._parse_video_list(html)
                result['list'] = videos[:20]
        except Exception as e:
            print(f"homeContent error: {e}")
            
        return result
        
    def homeVideoContent(self, *args, **kwargs):
        """获取首页视频 - TVBox必需方法"""
        try:
            html = self.fetch(self.siteUrl)
            if html:
                videos = self._parse_video_list(html)
                return {'list': videos[:20]}
        except:
            pass
        return {'list': []}
        
    def categoryContent(self, tid, pg=1, filter=False, ext=None, *args, **kwargs):
        """获取分类内容 - 修复分页"""
        result = {
            'list': [],
            'page': int(pg),
            'pagecount': 1,
            'limit': 20,
            'total': 0
        }
        
        try:
            page = int(pg)
            
            # 构建分类URL
            if tid in self.cateManual.values():
                # 格式如: 国产自拍-1
                url = f"{self.siteUrl}/categories/{urllib.parse.quote(tid)}"
                if page > 1:
                    url = f"{url}/page/{page}"
            else:
                # 处理传入的可能是分类名
                url = f"{self.siteUrl}/categories/{urllib.parse.quote(tid)}"
                if page > 1:
                    url = f"{url}/page/{page}"
            
            print(f"分类URL: {url}")
            html = self.fetch(url)
            
            if html:
                videos = self._parse_video_list(html)
                result['list'] = videos
                
                # 从HTML中提取总页数
                # 查找分页链接
                page_pattern = r'<a[^>]*href="[^"]*/page/(\d+)"[^>]*>(\d+)</a>'
                page_matches = re.findall(page_pattern, html)
                
                if page_matches:
                    pages = [int(p[1]) for p in page_matches]
                    if pages:
                        max_page = max(pages)
                        result['pagecount'] = max_page
                        print(f"找到页码: {pages}, 最大页: {max_page}")
                else:
                    # 尝试查找下一页链接
                    next_pattern = r'<a[^>]*href="[^"]*/page/(\d+)"[^>]*>下一页</a>'
                    next_match = re.search(next_pattern, html)
                    if next_match:
                        next_page = int(next_match.group(1))
                        result['pagecount'] = next_page
                        print(f"下一页到第{next_page}页")
                    else:
                        # 如果没有分页链接，但有视频，且视频数量满20，可能还有更多页
                        if videos and len(videos) >= 20:
                            result['pagecount'] = page + 1
                            print(f"视频数{len(videos)}，可能还有下一页")
                
                print(f"当前页: {page}, 总页数: {result['pagecount']}, 视频数: {len(videos)}")
                
        except Exception as e:
            print(f"categoryContent error: {e}")
            
        return result
        
    def detailContent(self, ids, *args, **kwargs):
        """获取详情内容"""
        vod_list = []
        
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            
            # 构建详情页URL
            if vid.startswith('http'):
                url = vid
            else:
                url = f"{self.siteUrl}/video/{vid}"
            
            print(f"详情URL: {url}")
            html = self.fetch(url)
            
            if html:
                vod = self._parse_detail(html, vid)
                if vod:
                    vod_list.append(vod)
                    
        except Exception as e:
            print(f"detailContent error: {e}")
            
        return {'list': vod_list}
        
    def searchContent(self, key, quick=False, *args, **kwargs):
        """搜索内容"""
        vod_list = []
        
        try:
            encoded_key = urllib.parse.quote(key)
            url = f"{self.siteUrl}/Search/{encoded_key}"
            print(f"搜索URL: {url}")
            
            html = self.fetch(url)
            if html:
                videos = self._parse_video_list(html)
                vod_list = videos[:20]
                print(f"搜索结果数: {len(vod_list)}")
                
        except Exception as e:
            print(f"searchContent error: {e}")
            
        return {'list': vod_list}
        
    def searchContentPage(self, key, quick=False, pg=1, *args, **kwargs):
        """分页搜索"""
        return self.searchContent(key, quick)
        
    def playerContent(self, flag, id, vipFlags=None, *args, **kwargs):
        """获取播放地址"""
        result = {}
        
        try:
            print(f"获取播放地址: flag={flag}, id={id}")
            
            if id.startswith('http'):
                play_url = id
            else:
                # 尝试获取真实播放地址
                url = f"{self.siteUrl}/video/{id}"
                html = self.fetch(url)
                play_url = self._extract_play_url(html) if html else url
                
            result['url'] = play_url
            result['parse'] = 0
            result['header'] = json.dumps({
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.siteUrl
            })
            
            print(f"播放地址: {play_url[:100] if play_url else 'None'}")
            
        except Exception as e:
            print(f"playerContent error: {e}")
            result['url'] = id
            
        return result
        
    def _parse_video_list(self, html):
        """解析视频列表"""
        videos = []
        
        # 匹配视频卡片
        patterns = [
            # 模式1: a标签包含p标签
            r'<a[^>]*href="([^"]*/(?:video|archives)/([^"/?]+))"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>.*?<p[^>]*>([^<]*)</p>',
            # 模式2: a标签包含div标签
            r'<a[^>]*href="([^"]*/(?:video|archives)/([^"/?]+))"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>.*?<div[^>]*>([^<]*)</div>',
            # 模式3: 更宽松的匹配
            r'<a[^>]*href="([^"]*/(?:video|archives)/([^"/?]+))"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>.*?<[^>]*>([^<]*)</[^>]*>'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            if matches:
                print(f"使用模式匹配到 {len(matches)} 个视频卡片")
                for match in matches:
                    try:
                        url = match[0]
                        vid = match[1]
                        img = match[2]
                        title = match[3].strip() if len(match) > 3 else ''
                        
                        # 清理标题
                        title = re.sub(r'<[^>]+>', '', title)
                        title = re.sub(r'\s+', ' ', title).strip()
                        
                        if not title or len(title) < 2:
                            continue
                            
                        # 处理相对路径
                        if not url.startswith('http'):
                            url = urllib.parse.urljoin(self.siteUrl, url)
                        if not img.startswith('http'):
                            img = urllib.parse.urljoin(self.siteUrl, img)
                        
                        # 提取时长
                        remarks = ''
                        dur_pattern = r'(\d+:\d+)'
                        dur_match = re.search(dur_pattern, html[html.find(title)-500:html.find(title)+500])
                        if dur_match:
                            remarks = dur_match.group(1)
                        
                        video = {
                            'vod_id': vid,
                            'vod_name': title[:100],
                            'vod_pic': img,
                            'vod_remarks': remarks,
                            'vod_content': title
                        }
                        videos.append(video)
                    except:
                        continue
                if videos:
                    break
        
        # 去重
        seen = set()
        unique_videos = []
        for v in videos:
            if v['vod_id'] not in seen:
                seen.add(v['vod_id'])
                unique_videos.append(v)
        
        print(f"解析到 {len(unique_videos)} 个视频")
        return unique_videos
        
    def _parse_detail(self, html, vid):
        """解析详情页"""
        vod = {
            'vod_id': vid,
            'vod_name': '',
            'vod_pic': '',
            'vod_actor': '',
            'vod_director': '',
            'vod_content': '',
            'vod_play_from': 'AV猴',
            'vod_play_url': '',
            'vod_year': '',
            'vod_area': '',
            'vod_remarks': ''
        }
        
        try:
            # 提取标题
            title_match = re.search(r'<title>([^<]+)</title>', html)
            if title_match:
                title = title_match.group(1).split('|')[0].strip()
                vod['vod_name'] = title
            
            # 提取缩略图
            img_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]*)"', html)
            if img_match:
                vod['vod_pic'] = img_match.group(1)
            
            # 提取描述
            desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
            if desc_match:
                vod['vod_content'] = desc_match.group(1)
            
            # 提取播放地址
            play_url = self._extract_play_url(html)
            if play_url:
                vod['vod_play_url'] = f"播放地址${play_url}"
            else:
                vod['vod_play_url'] = f"播放地址${self.siteUrl}/video/{vid}"
            
            # 提取观看数
            views_match = re.search(r'([\d.]+[千万]?)[^0-9]*?(?:次)?播放', html)
            if views_match:
                vod['vod_remarks'] = f"{views_match.group(1)}次播放"
                
        except Exception as e:
            print(f"_parse_detail error: {e}")
            
        return vod
        
    def _extract_play_url(self, html):
        """提取播放地址"""
        play_url = None
        
        # 从JSON-LD提取
        jsonld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        jsonld_match = re.search(jsonld_pattern, html, re.DOTALL)
        if jsonld_match:
            try:
                data = json.loads(jsonld_match.group(1))
                if isinstance(data, dict):
                    if 'contentUrl' in data:
                        play_url = data['contentUrl']
                    elif 'video' in data and isinstance(data['video'], dict):
                        if 'contentUrl' in data['video']:
                            play_url = data['video']['contentUrl']
            except:
                pass
        
        # 查找M3U8链接
        if not play_url:
            m3u8_pattern = r'(https?://[^"\']+\.m3u8[^"\']*)'
            m3u8_match = re.search(m3u8_pattern, html)
            if m3u8_match:
                play_url = m3u8_match.group(1)
        
        # 查找API链接
        if not play_url:
            api_pattern = r'(/api/[^"\']*\.m3u8[^"\']*)'
            api_match = re.search(api_pattern, html)
            if api_match:
                play_url = urllib.parse.urljoin(self.siteUrl, api_match.group(1))
        
        return play_url
        
    def localProxy(self, param, *args, **kwargs):
        """本地代理"""
        return None
        
    def fetch(self, url):
        """发送HTTP请求"""
        try:
            print(f"请求URL: {url}")
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                print(f"响应长度: {len(html)}")
                return html
        except Exception as e:
            print(f"fetch error {url}: {e}")
            return None


# 本地测试
if __name__ == "__main__":
    spider = Spider()
    
    print("=== 测试方法参数兼容性 ===")
    print("getDependence:", spider.getDependence("test") is not None)
    print("init:", spider.init("test") is None)
    
    print("\n=== 测试 homeContent ===")
    home = spider.homeContent("test_param")
    print(f"分类数量: {len(home.get('class', []))}")
    print(f"视频数量: {len(home.get('list', []))}")
    
    print("\n=== 测试分页功能 ===")
    cat1 = spider.categoryContent("国产自拍-1", 1)
    print(f"第一页视频数: {len(cat1.get('list', []))}")
    print(f"总页数: {cat1.get('pagecount')}")
    
    if cat1.get('list'):
        print("\n第一个视频:", cat1['list'][0]['vod_name'])