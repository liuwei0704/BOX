# coding: utf-8
"""
站点: 枫林网 (imaple8.co)
域名: https://imaple8.co/
类型: MacCMS 标准影视站
特性: HTML直接渲染，多分类（电影/电视剧/综艺/动漫）
"""

import re
import json
from urllib.parse import quote, urljoin, urlparse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://imaple8.co"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.host + '/',
        }
        # 分类列表（一级分类）
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
        ]
        
        # 筛选配置
        # 地区选项
        area_options = [
            {"n": "全部", "v": ""},
            {"n": "大陆", "v": "大陆"},
            {"n": "香港", "v": "香港"},
            {"n": "台湾", "v": "台湾"},
            {"n": "美国", "v": "美国"},
            {"n": "法国", "v": "法国"},
            {"n": "英国", "v": "英国"},
            {"n": "日本", "v": "日本"},
            {"n": "韩国", "v": "韩国"},
            {"n": "德国", "v": "德国"},
            {"n": "泰国", "v": "泰国"},
            {"n": "印度", "v": "印度"},
            {"n": "意大利", "v": "意大利"},
            {"n": "西班牙", "v": "西班牙"},
            {"n": "加拿大", "v": "加拿大"},
            {"n": "其他", "v": "其他"},
        ]
        # 年份选项（最近15年）
        year_options = [{"n": "全部", "v": ""}]
        import datetime
        current_year = datetime.datetime.now().year
        for y in range(current_year, current_year - 15, -1):
            year_options.append({"n": str(y), "v": str(y)})
        
        # 电影类型选项
        movie_type_options = [
            {"n": "全部", "v": ""},
            {"n": "动作", "v": "动作"},
            {"n": "喜剧", "v": "喜剧"},
            {"n": "爱情", "v": "爱情"},
            {"n": "科幻", "v": "科幻"},
            {"n": "恐怖", "v": "恐怖"},
            {"n": "剧情", "v": "剧情"},
            {"n": "战争", "v": "战争"},
            {"n": "纪录片", "v": "纪录片"},
            {"n": "动画", "v": "动画"},
            {"n": "悬疑", "v": "悬疑"},
            {"n": "犯罪", "v": "犯罪"},
            {"n": "冒险", "v": "冒险"},
            {"n": "奇幻", "v": "奇幻"},
            {"n": "古装", "v": "古装"},
            {"n": "微电影", "v": "微电影"},
            {"n": "动漫片", "v": "动漫片"},
        ]
        # 动漫类型选项（与电影略有不同）
        anime_type_options = [
            {"n": "全部", "v": ""},
            {"n": "港台動漫", "v": "港台動漫"},
            {"n": "日韓動漫", "v": "日韓動漫"},
            {"n": "大陸動漫", "v": "大陸動漫"},
            {"n": "歐美動漫", "v": "歐美動漫"},
            {"n": "海外動漫", "v": "海外動漫"},
        ]
        # 电视剧类型选项
        tv_type_options = [
            {"n": "全部", "v": ""},
            {"n": "古装", "v": "古装"},
            {"n": "都市", "v": "都市"},
            {"n": "爱情", "v": "爱情"},
            {"n": "悬疑", "v": "悬疑"},
            {"n": "犯罪", "v": "犯罪"},
            {"n": "历史", "v": "历史"},
            {"n": "战争", "v": "战争"},
            {"n": "科幻", "v": "科幻"},
            {"n": "奇幻", "v": "奇幻"},
            {"n": "喜剧", "v": "喜剧"},
            {"n": "剧情", "v": "剧情"},
            {"n": "家庭", "v": "家庭"},
            {"n": "武侠", "v": "武侠"},
            {"n": "泰剧", "v": "泰剧"},
            {"n": "港剧", "v": "港剧"},
            {"n": "台剧", "v": "台剧"},
            {"n": "日剧", "v": "日剧"},
            {"n": "韩剧", "v": "韩剧"},
            {"n": "美剧", "v": "美剧"},
            {"n": "海外剧", "v": "海外剧"},
        ]
        # 综艺类型选项
        variety_type_options = [
            {"n": "全部", "v": ""},
            {"n": "港台綜藝", "v": "港台綜藝"},
            {"n": "日韓綜藝", "v": "日韓綜藝"},
            {"n": "大陸綜藝", "v": "大陸綜藝"},
            {"n": "歐美綜藝", "v": "歐美綜藝"},
        ]
        
        self.filters = {
            # 电影筛选
            "1": [
                {"key": "area", "name": "地区", "value": area_options},
                {"key": "year", "name": "年份", "value": year_options},
                {"key": "type", "name": "类型", "value": movie_type_options},
            ],
            # 电视剧筛选
            "2": [
                {"key": "area", "name": "地区", "value": area_options},
                {"key": "year", "name": "年份", "value": year_options},
                {"key": "type", "name": "类型", "value": tv_type_options},
            ],
            # 综艺筛选
            "3": [
                {"key": "area", "name": "地区", "value": area_options},
                {"key": "year", "name": "年份", "value": year_options},
                {"key": "type", "name": "类型", "value": variety_type_options},
            ],
            # 动漫筛选
            "4": [
                {"key": "area", "name": "地区", "value": area_options},
                {"key": "year", "name": "年份", "value": year_options},
                {"key": "type", "name": "类型", "value": anime_type_options},
            ],
        }
    def getName(self):
        return "枫林网"

    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    def fix_url(self, url):
        if not url:
            return ""
        url = url.strip()
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.host.rstrip("/") + url
        return self.host.rstrip("/") + "/" + url.lstrip("/")

    def fetch_html(self, url):
        try:
            resp = self.fetch(url, headers=self.headers, timeout=15)
            if resp is None:
                return ""
            if hasattr(resp, "text"):
                return resp.text
            if hasattr(resp, "content"):
                if isinstance(resp.content, bytes):
                    try:
                        return resp.content.decode('utf-8', errors='ignore')
                    except:
                        pass
                return str(resp.content)
            return ""
        except Exception as e:
            print("fetch error:", e)
            return ""

    def _parse_extend(self, extend):
        """extend 参数多格式兼容"""
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
    def _extract_vod_id(self, url):
        """从详情页URL提取视频ID"""
        if not url:
            return ""
        m = re.search(r'/vod/(\d+)\.html', url)
        if m:
            return m.group(1)
        return url

    def _parse_video_list(self, html, limit=30):
        """解析视频列表"""
        videos = []
        if not html:
            return videos

        # 匹配视频项：.myui-vodlist__box
        pattern = r'<li[^>]*class="[^"]*col-lg-[^"]*"[^>]*>.*?<div[^>]*class="[^"]*myui-vodlist__box[^"]*"[^>]*>.*?<a[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*data-original="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*pic-text[^"]*"[^>]*>([^<]*)</span>.*?</a>.*?<div[^>]*class="[^"]*myui-vodlist__detail[^"]*"[^>]*>.*?<h4[^>]*class="[^"]*title[^"]*"[^>]*>.*?<a[^>]*href="[^"]*"[^>]*>(.*?)</a>.*?</h4>.*?</div>.*?</div>.*?</li>'
        matches = re.findall(pattern, html, re.DOTALL)

        for match in matches:
            href, title_attr, pic, remark, title = match
            vid = self._extract_vod_id(href)
            if not vid:
                continue
            name = title.strip() or title_attr.strip()
            if not name:
                continue
            pic_url = self.fix_url(pic.strip()) if pic else ""
            videos.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic_url,
                "vod_remarks": remark.strip() if remark else "",
            })
            if len(videos) >= limit:
                break

        return videos

    def _parse_page_count(self, html):
        """解析分页信息 - 支持枫林网的分页格式"""
        if not html:
            return 1
        
        # 方法1: 匹配 "当前页/总页数" 格式，如 "2/2766"
        page_info_pattern = r'<a[^>]*class="[^"]*btn[^"]*btn-warm[^"]*"[^>]*>(\d+)/(\d+)</a>'
        match = re.search(page_info_pattern, html)
        if match:
            return int(match.group(2))
        
        # 方法2: 查找 "尾頁" 链接，提取最大页码
        last_page_pattern = r'<a[^>]*href="[^"]*/page/(\d+)/[^"]*"[^>]*>尾頁</a>'
        match = re.search(last_page_pattern, html)
        if match:
            return int(match.group(1))
        
        # 方法3: 查找页码数字链接，取最大值
        page_pattern = r'<a[^>]*href="[^"]*/page/(\d+)/[^"]*"[^>]*>(\d+)</a>'
        matches = re.findall(page_pattern, html)
        if matches:
            pages = [int(m[1]) for m in matches if m[0].isdigit() and m[1].isdigit()]
            if pages:
                return max(pages)
        
        # 方法4: 查找 "下一页" 链接中的页码
        next_pattern = r'<a[^>]*href="[^"]*/page/(\d+)/[^"]*"[^>]*>下一頁</a>'
        match = re.search(next_pattern, html)
        if match:
            return int(match.group(1)) + 1
        
        return 1
    def _extract_m3u8_from_html(self, html):
        """从HTML中提取m3u8直链 - 参考王室日报的实现"""
        if not html:
            return None
        # 方法1: 从 player_aaaa 中提取
        pattern = r'var\s+player_aaaa\s*=\s*(\{[^;]+\});'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                url = data.get("url", "")
                if url and url.startswith("http") and ".m3u8" in url:
                    return url
            except Exception as e:
                # 如果JSON解析失败，尝试用正则提取url字段
                pass
        # 方法2: 直接提取url字段
        pattern2 = r'"url"\s*:\s*"([^"]+\.m3u8[^"]*)"'
        match2 = re.search(pattern2, html)
        if match2:
            url = match2.group(1)
            if url and url.startswith("http") and ".m3u8" in url:
                return url
        # 方法3: 查找任何m3u8链接
        pattern3 = r'https?://[^"\']+\.m3u8[^"\']*'
        match3 = re.search(pattern3, html)
        if match3:
            return match3.group(0)
        return None
    def homeContent(self, filter=False):
        return {
            "class": self.classes,
            "filters": self.filters if filter else {},
        }

    def getHomeContent(self, filter=False):
        return self.homeContent(filter)

    def homeVideoContent(self):
        """首页推荐 - 解析首页最新视频"""
        html = self.fetch_html(self.host + "/")
        if not html:
            return {"list": []}

        # 从首页提取视频列表（所有板块合并）
        videos = self._parse_video_list(html, 20)
        return {"list": videos}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        """分类列表 - 支持筛选和分页"""
        pg = int(pg) if pg else 1
        tid = str(tid)
        
        # extend 多格式兼容
        extend_dict = self._parse_extend(extend) if extend else {}
        
        # 类型名称到 show_id 的映射（电影分类下的类型）
        type_to_show_id = {
            "动作": "6",
            "喜剧": "7",
            "爱情": "8",
            "科幻": "9",
            "恐怖": "10",
            "剧情": "11",
            "战争": "12",
            "纪录片": "20",
            "微电影": "21",
            "动漫片": "22",
            "港台動漫": "33",
            "日韓動漫": "34",
            "大陸動漫": "35",
            "歐美動漫": "36",
            "海外動漫": "37",
            "港台綜藝": "29",
            "日韓綜藝": "30",
            "大陸綜藝": "31",
            "歐美綜藝": "32",
            "古装": "13",  # 电视剧类型
            "都市": "13",
            "悬疑": "13",
            "犯罪": "13",
            "历史": "13",
            "战争": "13",
            "科幻": "13",
            "奇幻": "13",
            "喜剧": "13",
            "剧情": "13",
            "家庭": "13",
            "武侠": "13",
            "泰剧": "38",
            "港剧": "14",
            "台剧": "15",
            "日剧": "16",
            "韩剧": "23",
            "美剧": "24",
            "海外剧": "25",
        }
        
        # 如果没有筛选参数，使用简化格式
        if not extend_dict:
            if pg == 1:
                url = f"{self.host}/type/{tid}.html"
            else:
                url = f"{self.host}/type/{tid}/page/{pg}.html"
        else:
            # 检查是否有类型筛选
            type_name = extend_dict.get("type", "")
            # 如果有类型筛选且可以映射到 show_id
            if type_name and type_name in type_to_show_id:
                show_id = type_to_show_id[type_name]
                if pg == 1:
                    url = f"{self.host}/show/{show_id}.html"
                else:
                    url = f"{self.host}/show/{show_id}/page/{pg}.html"
            else:
                # 没有类型筛选或类型无法映射，使用地区+年份筛选
                url_parts = [f"{self.host}/type/{tid}"]
                
                year = extend_dict.get("year", "")
                area = extend_dict.get("area", "")
                
                if year:
                    url_parts.append(f"year/{year}")
                if area:
                    url_parts.append(f"area/{area}")
                
                if pg > 1:
                    url_parts.append(f"page/{pg}")
                
                url = "/".join(url_parts) + ".html"
                # 如果没有年份也没有地区，使用默认
                if not year and not area:
                    if pg == 1:
                        url = f"{self.host}/type/{tid}.html"
                    else:
                        url = f"{self.host}/type/{tid}/page/{pg}.html"

        html = self.fetch_html(url)
        if not html:
            if pg == 1:
                fallback_url = f"{self.host}/type/{tid}.html"
            else:
                fallback_url = f"{self.host}/type/{tid}/page/{pg}.html"
            html = self.fetch_html(fallback_url)
            if not html:
                return {"list": [], "page": pg, "pagecount": 1, "limit": 20, "total": 0}

        videos = self._parse_video_list(html, 30)
        pagecount = self._parse_page_count(html)

        return {
            "list": videos,
            "page": pg,
            "pagecount": pagecount if pagecount > 0 else 1,
            "limit": 20,
            "total": pagecount * 20 if pagecount > 0 else 20,
        }
    def detailContent(self, ids):
        """详情页 - 直接访问播放页获取直链"""
        if not ids:
            return {"list": []}
        vid = str(ids[0]) if isinstance(ids, list) else str(ids)

        # 尝试从播放页提取直链（线路1，第1集）
        play_url = None
        for line in ["1", "3"]:  # 线路1: 无尽云, 线路3: 索尼云
            play_page_url = f"{self.host}/play/{vid}-{line}-1.html"
            play_html = self.fetch_html(play_page_url)
            if play_html:
                play_url = self._extract_m3u8_from_html(play_html)
                if play_url:
                    break

        # 获取基本信息（标题、封面、演员）
        title = vid
        pic = ""
        actor = ""
        content = ""
        detail_url = f"{self.host}/vod/{vid}.html"
        detail_html = self.fetch_html(detail_url)
        if detail_html:
            m = re.search(r'<h1[^>]*>([^<]+)</h1>', detail_html)
            if m:
                title = m.group(1).strip()
            m = re.search(r'<img[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*data-original="([^"]+)"', detail_html)
            if m:
                pic = self.fix_url(m.group(1))
            m = re.search(r'<p[^>]*>主演[：:]\s*([^<]+)</p>', detail_html)
            if m:
                actor = m.group(1).strip()
            m = re.search(r'<div[^>]*class="[^"]*myui-content__conten[^"]*"[^>]*>([^<]*)</div>', detail_html, re.DOTALL)
            if m:
                content = re.sub(r'<[^>]+>', '', m.group(1)).strip()

        if play_url:
            vod = {
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_content": content,
                "vod_actor": actor,
                "vod_remarks": "",
                "vod_play_from": "线路1",
                "vod_play_url": f"播放${play_url}",
            }
        else:
            # 降级：返回详情页URL
            vod = {
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_content": content,
                "vod_actor": actor,
                "vod_remarks": "",
                "vod_play_from": "线路1",
                "vod_play_url": f"播放${detail_url}",
            }
        return {"list": [vod]}
    def searchContent(self, key, quick=False, pg="1"):
        """搜索 - 解析搜索页面的HTML结构"""
        if not key:
            return {"list": [], "page": 1, "pagecount": 1, "total": 0}

        pg = int(pg) if pg else 1
        encoded_key = quote(key)
        if pg == 1:
            url = f"{self.host}/search/wd/{encoded_key}.html"
        else:
            url = f"{self.host}/search/page/{pg}/wd/{encoded_key}.html"

        html = self.fetch_html(url)
        if not html:
            return {"list": [], "page": pg, "pagecount": 1, "total": 0}

        videos = []
        # 搜索页面结构: #searchList li.clearfix
        pattern = r'<li[^>]*class="[^"]*clearfix[^"]*"[^>]*>.*?<a[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*href="([^"]+)"[^>]*data-original="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*pic-text[^"]*"[^>]*>([^<]*)</span>.*?</a>.*?<h4[^>]*class="[^"]*title[^"]*"[^>]*>.*?<a[^>]*class="[^"]*searchkey[^"]*"[^>]*href="[^"]*"[^>]*>([^<]*)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for match in matches:
            href, pic, remark, title = match
            vid = self._extract_vod_id(href)
            if not vid:
                continue
            name = title.strip() if title else ""
            if not name:
                continue
            pic_url = self.fix_url(pic.strip()) if pic else ""
            videos.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic_url,
                "vod_remarks": remark.strip() if remark else "",
            })

        # 解析分页
        pagecount = 1
        pager = re.search(r'<a[^>]*class="[^"]*btn[^"]*"[^>]*href="[^"]*page/(\d+)/wd/[^"]*"[^>]*>(\d+)</a>', html)
        if pager:
            pagecount = int(pager.group(2))
        # 检查是否有"尾页"
        last_page = re.search(r'/search/page/(\d+)/wd/[^"]*"[^>]*>尾頁</a>', html)
        if last_page:
            pagecount = int(last_page.group(1))

        return {
            "list": videos,
            "page": pg,
            "pagecount": pagecount if pagecount > 0 else 1,
            "total": pagecount * 20 if pagecount > 0 else 20,
        }
    def playerContent(self, flag, vid, vipFlags=None):
        """播放解析 - 直接访问播放页提取直链"""
        headers = {
            "User-Agent": self.headers.get("User-Agent", ""),
            "Referer": self.host + "/",
        }

        # 确保 vid 是字符串
        vid = str(vid) if vid is not None else ""

        if not vid:
            return {"parse": 1, "url": "", "header": headers}

        # 如果已经是直链
        if vid.startswith("http") and ".m3u8" in vid:
            return {"parse": 0, "url": vid, "header": headers}

        # 如果是数字ID，直接访问播放页提取直链
        if vid.isdigit():
            # 尝试线路1（无尽云）
            play_url = None
            for line in ["1", "3", "2", "4"]:
                play_page_url = f"{self.host}/play/{vid}-{line}-1.html"
                html = self.fetch_html(play_page_url)
                if html:
                    play_url = self._extract_m3u8_from_html(html)
                    if play_url:
                        return {"parse": 0, "url": play_url, "header": headers}

        # 如果传入的是URL，尝试从该页面提取直链
        if vid.startswith("http"):
            html = self.fetch_html(vid)
            if html:
                play_url = self._extract_m3u8_from_html(html)
                if play_url:
                    return {"parse": 0, "url": play_url, "header": headers}
            return {"parse": 1, "url": vid, "header": headers}

        # 降级嗅探
        return {"parse": 1, "url": f"{self.host}/vod/{vid}.html", "header": headers}
    def recommendContent(self, ids):
        """相关推荐"""
        return {"list": []}

    def destroy(self):
        pass

    def localProxy(self, params):
        return [404, "text/plain", b"Not Found"]