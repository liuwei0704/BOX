# 电影人生 Spider (dyrsok.org) - 修复标题提取
import re
import json
import urllib.request
import urllib.parse
import gzip
from io import BytesIO
from urllib.parse import urljoin

class Spider:
    def __init__(self):
        self.site_url = "https://www.dyrsok.org"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.site_url
        }
        
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

    def fetch(self, url):
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                if resp.headers.get('Content-Encoding') == 'gzip':
                    buf = BytesIO(raw)
                    with gzip.GzipFile(fileobj=buf) as gz:
                        return gz.read().decode('utf-8', errors='ignore')
                return raw.decode('utf-8', errors='ignore')
        except Exception as e:
            return ""

    def fix_url(self, url):
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        return urljoin(self.site_url, url)

    def extract_vod_list(self, html):
        result = []
        items = re.findall(r'<div class="[^"]*relative group[^"]*"[^>]*>(.*?)</div>\s*(?=<div|<a|</section|</main)', html, re.DOTALL)
        for item in items:
            try:
                a_match = re.search(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>', item)
                if not a_match:
                    continue
                url = self.fix_url(a_match.group(1))
                if not re.search(r'/dyrsorg-\d+/', url):
                    continue
                
                title = ""
                h3_match = re.search(r'<h3[^>]*>(.*?)</h3>', item, re.DOTALL)
                if h3_match:
                    title = re.sub(r'<[^>]+>', '', h3_match.group(1)).strip()
                if not title:
                    title_match = re.search(r'title=["\']([^"\']+)["\']', a_match.group(0))
                    if title_match:
                        title = title_match.group(1)
                if not title:
                    continue
                
                pic = ""
                img_match = re.search(r'<img[^>]*data-src=["\']([^"\']+)["\']', item)
                if img_match:
                    pic = self.fix_url(img_match.group(1))
                
                remark = ""
                r1 = re.search(r'<div[^>]*backdrop-blur-sm[^>]*>(.*?)</div>', item, re.DOTALL)
                if r1:
                    remark = re.sub(r'<[^>]+>', '', r1.group(1)).strip()
                if not remark:
                    r2 = re.search(r'(\d+集)', item)
                    if r2:
                        remark = r2.group(1)
                if not remark:
                    r3 = re.search(r'(1080P|720P|4K|HD)', item, re.IGNORECASE)
                    if r3:
                        remark = r3.group(1).upper()
                
                result.append({
                    "vod_id": url,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
                if len(result) >= 20:
                    break
            except:
                continue
        return result

    def homeContent(self, filter=False):
        result = {"class": [], "list": []}
        for tid, info in self.categories.items():
            item = {"type_id": tid, "type_name": info["name"]}
            if filter and tid in self.filters:
                item["filters"] = self.filters[tid]
            result["class"].append(item)
        
        html = self.fetch(self.site_url + "/")
        if html:
            result["list"] = self.extract_vod_list(html)
        return result

    def homeVideoContent(self):
        return self.homeContent(filter=False)

    def categoryContent(self, tid, pg=1, filter=False, extend={}):
        p = int(pg) - 1
        info = self.categories.get(tid)
        if not info:
            return {"list": []}
        
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
        
        return {
            "list": self.extract_vod_list(html),
            "page": pg,
            "pagecount": 1,
            "total": 0
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
        
        # 修复标题提取
        title = ""
        # 方法1: 从 flex-grow 区域的 h1 提取
        h1_match = re.search(r'<div[^>]*flex-grow[^>]*>.*?<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        if h1_match:
            title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
        # 方法2: 从 h1 提取（排除站点名）
        if not title:
            h1_match2 = re.search(r'<h1[^>]*>(.*?)</h1>', html)
            if h1_match2:
                candidate = re.sub(r'<[^>]+>', '', h1_match2.group(1)).strip()
                if candidate and "电影人生" not in candidate:
                    title = candidate
        # 方法3: 从 og:title 提取
        if not title:
            og_match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html)
            if og_match:
                title = og_match.group(1).split('-')[0].strip()
        # 方法4: 从 title 标签提取
        if not title:
            title_match = re.search(r'<title>(.*?)</title>', html)
            if title_match:
                title = title_match.group(1).split('-')[0].strip()
        
        # 图片
        pic = ""
        img_match = re.search(r'<img[^>]*data-src=["\']([^"\']+)["\']', html)
        if img_match:
            pic = self.fix_url(img_match.group(1))
        
        # 简介
        desc = ""
        desc_match = re.search(r'<div[^>]*bg-gray-50[^>]*text-justify[^>]*>(.*?)</div>', html, re.DOTALL)
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
        
        # 年份、类型
        year = ""
        type_name = ""
        tags = re.findall(r'<span[^>]*bg-gray-100[^>]*>(.*?)</span>', html)
        if len(tags) >= 1:
            type_name = re.sub(r'<[^>]+>', '', tags[0]).strip()
        if len(tags) >= 2:
            year = re.sub(r'<[^>]+>', '', tags[1]).strip()
        
        # 获取线路
        origins = []
        origin_btns = re.findall(r'<button[^>]*data-origin=["\']([^"\']+)["\'][^>]*>', html)
        for origin in origin_btns:
            if origin and origin not in origins:
                origins.append(origin)
        if not origins:
            origins = ["超级线路"]
        
        # 获取剧集
        eps = []
        ep_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*class="[^"]*list-item[^"]*"[^>]*>', html)
        for i, href in enumerate(ep_links):
            p_match = re.search(r'[?&]p=(\d+)', href)
            p = p_match.group(1) if p_match else str(i)
            ep_name = "第" + str(i+1) + "集"
            ep_title_match = re.search(r'data-title=["\']([^"\']+)["\']', href)
            if ep_title_match:
                ep_name = ep_title_match.group(1)
            eps.append({"name": ep_name, "p": p, "href": href})
        
        if not eps:
            eps = [{"name": "正片", "p": "0", "href": ""}]
        
        play_from = []
        play_url_parts = []
        for origin in origins:
            play_from.append(origin)
            ep_parts = []
            for ep in eps:
                if ep["href"]:
                    ep_link = self.site_url + ep["href"]
                else:
                    ep_link = self.site_url + url.split("/")[-1] + "?origin=" + origin + "&p=" + ep["p"]
                ep_parts.append(ep["name"] + "$" + ep_link)
            play_url_parts.append("#".join(ep_parts))
        
        return {"list": [{
            "vod_id": url,
            "vod_name": title,
            "vod_pic": pic,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url_parts),
            "vod_year": year,
            "vod_type": type_name,
            "vod_content": desc
        }]}

    def searchContent(self, key, quick=False, pg=1):
        p = int(pg) - 1
        url = self.site_url + "/s.html?name=" + urllib.parse.quote(key) + "&page=" + str(p)
        html = self.fetch(url)
        if not html:
            return {"list": []}
        return {"list": self.extract_vod_list(html)}

    def playerContent(self, flag, id, vipFlags=[]):
        html = self.fetch(id)
        if not html:
            return {"parse": 0, "playUrl": id}
        
        preload_match = re.search(r'<link rel="preload" href="([^"]+)"', html)
        if preload_match:
            m3u8_url = self.fix_url(preload_match.group(1))
            m3u8_url = m3u8_url.replace('&amp;', '&')
            return {"parse": 0, "playUrl": m3u8_url}
        
        vod_list_match = re.search(r'dyrs_vod_list\s*=\s*JSON\.parse\([\'"](.*?)[\'"]\)', html)
        if vod_list_match:
            try:
                json_str = vod_list_match.group(1).replace('\\"', '"').replace('\\\\', '\\')
                data = json.loads(json_str)
                if data and len(data) > 0:
                    m3u8_url = self.fix_url(data[0].get("url", ""))
                    m3u8_url = m3u8_url.replace('&amp;', '&')
                    return {"parse": 0, "playUrl": m3u8_url}
            except:
                pass
        
        return {"parse": 0, "playUrl": id}