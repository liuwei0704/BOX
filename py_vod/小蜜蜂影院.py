# 小蜜蜂影院 - TVBox FongMi 爬虫源
# 站点: https://www.xmfyy.cc/
# 参考: 99itv_1.py 的播放直链优化方案

import re
import json
import urllib.parse
from bs4 import BeautifulSoup

class Spider:
    def __init__(self):
        self.host = "https://www.xmfyy.cc"
        self.site_name = "小蜜蜂影院"
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        self.headers = {
            "User-Agent": self.ua,
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate"
        }
        
        self.classes = [
            {"id": "1", "name": "电影", "sub": [
                {"id": "6", "name": "动作片"},
                {"id": "7", "name": "喜剧片"},
                {"id": "8", "name": "爱情片"},
                {"id": "9", "name": "科幻片"},
                {"id": "10", "name": "恐怖片"},
                {"id": "11", "name": "剧情片"},
                {"id": "12", "name": "战争片"},
                {"id": "21", "name": "悬疑片"}
            ]},
            {"id": "2", "name": "连续剧", "sub": [
                {"id": "13", "name": "国产剧"},
                {"id": "14", "name": "港台剧"},
                {"id": "15", "name": "日韩剧"},
                {"id": "16", "name": "欧美剧"},
                {"id": "38", "name": "纪录片"},
                {"id": "37", "name": "其他剧"}
            ]},
            {"id": "4", "name": "动漫", "sub": [
                {"id": "28", "name": "动漫"},
                {"id": "39", "name": "番剧"},
                {"id": "19", "name": "动画片"}
            ]},
            {"id": "3", "name": "综艺"}
        ]
        
        self.filters = {}
        for cls in self.classes:
            main_id = cls["id"]
            if "sub" in cls and cls["sub"]:
                filter_opts = [{"n": "全部", "v": ""}]
                for sub in cls["sub"]:
                    filter_opts.append({"n": sub["name"], "v": sub["id"]})
                self.filters[main_id] = [
                    {"key": "class", "name": "分类", "value": filter_opts}
                ]
            else:
                self.filters[main_id] = []

    def init(self, extend=None):
        pass

    def getDependence(self):
        return ["bs4"]

    def destroy(self):
        pass

    def _fetch(self, url, headers=None):
        """优先使用 self.fetch()，备用 urllib.request"""
        if headers is None:
            headers = self.headers.copy()
        try:
            r = self.fetch(url, headers=headers, timeout=15)
            if r and hasattr(r, 'text') and r.text:
                return r.text
        except Exception as e:
            pass
        try:
            import urllib.request
            import gzip
            import zlib
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=15)
            data = response.read()
            encoding = response.headers.get('Content-Encoding', '')
            if 'gzip' in encoding:
                data = gzip.decompress(data)
            elif 'deflate' in encoding:
                data = zlib.decompress(data, -zlib.MAX_WBITS)
            charset = 'utf-8'
            content_type = response.headers.get('Content-Type', '')
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[-1].strip()
            return data.decode(charset, errors='ignore')
        except Exception as e:
            pass
        return None

    def _parse_extend(self, extend):
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            try:
                return json.loads(extend)
            except:
                clean = extend.strip().strip('{}')
                result = {}
                if clean:
                    for part in clean.split(','):
                        if '=' in part:
                            key, val = part.split('=', 1)
                            result[key.strip()] = val.strip()
                return result
        return {}

    def _fix_url(self, url):
        if not url:
            return ""
        url = url.replace('\\/', '/')
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.host + url
        return self.host + '/' + url

    def _decode_player_url(self, url, encrypt):
        """参考 99itv_1.py: 支持多种 encrypt 格式解码"""
        if not url:
            return ''
        try:
            if encrypt == 1:
                url = urllib.parse.unquote(url)
            elif encrypt == 2:
                import base64
                url = base64.b64decode(urllib.parse.unquote(url)).decode('utf-8', errors='ignore')
            else:
                url = urllib.parse.unquote(url)
        except Exception:
            pass
        return self._fix_url(url)

    def _media_header(self, referer):
        """参考 99itv_1.py: 标准 header 序列化"""
        return json.dumps({
            'User-Agent': self.ua,
            'Referer': referer or self.host + '/',
            'Origin': self.host
        }, ensure_ascii=False)

    def _parse_vod_list(self, html):
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        seen = set()
        
        elements = soup.select('.hl-vod-list .hl-list-item, .hl-vod-list .hl-item-wrap')
        if not elements:
            elements = soup.select('.hl-list-item, .hl-item-wrap')
        if not elements:
            elements = soup.select('a[href*="/vod/detail/"]')
            for a in elements:
                href = a.get('href', '')
                vid = href.split('/id/')[-1].replace('.html', '').strip()
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                title = a.get('title', '') or a.get('alt', '')
                pic = a.get('data-original', '') or a.get('src', '')
                items.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": self._fix_url(pic),
                    "vod_remarks": ""
                })
            return items
        
        for item in elements:
            a = item.select_one('a.hl-item-thumb, a.hl-item-pic, a[href*="/vod/detail/"]')
            if not a:
                continue
            href = a.get('href', '')
            if not href or '/vod/detail/' not in href:
                continue
            vid = href.split('/id/')[-1].replace('.html', '').strip()
            if vid in seen:
                continue
            seen.add(vid)
            title_el = item.select_one('.hl-item-title a, .hl-item-text .hl-title a, .hl-item-name a')
            if title_el:
                title = title_el.get_text(strip=True)
            else:
                title = a.get('title', '') or a.get('alt', '')
            pic = a.get('data-original', '') or a.get('src', '')
            remark = ''
            text_el = item.select_one('.hl-pic-text .remarks, .hl-pic-text .hl-lc-1, .hl-item-remarks')
            if text_el:
                remark = text_el.get_text(strip=True)
            items.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": self._fix_url(pic),
                "vod_remarks": remark
            })
        return items

    def homeContent(self, filter=False):
        result = {
            "class": [],
            "filters": self.filters,
            "list": []
        }
        for cls in self.classes:
            result["class"].append({
                "type_id": cls["id"],
                "type_name": cls["name"]
            })
        html = self._fetch(self.host + "/")
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            items = []
            seen = set()
            for a in soup.select('a[href*="/vod/detail/"]'):
                vid = a.get('href', '').split('/id/')[-1].replace('.html', '').strip()
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                title = a.get('title', '') or ''
                if not title:
                    title_el = a.select_one('.hl-lc-1')
                    if title_el:
                        title = title_el.get_text(strip=True)
                pic = a.get('data-original', '') or a.get('src', '')
                remark = ''
                text_el = a.select_one('.hl-pic-text .remarks, .hl-pic-text .hl-lc-1')
                if text_el:
                    remark = text_el.get_text(strip=True)
                items.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": self._fix_url(pic),
                    "vod_remarks": remark
                })
                if len(items) >= 20:
                    break
            result["list"] = items[:20]
        return result

    def homeVideoContent(self):
        return self.homeContent(filter=False)

    def categoryContent(self, tid, pg=1, filter=False, extend=None):
        pg = int(pg) if pg else 1
        filters = self._parse_extend(extend)
        sub_class = filters.get('class', '')
        target_id = sub_class if sub_class else tid
        if pg == 1:
            url = f"{self.host}/index.php/vod/show/id/{target_id}.html"
        else:
            url = f"{self.host}/index.php/vod/show/id/{target_id}/page/{pg}.html"
        html = self._fetch(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 0, "limit": 20, "total": 0}
        items = self._parse_vod_list(html)
        pagecount = pg
        test_url = f"{self.host}/index.php/vod/show/id/{target_id}/page/{pg+1}.html"
        test_html = self._fetch(test_url)
        if test_html:
            test_items = self._parse_vod_list(test_html)
            if len(test_items) > 0:
                pagecount = pg + 1
        if len(items) == 0:
            pagecount = 0
        return {
            "list": items,
            "page": pg,
            "pagecount": pagecount,
            "limit": 20,
            "total": len(items) * max(1, pagecount)
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = ids[0] if isinstance(ids, list) else ids
        url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
        html = self._fetch(url)
        if not html:
            return {"list": []}
        soup = BeautifulSoup(html, 'html.parser')
        title = ''
        title_selectors = [
            'h2 .hl-infos-title',
            '.hl-vod-name h2',
            '.hl-infos-title',
            'h1',
            '.vod-title',
            '.title',
            'meta[property="og:title"]'
        ]
        for sel in title_selectors:
            el = soup.select_one(sel)
            if el:
                if sel == 'meta[property="og:title"]':
                    title = el.get('content', '')
                else:
                    title = el.get_text(strip=True)
                if title:
                    break
        pic = ''
        pic_el = soup.select_one('.hl-item-thumb, .hl-item-pic img, .hl-detail-pic img')
        if pic_el:
            pic = pic_el.get('data-original', '') or pic_el.get('src', '')
        content = ''
        content_el = soup.select_one('.hl-vod-data .blurb, .hl-infos-content .hl-tag-item + .hl-tag-item, .hl-desc, .hl-blurb')
        if content_el:
            content = content_el.get_text(strip=True)
        line_groups = {}
        line_names = []
        tabs = soup.select('.hl-plays-from .hl-tabs-btn, .hl-play-source .hl-tabs-btn')
        for tab in tabs:
            name = tab.get('alt', '') or tab.get_text(strip=True)
            if name:
                line_names.append(name)
        if not line_names:
            line_names = ["默认线路"]
        boxes = soup.select('.hl-play-source .hl-tabs-box, .hl-tabs-box')
        if boxes and len(boxes) >= len(line_names):
            for i, box in enumerate(boxes):
                if i >= len(line_names):
                    break
                line_name = line_names[i]
                episodes = []
                for a in box.select('a[href*="/vod/play/"]'):
                    ep_href = a.get('href', '')
                    ep_name = a.get_text(strip=True)
                    if ep_href:
                        ep_url = self._fix_url(ep_href)
                        if ep_name:
                            episodes.append(f"{ep_name}${ep_url}")
                        else:
                            episodes.append(ep_url)
                if episodes:
                    line_groups[line_name] = episodes
        if not line_groups:
            play_lists = soup.select('.hl-plays-list')
            if play_lists:
                for i, play_list in enumerate(play_lists):
                    line_name = line_names[i] if i < len(line_names) else f"线路{i+1}"
                    episodes = []
                    for a in play_list.select('a[href*="/vod/play/"]'):
                        ep_href = a.get('href', '')
                        ep_name = a.get_text(strip=True)
                        if ep_href:
                            ep_url = self._fix_url(ep_href)
                            if ep_name:
                                episodes.append(f"{ep_name}${ep_url}")
                            else:
                                episodes.append(ep_url)
                    if episodes:
                        line_groups[line_name] = episodes
        if not line_groups:
            all_links = soup.select('a[href*="/vod/play/"]')
            if all_links:
                line_name = "默认线路"
                episodes = []
                seen = set()
                for a in all_links:
                    ep_href = a.get('href', '')
                    if ep_href in seen:
                        continue
                    seen.add(ep_href)
                    ep_name = a.get_text(strip=True)
                    if ep_href:
                        ep_url = self._fix_url(ep_href)
                        if ep_name:
                            episodes.append(f"{ep_name}${ep_url}")
                        else:
                            episodes.append(ep_url)
                if episodes:
                    line_groups[line_name] = episodes
        play_from_list = []
        play_url_list = []
        for line_name, episodes in line_groups.items():
            play_from_list.append(line_name)
            play_url_list.append("#".join(episodes))
        return {
            "list": [{
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": self._fix_url(pic),
                "vod_content": content,
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }]
        }

    def searchContent(self, key, quick=False, pg=1):
        pg = int(pg) if pg else 1
        encoded_key = urllib.parse.quote(key)
        if pg == 1:
            url = f"{self.host}/index.php/vod/search.html?wd={encoded_key}"
        else:
            url = f"{self.host}/index.php/vod/search.html?wd={encoded_key}&page={pg}"
        html = self._fetch(url)
        if not html:
            return {"list": [], "pagecount": 0}
        items = self._parse_vod_list(html)
        pagecount = pg
        if len(items) >= 20:
            test_url = f"{self.host}/index.php/vod/search.html?wd={encoded_key}&page={pg+1}"
            test_html = self._fetch(test_url)
            if test_html:
                test_items = self._parse_vod_list(test_html)
                if len(test_items) > 0:
                    pagecount = pg + 1
        if len(items) == 0:
            pagecount = 0
        return {
            "list": items,
            "pagecount": pagecount
        }

    def playerContent(self, flag, id, vipFlags=None):
        """参考 99itv_1.py: 优先提取 player_aaaa 并解码"""
        ret = {'parse': 1, 'playUrl': '', 'url': id or '', 'header': ''}
        if not id:
            return ret
        
        full = self._fix_url(id)
        if re.search(r'\.(m3u8|mp4|flv)(\?|$)', full, re.I):
            return {
                'parse': 0,
                'playUrl': '',
                'url': full,
                'header': self._media_header(self.host + '/')
            }
        
        html = self._fetch(full)
        if html:
            # 方法1: player_aaaa 提取 (增加 </script> 边界)
            m = re.search(r'var\s+player_aaaa\s*=\s*(\{[\s\S]*?\})\s*</script>', html, re.I)
            if not m:
                m = re.search(r'var\s+player_\w+\s*=\s*(\{[\s\S]*?\})\s*;', html, re.I)
            if m:
                try:
                    data = json.loads(m.group(1))
                    purl = data.get('url', '')
                    encrypt = data.get('encrypt', 0)
                    if purl:
                        purl = self._decode_player_url(purl, encrypt)
                        if re.search(r'\.(m3u8|mp4|flv)(\?|$)', purl, re.I):
                            return {
                                'parse': 0,
                                'playUrl': '',
                                'url': purl,
                                'header': self._media_header(full)
                            }
                        if purl:
                            return {
                                'parse': 1,
                                'playUrl': '',
                                'url': purl,
                                'header': self._media_header(full)
                            }
                except Exception as e:
                    pass
            
            # 方法2: iframe 递归
            im = re.search(r'<iframe[^>]+src="([^"]+)"', html, re.I)
            if im:
                return self.playerContent(flag, self._fix_url(im.group(1)), vipFlags)
            
            # 方法3: 全文搜索 m3u8
            mm = re.search(r'(https?://[^\s"\']+?\.(?:m3u8|mp4|flv)[^\s"\']*)', html, re.I)
            if mm:
                return {
                    'parse': 0,
                    'playUrl': '',
                    'url': mm.group(1).replace('\\/', '/'),
                    'header': self._media_header(full)
                }
        
        ret['url'] = full
        ret['header'] = self._media_header(full)
        return ret

    def localProxy(self, params):
        pass


# 兼容性函数
def getSpider():
    return Spider()

def getHomeContent():
    return Spider().homeContent()

def getHomeVideoContent():
    return Spider().homeVideoContent()

def getCategoryContent(tid, pg=1, filter=False, extend=None):
    return Spider().categoryContent(tid, pg, filter, extend)

def getDetailContent(ids):
    return Spider().detailContent(ids)

def getSearchContent(key, quick=False, pg=1):
    return Spider().searchContent(key, quick, pg)

def getPlayerContent(flag, id, vipFlags=None):
    return Spider().playerContent(flag, id, vipFlags)

def getDependence():
    return Spider().getDependence()

def destroy():
    return Spider().destroy()