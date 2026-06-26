# coding=utf-8
import re
import json
import urllib.request
import urllib.parse
import base64
from base.spider import Spider

BASE = "https://missavt.com"

# AES 解密 Key 和 IV (从 crypto_image.js 提取)
AES_KEY = b'f5d965df75336270'
AES_IV = b'97b60394abc2fbe1'

class Spider(Spider):
    def getName(self):
        return "MissAVt"

    def init(self, extend=""):
        self.site_url = BASE
        self._image_cache = {}
        self._decrypt_cache = {}
        self._og_cache = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": BASE + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

    def getDependence(self):
        return []

    def header(self):
        return self.headers

    def _get(self, url):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return None

    def _get_binary(self, url):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.read()
        except Exception as e:
            return None

    def _fix(self, u):
        if not u:
            return ""
        u = u.strip()
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return BASE + u
        return u

    def _decrypt_aes_cbc(self, encrypted_data):
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
            pad_len = decrypted[-1]
            if pad_len < 1 or pad_len > 16:
                return decrypted
            decrypted = decrypted[:-pad_len]
            return decrypted
        except:
            try:
                from Crypto.Cipher import AES
                from Crypto.Util.Padding import unpad
                cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
                decrypted = cipher.decrypt(encrypted_data)
                try:
                    decrypted = unpad(decrypted, AES.block_size)
                except:
                    pass
                return decrypted
            except:
                return None

    def _decrypt_image_url(self, url):
        if url in self._decrypt_cache:
            return self._decrypt_cache[url]
        if 'pic.nhoqpp.cn' not in url and 'pic.zdpxxq.cn' not in url:
            return url
        encrypted_data = self._get_binary(url)
        if not encrypted_data:
            return url
        decrypted = self._decrypt_aes_cbc(encrypted_data)
        if not decrypted:
            return url
        if decrypted[:2] == b'\xff\xd8':
            mime = 'image/jpeg'
        elif decrypted[:4] == b'\x89PNG':
            mime = 'image/png'
        elif decrypted[:3] == b'GIF':
            mime = 'image/gif'
        else:
            mime = 'image/jpeg'
        b64 = base64.b64encode(decrypted).decode('ascii')
        data_uri = f"data:{mime};base64,{b64}"
        self._decrypt_cache[url] = data_uri
        return data_uri

    def _get_og_image(self, vid):
        if vid in self._og_cache:
            return self._og_cache[vid]
        try:
            url = f"{BASE}/watch/{vid}/"
            html = self._get(url)
            if html:
                m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
                if m:
                    pic = self._fix(m.group(1))
                    self._og_cache[vid] = pic
                    return pic
        except:
            pass
        return ""

    def _parse_list(self, html, max_items=24):
        if not html:
            return []
        results = []
        
        pattern = r'<a[^>]*href="/watch/([^"/]+)/?"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?</a>\s*<a[^>]*[^>]*>([^<]+)</a>'
        matches = list(re.finditer(pattern, html, re.DOTALL))
        
        for idx, m in enumerate(matches[:max_items]):
            vid = m.group(1).strip()
            pic_url = self._fix(m.group(2))
            title = m.group(3).strip()
            
            # 优先使用 og:image（最快，无需解密）
            pic = self._get_og_image(vid)
            
            # 如果 og:image 获取失败，且索引小于8，尝试解密
            if not pic and idx < 8:
                pic = self._decrypt_image_url(pic_url)
            
            # 如果还是失败，使用原始加密URL
            if not pic:
                pic = pic_url
            
            results.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic
            })
        
        if not results:
            pattern2 = r'<a[^>]*href="/watch/([^"/]+)/?"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*>.*?</a>.*?<a[^>]*class="[^"]*line-clamp[^"]*"[^>]*>([^<]+)</a>'
            matches2 = list(re.finditer(pattern2, html, re.DOTALL))
            for idx, m in enumerate(matches2[:max_items]):
                vid = m.group(1).strip()
                pic_url = self._fix(m.group(2))
                title = m.group(3).strip()
                pic = self._get_og_image(vid)
                if not pic and idx < 8:
                    pic = self._decrypt_image_url(pic_url)
                if not pic:
                    pic = pic_url
                results.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": pic
                })
        
        return results

    def homeVideoContent(self):
        return self.homeContent(False)

    def homeContent(self, filter):
        html = self._get(BASE + "/")
        video_list = self._parse_list(html, 24) if html else []
        return {
            "class": [
                {"type_id": "1", "type_name": "推荐视频"},
                {"type_id": "2", "type_name": "热门视频"},
                {"type_id": "3", "type_name": "无码破解"},
                {"type_id": "4", "type_name": "中文字幕"},
                {"type_id": "5", "type_name": "素人"},
            ],
            "list": video_list,
            "filters": {}
        }

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if pg else 1
        type_map = {
            "1": "",
            "2": "/sort/month_hot/",
            "3": "/category/reducing-mosaic/",
            "4": "/category/chinese-subtitle/",
            "5": "/category/amateur/",
        }
        base_path = type_map.get(tid, "")
        if base_path == "":
            url = BASE + "/" if page == 1 else f"{BASE}/?page={page}"
        else:
            url = f"{BASE}{base_path}" if page == 1 else f"{BASE}{base_path.rstrip('/')}/{page}/"
        
        html = self._get(url)
        video_list = self._parse_list(html, 24) if html else []
        pagecount = 50
        if html:
            m = re.search(r'第\d+/(\d+)\s*页', html)
            if m:
                try:
                    pagecount = int(m.group(1))
                except:
                    pass
        return {
            "page": page,
            "pagecount": pagecount,
            "limit": len(video_list),
            "total": pagecount * 20,
            "list": video_list
        }

    def detailContent(self, ids):
        result = {"list": []}
        for vod_id in ids:
            try:
                url = f"{BASE}/watch/{vod_id}/"
                html = self._get(url)
                if not html:
                    continue
                title = ""
                m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
                if m:
                    title = m.group(1).strip()
                if not title:
                    m = re.search(r'<title>([^<]+)</title>', html)
                    if m:
                        title = m.group(1).strip().replace(' - MissAVt', '').replace(' - MissAV', '')
                pic = ""
                m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
                if m:
                    pic = self._fix(m.group(1))
                if not pic:
                    m = re.search(r'<meta[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']', html)
                    if m:
                        pic = self._fix(m.group(1))
                if not pic:
                    m = re.search(r'<xg-poster[^>]*style="background-image:url\(([^)]+)\)"', html)
                    if m:
                        pic = self._fix(m.group(1).strip('"\''))
                play_url = ""
                m = re.search(r'<div[^>]*class="poster"[^>]*data-url="([^"]+)"', html)
                if m:
                    play_url = self._fix(m.group(1))
                if not play_url:
                    m = re.search(r'data-url="([^"]+\.m3u8[^"]*)"', html)
                    if m:
                        play_url = self._fix(m.group(1))
                if not play_url:
                    m = re.search(r'<video[^>]*src="([^"]+)"', html)
                    if m:
                        play_url = self._fix(m.group(1))
                if not play_url:
                    m = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html)
                    if m:
                        play_url = m.group(1)
                play_str = f"默认播放${play_url}" if play_url else f"详情页${url}"
                result["list"].append({
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_play_from": "MissAVt",
                    "vod_play_url": play_str
                })
            except Exception as e:
                continue
        return result

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if pg else 1
        encoded_key = urllib.parse.quote(key)
        url = f"{BASE}/search/{encoded_key}/" if page == 1 else f"{BASE}/search/{encoded_key}/?page={page}"
        html = self._get(url)
        video_list = self._parse_list(html, 24) if html else []
        return {"list": video_list, "page": page, "pagecount": 20}

    def playerContent(self, flag, id, vipFlags):
        return {
            "parse": 0,
            "url": id,
            "header": json.dumps({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": BASE + "/"
            })
        }

    def destroy(self):
        pass