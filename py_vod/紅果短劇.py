# coding=utf-8
# GuoGuo 爬虫 - 融合8个Java类
# 来源: GuoGuo.java, GuoGuoClient.java, GuoGuoPlay.java,
#        GuoGuoCenc.java, GuoGuoProxy.java, GuoGuoSession.java,
#        GuoGuoSignClient.java, GuoGuoNative.java
#
# 数据来源: 番茄小说(novelread)短剧平台 API
# X-Gorgon 和 spade_a (CENC key) 均在本地计算, 无外部签名服务依赖

import base64
import gzip
import hashlib
import json
import os
import re
import secrets
import tempfile
import threading
import time
import uuid
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urljoin, urlparse
from os.path import getsize as _os_path_getsize, exists as _os_path_exists
from os.path import join as _os_path_join
from os import makedirs as _os_makedirs


# ==================== 流式代理 Server (模块级, 独立于 Spider 实例) ====================
#   - 已解密缓存文件按 Range 读取
#   - 首播按 Range 回源，只解密当前 MP4 sample
#   - 起本地 ThreadingHTTPServer，避免大字节数组经过 TVBox 框架
#
# ExoPlayer 行为: 首次请求 bytes=0- 拉头部 (moov), 然后多次拉 sample 区间
# Range 请求通常 256KB ~ 1MB, 每次几毫秒就完成, 不会触发 8s 超时.

_GUOGUO_STREAM_HTTP = None  # 全局句柄, 避免 GC
_JAVA_AES_CIPHER = None
_JAVA_AES_SECRET_KEY = None
_JAVA_AES_IV = None
_JAVA_AES_UNAVAILABLE = False
_JAVA_AES_INIT_LOCK = threading.Lock()
_PY_AES = None
_PY_COUNTER = None
_PY_AES_UNAVAILABLE = False
_PY_AES_INIT_LOCK = threading.Lock()
_AES_BACKEND_LOGGED = False


def _is_cancel_requested(cancel_check):
    try:
        return bool(cancel_check is not None and cancel_check())
    except Exception:
        return False


class _GuoGuoStreamHandler(BaseHTTPRequestHandler):
    """处理 /stream/<token> 的 HTTP Range 请求"""

    protocol_version = "HTTP/1.1"

    def do_HEAD(self):
        self._serve(True)

    def do_GET(self):
        self._serve(False)

    def _serve(self, head_only):
        try:
            # 解析 token
            path = urlparse(self.path).path
            token = path.rsplit("/", 1)[-1].strip()
            if not token:
                self.send_error(404, "missing token")
                return

            # 从 Spider 类取 item
            item = Spider._stream_resolve(token)
            if not item:
                self.send_error(404, "token expired")
                return

            if not head_only:
                self._start_next_episode_prefetch(item)

            if item.get("mode") == "partial":
                self._serve_partial(item, head_only)
                return

            file_path = item.get("path", "")
            try:
                total = _os_path_getsize(file_path)
            except Exception:
                self.send_error(404, "file missing")
                return

            mime = item.get("mime", "video/mp4")
            requested = self._parse_range(self.headers.get("Range"), total)

            if requested == "invalid":
                self.send_response(416)
                self.send_header("Content-Range", "bytes */%d" % total)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            if requested:
                start, end = requested
                self.send_response(206)
                self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, total))
            else:
                start, end = 0, total - 1
                self.send_response(200)

            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()

            if head_only:
                return

            # 按 chunk 读取磁盘, 阻塞写给客户端
            chunk = 1024 * 1024
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    to_read = min(chunk, remaining)
                    buf = f.read(to_read)
                    if not buf:
                        break
                    self.wfile.write(buf)
                    self.wfile.flush()
                    remaining -= len(buf)
        except (BrokenPipeError, ConnectionResetError):
            # 客户端断开是正常情况
            pass
        except Exception as e:
            print("echo-GuoGuo流式 响应失败:", e)
            try:
                self.send_error(500, str(e))
            except Exception:
                pass

    @staticmethod
    def _start_next_episode_prefetch(item):
        spider = item.get("spider")
        next_vid = item.get("prefetch_vid", "")
        if spider is None or not next_vid:
            return
        generation = item.get("prefetch_generation", 0)
        if not spider._is_play_request_current(generation):
            return
        with Spider._STREAM_ITEMS_LOCK:
            if item.get("prefetch_started"):
                return
            item["prefetch_started"] = True
        spider._prefetch_next_episode(next_vid, item.get("prefetch_quality", ""), generation)

    def _serve_partial(self, item, head_only):
        """按播放器 Range 回源并按 sample 解密，不等待整部 MP4。"""
        spider = item.get("spider")
        if spider is None:
            self.send_error(404, "stream expired")
            return
        meta = spider._load_partial_meta(item.get("url", ""), item.get("key", ""))
        total = int(meta.get("total", 0))
        if total <= 0:
            raise Exception("invalid stream length")
        range_value = self.headers.get("Range")
        requested = spider._parse_player_range(range_value, total, spider._PARTIAL_RANGE_MAX)
        if requested == "invalid":
            self.send_response(416)
            self.send_header("Content-Range", "bytes */%d" % total)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        stream_from_position = False
        if requested:
            start, end = requested
            # IJK 对首个 206 小 Range 可能读完后不再发起下一次请求。
            # 从 0 开始时改为完整 200 响应，正文仍按小段回源并连续写出。
            if start == 0:
                end = total - 1
                status = 200
            else:
                raw_range = str(range_value)[6:].split(",", 1)[0].strip()
                _, range_sep, range_right = raw_range.partition("-")
                stream_from_position = bool(range_sep and not range_right.strip())
                if stream_from_position:
                    end = total - 1
                status = 206
        else:
            # ExoPlayer 首次 position=0、length=未知时通常不会携带 Range。
            # 此处必须保留 200/完整 Content-Length，但正文按小段持续写出。
            start, end, status = 0, total - 1, 200

        if head_only:
            self.send_response(status)
            if status == 206:
                self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, total))
            self.send_header("Content-Type", item.get("mime", "video/mp4"))
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            return

        if status == 200 or stream_from_position:
            first_end = min(end, self._partial_chunk_end(spider, start))
            try:
                first_body = spider._partial_transform_range(meta, start, first_end)
            except Exception as e:
                print("echo-GuoGuo流式 首段失败，回退整段: %s" % e)
                clear = spider._load_clear(item.get("url", ""), item.get("key", ""))
                if not clear or len(clear) < total:
                    raise Exception("fallback clear data unavailable")
                first_body = bytes(clear)

            self.send_response(status)
            if status == 206:
                self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, total))
            self.send_header("Content-Type", item.get("mime", "video/mp4"))
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(first_body)
            self.wfile.flush()
            if len(first_body) >= total:
                return

            offset = first_end + 1
            while offset < total:
                part_end = min(total - 1, self._partial_chunk_end(spider, offset))
                try:
                    body = spider._partial_transform_range(meta, offset, part_end)
                except Exception as e:
                    # 首段已经送达，后续 Range 失败只补齐剩余明文，避免提前中断。
                    print("echo-GuoGuo流式 后续分段失败，回退整段: %s" % e)
                    clear = spider._load_clear(item.get("url", ""), item.get("key", ""))
                    if not clear or len(clear) < total:
                        raise Exception("fallback clear data unavailable")
                    body = bytes(clear[offset:])
                    self.wfile.write(body)
                    self.wfile.flush()
                    return
                self.wfile.write(body)
                self.wfile.flush()
                offset = part_end + 1
            return

        try:
            body = spider._partial_transform_range(meta, start, end)
        except Exception as e:
            # 只有 CDN Range/索引异常才退回旧整段方案，正常播放不会走这里。
            print("echo-GuoGuo流式 分段失败，回退整段: %s" % e)
            clear = spider._load_clear(item.get("url", ""), item.get("key", ""))
            if not clear or len(clear) < end + 1:
                raise Exception("fallback clear data unavailable")
            body = bytes(clear[start:end + 1])

        self.send_response(status)
        if status == 206:
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, total))
        self.send_header("Content-Type", item.get("mime", "video/mp4"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        chunk = 256 * 1024
        for offset in range(0, len(body), chunk):
            self.wfile.write(body[offset:offset + chunk])
        self.wfile.flush()

    @staticmethod
    def _partial_chunk_end(spider, start):
        return start + max(1, int(spider._PARTIAL_RANGE_MAX)) - 1

    @staticmethod
    def _parse_range(value, total):
        """解析 Range 头"""
        if not value or not value.lower().startswith("bytes="):
            return None
        value = value[6:].split(",", 1)[0].strip()
        left, _, right = value.partition("-")
        if not left:
            # suffix range: bytes=-N (取最后 N 字节)
            size = min(total, int(right))
            return total - size, total - 1
        start = int(left)
        end = int(right) if right else total - 1
        if start >= total or start < 0:
            return "invalid"
        return start, min(end, total - 1)

    def log_message(self, fmt, *args):
        pass


# ==================== 本地 X-Gorgon (移植自红果 liushen xgorgon.py) ====================
# 直接本地计算 X-Gorgon, 不走任何外部签名服务.

def _local_xgorgon_rc4(data, key):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    result = bytearray(len(data))
    for k, v in enumerate(data):
        i = (i + 1) & 0xff
        x = S[i]
        j = (j + x) & 0xff
        y = S[j]
        S[i] = y
        result[k] = v ^ S[(y + y) & 0xff]
    return bytes(result)


def _local_xgorgon_reverse_bits(num):
    bin_num = bin(num)[2:].zfill(8)
    return int(bin_num[::-1], 2)


def _local_md5_hex(data, data_type=None):
    """等价于 flurl.header.xssstub_hash_md5_hex, 始终返回大写 hex"""
    if not data:
        return ""
    if data_type == "md5":
        return data.upper() if isinstance(data, str) else data
    md5 = hashlib.md5()
    if isinstance(data, str):
        md5.update(data.encode("utf-8"))
    elif isinstance(data, (bytes, bytearray)):
        md5.update(bytes(data))
    elif data_type == "application/json; charset=UTF-8":
        md5.update(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    else:
        md5.update(urllib.parse.urlencode(data).encode("utf-8"))
    return md5.hexdigest().upper()


# 固定 seed: 84 04 (gorgon_84), 参考红果 liushen
_GORGON_84 = bytes([0x4a, 0x16, 0x47, 0x6c, 0x84, 0x04])


def local_encrypt_gorgon(body, query, khronos, xg_rand, data_type=None):
    """本地计算 X-Gorgon.

    入参:
      body: str (POST body, 通常是 JSON 字符串) 或 bytes
      query: str (URL query 字符串, 不含 ?)
      khronos: int (服务器时间戳)
      xg_rand: int (2字节随机数, 0-65535)
      data_type: str ('application/json; charset=UTF-8' 等)
    返回: 52 字符 hex 字符串
    """
    xg_seed = 320
    body_md5 = _local_md5_hex(body, data_type).lower() if body else ""
    data = hashlib.md5(query.encode("utf-8")).digest()[:4]
    if body_md5:
        data += bytes.fromhex(body_md5)[:4]
    else:
        data += b"\x00\x00\x00\x00"
    data += b"\x00\x00\x00\x00"
    mssdk_version_int = 67503104
    data += mssdk_version_int.to_bytes(4, "little")
    data += khronos.to_bytes(4, "big")
    key = bytes([
        _GORGON_84[0],
        xg_seed & 0xff,
        _GORGON_84[1],
        (xg_rand >> 8) & 0xff,
        _GORGON_84[2],
        _GORGON_84[3],
        (xg_seed >> 8) & 0xff,
        xg_rand & 0xff,
    ])
    out = bytearray(_local_xgorgon_rc4(data, key))
    for i in range(len(out)):
        a = out[i]
        out[i] = (a >> 4 | (a << 4)) & 0xFF
        a = out[i + 1] if i + 1 < len(out) else out[0]
        a ^= out[i]
        a = _local_xgorgon_reverse_bits(a)
        out[i] = (~(a ^ 20)) & 0xFF
    ret = _GORGON_84[-2:]
    ret += xg_rand.to_bytes(2, "little")
    ret += xg_seed.to_bytes(2, "little")
    ret += bytes(out)
    return ret.hex()


def local_sign_request(query, body_md5_hex, cookie, khronos):
    """返回 {x_gorgon, x_khronos}.

    body_md5_hex: 已计算的 body md5 (大写), 通常调用方传入.
    """
    import random
    xg_rand = random.randint(0, 0xFFFF)
    x_gorgon = local_encrypt_gorgon(
        body=body_md5_hex or "",
        query=query or "",
        khronos=int(khronos),
        xg_rand=xg_rand,
        data_type="md5",
    )
    return {
        "x_gorgon": x_gorgon,
        "x_khronos": str(int(khronos)),
    }


# 签名服务兜底 (HMAC-SHA256). 当本地 X-Gorgon 被视频播放接口拒绝时回退.
_HMAC_KEY = bytes([
    0x20, 0x36, 0x11, 0xe7, 0xfb, 0xb5, 0x3a, 0x20,
    0xb5, 0xe8, 0x71, 0x64, 0xea, 0x59, 0xdf, 0xb7,
    0x50, 0x5d, 0x40, 0x32, 0xeb, 0x5f, 0x81, 0x0f,
    0x68, 0x27, 0x67, 0x6f, 0x40, 0xcd, 0xd8, 0xcc,
])
_SIGN_HOST = "https://jk.catvod.site/jk/hg"
_APP_ID = "guoguo-t4"


def _remote_sign(path, body_str):
    """调用签名服务 /v1/sign, 拿到 {x_gorgon, x_khronos}. 仅作本地 X-Gorgon 被拒时的兜底."""
    import hmac as hmac_mod
    import uuid
    body_bytes = body_str.encode("utf-8")
    ts = int(time.time())
    nonce = str(uuid.uuid4())
    data_hash = hashlib.sha256(body_bytes).hexdigest()
    message = f"POST|{path}|{data_hash}|{ts}|{nonce}".encode("utf-8")
    sign = hmac_mod.new(_HMAC_KEY, message, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-App-Id": _APP_ID,
        "X-App-Ts": str(ts),
        "X-App-Nonce": nonce,
        "X-App-Sign": sign,
    }
    try:
        req = urllib.request.Request(_SIGN_HOST + path, data=body_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        raise Exception("sign service " + path + ": " + str(e))
    obj = json.loads(raw) if raw else {}
    if "error" in obj:
        raise Exception("sign service " + path + ": " + str(obj.get("error", "")))
    return obj


from base.spider import Spider


class Spider(Spider):
    """GuoGuo - 番茄短剧聚合爬虫, 融合8个Java类"""

    # ==================== 常量 (来自 GuoGuo.java) ====================

    FALLBACK_FLAGS = ["1080P", "720P", "480P", "360P"]
    CLASSES = [
        ["short_play", "短剧"],
        ["comic_series", "漫剧"],
        ["ai_series", "AI短剧"],
        ["rank", "排行榜"],
        ["recommend", "热搜推荐"],
    ]
    HOME_SEEDS = ["霸总", "重生", "战神", "神医", "甜宠", "穿越", "闪婚", "复仇"]

    # ==================== 流式代理 Server ====================
    # 已缓存视频读磁盘；首次视频通过本地 HTTP 按 Range 回源并解密 sample。
    _STREAM_ITEMS = {}
    _STREAM_ITEMS_LOCK = threading.Lock()
    _STREAM_SERVER = None
    _STREAM_SERVER_LOCK = threading.Lock()
    _STREAM_CHUNK = 1024 * 1024
    _STREAM_TTL = 1800

    @classmethod
    def _stream_register(cls, file_path, mime="video/mp4", spider=None,
                         prefetch_vid="", prefetch_quality="", prefetch_generation=0):
        """注册磁盘上的视频文件, 返回 http://127.0.0.1:PORT/stream/<token> URL"""
        with cls._STREAM_ITEMS_LOCK:
            cls._stream_cleanup_locked()
            token = secrets.token_urlsafe(18)
            cls._STREAM_ITEMS[token] = {
                "path": file_path,
                "mime": mime,
                "size": _os_path_getsize(file_path) if _os_path_exists(file_path) else 0,
                "used": time.time(),
                "spider": spider,
                "prefetch_vid": prefetch_vid,
                "prefetch_quality": prefetch_quality,
                "prefetch_generation": prefetch_generation,
            }
        port = cls._stream_ensure_server()
        return "http://127.0.0.1:%d/stream/%s" % (port, token)

    @classmethod
    def _stream_register_partial(cls, spider, url, key, mime="video/mp4",
                                 prefetch_vid="", prefetch_quality="", prefetch_generation=0):
        """注册按 Range 回源的 CENC 视频，不等待完整 MP4 下载。"""
        with cls._STREAM_ITEMS_LOCK:
            cls._stream_cleanup_locked()
            token = secrets.token_urlsafe(18)
            cls._STREAM_ITEMS[token] = {
                "mode": "partial",
                "spider": spider,
                "url": url,
                "key": key,
                "mime": mime,
                "used": time.time(),
                "prefetch_vid": prefetch_vid,
                "prefetch_quality": prefetch_quality,
                "prefetch_generation": prefetch_generation,
            }
        port = cls._stream_ensure_server()
        return "http://127.0.0.1:%d/stream/%s" % (port, token)

    @classmethod
    def _stream_cleanup_locked(cls):
        now = time.time()
        expired = [k for k, v in cls._STREAM_ITEMS.items()
                   if now - v.get("used", now) > cls._STREAM_TTL]
        for k in expired:
            try:
                cls._STREAM_ITEMS.pop(k, None)
            except Exception:
                pass

    @classmethod
    def _stream_ensure_server(cls):
        global _GUOGUO_STREAM_HTTP
        with cls._STREAM_SERVER_LOCK:
            if cls._STREAM_SERVER is None:
                srv = ThreadingHTTPServer(("127.0.0.1", 0), _GuoGuoStreamHandler)
                t = threading.Thread(target=srv.serve_forever, name="GuoGuoStreamServer", daemon=True)
                t.start()
                cls._STREAM_SERVER = srv
                _GUOGUO_STREAM_HTTP = srv
                print("echo-GuoGuo流式 启动 port=%d" % srv.server_address[1])
        return cls._STREAM_SERVER.server_address[1]

    @classmethod
    def _stream_resolve(cls, token):
        with cls._STREAM_ITEMS_LOCK:
            item = cls._STREAM_ITEMS.get(token)
            if item:
                item["used"] = time.time()
            return item

    # ==================== 常量 (来自 GuoGuoClient.java) ====================

    AID = "8662"
    APP_NAME = "novelread"
    VERSION_CODE = "72732"
    VERSION_NAME = "7.2.7.32"
    RANK_CELL_ID = "7470092475068071998"
    RANK_PAGE_SIZE = 10
    SERIES_CACHE_MAX = 800

    BASES = [
        "https://api5-normal-sinfonlineb.fqnovel.com",
        "https://api5-normal.fqnovel.com",
        "https://api5-normal-sinfonlinec.fqnovel.com",
        "https://reading.snssdk.com",
    ]

    CELL_CHANGE = "/reading/bookapi/bookmall/cell/change/v:version/"
    CUE = "/reading/bookapi/search/cue/v"
    LAND = "/reading/distribution/category/landpage/v1/"
    LANDING = "/reading/bookapi/search/schema_landing/v"
    WEB_SEARCH = "https://hongguoduanju.com/search/"

    # ==================== 常量 (来自 GuoGuoPlay.java) ====================

    DETAIL_PATH = "/novel/player/video_detail/v1/"
    VM_PATH = "/novel/player/video_model/v1/"
    MULTI_VM_PATH = "/novel/player/multi_video_model/player/v1"
    PLAY_HOSTS = [
        "https://api5-normal.fqnovel.com",
        "https://api5-normal-sinfonlineb.fqnovel.com",
        "https://api5-normal-sinfonlinec.fqnovel.com",
    ]

    # ==================== 常量 (来自 GuoGuoProxy.java) ====================

    PROXY_UA = "Mozilla/5.0 (Linux; Android 12; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"

    # ==================== 常量 (来自 GuoGuoCenc.java) ====================

    CENC_CONTAINERS = {"moov", "trak", "mdia", "minf", "stbl", "sinf", "schi"}

    # ==================== 类级缓存 ====================

    _SERIES_CACHE = {}
    _SERIES_CACHE_LOCK = threading.Lock()
    _PROXY_CACHE = {}
    _PROXY_CACHE_LOCK = threading.Lock()
    _PROXY_TOKENS = {}
    _PROXY_TOKENS_LOCK = threading.Lock()

    _GLOBAL_PROXY_CACHE = {}
    _GLOBAL_PROXY_CACHE_LOCK = threading.Lock()
    _PROXY_LOAD_LOCKS = {}
    _PROXY_LOAD_LOCKS_LOCK = threading.Lock()
    _PROXY_PREFETCH_THREADS = {}
    _PROXY_PREFETCH_LOCK = threading.Lock()
    _NEXT_EPISODE_CACHE = {}
    _NEXT_EPISODE_CACHE_LOCK = threading.Lock()
    _NEXT_EPISODE_CACHE_MAX = 800
    _NEXT_EPISODE_PREFETCH_THREADS = {}
    _NEXT_EPISODE_PREFETCH_LOCK = threading.Lock()
    _NEXT_EPISODE_PREFETCH_DELAY = 3
    _STREAM_FILE_LOCKS = {}
    _STREAM_FILE_LOCKS_LOCK = threading.Lock()
    _STREAM_CACHE_MAX = 4
    _STREAM_CACHE_DIR = ""
    _STREAM_CACHE_DIR_LOCK = threading.Lock()
    # 按播放器 Range 请求缓存 MP4 索引。索引只包含 moov 和 sample 元数据，
    # 不缓存整部视频，避免首次播放必须等待完整下载和解密。
    _PARTIAL_META_CACHE = {}
    _PARTIAL_META_CACHE_LOCK = threading.Lock()
    _PARTIAL_META_LOAD_LOCKS = {}
    _PARTIAL_META_LOAD_LOCKS_LOCK = threading.Lock()
    _PARTIAL_RANGE_FETCH_LOCKS = {}
    _PARTIAL_RANGE_FETCH_LOCKS_LOCK = threading.Lock()
    # 首播先回源较小分段，尽快把 ftyp/moov 和首个 sample 交给播放器。
    _PARTIAL_RANGE_MAX = 256 * 1024
    _EPISODE_CACHE = {}
    _EPISODE_CACHE_LOCK = threading.Lock()
    _REMOTE_SIGN_UNTIL = 0
    _REMOTE_SIGN_LOCK = threading.Lock()

    def getName(self):
        return "GuoGuo"

    # ============================================================
    # HTTP 工具 (替代 OkHttp)
    # ============================================================

    def _http_get(self, url, headers=None):
        req_headers = {"User-Agent": self._ua()}
        if isinstance(headers, dict):
            req_headers.update(headers)
        try:
            rsp = self.fetch(url, headers=req_headers)
            if rsp is None:
                return ""
            if hasattr(rsp, "text"):
                return rsp.text or ""
            if hasattr(rsp, "read"):
                return rsp.read().decode("utf-8", errors="ignore")
            return str(rsp)
        except Exception:
            pass
        try:
            req = urllib.request.Request(url, headers=req_headers, method="GET")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _http_post(self, url, body, headers=None):
        req_headers = self._ua_header()
        req_headers["Content-Type"] = "application/json"
        if isinstance(headers, dict):
            req_headers.update(headers)
        body_bytes = body.encode("utf-8") if isinstance(body, str) else body
        try:
            rsp = self.post(url, headers=req_headers, data=body_bytes)
            if rsp is not None:
                if hasattr(rsp, "text"):
                    return rsp.text or ""
                if hasattr(rsp, "read"):
                    return rsp.read().decode("utf-8", errors="ignore")
                return str(rsp)
        except Exception:
            pass
        try:
            req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            try:
                return e.read().decode("utf-8", errors="ignore")
            except Exception:
                return ""
        except Exception:
            return ""

    def _http_get_bytes(self, url, headers=None, cancel_check=None):
        req_headers = {"User-Agent": self.PROXY_UA}
        if isinstance(headers, dict):
            req_headers.update(headers)
        if _is_cancel_requested(cancel_check):
            return None
        if cancel_check is not None:
            response = None
            try:
                response = self.fetch(url, headers=req_headers, timeout=30, stream=True)
                if response is not None:
                    iterator = response.iter_content(chunk_size=64 * 1024) if hasattr(response, "iter_content") else None
                    if iterator is not None:
                        data = bytearray()
                        for chunk in iterator:
                            if _is_cancel_requested(cancel_check):
                                return None
                            if chunk:
                                data.extend(chunk)
                        return bytes(data)
                    if _is_cancel_requested(cancel_check):
                        return None
                    if hasattr(response, "content"):
                        return response.content
                    if hasattr(response, "read"):
                        return response.read()
            except Exception:
                pass
            finally:
                try:
                    if response is not None:
                        response.close()
                except Exception:
                    pass
            if _is_cancel_requested(cancel_check):
                return None
        # 视频回源优先使用项目内 requests 通道。模拟器上 urllib 可能在
        # TLS/连接阶段长时间阻塞，导致本地代理在播放器超时前无法返回。
        try:
            rsp = self.fetch(url, headers=req_headers, timeout=30)
            if rsp is not None:
                if hasattr(rsp, "content"):
                    return rsp.content
                if hasattr(rsp, "read"):
                    return rsp.read()
        except Exception:
            pass
        # 仅在 requests 不可用时保留 urllib 兜底，避免改变旧环境兼容性。
        try:
            req = urllib.request.Request(url, headers=req_headers, method="GET")
            with urllib.request.urlopen(req, timeout=15) as resp:
                if cancel_check is not None:
                    data = bytearray()
                    while True:
                        if _is_cancel_requested(cancel_check):
                            return None
                        chunk = resp.read(64 * 1024)
                        if not chunk:
                            return bytes(data)
                        data.extend(chunk)
                return resp.read()
        except Exception:
            pass
        return b""

    def _ua(self):
        return "com.phoenix.read/72732 (Linux; U; Android 13; zh_CN; Mi 10; Build/TKQ1.221114.001)"

    def _ua_header(self):
        return {
            "User-Agent": self._ua(),
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-ss-dp": "8662",
        }

    def _json_safe(self, obj, default=None):
        if default is None:
            default = {}
        if isinstance(obj, (dict, list)):
            return obj
        try:
            return json.loads(str(obj or "").strip())
        except Exception:
            return default

    @staticmethod
    def _is_empty(s):
        return s is None or (isinstance(s, str) and s.strip() == "")

    # ============================================================
    # GuoGuoClient - HTTP API 客户端
    # ============================================================

    def __init_client(self, device_id="", iid=""):
        if not device_id:
            device_id = "1677186774376987"
        if not iid:
            iid = "4351204728771643"
        self.device_id = device_id
        self.iid = iid
        self.prefer_base = self.BASES[0]
        self.session_id = ""
        self.rank_filter_key = ""
        self.rank_session_id = ""
        self.rank_version = ""
        self.session_uuid = str(uuid.uuid4())

    def _ordered_bases(self):
        if not self.prefer_base:
            return list(self.BASES)
        result = [self.prefer_base]
        for b in self.BASES:
            if b != self.prefer_base:
                result.append(b)
        return result

    def _append(self, sb, key, value):
        if sb:
            sb.append("&")
        sb.append(urllib.parse.quote_plus(key))
        sb.append("=")
        sb.append(urllib.parse.quote_plus("" if value is None else value))

    def _device_query(self):
        now = int(time.time() * 1000)
        sb = []
        params = [
            ("device_id", self.device_id),
            ("iid", self.iid),
            ("aid", "8662"),
            ("app_name", "novelread"),
            ("version_code", "72732"),
            ("version_name", "7.2.7.32"),
            ("device_platform", "android"),
            ("os", "android"),
            ("ssmix", "a"),
            ("device_type", "Mi 10"),
            ("device_brand", "Xiaomi"),
            ("language", "zh"),
            ("os_api", "33"),
            ("os_version", "13"),
            ("manifest_version_code", "72732"),
            ("resolution", "1080*2206"),
            ("dpi", "440"),
            ("update_version_code", "72732"),
            ("_rticket", str(now)),
            ("host_abi", "arm64-v8a"),
            ("dragon_device_type", "phone"),
            ("channel", "update_64"),
            ("ac", "wifi"),
            ("cdid", str(uuid.uuid4())),
        ]
        for k, v in params:
            self._append(sb, k, v)
        return "".join(sb)

    def _multi_device_query(self):
        """公共参数 for multi_video_model/player, 保留当前版本号。"""
        rticket = str(int(time.time() * 1000))
        sb = []
        params = [
            ("iid", self.iid),
            ("device_id", self.device_id),
            ("ac", "wifi"),
            ("channel", "bd_mr_hg78_duanju_cn_and_htl_cl_kl50_06"),
            ("aid", self.AID),
            ("app_name", self.APP_NAME),
            ("version_code", self.VERSION_CODE),
            ("version_name", self.VERSION_NAME),
            ("device_platform", "android"),
            ("os", "android"),
            ("ssmix", "a"),
            ("device_type", "Mi 10"),
            ("device_brand", "Xiaomi"),
            ("language", "zh"),
            ("os_api", "33"),
            ("os_version", "13"),
            ("manifest_version_code", self.VERSION_CODE),
            ("resolution", "1080*2206"),
            ("dpi", "440"),
            ("update_version_code", self.VERSION_CODE),
            ("gender", "2"),
            ("host_abi", "arm64-v8a"),
            ("dragon_device_type", "phone"),
            ("need_personal_recommend", "1"),
            ("pv_player", self.VERSION_CODE),
            ("player_so_load", "1"),
            ("compliance_status", "0"),
            ("is_android_pad_screen", "0"),
            ("network_type", "4"),
            ("_rticket", rticket),
        ]
        for k, v in params:
            self._append(sb, k, v)
        return "".join(sb), rticket

    def _device_query_for_sign(self):
        sb = []
        params = [
            ("aid", "8662"),
            ("device_platform", "android"),
            ("os_version", "13"),
            ("version_code", "72732"),
            ("version_name", "7.2.7.32"),
            ("app_name", "novelread"),
            ("channel", "seo_laxin_pc_android"),
            ("device_id", self.device_id),
            ("iid", self.iid),
            ("device_type", "Mi 10"),
            ("device_brand", "Xiaomi"),
            ("language", "zh"),
        ]
        for k, v in params:
            self._append(sb, k, v)
        return "".join(sb)

    def _walk_videos(self, node, out, depth=0):
        if node is None:
            return
        if depth > 14:
            return
        if isinstance(node, dict):
            if "series_id" in node and "title" in node:
                if "vid" in node or "episode_cnt" in node or "use_video_model" in node:
                    out.append(node)
            for k in list(node.keys()):
                self._walk_videos(node[k], out, depth + 1)
        elif isinstance(node, list):
            limit = min(len(node), 120)
            for i in range(limit):
                self._walk_videos(node[i], out, depth + 1)

    def _extract_videos(self, root):
        all_videos = []
        self._walk_videos(root, all_videos, 0)
        dedup = {}
        for obj in all_videos:
            series_id = str(obj.get("series_id", ""))
            if self._is_empty(series_id):
                continue
            if series_id in dedup:
                continue
            dedup[series_id] = obj
        result = list(dedup.values())
        self._remember_series(result)
        return result

    def _remember_series(self, series):
        if not series:
            return
        with self._SERIES_CACHE_LOCK:
            for obj in series:
                if obj is None:
                    continue
                sid = str(obj.get("series_id", ""))
                if self._is_empty(sid):
                    continue
                self._SERIES_CACHE[sid] = obj
            if len(self._SERIES_CACHE) > self.SERIES_CACHE_MAX:
                keys = list(self._SERIES_CACHE.keys())
                for k in keys[:400]:
                    self._SERIES_CACHE.pop(k, None)

    def _parse_selector_rows(self, root):
        result = {}
        if not isinstance(root, dict):
            return result
        data = root.get("data")
        if not isinstance(data, dict):
            return result
        rows = data.get("selector_rows")
        if not isinstance(rows, list):
            return result
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_type = row.get("row_type", "")
            if self._is_empty(row_type):
                row_type = row.get("type", "")
            if self._is_empty(row_type):
                continue
            if row_type == "genre":
                continue
            items = row.get("items")
            if items is None:
                items = row.get("selector_items")
            if not isinstance(items, list):
                continue
            lst = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                show_name = item.get("show_name", "")
                item_id = item.get("selector_item_id", "")
                if self._is_empty(show_name) or self._is_empty(item_id):
                    continue
                lst.append([show_name, item_id])
            if lst:
                result[row_type] = lst
        return result

    def _get_json(self, path, params=None):
        query = self._device_query()
        if params:
            for k, v in params.items():
                query += "&" + urllib.parse.quote_plus(k) + "=" + urllib.parse.quote_plus("" if v is None else str(v))
        bases = self._ordered_bases()
        for base in bases:
            try:
                url = base + path + "?" + query
                body = self._http_get(url, self._ua_header())
                if self._is_empty(body):
                    continue
                self.prefer_base = base
                return self._json_safe(body)
            except Exception:
                continue
        return {}

    def _landpage(self, genre, sort, theme_filter, role_filter, offset, limit, req_scene):
        if self._is_empty(genre):
            genre = "short_play"
        select_items = {
            "category_dim_epoch": [],
            "online_time": [],
            "gender": [],
            "category_dim_role": [] if self._is_empty(role_filter) else [role_filter],
            "genre": [genre],
            "sort": [] if self._is_empty(sort) else [sort],
            "category_dim_theme": [] if self._is_empty(theme_filter) else [theme_filter],
        }
        if limit <= 0:
            limit = 18
        body = {
            "filter_ids": "",
            "req_scene": genre,
            "offset": max(0, offset),
            "need_selector_panel": req_scene == "only_panel",
            "limit": limit,
            "select_items": select_items,
            "session_id": self.session_id or "",
        }
        if self._is_empty(req_scene):
            req_scene = "only_content"
        body["req_type"] = req_scene
        body["client_req_type"] = 1
        resp = self._post_land(body)
        data = resp.get("data") if isinstance(resp, dict) else None
        if isinstance(data, dict):
            new_sess = data.get("session_id", "")
            if not self._is_empty(new_sess):
                self.session_id = new_sess
        return resp

    def _post_land(self, body):
        bases = self._ordered_bases()
        json_body = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        for base in bases:
            try:
                url = base + self.LAND + "?" + self._device_query()
                resp = self._http_post(url, json_body, self._ua_header())
                if self._is_empty(resp):
                    continue
                self.prefer_base = base
                return self._json_safe(resp)
            except Exception:
                continue
        return {}

    def _rank_cell_change(self, filter_key, sub_items, offset):
        if self._is_empty(filter_key):
            filter_key = "all"
        if sub_items is None:
            sub_items = ""
        composed_key = filter_key + "|" + sub_items
        if composed_key != self.rank_filter_key:
            self.rank_filter_key = composed_key
            self.rank_session_id = ""
            self.rank_version = ""
        params = {
            "cell_id": self.RANK_CELL_ID,
            "client_req_type": "2",
        }
        params["client_template"] = "2"
        params["tab_type"] = "26"
        params["screen_width_px"] = "1080"
        params["selected_items"] = filter_key
        params["sub_selected_items"] = sub_items
        params["session_uuid"] = self.session_uuid
        params["panel_selected_items"] = ""
        params["background_selected_items"] = ""
        params["celebrity_user_id"] = ""
        params["filter_ids"] = ""
        if offset > 0:
            params["unlimited_selector_change_type"] = "1"
            params["offset"] = str(max(0, offset))
            if not self._is_empty(self.rank_session_id):
                params["session_id"] = self.rank_session_id
            if not self._is_empty(self.rank_version):
                params["rank_version"] = self.rank_version
        else:
            params["unlimited_selector_change_type"] = "2"
            params["rank_version"] = ""
        resp = self._get_json(self.CELL_CHANGE, params)
        data = resp.get("data") if isinstance(resp, dict) else None
        if isinstance(data, dict):
            sid = data.get("session_id", "")
            if not self._is_empty(sid):
                self.rank_session_id = sid
            rv = data.get("rank_version", "")
            if not self._is_empty(rv):
                self.rank_version = rv
        return resp

    def _web_search_videos(self, keyword):
        url = self.WEB_SEARCH + urllib.parse.quote(keyword, safe="")
        headers = {
            "Accept": "text/html,application/xhtml+xml",
            "Referer": "https://hongguoduanju.com/",
        }
        page = self._http_get(url, headers)
        if self._is_empty(page):
            return []
        try:
            page = page.replace("\x00", "")
            marker = "_ROUTER_DATA = "
            start = page.find(marker)
            if start < 0:
                return []
            root, _ = json.JSONDecoder().raw_decode(page[start + len(marker):])
            loader_data = root.get("loaderData") if isinstance(root, dict) else None
            if not isinstance(loader_data, dict):
                return []
            search_list = None
            for value in loader_data.values():
                if isinstance(value, dict) and isinstance(value.get("searchList"), list):
                    search_list = value.get("searchList")
                    break
            if not isinstance(search_list, list):
                return []
        except Exception:
            return []

        videos = []
        dedup = {}
        for item in search_list:
            if not isinstance(item, dict):
                continue
            data = item.get("video_data")
            if not isinstance(data, dict):
                continue
            series_id = str(data.get("series_id", "")).strip()
            title = str(data.get("series_title", item.get("name", ""))).strip()
            if self._is_empty(series_id) or self._is_empty(title) or series_id in dedup:
                continue
            vids = data.get("vid_list")
            vid = str(vids[0]).strip() if isinstance(vids, list) and vids else ""
            try:
                episode_cnt = int(data.get("episode_cnt", 0) or 0)
            except Exception:
                episode_cnt = 0
            obj = {
                "series_id": series_id,
                "title": title,
                "cover": str(data.get("series_cover", "")),
                "video_desc": str(data.get("series_intro", "")),
                "episode_cnt": episode_cnt,
                "series_status": data.get("series_status", ""),
                "episode_right_text": str(data.get("episode_right_text", "")),
                "vid": vid,
            }
            dedup[series_id] = obj
            videos.append(obj)
        self._remember_series(videos)
        return videos

    def _search_videos(self, keyword):
        keyword = str(keyword or "").strip()
        if self._is_empty(keyword):
            return []

        videos = self._web_search_videos(keyword)
        if videos:
            return videos

        params = {"query": keyword, "offset": "0", "count": "20"}
        videos = self._extract_videos(self._get_json(self.LANDING, params))
        if not videos and "短剧" not in keyword:
            params["query"] = keyword + "短剧"
            videos = self._extract_videos(self._get_json(self.LANDING, params))
        return videos

    @staticmethod
    def _same_title(left, right):
        left = re.sub(r"\s+", "", str(left or "")).strip().lower()
        right = re.sub(r"\s+", "", str(right or "")).strip().lower()
        return bool(left) and left == right

    def _search_exact_video(self, title):
        title = str(title or "").strip()
        if self._is_empty(title):
            return None
        result = self._search_videos(title)
        for obj in result:
            if self._same_title(obj.get("title", ""), title):
                return obj
        return None

    def _find_detail(self, id_str, expected_title=""):
        if self._is_empty(id_str):
            return None
        id_str = id_str.strip()
        has_sep = "|" in id_str
        if has_sep:
            parts = id_str.split("|")
            query = parts[0].strip()
            series_id = parts[1].strip() if len(parts) > 1 else ""
            episode_cnt = 0
            if len(parts) > 2:
                try:
                    episode_cnt = int(parts[2].strip())
                except Exception:
                    episode_cnt = 0
            vid = parts[3].strip() if len(parts) > 3 else ""
        else:
            episode_cnt = 0
            query = id_str
            series_id = ""
            vid = ""
        with self._SERIES_CACHE_LOCK:
            cached = self._SERIES_CACHE.get(query)
        if cached is not None:
            return cached
        if id_str.isdigit():
            return {
                "series_id": id_str,
                "title": expected_title or "",
                "_verify_id": True,
            }
        if self._is_empty(series_id):
            if self._is_empty(vid):
                results = self._search_videos(id_str)
                for obj in results:
                    if (id_str == str(obj.get("series_id", "")) or id_str == str(obj.get("title", ""))) and (self._is_empty(expected_title) or self._same_title(obj.get("title", ""), expected_title)):
                        return obj
                if not self._is_empty(expected_title):
                    return self._search_exact_video(expected_title)
                if not results:
                    return None
                return results[0]
            else:
                return self._search_by_vid_and_build(query, series_id, vid, episode_cnt)
        else:
            return self._search_by_vid_and_build(query, series_id, vid, episode_cnt)

    def _search_by_vid_and_build(self, query, series_id, vid, episode_cnt):
        if not self._is_empty(vid):
            results = self._search_videos(vid)
            for obj in results:
                if query == str(obj.get("series_id", "")) or vid == str(obj.get("title", "")):
                    return obj
        detail = {"series_id": query}
        if not self._is_empty(series_id):
            detail["vid"] = series_id
        if not self._is_empty(vid):
            detail["title"] = vid
        if episode_cnt > 0:
            detail["episode_cnt"] = episode_cnt
        with self._SERIES_CACHE_LOCK:
            self._SERIES_CACHE[query] = detail
        return detail

    def _play_headers(self):
        return {"User-Agent": self._ua()}

    def _derive_key(self, spade_a):
        """从 spade_a (Base64) 本地解出 16 字节 content_key -> hex 字符串.

        纯算法, 不走网络, 不依赖 cryptography 等第三方库.
        """
        if self._is_empty(spade_a):
            raise Exception("spade_a empty")
        s = spade_a.strip()
        m = 4 - len(s) % 4
        if m != 4:
            s += "=" * m
        raw = base64.b64decode(s)
        if len(raw) < 3:
            raise Exception("spade_a too short: %d bytes" % len(raw))
        v6 = raw[0] ^ raw[1] ^ raw[2]
        v8 = len(raw) - v6 + 47
        if v8 <= 0 or v8 > len(raw) * 2:
            raise Exception("spade_a v8=%d out of range" % v8)
        if 1 + v8 > len(raw):
            v8 = len(raw) - 1
        if v8 < 33:
            raise Exception("spade_a v8=%d too small" % v8)
        v13 = bytearray(raw[1:1 + v8])
        vA, vB = 85, 246
        for i in range(v8):
            popcnt = bin(i).count("1")
            if i & 1:
                v24, vA = vA, v13[i]
            else:
                v24, vB = vB, v13[i]
            v25 = v24 ^ v13[i]
            v13[i] = (-21 - popcnt + v25) & 0xFF
        return bytes(v13[1:33]).decode("ascii")

    # ============================================================
    # GuoGuoPlay - 播放处理
    # ============================================================

    def __init_play(self, quality):
        self.vm_cache = {}
        self.play_lock = threading.Lock()
        self._play_request_lock = threading.Lock()
        self._play_request_generation = 0
        self.quality = quality if not self._is_empty(quality) else "1080"

    def _md5_upper(self, data_bytes):
        h = hashlib.md5(data_bytes).hexdigest().upper()
        return h

    @staticmethod
    def _parse_height(s):
        if not s:
            return 0
        try:
            num = re.sub(r"[^0-9]", "", str(s).lower())
            return int(num) if num else 0
        except Exception:
            return 0

    @classmethod
    def _normalize_def(cls, s):
        h = cls._parse_height(s)
        if h > 0:
            return str(h) + "p"
        return ""

    @classmethod
    def _tier_meta(cls, tier):
        meta = tier.get("video_meta") if isinstance(tier, dict) else None
        return meta if isinstance(meta, dict) else {}

    @classmethod
    def _tier_definition(cls, tier):
        if not isinstance(tier, dict):
            return ""
        value = tier.get("definition", "")
        if cls._is_empty(value):
            value = cls._tier_meta(tier).get("definition", "")
        return value

    @classmethod
    def _tier_spade_a(cls, tier):
        if not isinstance(tier, dict):
            return ""
        value = tier.get("spade_a", "")
        if cls._is_empty(value):
            meta_encrypt = cls._tier_meta(tier).get("encrypt_info")
            if isinstance(meta_encrypt, dict):
                value = meta_encrypt.get("spade_a", "")
        if cls._is_empty(value):
            encrypt_info = tier.get("encrypt_info")
            if isinstance(encrypt_info, dict):
                value = encrypt_info.get("spade_a", "")
        return value

    @classmethod
    def _tier_bitrate(cls, tier):
        if not isinstance(tier, dict):
            return 0
        value = tier.get("bitrate", 0)
        if not value:
            value = cls._tier_meta(tier).get("bitrate", 0)
        try:
            return int(value or 0)
        except Exception:
            return 0

    @classmethod
    def _quality_height(cls, tier):
        if not isinstance(tier, dict):
            return 0
        def_val = cls._tier_definition(tier)
        h = cls._parse_height(def_val)
        if h > 0:
            return h
        meta = cls._tier_meta(tier)
        vw = int(tier.get("vwidth", meta.get("vwidth", 0)) or 0)
        vh = int(tier.get("vheight", meta.get("vheight", 0)) or 0)
        if vw > 0 and vh > 0:
            return min(vw, vh)
        if vh > 0:
            return vh
        if vw > 0:
            return vw
        return 0

    @classmethod
    def _is_playable_tier(cls, tier):
        if not isinstance(tier, dict):
            return False
        if cls._is_empty(tier.get("main_url", "")):
            return False
        if cls._is_empty(cls._tier_spade_a(tier)):
            return False
        return cls._quality_height(tier) > 0

    @staticmethod
    def is_vid(s):
        if not s or len(s) < 15:
            return False
        return s.isdigit()

    def _collect_candidates(self, model):
        candidates = []
        video_list = model.get("video_list")
        if isinstance(video_list, dict):
            video_items = list(video_list.values())
        elif isinstance(video_list, list):
            video_items = video_list
        else:
            video_items = []
        for tier in video_items:
            if self._is_playable_tier(tier):
                candidates.append(tier)
        dynamic_list = model.get("dynamic_video_list")
        if isinstance(dynamic_list, list):
            for tier in dynamic_list:
                if self._is_playable_tier(tier):
                    candidates.append(tier)
        dedup = {}
        for tier in candidates:
            h = self._quality_height(tier)
            if h <= 0:
                continue
            if h in dedup:
                b1 = self._tier_bitrate(tier)
                b2 = self._tier_bitrate(dedup[h])
                if b1 > b2:
                    dedup[h] = tier
            else:
                dedup[h] = tier
        return list(dedup.values())

    @classmethod
    def _def_equals(cls, tier, want_def):
        if cls._is_empty(want_def) or not isinstance(tier, dict):
            return False
        def_val = cls._tier_definition(tier)
        normalized = cls._normalize_def(def_val)
        return want_def == normalized

    @classmethod
    def _score_against_want(cls, h, want_h):
        if h <= 0:
            return 10000
        if want_h <= 0:
            return 1000 - h
        if h == want_h:
            return 0
        if h < want_h:
            return want_h - h
        return h - want_h + 1000

    def _rank_qualities(self, model, want):
        candidates = self._collect_candidates(model)
        want_def = self._normalize_def(want)
        want_h = self._parse_height(want)

        def sort_key(tier):
            a_match = self._def_equals(tier, want_def)
            h = self._quality_height(tier)
            score = self._score_against_want(h, want_h)
            return (0 if a_match else 1, score, -h)

        candidates.sort(key=sort_key)
        return candidates

    def _signed_post(self, path, body_obj):
        body = json.dumps(body_obj, ensure_ascii=False, separators=(",", ":"))
        body = body.replace(" ", "")
        body_bytes = body.encode("utf-8")
        body_md5 = self._md5_upper(body_bytes)
        device_query = self._device_query_for_sign()
        khronos = int(time.time())

        def build_headers(gorgon, khronos_str):
            return {
                "User-Agent": self._ua(),
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
                "x-ss-dp": "8662",
                "x-ss-stub": body_md5,
                "X-Gorgon": gorgon,
                "X-Khronos": khronos_str,
            }

        def post_once(gorgon, khronos_str):
            headers = build_headers(gorgon, khronos_str)
            for host in self.PLAY_HOSTS:
                try:
                    url = host + path + "?" + device_query
                    resp = self._http_post(url, body, headers)
                    if self._is_empty(resp):
                        continue
                    trimmed = resp.strip()
                    if not trimmed.startswith("<") and not trimmed.lower().startswith("<!doctype"):
                        return self._json_safe(resp)
                except Exception as e:
                    return {"_err": str(e), "_host": host}
            return {"_err": "all hosts empty", "_host": ""}

        def try_gorgon(gorgon, khronos_str, source):
            obj = post_once(gorgon, khronos_str)
            if "_err" in obj:
                raise Exception(obj["_err"])
            code = obj.get("code")
            try:
                code = int(code) if code is not None else None
            except Exception:
                code = None
            if code == 0 and "data" in obj:
                return obj
            raise Exception(source + " rejected: code=%s" % code)

        with type(self)._REMOTE_SIGN_LOCK:
            use_remote = time.time() < type(self)._REMOTE_SIGN_UNTIL
        if not use_remote:
            local = local_sign_request(device_query, body_md5, "", khronos)
            try:
                return try_gorgon(local["x_gorgon"], local["x_khronos"], "local")
            except Exception as e:
                with type(self)._REMOTE_SIGN_LOCK:
                    type(self)._REMOTE_SIGN_UNTIL = time.time() + 600
                print("echo-GuoGuo local X-Gorgon 失败 (%s), 回退签名服务" % e)
        remote = _remote_sign("/v1/sign", json.dumps({
            "query": device_query, "body_md5": body_md5, "cookie": "", "khronos": str(khronos),
        }, ensure_ascii=False, separators=(",", ":")))
        return try_gorgon(remote.get("x_gorgon", ""), remote.get("x_khronos", str(khronos)), "remote")

    def _multi_video_post(self, vid):
        query, rticket = self._multi_device_query()
        body_obj = {
            "biz_param": {
                "caller_scene": "player",
                "detail_page_version": 0,
                "device_level": 3,
                "disable_digg_stat": False,
                "disable_video_relate_book": False,
                "expire_strategy": "opt",
                "from_video_id": "",
                "image_shrink_datas_str": "W3siaW1hZ2VfdHlwZSI6MiwiaW1hZ2Vfd2lkdGgiOjM1OSwic2hyaW5rX3R5cGUiOjJ9LHsiaW1hZ2VfdHlwZSI6MywiaW1hZ2Vfd2lkdGgiOjEwNzgsInNocmlua190eXBlIjozfSx7ImltYWdlX3R5cGUiOjQsImltYWdlX3dpZHRoIjo5OSwic2hyaW5rX3R5cGUiOjR9XQ==",
                "need_all_video_definition": True,
                "need_mp4_align": True,
                "screen_width_px": "1080",
                "source": 4,
                "use_os_player": False,
                "use_server_dns": False,
                "video_id_type": 0,
                "video_platform": 1024,
                "item_map": {"1004": str(vid)},
            },
            "dr_scene": "player",
            "mixed_video_id_map": {"1004": [str(vid)]},
        }
        body = json.dumps(body_obj, ensure_ascii=False, separators=(",", ":"))
        body_bytes = gzip.compress(body.encode("utf-8"))
        headers = {
            "User-Agent": self._ua(),
            "Accept": "application/json; charset=utf-8,application/x-protobuf",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Encoding": "gzip",
            "Authorization": "Bearer",
            "x-reading-request": rticket + "-" + str(secrets.randbelow(32768)),
            "x-xs-from-web": "0",
            "x-vc-bdturing-sdk-version": "4.0.3.cn",
            "Referer": "https://api5-normal-sinfonlinec.fqnovel.com/",
        }
        hosts = [
            "https://api5-normal-sinfonlinec.fqnovel.com",
            "https://api5-normal.fqnovel.com",
            "https://api5-normal-sinfonlineb.fqnovel.com",
        ]
        last = None
        for host in hosts:
            raw = self._http_post(host + self.MULTI_VM_PATH + "?" + query, body_bytes, headers)
            obj = self._json_safe(raw)
            try:
                code = int(obj.get("code", -1)) if isinstance(obj, dict) else -1
            except Exception:
                code = -1
            if code == 0 and isinstance(obj, dict) and isinstance(obj.get("data"), dict):
                return obj
            last = obj
        if isinstance(last, dict):
            msg = last.get("debug_info") or last.get("message") or last.get("BaseResp", {}).get("StatusMessage")
            raise Exception("multi_video_model: " + str(msg or "request failed"))
        raise Exception("multi_video_model: request failed")

    def _load_multi_video_model(self, vid):
        resp = self._multi_video_post(vid)
        data = resp.get("data")
        entry = data.get(str(vid)) if isinstance(data, dict) else None
        vm = entry.get("video_model") if isinstance(entry, dict) else None
        if isinstance(vm, str):
            model = self._json_safe(vm)
        elif isinstance(vm, dict):
            model = vm
        else:
            raise Exception("no video_model")
        if not isinstance(model, dict):
            raise Exception("invalid video_model")
        return model

    def _load_legacy_video_model(self, vid):
        biz_param = {
            "detail_page_version": 0,
            "device_level": 3,
            "disable_digg_stat": False,
            "disable_video_relate_book": False,
            "from_video_id": "",
            "need_all_video_definition": True,
            "need_mp4_align": False,
            "use_os_player": False,
            "use_server_dns": True,
            "use_server_dns_scene": "cold_start_stage",
            "video_platform": 0,
        }
        outer = {"biz_param": biz_param, "content_type": 1, "video_id": vid}
        resp = self._signed_post(self.VM_PATH, outer)
        code_raw = resp.get("code", -1)
        code = int(code_raw) if code_raw is not None else -1
        if code != 0:
            msg = resp.get("message", resp.get("StatusMessage", "code" + str(resp.get("code"))))
            raise Exception("video_model: " + str(msg))
        data = resp.get("data")
        if not isinstance(data, dict):
            raise Exception("no data")
        vm = data.get("video_model")
        if isinstance(vm, str):
            model = self._json_safe(vm)
        elif isinstance(vm, dict):
            model = vm
        else:
            raise Exception("no video_model")
        return model

    def _load_video_model(self, vid, want_quality=""):
        now = int(time.time() * 1000)
        want_h = self._parse_height(want_quality or self.quality)
        use_multi = want_h >= 1080
        cache_key = str(vid) + ("::multi" if use_multi else "::legacy")
        cached = self.vm_cache.get(cache_key)
        if cached and cached[0] > now and isinstance(cached[1], dict):
            return cached[1]

        loaders = [self._load_multi_video_model, self._load_legacy_video_model]
        if not use_multi:
            loaders.reverse()
        last_error = None
        for loader in loaders:
            try:
                model = loader(vid)
                self.vm_cache[cache_key] = [now + 480000, model]
                return model
            except Exception as error:
                last_error = error
                print("echo-GuoGuo %s 失败，尝试备用接口: %s" %
                      ("multi_video_model" if loader == self._load_multi_video_model else "video_model", error))
        if last_error is not None:
            raise last_error
        raise Exception("no video_model")

    def _episode_vids(self, series_id, vid, detail=None, expected_title=""):
        result = []
        # 缓存: 避免重复请求
        cache_key = f"ep::{series_id}::{vid}"
        with self._EPISODE_CACHE_LOCK:
            cached = self._EPISODE_CACHE.get(cache_key)
        if cached is not None and self._is_empty(expected_title):
            return cached
        # 当 vid 为空但 series_id 有值时, 尝试用 SERIES_CACHE 中的 vid
        if self._is_empty(vid) and not self._is_empty(series_id):
            with self._SERIES_CACHE_LOCK:
                series_obj = self._SERIES_CACHE.get(series_id)
            if isinstance(series_obj, dict):
                cached_vid = str(series_obj.get("vid", ""))
                if self.is_vid(cached_vid):
                    vid = cached_vid
        if self._is_empty(series_id):
            if not self._is_empty(vid):
                result.append(vid)
            with self._EPISODE_CACHE_LOCK:
                self._EPISODE_CACHE[cache_key] = result
            return result
        try:
            req = {"series_id": series_id, "video": vid or "", "content_type": 1}
            resp = self._signed_post(self.DETAIL_PATH, req)
            code_raw = resp.get("code", -1)
            code = int(code_raw) if code_raw is not None else -1
            if code == 0:
                data = resp.get("data")
                video_data = data.get("video_data") if isinstance(data, dict) else None
                video_list = video_data.get("video_list") if isinstance(video_data, dict) else None
                actual_title = str(video_data.get("series_title", "")).strip() if isinstance(video_data, dict) else ""
                if isinstance(detail, dict) and actual_title:
                    detail["_title_mismatch"] = not self._is_empty(expected_title) and not self._same_title(actual_title, expected_title)
                    detail["_actual_title"] = actual_title
                    if self._is_empty(expected_title) or not detail["_title_mismatch"]:
                        detail["title"] = actual_title
                    cover = video_data.get("series_cover", "")
                    if cover:
                        detail["cover"] = cover
                    intro = video_data.get("series_intro", "")
                    if intro:
                        detail["video_desc"] = intro
                    actual_episode_cnt = int(video_data.get("episode_cnt", 0) or 0)
                    if actual_episode_cnt > 0:
                        detail["episode_cnt"] = actual_episode_cnt
                episode_right_text = str(video_data.get("episode_right_text", "")).strip() if isinstance(video_data, dict) else ""
                if episode_right_text:
                    if isinstance(detail, dict):
                        detail["episode_right_text"] = episode_right_text
                    with self._SERIES_CACHE_LOCK:
                        series_obj = self._SERIES_CACHE.get(str(series_id))
                        if isinstance(series_obj, dict):
                            series_obj["episode_right_text"] = episode_right_text
                # 详情接口已验证剧名一致后，缓存完整元数据，避免下次只命中列表缓存。
                if isinstance(detail, dict) and actual_title and not detail.get("_title_mismatch"):
                    with self._SERIES_CACHE_LOCK:
                        self._SERIES_CACHE[str(series_id)] = detail
                        if len(self._SERIES_CACHE) > self.SERIES_CACHE_MAX:
                            keys = list(self._SERIES_CACHE.keys())
                            for cache_key in keys[:400]:
                                self._SERIES_CACHE.pop(cache_key, None)
                if isinstance(video_list, list):
                    meta_list = []
                    vids = []
                    for i, item in enumerate(video_list):
                        if not isinstance(item, dict):
                            continue
                        # 实际 API 字段: vid (不是 video_id/video)
                        v = item.get("vid", "")
                        if not v:
                            v = item.get("video_id", "")
                        if not v:
                            v = item.get("video", "")
                        v = str(v)
                        if not self.is_vid(v):
                            continue
                        # 实际 API 排序字段: vid_index (从 1 开始)
                        sort_val = int(item.get("vid_index", 0) or 0)
                        if sort_val <= 0:
                            sort_val = i + 1
                        meta_list.append([sort_val, len(vids)])
                        vids.append(v)
                    meta_list.sort(key=lambda x: x[0] if x[0] > 0 else 1000000)
                    for meta in meta_list:
                        result.append(vids[meta[1]])
                    if not result and isinstance(detail, dict):
                        detail["_detail_failed"] = True
                elif isinstance(detail, dict):
                    detail["_detail_failed"] = True
            elif isinstance(detail, dict):
                detail["_detail_failed"] = True
        except Exception:
            if isinstance(detail, dict):
                detail["_detail_failed"] = True
        if not result and self.is_vid(vid):
            result.append(vid)
        # 控制缓存大小
        with self._EPISODE_CACHE_LOCK:
            if len(self._EPISODE_CACHE) > 64:
                keys = list(self._EPISODE_CACHE.keys())[:32]
                for k in keys:
                    self._EPISODE_CACHE.pop(k, None)
            self._EPISODE_CACHE[cache_key] = result
        return result

    @classmethod
    def _remember_next_episodes(cls, episode_vids):
        if not isinstance(episode_vids, list) or len(episode_vids) < 2:
            return
        with cls._NEXT_EPISODE_CACHE_LOCK:
            for index in range(len(episode_vids) - 1):
                current = str(episode_vids[index] or "")
                next_vid = str(episode_vids[index + 1] or "")
                if cls.is_vid(current) and cls.is_vid(next_vid) and current != next_vid:
                    cls._NEXT_EPISODE_CACHE[current] = next_vid
            if len(cls._NEXT_EPISODE_CACHE) > cls._NEXT_EPISODE_CACHE_MAX:
                keys = list(cls._NEXT_EPISODE_CACHE.keys())
                for key in keys[:len(keys) // 2]:
                    cls._NEXT_EPISODE_CACHE.pop(key, None)

    @classmethod
    def _next_episode_vid(cls, vid):
        with cls._NEXT_EPISODE_CACHE_LOCK:
            return cls._NEXT_EPISODE_CACHE.get(str(vid), "")

    def _tier_source(self, tier):
        main_url = tier.get("main_url", "")
        spade_a = self._tier_spade_a(tier)
        if self._is_empty(main_url) or self._is_empty(spade_a):
            raise Exception("missing main_url/spade_a")
        if str(main_url).startswith(("http://", "https://", "//")):
            url = str(main_url).strip()
        else:
            url_bytes = base64.b64decode(main_url)
            url = url_bytes.decode("utf-8", errors="ignore").strip()
        if url.startswith("//"):
            url = "https:" + url
        if not url.startswith("http"):
            raise Exception("invalid main_url")
        return url, self._derive_key(spade_a)

    def _begin_play_request(self):
        with self._play_request_lock:
            self._play_request_generation += 1
            return self._play_request_generation

    def _is_play_request_current(self, generation):
        with self._play_request_lock:
            return generation == self._play_request_generation

    def _resolve_play_locked(self, vid, want_quality, prefetch_vid="", prefetch_generation=0):
        if self._is_empty(want_quality):
            want_quality = self.quality
        model = self._load_video_model(vid, want_quality)
        ranked = self._rank_qualities(model, want_quality)
        if not ranked:
            raise Exception("no playable quality")
        last_err = None
        for tier in ranked:
            try:
                url, key = self._tier_source(tier)
                return self._proxy_play_url(
                    url, key, True, True, prefetch_vid, want_quality, prefetch_generation)
            except Exception as e:
                last_err = e
                continue
        if last_err is not None:
            raise last_err
        raise Exception("missing main_url/spade_a")

    def _resolve_play(self, vid, want_quality=None, prefetch_vid="", prefetch_generation=0):
        if not self.is_vid(vid):
            raise Exception("bad video_id")
        with self.play_lock:
            return self._resolve_play_locked(
                vid, want_quality or self.quality, prefetch_vid, prefetch_generation)

    # ============================================================
    # GuoGuoCenc - CENC/DRM 解密
    # ============================================================

    @staticmethod
    def _hex_to_bytes(hex_str):
        if hex_str is None:
            hex_str = ""
        else:
            hex_str = hex_str.strip()
        if len(hex_str) % 2 == 1:
            raise ValueError("bad hex")
        return bytes(int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2))

    @staticmethod
    def _u(data, offset, length):
        value = 0
        for i in range(length):
            value = (value << 8) | (data[offset + i] & 0xff)
        return value

    @staticmethod
    def _typ(data, offset):
        return "".join(chr(data[offset + i] & 0xff) for i in range(4))

    def _cenc_parse(self, data, offset, end):
        boxes = []
        pos = offset
        while pos + 8 <= end:
            size = self._u(data, pos, 4)
            typ = self._typ(data, pos + 4)
            if size == 1:
                size = self._u(data, pos + 8, 8)
                header_size = 16
            else:
                if size == 0:
                    size = end - pos
                header_size = 8
            if size < 8:
                break
            if pos + size > end:
                break
            box = {"type": typ, "offset": pos, "header": header_size, "size": size, "children": []}
            data_start = pos + header_size
            if typ in self.CENC_CONTAINERS:
                box["children"] = self._cenc_parse(data, data_start, pos + int(size))
            elif typ == "stsd":
                box["children"] = self._cenc_parse(data, data_start + 8, pos + int(size))
            elif typ in ("hvc1", "hev1", "avc1", "mp4a"):
                box["children"] = self._cenc_parse(data, data_start + 0x4e, pos + int(size))
            elif typ in ("encv", "enca"):
                box["children"] = self._cenc_parse(data, data_start + 0x1c, pos + int(size))
            boxes.append(box)
            pos = pos + int(size)
        return boxes

    def _cenc_find(self, boxes, typ):
        for box in boxes:
            if box["type"] == typ:
                return box
            found = self._cenc_find(box["children"], typ)
            if found is not None:
                return found
        return None

    def _cenc_find_all(self, boxes, typ, out):
        for box in boxes:
            if box["type"] == typ:
                out.append(box)
            self._cenc_find_all(box["children"], typ, out)

    @staticmethod
    def _ctr_decrypt(key, iv, data):
        full_iv = (iv + b"\x00" * 16)[:16]
        try:
            clear = Spider._ctr_decrypt_pycrypto(key, full_iv, data)
            if clear is not None:
                return clear
        except Exception:
            pass
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            cipher = Cipher(algorithms.AES(key), modes.CTR(full_iv))
            decryptor = cipher.decryptor()
            return decryptor.update(data) + decryptor.finalize()
        except Exception:
            pass
        try:
            clear = Spider._ctr_decrypt_java(key, full_iv, data)
            if clear is not None:
                return clear
        except Exception:
            pass
        return Spider._ctr_decrypt_pure(key, (iv + b"\x00" * 16)[:16], data)

    @staticmethod
    def _ctr_decrypt_pycrypto(key, full_iv, data):
        """优先使用 Chaquopy 内置的 PyCryptodome C 实现。"""
        global _PY_AES, _PY_COUNTER, _PY_AES_UNAVAILABLE, _AES_BACKEND_LOGGED
        if _PY_AES_UNAVAILABLE:
            return None
        if _PY_AES is None:
            with _PY_AES_INIT_LOCK:
                if _PY_AES is None:
                    try:
                        from Crypto.Cipher import AES
                        from Crypto.Util import Counter
                        _PY_AES = AES
                        _PY_COUNTER = Counter
                    except Exception:
                        _PY_AES_UNAVAILABLE = True
                        return None
        try:
            counter = _PY_COUNTER.new(128, initial_value=int.from_bytes(full_iv, "big"))
            result = _PY_AES.new(key, _PY_AES.MODE_CTR, counter=counter).decrypt(data)
            if not _AES_BACKEND_LOGGED:
                _AES_BACKEND_LOGGED = True
                print("echo-GuoGuo AES=PyCryptodome")
            return result
        except Exception:
            return None

    @staticmethod
    def _ctr_decrypt_java(key, full_iv, data):
        """优先使用 Android/JVM AES，避免缺少原生 Crypto 时落入纯 Python 慢路径。"""
        global _JAVA_AES_CIPHER, _JAVA_AES_SECRET_KEY, _JAVA_AES_IV, _JAVA_AES_UNAVAILABLE
        if _JAVA_AES_UNAVAILABLE:
            return None
        if _JAVA_AES_CIPHER is None:
            with _JAVA_AES_INIT_LOCK:
                if _JAVA_AES_CIPHER is None:
                    try:
                        from java import jclass
                        _JAVA_AES_CIPHER = jclass("javax.crypto.Cipher")
                        _JAVA_AES_SECRET_KEY = jclass("javax.crypto.spec.SecretKeySpec")
                        _JAVA_AES_IV = jclass("javax.crypto.spec.IvParameterSpec")
                    except Exception:
                        _JAVA_AES_UNAVAILABLE = True
                        return None
        try:
            # Cipher 对象不能跨线程共享，但密钥和 IV 对象可以复用。
            # 纯 Java 回退只在 PyCryptodome/cryptography 不可用时执行。
            cipher = _JAVA_AES_CIPHER.getInstance("AES/CTR/NoPadding")
            secret_key = _JAVA_AES_SECRET_KEY(key, "AES")
            iv_spec = _JAVA_AES_IV(full_iv)
            cipher.init(_JAVA_AES_CIPHER.DECRYPT_MODE, secret_key, iv_spec)
            return bytes(cipher.doFinal(data))
        except Exception:
            return None

    def _parse_senc(self, data, senc, default_iv_len):
        ivs = []
        subsamples = []
        base = senc["offset"] + senc["header"]
        version_flags = self._u(data, base + 1, 3)
        has_subsamples = (version_flags & 0x02) != 0
        base += 4
        entry_count = self._u(data, base, 4)
        base += 4
        for _ in range(entry_count):
            iv = data[base:base + default_iv_len]
            ivs.append(iv)
            base += default_iv_len
            if has_subsamples:
                subsample_count = self._u(data, base, 2)
                base += 2
                subs = []
                for _ in range(subsample_count):
                    clear_len = self._u(data, base, 2)
                    enc_len = self._u(data, base + 2, 4)
                    subs.append([clear_len, enc_len])
                    base += 6
                subsamples.append(subs)
            else:
                subsamples.append([])
        return ivs, subsamples

    def _sample_offsets(self, data, stbl_children):
        stsz = self._cenc_find(stbl_children, "stsz")
        stsc = self._cenc_find(stbl_children, "stsc")
        stco = self._cenc_find(stbl_children, "stco")
        use_co64 = False
        if stco is None:
            stco = self._cenc_find(stbl_children, "co64")
            use_co64 = True
        if stsz is None or stsc is None or stco is None:
            return []
        stsz_base = stsz["offset"] + stsz["header"] + 4
        uniform_size = self._u(data, stsz_base, 4)
        sample_count = self._u(data, stsz_base + 4, 4)
        sample_sizes = []
        if uniform_size != 0:
            sample_sizes = [uniform_size] * sample_count
        else:
            p = stsz_base + 8
            for i in range(sample_count):
                sample_sizes.append(self._u(data, p + i * 4, 4))
        stsc_base = stsc["offset"] + stsc["header"] + 4
        stsc_count = self._u(data, stsc_base, 4)
        first_chunks = []
        samples_per_chunk = []
        for i in range(stsc_count):
            p = stsc_base + 4 + i * 12
            first_chunks.append(self._u(data, p, 4))
            samples_per_chunk.append(self._u(data, p + 4, 4))
        stco_base = stco["offset"] + stco["header"] + 4
        chunk_count = self._u(data, stco_base, 4)
        chunk_offsets = []
        entry_size = 8 if use_co64 else 4
        for i in range(chunk_count):
            p = stco_base + 4 + i * entry_size
            chunk_offsets.append(self._u(data, p, entry_size))
        result = []
        sample_idx = 0
        for chunk_idx in range(chunk_count):
            if sample_idx >= sample_count:
                break
            interval_idx = stsc_count - 1
            for k in range(stsc_count):
                if chunk_idx + 1 < first_chunks[k]:
                    interval_idx = k - 1
                    break
            spc = samples_per_chunk[interval_idx] if interval_idx >= 0 else 0
            chunk_base = chunk_offsets[chunk_idx]
            off = chunk_base
            for _ in range(spc):
                if sample_idx >= sample_count:
                    break
                result.append([off, sample_sizes[sample_idx]])
                off += sample_sizes[sample_idx]
                sample_idx += 1
        return result

    def _decrypt_sample(self, key, iv, sample_data, subsample_ranges):
        if not subsample_ranges:
            return self._ctr_decrypt(key, iv, sample_data)
        output = bytearray(len(sample_data))
        enc_segments = []
        enc_stream = bytearray()
        src_pos = 0
        dst_pos = 0
        for r in subsample_ranges:
            clear_len = r[0]
            enc_len = r[1]
            output[dst_pos:dst_pos + clear_len] = sample_data[src_pos:src_pos + clear_len]
            dst_pos += clear_len
            enc_segments.append([dst_pos, enc_len])
            enc_stream.extend(sample_data[src_pos + clear_len:src_pos + clear_len + enc_len])
            dst_pos += enc_len
            src_pos += clear_len + enc_len
        decrypted_enc = self._ctr_decrypt(key, iv, bytes(enc_stream))
        dec_pos = 0
        for seg in enc_segments:
            seg_offset = seg[0]
            seg_len = seg[1]
            output[seg_offset:seg_offset + seg_len] = decrypted_enc[dec_pos:dec_pos + seg_len]
            dec_pos += seg_len
        return bytes(output)

    def _cenc_decrypt(self, data, key_hex):
        content_key = self._hex_to_bytes(key_hex)
        if len(content_key) != 16:
            raise ValueError("content key 必须 16B")
        mp4 = bytearray(data)
        boxes = self._cenc_parse(mp4, 0, len(mp4))
        moov = self._cenc_find(boxes, "moov")
        if moov is None:
            raise Exception("无 moov")
        traks = []
        self._cenc_find_all(moov["children"], "trak", traks)
        for trak in traks:
            stbl = self._cenc_find(trak["children"], "stbl")
            senc = self._cenc_find(trak["children"], "senc")
            if stbl is None or senc is None:
                continue
            tenc = self._cenc_find(trak["children"], "tenc")
            if tenc is not None:
                pos = tenc["offset"] + tenc["header"] + 7
                default_iv_len = mp4[pos] & 0xff
            else:
                default_iv_len = 8
            frma = self._cenc_find(trak["children"], "frma")
            original_type = None
            if frma is not None:
                pos = frma["offset"] + frma["header"]
                original_type = mp4[pos:pos + 4]
            sample_offsets = self._sample_offsets(mp4, stbl["children"])
            ivs, subsamples = self._parse_senc(mp4, senc, default_iv_len)
            sample_count = min(len(sample_offsets), len(ivs), len(subsamples))
            for i in range(sample_count):
                offset = sample_offsets[i][0]
                size = sample_offsets[i][1]
                sample_data = bytes(mp4[offset:offset + size])
                iv = ivs[i]
                subs = subsamples[i]
                decrypted = self._decrypt_sample(content_key, iv, sample_data, subs)
                mp4[offset:offset + size] = decrypted
            if original_type is not None:
                for enc_type in ("encv", "enca"):
                    enc_box = self._cenc_find(trak["children"], enc_type)
                    if enc_box is not None:
                        type_pos = enc_box["offset"] + 4
                        mp4[type_pos:type_pos + 4] = original_type
            free_bytes = b"free"
            for drm_type in ("sinf", "schi", "saio", "saiz"):
                drm_box = self._cenc_find(trak["children"], drm_type)
                if drm_box is not None:
                        type_pos = drm_box["offset"] + 4
                        mp4[type_pos:type_pos + 4] = free_bytes
        return bytes(mp4)

    # ============================================================
    # GuoGuoCenc - 按 Range 解密
    # ============================================================

    @staticmethod
    def _parse_content_range(value):
        if not value:
            return None
        match = re.search(r"bytes\s+(\d+)-(\d+)/(\d+|\*)", str(value), re.I)
        if not match:
            return None
        total = 0 if match.group(3) == "*" else int(match.group(3))
        return int(match.group(1)), int(match.group(2)), total

    def _partial_range_fetch_lock(self, url):
        with self._PARTIAL_RANGE_FETCH_LOCKS_LOCK:
            lock = self._PARTIAL_RANGE_FETCH_LOCKS.get(url)
            if lock is None:
                lock = threading.Lock()
                self._PARTIAL_RANGE_FETCH_LOCKS[url] = lock
            return lock

    def _http_get_range(self, url, start, end):
        # IJK 可能同时打开 200 连续流和 206 定位请求；同一源视频的
        # 回源 Range 串行执行，避免重叠请求互相拖住。
        with self._partial_range_fetch_lock(url):
            return self._http_get_range_locked(url, start, end)

    def _http_get_range_locked(self, url, start, end):
        """请求源 MP4 的一段数据，返回 (bytes, 实际起点, 总长度)。"""
        if start < 0 or end < start:
            raise ValueError("bad source range")
        started = time.time()
        req_headers = {"User-Agent": self.PROXY_UA, "Range": "bytes=%d-%d" % (start, end)}
        response = None
        try:
            response = self.fetch(url, headers=req_headers, timeout=30, stream=True)
            if response is None:
                raise Exception("empty response")
            status = int(getattr(response, "status_code", 0) or 0)
            response_headers = getattr(response, "headers", {}) or {}
            range_info = self._parse_content_range(response_headers.get("Content-Range"))
            actual_start = range_info[0] if range_info else 0
            total = range_info[2] if range_info else 0
            content_length = response_headers.get("Content-Length", "")
            try:
                content_length = int(content_length)
            except Exception:
                content_length = 0
            if total <= 0 and status == 200 and content_length > 0:
                total = content_length

            wanted = end - start + 1
            # CDN 偶尔忽略 Range 返回 200。此时只读到目标位置，避免把整段
            # MP4 再复制一遍；如果真的不支持 Range，start>0 会多读并丢弃前缀。
            read_limit = wanted if status == 206 else end + 1
            data = bytearray()
            iterator = response.iter_content(chunk_size=64 * 1024) if hasattr(response, "iter_content") else None
            if iterator is not None:
                for chunk in iterator:
                    if not chunk:
                        continue
                    data.extend(chunk)
                    if len(data) >= read_limit:
                        break
            elif hasattr(response, "content"):
                data.extend(response.content[:read_limit])
            else:
                data.extend(response.read(read_limit))

            if status == 206:
                if actual_start != start:
                    raise Exception("source range start mismatch")
                body = bytes(data[:wanted])
            else:
                if len(data) < end + 1:
                    raise Exception("source ignored Range and returned short body")
                body = bytes(data[start:end + 1])
                actual_start = start
            if len(body) != wanted:
                raise Exception("source range short body %d/%d" % (len(body), wanted))
            elapsed_ms = int((time.time() - started) * 1000)
            if start == 0 or elapsed_ms >= 2000:
                print("echo-GuoGuo代理 回源=%d-%d status=%d bytes=%d time=%dms" %
                      (start, end, status, len(body), elapsed_ms))
            return body, actual_start, total
        except Exception:
            # 保留 urllib 兜底，兼容 requests 在部分 Chaquopy 环境不可用的情况。
            try:
                req = urllib.request.Request(url, headers=req_headers, method="GET")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read()
                    range_info = self._parse_content_range(resp.headers.get("Content-Range"))
                    if range_info:
                        body = raw[:end - start + 1]
                        elapsed_ms = int((time.time() - started) * 1000)
                        print("echo-GuoGuo代理 回源=%d-%d status=urllib bytes=%d time=%dms" %
                              (start, end, len(body), elapsed_ms))
                        return body, range_info[0], range_info[2]
                    if len(raw) < end + 1:
                        raise Exception("source fallback short body")
                    body = raw[start:end + 1]
                    elapsed_ms = int((time.time() - started) * 1000)
                    print("echo-GuoGuo代理 回源=%d-%d status=urllib bytes=%d time=%dms" %
                          (start, end, len(body), elapsed_ms))
                    return body, start, len(raw)
            except Exception as fallback_error:
                raise Exception("range request failed: " + str(fallback_error))
        finally:
            try:
                if response is not None:
                    response.close()
            except Exception:
                pass

    @staticmethod
    def _top_box_header(data, wanted_type):
        """只读取顶层 box 头，允许 box 本体尚未全部读完。"""
        pos = 0
        end = len(data)
        while pos + 8 <= end:
            size = int.from_bytes(data[pos:pos + 4], "big")
            typ = data[pos + 4:pos + 8].decode("latin1", errors="ignore")
            header = 8
            if size == 1:
                if pos + 16 > end:
                    return None
                size = int.from_bytes(data[pos + 8:pos + 16], "big")
                header = 16
            elif size == 0:
                return None
            if size < header:
                return None
            if typ == wanted_type:
                return pos, size, header
            if pos + 8 > end:
                return None
            pos += size
        return None

    def _partial_meta_key(self, url, key):
        return self._md5_lower(url + "|" + key)

    def _partial_track_index(self, data, stbl_children, senc, default_iv_len):
        """保存 sample 表的位置；实际 sample 在播放到对应 Range 时才展开。"""
        stsz = self._cenc_find(stbl_children, "stsz")
        stsc = self._cenc_find(stbl_children, "stsc")
        stco = self._cenc_find(stbl_children, "stco")
        use_co64 = False
        if stco is None:
            stco = self._cenc_find(stbl_children, "co64")
            use_co64 = True
        if stsz is None or stsc is None or stco is None:
            return None

        stsz_base = stsz["offset"] + stsz["header"] + 4
        uniform_size = self._u(data, stsz_base, 4)
        sample_count = self._u(data, stsz_base + 4, 4)
        size_pos = stsz_base + 8

        stsc_base = stsc["offset"] + stsc["header"] + 4
        stsc_count = self._u(data, stsc_base, 4)
        stsc_entries = []
        for i in range(stsc_count):
            pos = stsc_base + 4 + i * 12
            stsc_entries.append([self._u(data, pos, 4), self._u(data, pos + 4, 4)])
        if not stsc_entries:
            return None

        stco_base = stco["offset"] + stco["header"] + 4
        chunk_count = self._u(data, stco_base, 4)
        entry_size = 8 if use_co64 else 4
        if chunk_count <= 0:
            return None

        senc_base = senc["offset"] + senc["header"]
        flags = self._u(data, senc_base + 1, 3)
        senc_count = self._u(data, senc_base + 4, 4)
        sample_count = min(sample_count, senc_count)
        if sample_count <= 0:
            return None

        first_chunk_offset = self._u(data, stco_base + 4, entry_size)
        return {
            "sample_count": sample_count,
            "uniform_size": uniform_size,
            "size_pos": size_pos,
            "stsc": stsc_entries,
            "chunk_count": chunk_count,
            "chunk_pos": stco_base + 4,
            "chunk_entry_size": entry_size,
            "iv_len": default_iv_len,
            "has_subsamples": (flags & 0x02) != 0,
            "senc_pos": senc_base + 8,
            "next_sample": 0,
            "next_chunk": 0,
            "next_in_chunk": 0,
            "stsc_index": 0,
            "next_offset": first_chunk_offset,
            "samples": [],
        }

    def _partial_track_next_sample(self, data, track):
        """顺序展开一个 sample。正常播放时每个 sample 只解析一次。"""
        sample_index = track["next_sample"]
        if sample_index >= track["sample_count"] or track["next_chunk"] >= track["chunk_count"]:
            return None

        uniform_size = track["uniform_size"]
        if uniform_size:
            sample_size = uniform_size
        else:
            sample_size = self._u(data, track["size_pos"] + sample_index * 4, 4)
        if sample_size <= 0:
            return None

        pos = track["senc_pos"]
        iv_len = track["iv_len"]
        iv = bytes(data[pos:pos + iv_len])
        if len(iv) != iv_len:
            return None
        pos += iv_len
        subs = []
        if track["has_subsamples"]:
            subsample_count = self._u(data, pos, 2)
            pos += 2
            for _ in range(subsample_count):
                subs.append([self._u(data, pos, 2), self._u(data, pos + 2, 4)])
                pos += 6

        sample = {
            "offset": track["next_offset"],
            "size": sample_size,
            "iv": iv,
            "subs": subs,
        }
        track["samples"].append(sample)
        track["senc_pos"] = pos
        track["next_sample"] = sample_index + 1

        samples_per_chunk = track["stsc"][track["stsc_index"]][1]
        if track["next_in_chunk"] + 1 >= samples_per_chunk:
            next_chunk = track["next_chunk"] + 1
            track["next_chunk"] = next_chunk
            track["next_in_chunk"] = 0
            while (track["stsc_index"] + 1 < len(track["stsc"])
                   and next_chunk + 1 >= track["stsc"][track["stsc_index"] + 1][0]):
                track["stsc_index"] += 1
            if next_chunk < track["chunk_count"]:
                chunk_pos = track["chunk_pos"] + next_chunk * track["chunk_entry_size"]
                track["next_offset"] = self._u(data, chunk_pos, track["chunk_entry_size"])
        else:
            track["next_in_chunk"] += 1
            track["next_offset"] += sample_size
        return sample

    def _partial_samples_for_range(self, meta, start, end):
        """按需扩展各轨的 sample 缓存，返回当前 Range 覆盖的 sample。"""
        data = meta["head"]
        matches = []
        with meta["sample_lock"]:
            for track in meta.get("tracks", []):
                samples = track["samples"]
                while True:
                    if samples and samples[-1]["offset"] > end:
                        break
                    sample = self._partial_track_next_sample(data, track)
                    if sample is None or sample["offset"] > end:
                        break
                for sample in samples:
                    sample_start = sample["offset"]
                    sample_end = sample_start + sample["size"] - 1
                    if sample_end < start:
                        continue
                    if sample_start > end:
                        break
                    matches.append(sample)
        matches.sort(key=lambda item: item["offset"])
        return matches

    def _load_partial_meta(self, url, key):
        """仅下载并解析 ftyp/moov，延迟展开 CENC sample。"""
        cache_key = self._partial_meta_key(url, key)
        with self._PARTIAL_META_CACHE_LOCK:
            cached = self._PARTIAL_META_CACHE.get(cache_key)
            if cached is not None:
                return cached
        with self._PARTIAL_META_LOAD_LOCKS_LOCK:
            load_lock = self._PARTIAL_META_LOAD_LOCKS.get(cache_key)
            if load_lock is None:
                load_lock = threading.Lock()
                self._PARTIAL_META_LOAD_LOCKS[cache_key] = load_lock
        with load_lock:
            with self._PARTIAL_META_CACHE_LOCK:
                cached = self._PARTIAL_META_CACHE.get(cache_key)
                if cached is not None:
                    return cached

            # 首播先拉取较小探测段；如果 moov 未完整包含在其中，再按 moov
            # 实际结束位置补拉，避免每次首播固定等待 1MB。
            probe_end = self._PARTIAL_RANGE_MAX - 1
            probe, probe_start, total = self._http_get_range(url, 0, probe_end)
            if probe_start != 0:
                raise Exception("metadata range must start at zero")
            moov_header = self._top_box_header(probe, "moov")
            if moov_header is None:
                # 常规文件 moov 在前；没有可识别的前置 moov 时交给整段兜底。
                raise Exception("moov not found in head")
            moov_offset, moov_size, _ = moov_header
            moov_end = moov_offset + moov_size
            if len(probe) >= moov_end:
                head = probe[:moov_end]
                source_prefix = probe
            else:
                head, head_start, head_total = self._http_get_range(url, 0, moov_end - 1)
                if head_start != 0 or len(head) < moov_end:
                    raise Exception("moov range short body")
                source_prefix = head
                if total <= 0:
                    total = head_total
            if total <= 0:
                total = moov_end

            mp4 = bytearray(head)
            boxes = self._cenc_parse(mp4, 0, len(mp4))
            moov = self._cenc_find(boxes, "moov")
            if moov is None:
                raise Exception("invalid moov")
            traks = []
            self._cenc_find_all(moov["children"], "trak", traks)
            patches = []
            tracks = []
            content_key = self._hex_to_bytes(key)
            if len(content_key) != 16:
                raise ValueError("content key 必须 16B")
            for trak in traks:
                stbl = self._cenc_find(trak["children"], "stbl")
                senc = self._cenc_find(trak["children"], "senc")
                if stbl is None or senc is None:
                    continue
                tenc = self._cenc_find(trak["children"], "tenc")
                if tenc is not None:
                    pos = tenc["offset"] + tenc["header"] + 7
                    default_iv_len = mp4[pos] & 0xff
                else:
                    default_iv_len = 8
                track = self._partial_track_index(mp4, stbl["children"], senc, default_iv_len)
                if track is not None:
                    tracks.append(track)

                frma = self._cenc_find(trak["children"], "frma")
                if frma is not None:
                    original_type = bytes(mp4[frma["offset"] + frma["header"]:frma["offset"] + frma["header"] + 4])
                    for enc_type in ("encv", "enca"):
                        enc_box = self._cenc_find(trak["children"], enc_type)
                        if enc_box is not None:
                            patches.append([enc_box["offset"] + 4, original_type])
                for drm_type in ("sinf", "schi", "saio", "saiz"):
                    drm_box = self._cenc_find(trak["children"], drm_type)
                    if drm_box is not None:
                        patches.append([drm_box["offset"] + 4, b"free"])

            meta = {
                "url": url,
                "key": key,
                "content_key": content_key,
                "total": int(total),
                "head": bytes(head),
                "head_end": len(head),
                "source_prefix": bytes(source_prefix),
                "source_prefix_end": len(source_prefix),
                "patches": patches,
                "tracks": tracks,
                "sample_lock": threading.Lock(),
            }
            with self._PARTIAL_META_CACHE_LOCK:
                self._PARTIAL_META_CACHE[cache_key] = meta
                if len(self._PARTIAL_META_CACHE) > 16:
                    oldest = list(self._PARTIAL_META_CACHE.keys())[0]
                    self._PARTIAL_META_CACHE.pop(oldest, None)
            sample_count = sum(track["sample_count"] for track in tracks)
            print("echo-GuoGuo代理 索引完成 moov=%d prefix=%d tracks=%d samples=%d total=%d" %
                  (len(head), len(source_prefix), len(tracks), sample_count, int(total)))
            return meta

    def _partial_source_range(self, meta, start, end):
        """优先复用已下载的 moov，再只回源 mdat 所需区间。"""
        prefix_end = int(meta.get("source_prefix_end", meta.get("head_end", 0)))
        prefix = meta.get("source_prefix", meta.get("head", b""))
        pieces = []
        if start < prefix_end:
            prefix_end_part = min(end + 1, prefix_end)
            pieces.append(bytes(prefix[start:prefix_end_part]))
        remote_start = max(start, prefix_end)
        if remote_start <= end:
            remote, actual_start, _ = self._http_get_range(meta["url"], remote_start, end)
            if actual_start != remote_start:
                raise Exception("source data range mismatch")
            pieces.append(remote)
        body = b"".join(pieces)
        expected = end - start + 1
        if len(body) != expected:
            raise Exception("assembled range short body %d/%d" % (len(body), expected))
        return body

    def _partial_transform_range(self, meta, start, end):
        """回源一个 Range，补齐被截断的 sample 后逐 sample 解密。"""
        fetch_start = start
        fetch_end = end
        overlaps = self._partial_samples_for_range(meta, start, end)
        for sample in overlaps:
            sample_start = int(sample["offset"])
            sample_end = sample_start + int(sample["size"]) - 1
            fetch_start = min(fetch_start, sample_start)
            fetch_end = max(fetch_end, sample_end)
        payload = bytearray(self._partial_source_range(meta, fetch_start, fetch_end))
        for patch_pos, patch_value in meta.get("patches", []):
            patch_end = patch_pos + len(patch_value)
            if patch_end <= fetch_start or patch_pos > fetch_end:
                continue
            rel = patch_pos - fetch_start
            if rel >= 0 and rel + len(patch_value) <= len(payload):
                payload[rel:rel + len(patch_value)] = patch_value
        for sample in overlaps:
            sample_start = int(sample["offset"])
            sample_end = sample_start + int(sample["size"])
            rel_start = sample_start - fetch_start
            sample_data = bytes(payload[rel_start:rel_start + int(sample["size"])])
            decrypted = self._decrypt_sample(meta["content_key"], sample["iv"], sample_data, sample["subs"])
            payload[rel_start:rel_start + len(decrypted)] = decrypted
        rel = start - fetch_start
        return bytes(payload[rel:rel + end - start + 1])

    @staticmethod
    def _parse_player_range(value, total, max_size):
        if not value or not str(value).lower().startswith("bytes="):
            return None
        raw = str(value)[6:].split(",", 1)[0].strip()
        left, sep, right = raw.partition("-")
        if not sep:
            return "invalid"
        try:
            if not left:
                suffix = int(right)
                if suffix <= 0:
                    return "invalid"
                start = max(0, total - suffix)
                end = total - 1
            else:
                start = int(left)
                if start < 0 or start >= total:
                    return "invalid"
                end = int(right) if right else min(total - 1, start + max_size - 1)
                end = min(end, total - 1, start + max_size - 1)
            return start, end
        except Exception:
            return "invalid"

    # ============================================================
    # GuoGuoProxy - 视频代理
    # ============================================================

    @staticmethod
    def _md5_lower(s):
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def _load_clear(self, url, key, cancel_check=None):
        if _is_cancel_requested(cancel_check):
            return None
        cache_key = self._md5_lower(url + "|" + key)
        # 优先从类级缓存取
        with self._PROXY_CACHE_LOCK:
            cached = self._PROXY_CACHE.get(cache_key)
            if cached is not None:
                return cached
        # 再从全局缓存取 (跨实例, 不受 destroy 影响)
        with self._GLOBAL_PROXY_CACHE_LOCK:
            cached = self._GLOBAL_PROXY_CACHE.get(cache_key)
            if cached is not None:
                # 回填到类级缓存
                with self._PROXY_CACHE_LOCK:
                    self._PROXY_CACHE[cache_key] = cached
                return cached
        with self._PROXY_LOAD_LOCKS_LOCK:
            load_lock = self._PROXY_LOAD_LOCKS.get(cache_key)
            if load_lock is None:
                load_lock = threading.Lock()
                self._PROXY_LOAD_LOCKS[cache_key] = load_lock
        with load_lock:
            if _is_cancel_requested(cancel_check):
                return None
            # 播放器超时重试时，复查缓存，避免重复下载同一视频。
            with self._PROXY_CACHE_LOCK:
                cached = self._PROXY_CACHE.get(cache_key)
                if cached is not None:
                    return cached
            with self._GLOBAL_PROXY_CACHE_LOCK:
                cached = self._GLOBAL_PROXY_CACHE.get(cache_key)
                if cached is not None:
                    with self._PROXY_CACHE_LOCK:
                        self._PROXY_CACHE[cache_key] = cached
                    return cached

            try:
                data = self._http_get_bytes(url, {"User-Agent": self.PROXY_UA}, cancel_check)
            except Exception as e:
                raise Exception(f"cdn http error (load): {e}")
            if _is_cancel_requested(cancel_check):
                return None
            if not data:
                raise Exception(f"cdn http error: empty body, url_len={len(url)}")
            try:
                clear = self._cenc_decrypt(data, key)
            except Exception as e:
                raise Exception(f"cdn decrypt error: {e}")
            if _is_cancel_requested(cancel_check):
                return None
            with self._PROXY_CACHE_LOCK:
                self._PROXY_CACHE[cache_key] = clear
            with self._GLOBAL_PROXY_CACHE_LOCK:
                self._GLOBAL_PROXY_CACHE[cache_key] = clear
                if len(self._GLOBAL_PROXY_CACHE) > 8:
                    oldest = list(self._GLOBAL_PROXY_CACHE.keys())[0]
                    self._GLOBAL_PROXY_CACHE.pop(oldest, None)
            return clear

    def _prefetch_proxy(self, url, key):
        """后台预热视频，给播放器打开本地代理留出下载时间。"""
        cache_key = self._md5_lower(url + "|" + key)
        with self._PROXY_PREFETCH_LOCK:
            thread = self._PROXY_PREFETCH_THREADS.get(cache_key)
            if thread is not None and thread.is_alive():
                return

            def load():
                try:
                    self._load_clear(url, key)
                except Exception as e:
                    print("echo-GuoGuo代理 预热失败: %s" % e)

            thread = threading.Thread(target=load, name="GuoGuoProxyPrefetch", daemon=True)
            self._PROXY_PREFETCH_THREADS[cache_key] = thread
            thread.start()

    def _register_token(self, url, key):
        """生成 token (短 hash, 依赖内存缓存)

        为了兼容老 TVBox 框架, 使用短 hash token, 内存缓存保存 url+key 映射.
        destroy() 调用后 token 失效, 但全局代理缓存 _GLOBAL_PROXY_CACHE 仍可用.
        """
        # 短 hash token (20 字符), 避免 URL 超长
        token_src = url + "|" + key + "|" + str(time.time())
        token = hashlib.md5(token_src.encode("utf-8")).hexdigest()[:20]
        # 缓存到内存 (跨 destroy 之前有效)
        with self._PROXY_TOKENS_LOCK:
            self._PROXY_TOKENS[token] = [url, key, time.time() + 7200]  # 2小时过期
            if len(self._PROXY_TOKENS) > 32:
                oldest = list(self._PROXY_TOKENS.keys())[0]
                self._PROXY_TOKENS.pop(oldest, None)
        return token

    def _resolve_token(self, token):
        """从 token 解析 url+key (从内存缓存取)"""
        if not self._is_empty(token):
            with self._PROXY_TOKENS_LOCK:
                entry = self._PROXY_TOKENS.get(token)
            if entry is not None:
                return entry[0], entry[1]
        return None, None

    # ============================================================
    # GuoGuoProxy - 整段 MP4 兜底
    # ============================================================
    #
    # 当本地按 Range 流服务不可用时，保留原完整解密路径作为兼容兜底。
    #

    # 临时文件目录
    _PROXY_TMP_DIR = "/tmp/guoguo_proxy"
    # pdata 短 token 长度
    _PROXY_TOKEN_LEN = 16

    def _ensure_tmp_dir(self):
        """确保临时目录存在"""
        try:
            import os
            if not os.path.isdir(self._PROXY_TMP_DIR):
                os.makedirs(self._PROXY_TMP_DIR, exist_ok=True)
        except Exception:
            pass

    def _build_pdata(self, url, key, need_decrypt):
        """构造 base64 编码的自包含 pdata (跨 destroy 仍有效)

        参考蓝天: 用 base64(JSON) 包含全部回源信息, 不依赖任何内存缓存.
        """
        pdata_obj = {
            "u": url,
            "k": key,
            "n": 1 if need_decrypt else 0,
        }
        raw = json.dumps(pdata_obj, separators=(",", ":")).encode("utf-8")
        # urlsafe base64, 去掉 padding
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    def _decode_pdata(self, pdata_b64):
        """解析 base64 编码的 pdata"""
        if not pdata_b64:
            return None
        pdata_b64 = pdata_b64.strip()
        try:
            padded = pdata_b64 + "=" * (-len(pdata_b64) % 4)
            raw = base64.urlsafe_b64decode(padded.encode("ascii"))
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict):
                return None
            return obj
        except Exception:
            return None

    def _proxy_play_url(self, url, key, need_decrypt, preload,
                        prefetch_vid="", prefetch_quality="", prefetch_generation=0):
        """返回本地代理 URL

        关键: 走本地 HTTP 流服务：
              - 已完整缓存的 MP4 直接读磁盘
              - 首播只取 moov 和当前 sample，按播放器进度继续解密

        兜底: 如果流式 server 启动失败, 退回 pdata 模式 (一次性 12MB bytes).
        """
        if self._is_empty(url):
            return ""
        if not need_decrypt:
            return url
        if self._is_empty(key):
            return url
        key = key.strip()
        try:
            # 命中完整缓存时直接走磁盘；首次播放则直接注册按 Range 的
            # 本地 CENC 代理，播放器读到哪里才回源并解密到哪里。
            cache_key = self._md5_lower(url + "|" + key)
            cache_dir = self._stream_cache_dir()
            cached_path = _os_path_join(cache_dir, cache_key + ".mp4") if cache_dir else ""
            if cached_path and _os_path_exists(cached_path) and _os_path_getsize(cached_path) > 0:
                stream_url = self._stream_register(
                    cached_path, "video/mp4", self, prefetch_vid, prefetch_quality, prefetch_generation)
                if stream_url:
                    return stream_url
            return self._stream_register_partial(
                self, url, key, "video/mp4", prefetch_vid, prefetch_quality, prefetch_generation)
        except Exception as e:
            try:
                print("echo-GuoGuo流式 _proxy_play_url 失败:", e)
            except Exception:
                pass
            return ""

    def _stream_file_lock(self, cache_key):
        with self._STREAM_FILE_LOCKS_LOCK:
            lock = self._STREAM_FILE_LOCKS.get(cache_key)
            if lock is None:
                lock = threading.Lock()
                self._STREAM_FILE_LOCKS[cache_key] = lock
            return lock

    def _drop_clear_cache(self, cache_key):
        with self._PROXY_CACHE_LOCK:
            self._PROXY_CACHE.pop(cache_key, None)
        with self._GLOBAL_PROXY_CACHE_LOCK:
            self._GLOBAL_PROXY_CACHE.pop(cache_key, None)

    def _stream_cache_dir(self):
        cls = type(self)
        with cls._STREAM_CACHE_DIR_LOCK:
            if cls._STREAM_CACHE_DIR and os.path.isdir(cls._STREAM_CACHE_DIR):
                return cls._STREAM_CACHE_DIR
            candidates = ["/tmp/guoguo_stream"]
            try:
                runtime_tmp = tempfile.gettempdir()
                if runtime_tmp:
                    candidates.append(_os_path_join(runtime_tmp, "guoguo_stream"))
            except Exception:
                pass
            try:
                candidates.append(_os_path_join(os.path.expanduser("~"), "guoguo_stream"))
            except Exception:
                pass
            try:
                candidates.append(_os_path_join(os.getcwd(), "guoguo_stream"))
            except Exception:
                pass
            for path in candidates:
                try:
                    _os_makedirs(path, exist_ok=True)
                    probe_path = _os_path_join(path, ".guoguo_write_%d" % threading.get_ident())
                    with open(probe_path, "wb") as f:
                        f.write(b"")
                    os.remove(probe_path)
                    cls._STREAM_CACHE_DIR = path
                    return path
                except Exception:
                    pass
            cls._STREAM_CACHE_DIR = ""
            return ""

    def _trim_stream_cache(self, keep_path):
        try:
            tmp_dir = os.path.dirname(keep_path)
            protected_paths = {keep_path}
            with self._STREAM_ITEMS_LOCK:
                for item in self._STREAM_ITEMS.values():
                    path = item.get("path", "")
                    if path:
                        protected_paths.add(path)
            entries = []
            for name in os.listdir(tmp_dir):
                if not name.endswith(".mp4"):
                    continue
                path = _os_path_join(tmp_dir, name)
                try:
                    entries.append((os.path.getmtime(path), path))
                except Exception:
                    pass
            entries.sort(reverse=True)
            for _, path in entries[self._STREAM_CACHE_MAX:]:
                if path not in protected_paths:
                    try:
                        os.remove(path)
                    except Exception:
                        pass
        except Exception:
            pass

    def _cache_stream_file(self, url, key, cancel_check=None):
        """下载解密后写入磁盘，供下一集直接走本地 Range 读取。"""
        if _is_cancel_requested(cancel_check):
            return ""
        cache_key = self._md5_lower(url + "|" + key)
        tmp_dir = self._stream_cache_dir()
        if not tmp_dir:
            raise Exception("stream cache directory unavailable")
        tmp_path = _os_path_join(tmp_dir, cache_key + ".mp4")
        with self._stream_file_lock(cache_key):
            if _is_cancel_requested(cancel_check):
                return ""
            if _os_path_exists(tmp_path) and _os_path_getsize(tmp_path) > 0:
                return tmp_path
            clear = self._load_clear(url, key, cancel_check)
            if _is_cancel_requested(cancel_check):
                return ""
            if not clear:
                return ""
            part_path = tmp_path + ".part." + str(threading.get_ident())
            try:
                with open(part_path, "wb") as f:
                    f.write(clear)
                if _is_cancel_requested(cancel_check):
                    return ""
                os.replace(part_path, tmp_path)
            finally:
                try:
                    if _os_path_exists(part_path):
                        os.remove(part_path)
                except Exception:
                    pass
            self._drop_clear_cache(cache_key)
        self._trim_stream_cache(tmp_path)
        return tmp_path

    def _prefetch_next_episode(self, next_vid, quality, generation):
        if not self.is_vid(next_vid) or not self._is_play_request_current(generation):
            return
        quality = quality or self.quality
        thread_key = str(next_vid) + "::" + str(quality) + "::" + str(generation)
        with self._NEXT_EPISODE_PREFETCH_LOCK:
            existing = self._NEXT_EPISODE_PREFETCH_THREADS.get(thread_key)
            if existing is not None and existing.is_alive():
                return

            def preload():
                try:
                    # 当前集已开始向播放器发送数据后，再让下一集占用带宽。
                    time.sleep(self._NEXT_EPISODE_PREFETCH_DELAY)
                    if not self._is_play_request_current(generation):
                        return
                    model = self._load_video_model(next_vid, quality)
                    if not self._is_play_request_current(generation):
                        return
                    ranked = self._rank_qualities(model, quality)
                    if not ranked:
                        raise Exception("no playable quality")
                    last_error = None
                    for tier in ranked:
                        if not self._is_play_request_current(generation):
                            return
                        try:
                            url, key = self._tier_source(tier)
                            cancel_check = lambda: not self._is_play_request_current(generation)
                            if self._cache_stream_file(url, key, cancel_check):
                                return
                        except Exception as e:
                            last_error = e
                    if last_error is not None:
                        raise last_error
                    raise Exception("missing main_url/spade_a")
                except Exception as e:
                    print("echo-GuoGuo代理 下一集预下载失败: %s" % e)
                finally:
                    with self._NEXT_EPISODE_PREFETCH_LOCK:
                        if self._NEXT_EPISODE_PREFETCH_THREADS.get(thread_key) is threading.current_thread():
                            self._NEXT_EPISODE_PREFETCH_THREADS.pop(thread_key, None)

            thread = threading.Thread(target=preload, name="GuoGuoNextEpisodePrefetch", daemon=True)
            self._NEXT_EPISODE_PREFETCH_THREADS[thread_key] = thread
            thread.start()

    def _make_stream_url(self, url, key):
        """把解密后的 MP4 写到磁盘, 注册到流式 server, 返回 http://127.0.0.1:PORT/stream/<token> URL"""
        try:
            tmp_path = self._cache_stream_file(url, key)
            if not tmp_path:
                return ""
            # 注册到流式 server
            return self._stream_register(tmp_path, "video/mp4")
        except Exception as e:
            try:
                print("echo-GuoGuo流式 _make_stream_url 失败:", e)
            except Exception:
                pass
            return ""

    def localProxy(self, param):
        """处理本地代理请求, 返回完整解密后的 MP4 视频

        同时支持 pdata 模式 (推荐) 和 短 hash t= 模式 (兼容老版本).
        - pdata: base64(JSON) 自包含, 跨 destroy() 仍可解析
        - t=:    短 hash, 依赖 _PROXY_TOKENS 内存缓存

        返回 [status, mime, bytes] (TVBox 框架标准格式).
        """
        try:
            if not isinstance(param, dict):
                if isinstance(param, str):
                    param = self._parse_query(param)
                else:
                    param = {}

            # 模式 1: pdata (推荐, 跨 destroy 有效)
            pdata_b64 = param.get("pdata") or ""
            url, key = "", ""
            if pdata_b64:
                pd = self._decode_pdata(pdata_b64)
                if isinstance(pd, dict):
                    url = str(pd.get("u") or "")
                    key = str(pd.get("k") or "")

            # 模式 2: 短 hash t= (兜底, 内存缓存)
            if (not url or not key):
                token = param.get("t") or param.get("token") or ""
                token = str(token).strip()
                if token:
                    url, key = self._resolve_token(token)

            if not url or not key:
                return [404, "text/plain; charset=utf-8", b"invalid or expired proxy param"]

            # 播放器通常先请求 Range: bytes=0-，只需把 moov 和当前 sample
            # 返回即可。该分支不把整部加密 MP4 传过 Python/Java 桥。
            range_value = param.get("range") or param.get("Range") or ""
            if range_value:
                try:
                    meta = self._load_partial_meta(url, key)
                    total = int(meta.get("total", 0))
                    requested = self._parse_player_range(range_value, total, self._PARTIAL_RANGE_MAX)
                    if requested == "invalid" or total <= 0:
                        return [416, "video/mp4", b"", {
                            "Content-Range": "bytes */%d" % max(0, total),
                            "Accept-Ranges": "bytes",
                            "Content-Length": "0",
                        }]
                    start, end = requested if requested else (0, min(total - 1, self._PARTIAL_RANGE_MAX - 1))
                    body = self._partial_transform_range(meta, start, end)
                    return [206, "video/mp4", body, {
                        "Content-Range": "bytes %d-%d/%d" % (start, end, total),
                        "Accept-Ranges": "bytes",
                        "Content-Length": str(len(body)),
                        "Cache-Control": "no-store",
                    }]
                except Exception as range_error:
                    print("echo-GuoGuo代理 分段失败，回退整段: %s" % range_error)

            clear_data = self._load_clear(url, key)
            if not clear_data:
                return [500, "text/plain; charset=utf-8", b"decrypt failed: empty data"]

            # 返回 bytes (TVBox 框架对 [code, mime, bytes] 兼容性最好)
            if isinstance(clear_data, (bytes, bytearray)):
                body = bytes(clear_data)
            else:
                body = str(clear_data).encode("utf-8")
            return [200, "video/mp4", body]
        except Exception as e:
            try:
                err = f"proxy error: {e}".encode("utf-8")
            except Exception:
                err = b"proxy error"
            return [500, "text/plain; charset=utf-8", err]

    @staticmethod
    def _parse_query(query_str):
        """解析 URL 查询字符串为 dict"""
        result = {}
        try:
            if "?" in query_str:
                query_str = query_str.split("?", 1)[1]
            if "#" in query_str:
                query_str = query_str.split("#", 1)[0]
            for pair in query_str.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    result[urllib.parse.unquote(k)] = urllib.parse.unquote(v)
                elif pair:
                    result[urllib.parse.unquote(pair)] = ""
        except Exception:
            pass
        return result

    # ============================================================
    # Spider 辅助方法 (来自 GuoGuo.java)
    # ============================================================

    def _pick(self, extend, key, default=""):
        if not extend:
            return default
        if key not in extend:
            return default
        value = extend[key]
        if self._is_empty(value):
            return default
        return value

    def _land_videos(self, category_id, param1, param2, param3, offset, count):
        result = self._landpage(category_id, param1, param2, param3, offset, count, "only_content")
        data = result.get("data") if isinstance(result, dict) else None
        if isinstance(data, dict) and "video_data" in data:
            return self._extract_videos(data.get("video_data"))
        return self._extract_videos(result)

    def _rank_videos(self, filter_key, session_id, offset):
        try:
            result = self._rank_cell_change(filter_key, session_id, offset)
            data = result.get("data") if isinstance(result, dict) else None
            if isinstance(data, dict):
                return self._extract_videos(data)
            return self._extract_videos(result)
        except Exception:
            return []

    def _seed_videos(self, min_count):
        all_videos = []
        max_seeds = min(len(self.HOME_SEEDS), 3)
        for i in range(max_seeds):
            videos = self._search_videos(self.HOME_SEEDS[i])
            all_videos.extend(videos)
            if len(all_videos) >= min_count:
                break
        unique_map = {}
        for item in all_videos:
            sid = str(item.get("series_id", ""))
            if self._is_empty(sid):
                continue
            if sid in unique_map:
                continue
            unique_map[sid] = item
            if len(unique_map) >= min_count:
                break
        return list(unique_map.values())

    def _to_vod_list(self, videos, use_episode_right_text=False):
        lst = []
        if not videos:
            return lst
        for item in videos:
            series_id = str(item.get("series_id", ""))
            title = str(item.get("title", ""))
            if self._is_empty(series_id) or self._is_empty(title):
                continue
            cover = item.get("cover", "")
            if self._is_empty(cover):
                cover = item.get("thumb_url", "")
            note = str(item.get("episode_right_text", "")).strip() if use_episode_right_text else ""
            if not note:
                episode_cnt = int(item.get("episode_cnt", 0) or 0)
                if episode_cnt > 0:
                    note = f"全{episode_cnt}集"
                if "score" in item:
                    score = str(item.get("score", ""))
                    if not self._is_empty(score):
                        sep = " " if note else ""
                        note = f"{note}{sep}{score}分"
            lst.append({
                "vod_id": series_id + "_" + title,
                "vod_name": title,
                "vod_pic": cover,
                "vod_remarks": note,
            })
        return lst

    def _join_category_names(self, category_data):
        if category_data is None:
            return ""
        try:
            if isinstance(category_data, str):
                if not category_data.startswith("["):
                    return ""
                arr = self._json_safe(category_data, [])
            elif isinstance(category_data, list):
                arr = category_data
            else:
                return ""
            names = []
            for i in range(min(len(arr), 6)):
                item = arr[i]
                if not isinstance(item, dict):
                    continue
                name = item.get("name", "")
                if self._is_empty(name):
                    continue
                names.append(name)
            return ",".join(names)
        except Exception:
            return ""

    def _add_filter(self, filters, selector_rows, key, name):
        items = selector_rows.get(key)
        if not items:
            return
        values = [{"n": "全部", "v": ""}]
        count = 0
        for pair in items:
            values.append({"n": pair[0], "v": pair[1]})
            count += 1
            if count >= 40:
                break
        filters.append({"key": key, "name": name, "value": values})

    def _build_filters(self, category_id):
        cached = self.filter_cache.get(category_id)
        if cached is not None:
            return cached
        filters = []
        try:
            result = self._landpage(category_id, "", "", "", 0, 1, "only_panel")
            selector_rows = self._parse_selector_rows(result)
            self._add_filter(filters, selector_rows, "category_dim_theme", "题材")
            self._add_filter(filters, selector_rows, "category_dim_role", "人设")
            self._add_filter(filters, selector_rows, "sort", "排序")
            self._add_filter(filters, selector_rows, "gender", "频道")
            self._add_filter(filters, selector_rows, "online_time", "上新")
        except Exception:
            pass
        if not filters:
            filters.append({
                "key": "category_dim_role", "name": "人设",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "霸总", "v": "cate_266"},
                    {"n": "重生", "v": "cate_36"},
                    {"n": "穿越", "v": "cate_37"},
                    {"n": "甜宠", "v": "cate_96"},
                    {"n": "神医", "v": "cate_26"},
                    {"n": "神豪", "v": "cate_20"},
                    {"n": "脑洞", "v": "cate_262"},
                ],
            })
            filters.append({
                "key": "category_dim_theme", "name": "题材",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "现言", "v": "cate_1021"},
                    {"n": "古言", "v": "cate_439"},
                    {"n": "战神", "v": "cate_1038"},
                    {"n": "悬疑", "v": "cate_165"},
                ],
            })
        self.filter_cache[category_id] = filters
        return filters

    def _build_rank_filters(self):
        cached = self.filter_cache.get("rank")
        if cached is not None:
            return cached
        filters = [
            {
                "key": "sub_selected_items", "name": "榜单",
                "value": [
                    {"n": "推荐榜", "v": "ranklist_hot_sc"},
                    {"n": "热播榜", "v": "ranklist_hot_play_sc"},
                    {"n": "臻果榜", "v": "ranklist_prestige"},
                    {"n": "预约榜", "v": "ranklist_subscribe"},
                ],
            },
            {
                "key": "selected_items", "name": "体裁",
                "value": [
                    {"n": "全部", "v": "all"},
                    {"n": "真人剧", "v": "human"},
                    {"n": "漫剧", "v": "comic_series_rank"},
                    {"n": "AI剧", "v": "ai_playlet"},
                ],
            },
        ]
        self.filter_cache["rank"] = filters
        return filters

    # ============================================================
    # Spider 生命周期方法
    # ============================================================

    def init(self, extend=""):
        self.quality = "720p"
        self.filter_cache = {}
        iid = ""
        if extend is None:
            extend = ""
        else:
            extend = extend.strip()
        if extend:
            try:
                if extend.startswith("{"):
                    obj = self._json_safe(extend, {})
                    iid = obj.get("iid", "")
                    try:
                        q = str(obj.get("quality", self.quality)).strip()
                        if re.match(r"^[A-Za-z0-9_-]{1,16}$", q):
                            self.quality = q
                    except Exception:
                        pass
            except Exception:
                pass
        self.__init_client("", iid)
        self.__init_play(self.quality)

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        try:
            self._begin_play_request()
        except Exception:
            pass
        try:
            with self._PROXY_CACHE_LOCK:
                self._PROXY_CACHE.clear()
            with self._PROXY_TOKENS_LOCK:
                self._PROXY_TOKENS.clear()
        except Exception:
            pass

    def homeContent(self, filter):
        classes = [{"type_id": c[0], "type_name": c[1]} for c in self.CLASSES]
        if filter:
            filters = {}
            for c in self.CLASSES:
                type_id = c[0]
                if type_id == "recommend":
                    continue
                if type_id == "rank":
                    filters[type_id] = self._build_rank_filters()
                else:
                    filters[type_id] = self._build_filters(type_id)
            return {"class": classes, "filters": filters}
        else:
            videos = self._land_videos("short_play", "", "", "", 0, 18)
            vod_list = self._to_vod_list(videos)
            return {"class": classes, "list": vod_list}

    def homeVideoContent(self):
        videos = self._land_videos("short_play", "", "", "", 0, 24)
        vod_list = self._to_vod_list(videos)
        if not vod_list:
            seed_result = self._seed_videos(12)
            vod_list = self._to_vod_list(seed_result)
        return {"list": vod_list}

    def categoryContent(self, tid, pg, flag, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        if extend is None:
            extend = {}
        videos = []
        if tid == "rank":
            rank_filter = self._pick(extend, "sub_selected_items", "all")
            genre_filter = self._pick(extend, "ranklist_hot_sc", "ranklist_hot_sc")
            offset = (page - 1) * 10
            videos = self._rank_videos(genre_filter, rank_filter, offset)
        elif tid == "recommend":
            offset = (page - 1) * 18
            videos = self._land_videos("short_play", "hot", "", "", offset, 18)
            if not videos:
                videos = self._land_videos("short_play", "", "", "", offset, 18)
        else:
            if self._is_empty(tid):
                tid = "short_play"
            sort = self._pick(extend, "sort", "")
            theme = self._pick(extend, "theme", "")
            role = self._pick(extend, "category_dim_theme", theme)
            gender = self._pick(extend, "gender", "")
            online_time = self._pick(extend, "category_dim_role", role)
            offset = (page - 1) * 18
            videos = self._land_videos(tid, sort, gender, online_time, offset, 18)
        vod_list = self._to_vod_list(videos)
        page_size = 18
        has_more = len(vod_list) >= page_size
        next_page = page + 1 if has_more else page
        return {
            "list": vod_list,
            "page": page,
            "pagecount": next_page,
            "limit": page_size,
            "total": next_page * page_size,
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        raw_id = str(ids[0] or "").strip()
        series_id = raw_id
        expected_title = str(ids[1] or "").strip() if len(ids) > 1 else ""
        if "_" in raw_id:
            id_part, title_part = raw_id.split("_", 1)
            if id_part.isdigit() and title_part.strip():
                series_id = id_part
                expected_title = title_part.strip()
        detail = self._find_detail(series_id, expected_title)
        if detail is None:
            return {"msg": "未找到该短剧", "list": []}
        detail_sid = str(detail.get("series_id", ""))
        title = str(detail.get("title", ""))
        cover = str(detail.get("cover", ""))
        desc = str(detail.get("video_desc", ""))
        vid = str(detail.get("vid", ""))
        episode_cnt = int(detail.get("episode_cnt", 0) or 0)
        if episode_cnt <= 0:
            episode_cnt = 1
        episode_names = []
        episode_vids = self._episode_vids(detail_sid, vid, detail, expected_title)
        if not detail.get("_title_mismatch"):
            title = str(detail.get("title", ""))
            cover = str(detail.get("cover", ""))
            desc = str(detail.get("video_desc", ""))
            vid = str(detail.get("vid", ""))
            episode_cnt = int(detail.get("episode_cnt", 0) or 0)
            if episode_cnt <= 0:
                episode_cnt = 1
        if (detail.get("_title_mismatch") or detail.get("_detail_failed")) and not self._is_empty(expected_title):
            replacement = self._search_exact_video(expected_title)
            if replacement is None:
                return {"msg": "未找到该短剧", "list": []}
            detail = replacement
            detail_sid = str(detail.get("series_id", ""))
            title = str(detail.get("title", ""))
            cover = str(detail.get("cover", ""))
            desc = str(detail.get("video_desc", ""))
            vid = str(detail.get("vid", ""))
            episode_cnt = int(detail.get("episode_cnt", 0) or 0)
            if episode_cnt <= 0:
                episode_cnt = 1
            episode_vids = self._episode_vids(detail_sid, vid, detail, expected_title)
        if episode_vids:
            self._remember_next_episodes(episode_vids)
            # TVBox 标准: vod_play_url = 集名$地址#集名$地址#...
            for i in range(len(episode_vids)):
                episode_names.append(f"第{i+1}集${episode_vids[i]}")
        elif self.is_vid(vid):
            episode_names.append(f"第1集${vid}")
        else:
            max_ep = episode_cnt
            for i in range(1, max_ep + 1):
                episode_names.append(f"第{i}集${detail_sid}#{vid}#{i}")
        total_eps = max(episode_cnt, len(episode_names))
        note = f"全{total_eps}集"
        episode_right_text = str(detail.get("episode_right_text", "")).strip()
        director = ""
        if episode_right_text.startswith("更新至"):
            director = episode_right_text
        elif episode_right_text.startswith("全"):
            director = "已完结_" + episode_right_text
        vod = {
            "vod_id": detail_sid + "_" + title if title else detail_sid,
            "vod_name": title,
            "vod_pic": cover,
            "vod_remarks": note,
            "vod_content": desc,
            "type_name": self._join_category_names(detail.get("category_schema")),
        }
        if director:
            vod["vod_director"] = director
        if "score" in detail:
            vod["vod_year"] = str(detail.get("score", "")) + "分"
        play_from = "$$$".join(self.FALLBACK_FLAGS)
        # TVBox 标准格式: # 分隔同一线路的剧集, $ 分隔集名/地址
        play_url_list = ["#".join(episode_names) for _ in self.FALLBACK_FLAGS]
        vod["vod_play_from"] = play_from
        vod["vod_play_url"] = "$$$".join(play_url_list)
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        videos = self._search_videos(key)
        vod_list = self._to_vod_list(videos, True)
        # 兼容带分页参数的调用方；搜索仍固定返回第一页。
        return {
            "list": vod_list,
            "page": 1,
            "pagecount": 1,
            "limit": len(vod_list),
            "total": len(vod_list),
        }

    def playerContent(self, flag, id, vipFlags):
        play_generation = self._begin_play_request()
        rule_str = str(id or "")
        if self._is_empty(rule_str):
            return {"msg": "播放参数为空"}
        rule_str = rule_str.strip()
        vid = None
        next_vid = ""
        # TVBox 从 vod_play_url 取播放参数, 格式: "集名$地址"
        # 其中 "地址" 可能是:
        #   1) 纯 vid (e.g. "第1集$7553497007294270489")
        #   2) seriesId#vid#index (e.g. "第1集$seriesId#vid#1")
        # 提取 "$" 之后的地址部分
        if "$" in rule_str:
            dollar_idx = rule_str.find("$")
            addr = rule_str[dollar_idx + 1:].strip()
        else:
            addr = rule_str
        if "#" in addr:
            # 格式: seriesId#vid#index
            parts = addr.split("#", -1)
            if len(parts) < 2:
                return {"msg": "播放参数格式错误"}
            series_id_param = parts[0].strip()
            vid_param = parts[1].strip() if len(parts) > 1 else ""
            ep_index = 1
            if len(parts) > 2:
                try:
                    ep_index = max(1, int(parts[2].strip()))
                except Exception:
                    ep_index = 1
            episode_vids = self._episode_vids(series_id_param, vid_param)
            if episode_vids:
                idx = min(ep_index, len(episode_vids)) - 1
                vid = episode_vids[idx]
                if idx + 1 < len(episode_vids):
                    next_vid = episode_vids[idx + 1]
                self._remember_next_episodes(episode_vids)
            elif self.is_vid(vid_param):
                vid = vid_param
        else:
            # 纯地址: 可能是 vid, 也可能是 seriesId (无 vid 时的兜底)
            if self.is_vid(addr):
                vid = addr
            else:
                # 当作 seriesId, 取 _episode_vids 第 1 个
                eps = self._episode_vids(addr, "")
                if eps:
                    vid = eps[0]
                elif self.is_vid(addr):
                    vid = addr
        if not self.is_vid(vid):
            return {"msg": "无效分集 id"}
        if not self.is_vid(next_vid):
            next_vid = self._next_episode_vid(vid)
        quality_to_use = self.quality
        if not self._is_empty(flag):
            normalized = self._normalize_def(flag.strip())
            if not self._is_empty(normalized):
                quality_to_use = normalized
        try:
            play_url = self._resolve_play(vid, quality_to_use, next_vid, play_generation)
            if self._is_empty(play_url):
                return {"msg": "取流失败"}
            return {
                "parse": 0,
                "url": play_url,
                "header": self._play_headers(),
            }
        except Exception as e:
            return {"msg": f"播放失败：{e}"}

    # ============================================================
    # 纯 Python AES-CTR (回退)
    # ============================================================

    _SBOX = [
        0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
        0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
        0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
        0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
        0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
        0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
        0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
        0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
        0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
        0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
        0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
        0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
        0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
        0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
        0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
        0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
    ]

    @classmethod
    def _key_expansion(cls, key):
        """AES 密钥扩展 (支持 AES-128 和 AES-256)"""
        key_len = len(key)
        if key_len == 16:
            nk, nr = 4, 10
        elif key_len == 32:
            nk, nr = 8, 14
        else:
            raise ValueError(f"不支持的 AES 密钥长度: {key_len}")
        w = []
        for i in range(nk):
            w.append([key[4*i], key[4*i+1], key[4*i+2], key[4*i+3]])
        rcon = [0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36]
        total_words = 4 * (nr + 1)
        for i in range(nk, total_words):
            temp = list(w[i-1])
            if i % nk == 0:
                temp = temp[1:] + temp[:1]
                temp = [cls._SBOX[b] for b in temp]
                temp[0] ^= rcon[i//nk - 1]
            elif nk > 6 and i % nk == 4:
                temp = [cls._SBOX[b] for b in temp]
            w.append([w[i-nk][j] ^ temp[j] for j in range(4)])
        return w

    @classmethod
    def _gmul(cls, a, b):
        p = 0
        for _ in range(8):
            if b & 1:
                p ^= a
            hi = a & 0x80
            a = (a << 1) & 0xff
            if hi:
                a ^= 0x1b
            b >>= 1
        return p

    @classmethod
    def _encrypt_block(cls, block, w):
        nr = len(w) // 4 - 1
        s = [[block[r + 4*c] for c in range(4)] for r in range(4)]
        cls._add_round_key(s, w, 0)
        for r in range(1, nr):
            cls._sub_bytes(s)
            cls._shift_rows(s)
            cls._mix_columns(s)
            cls._add_round_key(s, w, r)
        cls._sub_bytes(s)
        cls._shift_rows(s)
        cls._add_round_key(s, w, nr)
        out = []
        for c in range(4):
            for r in range(4):
                out.append(s[r][c])
        return out

    @classmethod
    def _add_round_key(cls, s, w, rnd):
        for c in range(4):
            for r in range(4):
                s[r][c] ^= w[rnd*4 + c][r]

    @classmethod
    def _sub_bytes(cls, s):
        for r in range(4):
            for c in range(4):
                s[r][c] = cls._SBOX[s[r][c]]

    @classmethod
    def _shift_rows(cls, s):
        s[1] = s[1][1:] + s[1][:1]
        s[2] = s[2][2:] + s[2][:2]
        s[3] = s[3][3:] + s[3][:3]

    @classmethod
    def _mix_columns(cls, s):
        for c in range(4):
            a0,a1,a2,a3 = s[0][c],s[1][c],s[2][c],s[3][c]
            s[0][c] = cls._gmul(a0,2) ^ cls._gmul(a1,3) ^ a2 ^ a3
            s[1][c] = a0 ^ cls._gmul(a1,2) ^ cls._gmul(a2,3) ^ a3
            s[2][c] = a0 ^ a1 ^ cls._gmul(a2,2) ^ cls._gmul(a3,3)
            s[3][c] = cls._gmul(a0,3) ^ a1 ^ a2 ^ cls._gmul(a3,2)

    @classmethod
    def _ctr_decrypt_pure(cls, key, iv, data):
        w = cls._key_expansion(list(key))
        counter = int.from_bytes(iv, "big")
        result = bytearray()
        for i in range(0, len(data), 16):
            ctr_block = counter.to_bytes(16, "big")
            enc = cls._encrypt_block(list(ctr_block), w)
            block = data[i:i+16]
            for j in range(len(block)):
                result.append(block[j] ^ enc[j])
            counter = (counter + 1) & ((1 << 128) - 1)
        return bytes(result)
