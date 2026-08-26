# coding: utf-8
import json
import re
import urllib.parse
from urllib.parse import urljoin, urlparse, quote
import posixpath
import re
import urllib.parse
from urllib.parse import urljoin, urlparse, quote
import posixpath

from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://se.xiaosejie61.xyz"
        self.classes = [
            {"type_id": "guochan", "type_name": "国产"},
            {"type_id": "riben", "type_name": "日本"},
            {"type_id": "haiwai", "type_name": "海外"},
            {"type_id": "tese", "type_name": "特色"},
            {"type_id": "tongxing", "type_name": "同性"}
        ]
        self.filters = {
            "guochan": [],
            "riben": [],
            "haiwai": [],
            "tese": [],
            "tongxing": []
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36",
            "Referer": self.host + "/"
        }

    def getName(self):
        return "小涩界"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """从首页提取推荐内容"""
        url = f"{self.host}/"
        res = self.fetch(url, headers=self.headers, timeout=10)
        if not res or res.status_code != 200:
            return {"list": []}
        html = res.text
        items = []
        # 提取所有 vod-item 块
        blocks = re.findall(r'<dl class="vod-item">(.*?)</dl>', html, re.DOTALL)
        for block in blocks:
            # 提取链接 (vod_id)
            link_match = re.search(r'<a href="([^"]+)"', block)
            if not link_match:
                continue
            vod_id = link_match.group(1).strip()
            if vod_id.startswith("/"):
                vod_id = vod_id
            
            # 提取封面图 - 优先 src，其次 data-src
            pic = ""
            pic_match = re.search(r'<img[^>]*src="([^"]+)"', block)
            if pic_match:
                pic = pic_match.group(1)
            if not pic:
                pic_match = re.search(r'<img[^>]*data-src="([^"]+)"', block)
                if pic_match:
                    pic = pic_match.group(1)
            
            # 提取标题
            title_match = re.search(r'<h3>([^<]+)</h3>', block)
            if not title_match:
                continue
            name = title_match.group(1).strip()
            
            # 去重
            if any(item["vod_id"] == vod_id for item in items):
                continue
            
            items.append({
                "vod_id": vod_id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": ""
            })
            if len(items) >= 50:
                break
        return {"list": items}
    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/vodtype/{tid}-{page}/"
        res = self.fetch(url, headers=self.headers, timeout=10)
        if not res or res.status_code != 200:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
        html = res.text
        items = []
        # 使用块提取方式，确保 vod_id 和 vod_name 正确匹配
        blocks = re.findall(r'<dl class="vod-item">(.*?)</dl>', html, re.DOTALL)
        for block in blocks:
            # 提取链接 (vod_id)
            link_match = re.search(r'<a href="([^"]+)"', block)
            if not link_match:
                continue
            vod_id = link_match.group(1).strip()
            if vod_id.startswith("/"):
                vod_id = vod_id
            
            # 提取封面图 - 优先 src，其次 data-src
            pic = ""
            pic_match = re.search(r'<img[^>]*src="([^"]+)"', block)
            if pic_match:
                pic = pic_match.group(1)
            if not pic:
                pic_match = re.search(r'<img[^>]*data-src="([^"]+)"', block)
                if pic_match:
                    pic = pic_match.group(1)
            
            # 提取标题
            title_match = re.search(r'<h3>([^<]+)</h3>', block)
            if not title_match:
                continue
            name = title_match.group(1).strip()
            
            # 去重
            if any(item["vod_id"] == vod_id for item in items):
                continue
            
            items.append({
                "vod_id": vod_id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": ""
            })
        
        # 提取总条数
        total = 0
        total_match = re.search(r'<em class="mac_total">(\d+)</em>', html)
        if total_match:
            total = int(total_match.group(1))
        
        # 提取分页信息
        pagecount = 1
        pagination_pattern = rf'<a[^>]*href="[^"]*?/vodtype/{tid}-(\d+)/"[^>]*>'
        page_matches = re.findall(pagination_pattern, html)
        if page_matches:
            page_numbers = [int(p) for p in page_matches if p.isdigit()]
            if page_numbers:
                pagecount = max(page_numbers)
        
        last_match = re.search(r'尾页[^<]*</a>', html)
        if last_match:
            last_url_match = re.search(rf'href="[^"]*?/vodtype/{tid}-(\d+)/"', last_match.group(0))
            if last_url_match:
                pagecount = int(last_url_match.group(1))
        
        if pagecount <= 1 and total > 20:
            pagecount = (total + 19) // 20
        
        return {
            "list": items,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 20,
            "total": total
        }

    def detailContent(self, ids):
        import html
        if not ids or not ids[0]:
            return {"list": []}
        vod_id = ids[0]
        if vod_id.startswith("/"):
            url = f"{self.host}{vod_id}"
        else:
            url = vod_id
        
        self.log({"detail": "fetching", "vod_id": vod_id, "url": url})
        
        res = self.fetch(url, headers=self.headers, timeout=10)
        if not res or res.status_code != 200:
            return {"list": []}
        html_text = res.text
        
        # 提取标题
        title_match = re.search(r'<h1>.*?\[[^\]]+\]\s*([^<]+)</h1>', html_text, re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        if not title:
            title_match = re.search(r'<h1>([^<]+)</h1>', html_text)
            title = title_match.group(1).strip() if title_match else ""
        
        # 提取封面图
        pic = ""
        pic_match = re.search(r'window\.PC_PLAYER_POSTER\s*=\s*"([^"]+)"', html_text)
        if pic_match:
            pic = pic_match.group(1)
        if not pic:
            pic_match = re.search(r'<img class="vod-cover".*?src="([^"]+)"', html_text)
            pic = pic_match.group(1) if pic_match else ""
        
        # 提取简介 - 解码HTML实体
        desc_match = re.search(r'<div class="play-desc-body"[^>]*>([^<]+(?:<[^>]+>[^<]*</[^>]+>)*[^<]*)</div>', html_text, re.DOTALL)
        desc = desc_match.group(1).strip() if desc_match else ""
        desc = re.sub(r'<[^>]+>', '', desc)
        desc = html.unescape(desc).strip()
        
        # 提取播放地址 - 精确匹配当前视频的 player_aaaa
        play_url = ""
        from_name = "播放"
        
        # 方法1: 从 player_aaaa 对象提取
        player_match = re.search(r'var\s+player_aaaa\s*=\s*(\{[^;]+\});', html_text, re.DOTALL)
        if player_match:
            try:
                import json
                player_data = json.loads(player_match.group(1))
                play_url = player_data.get("url", "").replace("\\/", "/")
                from_name = player_data.get("from", "播放")
                self.log({"detail": "player_aaaa", "play_url": play_url, "from": from_name})
            except Exception as e:
                self.log({"detail": "player_aaaa_parse_error", "error": str(e)})
        
        # 方法2: 如果 player_aaaa 没有 url，搜索页面中的 m3u8
        if not play_url:
            # 搜索 "url":"http...m3u8" 但排除广告
            url_pattern = r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"'
            url_matches = re.findall(url_pattern, html_text)
            for match in url_matches:
                candidate = match.replace("\\/", "/")
                if candidate.startswith("http") and "index.m3u8" in candidate:
                    play_url = candidate
                    self.log({"detail": "url_match", "play_url": play_url})
                    break
        
        # 方法3: 搜索任何 m3u8 链接
        if not play_url:
            m3u8_match = re.search(r'https?://[^"\']+\.m3u8[^"\']*', html_text)
            if m3u8_match:
                play_url = m3u8_match.group(0)
                self.log({"detail": "m3u8_match", "play_url": play_url})
        
        vod = {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": "",
            "vod_content": desc,
            "vod_play_from": from_name,
            "vod_play_url": f"播放${play_url}" if play_url else ""
        }
        
        self.log({"detail": "result", "vod_id": vod_id, "title": title[:20], "play_url": play_url[:80] if play_url else "None"})
        return {"list": [vod]}
    # 调试日志 - 记录提取结果
        self.log({"detail": "extracted", "vod_id": vod_id, "play_url": play_url[:100] if play_url else "None", "title": title[:30]})

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        url = f"{self.host}/vodsearch/-------------/?wd={key}"
        res = self.fetch(url, headers=self.headers, timeout=10)
        if not res or res.status_code != 200:
            return {"list": [], "page": 1}
        html = res.text
        items = []
        pattern = r'<dl class="vod-item">.*?<a href="([^"]+)".*?<img class="vod-cover".*?src="([^"]+)".*?alt="([^"]+)".*?<h3>([^<]+)</h3>'
        matches = re.findall(pattern, html, re.DOTALL)
        for link, pic, alt, name in matches:
            vod_id = link.strip()
            if vod_id.startswith("/"):
                vod_id = vod_id
            items.append({
                "vod_id": vod_id,
                "vod_name": name.strip(),
                "vod_pic": pic.strip(),
                "vod_remarks": ""
            })
        return {"list": items, "page": int(pg)}

    def playerContent(self, flag, id, vipFlags):
        # 如果已经是直链（m3u8/mp4），走代理过滤广告
        if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
            if ".m3u8" in id:
                return {"parse": 0, "url": self._m3u8_proxy_url(id), "header": {"User-Agent": self.headers["User-Agent"]}}
            return {"parse": 0, "url": id, "header": {"User-Agent": self.headers["User-Agent"]}}
        # 如果是播放页ID，尝试提取播放地址
        if id.startswith("/"):
            url = f"{self.host}{id}"
        else:
            url = id
        res = self.fetch(url, headers=self.headers, timeout=10)
        if not res or res.status_code != 200:
            return {"parse": 1, "url": url, "header": self.headers}
        html = res.text
        play_match = re.search(r'"url":"([^"]+)"', html)
        if play_match:
            play_url = play_match.group(1).replace("\\/", "/")
            if play_url.startswith("http"):
                if ".m3u8" in play_url:
                    return {"parse": 0, "url": self._m3u8_proxy_url(play_url), "header": {"User-Agent": self.headers["User-Agent"]}}
                return {"parse": 0, "url": play_url, "header": {"User-Agent": self.headers["User-Agent"]}}
        # 如果无法提取直链，降级为嗅探
        return {"parse": 1, "url": url, "header": self.headers}

    def _m3u8_proxy_url(self, url):
        """生成m3u8代理地址"""
        if url:
            url = url.replace("\\/", "/")
        return self.getProxyUrl() + "?do=py&url=" + quote(str(url or ""), safe="")

    def getProxyUrl(self):
        """获取本地代理地址"""
        return "http://127.0.0.1:9978/proxy"

    def _m3u8_proxy_url(self, url):
        """生成m3u8代理地址"""
        return self.getProxyUrl() + "&url=" + quote(str(url or ""), safe="")

    def getProxyUrl(self):
        """获取本地代理地址"""
        return "http://127.0.0.1:9978/proxy?do=py"

    def recommendContent(self, ids, pg):
        # 从详情页提取"猜你喜欢"
        vod_id = ids[0]
        if vod_id.startswith("/"):
            url = f"{self.host}{vod_id}"
        else:
            url = vod_id
        res = self.fetch(url, headers=self.headers, timeout=10)
        if not res or res.status_code != 200:
            return {"list": []}
        html = res.text
        items = []
        pattern = r'<dl class="vod-item">.*?<a href="([^"]+)".*?<img class="vod-cover".*?src="([^"]+)".*?alt="([^"]+)".*?<h3>([^<]+)</h3>'
        matches = re.findall(pattern, html, re.DOTALL)
        for link, pic, alt, name in matches:
            vod_id_item = link.strip()
            if vod_id_item.startswith("/"):
                vod_id_item = vod_id_item
            items.append({
                "vod_id": vod_id_item,
                "vod_name": name.strip(),
                "vod_pic": pic.strip(),
                "vod_remarks": ""
            })
        return {"list": items}

    def localProxy(self, param):
        """m3u8 广告分片过滤 - v3.0 优化版"""
        try:
            # 调试日志
            self.log({"localProxy": "called", "param_type": str(type(param)), "param": str(param)[:200]})
            
            # 兼容多种参数格式
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "") or param.get("do", "")
            elif isinstance(param, str):
                target = param
            else:
                target = str(param or "")

            # 如果 target 是完整的代理 URL，提取其中的 url 参数
            if target.startswith("http://127.0.0.1:9978/proxy"):
                parsed = urlparse(target)
                query = urllib.parse.parse_qs(parsed.query)
                target = query.get("url", [""])[0] or query.get("source", [""])[0] or target

            # 剥离前缀 url= 并解码
            if target.startswith("url="):
                target = target[4:]
            target = urllib.parse.unquote(str(target or ""))

            self.log({"localProxy": "target", "target": target[:200]})

            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]

            # 发起 HTTP 请求获取 m3u8 内容
            resp = self.fetch(target, headers=self.headers, timeout=15)
            if not resp:
                return [502, "text/plain", b"fetch failed"]

            content = getattr(resp, "content", b"") or b""
            if not content and hasattr(resp, "text") and resp.text:
                content = resp.text.encode("utf-8", errors="ignore")

            if not content:
                return [502, "text/plain", b"empty content"]

            text = content.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in text:
                return [502, "text/plain", b"invalid m3u8"]

            cleaned = self._clean_m3u8(text, target)
            self.log({"localProxy": "cleaned_length", "length": len(cleaned), "ad_filtered": "yes"})
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

        except Exception as e:
            error_msg = f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")
            self.log({"localProxy": "error", "error": str(e)})
            return [500, "text/plain", error_msg]

    def _clean_m3u8(self, text, source_url):
        """清洗m3u8 - 广告分片过滤 v3.0（修复版 - 强制使用 source_dir）"""
        lines = [line.strip() for line in str(text or "").replace("\r", "").split("\n") if line.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 处理多码率 Master Playlist
        if any(line.startswith("#EXT-X-STREAM-INF") for line in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urljoin(source_url, line)
                    out.append(self._m3u8_proxy_url(child) if ".m3u8" in child.lower() else child)
            return "\n".join(out) + "\n"

        parsed = urlparse(source_url)
        source_dir = posixpath.dirname(parsed.path)
        if not source_dir.endswith("/"):
            source_dir += "/"

        # 强制使用 source_dir 作为正片目录
        main_dir = source_dir

        # 如果 source_dir 包含日期，优先使用它
        # 不依赖 #EXT-X-KEY，直接使用 source_url 的目录
        self.log({"m3u8": "debug", "source_dir": source_dir, "main_dir": main_dir, "total_lines": len(lines)})

        segments = []
        pending = []
        ad_count = 0
        total_segments = 0

        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media_url = urljoin(source_url, line)
                media_parsed = urlparse(media_url)
                total_segments += 1

                # 判断分片是否属于 source_dir
                is_ad = not media_parsed.path.startswith(main_dir)

                if not is_ad:
                    segments.extend(pending)
                    segments.append(media_url)
                else:
                    ad_count += 1
                pending = []
                continue

            if not line.startswith("#"):
                segments.append(urljoin(source_url, line))
            else:
                segments.append(line)

        # 二次清洗
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in ("#EXT-X-KEY:METHOD=NONE", "#EXT-X-DISCONTINUITY"):
                if not out or out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
                    continue
            out.append(line)

        while len(out) > 1 and out[-1] in ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE"):
            out.pop()

        self.log({"m3u8": "filtered", "ad_count": ad_count, "total_segments": total_segments, "kept_segments": len(segments)})
        return "\n".join(out) + "\n"
    def _rewrite_m3u8_tag(self, line, source_url):
        """重写m3u8标签中的URI（补全绝对地址）"""
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(match):
                uri = match.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)

        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urljoin(source_url, line)

        return line
    def destroy(self):
        pass