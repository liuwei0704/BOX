#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import json
import urllib.request
import urllib.parse

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

class Spider:
    def getName(self):
        return "AVzmz"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.site_url = "https://a.avzmz11.cc"
        self.base_path = "/a"
        self.limit = 24
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        self.headers = {
            'User-Agent': self.ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.site_url + self.base_path + '/',
        }
        if HAS_REQUESTS:
            self.session = requests.Session()
            self.session.headers.update(self.headers)
            retry = Retry(total=2, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            self.session.verify = False
            self.session.cookies.set('YES_Eighteen', 'IamOverEighteenYearsOld', domain='a.avzmz11.cc')
        else:
            self.session = None
        self.categories = [
            {"type_id": "244", "type_name": "163资源"},
            {"type_id": "358", "type_name": "zmz资源"},
            {"type_id": "329", "type_name": "裤子资源"},
            {"type_id": "119", "type_name": "不卡资源"},
            {"type_id": "286", "type_name": "兔儿资源"},
            {"type_id": "370", "type_name": "森林资源"},
        ]
        # 子分类筛选配置
        self.filters = {
            "244": [
                {"key": "sub_id", "name": "子分类", "value": [
                    {"n": "全部", "v": "244"},
                    {"n": "AV解说", "v": "266"},
                    {"n": "国产自拍", "v": "254"},
                    {"n": "熟女人妻", "v": "255"},
                    {"n": "萝莉少女", "v": "256"},
                    {"n": "百合剧情", "v": "257"},
                    {"n": "美乳巨乳", "v": "258"},
                    {"n": "强歼乱伦", "v": "259"},
                    {"n": "抖音视频", "v": "260"},
                ]}
            ],
            "358": [
                {"key": "sub_id", "name": "子分类", "value": [
                    {"n": "全部", "v": "358"},
                    {"n": "高清有码", "v": "369"},
                    {"n": "动漫精选", "v": "368"},
                    {"n": "学生妹", "v": "367"},
                    {"n": "中文字幕", "v": "366"},
                    {"n": "高清无码", "v": "365"},
                    {"n": "黑料网曝", "v": "364"},
                    {"n": "主播网红", "v": "363"},
                    {"n": "乱伦系列", "v": "362"},
                ]}
            ],
            "329": [
                {"key": "sub_id", "name": "子分类", "value": [
                    {"n": "全部", "v": "329"},
                    {"n": "日本有码", "v": "330"},
                    {"n": "无码中文", "v": "331"},
                    {"n": "有码中文", "v": "332"},
                    {"n": "日本无码", "v": "333"},
                    {"n": "国产视频", "v": "334"},
                    {"n": "欧美高清", "v": "335"},
                    {"n": "动漫剧情", "v": "336"},
                ]}
            ],
            "119": [
                {"key": "sub_id", "name": "子分类", "value": [
                    {"n": "全部", "v": "119"},
                    {"n": "国产视频", "v": "120"},
                    {"n": "中文字幕", "v": "121"},
                    {"n": "国产传媒", "v": "122"},
                    {"n": "日本有码", "v": "123"},
                    {"n": "日本无码", "v": "124"},
                    {"n": "欧美无码", "v": "125"},
                    {"n": "强干乱伦", "v": "126"},
                    {"n": "制服诱惑", "v": "127"},
                ]}
            ],
            "286": [
                {"key": "sub_id", "name": "子分类", "value": [
                    {"n": "全部", "v": "286"},
                    {"n": "精品推荐", "v": "304"},
                    {"n": "主播秀色", "v": "305"},
                    {"n": "日本有码", "v": "306"},
                    {"n": "日本无码", "v": "307"},
                    {"n": "中文字幕", "v": "308"},
                    {"n": "童颜巨乳", "v": "309"},
                    {"n": "性感人妻", "v": "310"},
                    {"n": "强歼乱伦", "v": "311"},
                ]}
            ],
            "370": [
                {"key": "sub_id", "name": "子分类", "value": [
                    {"n": "全部", "v": "370"},
                    {"n": "精品推荐", "v": "371"},
                    {"n": "国产情色", "v": "372"},
                    {"n": "亚洲无码", "v": "373"},
                    {"n": "亚洲有码", "v": "374"},
                    {"n": "中文字幕", "v": "375"},
                    {"n": "强*乱伦", "v": "376"},
                    {"n": "欧美精品", "v": "377"},
                    {"n": "萝莉少女", "v": "378"},
                ]}
            ],
        }

    def _ensure_init(self):
        if not hasattr(self, 'site_url'):
            self.init()

    def fetch(self, url):
        try:
            if HAS_REQUESTS and self.session:
                res = self.session.get(url, timeout=15)
                res.encoding = 'utf-8'
                return res.text
            else:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"fetch error: {e}")
            return None

    def _parse_video_list(self, html, limit=None):
        video_list = []
        if not html:
            return video_list
        pattern = r'<a[^>]*href="(/a/index.php/vod/detail/id/(\d+)\.html)"[^>]*title="([^"]*)"[^>]*>'
        matches = re.findall(pattern, html)
        seen = set()
        for href, vod_id, title in matches:
            if href in seen:
                continue
            seen.add(href)
            if not title or re.match(r'^\d{4}-\d{2}-\d{2}$', title):
                continue
            vod_pic = ''
            img_pattern = r'<img[^>]*data-original="([^"]*)"[^>]*>'
            img_match = re.search(img_pattern, html[html.find(href):html.find(href)+800])
            if img_match:
                vod_pic = img_match.group(1)
            video_list.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": vod_pic,
                "vod_remarks": ""
            })
            if limit and len(video_list) >= limit:
                break
        return video_list

    def homeContent(self, filter=False):
        self._ensure_init()
        url = f"{self.site_url}{self.base_path}/index.php/vod/type/id/244.html"
        html = self.fetch(url)
        video_list = self._parse_video_list(html, self.limit) if html else []
        return {"class": self.categories, "list": video_list, "filters": self.filters}

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter=False, extend={}):
        self._ensure_init()
        page = int(pg) if pg else 1
        # 如果有子分类筛选，使用子分类ID
        cat_id = tid
        if isinstance(extend, dict) and 'sub_id' in extend and extend['sub_id']:
            cat_id = extend['sub_id']
        url = f"{self.site_url}{self.base_path}/index.php/vod/type/id/{cat_id}.html"
        if page > 1:
            url = f"{self.site_url}{self.base_path}/index.php/vod/type/id/{cat_id}/page/{page}.html"
        html = self.fetch(url)
        if not html:
            return {"list": [], "page": page, "pagecount": 1, "limit": self.limit, "total": 0}
        video_list = self._parse_video_list(html)
        pagecount = 1
        page_match = re.search(r'(\d+)\s*/\s*(\d+)', html)
        if page_match:
            pagecount = int(page_match.group(2))
        else:
            page_links = re.findall(r'page/(\d+)\.html', html)
            if page_links:
                max_page = max([int(p) for p in page_links])
                if max_page > pagecount:
                    pagecount = max_page
        if pagecount <= 0:
            pagecount = 100
        return {"list": video_list, "page": page, "pagecount": pagecount, "limit": self.limit, "total": 0}

    def detailContent(self, ids):
        self._ensure_init()
        if not ids:
            return {"list": []}
        vod_id = ids[0]
        url = f"{self.site_url}{self.base_path}/index.php/vod/detail/id/{vod_id}.html"
        html = self.fetch(url)
        if not html:
            return {"list": []}
        vod_name = ''
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if title_match:
            vod_name = title_match.group(1).strip()
        if not vod_name:
            title_match = re.search(r'<title>([^<]+)</title>', html)
            if title_match:
                vod_name = title_match.group(1).strip()
                vod_name = re.sub(r'[-–]AVzmz.*$', '', vod_name).strip()
        vod_pic = ''
        pic_match = re.search(r'<img[^>]*data-original="([^"]+)"[^>]*class="[^"]*content-img[^"]*"', html)
        if pic_match:
            vod_pic = pic_match.group(1)
        vod_class = ''
        cls_match = re.search(r'类别[：:]\s*([^<]+)', html)
        if cls_match:
            vod_class = cls_match.group(1).strip()
        play_from_list = []
        play_url_list = []
        block_pattern = r'<div class="ap-player-heading">\s*<strong>([^<]+)</strong>\s*</div>\s*<ul class="ap-player-list">(.*?)</ul>'
        blocks = re.findall(block_pattern, html, re.DOTALL)
        for source_name, content in blocks:
            episodes = []
            ep_pattern = r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            ep_matches = re.findall(ep_pattern, content)
            for ep_href, ep_text in ep_matches:
                if ep_href and ep_text:
                    episodes.append(f"{ep_text}${ep_href}")
            if episodes:
                play_from_list.append(source_name.strip())
                play_url_list.append('#'.join(episodes))
        if not play_from_list:
            match = re.search(r'var\s+player_aaaa\s*=\s*({[^;]+});', html)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if data.get('link'):
                        play_from_list.append('默认线路')
                        play_url_list.append(f'第1集${data["link"]}')
                except:
                    pass
        if not play_from_list:
            play_links = re.findall(r'<a[^>]*href="(/a/index.php/vod/play/id/[^"]+)"[^>]*>([^<]+)</a>', html)
            if play_links:
                play_from_list.append('默认线路')
                episodes = []
                for href, text in play_links:
                    episodes.append(f'{text}${href}')
                play_url_list.append('#'.join(episodes))
        return {"list": [{
            "vod_id": vod_id,
            "vod_name": vod_name,
            "vod_pic": vod_pic,
            "vod_content": "",
            "vod_director": "",
            "vod_actor": "",
            "vod_class": vod_class,
            "vod_play_from": '$$$'.join(play_from_list),
            "vod_play_url": '$$$'.join(play_url_list)
        }]}

    def searchContent(self, key, quick=False, pg="1"):
        self._ensure_init()
        page = int(pg) if pg else 1
        url = f"{self.site_url}{self.base_path}/index.php/vod/search/wd/{key}.html"
        if page > 1:
            url = f"{self.site_url}{self.base_path}/index.php/vod/search/wd/{key}/page/{page}.html"
        html = self.fetch(url)
        if not html:
            return {"list": [], "page": page, "pagecount": 1}
        video_list = self._parse_video_list(html)
        return {"list": video_list, "page": page, "pagecount": 1}

    def playerContent(self, flag, id, vipFlags):
        self._ensure_init()
        if id.startswith('http'):
            play_url = id
        elif id.startswith('/'):
            play_url = self.site_url + id
        else:
            play_url = self.site_url + '/' + id.lstrip('/')
        html = self.fetch(play_url)
        if not html:
            return {"parse": 1, "url": play_url, "header": self.headers}
        match = re.search(r'player_aaaa\s*=\s*\{[^}]*"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
        if match:
            direct_url = match.group(1)
            if direct_url.startswith('//'):
                direct_url = 'https:' + direct_url
            return {"parse": 0, "url": direct_url, "header": {"User-Agent": self.ua, "Referer": self.site_url + self.base_path + "/"}}
        m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if m3u8_match:
            return {"parse": 0, "url": m3u8_match.group(0), "header": {"User-Agent": self.ua, "Referer": self.site_url + self.base_path + "/"}}
        return {"parse": 1, "url": play_url, "header": self.headers}