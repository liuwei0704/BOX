# coding=utf-8
# !/usr/bin/python

"""

作者 春江墨雨 by DeepSeek
                    ====================LeMoN====================

"""

from Crypto.Util.Padding import unpad
from Crypto.Util.Padding import pad
from urllib.parse import unquote
from Crypto.Cipher import ARC4
from urllib.parse import quote
from base.spider import Spider
from Crypto.Cipher import AES
from datetime import datetime
from bs4 import BeautifulSoup
from base64 import b64decode
import urllib.request
import urllib.parse
import datetime
import binascii
import requests
import base64
import json
import time
import sys
import re
import os

sys.path.append('..')

xurl = "https://www.zchongli.com"

headerx = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.zchongli.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

class Spider(Spider):
    global xurl
    global headerx

    def getName(self):
        return "天堂短剧网"

    def init(self, extend):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def extract_middle_text(self, text, start_str, end_str, pl, start_index1: str = '', end_index2: str = ''):
        if pl == 3:
            plx = []
            while True:
                start_index = text.find(start_str)
                if start_index == -1:
                    break
                end_index = text.find(end_str, start_index + len(start_str))
                if end_index == -1:
                    break
                middle_text = text[start_index + len(start_str):end_index]
                plx.append(middle_text)
                text = text.replace(start_str + middle_text + end_str, '')
            if len(plx) > 0:
                purl = ''
                for i in range(len(plx)):
                    matches = re.findall(start_index1, plx[i])
                    output = ""
                    for match in matches:
                        match3 = re.search(r'(?:^|[^0-9])(\d+)(?:[^0-9]|$)', match[1])
                        if match3:
                            number = match3.group(1)
                        else:
                            number = 0
                        if 'http' not in match[0]:
                            output += f"#{match[1]}${number}{xurl}{match[0]}"
                        else:
                            output += f"#{match[1]}${number}{match[0]}"
                    output = output[1:]
                    purl = purl + output + "$$$"
                purl = purl[:-3]
                return purl
            else:
                return ""
        else:
            start_index = text.find(start_str)
            if start_index == -1:
                return ""
            end_index = text.find(end_str, start_index + len(start_str))
            if end_index == -1:
                return ""

        if pl == 0:
            middle_text = text[start_index + len(start_str):end_index]
            return middle_text.replace("\\", "")

        if pl == 1:
            middle_text = text[start_index + len(start_str):end_index]
            matches = re.findall(start_index1, middle_text)
            if matches:
                jg = ' '.join(matches)
                return jg

        if pl == 2:
            middle_text = text[start_index + len(start_str):end_index]
            matches = re.findall(start_index1, middle_text)
            if matches:
                new_list = [f'{item}' for item in matches]
                jg = '$$$'.join(new_list)
                return jg

    def homeContent(self, filter):
        """获取首页分类"""
        result = {"class": []}
        
        try:
            detail = requests.get(url=xurl, headers=headerx, timeout=10)
            detail.encoding = "utf-8"
            res = detail.text
            
            # 从顶部菜单中提取主要分类
            soup = BeautifulSoup(res, 'html.parser')
            
            # 查找顶部菜单
            nav_menu = soup.find('ul', class_='myui-header__menu')
            if nav_menu:
                menu_items = nav_menu.find_all('li', class_='visible-inline-lg')
                for item in menu_items:
                    a_tag = item.find('a')
                    if a_tag and a_tag.get('href'):
                        href = a_tag.get('href')
                        name = a_tag.text.strip()
                        # 跳过首页
                        if href != '/' and href.startswith('/show/'):
                            result["class"].append({
                                "type_id": href,
                                "type_name": name
                            })
            
            # 如果没有找到足够分类，添加一些默认分类
            if len(result["class"]) < 5:
                default_categories = [
                    {"type_id": "/show/1.html", "type_name": "电影"},
                    {"type_id": "/show/2.html", "type_name": "电视剧"},
                    {"type_id": "/show/3.html", "type_name": "短剧"},
                    {"type_id": "/show/4.html", "type_name": "动漫"},
                    {"type_id": "/show/5.html", "type_name": "综艺"},
                    {"type_id": "/show/19.html", "type_name": "爱情片"},
                    {"type_id": "/show/7.html", "type_name": "动作片"},
                    {"type_id": "/show/9.html", "type_name": "喜剧片"},
                    {"type_id": "/show/11.html", "type_name": "恐怖片"},
                    {"type_id": "/show/16.html", "type_name": "悬疑片"},
                ]
                result["class"] = default_categories
                
        except Exception as e:
            print(f"获取首页分类时出错: {e}")
            # 返回默认分类
            result["class"] = [
                {"type_id": "/show/1.html", "type_name": "电影"},
                {"type_id": "/show/2.html", "type_name": "电视剧"},
                {"type_id": "/show/3.html", "type_name": "短剧"},
                {"type_id": "/show/4.html", "type_name": "动漫"},
                {"type_id": "/show/5.html", "type_name": "综艺"},
            ]
        
        return result

    def homeVideoContent(self):
        return []

    def categoryContent(self, cid, pg, filter, ext):
        """获取分类内容"""
        result = {}
        videos = []
        
        try:
            page = int(pg) if pg else 1
            
            # 构建URL
            if cid.endswith('.html'):
                if page == 1:
                    url = cid
                else:
                    base_url = cid.replace('.html', '')
                    url = f"{base_url}/page/{page}.html"
            else:
                if page == 1:
                    url = f"{cid}.html"
                else:
                    url = f"{cid}/page/{page}.html"
            
            if not url.startswith('http'):
                url = xurl + url
            
            print(f"分类页URL: {url}")
            
            response = requests.get(url=url, headers=headerx, timeout=10)
            response.encoding = "utf-8"
            html = response.text
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找视频列表
            vodlist = soup.find('ul', class_='myui-vodlist')
            
            if vodlist:
                # 查找所有视频项
                items = vodlist.find_all('li', recursive=False)
                
                for item in items:
                    try:
                        # 查找视频盒子
                        box = item.find('div', class_='myui-vodlist__box')
                        if not box:
                            continue
                        
                        # 获取视频链接
                        link_tag = box.find('a', class_='myui-vodlist__thumb')
                        if not link_tag:
                            continue
                        
                        href = link_tag.get('href', '')
                        title = link_tag.get('title', '')
                        
                        if not href or not title:
                            continue
                        
                        # 获取封面图片
                        img_src = link_tag.get('data-original', '')
                        if not img_src:
                            img_tag = link_tag.find('img')
                            if img_tag:
                                img_src = img_tag.get('data-original', img_tag.get('src', ''))
                        
                        # 获取标签和状态
                        tags = []
                        status = ""
                        
                        # 查找标签
                        tag_spans = link_tag.find_all('span', class_='pic-tag')
                        for tag_span in tag_spans:
                            tags.append(tag_span.text.strip())
                        
                        # 查找状态
                        status_span = link_tag.find('span', class_='pic-text')
                        if status_span:
                            status = status_span.text.strip()
                        
                        # 获取描述
                        detail_div = box.find('div', class_='myui-vodlist__detail')
                        desc = ""
                        if detail_div:
                            desc_p = detail_div.find('p', class_='text')
                            if desc_p:
                                desc = desc_p.text.strip()
                        
                        # 构建视频信息
                        vod_id = href
                        if not vod_id.startswith('http'):
                            vod_id = xurl + vod_id
                        
                        # 构建备注
                        remarks_parts = []
                        if tags:
                            remarks_parts.append(' '.join(tags))
                        if status:
                            remarks_parts.append(status)
                        remarks = ' | '.join(remarks_parts) if remarks_parts else "正片"
                        
                        video = {
                            "vod_id": vod_id,
                            "vod_name": title,
                            "vod_pic": img_src,
                            "vod_remarks": remarks
                        }
                        
                        videos.append(video)
                        
                    except Exception as e:
                        print(f"解析视频项时出错: {e}")
                        continue
            
            # 获取分页信息
            total = 999999
            limit = len(videos) if videos else 90
            
            # 尝试从页面获取总页数
            pagecount = 9999
            pagination = soup.find('ul', class_='pagination')
            if pagination:
                page_items = pagination.find_all('li')
                if page_items:
                    last_page = page_items[-2].text if len(page_items) > 1 else '1'
                    if last_page.isdigit():
                        pagecount = int(last_page)
            
            result = {
                'list': videos,
                'page': page,
                'pagecount': pagecount,
                'limit': limit,
                'total': total
            }
            
        except Exception as e:
            print(f"获取分类内容时出错: {e}")
            import traceback
            traceback.print_exc()
            result = {
                'list': [],
                'page': 1,
                'pagecount': 1,
                'limit': 0,
                'total': 0
            }
        
        return result

    def detailContent(self, ids):
        """获取详情内容"""
        result = {}
        videos = []
        
        try:
            did = ids[0]
            if not did.startswith('http'):
                did = xurl + did
            
            print(f"详情页URL: {did}")
            
            response = requests.get(url=did, headers=headerx, timeout=10)
            response.encoding = "utf-8"
            html = response.text
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取基本信息
            title = ""
            content = ""
            year = ""
            area = ""
            actor = ""
            director = ""
            vod_pic = ""
            vod_remarks = ""
            score = ""
            
            # 1. 提取标题
            title_tag = soup.find('h1', class_='title')
            if title_tag:
                title = title_tag.text.strip()
            
            # 2. 提取封面图片
            img_tag = soup.find('img', class_='lazyload')
            if img_tag:
                vod_pic = img_tag.get('data-original', '')
                if not vod_pic:
                    vod_pic = img_tag.get('src', '')
            
            # 3. 提取详情信息
            detail_div = soup.find('div', class_='myui-content__detail')
            if detail_div:
                # 提取评分
                score_span = detail_div.find('span', class_='branch')
                if score_span:
                    score = score_span.text.strip()
                
                # 提取分类
                type_link = detail_div.find('a', href=re.compile(r'/show/\d+\.html'))
                if type_link:
                    vod_remarks = type_link.text.strip()
                
                # 使用正则提取各种信息
                detail_text = str(detail_div)
                
                # 提取年份
                year_match = re.search(r'年份[^>]*?>[^>]*?>([^<]+)', detail_text)
                if year_match:
                    year = year_match.group(1).strip()
                
                # 提取地区
                area_match = re.search(r'地区[^>]*?>[^>]*?>([^<]+)', detail_text)
                if area_match:
                    area = area_match.group(1).strip()
                
                # 提取导演
                director_match = re.search(r'导演[^>]*?>([^<]+)', detail_text)
                if director_match:
                    director = director_match.group(1).strip()
                
                # 提取演员
                actor_match = re.search(r'主演[^>]*?>([^<]+)', detail_text)
                if actor_match:
                    actor = actor_match.group(1).strip()
            
            # 4. 提取简介
            content_div = soup.find('div', id='desc')
            if not content_div:
                content_div = soup.find('div', class_='content')
            
            if content_div:
                sketch_span = content_div.find('span', class_='sketch')
                if sketch_span:
                    content = sketch_span.text.strip()
                else:
                    content = content_div.text.strip()
            
            # 5. 提取播放列表
            play_url = ""
            play_from = []
            
            # 查找播放地址区域
            play_section = soup.find('div', class_='tab-content')
            if play_section:
                # 查找所有线路
                tab_panes = play_section.find_all('div', class_='tab-pane')
                
                for pane in tab_panes:
                    # 获取线路名称（从对应的tab标签获取）
                    pane_id = pane.get('id', '')
                    if pane_id:
                        tab_link = soup.find('a', href=f'#{pane_id}')
                        if tab_link:
                            line_name = tab_link.text.strip()
                            play_from.append(line_name)
                    
                    # 查找该线路下的播放集数
                    play_items = pane.find_all('li')
                    for item in play_items:
                        a_tag = item.find('a')
                        if a_tag:
                            play_name = a_tag.text.strip()
                            play_href = a_tag.get('href', '')
                            
                            if play_href:
                                if not play_href.startswith('http'):
                                    play_href = xurl + play_href
                                
                                # 如果有线路名称，添加到播放名
                                if play_from:
                                    current_line = play_from[-1] if play_from else "线路1"
                                    full_name = f"{current_line}-{play_name}"
                                else:
                                    full_name = play_name
                                
                                play_url += f"{full_name}${play_href}#"
            
            if play_url:
                play_url = play_url.rstrip('#')
            
            # 如果没有找到播放列表，尝试查找免费播放按钮
            if not play_url:
                free_play = soup.find('a', class_='btn-warm')
                if free_play and '免费播放' in free_play.text:
                    play_href = free_play.get('href', '')
                    if play_href:
                        if not play_href.startswith('http'):
                            play_href = xurl + play_href
                        play_url = f"正片${play_href}"
                        play_from = ["免费播放"]
            
            # 构建播放来源字符串
            if play_from:
                play_from_str = "$$$".join(play_from)
            else:
                play_from_str = "天堂短剧"
            
            # 构建视频信息
            video_info = {
                "vod_id": did,
                "vod_name": title,
                "vod_pic": vod_pic,
                "vod_year": year,
                "vod_area": area,
                "vod_actor": actor,
                "vod_director": director,
                "vod_content": content,
                "vod_play_from": play_from_str,
                "vod_play_url": play_url
            }
            
            # 添加评分到备注
            if score:
                if vod_remarks:
                    video_info["vod_remarks"] = f"{vod_remarks} | {score}分"
                else:
                    video_info["vod_remarks"] = f"{score}分"
            elif vod_remarks:
                video_info["vod_remarks"] = vod_remarks
            
            videos.append(video_info)
            
        except Exception as e:
            print(f"获取详情内容时出错: {e}")
            import traceback
            traceback.print_exc()
            videos.append({
                "vod_id": did,
                "vod_name": "获取失败",
                "vod_content": str(e)
            })
        
        result['list'] = videos
        return result

    def playerContent(self, flag, id, vipFlags):
        """获取播放地址 - 从播放页提取m3u8地址"""
        result = {}
        
        try:
            print(f"播放页URL: {id}")
            
            # 访问播放页
            response = requests.get(url=id, headers=headerx, timeout=10)
            response.encoding = "utf-8"
            html = response.text
            
            # 调试：保存HTML用于分析
            # with open('play_page.html', 'w', encoding='utf-8') as f:
            #     f.write(html)
            
            # 方法1: 直接查找JavaScript中的player变量
            play_url = ""
            
            # 查找 player_aaaa 变量
            player_pattern = r'var\s+player_aaaa\s*=\s*({[^}]+})'
            player_match = re.search(player_pattern, html)
            
            if player_match:
                try:
                    player_data = player_match.group(1)
                    # 将JavaScript对象转换为Python字典
                    # 替换一些JS格式
                    player_data = player_data.replace('\\/', '/')
                    
                    # 使用正则提取关键字段
                    url_match = re.search(r'"url"\s*:\s*"([^"]+)"', player_data)
                    if url_match:
                        play_url = url_match.group(1)
                        # 解码Unicode转义序列
                        play_url = play_url.encode('utf-8').decode('unicode_escape')
                except:
                    pass
            
            # 方法2: 如果没有找到，尝试查找其他player变量
            if not play_url:
                alt_patterns = [
                    r'var\s+player_\w+\s*=\s*{[^}]+"url"\s*:\s*"([^"]+)"',
                    r'player\.url\s*=\s*["\']([^"\']+)["\']',
                    r'url:\s*["\']([^"\']+)["\']',
                    r'var\s+url\s*=\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in alt_patterns:
                    matches = re.findall(pattern, html)
                    if matches:
                        play_url = matches[0]
                        break
            
            # 方法3: 查找m3u8链接
            if not play_url:
                m3u8_pattern = r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']'
                matches = re.findall(m3u8_pattern, html)
                if matches:
                    play_url = matches[0]
            
            # 方法4: 查找iframe
            if not play_url:
                iframe_pattern = r'<iframe[^>]*src="([^"]*)"[^>]*>'
                iframe_matches = re.findall(iframe_pattern, html)
                if iframe_matches:
                    iframe_src = iframe_matches[0]
                    if not iframe_src.startswith('http'):
                        iframe_src = xurl + iframe_src
                    
                    # 访问iframe获取播放地址
                    try:
                        iframe_response = requests.get(url=iframe_src, headers=headerx, timeout=5)
                        iframe_response.encoding = "utf-8"
                        iframe_html = iframe_response.text
                        
                        # 在iframe中查找播放地址
                        iframe_url_patterns = [
                            r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                            r'url:\s*["\']([^"\']+)["\']',
                            r'file:\s*["\']([^"\']+)["\']'
                        ]
                        
                        for pattern in iframe_url_patterns:
                            matches = re.findall(pattern, iframe_html)
                            if matches:
                                play_url = matches[0]
                                break
                    except:
                        pass
            
            # 清理URL
            if play_url:
                # 移除转义字符
                play_url = play_url.replace('\\/', '/').replace('\\"', '"')
                # 确保URL完整
                if play_url.startswith('//'):
                    play_url = 'https:' + play_url
                elif play_url.startswith('/'):
                    play_url = xurl + play_url
            
            print(f"提取到的播放地址: {play_url}")
            
            # 如果还是没有找到播放地址，使用原始URL
            if not play_url:
                play_url = id
            
            result["parse"] = 0  # 0表示不解析，直接播放
            result["playUrl"] = ''
            result["url"] = play_url
            result["header"] = {
                'User-Agent': headerx['User-Agent'],
                'Referer': xurl + '/',
                'Origin': xurl
            }
            
            # 添加调试信息
            result["header"]["X-Debug-URL"] = id
            
        except Exception as e:
            print(f"获取播放地址时出错: {e}")
            import traceback
            traceback.print_exc()
            result["parse"] = 0
            result["playUrl"] = ''
            result["url"] = ''
            result["header"] = headerx
        
        return result

    def searchContentPage(self, key, quick, pg):
        """搜索内容（带分页）"""
        result = {}
        videos = []
        
        try:
            page = int(pg) if pg else 1
            
            # 构建搜索URL
            if page == 1:
                search_url = f"{xurl}/search.html?wd={urllib.parse.quote(key)}"
            else:
                search_url = f"{xurl}/search/page/{page}.html?wd={urllib.parse.quote(key)}"
            
            print(f"搜索URL: {search_url}")
            
            response = requests.get(url=search_url, headers=headerx, timeout=10)
            response.encoding = "utf-8"
            html = response.text
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找视频列表
            vodlist = soup.find('ul', class_='myui-vodlist')
            
            if vodlist:
                # 查找所有视频项
                items = vodlist.find_all('li', recursive=False)
                
                for item in items:
                    try:
                        box = item.find('div', class_='myui-vodlist__box')
                        if not box:
                            continue
                        
                        # 获取视频链接
                        link_tag = box.find('a', class_='myui-vodlist__thumb')
                        if not link_tag:
                            continue
                        
                        href = link_tag.get('href', '')
                        title = link_tag.get('title', '')
                        
                        if not href or not title:
                            continue
                        
                        # 获取封面图片
                        img_src = link_tag.get('data-original', '')
                        if not img_src:
                            img_tag = link_tag.find('img')
                            if img_tag:
                                img_src = img_tag.get('data-original', img_tag.get('src', ''))
                        
                        # 获取标签和状态
                        tags = []
                        status = ""
                        
                        tag_spans = link_tag.find_all('span', class_='pic-tag')
                        for tag_span in tag_spans:
                            tags.append(tag_span.text.strip())
                        
                        status_span = link_tag.find('span', class_='pic-text')
                        if status_span:
                            status = status_span.text.strip()
                        
                        # 构建视频信息
                        vod_id = href
                        if not vod_id.startswith('http'):
                            vod_id = xurl + vod_id
                        
                        # 构建备注
                        remarks_parts = []
                        if tags:
                            remarks_parts.append(' '.join(tags))
                        if status:
                            remarks_parts.append(status)
                        remarks = ' | '.join(remarks_parts) if remarks_parts else "正片"
                        
                        video = {
                            "vod_id": vod_id,
                            "vod_name": title,
                            "vod_pic": img_src,
                            "vod_remarks": remarks
                        }
                        
                        videos.append(video)
                        
                    except Exception as e:
                        print(f"解析搜索结果项时出错: {e}")
                        continue
            
            # 获取分页信息
            total = 999999
            limit = len(videos) if videos else 90
            
            # 尝试获取总页数
            pagecount = 9999
            pagination = soup.find('ul', class_='pagination')
            if pagination:
                page_items = pagination.find_all('li')
                if page_items:
                    last_page = page_items[-2].text if len(page_items) > 1 else '1'
                    if last_page.isdigit():
                        pagecount = int(last_page)
            
            result = {
                'list': videos,
                'page': page,
                'pagecount': pagecount,
                'limit': limit,
                'total': total
            }
            
        except Exception as e:
            print(f"搜索时出错: {e}")
            result = {
                'list': [],
                'page': 1,
                'pagecount': 1,
                'limit': 0,
                'total': 0
            }
        
        return result

    def searchContent(self, key, quick, pg="1"):
        return self.searchContentPage(key, quick, pg)

    def localProxy(self, params):
        if params['type'] == "m3u8":
            return self.proxyM3u8(params)
        elif params['type'] == "media":
            return self.proxyMedia(params)
        elif params['type'] == "ts":
            return self.proxyTs(params)
        return None