# coding: utf-8
import json
import re
from urllib.parse import quote, urljoin, unquote, urlparse

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://riznh.jgmz.beer"  # 当前可用域名，支持备用域名切换
        self.classes = [
            {"type_id": "20", "type_name": "学生少女"},
            {"type_id": "21", "type_name": "技师风采"},
            {"type_id": "22", "type_name": "熟女少妇"},
            {"type_id": "23", "type_name": "国产热播"},
            {"type_id": "24", "type_name": "反差母狗"},
            {"type_id": "25", "type_name": "美脚丝足"},
            {"type_id": "26", "type_name": "情侣自拍"},
            {"type_id": "27", "type_name": "私房俱乐部"},
            {"type_id": "28", "type_name": "偷情约炮"},
            {"type_id": "29", "type_name": "真实偷拍"},
            {"type_id": "30", "type_name": "高潮喷水"},
            {"type_id": "31", "type_name": "强奸迷奸"},
            {"type_id": "32", "type_name": "户外露出"},
            {"type_id": "33", "type_name": "SM调教"},
            {"type_id": "34", "type_name": "情趣内衣"},
            {"type_id": "35", "type_name": "精选探花"},
            {"type_id": "36", "type_name": "网曝门事件"},
            {"type_id": "37", "type_name": "校园猛料"},
            {"type_id": "38", "type_name": "网红流出"},
            {"type_id": "39", "type_name": "明星黑料"},
            {"type_id": "40", "type_name": "裸贷肉偿"},
            {"type_id": "41", "type_name": "婚闹恶俗"},
            {"type_id": "42", "type_name": "抓奸名场面"},
            {"type_id": "43", "type_name": "男同女同"},
            {"type_id": "44", "type_name": "JK少女"},
            {"type_id": "45", "type_name": "黑丝白丝"},
            {"type_id": "46", "type_name": "女仆"},
            {"type_id": "47", "type_name": "cosplay"},
            {"type_id": "48", "type_name": "OL制服"},
            {"type_id": "49", "type_name": "旗袍"},
            {"type_id": "50", "type_name": "空姐制服"},
            {"type_id": "51", "type_name": "护士医生"},
            {"type_id": "52", "type_name": "伦理之爱"},
            {"type_id": "53", "type_name": "禁忌母子"},
            {"type_id": "54", "type_name": "兄弟姐妹"},
            {"type_id": "55", "type_name": "爱上嫂子"},
            {"type_id": "56", "type_name": "狂操小姨"},
            {"type_id": "57", "type_name": "换夫换妻"},
            {"type_id": "58", "type_name": "淫荡儿媳"},
            {"type_id": "59", "type_name": "爷爷奶奶"},
            {"type_id": "60", "type_name": "伦理精选"},
            {"type_id": "61", "type_name": "啪啪直播"},
            {"type_id": "62", "type_name": "学生直播"},
            {"type_id": "63", "type_name": "自慰诱惑"},
            {"type_id": "64", "type_name": "乱伦直播"},
            {"type_id": "65", "type_name": "户外勾搭"},
            {"type_id": "66", "type_name": "车震直播"},
            {"type_id": "67", "type_name": "国产AV"},
            {"type_id": "68", "type_name": "网红主播"},
            {"type_id": "69", "type_name": "欧美精选"},
            {"type_id": "70", "type_name": "户外搭讪"},
            {"type_id": "71", "type_name": "美女自慰"},
            {"type_id": "72", "type_name": "乱伦直播"},
            {"type_id": "73", "type_name": "黑人大屌"},
            {"type_id": "74", "type_name": "群P大作战"},
            {"type_id": "75", "type_name": "欧美重口"},
            {"type_id": "76", "type_name": "人兽性交"},
            {"type_id": "77", "type_name": "SM性虐"},
            {"type_id": "78", "type_name": "人妖伪娘"},
            {"type_id": "79", "type_name": "孕妇内射"},
            {"type_id": "80", "type_name": "吃屎喝尿"},
            {"type_id": "81", "type_name": "扩阴拳交"},
            {"type_id": "82", "type_name": "阳具巨物"},
            {"type_id": "83", "type_name": "3D动漫"},
            {"type_id": "84", "type_name": "同人动漫"},
            {"type_id": "85", "type_name": "剧情故事"},
            {"type_id": "86", "type_name": "国产动漫"},
            {"type_id": "87", "type_name": "日韩动漫"},
            {"type_id": "88", "type_name": "欧美动漫"},
            {"type_id": "89", "type_name": "港台动漫"},
            {"type_id": "90", "type_name": "海外动漫"},
            {"type_id": "91", "type_name": "日本中文"},
            {"type_id": "92", "type_name": "无码流出"},
            {"type_id": "93", "type_name": "FC2"},
            {"type_id": "94", "type_name": "HEYZO"},
            {"type_id": "95", "type_name": "东京热"},
            {"type_id": "96", "type_name": "一本道"},
            {"type_id": "97", "type_name": "人妻斩"},
            {"type_id": "98", "type_name": "主播网黄"},
            {"type_id": "99", "type_name": "色情综艺"},
            {"type_id": "100", "type_name": "情色AV"}
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.200 Mobile Safari/537.36",
            "Referer": self.host + "/"
        }

    def getName(self):
        return "娇骨迷踪"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        url = self.host + "/"
        html = self.fetch(url, headers=self.headers).text
        items = self._parse_video_items(html)
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        # 分类页URL格式：/index.php/vod/type/id/{tid}/page/{page}.html
        url = f"{self.host}/index.php/vod/type/id/{tid}/page/{page}.html"
        html = self.fetch(url, headers=self.headers).text
        items = self._parse_video_items(html)
        # 提取总页数
        total = self._extract_total(html)
        return {
            "list": items,
            "page": int(page),
            "pagecount": total if total > 0 else 100,
            "limit": 20,
            "total": total
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        # 处理 ids 可能是 int 或 list
        if isinstance(ids, list):
            vod_id = str(ids[0]) if ids else ""
        else:
            vod_id = str(ids)
        if not vod_id:
            return {"list": []}
        url = f"{self.host}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        html = self.fetch(url, headers=self.headers).text
        # 提取播放地址
        play_url = self._extract_play_url(html)
        # 提取标题
        title_match = re.search(r'<h1>([^<]+)</h1>', html)
        title = title_match.group(1) if title_match else "视频"
        # 提取封面图
        pic_match = re.search(r'<img[^>]+class="thumb_img"[^>]+data-src="([^"]+)"', html)
        pic = pic_match.group(1) if pic_match else ""
        return {
            "list": [{
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_play_from": "播放",
                "vod_play_url": f"播放${play_url}" if play_url else ""
            }]
        }
    def searchContent(self, key, quick, pg="1"):
        url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}"
        html = self.fetch(url, headers=self.headers).text
        items = self._parse_video_items(html)
        return {"list": items, "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        # 传入的 id 是 m3u8 直链
        if id and (id.endswith(".m3u8") or id.startswith("https://")):
            return {"parse": 0, "url": self._m3u8_proxy_url(id), "header": self.headers}
        return {"parse": 1, "url": id, "header": self.headers}

    def _m3u8_proxy_url(self, url):
        """生成 m3u8 代理地址"""
        return self.getProxyUrl() + "&url=" + quote(str(url or ""), safe="")

    def _parse_video_items(self, html):
        """解析视频列表项"""
        items = []
        # 匹配 .block-post .item 或 .item 结构
        pattern = r'<div class="item">.*?<a href="([^"]+)" title="([^"]+)">.*?<img[^>]+data-src="([^"]+)".*?<span class="type">([^<]*)</span>.*?<i class="icon-eye"></i>([^<]*)</span>'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            link, title, pic, remark, views = match
            vod_id = re.search(r'/id/(\d+)/', link)
            if vod_id:
                items.append({
                    "vod_id": vod_id.group(1),
                    "vod_name": title.strip(),
                    "vod_pic": pic,
                    "vod_remarks": remark.strip() or views.strip()
                })
        return items

    def _extract_play_url(self, html):
        """从详情页提取播放地址"""
        # 精确匹配 player_aaaa 对象中的 url
        match = re.search(r'player_aaaa\s*=\s*\{[^}]*?"url"\s*:\s*"([^"]+)"', html)
        if match:
            url = match.group(1)
            # 处理转义的反斜杠
            url = url.replace('\\/', '/')
            return url
        return ""
    def _extract_total(self, html):
        """提取总记录数"""
        match = re.search(r'\.mac_total[^>]*>([^<]+)</span>', html)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
        # 尝试从分页提取总页数
        pages = re.findall(r'<a href="[^"]*/page/(\d+)\.html">', html)
        if pages:
            try:
                return int(pages[-1]) * 20
            except:
                pass
        return 0

    def localProxy(self, param):
        """m3u8 本地代理"""
        target = unquote(str((param or {}).get("url", "") or ""))
        if not re.match(r"^https?://", target, re.I):
            return [400, "text/plain", b"invalid url"]
        try:
            res = self.fetch(target, headers=self.headers, timeout=15)
            if not res or getattr(res, "status_code", 0) != 200:
                return [502, "text/plain", b"m3u8 fetch failed"]
            raw = getattr(res, "content", b"") or b""
            text = raw.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]
            cleaned = self._clean_m3u8(text, target)
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]
        except Exception as e:
            self.log("m3u8代理失败: " + str(e))
            return [500, "text/plain", b"m3u8 proxy error"]

    def _clean_m3u8(self, text, source_url):
        """清洗 m3u8：过滤广告分片，保留正片"""
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 处理多码率（主 m3u8）
        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"

        # 单码率：过滤非正片分片
        source_path = urlparse(source_url).path
        source_parts = [p for p in source_path.split("/") if p]
        # 取路径中前两层作为内容根目录标识（通常正片分片都在同一个子目录下）
        content_root = "/" + "/".join(source_parts[:2]) + "/" if len(source_parts) >= 2 else ""
        if not content_root:
            # 如果没有足够层级，使用源URL的目录前缀
            content_root = source_url.rsplit("/", 1)[0] + "/"

        segments = []
        pending = []
        ad_segments_removed = 0

        # 广告分片模式特征
        ad_patterns = [
            r'(?i)ad[_-]?\d*\.ts$',
            r'(?i)banner[_-]?\d*\.ts$',
            r'(?i)promo[_-]?\d*\.ts$',
            r'(?i)广告[_-]?\d*\.ts$',
            r'(?i)gg[_-]?\d*\.ts$',
            r'(?i)guanggao[_-]?\d*\.ts$',
            r'(?i)tuiguang[_-]?\d*\.ts$',
            r'(?i)推广[_-]?\d*\.ts$',
            r'(?i)sponsor[_-]?\d*\.ts$',
            r'(?i)logo[_-]?\d*\.ts$',
            r'(?i)watermark[_-]?\d*\.ts$',
            r'(?i)pre[_-]?roll[_-]?\d*\.ts$',
            r'(?i)post[_-]?roll[_-]?\d*\.ts$',
            r'(?i)mid[_-]?roll[_-]?\d*\.ts$',
        ]

        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media = urljoin(source_url, line)
                # 检查是否为广告分片
                is_ad = False

                # 1. 路径检测：分片路径是否在内容根目录下
                if content_root and content_root not in urlparse(media).path:
                    is_ad = True

                # 2. 文件名模式检测
                if not is_ad:
                    file_name = urlparse(media).path.split("/")[-1]
                    for pattern in ad_patterns:
                        if re.search(pattern, file_name):
                            is_ad = True
                            break

                # 3. 时长检测：#EXTINF 中的时长异常（过短或过长）
                if not is_ad and pending:
                    extinf_line = pending[0]
                    duration_match = re.search(r'#EXTINF:([\d.]+)', extinf_line)
                    if duration_match:
                        duration = float(duration_match.group(1))
                        if duration < 1.0 or duration > 120.0:
                            is_ad = True

                if is_ad:
                    ad_segments_removed += 1
                else:
                    segments.extend(pending)
                    segments.append(media)
                pending = []
                continue
            segments.append(self._rewrite_m3u8_tag(line, source_url))

        # 后处理：移除冗余的 EXT-X-DISCONTINUITY 和 EXT-X-KEY:METHOD=NONE
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line == "#EXT-X-KEY:METHOD=NONE" or line == "#EXT-X-DISCONTINUITY":
                if not out or out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
                    continue
            out.append(line)

        while len(out) > 1 and out[-2] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
            out.pop(-2)

        if ad_segments_removed:
            self.log("m3u8已过滤广告分片: %d 个" % ad_segments_removed)

        return "\n".join(out) + "\n"
    def _rewrite_m3u8_tag(self, line, source_url):
        """重写 m3u8 标签中的 URI"""
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(match):
                return 'URI="' + urljoin(source_url, match.group(1)) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)
        if line and not line.startswith("#"):
            return urljoin(source_url, line)
        return line