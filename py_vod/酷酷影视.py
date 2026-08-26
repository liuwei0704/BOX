# coding=utf-8
"""
站点: 酷酷影视
域名: https://www.kukuys.com
类型: HTML影视站 + 加密播放器
"""

import re
import json
import time
import base64
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup
from Crypto.Cipher import AES


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
        if timeout is None:
            timeout = self.timeout
        if params:
            if '?' in url:
                sep = '&'
            else:
                sep = '?'
            url = url + sep + "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        return self.fetch(url, headers=self.header(), timeout=timeout)

    def _get_home_cache(self):
        if self._home_cache is None:
            try:
                rsp = self._fetch(self.host)
                if rsp and rsp.status_code == 200:
                    self._home_cache = rsp.text
            except Exception:
                pass
        return self._home_cache

    def _parse_video_items(self, html, limit=0):
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
                videos.append({"vod_id": vid, "vod_name": name, "vod_pic": pic, "vod_remarks": remark})
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
        html = self._get_home_cache()
        if html:
            videos = self._parse_video_items(html)
            return {"list": videos[:40]}
        return {"list": []}

    def categoryContent(self, tid, pg, filter=False, extend=""):
        pg = int(pg) if pg else 1
        result = {"list": [], "page": pg, "pagecount": 1, "limit": 20, "total": 0}
        try:
            if pg <= 1:
                url = f"{self.host}/p2/{tid}-1--time-----.html"
            else:
                url = f"{self.host}/p2/{tid}-{pg}--time-----.html"
            rsp = self._fetch(url)
            if rsp and rsp.status_code == 200 and rsp.text and "验证" not in rsp.text:
                videos = self._parse_video_items(rsp.text)
                if videos:
                    result["list"] = videos
                    pg_nums = re.findall(rf'/{tid}-(\d+)--time', rsp.text)
                    if pg_nums:
                        result["pagecount"] = max([int(n) for n in pg_nums]) + 1
                    else:
                        result["pagecount"] = pg + 1
                    result["total"] = len(videos) * result["pagecount"]
                    return result
        except Exception:
            pass
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
            name = ""
            h1 = soup.find("h1")
            if h1:
                name = h1.get_text(strip=True)
                name = re.sub(r"\s*\(\d{4}\)\s*", "", name)
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
            content = ""
            desc_elem = soup.find("meta", property="og:description")
            if desc_elem:
                content = desc_elem.get("content", "")
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
        result = {"parse": 1, "url": "", "header": self.header()}
        try:
            if not play_id:
                return result
            if play_id.startswith("//"):
                play_url = "https:" + play_id
            elif play_id.startswith("/"):
                play_url = self.host + play_id
            elif play_id.startswith("http"):
                play_url = play_id
            else:
                play_url = self.host + "/" + play_id
            # 尝试提取直链
            m3u8_url = self._extract_m3u8(play_url)
            if m3u8_url:
                result["parse"] = 0
                result["url"] = m3u8_url
                result["header"] = {"User-Agent": "Mozilla/5.0"}
                return result
            # 降级：返回播放器页面地址
            iframe_url = self._extract_iframe(play_url)
            if iframe_url:
                result["parse"] = 1
                result["url"] = iframe_url
                result["header"] = {"User-Agent": "Mozilla/5.0"}
                return result
            result["parse"] = 1
            result["url"] = play_url
            result["header"] = {"User-Agent": "Mozilla/5.0"}
        except Exception:
            result["parse"] = 1
            result["url"] = play_id if play_id else ""
            result["header"] = {"User-Agent": "Mozilla/5.0"}
        return result

    def _extract_iframe(self, play_url):
        """提取iframe地址"""
        try:
            rsp = self.fetch(play_url, headers=self.header(), timeout=self.timeout)
            if not rsp or rsp.status_code != 200:
                return None
            html = rsp.text
            iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if iframe_match:
                src = iframe_match.group(1)
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = self.host + src
                return src
            return None
        except Exception:
            return None

    def _extract_m3u8(self, play_url):
        """完整解密提取m3u8"""
        try:
            # 获取播放页
            rsp = self.fetch(play_url, headers=self.header(), timeout=self.timeout)
            if not rsp or rsp.status_code != 200:
                return None
            html = rsp.text
            if not html:
                return None
            # 直接搜索m3u8
            m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html, re.IGNORECASE)
            if m3u8_match:
                return m3u8_match.group(1)
            # 提取iframe
            iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not iframe_match:
                return None
            player_src = iframe_match.group(1)
            if player_src.startswith("//"):
                player_src = "https:" + player_src
            elif player_src.startswith("/"):
                player_src = self.host + player_src
            if '.m3u8' in player_src.lower():
                return player_src
            # 访问播放器页面
            player_rsp = self.fetch(player_src, headers=self.header(), timeout=self.timeout)
            if not player_rsp or player_rsp.status_code != 200:
                return None
            player_html = player_rsp.text
            # 在播放器页面搜索m3u8
            m3u8_in_player = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', player_html, re.IGNORECASE)
            if m3u8_in_player:
                return m3u8_in_player.group(1)
            # === 完整解密 ===
            key_match = re.search(r'var raw_key = \[([^\]]+)\]', player_html)
            if not key_match:
                return None
            raw_key = [int(x.strip()) for x in key_match.group(1).split(',')]
            key_bytes = bytes(raw_key)
            enc_match = re.search(r'var encrypted = "([^"]+)"', player_html)
            if not enc_match:
                return None
            encrypted_hex = enc_match.group(1)
            ciphertext = bytes.fromhex(encrypted_hex)
            iv = ciphertext[:16]
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv)
            decrypted_bytes = cipher.decrypt(ciphertext[16:])
            pad_len = decrypted_bytes[-1]
            if 1 <= pad_len <= 16:
                decrypted_bytes = decrypted_bytes[:-pad_len]
            decrypted = decrypted_bytes.decode('utf-8', errors='ignore')
            token_match = re.search(r"var token = '([^']+)'", decrypted)
            if not token_match:
                return None
            token = token_match.group(1)
            uid_match = re.search(r"var videouid = '([^']+)'", decrypted)
            videouid = uid_match.group(1) if uid_match else ""
            danmu_match = re.search(r"var videodanmuid = '([^']+)'", decrypted)
            videodanmuid = danmu_match.group(1) if danmu_match else ""
            vfkey_match = re.search(r"var videovfkey = '([^']+)'", decrypted)
            videovfkey = vfkey_match.group(1) if vfkey_match else ""
            parsed = urllib.parse.urlparse(player_src)
            params = urllib.parse.parse_qs(parsed.query)
            encrypted_id = params.get('id', [''])[0]
            video_name = params.get('name', [''])[0]
            video_sid = params.get('num', [''])[0]
            if not encrypted_id:
                try:
                    decoded_token = base64.b64decode(token).decode('utf-8', errors='ignore')
                    id_match = re.search(r'id=([^&]+)', decoded_token)
                    if id_match:
                        encrypted_id = id_match.group(1)
                except:
                    pass
            if not encrypted_id:
                return None
            api_url = "https://player.kukuys6.com/newid/apii.php"
            api_params = {
                'token': token,
                'id': encrypted_id,
                'name': video_name or '未知',
                'sid': video_sid or '1',
                'uid': videouid,
                'danmuid': videodanmuid,
                'vfkey': videovfkey,
                '_t': str(int(time.time() * 1000))
            }
            api_full_url = api_url + "?" + "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in api_params.items()])
            api_rsp = self.fetch(api_full_url, headers=self.header(), timeout=self.timeout)
            if not api_rsp or api_rsp.status_code != 200:
                return None
            data = json.loads(api_rsp.text)
            if data.get('msg') == '200' and data.get('url'):
                video_url = data['url']
                m3u8_match2 = re.search(r'url=([^&]+)', video_url)
                if m3u8_match2:
                    m3u8_url = urllib.parse.unquote(m3u8_match2.group(1))
                    if '.m3u8' in m3u8_url:
                        return m3u8_url
            return None
        except Exception:
            return None

    def localProxy(self, params):
        return [200, "video/MP2T", ""]

    def destroy(self):
        pass