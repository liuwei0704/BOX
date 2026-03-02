# -*- coding: utf-8 -*-
import re
import json
import requests
from urllib.parse import urljoin, urlparse, parse_qs

class Spider:
    def getDependence(self): 
        return ['requests']
    
    def init(self, extend=""): 
        return {}
    
    def getName(self): 
        return "速剧"
    
    def homeContent(self, filter):
        classes = [
            {"type_id": "1", "type_name": "已完结"},
            {"type_id": "2", "type_name": "都市"},
            {"type_id": "3", "type_name": "甜宠"},
            {"type_id": "4", "type_name": "逆袭"},
            {"type_id": "5", "type_name": "穿越"},
            {"type_id": "6", "type_name": "玄幻"},
            {"type_id": "7", "type_name": "古装"},
            {"type_id": "8", "type_name": "搞笑"},
            {"type_id": "9", "type_name": "爱情"},
            {"type_id": "10", "type_name": "复仇"},
            {"type_id": "11", "type_name": "重生"},
            {"type_id": "12", "type_name": "豪门"},
            {"type_id": "13", "type_name": "奇幻"},
            {"type_id": "14", "type_name": "权谋"},
            {"type_id": "15", "type_name": "家庭"},
            {"type_id": "16", "type_name": "总裁"},
            {"type_id": "17", "type_name": "宫斗"}
        ]
        
        result = {"class": classes, "list": []}
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://suju.cc', headers=headers, timeout=10)
            html = response.text
            
            pattern = r'<a href="(/showview/[^"]+\.html)"[^>]*class="block cursor-pointer"[^>]*>(.*?)</a>'
            blocks = re.findall(pattern, html, re.DOTALL)
            
            for href, block in blocks[:30]:
                title_match = re.search(r'<div class="font-bold line-clamp-2">([^<]+)</div>', block)
                if not title_match:
                    continue
                title = title_match.group(1).strip()
                
                pic_match = re.search(r'data-lazy="([^"]+)"', block)
                pic = pic_match.group(1) if pic_match else ""
                if pic and not pic.startswith('http'):
                    pic = 'https://suju.cc' + pic
                
                status_match = re.search(r'<div class="p-1 bg-surface[^"]*"[^>]*>([^<]+)</div>', block)
                status = status_match.group(1).strip() if status_match else "短剧"
                
                vod_id = 'https://suju.cc' + href
                result["list"].append({
                    "vod_id": vod_id,
                    "vod_name": title[:50],
                    "vod_pic": pic,
                    "vod_remarks": status
                })
                    
        except Exception as e:
            print(f"homeContent error: {e}")
        
        return result
    
    def homeVideoContent(self):
        return self.homeContent(None)
    
    def categoryContent(self, tid, pg, filter, extend):
        result = {
            'page': pg,
            'pagecount': 50,
            'limit': 30,
            'total': 1500,
            'list': []
        }
        
        try:
            # 分类URL映射 - 基于首页导航栏的实际URL
            category_urls = {
                '1': '/shuku/full_J_0_0_2_0_{pg}.html',   # 已完结
                '2': '/shuku/full_J___0_KrA_{pg}.html',   # 都市
                '3': '/shuku/full_J___0_Jx_{pg}.html',    # 甜宠
                '4': '/shuku/full_J___0_vQ_{pg}.html',    # 逆袭
                '5': '/shuku/full_J___0_JM_{pg}.html',    # 穿越
                '6': '/shuku/full_J___0_JC_{pg}.html',    # 玄幻
                '7': '/shuku/full_J___0_Ktp_{pg}.html',   # 古装
                '8': '/shuku/full_J___0_Jx_{pg}.html',    # 搞笑
                '9': '/shuku/full_J___0_KXA_{pg}.html',   # 爱情
                '10': '/shuku/full_J___0_Kr9_{pg}.html',  # 复仇
                '11': '/shuku/full_J___0_KtN_{pg}.html',  # 重生
                '12': '/shuku/full_J___0_KrA_{pg}.html',  # 豪门
                '13': '/shuku/full_J___0_JC_{pg}.html',   # 奇幻
                '14': '/shuku/full_J___0_Kar_{pg}.html',  # 权谋
                '15': '/shuku/full_J___0_KBu_{pg}.html',  # 家庭
                '16': '/shuku/full_J___0_KXn_{pg}.html',  # 总裁
                '17': '/shuku/full_J___0_Ktp_{pg}.html',  # 宫斗
            }
            
            # 获取对应的分类URL
            url_pattern = category_urls.get(tid)
            if not url_pattern:
                # 如果没有对应的分类，返回空列表
                return result
            
            # 替换页码
            category_url = 'https://suju.cc' + url_pattern.replace('{pg}', str(pg))
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(category_url, headers=headers, timeout=10)
            html = response.text
            
            # 提取视频列表 - 使用与首页相同的提取逻辑
            pattern = r'<a href="(/showview/[^"]+\.html)"[^>]*class="block cursor-pointer"[^>]*>(.*?)</a>'
            blocks = re.findall(pattern, html, re.DOTALL)
            
            for href, block in blocks[:30]:
                title_match = re.search(r'<div class="font-bold line-clamp-2">([^<]+)</div>', block)
                if not title_match:
                    continue
                title = title_match.group(1).strip()
                
                pic_match = re.search(r'data-lazy="([^"]+)"', block)
                pic = pic_match.group(1) if pic_match else ""
                if pic and not pic.startswith('http'):
                    pic = 'https://suju.cc' + pic
                
                status_match = re.search(r'<div class="p-1 bg-surface[^"]*"[^>]*>([^<]+)</div>', block)
                status = status_match.group(1).strip() if status_match else "短剧"
                
                vod_id = 'https://suju.cc' + href
                result["list"].append({
                    "vod_id": vod_id,
                    "vod_name": title[:50],
                    "vod_pic": pic,
                    "vod_remarks": status
                })
                    
        except Exception as e:
            print(f"categoryContent error: {e}")
        
        return result
    
    def detailContent(self, ids):
        result = {"list": []}
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                vod_id = 'https://suju.cc' + vod_id
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(vod_id, headers=headers, timeout=10)
            html = response.text
            
            title_match = re.search(r'<h2 class="text-xl font-bold truncate">([^<]+)</h2>', html)
            if not title_match:
                title_match = re.search(r'<title>(.*?)</title>', html)
            title = title_match.group(1) if title_match else "未知标题"
            title = title.replace(' - 速剧', '').replace('速剧', '').strip()
            
            subtitle_match = re.search(r'<p class="text-sm text-primary">([^<]+)</p>', html)
            subtitle = subtitle_match.group(1).strip() if subtitle_match else ""
            
            pic_match = re.search(r'data-lazy="([^"]+)"', html)
            pic = pic_match.group(1) if pic_match else ""
            if pic and not pic.startswith('http'):
                pic = 'https://suju.cc' + pic
            
            desc_match = re.search(r'<p class="mt-2 opacity-80 text-sm line-clamp-2">([^<]+)</p>', html)
            desc = desc_match.group(1).strip() if desc_match else ""
            
            vid = vod_id.replace('https://suju.cc/showview/', '').replace('.html', '')
            
            line_matches = re.findall(r'<a href="(/play/[^"]+\?road=(\d+))"[^>]*>🎥 播放线路 (\d+)</a>', html)
            
            if line_matches:
                play_from = []
                play_urls = []
                line_matches.sort(key=lambda x: int(x[1]))
                
                for path, road_num, display_num in line_matches:
                    play_from.append(f"线路{display_num}")
                    episodes = []
                    for i in range(1, 81):
                        ep_url = f"https://suju.cc/play/{vid}/{i}?road={road_num}"
                        episodes.append(f"第{str(i).zfill(2)}集${ep_url}")
                    play_urls.append('#'.join(episodes))
                
                vod_play_from = "$$$".join(play_from)
                vod_play_url = "$$$".join(play_urls)
            else:
                vod_play_from = "速剧"
                episodes = []
                for i in range(1, 81):
                    ep_url = f"https://suju.cc/play/{vid}/{i}.html"
                    episodes.append(f"第{str(i).zfill(2)}集${ep_url}")
                vod_play_url = '#'.join(episodes)
            
            vod = {
                "vod_id": vod_id,
                "vod_name": title,
                "vod_sub": subtitle,
                "vod_pic": pic,
                "type_name": "短剧",
                "vod_content": desc,
                "vod_play_from": vod_play_from,
                "vod_play_url": vod_play_url
            }
            result["list"].append(vod)
        except Exception as e:
            print(f"detailContent error: {e}")
        
        return result
    
    def searchContent(self, key, quick):
        result = {"list": []}
        try:
            search_url = f'https://suju.cc/searchlist/{key}/1.html'
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(search_url, headers=headers, timeout=10)
            html = response.text
            
            pattern = r'<a href="(/showview/[^"]+\.html)"[^>]*class="block cursor-pointer"[^>]*>.*?<div class="font-bold line-clamp-2">([^<]+)</div>'
            items = re.findall(pattern, html, re.DOTALL)
            
            for href, title in items[:20]:
                title = title.strip()
                if key.lower() in title.lower():
                    vod_id = 'https://suju.cc' + href
                    result["list"].append({
                        "vod_id": vod_id,
                        "vod_name": title[:50],
                        "vod_pic": "",
                        "vod_remarks": ""
                    })
        except Exception as e:
            print(f"searchContent error: {e}")
        
        return result
    
    def playerContent(self, flag, id, vipFlags):
        result = {}
        try:
            if not id.startswith('http'):
                id = 'https://suju.cc' + id
            result = {"parse": 1, "url": id, "header": '{"User-Agent": "Mozilla/5.0"}'}
        except Exception as e:
            print(f"playerContent error: {e}")
        return result
    
    def isVideoFormat(self, url):
        return url.endswith(('.mp4', '.m3u8'))
    
    def localProxy(self, param):
        return None