import sys
import re
import requests
from urllib.parse import urljoin, urlparse
import base64

class Spider():
    host = "https://www.dianying102.xyz"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host
        }
        self.timeout = 15
        self.session = requests.Session()
        
    def getName(self):
        return "电影102"
    
    def getDependence(self):
        """返回依赖模块列表"""
        return []
    
    def init(self, extend=""):
        return ""

    def fetch(self, url, retry=3):
        """带重试机制的请求函数"""
        for i in range(retry):
            try:
                rsp = self.session.get(url, headers=self.headers, timeout=self.timeout)
                if rsp.status_code == 200:
                    return rsp
            except:
                if i == retry - 1:
                    return None
                continue
        return None

    def homeContent(self, filter):
        """首页内容 - 根据实际网站分类"""
        # 从网站获取的实际分类
        class_list = [
            {"type_id": "28", "type_name": "电影"},
            {"type_id": "24", "type_name": "国产剧"},
            {"type_id": "20", "type_name": "日剧"},
            {"type_id": "21", "type_name": "韩剧"},
            {"type_id": "2", "type_name": "欧美剧"},
            {"type_id": "22", "type_name": "台剧"},
            {"type_id": "23", "type_name": "港剧"},
            {"type_id": "25", "type_name": "泰剧"},
            {"type_id": "27", "type_name": "其他剧"},
            {"type_id": "26", "type_name": "日漫"},
            {"type_id": "29", "type_name": "国漫"},
            {"type_id": "32", "type_name": "欧美漫"},
            {"type_id": "31", "type_name": "综艺"},
            {"type_id": "34", "type_name": "纪录片"},
            {"type_id": "35", "type_name": "伦理片"},
            {"type_id": "36", "type_name": "短剧"}
        ]
        
        recommend_list = []
        rsp = self.fetch(self.host)
        if rsp:
            recommend_list = self.parse_list(rsp.text)
        
        return {
            'class': class_list,
            'list': recommend_list[:20]
        }

    def homeVideoContent(self):
        """首页视频内容"""
        result = self.homeContent(False)
        return result.get('list', [])

    def categoryContent(self, tid, pg, filter, extend):
        """分类列表页"""
        if pg == 1:
            url = f"{self.host}/index.php/vod/type/id/{tid}.html"
        else:
            url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
        
        rsp = self.fetch(url)
        if not rsp:
            return {
                'list': [],
                'page': int(pg),
                'pagecount': 1,
                'limit': 20,
                'total': 0
            }
        
        video_list = self.parse_list(rsp.text)
        pagecount = self.parse_pagecount(rsp.text)
        
        if pagecount < int(pg):
            pagecount = int(pg)
        
        total = pagecount * 20
        
        return {
            'list': video_list,
            'page': int(pg),
            'pagecount': pagecount,
            'limit': 20,
            'total': total
        }

    def detailContent(self, ids):
        """视频详情页"""
        vod_id = ids[0]
        url = f"{self.host}/index.php/vod/detail/id/{vod_id}.html"
        
        rsp = self.fetch(url)
        if not rsp:
            return {"list": []}
        
        html = rsp.text
        
        vod = {
            "vod_id": vod_id,
            "vod_name": self.extract_info(html, r'<h1[^>]*class="title"[^>]*>([^<]+)</h1>') or 
                       self.extract_info(html, r'<h1[^>]*>([^<]+)</h1>'),
            "vod_pic": self.extract_pic(html),
            "type_name": self.extract_info(html, r'分类[：:]\s*</span>\s*<[^>]*>([^<]+)</a>') or 
                        self.extract_info(html, r'类型[：:]\s*([^<]+)'),
            "vod_year": self.extract_info(html, r'年份[：:]\s*</span>\s*<[^>]*>([^<]+)</a>') or 
                       self.extract_info(html, r'年份[：:]\s*([^<]+)'),
            "vod_area": self.extract_info(html, r'地区[：:]\s*</span>\s*<[^>]*>([^<]+)</a>') or 
                       self.extract_info(html, r'地区[：:]\s*([^<]+)'),
            "vod_remarks": self.extract_remarks(html),
            "vod_actor": self.extract_actor(html),
            "vod_director": self.extract_director(html),
            "vod_content": self.extract_content(html)
        }
        
        play_from, play_url = self.extract_playlist(html)
        vod["vod_play_from"] = play_from
        vod["vod_play_url"] = play_url
        
        return {"list": [vod]}

    def searchContent(self, key, quick, pg=1):
        """搜索功能"""
        url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{key}.html"
        
        rsp = self.fetch(url)
        if not rsp:
            return {"list": []}
        
        video_list = self.parse_list(rsp.text)
        pagecount = self.parse_pagecount(rsp.text)
        
        return {
            'list': video_list,
            'page': int(pg),
            'pagecount': pagecount,
            'limit': 20,
            'total': pagecount * 20
        }

    def playerContent(self, flag, id, vipFlags):
        """播放地址解析"""
        if id.startswith('http'):
            play_url = id
        elif id.startswith('/'):
            play_url = urljoin(self.host, id)
        else:
            play_url = f"{self.host}/index.php/vod/play/id/{id}.html"
        
        rsp = self.fetch(play_url)
        if not rsp:
            return {"parse": 1, "url": play_url}
        
        html = rsp.text
        video_url = self.extract_video_url(html)
        
        if video_url:
            return {"parse": 0, "url": video_url}
        
        iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', html)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            if iframe_url.startswith('//'):
                iframe_url = 'https:' + iframe_url
            elif iframe_url.startswith('/'):
                iframe_url = urljoin(self.host, iframe_url)
            
            rsp2 = self.fetch(iframe_url)
            if rsp2:
                video_url = self.extract_video_url(rsp2.text)
                if video_url:
                    return {"parse": 0, "url": video_url}
        
        parsers = [
            f"https://jx.aidouer.net/?url={play_url}",
            f"https://jx.playerjy.com/?url={play_url}",
            f"https://jx.bozrc.com:4433/player/?url={play_url}"
        ]
        
        return {"parse": 0, "url": parsers[0]}

    def extract_video_url(self, html):
        """从HTML中提取视频URL"""
        patterns = [
            r'(https?://[^\s\'"]+\.(?:m3u8|mp4|flv|mkv|avi)[^\s\'"]*)',
            r'<video[^>]*src="([^"]+\.(?:m3u8|mp4)[^"]*)"',
            r'data-url="([^"]+\.(?:m3u8|mp4)[^"]*)"',
            r'url[\s]*:[\s]*[\'"]([^\'"]+\.(?:m3u8|mp4)[^\'"]*)[\'"]',
            r'videoUrl[\s]*:[\s]*[\'"]([^\'"]+)[\'"]',
            r'playUrl[\s]*:[\s]*[\'"]([^\'"]+)[\'"]',
            r'atob\([\'"]([^\'"]+)[\'"]\)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.I)
            if matches:
                url = matches[0]
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    url = urljoin(self.host, url)
                return url
        
        b64_pattern = r'Base64\.decode\([\'"]([A-Za-z0-9+/=]+)[\'"]\)'
        b64_match = re.search(b64_pattern, html)
        if b64_match:
            try:
                decoded = base64.b64decode(b64_match.group(1)).decode('utf-8')
                if 'http' in decoded:
                    return decoded
            except:
                pass
        
        return None

    def parse_list(self, html, is_recommend=False):
        """解析视频列表 - 修复角标"""
        video_list = []
        
        # 查找所有视频项，直接包含角标
        pattern = r'<a[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*data-original="([^"]+)"[^>]*>.*?<span[^>]*class="pic-text[^"]*"[^>]*>([^<]+)</span>'
        matches = re.findall(pattern, html, re.S)
        
        for match in matches:
            href = match[0]
            title = match[1]
            pic = match[2]
            remark = match[3].strip() if len(match) > 3 else ""
            
            vid = self.extract_vod_id(href)
            if not vid:
                continue
            
            if pic:
                if pic.startswith('//'):
                    pic = 'https:' + pic
                elif pic.startswith('/'):
                    pic = urljoin(self.host, pic)
            
            video_list.append({
                "vod_id": vid,
                "vod_name": title.strip(),
                "vod_pic": pic,
                "vod_remarks": remark
            })
        
        # 如果没有找到带角标的，尝试不带角标的并单独提取角标
        if not video_list:
            pattern2 = r'<a[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*data-original="([^"]+)"[^>]*>'
            matches2 = re.findall(pattern2, html, re.S)
            
            for match in matches2:
                href = match[0]
                title = match[1]
                pic = match[2]
                
                vid = self.extract_vod_id(href)
                if not vid:
                    continue
                
                if pic:
                    if pic.startswith('//'):
                        pic = 'https:' + pic
                    elif pic.startswith('/'):
                        pic = urljoin(self.host, pic)
                
                # 单独提取角标
                remark = ""
                # 在当前视频项附近查找角标
                context = html[html.find(href)-200:html.find(href)+500]
                remark_match = re.search(r'<span[^>]*class="pic-text[^"]*"[^>]*>([^<]+)</span>', context)
                if remark_match:
                    remark = remark_match.group(1).strip()
                
                video_list.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
        
        return video_list

    def parse_pagecount(self, html):
        """解析总页数"""
        match = re.search(r'共(\d+)页', html)
        if match:
            return int(match.group(1))
        
        page_links = re.findall(r'<a[^>]*href="[^"]*/page/(\d+)\.html"', html)
        if page_links:
            pages = [int(p) for p in page_links]
            return max(pages)
        
        last_page = re.search(r'<a[^>]*href="[^"]*/page/(\d+)\.html"[^>]*>尾页', html)
        if last_page:
            return int(last_page.group(1))
        
        numbers = re.findall(r'<li[^>]*class="[^"]*page-item[^"]*"[^>]*>.*?<a[^>]*>(\d+)</a>', html)
        if numbers:
            nums = [int(n) for n in numbers]
            return max(nums)
        
        return 1

    def extract_vod_id(self, href):
        """从链接中提取视频ID"""
        patterns = [
            r'/id/(\d+)\.html',
            r'/(\d+)\.html',
            r'id=(\d+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, href)
            if match:
                return match.group(1)
        return ""

    def extract_info(self, html, pattern):
        """提取信息辅助函数"""
        match = re.search(pattern, html, re.S)
        return match.group(1).strip() if match else ""

    def extract_pic(self, html):
        """提取封面图"""
        patterns = [
            r'data-original="([^"]+)"',
            r'<img[^>]*src="([^"]+)"[^>]*class="[^"]*myui-vodlist__thumb[^"]*"',
            r'<img[^>]*src="([^"]+)"[^>]*>'
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                pic = match.group(1)
                if pic.startswith('//'):
                    return 'https:' + pic
                elif pic.startswith('/'):
                    return urljoin(self.host, pic)
                return pic
        return ""

    def extract_remarks(self, html):
        """提取备注信息"""
        patterns = [
            r'更新[：:]\s*</span>\s*([^<]+)',
            r'状态[：:]\s*([^<]+)',
            r'<span[^>]*class="pic-text[^"]*"[^>]*>([^<]+)</span>'
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1).strip()
        return ""

    def extract_actor(self, html):
        """提取演员"""
        patterns = [
            r'主演[：:]\s*</span>\s*([^<]+)',
            r'演员[：:]\s*([^<]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.S)
            if match:
                return re.sub(r'\s+', '', match.group(1).strip())
        return ""

    def extract_director(self, html):
        """提取导演"""
        patterns = [
            r'导演[：:]\s*</span>\s*([^<]+)',
            r'导演[：:]\s*([^<]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.S)
            if match:
                return re.sub(r'\s+', '', match.group(1).strip())
        return ""

    def extract_content(self, html):
        """提取简介"""
        patterns = [
            r'简介[：:]\s*</span>\s*([^<]+)',
            r'剧情[：:]\s*([^<]+)',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>([^<]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.S)
            if match:
                return match.group(1).strip()
        return ""

    def extract_playlist(self, html):
        """提取播放列表"""
        play_from_list = []
        play_url_list = []
        
        sections = re.findall(r'<ul[^>]*class="[^"]*myui-content__list[^"]*"[^>]*>(.*?)</ul>', html, re.S)
        
        if sections:
            for idx, section in enumerate(sections):
                from_name = f"线路{idx+1}"
                from_match = re.search(r'<h4[^>]*>([^<]+)</h4>', html[:html.find(section)])
                if from_match:
                    from_name = from_match.group(1).strip()
                
                episodes = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', section)
                if episodes:
                    episode_list = []
                    for href, name in episodes:
                        play_id = self.extract_play_id(href)
                        if play_id:
                            episode_list.append(f"{name.strip()}${play_id}")
                    
                    if episode_list:
                        play_from_list.append(from_name)
                        play_url_list.append("#".join(episode_list))
        
        if not play_from_list:
            all_links = re.findall(r'<a[^>]*href="(/index.php/vod/play/[^"]+)"[^>]*>([^<]+)</a>', html)
            play_links = []
            for href, name in all_links:
                if 'play' in href:
                    play_id = self.extract_play_id(href)
                    if play_id:
                        play_links.append(f"{name.strip()}${play_id}")
            
            if play_links:
                play_from_list.append("默认线路")
                play_url_list.append("#".join(play_links))
        
        return "$$$".join(play_from_list), "$$$".join(play_url_list)

    def extract_play_id(self, href):
        """从播放链接中提取播放标识"""
        if 'id/' in href:
            id_match = re.search(r'id/(\d+)/sid/(\d+)/nid/(\d+)', href)
            if id_match:
                return f"{id_match.group(1)}-{id_match.group(2)}-{id_match.group(3)}"
        return href