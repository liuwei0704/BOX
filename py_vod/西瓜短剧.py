# -*- coding: utf-8 -*-
# 站点: 西瓜短剧 (m.xgshort.com)
# 架构: SPA + JSON API
# 反爬: Cloudflare —— 用 curl_cffi 模拟 TLS 指纹过盾, requests 兜底
# 关键接口:
#   /api/home/categories                分类
#   /api/home/gethomemodules?channeid=1 首页模块
#   /api/list/getfiltersdata            分类列表+翻页
#   /api/list/fuzzysearch               搜索
#   /api/video/episodes                 详情+多集数
#   /api/video/url/query                取播放直链
import time
import json
import requests

try:
    from curl_cffi import requests as _creq
    _HAS_CFFI = True
except Exception:
    _HAS_CFFI = False


class Spider:
    def __init__(self):
        self.baseurl = "https://m.xgshort.com"
        if _HAS_CFFI:
            self.session = _creq.Session(impersonate="chrome120")
        else:
            self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": self.baseurl + "/movie",
            "Origin": self.baseurl,
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
        })
        self.token = None
        self.token_expire = 0
        self.categories = []
        self.CLASSICAL_MAP = {
            "成人": "风月", "色情": "春宫", "淫": "风月", "黄色": "春宫", "淫秽": "猥亵",
            "激情": "云雨", "做爱": "云雨", "性交": "交欢", "欲": "情思", "高潮": "云端",
            "偷拍": "窥帘", "偷窥": "窥帘", "乱伦": "禁脔", "强奸": "强占", "无码": "素纱",
            "有码": "遮面", "熟女": "徐娘", "萝莉": "豆蔻", "幼女": "玉蕊", "少女": "碧玉",
            "学生": "书生", "人妻": "罗敷", "护士": "药女", "教师": "先生", "丝袜": "丝履",
            "巨乳": "丰盈", "臀": "玉臀", "脚": "莲步", "赌博": "孤注", "毒品": "药石",
            "广告": "告示", "暴力": "杀伐", "恐怖": "幽冥", "裸体": "玉体", "自慰": "弄玉",
            "口交": "含朱", "肛交": "后庭", "群交": "合卺", "车震": "车行", "野战": "郊合",
        }
        self.MINOR_KEYWORDS = ["萝莉", "幼女", "少女", "学生", "童", "未成年", "teen", "loli", "schoolgirl", "豆蔻", "玉蕊", "碧玉", "书生", "稚子"]

    def desensitize(self, text):
        if not text:
            return text
        if isinstance(text, (int, float)):
            return text
        result = str(text)
        for k, v in self.CLASSICAL_MAP.items():
            result = result.replace(k, v)
        return result

    def is_minor(self, text):
        if not text:
            return False
        t = str(text).lower()
        for kw in self.MINOR_KEYWORDS:
            if kw.lower() in t:
                return True
        return False

    def getDependence(self):
        return ""

    def init(self, extend):
        try:
            cfg = extend
            if isinstance(extend, str):
                cfg = json.loads(extend)
            if isinstance(cfg, dict) and cfg.get("baseurl"):
                self.baseurl = cfg["baseurl"]
        except:
            pass
        self._ensure_token()

    # ---------- 鉴权 ----------
    def _ensure_token(self):
        now = time.time()
        if self.token and now < self.token_expire:
            return True
        return self._guest_login()

    def _guest_login(self):
        for _ in range(5):
            try:
                # 先访问 movie 页建立 CF 会话 + 拿 guest cookie
                try:
                    self.session.get(self.baseurl + "/movie", timeout=12)
                except:
                    pass
                time.sleep(0.3)
                r = self.session.post(
                    self.baseurl + "/api/auth/guest-login",
                    json={"guestToken": ""},
                    timeout=12,
                )
                if r.status_code in (200, 201):
                    data = r.json()
                    token = data.get("access_token", "") or (data.get("data") or {}).get("access_token", "")
                    if token:
                        self.token = token
                        exp = data.get("expires_in") or (data.get("data") or {}).get("expires_in") or 604800
                        self.token_expire = time.time() + int(exp) - 300
                        self.session.headers["Authorization"] = "Bearer " + token
                        return True
            except:
                pass
            time.sleep(1)
        return False

    # ---------- 基础请求 ----------
    def _get(self, path, params=None, need_token=False):
        if need_token:
            self._ensure_token()
        for _ in range(3):
            try:
                r = self.session.get(self.baseurl + path, params=params, timeout=15)
                if r.status_code == 200:
                    return r.json()
                if r.status_code in (401, 403) and need_token:
                    self.token = None
                    self._ensure_token()
                    continue
            except:
                time.sleep(0.5)
        return None

    def _post(self, path, data, need_token=False):
        if need_token:
            self._ensure_token()
        for _ in range(3):
            try:
                r = self.session.post(self.baseurl + path, json=data, timeout=15)
                if r.status_code in (200, 201):
                    return r.json()
                if r.status_code in (401, 403) and need_token:
                    self.token = None
                    self._ensure_token()
                    continue
            except:
                time.sleep(0.5)
        return None

    def _load_categories(self):
        if self.categories:
            return self.categories
        data = self._get("/api/home/categories")
        if isinstance(data, list):
            self.categories = data
        elif isinstance(data, dict):
            self.categories = data.get("data", []) or []
        return self.categories

    # ---------- 列表项解析 ----------
    def _parse_vod(self, item):
        title = item.get("title", item.get("seriesTitle", ""))
        if self.is_minor(title):
            return None
        vod_id = item.get("shortId", item.get("seriesShortId", ""))
        if not vod_id:
            return None
        remarks = item.get("upStatus", item.get("updateStatus", "")) or ""
        score = item.get("score", item.get("seriesScore", ""))
        if score:
            remarks = str(score) + "分 " + remarks
        return {
            "vod_id": str(vod_id),
            "vod_name": self.desensitize(title),
            "vod_pic": item.get("coverUrl", item.get("seriesCoverUrl", "")),
            "vod_remarks": self.desensitize(remarks),
            "vod_content": self.desensitize(item.get("description", "")),
            "vod_actor": self.desensitize(item.get("author", item.get("actor", ""))),
            "vod_year": "",
            "vod_area": "",
            "vod_director": "",
        }

    # ---------- 首页 ----------
    def homeContent(self, filter=True):
        cats = self._load_categories()
        class_list = []
        filters = {}
        for c in cats:
            if not c.get("isEnabled", True):
                continue
            cid = str(c.get("id", ""))
            cname = self.desensitize(c.get("name", ""))
            if not cid or self.is_minor(cname):
                continue
            class_list.append({"type_id": cid, "type_name": cname})
            filters[cid] = []
        video_list = []
        data = self._get("/api/home/gethomemodules", params={"channeid": 1})
        modules = []
        if isinstance(data, dict):
            modules = (data.get("data") or {}).get("list", []) or []
        for mod in modules:
            mtype = mod.get("type")
            if mtype == 3:
                for item in mod.get("list", []) or []:
                    vod = self._parse_vod(item)
                    if vod:
                        video_list.append(vod)
            elif mtype == 0:
                for b in mod.get("banners", []) or []:
                    if b.get("isAd"):
                        continue
                    item = dict(b)
                    item.setdefault("shortId", b.get("shortId", ""))
                    vod = self._parse_vod(item)
                    if vod:
                        video_list.append(vod)
        return {"class": class_list, "filters": filters, "list": video_list}

    def homeVideoContent(self):
        return {"list": self.homeContent().get("list", [])}

    # ---------- 分类(真实翻页) ----------
    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg) if pg else 1
        except:
            page = 1
        if page < 1:
            page = 1
        ids = "0,0,0,0,0,0,0"
        if isinstance(extend, dict):
            vals = []
            for i in range(7):
                vals.append(str(extend.get("f%d" % i, extend.get(str(i), "0")) or "0"))
            ids = ",".join(vals)
        data = self._get("/api/list/getfiltersdata", params={
            "channeid": str(tid),
            "ids": ids,
            "page": page,
            "size": 20,
        })
        video_list = []
        total = 0
        has_more = False
        if isinstance(data, dict):
            d = data.get("data") or {}
            total = d.get("total", 0) or 0
            has_more = bool(d.get("hasMore"))
            for item in d.get("list", []) or []:
                vod = self._parse_vod(item)
                if vod:
                    video_list.append(vod)
        if has_more:
            pagecount = page + 1
        elif video_list:
            pagecount = page
        else:
            pagecount = 0
        return {
            "page": page,
            "pagecount": pagecount,
            "limit": 20,
            "total": total,
            "list": video_list,
        }

    # ---------- 详情(多线路+多集数) ----------
    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        if isinstance(ids, str):
            ids = [ids]
        result_list = []
        for vod_id in ids:
            vid = str(vod_id)
            data = self._get("/api/video/episodes", params={"seriesShortId": vid, "size": 500}, need_token=True)
            if not (isinstance(data, dict) and data.get("data")):
                continue
            d = data["data"]
            si = d.get("seriesInfo") or {}
            eps = d.get("list") or []
            vod_name = si.get("title", "")
            if self.is_minor(vod_name):
                continue
            from collections import OrderedDict
            lines = OrderedDict()
            for ep in eps:
                ep_num = ep.get("episodeNumber", 0)
                ep_title = ep.get("episodeTitle") or ep.get("title") or ("第%s集" % ep_num)
                if self.is_minor(ep_title):
                    continue
                ek = ep.get("episodeAccessKey", "")
                if not ek:
                    continue
                urls = ep.get("urls") or []
                quality = urls[0].get("quality", "") if urls else ""
                line_name = ("%s线路" % quality) if quality else "默认线路"
                lines.setdefault(line_name, []).append((ep_num, ep_title, ek))
            if not lines:
                continue
            play_from_list = []
            play_url_list = []
            for line_name, items in lines.items():
                try:
                    items.sort(key=lambda x: int(x[0]))
                except:
                    pass
                segs = ["%s$%s" % (self.desensitize(t), k) for _, t, k in items]
                play_from_list.append(line_name)
                play_url_list.append("#".join(segs))
            vod = {
                "vod_id": vid,
                "vod_name": self.desensitize(vod_name),
                "vod_pic": si.get("coverUrl", ""),
                "vod_remarks": self.desensitize(si.get("updateStatus", "")),
                "vod_content": self.desensitize(si.get("description", "")),
                "vod_actor": self.desensitize(si.get("starring", si.get("actor", ""))),
                "vod_director": self.desensitize(si.get("director", "")),
                "vod_year": "",
                "vod_area": self.desensitize(si.get("channeName", "")),
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list),
            }
            result_list.append(vod)
        return {"list": result_list}

    # ---------- 搜索 ----------
    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg) if pg else 1
        except:
            page = 1
        video_list = []
        data = self._get("/api/list/fuzzysearch", params={"keyword": key, "page": page, "size": 20})
        total = 0
        has_more = False
        if isinstance(data, dict):
            d = data.get("data") or {}
            total = d.get("total", 0) or 0
            has_more = bool(d.get("hasMore"))
            for item in d.get("list", []) or []:
                vod = self._parse_vod(item)
                if vod:
                    video_list.append(vod)
        if has_more:
            pagecount = page + 1
        elif video_list:
            pagecount = page
        else:
            pagecount = 0
        return {
            "page": page,
            "pagecount": pagecount,
            "limit": 20,
            "total": total,
            "list": video_list,
        }

    # ---------- 播放 ----------
    def playerContent(self, flag, id, vipFlags):
        ep_key = str(id)
        play_url = ""
        data = self._post(
            "/api/video/url/query",
            {"type": "episode", "accessKey": ep_key},
            need_token=True,
        )
        if isinstance(data, dict):
            urls = (data.get("data") or {}).get("urls") or []
            if isinstance(urls, list) and urls:
                u = urls[0]
                play_url = u.get("cdnUrl") or u.get("ossUrl") or ""
        fmt = "application/x-mpegURL" if ".m3u8" in play_url else "video/mp4"
        return {
            "parse": 0,
            "jx": 0,
            "url": play_url,
            "header": {
                "User-Agent": self.session.headers["User-Agent"],
                "Referer": self.baseurl + "/",
            },
            "format": fmt,
        }

    def localProxy(self, param):
        return [404, "text/plain", ""]

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def action(self, action):
        pass

    def destroy(self):
        self.session.close()