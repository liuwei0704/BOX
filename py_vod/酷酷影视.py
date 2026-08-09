# coding=utf-8
"""
站点: 酷酷影视
域名: https://www.kukuys.com
类型: HTML影视站
特点: iframe嵌套播放器, 多线路, 分类筛选, JS加密播放器
"""

import re
import json
import time
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup


class Spider(Spider):
    def __init__(self):
        super().__init__()
        self.host = "https://www.kukuys.com"
        self.player_host = "https://player.kukuys6.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": self.host,
        }
        self.timeout = 20
        # 分类列表 - 硬编码零网络依赖
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "5", "type_name": "动作片"},
            {"type_id": "6", "type_name": "喜剧片"},
            {"type_id": "7", "type_name": "爱情片"},
            {"type_id": "8", "type_name": "科幻片"},
            {"type_id": "9", "type_name": "恐怖片"},
            {"type_id": "10", "type_name": "剧情片"},
            {"type_id": "11", "type_name": "战争片"},
            {"type_id": "12", "type_name": "国产剧"},
            {"type_id": "13", "type_name": "香港剧"},
            {"type_id": "14", "type_name": "韩国剧"},
            {"type_id": "15", "type_name": "欧美剧"},
            {"type_id": "16", "type_name": "台湾剧"},
            {"type_id": "17", "type_name": "日本剧"},
            {"type_id": "18", "type_name": "海外剧"},
            {"type_id": "19", "type_name": "微电影"},
            {"type_id": "20", "type_name": "好看视频"},
            {"type_id": "21", "type_name": "福利片"},
        ]
        self.filters = {}
        self._home_cache = None

    def getName(self):
        return "酷酷影视"

    def init(self, extend=""):
        pass

    def header(self):
        return self.headers.copy()

    def _fetch(self, url, params=None, timeout=None):
        """封装请求，支持params参数"""
        if timeout is None:
            timeout = self.timeout
        if params:
            # 构建完整URL
            if '?' in url:
                sep = '&'
            else:
                sep = '?'
            url = url + sep + "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        return self.fetch(url, headers=self.header(), timeout=timeout)

    def _get_home_cache(self):
        """获取首页缓存数据"""
        if self._home_cache is None:
            try:
                rsp = self._fetch(self.host)
                if rsp and rsp.status_code == 200:
                    self._home_cache = rsp.text
            except Exception:
                pass
        return self._home_cache

    def _parse_video_items(self, html, limit=0):
        """通用视频列表解析"""
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        videos = []
        seen_ids = set()

        items = soup.select(".pic a.link, .pic a, .aclcon1 .iul li a.link, .paaContainer a")
        for a in items:
            try:
                href = a.get("href", "")
                if not href or "/v/" not in href:
                    continue
                vid_match = re.search(r"/v/(\d+)\.html", href)
                if not vid_match:
                    continue
                vid = vid_match.group(1)
                if vid in seen_ids:
                    continue

                img = a.find("img")
                pic = ""
                if img:
                    pic = img.get("data-original") or img.get("src", "")
                    if pic and pic.startswith("//"):
                        pic = "https:" + pic
                    elif pic and pic.startswith("/") and not pic.startswith("//"):
                        pic = self.host + pic

                name = img.get("alt", "") if img else ""
                if not name:
                    name = a.get("title", "")

                remark = ""
                state_span = a.select_one(".state .zt")
                if state_span:
                    remark = state_span.text.strip()
                if not remark:
                    parent = a.parent
                    for _ in range(2):
                        if not parent:
                            break
                        for tag in parent.find_all(["span", "em", "font"]):
                            t = tag.get_text(strip=True)
                            if t and any(k in t for k in ["集", "完", "HD", "蓝光", "期", "更新", "暂无"]):
                                remark = t
                                break
                        if remark:
                            break
                        parent = parent.parent

                seen_ids.add(vid)
                videos.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": remark,
                })
                if limit and len(videos) >= limit:
                    break
            except Exception:
                continue
        return videos

    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐"""
        html = self._get_home_cache()
        if html:
            videos = self._parse_video_items(html)
            return {"list": videos[:40]}
        return {"list": []}

    def categoryContent(self, tid, pg, filter=False, extend=""):
        """分类列表 - 使用首页数据作为降级"""
        pg = int(pg) if pg else 1
        result = {"list": [], "page": pg, "pagecount": 1, "limit": 20, "total": 0}

        try:
            # 尝试获取分类页
            if pg <= 1:
                url = f"{self.host}/p2/{tid}-1--time-----.html"
            else:
                url = f"{self.host}/p2/{tid}-{pg}--time-----.html"

            rsp = self._fetch(url)
            if rsp and rsp.status_code == 200 and rsp.text and "验证" not in rsp.text:
                videos = self._parse_video_items(rsp.text)
                if videos:
                    result["list"] = videos
                    # 提取页数
                    pg_nums = re.findall(rf'/{tid}-(\d+)--time', rsp.text)
                    if pg_nums:
                        result["pagecount"] = max([int(n) for n in pg_nums]) + 1
                    else:
                        result["pagecount"] = pg + 1
                    result["total"] = len(videos) * result["pagecount"]
                    return result
        except Exception:
            pass

        # 降级：使用首页数据
        html = self._get_home_cache()
        if html:
            all_videos = self._parse_video_items(html)
            start = (pg - 1) * 20
            end = start + 20
            page_items = all_videos[start:end] if start < len(all_videos) else []
            result["list"] = page_items
            result["pagecount"] = 2 if len(all_videos) > 20 else 1
            result["total"] = len(all_videos)

        return result

    def detailContent(self, ids):
        """详情页"""
        result = {"list": []}
        try:
            vid = ids[0] if ids else ""
            if not vid:
                return result

            url = f"{self.host}/v/{vid}.html"
            rsp = self._fetch(url)
            if not rsp or rsp.status_code != 200:
                return result

            soup = BeautifulSoup(rsp.text, "html.parser")

            # 标题
            name = ""
            h1 = soup.find("h1")
            if h1:
                name = h1.get_text(strip=True)
                name = re.sub(r"\s*\(\d{4}\)\s*", "", name)

            # 封面
            pic = ""
            img = soup.select_one(".pic-hb .img img.lazy")
            if img:
                pic = img.get("data-original") or img.get("src", "")
            if not pic:
                meta_img = soup.find("meta", property="og:image")
                if meta_img:
                    pic = meta_img.get("content", "")
            if pic and pic.startswith("//"):
                pic = "https:" + pic

            # 简介
            content = ""
            desc_elem = soup.find("meta", property="og:description")
            if desc_elem:
                content = desc_elem.get("content", "")

            # 基本信息
            year = ""
            area = ""
            actor = ""
            director = ""
            remarks = ""

            info_dl = soup.select(".info dl")
            for dl in info_dl:
                for dd in dl.find_all("dd"):
                    text = dd.get_text(strip=True)
                    if "状态：" in text:
                        remarks = text.replace("状态：", "").strip()
                    elif "主演：" in text:
                        actor = text.replace("主演：", "").strip()
                    elif "导演：" in text:
                        director = text.replace("导演：", "").strip()
                    elif "年份：" in text:
                        year = text.replace("年份：", "").strip()
                    elif "地区：" in text:
                        area = text.replace("地区：", "").strip()

            if not year:
                meta_year = soup.find("meta", property="og:video:release_date")
                if meta_year:
                    year = meta_year.get("content", "")
            if not area:
                meta_area = soup.find("meta", property="og:video:area")
                if meta_area:
                    area = meta_area.get("content", "")

            # 解析线路和剧集
            play_from_list = []
            play_url_list = []

            tab_items = soup.select(".playfrom li")
            playlist_divs = soup.select('div[id^="stab1"]')

            for i, div in enumerate(playlist_divs):
                from_name = f"线路{i+1}"
                if i < len(tab_items):
                    from_name = tab_items[i].get_text(strip=True)
                    from_name = re.sub(r"\d+$", "", from_name).strip()

                links = div.find_all("a", href=re.compile(r"/play/"))
                episodes = []
                for link in links:
                    ep_title = link.get_text(strip=True)
                    ep_url = link.get("href", "")
                    if ep_title and ep_url:
                        if ep_url.startswith("//"):
                            ep_url = "https:" + ep_url
                        elif ep_url.startswith("/"):
                            ep_url = self.host + ep_url
                        episodes.append(f"{ep_title}${ep_url}")

                if episodes:
                    play_from_list.append(from_name)
                    play_url_list.append("#".join(episodes))

            # 备用提取
            if not play_from_list:
                play_links = soup.find_all("a", href=re.compile(r"/play/"))
                if play_links:
                    episodes = []
                    for link in play_links:
                        ep_title = link.get_text(strip=True)
                        ep_url = link.get("href", "")
                        if ep_title and ep_url:
                            if ep_url.startswith("//"):
                                ep_url = "https:" + ep_url
                            elif ep_url.startswith("/"):
                                ep_url = self.host + ep_url
                            episodes.append(f"{ep_title}${ep_url}")
                    if episodes:
                        play_from_list = ["默认线路"]
                        play_url_list = ["#".join(episodes)]

            video = {
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "vod_content": content,
                "vod_year": year,
                "vod_area": area,
                "vod_actor": actor,
                "vod_director": director,
                "vod_remarks": remarks,
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list),
            }
            result["list"] = [video]
        except Exception:
            pass
        return result

    def searchContent(self, key, quick=False, pg=1):
        """搜索 - 使用首页数据匹配降级"""
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}
        try:
            keyword = urllib.parse.quote(key)
            if int(pg) <= 1:
                url = f"{self.host}/vod-search-wd-{keyword}.html"
            else:
                url = f"{self.host}/vod-search-wd-{keyword}-{pg}.html"

            rsp = self._fetch(url)
            if rsp and rsp.status_code == 200 and rsp.text and "验证" not in rsp.text:
                videos = self._parse_video_items(rsp.text)
                if videos:
                    result["list"] = videos
                    pg_nums = re.findall(r'-wd-[\w%]+-(\d+)\.html', rsp.text)
                    if pg_nums:
                        result["pagecount"] = max([int(n) for n in pg_nums]) + 1
                    else:
                        result["pagecount"] = int(pg) + 1
                    result["total"] = len(videos) * result["pagecount"]
                    return result
        except Exception:
            pass

        # 降级：从首页数据中匹配关键词
        html = self._get_home_cache()
        if html:
            all_videos = self._parse_video_items(html)
            matched = []
            key_lower = key.lower()
            for item in all_videos:
                if key_lower in item.get("vod_name", "").lower():
                    matched.append(item)
            start = (int(pg) - 1) * 20
            end = start + 20
            result["list"] = matched[start:end] if start < len(matched) else []
            result["pagecount"] = 1 if len(matched) <= 20 else 2
            result["total"] = len(matched)

        return result

    def playerContent(self, flag, play_id, vipFlags):
        """解析播放地址 - 优先提取播放器页面地址"""
        result = {"parse": 1, "url": "", "header": {}}

        try:
            if not play_id:
                return result

            # 构建完整播放URL
            if play_id.startswith("//"):
                play_url = "https:" + play_id
            elif play_id.startswith("/"):
                play_url = self.host + play_id
            elif play_id.startswith("http"):
                play_url = play_id
            else:
                play_url = self.host + "/" + play_id

            # 方法1: 直接检查是否为m3u8/mp4直链
            if '.m3u8' in play_url.lower() or '.mp4' in play_url.lower():
                result["parse"] = 0
                result["url"] = play_url
                result["header"] = self._video_header()
                return result

            # 方法2: 尝试提取iframe中的播放器地址
            try:
                import re
                rsp = self.fetch(play_url, headers=self.header(), timeout=self.timeout)
                if rsp and rsp.status_code == 200 and rsp.text:
                    html = rsp.text
                    # 查找iframe
                    iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
                    if iframe_match:
                        player_src = iframe_match.group(1)
                        if player_src.startswith("//"):
                            player_src = "https:" + player_src
                        elif player_src.startswith("/"):
                            player_src = self.host + player_src
                        # 返回播放器页面地址
                        result["parse"] = 1
                        result["url"] = player_src
                        result["header"] = self._video_header()
                        return result
            except Exception:
                pass

            # 方法3: 直接返回播放页地址
            result["parse"] = 1
            result["url"] = play_url
            result["header"] = self._video_header()

        except Exception:
            result["parse"] = 1
            result["url"] = play_id if play_id else ""
            result["header"] = self._video_header()

        return result
    def _video_header(self):
        """纯净播放请求头 - 参考91PORN"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }

    def _extract_play_url(self, play_url):
        """从播放页提取播放地址 - 使用self.fetch替代requests"""
        try:
            import re

            # 使用self.fetch获取播放页
            rsp = self.fetch(play_url, headers=self.header(), timeout=self.timeout)
            if not rsp or rsp.status_code != 200:
                return None
            html = rsp.text
            if not html:
                return None

            # 层级1: 直接搜索m3u8
            m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html, re.IGNORECASE)
            if m3u8_match:
                return m3u8_match.group(1)

            # 层级2: 从iframe中提取播放器地址
            iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if iframe_match:
                player_src = iframe_match.group(1)
                if player_src.startswith("//"):
                    player_src = "https:" + player_src
                elif player_src.startswith("/"):
                    player_src = self.host + player_src

                # 如果iframe直接是m3u8
                if '.m3u8' in player_src.lower():
                    return player_src

                # 访问播放器页面
                try:
                    player_rsp = self.fetch(player_src, headers=self.header(), timeout=self.timeout)
                    if player_rsp and player_rsp.status_code == 200 and player_rsp.text:
                        player_html = player_rsp.text
                        # 在播放器页面搜索m3u8
                        m3u8_in_player = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', player_html, re.IGNORECASE)
                        if m3u8_in_player:
                            return m3u8_in_player.group(1)
                        # 尝试解密播放器数据
                        decrypted = self._decrypt_player_html(player_html)
                        if decrypted and '.m3u8' in decrypted:
                            return decrypted
                except Exception:
                    pass

            # 层级3: 从script中提取
            scripts = re.findall(r'<script[^>]*>([^<]+)</script>', html, re.IGNORECASE | re.DOTALL)
            for script in scripts:
                m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', script, re.IGNORECASE)
                if m3u8_match:
                    return m3u8_match.group(1)

            return None
        except Exception:
            return None
    def _decrypt_player_html(self, html):
        """解密播放器数据 - 参考91PORN的解密模式"""
        try:
            import re
            import json
            import time
            import urllib.parse
            from Crypto.Cipher import AES

            # 提取raw_key和encrypted
            key_match = re.search(r'var raw_key = \[([^\]]+)\]', html)
            if not key_match:
                return None
            raw_key = [int(x.strip()) for x in key_match.group(1).split(',')]
            key_bytes = bytes(raw_key)

            enc_match = re.search(r'var encrypted = "([^"]+)"', html)
            if not enc_match:
                return None
            encrypted_hex = enc_match.group(1)

            # AES-CBC解密
            ciphertext = bytes.fromhex(encrypted_hex)
            iv = ciphertext[:16]
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv)
            decrypted_bytes = cipher.decrypt(ciphertext[16:])

            # 去除PKCS7填充
            pad_len = decrypted_bytes[-1]
            if 1 <= pad_len <= 16:
                decrypted_bytes = decrypted_bytes[:-pad_len]
            decrypted = decrypted_bytes.decode('utf-8', errors='ignore')

            # 从解密数据中提取API参数
            token_match = re.search(r"var token = '([^']+)'", decrypted)
            token = token_match.group(1) if token_match else ""

            if not token:
                return None

            # 提取其他参数
            uid_match = re.search(r"var videouid = '([^']+)'", decrypted)
            videouid = uid_match.group(1) if uid_match else ""

            danmu_match = re.search(r"var videodanmuid = '([^']+)'", decrypted)
            videodanmuid = danmu_match.group(1) if danmu_match else ""

            vfkey_match = re.search(r"var videovfkey = '([^']+)'", decrypted)
            videovfkey = vfkey_match.group(1) if vfkey_match else ""

            # 从decrypted中尝试提取id
            # 有些站点把id埋在decrypted中
            id_match = re.search(r'getUrlParam\("id"\)', decrypted)
            if not id_match:
                # 尝试从token中提取id信息
                # token可能包含id
                import base64
                try:
                    decoded_token = base64.b64decode(token).decode('utf-8', errors='ignore')
                    id_from_token = re.search(r'id=([^&]+)', decoded_token)
                    if id_from_token:
                        encrypted_id = id_from_token.group(1)
                    else:
                        encrypted_id = ''
                except:
                    encrypted_id = ''
            else:
                encrypted_id = ''

            if not encrypted_id:
                return None

            # 构建API请求
            api_url = "https://player.kukuys6.com/newid/apii.php"
            api_params = {
                'token': token,
                'id': encrypted_id,
                'name': '',
                'sid': '',
                'uid': videouid,
                'danmuid': videodanmuid,
                'vfkey': videovfkey,
                '_t': str(int(time.time() * 1000))
            }

            import requests
            api_full_url = api_url + "?" + "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in api_params.items()])

            api_rsp = requests.get(api_full_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            if api_rsp.status_code == 200 and api_rsp.text:
                data = json.loads(api_rsp.text)
                if data.get('msg') == '200' and data.get('url'):
                    video_url = data['url']
                    m3u8_match = re.search(r'url=([^&]+)', video_url)
                    if m3u8_match:
                        m3u8_url = urllib.parse.unquote(m3u8_match.group(1))
                        if '.m3u8' in m3u8_url:
                            return m3u8_url

            return None
        except Exception:
            return None
    def _decrypt_with_requests(self, html):
        """使用requests完整解密播放器数据"""
        try:
            import re
            import json
            import time
            import urllib.parse
            from Crypto.Cipher import AES

            # 提取raw_key和encrypted
            key_match = re.search(r'var raw_key = \[([^\]]+)\]', html)
            if not key_match:
                return None
            raw_key = [int(x.strip()) for x in key_match.group(1).split(',')]
            key_bytes = bytes(raw_key)

            enc_match = re.search(r'var encrypted = "([^"]+)"', html)
            if not enc_match:
                return None
            encrypted_hex = enc_match.group(1)

            # AES-CBC解密
            ciphertext = bytes.fromhex(encrypted_hex)
            iv = ciphertext[:16]
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv)
            decrypted_bytes = cipher.decrypt(ciphertext[16:])

            # 去除PKCS7填充
            pad_len = decrypted_bytes[-1]
            if 1 <= pad_len <= 16:
                decrypted_bytes = decrypted_bytes[:-pad_len]
            decrypted = decrypted_bytes.decode('utf-8', errors='ignore')

            # 提取API参数
            token_match = re.search(r"var token = '([^']+)'", decrypted)
            token = token_match.group(1) if token_match else ""

            uid_match = re.search(r"var videouid = '([^']+)'", decrypted)
            videouid = uid_match.group(1) if uid_match else ""

            danmu_match = re.search(r"var videodanmuid = '([^']+)'", decrypted)
            videodanmuid = danmu_match.group(1) if danmu_match else ""

            vfkey_match = re.search(r"var videovfkey = '([^']+)'", decrypted)
            videovfkey = vfkey_match.group(1) if vfkey_match else ""

            # 从decrypted中提取encryptedId
            enc_id_match = re.search(r"var encryptedUrl = getUrlParam\('id'\)", decrypted)
            if not enc_id_match:
                return None

            if not token:
                return None

            # 从URL参数获取id - 从原始播放页URL提取
            # 由于无法直接获取，尝试从decrypted中搜索
            id_match = re.search(r'getUrlParam\("id"\)', decrypted)
            if not id_match:
                return None

            # 实际上需要从播放页URL获取id参数
            # 这里用另一种方式：从decrypted中搜索可能的id
            # 但更可靠的是从播放页URL中提取
            import urllib.parse as urlparse
            # 从调用方传入的play_url中提取id
            # 但这个函数接收的是播放器页面HTML，没有URL
            # 所以需要重构成传入url参数

            return None
        except Exception:
            return None
    def _extract_direct_url(self, play_url):
        """从播放页提取m3u8直链 - 参考44ggjj的简洁风格"""
        try:
            import re
            import json
            import time
            import urllib.parse

            # 获取播放器页面
            rsp = self.fetch(play_url, headers=self.header(), timeout=self.timeout)
            if not rsp or rsp.status_code != 200:
                return None
            html = rsp.text
            if not html or len(html) < 100:
                return None

            # 方法1: 直接查找iframe中的播放器地址
            iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if iframe_match:
                player_src = iframe_match.group(1)
                # 如果是直接播放地址
                if '.m3u8' in player_src or '.mp4' in player_src:
                    return player_src
                # 如果是播放器页面，尝试从播放器页面提取m3u8
                if 'player.' in player_src or 'newid' in player_src:
                    # 尝试直接返回播放器页面地址（交给壳端处理）
                    # 但先尝试从播放器页面提取m3u8
                    player_rsp = self.fetch(player_src, headers=self.header(), timeout=self.timeout)
                    if player_rsp and player_rsp.status_code == 200 and player_rsp.text:
                        # 尝试在播放器页面中查找m3u8
                        m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', player_rsp.text)
                        if m3u8_match:
                            return m3u8_match.group(1)
                        # 尝试查找加密数据并解密
                        encrypted_url = self._decrypt_player_data(player_rsp.text)
                        if encrypted_url and '.m3u8' in encrypted_url:
                            return encrypted_url

            # 方法2: 直接在HTML中查找m3u8
            m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
            if m3u8_match:
                return m3u8_match.group(1)

            # 方法3: 在script中查找
            scripts = re.findall(r'<script[^>]*>([^<]+)</script>', html, re.IGNORECASE | re.DOTALL)
            for script in scripts:
                if '.m3u8' in script:
                    m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', script)
                    if m3u8_match:
                        return m3u8_match.group(1)

            return None
        except Exception:
            return None

    def _decrypt_player_data(self, html):
        """解密播放器数据 - 参考44ggjj的ENC2风格但适用于当前站点"""
        try:
            import re
            import json
            import time
            import urllib.parse
            from Crypto.Cipher import AES

            # 提取raw_key和encrypted
            key_match = re.search(r'var raw_key = \[([^\]]+)\]', html)
            if not key_match:
                return None
            raw_key = [int(x.strip()) for x in key_match.group(1).split(',')]
            key_bytes = bytes(raw_key)

            enc_match = re.search(r'var encrypted = "([^"]+)"', html)
            if not enc_match:
                return None
            encrypted_hex = enc_match.group(1)

            # AES-CBC解密
            ciphertext = bytes.fromhex(encrypted_hex)
            iv = ciphertext[:16]
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv)
            decrypted_bytes = cipher.decrypt(ciphertext[16:])

            # 去除PKCS7填充
            pad_len = decrypted_bytes[-1]
            if 1 <= pad_len <= 16:
                decrypted_bytes = decrypted_bytes[:-pad_len]
            decrypted = decrypted_bytes.decode('utf-8', errors='ignore')

            # 提取API参数
            token_match = re.search(r"var token = '([^']+)'", decrypted)
            token = token_match.group(1) if token_match else ""

            uid_match = re.search(r"var videouid = '([^']+)'", decrypted)
            videouid = uid_match.group(1) if uid_match else ""

            danmu_match = re.search(r"var videodanmuid = '([^']+)'", decrypted)
            videodanmuid = danmu_match.group(1) if danmu_match else ""

            vfkey_match = re.search(r"var videovfkey = '([^']+)'", decrypted)
            videovfkey = vfkey_match.group(1) if vfkey_match else ""

            if not token:
                return None

            # 从URL获取参数
            parsed = urllib.parse.urlparse(html)
            # 实际上参数在播放页URL中，需要从外部传入
            # 这里简化处理：尝试从decrypted中提取encryptedUrl
            enc_url_match = re.search(r"var encryptedUrl = getUrlParam\('id'\);\s*var videoName = getUrlParam\('name'\)", decrypted)
            # 从全局上下文获取id
            # 由于无法获取原始URL，这里尝试从decrypted中提取
            id_match = re.search(r"getUrlParam\('id'\)", decrypted)
            if not id_match:
                return None

            # 构建API请求
            api_url = "https://player.kukuys6.com/newid/apii.php"
            api_params = {
                'token': token,
                'id': '',  # 需要从外部传入
                'name': '',
                'sid': '',
                'uid': videouid,
                'danmuid': videodanmuid,
                'vfkey': videovfkey,
                '_t': str(int(time.time() * 1000))
            }

            # 由于无法获取完整参数，返回None让调用方降级
            return None
        except Exception:
            return None
    def _extract_m3u8(self, play_url):
        """从播放页提取m3u8直链"""
        try:
            import re
            import json
            import time
            import urllib.parse

            # 获取播放器页面
            rsp = self.fetch(play_url, headers=self.header(), timeout=self.timeout)
            if not rsp or rsp.status_code != 200:
                return None
            html = rsp.text
            if not html or len(html) < 100:
                return None

            # 1. 提取raw_key和encrypted
            key_match = re.search(r'var raw_key = \[([^\]]+)\]', html)
            if not key_match:
                return None
            raw_key = [int(x.strip()) for x in key_match.group(1).split(',')]
            key_bytes = bytes(raw_key)

            enc_match = re.search(r'var encrypted = "([^"]+)"', html)
            if not enc_match:
                return None
            encrypted_hex = enc_match.group(1)

            # AES-CBC解密
            from Crypto.Cipher import AES
            ciphertext = bytes.fromhex(encrypted_hex)
            iv = ciphertext[:16]
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv)
            decrypted_bytes = cipher.decrypt(ciphertext[16:])

            # 手动去除PKCS7填充
            pad_len = decrypted_bytes[-1]
            if 1 <= pad_len <= 16:
                decrypted_bytes = decrypted_bytes[:-pad_len]
            decrypted = decrypted_bytes.decode('utf-8', errors='ignore')

            # 2. 提取API参数
            token_match = re.search(r"var token = '([^']+)'", decrypted)
            token = token_match.group(1) if token_match else ""

            uid_match = re.search(r"var videouid = '([^']+)'", decrypted)
            videouid = uid_match.group(1) if uid_match else ""

            danmu_match = re.search(r"var videodanmuid = '([^']+)'", decrypted)
            videodanmuid = danmu_match.group(1) if danmu_match else ""

            vfkey_match = re.search(r"var videovfkey = '([^']+)'", decrypted)
            videovfkey = vfkey_match.group(1) if vfkey_match else ""

            # 从URL提取参数
            parsed = urllib.parse.urlparse(play_url)
            params = urllib.parse.parse_qs(parsed.query)
            encrypted_id = params.get('id', [''])[0]
            video_name = params.get('name', [''])[0]
            video_sid = params.get('num', [''])[0]

            if not token or not encrypted_id:
                return None

            # 3. 请求API
            api_url = "https://player.kukuys6.com/newid/apii.php"
            api_params = {
                'token': token,
                'id': encrypted_id,
                'name': video_name,
                'sid': video_sid,
                'uid': videouid,
                'danmuid': videodanmuid,
                'vfkey': videovfkey,
                '_t': str(int(time.time() * 1000))
            }

            # 构建完整API URL
            api_full_url = api_url + "?" + "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in api_params.items()])

            api_rsp = self.fetch(api_full_url, headers=self.header(), timeout=self.timeout)
            if api_rsp and api_rsp.status_code == 200 and api_rsp.text:
                data = json.loads(api_rsp.text)
                if data.get('msg') == '200' and data.get('url'):
                    video_url = data['url']
                    m3u8_match = re.search(r'url=([^&]+)', video_url)
                    if m3u8_match:
                        m3u8_url = urllib.parse.unquote(m3u8_match.group(1))
                        if '.m3u8' in m3u8_url:
                            return m3u8_url

            return None
        except Exception:
            return None

    def localProxy(self, params):
        return [200, "video/MP2T", ""]

    def destroy(self):
        pass