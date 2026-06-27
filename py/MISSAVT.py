# coding=utf-8
import re
import json
import urllib.request
import urllib.parse
from base.spider import Spider

BASE = "https://missavt.com"

class Spider(Spider):
    def getName(self):
        return "MissAVt"

    def init(self, extend=""):
        self.site_url = BASE
        self._og_cache = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": BASE + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

    def getDependence(self):
        return []

    def header(self):
        return self.headers

    def _get(self, url):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except:
            return None

    def _fix(self, u):
        if not u:
            return ""
        u = u.strip()
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return BASE + u
        return u

    def _get_og_image(self, vid):
        """从详情页获取og:image"""
        if vid in self._og_cache:
            return self._og_cache[vid]
        try:
            url = f"{BASE}/watch/{vid}/"
            html = self._get(url)
            if html:
                m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
                if m:
                    pic = self._fix(m.group(1))
                    self._og_cache[vid] = pic
                    return pic
        except:
            pass
        return ""

    def _parse_list(self, html, max_items=24):
        if not html:
            return []
        results = []
        pattern = r'<a[^>]*href="/watch/([^"/]+)/?"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?</a>\s*<a[^>]*[^>]*>([^<]+)</a>'
        matches = list(re.finditer(pattern, html, re.DOTALL))
        for m in matches[:max_items]:
            vid = m.group(1).strip()
            title = m.group(3).strip()
            pic = self._get_og_image(vid)
            results.append({"vod_id": vid, "vod_name": title, "vod_pic": pic})
        if not results:
            pattern2 = r'<a[^>]*href="/watch/([^"/]+)/?"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?</a>.*?<a[^>]*class="[^"]*line-clamp[^"]*"[^>]*>([^<]+)</a>'
            matches2 = list(re.finditer(pattern2, html, re.DOTALL))
            for m in matches2[:max_items]:
                vid = m.group(1).strip()
                title = m.group(3).strip()
                pic = self._get_og_image(vid)
                results.append({"vod_id": vid, "vod_name": title, "vod_pic": pic})
        return results

    def homeVideoContent(self):
        return self.homeContent(False)

    def homeContent(self, filter):
        html = self._get(BASE + "/")
        video_list = self._parse_list(html, 24) if html else []
        classes = [
            {"type_id": "1", "type_name": "📺 首页"},
            {"type_id": "sort_hot", "type_name": "🔥 当前最热"},
            {"type_id": "sort_renew", "type_name": "🆕 最新更新"},
            {"type_id": "sort_month_hot", "type_name": "📈 本月最热"},
            {"type_id": "category_censored", "type_name": "🔞 有码AV"},
            {"type_id": "category_chinese-subtitle", "type_name": "🇨🇳 中文字幕"},
            {"type_id": "category_renqishunv", "type_name": "👩 人妻熟女"},
            {"type_id": "category_zhifuyouhuo", "type_name": "👔 制服诱惑"},
            {"type_id": "category_tiaojiaoSM", "type_name": "⛓️ 调教SM"},
            {"type_id": "category_jiatingluanlun", "type_name": "🏠 家庭乱伦"},
            {"type_id": "category_madou", "type_name": "🎬 麻豆传媒"},
            {"type_id": "category_swag", "type_name": "🎬 SWAG"},
            {"type_id": "category_sweet-heart-vlog", "type_name": "🍬 糖心vlog"},
            {"type_id": "category_ed-mosaic", "type_name": "🎬 ED MOSAIC"},
            {"type_id": "category_douyin", "type_name": "📱 抖阴"},
            {"type_id": "category_91-studio", "type_name": "🎬 91制片厂"},
            {"type_id": "category_mr-rabbit", "type_name": "🐰 兔子先生"},
            {"type_id": "category_domestic-media", "type_name": "🎬 国产传媒"},
            {"type_id": "category_xingbatanhua", "type_name": "🌺 杏吧探花"},
            {"type_id": "category_uncensored-leak", "type_name": "💦 无码流出"},
            {"type_id": "category_fc2", "type_name": "🎥 FC2"},
            {"type_id": "category_tokyohot", "type_name": "🔥 东京热"},
            {"type_id": "category_marriedslash", "type_name": "🔪 人妻斩"},
            {"type_id": "category_heyzo", "type_name": "🎬 HEYZO"},
            {"type_id": "category_reducing-mosaic", "type_name": "🔓 无码破解"},
            {"type_id": "category_10musume", "type_name": "🎬 10musume"},
            {"type_id": "category_pacopacomama", "type_name": "👩 pacopacomama"},
            {"type_id": "category_xxx-av", "type_name": "🎬 xxx-av"},
            {"type_id": "category_caribbeancompr", "type_name": "🎬 Caribbeancompr"},
            {"type_id": "category_caribbeancom", "type_name": "🎬 Caribbeancom"},
            {"type_id": "category_1pondo", "type_name": "📖 一本道"},
            {"type_id": "category_siro", "type_name": "🎬 SIRO"},
            {"type_id": "category_luxu", "type_name": "🎬 lulu"},
            {"type_id": "category_gana", "type_name": "🎬 gana"},
            {"type_id": "category_prestige-premium", "type_name": "🎬 PRESTIGE PREMIUM"},
            {"type_id": "category_s-cute", "type_name": "🎬 S-CUTE"},
            {"type_id": "category_ara", "type_name": "🎬 ARA"},
            {"type_id": "actresses_hot", "type_name": "👩 AV女优"},
            {"type_id": "tags", "type_name": "🏷️ AV标签"},
            {"type_id": "articles", "type_name": "📝 AV影评"},
        ]
        return {"class": classes, "list": video_list, "filters": {}}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        type_map = {
            "1": "",
            "sort_hot": "/sort/hot/",
            "sort_renew": "/sort/renew/",
            "sort_month_hot": "/sort/month_hot/",
            "category_censored": "/category/censored/",
            "category_chinese-subtitle": "/category/chinese-subtitle/",
            "category_renqishunv": "/category/renqishunv/",
            "category_zhifuyouhuo": "/category/zhifuyouhuo/",
            "category_tiaojiaoSM": "/category/tiaojiaoSM/",
            "category_jiatingluanlun": "/category/jiatingluanlun/",
            "category_madou": "/category/madou/",
            "category_swag": "/category/swag/",
            "category_sweet-heart-vlog": "/category/sweet-heart-vlog/",
            "category_ed-mosaic": "/category/ed-mosaic/",
            "category_douyin": "/category/douyin/",
            "category_91-studio": "/category/91-studio/",
            "category_mr-rabbit": "/category/mr-rabbit/",
            "category_domestic-media": "/category/domestic-media/",
            "category_xingbatanhua": "/category/xingbatanhua/",
            "category_uncensored-leak": "/category/uncensored-leak/",
            "category_fc2": "/category/fc2/",
            "category_tokyohot": "/category/tokyohot/",
            "category_marriedslash": "/category/marriedslash/",
            "category_heyzo": "/category/heyzo/",
            "category_reducing-mosaic": "/category/reducing-mosaic/",
            "category_10musume": "/category/10musume/",
            "category_pacopacomama": "/category/pacopacomama/",
            "category_xxx-av": "/category/xxx-av/",
            "category_caribbeancompr": "/category/caribbeancompr/",
            "category_caribbeancom": "/category/caribbeancom/",
            "category_1pondo": "/category/1pondo/",
            "category_siro": "/category/siro/",
            "category_luxu": "/category/luxu/",
            "category_gana": "/category/gana/",
            "category_prestige-premium": "/category/prestige-premium/",
            "category_s-cute": "/category/s-cute/",
            "category_ara": "/category/ara/",
            "actresses_hot": "/actresses/hot/",
            "tags": "/tags/",
            "articles": "/articles/",
        }
        base_path = type_map.get(tid, "")
        if base_path == "":
            url = BASE + "/" if page == 1 else f"{BASE}/?page={page}"
        else:
            url = f"{BASE}{base_path}" if page == 1 else f"{BASE}{base_path.rstrip('/')}/{page}/"
        html = self._get(url)
        video_list = self._parse_list(html, 24) if html else []
        pagecount = 50
        if html:
            m = re.search(r'第\d+/(\d+)\s*页', html)
            if m:
                try:
                    pagecount = int(m.group(1))
                except:
                    pass
        return {
            "page": page,
            "pagecount": pagecount,
            "limit": len(video_list),
            "total": pagecount * 20,
            "list": video_list
        }

    def detailContent(self, ids):
        result = {"list": []}
        for vod_id in ids:
            try:
                embed_url = f"{BASE}/embed/{vod_id}/"
                embed_html = self._get(embed_url)
                if not embed_html:
                    continue
                
                detail_url = f"{BASE}/watch/{vod_id}/"
                detail_html = self._get(detail_url)
                title = ""
                pic = ""
                if detail_html:
                    m = re.search(r'<h1[^>]*>([^<]+)</h1>', detail_html)
                    if m:
                        title = m.group(1).strip()
                    if not title:
                        m = re.search(r'<title>([^<]+)</title>', detail_html)
                        if m:
                            title = m.group(1).strip().replace(' - MissAVt', '').replace(' - MissAV', '')
                    m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', detail_html)
                    if m:
                        pic = self._fix(m.group(1))
                    if not pic:
                        m = re.search(r'<meta[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']', detail_html)
                        if m:
                            pic = self._fix(m.group(1))
                
                play_url = ""
                m = re.search(r'<source[^>]*src="([^"]+\.m3u8[^"]*)"', embed_html)
                if m:
                    play_url = self._fix(m.group(1))
                if not play_url:
                    m = re.search(r'<video[^>]*src="([^"]+\.m3u8[^"]*)"', embed_html)
                    if m:
                        play_url = self._fix(m.group(1))
                if not play_url:
                    m = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', embed_html)
                    if m:
                        play_url = m.group(1)
                
                play_str = f"播放${play_url}" if play_url else f"播放{detail_url}"
                result["list"].append({
                    "vod_id": vod_id,
                    "vod_name": title or vod_id,
                    "vod_pic": pic,
                    "vod_play_from": "MissAVt",
                    "vod_play_url": play_str
                })
            except:
                continue
        return result

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        encoded_key = urllib.parse.quote(key)
        url = f"{BASE}/search/{encoded_key}/" if page == 1 else f"{BASE}/search/{encoded_key}/?page={page}"
        html = self._get(url)
        video_list = self._parse_list(html, 24) if html else []
        return {"list": video_list, "page": page, "pagecount": 20}

    def playerContent(self, flag, id, vipFlags):
        return {
            "parse": 0,
            "url": id,
            "header": json.dumps({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": BASE + "/"
            })
        }

    def destroy(self):
        pass