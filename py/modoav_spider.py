# coding=utf-8
# 魔都AV (modoav) TVBox Python 爬虫 v2.3
# 修复详情页标题提取

import re
import json
import urllib.request
import urllib.parse
import gzip
from io import BytesIO

class Spider:
    def __init__(self):
        self.site_url = "https://26z5.modoav.xyz"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.site_url
        }
        
        self.categories = {
            "zhongwen": {"name": "中文传媒", "tid": "中文传媒"},
            "guochan": {"name": "国产", "tid": "国产"},
            "oumeiav": {"name": "欧美AV", "tid": "欧美AV"},
            "ribenav": {"name": "日本AV", "tid": "日本AV"},
            "madou": {"name": "麻豆传媒", "tid": "传媒-麻豆传媒"},
            "jingdong": {"name": "精东影业", "tid": "传媒-精东影业"},
            "mitao": {"name": "蜜桃传媒", "tid": "传媒-蜜桃传媒"},
            "guodong": {"name": "果冻传媒", "tid": "传媒-果冻传媒"},
            "xingkong": {"name": "星空无限传媒", "tid": "传媒-星空无限传媒"},
            "sa": {"name": "SA国际传媒", "tid": "传媒-SA国际传媒"},
            "xingshijie": {"name": "性视界传媒", "tid": "传媒-性视界传媒"},
            "zipai": {"name": "国产-自拍", "tid": "国产-自拍"},
            "toupai": {"name": "国产-偷拍", "tid": "国产-偷拍"},
            "tanhua": {"name": "国产-探花", "tid": "国产-探花"},
            "zhubo": {"name": "国产-主播", "tid": "国产-主播"},
            "tianmei": {"name": "天美传媒", "tid": "传媒-天美传媒"},
            "oumeiwuma": {"name": "欧美高清无码", "tid": "欧美-高清无码"},
            "oumeiyouma": {"name": "欧美高清有码", "tid": "欧美-高清有码"},
            "ribenzimu": {"name": "日本中文字幕", "tid": "日本-中文字幕"},
            "ribenwuma": {"name": "日本无码流出", "tid": "日本-无码流出"},
            "ribenyouma": {"name": "日本高清有码", "tid": "日本-高清有码"},
            "huangjia": {"name": "皇家华人", "tid": "传媒-皇家华人"},
            "oumeizimu": {"name": "欧美中文字幕", "tid": "欧美-中文字幕"},
            "dongman": {"name": "动漫", "tid": "动漫"},
            "chi_gua": {"name": "吃瓜黑料", "tid": "吃瓜黑料"},
            "hanguoav": {"name": "韩国AV", "tid": "韩国AV"},
            "hanguozhubo": {"name": "韩国主播", "tid": "韩国-主播"},
            "ribensuren": {"name": "日本素人", "tid": "日本-素人"},
        }
        
        self.filters = [
            {"key": "rq", "name": "排序", "value": [
                {"n": "最新更新", "v": ""},
                {"n": "最新点播", "v": "db"},
                {"n": "最多点击", "v": "h"},
                {"n": "最多弹幕", "v": "d"},
                {"n": "最新弹幕", "v": "dt"},
                {"n": "最多评论", "v": "p"},
                {"n": "最新评论", "v": "pt"},
                {"n": "最多收藏", "v": "s"},
                {"n": "最新收藏", "v": "st"},
                {"n": "最多点赞", "v": "z"},
                {"n": "最新点赞", "v": "zt"},
            ]}
        ]

    def init(self, cfg=None):
        if cfg:
            if isinstance(cfg, list) and len(cfg) > 0:
                cfg = cfg[0]
            if isinstance(cfg, str):
                if cfg.startswith('http'):
                    self.site_url = cfg.rstrip('/')
                elif cfg.startswith('{'):
                    try:
                        config = json.loads(cfg)
                        if 'site_url' in config:
                            self.site_url = config['site_url'].rstrip('/')
                    except:
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
        if url.startswith("/"):
            return self.site_url + url
        return self.site_url + "/" + url

    def extract_vod_list(self, html):
        """提取视频列表 - 每个视频独立提取角标和分类"""
        result = []
        
        # 使用更精确的匹配: 匹配完整的 tile-grid-item 块
        items = re.split(r'(?=<div[^>]*class="[^"]*tile-grid-item[^"]*"[^>]*>)', html)
        
        for item in items:
            if not re.search(r'tile-grid-item', item):
                continue
            
            try:
                # 提取链接
                href_match = re.search(r'<a[^>]*href="([^"]+)"', item)
                if not href_match:
                    continue
                href = href_match.group(1)
                
                # 提取视频ID
                id_match = re.search(r'play-(\d+)-', href)
                vod_id = id_match.group(1) if id_match else '0'
                if vod_id == '0':
                    continue
                
                # 提取图片
                img_match = re.search(r'<img[^>]*(?:data-src|src)="([^"]+)"', item)
                pic = self.fix_url(img_match.group(1)) if img_match else ""
                
                # 提取标题
                title_match = re.search(r'<span[^>]*>([^<]+)</span>', item)
                title = title_match.group(1).strip() if title_match else ""
                if not title:
                    continue
                title = re.sub(r'<[^>]+>', '', title).strip()
                
                # 从卡片内部提取角标 (icon-top-right)
                badge = ""
                badge_match = re.search(r'<i[^>]*class="[^"]*icon-top-right[^"]*"[^>]*>([^<]+)</i>', item)
                if badge_match:
                    badge = badge_match.group(1).strip()
                    badge = badge.replace('&nbsp;', '').strip()
                
                # 从卡片内部提取分类
                cat_name = ""
                cat_match = re.search(r'<a[^>]*href="/\?fenlei=[^"]+"[^>]*>([^<]+)</a>', item)
                if cat_match:
                    cat_name = cat_match.group(1).strip()
                
                # 组合备注
                remark = ""
                if badge:
                    remark = badge
                if cat_name:
                    if remark:
                        remark = remark + " | " + cat_name
                    else:
                        remark = cat_name
                
                result.append({
                    "vod_id": str(vod_id),
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
                
                if len(result) >= 20:
                    break
                    
            except Exception as e:
                continue
        
        # 如果没有匹配到任何视频，使用备用方法
        if not result:
            pattern = r'tile-grid-item.*?<a[^>]*href="([^"]+)".*?<img[^>]*(?:data-src|src)="([^"]+)".*?<span[^>]*>([^<]+)</span>'
            matches = re.findall(pattern, html, re.DOTALL)
            
            for href, img, title in matches:
                try:
                    id_match = re.search(r'play-(\d+)-', href)
                    vod_id = id_match.group(1) if id_match else '0'
                    pic = self.fix_url(img)
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    if not title:
                        title = f"视频_{vod_id}"
                    
                    result.append({
                        "vod_id": str(vod_id),
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": ""
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
            if filter:
                item["filters"] = self.filters
            result["class"].append(item)
        
        html = self.fetch(self.site_url + "/")
        if html:
            result["list"] = self.extract_vod_list(html)
        
        return result

    def homeVideoContent(self):
        return self.homeContent(filter=False)

    def categoryContent(self, tid, pg=1, filter=False, extend={}):
        p = int(pg) if pg else 1
        
        info = self.categories.get(tid)
        if info:
            real_tid = info["tid"]
        else:
            real_tid = tid
        
        encoded_tid = urllib.parse.quote(str(real_tid), safe='')
        url = self.site_url + "/?fenlei=" + encoded_tid + "&p=" + str(p)
        
        if extend.get("rq"):
            url += "&rq=" + extend["rq"]
        
        html = self.fetch(url)
        if not html:
            return {"list": []}
        
        vod_list = self.extract_vod_list(html)
        
        pagecount = p
        page_links = re.findall(r'<a[^>]*>(\d+)</a>', html)
        if page_links:
            nums = [int(x) for x in page_links if x.isdigit()]
            if nums:
                pagecount = max(nums)
        
        if pagecount <= p and len(vod_list) > 0:
            pagecount = p + 1
        
        return {
            "list": vod_list,
            "page": p,
            "pagecount": pagecount,
            "total": len(vod_list)
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        
        vod_id = str(ids[0]).strip()
        url = self.site_url + "/?play-" + vod_id + "-1-.html"
        html = self.fetch(url)
        if not html:
            return {"list": []}
        
        # 从<title>标签提取标题
        title = ""
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            title = title_match.group(1).strip()
            # 去掉结尾的 "-在线播放-魔都AV"
            title = re.sub(r'-在线播放-魔都AV$', '', title)
            # 去掉开头的可能多余内容
            title = title.strip()
        
        # 如果title标签没提取到，尝试og:title
        if not title:
            og_match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html)
            if og_match:
                title = og_match.group(1).strip()
                title = re.sub(r'-在线播放-魔都AV$', '', title)
        
        # 如果还是没有，使用video_id作为标题
        if not title:
            title = f"视频_{vod_id}"
        
        # 提取封面
        pic = ""
        img_match = re.search(r'<img[^>]*(?:data-src|src)="([^"]+)"[^>]*>', html)
        if img_match:
            pic = self.fix_url(img_match.group(1))
        
        # 提取简介
        content = ""
        meta_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        if meta_match:
            content = meta_match.group(1).strip()
        
        # 提取分类
        category = ""
        cat_match = re.search(r'<a[^>]*href="/\?fenlei=([^"]+)"[^>]*>([^<]+)</a>', html)
        if cat_match:
            category = cat_match.group(2)
        
        # 提取播放地址
        play_url = ""
        m3u8_match = re.search(r'data-preview="([^"]+\.m3u8[^"]*)"', html)
        if m3u8_match:
            play_url = m3u8_match.group(1)
        if not play_url:
            m3u8_match2 = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
            if m3u8_match2:
                play_url = m3u8_match2.group(0)
        
        # 如果还是没提取到播放地址，尝试从iframe中提取
        if not play_url:
            iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', html)
            if iframe_match:
                iframe_url = self.fix_url(iframe_match.group(1))
                iframe_html = self.fetch(iframe_url)
                if iframe_html:
                    m3u8_match3 = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', iframe_html)
                    if m3u8_match3:
                        play_url = m3u8_match3.group(0)
        
        return {"list": [{
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_content": content,
            "vod_play_from": category if category else "默认",
            "vod_play_url": play_url if play_url else ""
        }]}

    def searchContent(self, key, quick=False, pg=1):
        p = int(pg) if pg else 1
        encoded_key = urllib.parse.quote(str(key), safe='')
        url = self.site_url + "/?search=" + encoded_key + "&p=" + str(p)
        
        html = self.fetch(url)
        if not html:
            return {"list": []}
        
        vod_list = self.extract_vod_list(html)
        
        pagecount = p
        page_links = re.findall(r'<a[^>]*>(\d+)</a>', html)
        if page_links:
            nums = [int(x) for x in page_links if x.isdigit()]
            if nums:
                pagecount = max(nums)
        
        if pagecount <= p and len(vod_list) > 0:
            pagecount = p + 1
        
        return {
            "list": vod_list,
            "page": p,
            "pagecount": pagecount,
            "total": len(vod_list)
        }

    def playerContent(self, flag, id, vipFlags=[]):
        if id.startswith('http'):
            play_url = id
        else:
            detail_url = self.site_url + "/?play-" + id + "-1-.html"
            html = self.fetch(detail_url)
            if html:
                m3u8_match = re.search(r'data-preview="([^"]+\.m3u8[^"]*)"', html)
                if m3u8_match:
                    play_url = m3u8_match.group(1)
                else:
                    m3u8_match2 = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
                    if m3u8_match2:
                        play_url = m3u8_match2.group(0)
                    else:
                        iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', html)
                        if iframe_match:
                            iframe_url = self.fix_url(iframe_match.group(1))
                            iframe_html = self.fetch(iframe_url)
                            if iframe_html:
                                m3u8_match3 = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', iframe_html)
                                if m3u8_match3:
                                    play_url = m3u8_match3.group(0)
            else:
                return {"parse": 0, "url": id}
        
        if not play_url:
            return {"parse": 0, "url": id}
        
        return {"parse": 0, "url": play_url}