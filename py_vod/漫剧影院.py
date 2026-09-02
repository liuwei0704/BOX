# coding: utf-8
# 站点：漫剧影院
# 域名：https://hg.115567.xyz
# 类型：API 驱动影视站
# 接口：/api/categories, /api/home, /api/drama, /api/search, /api/stream
# 特点：无加密，无广告 m3u8，分页 page+pageSize=30
# 最后验证：2026-09-02

import json
import re
from urllib.parse import quote, urljoin, unquote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://hg.115567.xyz"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "1", "type_name": "成人漫剧"},
            {"type_id": "2", "type_name": "AI短剧"},
            {"type_id": "18", "type_name": "擦边短剧"}
        ]
        self.filters = {
            "1": [],
            "2": [],
            "18": []
        }

    def getName(self):
        return "漫剧影院"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def _parse_extend(self, extend):
        """统一解析 extend 参数，支持 dict / 字符串键值对格式"""
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

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐列表"""
        try:
            res = self.fetch(f"{self.host}/api/home?page=1&pageSize=30", headers=self.headers)
            data = res.json() if res else {}
            items = data.get("latest", [])
            return {"list": self._parse_list(items)}
        except Exception as e:
            self.log({"action": "homeVideoContent", "error": str(e)})
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        """分类列表（分页）"""
        page = pg or "1"
        try:
            # 解析 extend 筛选
            ext = self._parse_extend(extend)
            # 构造请求
            url = f"{self.host}/api/filter?category_id={tid}&page={page}&pageSize=30"
            res = self.fetch(url, headers=self.headers)
            data = res.json() if res else {}
            items = data.get("list", [])
            has_more = data.get("hasMore", False)
            # pagecount 暂时用 hasMore 推断（API 未返回总页数）
            pagecount = int(page) + 1 if has_more else int(page)
            return {
                "list": self._parse_list(items),
                "page": int(page),
                "pagecount": pagecount,
                "limit": 30,
                "total": data.get("total", 0)
            }
        except Exception as e:
            self.log({"action": "categoryContent", "tid": tid, "pg": pg, "error": str(e)})
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 30, "total": 0}

    def detailContent(self, ids):
        """详情页"""
        if not ids:
            return {"list": []}
        vid = str(ids[0])
        try:
            res = self.fetch(f"{self.host}/api/drama?id={vid}", headers=self.headers)
            data = res.json() if res else {}
            vod = {
                "vod_id": str(data.get("id", vid)),
                "vod_name": data.get("title", ""),
                "vod_pic": self._fix_cover(data.get("cover", "")),
                "vod_remarks": data.get("remarks", ""),
                "vod_actor": "",
                "vod_director": "",
                "vod_content": data.get("description", "") or "",
                "vod_year": data.get("year", ""),
                "vod_lang": data.get("lang", "")
            }
            # 构造播放线路
            episodes = data.get("episodes", [])
            if episodes:
                # 单线路：按集数排序
                eps_sorted = sorted(episodes, key=lambda x: x.get("ep", 0))
                play_urls = []
                for ep in eps_sorted:
                    ep_id = ep.get("id")
                    ep_num = ep.get("ep", 0)
                    if ep_id:
                        play_urls.append(f"第{ep_num:02d}集${ep_id}")
                if play_urls:
                    vod["vod_play_from"] = "播放"
                    vod["vod_play_url"] = "#".join(play_urls)
                else:
                    vod["vod_play_from"] = ""
                    vod["vod_play_url"] = ""
            else:
                vod["vod_play_from"] = ""
                vod["vod_play_url"] = ""
            return {"list": [vod]}
        except Exception as e:
            self.log({"action": "detailContent", "ids": ids, "error": str(e)})
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        """搜索"""
        if not key:
            return {"list": [], "page": 1}
        try:
            url = f"{self.host}/api/search?q={quote(key)}&page={pg}&pageSize=30"
            res = self.fetch(url, headers=self.headers)
            data = res.json() if res else {}
            items = data.get("list", [])
            return {
                "list": self._parse_list(items),
                "page": int(pg)
            }
        except Exception as e:
            self.log({"action": "searchContent", "key": key, "error": str(e)})
            return {"list": [], "page": 1}

    def playerContent(self, flag, id, vipFlags):
        """播放"""
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        try:
            # id 是剧集 epId
            # 解析 dramaId 和 epId（id 格式可能为 dramaId_epId 或纯 epId）
            # 从 flag 中提取或从 id 推断
            parts = str(id).split("_")
            if len(parts) == 2:
                drama_id, ep_id = parts[0], parts[1]
            else:
                # 纯 epId，需要从详情获取 dramaId
                ep_id = str(id)
                # 尝试从缓存或延后获取，这里直接用 ep_id 请求 stream
                # 但 stream 需要 drama 参数，尝试从 id 中提取
                drama_id = ""
                # 如果 flag 包含 dramaId
                if flag and flag.isdigit():
                    drama_id = flag
                else:
                    # 无法确定 dramaId，尝试用 0 或空
                    drama_id = "0"
            # 请求播放流
            stream_url = f"{self.host}/api/stream?drama={drama_id}&ep=0&epId={ep_id}"
            # 如果 drama_id 是 0，尝试直接用 ep_id 作为 drama_id
            if drama_id == "0":
                stream_url = f"{self.host}/api/stream?drama={ep_id}&ep=0&epId={ep_id}"
            res = self.fetch(stream_url, headers=self.headers)
            data = res.json() if res else {}
            stream = data.get("stream", "")
            if not stream:
                return {"parse": 0, "url": "", "header": {}}
            # 处理流地址
            if stream.startswith("/"):
                stream = f"{self.host}{stream}"
            # 如果是 m3u8，走代理清洗（但该站无广告，仅做绝对地址补全）
            if ".m3u8" in stream.lower():
                return {
                    "parse": 0,
                    "url": self._m3u8_proxy_url(stream),
                    "header": {"User-Agent": self.headers["User-Agent"]}
                }
            return {
                "parse": 0,
                "url": stream,
                "header": {"User-Agent": self.headers["User-Agent"]}
            }
        except Exception as e:
            self.log({"action": "playerContent", "id": id, "error": str(e)})
            return {"parse": 0, "url": "", "header": {}}

    def recommendContent(self, ids, pg):
        """相关推荐"""
        if not ids:
            return {"list": []}
        vid = str(ids[0])
        try:
            res = self.fetch(f"{self.host}/api/drama?id={vid}", headers=self.headers)
            data = res.json() if res else {}
            related = data.get("related", [])
            return {"list": self._parse_list(related)}
        except Exception as e:
            self.log({"action": "recommendContent", "ids": ids, "error": str(e)})
            return {"list": []}

    def destroy(self):
        """清理资源"""
        pass

    def _parse_list(self, items):
        """统一解析列表项"""
        result = []
        for item in items:
            if not item:
                continue
            vid = item.get("id")
            title = item.get("title")
            if not vid or not title:
                continue
            cover = self._fix_cover(item.get("cover", ""))
            remark = item.get("badge", "") or item.get("remarks", "") or f"{item.get('episode_count', 0)}集"
            result.append({
                "vod_id": str(vid),
                "vod_name": title,
                "vod_pic": cover,
                "vod_remarks": remark
            })
        return result

    def _fix_cover(self, url):
        """修复封面图地址"""
        if not url:
            return ""
        if url.startswith("/"):
            return f"{self.host}{url}"
        if not url.startswith("http"):
            return f"{self.host}/{url}"
        return url

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        """生成 m3u8 代理地址"""
        if not url:
            return ""
        if not url.startswith("http"):
            url = urljoin(self.host, url)
        return f"{self.getProxyUrl()}?do=py&url={quote(url, safe='')}"

    def localProxy(self, param):
        """m3u8 本地代理（本站无广告，仅做绝对地址补全）"""
        try:
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")
            if target.startswith("url="):
                target = target[4:]
            elif "url=" in target and "?" in target:
                qs = target.split("?", 1)[1]
                for part in qs.split("&"):
                    if part.startswith("url="):
                        target = unquote(part[4:])
                        break
            target = unquote(str(target or ""))
            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            resp = self.fetch(target, headers=self.headers, timeout=20)
            if not resp:
                return [502, "text/plain", b"fetch failed"]
            content = getattr(resp, "content", b"") or b""
            if not content and getattr(resp, "text", ""):
                content = resp.text.encode("utf-8", errors="ignore")
            if not content:
                return [502, "text/plain", b"empty content"]

            if b"#EXTM3U" in content[:256]:
                cleaned = self._clean_m3u8(content.decode("utf-8", errors="ignore"), target)
                return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

            return [200, "application/octet-stream", content]
        except Exception as e:
            return [500, "text/plain", f"localProxy error: {e}".encode("utf-8", errors="ignore")]

    def _clean_m3u8(self, text, source_url):
        """清洗 m3u8：仅做绝对地址补全（本站无广告）"""
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 检查是否为多码率
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urljoin(source_url, line)
                    if ".m3u8" in child.lower():
                        out.append(self._m3u8_proxy_url(child))
                    else:
                        out.append(child)
            return "\n".join(out) + "\n"

        # 单码率：补全所有相对路径
        out = []
        for line in lines:
            if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
                def repl(m):
                    uri = m.group(1)
                    if uri.startswith(("http://", "https://")):
                        return f'URI="{uri}"'
                    return f'URI="{urljoin(source_url, uri)}"'
                out.append(re.sub(r'URI="([^"]+)"', repl, line))
            elif line and not line.startswith("#"):
                if line.startswith(("http://", "https://")):
                    out.append(line)
                else:
                    out.append(urljoin(source_url, line))
            else:
                out.append(line)

        return "\n".join(out) + "\n"