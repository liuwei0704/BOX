# coding=utf-8
import sys
import os
import re
import json
import urllib.parse
import base64
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    def getName(self):
        return "桃子影视"
    
    def init(self, extend=""):
        # 使用正确的域名
        self.host = "https://www.taozi008.com"
        print(f"桃子影视爬虫初始化: {self.host}")
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
    
    def homeContent(self, filter):
        """返回分类列表"""
        result = {}
        classes = [
            {"type_name": "电影", "type_id": "229"},
            {"type_name": "电视剧", "type_id": "230"},
            {"type_name": "综艺", "type_id": "231"},
            {"type_name": "动漫", "type_id": "232"}
        ]
        result["class"] = classes
        return result
    
    def homeVideoContent(self):
        """首页推荐视频 - 简化版，直接返回空"""
        return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类页面内容"""
        try:
            # 构建分类URL
            url = f"{self.host}/vod/index.html?type_id={tid}"
            
            # 添加分页
            if int(pg) > 1:
                url += f"&page={pg}"
            
            print(f"正在抓取分类页面: tid={tid}, page={pg}, url={url}")
            rsp = self.fetch(url, headers=self.header())
            
            # 检查响应
            if rsp.status_code != 200:
                print(f"请求失败，状态码: {rsp.status_code}")
                return self._get_empty_data(pg)
            
            # 解析HTML
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 查找视频列表项
            items = root.select('.lists.lists-filter .lists-content ul li, .lists.lists-thumb-top .lists-content ul li')
            
            if not items:
                print("未找到视频列表，HTML结构可能已变化")
                return self._get_empty_data(pg)
            
            for idx, item in enumerate(items[:20]):  # 限制最多20个
                try:
                    # 查找链接
                    a = item.find('a', class_='thumbnail')
                    if not a:
                        continue
                    
                    # 获取视频链接
                    href = a.get('href', '')
                    if not href:
                        continue
                    
                    vod_id = self.host + href if href.startswith('/') else href
                    
                    # 获取标题
                    vod_name = ""
                    h2 = item.find('h2')
                    if h2:
                        vod_name = h2.text.strip()
                    
                    if not vod_name:
                        continue
                    
                    # 获取封面图
                    vod_pic = ""
                    img = a.find('img')
                    if img and 'src' in img.attrs:
                        vod_pic = img['src']
                        if vod_pic.startswith('//'):
                            vod_pic = 'https:' + vod_pic
                        elif vod_pic.startswith('/'):
                            vod_pic = self.host + vod_pic
                        elif not vod_pic.startswith('http'):
                            vod_pic = self.host + '/' + vod_pic
                    
                    # 获取备注信息
                    vod_remarks = []
                    
                    # 更新状态
                    note_elem = a.find(class_='note')
                    if note_elem:
                        vod_remarks.append(note_elem.text.strip())
                    
                    # 年份和地区
                    countrie_elem = a.find(class_='countrie')
                    if countrie_elem:
                        vod_remarks.append(countrie_elem.text.strip().replace('\n', ' '))
                    
                    # 评分
                    rate_elem = item.find(class_='rate')
                    if rate_elem:
                        vod_remarks.append(f"评分:{rate_elem.text.strip()}")
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": " | ".join(vod_remarks) if vod_remarks else ""
                    })
                    
                except Exception as e:
                    continue
            
            # 获取总页数
            pagecount = int(pg)
            pagination = root.find('ul', class_='myci-page')
            if pagination:
                last_page = pagination.find('a', string='尾页')
                if last_page:
                    href = last_page.get('href', '')
                    if href:
                        match = re.search(r'page=(\d+)', href)
                        if match:
                            try:
                                pagecount = int(match.group(1))
                            except:
                                pass
            
            print(f"成功抓取 {len(videos)} 个视频，当前页: {pg}, 总页数: {pagecount}")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": max(pagecount, int(pg)),
                "limit": 20,
                "total": len(videos) * max(pagecount, 1)
            }
            
        except Exception as e:
            print(f"分类页面抓取出错: {str(e)}")
            return self._get_empty_data(pg)
    
    def _get_empty_data(self, pg):
        """返回空数据"""
        return {
            "list": [],
            "page": int(pg),
            "pagecount": int(pg),
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
            
            print(f"正在获取详情页: {url}")
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 获取标题
            vod_name = "未知"
            title_elem = root.find('h1', class_='product-title')
            if title_elem:
                vod_name = title_elem.text.strip()
            else:
                title_elem = root.find('h1')
                if title_elem:
                    vod_name = title_elem.text.strip()
            
            # 获取封面
            vod_pic = ""
            img_selectors = ['img.thumb', 'img.thumb.detail-img', 'img.cover', '.thumbnail img']
            for selector in img_selectors:
                img_elem = root.select_one(selector)
                if img_elem and 'src' in img_elem.attrs:
                    vod_pic = img_elem['src']
                    break
            
            if vod_pic:
                if vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
                elif vod_pic.startswith('/'):
                    vod_pic = self.host + vod_pic
                elif not vod_pic.startswith('http'):
                    vod_pic = self.host + '/' + vod_pic
            
            # 获取年份
            vod_year = ""
            year_match = re.search(r'\((\d{4})\)', vod_name)
            if year_match:
                vod_year = year_match.group(1)
            
            # 获取导演
            vod_director = ""
            director_elem = root.find('div', class_='product-excerpt', string=re.compile('导演'))
            if director_elem:
                director_text = director_elem.get_text(strip=True).replace('导演：', '')
                vod_director = director_text
            
            # 获取演员
            vod_actor = ""
            actor_elem = root.find('div', class_='product-excerpt', string=re.compile('主演'))
            if actor_elem:
                actor_text = actor_elem.get_text(strip=True).replace('主演：', '')
                vod_actor = actor_text
            
            # 获取地区
            vod_area = ""
            area_elem = root.find('div', class_='product-excerpt', string=re.compile('制片国家/地区'))
            if area_elem:
                area_text = area_elem.get_text(strip=True).replace('制片国家/地区：', '')
                vod_area = area_text.strip()
            
            # 获取描述
            vod_content = ""
            desc_elem = root.find('div', class_='product-excerpt', string=re.compile('剧情简介'))
            if desc_elem:
                # 获取父元素下的所有文本
                desc_container = desc_elem.parent
                if desc_container:
                    # 找到剧情简介后面的span标签内容
                    span_elem = desc_container.find('span')
                    if span_elem:
                        vod_content = span_elem.get_text(strip=True)
            
            if not vod_content:
                # 备用方法：从meta description获取
                meta_desc = root.find('meta', {'name': 'description'})
                if meta_desc and 'content' in meta_desc.attrs:
                    vod_content = meta_desc['content']
            
            # 解析播放列表
            play_from_list = ["线路1"]
            
            # 获取剧集列表
            episode_items = root.select('.playEpisodes li a')
            episodes = []
            
            if episode_items:
                for item in episode_items:
                    episode_name = item.text.strip()
                    episode_url = item.get('href', '')
                    if episode_url:
                        if not episode_url.startswith('http'):
                            episode_url = self.host + episode_url if episode_url.startswith('/') else episode_url
                        episodes.append(f"{episode_name}${episode_url}")
            
            # 如果没有解析到剧集，使用详情页链接
            if not episodes:
                episodes.append(f"第1集${url}")
            
            play_url_list = ["#".join(episodes)]
            
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": vod_year,
                "vod_actor": vod_actor,
                "vod_director": vod_director,
                "vod_area": vod_area,
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }
            
            print(f"详情页解析完成: {vod_name}, 共{len(episodes)}集")
            return {"list": [video]}
            
        except Exception as e:
            print(f"详情页获取失败: {str(e)}")
            # 返回基本的详情信息
            video = {
                "vod_id": ids[0],
                "vod_name": "视频详情",
                "vod_pic": "",
                "vod_content": "详情加载中...",
                "vod_play_from": "默认",
                "vod_play_url": f"第1集${ids[0]}"
            }
            return {"list": [video]}
    
    def searchContent(self, key, quick, pg=1):
        """搜索功能 - 已修复"""
        try:
            encoded_key = urllib.parse.quote(key)
            
            # 注意：搜索结果页面实际上是从 /public/auto/search1.html 获取的
            # 从HTML可以看到，搜索结果是通过Ajax加载到这个地址
            url = f"{self.host}/public/auto/search1.html?keyword={encoded_key}"
            
            if int(pg) > 1:
                url += f"&page={pg}"
            
            print(f"正在搜索: {key}, 第{pg}页, 搜索URL: {url}")
            rsp = self.fetch(url, headers=self.header())
            
            # 检查响应
            if rsp.status_code != 200:
                print(f"搜索请求失败，状态码: {rsp.status_code}")
                # 尝试备用方法：直接访问搜索页面
                url = f"{self.host}/search/index.html?keyword={encoded_key}"
                if int(pg) > 1:
                    url += f"&page={pg}"
                print(f"尝试备用搜索URL: {url}")
                rsp = self.fetch(url, headers=self.header())
                if rsp.status_code != 200:
                    return {"list": []}
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 检查是否有搜索结果
            no_result = root.find('p', string=re.compile('未搜索到相关内容'))
            if no_result:
                print(f"未搜索到相关内容: {key}")
                return {"list": []}
            
            # 尝试多种选择器来获取搜索结果项
            selectors = [
                '.lists.lists-filter .lists-content ul li',
                '.lists.lists-thumb-top .lists-content ul li',
                '.lists-content ul li',
                '.lists ul li',
                '.lists li'
            ]
            
            items = None
            for selector in selectors:
                items = root.select(selector)
                if items:
                    print(f"使用选择器 '{selector}' 找到 {len(items)} 个结果项")
                    break
            
            if not items:
                # 尝试更通用的选择器
                items = root.find_all('li')
                print(f"使用通用选择器找到 {len(items)} 个li元素")
            
            for item in items:
                try:
                    # 查找链接和标题
                    a = None
                    
                    # 尝试多种方式查找链接
                    link_selectors = ['a.thumbnail', 'a', '.thumbnail a']
                    for selector in link_selectors:
                        a_element = item.select_one(selector)
                        if a_element:
                            a = a_element
                            break
                    
                    if not a:
                        # 直接查找href属性
                        a = item.find('a', href=True)
                    
                    if not a:
                        continue
                    
                    href = a.get('href', '')
                    if not href:
                        continue
                    
                    vod_id = self.host + href if href.startswith('/') else href
                    
                    # 获取标题
                    vod_name = ""
                    
                    # 尝试多种方式获取标题
                    h2 = item.find('h2')
                    if h2:
                        vod_name = h2.text.strip()
                    
                    if not vod_name:
                        # 尝试从a标签获取title属性
                        vod_name = a.get('title', '')
                    
                    if not vod_name:
                        # 从a标签的文本内容获取
                        vod_name = a.text.strip()
                    
                    if not vod_name:
                        continue
                    
                    # 清理标题
                    vod_name = re.sub(r'\s+', ' ', vod_name).strip()
                    
                    # 获取封面
                    vod_pic = ""
                    img = a.find('img')
                    if img and 'src' in img.attrs:
                        vod_pic = img['src']
                        if vod_pic.startswith('//'):
                            vod_pic = 'https:' + vod_pic
                        elif vod_pic.startswith('/'):
                            vod_pic = self.host + vod_pic
                        elif not vod_pic.startswith('http'):
                            vod_pic = self.host + '/' + vod_pic
                    
                    # 获取备注
                    vod_remarks = ""
                    note_elem = a.find(class_='note')
                    if note_elem:
                        vod_remarks = note_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                    
                except Exception as e:
                    print(f"解析搜索结果项时出错: {str(e)}")
                    continue
            
            print(f"搜索到 {len(videos)} 个结果")
            
            # 尝试获取总页数
            pagecount = 1
            pagination = root.find('ul', class_='myci-page')
            if pagination:
                last_page = pagination.find('a', string='尾页')
                if last_page:
                    href = last_page.get('href', '')
                    if href:
                        match = re.search(r'page=(\d+)', href)
                        if match:
                            try:
                                pagecount = int(match.group(1))
                            except:
                                pass
                else:
                    # 尝试获取所有页码链接
                    page_links = pagination.find_all('a')
                    page_numbers = []
                    for link in page_links:
                        text = link.text.strip()
                        if text.isdigit():
                            page_numbers.append(int(text))
                    if page_numbers:
                        pagecount = max(page_numbers)
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": max(pagecount, int(pg)),
                "limit": 20,
                "total": len(videos)
            }
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"list": []}
    
    def playerContent(self, flag, id, vipFlags):
        """解析播放地址 - 改进版本"""
        try:
            print(f"正在解析播放地址: {id}")
            
            # 获取播放页面内容
            rsp = self.fetch(id, headers=self.header())
            html_content = rsp.text
                        
            # 查找所有可能的base64编码字符串
            m3u8_url = ""
            
            # 方法1：查找特定的base64模式
            base64_patterns = [
                r'"file":"([A-Za-z0-9+/=]{100,})"',
                r'file["\']?\s*:\s*["\']([A-Za-z0-9+/=]{100,})["\']',
                r'["\']([A-Za-z0-9+/=]{100,})["\']'
            ]
            
            for pattern in base64_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    try:
                        # 尝试去掉前3个字符后解码
                        if len(match) > 3:
                            # 检查是否是已知的前缀（KhY, XPQ等）
                            if match.startswith(('KhY', 'XPQ', 'd4g', 'yYQ', 'frX', '7eR', 'U0j', '898', 'oLX', 'jwR')):
                                encrypted = match[3:]
                            else:
                                encrypted = match
                            
                            # base64解码
                            decoded_bytes = base64.b64decode(encrypted)
                            decoded_str = decoded_bytes.decode('utf-8')
                            
                            # URL解码
                            m3u8_url = urllib.parse.unquote(decoded_str)
                            
                            # 验证是否是有效的m3u8地址
                            if 'm3u8' in m3u8_url.lower() and m3u8_url.startswith('http'):
                                print(f"成功解析m3u8地址: {m3u8_url[:100]}...")
                                break
                    except Exception as e:
                        continue
                if m3u8_url:
                    break
            
            # 方法2：如果没找到，尝试直接查找m3u8
            if not m3u8_url:
                m3u8_pattern = r'https?://[^\s"\']+\.m3u8[^\s"\']*'
                m3u8_matches = re.findall(m3u8_pattern, html_content, re.IGNORECASE)
                if m3u8_matches:
                    m3u8_url = m3u8_matches[0]
                    print(f"直接找到m3u8地址: {m3u8_url[:100]}...")
            
            if m3u8_url:
                # 确保URL是完整的
                if m3u8_url.startswith('//'):
                    m3u8_url = 'https:' + m3u8_url
                
                # 清理URL
                m3u8_url = m3u8_url.strip()
                if m3u8_url.endswith('"') or m3u8_url.endswith("'"):
                    m3u8_url = m3u8_url[:-1]
                if m3u8_url.startswith('"') or m3u8_url.startswith("'"):
                    m3u8_url = m3u8_url[1:]
                
                # 设置headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': id,
                    'Origin': 'https://www.taozi008.com'
                }
                
                result = {
                    "parse": 0,  # 0表示直接播放
                    "url": m3u8_url,
                    "header": json.dumps(headers)  # 转换为JSON字符串
                }
                print(f"返回m3u8地址: {m3u8_url[:200]}...")
                return result
            else:
                print("未找到m3u8地址，返回原始链接让TVBox解析")
                # 如果找不到m3u8，返回原始链接让TVBox解析
                headers = self.header()
                headers['Referer'] = id
                
                result = {
                    "parse": 1,  # 1表示让TVBox解析
                    "url": id,
                    "header": json.dumps(headers)
                }
                return result
                
        except Exception as e:
            print(f"播放地址解析失败: {str(e)}")
            # 失败时返回原链接让TVBox处理
            headers = self.header()
            headers['Referer'] = id
            
            result = {
                "parse": 1,  # 1表示让TVBox解析
                "url": id,
                "header": json.dumps(headers)
            }
            return result
    
    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        video_formats = ['.m3u8', '.mp4', '.avi', '.mkv', '.flv', '.ts', '.webm']
        return any(fmt in url.lower() for fmt in video_formats)
    
    def localProxy(self, params):
        """本地代理"""
        return [200, "video/MP2T", ""]