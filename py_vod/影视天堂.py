# coding: utf-8
import json
import re
from urllib.parse import urljoin, urlparse, quote

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def __init__(self):
        self.host = "https://ysttv.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 22127RK46C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
            "Referer": self.host + "/"
        }
        self.classes = [
            {"type_id": "movie", "type_name": "电影"},
            {"type_id": "teleplay", "type_name": "剧集"},
            {"type_id": "variety", "type_name": "综艺"},
            {"type_id": "anime", "type_name": "动漫"},
            {"type_id": "playlet", "type_name": "短剧"},
        ]
        # 筛选配置 - 每个分类独立
        self.filters = {
            "movie": self._get_movie_filters(),
            "teleplay": self._get_teleplay_filters(),
            "variety": self._get_variety_filters(),
            "anime": self._get_anime_filters(),
            "playlet": self._get_playlet_filters(),
        }
    def _get_movie_filters(self):
        return [
            {
                "key": "type",
                "name": "类型",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "动作", "v": "action"},
                    {"n": "喜剧", "v": "comedy"},
                    {"n": "爱情", "v": "romance"},
                    {"n": "科幻", "v": "sci-fi"},
                    {"n": "悬疑", "v": "mystery"},
                    {"n": "惊悚", "v": "thriller"},
                    {"n": "恐怖", "v": "horror"},
                    {"n": "犯罪", "v": "crime"},
                    {"n": "剧情", "v": "drama"},
                    {"n": "奇幻", "v": "fantasy"},
                    {"n": "冒险", "v": "adventure"},
                    {"n": "战争", "v": "war"},
                    {"n": "历史", "v": "history"},
                    {"n": "传记", "v": "biography"},
                    {"n": "音乐", "v": "music"},
                    {"n": "歌舞", "v": "musical"},
                    {"n": "运动", "v": "sports"},
                    {"n": "灾难", "v": "disaster"},
                    {"n": "伦理", "v": "ethics"},
                    {"n": "情色", "v": "erotic"},
                    {"n": "同性", "v": "lgbt"},
                ]
            },
            {
                "key": "year",
                "name": "年份",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "2025", "v": "2025"},
                    {"n": "2024", "v": "2024"},
                    {"n": "2023", "v": "2023"},
                    {"n": "2022", "v": "2022"},
                    {"n": "2021", "v": "2021"},
                    {"n": "2020", "v": "2020"},
                    {"n": "2019", "v": "2019"},
                    {"n": "2018", "v": "2018"},
                    {"n": "2017", "v": "2017"},
                    {"n": "2016", "v": "2016"},
                    {"n": "2015", "v": "2015"},
                    {"n": "2014", "v": "2014"},
                    {"n": "2013", "v": "2013"},
                    {"n": "2012", "v": "2012"},
                    {"n": "2011", "v": "2011"},
                    {"n": "2010", "v": "2010"},
                    {"n": "2009", "v": "2009"},
                    {"n": "2008", "v": "2008"},
                    {"n": "2007", "v": "2007"},
                    {"n": "2006", "v": "2006"},
                    {"n": "2005", "v": "2005"},
                    {"n": "2004", "v": "2004"},
                    {"n": "2003", "v": "2003"},
                    {"n": "2002", "v": "2002"},
                    {"n": "2001", "v": "2001"},
                    {"n": "2000", "v": "2000"},
                ]
            },
            {
                "key": "area",
                "name": "地区",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "大陆", "v": "china"},
                    {"n": "台湾", "v": "taiwan"},
                    {"n": "香港", "v": "hong-kong"},
                    {"n": "美国", "v": "usa"},
                    {"n": "韩国", "v": "korea"},
                    {"n": "日本", "v": "japan"},
                    {"n": "英国", "v": "uk"},
                    {"n": "法国", "v": "france"},
                    {"n": "德国", "v": "germany"},
                    {"n": "泰国", "v": "thailand"},
                    {"n": "印度", "v": "india"},
                    {"n": "澳大利亚", "v": "australia"},
                    {"n": "加拿大", "v": "canada"},
                    {"n": "西班牙", "v": "spain"},
                    {"n": "意大利", "v": "italy"},
                    {"n": "俄罗斯", "v": "russia"},
                    {"n": "巴西", "v": "brazil"},
                    {"n": "墨西哥", "v": "mexico"},
                ]
            },
            {
                "key": "sort",
                "name": "排序",
                "value": [
                    {"n": "时间", "v": "latest"},
                    {"n": "人气", "v": "hot"},
                    {"n": "评分", "v": "rating"},
                ]
            }
        ]

    def _get_teleplay_filters(self):
        return [
            {
                "key": "type",
                "name": "类型",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "剧情", "v": "drama"},
                    {"n": "爱情", "v": "romance"},
                    {"n": "喜剧", "v": "comedy"},
                    {"n": "悬疑", "v": "mystery"},
                    {"n": "惊悚", "v": "thriller"},
                    {"n": "恐怖", "v": "horror"},
                    {"n": "犯罪", "v": "crime"},
                    {"n": "动作", "v": "action"},
                    {"n": "奇幻", "v": "fantasy"},
                    {"n": "科幻", "v": "sci-fi"},
                    {"n": "古装", "v": "costume"},
                    {"n": "家庭", "v": "family"},
                    {"n": "同性", "v": "lgbt"},
                    {"n": "战争", "v": "war"},
                    {"n": "历史", "v": "history"},
                    {"n": "短片", "v": "short-series"},
                    {"n": "动画", "v": "animation"},
                    {"n": "伦理", "v": "ethics"},
                    {"n": "情色", "v": "erotic"},
                ]
            },
            {
                "key": "year",
                "name": "年份",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "2025", "v": "2025"},
                    {"n": "2024", "v": "2024"},
                    {"n": "2023", "v": "2023"},
                    {"n": "2022", "v": "2022"},
                    {"n": "2021", "v": "2021"},
                    {"n": "2020", "v": "2020"},
                    {"n": "2019", "v": "2019"},
                    {"n": "2018", "v": "2018"},
                    {"n": "2017", "v": "2017"},
                    {"n": "2016", "v": "2016"},
                    {"n": "2015", "v": "2015"},
                    {"n": "2014", "v": "2014"},
                    {"n": "2013", "v": "2013"},
                    {"n": "2012", "v": "2012"},
                    {"n": "2011", "v": "2011"},
                    {"n": "2010", "v": "2010"},
                ]
            },
            {
                "key": "area",
                "name": "地区",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "大陆", "v": "china"},
                    {"n": "台湾", "v": "taiwan"},
                    {"n": "香港", "v": "hong-kong"},
                    {"n": "美国", "v": "usa"},
                    {"n": "韩国", "v": "korea"},
                    {"n": "日本", "v": "japan"},
                    {"n": "英国", "v": "uk"},
                    {"n": "泰国", "v": "thailand"},
                ]
            },
            {
                "key": "sort",
                "name": "排序",
                "value": [
                    {"n": "时间", "v": "latest"},
                    {"n": "人气", "v": "hot"},
                    {"n": "评分", "v": "rating"},
                ]
            }
        ]

    def _get_variety_filters(self):
        return [
            {
                "key": "type",
                "name": "类型",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "真人秀", "v": "reality-show"},
                    {"n": "脱口秀", "v": "talk-show"},
                    {"n": "选秀", "v": "talent-show"},
                ]
            },
            {
                "key": "year",
                "name": "年份",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "2025", "v": "2025"},
                    {"n": "2024", "v": "2024"},
                    {"n": "2023", "v": "2023"},
                ]
            },
            {
                "key": "area",
                "name": "地区",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "大陆", "v": "china"},
                    {"n": "香港", "v": "hong-kong"},
                    {"n": "台湾", "v": "taiwan"},
                    {"n": "韩国", "v": "korea"},
                    {"n": "日本", "v": "japan"},
                    {"n": "美国", "v": "usa"},
                ]
            },
            {
                "key": "sort",
                "name": "排序",
                "value": [
                    {"n": "时间", "v": "latest"},
                    {"n": "人气", "v": "hot"},
                    {"n": "评分", "v": "rating"},
                ]
            }
        ]

    def _get_anime_filters(self):
        return [
            {
                "key": "type",
                "name": "类型",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "日漫", "v": "anime-jp"},
                    {"n": "国漫", "v": "anime-cn"},
                    {"n": "美漫", "v": "anime-us"},
                ]
            },
            {
                "key": "year",
                "name": "年份",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "2025", "v": "2025"},
                    {"n": "2024", "v": "2024"},
                    {"n": "2023", "v": "2023"},
                ]
            },
            {
                "key": "area",
                "name": "地区",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "日本", "v": "japan"},
                    {"n": "大陆", "v": "china"},
                    {"n": "美国", "v": "usa"},
                ]
            },
            {
                "key": "sort",
                "name": "排序",
                "value": [
                    {"n": "时间", "v": "latest"},
                    {"n": "人气", "v": "hot"},
                    {"n": "评分", "v": "rating"},
                ]
            }
        ]

    def _get_playlet_filters(self):
        return [
            {
                "key": "type",
                "name": "类型",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "重生", "v": "rebirth"},
                    {"n": "穿越", "v": "time-travel"},
                    {"n": "复仇", "v": "revenge"},
                    {"n": "战神", "v": "war-god"},
                    {"n": "神医", "v": "divine-doctor"},
                    {"n": "萌娃", "v": "cute-kids"},
                    {"n": "都市", "v": "urban"},
                    {"n": "言情", "v": "romance"},
                    {"n": "玄幻", "v": "xuanhuan"},
                    {"n": "喜剧", "v": "comedy"},
                    {"n": "古装", "v": "costume"},
                ]
            },
            {
                "key": "year",
                "name": "年份",
                "value": [
                    {"n": "全部", "v": ""},
                    {"n": "2025", "v": "2025"},
                    {"n": "2024", "v": "2024"},
                ]
            },
            {
                "key": "sort",
                "name": "排序",
                "value": [
                    {"n": "时间", "v": "latest"},
                    {"n": "人气", "v": "hot"},
                    {"n": "评分", "v": "rating"},
                ]
            }
        ]
    def getName(self):
        return "影视天堂"

    def getDependence(self):
        return []

    def init(self, extend=""):
        self.extend = extend or ""

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters if filter else {}}

    def getHomeContent(self, filter):
        return self.homeContent(filter)

    def homeVideoContent(self):
        html = self._fetch_html("/vod")
        if not html:
            return {"list": []}
        return self._parse_video_list(html)

    def categoryContent(self, tid, pg, filter, extend):
        """分类列表 - 支持分页和筛选"""
        page = pg or "1"
        extend_dict = self._parse_extend(extend)
        
        # 构建URL基础路径: /vod/{tid}
        base_path = f"/vod/{tid}"
        
        # 构建筛选路径
        filter_path = ""
        type_val = extend_dict.get("type", "")
        year_val = extend_dict.get("year", "")
        area_val = extend_dict.get("area", "")
        sort_val = extend_dict.get("sort", "latest")
        
        # 类型筛选: /vod/{tid}/{type}
        if type_val:
            filter_path = f"/{type_val}"
        # 年份筛选: /vod/{tid}/year{year}
        elif year_val:
            filter_path = f"/year{year_val}"
        # 地区筛选: /vod/{tid}/area-{area}
        elif area_val:
            filter_path = f"/area-{area_val}"
        # 排序: /vod/{tid}/{sort} (hot/rating)
        elif sort_val and sort_val != "latest":
            filter_path = f"/{sort_val}"
        
        # 完整URL
        if page == "1":
            url = f"{self.host}{base_path}{filter_path}"
        else:
            url = f"{self.host}{base_path}{filter_path}/{page}"
        
        html = self._fetch_html(url)
        if not html:
            return {"list": [], "page": int(page), "pagecount": 1, "limit": 20, "total": 0}
        
        result = self._parse_video_list(html)
        page_info = self._parse_pagination(html)
        return {
            "list": result.get("list", []),
            "page": int(page),
            "pagecount": page_info.get("pagecount", 1),
            "limit": 20,
            "total": page_info.get("total", 0)
        }
    def detailContent(self, ids):
        vod_id = str(ids[0]) if ids else ""
        if not vod_id:
            return {"list": []}
        
        if "|$|" in vod_id:
            parts = vod_id.split("|$|")
            vid = parts[0]
            name = parts[1] if len(parts) > 1 else ""
            pic = parts[2] if len(parts) > 2 else ""
            remark = parts[3] if len(parts) > 3 else ""
        else:
            vid = vod_id
            name = ""
            pic = ""
            remark = ""
        
        html = self._fetch_html(f"/detail/{vid}/")
        if not html:
            if name:
                return {"list": [{
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": remark,
                    "vod_play_from": "播放",
                    "vod_play_url": f"播放$/{vid}/1"
                }]}
            return {"list": []}
        
        return self._parse_detail(html, vid, vod_id, name, pic, remark)

    def searchContent(self, key, quick, pg="1"):
        if not key:
            return {"list": [], "page": 1}
        
        page = pg or "1"
        encoded_key = quote(str(key), safe='')
        if page == "1":
            search_url = f"{self.host}/search/video/{encoded_key}"
        else:
            search_url = f"{self.host}/search/video/{encoded_key}?page={page}"
        
        html = self._fetch_html(search_url)
        if not html:
            return {"list": [], "page": int(page)}
        
        if "没有找到" in html or "暂无数据" in html or "搜索无结果" in html:
            return {"list": [], "page": int(page)}
        
        result = self._parse_search_results(html)
        return {
            "list": result.get("list", []),
            "page": int(page)
        }

    def playerContent(self, flag, id, vipFlags):
        if not id:
            return {"parse": 0, "url": "", "header": {}}
        
        play_url = str(id).strip()
        if play_url.startswith("http") and ".m3u8" in play_url:
            return {
                "parse": 0,
                "url": play_url,
                "header": {"User-Agent": self.headers["User-Agent"]}
            }
        
        if play_url.startswith("/play/"):
            html = self._fetch_html(play_url)
            if not html:
                return {"parse": 1, "url": play_url, "header": self.headers}
            
            m3u8_url = self._extract_m3u8_from_play(html)
            if m3u8_url:
                return {
                    "parse": 0,
                    "url": m3u8_url,
                    "header": {"User-Agent": self.headers["User-Agent"]}
                }
            
            m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
            if m3u8_match:
                return {
                    "parse": 0,
                    "url": m3u8_match.group(0),
                    "header": {"User-Agent": self.headers["User-Agent"]}
                }
            
            play_vars = re.search(r'var\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html)
            if play_vars:
                return {
                    "parse": 0,
                    "url": play_vars.group(1),
                    "header": {"User-Agent": self.headers["User-Agent"]}
                }
            
            return {"parse": 1, "url": play_url, "header": self.headers}
        
        if play_url.startswith("http"):
            html = self._fetch_html(play_url)
            if html:
                m3u8_url = self._extract_m3u8_from_play(html)
                if m3u8_url:
                    return {
                        "parse": 0,
                        "url": m3u8_url,
                        "header": {"User-Agent": self.headers["User-Agent"]}
                    }
            return {"parse": 1, "url": play_url, "header": self.headers}
        
        return {"parse": 0, "url": "", "header": {}}

    def recommendContent(self, ids, pg):
        vid = str(ids[0]) if ids else ""
        if not vid:
            return {"list": []}
        
        html = self._fetch_html(f"/detail/{vid}/")
        if not html:
            return {"list": []}
        
        return self._parse_recommend(html)

    def destroy(self):
        pass

    # ==================== 辅助方法 ====================

    def _fetch_html(self, path):
        if path.startswith("http"):
            url = path
        else:
            url = self.host + path
        try:
            resp = self.fetch(url, headers=self.headers, timeout=10)
            if resp and getattr(resp, "status_code", 0) == 200:
                return getattr(resp, "text", "") or ""
            return ""
        except Exception as e:
            self.log({"action": "fetch_fail", "url": url, "error": str(e)})
            return ""

    def _parse_video_list(self, html):
        """解析视频列表"""
        items = []
        # 匹配 .video-card 或 a.video-card
        card_pattern = r'<a[^>]*class="[^"]*video-card[^"]*"[^>]*href="(/detail/(\d+)/?)"[^>]*title="([^"]*)"[^>]*>(.*?)</a>'
        cards = re.findall(card_pattern, html, re.DOTALL)
        
        for card in cards:
            href = card[0]
            vid = card[1]
            title = card[2].strip()
            card_html = card[3]
            if not title:
                continue
            
            # 提取封面图 - 在card_html中查找
            pic = ""
            # 优先查找 data-src
            img_match = re.search(r'<img[^>]*data-src="([^"]+)"', card_html, re.DOTALL)
            if img_match:
                pic = img_match.group(1)
            else:
                # 查找 src 但排除 poster_loading
                img_match = re.search(r'<img[^>]*src="([^"]+)"', card_html, re.DOTALL)
                if img_match and "poster_loading" not in img_match.group(1):
                    pic = img_match.group(1)
            
            # 提取分类标签
            category = ""
            cat_match = re.search(r'<span[^>]*class="[^"]*tag[^"]*bg-primary[^"]*"[^>]*>([^<]+)</span>', card_html, re.DOTALL)
            if cat_match:
                category = cat_match.group(1).strip()
            
            # 提取角标/备注
            remark = ""
            remark_match = re.search(r'<span[^>]*class="[^"]*text-white[^"]*"[^>]*>([^<]+)</span>', card_html, re.DOTALL)
            if remark_match:
                remark = remark_match.group(1).strip()
            
            # 提取子标题
            subtitle = ""
            sub_match = re.search(r'<div[^>]*class="[^"]*subtitle[^"]*"[^>]*>([^<]+)</div>', card_html, re.DOTALL)
            if sub_match:
                subtitle = sub_match.group(1).strip()
            
            # 构建 vod_id 打包数据
            vod_id = f"{vid}|$|{title}|$|{pic}|$|{remark}"
            
            items.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark or category or subtitle
            })
        
        return {"list": items}
    def _parse_pagination(self, html):
        result = {"pagecount": 1, "total": 0}
        total_match = re.search(r'data-rec-total="(\d+)"', html)
        if total_match:
            result["total"] = int(total_match.group(1))
        page_match = re.search(r'data-page="(\d+)"', html)
        if page_match:
            result["pagecount"] = max(1, (result["total"] + 19) // 20) if result["total"] > 0 else 1
        return result

    def _parse_detail(self, html, vid, vod_id, name, pic, remark):
        if not name:
            name_match = re.search(r'<h1[^>]*class="[^"]*text-5xl[^"]*"[^>]*>《([^》]*)》</h1>', html)
            if name_match:
                name = name_match.group(1).strip()
            else:
                name_match = re.search(r'<title>([^<]*)</title>', html)
                if name_match:
                    name = name_match.group(1).replace(" - 影视天堂", "").strip()
        
        if not pic:
            pic_match = re.search(r'<img[^>]*data-src="([^"]+)"[^>]*class="[^"]*w-full[^"]*"', html)
            if pic_match:
                pic = pic_match.group(1)
        
        content = ""
        content_match = re.search(r'<div[^>]*class="[^"]*line-clamp-6[^"]*"[^>]*>([^<]*)</div>', html)
        if content_match:
            content = content_match.group(1).strip()
        
        director = ""
        director_match = re.search(r'导演[：:]\s*([^<]+)</div>', html)
        if director_match:
            director = director_match.group(1).strip()
        
        actor = ""
        actor_match = re.search(r'主演[：:]\s*([^<]+)</div>', html)
        if actor_match:
            actor = actor_match.group(1).strip()
        
        episodes = []
        ep_pattern = r'<a[^>]*href="(/play/\d+/(\d+)/?)"[^>]*>第(\d+)集</a>'
        ep_matches = re.findall(ep_pattern, html)
        if ep_matches:
            ep_set = {}
            for ep in ep_matches:
                href = ep[0]
                ep_num = int(ep[1]) if ep[1].isdigit() else int(ep[2])
                ep_set[ep_num] = href
            for ep_num in sorted(ep_set.keys()):
                episodes.append({"num": ep_num, "href": ep_set[ep_num]})
        else:
            ep_pattern2 = r'<a[^>]*href="(/play/\d+/(\d+)/?)"[^>]*>(\d+)</a>'
            ep_matches2 = re.findall(ep_pattern2, html)
            for ep in ep_matches2:
                href = ep[0]
                ep_num = int(ep[1]) if ep[1].isdigit() else int(ep[2])
                if ep_num not in [e["num"] for e in episodes]:
                    episodes.append({"num": ep_num, "href": href})
            episodes.sort(key=lambda x: x["num"])
        
        if episodes:
            play_urls = []
            for ep in episodes:
                play_urls.append(f"第{ep['num']}集${ep['href']}")
            vod_play_url = "#".join(play_urls)
            vod_play_from = "播放"
        else:
            play_btn = re.search(r'<a[^>]*href="(/play/\d+/\d+)"[^>]*>立即播放</a>', html)
            if play_btn:
                vod_play_url = f"播放${play_btn.group(1)}"
                vod_play_from = "播放"
            else:
                vod_play_url = f"播放$/{vid}/1"
                vod_play_from = "播放"
        
        return {
            "list": [{
                "vod_id": vod_id,
                "vod_name": name or "视频",
                "vod_pic": pic,
                "vod_remarks": remark or "",
                "vod_actor": actor,
                "vod_director": director,
                "vod_content": content,
                "vod_play_from": vod_play_from,
                "vod_play_url": vod_play_url
            }]
        }

    def _extract_m3u8_from_play(self, html):
        mse_match = re.search(r'<div[^>]*id="mse"[^>]*data-url="([^"]+)"', html)
        if mse_match:
            return mse_match.group(1).replace("&amp;", "&")
        
        m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if m3u8_match:
            return m3u8_match.group(0)
        
        player_match = re.search(r'(?:url|video|src)\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html, re.IGNORECASE)
        if player_match:
            return player_match.group(1)
        
        return None

    def _parse_recommend(self, html):
        items = []
        rec_pattern = r'<a[^>]*class="[^"]*video-card[^"]*"[^>]*href="(/detail/(\d+)/?)"[^>]*title="([^"]*)"[^>]*>'
        rec_matches = re.findall(rec_pattern, html)
        
        for rec in rec_matches:
            href = rec[0]
            vid = rec[1]
            title = rec[2].strip()
            if not title:
                continue
            pic = ""
            card_start = html.find(href)
            if card_start != -1:
                card_end = html.find("</a>", card_start)
                if card_end != -1:
                    card_html = html[card_start:card_end]
                    img_match = re.search(r'<img[^>]*data-src="([^"]+)"', card_html)
                    if img_match:
                        pic = img_match.group(1)
            items.append({
                "vod_id": f"{vid}|$|{title}|$|{pic}|$|",
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": ""
            })
        
        return {"list": items[:20]}

    def _parse_extend(self, extend):
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

    def _parse_search_results(self, html):
        """解析搜索结果 - 搜索页面结构与首页不同"""
        items = []
        li_pattern = r'<li>\s*<a[^>]*href="(/detail/(\d+)/?)"[^>]*title="([^"]*)"[^>]*>(.*?)</a>\s*</li>'
        matches = re.findall(li_pattern, html, re.DOTALL)
        
        for match in matches:
            href = match[0]
            vid = match[1]
            title = match[2].strip()
            content = match[3]
            
            if not title:
                continue
            
            pic = ""
            img_match = re.search(r'<img[^>]*data-src="([^"]+)"', content)
            if img_match:
                pic = img_match.group(1)
            else:
                img_match = re.search(r'<img[^>]*src="([^"]+)"', content)
                if img_match and "poster_loading" not in img_match.group(1):
                    pic = img_match.group(1)
            
            remark = ""
            info_match = re.search(r'<div[^>]*class="[^"]*my-0\.5[^"]*"[^>]*>\s*<span>([^<]*)</span>\s*<span>([^<]*)</span>\s*<span>([^<]*)</span>', content)
            if info_match:
                category = info_match.group(1).strip()
                year = info_match.group(2).strip()
                area = info_match.group(3).strip()
                remark = f"{category} {year} {area}".strip()
            
            if not remark:
                info_match = re.search(r'<div[^>]*class="[^"]*my-0\.5[^"]*"[^>]*>([^<]+)</div>', content)
                if info_match:
                    remark = info_match.group(1).strip()
            
            vod_id = f"{vid}|$|{title}|$|{pic}|$|{remark}"
            items.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        
        return {"list": items}