import json
import re
from base.spider import Spider
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

class Spider(Spider):
    def __init__(self):
        self.host = "https://2z9q8w7j0x2.shop"
        self.name = "笔盒"
        self.aes_key = bytes.fromhex("f6322fa1c064370ea40c8cdc20649f8e")
        self.aes_iv = bytes.fromhex("f6322fa1c064370ea40c8cdc20649f8e")
        self.classes = [
            {"type_id": "1", "type_name": "首页推荐"},
            {"type_id": "2", "type_name": "最新视频"},
            {"type_id": "3", "type_name": "笔盒APP精选"},
            {"type_id": "4", "type_name": "AI系列"},
            {"type_id": "5", "type_name": "调教骚货小学妹"},
            {"type_id": "6", "type_name": "操翻童颜巨乳女友"},
            {"type_id": "7", "type_name": "无套抽插极品嫩逼"},
            {"type_id": "8", "type_name": "继姐妹骚逼诱惑"},
            {"type_id": "9", "type_name": "哄骗玩弄萝莉妹"},
            {"type_id": "10", "type_name": "女上位全自动榨精"},
            {"type_id": "11", "type_name": "反差黑丝母狗"},
            {"type_id": "12", "type_name": "精选AV"}
        ]
        self.filters = {}
        self._play_cache = {}
        self._source_cache = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.host + "/"
        }
        
        self.search_keywords = {
            "4": "AI",
            "1": "最新视频",
            "2": "最新视频",
            "3": "笔盒APP精选"
        }
        
    def init(self, extend=""):
        pass
        
    def getName(self):
        return self.name
        
    def homeContent(self, filter=False):
        return {"class": self.classes, "filters": self.filters}
    
    def getHomeContent(self, filter=False):
        return self.homeContent(filter)
    
    def homeVideoContent(self):
        return self.categoryContent(tid="2", pg="1")
    
    def _aes_decrypt(self, hex_str):
        try:
            ciphertext = bytes.fromhex(hex_str)
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
            decrypted = cipher.decrypt(ciphertext)
            decrypted = unpad(decrypted, AES.block_size)
            return decrypted.decode('utf-8', errors='ignore')
        except Exception as e:
            return None
    
    def _parse_decrypted(self, text):
        if not text:
            return None
        start = re.search(r'[{\[]', text)
        if start:
            text = text[start.start():]
        try:
            return json.loads(text)
        except:
            return None
    
    def _api(self, path):
        url = self.host + path
        try:
            resp = self.fetch(url)
            if resp.status_code == 200:
                return resp.json()
            return None
        except:
            return None
    
    def _get_detail_data(self, vid):
        data = self._api(f"/api/vod/detail/{vid}")
        if not data or data.get("code") != 200:
            return None
        encrypted = data.get("data")
        if not encrypted:
            return None
        decrypted_text = self._aes_decrypt(encrypted)
        if not decrypted_text:
            return None
        return self._parse_decrypted(decrypted_text)
    
    def _get_category_data(self, keyword, page, limit=20):
        path = f"/api/vod/search?keyword={keyword}&page={page}&limit={limit}"
        data = self._api(path)
        if data and data.get("code") == 200:
            encrypted = data.get("data")
            if encrypted:
                decrypted_text = self._aes_decrypt(encrypted)
                if decrypted_text:
                    result = self._parse_decrypted(decrypted_text)
                    if result and (result.get("list") or result.get("data")):
                        return result
        return None
    
    def categoryContent(self, tid, pg, filter=False, extend=""):
        try:
            page = int(pg) if pg else 1
            class_map = {c["type_id"]: c["type_name"] for c in self.classes}
            keyword = class_map.get(str(tid), "")
            
            if not keyword:
                return {"list": []}
            
            search_key = self.search_keywords.get(str(tid), keyword)
            result = self._get_category_data(search_key, page)
            if not result:
                return {"list": []}
            
            total_pages = result.get("totalPages", 1)
            if total_pages < 1:
                total_pages = 1
            
            items_data = result.get("list", result.get("data", []))
            items = []
            for v in items_data:
                pic = v.get("vodPic", "")
                if pic and pic.endswith('.txt'):
                    pic = "https://via.placeholder.com/400x225?text=Video"
                items.append({
                    "vod_id": v.get("vodId", ""),
                    "vod_name": v.get("vodName", ""),
                    "vod_pic": pic if pic.startswith('http') else "https://via.placeholder.com/400x225?text=Video",
                    "vod_remarks": v.get("vodClass", [""])[0] if v.get("vodClass") else ""
                })
            
            return {
                "list": items,
                "page": page,
                "pagecount": total_pages,
                "total": result.get("total", len(items_data)),
                "limit": 20
            }
        except Exception as e:
            return {"list": []}
    
    def detailContent(self, ids):
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            result = self._get_detail_data(vid)
            if not result:
                return {"list": []}
            
            play_source = result.get("vodPlaySource")
            
            play_from = []
            play_url = []
            play_cache = {}
            
            pic = result.get("vodPic", "")
            if pic and pic.endswith('.txt'):
                pic = "https://via.placeholder.com/400x225?text=Video"
            
            if play_source and isinstance(play_source, dict):
                for src_name, items in play_source.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                source = item.get("from") or item.get("source") or src_name
                                url = item.get("url") or item.get("playUrl") or ""
                                need_parse = item.get("needParse", False)
                                
                                if need_parse:
                                    # 需要解析的播放源，直接使用详情页URL让WebView处理
                                    play_from.append(source + "(解析)")
                                    play_url.append(source + "$" + f"{self.host}/vods/{vid}")
                                    play_cache[source] = f"{self.host}/vods/{vid}"
                                    self._source_cache[source] = vid
                                elif url and url.startswith("http"):
                                    play_from.append(source)
                                    play_url.append(source + "$" + url)
                                    play_cache[source] = url
                                    self._source_cache[source] = vid
            
            if not play_url:
                direct_url = result.get("playUrl") or result.get("url") or result.get("play_url")
                if direct_url and direct_url.startswith("http"):
                    play_from.append("直链")
                    play_url.append("直链$" + direct_url)
                    play_cache["直链"] = direct_url
                    self._source_cache["直链"] = vid
            
            self._play_cache[vid] = play_cache
            
            return {
                "list": [{
                    "vod_id": vid,
                    "vod_name": result.get("vodName", ""),
                    "vod_pic": pic,
                    "vod_play_from": "$$$".join(play_from) if play_from else "直链",
                    "vod_play_url": "$$$".join(play_url) if play_url else f"直链${self.host}/vods/{vid}",
                    "vod_content": result.get("vodDesc", "")
                }]
            }
        except Exception as e:
            return {"list": []}
    
    def searchContent(self, key, quick=False, pg="1"):
        try:
            page = int(pg) if pg else 1
            data = self._api(f"/api/vod/search?keyword={key}&page={page}&limit=20")
            if not data or data.get("code") != 200:
                return {"list": []}
            encrypted = data.get("data")
            if not encrypted:
                return {"list": []}
            decrypted_text = self._aes_decrypt(encrypted)
            if not decrypted_text:
                return {"list": []}
            result = self._parse_decrypted(decrypted_text)
            if not result:
                return {"list": []}
            
            total_pages = result.get("totalPages", 1)
            if total_pages < 1:
                total_pages = 1
            
            if result and ("list" in result or "data" in result):
                items_data = result.get("list", result.get("data", []))
                items = []
                for v in items_data:
                    pic = v.get("vodPic", "")
                    if pic and pic.endswith('.txt'):
                        pic = "https://via.placeholder.com/400x225?text=Video"
                    items.append({
                        "vod_id": v.get("vodId", ""),
                        "vod_name": v.get("vodName", ""),
                        "vod_pic": pic if pic.startswith('http') else "https://via.placeholder.com/400x225?text=Video",
                        "vod_remarks": v.get("vodClass", [""])[0] if v.get("vodClass") else ""
                    })
                return {
                    "list": items, 
                    "page": page, 
                    "pagecount": total_pages,
                    "limit": 20,
                    "total": result.get("total", len(items_data))
                }
            return {"list": []}
        except:
            return {"list": []}
    
    def playerContent(self, ids, flag="", extend=""):
        try:
            # TVBox调用: flag=播放源名称, ids=播放地址
            # 优先使用ids（播放地址）
            play_url = ids if isinstance(ids, str) else (ids[0] if ids else "")
            
            # 如果flag是完整的URL，也尝试
            if not play_url or not play_url.startswith("http"):
                if flag and flag.startswith("http"):
                    play_url = flag
            
            # 如果ids是URL格式
            if play_url and play_url.startswith("http"):
                # 如果是m3u8/mp4直链，直接播放
                if ".m3u8" in play_url or ".mp4" in play_url or ".ts" in play_url:
                    return {"parse": 0, "url": play_url, "header": self.headers}
                # 否则让WebView去处理
                return {"parse": 1, "url": play_url, "header": self.headers}
            
            # 如果ids是播放源名称，从缓存查找
            source = ids if isinstance(ids, str) else (ids[0] if ids else "")
            if source and source in self._source_cache:
                vid = self._source_cache[source]
                if vid in self._play_cache:
                    cache = self._play_cache[vid]
                    if source in cache:
                        url = cache[source]
                        if ".m3u8" in url or ".mp4" in url or ".ts" in url:
                            return {"parse": 0, "url": url, "header": self.headers}
                        return {"parse": 1, "url": url, "header": self.headers}
            
            # 默认降级
            return {
                "parse": 1,
                "url": f"{self.host}/vods/{source}" if source else self.host + "/home",
                "header": self.headers
            }
        except Exception as e:
            return {"parse": 1, "url": self.host + "/home"}
    
    def siteInfo(self):
        return {
            "site": self.name,
            "host": self.host,
            "version": "1.0.0",
            "description": "笔盒 - 成人影视聚合站"
        }