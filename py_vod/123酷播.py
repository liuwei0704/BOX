# -*- coding: utf-8 -*-
# 站点: 123酷播 (https://123kubo.tv)
# 类型: 标准影视站
# 特性: HTML解析、多线路、m3u8直链、内置分类筛选

import re
import json
import base64
from urllib.parse import urljoin


class Spider:
    """123酷播 爬虫 - TVBox/FongMi 兼容"""

    def __init__(self):
        self.host = "https://123kubo.tv"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': self.host,
        }
        # 分类硬编码 - 零网络依赖
        self.classes = [
            {"type_name": "電影", "type_id": "1"},
            {"type_name": "連續劇", "type_id": "2"},
            {"type_name": "綜藝", "type_id": "3"},
            {"type_name": "動漫", "type_id": "4"},
        ]
        self.filters = {
            "1": [{"key": "tid", "name": "類型", "value": [{"n": "全部", "v": "1"}, {"n": "動作片", "v": "6"}, {"n": "喜劇片", "v": "7"}, {"n": "愛情片", "v": "8"}, {"n": "科幻片", "v": "9"}, {"n": "恐怖片", "v": "10"}, {"n": "劇情片", "v": "11"}, {"n": "戰爭片", "v": "12"}, {"n": "紀錄片", "v": "20"}, {"n": "微電影", "v": "21"}, {"n": "動漫片", "v": "22"}, {"n": "倫理片", "v": "23"}]}],
            "2": [{"key": "tid", "name": "類型", "value": [{"n": "全部", "v": "2"}, {"n": "陸劇", "v": "13"}, {"n": "港劇", "v": "14"}, {"n": "台劇", "v": "15"}, {"n": "日劇", "v": "16"}, {"n": "韓劇", "v": "24"}, {"n": "美劇", "v": "25"}, {"n": "泰劇", "v": "26"}, {"n": "海外劇", "v": "27"}]}],
            "3": [{"key": "tid", "name": "類型", "value": [{"n": "全部", "v": "3"}, {"n": "內地綜藝", "v": "28"}, {"n": "日韓綜藝", "v": "29"}, {"n": "港台綜藝", "v": "30"}, {"n": "歐美綜藝", "v": "31"}]}],
            "4": [{"key": "tid", "name": "類型", "value": [{"n": "全部", "v": "4"}, {"n": "國產動漫", "v": "32"}, {"n": "日韓動漫", "v": "33"}, {"n": "港台動漫", "v": "34"}, {"n": "歐美動漫", "v": "35"}, {"n": "海外動漫", "v": "36"}]}]
        }

    def getName(self):
        return "123酷播"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def siteInfo(self):
        return {"name": "123酷播", "host": self.host}

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters}

    def getHomeContent(self):
        return self.homeContent(False)

    def homeVideoContent(self):
        try:
            html = self._fetch(self.host)
            return {"list": self._parse_list(html), "page": 1}
        except Exception:
            return {"list": []}

    def _fetch(self, url):
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except:
            return ""

    def _parse_extend(self, extend):
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            try:
                if extend.startswith("{") and extend.endswith("}"):
                    import ast
                    return ast.literal_eval(extend)
            except:
                pass
            result = {}
            for part in extend.split(","):
                if "=" in part:
                    k, v = part.split("=", 1)
                    result[k.strip()] = v.strip()
            return result
        return {}

    def categoryContent(self, tid, pg=1, filter=False, extend=""):
        try:
            pg = int(pg) if pg else 1
            ext = self._parse_extend(extend)
            target_tid = ext.get("tid", tid)
            url = f"{self.host}/show/{target_tid}/page/{pg}.html"
            html = self._fetch(url)
            v_list = self._parse_list(html)
            return {"list": v_list, "page": pg, "pagecount": pg + 1, "limit": len(v_list), "total": len(v_list)}
        except Exception:
            return {"list": [], "page": int(pg) if pg else 1}

    def _parse_list(self, html):
        """解析列表 - 分类页使用"""
        if not html:
            return []
        result = []
        seen = set()
        blacklist = ["線上看", "首頁", "專題", "留言", "排行", "最近更新", "推薦", "APP", "公告"]
        
        # 直接匹配每个列表项
        pattern = r'<li[^>]*class="[^"]*hl-list-item[^"]*"[^>]*>(.*?)</li>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for item_html in items:
            a_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>', item_html)
            if not a_match:
                continue
            href = a_match.group(1)
            name = a_match.group(2).strip()
            
            if not name:
                title_match = re.search(r'hl-item-title[^>]*>.*?<a[^>]*>(.*?)</a>', item_html, re.DOTALL)
                if title_match:
                    name = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            
            if not name or href in seen:
                continue
            
            name = re.sub(r'[-|_]?(電影|劇集|動漫|綜藝|免費|高清)?線上看.*', '', name).strip()
            name = name.replace("123酷播", "").strip()
            if not name or len(name) < 2 or len(name) > 40 or name in blacklist:
                continue
            
            pic = re.search(r'data-original="([^"]+)"', item_html)
            if not pic:
                pic = re.search(r'src="([^"]+)"', item_html)
            pic_url = pic.group(1) if pic else ""
            if pic_url and not pic_url.startswith('http'):
                pic_url = urljoin(self.host, pic_url)
            
            remarks = re.search(r'remarks[^>]*>([^<]+)<', item_html)
            remarks_text = remarks.group(1).strip() if remarks else ""
            if not remarks_text:
                remarks = re.search(r'hl-pic-text[^>]*>.*?<span[^>]*>([^<]+)<', item_html, re.DOTALL)
                remarks_text = remarks.group(1).strip() if remarks else ""
            
            seen.add(href)
            result.append({
                "vod_id": href,
                "vod_name": name,
                "vod_pic": pic_url or "",
                "vod_remarks": remarks_text
            })
        
        return result

    def _parse_search_list(self, html):
        """专门解析搜索页面列表"""
        if not html:
            return []
        result = []
        seen = set()
        blacklist = ["線上看", "首頁", "專題", "留言", "排行", "最近更新", "推薦", "APP", "公告"]
        
        # 搜索页面使用 hl-list-item hl-col-xs-12
        # 使用更直接的匹配方式：找所有 hl-list-item 然后提取
        pattern = r'<li[^>]*class="[^"]*hl-list-item[^"]*"[^>]*>(.*?)</li>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for item_html in items:
            # 提取a标签 - 查找 hl-item-thumb 或直接找 a
            a_match = re.search(r'<a[^>]*class="[^"]*hl-item-thumb[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>', item_html)
            if not a_match:
                a_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>', item_html)
            if not a_match:
                continue
            
            href = a_match.group(1)
            name = a_match.group(2).strip()
            
            if not name:
                title_match = re.search(r'hl-item-title[^>]*>.*?<a[^>]*>(.*?)</a>', item_html, re.DOTALL)
                if title_match:
                    name = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            
            if not name or href in seen:
                continue
            
            name = re.sub(r'[-|_]?(電影|劇集|動漫|綜藝|免費|高清)?線上看.*', '', name).strip()
            name = name.replace("123酷播", "").strip()
            if not name or len(name) < 2 or len(name) > 40 or name in blacklist:
                continue
            
            pic = re.search(r'data-original="([^"]+)"', item_html)
            if not pic:
                pic = re.search(r'src="([^"]+)"', item_html)
            pic_url = pic.group(1) if pic else ""
            if pic_url and not pic_url.startswith('http'):
                pic_url = urljoin(self.host, pic_url)
            
            remarks = re.search(r'remarks[^>]*>([^<]+)<', item_html)
            remarks_text = remarks.group(1).strip() if remarks else ""
            if not remarks_text:
                remarks = re.search(r'hl-pic-text[^>]*>.*?<span[^>]*>([^<]+)<', item_html, re.DOTALL)
                remarks_text = remarks.group(1).strip() if remarks else ""
            
            seen.add(href)
            result.append({
                "vod_id": href,
                "vod_name": name,
                "vod_pic": pic_url or "",
                "vod_remarks": remarks_text
            })
        
        return result

    def _extract_attr(self, text, start, end):
        """提取属性值"""
        pos = text.find(start)
        if pos == -1:
            return ""
        pos2 = text.find(end, pos + len(start))
        if pos2 == -1:
            return ""
        return text[pos + len(start):pos2].strip()

    def _extract_between(self, text, marker, end):
        """提取标记之间的内容"""
        pos = text.find(marker)
        if pos == -1:
            return ""
        pos2 = text.find(end, pos)
        if pos2 == -1:
            return ""
        tag_end = text.find('>', pos)
        if tag_end != -1 and tag_end < pos2:
            content_start = tag_end + 1
            if content_start < pos2:
                return text[content_start:pos2].strip()
        return ""

    def _dedupe(self, items):
        seen = set()
        result = []
        for item in items:
            if item and item.get("vod_id") not in seen:
                result.append(item)
                seen.add(item.get("vod_id"))
        return result

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = ids[0]
        url = f"{self.host}{vid}" if vid.startswith("/") else vid
        try:
            html = self._fetch(url)
            if not html:
                return {"list": []}
            title = self._extract_between(html, '<title>', '</title>')
            if title:
                title = re.sub(r'[-|_]?(電影|劇集|動漫|綜藝|免費|高清)?線上看.*', '', title).strip()
            pic = self._extract_attr(html, 'data-original="', '"')
            if not pic:
                pic = self._extract_attr(html, 'src="', '"')
            if pic and not pic.startswith('http'):
                pic = urljoin(self.host, pic)
            from_list = []
            url_list = []
            tabs = re.findall(r'<[^>]*class="[^"]*hl-tabs-btn[^"]*"[^>]*>([^<]+)</', html)
            ul_pattern = r'<ul[^>]*class="[^"]*hl-plays-list[^"]*"[^>]*>(.*?)</ul>'
            uls = re.findall(ul_pattern, html, re.DOTALL)
            if not uls:
                uls = re.findall(r'<div[^>]*class="[^"]*play-list[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            for i, ul_html in enumerate(uls):
                name = tabs[i].strip() if i < len(tabs) else f"線路{i+1}"
                from_list.append(name)
                links = []
                for a_match in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', ul_html):
                    a_href = a_match.group(1)
                    a_text = a_match.group(2).strip()
                    if a_href:
                        links.append(f"{a_text}${a_href}")
                url_list.append("#".join(links))
            vod = {
                "vod_id": vid,
                "vod_name": title or "未知",
                "vod_pic": pic or "",
                "vod_play_from": "$$$".join(from_list) if from_list else "線路1",
                "vod_play_url": "$$$".join(url_list) if url_list else ""
            }
            return {"list": [vod]}
        except Exception:
            return {"list": []}

    def searchContent(self, key, quick=False, pg=1):
        if not key:
            return {"list": []}
        try:
            pg = int(pg) if pg else 1
            # 对中文关键词进行URL编码
            from urllib.parse import quote
            encoded_key = quote(key, safe='')
            url = f"{self.host}/search/page/{pg}/wd/{encoded_key}.html"
            html = self._fetch(url)
            if not html:
                return {"list": []}
            v_list = self._parse_search_list(html)
            return {"list": v_list, "page": pg}
        except Exception as e:
            return {"list": []}
    def playerContent(self, flag, id, vipFlags=None):
        if not id:
            return {"parse": 1, "url": "", "header": self.headers}
        url = f"{self.host}{id}" if id.startswith("/") else id
        try:
            html = self._fetch(url)
            if not html:
                return {"parse": 1, "url": url, "header": self.headers}
            m3u8_match = re.search(r'(https?:\\?/\\?/[^"\']+\.m3u8[^"\']*)', html)
            if m3u8_match:
                return {"parse": 0, "url": m3u8_match.group(1).replace('\\/', '/'), "header": self.headers}
            mp4_match = re.search(r'(https?:\\?/\\?/[^"\']+\.mp4[^"\']*)', html)
            if mp4_match:
                return {"parse": 0, "url": mp4_match.group(1).replace('\\/', '/'), "header": self.headers}
            config_match = re.search(r'player_aaaa\s*=\s*(\{.*?\})', html, re.DOTALL)
            if config_match:
                try:
                    config = json.loads(config_match.group(1))
                    play_url = config.get('url', '').replace('\\/', '/')
                    if play_url:
                        if not any(x in play_url.lower() for x in ['.m3u8', '.mp4', 'http']) and len(play_url) > 20:
                            try:
                                play_url = base64.b64decode(play_url).decode('utf-8')
                            except:
                                pass
                        if '.m3u8' in play_url.lower() or '.mp4' in play_url.lower():
                            return {"parse": 0, "url": play_url, "header": self.headers}
                except:
                    pass
            iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', html)
            if iframe_match:
                iframe_url = iframe_match.group(1).replace('\\/', '/')
                if iframe_url.startswith("//"):
                    iframe_url = "https:" + iframe_url
                elif iframe_url.startswith("/"):
                    iframe_url = self.host + iframe_url
                return {"parse": 1, "url": iframe_url, "header": self.headers}
            return {"parse": 1, "url": url, "header": self.headers}
        except Exception:
            return {"parse": 1, "url": url, "header": self.headers}