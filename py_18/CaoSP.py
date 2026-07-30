# Caosp影视 Spider - 修复版 v10 (子分类作为筛选器)
import re
import json
import urllib.request
import urllib.parse
from urllib.parse import urljoin

class Spider:
    def __init__(self):
        self.base_url = "https://web.caosp3.cc"
        self.site_url = "/a/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.base_url + "/a/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive"
        }
        
        # 主分类
        self.categories = {
            "244": {"name": "163资源"},
            "358": {"name": "Cao资源"},
            "329": {"name": "裤子资源"},
            "119": {"name": "不卡资源"},
            "286": {"name": "兔儿资源"},
            "370": {"name": "森林资源"}
        }
        
        # 子分类（用于筛选）
        self.sub_categories = {
            "244": ["AV解说", "国产自拍", "熟女人妻", "萝莉少女", "百合剧情", "美乳巨乳", "强歼乱伦", "抖音视频", "韩国主播", "网红头条"],
            "358": ["高清有码", "动漫精选", "学生妹", "中文字幕", "高清无码", "黑料网曝", "主播网红", "乱伦系列", "国产精品", "偷拍自拍"],
            "329": ["日本有码", "无码中文", "有码中文", "日本无码", "国产视频", "欧美高清", "动漫剧情"],
            "119": ["国产视频", "中文字幕", "国产传媒", "日本有码", "日本无码", "欧美无码", "强干乱伦", "制服诱惑", "国产主播", "激情动漫"],
            "286": ["精品推荐", "主播秀色", "日本有码", "日本无码", "中文字幕", "童颜巨乳", "性感人妻", "强歼乱伦", "欧美情色", "三级伦理"],
            "370": ["精品推荐", "国产情色", "亚洲无码", "亚洲有码", "中文字幕", "强*乱伦", "欧美精品", "萝莉少女", "日本精品", "Cosplay"]
        }

    def init(self, cfg=None):
        pass

    def getDependence(self):
        return []

    def fetch(self, url):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                return html
        except Exception as e:
            print(f"fetch error: {e}")
            return ""

    def fix_url(self, url):
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.base_url + url
        return urljoin(self.base_url, url)

    def extract_id_from_url(self, url):
        match = re.search(r'/detail/id/(\d+)\.html', url)
        if match:
            return match.group(1)
        match = re.search(r'/play/id/(\d+)/', url)
        if match:
            return match.group(1)
        match = re.search(r'[?&]id=(\d+)', url)
        if match:
            return match.group(1)
        return url

    def extract_vod_list(self, html):
        result = []
        pattern = r'<a[^>]*class="[^"]*vod-item[^"]*"[^>]*href="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*vod-thumb[^"]*"[^>]*>.*?<img[^>]*(?:data-original|src)="([^"]+)"[^>]*alt="([^"]*)"[^>]*>.*?</div>.*?<div[^>]*class="[^"]*vod-name[^"]*"[^>]*>([^<]*)</div>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for match in matches:
            href, img, alt, name = match
            title = alt if alt and alt.strip() else name
            if not title or not title.strip():
                continue
            vod_id = self.extract_id_from_url(href)
            result.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": self.fix_url(img),
                "vod_remarks": ""
            })
            if len(result) >= 20:
                break
        
        if not result:
            pattern2 = r'<a[^>]*href="([^"]*(?:detail|play)[^"]+)"[^>]*>.*?<img[^>]*(?:data-original|src)="([^"]+)"[^>]*(?:alt="([^"]*)")?.*?<div[^>]*class="[^"]*vod-name[^"]*"[^>]*>([^<]*)</div>'
            matches2 = re.findall(pattern2, html, re.DOTALL)
            for match in matches2:
                href, img, alt, name = match
                title = alt if alt and alt.strip() else name
                if not title or not title.strip():
                    continue
                vod_id = self.extract_id_from_url(href)
                result.append({
                    "vod_id": vod_id,
                    "vod_name": title.strip(),
                    "vod_pic": self.fix_url(img),
                    "vod_remarks": ""
                })
                if len(result) >= 20:
                    break
        
        return result

    def homeContent(self, filter=False):
        result = {"class": [], "list": [], "filters": {}}
        
        # 只返回主分类
        for tid, info in self.categories.items():
            result["class"].append({
                "type_id": tid,
                "type_name": info["name"]
            })
            
            # 如果有子分类，构建筛选器
            if filter and tid in self.sub_categories:
                filters = []
                # 构建子分类选项
                options = [{"n": "全部", "v": ""}]
                for sub in self.sub_categories[tid]:
                    options.append({"n": sub, "v": sub})
                filters.append({
                    "key": "class",
                    "name": "分类",
                    "value": options
                })
                result["filters"][tid] = filters
        
        # 获取首页推荐
        html = self.fetch(self.base_url + self.site_url)
        if html:
            result["list"] = self.extract_vod_list(html)
        
        return result

    def homeVideoContent(self):
        return self.homeContent(filter=False)

    def categoryContent(self, tid, pg=1, filter=False, extend={}):
        p = int(pg)
        
        # 构建URL - 使用主分类ID
        url = f"{self.base_url}/a/index.php/vod/type/id/{tid}/page/{p}.html"
        
        # 如果有筛选参数，添加到URL
        if extend and extend.get("class"):
            # 子分类名称作为筛选参数
            sub_class = extend.get("class")
            # 尝试在URL中添加筛选
            url += f"?class={urllib.parse.quote(sub_class)}"
        
        html = self.fetch(url)
        if not html:
            return {"list": [], "page": p, "pagecount": 1}
        
        vod_list = self.extract_vod_list(html)
        
        has_next = re.search(r'<a[^>]*href="[^"]*page/' + str(p+1) + r'\.html"', html)
        pagecount = p + 1 if has_next else p
        
        return {
            "list": vod_list,
            "page": p,
            "pagecount": pagecount,
            "total": len(vod_list)
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        
        vid = ids[0]
        if "detail/id/" in vid or "play/id/" in vid:
            vid = self.extract_id_from_url(vid)
        
        url = f"{self.base_url}/a/index.php/vod/detail/id/{vid}.html"
        html = self.fetch(url)
        if not html:
            return {"list": []}
        
        # 提取标题
        title = ""
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if title_match:
            title = title_match.group(1).strip()
        if not title:
            title_match = re.search(r'<div[^>]*class="[^"]*video-title[^"]*"[^>]*>([^<]+)</div>', html)
            if title_match:
                title = title_match.group(1).strip()
        
        # 提取封面
        pic = ""
        pic_match = re.search(r'<div[^>]*class="[^"]*detail-pic[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"', html, re.DOTALL)
        if pic_match:
            pic = self.fix_url(pic_match.group(1))
        if not pic:
            pic_match = re.search(r'<img[^>]*class="[^"]*lazyload[^"]*"[^>]*data-original="([^"]+)"', html)
            if pic_match:
                pic = self.fix_url(pic_match.group(1))
        
        # 提取标签
        tags = []
        tag_matches = re.findall(r'<span[^>]*>[^<]*(?:精品推荐|高清|无码|有码|字幕|精品|推荐|国产|日本|欧美|亚洲|动漫|萝莉|人妻|乱伦|自拍|主播|网红|偷拍|制服|剧情|巨乳|少女|学生|中文|Cosplay)[^<]*</span>', html)
        for tag in tag_matches:
            clean = re.sub(r'<[^>]+>', '', tag).strip()
            if clean and clean not in tags and len(clean) < 20:
                tags.append(clean)
        
        # 提取所有线路
        play_from = []
        play_url_parts = []
        
        pos = 0
        while True:
            start = html.find('<div class="play-section"', pos)
            if start == -1:
                start = html.find('<div class="play-section ', pos)
            if start == -1:
                break
            
            depth = 0
            end = start
            i = start
            while i < len(html):
                if html[i:i+4] == '<div':
                    depth += 1
                    i += 4
                elif html[i:i+6] == '</div>':
                    depth -= 1
                    i += 6
                    if depth == 0:
                        end = i
                        break
                else:
                    i += 1
            
            if depth != 0:
                break
            
            section = html[start:end]
            
            title_match = re.search(r'<div[^>]*class="[^"]*section-title[^"]*"[^>]*>(.*?)</div>', section, re.DOTALL)
            if title_match:
                source_name = title_match.group(1).strip()
                source_name = re.sub(r'[🍓🥩🎬]', '', source_name).strip()
                if source_name and source_name not in ["", "播放源", "线路"]:
                    play_list_match = re.search(r'<div[^>]*class="[^"]*play-list[^"]*"[^>]*>(.*?)</div>', section, re.DOTALL)
                    if play_list_match:
                        play_links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', play_list_match.group(1))
                        if play_links:
                            eps = []
                            for link, name in play_links:
                                full_url = self.fix_url(link)
                                eps.append(name + "$" + full_url)
                            if eps:
                                play_from.append(source_name)
                                play_url_parts.append("#".join(eps))
            
            pos = end
        
        if not play_from:
            play_links = re.findall(r'<a[^>]*class="[^"]*play-item[^"]*"[^>]*href="([^"]*play[^"]+)"[^>]*>([^<]+)</a>', html)
            if play_links:
                play_from.append("默认来源")
                eps = []
                for link, name in play_links:
                    full_url = self.fix_url(link)
                    eps.append(name + "$" + full_url)
                if eps:
                    play_url_parts.append("#".join(eps))
            else:
                play_from = ["默认来源"]
                play_link_match = re.search(r'<a[^>]*href="([^"]*play[^"]*id/' + vid + r'[^"]*)"[^>]*>', html)
                if play_link_match:
                    full_url = self.fix_url(play_link_match.group(1))
                    play_url_parts = ["正片$" + full_url]
                else:
                    play_url_parts = [""]
        
        vod = {
            "vod_id": vid,
            "vod_name": title or "未知标题",
            "vod_pic": pic,
            "vod_content": " | ".join(tags) if tags else "",
            "vod_play_from": "$$$".join(play_from) if play_from else "默认来源",
            "vod_play_url": "$$$".join(play_url_parts) if play_url_parts else ""
        }
        
        return {"list": [vod]}

    def searchContent(self, key, quick=False, pg=1):
        p = int(pg)
        encoded_key = urllib.parse.quote(key)
        url = f"{self.base_url}/a/index.php/vod/search/wd/{encoded_key}.html"
        if p > 1:
            url = f"{self.base_url}/a/index.php/vod/search/wd/{encoded_key}/page/{p}.html"
        
        html = self.fetch(url)
        if not html:
            return {"list": [], "page": p, "pagecount": 1}
        
        vod_list = self.extract_vod_list(html)
        return {"list": vod_list, "page": p, "pagecount": 1}

    def playerContent(self, flag, id, vipFlags=[]):
        if id.startswith("http"):
            play_url = id
        else:
            parts = id.split('/')
            if len(parts) >= 3:
                video_id, sid, nid = parts[0], parts[1], parts[2]
                play_url = f"{self.base_url}/a/index.php/vod/play/id/{video_id}/sid/{sid}/nid/{nid}.html"
            else:
                vid = self.extract_id_from_url(id)
                play_url = f"{self.base_url}/a/index.php/vod/play/id/{vid}/sid/1/nid/1.html"
        
        html = self.fetch(play_url)
        if not html:
            return {"parse": 0, "playUrl": play_url}
        
        url_match = re.search(r'"url"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
        if url_match:
            video_url = url_match.group(1)
            video_url = video_url.replace('\\/', '/').replace('\\\\', '\\')
            if video_url and (video_url.endswith('.m3u8') or 'm3u8' in video_url.lower()):
                return {"parse": 0, "playUrl": video_url}
        
        m3u8_match = re.search(r'(https?://[^\s"]+\.m3u8[^\s"]*)', html)
        if m3u8_match:
            video_url = m3u8_match.group(1)
            return {"parse": 0, "playUrl": video_url}
        
        iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', html)
        if iframe_match:
            iframe_url = self.fix_url(iframe_match.group(1))
            return self.playerContent(flag, iframe_url, vipFlags)
        
        return {"parse": 0, "playUrl": play_url}