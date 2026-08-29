# coding: utf-8
import re
import urllib.parse
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://zhuijutu.cc"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "23", "type_name": "短剧"},
            {"type_id": "2", "type_name": "连续剧"},
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "综艺"},
        ]
        self.filters = {}

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
                    "vod_play_url": f"播放$/{vid}"
                }]}
            return {"list": []}

        return self._parse_detail(html, vid, vod_id, name, pic, remark)

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}

        page = pg or "1"
        encoded_key = quote(str(key), safe='')
        url = f"{self.host}/vodsearch/{encoded_key}-------------.html"
        if page != "1":
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
        # 参考王室日报.py的实现方式
        # 如果id是m3u8链接，直接返回
        if id and id.startswith("http") and ".m3u8" in id:
            return {
                "parse": 0, 
                "url": id, 
                "header": {"User-Agent": self.headers.get("User-Agent", "")}
            }
        
        # 如果id是播放页URL，请求并提取m3u8
        if id and id.startswith("http"):
            html = self._fetch_html(id)
            play_url = self._extract_m3u8_from_html(html)
            if play_url:
                return {
                    "parse": 0, 
                    "url": play_url, 
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }
            return {"parse": 1, "url": id, "header": self.headers}
        
        # 如果id是相对路径，构建完整URL
        if id and id.startswith("/"):
            full_url = self.host + id
            html = self._fetch_html(full_url)
            play_url = self._extract_m3u8_from_html(html)
            if play_url:
                return {
                    "parse": 0, 
                    "url": play_url, 
                    "header": {"User-Agent": self.headers.get("User-Agent", "")}
                }
            return {"parse": 1, "url": full_url, "header": self.headers}
        
        # 如果id是vod_id，尝试获取详情页
        if id:
            detail_url = f"{self.host}/voddetail/{id}/"
            html = self._fetch_html(detail_url)
            # 从详情页提取播放链接
            play_url = self._extract_m3u8_from_html(html)
            if play_url:
                return {
                    "parse": 0, 
                    "url": play_url, 
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
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            headers["Accept-Language"] = "zh-CN,zh;q=0.9,en;q=0.8"
            headers["Connection"] = "keep-alive"
            resp = self.fetch(url, headers=headers, timeout=15)
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
        thumb_pattern = r'<a[^>]*class="[^"]*hl-item-thumb[^"]*"[^>]*href="(/voddetail/(\d+)\.html)"[^>]*title="([^"]*)"[^>]*data-original="([^"]*)"[^>]*>'
        thumbs = re.findall(thumb_pattern, html)

        for thumb in thumbs:
            href = thumb[0]
            vid = thumb[1]
            title = thumb[2].strip()
            pic = thumb[3]
            if not title:
                continue

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

            vod_id = f"{vid}|$|{title}|$|{pic}|$|{remark}"
            items.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })

        return {"list": items}

    def _parse_pagination(self, html):
        result = {"pagecount": 1, "total": 0}
        total_match = re.search(r'data-rec-total="(\d+)"', html)
        if total_match:
            result["total"] = int(total_match.group(1))
        page_match = re.search(r'data-pagecount="(\d+)"', html)
        if page_match:
            result["pagecount"] = int(page_match.group(1))
        if result["pagecount"] == 1:
            max_page = 1
            for m in re.finditer(r'/vodshow/\d+--------(\d+)---\.html', html):
                p = int(m.group(1))
                if p > max_page:
                    max_page = p
            result["pagecount"] = max_page if max_page > 1 else 1
        return result

    def _parse_detail(self, html, vid, vod_id, name, pic, remark):
        if not name:
            name_match = re.search(r'<h1[^>]*class="[^"]*hl-text-site[^"]*"[^>]*>([^<]+)</h1>', html)
            if name_match:
                name = name_match.group(1).strip()
            else:
                name_match = re.search(r'<title>([^<]*)</title>', html)
                if name_match:
                    name = name_match.group(1).replace(" - 追剧兔", "").strip()

        if not pic:
            img_match = re.search(r'<[^>]*class="[^"]*hl-item-thumb[^"]*"[^>]*data-original="([^"]+)"', html)
            if img_match:
                pic = img_match.group(1)

        content = ""
        content_match = re.search(r'<[^>]*class="[^"]*hl-content-rt[^"]*"[^>]*>\s*<p[^>]*>([^<]+)</p>', html)
        if content_match:
            content = content_match.group(1).strip()
        else:
            content_match = re.search(r'<p[^>]*class="[^"]*hl-desc[^"]*"[^>]*>([^<]+)</p>', html)
            if content_match:
                content = content_match.group(1).strip()

        director = ""
        actor = ""
        info_items = re.findall(r'<[^>]*class="[^"]*hl-info-item[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        for item in info_items:
            label_match = re.search(r'<[^>]*class="[^"]*hl-info-label[^"]*"[^>]*>([^<]+)</div>', item)
            value_match = re.search(r'<[^>]*class="[^"]*hl-info-value[^"]*"[^>]*>([^<]+)</div>', item)
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

        # 1. 提取所有线路名称
        tab_pattern = r'<a[^>]*class="[^"]*hl-tabs-btn[^"]*"[^>]*alt="([^"]*)"[^>]*>'
        tabs = re.findall(tab_pattern, html)
        if not tabs:
            tab_pattern2 = r'<a[^>]*class="[^"]*hl-tabs-btn[^"]*"[^>]*>([^<]+)</a>'
            tabs = re.findall(tab_pattern2, html)
            tabs = [t.strip() for t in tabs]

        # 2. 提取所有线路对应的播放列表容器
        container_pattern = r'<div[^>]*class="[^"]*hl-tabs-box[^"]*"[^>]*>(.*?)</div>'
        containers = re.findall(container_pattern, html, re.DOTALL)

        # 3. 如果线路数量与容器数量匹配，逐个提取
        if tabs and containers and len(tabs) == len(containers):
            for idx, tab in enumerate(tabs):
                source_name = tab.strip()
                container = containers[idx]
                episodes = []
                # 提取播放链接
                ep_pattern = r'<a[^>]*href="(/vodplay/[^"]+)"[^>]*>([^<]+)</a>'
                ep_matches = re.findall(ep_pattern, container)
                for ep in ep_matches:
                    ep_href = ep[0]
                    ep_text = ep[1].strip()
                    if ep_text and ep_href:
                        episodes.append(f"{ep_text}${ep_href}")
                if episodes:
                    play_from_list.append(source_name)
                    play_url_list.append("#".join(episodes))

        # 4. 如果容器数量不匹配或没有线路，尝试直接提取所有 hl-plays-list
        if not play_from_list:
            ul_pattern = r'<ul[^>]*class="[^"]*hl-plays-list[^"]*"[^>]*id="[^"]*"[^>]*>(.*?)</ul>'
            ul_matches = re.findall(ul_pattern, html, re.DOTALL)
            if len(ul_matches) > 1:
                for idx, ul in enumerate(ul_matches):
                    source_name = f"线路{idx+1}"
                    episodes = []
                    ep_pattern = r'<a[^>]*href="(/vodplay/[^"]+)"[^>]*>([^<]+)</a>'
                    ep_matches = re.findall(ep_pattern, ul)
                    for ep in ep_matches:
                        ep_href = ep[0]
                        ep_text = ep[1].strip()
                        if ep_text and ep_href:
                            episodes.append(f"{ep_text}${ep_href}")
                    if episodes:
                        play_from_list.append(source_name)
                        play_url_list.append("#".join(episodes))
            elif ul_matches:
                # 只有一个播放列表
                episodes = []
                ep_pattern = r'<a[^>]*href="(/vodplay/[^"]+)"[^>]*>([^<]+)</a>'
                ep_matches = re.findall(ep_pattern, ul_matches[0])
                for ep in ep_matches:
                    ep_href = ep[0]
                    ep_text = ep[1].strip()
                    if ep_text and ep_href:
                        episodes.append(f"{ep_text}${ep_href}")
                if episodes:
                    play_from_list.append("播放")
                    play_url_list.append("#".join(episodes))

        # 5. 兜底：直接查找所有 /vodplay/ 链接
        if not play_from_list:
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
        """从HTML中提取m3u8地址 - 更健壮的提取方式"""
        if not html:
            return None
        
        # 方法1: 直接用正则提取 player_aaaa.url
        # 匹配 "url":"https://xxx.m3u8" 或 "url":"https://xxx.m3u8?xxx"
        pattern1 = r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"'
        match1 = re.search(pattern1, html)
        if match1:
            url = match1.group(1)
            if url.startswith("http"):
                return url
        
        # 方法2: 从 player_aaaa 对象中提取（完整解析）
        pattern2 = r'var\s+player_aaaa\s*=\s*(\{[^}]*"url"\s*:\s*"([^"]+)"[^}]*\})'
        match2 = re.search(pattern2, html, re.DOTALL)
        if match2:
            # 直接提取 url 组
            url = match2.group(2)
            if url.startswith("http"):
                return url
            # 尝试 json 解析
            try:
                import json
                # 处理可能的转义
                json_str = match2.group(1)
                data = json.loads(json_str)
                url = data.get("url", "")
                if url and url.startswith("http"):
                    return url
            except:
                pass
        
        # 方法3: 查找任何m3u8链接
        pattern3 = r'https?://[^\s"\']+\.m3u8[^\s"\']*'
        match3 = re.search(pattern3, html)
        if match3:
            return match3.group(0)
        
        # 方法4: 查找 player_data 或其他常见变量
        pattern4 = r'(?:player_data|MacPlayer)\s*\.\s*(?:url|playurl)\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']'
        match4 = re.search(pattern4, html)
        if match4:
            return match4.group(1)
        
        return None
    def _m3u8_proxy_url(self, url):
        """生成m3u8代理地址"""
        if url:
            url = url.replace("\\/", "/")
        return "http://127.0.0.1:9978/proxy?do=py&url=" + urllib.parse.quote(str(url or ""), safe="")