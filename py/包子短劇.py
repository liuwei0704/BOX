# 包子短剧 Spider (baoziduanju.com)
import sys
import re
import json
import urllib.parse
from urllib.parse import urljoin, quote

class Spider:
    def __init__(self):
        self.site_url = "https://baoziduanju.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': self.site_url
        }
        
        self.categories = [
            {"type_id": "1", "type_name": "系统觉醒", "url": "/category/系统觉醒.html"},
            {"type_id": "2", "type_name": "穿越重生", "url": "/category/穿越重生.html"},
            {"type_id": "3", "type_name": "都市逆袭", "url": "/category/都市逆袭.html"},
            {"type_id": "4", "type_name": "古风权谋", "url": "/category/古风权谋.html"},
            {"type_id": "5", "type_name": "总裁娇妻", "url": "/category/总裁娇妻.html"},
            {"type_id": "6", "type_name": "玄幻仙侠", "url": "/category/玄幻仙侠.html"},
            {"type_id": "7", "type_name": "奇幻科幻", "url": "/category/奇幻科幻.html"}
        ]

    def init(self, cfg=None):
        pass

    def getDependence(self):
        return []

    def getClass(self):
        result = []
        for cat in self.categories:
            result.append({
                "type_id": self.site_url + cat["url"],
                "type_name": cat["type_name"]
            })
        return result

    def _fetch(self, url, is_json=False):
        import urllib.request
        try:
            parsed = urllib.parse.urlparse(url)
            path_parts = parsed.path.split('/')
            encoded_path = '/'.join(quote(p) if p and not re.match(r'^[a-zA-Z0-9\-_.~]+$', p) else p for p in path_parts)
            encoded_url = urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, encoded_path, 
                parsed.params, parsed.query, parsed.fragment
            ))
            
            req = urllib.request.Request(encoded_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
                if is_json:
                    return json.loads(content)
                return content
        except Exception as e:
            return None if not is_json else {}

    def fix_url(self, url):
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        return urljoin(self.site_url, url)

    def extract_list(self, html):
        result = []
        seen = set()
        if not html or 'video-card' not in html:
            return result
        
        pattern = r'<a\s+href="(/video/\d+\.html)"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*video-duration[^"]*"[^>]*>([^<]+)</div>.*?<div[^>]*class="[^"]*video-title[^"]*"[^>]*>([^<]+)</div>'
        
        for href, pic, duration, title in re.findall(pattern, html, re.DOTALL):
            url = self.fix_url(href)
            if url in seen:
                continue
            seen.add(url)
            
            result.append({
                "vod_id": url,
                "vod_name": title.strip(),
                "vod_pic": self.fix_url(pic),
                "vod_remarks": duration.strip()
            })
        
        return result

    def homeContent(self, filter=False):
        class_list = self.getClass()
        html = self._fetch(self.site_url + "/")
        video_list = self.extract_list(html) if html else []
        return {
            "class": class_list,
            "list": video_list
        }

    def homeVideoContent(self):
        return self.homeContent()

    def categoryContent(self, tid, pg=1, filter=False, extend={}):
        p = int(pg) if pg else 1
        
        if p > 1:
            if tid.endswith('.html'):
                url = tid.replace('.html', f'/page/{p}.html')
            else:
                url = tid + f'/page/{p}'
        else:
            url = tid
        
        html = self._fetch(url)
        if not html:
            return {"list": []}
        
        vod_list = self.extract_list(html)
        
        return {
            "list": vod_list,
            "page": p,
            "pagecount": 20
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        
        url = ids[0]
        if not url.startswith("http"):
            url = self.fix_url(url)
        
        html = self._fetch(url)
        if not html:
            return {"list": []}
        
        # 标题
        title = "短剧"
        t = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        if t:
            title = re.sub(r'<[^>]+>', '', t.group(1)).strip()
            title = title.split('-')[0].strip()
        
        # 封面
        pic = ""
        p = re.search(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))["\']', html)
        if p:
            pic = self.fix_url(p.group(1))
        
        # 提取播放地址
        play_urls = []
        
        # 从 vodPlayUrl 提取
        for m in re.finditer(r"vodPlayUrl\s*=\s*['\"](.*?)['\"]", html):
            raw = m.group(1).replace('\\/', '/')
            if '$' in raw:
                parts = raw.split('$', 1)
                name = parts[0].strip()
                url_play = parts[1] if len(parts) > 1 else raw
                if url_play and '.m3u8' in url_play:
                    play_urls.append({"name": name or "正片", "url": url_play})
            elif '.m3u8' in raw:
                play_urls.append({"name": "正片", "url": raw})
        
        # 从选集列表提取
        if not play_urls:
            ep_pattern = r'<a[^>]+href="(/watch/\d+_\d+\.html)"[^>]*>.*?第(\d+)集'
            for href, ep_num in re.findall(ep_pattern, html):
                play_urls.append({
                    "name": f"第{ep_num}集",
                    "url": self.fix_url(href)
                })
        
        if not play_urls:
            play_urls.append({"name": "正片", "url": url})
        
        play_url_str = "#".join([f"{item['name']}${item['url']}" for item in play_urls])
        
        # 备注
        remark = "已完结"
        r = re.search(r'<div[^>]*class="[^"]*video-duration[^"]*"[^>]*>(.*?)</div>', html)
        if r:
            remark = r.group(1).strip()
        
        vod = {
            "vod_id": url,
            "vod_name": title,
            "vod_pic": pic,
            "vod_play_from": "包子专线",
            "vod_play_url": play_url_str,
            "vod_content": remark,
            "vod_remarks": remark
        }
        
        return {"list": [vod]}

    def searchContent(self, key, quick=False, pg=1):
        """
        搜索功能 - 使用API: /api/videos/search
        """
        p = int(pg) if pg else 1
        encoded = quote(key)
        url = f"{self.site_url}/api/videos/search?q={encoded}&page={p}&limit=20"
        
        data = self._fetch(url, is_json=True)
        if not data or data.get('code') != 200:
            return {"list": []}
        
        videos = data.get('data', {}).get('videos', [])
        result = []
        
        for v in videos:
            vid = str(v.get('vod_id', ''))
            if not vid:
                continue
            
            # 构造视频URL
            vod_url = f"/video/{vid}.html"
            
            # 提取播放地址（如果有）
            play_url = v.get('vod_play_url', '')
            
            result.append({
                "vod_id": vod_url,
                "vod_name": v.get('vod_name', '短剧'),
                "vod_pic": self.fix_url(v.get('vod_pic', '')),
                "vod_remarks": v.get('vod_remarks', '已完结')
            })
        
        return {"list": result}

    def playerContent(self, flag, id, vipFlags=[]):
        return {"parse": 0, "playUrl": id}

    def destroy(self):
        pass