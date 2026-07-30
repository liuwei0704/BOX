# coding: utf-8
"""
AI视频 - TVBox/FongMi 爬虫源
站点: https://en.shipinqd.com/
播放策略: 使用 CDN 域名 gr32fe.sxwph.com 请求 m3u8
图片: 使用 CDN 域名 gr32fe.sxwph.com
作者: AI Assistant
日期: 2026-07-31
"""
import re
import json
from urllib.parse import quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://en.shipinqd.com"
        self.cdn_host = "https://gr32fe.sxwph.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://en.shipinqd.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.cookies = {}

        self.classes = [
            {"type_id": "cate27", "type_name": "禁漫领域"},
            {"type_id": "cate45", "type_name": "黑料泄密"},
            {"type_id": "cate57", "type_name": "少女系列"},
            {"type_id": "cate72", "type_name": "逆天乱伦"},
            {"type_id": "cate84", "type_name": "稀缺重口"},
            {"type_id": "cate94", "type_name": "偷窥欲望"},
            {"type_id": "cate100", "type_name": "探花约啪"},
            {"type_id": "cate101", "type_name": "传媒资源"},
            {"type_id": "cate117", "type_name": "精品日本AV"},
            {"type_id": "cate118", "type_name": "欧美系列"},
        ]

        self.filters = {
            "cate27": [
                {"key": "cate_id", "name": "子分类", "value": [
                    {"n": "原神系列", "v": "cate28"},
                    {"n": "游戏国漫", "v": "cate29"},
                    {"n": "动漫爆乳", "v": "cate30"},
                    {"n": "动漫剧情", "v": "cate31"},
                    {"n": "动漫制服", "v": "cate32"},
                    {"n": "动漫御姐", "v": "cate33"},
                    {"n": "动漫萝莉", "v": "cate34"},
                    {"n": "动漫乱伦", "v": "cate35"},
                    {"n": "motion anime", "v": "cate36"},
                    {"n": "人外重口", "v": "cate37"},
                    {"n": "剧场番剧", "v": "cate38"},
                    {"n": "动漫MMD", "v": "cate39"},
                    {"n": "同人COS", "v": "cate40"},
                    {"n": "H动漫", "v": "cate41"},
                    {"n": "3D动漫", "v": "cate42"},
                    {"n": "动漫里番", "v": "cate43"},
                    {"n": "全部", "v": "cate44"},
                ]}
            ],
            "cate45": [
                {"key": "cate_id", "name": "子分类", "value": [
                    {"n": "一直偷情一直爽", "v": "cate46"},
                    {"n": "网爆泄密", "v": "cate47"},
                    {"n": "母狗-胯下呻吟不断", "v": "cate48"},
                    {"n": "狼友投稿", "v": "cate49"},
                    {"n": "霸凌事件", "v": "cate50"},
                    {"n": "醉奸", "v": "cate51"},
                    {"n": "轮奸专区", "v": "cate52"},
                    {"n": "黑料强奸", "v": "cate53"},
                    {"n": "淫妻-除了老公谁操都会高潮", "v": "cate54"},
                    {"n": "独家揭秘-走进女神的私密世界", "v": "cate55"},
                    {"n": "热点黑料", "v": "cate56"},
                ]}
            ],
            "cate57": [
                {"key": "cate_id", "name": "子分类", "value": [
                    {"n": "白虎嫩穴｜极致嫩滑，欲望释放", "v": "cate58"},
                    {"n": "萝莉少女", "v": "cate59"},
                    {"n": "冷峻警服，点燃你内心的野性", "v": "cate60"},
                    {"n": "新娘的隐秘情事，激情无法自控", "v": "cate61"},
                    {"n": "嫩穴被征服，后入带来高潮爆发", "v": "cate62"},
                    {"n": "自制短剧", "v": "cate63"},
                    {"n": "校园春色，藏不住的少女心事", "v": "cate64"},
                    {"n": "淫欲空姐｜制服下的欲望翱翔", "v": "cate65"},
                    {"n": "淫乱少女主播", "v": "cate66"},
                    {"n": "【极致诱惑】骚护士精选内容", "v": "cate67"},
                    {"n": "甜美JK，带你体验纯真与欲望交织", "v": "cate68"},
                    {"n": "OL的秘密花园", "v": "cate69"},
                    {"n": "角色扮演COS", "v": "cate70"},
                    {"n": "丝袜控", "v": "cate71"},
                ]}
            ],
            "cate72": [
                {"key": "cate_id", "name": "子分类", "value": [
                    {"n": "侄女乱伦", "v": "cate73"},
                    {"n": "兄弟姐妹｜别射里面，乖嘛！", "v": "cate74"},
                    {"n": "禁忌母子-儿子，使劲干我", "v": "cate75"},
                    {"n": "饺子好吃，嫂子更好玩", "v": "cate76"},
                    {"n": "禁忌之爱｜家人之间的秘密激情", "v": "cate77"},
                    {"n": "舅侄叔侄乱伦", "v": "cate78"},
                    {"n": "师生乱伦", "v": "cate79"},
                    {"n": "淫荡岳母", "v": "cate80"},
                    {"n": "小姨子的爱-带着小姨子跑路做爱", "v": "cate81"},
                    {"n": "兄妹乱伦", "v": "cate82"},
                    {"n": "淫乱父女-爸爸，轻点好不好", "v": "cate83"},
                ]}
            ],
            "cate84": [
                {"key": "cate_id", "name": "子分类", "value": [
                    {"n": "疯狂孕妇", "v": "cate85"},
                    {"n": "好奇猎奇", "v": "cate86"},
                    {"n": "变态家族", "v": "cate87"},
                    {"n": "捆绑电击", "v": "cate88"},
                    {"n": "屎尿泄物", "v": "cate89"},
                    {"n": "极限虐肛", "v": "cate90"},
                    {"n": "扩阴拳交", "v": "cate91"},
                    {"n": "性虐调教", "v": "cate92"},
                    {"n": "人兽杂交", "v": "cate93"},
                ]}
            ],
            "cate94": [
                {"key": "cate_id", "name": "子分类", "value": [
                    {"n": "监控破解", "v": "cate95"},
                    {"n": "酒店开房-探花系列", "v": "cate96"},
                    {"n": "裸贷肉偿", "v": "cate97"},
                    {"n": "抄底街射", "v": "cate98"},
                    {"n": "厕拍精选", "v": "cate99"},
                ]}
            ],
            "cate101": [
                {"key": "cate_id", "name": "子分类", "value": [
                    {"n": "蜜桃传媒", "v": "cate102"},
                    {"n": "天美传媒", "v": "cate103"},
                    {"n": "麻豆传媒", "v": "cate104"},
                    {"n": "糖心传媒", "v": "cate105"},
                    {"n": "SA国际传媒", "v": "cate106"},
                    {"n": "传媒乌托邦", "v": "cate107"},
                    {"n": "大象传媒", "v": "cate108"},
                    {"n": "星空無限傳媒", "v": "cate109"},
                    {"n": "果冻传媒", "v": "cate110"},
                    {"n": "SWAG", "v": "cate111"},
                    {"n": "91制片厂", "v": "cate112"},
                    {"n": "起点性世界传媒", "v": "cate113"},
                    {"n": "杏吧傳媒", "v": "cate114"},
                    {"n": "扣扣传媒", "v": "cate115"},
                    {"n": "精东传媒", "v": "cate116"},
                ]}
            ],
            "cate118": [
                {"key": "cate_id", "name": "子分类", "value": [
                    {"n": "欧美精选 - 大洋马异域风情", "v": "cate119"},
                    {"n": "双龙入洞", "v": "cate120"},
                    {"n": "欧美重口-你认为你变态？多学学", "v": "cate121"},
                    {"n": "美女自慰", "v": "cate122"},
                    {"n": "户外搭讪", "v": "cate123"},
                    {"n": "黑人大屌-操的你腿打摆子", "v": "cate124"},
                    {"n": "成人剧情", "v": "cate125"},
                    {"n": "全部", "v": "cate126"},
                ]}
            ],
            "cate100": [],
            "cate117": [],
        }

    def getName(self):
        return "AI视频"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        url = self.host + "/"
        html = self._fetch_html(url)
        if not html:
            return {"list": []}
        items = self._parse_video_list(html)
        return {"list": items}

    def _get_default_sub_category(self, tid):
        if tid in self.filters and self.filters[tid]:
            for filter_item in self.filters[tid]:
                if "value" in filter_item and filter_item["value"]:
                    return filter_item["value"][0].get("v")
        return None

    def categoryContent(self, tid, pg, filter=False, extend=""):
        if not tid.startswith("cate"):
            tid = "cate" + str(tid)

        real_tid = tid
        if extend:
            if isinstance(extend, dict):
                if "cate_id" in extend:
                    real_tid = extend["cate_id"]
            elif isinstance(extend, str):
                try:
                    ext = json.loads(extend)
                    if "cate_id" in ext:
                        real_tid = ext["cate_id"]
                except:
                    pass
        else:
            default_sub = self._get_default_sub_category(tid)
            if default_sub:
                real_tid = default_sub

        pg = str(pg) if pg else "1"
        if pg == "1":
            url = self.host + "/category/" + real_tid + "/"
        else:
            url = self.host + "/category/" + real_tid + "/" + pg + "/"

        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}

        items = self._parse_video_list(html)
        pagecount = self._parse_page_count(html)

        return {
            "list": items,
            "page": int(pg),
            "pagecount": pagecount if pagecount > 0 else 50,
            "limit": 20,
            "total": 0,
        }

    def detailContent(self, ids):
        if not ids or len(ids) == 0:
            return {"list": []}

        vid = ids[0]
        if "/video/" in vid:
            vid = vid.split("/video/")[-1].rstrip("/")

        detail_url = self.host + "/video/" + str(vid) + "/"
        html = self._fetch_html(detail_url)
        if not html:
            return {"list": []}

        title = self._extract_title(html)
        pic = self._extract_pic(html)
        desc = self._extract_desc(html)

        vod = {
            "vod_id": str(vid),
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": desc,
            "vod_content": desc,
            "vod_play_from": "播放",
            "vod_play_url": "播放$" + str(vid),
        }

        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}

        keyword = key.strip()
        pg = str(pg) if pg else "1"
        url = self.host + "/search/" + quote(keyword) + "/"
        if pg != "1":
            url = self.host + "/search/" + quote(keyword) + "/" + pg + "/"

        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": int(pg)}

        items = self._parse_video_list(html)
        pagecount = self._parse_page_count(html)

        return {
            "list": items,
            "page": int(pg),
            "pagecount": pagecount if pagecount > 0 else 20,
        }

    def playerContent(self, flag, vid, vipFlags):
        if vid and (vid.endswith(".m3u8") or vid.endswith(".mp4")):
            if "en.shipinqd.com" in vid:
                vid = vid.replace("en.shipinqd.com", "gr32fe.sxwph.com")
            return {"parse": 0, "url": vid, "header": self.headers}

        if vid and vid.startswith("http"):
            match = re.search(r'/video/(\d+)/', vid)
            if match:
                vid = match.group(1)
            else:
                return {"parse": 1, "url": vid, "header": self.headers}

        detail_url = self.host + "/video/" + str(vid) + "/"
        html = self._fetch_html(detail_url)
        if html:
            archive_data = self._extract_archive_player(html)
            if archive_data:
                raw_path = archive_data.get("rawPath", "")
                if raw_path:
                    if raw_path.startswith("/"):
                        m3u8_url = self.cdn_host + raw_path
                    else:
                        m3u8_url = raw_path.replace("en.shipinqd.com", "gr32fe.sxwph.com")
                    return {"parse": 0, "url": m3u8_url, "header": self.headers}

        return {"parse": 1, "url": detail_url, "header": self.headers}

    def localProxy(self, params):
        return [404, "text/plain", "Not Found", {}]

    def _fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if resp and hasattr(resp, "text"):
                if hasattr(resp, "cookies"):
                    self.cookies.update(resp.cookies)
                return resp.text
            return None
        except Exception as e:
            self.log({"action": "fetch_error", "url": url, "error": str(e)})
            return None

    def _parse_video_list(self, html):
        items = []
        card_pattern = r'<li[^>]*class="[^"]*section-content__item[^"]*(?!module-two)"[^>]*>.*?<a[^>]*href="(/video/(\d+)/)"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?<h3[^>]*class="[^"]*text-truncate[^"]*"[^>]*>(.*?)</h3>.*?<span[^>]*class="eye"[^>]*>(.*?)</span>'
        matches = re.findall(card_pattern, html, re.DOTALL)

        if not matches:
            card_pattern2 = r'<a[^>]*href="(/video/(\d+)/)"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?<h3[^>]*class="[^"]*text-truncate[^"]*"[^>]*>(.*?)</h3>'
            matches = re.findall(card_pattern2, html, re.DOTALL)

        for match in matches:
            if len(match) >= 4:
                href = match[0]
                vid = match[1]
                pic = match[2]
                title = re.sub(r'<[^>]+>', '', match[3].strip())
                remark = match[4] if len(match) > 4 else ""

                if href and vid and title:
                    if pic and pic.startswith("http"):
                        img_url = pic.replace("en.shipinqd.com", "gr32fe.sxwph.com")
                    else:
                        img_url = self.cdn_host + pic if pic else ""
                    items.append({
                        "vod_id": vid,
                        "vod_name": title[:50],
                        "vod_pic": img_url,
                        "vod_remarks": remark,
                    })

        seen = set()
        unique_items = []
        for item in items:
            key = item["vod_id"]
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        return unique_items[:50]

    def _parse_page_count(self, html):
        pages = re.findall(r'<a[^>]*href="[^"]*/(\d+)/"[^>]*>\d+</a>', html)
        if pages:
            return max([int(p) for p in pages if p.isdigit()])
        return 1

    def _extract_title(self, html):
        match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
        if match:
            return match.group(1).strip()
        match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
        if match:
            return re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return ""

    def _extract_pic(self, html):
        archive_data = self._extract_archive_player(html)
        if archive_data:
            poster = archive_data.get("posterImg", "")
            if poster:
                return poster.replace("en.shipinqd.com", "gr32fe.sxwph.com")
        match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if match:
            pic = match.group(1)
            if pic.startswith("/"):
                return self.cdn_host + pic
            return pic.replace("en.shipinqd.com", "gr32fe.sxwph.com")
        match = re.search(r'<img[^>]*data-src="([^"]+)"[^>]*class="[^"]*cover[^"]*"', html)
        if match:
            pic = match.group(1)
            if "/system/" not in pic:
                if pic.startswith("http"):
                    return pic.replace("en.shipinqd.com", "gr32fe.sxwph.com")
                return self.cdn_host + pic
        return ""

    def _extract_desc(self, html):
        match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        if match:
            return match.group(1)[:200]
        return ""

    def _extract_archive_player(self, html):
        start_pattern = r'__ARCHIVE_PLAYER__\s*=\s*(\{)'
        match = re.search(start_pattern, html)
        if not match:
            return None

        start_idx = match.start(1)
        stack = []
        in_string = False
        escape_next = False
        end_idx = None

        for i in range(start_idx, len(html)):
            char = html[i]
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == '{':
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        end_idx = i + 1
                        break

        if end_idx is None:
            return None

        json_str = html[start_idx:end_idx]
        try:
            return json.loads(json_str)
        except:
            return None