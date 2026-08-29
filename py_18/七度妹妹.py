# coding: utf-8
import re
import json
from urllib.parse import urljoin, quote, unquote, urlparse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://uga.qdmm8.motorcycles"
        self.base_path = "/cn/home/web"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + self.base_path + "/"
        }
        # 分类列表（从首页导航提取）
        self.classes = [
            {"type_id": "20", "type_name": "美女写真"},
            {"type_id": "21", "type_name": "国产精品"},
            {"type_id": "22", "type_name": "无码专区"},
            {"type_id": "23", "type_name": "中文字幕"},
            {"type_id": "24", "type_name": "强奸乱伦"},
            {"type_id": "25", "type_name": "人妻熟女"},
            {"type_id": "26", "type_name": "亚洲情色"},
            {"type_id": "27", "type_name": "制服丝袜"},
            {"type_id": "28", "type_name": "SM捆绑"},
            {"type_id": "29", "type_name": "自淫系列"},
            {"type_id": "30", "type_name": "三级伦理"}
        ]
        # 站点无筛选功能，返回空filters
        self.filters = {}
        self._session = None

    def getName(self):
        return "七度妹妹"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""
        if self._session is None:
            try:
                import requests
                self._session = requests.Session()
            except:
                self._session = None

    def destroy(self):
        if self._session:
            try:
                self._session.close()
            except:
                pass
            self._session = None

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐列表"""
        url = self.host + self.base_path + "/"
        res = self.fetch(url, headers=self.headers, timeout=10)
        if not res:
            return {"list": []}
        html = res.text if hasattr(res, "text") else str(res.content or "", "utf-8", errors="ignore")
        items = self._parse_list_items(html, "ul.fed-list-info li.fed-list-item")
        return {"list": items[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        # 分类列表URL
        url = f"{self.host}{self.base_path}/index.php/vod/type/id/{tid}/page/{page}.html"
        res = self.fetch(url, headers=self.headers, timeout=10)
        if not res:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
        html = res.text if hasattr(res, "text") else str(res.content or "", "utf-8", errors="ignore")
        items = self._parse_list_items(html, "ul.fed-list-info li.fed-list-item")
        # 提取分页信息
        pagecount = self._parse_pagecount(html)
        total = pagecount * 20
        return {
            "list": items,
            "page": int(page),
            "pagecount": pagecount,
            "limit": 20,
            "total": total
        }

    def _parse_list_items(self, html, selector):
        """解析列表项，使用正则提取"""
        items = []
        # 匹配 fed-list-item 块
        pattern = r'<li[^>]*class="[^"]*fed-list-item[^"]*"[^>]*>.*?<a[^>]*class="[^"]*fed-list-pics[^"]*"[^>]*href="([^"]+)"[^>]*data-original="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*fed-list-score[^"]*"[^>]*>([^<]*)</span>.*?</a>.*?<a[^>]*class="[^"]*fed-list-title[^"]*"[^>]*href="[^"]*"[^>]*>([^<]*)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            link, pic, score, title = match
            vod_id = self._extract_vod_id(link)
            if not vod_id:
                continue
            # 补全图片URL
            if pic and not pic.startswith("http"):
                pic = urljoin(self.host + self.base_path + "/", pic)
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": pic,
                "vod_remarks": score.strip() if score else ""
            })
        return items

    def _parse_pagecount(self, html):
        """解析总页数"""
        # 匹配分页信息 - 优先从分页链接提取
        # 匹配 "尾页" 链接中的最大页码
        last_match = re.search(r'<a[^>]*href="[^"]*page/(\d+)\.html"[^>]*>.*?尾页', html)
        if last_match:
            return int(last_match.group(1))
        # 匹配页码列表中的最大数字
        page_nums = re.findall(r'<a[^>]*href="[^"]*page/(\d+)\.html"[^>]*>', html)
        if page_nums:
            return max(int(p) for p in page_nums)
        # 匹配 "共 X 页"
        m = re.search(r'共\s*(\d+)\s*页', html)
        if m:
            return int(m.group(1))
        # 匹配 pagecount 变量
        m = re.search(r'pagecount["\']?\s*[:=]\s*["\']?(\d+)', html)
        if m:
            return int(m.group(1))
        # 默认50页
        return 50
    def _extract_vod_id(self, link):
        """从链接提取视频ID"""
        # /vod/play/id/1285506/sid/1/nid/1.html
        m = re.search(r'/vod/play/id/(\d+)', link)
        if m:
            return m.group(1)
        m = re.search(r'/vod/detail/id/(\d+)', link)
        if m:
            return m.group(1)
        return None

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vod_id = ids[0]
        # 直接构造详情URL
        detail_url = f"{self.host}{self.base_path}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        res = self.fetch(detail_url, headers=self.headers, timeout=10)
        if not res:
            return {"list": []}
        html = res.text if hasattr(res, "text") else str(res.content or "", "utf-8", errors="ignore")
        return self._parse_detail(html, vod_id)

    def _parse_detail(self, html, vod_id):
        """解析详情页"""
        # 提取标题 - 增强版
        title = ""
        # 方式1: h3 > a 后的文本
        title_match = re.search(r'<h3[^>]*class="[^"]*fed-part-eone[^"]*"[^>]*><a[^>]*>[^<]*</a>([^<]+)</h3>', html)
        if title_match:
            title = title_match.group(1).strip()
        if not title:
            # 方式2: 直接匹配 h3 内的 a 标签
            title_match = re.search(r'<h3[^>]*class="[^"]*fed-part-eone[^"]*"[^>]*><a[^>]*href="[^"]*"[^>]*>([^<]+)</a>', html)
            if title_match:
                title = title_match.group(1).strip()
        if not title:
            # 方式3: title 标签
            title_match = re.search(r'<title>([^<]+)</title>', html)
            if title_match:
                title = title_match.group(1).strip()
                if ' - ' in title:
                    title = title.split(' - ')[0]
        if not title:
            title = f"视频{vod_id}"

        # 提取封面
        pic = ""
        pic_match = re.search(r'<a[^>]*class="[^"]*fed-list-pics[^"]*"[^>]*data-original="([^"]+)"', html)
        if pic_match:
            pic = pic_match.group(1)
        if not pic:
            pic_match = re.search(r'<img[^>]*class="[^"]*fed-list-pics[^"]*"[^>]*data-original="([^"]+)"', html)
            if pic_match:
                pic = pic_match.group(1)
        if pic and not pic.startswith("http"):
            pic = urljoin(self.host + self.base_path + "/", pic)

        # 提取简介/备注
        content = ""
        remark_match = re.search(r'<span[^>]*class="[^"]*fed-text-muted[^"]*"[^>]*>简介[：:]\s*</span>\s*([^<]+)</li>', html)
        if remark_match:
            content = remark_match.group(1).strip()
        if not content:
            remark_match = re.search(r'<div[^>]*class="[^"]*fed-desc-info[^"]*"[^>]*>([^<]+)</div>', html)
            if remark_match:
                content = remark_match.group(1).strip()

        # 提取播放地址
        play_url = self._extract_play_url(html)
        if play_url:
            if play_url.endswith(".m3u8") or "m3u8" in play_url.lower():
                play_url = self._m3u8_proxy_url(play_url)
            return {
                "list": [{
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": "直链",
                    "vod_content": content,
                    "vod_play_from": "播放",
                    "vod_play_url": f"播放${play_url}"
                }]
            }

        return {
            "list": [{
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": "播放页",
                "vod_content": content,
                "vod_play_from": "播放",
                "vod_play_url": f"播放$play://{vod_id}"
            }]
        }
    def _extract_play_url(self, html):
        """从HTML中提取播放地址"""
        # 从 player_data 中提取
        m = re.search(r'player_data\s*=\s*({[^}]+})', html)
        if m:
            try:
                data = json.loads(m.group(1))
                return data.get("url", "")
            except:
                pass

        # 从 MacPlayer 中提取
        m = re.search(r'MacPlayer\.PlayUrl\s*=\s*["\']([^"\']+)["\']', html)
        if m:
            return m.group(1)

        # 从页面中直接搜索m3u8
        m = re.search(r'https?://[^"\']+\.m3u8[^"\']*', html)
        if m:
            return m.group(0)

        return ""

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        url = f"{self.host}{self.base_path}/index.php/vod/search.html?wd={quote(key)}&page={pg}"
        res = self.fetch(url, headers=self.headers, timeout=10)
        if not res:
            return {"list": [], "page": int(pg)}
        html = res.text if hasattr(res, "text") else str(res.content or "", "utf-8", errors="ignore")
        items = self._parse_search_items(html)
        return {"list": items, "page": int(pg)}

    def _parse_search_items(self, html):
        """解析搜索页结果 (dl.fed-list-deta结构)"""
        items = []
        # 匹配 dl.fed-list-deta 块
        pattern = r'<dl[^>]*class="[^"]*fed-list-deta[^"]*"[^>]*>.*?<a[^>]*class="[^"]*fed-list-pics[^"]*"[^>]*href="([^"]+)"[^>]*data-original="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*fed-list-score[^"]*"[^>]*>([^<]*)</span>.*?</a>.*?<h3[^>]*class="[^"]*fed-part-eone[^"]*"[^>]*><a[^>]*href="[^"]*"[^>]*>([^<]*)</a></h3>'
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            link, pic, score, title = match
            vod_id = self._extract_vod_id(link)
            if not vod_id:
                continue
            if pic and not pic.startswith("http"):
                pic = urljoin(self.host + self.base_path + "/", pic)
            items.append({
                "vod_id": vod_id,
                "vod_name": title.strip(),
                "vod_pic": pic,
                "vod_remarks": score.strip() if score else ""
            })
        return items
    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": {}}

        # 如果是代理地址，直接返回
        if id.startswith("http") and "m3u8" in id.lower():
            try:
                # 检查m3u8是否可访问，5秒超时
                res = self.fetch(id, headers=self.headers, timeout=5)
                if res and hasattr(res, "status_code") and res.status_code == 200:
                    # 检查内容是否有效m3u8
                    content = getattr(res, "content", b"") or b""
                    if b"#EXTM3U" in content[:256]:
                        return {"parse": 0, "url": id, "header": {"User-Agent": self.headers["User-Agent"]}}
                    else:
                        self.log(f"m3u8内容无效，交由播放器直连尝试")
                        return {"parse": 0, "url": id, "header": {"User-Agent": self.headers["User-Agent"]}}
                else:
                    # 状态码非200，尝试降级到parse:1
                    status = getattr(res, "status_code", 0) if res else 0
                    self.log(f"m3u8预检失败 status={status}，降级到parse:1")
                    # 返回播放页URL让壳端嗅探
                    return {"parse": 1, "url": id, "header": self.headers}
            except Exception as e:
                self.log(f"m3u8预检异常: {str(e)[:50]}，降级到parse:1")
                # 超时或网络错误，降级嗅探
                return {"parse": 1, "url": id, "header": self.headers}

        # 如果是play://协议，去播放页提取
        if id.startswith("play://"):
            vod_id = id.replace("play://", "")
            play_url = f"{self.host}{self.base_path}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
            try:
                res = self.fetch(play_url, headers=self.headers, timeout=10)
                if res and hasattr(res, "status_code") and res.status_code == 200:
                    html = res.text if hasattr(res, "text") else str(res.content or "", "utf-8", errors="ignore")
                    m3u8_url = self._extract_play_url(html)
                    if m3u8_url:
                        if ".m3u8" in m3u8_url.lower():
                            # 再次验证m3u8是否可访问
                            try:
                                verify = self.fetch(m3u8_url, headers=self.headers, timeout=5)
                                if verify and hasattr(verify, "status_code") and verify.status_code == 200:
                                    if b"#EXTM3U" in (getattr(verify, "content", b"") or b"")[:256]:
                                        return {"parse": 0, "url": self._m3u8_proxy_url(m3u8_url), "header": {"User-Agent": self.headers["User-Agent"]}}
                            except:
                                pass
                            # 验证失败，仍尝试播放
                            return {"parse": 0, "url": self._m3u8_proxy_url(m3u8_url), "header": {"User-Agent": self.headers["User-Agent"]}}
                        return {"parse": 0, "url": m3u8_url, "header": {"User-Agent": self.headers["User-Agent"]}}
            except Exception as e:
                self.log(f"播放页请求异常: {str(e)[:50]}")

        # 降级嗅探 - 带完整header
        return {"parse": 1, "url": id, "header": self.headers}
    def recommendContent(self, ids, pg):
        """相关推荐"""
        if not ids:
            return {"list": []}
        vod_id = ids[0] if isinstance(ids, list) else ids
        # 获取当前视频分类，然后取同分类推荐
        detail_url = f"{self.host}{self.base_path}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
        res = self.fetch(detail_url, headers=self.headers, timeout=10)
        if not res:
            return {"list": []}
        html = res.text if hasattr(res, "text") else str(res.content or "", "utf-8", errors="ignore")
        # 提取相关推荐
        items = self._parse_list_items(html, "ul.fed-list-info li.fed-list-item")
        return {"list": items[:12]}

    def _m3u8_proxy_url(self, url):
        """生成m3u8代理地址"""
        if url and url.startswith("http"):
            return f"http://127.0.0.1:9978/proxy?do=py&url={quote(url, safe='')}"
        return url

    def localProxy(self, param):
        """m3u8本地代理 + 广告分片过滤"""
        try:
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")
            if target.startswith("url="):
                target = target[4:]
            elif "url=" in target:
                qs = urlparse(target).query
                qs_dict = dict(x.split("=", 1) for x in qs.split("&") if "=" in x)
                target = qs_dict.get("url", "")
            target = unquote(str(target or ""))
            if not target or not target.startswith("http"):
                return [400, "text/plain", b"invalid url"]

            resp = self.fetch(target, headers=self.headers, timeout=20)
            if not resp:
                return [502, "text/plain", b"fetch failed"]
            content = getattr(resp, "content", b"") or b""
            if not content and hasattr(resp, "text") and resp.text:
                content = resp.text.encode("utf-8", errors="ignore")
            if not content:
                return [502, "text/plain", b"empty content"]

            # 检测m3u8
            if b"#EXTM3U" in content[:256]:
                cleaned = self._clean_m3u8(content.decode("utf-8", errors="ignore"), target)
                return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

            # 非m3u8直接透传
            return [200, "application/octet-stream", content]
        except Exception as e:
            return [500, "text/plain", f"localProxy error: {e}".encode("utf-8", errors="ignore")]

    def _clean_m3u8(self, text, source_url):
        """清洗m3u8：检测图片流 + 广告分片过滤"""
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 第1层：图片流伪装检测
        is_png_stream = False
        low_source = (source_url or "").lower()
        for sig in ("doyinapi", "svip", "imgcdn", "photo", "ckzyc", "ckzy3"):
            if sig in low_source:
                is_png_stream = True
                break
        if not is_png_stream:
            for line in lines:
                if '.png' in line.lower() or '.jpg' in line.lower() or '.jpeg' in line.lower() or '.webp' in line.lower():
                    if not line.startswith("#"):
                        is_png_stream = True
                        break

        # 第2层：多码率主表
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

        # 第3层：正片目录锚点（优先从KEY URI提取）
        main_dir = self._resolve_main_dir(lines, source_url)

        # 第4层：分片过滤（图片流和普通流统一处理）
        segments = []
        pending = []
        removed = 0
        kept = 0

        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media_url = urljoin(source_url, line)
                # 判断是否为正片
                is_main = self._is_main_segment(media_url, main_dir)
                if is_main:
                    segments.extend(pending)
                    # 如果是图片流，替换扩展名
                    if is_png_stream:
                        for ext in (".png", ".jpeg", ".jpg", ".webp"):
                            if ext in media_url:
                                media_url = media_url.replace(ext, ".ts")
                                break
                    segments.append(media_url)
                    kept += 1
                else:
                    removed += 1
                pending = []
                continue
            if line.startswith("#"):
                segments.append(line)
            else:
                media_url = urljoin(source_url, line)
                if is_png_stream:
                    for ext in (".png", ".jpeg", ".jpg", ".webp"):
                        if ext in media_url:
                            media_url = media_url.replace(ext, ".ts")
                            break
                segments.append(media_url)

        # 第5层：全滤兜底
        if kept == 0 and removed > 0:
            self.log("广告过滤命中全部分片，判定锚点失效，回退为不过滤模式")
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            # 如果是图片流，替换扩展名
            if is_png_stream:
                out_str = "\n".join(out)
                for ext in (".png", ".jpeg", ".jpg", ".webp"):
                    out_str = out_str.replace(ext, ".ts")
                return out_str + "\n"
            return "\n".join(out) + "\n"

        if removed:
            self.log(f"m3u8已过滤广告分片: {removed}个，保留正片: {kept}个")
        else:
            self.log(f"m3u8无广告分片，保留正片: {kept}个")

        # 冗余标签清理
        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"
    def _is_fake_image_stream(self, text, source_url):
        """检测是否为图片流伪装"""
        low_url = (source_url or "").lower()
        # 已知图片流服务商特征
        for sig in ("doyinapi", "svip", "imgcdn", "photo", "ckzyc", "ckzy3"):
            if sig in low_url:
                return True
        # 检测分片扩展名是否为图片格式
        for line in str(text or "").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            low = line.lower().split("?")[0]
            if low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                return True
        return False

    def _resolve_main_dir(self, lines, source_url):
        """解析正片目录锚点"""
        import posixpath
        parsed = urlparse(source_url)
        main_dir = posixpath.dirname(parsed.path)
        if not main_dir.endswith("/"):
            main_dir += "/"

        # 优先从KEY URI提取
        for line in lines:
            if not line.startswith("#EXT-X-KEY") or "URI=" not in line:
                continue
            m = re.search(r'URI="([^"]+)"', line)
            if not m:
                continue
            key_uri = m.group(1)
            if not key_uri.startswith("http"):
                key_uri = urljoin(source_url, key_uri)
            key_path = urlparse(key_uri).path
            key_dir = posixpath.dirname(key_path)
            if key_dir and key_dir != "/":
                return key_dir + "/"
        return main_dir

    def _is_main_segment(self, media_url, main_dir):
        """判断分片是否为正片"""
        if not main_dir:
            return True
        media_path = urlparse(media_url).path
        return media_path.startswith(main_dir)

    def _rewrite_m3u8_tag(self, line, source_url):
        """重写m3u8标签中的URI"""
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(m):
                uri = m.group(1)
                if uri.startswith(("http://", "https://")):
                    return f'URI="{uri}"'
                return f'URI="{urljoin(source_url, uri)}"'
            return re.sub(r'URI="([^"]+)"', repl, line)
        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urljoin(source_url, line)
        return line

    def _dedup_tags(self, segments, source_url):
        """去重冗余标签"""
        NOISE = ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE")
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in NOISE:
                if not out or out[-1] in NOISE:
                    continue
            out.append(line)
        # 清理尾部噪声
        while len(out) > 1 and out[-1] in NOISE:
            out.pop()
        return out