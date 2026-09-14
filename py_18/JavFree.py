# -*- coding: utf-8 -*-
"""
四壳通用Python Spider - JavFree
站点类型: WordPress系JAV视频站 (theme x01)
核心特征: 分类页/censored/分页?p=N, 详情页/video-{slug}/, 播放源为k2s.cc下载链接
"""

import re
import json
import urllib.parse

try:
    from base.spider import Spider as BaseSpider
except Exception:
    class BaseSpider(object):
        def init(self, extend=""):
            pass
        def homeContent(self, filter):
            return {}
        def categoryContent(self, tid, pg, filter, extend):
            return {}
        def detailContent(self, ids):
            return {}
        def searchContent(self, key, quick, pg):
            return {}
        def playerContent(self, flag, id, vipFlags):
            return {}
        def getDependence(self):
            return ""
        def localProxy(self, param):
            return [404, "text/plain", ""]
        def destroy(self):
            pass
        def isVideoFormat(self, url):
            return False
        def getName(self):
            return ""
        def getApp(self):
            return ""
        def isManualVideo(self):
            return False

try:
    import requests
except Exception:
    requests = None


# 未成年关键词（铁律13：命中即跳过不返回）
JUVENILE_KEYWORDS = [
    "萝莉", "幼女", "童", "未成年", "teen", "loli", "schoolgirl",
    "小学生", "初中生", "高中生", "学生妹", "幼", "小女", "女童", "儿童",
    "young", "petite", "teenie", "underage", "minor",
    "school girl", "teenage", "teenager", "juvenile",
]


def _is_juvenile(text):
    """检测文本是否含未成年相关词，命中返回True（需跳过）"""
    if not text:
        return False
    t = text.lower()
    for kw in JUVENILE_KEYWORDS:
        if kw.lower() in t:
            return True
    return False


class Spider(BaseSpider):
    """四壳通用Spider - JavFree"""

    # 站点配置
    baseUrl = "https://javfree.com"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    # 分类列表（网站原始英文分类名，不脱敏）
    classList = [
        {"type_id": "censored", "type_name": "Censored"},
        {"type_id": "uncensored", "type_name": "Uncensored"},
        {"type_id": "genre/amateur", "type_name": "Amateur"},
        {"type_id": "genre/china-subtitle", "type_name": "China Subtitle"},
        {"type_id": "genre/english-subtile", "type_name": "English Subtitle"},
    ]

    filters = {}

    def __init__(self):
        self.rawSite = self.baseUrl
        self.siteUrl = self.baseUrl
        self.HOST = self.baseUrl
        self.extend = ""
        self.session = None

    # ==================== 工具方法 ====================

    def _get_session(self):
        if self.session is None:
            if requests:
                self.session = requests.Session()
                self.session.headers.update(self.header)
        return self.session

    def _http_get(self, url, timeout=15):
        """HTTP GET请求"""
        try:
            sess = self._get_session()
            if sess:
                r = sess.get(url, timeout=timeout, allow_redirects=True)
                return r.text
            else:
                import urllib.request
                req = urllib.request.Request(url, headers=self.header)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[JavFree] GET error: {e}")
            return ""

    def _parse_list_page(self, html):
        """
        解析列表页（分类页/搜索页/首页），提取视频卡片
        卡片结构: <a rel="bookmark" class="img" title="标题" href="URL"><img data-src="封面">
        返回: list of {vod_id, vod_name, vod_pic, vod_remarks}
        """
        results = []
        # 匹配视频卡片
        pattern = re.compile(
            r'<a[^>]*rel="bookmark"[^>]*title="([^"]*)"[^>]*href="(https://javfree\.com/video-[^"]+)"[\s\S]*?data-src="([^"]+\.(?:jpg|jpeg|png|webp))"',
            re.DOTALL
        )
        for m in pattern.finditer(html):
            vod_name = m.group(1).strip()
            vod_url = m.group(2).strip()
            vod_pic = m.group(3).strip()
            # 从URL提取vod_id（slug）
            vod_id = vod_url.rstrip("/").split("/")[-1]
            # 铁律13：未成年相关条目跳过
            if _is_juvenile(vod_name):
                continue
            results.append({
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_remarks": "",
            })
        return results

    def _parse_total_pages(self, html):
        """解析总页数 - 本站分页格式 ?p=N"""
        pages = re.findall(r'\?p=(\d+)', html)
        if pages:
            return max(int(p) for p in pages)
        return 1

    def _parse_detail_page(self, html, vod_id):
        """
        解析详情页，提取标题、封面、播放地址（k2s.cc下载链接）
        """
        result = {
            "vod_id": vod_id,
            "vod_name": "",
            "vod_pic": "",
            "vod_content": "",
            "vod_actor": "",
            "vod_director": "",
            "vod_year": "",
            "vod_area": "",
            "vod_remarks": "",
            "vod_score": "",
            "play_url": "",
            "play_from": "k2s",
        }

        # 1. 提取标题 <title>Watch XXX - JavFree.com</title>
        title_m = re.search(r"<title>Watch\s+([^<]+?)\s*[-–—]\s*JavFree", html, re.I)
        if title_m:
            result["vod_name"] = title_m.group(1).strip()
        else:
            title_m2 = re.search(r"<title>([^<]+)</title>", html)
            if title_m2:
                t = title_m2.group(1).strip()
                t = re.sub(r"^Watch\s+", "", t, flags=re.I)
                t = re.sub(r"\s*[-–—]\s*JavFree\.com\s*$", "", t, flags=re.I)
                result["vod_name"] = t

        # 2. 提取播放地址 - k2s.cc下载链接
        k2s_m = re.search(r'href="(https://k2s\.cc/file/[^"]+)"', html)
        if k2s_m:
            result["play_url"] = k2s_m.group(1).strip()
        else:
            # 兜底：找任何外部视频/下载链接
            ext_m = re.search(r'href="(https?://(?:k2s|katfile|filemoon|dood|streamtape)[^"]+)"', html, re.I)
            if ext_m:
                result["play_url"] = ext_m.group(1).strip()

        # 3. 提取封面
        pic_m = re.search(r'(?:data-src|src)="(https://img\.javfree\.com/[^"]+\.(?:jpg|jpeg|png|webp))"', html)
        if pic_m:
            result["vod_pic"] = pic_m.group(1).strip()
        else:
            og_image = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
            if og_image:
                result["vod_pic"] = og_image.group(1).strip()

        # 4. 提取详情信息
        # 番号（从标题或页面提取）
        code_m = re.search(r'([A-Z]{2,6}-\d{2,4})', result["vod_name"])
        if code_m:
            result["vod_remarks"] = code_m.group(1)

        # 女优/演员
        actor_m = re.findall(r'href="https://javfree\.com/star/[^"]*"[^>]*>([^<]+)<', html)
        if actor_m:
            result["vod_actor"] = ", ".join(set(a.strip() for a in actor_m if a.strip()))

        # 分类/标签
        genre_m = re.findall(r'href="https://javfree\.com/(?:genre|tag)/[^"]*"[^>]*>([^<]+)<', html)
        if genre_m:
            genres = ", ".join(set(g.strip() for g in genre_m if g.strip()))
            if not result["vod_remarks"]:
                result["vod_remarks"] = genres

        # 简介/描述
        desc_m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        if desc_m:
            result["vod_content"] = desc_m.group(1).strip()

        return result

    # ==================== 13标准接口 ====================

    def init(self, extend=""):
        """初始化"""
        self.extend = extend if extend else ""
        if self.extend:
            try:
                ext = json.loads(self.extend) if isinstance(self.extend, str) else self.extend
                if ext.get("siteUrl"):
                    self.siteUrl = ext["siteUrl"]
                    self.HOST = self.siteUrl
                if ext.get("proxy"):
                    self.siteUrl = ext["proxy"]
                    self.HOST = self.siteUrl
                if ext.get("direct") is True:
                    self.siteUrl = self.baseUrl
                    self.HOST = self.baseUrl
            except Exception:
                pass

    def homeContent(self, filter=None):
        """首页：返回分类列表+filters"""
        return {
            "class": self.classList,
            "filters": self.filters,
        }

    def categoryContent(self, tid, pg, filter=None, extend=None):
        """
        分类内容
        tid: 分类标识（如 censored, uncensored, genre/amateur）
        pg: 页码，分页格式 ?p=N
        """
        pg = int(pg) if pg else 1
        # 构建分类URL
        if tid.startswith("genre/"):
            cat_path = f"/{tid}/"
        else:
            cat_path = f"/{tid}/"

        if pg == 1:
            url = f"{self.baseUrl}{cat_path}"
        else:
            url = f"{self.baseUrl}{cat_path}?p={pg}"

        html = self._http_get(url)
        if not html:
            return {"page": pg, "pagecount": 1, "limit": 40, "total": 0, "list": []}

        vod_list = self._parse_list_page(html)
        pagecount = self._parse_total_pages(html)
        total = pagecount * 40

        return {
            "page": pg,
            "pagecount": pagecount,
            "limit": 40,
            "total": total,
            "list": vod_list,
        }

    def detailContent(self, ids):
        """
        详情内容
        ids: list/tuple of vod_id（slug，如 video-skmj-444-xxx）
        """
        if isinstance(ids, str):
            ids = [ids]

        vod_list = []
        for vod_id in ids:
            if not vod_id:
                continue
            # 构建详情页URL
            if vod_id.startswith("http"):
                url = vod_id
            elif vod_id.startswith("video-"):
                url = f"{self.baseUrl}/{vod_id}/"
            else:
                url = f"{self.baseUrl}/video-{vod_id}/"

            html = self._http_get(url)
            if not html:
                continue

            info = self._parse_detail_page(html, vod_id)

            # 铁律13：未成年相关条目跳过
            if _is_juvenile(info.get("vod_name", "")) or _is_juvenile(info.get("vod_content", "")):
                continue

            vod_item = {
                "vod_id": str(vod_id),
                "vod_name": info.get("vod_name", ""),
                "vod_pic": info.get("vod_pic", ""),
                "vod_content": info.get("vod_content", ""),
                "vod_actor": info.get("vod_actor", ""),
                "vod_director": info.get("vod_director", ""),
                "vod_year": info.get("vod_year", ""),
                "vod_area": info.get("vod_area", ""),
                "vod_remarks": info.get("vod_remarks", ""),
                "vod_score": info.get("vod_score", ""),
                "vod_play_from": info.get("play_from", "k2s"),
                "vod_play_url": info.get("play_url", ""),
            }
            vod_list.append(vod_item)

        return {"list": vod_list}

    def searchContent(self, key, quick=None, pg=None):
        """
        搜索内容
        搜索URL: /search/?q=关键词
        """
        pg = int(pg) if pg else 1
        params = {"q": key}
        if pg > 1:
            params["p"] = pg
        url = f"{self.baseUrl}/search/?{urllib.parse.urlencode(params)}"

        html = self._http_get(url)
        if not html:
            return {"page": pg, "pagecount": 1, "limit": 40, "total": 0, "list": []}

        vod_list = self._parse_list_page(html)
        pagecount = self._parse_total_pages(html)
        total = pagecount * 40

        return {
            "page": pg,
            "pagecount": pagecount,
            "limit": 40,
            "total": total,
            "list": vod_list,
        }

    def playerContent(self, flag, id, vipFlags=None):
        """播放内容 - k2s.cc下载链接直接透传"""
        header = {
            "User-Agent": self.header["User-Agent"],
            "Referer": self.baseUrl + "/",
            "Origin": self.baseUrl,
        }
        return {
            "parse": 0,
            "jx": 0,
            "url": id,
            "header": header,
        }

    def getDependence(self):
        return ""

    def localProxy(self, param):
        """本地代理（基础实现）"""
        try:
            if not param or not isinstance(param, dict):
                return [404, "text/plain", ""]
            url = param.get("url", "")
            if not url:
                return [404, "text/plain", ""]
            # 本站为k2s.cc下载链接，非m3u8流，直接透传
            return [200, "text/plain", url]
        except Exception as e:
            print(f"[JavFree] localProxy error: {e}")
            return [500, "text/plain", str(e)]

    def destroy(self):
        if self.session:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None

    def isVideoFormat(self, url):
        if not url:
            return False
        return any(ext in url.lower() for ext in [".m3u8", ".mp4", ".mkv", ".avi", ".flv", ".ts", "k2s.cc", "katfile"])

    def getName(self):
        return "JavFree"

    def getApp(self):
        return "JavFree"

    def isManualVideo(self):
        return False


if __name__ == "__main__":
    sp = Spider()
    sp.init()
    print("=== homeContent ===")
    home = sp.homeContent()
    print(f"分类数: {len(home.get('class', []))}")
    for c in home["class"]:
        print(f"  {c['type_id']}: {c['type_name']}")

    print("\n=== categoryContent (censored, pg=1) ===")
    cat = sp.categoryContent("censored", "1")
    print(f"page={cat['page']}, pagecount={cat['pagecount']}, 列表={len(cat['list'])}")
    if cat["list"]:
        print(f"首个: {cat['list'][0]['vod_name'][:50]}")
        print(f"封面: {cat['list'][0]['vod_pic'][:60]}")

    print("\n=== detailContent ===")
    if cat["list"]:
        first_id = cat["list"][0]["vod_id"]
        detail = sp.detailContent([first_id])
        print(f"详情数: {len(detail['list'])}")
        if detail["list"]:
            d = detail["list"][0]
            print(f"标题: {d['vod_name'][:50]}")
            print(f"播放: {d['vod_play_url'][:80]}")
            print(f"女优: {d['vod_actor'][:50]}")

    print("\n=== searchContent ===")
    search = sp.searchContent("skmj")
    print(f"列表={len(search['list'])}")

    sp.destroy()
    print("\n=== 测试完成 ===")
