# coding=utf-8
import sys
import os
import re
import json
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    def getName(self):
        return "新站点名称"
    
    def init(self, extend=""):
        self.host = "https://www.yoursite.com"
        # 如果需要登录或其他初始化，在这里处理
        pass
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }
    
    def homeContent(self, filter):
        """返回分类列表"""
        result = {}
        classes = [
            {"type_name": "电影", "type_id": "movie"},
            {"type_name": "电视剧", "type_id": "tv"},
            {"type_name": "动漫", "type_id": "anime"},
            {"type_name": "综艺", "type_id": "variety"}
        ]
        result["class"] = classes
        return result
    
    def homeVideoContent(self):
        """首页推荐视频"""
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 根据网站实际结构选择元素
            items = root.select('.video-list .item')  # 修改选择器
            
            for item in items:
                try:
                    a = item.find('a')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取标题
                    vod_name = a.get('title', '')
                    if not vod_name:
                        title_elem = a.find('h3') or a.find('h2') or a.find('span', class_='title')
                        if title_elem:
                            vod_name = title_elem.text.strip()
                    
                    # 获取封面图
                    vod_pic = ""
                    img = item.find('img')
                    if img and 'src' in img.attrs:
                        vod_pic = img['src']
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
                    
                    # 获取备注（更新状态）
                    vod_remarks = ""
                    remark_elem = item.find('span', class_='remark') or item.find('i')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception as e:
                    print(f"解析单个视频时出错: {e}")
                    continue
            
            return {"list": videos}
        except Exception as e:
            print(f"首页视频解析错误: {e}")
            return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类页面内容"""
        try:
            # 构建分类URL
            if int(pg) > 1:
                url = f"{self.host}/{tid}/page/{pg}/"
            else:
                url = f"{self.host}/{tid}/"
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 根据实际结构选择元素
            items = root.select('.list-item')  # 修改选择器
            
            for item in items:
                try:
                    a = item.find('a')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取标题
                    vod_name = a.get('title', '')
                    if not vod_name:
                        title_elem = a.find('.title') or a.find('h3')
                        if title_elem:
                            vod_name = title_elem.text.strip()
                    
                    # 获取封面图
                    vod_pic = ""
                    img = item.find('img')
                    if img and 'src' in img.attrs:
                        vod_pic = img['src']
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
                    
                    # 获取备注
                    vod_remarks = ""
                    remark_elem = item.find('.update') or item.find('.score')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception as e:
                    print(f"分类解析单个视频时出错: {e}")
                    continue
            
            # 分页信息
            pagecount = 1
            pagination = root.find('.pagination')
            if pagination:
                page_links = pagination.find_all('a')
                page_numbers = []
                for link in page_links:
                    try:
                        num = int(link.text.strip())
                        page_numbers.append(num)
                    except:
                        pass
                if page_numbers:
                    pagecount = max(page_numbers)
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 20,
                "total": len(videos) * pagecount
            }
        except Exception as e:
            print(f"分类页面解析错误: {e}")
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }
    
    def detailContent(self, ids):
        """视频详情页"""
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                url = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
            else:
                url = vod_id
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 解析基本信息
            vod_name = root.find('h1').text.strip() if root.find('h1') else "未知"
            
            # 封面图
            vod_pic = ""
            cover_img = root.find('.cover-img') or root.find('.poster') or root.find('img', {'class': re.compile('cover|poster')})
            if cover_img and 'src' in cover_img.attrs:
                vod_pic = cover_img['src']
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
            
            # 描述
            vod_content = ""
            desc_elem = root.find('.description') or root.find('.intro') or root.find('.plot')
            if desc_elem:
                vod_content = desc_elem.text.strip()
            
            # 其他信息（年份、演员等）
            info_dict = {}
            info_section = root.find('.info') or root.find('.details')
            if info_section:
                for dl in info_section.find_all('dl'):
                    dt = dl.find('dt')
                    dd = dl.find('dd')
                    if dt and dd:
                        label = dt.text.strip().replace(':', '')
                        value = dd.text.strip()
                        info_dict[label] = value
            
            # 解析播放源
            play_from_list = []
            play_url_list = []
            
            # 查找播放列表
            play_sections = root.find_all('.play-source') or root.find_all('.episode-list')
            
            for section in play_sections:
                # 播放源名称
                source_name = "默认"
                source_title = section.find('h3') or section.find('h4')
                if source_title:
                    source_name = source_title.text.strip()
                
                # 播放列表
                episodes = []
                for ep_link in section.find_all('a', href=True):
                    ep_title = ep_link.text.strip()
                    ep_url = ep_link['href']
                    
                    if ep_url and not ep_url.startswith('http'):
                        ep_url = self.host + ep_url if ep_url.startswith('/') else ep_url
                    
                    if ep_title and ep_url:
                        episodes.append(f"{ep_title}${ep_url}")
                
                if episodes:
                    play_from_list.append(source_name)
                    play_url_list.append("#".join(episodes))
            
            # 如果没有找到播放列表，使用备用方法
            if not play_from_list:
                all_play_links = root.find_all('a', href=re.compile(r'/play/|/watch/'))
                if all_play_links:
                    episodes = []
                    for link in all_play_links[:50]:
                        title = link.text.strip()
                        href = link.get('href', '')
                        
                        if href and not href.startswith('http'):
                            href = self.host + href if href.startswith('/') else href
                        
                        if title and href:
                            episodes.append(f"{title}${href}")
                    
                    if episodes:
                        play_from_list = ["播放源"]
                        play_url_list = ["#".join(episodes)]
            
            # 构建结果
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": info_dict.get('年份', info_dict.get('Year', '')),
                "vod_actor": info_dict.get('演员', info_dict.get('Actor', '')),
                "vod_director": info_dict.get('导演', info_dict.get('Director', '')),
                "vod_area": info_dict.get('地区', info_dict.get('Region', '')),
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }
            
            return {"list": [video]}
            
        except Exception as e:
            print(f"详情页解析错误: {e}")
            import traceback
            traceback.print_exc()
            
            video = {
                "vod_id": ids[0],
                "vod_name": "加载失败",
                "vod_pic": "",
                "vod_content": "",
                "vod_play_from": "默认",
                "vod_play_url": f"第1集${self.host}"
            }
            return {"list": [video]}
    
    def searchContent(self, key, quick, pg=1):
        """搜索功能"""
        try:
            encoded_key = urllib.parse.quote(key)
            search_url = f"{self.host}/search?q={encoded_key}&page={pg}"
            
            rsp = self.fetch(search_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 解析搜索结果
            result_items = root.select('.search-result .item') or root.find_all('div', class_='result-item')
            
            for item in result_items:
                try:
                    a = item.find('a')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 标题
                    vod_name = a.get('title', '')
                    if not vod_name:
                        title_elem = a.find('.title') or a.find('h3')
                        if title_elem:
                            vod_name = title_elem.text.strip()
                    
                    # 封面
                    vod_pic = ""
                    img = item.find('img')
                    if img and 'src' in img.attrs:
                        vod_pic = img['src']
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
                    
                    # 备注
                    vod_remarks = ""
                    remark_elem = item.find('.remark') or item.find('.update')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception as e:
                    print(f"搜索解析单个结果时出错: {e}")
                    continue
            
            # 分页信息
            pagecount = 1
            pagination = root.find('.pagination')
            if pagination:
                last_page_link = pagination.find('a', class_='last') or pagination.find_all('a')[-1]
                if last_page_link and last_page_link.get('href'):
                    href = last_page_link['href']
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        pagecount = int(match.group(1))
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 20,
                "total": len(videos) * pagecount
            }
            
        except Exception as e:
            print(f"搜索解析错误: {e}")
            return {"list": []}
    
    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        result = {}
        
        try:
            if not id.startswith('http'):
                play_url = self.host + id if id.startswith('/') else self.host + '/' + id
            else:
                play_url = id
            
            rsp = self.fetch(play_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 尝试解析播放地址
            video_url = None
            
            # 1. 查找iframe
            iframe = root.find('iframe')
            if iframe and iframe.get('src'):
                video_url = iframe['src']
            
            # 2. 查找video标签
            if not video_url:
                video_tag = root.find('video')
                if video_tag and video_tag.get('src'):
                    video_url = video_tag['src']
            
            # 3. 查找source标签
            if not video_url:
                source_tag = root.find('source')
                if source_tag and source_tag.get('src'):
                    video_url = source_tag['src']
            
            # 4. 查找javascript中的播放地址
            if not video_url:
                script_tags = root.find_all('script')
                for script in script_tags:
                    if script.string:
                        # 尝试匹配各种视频地址格式
                        patterns = [
                            r'url:\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'src:\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'file:\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']'
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, script.string)
                            if match:
                                video_url = match.group(1)
                                break
            
            if video_url:
                result["parse"] = 0
                result["url"] = video_url
            else:
                # 如果找不到直接播放地址，让TVBox解析
                result["parse"] = 1
                result["url"] = play_url
            
            result["header"] = self.header()
            
        except Exception as e:
            print(f"播放地址解析错误: {e}")
            result["parse"] = 1
            result["url"] = id
            result["header"] = self.header()
        
        return result
    
    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        video_formats = ['.m3u8', '.mp4', '.avi', '.mkv', '.flv', '.ts', '.webm']
        return any(fmt in url.lower() for fmt in video_formats)
    
    def localProxy(self, params):
        """本地代理"""
        return [200, "video/MP2T", ""]