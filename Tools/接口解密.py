#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox 本地包生成器（后端版 + 直连版）
功能：解析 TVBox 配置接口，自动识别 JSON/BMP/JPEG/PNG/WebP/Base64/Hex 等加密格式，
      下载所有资源（sites/jars/ext/spider/logo/wallpaper/drpy依赖等）到本地，
      生成本地离线配置包。
      支持 PHP 后端解密优先，直连解码兜底，外部 API 第三层降级。
      自动识别 TXT(#genre#) 和 M3U(#EXTM3U) 直播源。
      支持 key 前置格式输出（紧凑模式）。
支持：多线程并发下载 | 自定义 UA | 中文域名 | 代理 | 隐写图片解密 | AES-CBC | drpy依赖
用法：python tvbox_local_package.py --url <接口地址> [选项]
"""

import os
import sys
import json
import re
import base64
import struct
import time
import hashlib
import argparse
import urllib.parse
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Set

try:
    import requests
except ImportError:
    print("⚠️ 请先安装 requests: pip install requests")
    sys.exit(1)

# AES解密库（PNG/hex CBC/Base64** 解密），优先 pycryptodome，降级 pyaes（纯Python无需编译）
_HAS_AES = False
_AES_MODE = None
try:
    from Crypto.Cipher import AES as _AES_IMPL
    _AES_MODE = 'pycryptodome'
    _HAS_AES = True
except ImportError:
    try:
        import pyaes as _AES_IMPL
        _AES_MODE = 'pyaes'
        _HAS_AES = True
    except ImportError:
        pass

# 尝试导入 idna（用于中文域名编码）
try:
    import idna
    HAS_IDNA = True
except ImportError:
    HAS_IDNA = False
    print("⚠️ 未安装 idna，中文域名可能无法正常解析")
    print("   安装: pip install idna")


# ============================================================
# 核心配置
# ============================================================

DEFAULT_CONCURRENT = 3
DEFAULT_TIMEOUT = 120
DEFAULT_OUTPUT_DIR = "files"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8901/lib/php/api.php"
DEFAULT_USER_AGENT = "okhttp/4.12.0"
DEFAULT_FOLDER_NAME = "TVBox本地包"
DEFAULT_EXTERNAL_API_URL = "https://xn--v4q818bf34b.cc/helper/api.php"
DEFAULT_EXTS = "py,js,json,txt"


# ============================================================
# 全局变量（用于存储命令行参数）
# ============================================================

ALLOWED_EXT_FOR_EXT_FIELD = []


# ============================================================
# 中文域名编码
# ============================================================

def punycode_encode_domain(hostname: str) -> str:
    """将中文域名转换为 Punycode"""
    if not hostname:
        return hostname
    
    if 'xn--' in hostname:
        return hostname
    
    if not re.search(r'[\u4e00-\u9fa5]', hostname):
        return hostname
    
    if HAS_IDNA:
        try:
            encoded = idna.encode(hostname).decode('ascii')
            return encoded
        except Exception:
            pass
    
    try:
        encoded = hostname.encode('idna').decode('ascii')
        return encoded
    except Exception:
        pass
    
    try:
        parts = hostname.split('.')
        encoded_parts = []
        for part in parts:
            if re.search(r'[\u4e00-\u9fa5]', part):
                try:
                    encoded = part.encode('idna').decode('ascii')
                    encoded_parts.append(encoded)
                except:
                    encoded_parts.append(urllib.parse.quote(part))
            else:
                encoded_parts.append(part)
        return '.'.join(encoded_parts)
    except Exception:
        pass
    
    return urllib.parse.quote(hostname)


def encode_url_with_chinese(url: str) -> str:
    """编码包含中文的URL"""
    if not url:
        return url
    
    if 'xn--' in url:
        return url
    
    try:
        parsed = urlparse(url)
        if not parsed.hostname:
            return url
        
        if not re.search(r'[\u4e00-\u9fa5]', parsed.hostname):
            return url
        
        encoded_host = punycode_encode_domain(parsed.hostname)
        
        result = ''
        if parsed.scheme:
            result += parsed.scheme + '://'
        result += encoded_host
        if parsed.port:
            result += ':' + str(parsed.port)
        if parsed.path:
            path = parsed.path
            if re.search(r'[\u4e00-\u9fa5]', path):
                path_parts = path.split('/')
                encoded_parts = []
                for part in path_parts:
                    if part and re.search(r'[\u4e00-\u9fa5]', part):
                        encoded_parts.append(urllib.parse.quote(part))
                    else:
                        encoded_parts.append(part)
                path = '/'.join(encoded_parts)
            result += path
        if parsed.query:
            result += '?' + parsed.query
        if parsed.fragment:
            result += '#' + parsed.fragment
        
        return result
    except Exception:
        return url


# ============================================================
# URL 清洗工具
# ============================================================

def clean_url_string(url: str) -> str:
    """清洗URL，去除 ;md5;xxx 等后缀"""
    if not url:
        return url
    
    clean = url
    if ';md5;' in clean:
        clean = clean.split(';md5;')[0]
    if ';MD5;' in clean:
        clean = clean.split(';MD5;')[0]
    if ';' in clean and clean.endswith(';'):
        clean = clean.rstrip(';')
    
    return clean


# ============================================================
# 工具函数
# ============================================================

def get_file_extension(url: str) -> str:
    """获取URL的文件扩展名"""
    clean_url = url.split('?')[0].split('#')[0]
    ext = os.path.splitext(clean_url)[1].lower()
    return ext


def get_target_folder(url: str, parent_key: str = '') -> str:
    """根据URL和父级key确定目标文件夹"""
    ext = get_file_extension(url)
    url_lower = url.lower()
    
    if parent_key == 'spider':
        return 'jar/'
    
    if parent_key in ['lives', 'live']:
        return 'live/'
    
    if parent_key == 'wallpaper':
        return 'img/'
    
    if parent_key == 'logo':
        return 'img/'
    
    if parent_key == 'ext':
        if ext in ['.py']:
            return 'py/'
        if ext in ['.js']:
            return 'js/'
        if ext in ['.json', '.txt']:
            return 'json/'
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.bmp']:
            return 'img/'
        return 'other/'
    
    if ext in ['.m3u', '.m3u8']:
        return 'live/'
    if ext in ['.js']:
        return 'js/'
    if ext in ['.py']:
        return 'py/'
    if ext in ['.json']:
        return 'json/'
    if ext in ['.jar']:
        return 'jar/'
    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.bmp']:
        return 'img/'
    if ext in ['.txt']:
        return 'json/'
    
    if 'xbpq' in url_lower:
        return 'XBPQ/'
    if 'xyq' in url_lower:
        return 'XYQ/'
    
    return 'other/'


def get_filename_from_url(url: str) -> str:
    """从URL提取文件名"""
    clean = clean_url_string(url)
    
    try:
        parsed = urlparse(clean)
        path = parsed.path
        filename = os.path.basename(path)
        if filename and filename != '/':
            filename = filename.split('?')[0].split('#')[0]
            if filename:
                return filename
    except Exception:
        pass
    
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    ext = get_file_extension(url)
    return f"file_{url_hash}{ext}"


def resolve_relative_path(base_url: str, relative_path: str) -> str:
    """解析相对路径为绝对URL"""
    if not base_url or not relative_path:
        return relative_path
    
    if relative_path.startswith(('http://', 'https://')):
        return relative_path
    
    try:
        base_dir = base_url[:base_url.rfind("/")] if "/" in base_url else base_url
        rel = relative_path[2:] if relative_path.startswith("./") else relative_path
        return base_dir + "/" + rel
    except Exception:
        return relative_path


def should_download_resource(url: str, parent_key: str = '') -> bool:
    """判断资源是否应该下载"""
    if not url or not isinstance(url, str):
        return False
    
    url_str = url.strip()
    if not url_str or len(url_str) < 5:
        return False
    
    if '{' in url_str and '}' in url_str:
        return False
    
    url_lower = url_str.lower()

    if any(url_lower.startswith(p) for p in ["http://127.0.0.1", "http://localhost", "https://localhost", "http://::1"]):
        return False

    if parent_key == 'spider':
        return True
    
    if parent_key in ['lives', 'live']:
        if 'epg.112114' in url_lower or 'epg.v1.mk' in url_lower or 'epg.iill' in url_lower:
            return False
        if 'logo/' in url_lower or '/logo' in url_lower:
            return False
        if not (url_lower.startswith('http://') or url_lower.startswith('https://') or 
                url_lower.startswith('./') or url_lower.startswith('../') or url_lower.startswith('/')):
            return False
        if any(ext in url_lower for ext in ['.m3u', '.m3u8', '.txt']):
            return True
        if 'gitee.com' in url_lower:
            return False
        if url_lower.startswith('http') and ('m3u' in url_lower or 'live' in url_lower):
            return True
        return False
    
    if parent_key == 'wallpaper':
        return False
    
    if parent_key == 'logo':
        return True
    
    if parent_key == 'ext':
        ext = get_file_extension(url_str)
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.bmp']:
            return True
        if ALLOWED_EXT_FOR_EXT_FIELD:
            if ext in ALLOWED_EXT_FOR_EXT_FIELD:
                return True
        else:
            if ext in ['.py', '.js', '.json', '.txt']:
                return True
        return False
    
    allowed_exts = ['.js', '.py', '.json', '.jar', '.png', '.jpg', '.jpeg', '.gif', '.svg', 
                   '.ico', '.webp', '.bmp', '.m3u', '.m3u8', '.txt', '.xml']
    ext = get_file_extension(url_str)
    if ext in allowed_exts:
        return True
    
    if any(k in url_lower for k in ['xbpq', 'xyq']):
        return True
    
    return False


# ============================================================
# 加密数据检测
# ============================================================

def is_encrypted_data(content: str) -> bool:
    """检测是否是TVBox加密数据"""
    if not content:
        return False
    
    try:
        content.encode('utf-8')
        is_utf8 = True
    except UnicodeEncodeError:
        is_utf8 = False
    
    if not is_utf8:
        return True
    
    clean = content.replace('\n', '').replace(' ', '').replace('\r', '').strip()
    if clean.startswith('2423'):
        return True
    if '2324' in clean:
        return True
    if '**' in content and len(content) > 50:
        return True
    
    return False


def extract_json_from_content(content: str) -> Optional[str]:
    """从内容中提取JSON"""
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        try:
            json_str = json_match.group()
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            json_str = re.sub(r'\/\/.*$', '', json_str, flags=re.MULTILINE)
            json_str = re.sub(r'/\*[\s\S]*?\*/', '', json_str)
            json_str = json_str.replace('，', ',').replace('：', ':')
            json.loads(json_str)
            return json_str
        except:
            pass
    return None


def parse_tvbox_config(content: str) -> Optional[Dict]:
    """解析TVBox配置文件"""
    if not content or not content.strip():
        return None
    
    if content[0] == '\ufeff':
        content = content[1:]
    
    try:
        return json.loads(content, strict=False)
    except:
        pass
    
    if '#genre#' in content or '#genre#' in content:
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        if len(lines) >= 2:
            sites = []
            current_site = None
            current_lives = []
            for line in lines:
                if '#genre#' in line:
                    if current_site and current_lives:
                        current_site['lives'] = current_lives
                        sites.append(current_site)
                    name = line.split(',')[0].strip()
                    current_site = {
                        'key': f'txt_{name}',
                        'name': name,
                        'type': 0,
                        'lives': []
                    }
                    current_lives = []
                elif ',' in line and current_site:
                    parts = line.split(',', 1)
                    current_lives.append({
                        'name': parts[0].strip(),
                        'url': parts[1].strip()
                    })
            if current_site and current_lives:
                current_site['lives'] = current_lives
                sites.append(current_site)
            if sites:
                lives = []
                for site in sites:
                    if site.get('lives'):
                        for live in site['lives']:
                            live['group'] = site['name']
                            lives.append(live)
                return {
                    'sites': [],
                    'lives': lives,
                    'parses': [], '_txt_source': True,
                    '_txt_source': True
                }
    
    json_str = extract_json_from_content(content)
    if json_str:
        try:
            return json.loads(json_str)
        except:
            pass
    
    try:
        fixed = content
        lines = fixed.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('//') and not stripped.startswith('//http'):
                if not (stripped.startswith('//http') or stripped.startswith('//https')):
                    continue
            clean_lines.append(line)
        fixed = '\n'.join(clean_lines)
        fixed = re.sub(r'/\*[\s\S]*?\*/', '', fixed)
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        fixed = fixed.replace('，', ',').replace('：', ':')
        return json.loads(fixed)
    except:
        pass
    
    return None


def extract_resources(config: Dict, base_url: str = '') -> List[Dict]:
    """从配置中提取所有可下载资源"""
    resources = []
    seen_urls = set()
    
    _drpy_result = {'urls': []}
    _drpy_api_added = False
    def extract_recursive(obj, parent_key: str = '', path: str = ''):
        nonlocal _drpy_result, _drpy_api_added
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_parent = parent_key
                if key in ['lives', 'live']:
                    new_parent = 'lives'
                elif key in ['api']:
                    new_parent = 'ext'
                    if isinstance(value, str) and ('drpy2.min.js' in value or 'drpy.min.js' in value):
                        _drpy_result['urls'].append(value)
                        if _drpy_api_added:
                            continue
                        _drpy_api_added = True
                elif key in ['ext']:
                    new_parent = 'ext'
                elif key in ['spider']:
                    new_parent = 'spider'
                elif key in ['wallpaper']:
                    new_parent = 'wallpaper'
                elif key in ['logo']:
                    new_parent = 'logo'
                elif key in ['site', 'rule', 'json']:
                    new_parent = 'ext'
                
                _skip_fields = {'name', 'key', 'type', 'group', 'title', 'note', 'header', 'filter',
                                 'version', 'description', 'remark', 'status', 'author', 'channel',
                                 'categories', 'category', 'searchable', 'quick', 'playerType',
                                 'timeout', 'parse', 'host', 'playUrl', 'click'}
                if isinstance(value, str):
                    if key not in _skip_fields:
                        process_url(value, new_parent)
                else:
                    extract_recursive(value, new_parent, f"{path}.{key}")
        
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, str):
                    process_url(item, parent_key)
                elif isinstance(item, dict):
                    if 'url' in item and isinstance(item['url'], str):
                        process_url(item['url'], parent_key)
                    if 'path' in item and isinstance(item['path'], str):
                        process_url(item['path'], parent_key)
                    if 'src' in item and isinstance(item['src'], str):
                        process_url(item['src'], parent_key)
                    if 'href' in item and isinstance(item['href'], str):
                        process_url(item['href'], parent_key)
                    extract_recursive(item, parent_key)
        
        elif isinstance(obj, str):
            process_url(obj, parent_key)
    
    def process_url(url_str: str, parent_key: str):
        if not url_str or not isinstance(url_str, str):
            return
        
        url_str = url_str.strip()
        if not url_str:
            return
        
        md5_suffix = ''
        _url_clean = url_str
        if ';md5;' in url_str:
            _idx = url_str.find(';md5;')
            md5_suffix = url_str[_idx:]
            _url_clean = url_str[:_idx]
        
        if not should_download_resource(_url_clean, parent_key):
            return
        
        is_relative = not (_url_clean.startswith('http://') or _url_clean.startswith('https://'))
        
        if is_relative and base_url:
            full_url = resolve_relative_path(base_url, _url_clean)
        elif not is_relative:
            full_url = _url_clean
        else:
            full_url = _url_clean
        
        if full_url in seen_urls:
            return
        seen_urls.add(full_url)
        
        folder = get_target_folder(full_url, parent_key)
        filename = get_filename_from_url(full_url)
        
        if parent_key == 'spider':
            folder = 'jar/'
        
        res = {
            'url': full_url,
            'original': url_str,
            'folder': folder,
            'filename': filename,
            'parent_key': parent_key
        }
        if md5_suffix:
            res['md5_suffix'] = md5_suffix
        resources.append(res)
        
        if parent_key == 'ext' and '?' in url_str:
            from urllib.parse import urlparse as _up, parse_qs as _pqs
            try:
                _parsed = _up(url_str)
                _params = _pqs(_parsed.query)
                for _pk, _pv in _params.items():
                    for _pval in _pv:
                        if not (_pval.startswith('http://') or _pval.startswith('https://')):
                            continue
                        if not should_download_resource(_pval, 'ext'):
                            continue
                        _efolder = get_target_folder(_pval, 'ext')
                        _efname = get_filename_from_url(_pval)
                        if _pval not in seen_urls:
                            seen_urls.add(_pval)
                            resources.append({
                                'url': _pval, 'original': _pval,
                                'folder': _efolder, 'filename': _efname,
                                'parent_key': 'ext'
                            })
            except:
                pass
    
    extract_recursive(config)
    return resources


# ============================================================
# 后端API调用
# ============================================================

class BackendAPI:
    """TVBox后端API客户端"""
    
    def __init__(self, backend_url: str = DEFAULT_BACKEND_URL, user_agent: str = DEFAULT_USER_AGENT, proxy: str = ""):
        self.backend_url = backend_url
        self.user_agent = user_agent
        self.proxy = proxy
        self.available = False
        self.detail = ""
    
    def test_connection(self) -> bool:
        """测试后端连接"""
        print(f"🔌 检测后端连接: {self.backend_url}")
        try:
            response = requests.get(
                f"{self.backend_url}?action=health",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.available = True
                    php_version = data.get('php_version', '未知')
                    extensions = data.get('extensions', {})
                    openssl = '✅' if extensions.get('openssl') else '❌'
                    curl = '✅' if extensions.get('curl') else '❌'
                    self.detail = f"PHP {php_version} | OpenSSL: {openssl} | cURL: {curl}"
                    return True
                else:
                    self.detail = f"后端返回异常: {data}"
                    return False
            else:
                self.detail = f"HTTP {response.status_code}"
                return False
        except requests.exceptions.ConnectionError:
            self.detail = "连接失败，请检查后端是否运行"
            return False
        except requests.exceptions.Timeout:
            self.detail = "连接超时"
            return False
        except Exception as e:
            self.detail = f"错误: {str(e)}"
            return False
    
    def fetch_url(self, url: str) -> Optional[str]:
        """通过后端获取URL内容"""
        if not self.available:
            return None
        
        encoded_url = encode_url_with_chinese(url)
        
        try:
            response = requests.post(
                self.backend_url,
                data={
                    'action': 'fetch',
                    'url': encoded_url,
                    'ua': self.user_agent
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('data')
                else:
                    print(f"❌ 后端获取失败: {data.get('error', '未知错误')}")
                    return None
        except Exception as e:
            print(f"❌ 后端请求失败: {e}")
            return None
        
        return None
    
    def decrypt_data(self, data: str) -> Optional[str]:
        """通过后端解密数据"""
        if not self.available:
            return None
        
        try:
            response = requests.post(
                self.backend_url,
                data={
                    'action': 'decrypt',
                    'input': data
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('data')
                else:
                    print(f"❌ 后端解密失败: {result.get('error', '未知错误')}")
                    return None
        except Exception as e:
            print(f"❌ 后端解密请求失败: {e}")
            return None
        
        return None


def decode_bmp(content: bytes):
    """从BMP图片提取TVBox JSON数据（饭太硬格式）"""
    if len(content) < 100 or content[:2] != b'BM':
        return None
    pixel_offset = struct.unpack('<I', content[10:14])[0]
    pixel_data = content[pixel_offset:]
    if not pixel_data:
        return None
    for key in [0x9B, 0xAF, 0x5A, 0x66, 0x88, 0x77]:
        decoded = bytes([b ^ key for b in pixel_data])
        text = decoded.decode('utf-8', errors='replace').strip()
        start = text.find('{')
        if start < 0:
            start = text.find('[')
        if start >= 0:
            import json as _json
            candidate = text[start:]
            try:
                _json.loads(candidate)
                return candidate
            except:
                continue
    return None


def pad_end(key: str) -> str:
    """autoUrl.py 补齐方式：ASCII '0' 补齐到16字节"""
    return key + "0000000000000000"[:16 - len(key)]

def decode_png_encrypted(content: str) -> Optional[Dict]:
    """解密FongMi/TVBox PNG隐写格式"""
    if not content or len(content) < 50:
        return None
    
    try:
        content = content.strip()
        r = len(content) % 4
        if r:
            content += '=' * (4 - r)
        
        hexdata = base64.b64decode(content).decode('ascii', errors='ignore')
        if not hexdata.startswith('2423') and not hexdata.startswith('24'):
            return None
        
        if len(hexdata) % 2 != 0:
            hexdata = hexdata[:-1]
        raw = bytes.fromhex(hexdata).decode('latin-1').lower()
        
        key_start = raw.find('$#')
        if key_start < 0: return None
        key_end = raw.find('#$', key_start + 2)
        if key_end < 0: return None
        key = raw[key_start+2:key_end]
        
        iv = raw[-13:]
        
        hdr_end = hexdata.find('2324')
        if hdr_end < 0: return None
        hdr_end += 4
        
        cipher_hex = hexdata[hdr_end:-26]
        if len(cipher_hex) < 32:
            return None
        
        cipher = bytes.fromhex(cipher_hex)
        
        key_full = pad_end(key).encode('latin-1')
        iv_full = pad_end(iv).encode('latin-1')
        
        if _AES_MODE == 'pycryptodome':
            _aes = _AES_IMPL.new(key_full, _AES_IMPL.MODE_CBC, iv_full)
            decrypted = _aes.decrypt(cipher)
        elif _AES_MODE == 'pyaes':
            _aes_cbc = _AES_IMPL.AESModeOfOperationCBC(key_full, iv=iv_full)
            _decrypter = _AES_IMPL.Decrypter(_aes_cbc)
            decrypted = _decrypter.feed(cipher)
            decrypted += _decrypter.feed()
        else:
            print("⚠️ 未安装AES库: pip install pycryptodome 或 pip install pyaes", flush=True)
            return None
        pad_len = decrypted[-1]
        if 0 < pad_len <= 16:
            decrypted = decrypted[:-pad_len]
        
        result_txt = decrypted.decode('utf-8')
        json.loads(result_txt)
        print(f"\U0001f513 PNG解密成功 (AES-128-CBC)", flush=True)
        return result_txt
    except ImportError:
        print("⚠️ 缺少pycryptodome，请pip install pycryptodome", flush=True)
    except Exception as e:
        print(f"⚠️ PNG解密异常: {e}", flush=True)
    
    return None


def decrypt_cbc(hex_data: str) -> Optional[str]:
    """AES-CBC解密纯hex数据"""
    if not hex_data or len(hex_data) < 50:
        return None
    try:
        cleaned = re.sub(r'\s+', '', hex_data)
        raw_bytes = bytes.fromhex(cleaned) if len(cleaned) % 2 == 0 else bytes.fromhex(cleaned[:-1])
        raw_str = raw_bytes.decode('latin-1').lower()
        
        key_start = raw_str.find('$#')
        if key_start < 0: return None
        key_end = raw_str.find('#$', key_start + 2)
        if key_end < 0: return None
        key = raw_str[key_start+2:key_end]
        
        iv = raw_str[-13:]
        
        hdr_end = cleaned.find('2324')
        if hdr_end < 0: return None
        hdr_end += 4
        
        cipher_hex = cleaned[hdr_end:-26]
        if len(cipher_hex) < 32:
            return None
        
        cipher = bytes.fromhex(cipher_hex)
        
        key_full = pad_end(key).encode('latin-1')
        iv_full = pad_end(iv).encode('latin-1')
        
        if _AES_MODE == 'pycryptodome':
            _aes = _AES_IMPL.new(key_full, _AES_IMPL.MODE_CBC, iv_full)
            decrypted = _aes.decrypt(cipher)
        elif _AES_MODE == 'pyaes':
            _aes = _AES_IMPL.AESModeOfOperationCBC(key_full, iv=iv_full)
            decrypted = b''
            for _i in range(0, len(cipher), 16):
                decrypted += _aes.decrypt(cipher[_i:_i+16])
        else:
            return None
        
        pad_len = decrypted[-1]
        if pad_len > 0 and pad_len <= 16:
            decrypted = decrypted[:-pad_len]
        
        result = decrypted.decode('utf-8', errors='replace').strip()
        if result.startswith('{') or result.startswith('['):
            return result
        return None
    except Exception:
        return None


def decode_image(content: bytes):
    """通用图片隐写解码"""
    if not content or len(content) < 50:
        return None
    
    if len(content) > 200 and content[:4] == b'RIFF' and b'WEBP' in content[:12]:
        import re as _re_w
        text = content.decode('latin-1')
        b64s = _re_w.findall(r'[A-Za-z0-9+/=]{200,}', text)
        for b64 in b64s:
            try:
                pad = 4 - len(b64) % 4
                if pad != 4: b64 += '=' * pad
                dec = __import__('base64').b64decode(b64)
                return json.loads(dec)
            except:
                continue
    
    if content[:4] == b'\x89PNG':
        import struct as _s, base64 as _b64
        iend_pos = content.rfind(b'IEND')
        if iend_pos > 0:
            after_iend = content[iend_pos + 8:]
            if len(after_iend) > 50:
                import re as _re
                b64s = _re.findall(rb'[A-Za-z0-9+/]{100,}=*', after_iend)
                for b64 in b64s:
                    try:
                        padding = 4 - len(b64) % 4
                        if padding != 4:
                            b64 += b'=' * padding
                        dec = _b64.b64decode(b64)
                        try:
                            return json.loads(dec)
                        except:
                            pass
                        try:
                            txt = dec.decode('ascii', errors='ignore').strip()
                            txt = ''.join(c for c in txt if c in '0123456789abcdefABCDEF')
                            if len(txt) > 50:
                                if len(txt) % 2: txt = txt[:-1]
                                hex_bytes = bytes.fromhex(txt)
                                try:
                                    return json.loads(hex_bytes)
                                except:
                                    pass
                        except:
                            pass
                        try:
                            txt = dec.decode('utf-8', errors='ignore').strip()
                            import re as _re2
                            m = _re2.search(r'\$\#(\w+)\#\$', txt)
                            if m:
                                rest = txt[m.end():]
                                try:
                                    return json.loads(rest)
                                except:
                                    pass
                        except:
                            pass
                        try:
                            txt = dec.decode('utf-8', errors='ignore')
                            start = txt.find('{')
                            if start >= 0:
                                depth, end = 0, 0
                                for i, ch in enumerate(txt[start:], start):
                                    if ch == '{': depth += 1
                                    elif ch == '}':
                                        depth -= 1
                                        if depth == 0: end = i + 1; break
                                if end > 0:
                                    try:
                                        return json.loads(txt[start:end])
                                    except:
                                        pass
                        except:
                            pass
                    except:
                        pass
            
            b64_start = after_iend.find(b'MjQ')
            if b64_start >= 0:
                b64_part = after_iend[b64_start:]
                b64_clean = bytes([b for b in b64_part if b in __import__('string').ascii_letters.encode() or b in b'0123456789+/='])
                if b64_clean:
                    try:
                        result = decode_png_encrypted(b64_clean.decode('ascii'))
                        if result:
                            return result
                    except:
                        pass
    
    jpeg_end = b'\xff\xd9'
    pos = content.rfind(jpeg_end)
    if pos >= 0 and pos + 2 < len(content):
        extra = content[pos + 2:]
        if extra.strip():
            try:
                import json as _j
                return _j.loads(extra)
            except:
                pass
            try:
                import json as _j
                import base64 as _b
                decoded = _b.b64decode(extra).decode('utf-8', errors='ignore')
                start = decoded.find('{')
                if start < 0: start = decoded.find('[')
                if start >= 0: return decoded[start:]
            except:
                pass
    
    text = content.decode('utf-8', errors='ignore')
    if not text.strip():
        return None
    try:
        import json as _j
        return _j.loads(text)
    except:
        pass
    b64_pattern = __import__('re').compile(r'[A-Za-z0-9+/=]{50,}')
    for match in b64_pattern.finditer(text):
        try:
            import json as _j
            import base64 as _b
            decoded = _b.b64decode(match.group()).decode('utf-8', errors='ignore')
            start = decoded.find('{')
            if start < 0: start = decoded.find('[')
            if start >= 0:
                _j.loads(decoded[start:])
                return decoded[start:]
        except:
            continue
    return None


# ============================================================
# 下载器
# ============================================================

class Downloader:
    """文件下载器"""
    
    def __init__(self, backend: BackendAPI, concurrent: int = DEFAULT_CONCURRENT, timeout: int = DEFAULT_TIMEOUT):
        self.backend = backend
        self.concurrent = concurrent
        self.timeout = timeout
        self.proxy = backend.proxy if backend else ""
        self.downloaded = []
        self.failed = []
        self.total = 0
        self.completed = 0
    
    def download_file(self, url: str, save_path: str, retries: int = 3) -> bool:
        """下载单个文件 - 全部由 Python 直连下载"""
        cleaned_url = clean_url_string(url)
        
        proxy_msg = f"，代理: {self.proxy}" if self.proxy else ""
        print(f"📥 Python直连下载{proxy_msg}...")
        for attempt in range(retries):
            try:
                encoded_url = encode_url_with_chinese(cleaned_url)
                
                headers = {
                    'User-Agent': self.backend.user_agent if self.backend else 'okhttp/4.12.0',
                    'Accept': '*/*',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Connection': 'keep-alive'
                }
                
                proxies = None
                if self.proxy:
                    proxies = {"http": self.proxy, "https": self.proxy}
                response = requests.get(encoded_url, headers=headers, timeout=self.timeout, stream=True, proxies=proxies)
                
                if response.status_code == 200:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return True
                elif response.status_code == 404:
                    print(f"   ⚠️ 404: {os.path.basename(save_path)}")
                    return False
                elif response.status_code >= 400:
                    if attempt < retries - 1:
                        time.sleep(0.5 * (attempt + 1))
                    continue
            except Exception:
                if attempt < retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                continue
        
        return False
    
    def download_all(self, resources: List[Dict], output_dir: str) -> Tuple[List, List]:
        """批量下载所有资源 - 逐行显示进度"""
        self.downloaded = []
        self.failed = []
        self.total = len(resources)
        self.completed = 0
        
        print(f"\n📥 准备下载 {self.total} 个文件...", flush=True)
        print(f"   📁 保存到: {output_dir}")
        print(f"   ⚡ 并发数: {self.concurrent}", flush=True)
        print()
        
        tasks = []
        for resource in resources:
            save_path = os.path.join(output_dir, resource['folder'], resource['filename'])
            tasks.append({
                'url': resource['url'],
                'save_path': save_path,
                'resource': resource
            })
        
        with ThreadPoolExecutor(max_workers=self.concurrent) as executor:
            futures = {}
            for task in tasks:
                future = executor.submit(self.download_file, task['url'], task['save_path'])
                futures[future] = task
            
            for future in as_completed(futures):
                task = futures[future]
                success = future.result()
                
                self.completed += 1
                if success:
                    self.downloaded.append(task['resource'])
                    status = "✅"
                else:
                    self.failed.append(task['resource'])
                    status = "❌"
                
                pct = int(self.completed / self.total * 100)
                filename = task['resource']['filename']
                folder = task['resource']['folder'].rstrip('/')
                print(f"[{pct:3d}%] {status} [{folder}] {filename}", flush=True)
        
        print(f"\n{'='*50}")
        print(f"📊 下载完成!")
        print(f"   ✅ 成功: {len(self.downloaded)} 个")
        if self.failed:
            print(f"   ❌ 失败: {len(self.failed)} 个")
        print(f"{'='*50}")
        
        return self.downloaded, self.failed


# ============================================================
# 本地包生成器
# ============================================================

class LocalPackageGenerator:
    """本地包生成器"""
    
    def __init__(self, output_dir: str = DEFAULT_OUTPUT_DIR, 
                 backend_url: str = DEFAULT_BACKEND_URL,
                 user_agent: str = DEFAULT_USER_AGENT,
                 folder_name: str = DEFAULT_FOLDER_NAME,
                 proxy: str = "",
                 external_api_url: str = DEFAULT_EXTERNAL_API_URL):
        self.base_output_dir = output_dir
        self.folder_name = folder_name
        self.output_dir = os.path.join(output_dir, folder_name)
        self.user_agent = user_agent
        self.proxy = proxy
        self.backend = BackendAPI(backend_url, user_agent, proxy)
        self.resources = []
        self.config = None
        self.base_url = ''
        self.file_map = {}
        self._backend_fetched = False
        self.raw_content = None
        self.external_api_url = external_api_url
        self._local_decode_success = False
    
    def _decode_bmp_raw(self, bmp_raw: bytes) -> Optional[str]:
        """BMP原始解码"""
        import struct
        pixel_offset = struct.unpack('<I', bmp_raw[10:14])[0]
        pixel_data = bmp_raw[pixel_offset:]
        for key in [0x9B, 0xAF, 0x5A, 0x66, 0x88, 0x77]:
            decoded = bytes([b ^ key for b in pixel_data])
            text = decoded.decode('utf-8', errors='replace').strip()
            start = text.find('{')
            if start < 0: start = text.find('[')
            if start >= 0:
                import json as _j
                candidate = text[start:]
                depth, end = 0, 0
                for i, ch in enumerate(candidate):
                    if ch == '{': depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0: end = i + 1; break
                if end > 0:
                    try:
                        _j.loads(candidate[:end])
                        return candidate[:end]
                    except: pass
            if '#genre' in text:
                return decoded.decode('utf-8', errors='replace')
        return None
    
    def _external_api_decrypt(self, url: str) -> Optional[str]:
        """调用外部解密API兜底"""
        if not self.external_api_url:
            return None
        
        print(f"🔄 尝试外部解密API: {self.external_api_url}", flush=True)
        import requests as _r
        
        try:
            api_url = self.external_api_url
            
            if '?url=' in api_url:
                full_url = api_url + url
                print(f"   📤 GET: {full_url[:80]}...", flush=True)
                
                resp = _r.get(full_url, timeout=180, headers={"User-Agent": "okhttp/4.12.0"})
                
                if resp.status_code == 200:
                    content = resp.text
                    try:
                        data = resp.json()
                        if data.get('status') == 'success':
                            result = data.get('formattedContent') or data.get('data', '')
                            if result:
                                print("✅ 外部API解密成功 (GET)", flush=True)
                                return result
                    except:
                        pass
                    
                    if content and len(content) > 100:
                        trimmed = content.lstrip('\ufeff \t\n\r')
                        if trimmed.startswith('{') or trimmed.startswith('[') or trimmed.startswith('#') or '#genre#' in content:
                            print("✅ 外部API返回有效内容 (GET)", flush=True)
                            return content
                        else:
                            print(f"⚠️ 外部API返回的内容不是有效配置，前200字符: {content[:200]}", flush=True)
                    else:
                        print(f"⚠️ 外部API返回内容太短: {len(content)} 字符", flush=True)
                else:
                    print(f"⚠️ 外部API HTTP {resp.status_code}", flush=True)
                return None
            
            else:
                print(f"   📤 POST JSON: {api_url}", flush=True)
                
                resp = _r.post(api_url, 
                    json={"action": "fetch_content", "params": {"url": url}, "ts": int(time.time())},
                    timeout=180,
                    headers={"User-Agent": "okhttp/4.12.0", "Content-Type": "application/json"})
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('status') == 'success':
                        result = data.get('formattedContent') or data.get('data', '')
                        if result:
                            print("✅ 外部API解密成功 (POST)", flush=True)
                            return result
                        else:
                            print("⚠️ 外部API返回为空", flush=True)
                    else:
                        print(f"⚠️ 外部API返回失败: {data.get('message', 'unknown')}", flush=True)
                else:
                    print(f"⚠️ 外部API HTTP {resp.status_code}", flush=True)
                return None
                
        except _r.exceptions.Timeout:
            print("⚠️ 外部API请求超时", flush=True)
            return None
        except _r.exceptions.ConnectionError:
            print("⚠️ 外部API连接失败", flush=True)
            return None
        except Exception as e:
            print(f"⚠️ 外部API调用异常: {e}", flush=True)
            return None
    
    def init_backend(self) -> bool:
        """初始化后端连接"""
        if self.backend.test_connection():
            print(f"✅ 后端连接成功")
            print(f"   📌 {self.backend.detail}")
            return True
        else:
            print(f"❌ 后端连接失败: {self.backend.detail}")
            print(f"   💡 提示: 请确保后端服务已启动")
            print(f"   💡 后端地址: {self.backend.backend_url}")
            print(f"   💡 启动命令: php -S 0.0.0.0:8901 api.php")
            return False
    
    def fetch_content(self, url: str) -> Optional[str]:
        """获取内容 - 后端优先，直连兜底"""
        if self.backend.available:
            try:
                print(f"📥 通过后端获取: {url}")
                content = self.backend.fetch_url(url)
                if content:
                    print("✅ 后端获取成功")
                    self._backend_fetched = True
                    return content
                else:
                    print("⚠️ 后端获取失败，尝试直接下载")
            except Exception as e:
                print(f"⚠️ 后端获取异常: {e}")

        return self._direct_download(url)
    
    def _direct_download(self, url: str) -> Optional[str]:
        """直接下载"""
        encoded_url = encode_url_with_chinese(url)
        if encoded_url != url:
            print(f"   🌐 中文域名编码: {url} -> {encoded_url}")

        attempts = [
            (self.user_agent, f"📥 配置UA: {encoded_url[:60]}..."),
        ]

        for ua, msg in attempts:
            try:
                print(msg, flush=True)
                headers = {}
                if ua:
                    headers['User-Agent'] = ua
                
                proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
                resp = requests.get(encoded_url, headers=headers, timeout=15, proxies=proxies)

                if resp.status_code == 200:
                    raw = resp.content
                    _is_img = ((len(raw) >= 2 and raw[:2] == b'BM') or 
                               (len(raw) >= 4 and raw[:4] == b'\x89PNG') or
                               (len(raw) >= 4 and raw[:4] == b'RIFF' and b'WEBP' in raw[:12]) or
                               (len(raw) >= 2 and raw[:2] == b'\xff\xd8') or
                               (len(raw) >= 4 and raw[:4] == b'GIF8'))
                    if _is_img:
                        content = raw.decode('latin1')
                    else:
                        try:
                            content = resp.text
                        except:
                            try:
                                content = raw.decode('utf-8', errors='ignore')
                            except:
                                content = raw.decode('gbk', errors='ignore')
                    is_binary = (len(raw) >= 2 and raw[:2] == b'BM') or \
                                (len(raw) >= 4 and raw[:4] == b'\x89PNG') or \
                                (len(raw) >= 4 and raw[:4] == b'RIFF' and b'WEBP' in raw[:12]) or \
                                (len(raw) >= 2 and raw[:2] == b'\xff\xd8') or \
                                (len(raw) >= 4 and raw[:4] == b'GIF8')
                    if not is_binary and isinstance(content, str):
                        trimmed = content.lstrip('\ufeff \t\n\r')[:50].lower()
                        if trimmed.startswith('<!doctype') or trimmed.startswith('<html') or trimmed.startswith('<'):
                            print(f"   ⚠️ 是 HTML 页面，走外部API兜底...", flush=True)
                            continue
                    print("✅ 下载成功", flush=True)
                    return content
                else:
                    print(f"⚠️ HTTP {resp.status_code}", flush=True)
            except Exception as e:
                print(f"⚠️ {e}", flush=True)

        return None
    
    def load_config(self, url: str) -> bool:
        """加载TVBox配置"""
        self.base_url = url
        
        content = self.fetch_content(url)
        if not content:
            if self.external_api_url:
                print("📥 直连失败，尝试外部API...", flush=True)
                ext_decoded = self._external_api_decrypt(url)
                if ext_decoded:
                    content = ext_decoded
                    print("✅ 外部API解密成功", flush=True)
                else:
                    print("❌ 获取内容失败")
                    return False
            else:
                print("❌ 获取内容失败")
                return False
        
        self.raw_content = content
        
        if self._backend_fetched:
            self._local_decode_success = True
        
        if not self._local_decode_success and isinstance(content, str):
            trimmed = content.lstrip('\ufeff \t\n\r')[:50].lower()
            if trimmed.startswith('#') or trimmed.startswith('{') or trimmed.startswith('[') or '#genre#' in content:
                self._local_decode_success = True

        if not self._local_decode_success and isinstance(content, str) and len(content) > 100:
            cleaned = re.sub(r'\s+', '', content)
            if re.match(r'^[A-Fa-f0-9]+$', cleaned) and len(cleaned) > 100:
                try:
                    decrypted = decrypt_cbc(cleaned)
                    if decrypted:
                        content = decrypted
                        self._local_decode_success = True
                        print("\U0001f513 \u89e3\u6790AES-CBC\u52a0\u5bc6\u6570\u636e\u6210\u529f", flush=True)
                except:
                    pass
        
        if not self._local_decode_success and isinstance(content, str) and '**' in content:
            try:
                m = re.search(r'[A-Za-z0-9]{8}\*\*(.+)', content, re.DOTALL)
                if m:
                    b64_data = m.group(1).strip()
                    decoded_bytes = base64.b64decode(b64_data)
                    decoded_text = decoded_bytes.decode('utf-8', errors='replace')
                    json.loads(decoded_text.lstrip('\ufeff').strip(), strict=False)
                    content = decoded_text
                    self._local_decode_success = True
                    print("\U0001f513 \u89e3\u6790Base64\u52a0\u5bc6\u6570\u636e\u6210\u529f", flush=True)
            except:
                pass

        if self._local_decode_success:
            pass
        elif len(content) > 100 and isinstance(content, str) and content[:2] == 'BM':
            decoded = decode_bmp(content.encode('latin1'))
            if decoded:
                content = decoded
                self._local_decode_success = True
                print("🔓 解析BMP隐写成功", flush=True)
        elif len(content) > 100 and isinstance(content, str):
            try:
                decoded = decode_image(content.encode('latin1'))
                if decoded:
                    content = json.dumps(decoded, ensure_ascii=False) if isinstance(decoded, dict) else decoded
                    self._local_decode_success = True
                    print("🔓 解析图片隐写成功", flush=True)
            except:
                pass
        
        if not self._local_decode_success and self.external_api_url:
            ext_decoded = self._external_api_decrypt(url)
            if ext_decoded:
                content = ext_decoded
                print("✅ 外部API解密成功", flush=True)
        
        _is_json = False
        try:
            json.loads(content.lstrip('\ufeff').strip(), strict=False)
            _is_json = True
        except:
            pass
        
        if _is_json:
            pass
        else:
            print("📄 检测到原始文件类型（非JSON），直接保存", flush=True)
            self._raw_file = True
            self._raw_file_content = content
            self.config = {'_raw_file': True, 'url': url}
            return True
        
        if not self._backend_fetched and not _is_json and is_encrypted_data(content):
            print("🔓 检测到加密数据")
            if self.backend.available:
                decrypted = self.backend.decrypt_data(content)
                if decrypted:
                    content = decrypted
                    print("✅ 后端解密成功")
                else:
                    print("⚠️ 后端解密失败")
            else:
                json_str = extract_json_from_content(content)
                if json_str:
                    content = json_str
                    print("✅ 从加密数据中提取JSON成功")
                else:
                    print("❌ 无法解密")
                    return False
        
        config = parse_tvbox_config(content)
        if not config:
            print("❌ 解析配置失败")
            print(f"   内容预览: {content[:200]}...")
            return False
        
        self.config = config
        return True
    
    def extract_resources(self) -> int:
        """提取资源列表"""
        if not self.config:
            return 0
        
        if self.config.get('_raw_file'):
            self._is_raw_source = True
            self.resources = []
            return self._save_raw_file()
        
        self.resources = extract_resources(self.config, self.base_url)
        self._drpy_api_urls = []
        for _site in (self.config or {}).get('sites', []):
            _api = _site.get('api', '')
            if isinstance(_api, str) and ('drpy2.min.js' in _api or 'drpy.min.js' in _api):
                if _api.startswith('./') or _api.startswith('../'):
                    from urllib.parse import urljoin
                    _api = urljoin(self.base_url, _api)
                self._drpy_api_urls.append(_api)
        return len(self.resources)
    
    def _save_raw_file(self) -> int:
        """保存原始文件（非JSON内容）"""
        content = getattr(self, '_raw_file_content', self.raw_content)
        if not content:
            return 0
        
        txt = content if isinstance(content, str) else content.decode('utf-8', errors='replace')
        
        if txt.strip().startswith('#EXTM3U'):
            ext = '.m3u'
        elif txt.strip().startswith('#genre#'):
            ext = '.txt'
        else:
            ext = os.path.splitext(self.config.get('url', ''))[1].lower()
            if ext in ('.bmp', '.m3u8', ''):
                ext = '.txt'
        
        raw_dir = os.path.join(self.output_dir, 'raw')
        os.makedirs(raw_dir, exist_ok=True)
        self._raw_ext = ext
        filepath = os.path.join(raw_dir, f'source{ext}')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(txt)
        print(f"✅ 原始文件已保存: {filepath}", flush=True)
        return 0
    
    def download_resources(self, concurrent: int = DEFAULT_CONCURRENT, timeout: int = DEFAULT_TIMEOUT) -> Tuple[List, List]:
        """下载所有资源"""
        if getattr(self, '_is_raw_source', False):
            os.makedirs(self.output_dir, exist_ok=True)
            return [], []
        
        if not self.resources:
            return [], []
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        if self.raw_content:
            try:
                try:
                    parsed = json.loads(self.raw_content)
                    formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
                except:
                    formatted = self.raw_content
                
                origin_path = os.path.join(self.output_dir, 'origin.json')
                with open(origin_path, 'w', encoding='utf-8') as f:
                    f.write(formatted)
                print(f"📝 原始配置文件已保存: origin.json")
            except Exception as e:
                print(f"⚠️ 保存原始配置失败: {e}")
        else:
            print("⚠️ 没有原始配置内容可保存")
        
        downloader = Downloader(self.backend, concurrent, timeout)
        
        print(f"📥 开始下载 {len(self.resources)} 个资源...")
        print(f"   User-Agent: {self.user_agent}")
        print(f"   📁 输出目录: {self.output_dir}")
        
        folder_counts = {}
        spider_count = 0
        ext_count = 0
        wallpaper_count = 0
        for r in self.resources:
            folder = r['folder'].rstrip('/')
            folder_counts[folder] = folder_counts.get(folder, 0) + 1
            if r['parent_key'] == 'spider':
                spider_count += 1
            if r['parent_key'] == 'ext':
                ext_count += 1
            if r['parent_key'] == 'wallpaper':
                wallpaper_count += 1
        
        print("📂 资源分布:")
        for folder, count in sorted(folder_counts.items()):
            print(f"  📁 {folder}/: {count} 个文件")
        if spider_count > 0:
            print(f"   📌 spider 字段: {spider_count} 个 (全部放入 jar/)")
        if ext_count > 0:
            print(f"   📌 ext/api 字段: {ext_count} 个 (py→py/, js→js/, json/txt→json/)")
        if wallpaper_count > 0:
            print(f"   📌 wallpaper 字段: {wallpaper_count} 个 (已跳过，不下载)")
        print()
        
        downloaded, failed = downloader.download_all(self.resources, self.output_dir)
        
        self.file_map = {}
        for r in downloaded:
            local_path = os.path.join(r['folder'], r['filename'])
            self.file_map[r['url']] = local_path
            if r.get('md5_suffix'):
                self.file_map[r['original']] = local_path + r['md5_suffix']
            else:
                self.file_map[r['original']] = local_path
        
        _drpy_success_url = None
        _drpy_success_local = None
        _drpy_downloaded_urls = {r['url'] for r in downloaded}
        _all_drpy_urls = getattr(self, '_drpy_api_urls', [])
        for _i, _drpy_url in enumerate(_all_drpy_urls):
            if _drpy_url in _drpy_downloaded_urls:
                _drpy_success_url = _drpy_url
                _drpy_success_local = self.file_map.get(_drpy_url)
                break
            for _j in range(_i + 1, len(_all_drpy_urls)):
                _next_url = _all_drpy_urls[_j]
                if not should_download_resource(_next_url, 'ext'):
                    continue
                _folder = get_target_folder(_next_url, 'ext')
                _fname = get_filename_from_url(_next_url)
                _save_dir = os.path.join(self.output_dir, _folder)
                os.makedirs(_save_dir, exist_ok=True)
                _save_path = os.path.join(_save_dir, _fname)
                _dler = Downloader(self.backend, 3, timeout)
                print(f'🔄 drpy备选: {_fname}', flush=True)
                _ok = _dler.download_file(_next_url, _save_path)
                if _ok:
                    _local_path = os.path.join(_folder, _fname)
                    self.file_map[_next_url] = _local_path
                    _drpy_success_url = _next_url
                    _drpy_success_local = _local_path
                    downloaded.append({'url': _next_url, 'filename': _fname, 'folder': _folder, 'parent_key': 'ext'})
                    print(f'  ✅ drpy备选下载成功: {_fname}', flush=True)
                    break
                else:
                    print(f'  ⚠️ drpy备选下载失败: {_fname}', flush=True)
            if _drpy_success_url:
                break
        
        if _drpy_success_url is None and _all_drpy_urls:
            print('  ⚠️ 所有 drpy*.min.js 下载均失败，api配置保持原链接', flush=True)
        elif _drpy_success_url and _drpy_success_local:
            for _drpy_url in _all_drpy_urls:
                if _drpy_url not in self.file_map:
                    self.file_map[_drpy_url] = _drpy_success_local
            _all_drpy_set = set(_all_drpy_urls)
            failed = [r for r in failed if r.get('url') not in _all_drpy_set]
        
        dep_extras = []
        import re as _re
        _drpy_processed = False
        for r in downloaded:
            fname = r['filename']
            if not fname.endswith('.min.js') or not (fname.startswith('drpy') or 'drpy' in fname.lower()):
                continue
            if _drpy_processed:
                continue
            save_dir = os.path.join(self.output_dir, r['folder'])
            save_path = os.path.join(save_dir, fname)
            if not os.path.exists(save_path):
                continue
            try:
                with open(save_path, 'r', encoding='utf-8', errors='ignore') as _f:
                    js_content = _f.read()
                deps = _re.findall(r'import\s*(?:\{[^}]*\}|\*\s*as\s*\w+|\w+(?:\s*,\s*\{[^}]*\})?)\s*from\s*["\']([^"\']+)["\']', js_content)
                deps += _re.findall(r'import\s*["\']([^"\']+)["\']', js_content)
                for dep in deps:
                    if not dep.startswith('./') and not dep.startswith('../'):
                        continue
                    dep_url = urljoin(r['url'], dep)
                    if dep_url in self.file_map:
                        continue
                    dep_fname = dep.lstrip('./').lstrip('/')
                    if not dep_fname:
                        continue
                    dep_path = os.path.join(save_dir, dep_fname)
                    print(f'🔍 检测到依赖: {fname} → {dep_fname}', flush=True)
                    downloader2 = Downloader(self.backend, 3, 120)
                    for attempt in range(3):
                        ok = downloader2.download_file(dep_url, dep_path)
                        if ok:
                            dep_local = os.path.join(r['folder'], dep_fname)
                            self.file_map[dep_url] = dep_local
                            print(f'  ✅ 依赖下载成功: {dep_fname}', flush=True)
                            _drpy_processed = True
                            dep_extras.append({'url': dep_url, 'filename': dep_fname, 'folder': r['folder'], 'parent_key': 'ext'})
                            break
                        else:
                            print(f'  ⚠️ 依赖下载失败(第{attempt+1}次): {dep_fname}', flush=True)
            except Exception as e:
                print(f'  ⚠️ 读取依赖失败: {e}', flush=True)
        
        if not _drpy_processed and any(
            fname.endswith('.min.js') and (fname.startswith('drpy') or 'drpy' in fname.lower())
            for r in downloaded
        ):
            _drpy_processed = True
        
        if dep_extras:
            print(f'📦 额外下载了 {len(dep_extras)} 个依赖文件', flush=True)
        
        img_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
        for r in downloaded:
            fname = r['filename']
            ext = os.path.splitext(fname)[1].lower()
            if ext not in img_exts:
                continue
            if r.get('parent_key', '') not in ('ext', 'api'):
                continue
            save_dir = os.path.join(self.output_dir, r['folder'])
            save_path = os.path.join(save_dir, fname)
            if not os.path.exists(save_path):
                continue
            try:
                with open(save_path, 'rb') as _f:
                    raw_bytes = _f.read()
            except:
                continue
            
            decoded = None
            sig = raw_bytes[:4]
            is_real_bmp = ext == '.bmp' and sig[:2] == b'BM'
            is_real_png = ext == '.png' and sig == b'\x89PNG'
            is_real_jpg = ext in ('.jpg', '.jpeg') and sig[:2] == b'\xff\xd8'
            
            if is_real_bmp:
                decoded = decode_bmp(raw_bytes)
            elif is_real_png:
                try:
                    raw_str = raw_bytes.decode('latin1')
                    png_dec = decode_png_encrypted(raw_str)
                    if png_dec and isinstance(png_dec, dict):
                        decoded = json.dumps(png_dec, ensure_ascii=False)
                except:
                    pass
                if not decoded:
                    img_dec = decode_image(raw_bytes)
                    if img_dec:
                        if isinstance(img_dec, dict):
                            decoded = json.dumps(img_dec, ensure_ascii=False)
                        else:
                            decoded = str(img_dec)
            elif is_real_jpg:
                img_dec = decode_image(raw_bytes)
                if img_dec:
                    if isinstance(img_dec, dict):
                        decoded = json.dumps(img_dec, ensure_ascii=False)
                    else:
                        decoded = str(img_dec)
            else:
                try:
                    raw_text = raw_bytes.decode('utf-8', errors='ignore')
                    trimmed = raw_text.lstrip('\ufeff \t\n\r')
                    if trimmed.startswith('{') or trimmed.startswith('['):
                        try:
                            json.loads(trimmed)
                            decoded = trimmed
                        except:
                            pass
                    if not decoded:
                        decoded = raw_text
                except:
                    pass
            
            if not decoded and self.external_api_url:
                ext_decoded = self._external_api_decrypt(r['url'])
                if ext_decoded:
                    decoded = ext_decoded
                    print(f'  \U0001f310 \u5916\u90e8API\u89e3\u5bc6\u6210\u529f: {fname}', flush=True)

            if not decoded:
                continue

            trimmed = decoded.lstrip('\ufeff \t\n\r')
            new_ext = '.txt'
            if trimmed.startswith('{') or trimmed.startswith('['):
                try:
                    json.loads(trimmed)
                    new_ext = '.json'
                except:
                    pass
            elif trimmed.startswith('#EXTM3U'):
                new_ext = '.m3u'
            elif any(kw in trimmed[:200] for kw in ['function ', 'var ', 'let ', 'const ', 'import ', 'module.exports', 'export ', 'require(']):
                new_ext = '.js'
            if new_ext == '.txt' and is_encrypted_data(decoded):
                json_str = extract_json_from_content(decoded)
                if json_str:
                    decoded = json_str
                    new_ext = '.json'
            
            base = os.path.splitext(fname)[0]
            new_fname = base + new_ext
            _target_folder = 'json/'
            if new_ext == '.js':
                _target_folder = 'js/'
            elif new_ext == '.m3u':
                _target_folder = 'live/'
            _target_dir = os.path.join(self.output_dir, _target_folder)
            os.makedirs(_target_dir, exist_ok=True)
            new_path = os.path.join(_target_dir, new_fname)
            try:
                with open(new_path, 'w', encoding='utf-8') as _f:
                    _f.write(decoded)
                print(f'🔓 图片隐写解密: {fname} → {_target_folder}{new_fname}', flush=True)
            except Exception as _e:
                print(f'  ⚠️ 保存解密文件失败: {new_fname} - {_e}', flush=True)
                continue
            
            try:
                os.remove(save_path)
            except:
                pass
            
            if os.path.exists(new_path) and new_ext != new_fname:
                import base64 as _b64, gzip as _gz
                try:
                    with open(new_path, 'r', encoding='utf-8', errors='ignore') as _f:
                        _inner = _f.read().strip()
                    if len(_inner) > 50 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in _inner):
                        _raw = _b64.b64decode(_inner)
                        try:
                            _decomp = _gz.decompress(_raw)
                            _inner_decoded = _decomp.decode('utf-8', errors='ignore')
                            _inner_trimmed = _inner_decoded.lstrip('\ufeff \t\n\r')
                            _chain_ext = '.txt'
                            if _inner_trimmed.startswith('{') or _inner_trimmed.startswith('['):
                                try:
                                    json.loads(_inner_trimmed)
                                    _chain_ext = '.json'
                                except:
                                    pass
                            elif any(kw in _inner_trimmed[:200] for kw in ['function ', 'var ', 'let ', 'const ', 'import ', 'module.exports']):
                                _chain_ext = '.js'
                            elif _inner_trimmed.startswith('#EXTM3U'):
                                _chain_ext = '.m3u'
                            _chain_fname = os.path.splitext(new_fname)[0] + _chain_ext
                            if _chain_fname != new_fname:
                                _old_fname = new_fname
                                _chain_path = os.path.join(os.path.dirname(new_path), _chain_fname)
                                with open(_chain_path, 'w', encoding='utf-8') as _f:
                                    _f.write(_inner_decoded)
                                print(f'  🔗 链式解密: {new_fname} → {_chain_fname}', flush=True)
                                _intermediate = os.path.join(os.path.dirname(new_path), _old_fname)
                                new_fname = _chain_fname
                                new_path = _chain_path
                                try:
                                    os.remove(_intermediate)
                                except:
                                    pass
                        except:
                            pass
                except:
                    pass
            
            old_local = os.path.join(r['folder'], fname)
            new_local = os.path.join(_target_folder, new_fname)
            for k in list(self.file_map.keys()):
                if self.file_map[k] == old_local:
                    self.file_map[k] = new_local
        
        return downloaded, failed
    

    def organize_files(self):
        """扫描所有目录，按文件扩展名整理到对应目录，更新 file_map"""
        print("\n📂 整理文件到对应目录...", flush=True)
        
        ext_dir_map = {
            '.json': 'json/', '.js': 'js/', '.m3u': 'live/',
            '.txt': 'txt/',
            '.png': 'img/', '.jpg': 'img/', '.jpeg': 'img/',
            '.gif': 'img/', '.bmp': 'img/', '.webp': 'img/', '.ico': 'img/',
            '.php': 'php/', '.html': 'html/', '.css': 'css/', '.py': 'py/',
            '.xml': 'xml/', '.svg': 'img/', '.woff': 'font/', '.ttf': 'font/',
        }
        
        for d_name in ['other/', 'img/', 'json/', 'js/', 'live/', 'txt/', 'php/', 'html/', 'css/', 'py/', 'xml/', 'font/']:
            d_path = os.path.join(self.output_dir, d_name)
            if not os.path.isdir(d_path):
                continue
            for f in sorted(os.listdir(d_path)):
                f_path = os.path.join(d_path, f)
                if not os.path.isfile(f_path):
                    continue
                ext = os.path.splitext(f)[1].lower()
                target = ext_dir_map.get(ext, 'other/')
                if target == d_name:
                    continue
                target_dir = os.path.join(self.output_dir, target)
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, f)
                if os.path.exists(target_path):
                    base, e = os.path.splitext(f)
                    n = 1
                    while os.path.exists(os.path.join(target_dir, f'{base}_{n}{e}')):
                        n += 1
                    target_path = os.path.join(target_dir, f'{base}_{n}{e}')
                os.rename(f_path, target_path)
                print(f'  📦 {d_name}{f} → {target}{os.path.basename(target_path)}', flush=True)
                old_rel = os.path.join(d_name, f)
                new_rel = os.path.join(target, os.path.basename(target_path))
                for k in list(self.file_map.keys()):
                    if self.file_map[k] == old_rel:
                        self.file_map[k] = new_rel
        
        for d_name in list(ext_dir_map.values()) + ['other/']:
            d_path = os.path.join(self.output_dir, d_name)
            if os.path.isdir(d_path) and not os.listdir(d_path):
                try:
                    os.rmdir(d_path)
                    print(f'  🗑️ 删除空目录: {d_name}', flush=True)
                except:
                    pass

    def _format_site_key_first(self, site: dict) -> dict:
        """将站点对象格式化为 key 前置的字典"""
        if not site:
            return {}
        ordered = {}
        if 'key' in site:
            ordered['key'] = site['key']
        for k in ['name', 'type', 'api', 'indexs', 'searchable', 'filterable', 'quickSearch', 'changeable', 'ext', 'playerType', 'timeout', 'host', 'playUrl', 'header', 'jar', 'genre', 'style', 'doh', 'ads', 'rules']:
            if k in site and k != 'key':
                ordered[k] = site[k]
        for k, v in site.items():
            if k != 'key' and k not in ordered:
                ordered[k] = v
        return ordered

    def _format_config_key_first(self, config: dict, compact: bool = True) -> str:
        """将配置格式化为 key 前置的 JSON 字符串
        compact=True: 紧凑格式（整个配置一行，无换行缩进）
        compact=False: 漂亮格式（每个站点一行）
        """
        if not config:
            return "{}"
        
        output = {}
        for k in ['spider', 'logo', 'danmaku', 'wallpaper', 'lives', 'parses', 'doh', 'ads', 'ijk', 'proxy', 'rules']:
            if k in config:
                output[k] = config[k]
        
        if 'sites' in config and isinstance(config['sites'], list):
            output['sites'] = [self._format_site_key_first(s) for s in config['sites']]
        
        if compact:
            # 紧凑模式：整个配置一行，无换行缩进
            return json.dumps(output, ensure_ascii=False, separators=(',', ':'))
        else:
            # 漂亮模式：每个站点一行
            lines = []
            lines.append('{')
            
            top_fields = ['spider', 'logo', 'danmaku', 'wallpaper']
            top_lines = []
            for k in top_fields:
                if k in output:
                    val = output[k]
                    if isinstance(val, str):
                        val_escaped = json.dumps(val, ensure_ascii=False)
                        top_lines.append(f'  "{k}": {val_escaped}')
                    else:
                        top_lines.append(f'  "{k}": {json.dumps(val, ensure_ascii=False)}')
            if top_lines:
                lines.append(',\n'.join(top_lines))
                if 'sites' in output or 'lives' in output or 'parses' in output:
                    lines.append(',')
            
            if 'sites' in output and output['sites']:
                lines.append('  "sites": [')
                site_lines = []
                for site in output['sites']:
                    site_lines.append('    ' + json.dumps(site, ensure_ascii=False))
                lines.append(',\n'.join(site_lines))
                lines.append('  ]')
                if 'lives' in output or 'parses' in output:
                    lines.append(',')
            
            if 'lives' in output and output['lives']:
                lines.append('  "lives": [')
                live_lines = []
                for live in output['lives']:
                    live_lines.append('    ' + json.dumps(live, ensure_ascii=False))
                lines.append(',\n'.join(live_lines))
                lines.append('  ]')
                if 'parses' in output:
                    lines.append(',')
            
            if 'parses' in output and output['parses']:
                lines.append('  "parses": [')
                parse_lines = []
                for parse in output['parses']:
                    parse_lines.append('    ' + json.dumps(parse, ensure_ascii=False))
                lines.append(',\n'.join(parse_lines))
                lines.append('  ]')
                if 'doh' in output or 'ads' in output or 'ijk' in output or 'proxy' in output or 'rules' in output:
                    lines.append(',')
            
            other_fields = ['doh', 'ads', 'ijk', 'proxy', 'rules']
            other_lines = []
            for k in other_fields:
                if k in output and output[k]:
                    val = output[k]
                    other_lines.append(f'  "{k}": {json.dumps(val, ensure_ascii=False)}')
            if other_lines:
                lines.append(',\n'.join(other_lines))
            
            lines.append('}')
            return '\n'.join(lines)

    def generate_config(self, output_filename: str = 'index.json', key_first: bool = True, compact: bool = True) -> str:
        """生成本地化配置
        key_first=True: key 前置
        compact=True: 紧凑格式（整个配置一行）
        """
        self.organize_files()
        if getattr(self, '_is_raw_source', False):
            ext = getattr(self, '_raw_ext', '.txt')
            cfg = {"sites": [], "lives": [{"group": "原始源", "name": f"Raw Source ({ext})", "url": f"raw/source{ext}"}], "parses": []}
            cfg_path = os.path.join(self.output_dir, output_filename)
            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            print(f"✅ 原始源配置已保存: {cfg_path}", flush=True)
            return cfg_path
        
        if not self.config:
            return ''
        
        import copy
        local_config = copy.deepcopy(self.config)
        
        def replace_urls(obj):
            if isinstance(obj, dict):
                for key, value in list(obj.items()):
                    if isinstance(value, str):
                        if value in self.file_map:
                            obj[key] = './' + self.file_map[value]
                        else:
                            for url, local in self.file_map.items():
                                if value == url or value == os.path.basename(url):
                                    obj[key] = './' + local
                                    break
                    elif isinstance(value, (dict, list)):
                        replace_urls(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, str):
                        if item in self.file_map:
                            obj[i] = './' + self.file_map[item]
                        else:
                            for url, local in self.file_map.items():
                                if item == url or item == os.path.basename(url):
                                    obj[i] = './' + local
                                    break
                    elif isinstance(item, (dict, list)):
                        replace_urls(item)
        
        replace_urls(local_config)
        local_config.pop('_txt_source', None)
        
        config_path = os.path.join(self.output_dir, output_filename)
        
        if key_first:
            content = self._format_config_key_first(local_config, compact=compact)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(local_config, f, ensure_ascii=False, indent=2)
        
        return config_path
    
    def generate_report(self) -> str:
        """生成下载报告"""
        total = len(self.resources)
        downloaded = len([r for r in self.resources if r['url'] in self.file_map])
        failed = total - downloaded
        
        folder_stats = {}
        for r in self.resources:
            folder = r['folder'].rstrip('/')
            if folder not in folder_stats:
                folder_stats[folder] = {'total': 0, 'success': 0, 'failed': 0}
            folder_stats[folder]['total'] += 1
            if r['url'] in self.file_map:
                folder_stats[folder]['success'] += 1
            else:
                folder_stats[folder]['failed'] += 1
        
        report = f"""
📊 TVBox 本地包生成报告
{'=' * 50}
📁 输出目录: {self.output_dir}
📄 配置文件: index.json
📄 原始配置: origin.json
📦 资源总数: {total}
✅ 下载成功: {downloaded}
❌ 下载失败: {failed}
🔗 User-Agent: {self.user_agent}
🔌 后端状态: {'✅ 已连接' if self.backend.available else '❌ 未连接'}
📋 ext/api 下载类型: {', '.join(ALLOWED_EXT_FOR_EXT_FIELD) if ALLOWED_EXT_FOR_EXT_FIELD else 'py, js, json, txt'}

📂 文件分布:
"""
        
        for folder, stats in sorted(folder_stats.items()):
            status = "✅" if stats['failed'] == 0 else "⚠️"
            report += f"  {status} 📁 {folder}/: {stats['success']}/{stats['total']} 成功"
            if stats['failed'] > 0:
                report += f" ({stats['failed']} 失败)"
            report += "\n"
        
        key_stats = {}
        for r in self.resources:
            key = r['parent_key']
            if key not in key_stats:
                key_stats[key] = 0
            key_stats[key] += 1
        
        report += f"\n📋 来源分布:\n"
        for key, count in sorted(key_stats.items()):
            report += f"  • {key}: {count} 个\n"
        
        return report


# ============================================================
# 命令行接口
# ============================================================

def main():
    global ALLOWED_EXT_FOR_EXT_FIELD
    
    parser = argparse.ArgumentParser(description='TVBox本地包生成器（后端版+直连版）')
    parser.add_argument('-u', '--url', required=True, help='TVBox接口URL（支持中文域名）')
    parser.add_argument('-o', '--output', default='TVBox_Local', help='输出父目录')
    parser.add_argument('-n', '--name', default=DEFAULT_FOLDER_NAME, help='本地包文件夹名称 (默认: TVBox本地包)')
    parser.add_argument('-b', '--backend', default=DEFAULT_BACKEND_URL, help='后端API地址')
    parser.add_argument('-a', '--ua', default=DEFAULT_USER_AGENT, help='User-Agent (默认: okhttp/4.12.0)')
    parser.add_argument('-c', '--concurrent', type=int, default=3, help='并发下载数 (1-10)')
    parser.add_argument('-t', '--timeout', type=int, default=120, help='下载超时秒数')
    parser.add_argument('--exts', default=DEFAULT_EXTS, 
                        help='ext/api字段下载的文件扩展名，逗号分隔 (默认: py,js,json,txt)')
    parser.add_argument('--no-backend', action='store_true', help='不使用后端（直接下载，更快）')
    parser.add_argument('--proxy', help='SOCKS5代理地址 (如 socks5://127.0.0.1:7890)，后端下载失败时作为直连降级')
    parser.add_argument('--external-api', default=DEFAULT_EXTERNAL_API_URL,
                        help='外部解密API地址 (默认: 摸鱼工具箱接口解密)')
    parser.add_argument('--no-download', action='store_true', help='只解析不下载')
    parser.add_argument('--no-key-first', action='store_true', help='不使用 key 前置格式（标准 JSON 格式）')
    parser.add_argument('--pretty', action='store_true', help='漂亮格式（每个站点一行，有缩进），默认紧凑格式')
    
    args = parser.parse_args()
    
    ALLOWED_EXT_FOR_EXT_FIELD = ['.' + ext.strip() for ext in args.exts.split(',') if ext.strip()]
    if not ALLOWED_EXT_FOR_EXT_FIELD:
        ALLOWED_EXT_FOR_EXT_FIELD = ['.py', '.js', '.json', '.txt']
    
    folder_name = re.sub(r'[<>:"/\\|?*]', '_', args.name).strip()
    if not folder_name:
        folder_name = DEFAULT_FOLDER_NAME
    
    print(f"🚀 TVBox 本地包生成器（后端版+直连版）", flush=True)
    print(f"📡 接口地址: {args.url}", flush=True)
    print(f"📁 输出父目录: {args.output}", flush=True)
    print(f"📂 本地包文件夹: {folder_name}", flush=True)
    print(f"📁 完整输出路径: {os.path.join(args.output, folder_name)}", flush=True)
    print(f"🔗 后端地址: {args.backend}", flush=True)
    print(f"🔑 User-Agent: {args.ua}", flush=True)
    if args.proxy:
        print(f"🔌 代理: {args.proxy}", flush=True)
    if args.external_api:
        print(f"🌐 外部解密API: {args.external_api}", flush=True)
    print(f"⚡ 并发数: {args.concurrent}", flush=True)
    print(f"📋 ext/api 下载类型: {', '.join(ALLOWED_EXT_FOR_EXT_FIELD)}", flush=True)
    print(f"📋 key 前置格式: {'❌ 禁用' if args.no_key_first else '✅ 启用'}", flush=True)
    print(f"📋 输出格式: {'漂亮格式' if args.pretty else '紧凑格式'}", flush=True)
    print(flush=True)
    
    generator = LocalPackageGenerator(args.output, args.backend, args.ua, folder_name, 
                                       args.proxy or "", args.external_api or "")
    
    if not args.no_backend:
        generator.init_backend()
    else:
        print("⚠️ 已禁用后端（直接下载模式）", flush=True)
    
    print("📥 加载配置...", flush=True)
    if not generator.load_config(args.url):
        print("❌ 加载配置失败", flush=True)
        sys.exit(1)
    print("✅ 配置加载成功", flush=True)
    
    print("🔍 提取资源...", flush=True)
    count = generator.extract_resources()
    print(f"✅ 找到 {count} 个可下载资源", flush=True)
    
    spider_count = len([r for r in generator.resources if r['parent_key'] == 'spider'])
    ext_count = len([r for r in generator.resources if r['parent_key'] == 'ext'])
    wallpaper_count = len([r for r in generator.resources if r['parent_key'] == 'wallpaper'])
    if spider_count > 0:
        print(f"   📌 spider 字段: {spider_count} 个 (全部放入 jar/)", flush=True)
    if ext_count > 0:
        print(f"   📌 ext/api 字段: {ext_count} 个 (下载类型: {', '.join(ALLOWED_EXT_FOR_EXT_FIELD)})", flush=True)
    if wallpaper_count > 0:
        print(f"   📌 wallpaper 字段: {wallpaper_count} 个 (已跳过，不下载)", flush=True)
    
    if count == 0 and not getattr(generator, '_is_raw_source', False):
        print("⚠️ 没有找到可下载的资源", flush=True)
        sys.exit(0)
    
    print("\n📋 资源预览 (前10个):", flush=True)
    for i, r in enumerate(generator.resources[:10]):
        parent_info = f"[spider]" if r['parent_key'] == 'spider' else f"[{r['parent_key']}]"
        print(f"  {i+1}. {parent_info} {r['folder']}{r['filename']}", flush=True)
    if count > 10:
        print(f"  ... 还有 {count - 10} 个资源", flush=True)
    
    if args.no_download:
        print("\n⚠️ 只解析模式，不执行下载", flush=True)
        sys.exit(0)
    
    print(flush=True)
    
    if hasattr(generator, '_is_raw_source') and generator._is_raw_source:
        print("\n✨ 完成!", flush=True)
        return
    
    downloaded, failed = generator.download_resources(args.concurrent, args.timeout)
    
    if downloaded:
        print("\n📝 生成本地配置...", flush=True)
        compact = not args.pretty  # 默认紧凑，--pretty 时漂亮
        config_path = generator.generate_config(key_first=not args.no_key_first, compact=compact)
        print(f"✅ 配置已保存: {config_path}", flush=True)
    
    print("\n" + generator.generate_report(), flush=True)
    
    if failed:
        print("\n❌ 下载失败的文件 (最多显示10个):", flush=True)
        for r in failed[:10]:
            print(f"  - {r['url']}", flush=True)
        if len(failed) > 10:
            print(f"  ... 还有 {len(failed) - 10} 个失败", flush=True)
    
    print("\n✨ 完成!", flush=True)


if __name__ == '__main__':
    main()