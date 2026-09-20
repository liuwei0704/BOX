# coding: utf-8
# 站点：优酷视界TV
# 域名：https://9yujrhflajhak6c2uon7xbmrko.youkushijie.sbs/
# 类型：MacCMS 标准影视站
# 分类：动漫肉番(1)、主播大秀(2)、校园春色(14)、巨乳系列(3)、偷拍自拍(15)、制服诱惑(4)、强奸乱伦(16)、SM调教(5)

import json
import re
from urllib.parse import quote, urljoin, unquote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://9yujrhflajhak6c2uon7xbmrko.youkushijie.sbs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "1", "type_name": "动漫肉番"},
            {"type_id": "2", "type_name": "主播大秀"},
            {"type_id": "14", "type_name": "校园春色"},
            {"type_id": "3", "type_name": "巨乳系列"},
            {"type_id": "15", "type_name": "偷拍自拍"},
            {"type_id": "4", "type_name": "制服诱惑"},
            {"type_id": "16", "type_name": "强奸乱伦"},
            {"type_id": "5", "type_name": "SM调教"}
        ]
        self.filters = {str(c["type_id"]): [] for c in self.classes}

    def getName(self):
        return "优酷视界"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        try:
            res = self.fetch(self.host + "/", headers=self.headers, timeout=15)
            html = res.text if hasattr(res, "text") else ""
            if not html:
                return {"list": []}

            items = []
            prog_cards = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*program-card[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*program-name[^"]*">([^<]+)</div>.*?<div[^>]*class="[^"]*program-highlight[^"]*">([^<]*)</div>', html, re.DOTALL)
            for href, pic, name, remark in prog_cards:
                vid = self._extract_vid_from_url(href)
                if vid:
                    items.append({
                        "vod_id": vid,
                        "vod_name": name.strip(),
                        "vod_pic": pic if pic.startswith("http") else self.host + pic,
                        "vod_remarks": remark.strip()[:20] if remark.strip() else "热播"
                    })

            kids_cards = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*kids-card[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*kids-name[^"]*">([^<]+)</div>.*?<div[^>]*class="[^"]*kids-desc[^"]*">([^<]*)</div>', html, re.DOTALL)
            for href, pic, name, remark in kids_cards:
                vid = self._extract_vid_from_url(href)
                if vid:
                    items.append({
                        "vod_id": vid,
                        "vod_name": name.strip(),
                        "vod_pic": pic if pic.startswith("http") else self.host + pic,
                        "vod_remarks": remark.strip()[:20] if remark.strip() else "上新"
                    })

            return {"list": items}
        except Exception as e:
            self.log({"action": "homeVideoContent", "error": str(e)})
            return {"list": []}

    def _extract_vid_from_url(self, url):
        m = re.search(r'/play/id/(\d+)', url)
        return m.group(1) if m else None

    def _parse_extend(self, extend):
        if not extend:
            return {}
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            try:
                return json.loads(extend)
            except:
                pass
            result = {}
            for part in extend.split(','):
                if '=' in part:
                    k, v = part.split('=', 1)
                    result[k.strip()] = v.strip()
            return result
        return {}

    def _extract_m3u8(self, html):
        if not html:
            return None, None

        player_match = re.search(r'var\s+player_aaaa\s*=\s*({[^;]+});', html, re.DOTALL)
        if player_match:
            try:
                player_data = json.loads(player_match.group(1))
                url = player_data.get("url")
                if url and url.endswith((".m3u8", ".mp4")):
                    url = url.replace("\\/", "/")
                    return url, "player_aaaa"
            except:
                pass

        m3u8_matches = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
        if m3u8_matches:
            url = m3u8_matches[0].replace("\\/", "/")
            return url, "direct"

        iframe_match = re.search(r'<iframe[^>]*src="[^"]*url=([^"&]+)"[^>]*>', html)
        if iframe_match:
            url = unquote(iframe_match.group(1)).replace("\\/", "/")
            if url.endswith((".m3u8", ".mp4")):
                return url, "iframe"

        loose_match = re.search(r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"', html)
        if loose_match:
            url = loose_match.group(1).replace("\\/", "/")
            return url, "loose"

        return None, None

    def categoryContent(self, tid, pg, filter, extend):
        try:
            # 兼容多种分页参数来源
            page = "1"
            if pg and pg not in ("", "0"):
                page = str(pg)
            elif extend and isinstance(extend, dict):
                page = str(extend.get("page") or extend.get("pg") or "1")
            elif isinstance(extend, str):
                try:
                    ex = json.loads(extend)
                    page = str(ex.get("page") or ex.get("pg") or "1")
                except:
                    pass

            if isinstance(page, int):
                page = str(page)

            # 构建 URL：第一页用 .html，第二页开始用 /page/{page}.html
            base_url = f"{self.host}/index.php/vod/type/id/{tid}.html"
            if page == "1":
                url = base_url
            else:
                url = base_url.replace('.html', f'/page/{page}.html')

            res = self.fetch(url, headers=self.headers, timeout=15)
            html = res.text if hasattr(res, "text") else ""
            if not html:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

            # 解析视频列表
            items = []
            cards = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*kids-card[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*kids-name[^"]*">([^<]+)</div>.*?<div[^>]*class="[^"]*kids-desc[^"]*">([^<]*)</div>', html, re.DOTALL)
            for href, pic, name, remark in cards:
                vid = self._extract_vid_from_url(href)
                if vid:
                    items.append({
                        "vod_id": vid,
                        "vod_name": name.strip(),
                        "vod_pic": pic if pic.startswith("http") else self.host + pic,
                        "vod_remarks": remark.strip()[:20] if remark.strip() else ""
                    })

            # ===== 计算分页信息 =====
            pagecount = 1

            # 方法1：从所有 page-btn 中提取最大页码（包括 <a> 和 <button>）
            page_matches = re.findall(r'<a[^>]*class="[^"]*page-btn[^"]*"[^>]*>(\d+)</a>', html)
            page_matches += re.findall(r'<button[^>]*class="[^"]*page-btn[^"]*"[^>]*>(\d+)</button>', html)
            if page_matches:
                pagecount = max([int(p) for p in page_matches if p.isdigit()] + [1])

            # 方法2：从页面中提取"共X页"或"第1/X页"
            page_info = re.search(r'共\s*(\d+)\s*页', html)
            if not page_info:
                page_info = re.search(r'第\s*\d+\s*/\s*(\d+)\s*页', html)
            if page_info:
                pagecount = int(page_info.group(1))

            # 方法3：从分页控件中的省略号后的页码提取
            dots_match = re.search(r'\.\.\.\s*<a[^>]*>(\d+)</a>', html)
            if dots_match:
                pagecount = int(dots_match.group(1))

            # 方法4：探测下一页
            if pagecount == 1 and int(page) == 1:
                try:
                    next_url = base_url.replace('.html', '/page/2.html')
                    next_res = self.fetch(next_url, headers=self.headers, timeout=10)
                    next_html = next_res.text if hasattr(next_res, "text") else ""
                    if next_html and "kids-card" in next_html:
                        pagecount = 2
                        third_url = base_url.replace('.html', '/page/3.html')
                        third_res = self.fetch(third_url, headers=self.headers, timeout=10)
                        third_html = third_res.text if hasattr(third_res, "text") else ""
                        if third_html and "kids-card" in third_html:
                            pagecount = 3
                            for p in range(4, 6):
                                test_url = base_url.replace('.html', f'/page/{p}.html')
                                test_res = self.fetch(test_url, headers=self.headers, timeout=8)
                                test_html = test_res.text if hasattr(test_res, "text") else ""
                                if test_html and "kids-card" in test_html:
                                    pagecount = p
                                else:
                                    break
                except:
                    pass

            # 方法5：从数据量推断
            if len(items) >= 20 and pagecount == 1:
                pagecount = int(page) + 1

            return {
                "list": items,
                "page": int(page),
                "pagecount": pagecount,
                "limit": 20,
                "total": pagecount * 20
            }
        except Exception as e:
            self.log({"action": "categoryContent", "tid": tid, "pg": pg, "error": str(e)})
            return {"list": [], "page": int(pg or 1), "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        try:
            if isinstance(ids, (list, tuple)):
                vid = str(ids[0])
            else:
                vid = str(ids)

            play_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"

            vod = {
                "vod_id": str(vid),
                "vod_name": f"视频_{vid}",
                "vod_pic": "",
                "vod_content": "",
                "vod_remarks": "",
                "vod_play_from": "优酷云",
                "vod_play_url": ""
            }

            try:
                res = self.fetch(play_url, headers=self.headers, timeout=15)
                html = res.text if hasattr(res, "text") else ""

                if html:
                    title_match = re.search(r'<title>([^<]+)</title>', html)
                    if title_match:
                        title = title_match.group(1).replace(" - 高清资源 - 优酷视界", "").replace("在线播放", "").strip()
                        if title:
                            vod["vod_name"] = title

                    pic_match = re.search(r'<img[^>]*class="[^"]*vod_img[^"]*"[^>]*src="([^"]+)"', html, re.DOTALL)
                    if not pic_match:
                        pic_match = re.search(r'<img[^>]*data-original="([^"]+)"', html, re.DOTALL)
                    if pic_match:
                        pic = pic_match.group(1)
                        vod["vod_pic"] = pic if pic.startswith("http") else self.host + pic

                    desc_match = re.search(r'<span[^>]*class="[^"]*vod_content[^"]*"[^>]*>([^<]*)</span>', html)
                    if desc_match:
                        vod["vod_content"] = desc_match.group(1).strip()

                    m3u8_url, source = self._extract_m3u8(html)
                    if m3u8_url:
                        vod["vod_play_url"] = f"播放$play@@{quote(m3u8_url)}"
                    else:
                        vod["vod_play_url"] = f"播放$play@@{quote(play_url)}"
            except Exception as e:
                self.log({"action": "detailContent_fetch_error", "error": str(e)})
                vod["vod_play_url"] = f"播放$play@@{quote(play_url)}"

            return {"list": [vod]}
        except Exception as e:
            self.log({"action": "detailContent_error", "ids": ids, "error": str(e)})
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        try:
            url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}"
            if pg != "1":
                url += f"&pg={pg}"

            res = self.fetch(url, headers=self.headers, timeout=15)
            html = res.text if hasattr(res, "text") else ""
            if not html:
                return {"list": [], "page": int(pg)}

            items = []
            cards = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*kids-card[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*kids-name[^"]*">([^<]+)</div>.*?<div[^>]*class="[^"]*kids-desc[^"]*">([^<]*)</div>', html, re.DOTALL)
            for href, pic, name, remark in cards:
                vid = self._extract_vid_from_url(href)
                if vid:
                    items.append({
                        "vod_id": vid,
                        "vod_name": name.strip(),
                        "vod_pic": pic if pic.startswith("http") else self.host + pic,
                        "vod_remarks": remark.strip()[:20] if remark.strip() else ""
                    })

            return {"list": items, "page": int(pg)}
        except Exception as e:
            self.log({"action": "searchContent", "key": key, "error": str(e)})
            return {"list": [], "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "")

        if raw.startswith("play@@"):
            url = unquote(raw.replace("play@@", "", 1))
            url = url.replace("\\/", "/")
            if not url.endswith((".m3u8", ".mp4")):
                try:
                    res = self.fetch(url, headers=self.headers, timeout=10)
                    html = res.text if hasattr(res, "text") else ""
                    if html:
                        m3u8_url, source = self._extract_m3u8(html)
                        if m3u8_url:
                            return {"parse": 0, "url": m3u8_url, "header": {"User-Agent": self.headers["User-Agent"]}}
                except:
                    pass
                return {"parse": 1, "url": url, "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}}
            return {"parse": 0, "url": url, "header": {"User-Agent": self.headers["User-Agent"]}}

        if raw.endswith((".m3u8", ".mp4")):
            url = raw.replace("\\/", "/")
            return {"parse": 0, "url": url, "header": {"User-Agent": self.headers["User-Agent"]}}

        if raw.startswith("http"):
            url = raw.replace("\\/", "/")
            try:
                res = self.fetch(url, headers=self.headers, timeout=10)
                html = res.text if hasattr(res, "text") else ""
                if html:
                    m3u8_url, source = self._extract_m3u8(html)
                    if m3u8_url:
                        return {"parse": 0, "url": m3u8_url, "header": {"User-Agent": self.headers["User-Agent"]}}
            except:
                pass

        return {"parse": 1, "url": raw, "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}}

    def localProxy(self, param):
        target = unquote(str((param or {}).get("url", "") or ""))
        if not re.match(r"^https?://", target, re.I):
            return [400, "text/plain", b"invalid url"]
        try:
            res = self.fetch(target, headers={"User-Agent": self.headers["User-Agent"]}, timeout=15, verify=False)
            if not res or getattr(res, "status_code", 0) != 200:
                return [502, "text/plain", b"m3u8 fetch failed"]
            raw = getattr(res, "content", b"") or b""
            text = raw.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]
            return [200, "application/vnd.apple.mpegurl", raw]
        except Exception as e:
            self.log("m3u8代理失败: " + str(e))
            return [500, "text/plain", b"m3u8 proxy error"]