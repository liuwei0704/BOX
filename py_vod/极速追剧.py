# coding: utf-8
# ============================================================
# 站点：极速追剧  https://jisuzhuiju.com
# 类型：标准 HTML 影视站（服务端渲染 + /api/play-url 取流）
# 内容：电视剧 / 电影 / 动漫 / 综艺
# 分类结构：静态硬编码 /type/{name}.html 对应 channel 1-4
# 列表：分类页按板块渲染；分页/筛选统一走 /filter?channel=&type=&area=&year=&sort=&page=N
# 详情：/detail/{id}.html  线路 data-key（qq/zj/...）+ /vodplay/{id}-{from}-{index}.html
# 取流：GET /api/play-url?vodId=&playFrom=&index=  ->  {code:200,url:m3u8}
# m3u8：标准 .ts 分片，无广告目录、无图片流，取证结论=直链透传不代理
# 搜索：/search?wd={kw}
# 最后验证：2026-09-22
# ============================================================
import json
import re
from urllib.parse import quote, urljoin, urlparse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):

    def __init__(self):
        self.extend = ""
        self.host = "https://jisuzhuiju.com"
        self.classes = [
            {"type_id": "1", "type_name": "电视剧"},
            {"type_id": "2", "type_name": "电影"},
            {"type_id": "3", "type_name": "动漫"},
            {"type_id": "4", "type_name": "综艺"},
        ]
        self.filters = {
            "1": [
                {"key": "type", "name": "类型", "value": [
                    {"n": "全部", "v": ""}, {"n": "剧情", "v": "7"}, {"n": "古装", "v": "9"},
                    {"n": "战争", "v": "10"}, {"n": "谍战", "v": "11"}, {"n": "爱情", "v": "12"},
                    {"n": "悬疑", "v": "14"}, {"n": "喜剧", "v": "18"}, {"n": "武侠", "v": "20"},
                    {"n": "科幻", "v": "29"}, {"n": "犯罪", "v": "35"}, {"n": "动作", "v": "41"},
                ]},
                {"key": "area", "name": "地区", "value": [
                    {"n": "全部", "v": ""}, {"n": "大陆", "v": "大陆"}, {"n": "香港", "v": "香港"},
                    {"n": "台湾", "v": "台湾"}, {"n": "韩国", "v": "韩国"}, {"n": "日本", "v": "日本"},
                    {"n": "美国", "v": "美国"}, {"n": "英国", "v": "英国"},
                ]},
                {"key": "sort", "name": "排序", "value": [
                    {"n": "最新", "v": "new"}, {"n": "最热", "v": "hot"},
                ]},
            ],
            "2": [
                {"key": "sort", "name": "排序", "value": [
                    {"n": "最新", "v": "new"}, {"n": "最热", "v": "hot"},
                ]},
            ],
            "3": [
                {"key": "sort", "name": "排序", "value": [
                    {"n": "最新", "v": "new"}, {"n": "最热", "v": "hot"},
                ]},
            ],
            "4": [
                {"key": "sort", "name": "排序", "value": [
                    {"n": "最新", "v": "new"}, {"n": "最热", "v": "hot"},
                ]},
            ],
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
            "Referer": self.host + "/",
        }

    # ---------------- 基础 ----------------

    def getName(self):
        return "极速追剧"

    def getDependence(self):
        return []

    def init(self, extend=""):
        # 零网络
        self.extend = extend or ""

    def destroy(self):
        pass

    def _fetch(self, url, headers=None, timeout=15):
        try:
            h = dict(self.headers)
            if headers:
                h.update(headers)
            r = self.fetch(url, headers=h, timeout=timeout)
            if not r:
                self.log({"fetch": "none", "url": url[:80]})
                return ""
            code = getattr(r, "status_code", None)
            txt = getattr(r, "text", None)
            if txt is None:
                try:
                    txt = r.content.decode("utf-8", errors="ignore")
                except Exception:
                    txt = ""
            if code != 200 or not txt:
                # 二次尝试：补 Accept 头 / 换 verify
                try:
                    h2 = dict(h)
                    h2["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                    h2["Accept-Language"] = "zh-CN,zh;q=0.9"
                    r2 = self.fetch(url, headers=h2, timeout=timeout)
                    if r2:
                        t2 = getattr(r2, "text", None) or ""
                        if not t2:
                            try:
                                t2 = r2.content.decode("utf-8", errors="ignore")
                            except Exception:
                                t2 = ""
                        if t2:
                            return t2
                except Exception:
                    pass
            if code != 200:
                return ""
            return txt or ""
        except Exception as e:
            self.log({"action": "fetch_fail", "url": url[:80], "error": type(e).__name__})
            return ""

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

    @staticmethod
    def _parse_extend(extend):
        """法则20：兼容 dict / 'a=b' / '{a=b}' 三种格式"""
        out = {}
        if not extend:
            return out
        if isinstance(extend, dict):
            return {k: v for k, v in extend.items() if v not in (None, "")}
        s = str(extend).strip()
        if s.startswith("{"):
            s = s.strip("{}")
        for part in re.split(r"[&,]", s):
            if "=" in part:
                k, v = part.split("=", 1)
                k, v = k.strip(), v.strip()
                if v:
                    out[k] = v
        return out

    @staticmethod
    def _clean(s):
        if not s:
            return ""
        s = re.sub(r"<[^>]+>", "", str(s))
        s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
        return s.strip()

    # ---------------- 卡片解析（分类/搜索共用） ----------------

    def _parse_cards(self, html):
        """列表卡片：vod-card 容器，详情链接 /detail/{id}.html"""
        items = []
        seen = set()
        if not html:
            return items
        blocks = re.split(r'<div class="col-4 col-md-2">', html)
        for blk in blocks[1:]:
            m = re.search(r'href="(/detail/(\d+)\.html)"', blk)
            if not m:
                continue
            vid = m.group(2)
            if vid in seen:
                continue
            name = ""
            mn = re.search(r'<p class="vod-title[^"]*">(.*?)</p>', blk, re.S)
            if mn:
                name = self._clean(mn.group(1))
            if not name:
                mn = re.search(r'<img[^>]*alt="(.*?)"', blk, re.S)
                if mn:
                    name = self._clean(mn.group(1)).replace("封面图片", "")
            if not name:
                continue
            pic = ""
            mp = re.search(r'<img[^>]*src="([^"]+)"', blk, re.S)
            if mp:
                pic = mp.group(1)
            remark = ""
            mr = re.search(r'<p class="vod-subtitle[^"]*">(.*?)</p>', blk, re.S)
            if mr:
                remark = self._clean(mr.group(1))
            seen.add(vid)
            items.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": remark,
            })
        return items

    # ---------------- 首页 ----------------

    def homeContent(self, filter):
        # 零网络
        return {
            "class": self.classes,
            "filters": self.filters if filter else {},
        }

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch(self.host + "/")
        items = self._parse_cards(html)
        return {"list": items[:60]}

    # ---------------- 分类 ----------------

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg or 1)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        ex = self._parse_extend(extend)
        channel = str(tid or "1")

        url = (self.host + "/filter?channel=" + quote(channel)
               + "&type=" + quote(ex.get("type", ""))
               + "&area=" + quote(ex.get("area", ""))
               + "&year=" + quote(ex.get("year", ""))
               + "&sort=" + quote(ex.get("sort", "new"))
               + "&page=" + str(page))

        html = self._fetch(url)
        items = self._parse_cards(html)

        pagecount = 999
        mp = re.search(r'page=(\d+)"[^>]*>\s*(?:末页|尾页)', html)
        if not mp:
            mp = re.search(r'共\s*(\d+)\s*页', html)
        if mp:
            try:
                pagecount = int(mp.group(1))
            except Exception:
                pass
        if not mp:
            nums = re.findall(r'page=(\d+)', html)
            if nums:
                try:
                    pagecount = max(int(n) for n in nums)
                except Exception:
                    pass

        return {
            "list": items,
            "page": page,
            "pagecount": pagecount,
            "limit": 24,
            "total": pagecount * 24,
        }

    # ---------------- 详情 ----------------

    def detailContent(self, ids):
        raw = self._norm_ids(ids)
        if not raw:
            return {"list": []}
        vid = raw.split("|$|")[0].split("-")[0]
        url = self.host + "/detail/" + vid + ".html"
        html = self._fetch(url)

        name = pic = content = remark = ""
        if html:
            mn = re.search(r'<meta property="og:title" content="(.*?)"', html, re.S)
            if mn:
                name = self._clean(mn.group(1)).replace("《", "").replace("》", "")
                name = re.sub(r"(电视剧|电影|动漫|综艺)?高清.*$", "", name).strip()
            if not name:
                mn = re.search(r"<title>(.*?)</title>", html, re.S)
                if mn:
                    name = self._clean(mn.group(1)).split("-")[0].strip()
            mp = re.search(r'<meta property="og:image" content="(.*?)"', html, re.S)
            if mp:
                pic = mp.group(1)
            mc = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
            if mc:
                content = self._clean(mc.group(1))
            mr = re.search(r'<span class="vod-subtitle[^"]*">(.*?)</span>', html, re.S)
            if mr:
                remark = self._clean(mr.group(1))

        # 线路：data-key（qq/zj/...）+ 每线路剧集
        froms, urls = [], []
        if html:
            # 线路 key 直接取自剧集链接 /vodplay/{id}-{from}-{index}.html
            groups = {}
            order = []
            for em in re.finditer(
                r'href="/vodplay/' + re.escape(vid) + r'-([^"\-]+)-(\d+)\.html"[^>]*>(.*?)</a>',
                html, re.S):
                fkey = em.group(1)
                idx = em.group(2)
                ep_name = self._clean(em.group(3)) or ("第%s集" % idx)
                pid = "%s|%s|%s" % (vid, fkey, idx)
                if fkey not in groups:
                    groups[fkey] = []
                    order.append(fkey)
                groups[fkey].append(ep_name + "$" + pid)
            tab_names = re.findall(r'class="source-tab[^"]*"[^>]*>(.*?)</button>', html, re.S)
            tab_names = [self._clean(t) for t in tab_names]
            for i, fkey in enumerate(order):
                eps = groups.get(fkey) or []
                if not eps:
                    continue
                nm = tab_names[i] if i < len(tab_names) and tab_names[i] else fkey
                froms.append(nm)
                urls.append("#".join(eps))

        if not froms:
            # 骨架兜底（法则35）：禁止返回空 list
            return {"list": [{
                "vod_id": vid, "vod_name": name or "未知标题", "vod_pic": pic,
                "vod_remarks": remark, "vod_content": content,
                "vod_play_from": "播放", "vod_play_url": "播放$%s|qq|1" % vid,
            }]}

        return {"list": [{
            "vod_id": vid,
            "vod_name": name or "未知标题",
            "vod_pic": pic,
            "vod_remarks": remark,
            "vod_content": content,
            "vod_play_from": "$$$".join(froms),
            "vod_play_url": "$$$".join(urls),
        }]}

    # ---------------- 搜索 ----------------

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg or 1)
        except Exception:
            page = 1
        url = self.host + "/search?wd=" + quote(str(key or ""))
        if page > 1:
            url += "&page=" + str(page)
        html = self._fetch(url)
        return {"list": self._parse_cards(html), "page": page}

    # ---------------- 播放 ----------------

    def _try_play_api(self, vod_id, from_key, idx):
        api = (self.host + "/api/play-url?vodId=" + quote(str(vod_id))
               + "&playFrom=" + quote(str(from_key))
               + "&index=" + quote(str(idx)))
        txt = self._fetch(api, headers={"Referer": self.host + "/"})
        if not txt:
            return ""
        try:
            js = json.loads(txt)
            if int(js.get("code", 0)) == 200:
                return js.get("url", "") or ""
        except Exception:
            m = re.search(r'"url"\s*:\s*"([^"]+)"', txt)
            if m:
                return m.group(1).replace("\\/", "/")
        return ""

    def playerContent(self, flag, id, vipFlags):
        pid = str(id or "")
        parts = pid.split("|")
        if len(parts) >= 3:
            vod_id, from_key, idx = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            vod_id, from_key, idx = parts[0], parts[1], "1"
        else:
            vod_id, from_key, idx = pid, "qq", "1"

        real = self._try_play_api(vod_id, from_key, idx)

        # 多级兜底：给定 key 失败时，扫详情页所有真实线路 key 依次重试
        if not real:
            html = self._fetch(self.host + "/detail/" + str(vod_id) + ".html")
            if html:
                keys = []
                for km in re.finditer(
                    r'href="/vodplay/' + re.escape(str(vod_id)) + r'-([^"\-]+)-(\d+)\.html"',
                    html):
                    k = km.group(1)
                    if k not in keys:
                        keys.append(k)
                for k in keys:
                    real = self._try_play_api(vod_id, k, idx)
                    if real:
                        from_key = k
                        break
                    real = self._try_play_api(vod_id, k, "1")
                    if real:
                        from_key = k
                        idx = "1"
                        break

        if real and real.startswith("http"):
            # 取证结论：标准 .ts 分片、无广告、无图片流 -> 直链透传，不代理
            return {
                "parse": 0,
                "url": real,
                "header": {
                    "User-Agent": self.headers["User-Agent"],
                    "Referer": self.host + "/",
                },
            }

        # 兜底：回播放页嗅探
        play_url = self.host + "/vodplay/%s-%s-%s.html" % (vod_id, from_key, idx)
        return {
            "parse": 1,
            "url": play_url,
            "header": {
                "User-Agent": self.headers["User-Agent"],
                "Referer": self.host + "/",
            },
        }

    # ---------------- 推荐 ----------------

    def recommendContent(self, ids, pg=1):
        raw = self._norm_ids(ids)
        if not raw:
            return {"list": []}
        vid = raw.split("|$|")[0].split("-")[0]
        html = self._fetch(self.host + "/detail/" + vid + ".html")
        items = self._parse_cards(html)
        items = [it for it in items if it.get("vod_id") != vid]
        return {"list": items[:12]}