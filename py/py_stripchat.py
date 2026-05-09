# coding=utf-8
#!/usr/bin/env python3
import json
import base64
import hashlib
import re
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

try:
    import requests
except:
    requests = None
try:
    from urllib.request import Request, urlopen
except:
    Request, urlopen = None, None

from base.spider import Spider


class Spider(Spider):
    HOST = "https://zh.stripchat.com"
    ORIGIN = HOST
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
        "Origin": ORIGIN,
        "Referer": f"{ORIGIN}/",
    }
    PREFERRED_VIDEO_CODEC = "H265"

    TAG_MAPPING = {"G": "girls", "C": "couples", "M": "men", "T": "trans"}
    CLASSES = [
        {"type_name": "女主播g", "type_id": "girls"},
        {"type_name": "情侣c", "type_id": "couples"},
        {"type_name": "男主播m", "type_id": "men"},
        {"type_name": "跨性别t", "type_id": "trans"},
    ]

    VALUE_TAGS = (
        {"n": "日本", "v": "tagLanguageJapanese"},
        {"n": "韓國", "v": "tagLanguageKorean"},
        {"n": "中国", "v": "tagLanguageChinese"},
        {"n": "亚洲", "v": "ethnicityAsian"},
        {"n": "白人", "v": "ethnicityWhite"},
        {"n": "拉丁", "v": "ethnicityLatino"},
        {"n": "混血", "v": "ethnicityMultiracial"},
        {"n": "印度", "v": "ethnicityIndian"},
        {"n": "阿拉伯", "v": "ethnicityMiddleEastern"},
        {"n": "黑人", "v": "ethnicityEbony"},
    )
    MEN_TAGS = (
        {"n": "情侣", "v": "sexGayCouples"},
        {"n": "直男", "v": "orientationStraight"},
    )

    URL_PATTERN = re.compile(r"https://media-hls\.doppiocdn\.\w+/b-hls-\d+/media\.mp4")
    M3U8_RESOLUTION_PATTERN = re.compile(r'_(\d+p\d*)\.m3u8')

    def init(self, extend="{}"):
        self.host = self.HOST
        self.headers = self.HEADERS.copy()
        self.stripchat_decrypt_key = self._decode_key_compact(
            "NDUgNTEgNzUgNjUgNjUgNDcgNjggMzIgNmIgNjEgNjUgNzcgNjEgMzMgNjMgNjg="
        )
        self.stripchat_auth_key = self._decode_key_compact(
            "NGYgNmYgNmIgMzcgNzEgNzUgNjEgNjkgNGUgNjcgNjkgNzkgNzUgNjggNjEgNjk="
        )

    def getName(self):
        return "StripChat"

    def isVideoFormat(self, url):
        return "m3u8" in url

    def manualVideoCheck(self):
        return False

    def homeContent(self, filter):
        filters = {}
        for tid in ["girls", "couples", "men", "trans"]:
            filters[tid] = [
                {
                    "key": "tag",
                    "value": (self.MEN_TAGS + self.VALUE_TAGS) 
                    if tid == "men" else self.VALUE_TAGS,
                }
            ]
        return {"class": self.CLASSES, "filters": filters}

    def categoryContent(self, tid, pg, filter, extend):
        limit = 60
        offset = limit * (int(pg) - 1)
        
        url = (
            f"{self.host}/api/front/models?improveTs=false&removeShows=false&"
            f"limit={limit}&offset={offset}&primaryTag={tid}&sortBy=stripRanking&"
            f"rcmGrp=A&rbCnGr=true&prxCnGr=false&nic=false"
        )
        
        if "tag" in extend:
            url = f'{url}&filterGroupTags=[["{extend["tag"]}"]]'
        
        try:
            text = self._get(url)
            if text is None:
                self.log("_get returned None")
                return {"list": [], "page": pg, "pagecount": 1, "limit": limit, "total": 0}
            rsp = json.loads(text)
            self.log(f"parsed json, models count: {len(rsp.get('models', []))}")
        except Exception as e:
            self.log(f"获取分类内容失败: {e}")
            return {"list": [], "page": pg, "pagecount": 1, "limit": limit, "total": 0}
        
        videos = []
        for vod in rsp.get("models", []):
            videos.append(
                {
                    "vod_id": str(vod["username"]).strip(),
                    "vod_name": (
                        f"{self._country_code_to_flag(str(vod['country']).strip())}"
                        f"{str(vod['username']).strip()}"
                    ),
                    "vod_pic": (
                        f"https://img.doppiocdn.net/thumbs/"
                        f"{vod['snapshotTimestamp']}/{vod['id']}"
                    ),
                    "vod_remarks": "" if vod.get("status") == "public" else "🎫",
                }
            )
        
        total = int(rsp.get("filteredCount", 0))
        pagecount = (total + limit - 1) // limit if total > 0 else 1
        
        return {
            "list": videos, "page": pg,
            "pagecount": pagecount, "limit": limit, "total": total,
        }

    def detailContent(self, array):
        username = array[0]
        try:
            text = self._get(f"{self.host}/api/front/v2/models/username/{username}/cam")
            if text is None:
                return {"list": []}
            rsp = json.loads(text)
        except Exception:
            return {"list": []}
        
        info = rsp["cam"]
        user = rsp["user"]["user"]
        user_id = str(user["id"])
        country = str(user["country"]).strip()
        is_live = "" if user.get("isLive", False) else " 已下播"
        flag = self._country_code_to_flag(country)
        
        remark = ""
        start_at = ""
        if show := info.get("show"):
            start_at = show.get("createdAt")
        elif show := info.get("groupShowAnnouncement"):
            start_at = show.get("startAt")
        if start_at:
            try:
                beijing_time = (
                    datetime.strptime(start_at, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)
                ).strftime("%m月%d日 %H:%M")
                remark = f"🎫 始於 {beijing_time}"
            except ValueError:
                pass
        
        return {"list": [{
            "vod_id": user_id,
            "vod_name": str(info["topic"]).strip(),
            "vod_pic": str(user["avatarUrl"]),
            "vod_director": f"{flag}{username}{is_live}",
            "vod_remarks": remark,
            "vod_play_from": "StripChat",
            "vod_play_url": f"{user_id}${user_id}",
        }]}

    def _process_key(self, key: str) -> Tuple[str, str]:
        parts = key.split(maxsplit=1)
        if len(parts) > 1 and (tag := self.TAG_MAPPING.get(parts[0].upper())):
            return tag, parts[1].strip()
        return "girls", key.strip()

    def searchContent(self, key, quick, pg="1"):
        if int(pg) > 1:
            return {"list": []}
        tag, search_key = self._process_key(key)
        try:
            text = self._get(
                f"{self.host}/api/front/v4/models/search/group/username?"
                f"query={search_key}&limit=900&primaryTag={tag}"
            )
            if text is None:
                return {"list": []}
            rsp = json.loads(text)
        except Exception:
            return {"list": []}
        
        result_list = []
        for user in rsp.get("models", []):
            if not user.get("isLive", False):
                continue
            result_list.append(
                {
                    "vod_id": str(user["username"]).strip(),
                    "vod_name": (
                        f"{self._country_code_to_flag(str(user['country']).strip())}"
                        f"{user['username']}"
                    ),
                    "vod_pic": (
                        f"https://img.doppiocdn.net/thumbs/"
                        f"{user['snapshotTimestamp']}/{user['id']}"
                    ),
                    "vod_remarks": "" if user.get("status") == "public" else "🎫",
                }
            )
        return {"list": result_list}

    def playerContent(self, flag, id, vipFlags):
        try:
            text = self._get(f"https://edge-hls.doppiocdn.net/hls/{id}/master/{id}_auto.m3u8?playlistType=lowLatency")
            if text is None:
                return {"url": [], "parse": "0", "contentType": "", "header": self.headers}
            lines = text.strip().split("\n")
        except Exception:
            return {"url": [], "parse": "0", "contentType": "", "header": self.headers}
        
        psch, pkey = "", ""
        url_list = []
        mouflon_processed = False
        
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-MOUFLON:") and not mouflon_processed:
                parts = line.split(":")
                if len(parts) >= 4:
                    psch, pkey = parts[2], parts[3]
                    mouflon_processed = True
            
            if "#EXT-X-STREAM-INF" in line:
                match = re.search(r'NAME="([^"]+)"', line)
                if not match:
                    continue
                qn = match.group(1)
                if i + 1 >= len(lines):
                    continue
                url_base = lines[i + 1]
                full_url = (
                    f"{url_base}&psch={psch}&pkey={pkey}&"
                    f"preferredVideoCodec={self.PREFERRED_VIDEO_CODEC}"
                )
                proxy_url = f"{self.getProxyUrl()}&url={quote(full_url)}"
                url_list.extend([qn, proxy_url])
        
        return {
            "url": url_list, "parse": "0",
            "contentType": "", "header": self.headers,
        }

    def localProxy(self, param):
        url = unquote(param["url"])
        try:
            text = self._get(url)
            if text is None:
                return [404, "text/plain", ""]
            if "Cloudflare" in text or "Attention Required" in text:
                blurred_url = self.M3U8_RESOLUTION_PATTERN.sub(
                    "_160p_blurred.m3u8", url
                )
                text = self._get(blurred_url)
                if text is None:
                    return [404, "text/plain", ""]
            if "#EXT-X-MOUFLON:URI:" in text:
                text = self._process_m3u8(text)
            return [200, "application/vnd.apple.mpegurl", text]
        except Exception as e:
            self.log(f"代理请求失败: {e}")
            return [500, "text/plain", f"Internal Server Error: {e}"]

    def _process_m3u8(self, content: str) -> str:
        lines = content.strip().split("\n")
        for i, line in enumerate(lines):
            if not line.startswith("#EXT-X-MOUFLON:URI:"):
                continue
            if i + 1 >= len(lines) or "media.mp4" not in lines[i + 1]:
                continue
            mouflon = line.split(":", 2)[2].strip()
            encrypted_stripped = re.sub(r"(_part\d+)?\.mp4$", "", mouflon)
            parts = encrypted_stripped.rsplit("_", 2)
            if len(parts) < 2:
                continue
            encrypted = parts[1]
            reversed_encrypted = encrypted[::-1]
            decrypted = self._decrypt(reversed_encrypted, self.stripchat_decrypt_key)
            replacement = mouflon.replace(encrypted, decrypted)
            lines[i + 1] = self.URL_PATTERN.sub(replacement, lines[i + 1])
        return "\n".join(lines)

    @staticmethod
    def _country_code_to_flag(country_code: str) -> str:
        if len(country_code) != 2 or not country_code.isalpha():
            return country_code
        try:
            return "".join(
                chr(ord(c.upper()) - ord("A") + 0x1F1E6) for c in country_code
            )
        except Exception:
            return country_code

    @staticmethod
    def _decode_key_compact(base64_str: str) -> str:
        decoded = base64.b64decode(base64_str).decode("utf-8")
        key_bytes = bytes(int(hex_str, 16) for hex_str in decoded.split(" "))
        return key_bytes.decode("utf-8")

    @lru_cache(maxsize=128)
    def _compute_hash(self, key: str) -> bytes:
        sha256 = hashlib.sha256()
        sha256.update(key.encode("utf-8"))
        return sha256.digest()

    def _decrypt(self, encrypted_b64: str, key: str) -> str:
        padding = len(encrypted_b64) % 4
        if padding:
            encrypted_b64 += "=" * (4 - padding)
        try:
            hash_bytes = self._compute_hash(key)
            encrypted_data = base64.b64decode(encrypted_b64)
            decrypted_bytes = bytearray()
            for i, cipher_byte in enumerate(encrypted_data):
                key_byte = hash_bytes[i % len(hash_bytes)]
                decrypted_bytes.append(cipher_byte ^ key_byte)
            return decrypted_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _get(self, url):
        """请求通道：只用 urllib（requests 被 CF 拦截）"""
        if Request and urlopen:
            try:
                req = Request(url, headers=self.headers)
                with urlopen(req, timeout=10) as resp:
                    data = resp.read().decode("utf-8", errors="ignore")
                    with open("/sdcard/_strip_data.txt", "w") as f:
                        f.write(f"len={len(data)}\nfirst500={data[:500]}")
                    return data
            except Exception as e:
                with open("/sdcard/_strip_data.txt", "w") as f:
                    f.write(f"urllib exception: {e}")
                return None
        return None

    def log(self, message: str):
        print(f"[{self.getName()}] {message}")