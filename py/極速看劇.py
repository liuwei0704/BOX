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
        return "极速看剧"
    
    def init(self, extend=""):
        self.host = "https://jddy.tv"
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
            {"type_name": "电影", "type_id": "1"},
            {"type_name": "电视剧", "type_id": "2"},
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
            
            # 首页有多个区块：电影、电视剧、动漫
            # 获取所有区块的视频
            sections = root.select('.index-tj .index-tj-l ul')
            
            for section in sections:
                items = section.find_all('li', class_='p2')
                
                for item in items:
                    try:
                        a = item.find('a', class_='link-hover')
                        if not a:
                            continue
                        
                        vod_id = a.get('href', '')
                        if vod_id and not vod_id.startswith('http'):
                            vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                        
                        # 获取标题
                        vod_name = ""
                        name_elem = a.find('p', class_='name')
                        if name_elem:
                            vod_name = name_elem.text.strip()
                        
                        # 获取封面图
                        vod_pic = ""
                        img = a.find('img')
                        if img:
                            vod_pic = img.get('src', '') or img.get('data-src', '')
                            if vod_pic:
                                if vod_pic.startswith('//'):
                                    vod_pic = 'https:' + vod_pic
                                elif not vod_pic.startswith('http'):
                                    vod_pic = self.host + vod_pic if vod_pic.startswith('/') else vod_pic
                        
                        # 获取备注（更新状态）
                        vod_remarks = ""
                        remark_elem = a.find('p', class_='other')
                        if remark_elem:
                            vod_remarks = remark_elem.text.strip()
                        
                        if vod_name and vod_id:
                            videos.append({
                                "vod_id": vod_id,
                                "vod_name": vod_name,
                                "vod_pic": vod_pic,
                                "vod_remarks": vod_remarks
                            })
                    except Exception as e:
                        print(f"首页解析单个视频时出错: {e}")
                        continue
            
            return {"list": videos[:60]}  # 限制返回数量
        except Exception as e:
            print(f"首页视频解析错误: {e}")
            return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类页面内容 - 基于实际HTML结构"""
        try:
            # 根据实际HTML，分类页面URL格式：
            # 第一页：/vodtype/1.html
            # 第二页：/vodtype/1-2.html
            # 以此类推
            
            if int(pg) == 1:
                url = f"{self.host}/vodtype/{tid}.html"
            else:
                url = f"{self.host}/vodtype/{tid}-{pg}.html"
            
            print(f"访问分类URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            
            if rsp.status_code != 200:
                print(f"页面访问失败，状态码: {rsp.status_code}")
                return {
                    "list": [],
                    "page": int(pg),
                    "pagecount": 1,
                    "limit": 30,
                    "total": 0
                }
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 根据实际HTML结构，视频项在 .index-area ul li 中
            # 每个li的class是 "p1 m1 "（注意有空格）
            video_items = root.select('.index-area ul li')
            
            # 如果没找到，尝试备用选择器
            if not video_items:
                video_items = root.find_all('li', class_=re.compile(r'p[0-9]'))
            
            print(f"找到 {len(video_items)} 个视频项")
            
            for item in video_items:
                try:
                    # 查找链接
                    a = item.find('a', class_='link-hover')
                    if not a:
                        continue
                    
                    # 获取视频ID
                    vod_id = a.get('href', '')
                    if vod_id:
                        if not vod_id.startswith('http'):
                            vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取标题
                    vod_name = ""
                    name_elem = a.find('p', class_='name')
                    if name_elem:
                        vod_name = name_elem.text.strip()
                    
                    # 如果没找到，尝试从a标签的title属性获取
                    if not vod_name:
                        vod_name = a.get('title', '')
                    
                    # 获取封面图
                    vod_pic = ""
                    img = a.find('img')
                    if img:
                        vod_pic = img.get('src', '') or img.get('data-src', '')
                        if vod_pic:
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            elif vod_pic.startswith('/'):
                                vod_pic = self.host + vod_pic
                            elif not vod_pic.startswith('http'):
                                vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
                    
                    # 获取备注
                    vod_remarks = ""
                    remark_elem = a.find('p', class_='other')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
                    # 获取演员信息（可选）
                    vod_actor = ""
                    actor_elem = a.find('p', class_='actor')
                    if actor_elem:
                        # 取第一个actor段落（演员信息）
                        actor_text = actor_elem.text.strip()
                        lines = actor_text.split('\n')
                        if lines:
                            vod_actor = lines[0].strip()
                    
                    if vod_name and vod_id:
                        videos.append({
                            "vod_id": vod_id,
                            "vod_name": vod_name,
                            "vod_pic": vod_pic,
                            "vod_remarks": vod_remarks,
                            "vod_actor": vod_actor
                        })
                        
                        print(f"解析视频: {vod_name}")
                    
                except Exception as e:
                    print(f"分类解析单个视频时出错: {e}")
                    continue
            
            # 分页信息
            pagecount = 1
            pagination = root.find('div', class_='page')
            
            if pagination:
                # 从文本提取总页数
                page_text = pagination.text.strip()
                print(f"分页文本: {page_text}")
                
                # 匹配"当前1/1372页"格式
                match = re.search(r'当前\d+/(\d+)页', page_text)
                if match:
                    pagecount = int(match.group(1))
                    print(f"从文本提取到总页数: {pagecount}")
                else:
                    # 尝试从链接中提取
                    page_links = pagination.find_all('a', class_='page_link')
                    page_numbers = []
                    
                    for link in page_links:
                        href = link.get('href', '')
                        if href:
                            # 匹配 /vodtype/1-1372.html 格式
                            match = re.search(r'/vodtype/\d+-(\d+)\.html', href)
                            if match:
                                try:
                                    page_numbers.append(int(match.group(1)))
                                except:
                                    pass
                    
                    if page_numbers:
                        pagecount = max(page_numbers)
                        print(f"从链接提取到最大页码: {pagecount}")
            
            print(f"返回 {len(videos)} 个视频，总页数: {pagecount}")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 30,
                "total": pagecount * 30
            }
            
        except Exception as e:
            print(f"分类页面解析错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 30,
                "total": 0
            }
    
    def detailContent(self, ids):
        """视频详情页 - 基于实际HTML结构"""
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                url = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
            else:
                url = vod_id
            
            print(f"访问详情页URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 解析基本信息
            vod_name = ""
            title_elem = root.find('h1', class_='name')
            if not title_elem:
                title_elem = root.find('h1')
            if title_elem:
                vod_name = title_elem.text.strip()
            
            # 封面图
            vod_pic = ""
            cover_img = root.select_one('.ct-l img')
            if cover_img:
                vod_pic = cover_img.get('src', '') or cover_img.get('data-src', '')
                if vod_pic:
                    if vod_pic.startswith('//'):
                        vod_pic = 'https:' + vod_pic
                    elif not vod_pic.startswith('http'):
                        vod_pic = self.host + vod_pic if vod_pic.startswith('/') else vod_pic
            
            # 描述 - 在.tab-jq中
            vod_content = ""
            desc_elem = root.select_one('.tab-jq')
            if desc_elem:
                # 清理描述文本
                vod_content = desc_elem.text.strip()
                # 移除最后的分享提示
                if "如果您喜欢" in vod_content and "别忘了分享给好友哦！" in vod_content:
                    vod_content = vod_content.split("如果您喜欢")[0].strip()
            
            # 其他信息 - 从dl dt dd中提取
            info_dict = {}
            info_section = root.select_one('.ct-c dl')
            if info_section:
                # 提取所有dt和dd
                current_key = ""
                for element in info_section.find_all(['dt', 'dd']):
                    if element.name == 'dt':
                        # 提取键名
                        text = element.text.strip()
                        if '：' in text:
                            key = text.split('：')[0].strip()
                            value = text.split('：', 1)[1].strip()
                            info_dict[key] = value
                            current_key = key
                        elif text and not text.endswith('：'):
                            # 可能是单独的标题
                            pass
                    elif element.name == 'dd':
                        # 提取值
                        text = element.text.strip()
                        if '：' in text:
                            parts = text.split('：', 1)
                            if len(parts) == 2:
                                info_dict[parts[0].strip()] = parts[1].strip()
                        elif current_key and text:
                            # 补充上一个key的值
                            info_dict[current_key] = text
            
            print(f"信息字典: {info_dict}")
            
            # 解析播放源 - 根据实际HTML结构
            play_from_list = []
            play_url_list = []
            
            # 查找播放源列表
            playfrom_div = root.select_one('.playfrom')
            if playfrom_div:
                # 提取播放源名称
                source_items = playfrom_div.find_all('li')
                source_names = []
                for item in source_items:
                    text = item.text.strip()
                    if text:
                        source_names.append(text)
                
                # 查找对应的播放列表
                for i, source_name in enumerate(source_names):
                    playlist_id = f"stab8{i+1}"  # stab81, stab82, stab83
                    playlist_div = root.select_one(f'#{playlist_id}')
                    
                    if playlist_div:
                        episodes = []
                        # 查找播放链接
                        play_links = playlist_div.find_all('a', href=True)
                        for link in play_links:
                            ep_title = link.text.strip()
                            ep_url = link.get('href', '')
                            
                            if ep_url:
                                if ep_url.startswith('//'):
                                    ep_url = 'https:' + ep_url
                                elif not ep_url.startswith('http'):
                                    ep_url = self.host + ep_url if ep_url.startswith('/') else self.host + '/' + ep_url
                            
                            if ep_title and ep_url:
                                episodes.append(f"{ep_title}${ep_url}")
                        
                        if episodes:
                            play_from_list.append(source_name)
                            play_url_list.append("#".join(episodes))
            
            # 如果上面的方法没找到，尝试备用方法
            if not play_from_list:
                # 查找所有vodplay链接
                play_links = root.find_all('a', href=re.compile(r'/vodplay/'))
                if play_links:
                    episodes = []
                    for link in play_links:
                        ep_title = link.text.strip()
                        ep_url = link.get('href', '')
                        
                        if ep_url:
                            if ep_url.startswith('//'):
                                ep_url = 'https:' + ep_url
                            elif not ep_url.startswith('http'):
                                ep_url = self.host + ep_url if ep_url.startswith('/') else self.host + '/' + ep_url
                        
                        if ep_title and ep_url:
                            episodes.append(f"{ep_title}${ep_url}")
                    
                    if episodes:
                        play_from_list = ["播放源"]
                        play_url_list = ["#".join(episodes)]
            
            # 如果仍然没有找到，使用vod_id作为播放地址
            if not play_from_list:
                play_from_list = ["默认播放源"]
                play_url_list = [f"第1集${vod_id}"]
            
            # 构建结果
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": info_dict.get('年份', info_dict.get('年代', '')),
                "vod_actor": info_dict.get('主演', info_dict.get('演员', '')),
                "vod_director": info_dict.get('导演', ''),
                "vod_area": info_dict.get('地区', info_dict.get('国家/地区', '')),
                "vod_remarks": info_dict.get('备注', info_dict.get('更新', '')),
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }
            
            print(f"详情页解析完成: {vod_name}")
            print(f"播放源: {play_from_list}")
            print(f"播放地址数量: {len(play_url_list[0].split('#')) if play_url_list else 0}")
            
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
            # 搜索URL格式
            search_url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            
            print(f"搜索URL: {search_url}")
            rsp = self.fetch(search_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 搜索结果的视频项应该和分类页类似
            video_items = root.select('.index-area ul li')
            
            if not video_items:
                video_items = root.find_all('li', class_=re.compile(r'p[0-9]'))
            
            for item in video_items:
                try:
                    a = item.find('a', class_='link-hover')
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id:
                        if not vod_id.startswith('http'):
                            vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 标题
                    vod_name = ""
                    name_elem = a.find('p', class_='name')
                    if name_elem:
                        vod_name = name_elem.text.strip()
                    
                    if not vod_name:
                        vod_name = a.get('title', '')
                    
                    # 封面
                    vod_pic = ""
                    img = a.find('img')
                    if img:
                        vod_pic = img.get('src', '') or img.get('data-src', '')
                        if vod_pic:
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            elif vod_pic.startswith('/'):
                                vod_pic = self.host + vod_pic
                            elif not vod_pic.startswith('http'):
                                vod_pic = 'https:' + vod_pic if vod_pic.startswith('//') else vod_pic
                    
                    # 备注
                    vod_remarks = ""
                    remark_elem = a.find('p', class_='other')
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
            pagination = root.find('div', class_='page')
            if pagination:
                page_text = pagination.text.strip()
                match = re.search(r'当前\d+/(\d+)页', page_text)
                if match:
                    pagecount = int(match.group(1))
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 30,
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
            
            print(f"解析播放地址: {play_url}")
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
            
            # 3. 查找script中的播放地址
            if not video_url:
                script_tags = root.find_all('script')
                for script in script_tags:
                    if script.string:
                        # 尝试匹配m3u8或mp4地址
                        patterns = [
                            r'["\'](https?://[^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                            r'url:\s*["\']([^"\']+)["\']',
                            r'src:\s*["\']([^"\']+)["\']',
                            r'file:\s*["\']([^"\']+)["\']'
                        ]
                        for pattern in patterns:
                            matches = re.findall(pattern, script.string)
                            for match in matches:
                                url = match[0] if isinstance(match, tuple) else match
                                if self.isVideoFormat(url):
                                    video_url = url
                                    break
                            if video_url:
                                break
            
            if video_url and self.isVideoFormat(video_url):
                result["parse"] = 0
                result["url"] = video_url
                print(f"找到直接播放地址: {video_url}")
            else:
                # 如果找不到直接播放地址，让TVBox解析
                result["parse"] = 1
                result["url"] = play_url
                print(f"使用代理解析播放地址: {play_url}")
            
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