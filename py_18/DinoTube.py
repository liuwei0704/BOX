# coding=utf-8
import sys
import re
import requests
import json
from bs4 import BeautifulSoup

# 导入基础类
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    host = "https://www.dinotube.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': "https://www.dinotube.com/zh/",
    }

    def getName(self):
        return "DinoTube (蜂蜜专用)"

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        result = {}
        # 预设中文分类，优化 type_id 对应关系
        result['class'] = [
            {"type_name": u"\u70ed\u95e8", "type_id": "popular"},
            {"type_name": u"\u65e5\u672c\u7684", "type_id": "category/japanese"},
            {"type_name": u"\u4e2d\u56fd\u7684", "type_id": "category/chinese"},
            {"type_name": u"\u97e9\u56fd\u7684", "type_id": "category/korean"},
            {"type_name": u"\u65e0\u7801", "type_id": "category/uncensored"},
            {"type_name": u"\u52a8\u6f2b", "type_id": "category/hentai"},
            {"type_name": u"\u7d20\u4eba", "type_id": "category/homemade-amateur"}
        ]
        
        # 首页推荐直接调用热门视频
        url = f"{self.host}/zh/popular"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            result['list'] = self.parseList(res.text)
        except Exception:
            result['list'] = []
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        # 翻页处理
        url = f"{self.host}/zh/{tid}?page={pg}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            result['list'] = self.parseList(res.text)
            result['page'] = int(pg)
            result['pagecount'] = 999
            result['limit'] = 20
            result['total'] = 9999
        except Exception:
            result['list'] = []
        return result

    def detailContent(self, ids):
        id = ids[0]
        # 处理重定向链接
        url = f"{self.host}{id}" if id.startswith("/") else id
        
        try:
            # allow_redirects=True 会自动跟随到最终的视频详情页 (如 fhgte.com 或 xh.partners)
            res = requests.get(url, headers=self.headers, timeout=10, allow_redirects=True)
            final_url = res.url
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 兼容不同站点的标题抓取
            title = soup.find(['h1', 'title'])
            name = title.get_text(strip=True) if title else "Video"
            
            pic = ""
            og_img = soup.find('meta', property="og:image")
            if og_img: pic = og_img['content']

            # 重点：构建播放地址。由于 final_url 是最终页面，我们将它传给 playerContent
            vod = {
                "vod_id": id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": "点击播放",
                "vod_content": f"来源页面: {final_url}",
                "vod_play_from": "DinoPlayer",
                "vod_play_url": f"立即播放${final_url}"
            }
            return {"list": [vod]}
        except Exception as e:
            return {"list": [{"vod_name": "解析失败", "vod_content": str(e)}]}

    def searchContent(self, key, quick, pg=1):
        url = f"{self.host}/zh/search?q={key}&page={pg}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            return {"list": self.parseList(res.text)}
        except Exception:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        # 修正：如果 id 已经是完整链接（http开头），则不再拼接 host
        url = id if id.startswith("http") else f"{self.host}{id}"
        
        try:
            headers = self.headers.copy()
            headers['Referer'] = url # 必须带上来源，防止 403
            
            res = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            final_url = res.url
            html = res.text
            
            # 1. 扫描 HLS/m3u8 直链
            m3u8_match = re.search(r'["\'](https?[:\\/\w\.-]+\.m3u8[^"\']*)["\']', html)
            if m3u8_match:
                video_url = m3u8_match.group(1).replace('\\/', '/')
                return {"parse": 0, "url": video_url, "header": {"Referer": final_url}}
            
            # 2. 扫描 MP4 直链
            mp4_match = re.search(r'["\'](https?[:\\/\w\.-]+\.mp4[^"\']*)["\']', html)
            if mp4_match:
                video_url = mp4_match.group(1).replace('\\/', '/')
                return {"parse": 0, "url": video_url, "header": {"Referer": final_url}}

            # 3. 扫描 JSON 变量 (针对加密站点)
            json_match = re.search(r'["\'](?:hls|file|url|src)["\']\s*:\s*["\'](https?.*?)["\']', html)
            if json_match:
                video_url = json_match.group(1).replace('\\/', '/')
                return {"parse": 0, "url": video_url, "header": {"Referer": final_url}}

            # 4. 保底：让系统嗅探
            return {"parse": 1, "url": final_url, "header": ""}
        except Exception:
            return {"parse": 1, "url": url, "header": ""}
        url = f"{self.host}{id}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            # 兼容多种常见的播放地址匹配模式
            match = re.search(r'video_url:\s*\'(.*?)\'', res.text)
            if not match:
                match = re.search(r'source:\s*"(.*?)"', res.text)
            if not match:
                match = re.search(r'\"(https?.*?\.m3u8.*?)\"', res.text)
            
            if match:
                video_url = match.group(1).replace('\/', '/')
                return {"parse": 0, "url": video_url, "header": {"Referer": self.host}}
            
            return {"parse": 1, "url": url, "header": ""}
        except Exception:
            return {"parse": 1, "url": url, "header": ""}

    def parseList(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        vods = []
        seen_ids = set()
        
        # 寻找所有的 card 容器
        items = soup.find_all('div', class_=re.compile(r'card'))
        
        for item in items:
            # 重点：提取 a 标签，该站链接可能包含 /out/ 或 /zh/video/
            a_tag = item.find('a', class_=re.compile(r'link'))
            if not a_tag:
                a_tag = item.find('a', href=True)
            
            if not a_tag: continue
            
            href = a_tag.get('href', '')
            # 兼容该站特有的 /out/?l= 链接或标准的 video 链接
            if not ("/video/" in href or "/out/" in href): continue
            
            # 使用 public-id 或 href 作为唯一标识
            pid = item.get('data-public-id') or href
            if pid in seen_ids: continue

            # 提取名称和图片
            img = item.find('img')
            name = ""
            pic = ""
            if img:
                name = img.get('alt') or img.get('title')
                pic = img.get('data-src') or img.get('src') or img.get('data-thumb', '')
            
            if not name:
                # 尝试寻找兄弟节点或内部文本
                name_node = item.find('div', class_=re.compile(r'title|name'))
                name = name_node.get_text(strip=True) if name_node else a_tag.get_text(strip=True)

            # 格式化地址
            if pic.startswith("//"): pic = "https:" + pic
            elif pic.startswith("/") and not pic.startswith("//"): pic = self.host + pic
            
            # 过滤干扰项
            if len(name) < 2: name = "DinoVideo_" + (pid[-5:] if pid else "Raw")

            vods.append({
                "vod_id": href,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": item.get_text(strip=True)[:10] if not img else ""
            })
            seen_ids.add(pid)
            
        # 暴力保底：如果 BeautifulSoup 还是没抓到，直接正则扫 /out/ 链接
        if not vods:
            out_links = re.findall(r'href="(/out/\?l=[^"]+)"', html)
            for l in out_links:
                if l not in seen_ids:
                    vods.append({"vod_id": l, "vod_name": "External Video", "vod_pic": "", "vod_remarks": ""})
                    seen_ids.add(l)
                    
        return vods