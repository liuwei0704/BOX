# coding: utf-8
# ============================================================
# 站点：Gitube 剧兔 (gitube.tv)
# 主域名：https://gitube.tv
# 发布页：无（MacCMS 站，固定域名）
# 内容类型：影视（电视剧/短剧/电影/动漫/综艺/陆剧/韩剧/美剧/日剧/台剧/港剧/海外剧/纪录片）
# 特殊说明：
#   - MacCMS 站，详情页 /title/{id}.html，播放页 /watch/{vid}-{lineId}-{epId}.html
#   - 分类列表 /browse/{tid}.html，分页 /browse/{tid}-{pg}.html（实测 883 页）
#   - 播放页内联 player_aaaa，encrypt=0，url 字段为真实播放地址
#     * m3u8 型线路（如意雲/優質雲/無盡雲等）url 直接是 m3u8 直链
#     * 外链型线路（騰訊/愛奇藝等）url 是第三方站播放页，需嗅探
#   - 搜索路径 /search/... 被 Cloudflare Managed Challenge 拦截（403），
#     搜索降级为 parse:1 嗅探 + 骨架兜底
# 最后验证时间：2026-09-18
# 来源：用户提供 URL
# ============================================================
import json
import re
from urllib.parse import quote, urljoin, unquote, urlparse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        # __init__ 只做本地初始化，禁止网络请求，保证首页秒出 class。
        self.extend = ""
        self.host = "https://gitube.tv"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Referer": self.host + "/",
        }
        # 静态分类（法则16/17：分类零网络依赖、硬编码）
        self.classes = [
            {"type_id": "2", "type_name": "電視劇"},
            {"type_id": "36", "type_name": "短劇"},
            {"type_id": "1", "type_name": "電影"},
            {"type_id": "35", "type_name": "動漫"},
            {"type_id": "29", "type_name": "綜藝"},
            {"type_id": "13", "type_name": "陸劇"},
            {"type_id": "20", "type_name": "韓劇"},
            {"type_id": "16", "type_name": "美劇"},
            {"type_id": "15", "type_name": "日劇"},
            {"type_id": "14", "type_name": "台劇"},
            {"type_id": "21", "type_name": "港劇"},
            {"type_id": "31", "type_name": "海外劇"},
            {"type_id": "22", "type_name": "紀錄片"},
        ]
        # 筛选：本站在详情页/分类页无真实筛选 DOM，统一留空数组（不伪造筛选）
        self.filters = {c["type_id"]: [] for c in self.classes}

    # ---------------- 基础方法 ----------------
    def getName(self):
        return "剧兔"

    def getDependence(self):
        return []

    def init(self, extend=""):
        # init 零网络；动态域名探测放到 getHost()（本站固定域名，直接返回）
        self.extend = extend or ""

    def destroy(self):
        self.extend = ""

    def _host(self):
        return self.host

    # ---------------- 通用工具 ----------------
    @staticmethod
    def _norm_ids(ids):
        """法则35：ids 可能是 list / str / int / bytes，禁止直接 ids[0]"""
        if ids is None:
            return ""
        if isinstance(ids, (list, tuple)):
            if not ids:
                return ""
            ids = ids[0]
        if isinstance(ids, bytes):
            ids = ids.decode("utf-8", errors="ignore")
        return str(ids).strip()

    def _fetch_text(self, url):
        """带判空与降级的 fetch（法则 runtime 8.2）"""
        try:
            r = self.fetch(url, headers=self.headers, timeout=15)
        except Exception as e:
            self.log({"fetch": "exception", "url": url, "error": type(e).__name__})
            return ""
        if not r or r.status_code != 200:
            self.log({"fetch": "failed", "url": url,
                      "status": r.status_code if r else None})
            return ""
        text = getattr(r, "text", "") or ""
        # CF 挑战页判定（法则：加 len < 800 约束，避免误判正常播放页）
        if len(text) < 800 and "window.location.href" in text:
            return ""
        return text

    @staticmethod
    def _clean(s):
        if not s:
            return ""
        s = re.sub(r"<[^>]+>", "", str(s))
        s = (s.replace("&nbsp;", " ").replace("&amp;", "&")
             .replace("&quot;", '"').replace("&#39;", "'")
             .replace("&lt;", "<").replace("&gt;", ">"))
        return s.strip()

    # ---------------- 列表解析（多级兜底，法则14） ----------------
    CARD_CANDIDATES = [".card", "article.card", "[class*=\"card\"]"]

    def _parse_list(self, html):
        """解析卡片列表。分类页/首页/推荐共用。
        分类页结构: <article class="card card--cN"> ... </article>
        详情页推荐区结构: 无 article 包裹, 直接 <a href="/title/{id}.html" class="card__body">
        """
        items = []
        if not html:
            return items
        seen = set()

        def _emit(block):
            m_link = re.search(r'href="(/title/(\d+)\.html)"', block)
            if not m_link:
                return
            vod_id = m_link.group(2)
            if vod_id in seen:
                return
            name = ""
            m_name = re.search(r'class="[^"]*card__title[^"]*"[^>]*>(.*?)</h3>', block, re.S)
            if m_name:
                name = self._clean(m_name.group(1))
            if not name:
                m_alt = re.search(r'alt="([^"]+)"', block)
                if m_alt:
                    name = self._clean(m_alt.group(1))
            pic = ""
            m_pic = re.search(r'<img[^>]+src="([^"]+)"', block)
            if m_pic:
                pic = urljoin(self._host() + "/", m_pic.group(1))
            remark = ""
            m_rem = re.search(r'class="[^"]*card__badge[^"]*"[^>]*>(.*?)</span>', block, re.S)
            if m_rem:
                remark = self._clean(m_rem.group(1))
            seen.add(vod_id)
            items.append({
                "vod_id": vod_id,
                "vod_name": name or "未知标题",
                "vod_pic": pic,
                "vod_remarks": remark,
            })

        # 主路径：按 <article ... card ...> 切分
        starts = [m.start() for m in re.finditer(r'<article[^>]*class="[^"]*\bcard\b[^"]*"', html)]
        if not starts:
            starts = [m.start() for m in re.finditer(r'<div[^>]*class="[^"]*\bcard\b[^"]*"', html)]
        if starts:
            starts.append(len(html))
            for i in range(len(starts) - 1):
                _emit(html[starts[i]:starts[i + 1]])
        # 兜底：详情页推荐区无 article 包裹，直接按 <a ... card__body> 切分
        if not items:
            starts2 = [m.start() for m in re.finditer(r'<a[^>]*class="[^"]*card__body[^"]*"', html)]
            starts2.append(len(html))
            for i in range(len(starts2) - 1):
                _emit(html[starts2[i]:starts2[i + 1]])
        return items
    def homeContent(self, filter):
        # 零网络。分类为硬编码（法则16/17）。
        # 本站两层结构：顶层13个分类；其中「電視劇(2)」为大类，其下用「類型」
        # 行切换子类(陸劇13/韓劇20/美劇16/日劇15/台劇14/港劇21/海外劇31/紀錄片22)，
        # 子类各自也是独立 tid，直接作为平级分类暴露即可。
        filters = {}
        if filter:
            # 筛选实测格式：/filter/{tid}-{地区}----------{年份}.html
            # 地区与年份两个维度；分页见 categoryContent（filter 路径每页约36条）。
            areas = [
                ("", "全部"), ("中國大陸", "中國大陸"), ("大陸", "大陸"),
                ("韓國", "韓國"), ("日本", "日本"), ("台灣", "台灣"),
                ("香港", "香港"), ("美國", "美國"), ("歐美", "歐美"),
                ("泰國", "泰國"), ("英國", "英國"), ("法國", "法國"),
                ("新加坡", "新加坡"), ("越南", "越南"), ("其他", "其他"),
            ]
            years = [("", "全部")] + [(str(y), str(y)) for y in range(2026, 2015, -1)]
            # 仅对「支持筛选」的影视类目挂筛选（纪录片等同样支持，统一挂上）
            for c in self.classes:
                tid = c["type_id"]
                filters[tid] = [
                    {"key": "area", "name": "地區",
                     "value": [{"n": n, "v": v} for v, n in areas]},
                    {"key": "year", "name": "年份",
                     "value": [{"n": n, "v": v} for v, n in years]},
                ]
        return {"class": self.classes, "filters": filters}
    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_text(self._host() + "/")
        return {"list": self._parse_list(html)}

    # ---------------- 分类（分页实测：/browse/{tid}-{pg}.html） ----------------
    def categoryContent(self, tid, pg, filter, extend):
        # 分页与筛选实测（权威链接取自页面 pager 区，逐字符核对）：
        #   第1页: /filter/{tid}-----------{year}.html   (tid后 11 个横杠)
        #   第N页: /filter/{tid}--------{pg}---{year}.html (tid后 8 个横杠)
        #   带地区: /filter/{tid}-{area}----------{year}.html
        #           /filter/{tid}-{area}----{pg}---{year}.html
        #   纯分类: /browse/{tid}.html 、/browse/{tid}-{pg}.html
        # 翻页关键：返回足够大的 pagecount，让壳子按需向后翻；
        #   实测各分类均有多个分页，翻到空页时本方法返回空 list，壳子自然停止。
        try:
            page = int(pg or 1)
        except (TypeError, ValueError):
            page = 1
        if page < 1:
            page = 1

        ext = extend or {}
        if not isinstance(ext, dict):
            ext = {}
        area = str(ext.get("area", "") or "")
        year = str(ext.get("year", "") or "")
        has_filter = bool(area or year)

        if has_filter:
            if area:
                if page == 1:
                    url = f"{self._host()}/filter/{tid}-{area}----------{year}.html"
                else:
                    url = f"{self._host()}/filter/{tid}-{area}----{page}---{year}.html"
            else:
                if page == 1:
                    url = f"{self._host()}/filter/{tid}-----------{year}.html"
                else:
                    url = f"{self._host()}/filter/{tid}--------{page}---{year}.html"
            html = self._fetch_text(url)
            items = self._parse_list(html)
            return {
                "list": items,
                "page": page,
                "pagecount": 999 if items else page,
                "limit": len(items) or 36,
                "total": len(items),
            }

        # 无筛选：走 /browse/ 并跨页去重（滤掉固定头部推荐区的重复项）
        if not hasattr(self, "_seen_ids") or not isinstance(self._seen_ids, dict):
            self._seen_ids = {}
        if page <= 1:
            self._seen_ids[tid] = set()
        seen = self._seen_ids.setdefault(tid, set())

        if page == 1:
            url = f"{self._host()}/browse/{tid}.html"
        else:
            url = f"{self._host()}/browse/{tid}-{page}.html"

        html = self._fetch_text(url)
        raw = self._parse_list(html)
        items = []
        for it in raw:
            vid = str(it.get("vod_id", ""))
            if vid and vid in seen:
                continue
            if vid:
                seen.add(vid)
            items.append(it)

        return {
            "list": items,
            "page": page,
            "pagecount": 999 if items else page,
            "limit": len(items) or 40,
            "total": len(items),
        }
    def _skeleton(self, vid, title="", pic="", remarks=""):
        pid = str(vid).replace("$", "|")
        return {"list": [{
            "vod_id": str(vid), "vod_name": title or "未知标题",
            "vod_pic": pic or "", "vod_remarks": remarks or "",
            "vod_content": "", "vod_play_from": "播放",
            "vod_play_url": "播放$" + pid,
        }]}

    def _probe_line(self, first_ep_url):
        """探测一条线路首个剧集能否解析出可播直链。返回 True=可播"""
        try:
            ph = self._fetch_text(first_ep_url)
            real = self._extract_player_url(ph)
            if not real:
                return False
            low = real.lower()
            if not (".m3u8" in low or ".mp4" in low or ".flv" in low):
                return False
            # m3u8 直链再验证分片可达（避免 502 的假可播）
            if ".m3u8" in low:
                return self._m3u8_reachable(real)
            return True
        except Exception:
            return False

    def _m3u8_reachable(self, m3u8_url):
        """抓 m3u8 并抽验一个分片是否可达（含多码率主表下钻一层）"""
        try:
            txt = ""
            r = self.fetch(m3u8_url, headers={"User-Agent": self.headers["User-Agent"]}, timeout=12)
            if r and r.status_code == 200:
                txt = r.text or ""
            if not txt or "#EXTM3U" not in txt:
                return False
            # 多码率主表: 找子流 m3u8 相对/绝对地址, 下钻一层
            sub = ""
            for line in txt.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    sub = urljoin(m3u8_url, line)
                    break
            if sub and ".m3u8" in sub.lower():
                r2 = self.fetch(sub, headers={"User-Agent": self.headers["User-Agent"]}, timeout=12)
                if r2 and r2.status_code == 200 and "#EXTM3U" in (r2.text or ""):
                    txt = r2.text
                    m3u8_url = sub
            # 抽一个分片
            for line in txt.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and (".ts" in line or ".m4s" in line or ".jpg" in line or ".png" in line):
                    seg = urljoin(m3u8_url, line)
                    try:
                        rr = self.fetch(seg, headers={"User-Agent": self.headers["User-Agent"]}, timeout=10)
                        return bool(rr and rr.status_code in (200, 206))
                    except Exception:
                        return False
            return True
        except Exception:
            return False
    def detailContent(self, ids):
        vod_id = self._norm_ids(ids)          # 唯一允许返回空 list 的分支
        if not vod_id:
            return {"list": []}
        vod_id = vod_id.split("|$|")[0]
        if not vod_id:
            return {"list": []}

        url = f"{self._host()}/title/{vod_id}.html"
        html = self._fetch_text(url)
        if not html or len(html) < 500:
            return self._skeleton(vod_id)

        name = ""
        m = (re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
             or re.search(r'<meta property="og:title" content="([^"]+)"', html))
        if m:
            name = self._clean(m.group(1))
        name = re.sub(r'線上看.*$', '', name).strip() or name

        pic = ""
        m = (re.search(r'<meta property="og:image" content="([^"]+)"', html)
             or re.search(r'class="detail-cover"[^>]*>.*?<img[^>]+src="([^"]+)"', html, re.S))
        if m:
            pic = urljoin(self._host() + "/", m.group(1))

        actor = director = content = remarks = ""
        m = re.search(r'<strong>演員:</strong>(.*?)</p>', html, re.S)
        if m:
            actor = self._clean(m.group(1))
        m = re.search(r'<strong>導演:</strong>(.*?)</p>', html, re.S)
        if m:
            director = self._clean(m.group(1))
        m = re.search(r'<strong>狀態:</strong>(.*?)</p>', html, re.S)
        if m:
            remarks = self._clean(m.group(1))
        m = re.search(r'id="desc".*?<div>(.*?)</div>', html, re.S)
        if m:
            content = self._clean(m.group(1))

        # 收集所有线路
        raw_lines = []   # [(line_name, [ep_url,...])]
        blocks = re.findall(
            r'<div class="playlist-block">.*?<h2 class="playlist-block__title">(.*?)</h2>'
            r'.*?<div class="playlist-grid">(.*?)</div>', html, re.S)
        for title_raw, grid in blocks:
            line_name = self._clean(title_raw) or "線路"
            eps = re.findall(r'<a href="(/watch/[^"]+\.html)">(.*?)</a>', grid, re.S)
            if not eps:
                continue
            ep_list = []
            for ep_href, ep_name in eps:
                ep_title = self._clean(ep_name) or "播放"
                ep_url = urljoin(self._host() + "/", ep_href)
                ep_list.append((ep_title, ep_url))
            if ep_list:
                raw_lines.append((line_name, ep_list))

        # 并发探测每条线路首个剧集, 只保留可播直链线路
        playable = []
        if raw_lines:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            first_urls = {i: ln[1][0][1] for i, ln in enumerate(raw_lines)}
            ok_idx = set()
            try:
                with ThreadPoolExecutor(max_workers=6) as ex:
                    futs = {ex.submit(self._probe_line, u): i for i, u in first_urls.items()}
                    for fu in as_completed(futs):
                        if fu.result():
                            ok_idx.add(futs[fu])
            except Exception:
                ok_idx = set(range(len(raw_lines)))   # 探测异常则不过滤
            for i, ln in enumerate(raw_lines):
                if i in ok_idx:
                    playable.append(ln)

        # 探测后一条可播都没有 → 回退到全部线路（避免误杀导致空）
        if not playable:
            playable = raw_lines

        play_from = []
        play_urls = []
        for line_name, ep_list in playable:
            ep_strs = [f"{t}${u}" for t, u in ep_list]
            if ep_strs:
                play_from.append(line_name)
                play_urls.append("#".join(ep_strs))

        if play_from and len(play_from) == len(play_urls) and any(play_urls):
            vod_play_from = "$$$".join(play_from)
            vod_play_url = "$$$".join(play_urls)
        else:
            vod_play_from = "播放"
            vod_play_url = "播放$" + f"{self._host()}/watch/{vod_id}-1-1.html"

        vod = {
            "vod_id": vod_id,
            "vod_name": name or "未知标题",
            "vod_pic": pic,
            "vod_remarks": remarks,
            "vod_actor": actor,
            "vod_director": director,
            "vod_content": content,
            "vod_play_from": vod_play_from,
            "vod_play_url": vod_play_url,
        }
        return {"list": [vod]}
    def searchContent(self, key, quick, pg="1"):
        # 搜索路径被 Cloudflare Managed Challenge 拦截，fetch 会拿到 403 挑战页。
        # 仍按标准路径请求，拿到内容则正常解析；拿不到返回空 list（不伪造）。
        if not key:
            return {"list": [], "page": int(pg or 1)}
        url = f"{self._host()}/search/-------------.html?wd={quote(key)}"
        html = self._fetch_text(url)
        return {"list": self._parse_list(html), "page": int(pg or 1)}

    # ---------------- 播放（解析 player_aaaa.url，m3u8 直链优先） ----------------
    def _resolve_m3u8(self, m3u8_url):
        """主表下钻: 返回可直接播的子流 m3u8 绝对地址; 非主表原样返回"""
        try:
            r = self.fetch(m3u8_url, headers={"User-Agent": self.headers["User-Agent"]}, timeout=12)
            if not r or r.status_code != 200:
                return m3u8_url
            txt = r.text or ""
            if "#EXTM3U" not in txt:
                return m3u8_url
            # 主表特征: 含 EXT-X-STREAM-INF
            if "#EXT-X-STREAM-INF" not in txt:
                return m3u8_url
            for line in txt.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    return urljoin(m3u8_url, line)
            return m3u8_url
        except Exception:
            return m3u8_url

    def playerContent(self, flag, id, vipFlags):
        play_url = str(id) if id else ""
        if "$" in play_url:
            parts = play_url.split("$", 1)
            if len(parts) == 2 and parts[1].strip():
                play_url = parts[1]
        if not play_url:
            return {"parse": 0, "url": "", "header": {}}
        if not play_url.startswith("http"):
            if play_url.startswith("//"):
                play_url = "https:" + play_url
            else:
                play_url = self._host() + "/" + play_url.lstrip("/")

        low = play_url.lower()
        # 直链 m3u8/mp4: 不带 Referer; m3u8 主表下钻出子流
        if low.endswith(".m3u8") or ".m3u8?" in low:
            real = self._resolve_m3u8(play_url)
            return {"parse": 0, "url": real,
                    "header": {"User-Agent": self.headers["User-Agent"]}}
        if low.endswith(".mp4") or ".mp4?" in low:
            return {"parse": 0, "url": play_url,
                    "header": {"User-Agent": self.headers["User-Agent"]}}

        if "/watch/" in play_url:
            html = self._fetch_text(play_url)
            real = self._extract_player_url(html)
            if real:
                rlow = real.lower()
                if ".m3u8" in rlow:
                    real = self._resolve_m3u8(real)
                    return {"parse": 0, "url": real,
                            "header": {"User-Agent": self.headers["User-Agent"]}}
                if ".mp4" in rlow or ".flv" in rlow:
                    return {"parse": 0, "url": real,
                            "header": {"User-Agent": self.headers["User-Agent"]}}
                return {"parse": 1, "url": real, "header": self.headers}
            return {"parse": 1, "url": play_url, "header": self.headers}

        return {"parse": 1, "url": play_url, "header": self.headers}
    def _extract_player_url(self, html):
        """从播放页提取 player_aaaa.url（平衡括号匹配，法则32）"""
        if not html:
            return ""
        idx = html.find("player_aaaa=")
        if idx < 0:
            idx = html.find("player_data=")
        if idx < 0:
            return ""
        start = html.find("{", idx)
        if start < 0:
            return ""
        depth = 0
        in_str = False
        esc = False
        end = -1
        for i in range(start, len(html)):
            ch = html[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end < 0:
            return ""
        raw = html[start:end]
        url = ""
        m = re.search(r'"url"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
        if m:
            url = m.group(1)
        if not url:
            return ""
        # 转义还原（法则32 L4）
        url = (url.replace("\\/", "/").replace("\\u002f", "/")
               .replace("&amp;", "&"))
        return url.strip()

    # ---------------- 推荐 ----------------
    def recommendContent(self, ids=None, pg=1):
        vod_id = self._norm_ids(ids)
        if not vod_id:
            return {"list": []}
        vod_id = vod_id.split("|$|")[0]
        url = f"{self._host()}/title/{vod_id}.html"
        html = self._fetch_text(url)
        if not html:
            return {"list": []}
        # 直接抽取详情页所有 /title/{id}.html 卡片链接（去重保序）
        items = []
        seen = set()
        for m in re.finditer(
            r'<a href="/title/(\d+)\.html"[^>]*class="[^"]*card__body[^"]*"[^>]*>'
            r'.*?<h3[^>]*class="[^"]*card__title[^"]*"[^>]*>(.*?)</h3>'
            r'.*?<p[^>]*class="[^"]*card__meta[^"]*"[^>]*>(.*?)</p>',
            html, re.S
        ):
            rid = m.group(1)
            if rid == vod_id or rid in seen:
                continue
            seen.add(rid)
            items.append({
                "vod_id": rid,
                "vod_name": self._clean(m.group(2)) or "未知标题",
                "vod_pic": "",
                "vod_remarks": self._clean(m.group(3)),
            })
        # 补封面：从 detail 页图片顺序不易对齐，单独抓 img 兜底留空
        return {"list": items}
