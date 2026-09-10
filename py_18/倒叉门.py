# 倒叉门 TVBox 爬虫
# 站点：https://pd.daocamen03.xyz
# 类型：成人视频聚合站（Vue SPA）
# 特点：首页预渲染卡片，直接包含 m3u8 地址
# 最后验证：2026-09-10

import re
import json
from base.spider import Spider

class Spider(Spider):
    def __init__(self):
        self.host = "https://pd.daocamen03.xyz"
        self.name = "倒叉门"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host + "/"
        }
        # 分类列表（从首页导航栏提取）
        self.classes = [
            {"type_id": "欧美视频", "type_name": "欧美视频"},
            {"type_id": "无码中字", "type_name": "无码中字"},
            {"type_id": "日本无码", "type_name": "日本无码"},
            {"type_id": "日本有码", "type_name": "日本有码"},
            {"type_id": "成人动漫", "type_name": "成人动漫"},
            {"type_id": "网曝吃瓜", "type_name": "网曝吃瓜"},
            {"type_id": "有码中字", "type_name": "有码中字"},
            {"type_id": "国产视频", "type_name": "国产视频"},
        ]
        self.filters = {}

    def init(self, extend=""):
        """初始化环境（零网络依赖）"""
        pass

    def getName(self):
        return self.name

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeContent(self, filter=False):
        """返回首页分类和筛选"""
        return {
            "class": self.classes,
            "filters": self.filters
        }

    def homeVideoContent(self):
        """返回首页推荐列表"""
        r = self.fetch(self.host + "/index.php", headers=self.headers, timeout=15)
        if not r or r.status_code != 200:
            return {"list": []}
        html = r.text
        items = self._parse_vod_list(html)
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        """返回分类列表（分页）"""
        # 分类页 URL 格式：category.php?name=分类名&page=页码
        # tid 是分类名（如 "欧美视频"）
        # pg 是页码（从 1 开始）
        page = pg or 1
        # URL 编码分类名
        import urllib.parse
        encoded_name = urllib.parse.quote(tid)
        url = f"{self.host}/category.php?name={encoded_name}&page={page}"
        r = self.fetch(url, headers=self.headers, timeout=15)
        if not r or r.status_code != 200:
            return {"list": [], "page": page, "pagecount": 1, "limit": 0, "total": 0}
        html = r.text
        items = self._parse_vod_list(html)
        # 获取总页数（从分页器解析）
        total_pages = self._parse_total_pages(html)
        return {
            "list": items,
            "page": page,
            "pagecount": total_pages,
            "limit": len(items),
            "total": len(items) * total_pages
        }
    def detailContent(self, ids):
        """返回视频详情+播放地址"""
        if not ids:
            return {"list": []}
        vid = ids[0]
        # 解码 vod_id：格式为 "标题|m3u8地址"
        if "|" in vid:
            parts = vid.split("|", 1)
            title = parts[0]
            url = parts[1]
            return {
                "list": [{
                    "vod_id": url,
                    "vod_name": title,
                    "vod_pic": "",
                    "type_name": "",
                    "vod_play_from": "播放",
                    "vod_play_url": "播放$" + url
                }]
            }
        # 兼容旧格式：直接是 m3u8 地址
        if vid.startswith("http") and ".m3u8" in vid:
            return {
                "list": [{
                    "vod_id": vid,
                    "vod_name": "视频",
                    "vod_pic": "",
                    "type_name": "",
                    "vod_play_from": "播放",
                    "vod_play_url": "播放$" + vid
                }]
            }
        return {"list": []}
    def searchContent(self, key, quick, pg=1):
        """返回搜索结果"""
        # 该站搜索为纯前端 Vue 组件，数据在客户端内存中过滤，无 API 请求
        # 服务端 search.php 只返回空壳页面，无法爬取搜索数据
        # 建议用户通过分类浏览查找内容
        return {"list": []}
    def playerContent(self, flag, id, vipFlags):
        """返回播放地址"""
        # 直接返回 m3u8 直链
        return {
            "parse": 0,
            "url": id,
            "header": self.headers
        }

    def recommendContent(self, ids, pg):
        """返回相关推荐"""
        # 从首页取推荐
        r = self.fetch(self.host + "/index.php", headers=self.headers, timeout=15)
        if not r or r.status_code != 200:
            return {"list": []}
        html = r.text
        items = self._parse_vod_list(html)
        return {"list": items}

    def destroy(self):
        """释放资源"""
        pass

    def _parse_vod_list(self, html):
        """解析视频列表（从 .vod 卡片）"""
        items = []
        # 匹配 .vod 容器
        pattern = r'<div class="vod">.*?<a href="\./detail\.php\?id=([^"]+)" target="_blank">.*?<img class="content-img lazy" data-original="([^"]+)"[^>]*>.*?<div class="vod-txt">.*?<a href="[^"]+" target="_blank">([^<]+)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        for m in matches:
            url = m[0]
            pic = m[1]
            title = m[2].strip()
            # 解码 URL 编码
            if url.startswith("https%3A"):
                url = self._url_decode(url)
            # vod_id 编码为 "标题|m3u8地址"，以便 detailContent 提取标题
            encoded_id = title + "|" + url
            items.append({
                "vod_id": encoded_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": ""
            })
        return items
    def _url_decode(self, s):
        """简单 URL 解码"""
        import urllib.parse
        return urllib.parse.unquote(s)

    def _parse_total_pages(self, html):
        """从 HTML 中解析总页数"""
        # 方式1：从分页器文本中提取 "1/2026" 格式
        match = re.search(r'(\d+)\s*/\s*(\d+)', html)
        if match:
            total = int(match.group(2))
            if total > 1:
                return total
        # 方式2：从分页器链接中取最大页码
        matches = re.findall(r'page=(\d+)', html)
        if matches:
            pages = [int(p) for p in matches]
            if pages:
                max_page = max(pages)
                if max_page > 1:
                    return max_page
        # 方式3：从尾页链接中提取
        match = re.search(r'page=(\d+)"[^>]*>尾页</a>', html)
        if match:
            return int(match.group(1))
        return 1
