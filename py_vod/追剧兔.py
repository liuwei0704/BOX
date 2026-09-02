# coding: utf-8
"""
站点信息：
- 主域名：zhuijutu.cc
- 备用域名：zhuijutu.xyz (发布页)
- 类型：MacCMS影视站
- 特殊：m3u8有广告分片，需通过localProxy过滤
- 验证时间：2026-09-02
- 来源：用户调试修复
- m3u8结构：单码率，有KEY URI，锚点路径 /video/linjiangezong/.../，广告目录 /video/adjump/time/
"""
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import urllib.parse
from urllib.parse import quote, urljoin
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://zhuijutu.cc"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive"
        }
        self.classes = [
            {"type_id": "2", "type_name": "连续剧"},
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "23", "type_name": "短剧"},
        ]
        self.filters = {
            "2": [
                {"key": "year", "name": "年份", "value": [
                    {"n": "全部", "v": ""},
                    {"n": "2026", "v": "2026"},
                    {"n": "2025", "v": "2025"},
                    {"n": "2024", "v": "2024"},
                    {"n": "2023", "v": "2023"},
                ]}
            ],
            "1": [],
            "4": [],
            "3": [],
            "23": []
        }

    def getName(self):
        return "追剧兔"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html("/")
        if not html:
            return {"list": []}
        return self._parse_home_video_list(html)

    def categoryContent(self, tid, pg, filter, extend):
        page = pg or "1"
        url = f"{self.host}/vodshow/{tid}--------{page}---.html"
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

        result = self._parse_video_list(html)
        page_info = self._parse_pagination(html)
        return {
            "list": result.get("list", []),
            "page": int(page),
            "pagecount": page_info.get("pagecount", 1),
            "limit": 20,
            "total": page_info.get("total", 0)
        }

    def detailContent(self, ids):
        vod_id = str(ids[0]) if ids else ""
        if not vod_id:
            return {"list": []}

        # 从列表传递的复合ID中提取信息
        if "|$|" in vod_id:
            parts = vod_id.split("|$|")
            vid = parts[0]
            name = parts[1] if len(parts) > 1 else ""
            pic = parts[2] if len(parts) > 2 else ""
            remark = parts[3] if len(parts) > 3 else ""
        else:
            vid = vod_id
            name = ""
            pic = ""
            remark = ""

        html = self._fetch_html(f"/voddetail/{vid}/")
        if not html:
            if name:
                return {"list": [{
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": remark,
                    "vod_play_from": "播放",
                    "vod_play_url": f"第1集$/{vid}"
                }]}
            return {"list": []}

        return self._parse_detail(html, vid, vod_id, name, pic, remark)

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}

        page = pg or "1"
        encoded_key = quote(str(key), safe='')
        if page == "1":
            url = f"{self.host}/vodsearch/{encoded_key}-------------.html"
        else:
            url = f"{self.host}/vodsearch/{encoded_key}----------{page}---.html"

        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": int(page)}

        if "没有找到" in html or "暂无数据" in html:
            return {"list": [], "page": int(page)}

        result = self._parse_video_list(html)
        return {
            "list": result.get("list", []),
            "page": int(page)
        }

    def playerContent(self, flag, id, vipFlags):
        """
        播放地址提取，优先返回 parse:0 直链
        从详情页传递的 play_id 格式：
        - 直接m3u8链接：http://xxx.m3u8
        - 播放页路径：/vodplay/xxx-1-1.html
        - 相对路径：/vodplay/xxx-1-1.html
        """
        if not id:
            return {"parse": 0, "url": "", "header": {}}

        play_url = str(id).strip()

        # 方法1：如果已经是m3u8直链，直接返回（不经过代理）
        if play_url.startswith("http") and ".m3u8" in play_url:
            return {
                "parse": 0,
                "url": play_url,
                "header": {"User-Agent": self.headers.get("User-Agent", "")}
            }

        # 方法2：完整播放页URL
        if play_url.startswith("http"):
            html = self._fetch_html(play_url)
            m3u8_url = self._extract_m3u8_from_html(html)
            if m3u8_url:
                return {
                    "parse": 0,
                    "url": m3u8_url,
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }
            return {"parse": 1, "url": play_url, "header": self.headers}

        # 方法3：相对路径 /vodplay/xxx-1-1.html
        if play_url.startswith("/"):
            full_url = self.host + play_url
            html = self._fetch_html(full_url)
            m3u8_url = self._extract_m3u8_from_html(html)
            if m3u8_url:
                return {
                    "parse": 0,
                    "url": m3u8_url,
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }
            return {"parse": 1, "url": full_url, "header": self.headers}

        # 方法4：如果id是vod_id，尝试构建播放页
        if play_url and play_url.isdigit():
            detail_url = f"{self.host}/voddetail/{play_url}/"
            html = self._fetch_html(detail_url)
            play_href = self._extract_first_play_href(html)
            if play_href:
                full_url = self.host + play_href
                play_html = self._fetch_html(full_url)
                m3u8_url = self._extract_m3u8_from_html(play_html)
                if m3u8_url:
                    return {
                        "parse": 0,
                        "url": m3u8_url,
                        "header": {"User-Agent": self.headers.get("User-Agent", "")}
                    }

        return {"parse": 1, "url": str(id or ""), "header": self.headers}

    def recommendContent(self, ids, pg):
        vid = str(ids[0]) if ids else ""
        if not vid:
            return {"list": []}

        html = self._fetch_html(f"/voddetail/{vid}/")
        if not html:
            return {"list": []}

        return self._parse_recommend(html)

    def destroy(self):
        pass

    # ==================== 辅助方法 ====================

    def _fetch_html(self, path):
        if path.startswith("http"):
            url = path
        else:
            url = self.host + path
        try:
            headers = self.headers.copy()
            # 禁用SSL验证，解决证书过期问题
            resp = self.fetch(url, headers=headers, timeout=15, verify=False)
            if resp is None:
                return ""
            if hasattr(resp, "text"):
                return resp.text or ""
            elif hasattr(resp, "content"):
                try:
                    return resp.content.decode("utf-8", errors="ignore")
                except:
                    return ""
            return ""
        except Exception as e:
            self.log({"action": "fetch_fail", "url": url, "error": str(e)})
            return ""

    def _parse_home_video_list(self, html):
        items = []
        pattern = r'<a[^>]*class="[^"]*hl-item-thumb[^"]*"[^>]*href="(/voddetail/(\d+)\.html)"[^>]*title="([^"]*)"[^>]*data-original="([^"]*)"[^>]*>'
        matches = re.findall(pattern, html)

        seen = set()
        for match in matches:
            href = match[0]
            vid = match[1]
            title = match[2].strip()
            pic = match[3]
            if not title or vid in seen:
                continue
            seen.add(vid)

            remark = self._extract_remark(html, href)
            vod_id = f"{vid}|$|{title}|$|{pic}|$|{remark}"
            items.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })

            if len(items) >= 32:
                break

        return {"list": items}

    def _parse_video_list(self, html):
        items = []
        pattern = r'<a[^>]*class="[^"]*hl-item-thumb[^"]*"[^>]*href="(/voddetail/(\d+)\.html)"[^>]*title="([^"]*)"[^>]*data-original="([^"]*)"[^>]*>'
        matches = re.findall(pattern, html)

        for match in matches:
            href = match[0]
            vid = match[1]
            title = match[2].strip()
            pic = match[3]
            if not title:
                continue

            remark = self._extract_remark(html, href)
            vod_id = f"{vid}|$|{title}|$|{pic}|$|{remark}"
            items.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })

        return {"list": items}

    def _extract_remark(self, html, href):
        """从HTML中提取角标备注"""
        a_pattern = r'<a[^>]*href="' + re.escape(href) + r'"[^>]*title="[^"]*"[^>]*>(.*?)</a>'
        a_match = re.search(a_pattern, html, re.DOTALL)
        a_content = a_match.group(1) if a_match else ""

        remark = ""
        remark_match = re.search(r'<span[^>]*class="[^"]*remarks[^"]*"[^>]*>([^<]+)</span>', a_content)
        if remark_match:
            remark = remark_match.group(1).strip()
        if not remark:
            state_match = re.search(r'<span[^>]*class="[^"]*state[^"]*"[^>]*>([^<]+)</span>', a_content)
            if state_match:
                remark = state_match.group(1).strip()
        if not remark:
            pic_text_match = re.search(r'<span[^>]*class="[^"]*hl-pic-text[^"]*"[^>]*>([^<]+)</span>', a_content)
            if pic_text_match:
                remark = pic_text_match.group(1).strip()
        return remark

    def _parse_pagination(self, html):
        result = {"pagecount": 1, "total": 0}
        total_match = re.search(r'data-rec-total="(\d+)"', html)
        if total_match:
            result["total"] = int(total_match.group(1))
        page_match = re.search(r'data-pagecount="(\d+)"', html)
        if page_match:
            result["pagecount"] = int(page_match.group(1))
        # 兜底：从分页链接中提取最大页码
        if result["pagecount"] == 1:
            max_page = 1
            for m in re.finditer(r'/vodshow/\d+--------(\d+)---\.html', html):
                p = int(m.group(1))
                if p > max_page:
                    max_page = p
            result["pagecount"] = max_page if max_page > 1 else 1
        return result

    def _parse_detail(self, html, vid, vod_id, name, pic, remark):
        # 提取名称
        if not name:
            name_match = re.search(r'<h2[^>]*class="[^"]*hl-dc-title[^"]*"[^>]*>([^<]+)</h2>', html)
            if name_match:
                name = name_match.group(1).strip()
            else:
                name_match = re.search(r'<title>([^<]*)</title>', html)
                if name_match:
                    name = name_match.group(1).replace(" - 追剧兔影视", "").strip()

        # 提取图片
        if not pic:
            img_match = re.search(r'<span[^>]*class="[^"]*hl-item-thumb[^"]*"[^>]*data-original="([^"]+)"', html)
            if img_match:
                pic = img_match.group(1)

        # 提取简介
        content = ""
        content_match = re.search(r'<span[^>]*class="[^"]*hl-content-text[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
        if content_match:
            content = re.sub(r'<[^>]+>', '', content_match.group(1)).strip()

        # 提取导演和演员
        director = ""
        actor = ""
        info_items = re.findall(r'<div[^>]*class="[^"]*hl-info-item[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        for item in info_items:
            label_match = re.search(r'<div[^>]*class="[^"]*hl-info-label[^"]*"[^>]*>([^<]+)</div>', item)
            value_match = re.search(r'<div[^>]*class="[^"]*hl-info-value[^"]*"[^>]*>([^<]+)</div>', item)
            if label_match and value_match:
                label = label_match.group(1).strip()
                value = value_match.group(1).strip()
                if "导演" in label:
                    director = value
                elif "主演" in label:
                    actor = value

        # ====== 多线路播放列表提取 ======
        play_from_list = []
        play_url_list = []

        # 1. 提取线路名称和对应的播放列表容器
        tab_pattern = r'<a[^>]*class="[^"]*hl-tabs-btn[^"]*"[^>]*alt="([^"]*)"[^>]*>'
        tabs = re.findall(tab_pattern, html)
        if not tabs:
            tab_pattern2 = r'<a[^>]*class="[^"]*hl-tabs-btn[^"]*"[^>]*>([^<]+)</a>'
            tabs = re.findall(tab_pattern2, html)
            tabs = [t.strip() for t in tabs if t.strip() and "线路" in t or "播放" in t]

        # 2. 提取播放列表容器
        container_pattern = r'<div[^>]*class="[^"]*hl-tabs-box[^"]*"[^>]*>(.*?)</div>'
        containers = re.findall(container_pattern, html, re.DOTALL)

        # 3. 匹配线路和容器
        if tabs and containers and len(tabs) == len(containers):
            for idx, tab in enumerate(tabs):
                source_name = tab.strip()
                if not source_name:
                    source_name = f"线路{idx+1}"
                container = containers[idx]
                episodes = self._extract_episodes(container)
                if episodes:
                    play_from_list.append(source_name)
                    play_url_list.append("#".join(episodes))

        # 4. 兜底：直接提取所有播放链接
        if not play_from_list:
            # 提取所有线路标签
            all_tabs = re.findall(r'<a[^>]*class="[^"]*hl-tabs-btn[^"]*"[^>]*>([^<]+)</a>', html)
            all_tabs = [t.strip() for t in all_tabs if t.strip()]
            all_containers = re.findall(r'<ul[^>]*class="[^"]*hl-plays-list[^"]*"[^>]*>(.*?)</ul>', html, re.DOTALL)

            if all_tabs and all_containers:
                for idx, tab in enumerate(all_tabs):
                    if idx < len(all_containers):
                        source_name = tab.strip()
                        episodes = self._extract_episodes(all_containers[idx])
                        if episodes:
                            play_from_list.append(source_name)
                            play_url_list.append("#".join(episodes))
            elif all_containers:
                # 无线路名称，使用默认
                for idx, container in enumerate(all_containers):
                    source_name = f"线路{idx+1}"
                    episodes = self._extract_episodes(container)
                    if episodes:
                        play_from_list.append(source_name)
                        play_url_list.append("#".join(episodes))

        # 5. 最终兜底
        if not play_from_list:
            # 直接查找所有 /vodplay/ 链接
            ep_pattern = r'<a[^>]*href="(/vodplay/[^"]+)"[^>]*>([^<]+)</a>'
            ep_matches = re.findall(ep_pattern, html)
            if ep_matches:
                episodes = []
                for ep in ep_matches:
                    ep_href = ep[0]
                    ep_text = ep[1].strip()
                    if ep_text and ep_href:
                        episodes.append(f"{ep_text}${ep_href}")
                if episodes:
                    play_from_list.append("播放")
                    play_url_list.append("#".join(episodes))
            else:
                play_from_list = ["播放"]
                play_url_list = [f"第1集$/{vid}"]

        return {
            "list": [{
                "vod_id": vod_id,
                "vod_name": name or "视频",
                "vod_pic": pic,
                "vod_remarks": remark or "",
                "vod_actor": actor,
                "vod_director": director,
                "vod_content": content,
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }]
        }

    def _extract_episodes(self, container):
        """从播放列表容器中提取剧集"""
        episodes = []
        ep_pattern = r'<a[^>]*href="(/vodplay/[^"]+)"[^>]*>([^<]+)</a>'
        ep_matches = re.findall(ep_pattern, container)
        for ep in ep_matches:
            ep_href = ep[0]
            ep_text = ep[1].strip()
            if ep_text and ep_href:
                episodes.append(f"{ep_text}${ep_href}")
        return episodes

    def _parse_recommend(self, html):
        items = []
        pattern = r'<a[^>]*class="[^"]*hl-item-thumb[^"]*"[^>]*href="(/voddetail/(\d+)/?)"[^>]*title="([^"]*)"[^>]*>'
        matches = re.findall(pattern, html)

        for match in matches:
            href = match[0]
            vid = match[1]
            title = match[2].strip()
            if not title:
                continue

            pic = ""
            a_pattern = r'<a[^>]*href="' + re.escape(href) + r'"[^>]*title="[^"]*"[^>]*>(.*?)</a>'
            a_match = re.search(a_pattern, html, re.DOTALL)
            if a_match:
                a_content = a_match.group(1)
                img_match = re.search(r'<[^>]*data-original="([^"]+)"', a_content)
                if img_match:
                    pic = img_match.group(1)

            items.append({
                "vod_id": f"{vid}|$|{title}|$|{pic}|$|",
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": ""
            })

        return {"list": items[:20]}

    def _parse_extend(self, extend):
        if not extend:
            return {}
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            try:
                import json
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

    def _extract_m3u8_from_html(self, html):
        """从播放页HTML中提取m3u8地址 - 多种方式兜底"""
        if not html:
            return None

        # 方法1: 从 player_aaaa 对象中提取（最可靠）
        # 匹配 var player_aaaa = {"url":"https://xxx.m3u8", ...}
        pattern1 = r'var\s+player_aaaa\s*=\s*(\{[^}]*"url"\s*:\s*"([^"]+\.m3u8[^"]*)"[^}]*\})'
        match1 = re.search(pattern1, html, re.DOTALL)
        if match1:
            url = match1.group(2)
            if url.startswith("http") and ".m3u8" in url:
                return url
            # 尝试JSON解析
            try:
                import json
                data = json.loads(match1.group(1))
                url = data.get("url", "")
                if url and url.startswith("http") and ".m3u8" in url:
                    return url
            except:
                pass

        # 方法2: 直接正则匹配 "url":"https://xxx.m3u8"
        pattern2 = r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"'
        match2 = re.search(pattern2, html)
        if match2:
            url = match2.group(1)
            if url.startswith("http") and ".m3u8" in url:
                return url

        # 方法3: 查找任何m3u8链接
        pattern3 = r'https?://[^\s"\']+\.m3u8[^\s"\']*'
        match3 = re.search(pattern3, html)
        if match3:
            return match3.group(0)

        # 方法4: 从 player_aaaa 中提取含m3u8的完整字符串（更宽松）
        pattern4 = r'player_aaaa\s*=\s*\{[^}]*"url"\s*:\s*"([^"]*m3u8[^"]*)"'
        match4 = re.search(pattern4, html, re.DOTALL)
        if match4:
            url = match4.group(1)
            if url.startswith("http"):
                return url
            # 处理转义
            url = url.replace("\\/", "/")
            if url.startswith("http"):
                return url

        # 方法5: 从播放器配置中提取（更宽泛）
        pattern5 = r'url\s*[:=]\s*["\']([^"\']*\.m3u8[^"\']*)["\']'
        match5 = re.search(pattern5, html)
        if match5:
            url = match5.group(1)
            if url.startswith("http"):
                return url

        return None

    def _extract_first_play_href(self, html):
        """从详情页提取第一个播放链接"""
        if not html:
            return None
        # 查找播放列表中的第一个链接
        pattern = r'<a[^>]*href="(/vodplay/[^"]+)"[^>]*>'
        matches = re.findall(pattern, html)
        if matches:
            return matches[0]
        return None

    def _m3u8_proxy_url(self, url):
        """生成m3u8代理地址"""
        if url:
            url = url.replace("\\/", "/")
        return "http://127.0.0.1:9978/proxy?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")

    def _is_fake_image_stream(self, text, source_url):
        """检测是否为图片流伪装"""
        low_url = (source_url or "").lower()
        # 图片流服务商特征
        for sig in ("doyinapi", "svip", "imgcdn", "photo"):
            if sig in low_url:
                return True
        # 分片扩展名为图片格式
        for line in str(text or "").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            low = line.lower().split("?")[0]
            if low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                return True
        return False

    def _resolve_main_dir(self, lines, source_url):
        """确定正片目录锚点，优先使用KEY URI目录"""
        import posixpath
        parsed = urllib.parse.urlparse(source_url)
        main_dir = posixpath.dirname(parsed.path)
        if not main_dir.endswith("/"):
            main_dir += "/"

        # 优先以KEY URI目录为锚点
        for line in lines:
            if not line.startswith("#EXT-X-KEY") or "URI=" not in line:
                continue
            m = re.search(r'URI="([^"]+)"', line)
            if not m:
                continue
            key_uri = m.group(1)
            if key_uri.startswith("http"):
                key_path = urllib.parse.urlparse(key_uri).path
            else:
                key_path = urllib.parse.urlparse(
                    urllib.parse.urljoin(source_url, key_uri)
                ).path
            key_dir = posixpath.dirname(key_path)
            if key_dir and key_dir != "/":
                return key_dir + "/"
        return main_dir

    def _filter_segments(self, lines, source_url, main_dir):
        """过滤分片，保留正片目录下的分片"""
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
                media_url = urllib.parse.urljoin(source_url, line)
                media_path = urllib.parse.urlparse(media_url).path
                if media_path.startswith(main_dir):
                    segments.extend(pending)
                    segments.append(media_url)
                    kept += 1
                else:
                    removed += 1
                pending = []
                continue
            if line.startswith("#"):
                segments.append(line)
            else:
                segments.append(urllib.parse.urljoin(source_url, line))
        return segments, removed, kept

    def _rewrite_m3u8_tag(self, line, source_url):
        """重写m3u8标签中的URI，补全绝对地址"""
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(match):
                uri = match.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urllib.parse.urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)
        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urllib.parse.urljoin(source_url, line)
        return line

    def _dedup_tags(self, segments, source_url):
        """清理冗余标签"""
        NOISE = ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE")
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in NOISE:
                if not out or out[-1] in NOISE:
                    continue
            out.append(line)
        while len(out) > 1 and out[-1] in NOISE:
            out.pop()
        return out

    def _clean_m3u8(self, text, source_url):
        """
        m3u8去广告五层管线：
        第1层：图片流伪装检测（命中则还原扩展名并立即return）
        第2层：多码率主表透传
        第3层：正片目录锚点（KEY URI优先）
        第4层：分片过滤（成对丢弃）
        第5层：冗余标签清理 + 全滤兜底
        """
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"

        # 第1层：图片流伪装
        if self._is_fake_image_stream(text, source_url):
            restored = text
            for ext in (".png", ".jpeg", ".jpg", ".webp"):
                restored = restored.replace(ext, ".ts")
            self.log("检测到图片流伪装，已还原扩展名 -> .ts，跳过广告过滤")
            out = [self._rewrite_m3u8_tag(l, source_url) for l in restored.replace("\r", "").split("\n") if l.strip()]
            return "\n".join(out) + "\n"

        # 第2层：多码率主表
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            out = []
            for line in lines:
                if line.startswith("#"):
                    out.append(line)
                else:
                    child = urllib.parse.urljoin(source_url, line)
                    if ".m3u8" in child.lower():
                        out.append(self._m3u8_proxy_url(child))
                    else:
                        out.append(child)
            return "\n".join(out) + "\n"

        # 第3层：正片目录锚点
        main_dir = self._resolve_main_dir(lines, source_url)

        # 第4层：分片过滤
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)

        # 第5层：全滤兜底（归零或误杀过半都回退）
        if removed > 0 and (kept == 0 or removed > kept):
            self.log(f"广告过滤命中过多分片(滤{removed}/留{kept})，判定锚点失效，回退为不过滤模式")
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"

        if removed:
            self.log(f"m3u8已过滤广告分片: {removed}个，保留正片: {kept}个")

        # 第5层：冗余标签清理
        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

    def localProxy(self, param):
        """
        m3u8本地代理 + 五层广告过滤
        """
        try:
            # 解析参数
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")

            if target.startswith("url="):
                target = target[4:]
            elif "url=" in target:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(target).query)
                if "url" in qs:
                    target = qs["url"][0]

            target = urllib.parse.unquote(str(target or ""))
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

            # 检查是否为m3u8
            if b"#EXTM3U" in content[:256]:
                cleaned = self._clean_m3u8(content.decode("utf-8", errors="ignore"), target)
                return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]

            # 非m3u8直接透传
            return [200, "application/octet-stream", content]

        except Exception as e:
            self.log({"action": "localProxy_error", "error": str(e)})
            return [500, "text/plain", f"localProxy error: {str(e)}".encode("utf-8", errors="ignore")]