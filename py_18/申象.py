# coding=utf-8
import json
import re
import time
import random
import string
import html
import urllib3
from requests import Session
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.path.append('..')
from base.spider import Spider

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Spider(Spider):
    BASES = ["https://api.yngszcfw.com", "https://api.qnang.com"]

    # ================== 核心静态字典 ==================
    VIDEO_GROUPS = {
        "1": {"n": "🔥 热门推荐", "items": [{"n": "每日更新", "v": "743"}, {"n": "无套内射", "v": "1019"}, {"n": "学生萝莉", "v": "144"}, {"n": "高清无码", "v": "119"}, {"n": "SM调教", "v": "184"}, {"n": "粉穴美鲍", "v": "1020"}, {"n": "多人运动", "v": "386"}, {"n": "强奸迷奸", "v": "380"}, {"n": "家庭乱伦", "v": "1021"}, {"n": "偷情换妻", "v": "1022"}, {"n": "G奶女神", "v": "1023"}, {"n": "淫荡按摩院", "v": "1024"}]},
        "399": {"n": "🇨🇳 传媒原创", "items": [{"n": "原创精品", "v": "175"}, {"n": "麻豆传媒", "v": "400"}, {"n": "天美传媒", "v": "401"}, {"n": "91制片厂", "v": "416"}, {"n": "蜜桃传媒", "v": "796"}, {"n": "精东传媒", "v": "403"}, {"n": "性世界传媒", "v": "1037"}, {"n": "星空传媒", "v": "431"}, {"n": "大象传媒", "v": "1033"}, {"n": "国际传媒", "v": "1032"}, {"n": "糖心vlog", "v": "1041"}, {"n": "QQ传媒", "v": "1031"}]},
        "5": {"n": "🇯🇵 日韩无码", "items": [{"n": "高清无码", "v": "119"}, {"n": "中文字幕", "v": "406"}, {"n": "水果派AV解说", "v": "411"}, {"n": "良家素人", "v": "409"}, {"n": "制服诱惑", "v": "129"}, {"n": "角色剧情", "v": "194"}, {"n": "日本乱伦", "v": "134"}, {"n": "强奸轮奸", "v": "128"}, {"n": "变态中出", "v": "797"}, {"n": "窃取NTR", "v": "407"}, {"n": "日本巨乳", "v": "436"}, {"n": "群P群交", "v": "195"}]},
        "4": {"n": "🎭 特殊癖好", "items": [{"n": "人妖伪娘", "v": "171"}, {"n": "女同百合", "v": "168"}, {"n": "兄弟情深", "v": "448"}, {"n": "裸贷肉偿", "v": "1851"}, {"n": "足交足控", "v": "172"}, {"n": "海外严选", "v": "131"}, {"n": "直播裸聊", "v": "120"}, {"n": "户外激情", "v": "389"}, {"n": "明星专场", "v": "387"}]},
        "393": {"n": "👨‍👩‍👧 家庭乱伦", "items": [{"n": "母子", "v": "395"}, {"n": "父女", "v": "446"}, {"n": "嫂子", "v": "396"}, {"n": "兄妹", "v": "397"}, {"n": "姐弟", "v": "398"}, {"n": "父子", "v": "1059"}, {"n": "近亲乱伦", "v": "453"}]},
        "1874": {"n": "🍉 吃瓜黑料", "items": [{"n": "黑料吃瓜", "v": "164"}, {"n": "网曝泄密", "v": "1846"}, {"n": "校园猛料", "v": "1840"}, {"n": "网红流出", "v": "1841"}, {"n": "明星黑料", "v": "1849"}, {"n": "抓奸现场", "v": "1843"}, {"n": "婚闹恶俗", "v": "1842"}]},
        "1844": {"n": "👗 制服诱惑", "items": [{"n": "角色扮演", "v": "135"}, {"n": "女仆", "v": "1848"}, {"n": "空姐制服", "v": "1818"}, {"n": "护士医生", "v": "1817"}, {"n": "OL制服", "v": "1816"}, {"n": "cosplay", "v": "1815"}, {"n": "JK少女", "v": "1814"}, {"n": "黑丝白丝", "v": "757"}, {"n": "旗袍", "v": "755"}]},
        "1873": {"n": "📹 探花精选", "items": [{"n": "探花精选", "v": "385"}, {"n": "小宝探花", "v": "1829"}, {"n": "锤子探花", "v": "1827"}, {"n": "利哥探花", "v": "1831"}, {"n": "文轩探花", "v": "1828"}, {"n": "七天探花", "v": "1826"}, {"n": "李寻欢探花", "v": "1832"}, {"n": "沈先生探花", "v": "1839"}, {"n": "千人斩探花", "v": "1830"}]},
        "881": {"n": "🌟 网黄大V", "items": [{"n": "推特欧尼", "v": "930"}, {"n": "辛尤里", "v": "936"}, {"n": "刘玥", "v": "920"}, {"n": "网黄精选", "v": "939"}, {"n": "柚子猫", "v": "809"}, {"n": "Cola酱", "v": "907"}, {"n": "知名网黄", "v": "1068"}, {"n": "玩偶姐姐", "v": "812"}, {"n": "台北娜娜", "v": "925"}, {"n": "唐伯虎", "v": "927"}]},
        "382": {"n": "🚽 偷拍街射", "items": [{"n": "澡堂洗浴", "v": "863"}, {"n": "厕所偷拍", "v": "763"}, {"n": "裙底偷拍", "v": "178"}, {"n": "街射涂鸦", "v": "862"}]},
        "412": {"n": "🎬 三级伦理", "items": [{"n": "日韩三级", "v": "804"}, {"n": "色情综艺", "v": "452"}, {"n": "国产三级", "v": "121"}, {"n": "欧美三级", "v": "943"}]},
        "967": {"n": "🧚‍♀️ 动漫二次元", "items": [{"n": "无码精选", "v": "956"}, {"n": "动漫中文", "v": "954"}, {"n": "精品动漫", "v": "127"}, {"n": "经典肉番", "v": "955"}, {"n": "同人系列", "v": "963"}, {"n": "3D动漫", "v": "147"}, {"n": "志同道合", "v": "1055"}, {"n": "真人coser", "v": "148"}]},
        "842": {"n": "💬 两性科普", "items": [{"n": "喷泉主义", "v": "828"}, {"n": "性爱小教室", "v": "821"}, {"n": "1G老濕", "v": "814"}, {"n": "搭讪大师", "v": "813"}, {"n": "小哥哥艾理", "v": "826"}, {"n": "鉴黄大师", "v": "864"}, {"n": "楚儿恋爱说", "v": "831"}, {"n": "微傲的性趣", "v": "824"}, {"n": "娜个奶姬", "v": "820"}, {"n": "一三蜜桃说", "v": "816"}]}
    }

    CATS = {
        "short_all": {"type": 2, "name": "短片", "items": [{"n": "窈窕美穴", "v": "1117"}, {"n": "丝袜足交", "v": "1116"}, {"n": "自慰喷水", "v": "1108"}, {"n": "可爱萝莉", "v": "1107"}, {"n": "群P乱交", "v": "1114"}, {"n": "sm调教", "v": "1109"}, {"n": "口舌侍奉", "v": "1113"}, {"n": "角色扮演", "v": "1112"}, {"n": "爆乳大奶", "v": "1110"}, {"n": "熟女少妇", "v": "1115"}]},
        "live_all": {"type": 3, "name": "平台", "items": [{"n": "半糖", "v": "1027"}, {"n": "SM", "v": "1871"}, {"n": "蜜桃", "v": "1025"}, {"n": "爱浪", "v": "1071"}, {"n": "夜来香", "v": "1092"}, {"n": "香闺", "v": "1079"}, {"n": "夜宴", "v": "1081"}, {"n": "红妆", "v": "1083"}, {"n": "美人妆", "v": "1105"}, {"n": "樱桃", "v": "616"}, {"n": "翠鸟", "v": "665"}, {"n": "中国", "v": "1778"}, {"n": "日韩", "v": "1779"}, {"n": "欧洲", "v": "1780"}, {"n": "俄罗斯", "v": "1781"}, {"n": "美国", "v": "1782"}, {"n": "户外", "v": "1786"}, {"n": "蚊香社", "v": "700"}]},
        "novel_all": {"type": 4, "name": "分类", "items": [{"n": "玄幻", "v": "443"}, {"n": "奇幻", "v": "439"}, {"n": "都市", "v": "438"}, {"n": "乱伦", "v": "455"}, {"n": "历史", "v": "442"}, {"n": "校园", "v": "437"}, {"n": "同人", "v": "429"}, {"n": "武侠", "v": "428"}, {"n": "科幻", "v": "432"}, {"n": "明星", "v": "457"}, {"n": "穿越", "v": "441"}]},
        "audio_all": {"type": 5, "name": "频道", "items": [{"n": "有声小说", "v": "459"}]},
        "comic_all": {"type": 6, "name": "题材", "items": [{"n": "破处", "v": "522"}, {"n": "强奸", "v": "512"}, {"n": "女仆", "v": "530"}, {"n": "调教", "v": "490"}, {"n": "乳交", "v": "532"}, {"n": "丝袜", "v": "484"}, {"n": "萝莉", "v": "492"}, {"n": "群P", "v": "482"}, {"n": "肛门", "v": "480"}, {"n": "内射中出", "v": "488"}, {"n": "巨乳大奶", "v": "481"}, {"n": "熟女人妻", "v": "503"}, {"n": "NTR", "v": "525"}, {"n": "女学生", "v": "496"}, {"n": "连裤袜", "v": "524"}, {"n": "制服", "v": "523"}]},
        "dark_all": {"type": 9, "name": "类型", "items": [{"n": "人与兽", "v": "186"}, {"n": "缅北风云", "v": "969"}, {"n": "外网秘闻", "v": "722"}, {"n": "拳入深渊", "v": "1005"}, {"n": "暴力奸杀", "v": "723"}, {"n": "SM重度调教", "v": "451"}, {"n": "灵异事件", "v": "854"}, {"n": "惊悚猎奇", "v": "450"}, {"n": "神奇妓院", "v": "149"}]},
        "image_all": {"type": 11, "name": "专区", "items": [{"n": "吃瓜黑料", "v": "947"}, {"n": "校园风流", "v": "948"}, {"n": "同城交友", "v": "949"}, {"n": "乱伦原创", "v": "950"}, {"n": "成人小说", "v": "951"}]},
        "news_all": {"type": 12, "name": "版块", "items": [{"n": "今日吃瓜", "v": "1172"}, {"n": "网红黑料", "v": "1179"}, {"n": "看片娱乐", "v": "1183"}, {"n": "学生校园", "v": "1182"}, {"n": "探花精选", "v": "1176"}, {"n": "国产剧情", "v": "1714"}, {"n": "免费短剧", "v": "1186"}, {"n": "明星黑料", "v": "1255"}, {"n": "吃瓜新闻", "v": "1178"}, {"n": "擦边撩骚", "v": "1260"}]},
        "monitor_all": {"type": 14, "name": "场景", "items": [{"n": "家庭摄像", "v": "1774"}, {"n": "黑客破解", "v": "1773"}, {"n": "情趣酒店", "v": "1775"}]}
    }

    ROUTE_TYPES = {"video_all": 1, "short_all": 2, "live_all": 3, "novel_all": 4, "audio_all": 5, "comic_all": 6, "dark_all": 9, "image_all": 11, "news_all": 12, "monitor_all": 14}
    
    SEARCH_TYPES = [1, 2, 3, 5, 9, 14, 4, 6, 8, 11, 12]

    # ================== 初始化与网络基类 ==================
    def init(self, extend=""):
        self.session = Session()
        self.ua = "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        self.session.headers.update({"User-Agent": self.ua, "Content-Type": "application/json;charset=UTF-8"})
        self.base = self.BASES[0].rstrip("/")
        self.device_sign = str(int(time.time() * 1000)) + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
        self.token = ""
        self.account()

    def getName(self): return "申象"

    def account(self):
        for b in self.BASES:
            try:
                url = b.rstrip("/") + "/api/user/account"
                res = self.session.post(url, json={"device_sign": self.device_sign, "device": "h5", "promotion_code": "QF6666"}, verify=False, timeout=5).json()
                data = res.get("data") or {}
                self.token = data.get("userinfo", {}).get("membertoken", "")
                if self.token:
                    self.base = b.rstrip("/")
                    self.session.headers.update({"token": self.token})
                    return True
            except:
                continue
        return False

    def _post(self, path, payload, retry=True):
        try:
            res = self.session.post(self.base + path, json=payload, verify=False, timeout=10).json()
            if retry and res.get("code") in [0, 401, 403] and ("登录" in str(res.get("msg")) or "token" in str(res.get("msg")).lower()):
                if self.account():
                    return self._post(path, payload, False)
            return res.get("data") or {}
        except:
            if retry:
                if self.account():
                    return self._post(path, payload, False)
            return {}

    # ================== 实用工具函数 ==================
    def _fix_url(self, u, strip_query=False):
        if not u: return ""
        u = str(u).replace("\\/", "/").replace("&amp;", "&").strip()
        if strip_query: u = u.split("?")[0]
        return "https:" + u if u.startswith("//") else u

    def _get_items(self, lst):
        return lst.get("data", []) if isinstance(lst, dict) else (lst if isinstance(lst, list) else [])

    def tag(self, typ):
        return {4: "小说", 6: "漫画", 8: "漫画", 11: "图片", 12: "图片"}.get(int(typ), "视频" if int(typ) in [1, 2, 3, 5, 9, 14] else "资源")

    def _clean_desc(self, text):
        if not text: return "暂无简介"
        text = html.unescape(str(text))
        text = re.sub(r"(?is)<script.*?>.*?</script>|<style.*?>.*?</style>", "", text)
        text = re.sub(r"(?i)<br\s*/?>|</p\s*>", "\n", text)
        text = re.sub(r"<[^>]+>", "", text)
        
        ad_flags = ['🔥 热门吃瓜', '🔥热门吃瓜', '备用地址', '下载app', '免费吃瓜', '福利导航', '成人福利', '防走丢', '专属链接', '永久地址', '获取最新', '备用网', '防失联']
        min_idx = len(text)
        for flag in ad_flags:
            idx = text.find(flag)
            if idx != -1 and idx < min_idx:
                min_idx = idx
                
        if min_idx < len(text):
            text = text[:min_idx]
            
        text = re.sub(r"https?://[^\s]+", "", text)
        return re.sub(r"\n{2,}", "\n\n", text).strip() or "暂无简介"

    def _extract_images(self, obj):
        text = json.dumps(obj, ensure_ascii=False).replace('\\/', '/')
        arr = re.findall(r"https?://[^\"\'\s<>,\\]+?\.(?:jpg|jpeg|png|webp|gif|js)(?:\?[^\"\'\s<>]*)?", text, re.I)
        return list(dict.fromkeys([self._fix_url(x) for x in arr]))

    def _parse_comic_urls(self, raw_str):
        if not raw_str: return []
        parts = str(raw_str).split(',')
        out, domain = [], ""
        for p in parts:
            p = p.split('?')[0].strip().replace('\\/', '/')
            if not p: continue
            if p.startswith('http'):
                arr = p.split('/', 3)
                if len(arr) >= 3:
                    domain = arr[0] + "//" + arr[2]
                out.append(p)
            elif p.startswith('//'):
                out.append('https:' + p)
            elif p.startswith('/'):
                out.append(domain + p if domain else self.base + p)
            else:
                out.append(p)
        return out

    def _get_selected_id(self, extend, default_id):
        if isinstance(extend, str):
            try: extend = json.loads(extend)
            except: extend = {}
        extend = extend or {}
        
        for k, v in extend.items():
            if k.startswith('cate_') and v and str(v) != "0": 
                val = str(v)
                if val in self.VIDEO_GROUPS:
                    items = self.VIDEO_GROUPS[val].get("items", [])
                    if items:
                        return str(items[0]["v"])
                return val
        
        return default_id

    # ================== 路由与分类 UI ==================
    def homeContent(self, filter):
        classes = [{"type_name": n, "type_id": i} for n, i in [("🎬 视频大区", "video_all"), ("📱 短视频区", "short_all"), ("📡 直播大区", "live_all"), ("📖 小说大区", "novel_all"), ("📻 电台大区", "audio_all"), ("📚 漫画大区", "comic_all"), ("🔞 专题大区", "dark_all"), ("🖼️ 图文社区", "image_all"), ("📰 吃瓜大区", "news_all"), ("📹 监控大区", "monitor_all")]]
        filters = {c["type_id"]: [] for c in classes}

        for pid, g in self.VIDEO_GROUPS.items():
            filters["video_all"].append({
                "key": f"cate_{pid}", 
                "name": g["n"], 
                "value": [{"n": "全部", "v": pid}] + [{"n": it["n"].replace('　','').strip(), "v": it["v"]} for it in g["items"]]
            })

        for route, cfg in self.CATS.items():
            if route in filters:
                filters[route].append({
                    "key": "cate_id", 
                    "name": cfg["name"], 
                    "value": [{"n": "全部", "v": "0"}] + cfg["items"]
                })

        return {"class": classes, "filters": filters}

    def categoryContent(self, tid, pg, filter, extend):
        real_tid = self.ROUTE_TYPES.get(tid, 1)
        
        if tid == "video_all":
            first_group = list(self.VIDEO_GROUPS.values())[0]
            default_cid = str(first_group["items"][0]["v"]) if first_group.get("items") else "1"
        else:
            cat_items = self.CATS.get(tid, {}).get("items")
            default_cid = str(cat_items[0]["v"]) if cat_items else "1"
            
        cid = self._get_selected_id(extend, default_cid)
        d = self._post("/api/index/resources_list", {"page": int(pg), "version": 2, "type": real_tid, "list_rows": 15, "category_id": int(cid)})
        
        out = {"list": [], "page": int(pg), "pagecount": 99, "limit": 15, "total": 999999}
        for x in self._get_items(d.get("list")):
            # 【强力除垢】：过滤掉官方硬塞的垃圾广告数据，防止进入死胡同
            # 1. is_ad 为 1
            # 2. 存在 ad_id 字段
            # 3. 名字包含“广告”
            # 4. 标题为空
            if str(x.get("is_ad", 0)) == "1" or x.get("ad_id") is not None or "广告" in str(x.get("name", "")) or "广告" in str(x.get("title", "")) or not (x.get("name") or x.get("title")):
                continue
            
            typ = int(x.get("type", real_tid))
            # 兼容直播大区使用 resources_id 代替 id 的情况
            item_id = str(x.get("id") or x.get("resources_id") or "")
            vid = f"direct@@{x.get('address')}" if typ == 3 and x.get('address') else item_id
            
            out["list"].append({
                "vod_id": vid, 
                "vod_name": x.get("name") or x.get("title") or "未知", 
                "vod_pic": self._fix_url(x.get("image") or x.get("img")), 
                "vod_remarks": self.tag(typ)
            })
        return out

    # ================== 详情提取 ==================
    def detailContent(self, ids):
        rid = str(ids[0] if isinstance(ids, list) else ids)
        if rid.startswith("direct@@"): return {"list": [{"vod_id": rid, "vod_name": "播放", "vod_pic": "", "type_name": "视频", "vod_content": "", "vod_play_from": "播放", "vod_play_url": f"播放${rid.replace('direct@@', '')}"}]}
        
        d = self._post("/api/recharge/info", {"resources_id": int(rid)})
        typ = int(d.get("type", 0))
        play_from, play_url = [], []
        
        paths = d.get("new_path") or d.get("path") or []
        paths = [paths] if isinstance(paths, dict) else (paths if isinstance(paths, list) else [])

        if typ == 4:
            eps = []
            first_source = None
            for i, p in enumerate(paths):
                if type(p) is dict:
                    source = p.get('remark') or "默认线路"
                    if first_source is None:
                        first_source = source
                    
                    if source == first_source:
                        name = p.get('name') or p.get('title') or f"第{i+1}章"
                        url = p.get('url') or p.get('path') or p.get('down_path')
                        if url:
                            if not url.startswith('http'):
                                url = "https:" + url if url.startswith("//") else self.base + url
                            eps.append(f"{name}$novel@@{name}@@{url}")
            
            if eps:
                play_from.append("阅读")
                play_url.append("#".join(eps))
                
        elif typ == 6:
            eps = []
            first_source = None
            for i, p in enumerate(paths):
                if type(p) is dict:
                    source_name = p.get('remark') or p.get('name') or f"线路{i+1}"
                    raw_str = p.get('url') or p.get('path') or ''
                    if first_source is None:
                        first_source = source_name
                        
                    if raw_str and source_name == first_source:
                        eps.append(f"全集$pics_raw@@{raw_str}")
            
            if eps:
                play_from.append("画册")
                play_url.append("#".join(eps))
                        
        elif typ in (11, 12):
            lines = {}
            for i, p in enumerate(paths):
                if type(p) is dict:
                    source = p.get('remark') or "视频"
                    name = p.get('name') or p.get('title') or f"线路{i+1}"
                    url = p.get('url') or p.get('path') or p.get('down_path') or p.get('address')
                    if url:
                        if source not in lines: lines[source] = []
                        lines[source].append(f"{name}${self._fix_url(url, strip_query=True)}")
            if not lines and d.get("address"):
                play_from.append("视频")
                play_url.append(f"播放${self._fix_url(d.get('address'), strip_query=True)}")
            else:
                for source, eps in lines.items():
                    play_from.append(source)
                    play_url.append("#".join(eps))
            
            imgs = self._extract_images(d)
            if imgs:
                play_from.append("图片")
                play_url.append("图片$pics@@" + "&&".join(imgs))
                
        else:
            lines = {}
            for i, p in enumerate(paths):
                if type(p) is dict:
                    source = p.get('remark') or "播放"
                    name = p.get('name') or p.get('title') or f"线路{i+1}"
                    url = p.get('url') or p.get('path') or p.get('down_path') or p.get('address')
                    if url:
                        if source not in lines: lines[source] = []
                        lines[source].append(f"{name}${self._fix_url(url, strip_query=True)}")
            if not lines and d.get("address"):
                play_from.append("播放")
                play_url.append(f"视频${self._fix_url(d.get('address'), strip_query=True)}")
            else:
                for source, eps in lines.items():
                    play_from.append(source)
                    play_url.append("#".join(eps))

        return {"list": [{
            "vod_id": rid,
            "vod_name": d.get("name") or d.get("title") or "未知",
            "vod_pic": self._fix_url(d.get("image") or d.get("img")),
            "type_name": self.tag(typ),
            "vod_content": self._clean_desc(f"{d.get('desc','')} \n {d.get('content','')}"),
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url)
        }]}

    # ================== 搜索与解析 ==================
    def _search_worker(self, key, pg, t):
        payload = {
            "list_rows": 12,
            "keywords": key,
            "page": int(pg),
            "type": t,
            "token": self.token
        }
        if t == 1: payload["just_video"] = 0
        headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "okhttp/4.12.0"}
        
        try:
            res = self.session.post(self.base + "/api/index/search", data=payload, headers=headers, verify=False, timeout=10).json()
            data = res.get("data") or {}
            return self._get_items(data.get("list"))
        except:
            return []

    def searchContent(self, key, quick, pg="1"):
        out, raw_results, seen = {"list": [], "page": int(pg)}, [], set()
        with ThreadPoolExecutor(max_workers=8) as pool:
            tasks = [pool.submit(self._search_worker, key, pg, t) for t in self.SEARCH_TYPES]
            for task in as_completed(tasks):
                for x in task.result() or []:
                    vid = str(x.get("id", ""))
                    if vid and vid not in seen:
                        seen.add(vid)
                        raw_results.append(x)
                        
        sort_map = {1:1, 2:1, 3:1, 5:1, 9:1, 14:1, 4:2, 6:3, 11:4, 12:4}
        raw_results.sort(key=lambda x: sort_map.get(int(x.get("type", 0)), 9))
        
        for x in raw_results:
            typ = int(x.get("type", 0))
            out["list"].append({"vod_id": str(x.get("id")), "vod_name": f"[{self.tag(typ)}] {x.get('name') or x.get('title') or '未知'}", "vod_pic": self._fix_url(x.get("image") or x.get("img")), "vod_remarks": self.tag(typ)})
        return out

    # ================== 播放层提取 ==================
    def playerContent(self, flag, id, vipFlags):
        if id.startswith("novel@@"):
            parts = id.replace("novel@@", "").split("@@", 1)
            name = parts[0] if len(parts) > 1 else "阅读"
            url = parts[1] if len(parts) > 1 else parts[0]
            
            try:
                if url.startswith("/"): url = self.base + url
                
                target_url = url
                if "token=" not in target_url:
                    target_url += ("&" if "?" in target_url else "?") + "token=" + self.token
                
                headers = {
                    "User-Agent": "okhttp/4.12.0"
                }
                
                res = self.session.get(target_url, headers=headers, verify=False, timeout=10)
                res.encoding = 'utf-8'
                content = res.text
                
                if len(content) < 200 and ("未登录" in content or "没有登录" in content or "token" in content.lower()):
                    self.account()
                    target_url = re.sub(r'token=[^&]*', 'token=' + self.token, target_url)
                    res = self.session.get(target_url, headers=headers, verify=False, timeout=10)
                    res.encoding = 'utf-8'
                    content = res.text
                    
                content = content.replace('\r\n', '\n').replace('\r', '\n')
                content = content.replace('\\r\\n', '\n').replace('\\n', '\n')
                content = content.replace('<br>', '\n').replace('<br/>', '\n').replace('</br>', '\n')
                
                lines = content.split('\n')
                content = '\n'.join([line.strip() for line in lines if line.strip()])
                
            except Exception as e:
                content = f"内容加载失败: {str(e)}"
                
            return {"parse": 0, "url": "novel://" + json.dumps({"title": name, "content": content}, ensure_ascii=False), "header": ""}
        
        if id.startswith("pics_raw@@"):
            raw_str = id.replace("pics_raw@@", "")
            imgs = self._parse_comic_urls(raw_str)
            return {"parse": 0, "url": "pics://" + "&&".join(imgs), "header": ""}
            
        if id.startswith("pics@@"): return {"parse": 0, "url": "pics://" + id.replace("pics@@", ""), "header": ""}
        if id.startswith("direct@@"): id = id.replace("direct@@", "")
        return {"parse": 0, "url": id, "header": {"User-Agent": self.ua}}
