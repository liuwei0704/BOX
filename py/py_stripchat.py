# coding=utf-8
import sys, re, base64, hashlib, json, requests, time
from base.spider import Spider
from datetime import datetime, timedelta
from urllib.parse import quote, unquote
from urllib3.util.retry import Retry

sys.path.append('..')


class Spider(Spider):
    def init(self, extend="{}"):
        origin = 'https://zh.stripchat.com'
        self.host = origin
        # 使用 doppiocdn.org 域名，国内可访问
        self.Doppiocdn = "doppiocdn.org"
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
        self.headers = {
            'Origin': origin,
            'Referer': f"{origin}/",
            'User-Agent': user_agent,
            "Accept-Language": "zh,en;q=0.5",
            "Cookie": "isVisitorsAgreementAccepted=1",
        }
        self.stripchat_preferredVideoCodec = "H265"
        self.stripchat_decrypt_key = self.decode_key_compact(
            "NDUgNTEgNzUgNjUgNjUgNDcgNjggMzIgNmIgNjEgNjUgNzcgNjEgMzMgNjMgNjg=")
        self._hash_cache = {}
        self.create_session_with_retry()

    def getName(self):
        return "StripChat"

    def isVideoFormat(self, url):
        return "m3u8" in url

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    def homeVideoContent(self):
        pass

    def homeContent(self, filter):
        CLASSES = [
            {'type_name': '女主播', 'type_id': 'girls'},
            {'type_name': '情侣', 'type_id': 'couples'},
            {'type_name': '男主播', 'type_id': 'men'},
            {'type_name': '跨性别', 'type_id': 'trans'}
        ]
        VALUE = [
            {"n": "日本", "v": "tagLanguageJapanese"},
            {"n": "韓國", "v": "tagLanguageKorean"},
            {'n': '中国', 'v': 'tagLanguageChinese'},
            {'n': '亚洲', 'v': 'ethnicityAsian'},
            {'n': '白人', 'v': 'ethnicityWhite'},
            {'n': '拉丁', 'v': 'ethnicityLatino'},
            {'n': '混血', 'v': 'ethnicityMultiracial'},
            {'n': '印度', 'v': 'ethnicityIndian'},
            {'n': '阿拉伯', 'v': 'ethnicityMiddleEastern'},
            {'n': '黑人', 'v': 'ethnicityEbony'}
        ]
        VALUE_MEN = [
            {'n': '情侣', 'v': 'sexGayCouples'},
            {'n': '直男', 'v': 'orientationStraight'}
        ]
        TIDS = ('girls', 'couples', 'men', 'trans')
        filters = {tid: [{'key': 'tag', 'value': VALUE_MEN + VALUE if tid == 'men' else VALUE}] for tid in TIDS}
        return {'class': CLASSES, 'filters': filters}

    def categoryContent(self, tid, pg, filter, extend):
        limit = 60
        offset = limit * (int(pg) - 1)
        url = f"{self.host}/api/front/models?improveTs=false&removeShows=false&limit={limit}&offset={offset}&primaryTag={tid}&sortBy=stripRanking&rcmGrp=A&rbCnGr=true&prxCnGr=false&nic=false"
        if 'tag' in extend:
            url += f'&filterGroupTags=[["{extend["tag"]}"]]'
        
        try:
            rsp = self.session_get(url).json()
        except Exception as e:
            print(f"category error: {e}")
            return {"list": [], "page": pg, "pagecount": 1}
        
        videos = []
        for v in rsp.get('models', []):
            name = v.get('username', '')
            flag = self.country_code_to_flag(str(v.get('country', '')))
            videos.append({
                "vod_id": name,
                "vod_name": f"{flag}{name}",
                "vod_pic": f"https://img.doppiocdn.com/thumbs/{v.get('snapshotTimestamp', '')}/{v.get('id', '')}",
                "vod_remarks": "" if v.get('status') == "public" else "私密"
            })
        
        total = int(rsp.get('filteredCount', 0))
        pagecount = (total + limit - 1) // limit if total > 0 else 1
        
        return {
            "list": videos,
            "page": pg,
            "pagecount": pagecount,
            "limit": limit,
            "total": total
        }

    def detailContent(self, array):
        username = array[0]
        
        try:
            rsp = self.session_get(f"{self.host}/api/front/v2/models/username/{username}/cam").json()
            info = rsp['cam']
            user = rsp['user']['user']
            uid = str(user['id'])
            isLive = user.get('isLive', False)
            flag = self.country_code_to_flag(str(user.get('country', '')))
            
            remark = "🔴 直播中" if isLive else "⚫ 已下播"
            show = info.get('show') or info.get('groupShowAnnouncement')
            if show:
                startAt = show.get('createdAt') or show.get('startAt')
                if startAt:
                    remark = f"🎫 始于 {(datetime.strptime(startAt, '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)).strftime('%m月%d日 %H:%M')}"
            
            return {'list': [{
                "vod_id": uid,
                "vod_name": str(info.get('topic', ''))[:80],
                "vod_pic": str(user.get('avatarUrl', '')),
                "vod_director": f"{flag}{username}",
                "vod_remarks": remark,
                'vod_play_from': 'StripChat',
                'vod_play_url': f"{uid}${uid}"
            }]}
        except Exception as e:
            print(f"detail error: {e}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        if int(pg) > 1:
            return {"list": []}
        
        tags = {'G': 'girls', 'C': 'couples', 'M': 'men', 'T': 'trans'}
        parts = key.split(maxsplit=1)
        if len(parts) > 1 and parts[0].upper() in tags:
            tag = tags[parts[0].upper()]
            search_key = parts[1].strip()
        else:
            tag = 'girls'
            search_key = key.strip()
        
        try:
            rsp = self.session_get(f"{self.host}/api/front/v4/models/search/group/username?query={search_key}&limit=50&primaryTag={tag}").json()
        except Exception:
            return {"list": []}
        
        videos = []
        for u in rsp.get('models', []):
            if not u.get('isLive'):
                continue
            name = u.get('username', '')
            flag = self.country_code_to_flag(str(u.get('country', '')))
            videos.append({
                "vod_id": name,
                "vod_name": f"{flag}{name}",
                "vod_pic": f"https://img.doppiocdn.com/thumbs/{u.get('snapshotTimestamp', '')}/{u.get('id', '')}",
                "vod_remarks": "" if u.get('status') == "public" else "私密"
            })
        
        return {"list": videos}

    def playerContent(self, flag, id, vipFlags):
        """获取播放地址 - 使用 doppiocdn.org 域名"""
        # 使用 doppiocdn.org（国内可访问）
        master_url = f"https://edge-hls.{self.Doppiocdn}/hls/{id}/master/{id}_auto.m3u8?playlistType=lowLatency"
        
        try:
            rsp = self.session_get(master_url)
            if rsp.status_code != 200:
                return {"url": [], "parse": '0', "header": self.headers}
            content = rsp.text
        except Exception as e:
            print(f"player error: {e}")
            return {"url": [], "parse": '0', "header": self.headers}
        
        lines = content.strip().split('\n')
        psch, pkey = 'v2', 'Ook7quaiNgiyuhai'
        urls = []
        processed = False
        
        for i, line in enumerate(lines):
            # 提取 MOUFLON 参数
            if line.startswith('#EXT-X-MOUFLON:') and not processed:
                parts = line.split(':')
                if len(parts) >= 4:
                    psch = parts[2]
                    pkey = parts[3]
                    processed = True
            
            if '#EXT-X-STREAM-INF' in line and i + 1 < len(lines):
                # 提取清晰度
                qn_start = line.find('NAME="') + 6
                qn_end = line.find('"', qn_start)
                qn = line[qn_start:qn_end] if qn_start > 6 else "auto"
                
                base_url = lines[i + 1]
                if "?" in base_url:
                    full_url = f"{base_url}&psch={psch}&pkey={pkey}&preferredVideoCodec={self.stripchat_preferredVideoCodec}"
                else:
                    full_url = f"{base_url}?psch={psch}&pkey={pkey}&preferredVideoCodec={self.stripchat_preferredVideoCodec}"
                
                # 通过代理获取
                urls.append(qn)
                urls.append(f"{self.getProxyUrl()}&url={quote(full_url)}")
        
        if not urls:
            proxy_url = f"{self.getProxyUrl()}&url={quote(master_url)}"
            urls = ["auto", proxy_url]
        
        headers = self.headers.copy()
        headers.pop('Accept-Language', None)
        
        return {"url": urls, "parse": '0', "header": headers}

    def localProxy(self, param):
        """代理处理 m3u8 请求"""
        url = unquote(param['url'])
        print(f"localProxy: {url[:100]}...")
        
        try:
            rsp = self.session_get(url)
        except Exception as e:
            print(f"proxy request error: {e}")
            return [404, "text/plain", ""]
        
        # 处理 403 错误，尝试模糊分辨率
        if rsp.status_code == 403:
            blurred_url = re.sub(r'(_\d+p\d*)?\.m3u8', '_160p_blurred.m3u8', url)
            try:
                rsp = self.session_get(blurred_url)
            except Exception:
                pass
        
        if rsp.status_code != 200:
            return [404, "text/plain", ""]
        
        # 处理 MOUFLON 加密
        if "#EXT-X-MOUFLON:URI:" in rsp.text:
            data = self.process_m3u8(rsp.text)
        else:
            data = rsp.text
        
        return [200, "application/vnd.apple.mpegurl", data]

    URL_PATTERN = re.compile(r'https://media-hls\.doppiocdn\.\w+/b-hls-\d+/media\.mp4')
    
    def process_m3u8(self, content):
        """处理 MOUFLON 加密的 m3u8"""
        lines = content.strip().split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#EXT-X-MOUFLON:URI:') and i + 1 < len(lines):
                if 'media.mp4' in lines[i + 1]:
                    mouflon = line.split(':', 2)[2].strip()
                    # 提取加密部分
                    encrypted_match = re.search(r'_([a-zA-Z0-9]+)\.mp4$', mouflon)
                    if encrypted_match:
                        encrypted = encrypted_match.group(1)
                        decrypted = self.decrypt(encrypted[::-1], self.stripchat_decrypt_key)
                        if decrypted:
                            new_mouflon = mouflon.replace(encrypted, decrypted)
                            lines[i + 1] = self.URL_PATTERN.sub(new_mouflon, lines[i + 1])
        return '\n'.join(lines)

    def country_code_to_flag(self, code):
        if len(code) != 2 or not code.isalpha():
            return code
        try:
            return ''.join(chr(ord(c.upper()) - ord('A') + 0x1F1E6) for c in code)
        except Exception:
            return code

    def decode_key_compact(self, b64):
        decoded = base64.b64decode(b64).decode()
        key_bytes = bytes(int(h, 16) for h in decoded.split())
        return key_bytes.decode()

    def compute_hash(self, key):
        if key not in self._hash_cache:
            self._hash_cache[key] = hashlib.sha256(key.encode()).digest()
        return self._hash_cache[key]

    def decrypt(self, b64, key):
        b64 += '=' * ((4 - len(b64) % 4) % 4)
        try:
            h = self.compute_hash(key)
            encrypted_data = base64.b64decode(b64)
            decrypted = bytearray()
            for i, b in enumerate(encrypted_data):
                decrypted.append(b ^ h[i % len(h)])
            return decrypted.decode(errors='ignore')
        except Exception:
            return ""

    def create_session_with_retry(self):
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def session_get(self, url, headers=None):
        if headers is None:
            headers = self.headers
        return self.session.get(url, headers=headers, timeout=10)