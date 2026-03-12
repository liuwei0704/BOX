import sys
import re
import json
import requests
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "Asian-AV"

    def init(self, extend=""):
        super().init(extend)
        self.site_url = "https://asian-av.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.site_url
        }

    def homeContent(self, filter):
        # 定义核心分类
        cate_list = [
            {"type_name": "最新视频", "type_id": "latest"},
            {"type_name": "热门视频", "type_id": "popular"},
            {"type_name": "最多观看", "type_id": "most-viewed"},
            {"type_name": "随机视频", "type_id": "random"}
        ]
        return {"class": cate_list}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if str(pg).isdigit() else 1
        # 构造分页URL：https://asian-av.com/page/2/?filter=popular
        if pg == 1:
            url = f"{self.site_url}/?filter={tid}"
        else:
            url = f"{self.site_url}/page/{pg}/?filter={tid}"
            
        res = self.fetch(url)
        video_list = []
        if res and res.ok:
            html = res.text
            # 匹配 article 块
            matches = re.findall(r'<article[^>]*>(.*?)</article>', html, re.S)
            for item_html in matches:
                # 提取ID和名称 (从 href="https://asian-av.com/7578/" 提取 7578)
                id_match = re.search(r'href="https://asian-av.com/(\d+)/"', item_html)
                name_match = re.search(r'title="([^"]+)"', item_html)
                # 提取封面 (data-src)
                pic_match = re.search(r'data-src="([^"]+)"', item_html)
                # 提取备注 (时长或播放量)
                remark_match = re.search(r'<span class="duration">([^<]+)</span>', item_html)

                if id_match and name_match:
                    video_list.append({
                        "vod_id": id_match.group(1),
                        "vod_name": name_match.group(1).strip(),
                        "vod_pic": pic_match.group(1) if pic_match else "",
                        "vod_remarks": remark_match.group(1) if remark_match else ""
                    })
        
        return {
            "list": video_list,
            "page": pg,
            "pagecount": pg + 1, # 简单处理，始终显示下一页
            "limit": 20,
            "total": 999
        }

    def detailContent(self, ids):
        if not hasattr(self, 'site_url'):
            self.site_url = "https://asian-av.com"
        if not hasattr(self, 'headers'):
            self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            
        vod_id = ids[0]
        url = f"{self.site_url}/{vod_id}/"
        res = self.fetch(url)
        if not res or not res.ok:
            return {}
        
        html = res.text
        # 提取标题和封面
        name = re.search(r'og:title" content="([^"]+)"', html)
        pic = re.search(r'og:image" content="([^"]+)"', html)
        
        vod = {
            "vod_id": vod_id,
            "vod_name": name.group(1) if name else "未知视频",
            "vod_pic": pic.group(1) if pic else "",
            "type_name": "成人视频",
            "vod_year": "",
            "vod_area": "亚洲",
            "vod_remarks": "高清",
            "vod_actor": "未知",
            "vod_director": "未知",
            "vod_content": name.group(1) if name else ""
        }
        
        # 构造播放线路：WP站点通常直连
        vod["vod_play_from"] = "插件播放"
        vod["vod_play_url"] = f"立即播放${vod_id}"
        
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        if not hasattr(self, 'site_url'):
            self.site_url = "https://asian-av.com"
        if not hasattr(self, 'headers'):
            self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            
        # 这里的 id 是 detailContent 传过来的 vod_id
        url = f"{self.site_url}/{id}/"
        res = self.fetch(url)
        if not res or not res.ok:
            return {}
        
        html = res.text
        # 深度嗅探：尝试在详情页源码中寻找任何可能的隐藏播放地址
        # 1. 尝试寻找被Base64混淆的地址 (通常以 aHR0c 开头)
        b64_match = re.search(r'(?:["\'])(aHR0c[a-zA-Z0-9+/=]{50,})(?:["\'])', html)
        if b64_match:
            import base64
            try:
                real_url = base64.b64decode(b64_match.group(1)).decode('utf-8')
                if "m3u8" in real_url or "mp4" in real_url:
                    return {"parse": 0, "url": real_url, "header": self.headers}
            except:
                pass

        # 2. 如果没有直接地址，返回页面让TVBox内置解析尝试嗅探
        return {"parse": 1, "url": url, "header": self.headers}

    def fetch(self, url):
        try:
            return requests.get(url, headers=self.headers, timeout=10, verify=False)
        except:
            return None