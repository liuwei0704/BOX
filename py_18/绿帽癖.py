# coding: utf-8
# 站点信息沉淀（法则24）
# 主域名: https://lmaopi.cc
# 备用域名: 暂无
# 发布页: https://lmaopi.cc
# 内容类型: 成人影视导航站
# 特殊说明: MT3模板系统，CDN线路需从页面动态获取，m3u8有AES-128加密
# 最后验证时间: 2026-08-31
# 来源: 用户提供
# m3u8结构摘要: 锚点采用KEY URI目录(/m-105/m3u8/)，无广告分片，全滤兜底保护

import json
import re
import urllib.parse
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def __init__(self):
        self.extend = ""
        self.host = "https://lmaopi.cc"
        self._cached_host = self.host
        self._cdn_line = None
        
        # 分类硬编码 - 从首页导航菜单提取（法则16/17）
        self.classes = [
            {"type_id": "cate4", "type_name": "真实破处 - 女人的一血"},
            {"type_id": "cate5", "type_name": "白虎嫩穴 - 粉粉嫩嫩"},
            {"type_id": "cate6", "type_name": "各种制服~无限诱惑"},
            {"type_id": "cate7", "type_name": "性爱教学-不一样的知识"},
            {"type_id": "cate8", "type_name": "二次元 - CosPlay"},
            {"type_id": "cate9", "type_name": "户外车震 - 震不止身体还有刺激"},
            {"type_id": "cate10", "type_name": "淫乱群P - 没洞找洞 有洞就近"},
            {"type_id": "cate11", "type_name": "淫妻绿奴 - 还是别人的老婆最香"},
            {"type_id": "cate12", "type_name": "勾引搭讪 - 今天所有女人都是我的猎物"},
            {"type_id": "cate13", "type_name": "AI明星/网红 - 明星网红的另外一面"},
            {"type_id": "cate14", "type_name": "户外野战 - 最刺激的还是户外野战"},
            {"type_id": "cate15", "type_name": "黄播回放"},
            {"type_id": "cate16", "type_name": "感受颅内高潮 - ASMR"},
            {"type_id": "cate17", "type_name": "国产三级片"},
            {"type_id": "cate18", "type_name": "韩国三级片"},
            {"type_id": "cate20", "type_name": "亲情用不断"},
            {"type_id": "cate21", "type_name": "姐弟大战"},
            {"type_id": "cate22", "type_name": "全家大乱斗"},
            {"type_id": "cate23", "type_name": "母爱如山"},
            {"type_id": "cate24", "type_name": "好玩不过嫂子"},
            {"type_id": "cate25", "type_name": "粉嫩鲍妹妹"},
            {"type_id": "cate26", "type_name": "小姨子的爱"},
            {"type_id": "cate27", "type_name": "淫荡儿媳"},
            {"type_id": "cate28", "type_name": "母女共侍"},
            {"type_id": "cate29", "type_name": "师生伦鲍连屌"},
            {"type_id": "cate30", "type_name": "兽父集结地"},
            {"type_id": "cate31", "type_name": "爷孙畸形的爱"},
            {"type_id": "cate33", "type_name": "每日更新~撸到腿软"},
            {"type_id": "cate34", "type_name": "高颜尤物 - 看片先看脸"},
            {"type_id": "cate35", "type_name": "smeeth精选-元气美少女"},
            {"type_id": "cate36", "type_name": "可爱萝莉 - 粉粉嫩嫩"},
            {"type_id": "cate37", "type_name": "TS-女人心男人身"},
            {"type_id": "cate38", "type_name": "女同性恋"},
            {"type_id": "cate39", "type_name": "口爆颜射 - 征服女人最大的满足感"},
            {"type_id": "cate40", "type_name": "人间凶器 - 巨乳女神"},
            {"type_id": "cate41", "type_name": "媚黑婊子 - 母狗爱黑屌"},
            {"type_id": "cate42", "type_name": "JK妹妹 - 宅男最爱"},
            {"type_id": "cate43", "type_name": "smeeth精选-福利姬"},
            {"type_id": "cate44", "type_name": "云集全网 - 网红黑料"},
            {"type_id": "cate45", "type_name": "你的~女仆妹妹"},
            {"type_id": "cate46", "type_name": "smeeth-动漫精选"},
            {"type_id": "cate47", "type_name": "smeeth精选-偷窥街拍"},
            {"type_id": "cate48", "type_name": "婚纱 - 都说是女人一辈子最美的时刻"},
            {"type_id": "cate49", "type_name": "反差婊 - 来看反差的骚娘们"},
            {"type_id": "cate50", "type_name": "骚母狗们~偷情约炮"},
            {"type_id": "cate51", "type_name": "短剧微剧 - 华流才是最屌的！"},
            {"type_id": "cate52", "type_name": "直播裸舞秀"},
            {"type_id": "cate53", "type_name": "色情综艺"},
            {"type_id": "cate55", "type_name": "辛尤里"},
            {"type_id": "cate56", "type_name": "阿朱姐姐"},
            {"type_id": "cate57", "type_name": "NicoLove妮可"},
            {"type_id": "cate58", "type_name": "御梦子"},
            {"type_id": "cate59", "type_name": "小桃酱"},
            {"type_id": "cate60", "type_name": "刘玥"},
            {"type_id": "cate61", "type_name": "吴梦梦"},
            {"type_id": "cate62", "type_name": "米菲兔"},
            {"type_id": "cate63", "type_name": "桥本香菜"},
            {"type_id": "cate64", "type_name": "小水水"},
            {"type_id": "cate65", "type_name": "台北娜娜"},
            {"type_id": "cate66", "type_name": "鸡教练"},
            {"type_id": "cate67", "type_name": "饼干姐姐"},
            {"type_id": "cate68", "type_name": "HongKongDoll"},
            {"type_id": "cate69", "type_name": "樱空桃桃"},
            {"type_id": "cate70", "type_name": "唐伯虎"},
            {"type_id": "cate71", "type_name": "小敏儿"},
            {"type_id": "cate72", "type_name": "下面有根棒棒糖"},
            {"type_id": "cate73", "type_name": "冉冉学姐"},
            {"type_id": "cate74", "type_name": "捅主任"},
            {"type_id": "cate75", "type_name": "粉色情人"},
            {"type_id": "cate76", "type_name": "小鸟酱"},
            {"type_id": "cate77", "type_name": "狐不妖"},
            {"type_id": "cate78", "type_name": "锅锅酱"},
            {"type_id": "cate79", "type_name": "麻酥酥"},
            {"type_id": "cate80", "type_name": "私人玩物"},
            {"type_id": "cate81", "type_name": "八月未央"},
            {"type_id": "cate82", "type_name": "萌白酱"},
            {"type_id": "cate83", "type_name": "米娜学姐"},
            {"type_id": "cate84", "type_name": "okirakuhuhu"},
            {"type_id": "cate85", "type_name": "香草少女"},
            {"type_id": "cate86", "type_name": "桃桃酱"},
            {"type_id": "cate87", "type_name": "Cola酱"},
            {"type_id": "cate88", "type_name": "柚子猫"},
            {"type_id": "cate89", "type_name": "西门吹穴"},
            {"type_id": "cate90", "type_name": "VIP专区"},
            {"type_id": "cate92", "type_name": "麻豆传媒"},
            {"type_id": "cate93", "type_name": "糖心VLOG"},
            {"type_id": "cate94", "type_name": "JVID"},
            {"type_id": "cate95", "type_name": "91制片厂"},
            {"type_id": "cate96", "type_name": "星空传媒"},
            {"type_id": "cate97", "type_name": "其它传媒"},
            {"type_id": "cate98", "type_name": "性视界"},
            {"type_id": "cate99", "type_name": "大象传媒"},
            {"type_id": "cate100", "type_name": "爱豆传媒"},
            {"type_id": "cate101", "type_name": "杏吧传媒"},
            {"type_id": "cate102", "type_name": "果冻传媒"},
            {"type_id": "cate103", "type_name": "精东影业"},
            {"type_id": "cate104", "type_name": "天美传媒"},
            {"type_id": "cate105", "type_name": "蜜桃传媒"},
            {"type_id": "cate107", "type_name": "高端外围"},
            {"type_id": "cate108", "type_name": "足浴会所"},
            {"type_id": "cate109", "type_name": "精选探花"},
            {"type_id": "cate110", "type_name": "杏吧探花"},
            {"type_id": "cate111", "type_name": "街边探店"},
            {"type_id": "cate112", "type_name": "双飞专场"},
            {"type_id": "cate113", "type_name": "商K探花"},
            {"type_id": "cate114", "type_name": "换妻探花"},
            {"type_id": "cate115", "type_name": "韩国-金先生"},
            {"type_id": "cate116", "type_name": "李寻欢-寻欢作乐看小李"},
            {"type_id": "cate117", "type_name": "小宝寻花-探花界的传说"},
            {"type_id": "cate118", "type_name": "文轩-新生代探花"},
            {"type_id": "cate119", "type_name": "91沉先生-探花界元老"},
            {"type_id": "cate121", "type_name": "素人 - 初下海素人"},
            {"type_id": "cate122", "type_name": "SM - 调教羞辱"},
            {"type_id": "cate123", "type_name": "人间胸器 - 巨巨巨巨乳"},
            {"type_id": "cate124", "type_name": "2025热门女优-TOP100"},
            {"type_id": "cate125", "type_name": "中文字幕 - 看剧情需要中字"},
            {"type_id": "cate126", "type_name": "高清无码 - 各大AV无码流出"},
            {"type_id": "cate127", "type_name": "韩国精选"},
            {"type_id": "cate128", "type_name": "水果派 - 懒人看AV"},
            {"type_id": "cate129", "type_name": "乱伦 - 来自亲情的爱"},
            {"type_id": "cate130", "type_name": "NTR - 出轨的娇妻"},
            {"type_id": "cate131", "type_name": "同人 - 当漫画变成现实"},
            {"type_id": "cate132", "type_name": "搜查官 - 别动！你被逮捕了"},
            {"type_id": "cate133", "type_name": "女教师 - 青春时期的幻想"},
            {"type_id": "cate134", "type_name": "FC2 - 素人类无码AV"},
            {"type_id": "cate135", "type_name": "户外 - 户外寻求刺激"},
            {"type_id": "cate136", "type_name": "AV新品推荐"},
            {"type_id": "cate138", "type_name": "欧美精选"},
            {"type_id": "cate139", "type_name": "SmeetH推荐"},
            {"type_id": "cate140", "type_name": "欧美剧情"},
            {"type_id": "cate141", "type_name": "按摩会所系列"},
            {"type_id": "cate142", "type_name": "抖音满天星系列-啄木鸟"},
            {"type_id": "cate143", "type_name": "钞能力之让丈夫做绿帽"},
            {"type_id": "cate144", "type_name": "剧情版小马拉大车"},
            {"type_id": "cate145", "type_name": "欧美黑白配"},
            {"type_id": "cate146", "type_name": "街头搭讪"},
            {"type_id": "cate147", "type_name": "一起来骑大洋马"},
            {"type_id": "cate148", "type_name": "超市惩罚女小偷"},
        ]
        # 站点无真实筛选，返回空filters（法则16）
        self.filters = {}

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }

    def getName(self):
        return "绿帽癖"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""
        # 动态获取CDN线路（懒加载，在playerContent中调用）

    def _get_cdn_line(self):
        """从首页获取CDN线路（法则18：动态域名）"""
        if self._cdn_line:
            return self._cdn_line
        
        try:
            resp = self.fetch(self.host + "/", headers=self.headers, timeout=10)
            if not resp or resp.status_code != 200:
                return "https://d32bg2g0w9aqg4.cloudfront.net"
            html = resp.text or ""
            # 提取cdn_lines JSON
            match = re.search(r'cdn_lines\s*=\s*[\'"](\[.*?\])[\'"]', html, re.DOTALL)
            if match:
                lines = json.loads(match.group(1))
                if lines and isinstance(lines, list) and len(lines) > 0:
                    # 使用第一个可用线路
                    for line in lines:
                        if line.get("cdnLine"):
                            self._cdn_line = line["cdnLine"]
                            return self._cdn_line
        except Exception:
            pass
        
        # 默认CDN
        self._cdn_line = "https://d32bg2g0w9aqg4.cloudfront.net"
        return self._cdn_line

    def homeContent(self, filter=False):
        """零网络依赖，只返回本地class/filters（法则16）"""
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐 - 从首页解析推荐视频"""
        try:
            resp = self.fetch(self.host + "/", headers=self.headers, timeout=10)
            if not resp or resp.status_code != 200:
                return {"list": []}
            html = resp.text or ""
            return self._parse_video_list(html)
        except Exception:
            return {"list": []}

    def categoryContent(self, tid, pg="1", filter=False, extend=""):
        """分类列表（分页）"""
        page = str(pg) if pg else "1"
        
        # 处理extend（法则20）
        extend_dict = self._parse_extend(extend)
        
        # 构建URL
        if page == "1":
            url = f"{self.host}/category/{tid}/"
        else:
            url = f"{self.host}/category/{tid}/{page}/"
        
        try:
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if not resp or resp.status_code != 200:
                return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
            html = resp.text or ""
            return self._parse_category_page(html, page, tid)
        except Exception:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}

    def _parse_extend(self, extend):
        """多格式extend解析（法则20）"""
        if not extend:
            return {}
        if isinstance(extend, dict):
            return extend
        if isinstance(extend, str):
            try:
                return json.loads(extend)
            except:
                pass
            result = {}
            for part in extend.split(','):
                if '=' in part:
                    k, v = part.split('=', 1)
                    result[k.strip()] = v.strip()
            return result
        return {}

    def _parse_video_list(self, html):
        """解析视频列表卡片"""
        items = []
        # 匹配 .mt3-card 中的视频卡片（排除广告）
        # 查找 <div class="mt3-card"> 中不含 "mt3-card--ad" 的卡片
        card_pattern = r'<div class="mt3-card(?!.*?mt3-card--ad).*?>.*?<a class="mt3-card-thumb" href="([^"]+)"[^>]*>.*?<img[^>]*data-original="([^"]+)"[^>]*>.*?<h4 class="mt3-card-title"><a href="[^"]*"[^>]*>(.*?)</a></h4>.*?<span class="mt3-card-duration">.*?<path[^>]*></path></svg>\s*(\d+)</span>.*?<span class="mt3-card-views">([^<]+)</span>'
        
        # 更健壮的解析：先分割卡片
        card_divs = re.findall(r'<div class="mt3-card(.*?)</div>', html, re.DOTALL)
        
        for card_html in card_divs:
            # 跳过广告卡片
            if 'mt3-card--ad' in card_html:
                continue
            
            # 提取链接
            link_match = re.search(r'<a class="mt3-card-thumb" href="([^"]+)"', card_html)
            if not link_match:
                continue
            link = link_match.group(1)
            # 确保链接完整
            if link.startswith('/'):
                link = self.host + link
            
            # 提取标题
            title_match = re.search(r'<h4 class="mt3-card-title"><a[^>]*>(.*?)</a></h4>', card_html, re.DOTALL)
            if not title_match:
                continue
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            
            # 提取图片
            img_match = re.search(r'<img[^>]*data-original="([^"]+)"', card_html)
            pic = img_match.group(1) if img_match else ""
            
            # 提取时长
            duration_match = re.search(r'<span class="mt3-card-duration">.*?<path[^>]*></path></svg>\s*(\d+)</span>', card_html, re.DOTALL)
            remark = duration_match.group(1) if duration_match else ""
            
            # 提取观看次数
            views_match = re.search(r'<span class="mt3-card-views">([^<]+)</span>', card_html)
            if views_match and not remark:
                remark = views_match.group(1).strip()
            
            # 提取vod_id
            vod_id = ""
            vid_match = re.search(r'/video/(\d+)/', link)
            if vid_match:
                vod_id = vid_match.group(1)
            else:
                # 如果没有数字ID，使用链接作为ID
                vod_id = link
            
            # 打包字段到vod_id（法则15：列表阶段打包轻量字段）
            packed_id = f"{vod_id}|$|{title}|$|{pic}|$|{remark}"
            
            items.append({
                "vod_id": packed_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })
            
            if len(items) >= 20:
                break
        
        return {"list": items}

    def _parse_category_page(self, html, page, tid):
        """解析分类页"""
        result = self._parse_video_list(html)
        result["page"] = int(page) if page.isdigit() else 1
        result["limit"] = 20
        result["total"] = 999  # 站点未显示总数
        
        # 尝试解析总页数
        pagecount = 1
        # 查找分页：<a class="mt3-pager-btn" href="/category/cate4/90/">...90...</a>
        page_matches = re.findall(r'<a class="mt3-pager-btn"[^>]*href="[^"]*/category/\w+/(\d+)/"[^>]*>', html)
        if page_matches:
            pages = [int(p) for p in page_matches if p.isdigit()]
            if pages:
                pagecount = max(pages)
        result["pagecount"] = pagecount
        
        return result

    def detailContent(self, ids):
        """详情页 - 轻量返回（法则15：列表打包，详情零网络）"""
        if not ids or not ids[0]:
            return {"list": []}
        
        raw = ids[0]
        parts = raw.split('|$|')
        
        vod_id = parts[0] if len(parts) > 0 else ""
        vod_name = parts[1] if len(parts) > 1 else "视频"
        vod_pic = parts[2] if len(parts) > 2 else ""
        vod_remark = parts[3] if len(parts) > 3 else ""
        
        # 构建播放页URL
        if vod_id and vod_id.startswith('http'):
            play_url = vod_id
        elif vod_id and vod_id.isdigit():
            play_url = f"{self.host}/video/{vod_id}/"
        else:
            play_url = f"{self.host}/video/{vod_id}/"
        
        vod = {
            "vod_id": raw,
            "vod_name": vod_name,
            "vod_pic": vod_pic,
            "vod_remarks": vod_remark,
            "vod_content": vod_remark,
            "vod_play_from": "播放",
            "vod_play_url": f"播放${play_url}"
        }
        
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        """搜索（法则22/25：多类型并发）"""
        try:
            # 确保pg为字符串
            page_str = str(pg) if pg is not None else "1"
            # 搜索URL
            url = f"{self.host}/search/{urllib.parse.quote(key)}/"
            if page_str != "1":
                url = f"{self.host}/search/{urllib.parse.quote(key)}/{page_str}/"
            
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if not resp or resp.status_code != 200:
                return {"list": [], "page": int(page_str)}
            
            html = resp.text or ""
            result = self._parse_video_list(html)
            result["page"] = int(page_str)
            return result
        except Exception:
            page_str = str(pg) if pg is not None else "1"
            return {"list": [], "page": int(page_str)}
    def playerContent(self, flag, id, vipFlags=[]):
        """播放解析 - 从详情页提取m3u8地址（法则7：直链优先）"""
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        
        # 如果已经是m3u8/mp4直链
        if id.startswith("http") and (".m3u8" in id or ".mp4" in id):
            if ".m3u8" in id:
                return {"parse": 0, "url": self._m3u8_proxy_url(id), "header": {"User-Agent": self.headers["User-Agent"]}}
            return {"parse": 0, "url": id, "header": {"User-Agent": self.headers["User-Agent"]}}
        
        # 如果是详情页URL，提取m3u8
        try:
            # 获取CDN线路
            cdn = self._get_cdn_line()
            
            resp = self.fetch(id, headers=self.headers, timeout=15)
            if not resp or resp.status_code != 200:
                # 降级嗅探（法则27：parse:1必须带header）
                return {"parse": 1, "url": id, "header": self.headers}
            
            html = resp.text or ""
            
            # 提取 #article-videos 的 data-url
            match = re.search(r'id="article-videos"[^>]*data-url="([^"]+)"', html)
            if match:
                url_path = match.group(1)
                # 拼接CDN
                if url_path.startswith("/"):
                    m3u8_url = cdn + url_path
                elif url_path.startswith("http"):
                    m3u8_url = url_path
                else:
                    m3u8_url = cdn + "/" + url_path
                
                # 返回代理地址（m3u8走localProxy清洗）
                return {"parse": 0, "url": self._m3u8_proxy_url(m3u8_url), "header": {"User-Agent": self.headers["User-Agent"]}}
            
            # 尝试从页面直接提取m3u8
            m3u8_match = re.search(r'https?://[^"\']+\.m3u8[^"\']*', html)
            if m3u8_match:
                m3u8_url = m3u8_match.group(0)
                return {"parse": 0, "url": self._m3u8_proxy_url(m3u8_url), "header": {"User-Agent": self.headers["User-Agent"]}}
            
            # 降级嗅探
            return {"parse": 1, "url": id, "header": self.headers}
        except Exception:
            return {"parse": 1, "url": id, "header": self.headers}

    def _m3u8_proxy_url(self, url):
        """生成m3u8代理地址"""
        if not url:
            return ""
        return self.getProxyUrl() + "?do=py&url=" + urllib.parse.quote(str(url), safe="")

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy"

    def localProxy(self, param):
        """m3u8本地代理 - 五层去广告管线（法则30）"""
        try:
            # 解析目标URL（三重兜底）
            if isinstance(param, dict):
                target = param.get("url", "") or param.get("source", "")
            else:
                target = str(param or "")
            
            if target.startswith("url="):
                target = target[4:]
            elif "url=" in target:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(target).query)
                if "url" in qs:
                    target = qs["url"][0]
            target = urllib.parse.unquote(str(target or ""))
            
            if not target or not re.match(r"^https?://", target, re.I):
                return [400, "text/plain", b"invalid url"]
            
            # 请求m3u8
            resp = self.fetch(target, headers=self.headers, timeout=20)
            if not resp or resp.status_code != 200:
                return [502, "text/plain", b"fetch failed"]
            
            content = getattr(resp, "content", b"") or b""
            if not content and getattr(resp, "text", ""):
                content = resp.text.encode("utf-8", errors="ignore")
            if not content:
                return [502, "text/plain", b"empty content"]
            
            # 检查是否为m3u8
            if b"#EXTM3U" not in content[:256]:
                return [200, "application/octet-stream", content]
            
            # 第1层：图片流伪装检测
            text = content.decode("utf-8", errors="ignore")
            if self._is_fake_image_stream(text, target):
                restored = text
                for ext in (".png", ".jpeg", ".jpg", ".webp"):
                    restored = restored.replace(ext, ".ts")
                self.log("检测到图片流伪装，已还原扩展名 -> .ts，跳过广告过滤")
                return [200, "application/vnd.apple.mpegurl", restored.encode("utf-8")]
            
            # 清洗m3u8（五层管线）
            cleaned = self._clean_m3u8(text, target)
            return [200, "application/vnd.apple.mpegurl", cleaned.encode("utf-8")]
        except Exception as e:
            self.log("localProxy error: " + str(e))
            return [500, "text/plain", str(e).encode("utf-8", errors="ignore")]

    def _is_fake_image_stream(self, text, source_url):
        """图片流伪装检测"""
        low_url = (source_url or "").lower()
        # 已知图片流服务商特征
        for sig in ("doyinapi", "svip", "imgcdn", "photo"):
            if sig in low_url:
                return True
        # 分片扩展名为图片格式
        for line in str(text or "").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            low = line.lower().split("?")[0]
            if low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                return True
        return False

    def _clean_m3u8(self, text, source_url):
        """五层m3u8清洗"""
        lines = [l.strip() for l in str(text or "").replace("\r", "").split("\n") if l.strip()]
        if not lines:
            return "#EXTM3U\n"
        
        # 第2层：多码率主表透传
        if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
            return self._clean_m3u8_multi(lines, source_url)
        
        # 第3层：正片目录锚点（KEY URI目录优先）
        main_dir = self._resolve_main_dir(lines, source_url)
        
        # 第4层：分片过滤
        segments, removed, kept = self._filter_segments(lines, source_url, main_dir)
        
        # 第5层：全滤兜底（kept==0时回退不过滤）
        if kept == 0 and removed > 0:
            self.log("广告过滤命中全部分片，判定锚点失效，回退为不过滤模式")
            out = [self._rewrite_m3u8_tag(l, source_url) for l in lines]
            return "\n".join(out) + "\n"
        
        if removed:
            self.log(f"m3u8已过滤广告分片: {removed}个，保留正片: {kept}个")
        
        # 第5层续：冗余标签清理
        out = self._dedup_tags(segments, source_url)
        return "\n".join(out) + "\n"

    def _clean_m3u8_multi(self, lines, source_url):
        """多码率主表透传"""
        out = []
        for line in lines:
            if line.startswith("#"):
                out.append(line)
                continue
            child = urllib.parse.urljoin(source_url, line)
            if ".m3u8" in child.lower():
                out.append(self._m3u8_proxy_url(child))
            else:
                out.append(child)
        return "\n".join(out) + "\n"

    def _resolve_main_dir(self, lines, source_url):
        """解析正片目录锚点：KEY URI目录优先"""
        import posixpath
        parsed = urllib.parse.urlparse(source_url)
        main_dir = posixpath.dirname(parsed.path)
        if not main_dir.endswith("/"):
            main_dir += "/"
        
        # 优先以KEY URI目录为锚点
        for line in lines:
            if not line.startswith("#EXT-X-KEY") or "URI=" not in line:
                continue
            m = re.search(r'URI="([^"]+)"', line)
            if not m:
                continue
            key_uri = m.group(1)
            key_full = key_uri if key_uri.startswith("http") else urllib.parse.urljoin(source_url, key_uri)
            key_path = urllib.parse.urlparse(key_full).path
            key_dir = posixpath.dirname(key_path)
            if key_dir and key_dir != "/":
                return key_dir + "/"
        return main_dir

    def _filter_segments(self, lines, source_url, main_dir):
        """分片过滤：仅保留正片目录前缀匹配的分片"""
        segments = []
        pending = []
        removed = 0
        kept = 0
        
        for line in lines:
            if line.startswith("#EXTINF"):
                pending = [line]
                continue
            if pending and line.startswith("#"):
                pending.append(line)
                continue
            if pending:
                media_url = urllib.parse.urljoin(source_url, line)
                media_path = urllib.parse.urlparse(media_url).path
                if media_path.startswith(main_dir):
                    segments.extend(pending)
                    segments.append(media_url)
                    kept += 1
                else:
                    removed += 1
                pending = []
                continue
            if line.startswith("#"):
                segments.append(line)
            else:
                segments.append(urllib.parse.urljoin(source_url, line))
        return segments, removed, kept

    def _dedup_tags(self, segments, source_url):
        """冗余标签清理：连续同类标签去重，清尾部"""
        NOISE = ("#EXT-X-DISCONTINUITY", "#EXT-X-KEY:METHOD=NONE")
        out = []
        for line in segments:
            line = self._rewrite_m3u8_tag(line, source_url)
            if line in NOISE:
                if not out or out[-1] in NOISE:
                    continue
            out.append(line)
        while len(out) > 1 and out[-1] in NOISE:
            out.pop()
        return out

    def _rewrite_m3u8_tag(self, line, source_url):
        """重写m3u8标签URI为绝对地址"""
        if line.startswith("#EXT-X-KEY") or line.startswith("#EXT-X-MAP"):
            def repl(m):
                uri = m.group(1)
                if uri.startswith(("http://", "https://")):
                    return 'URI="' + uri + '"'
                return 'URI="' + urllib.parse.urljoin(source_url, uri) + '"'
            return re.sub(r'URI="([^"]+)"', repl, line)
        if line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                return line
            return urllib.parse.urljoin(source_url, line)
        return line

    def recommendContent(self, ids, pg="1"):
        """相关推荐（从详情页解析）"""
        try:
            if not ids or not ids[0]:
                return {"list": []}
            raw = ids[0]
            parts = raw.split('|$|')
            vod_id = parts[0] if len(parts) > 0 else ""
            if vod_id and vod_id.isdigit():
                url = f"{self.host}/video/{vod_id}/"
            else:
                return {"list": []}
            
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if not resp or resp.status_code != 200:
                return {"list": []}
            html = resp.text or ""
            
            # 从详情页提取相关推荐（mt3-grid中的视频卡片）
            return self._parse_video_list(html)
        except Exception:
            return {"list": []}

    def destroy(self):
        """释放资源"""
        pass