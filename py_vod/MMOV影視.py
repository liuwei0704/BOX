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
        """返回站点名称"""
        return "MMOV影视"

    def init(self, extend=""):
        """初始化站点配置"""
        self.host = "https://www.mmov.app"
        pass

    def header(self):
        """请求头部"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }

    def homeContent(self, filter):
        """返回分类列表"""
        result = {}
        classes = [
            {"type_name": "电影", "type_id": "1"},
            {"type_name": "连续剧", "type_id": "2"},
            {"type_name": "综艺", "type_id": "3"},
            {"type_name": "动漫", "type_id": "4"}
        ]
        result["class"] = classes
        return result

    def homeVideoContent(self):
        """首页推荐视频"""
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 取第一个热播栏目
            items = root.select('ul.stui-vodlist li.stui-vodlist__item')
            
            for item in items[:12]:  # 首页通常取前12个
                try:
                    # 视频链接和标题
                    a_tag = item.select_one('a.stui-vodlist__thumb')
                    title_tag = item.select_one('h4.stui-vodlist__title a')
                    
                    if not a_tag or not title_tag:
                        continue
                    
                    vod_id = a_tag.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    vod_name = title_tag.get('title') or title_tag.text.strip()
                    
                    # 封面图 (处理懒加载 data-src)
                    vod_pic = ""
                    img_src = a_tag.get('data-src')
                    if img_src:
                        vod_pic = img_src
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else self.host + vod_pic
                    
                    # 更新状态/备注
                    vod_remarks = ""
                    remark_tag = item.select_one('span.pic-text')
                    if remark_tag:
                        vod_remarks = remark_tag.text.strip()
                    
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
        """分类页面内容 - 修正分页问题"""
        try:
            # 构建MMOV分类URL（修正分页逻辑）
            # 根据您提供的URL格式：/type/1-2.html
            base_url = f"{self.host}/type/{tid}.html"
            
            # 处理分页
            current_page = int(pg)
            if current_page > 1:
                # 第2页：/type/1-2.html
                url = f"{self.host}/type/{tid}-{current_page}.html"
            else:
                url = base_url
            
            print(f"访问分类URL: {url} (TID: {tid}, 页码: {pg})")
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 使用MMOV的选择器
            items = root.select('ul.stui-vodlist li.stui-vodlist__item')
            
            for item in items:
                try:
                    # 视频链接和标题
                    a_tag = item.select_one('a.stui-vodlist__thumb')
                    title_tag = item.select_one('h4.stui-vodlist__title a')
                    
                    if not a_tag or not title_tag:
                        continue
                    
                    vod_id = a_tag.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    vod_name = title_tag.get('title') or title_tag.text.strip()
                    
                    # 封面图
                    vod_pic = ""
                    img_src = a_tag.get('data-src')
                    if img_src:
                        vod_pic = img_src
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else self.host + vod_pic
                    
                    # 更新状态
                    vod_remarks = ""
                    remark_tag = item.select_one('span.pic-text')
                    if remark_tag:
                        vod_remarks = remark_tag.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception as e:
                    print(f"分类解析单个视频时出错: {e}")
                    continue
            
            # 【关键修正】分页解析逻辑
            pagecount = current_page  # 默认为当前页
            
            # 方法1: 查找分页控件
            pagination = root.select('.stui-page, .pagination, .stui-pannel__head')
            
            if pagination:
                page_numbers = []
                for element in pagination:
                    # 查找所有链接
                    links = element.select('a')
                    for link in links:
                        try:
                            text = link.text.strip()
                            href = link.get('href', '')
                            
                            # 从文本提取页码
                            if text.isdigit():
                                page_numbers.append(int(text))
                                continue
                                
                            # 从href提取页码
                            if href:
                                # 匹配 /type/1-2.html 格式
                                match = re.search(r'/type/\d+-(\d+)\.html', href)
                                if match:
                                    page_numbers.append(int(match.group(1)))
                                    continue
                                
                                # 匹配 /vodshow/1-----------2.html 格式
                                match = re.search(r'vodshow/\d+-----------(\d+)\.html', href)
                                if match:
                                    page_numbers.append(int(match.group(1)))
                                    continue
                                    
                                # 匹配 page= 参数
                                match = re.search(r'page[=_/](\d+)', href, re.I)
                                if match:
                                    page_numbers.append(int(match.group(1)))
                                    continue
                        except:
                            continue
            
            # 方法2: 查找"更多"链接
            if not page_numbers:
                more_links = root.select('a[href*="vodshow"]')
                for link in more_links:
                    href = link.get('href', '')
                    if href and 'vodshow' in href:
                        match = re.search(r'vodshow/\d+-----------(\d+)\.html', href)
                        if match:
                            try:
                                page_numbers.append(int(match.group(1)))
                            except:
                                pass
            
            # 确定总页数
            if page_numbers:
                # 取最大值，但至少为当前页
                max_page = max(page_numbers)
                pagecount = max(max_page, current_page)
            else:
                # 如果没有找到分页信息，但有视频内容，假设可以翻页
                if videos:
                    pagecount = max(current_page + 1, 2)  # 至少2页
                else:
                    pagecount = current_page
            
            print(f"解析结果: 当前页={current_page}, 总页数={pagecount}, 视频数={len(videos)}")
            
            return {
                "list": videos,
                "page": current_page,
                "pagecount": pagecount,
                "limit": 20,
                "total": len(videos) * pagecount  # 估算总数
            }
            
        except Exception as e:
            print(f"分类页面解析错误: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }

    def detailContent(self, ids):
        """视频详情页 - 完全适配MMOV结构"""
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                url = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
            else:
                url = vod_id
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 1. 解析基本信息
            # 标题
            vod_name = ""
            title_tag = root.select_one('.stui-content__detail h3.title')
            if title_tag:
                vod_name = title_tag.text.strip()
            
            # 封面图
            vod_pic = ""
            cover_img = root.select_one('.stui-content__thumb img')
            if cover_img:
                img_src = cover_img.get('data-src') or cover_img.get('src')
                if img_src:
                    vod_pic = img_src
                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else self.host + vod_pic
            
            # 描述
            vod_content = ""
            desc_tag = root.select_one('.stui-content__desc')
            if desc_tag:
                vod_content = desc_tag.text.strip()
            
            # 其他信息
            vod_year = ""
            vod_actor = ""
            vod_director = ""
            vod_area = ""
            
            # 从meta标签获取信息
            meta_area = root.find('meta', itemprop='contentLocation')
            if meta_area and meta_area.get('content'):
                vod_area = meta_area['content']
            
            meta_actor = root.find('meta', itemprop='actor')
            if meta_actor and meta_actor.get('content'):
                vod_actor = meta_actor['content']
            
            # 从页面数据区域获取信息
            data_section = root.select('.stui-content__detail p.data')
            for data_item in data_section:
                text = data_item.text
                if '年份：' in text:
                    year_link = data_item.find('a')
                    if year_link:
                        vod_year = year_link.text.strip()
                elif '主演：' in text:
                    actor_links = data_item.find_all('a')
                    if actor_links:
                        actors = [a.text.strip() for a in actor_links]
                        vod_actor = ','.join(actors) if not vod_actor else vod_actor
                elif '导演：' in text:
                    director_links = data_item.find_all('a')
                    if director_links:
                        directors = [a.text.strip() for a in director_links]
                        vod_director = ','.join(directors)
                elif '地区：' in text:
                    area_link = data_item.find('a')
                    if area_link:
                        vod_area = area_link.text.strip() if not vod_area else vod_area
            
            # 2. 解析播放列表 - 关键部分
            play_from_list = []
            play_url_list = []
            
            # 查找所有播放源面板
            play_panels = root.select('div.stui-pannel')
            
            for panel in play_panels:
                # 获取播放源名称
                panel_head = panel.select_one('.stui-pannel__head h3.title')
                if not panel_head:
                    continue
                    
                source_name = panel_head.text.strip()
                
                # 获取播放列表
                episodes = []
                play_links = panel.select('ul.stui-content__playlist a')
                
                for link in play_links:
                    episode_title = link.text.strip()
                    episode_url = link.get('href', '')
                    
                    if episode_url:
                        # 处理相对URL
                        if not episode_url.startswith('http'):
                            episode_url = self.host + episode_url if episode_url.startswith('/') else episode_url
                        
                        if episode_title and episode_url:
                            episodes.append(f"{episode_title}${episode_url}")
                
                if episodes:
                    play_from_list.append(source_name)
                    play_url_list.append("#".join(episodes))
            
            # 如果没有找到播放列表，使用备用方案
            if not play_from_list:
                # 尝试从"立即播放"按钮获取
                play_button = root.select_one('a.btn-primary[href*="vodplay"]')
                if play_button:
                    play_url = play_button.get('href', '')
                    if play_url:
                        if not play_url.startswith('http'):
                            play_url = self.host + play_url if play_url.startswith('/') else play_url
                        
                        play_from_list = ["默认"]
                        play_url_list = [f"第1集${play_url}"]
            
            # 3. 构建结果
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name or "未知标题",
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": vod_year,
                "vod_actor": vod_actor,
                "vod_director": vod_director,
                "vod_area": vod_area,
                "vod_play_from": "$$$".join(play_from_list) if play_from_list else "默认播放源",
                "vod_play_url": "$$$".join(play_url_list) if play_url_list else f"第1集${url}"
            }
            
            return {"list": [video]}
            
        except Exception as e:
            print(f"详情页解析错误: {e}")
            import traceback
            traceback.print_exc()
            
            # 返回错误信息
            video = {
                "vod_id": ids[0],
                "vod_name": "加载失败",
                "vod_pic": "",
                "vod_content": str(e),
                "vod_play_from": "默认",
                "vod_play_url": f"第1集${self.host}"
            }
            return {"list": [video]}

    def searchContent(self, key, quick, pg=1):
        """搜索功能"""
        try:
            encoded_key = urllib.parse.quote(key.encode('utf-8'))
            search_url = f"{self.host}/vodsearch/-------------.html?wd={encoded_key}&page={pg}"
            
            rsp = self.fetch(search_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 搜索结果选择器
            result_items = root.select('ul.stui-vodlist li.stui-vodlist__item')
            
            for item in result_items:
                try:
                    a_tag = item.select_one('a.stui-vodlist__thumb')
                    title_tag = item.select_one('h4 a')
                    
                    if not a_tag or not title_tag:
                        continue
                    
                    vod_id = a_tag.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    vod_name = title_tag.get('title') or title_tag.text.strip()
                    
                    # 封面
                    vod_pic = ""
                    img_src = a_tag.get('data-src')
                    if not img_src:
                        img_tag = a_tag.select_one('img')
                        if img_tag:
                            img_src = img_tag.get('src')
                    if img_src:
                        vod_pic = img_src
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else self.host + vod_pic
                    
                    # 备注
                    vod_remarks = ""
                    remark_tag = item.select_one('span.pic-text')
                    if remark_tag:
                        vod_remarks = remark_tag.text.strip()
                    
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
            pagination = root.select_one('.stui-page, .pagination')
            if pagination:
                page_links = pagination.select('a')
                page_numbers = []
                for link in page_links:
                    try:
                        if link.text.strip().isdigit():
                            page_numbers.append(int(link.text.strip()))
                    except:
                        pass
                if page_numbers:
                    pagecount = max(page_numbers)
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 20,
                "total": len(videos)
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
            
            video_url = None
            
            # 1. 查找iframe
            iframe = root.select_one('iframe')
            if iframe and iframe.get('src'):
                video_url = iframe['src']
            
            # 2. 查找video标签
            if not video_url:
                video_tag = root.select_one('video')
                if video_tag and video_tag.get('src'):
                    video_url = video_tag['src']
            
            # 3. 查找source标签
            if not video_url:
                source_tag = root.select_one('source')
                if source_tag and source_tag.get('src'):
                    video_url = source_tag['src']
            
            # 4. 查找javascript中的播放地址
            if not video_url:
                script_tags = root.select('script')
                for script in script_tags:
                    if script.string:
                        patterns = [
                            r'url:\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'src:\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'file:\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'player\.src\s*\(\s*["\']([^"\']+)["\']',
                            r'video_url\s*=\s*["\']([^"\']+)["\']'
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, script.string)
                            if match:
                                video_url = match.group(1)
                                break
            
            if video_url:
                # 处理相对URL
                if video_url.startswith('//'):
                    video_url = 'https:' + video_url
                elif not video_url.startswith('http'):
                    video_url = self.host + video_url if video_url.startswith('/') else video_url
                
                result["parse"] = 0  # 直接播放
                result["url"] = video_url
            else:
                # 如果找不到直接播放地址，让TVBox解析
                result["parse"] = 1  # 需要解析
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