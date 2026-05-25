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
        return "99专员_Fixed"
    
    def init(self, extend=""):
        self.host = "https://www.99zy1.top"
        pass
    
    def header(self, referer=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        if referer:
            headers['Referer'] = referer
        else:
            headers['Referer'] = self.host
        return headers
    
    def homeContent(self, filter):
        result = {}
        result["class"] = [
            {"type_name": "全网资源", "type_id": "1"}
        ]
        return result
    
    def homeVideoContent(self):
        try:
            rsp = self.fetch(self.host, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            items = root.select('.vod-list a')
            
            for item in items[:30]:
                vod_id = item.get('href', '')
                if not vod_id:
                    continue
                
                img = item.select_one('.vod-pic')
                vod_pic = img.get('src', '') if img else ""
                
                name_elem = item.select_one('.vod-name')
                vod_name = name_elem.text.strip() if name_elem else "未知"
                
                date_elem = item.select_one('.vod-date')
                vod_remarks = date_elem.text.strip() if date_elem else ""
                
                videos.append({
                    "vod_id": self.regUrl(vod_id),
                    "vod_name": vod_name,
                    "vod_pic": self.regUrl(vod_pic),
                    "vod_remarks": vod_remarks
                })
            
            return {"list": videos}
        except Exception as e:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        pg = int(pg)
        if pg > 1:
            url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
        else:
            url = f"{self.host}/index.php/vod/type/id/{tid}.html"
            
        try:
            # 首次请求带完整头
            rsp = self.fetch(url, headers=self.header(url))
            
            # 检查是否被 Cloudflare 拦截
            if 'Just a moment' in rsp.text or 'cf_chl' in rsp.text:
                # 重试一次，可能第一次触发了验证
                rsp = self.fetch(url, headers=self.header(url))
            
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            items = root.select('.vod-list a')
            
            # 如果还是没解析到，尝试备用选择器
            if not items:
                items = root.select('.vod-list .vod-item')
                for item in items:
                    a_tag = item.find('a')
                    if a_tag:
                        vod_id = a_tag.get('href', '')
                        img = a_tag.select_one('.vod-pic')
                        vod_pic = img.get('src', '') if img else ""
                        name_elem = a_tag.select_one('.vod-name')
                        vod_name = name_elem.text.strip() if name_elem else "未知"
                        date_elem = a_tag.select_one('.vod-date')
                        vod_remarks = date_elem.text.strip() if date_elem else ""
                        videos.append({
                            "vod_id": self.regUrl(vod_id),
                            "vod_name": vod_name,
                            "vod_pic": self.regUrl(vod_pic),
                            "vod_remarks": vod_remarks
                        })
            else:
                for item in items:
                    vod_id = item.get('href', '')
                    if not vod_id:
                        continue
                    
                    img = item.select_one('.vod-pic')
                    vod_pic = img.get('src', '') if img else ""
                    
                    name_elem = item.select_one('.vod-name')
                    vod_name = name_elem.text.strip() if name_elem else "未知"
                    
                    date_elem = item.select_one('.vod-date')
                    vod_remarks = date_elem.text.strip() if date_elem else ""
                    
                    videos.append({
                        "vod_id": self.regUrl(vod_id),
                        "vod_name": vod_name,
                        "vod_pic": self.regUrl(vod_pic),
                        "vod_remarks": vod_remarks
                    })

            # 分页解析
            page_count = pg
            pagination = root.select_one('.pagenavi_txt')
            if pagination:
                page_links = pagination.find_all('a')
                for link in page_links:
                    link_text = link.text.strip()
                    if link_text.isdigit():
                        page_count = max(page_count, int(link_text))

            return {
                "list": videos,
                "page": pg,
                "pagecount": page_count,
                "limit": len(videos),
                "total": 30 * page_count
            }
        except Exception as e:
            return {"list": [], "page": pg, "pagecount": pg}

    def detailContent(self, ids):
        vod_id = ids[0]
        url = self.regUrl(vod_id)
        
        try:
            rsp = self.fetch(url, headers=self.header(url))
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            vod_name = ""
            title_ele = root.select_one('.detail-pos text')
            if title_ele:
                vod_name = title_ele.text.strip()
            
            vod_pic = ""
            pic_tag = root.select_one('.detail-vod-pic')
            if pic_tag:
                vod_pic = self.regUrl(pic_tag.get('src', ''))
            
            play_from = []
            play_urls = []
            
            play_blocks = root.select('.detail-btns')
            for block in play_blocks:
                title_div = block.select_one('.detail-play-title text')
                line_name = title_div.text.strip() if title_div else "默认线路"
                
                play_btns = block.select('.play-btn a')
                episodes = []
                for btn in play_btns:
                    ep_name = btn.text.strip()
                    ep_link = btn.get('href', '')
                    if ep_link:
                        episodes.append(f"{ep_name}${self.regUrl(ep_link)}")
                
                if episodes:
                    play_from.append(line_name)
                    play_urls.append("#".join(episodes))
            
            if not play_urls:
                script_text = rsp.text
                match = re.search(r'var\s+player_aaaa\s*=\s*(\{.*?\});', script_text, re.DOTALL)
                if match:
                    try:
                        pd = json.loads(match.group(1))
                        u = pd.get('url', '')
                        if u:
                            eps = []
                            for p in u.split('#'):
                                sp = p.split('$', 1)
                                name, link = (sp[0], sp[1]) if len(sp) > 1 else (f"第{len(eps)+1}集", p)
                                eps.append(f"{name}${link}")
                            play_from.append("默认线路")
                            play_urls.append("#".join(eps))
                    except:
                        pass
            
            if not play_urls:
                txt = rsp.text
                m3u8 = re.findall(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', txt)
                mp4 = re.findall(r'(https?://[^"\'\s]+\.mp4[^"\'\s]*)', txt)
                if m3u8 or mp4:
                    eps = []
                    for item in m3u8[:10]:
                        eps.append(f"M3U8-{len(eps)+1}${item}")
                    for item in mp4[:10]:
                        eps.append(f"MP4-{len(eps)+1}${item}")
                    play_from.append("直链")
                    play_urls.append("#".join(eps))
            
            vod_content = ""
            desc_tag = root.select_one('.vod-desc') or root.select_one('.vod-content')
            if desc_tag:
                vod_content = desc_tag.text.strip()
            
            video = {
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_play_from": "$$$".join(play_from) if play_from else "",
                "vod_play_url": "$$$".join(play_urls) if play_urls else "",
                "vod_content": vod_content
            }
            return {"list": [video]}
        except Exception as e:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        pg = int(pg)
        encoded_key = urllib.parse.quote(key)
        
        if pg > 1:
            url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{encoded_key}.html"
        else:
            url = f"{self.host}/index.php/vod/search/wd/{encoded_key}.html"
            
        try:
            rsp = self.fetch(url, headers=self.header(url))
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            items = root.select('.vod-list a')
            for item in items:
                vod_id = item.get('href', '')
                if not vod_id:
                    continue
                
                img = item.select_one('.vod-pic')
                vod_pic = img.get('src', '') if img else ""
                
                name_elem = item.select_one('.vod-name')
                vod_name = name_elem.text.strip() if name_elem else "未知"
                
                date_elem = item.select_one('.vod-date')
                vod_remarks = date_elem.text.strip() if date_elem else ""
                
                videos.append({
                    "vod_id": self.regUrl(vod_id),
                    "vod_name": vod_name,
                    "vod_pic": self.regUrl(vod_pic),
                    "vod_remarks": vod_remarks
                })
            
            page_count = pg
            pagination = root.select_one('.pagenavi_txt')
            if pagination:
                page_links = pagination.find_all('a')
                for link in page_links:
                    link_text = link.text.strip()
                    if link_text.isdigit():
                        page_count = max(page_count, int(link_text))
            
            return {"list": videos, "page": pg, "pagecount": page_count}
        except Exception as e:
            return {"list": [], "page": pg, "pagecount": pg}

    def playerContent(self, flag, id, vipFlags):
        url = self.regUrl(id)
        result = {"parse": 1, "url": url, "header": self.header(url)}
        
        try:
            rsp = self.fetch(url, headers=self.header(url))
            script_text = rsp.text
            
            m3u8_match = re.search(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', script_text)
            if m3u8_match:
                result["parse"] = 0
                result["url"] = m3u8_match.group(1)
            else:
                mp4_match = re.search(r'(https?://[^"\'\s]+\.mp4[^"\'\s]*)', script_text)
                if mp4_match:
                    result["parse"] = 0
                    result["url"] = mp4_match.group(1)
        except Exception as e:
            pass
            
        return result

    def regUrl(self, url):
        if not url:
            return ""
        if url.startswith('//'):
            return "https:" + url
        if url.startswith('/'):
            return self.host + url
        return url