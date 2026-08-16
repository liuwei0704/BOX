# coding=utf-8
# 小宝影院 - TVBox FongMi 爬虫源
# 站点: https://xiaoheimi.cc

import sys
import os
import re
import json
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    def getName(self):
        return "小宝影院"
    
    def init(self, extend=""):
        self.host = "https://xiaoheimi.cc"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': self.host + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
        }
        print(f"[小宝影院] 初始化完成: {self.host}")
    
    def getDependence(self):
        return ["bs4"]
    
    def destroy(self):
        pass
    
    def header(self):
        return self.headers.copy()
    
    def _fetch(self, url, headers=None):
        """获取页面内容 - 与之前正常工作的版本一致"""
        if headers is None:
            headers = self.header()
        
        print(f"[小宝影院] _fetch 请求: {url}")
        
        # 使用基类 fetch
        for attempt in range(3):
            try:
                print(f"[小宝影院] 尝试 fetch (第 {attempt+1} 次)")
                rsp = self.fetch(url, headers=headers, timeout=15)
                if rsp and hasattr(rsp, 'text') and rsp.text:
                    print(f"[小宝影院] fetch 返回, 长度: {len(rsp.text)}")
                    return rsp
                if rsp and hasattr(rsp, 'content') and rsp.content:
                    class Resp:
                        def __init__(self, text, status):
                            self.text = text
                            self.status = status
                    try:
                        text = rsp.content.decode('utf-8', errors='ignore')
                        print(f"[小宝影院] fetch content 返回, 长度: {len(text)}")
                        return Resp(text, getattr(rsp, 'status', 200))
                    except:
                        pass
            except Exception as e:
                print(f"[小宝影院] fetch 异常: {e}")
        
        print(f"[小宝影院] fetch 失败")
        return None
    
    def _build_full_url(self, url):
        """将相对路径补全为完整URL"""
        if not url or not isinstance(url, str):
            return ''
        url = url.strip()
        if not url or url in ['小宝影院', 'null', 'undefined', '', 'javascript:;']:
            return ''
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        if url.startswith('./'):
            return self.host + url[1:]
        return self.host + '/' + url
    
    def _parse_video_item(self, item):
        """解析单个视频项"""
        link = item.find('a', class_='myui-vodlist__thumb')
        if not link:
            return None
        
        href = link.get('href', '')
        if not href:
            return None
        
        vod_id = self._build_full_url(href)
        title = link.get('title', '') or link.get('alt', '')
        if not title:
            title_el = item.find('h4', class_='title')
            if title_el:
                title = title_el.get_text(strip=True)
        
        pic = link.get('data-original', '') or link.get('src', '')
        pic = self._build_full_url(pic)
        
        remark = ''
        remark_span = item.find('span', class_='pic-text')
        if remark_span:
            remark = remark_span.get_text(strip=True)
        
        return {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": remark
        }
    
    def homeContent(self, filter):
        """返回分类列表和首页推荐"""
        result = {
            "class": [
                {"type_id": "7", "type_name": "电影"},
                {"type_id": "6", "type_name": "电视剧"},
                {"type_id": "5", "type_name": "动漫"},
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "21", "type_name": "纪录片"}
            ],
            "list": []
        }
        
        try:
            rsp = self._fetch(self.host + '/')
            if not rsp or not rsp.text:
                print("[小宝影院] 首页获取失败")
                return result
            
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            seen = set()
            
            # 提取首页视频列表
            vod_items = soup.select('.myui-vodlist__box')
            for item in vod_items:
                video = self._parse_video_item(item)
                if video and video['vod_id'] and video['vod_id'] not in seen:
                    seen.add(video['vod_id'])
                    videos.append(video)
                    if len(videos) >= 20:
                        break
            
            result["list"] = videos
            print(f"[小宝影院] 首页提取 {len(videos)} 个视频")
            
        except Exception as e:
            print(f"[小宝影院] homeContent 错误: {e}")
        
        return result
    
    def homeVideoContent(self):
        return self.homeContent(False)
    
    def categoryContent(self, tid, pg, filter, extend):
        """返回分类页内容"""
        pg = int(pg) if pg else 1
        result = {"list": [], "page": pg, "pagecount": 1, "limit": 0, "total": 0}
        
        try:
            if pg == 1:
                url = f"{self.host}/index.php/vod/type/id/{tid}.html"
            else:
                url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
            
            print(f"[小宝影院] 分类请求: {url}")
            rsp = self._fetch(url)
            if not rsp or not rsp.text:
                print("[小宝影院] 分类页面获取失败")
                return result
            
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            seen = set()
            
            vod_items = soup.select('.myui-vodlist__box')
            for item in vod_items:
                video = self._parse_video_item(item)
                if video and video['vod_id'] and video['vod_id'] not in seen:
                    seen.add(video['vod_id'])
                    videos.append(video)
            
            result["list"] = videos
            result["limit"] = len(videos)
            
            # 提取分页信息
            page_info = soup.find('ul', class_='myui-page')
            if page_info:
                page_links = page_info.find_all('a')
                max_page = 1
                for link in page_links:
                    href = link.get('href', '')
                    match = re.search(r'/page/(\d+)', href)
                    if match:
                        pg_num = int(match.group(1))
                        if pg_num > max_page:
                            max_page = pg_num
                result["pagecount"] = max_page if max_page > 1 else 1
            else:
                result["pagecount"] = 1
            
            result["total"] = result["pagecount"] * 20
            print(f"[小宝影院] 分类提取 {len(videos)} 个视频, 共 {result['pagecount']} 页")
            
        except Exception as e:
            print(f"[小宝影院] categoryContent 错误: {e}")
        
        return result
    
    def detailContent(self, ids):
        """返回详情页内容"""
        result = {"list": []}
        
        try:
            if isinstance(ids, list):
                vid = ids[0]
            else:
                vid = ids
            
            if vid.startswith('http'):
                match = re.search(r'/id/(\d+)', vid)
                if match:
                    vid = match.group(1)
            
            url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
            print(f"[小宝影院] 详情请求: {url}")
            
            rsp = self._fetch(url)
            if not rsp or not rsp.text:
                print("[小宝影院] 详情页获取失败")
                return result
            
            soup = BeautifulSoup(rsp.text, 'html.parser')
            
            vod = {
                "vod_id": vid,
                "vod_name": "",
                "vod_pic": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_area": "",
                "vod_year": "",
                "vod_remarks": "",
                "vod_play_from": "",
                "vod_play_url": ""
            }
            
            # 标题
            title_tag = soup.find('h1', class_='title')
            if title_tag:
                vod["vod_name"] = title_tag.get_text(strip=True)
            else:
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    vod["vod_name"] = og_title.get('content', '')
            
            # 封面
            thumb_div = soup.find('div', class_='myui-content__thumb')
            if thumb_div:
                img = thumb_div.find('img')
                if img:
                    pic = img.get('data-original', '') or img.get('src', '')
                    vod["vod_pic"] = self._build_full_url(pic)
            
            # 详细信息
            for p in soup.find_all('p', class_='data'):
                text = p.get_text(strip=True)
                if '分类：' in text or '類型：' in text:
                    link = p.find('a')
                    if link:
                        vod["type_name"] = link.get_text(strip=True)
                elif '地区：' in text or '地區：' in text:
                    link = p.find('a')
                    if link:
                        vod["vod_area"] = link.get_text(strip=True)
                elif '年份：' in text:
                    link = p.find('a')
                    if link:
                        vod["vod_year"] = link.get_text(strip=True)
                elif '更新：' in text:
                    span = p.find('span', class_='text-red')
                    if span:
                        vod["vod_remarks"] = span.get_text(strip=True)
                elif '主演：' in text:
                    actors = [a.get_text(strip=True) for a in p.find_all('a')]
                    if actors:
                        vod["vod_actor"] = ','.join(actors)
                elif '导演：' in text or '導演：' in text:
                    directors = [a.get_text(strip=True) for a in p.find_all('a')]
                    if directors:
                        vod["vod_director"] = ','.join(directors)
            
            # 简介
            desc_div = soup.find('div', class_='text-collapse')
            if desc_div:
                content_span = desc_div.find('span', class_='data')
                if content_span:
                    vod["vod_content"] = content_span.get_text(strip=True)
                else:
                    sketch = desc_div.find('span', class_='sketch')
                    if sketch:
                        vod["vod_content"] = sketch.get_text(strip=True)
            
            # 播放地址
            play_froms = []
            play_urls = []
            
            tab_links = soup.select('.myui-panel__head .nav-tabs li a')
            for tab in tab_links:
                name = tab.get_text(strip=True)
                if name:
                    play_froms.append(name)
            
            if not play_froms:
                play_froms = ["小宝影院"]
            
            tab_panes = soup.find_all('div', class_='tab-pane')
            for i, pane in enumerate(tab_panes):
                if i >= len(play_froms):
                    break
                episodes = []
                playlist = pane.find('ul', class_='myui-content__list')
                if playlist:
                    for link in playlist.find_all('a', href=True):
                        href = link.get('href', '')
                        if href and href != 'javascript:;':
                            ep_name = link.get_text(strip=True)
                            if ep_name:
                                ep_url = self._build_full_url(href)
                                if ep_url:
                                    episodes.append(f"{ep_name}${ep_url}")
                if episodes:
                    play_urls.append('#'.join(episodes))
            
            if not play_urls:
                playlist_ul = soup.find('ul', class_='myui-content__list')
                if playlist_ul:
                    episodes = []
                    for link in playlist_ul.find_all('a', href=True):
                        href = link.get('href', '')
                        if href and href != 'javascript:;':
                            ep_name = link.get_text(strip=True)
                            if ep_name:
                                ep_url = self._build_full_url(href)
                                if ep_url:
                                    episodes.append(f"{ep_name}${ep_url}")
                    if episodes:
                        play_urls.append('#'.join(episodes))
                        play_froms = ["小宝影院"]
            
            vod["vod_play_from"] = '$$$'.join(play_froms)
            vod["vod_play_url"] = '$$$'.join(play_urls)
            
            result["list"] = [vod]
            print(f"[小宝影院] 详情提取成功: {vod['vod_name']}")
            
        except Exception as e:
            print(f"[小宝影院] detailContent 错误: {e}")
        
        return result
    
    def searchContent(self, key, quick, pg=1):
        """搜索内容"""
        pg = int(pg) if pg else 1
        result = {"list": [], "pagecount": 1, "page": pg, "limit": 0, "total": 0}
        
        try:
            encoded_key = urllib.parse.quote(key)
            if pg == 1:
                search_url = f"{self.host}/index.php/vod/search.html?wd={encoded_key}"
            else:
                search_url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{encoded_key}.html"
            
            print(f"[小宝影院] 搜索: {key}, URL: {search_url}")
            
            rsp = self._fetch(search_url)
            if not rsp or not rsp.text:
                print("[小宝影院] 搜索页面获取失败")
                return result
            
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            seen = set()
            
            search_list = soup.find('ul', id='searchList')
            if search_list:
                items = search_list.find_all('li', class_='clearfix')
                for item in items:
                    title_tag = item.find('h4', class_='title')
                    if not title_tag:
                        continue
                    link_tag = title_tag.find('a')
                    if not link_tag:
                        continue
                    href = link_tag.get('href', '')
                    if not href:
                        continue
                    vod_id = self._build_full_url(href)
                    title = link_tag.get_text(strip=True)
                    
                    pic = ''
                    thumb_div = item.find('div', class_='thumb')
                    if thumb_div:
                        img = thumb_div.find('img')
                        if img:
                            pic = img.get('data-original', '') or img.get('src', '')
                    if not pic:
                        a_tag = item.find('a', class_='myui-vodlist__thumb')
                        if a_tag:
                            pic = a_tag.get('data-original', '') or a_tag.get('src', '')
                    pic = self._build_full_url(pic)
                    
                    remark = ''
                    pic_text = item.find('span', class_='pic-text')
                    if pic_text:
                        remark = pic_text.get_text(strip=True)
                    
                    if vod_id and vod_id not in seen and title:
                        seen.add(vod_id)
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": title,
                            "vod_pic": pic,
                            "vod_remarks": remark
                        })
            
            if not videos:
                vod_items = soup.select('.myui-vodlist__box')
                for item in vod_items:
                    video = self._parse_video_item(item)
                    if video and video['vod_id'] and video['vod_id'] not in seen:
                        seen.add(video['vod_id'])
                        videos.append(video)
            
            result["list"] = videos
            result["limit"] = len(videos)
            
            page_info = soup.find('ul', class_='myui-page')
            if page_info:
                mobile_span = page_info.find('span', class_='visible-xs')
                if mobile_span:
                    page_text = mobile_span.get_text(strip=True)
                    match = re.search(r'/(\d+)', page_text)
                    if match:
                        result["pagecount"] = int(match.group(1))
                else:
                    page_links = page_info.find_all('a')
                    max_page = 1
                    for link in page_links:
                        href = link.get('href', '')
                        match = re.search(r'/page/(\d+)', href)
                        if match:
                            pg_num = int(match.group(1))
                            if pg_num > max_page:
                                max_page = pg_num
                    result["pagecount"] = max_page if max_page > 1 else 1
            else:
                result["pagecount"] = 1
            
            result["total"] = result["pagecount"] * len(videos) if videos else 0
            print(f"[小宝影院] 搜索到 {len(videos)} 个结果, 共 {result['pagecount']} 页")
            
        except Exception as e:
            print(f"[小宝影院] searchContent 错误: {e}")
        
        return result
    
    def playerContent(self, ids, flag, ext):
        """返回播放地址 - header 直接返回 dict"""
        result = {"parse": 0, "playUrl": "", "url": "", "header": {}}
        
        # 直接构建 dict，不序列化
        clean_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': self.host + '/',
            'Origin': self.host,
        }
        
        try:
            play_url = ids
            print(f"[小宝影院] 播放请求 - ID: {play_url}, Flag: {flag}")
            
            # 如果 ids 是线路名称，从 flag 获取真实URL
            if play_url in ["小宝影院", "小宝影院1", "小宝影院2"]:
                if flag and flag.startswith('http'):
                    play_url = flag
                    print(f"[小宝影院] 从 flag 获取URL: {play_url}")
                else:
                    print(f"[小宝影院] 无效的线路名称: {play_url}")
                    return result
            
            if not play_url or not play_url.startswith('http'):
                print(f"[小宝影院] 无效的播放URL: {play_url}")
                return result
            
            # 如果是直链视频格式
            if re.search(r'\.(m3u8|mp4|flv)(\?|$)', play_url, re.I):
                result['parse'] = 0
                result['url'] = play_url
                result['header'] = clean_headers
                return result
            
            # 获取播放页面
            rsp = self._fetch(play_url)
            if not rsp or not rsp.text:
                print("[小宝影院] 播放页面获取失败")
                result["url"] = play_url
                result["header"] = clean_headers
                return result
            
            html = rsp.text
            
            # 提取 player_aaaa 中的 url
            match = re.search(r'var\s+player_aaaa\s*=\s*\{[^}]*"url"\s*:\s*"([^"]+)"', html)
            if not match:
                match = re.search(r"var\s+player_aaaa\s*=\s*\{[^}]*'url'\s*:\s*'([^']+)'", html)
            if match:
                purl = match.group(1)
                purl = purl.replace('\\/', '/')
                print(f"[小宝影院] 从 player_aaaa 提取: {purl[:100]}...")
                
                result['parse'] = 0
                result['url'] = purl
                result['header'] = clean_headers
                return result
            
            # 从 iframe 提取
            iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', html)
            if iframe_match:
                iframe_url = iframe_match.group(1)
                if iframe_url.startswith('/'):
                    iframe_url = self.host + iframe_url
                print(f"[小宝影院] 从 iframe 提取: {iframe_url}")
                return self.playerContent(iframe_url, flag, ext)
            
            # 直接搜索 m3u8
            m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
            if m3u8_match:
                purl = m3u8_match.group(1)
                print(f"[小宝影院] 从 HTML 提取 m3u8: {purl[:100]}...")
                result['parse'] = 0
                result['url'] = purl
                result['header'] = clean_headers
                return result
            
            print("[小宝影院] 未找到播放地址，使用默认")
            result["url"] = play_url
            result["header"] = clean_headers
            
        except Exception as e:
            print(f"[小宝影院] playerContent 错误: {e}")
            result["url"] = ids if ids and ids != "小宝影院" else ""
            result["header"] = clean_headers
        
        return result
    def isVideoFormat(self, url):
        if not url or not isinstance(url, str):
            return False
        video_exts = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.wmv', '.mov']
        return any(ext in url.lower() for ext in video_exts)
    
    def localProxy(self, params):
        return None


def getSpider():
    return Spider()

def getHomeContent():
    return Spider().homeContent(False)

def getHomeVideoContent():
    return Spider().homeVideoContent()

def getCategoryContent(tid, pg=1, filter=False, extend=None):
    return Spider().categoryContent(tid, pg, filter, extend)

def getDetailContent(ids):
    return Spider().detailContent(ids)

def getSearchContent(key, quick=False, pg=1):
    return Spider().searchContent(key, quick, pg)

def getPlayerContent(flag, id, vipFlags=None):
    return Spider().playerContent(id, flag, vipFlags)

def getDependence():
    return Spider().getDependence()

def destroy():
    return Spider().destroy()