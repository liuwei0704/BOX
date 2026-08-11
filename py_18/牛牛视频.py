# coding: utf-8
"""
牛牛视频 - TVBox/FongMi 爬虫源
站点: https://niuniuf.com/
播放策略: 使用 CDN 域名 gr32fe.sxwph.com 请求 m3u8
作者: AI Assistant
日期: 2026-07-24
"""
import re
import json
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://niuniuf.com"
        self.cdn_host = "https://gr32fe.sxwph.com"  # CDN 域名
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://niuniuf.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.cookies = {}
        
        self.classes = [
            {"type_id": "cate5", "type_name": "擦边短剧"},
            {"type_id": "cate18", "type_name": "原创乱伦"},
            {"type_id": "cate19", "type_name": "鬼父操女"},
            {"type_id": "cate20", "type_name": "淫母兽儿"},
            {"type_id": "cate21", "type_name": "嫂子诱惑"},
            {"type_id": "cate22", "type_name": "姐夫小姨子"},
            {"type_id": "cate26", "type_name": "爷孙禁忌"},
            {"type_id": "cate30", "type_name": "舅妈得爱情故事"},
            {"type_id": "cate31", "type_name": "御姐李老师"},
            {"type_id": "cate32", "type_name": "奶气草莓"},
            {"type_id": "cate33", "type_name": "会喷水的姐姐"},
            {"type_id": "cate34", "type_name": "伊藤诚"},
            {"type_id": "cate35", "type_name": "狠台北"},
            {"type_id": "cate36", "type_name": "公鸡俱乐部"},
            {"type_id": "cate38", "type_name": "免费专区"},
            {"type_id": "cate39", "type_name": "颜值女神"},
            {"type_id": "cate40", "type_name": "探花嫖妓"},
            {"type_id": "cate41", "type_name": "绿帽淫妻"},
            {"type_id": "cate42", "type_name": "母狗性奴"},
            {"type_id": "cate43", "type_name": "针孔偷拍"},
            {"type_id": "cate44", "type_name": "野战户外"},
            {"type_id": "cate45", "type_name": "成人综艺"},
            {"type_id": "cate46", "type_name": "网红骚播"},
            {"type_id": "cate48", "type_name": "精选爆款"},
            {"type_id": "cate66", "type_name": "白菜妹妹"},
            {"type_id": "cate67", "type_name": "菠萝啤beer~"},
            {"type_id": "cate68", "type_name": "网红妹妹"},
            {"type_id": "cate69", "type_name": "香艳职场"},
            {"type_id": "cate70", "type_name": "捅主任"},
            {"type_id": "cate71", "type_name": "双生の恋"},
            {"type_id": "cate72", "type_name": "台湾臀后艾丽"},
            {"type_id": "cate73", "type_name": "粉红兔的诱惑"},
            {"type_id": "cate74", "type_name": "COS美少女"},
            {"type_id": "cate75", "type_name": "女王梨奈"},
            {"type_id": "cate76", "type_name": "性感小猫咪"},
            {"type_id": "cate77", "type_name": "宜家门"},
            {"type_id": "cate78", "type_name": "颜射少女"},
            {"type_id": "cate79", "type_name": "迷奸柚"},
            {"type_id": "cate80", "type_name": "拳交女皇"},
            {"type_id": "cate82", "type_name": "Xreindeers"},
            {"type_id": "cate83", "type_name": "米胡桃"},
            {"type_id": "cate84", "type_name": "Andmlove"},
            {"type_id": "cate85", "type_name": "羞羞兔"},
            {"type_id": "cate86", "type_name": "Roko"},
            {"type_id": "cate87", "type_name": "Yominokuni"},
            {"type_id": "cate88", "type_name": "桃子派"},
            {"type_id": "cate89", "type_name": "下面有根棒棒糖"},
            {"type_id": "cate90", "type_name": "宝贝奶兽"},
            {"type_id": "cate91", "type_name": "BabyYurin"},
            {"type_id": "cate92", "type_name": "优咪Yumi"},
            {"type_id": "cate93", "type_name": "台湾兔兔"},
            {"type_id": "cate94", "type_name": "爱玩熊熊"},
            {"type_id": "cate95", "type_name": "鸡教练"},
            {"type_id": "cate96", "type_name": "樱桃空空"},
            {"type_id": "cate97", "type_name": "Miuzxc"},
            {"type_id": "cate108", "type_name": "精东影业"},
            {"type_id": "cate121", "type_name": "凌辱快感"},
            {"type_id": "cate130", "type_name": "孕妇风情"},
            {"type_id": "cate131", "type_name": "SM调教"},
            {"type_id": "cate132", "type_name": "媚黑骚逼"},
            {"type_id": "cate133", "type_name": "强奸迷奸"},
            {"type_id": "cate134", "type_name": "人妖伪娘"},
            {"type_id": "cate135", "type_name": "百合女同"},
            {"type_id": "cate136", "type_name": "男男之恋"},
            {"type_id": "cate137", "type_name": "偷窥偷拍"},
            {"type_id": "cate139", "type_name": "精选无码动漫"},
            {"type_id": "cate140", "type_name": "王者荣耀"},
            {"type_id": "cate141", "type_name": "经典老片"},
            {"type_id": "cate142", "type_name": "禁漫里番"},
            {"type_id": "cate143", "type_name": "巨乳动漫"},
            {"type_id": "cate144", "type_name": "中文字幕"},
            {"type_id": "cate145", "type_name": "魔"},
            {"type_id": "cate146", "type_name": "原神"},
            {"type_id": "cate147", "type_name": "综合"},
            {"type_id": "cate163", "type_name": "综艺推荐"},
            {"type_id": "cate164", "type_name": "性爱自修室"},
            {"type_id": "cate165", "type_name": "突袭女优家"},
            {"type_id": "cate166", "type_name": "淫娃培训营"},
            {"type_id": "cate167", "type_name": "淫欲游戏王"},
            {"type_id": "cate168", "type_name": "情趣K歌房"},
            {"type_id": "cate169", "type_name": "乱伦家庭"},
            {"type_id": "cate179", "type_name": "1G.老湿"},
            {"type_id": "cate180", "type_name": "嘿嘿啾芮"},
        ]
        self.filters = {}

    def getName(self):
        return "牛牛视频"

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

    def categoryContent(self, tid, pg, filter=False, extend=""):
        if not tid.startswith("cate"):
            tid = "cate" + str(tid)
        pg = str(pg) if pg else "1"
        if pg == "1":
            url = self.host + "/category/" + tid + "/"
        else:
            url = self.host + "/category/" + tid + "/" + pg + "/"

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
        """
        播放地址解析 - 使用 CDN 域名 gr32fe.sxwph.com 请求 m3u8
        """
        # 如果传入的是m3u8/mp4直链，直接返回
        if vid and (vid.endswith(".m3u8") or vid.endswith(".mp4")):
            # 如果是 niuniuf.com 的 m3u8，替换为 CDN 域名
            if "niuniuf.com" in vid:
                vid = vid.replace("niuniuf.com", "gr32fe.sxwph.com")
            return {"parse": 0, "url": vid, "header": self.headers}

        # 如果是完整的播放页URL，提取视频ID
        if vid and vid.startswith("http"):
            # 从URL中提取视频ID
            match = re.search(r'/video/(\d+)/', vid)
            if match:
                vid = match.group(1)
            else:
                return {"parse": 1, "url": vid, "header": self.headers}

        # 获取详情页HTML，提取 rawPath
        detail_url = self.host + "/video/" + str(vid) + "/"
        html = self._fetch_html(detail_url)
        if html:
            # 提取 __ARCHIVE_PLAYER__.rawPath
            archive_data = self._extract_archive_player(html)
            if archive_data:
                raw_path = archive_data.get("rawPath", "")
                if raw_path:
                    # 替换域名为 CDN 域名
                    if raw_path.startswith("/"):
                        m3u8_url = self.cdn_host + raw_path
                    else:
                        m3u8_url = raw_path.replace("niuniuf.com", "gr32fe.sxwph.com")
                    return {"parse": 0, "url": m3u8_url, "header": self.headers}

        # 降级：使用 parse:1 嗅探
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
        # 使用更简洁的解析方式
        li_pattern = r'<li[^>]*class="[^"]*section-content__item[^"]*"[^>]*>.*?<a[^>]*href="/video/(\d+)/"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<span[^>]*class="eye"[^>]*>(.*?)</span>'
        matches = re.findall(li_pattern, html, re.DOTALL)

        if not matches:
            li_pattern2 = r'<a[^>]*href="/video/(\d+)/"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>'
            matches2 = re.findall(li_pattern2, html, re.DOTALL)
            for match in matches2:
                if len(match) >= 3:
                    vid = match[0]
                    pic = match[1]
                    # 替换域名：wefs3.sxwph.com -> d2k58elwv8me3x.cloudfront.net
                    if "wefs3.sxwph.com" in pic:
                        pic = pic.replace("wefs3.sxwph.com", "d2k58elwv8me3x.cloudfront.net")
                    elif "sdsdsd.sxwph.com" in pic:
                        pic = pic.replace("sdsdsd.sxwph.com", "d2k58elwv8me3x.cloudfront.net")
                    title = re.sub(r'<[^>]+>', '', match[2].strip())
                    if vid and title:
                        items.append({
                            "vod_id": vid,
                            "vod_name": title,
                            "vod_pic": pic if pic.startswith("http") else self.host + pic,
                            "vod_remarks": "",
                        })
        else:
            for match in matches:
                if len(match) >= 4:
                    vid = match[0]
                    pic = match[1]
                    # 替换域名：wefs3.sxwph.com -> d2k58elwv8me3x.cloudfront.net
                    if "wefs3.sxwph.com" in pic:
                        pic = pic.replace("wefs3.sxwph.com", "d2k58elwv8me3x.cloudfront.net")
                    elif "sdsdsd.sxwph.com" in pic:
                        pic = pic.replace("sdsdsd.sxwph.com", "d2k58elwv8me3x.cloudfront.net")
                    title = re.sub(r'<[^>]+>', '', match[2].strip())
                    remark = match[3].strip() if len(match) > 3 else ""
                    if vid and title:
                        items.append({
                            "vod_id": vid,
                            "vod_name": title,
                            "vod_pic": pic if pic.startswith("http") else self.host + pic,
                            "vod_remarks": remark,
                        })

        # 去重
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
                return poster
        match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if match:
            pic = match.group(1)
            if pic.startswith("/"):
                pic = self.host + pic
            return pic
        match = re.search(r'<img[^>]*data-src="([^"]+)"[^>]*class="[^"]*cover[^"]*"', html)
        if match:
            pic = match.group(1)
            if "/system/" not in pic:
                return pic if pic.startswith("http") else self.host + pic
        return ""

    def _extract_desc(self, html):
        match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        if match:
            return match.group(1)[:200]
        return ""

    def _extract_archive_player(self, html):
        """
        从页面中提取 __ARCHIVE_PLAYER__ JSON 对象
        使用栈匹配处理嵌套的 {} 和 []
        """
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