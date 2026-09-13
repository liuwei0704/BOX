# coding: utf-8
# 站点：爆爽短剧 (https://www.bzhjz.com/)
# 架构：MacCMS + mxone-2 模板，标准 HTML 服务端渲染
# 分类：1电影 2电视剧 3综艺 4动漫 5短剧
# 列表分页：/vodshow/{tid}--------{pg}---.html
# 筛选：年份 /vodshow/{tid}-----------{year}.html ; 语言 /vodshow/{tid}----{lang}-------.html
#       地区 /vodshow/{tid}-{area}---------.html ; 字母 /vodshow/{tid}-----{letter}------.html
# 详情页：/vod/{id}.html
# 播放页：/play/{id}-{sid}-{nid}.html  player_aaaa.url = m3u8 直链（encrypt:0）
# 搜索页：/vodsearch/{kw}-------------.html
# 站点有 cookie 挑战：首页下发 server_session，带 cookie 才能访问内容页
# 主域名：https://www.bzhjz.com/
# 最后验证：2026-09-14
import json
import re
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.extend = ""
        self.host = "https://www.bzhjz.com"
        self._cookie = ""
        self._warmed = False
        self.classes = [
            {"type_id": "5", "type_name": "短剧"},
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "28", "type_name": "古装短剧"},
            {"type_id": "29", "type_name": "穿越短剧"},
            {"type_id": "30", "type_name": "甜宠短剧"},
            {"type_id": "31", "type_name": "逆袭短剧"},
        ]
        self.filters = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    def getName(self):
        return "爆爽短剧"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    # ---------- 网络层（cookie 挑战双保险：手动带 Cookie + 沙盒 session） ----------
    def _accumulate_cookie(self, r):
        try:
            sc = None
            if hasattr(r, "headers") and r.headers:
                sc = r.headers.get("Set-Cookie") or r.headers.get("set-cookie")
            if not sc:
                return
            parts = re.split(r",(?=[^;]+=)", sc)
            existing = {}
            if self._cookie:
                for item in self._cookie.split(";"):
                    item = item.strip()
                    if "=" in item:
                        k2, v2 = item.split("=", 1)
                        existing[k2.strip()] = v2.strip()
            for p in parts:
                kv = p.split(";")[0].strip()
                if "=" not in kv:
                    continue
                name = kv.split("=", 1)[0].strip()
                existing[name] = kv.split("=", 1)[1].strip()
            self._cookie = "; ".join("%s=%s" % (k, v) for k, v in existing.items())
        except Exception:
            pass

    def _warmup(self):
        try:
            r = self.fetch(self.host + "/", headers=self.headers, timeout=15)
            if r:
                self._accumulate_cookie(r)
        except Exception:
            pass

    def _fetch_html(self, url):
        # cookie 挑战：手动提取并累积 Set-Cookie 双保险；挑战页重试
        if not self._cookie:
            self._warmup()
        for attempt in range(3):
            h = dict(self.headers)
            if self._cookie:
                h["Cookie"] = self._cookie
            try:
                r = self.fetch(url, headers=h, timeout=15)
            except Exception as e:
                self.log({"fetch": "fail", "url": url[:60], "error": type(e).__name__, "try": attempt})
                self._warmup()
                continue
            if not r:
                continue
            self._accumulate_cookie(r)
            text = r.text or ""
            is_challenge = len(text) < 800 and "window.location.href" in text
            if r.status_code == 200 and not is_challenge:
                return text
            self._warmup()
        return ""

    # ---------- 解析 ----------
    def _parse_list(self, html):
        items = []
        if not html:
            return items
        # 按 <div class="module-item"> 切分，每块到下一个 module-item 或卡片尾部
        parts = html.split('<div class="module-item">')
        seen = set()
        for b in parts[1:]:
            # 截断到卡片结束（module-item-text 之后）
            te = b.find('module-item-text')
            if te != -1:
                b = b[:te + 200]
            m = re.search(r'<a href="(/vod/(\d+)\.html)"[^>]*title="([^"]*)"', b)
            if m:
                link, vid, title = m.group(1), m.group(2), m.group(3)
            else:
                m2 = re.search(r'<a href="(/vod/(\d+)\.html)"', b)
                if not m2:
                    continue
                link, vid, title = m2.group(1), m2.group(2), ""
            if vid in seen:
                continue
            seen.add(vid)
            if not title:
                tm = re.search(r'title="([^"]*)"', b)
                if tm:
                    title = tm.group(1)
            pic = ""
            pm = re.search(r'data-src="([^"]+)"', b)
            if pm:
                pic = pm.group(1)
            if pic and not pic.startswith("http"):
                pic = urljoin(self.host + "/", pic)
            remark = ""
            rm = re.search(r'<div class="module-item-text">([^<]*)</div>', b)
            if rm:
                remark = rm.group(1).strip()
            items.append({"vod_id": vid, "vod_name": title.strip(), "vod_pic": pic, "vod_remarks": remark})
        return items
    def _parse_search(self, html):
        items = []
        if not html:
            return items
        blocks = re.findall(r'<div class="module-search-item">(.*?)(?=<div class="module-search-item">|</div>\s*</div>\s*</div>\s*<div class="module-footer)', html, re.S)
        seen = set()
        for b in blocks:
            m = re.search(r'<h3><a href="(/vod/(\d+)\.html)"[^>]*title="([^"]*)"', b)
            if not m:
                m = re.search(r'<a href="(/vod/(\d+)\.html)"[^>]*title="([^"]*)"', b)
            if not m:
                continue
            vid = m.group(2)
            if vid in seen:
                continue
            seen.add(vid)
            title = m.group(3)
            pic = ""
            pm = re.search(r'data-src="([^"]+)"', b)
            if pm:
                pic = pm.group(1)
            if pic and not pic.startswith("http"):
                pic = urljoin(self.host + "/", pic)
            remark = ""
            rm = re.search(r'<a class="video-serial"[^>]*>([^<]*)</a>', b)
            if rm:
                remark = rm.group(1).strip()
            items.append({"vod_id": vid, "vod_name": title.strip(), "vod_pic": pic, "vod_remarks": remark})
        return items

    def _get_pagecount(self, html, pg):
        try:
            pages = re.findall(r'/vodshow/[^"\']*?-(\d+)---\.html', html)
            if pages:
                return max(int(x) for x in pages)
            m = re.search(r'(\d+)\s*/\s*(\d+)\s*页', html)
            if m:
                return int(m.group(2))
        except Exception:
            pass
        return int(pg)

    def homeVideoContent(self):
        html = self._fetch_html(self.host + "/vodshow/5--------1---.html")
        return {"list": self._parse_list(html)}

    @staticmethod
    def _norm_ids(ids):
        if ids is None:
            return ""
        if isinstance(ids, (list, tuple)):
            if not ids:
                return ""
            ids = ids[0]
        if isinstance(ids, bytes):
            ids = ids.decode("utf-8", errors="ignore")
        return str(ids).strip()

    def _skeleton(self, vid, title="", pic="", remarks="解析中"):
        pid = str(vid).split("|$|")[0].replace("$", "|")
        return {"list": [{
            "vod_id": vid, "vod_name": title or "未知标题", "vod_pic": pic or "",
            "vod_remarks": remarks, "vod_content": "",
            "vod_play_from": "播放", "vod_play_url": "播放$" + pid,
        }]}

    def detailContent(self, ids):
        raw = self._norm_ids(ids)
        if not raw:
            return {"list": []}
        ps = raw.split("|$|")
        vod_id = ps[0]
        old_name = ps[1] if len(ps) > 1 else ""
        old_pic = ps[2] if len(ps) > 2 else ""
        old_remark = ps[3] if len(ps) > 3 else ""

        url = self.host + "/vod/" + vod_id + ".html"
        html = self._fetch_html(url)
        if not html or len(html) < 500:
            return self._skeleton(raw, old_name, old_pic, old_remark)

        try:
            name = old_name
            nm = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
            if nm:
                name = re.sub(r"<[^>]+>", "", nm.group(1)).strip() or name
            if not name:
                tm = re.search(r"<title>(.*?)</title>", html, re.S)
                if tm:
                    name = re.split(r"[-_]", tm.group(1))[0].strip()

            pic = old_pic
            pm = re.search(r'<img[^>]*class="[^"]*lazy[^"]*"[^>]*data-src="([^"]+)"', html)
            if pm:
                pic = pm.group(1)
            if pic and not pic.startswith("http"):
                pic = urljoin(self.host + "/", pic)

            remark = old_remark
            rmk = re.search(r'状态[：:]\s*</span>\s*<[^>]*>([^<]*)<', html)
            if rmk:
                remark = rmk.group(1).strip()

            content = ""
            cm = re.search(r'<div class="[^"]*module-info-introduction-content[^"]*"[^>]*>(.*?)</div>', html, re.S)
            if cm:
                content = re.sub(r"<[^>]+>", "", cm.group(1)).strip()

            actor = ""
            am = re.search(r'主演[：:]\s*</span>(.*?)</div>', html, re.S)
            if am:
                actor = ",".join(re.findall(r'>([^<>/]+)</a>', am.group(1)))

            director = ""
            dm = re.search(r'导演[：:]\s*</span>(.*?)</div>', html, re.S)
            if dm:
                director = ",".join(re.findall(r'>([^<>/]+)</a>', dm.group(1)))

            # 线路：data-dropdown-value="线路N"；剧集容器 id="glist-{sid}"
            froms = []
            groups = []
            line_names = re.findall(r'<div class="module-tab-item[^"]*"[^>]*data-dropdown-value="([^"]+)"', html)
            glists = re.findall(r'<div[^>]*id="glist-(\d+)"[^>]*>(.*?)(?=<div[^>]*id="glist-\d+"|<div class="module-footer|</main>)', html, re.S)
            for idx, (sid, box) in enumerate(glists):
                eps = re.findall(r'<a href="(/play/[^"]+)"[^>]*>\s*<span>([^<]*)</span>', box, re.S)
                if not eps:
                    eps = re.findall(r'<a href="(/play/[^"]+)"[^>]*>(.*?)</a>', box, re.S)
                if not eps:
                    continue
                line_name = line_names[idx] if idx < len(line_names) else "线路%d" % (idx + 1)
                eps_list = []
                for href, ep_name in eps:
                    ep = re.sub(r"<[^>]+>", "", ep_name).strip()
                    if not ep:
                        continue
                    eps_list.append("%s$%s" % (ep, href))
                if eps_list:
                    froms.append(line_name)
                    groups.append("#".join(eps_list))

            if not froms:
                return self._skeleton(raw, name, pic, remark)

            vod = {
                "vod_id": raw, "vod_name": name or "视频", "vod_pic": pic,
                "vod_remarks": remark, "vod_actor": actor, "vod_director": director,
                "vod_content": content,
                "vod_play_from": "$$$".join(froms),
                "vod_play_url": "$$$".join(groups),
            }
            return {"list": [vod]}
        except Exception as e:
            self.log({"detail": "exception", "ids": raw, "error": type(e).__name__})
            return self._skeleton(raw, old_name, old_pic, old_remark)

    def _parse_extend(self, extend):
        if not extend:
            return {}
        if isinstance(extend, dict):
            return {k: v for k, v in extend.items() if v}
        if isinstance(extend, str):
            try:
                d = json.loads(extend)
                if isinstance(d, dict):
                    return {k: v for k, v in d.items() if v}
            except Exception:
                pass
            result = {}
            for part in extend.split(","):
                if "=" in part:
                    k, v = part.split("=", 1)
                    if v.strip():
                        result[k.strip()] = v.strip()
            return result
        return {}

    def categoryContent(self, tid, pg, filter, extend):
        page = str(pg or "1")
        ext = self._parse_extend(extend)
        area = ext.get("area", "")
        year = ext.get("year", "")
        lang = ext.get("lang", "")
        letter = ext.get("letter", "")
        if not area and not lang and not letter and not year:
            url = "%s/vodshow/%s--------%s---.html" % (self.host, tid, page)
        elif year and not area and not lang and not letter:
            url = "%s/vodshow/%s-----------%s.html" % (self.host, tid, year)
        elif lang and not area and not letter and not year:
            url = "%s/vodshow/%s----%s-------.html" % (self.host, tid, quote(lang, safe=""))
        elif area and not lang and not letter and not year:
            url = "%s/vodshow/%s-%s---------.html" % (self.host, tid, quote(area, safe=""))
        elif letter and not area and not lang and not year:
            url = "%s/vodshow/%s-----%s------.html" % (self.host, tid, letter)
        else:
            url = "%s/vodshow/%s--------%s---.html" % (self.host, tid, page)
        html = self._fetch_html(url)
        lst = self._parse_list(html)
        pagecount = self._get_pagecount(html, page) if html else int(page)
        return {"list": lst, "page": int(page), "pagecount": pagecount, "limit": 20, "total": pagecount * 20}

    def searchContent(self, key, quick, pg="1"):
        page = str(pg or "1")
        kw = quote(key, safe="")
        url = "%s/vodsearch/%s-------------.html" % (self.host, kw)
        if page != "1":
            url = "%s/vodsearch/%s-------------%s.html" % (self.host, kw, page)
        html = self._fetch_html(url)
        if html and ("没有找到" in html or "暂无数据" in html or "找不到" in html):
            return {"list": [], "page": int(page)}
        lst = self._parse_search(html)
        if not lst:
            lst = self._parse_list(html)
        return {"list": lst, "page": int(page)}

    def recommendContent(self, ids, pg="1"):
        try:
            raw = self._norm_ids(ids)
            if not raw:
                return {"list": []}
            vod_id = raw.split("|$|")[0]
            html = self._fetch_html(self.host + "/vod/" + vod_id + ".html")
            if not html:
                return {"list": []}
            m = re.search(r'相关影片.*?</div>\s*</div>\s*</div>', html, re.S)
            seg = m.group(0) if m else html
            return {"list": self._parse_list(seg)}
        except Exception:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        play_url = str(id) if id else ""
        if "$" in play_url:
            parts = play_url.split("$", 1)
            if len(parts) == 2:
                play_url = parts[1]
        if play_url.startswith(("http://", "https://")) and re.search(r"\.(m3u8|mp4|flv|m4s)(\?|$)", play_url, re.I):
            return {"parse": 0, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}}
        if play_url and not play_url.startswith("http"):
            play_url = urljoin(self.host + "/", play_url)
        if not play_url:
            return {"parse": 1, "url": self.host + "/", "header": self.headers}

        html = self._fetch_html(play_url)
        if html:
            idx = html.find("player_aaaa")
            if idx != -1:
                brace = html.find("{", idx)
                if brace != -1:
                    depth = 0
                    end = brace
                    for i in range(brace, len(html)):
                        c = html[i]
                        if c == "{":
                            depth += 1
                        elif c == "}":
                            depth -= 1
                            if depth == 0:
                                end = i + 1
                                break
                    try:
                        data = json.loads(html[brace:end])
                        u = data.get("url", "")
                        if u:
                            return {"parse": 0, "url": u, "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}}
                    except Exception:
                        pass
            um = re.search(r'(https?://[^\s"\'<>\\]+\.(?:m3u8|mp4))', html)
            if um:
                return {"parse": 0, "url": um.group(1), "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}}

        return {"parse": 1, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"}}

    def localProxy(self, param):
        return [404, "text/plain; charset=utf-8", "not implemented"]

    def destroy(self):
        try:
            self.session = None
        except Exception:
            pass