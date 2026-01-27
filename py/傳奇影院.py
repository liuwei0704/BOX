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
        return "传奇影院"
    
    def init(self, extend=""):
        self.host = "https://cqvod.com"
        pass
    
    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }
    
    def homeContent(self, filter):
        result = {}
        classes = [
            {"type_name": "电影", "type_id": "dianying"},
            {"type_name": "电视剧", "type_id": "dianshiju"},
            {"type_name": "综艺", "type_id": "zongyi"},
            {"type_name": "动漫", "type_id": "dongman"},
            {"type_name": "短剧", "type_id": "duanju"}
        ]
        result["class"] = classes
        return result
    
    def homeVideoContent(self):
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            items = root.select('.module-item')
            
            for item in items[:20]:
                try:
                    a = item.find('a', href=True)
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    vod_name = a.get('title', '')
                    if not vod_name:
                        title_elem = item.find('.module-item-title')
                        if title_elem:
                            vod_name = title_elem.text.strip()
                    
                    vod_pic = ""
                    img = item.find('img')
                    if img:
                        vod_pic = img.get('data-src', img.get('src', ''))
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = self.host + vod_pic if vod_pic.startswith('/') else vod_pic
                    
                    vod_remarks = ""
                    remark_elem = item.find('.video-class')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
                    year_type = ""
                    type_elem = item.find('.module-item-content')
                    if type_elem:
                        year_type = type_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks,
                        "vod_year_type": year_type
                    })
                except Exception:
                    continue
            
            return {"list": videos}
        except Exception:
            return {"list": []}
    
    def categoryContent(self, tid, pg, filter, extend):
        try:
            if int(pg) > 1:
                url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            else:
                url = f"{self.host}/vodshow/{tid}-----------.html"
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            items = root.select('.module-item')
            
            for item in items:
                try:
                    a = item.find('a', href=True)
                    if not a:
                        continue
                    
                    vod_id = a.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    vod_name = a.get('title', '')
                    if not vod_name:
                        title_elem = item.find('.module-item-title')
                        if title_elem:
                            vod_name = title_elem.text.strip()
                    
                    vod_pic = ""
                    img = item.find('img')
                    if img:
                        vod_pic = img.get('data-src', img.get('src', ''))
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = self.host + vod_pic if vod_pic.startswith('/') else vod_pic
                    
                    vod_remarks = ""
                    remark_elem = item.find('.video-class')
                    if remark_elem:
                        vod_remarks = remark_elem.text.strip()
                    
                    year_type = ""
                    content_elem = item.find('.module-item-content')
                    if content_elem:
                        year_type = content_elem.text.strip()
                    
                    vod_score = ""
                    score_elem = item.find('.pingfen')
                    if score_elem:
                        vod_score = score_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks,
                        "vod_score": vod_score,
                        "vod_info": year_type
                    })
                except Exception:
                    continue
            
            pagecount = 1
            pagination = root.find('div', id='page')
            if pagination:
                last_page = pagination.find('a', href=re.compile(r'--------\d+---\.html'))
                if last_page:
                    href = last_page.get('href', '')
                    match = re.search(r'--------(\d+)---\.html', href)
                    if match:
                        pagecount = int(match.group(1))
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount if pagecount > 0 else 1,
                "limit": 20,
                "total": len(videos) * pagecount
            }
        except Exception:
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }
    
    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                url = self.host + vod_id if vod_id.startswith('/') else self.host + '/' + vod_id
            else:
                url = vod_id
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            meta_actor = root.find('meta', {'property': 'og:video:actor'})
            meta_director = root.find('meta', {'property': 'og:video:director'})
            meta_year = root.find('meta', {'property': 'og:video:release_date'})
            meta_area = root.find('meta', {'property': 'og:video:area'})
            meta_type = root.find('meta', {'property': 'og:video:class'})
            meta_lang = root.find('meta', {'property': 'og:video:language'})
            
            # 修復標題提取：移除"夸克網盤"等字樣
            vod_name = ""
            title_elem = root.find('h1', class_='page-title')
            if title_elem:
                vod_name = title_elem.text.strip()
            else:
                title_tag = root.find('title')
                if title_tag:
                    vod_name = title_tag.text.strip()
            
            # 清理標題：移除夸克網盤、播放等字樣
            vod_name = self._clean_title(vod_name)
            
            vod_subname = ""
            subname_elem = root.find('h3', class_='video-info-item')
            if subname_elem:
                vod_subname = subname_elem.text.strip()
            
            vod_pic = ""
            meta_image = root.find('meta', {'property': 'og:image'})
            if meta_image and meta_image.get('content'):
                vod_pic = meta_image['content']
            else:
                img = root.find('img', {'data-src': True}) or root.find('img', {'src': re.compile(r'vod/')})
                if img:
                    vod_pic = img.get('data-src', img.get('src', ''))
            
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = self.host + vod_pic if vod_pic.startswith('/') else vod_pic
            
            vod_content = ""
            for div in root.find_all('div', class_='txtone container'):
                text = div.text.strip()
                if text and len(text) > 50:
                    vod_content = text
                    break
            
            if not vod_content:
                meta_desc = root.find('meta', {'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    vod_content = meta_desc['content']
            
            play_from_list = []
            play_url_list = []
            
            play_script = root.find('script', string=re.compile(r'var player_aaaa='))
            if play_script:
                script_text = play_script.string
                match = re.search(r'var player_aaaa\s*=\s*({.*?});', script_text, re.DOTALL)
                if match:
                    try:
                        player_data = json.loads(match.group(1))
                        play_url = player_data.get('url', '')
                        if play_url:
                            play_url = play_url.replace('\\/', '/')
                            play_from_list = ["默认线路"]
                            play_url_list = [f"高清${play_url}"]
                    except:
                        pass
            
            if not play_from_list:
                tab_items = root.select('.module-tab-item.tab-item')
                for tab_item in tab_items:
                    source_name = tab_item.get_text(strip=True)
                    if not source_name:
                        continue
                    
                    link = tab_item.get('href', '')
                    if not link:
                        continue
                    
                    if not link.startswith('http'):
                        link = self.host + link if link.startswith('/') else self.host + '/' + link
                    
                    play_from_list.append(source_name)
                    play_url_list.append(f"高清${link}")
            
            if not play_from_list:
                play_sections = root.select('.player-side-playlist')
                for section in play_sections:
                    source_name = "线路"
                    title_elem = section.find('.module-tab-name') or section.find('.module-title')
                    if title_elem:
                        source_name = title_elem.get_text(strip=True)
                    
                    episodes = []
                    ep_links = section.select('.module-blocklist a[href]')
                    for ep_link in ep_links:
                        ep_title = ep_link.get_text(strip=True)
                        ep_url = ep_link.get('href', '')
                        
                        if ep_url and not ep_url.startswith('http'):
                            ep_url = self.host + ep_url if ep_url.startswith('/') else self.host + '/' + ep_url
                        
                        if ep_title and ep_url:
                            episodes.append(f"{ep_title}${ep_url}")
                    
                    if episodes:
                        play_from_list.append(source_name)
                        play_url_list.append("#".join(episodes))
            
            if not play_from_list:
                play_from_list = ["默认线路"]
                play_url_list = [f"高清${url}"]
            
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_subname": vod_subname,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": meta_year.get('content', '') if meta_year else "",
                "vod_actor": meta_actor.get('content', '') if meta_actor else "",
                "vod_director": meta_director.get('content', '') if meta_director else "",
                "vod_area": meta_area.get('content', '') if meta_area else "",
                "vod_lang": meta_lang.get('content', '') if meta_lang else "",
                "vod_type": meta_type.get('content', '') if meta_type else "",
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }
            
            return {"list": [video]}
            
        except Exception:
            video = {
                "vod_id": ids[0],
                "vod_name": "加载失败",
                "vod_pic": "",
                "vod_content": "",
                "vod_play_from": "默认线路",
                "vod_play_url": f"高清${ids[0]}"
            }
            return {"list": [video]}
    
    def _clean_title(self, title):
        """清理标题，移除不必要的字樣"""
        if not title:
            return ""
        
        # 移除常见的网站标识和播放相关字樣
        remove_keywords = [
            '夸克網盤', '夸克网盘', 'kuake', 
            '在线播放', '播放', 
            ' - 传奇影院', '- 传奇影院',
            '|传奇影院', '| 传奇影院',
            '線上觀看', '在线观看',
             '全集', '下载'
        ]
        
        cleaned_title = title
        for keyword in remove_keywords:
            cleaned_title = cleaned_title.replace(keyword, '')
        
        # 移除首尾的破折号、空格等
        cleaned_title = re.sub(r'^[-|_\s]+|[-|_\s]+$', '', cleaned_title)
        
        return cleaned_title.strip()
    
    def searchContent(self, key, quick, pg=1):
        try:
            encoded_key = urllib.parse.quote(key)
            if int(pg) > 1:
                search_url = f"{self.host}/vodsearch/{encoded_key}---------{pg}---.html"
            else:
                search_url = f"{self.host}/vodsearch/{encoded_key}-------------.html"
            
            rsp = self.fetch(search_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            result_items = root.select('.module-search-item')
            
            for item in result_items:
                try:
                    play_link = item.find('a', {'href': re.compile(r'/vodplay/'), 'title': True})
                    if not play_link:
                        continue
                    
                    vod_id = play_link.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    vod_name = ""
                    title_elem = item.find('h3')
                    if title_elem:
                        title_link = title_elem.find('a')
                        if title_link:
                            vod_name = title_link.text.strip()
                    
                    if not vod_name:
                        vod_name = play_link.get('title', '').replace('立刻播放', '').strip()
                    
                    vod_pic = ""
                    img = item.find('img')
                    if img:
                        vod_pic = img.get('data-src', img.get('src', ''))
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = self.host + vod_pic if vod_pic.startswith('/') else vod_pic
                    
                    vod_remarks = ""
                    serial_elem = item.find('a', class_='video-serial')
                    if serial_elem:
                        vod_remarks = serial_elem.text.strip()
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks
                    })
                except Exception:
                    continue
            
            pagecount = 1
            pagination = root.find('div', id='page')
            if pagination:
                last_page = pagination.find('a', class_='page-next', href=re.compile(r'.*---------.*---\.html'))
                if last_page:
                    href = last_page.get('href', '')
                    match = re.search(r'---------(\d+)---\.html', href)
                    if match:
                        pagecount = int(match.group(1))
            
            if pagecount == 1 and videos:
                total_text = root.find('strong', class_='mac_total')
                if total_text:
                    try:
                        total_count = int(total_text.text.strip())
                        pagecount = (total_count + 9) // 10
                    except:
                        pass
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount if pagecount > 0 else 1,
                "limit": 10,
                "total": len(videos) * pagecount
            }
            
        except Exception:
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 10,
                "total": 0
            }
    
    def playerContent(self, flag, id, vipFlags):
        result = {}
        
        try:
            if not id.startswith('http'):
                play_url = self.host + id if id.startswith('/') else self.host + '/' + id
            else:
                play_url = id
            
            rsp = self.fetch(play_url, headers=self.header())
            html_content = rsp.text
            
            video_url = None
            
            match = re.search(r'var player_aaaa\s*=\s*({.*?});', html_content, re.DOTALL)
            if match:
                try:
                    player_data = json.loads(match.group(1))
                    video_url = player_data.get('url', '')
                    if video_url:
                        video_url = video_url.replace('\\/', '/')
                except:
                    pass
            
            if not video_url:
                soup = BeautifulSoup(html_content, 'html.parser')
                iframe = soup.find('iframe')
                if iframe and iframe.get('src'):
                    video_url = iframe['src']
            
            if not video_url:
                soup = BeautifulSoup(html_content, 'html.parser')
                video_tag = soup.find('video')
                if video_tag and video_tag.get('src'):
                    video_url = video_tag['src']
            
            if not video_url:
                m3u8_patterns = [
                    r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                    r'["\'](//[^"\']+\.m3u8[^"\']*)["\']',
                    r'url\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                    r'src\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']'
                ]
                for pattern in m3u8_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        video_url = match.group(1)
                        break
            
            if video_url:
                if video_url.startswith('//'):
                    video_url = 'https:' + video_url
                elif video_url.startswith('/'):
                    video_url = self.host + video_url
                elif not video_url.startswith('http'):
                    base_url = '/'.join(play_url.split('/')[:-1])
                    video_url = base_url + '/' + video_url
                
                result["parse"] = 0
                result["url"] = video_url
                result["header"] = self.header()
                result["header"]["Referer"] = play_url
            else:
                result["parse"] = 1
                result["url"] = play_url
                result["header"] = self.header()
                result["header"]["Referer"] = self.host
            
        except Exception:
            result["parse"] = 1
            result["url"] = id
            result["header"] = self.header()
            if id.startswith('http'):
                result["header"]["Referer"] = self.host
        
        return result
    
    def localProxy(self, params):
        return [200, "video/MP2T", ""]
