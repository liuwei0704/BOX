# coding: utf-8
# 站点: 护士AV (https://5g.hushiav7.cc/a/)
# 类型: MacCMS HTML解析站 + m3u8 本地代理去广告
# 主域名: https://5g.hushiav7.cc/a/

import re
import json
import urllib.parse
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://5g.hushiav7.cc/a"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "244", "type_name": "55资源"},
            {"type_id": "358", "type_name": "番茄资源"},
            {"type_id": "119", "type_name": "不卡资源"},
            {"type_id": "286", "type_name": "兔儿资源"},
            {"type_id": "370", "type_name": "森林资源"},
            {"type_id": "329", "type_name": "库库资源"}
        ]
        self.filters = {
            "244": [
                {"key": "sub", "name": "子分类", "value": [
                    {"n": "全部", "v": "244"},
                    {"n": "AV解说", "v": "266"},
                    {"n": "国产自拍", "v": "254"},
                    {"n": "熟女人妻", "v": "255"},
                    {"n": "萝莉少女", "v": "256"},
                    {"n": "百合剧情", "v": "257"},
                    {"n": "美乳巨乳", "v": "258"},
                    {"n": "强歼乱伦", "v": "259"},
                    {"n": "抖音视频", "v": "260"}
                ]}
            ],
            "358": [
                {"key": "sub", "name": "子分类", "value": [
                    {"n": "全部", "v": "358"},
                    {"n": "高清有码", "v": "369"},
                    {"n": "动漫精选", "v": "368"},
                    {"n": "学生妹", "v": "367"},
                    {"n": "中文字幕", "v": "366"},
                    {"n": "高清无码", "v": "365"},
                    {"n": "黑料网曝", "v": "364"},
                    {"n": "主播网红", "v": "363"},
                    {"n": "乱伦系列", "v": "362"}
                ]}
            ],
            "119": [
                {"key": "sub", "name": "子分类", "value": [
                    {"n": "全部", "v": "119"},
                    {"n": "国产视频", "v": "120"},
                    {"n": "中文字幕", "v": "121"},
                    {"n": "国产传媒", "v": "122"},
                    {"n": "日本有码", "v": "123"},
                    {"n": "日本无码", "v": "124"},
                    {"n": "欧美无码", "v": "125"},
                    {"n": "强干乱伦", "v": "126"},
                    {"n": "制服诱惑", "v": "127"}
                ]}
            ],
            "286": [
                {"key": "sub", "name": "子分类", "value": [
                    {"n": "全部", "v": "286"},
                    {"n": "精品推荐", "v": "304"},
                    {"n": "主播秀色", "v": "305"},
                    {"n": "日本有码", "v": "306"},
                    {"n": "日本无码", "v": "307"},
                    {"n": "中文字幕", "v": "308"},
                    {"n": "童颜巨乳", "v": "309"},
                    {"n": "性感人妻", "v": "310"},
                    {"n": "强歼乱伦", "v": "311"}
                ]}
            ],
            "370": [
                {"key": "sub", "name": "子分类", "value": [
                    {"n": "全部", "v": "370"},
                    {"n": "精品推荐", "v": "371"},
                    {"n": "国产情色", "v": "372"},
                    {"n": "亚洲无码", "v": "373"},
                    {"n": "亚洲有码", "v": "374"},
                    {"n": "中文字幕", "v": "375"},
                    {"n": "强*乱伦", "v": "376"},
                    {"n": "欧美精品", "v": "377"},
                    {"n": "萝莉少女", "v": "378"}
                ]}
            ],
            "329": [
                {"key": "sub", "name": "子分类", "value": [
                    {"n": "全部", "v": "329"},
                    {"n": "日本有码", "v": "330"},
                    {"n": "无码中文", "v": "331"},
                    {"n": "有码中文", "v": "332"},
                    {"n": "日本无码", "v": "333"},
                    {"n": "国产视频", "v": "334"},
                    {"n": "欧美高清", "v": "335"},
                    {"n": "动漫剧情", "v": "336"}
                ]}
            ]
        }
        # m3u8 广告切片识别黑名单
        self.ad_keywords = [
            "ad", "advertisement", "notice", "guanggao", 
            "qq.com", "baidu.com", "p2p", "sign", "gambling",
            "banner", "promo", "juqi", "mac.m3u8", "ad_slice"
        ]

    def init(self, extend=""):
        self.extend = extend or ""

    def _fetch_html(self, url):
        try:
            res = self.fetch(url, headers=self.headers, timeout=15)
            if res is None:
                return ""
            if hasattr(res, "text") and res.text:
                return res.text
            if hasattr(res, "content") and res.content:
                try:
                    return res.content.decode('utf-8', errors='ignore')
                except Exception:
                    pass
            return ""
        except Exception:
            return ""

    def _fix_url(self, url, base_url=None):
        if not url:
            return ''
        url = url.strip()
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        
        base = base_url if base_url else self.host
        if url.startswith('/'):
            parts = urllib.parse.urlparse(base)
            return f"{parts.scheme}://{parts.netloc}{url}"
        
        return urllib.parse.urljoin(base, url)

    def _parse_extend(self, extend):
        if not extend:
            return {}
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            try:
                return json.loads(extend)
            except Exception:
                pass
            res = {}
            for item in re.findall(r'(\w+)=([^&{}]+)', extend):
                res[item[0]] = item[1]
            return res
        return {}

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html(self.host + "/")
        items = self._parse_list(html)
        return {"list": items[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        actual_tid = tid
        ext_dict = self._parse_extend(extend)
        if ext_dict.get("sub"):
            actual_tid = ext_dict["sub"]

        page = pg or "1"
        url = f"{self.host}/index.php/vod/type/id/{actual_tid}/page/{page}.html"
        html = self._fetch_html(url)
        items = self._parse_list(html)
        pagecount = self._get_pagecount(html)
        return {
            "list": items,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 20,
            "total": pagecount * 20
        }

    def detailContent(self, ids):
        vid = str(ids[0]) if isinstance(ids, list) else str(ids)
        url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
        html = self._fetch_html(url)
        return self._parse_detail(html, vid)

    def searchContent(self, key, quick, pg="1"):
        if not key or not key.strip():
            return {"list": [], "page": 1}
        page = pg or "1"
        url = f"{self.host}/index.php/vod/search/wd/{urllib.parse.quote(key)}/page/{page}.html"
        html = self._fetch_html(url)
        items = self._parse_list(html)
        return {"list": items, "page": int(page)}

    def playerContent(self, flag, id, vipFlags):
        if id.startswith("http"):
            play_url = id
        else:
            parts = id.split("|")
            if len(parts) >= 3:
                vid, sid, nid = parts[0], parts[1], parts[2]
                play_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/{sid}/nid/{nid}.html"
            else:
                play_url = id

        html = self._fetch_html(play_url)
        m3u8_url = ""
        if html:
            match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
            if match:
                m3u8_url = match.group(1).replace("\\/", "/")
            else:
                match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
                if match:
                    m3u8_url = match.group(0).replace("\\/", "/")

        if m3u8_url:
            # 使用 proxy://do=m3u8 走本地代理实现切片级去广告
            proxy_url = f"proxy://do=m3u8&url={urllib.parse.quote(m3u8_url)}"
            return {
                "parse": 0,
                "url": proxy_url,
                "header": self.headers
            }

        return {"parse": 1, "url": play_url, "header": self.headers}

    def localProxy(self, param):
        """
        本地代理处理，专门拦截并清洗 m3u8 中的插播广告
        """
        req_type = param.get("do", "")
        url = param.get("url", "")
        if not url:
            return [404, "text/plain", "Missing URL"]

        if req_type == "m3u8":
            res = self.fetch(url, headers=self.headers, timeout=15)
            if not res or not res.text:
                return [404, "text/plain", "Fetch M3U8 Failed"]

            m3u8_text = res.text
            base_url = url

            # 若为主 m3u8 (包含其他子 index.m3u8)
            if "#EXT-X-STREAM-INF" in m3u8_text:
                lines = []
                for line in m3u8_text.splitlines():
                    line_str = line.strip()
                    if line_str and not line_str.startswith("#"):
                        sub_url = self._fix_url(line_str, base_url)
                        lines.append(f"proxy://do=m3u8&url={urllib.parse.quote(sub_url)}")
                    else:
                        lines.append(line)
                return [200, "application/vnd.apple.mpegurl", "\n".join(lines)]

            # 过滤广告切片与非正片断层标记
            clean_lines = []
            pending_extinf = None

            for line in m3u8_text.splitlines():
                line_str = line.strip()
                if not line_str:
                    continue

                # 剔除插播广告的不连续性标记
                if line_str.startswith("#EXT-X-DISCONTINUITY"):
                    continue

                if line_str.startswith("#EXTINF"):
                    pending_extinf = line_str
                    continue

                if line_str.startswith("#EXT-X-KEY"):
                    # 重新映射加密 Key 的绝对路径并走代理
                    key_match = re.search(r'URI="([^"]+)"', line_str)
                    if key_match:
                        raw_key_url = key_match.group(1)
                        abs_key_url = self._fix_url(raw_key_url, base_url)
                        proxy_key_url = f"proxy://do=proxy&url={urllib.parse.quote(abs_key_url)}"
                        line_str = line_str.replace(raw_key_url, proxy_key_url)
                    clean_lines.append(line_str)
                    continue

                if line_str.startswith("#"):
                    clean_lines.append(line_str)
                    continue

                # 校验切片是否为广告链接
                if any(kw in line_str.lower() for kw in self.ad_keywords):
                    # 匹配到广告分片，跳过对应的 #EXTINF 与 TS 地址
                    pending_extinf = None
                    continue

                # 正确切片：先补全上一步保存的 #EXTINF，再补全 TS 绝对路径
                if pending_extinf:
                    clean_lines.append(pending_extinf)
                    pending_extinf = None

                abs_ts_url = self._fix_url(line_str, base_url)
                clean_lines.append(abs_ts_url)

            return [200, "application/vnd.apple.mpegurl", "\n".join(clean_lines)]

        elif req_type == "proxy":
            # 通用文件代理 (处理跨域 Key 或资源文件)
            res = self.fetch(url, headers=self.headers, timeout=15)
            if res and hasattr(res, "content"):
                return [200, "application/octet-stream", res.content]
            return [404, "text/plain", "Proxy Failed"]

        return [404, "text/plain", "Invalid Action"]

    def _parse_list(self, html):
        items = []
        if not html:
            return items
        pattern = r'<li[^>]*class="[^"]*content-item[^"]*"[^>]*>(.*?)</li>'
        li_matches = re.findall(pattern, html, re.DOTALL)
        for li in li_matches:
            link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>', li)
            if not link_match:
                continue
            link = link_match.group(1)
            title_match = re.search(r'<a[^>]*title="([^"]*)"', li)
            title = title_match.group(1) if title_match else ""
            img_match = re.search(r'<img[^>]*data-original="([^"]+)"', li)
            if not img_match:
                img_match = re.search(r'<img[^>]*src="([^"]+)"', li)
            pic = img_match.group(1) if img_match else ""
            note_match = re.search(r'<span[^>]*class="[^"]*note[^"]*"[^>]*>([^<]*)</span>', li)
            remark = note_match.group(1) if note_match else ""
            vid_match = re.search(r'/vod/detail/id/(\d+)\.html', link)
            vid = vid_match.group(1) if vid_match else link
            if title:
                items.append({
                    "vod_id": vid,
                    "vod_name": title.strip(),
                    "vod_pic": pic,
                    "vod_remarks": remark.strip()
                })
        return items

    def _parse_detail(self, html, vid):
        if not html:
            return {"list": []}

        # 修复后的完整正则表达式匹配
        title_match = re.search(r'<h5[^>]*class="[^"]*title[^"]*"[^>]*>名称：([^<]*)</h5>', html)
        title = title_match.group(1).strip() if title_match else ""

        img_match = re.search(r'<img[^>]*class="[^"]*img-responsive[^"]*"[^>]*src="([^"]+)"', html)
        pic = img_match.group(1) if img_match else ""

        class_match = re.search(r'<h5[^>]*class="[^"]*title[^"]*"[^>]*>类别：([^<]*)</h5>', html)
        remark = class_match.group(1).strip() if class_match else ""

        content_match = re.search(r'<div[^>]*class="[^"]*vod_content[^"]*"[^>]*>([^<]*)</div>', html)
        content = content_match.group(1).strip() if content_match else ""

        play_from = []
        play_url = []

        line_matches = re.findall(r'<div[^>]*class="[^"]*ap-player-heading[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        line_names = []
        for lm in line_matches:
            strong_match = re.search(r'<strong>(.*?)</strong>', lm)
            if strong_match:
                line_names.append(strong_match.group(1).strip())
            else:
                text = re.sub(r'<[^>]+>', '', lm).strip()
                if text:
                    line_names.append(text)

        list_matches = re.findall(r'<ul[^>]*class="[^"]*ap-player-list[^"]*"[^>]*>(.*?)</ul>', html, re.DOTALL)
        for idx, ul in enumerate(list_matches):
            line_name = line_names[idx] if idx < len(line_names) else f"线路{idx+1}"
            items = re.findall(r'<li[^>]*class="[^"]*ap-player-item[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', ul, re.DOTALL)
            if items:
                eps = []
                for href, name in items:
                    name_clean = re.sub(r'<[^>]+>', '', name).strip()
                    eps.append(f"{name_clean}${href}")
                if eps:
                    play_from.append(line_name)
                    play_url.append("#".join(eps))

        if not play_from:
            btn_match = re.search(r'<a[^>]*href="([^"]*vod/play[^"]*)"[^>]*>立即播放</a>', html)
            if btn_match:
                play_url_raw = self._fix_url(btn_match.group(1))
                sid_match = re.search(r'sid/(\d+)', play_url_raw)
                nid_match = re.search(r'nid/(\d+)', play_url_raw)
                sid = sid_match.group(1) if sid_match else "1"
                nid = nid_match.group(1) if nid_match else "1"
                play_from.append("默认线路")
                play_url.append(f"第1集${vid}|{sid}|{nid}")

        return {
            "list": [{
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark,
                "vod_content": content,
                "vod_play_from": "$$$".join(play_from) if play_from else "",
                "vod_play_url": "$$$".join(play_url) if play_url else ""
            }]
        }

    def _get_pagecount(self, html):
        if not html:
            return 1
        last_match = re.search(r'<a[^>]*href="[^"]*page/(\d+)[^"]*"[^>]*>尾页</a>', html)
        if last_match:
            try:
                return int(last_match.group(1))
            except Exception:
                pass
        matches = re.findall(r'<a[^>]*href="[^"]*page/(\d+)[^"]*"[^>]*>(\d+)</a>', html)
        max_page = 1
        for href, num in matches:
            try:
                p = int(num)
                if p > max_page:
                    max_page = p
            except Exception:
                pass
        return max_page

    def destroy(self):
        pass