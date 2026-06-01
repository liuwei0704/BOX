# 电影人生 Spider (dyrsok.org) - 增强反爬版
import re
import json
import urllib.request
import urllib.parse
import urllib.error
import gzip
import time
import random
from io import BytesIO
from http.cookiejar import CookieJar

class Spider:
    def __init__(self):
        self.site_url = "https://www.dyrsok.org"
        
        # 多个 User-Agent 轮换
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
        
        # 使用 CookieJar 保持会话
        self.cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        
        self.categories = {
            "dianying": {"name": "电影", "url": "/dianying.html"},
            "dianshiju": {"name": "电视剧", "url": "/dianshiju.html"},
            "zongyi": {"name": "综艺", "url": "/zongyi.html"},
            "dongman": {"name": "动漫", "url": "/dongman.html"},
            "duanju": {"name": "短剧", "url": "/duanju.html"}
        }
        
        self.filters = {
            "dianying": [
                {"key": "class", "name": "分类", "value": [
                    {"n": "全部", "v": ""}, {"n": "剧情", "v": "剧情"},
                    {"n": "喜剧", "v": "喜剧"}, {"n": "动作", "v": "动作"},
                    {"n": "爱情", "v": "爱情"}, {"n": "惊悚", "v": "惊悚"},
                    {"n": "犯罪", "v": "犯罪"}, {"n": "悬疑", "v": "悬疑"},
                    {"n": "奇幻", "v": "奇幻"}, {"n": "科幻", "v": "科幻"},
                    {"n": "冒险", "v": "冒险"}, {"n": "战争", "v": "战争"},
                    {"n": "动画", "v": "动画"}, {"n": "古装", "v": "古装"}
                ]},
                {"key": "year", "name": "年份", "value": [
                    {"n": "全部", "v": ""}, {"n": "2026", "v": "2026"},
                    {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"},
                    {"n": "2023", "v": "2023"}, {"n": "2022", "v": "2022"}
                ]},
                {"key": "sort_field", "name": "排序", "value": [
                    {"n": "默认", "v": ""}, {"n": "热度", "v": "play_hot"},
                    {"n": "年份", "v": "year"}
                ]}
            ],
            "dianshiju": [
                {"key": "class", "name": "分类", "value": [
                    {"n": "全部", "v": ""}, {"n": "剧情", "v": "剧情"},
                    {"n": "爱情", "v": "爱情"}, {"n": "喜剧", "v": "喜剧"},
                    {"n": "悬疑", "v": "悬疑"}, {"n": "古装", "v": "古装"},
                    {"n": "都市", "v": "都市"}, {"n": "科幻", "v": "科幻"}
                ]},
                {"key": "year", "name": "年份", "value": [
                    {"n": "全部", "v": ""}, {"n": "2026", "v": "2026"},
                    {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"}
                ]}
            ],
            "zongyi": [
                {"key": "class", "name": "分类", "value": [
                    {"n": "全部", "v": ""}, {"n": "真人秀", "v": "真人秀"},
                    {"n": "综艺", "v": "综艺"}, {"n": "纪录片", "v": "纪录片"}
                ]}
            ],
            "dongman": [
                {"key": "class", "name": "分类", "value": [
                    {"n": "全部", "v": ""}, {"n": "冒险", "v": "冒险"},
                    {"n": "奇幻", "v": "奇幻"}, {"n": "科幻", "v": "科幻"},
                    {"n": "搞笑", "v": "搞笑"}, {"n": "战斗", "v": "战斗"}
                ]}
            ],
            "duanju": [
                {"key": "class", "name": "分类", "value": [
                    {"n": "全部", "v": ""}, {"n": "短剧", "v": "短剧"},
                    {"n": "剧情", "v": "剧情"}, {"n": "爱情", "v": "爱情"},
                    {"n": "爽文", "v": "爽文"}, {"n": "古装", "v": "古装"}
                ]}
            ]
        }

    def init(self, cfg=None):
        pass

    def getDependence(self):
        return []

    def get_random_ua(self):
        return random.choice(self.user_agents)
    
    def random_delay(self):
        """随机延迟，模拟人类行为"""
        time.sleep(random.uniform(1, 3))
    
    def fetch(self, url, retry=3):
        """获取网页内容，支持重试、随机UA、会话保持"""
        for attempt in range(retry):
            try:
                # 随机 User-Agent
                headers = self.headers.copy()
                headers["User-Agent"] = self.get_random_ua()
                headers["Referer"] = self.site_url
                
                # 首次请求访问首页获取cookie
                if attempt == 0 and len(self.cookie_jar) == 0:
                    try:
                        req = urllib.request.Request(self.site_url, headers=headers)
                        self.opener.open(req, timeout=15)
                        self.random_delay()
                    except:
                        pass
                
                # 正式请求
                req = urllib.request.Request(url, headers=headers)
                with self.opener.open(req, timeout=20) as resp:
                    raw = resp.read()
                    if resp.headers.get('Content-Encoding') == 'gzip':
                        buf = BytesIO(raw)
                        with gzip.GzipFile(fileobj=buf) as gz:
                            content = gz.read().decode('utf-8', errors='ignore')
                    else:
                        content = raw.decode('utf-8', errors='ignore')
                    
                    # 随机延迟，避免请求过快
                    self.random_delay()
                    return content
                    
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait_time = (attempt + 1) * 5 + random.uniform(0, 2)
                    print(f"遇到429限流，等待{wait_time:.1f}秒后重试...")
                    time.sleep(wait_time)
                    continue
                print(f"HTTP错误 {e.code}: {url}")
                return ""
            except Exception as e:
                print(f"Fetch error: {e}")
                if attempt < retry - 1:
                    time.sleep(3)
                    continue
                return ""
        return ""
    
    def extract_vod_list(self, html):
        """从HTML中提取视频列表"""
        vod_list = []
        if not html:
            return vod_list
        
        # 多种模式匹配
        patterns = [
            r'<a[^>]*href=["\'](/vod/[^"\']+)["\'][^>]*>.*?<img[^>]*src=["\']([^"\']+)["\'][^>]*>.*?<h3[^>]*>(.*?)</h3>',
            r'<a[^>]*href=["\'](/vod/[^"\']+)["\'][^>]*>.*?<img[^>]*data-src=["\']([^"\']+)["\'][^>]*>.*?<span[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</span>',
            r'<a[^>]*href=["\'](/vod/[^"\']+)["\'][^>]*>.*?<div[^>]*class="[^"]*name[^"]*"[^>]*>(.*?)</div>',
            r'<a[^>]*href=["\'](/vod/[^"\']+)["\'][^>]*>(.*?)</a>'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                for match in matches:
                    try:
                        vod_url = match[0] if match[0].startswith('http') else self.site_url + match[0]
                        pic_url = ""
                        title = ""
                        
                        if len(match) >= 3:
                            pic_url = match[1] if match[1] and (match[1].startswith('http') or match[1].startswith('/')) else ""
                            title = re.sub(r'<[^>]+>', '', match[2]).strip()
                        else:
                            title = re.sub(r'<[^>]+>', '', match[1]).strip()
                        
                        if pic_url and not pic_url.startswith('http'):
                            pic_url = self.site_url + pic_url
                        
                        # 过滤无效标题
                        if title and vod_url and 2 < len(title) < 100:
                            if not any(word in title for word in ['下一页', '加载', '更多', '广告']):
                                vod_list.append({
                                    "vod_id": vod_url,
                                    "vod_name": title,
                                    "vod_pic": pic_url,
                                    "vod_remarks": ""
                                })
                    except:
                        continue
                
                if vod_list:
                    break
        
        # 去重
        seen = set()
        unique_list = []
        for item in vod_list:
            if item["vod_id"] not in seen:
                seen.add(item["vod_id"])
                unique_list.append(item)
        
        return unique_list[:30]

    def homeContent(self, filter=False):
        result = {"class": [], "list": []}
        for tid, info in self.categories.items():
            item = {"type_id": tid, "type_name": info["name"]}
            if filter and tid in self.filters:
                item["filters"] = self.filters[tid]
            result["class"].append(item)
        
        # 获取首页推荐视频
        html = self.fetch(self.site_url + "/")
        if html:
            result["list"] = self.extract_vod_list(html)
        return result

    def homeVideoContent(self):
        return self.homeContent(filter=False)

    def categoryContent(self, tid, pg=1, filter=False, extend={}):
        p = int(pg)
        info = self.categories.get(tid)
        if not info:
            return {"list": []}
        
        # 构建URL
        url = self.site_url + info["url"] + "?page=" + str(p)
        
        if extend.get("class"):
            url += "&class=" + urllib.parse.quote(extend["class"])
        if extend.get("year"):
            url += "&year=" + extend["year"]
        if extend.get("sort_field"):
            url += "&sort_field=" + extend["sort_field"]
        
        html = self.fetch(url)
        if not html:
            return {"list": []}
        
        vod_list = self.extract_vod_list(html)
        
        # 简单分页判断
        pagecount = p + 1 if len(vod_list) >= 20 else p
        
        return {
            "list": vod_list,
            "page": p,
            "pagecount": pagecount,
            "total": len(vod_list)
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        url = ids[0]
        if not url.startswith("http"):
            url = self.site_url + url
        
        html = self.fetch(url)
        if not html:
            return {"list": []}
        
        # 标题提取
        title = ""
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        
        # 图片
        pic = ""
        img_match = re.search(r'<img[^>]*data-src=["\']([^"\']+)["\']', html)
        if img_match:
            pic = img_match.group(1)
            if not pic.startswith('http'):
                pic = self.site_url + pic
        
        # 简介
        desc = ""
        desc_match = re.search(r'<div[^>]*class="[^"]*desc[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
        
        # 获取剧集
        eps = []
        ep_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?(\d+)集', html)
        if not ep_links:
            ep_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html)
        
        for i, ep in enumerate(ep_links[:30]):
            if isinstance(ep, tuple):
                href = ep[0]
                ep_name = ep[1] if len(ep) > 1 else f"第{i+1}集"
            else:
                href = ep
                ep_name = f"第{i+1}集"
            
            ep_link = href if href.startswith('http') else self.site_url + href
            eps.append({"name": ep_name, "url": ep_link})
        
        if not eps:
            eps = [{"name": "正片", "url": url}]
        
        play_from = ["直接播放"]
        play_url = "#".join([f"{ep['name']}${ep['url']}" for ep in eps])
        
        return {"list": [{
            "vod_id": url,
            "vod_name": title,
            "vod_pic": pic,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": play_url,
            "vod_content": desc
        }]}

    def searchContent(self, key, quick=False, pg=1):
        p = int(pg)
        url = self.site_url + "/s.html?name=" + urllib.parse.quote(key) + "&page=" + str(p)
        html = self.fetch(url)
        if not html:
            return {"list": []}
        return {"list": self.extract_vod_list(html)}

    def playerContent(self, flag, id, vipFlags=[]):
        return {"parse": 0, "playUrl": id}