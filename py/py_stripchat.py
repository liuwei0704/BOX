# coding=utf-8
#!/usr/bin/env python3
import base64
import hashlib
import re
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

import requests
from urllib3.util.retry import Retry

from base.spider import Spider


class Spider(Spider):
    # 常量定義
    HOST = "https://zh.stripchat.com"
    ORIGIN = HOST
    HEADERS = {
        "Origin": ORIGIN,
        "Referer": f"{ORIGIN}/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) "
            "Gecko/20100101 Firefox/147.0"
        ),
    }
    PREFERRED_VIDEO_CODEC = "H265"  # 可選 H264、H265

    # 類別映射
    TAG_MAPPING = {"G": "girls", "C": "couples", "M": "men", "T": "trans"}
    CLASSES = [
        {"type_name": "女主播g", "type_id": "girls"},
        {"type_name": "情侣c", "type_id": "couples"},
        {"type_name": "男主播m", "type_id": "men"},
        {"type_name": "跨性别t", "type_id": "trans"},
    ]

    # 標籤配置
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

    # 編譯正則表達式
    URL_PATTERN = re.compile(r"https://media-hls\.doppiocdn\.\w+/b-hls-\d+/media\.mp4")
    M3U8_RESOLUTION_PATTERN = re.compile(r'_(\d+p\d*)\.m3u8')

    def init(self, extend="{}"):
        """初始化爬蟲"""
        self.host = self.HOST
        self.headers = self.HEADERS.copy()
        
        # 解密密鑰
        self.stripchat_decrypt_key = self._decode_key_compact(
            "NDUgNTEgNzUgNjUgNjUgNDcgNjggMzIgNmIgNjEgNjUgNzcgNjEgMzMgNjMgNjg="
        )
        self.stripchat_auth_key = self._decode_key_compact(
            "NGYgNmYgNmIgMzcgNzEgNzUgNjEgNjkgNGUgNjcgNjkgNzkgNzUgNjggNjEgNjk="
        )
        
        # 創建會話
        self._create_session_with_retry()

    def getName(self):
        return "StripChat"

    def isVideoFormat(self, url):
        return "m3u8" in url

    def manualVideoCheck(self):
        return False

    def homeContent(self, filter):
        """首頁內容"""
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
        """分類內容"""
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
            rsp = self.fetch(url).json()
        except Exception as e:
            self.log(f"獲取分類內容失敗: {e}")
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
            "list": videos,
            "page": pg,
            "pagecount": pagecount,
            "limit": limit,
            "total": total,
        }

    def detailContent(self, array):
        """詳情頁內容"""
        username = array[0]
        
        try:
            rsp = self.fetch(
                f"{self.host}/api/front/v2/models/username/{username}/cam"
            ).json()
        except Exception:
            return {"list": []}
        
        info = rsp["cam"]
        user = rsp["user"]["user"]
        user_id = str(user["id"])
        country = str(user["country"]).strip()
        
        is_live = "" if user.get("isLive", False) else " 已下播"
        flag = self._country_code_to_flag(country)
        
        # 處理演出信息
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
        
        vod = {
            "vod_id": user_id,
            "vod_name": str(info["topic"]).strip(),
            "vod_pic": str(user["avatarUrl"]),
            "vod_director": f"{flag}{username}{is_live}",
            "vod_remarks": remark,
            "vod_play_from": "StripChat",
            "vod_play_url": f"{user_id}${user_id}",
        }
        
        return {"list": [vod]}

    def _process_key(self, key: str) -> Tuple[str, str]:
        """處理搜索關鍵詞"""
        parts = key.split(maxsplit=1)
        if len(parts) > 1 and (tag := self.TAG_MAPPING.get(parts[0].upper())):
            return tag, parts[1].strip()
        return "girls", key.strip()

    def searchContent(self, key, quick, pg="1"):
        """搜索內容"""
        if int(pg) > 1:
            return {"list": []}
        
        tag, search_key = self._process_key(key)
        
        try:
            url = (
                f"{self.host}/api/front/v4/models/search/group/username?"
                f"query={search_key}&limit=900&primaryTag={tag}"
            )
            rsp = self.fetch(url).json()
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
        """播放器內容"""
        try:
            url = f"https://edge-hls.doppiocdn.net/hls/{id}/master/{id}_auto.m3u8?playlistType=lowLatency"
            rsp = self.fetch(url)
            lines = rsp.text.strip().split("\n")
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
                # 提取畫質名稱
                match = re.search(r'NAME="([^"]+)"', line)
                if not match:
                    continue
                    
                qn = match.group(1)
                
                # 獲取下一行的URL
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
            "url": url_list,
            "parse": "0",
            "contentType": "",
            "header": self.headers,
        }

    def localProxy(self, param):
        """本地代理"""
        url = unquote(param["url"])
        
        try:
            rsp = self.fetch(url)
            
            # 如果403錯誤，嘗試獲取模糊版本
            if rsp.status_code == 403:
                blurred_url = self.M3U8_RESOLUTION_PATTERN.sub(
                    "_160p_blurred.m3u8", url
                )
                rsp = self.fetch(blurred_url)
            
            if rsp.status_code != 200:
                return [404, "text/plain", ""]
            
            data = rsp.text
            
            # 處理MOUFLON加密
            if "#EXT-X-MOUFLON:URI:" in data:
                data = self._process_m3u8(data)
                
            return [200, "application/vnd.apple.mpegurl", data]
            
        except Exception as e:
            self.log(f"代理請求失敗: {e}")
            return [500, "text/plain", f"Internal Server Error: {e}"]

    def _process_m3u8(self, content: str) -> str:
        """處理M3U8內容，解密加密部分"""
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
        """將國家代碼轉換為旗幟emoji"""
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
        """解碼Base64格式的密鑰"""
        decoded = base64.b64decode(base64_str).decode("utf-8")
        key_bytes = bytes(int(hex_str, 16) for hex_str in decoded.split(" "))
        return key_bytes.decode("utf-8")

    @lru_cache(maxsize=128)
    def _compute_hash(self, key: str) -> bytes:
        """計算SHA-256哈希（帶緩存）"""
        sha256 = hashlib.sha256()
        sha256.update(key.encode("utf-8"))
        return sha256.digest()

    def _decrypt(self, encrypted_b64: str, key: str) -> str:
        """解密數據"""
        # 修復Base64填充
        padding = len(encrypted_b64) % 4
        if padding:
            encrypted_b64 += "=" * (4 - padding)
        
        try:
            # 計算哈希
            hash_bytes = self._compute_hash(key)
            
            # 解碼Base64
            encrypted_data = base64.b64decode(encrypted_b64)
            
            # 異或解密
            decrypted_bytes = bytearray()
            for i, cipher_byte in enumerate(encrypted_data):
                key_byte = hash_bytes[i % len(hash_bytes)]
                decrypted_bytes.append(cipher_byte ^ key_byte)
                
            return decrypted_bytes.decode("utf-8", errors="ignore")
            
        except Exception:
            return ""

    def _create_session_with_retry(self):
        """創建帶重試機制的會話"""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch(self, url: str, **kwargs):
        """發送HTTP請求"""
        headers = kwargs.pop("headers", self.headers)
        timeout = kwargs.pop("timeout", 10)
        
        try:
            return self.session.get(
                url, headers=headers, timeout=timeout, **kwargs
            )
        except requests.exceptions.Timeout:
            self.log(f"請求超時: {url}")
            raise
        except Exception as e:
            self.log(f"請求失敗: {url}, 錯誤: {e}")
            raise

    def log(self, message: str):
        """日誌記錄（可根據需要實現）"""
        print(f"[{self.getName()}] {message}")