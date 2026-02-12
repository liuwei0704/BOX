# -*- coding: utf-8 -*-
import re
import sys
import json
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    
    def init(self, extend=""):
        pass
    
    def getName(self):
        return "枝枝影视"
    
    def isVideoFormat(self, url):
        pass
    
    def manualVideoCheck(self):
        pass
    
    def destroy(self):
        pass
    
    # ------------------------- 网站配置 -------------------------
    host = 'https://www.zzoc.cc'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://www.zzoc.cc/'
    }
    
    # 分类映射 - 枝枝影视完整分类
    type_map = {
        '电影': '/vodtype/1.html',
        '电视剧': '/vodtype/2.html',
        '综艺': '/vodtype/3.html',
        '动漫': '/vodtype/4.html',
        '短剧': '/vodtype/20.html',
        '动作片': '/vodtype/6.html',
        '喜剧片': '/vodtype/7.html',
        '爱情片': '/vodtype/8.html',
        '科幻片': '/vodtype/9.html',
        '恐怖片': '/vodtype/10.html',
        '剧情片': '/vodtype/11.html',
        '战争片': '/vodtype/12.html',
        '动漫电影': '/vodtype/21.html',
        '纪录片': '/vodtype/31.html'
    }
    
    # ------------------------- 通用工具方法 -------------------------
    def _normalize_url(self, url):
        """标准化URL：处理相对路径、协议缺失等"""
        if not url:
            return url
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{self.host}{url}"
        return url
    
    def _extract_video_basic(self, item):
        """从列表项提取视频基本信息 - 只取第一个.title"""
        try:
            # 详情页链接
            link_elem = item('a')
            if not link_elem:
                return None
            link = self._normalize_url(link_elem.attr('href'))
            if not link or 'javascript' in link:
                return None
            
            # 标题 - 只取第一个.title
            title = ''
            title_elem = item('.title').eq(0)
            if title_elem:
                title = title_elem.text().strip()
            if not title:
                title = item('img').attr('alt') or ''
            if not title:
                title = item('a').text().strip()
            if not title:
                title = '未知片名'
            
            # 图片
            img = ''
            img_elem = item('img')
            if img_elem:
                img = img_elem.attr('src') or img_elem.attr('data-src') or ''
            img = self._normalize_url(img)
            
            # 备注
            remarks = ''
            tag_elem = item('.tag.text-overflow')
            if not tag_elem:
                tag_elem = item('.tag-box .tag')
            if tag_elem:
                remarks = tag_elem.text().strip()
            if not remarks:
                remarks = item('.hits').text().strip() or ''
            
            # 年份 - 从.info-bottom .right提取
            year = ''
            year_elem = item('.info-bottom .right')
            if year_elem:
                year = year_elem.text().strip()
            
            # 主演
            actor = ''
            actor_elem = item('.role')
            if actor_elem:
                actor = actor_elem.text().replace('主演：', '').strip()
            
            return {
                'vod_id': link,
                'vod_name': title,
                'vod_pic': img,
                'vod_remarks': remarks,
                'vod_year': year,
                'vod_actor': actor
            }
        except Exception as e:
            return None
    
    def getpq(self, text):
        """创建PyQuery对象，处理编码问题"""
        try:
            return pq(text)
        except:
            try:
                return pq(text.encode('utf-8'))
            except:
                return pq('')
    
    # ------------------------- 主要功能方法 -------------------------
    def homeContent(self, filter):
        """首页：分类 + 推荐列表"""
        try:
            html = self.fetch(self.host, headers=self.headers).text
            data = self.getpq(html)
            classes = []
            
            # 提取分类导航
            nav_items = data('.menu a')
            for item in nav_items.items():
                link = item.attr('href')
                name = item('.nav span').text().strip()
                if not name:
                    name = item.text().strip()
                
                if link and name and name in self.type_map:
                    type_url = self._normalize_url(link)
                    classes.append({
                        'type_name': name,
                        'type_id': type_url
                    })
            
            if not classes:
                for name, url in self.type_map.items():
                    classes.append({
                        'type_name': name,
                        'type_id': self._normalize_url(url)
                    })
            
            return {
                'class': classes,
                'list': self._get_home_list(data)
            }
        except Exception as e:
            return {'class': [], 'list': []}
    
    def _get_home_list(self, data):
        """首页推荐列表 - 只取正在热播区域"""
        videos = []
        items = data('#SliderList_0 .myui-vodbox-content')
        for item in items.items():
            video_info = self._extract_video_basic(item)
            if video_info:
                videos.append(video_info)
        return videos[:12]
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类页内容"""
        try:
            # 分页URL
            match = re.search(r'/vod(?:type|show)/(\d+)', tid)
            if match:
                type_id = match.group(1)
                url = f"{self.host}/vodshow/{type_id}--------{pg}---.html"
            else:
                url = tid if pg == '1' else tid.replace('.html', '') + f"--------{pg}---.html"
            
            html = self.fetch(url, headers=self.headers).text
            data = self.getpq(html)
            
            videos = []
            # 分类页影片容器
            items = data('.movie-ul .myui-vodbox-content, .vod-list-box .myui-vodbox-content, .show-vod-list .myui-vodbox-content')
            
            for item in items.items():
                if item.parents('[id^="SliderList_"]'):
                    continue
                video_info = self._extract_video_basic(item)
                if video_info:
                    videos.append(video_info)
            
            # 去重
            unique_videos = []
            seen_ids = set()
            for v in videos:
                if v['vod_id'] not in seen_ids:
                    seen_ids.add(v['vod_id'])
                    unique_videos.append(v)
            
            # 获取总页数
            pagecount = 10
            pagination = data('.pagination .pages-box a.page')
            max_page = 1
            for page_link in pagination.items():
                page_text = page_link.text().strip()
                if page_text.isdigit():
                    page_num = int(page_text)
                    if page_num > max_page:
                        max_page = page_num
            
            if max_page > 1:
                pagecount = max_page
            
            return {
                'list': unique_videos,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 30,
                'total': 999999
            }
        except Exception as e:
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}
    
    def _get_video_list(self, data):
        """提取搜索页视频"""
        videos = []
        items = data('.show-vod-list .movie-ul .myui-vodbox-content')
        for item in items.items():
            video_info = self._extract_video_basic(item)
            if video_info:
                videos.append(video_info)
        return videos
    
    def detailContent(self, ids):
        """详情页：提取视频详情 + 完整播放列表 + ✅ 修復年份（只取第一個四位數字）"""
        try:
            first_id = next(iter(ids)) if hasattr(ids, '__iter__') and not isinstance(ids, str) else ids
            html = self.fetch(first_id, headers=self.headers).text
            data = self.getpq(html)
            
            # ---------- 1. 影片基本信息 ----------
            # 标题
            title = data('h1').text().strip()
            if not title:
                title = data('.title').text().strip()
            if not title:
                title = data('meta[property="og:title"]').attr('content') or '未知片名'
            
            # 图片
            pic = ''
            poster = data('.poster img, .myui-vodlist__thumb img, .card-img img, .vod-pic img')
            if poster:
                pic = poster.attr('src') or poster.attr('data-src') or ''
            if not pic:
                pic = data('meta[property="og:image"]').attr('content') or ''
            pic = self._normalize_url(pic)
            
            # 简介
            content = ''
            intro = data('.info-intro, .content, .summary, .vod-content')
            if intro:
                content = intro.text().strip()
            if not content:
                content = data('meta[property="og:description"]').attr('content') or ''
            
            # 主演
            actor = ''
            roles = data('.info-roles')
            if roles:
                actor = roles.text().replace('主演：', '').strip()
            if not actor:
                actor = data('meta[property="og:video:actor"]').attr('content') or ''
            
            # 导演
            director = ''
            director_elem = data('.info-director')
            if director_elem:
                director = director_elem.text().replace('导演：', '').strip()
            
            # ✅ 修復年份提取 - 只取.info-bottom .right的第一個四位數字
            year = ''
            year_elem = data('.info-bottom .right')
            if year_elem:
                year_text = year_elem.text().strip()
                # 只取第一個符合四位數字的年份
                year_match = re.search(r'(\d{4})', year_text)
                if year_match:
                    year = year_match.group(1)
            
            # 地区
            area = ''
            area_elem = data('.info-area')
            if area_elem:
                area = area_elem.text().strip()
            
            # 备注（集数/状态）
            remarks = ''
            remarks_elem = data('.tag-box .tag, .tag.text-overflow')
            if remarks_elem:
                remarks = remarks_elem.text().strip()
            
            # ---------- 2. 播放列表 ----------
            play_from_list = []
            play_url_list = []
            
            # 详情页的播放列表结构
            player_tabs = data('.player-box .nav-btn li, .player-box .swiper-slide.player_name')
            
            for tab in player_tabs.items():
                tab_link = tab('a')
                tab_href = tab_link.attr('href')
                if not tab_href:
                    continue
                
                from_name = tab_link.text().strip()
                if not from_name:
                    from_name = f"線路{len(play_from_list)+1}"
                
                playlist_id = tab_href.replace('#', '')
                
                episode_links = []
                playlist_div = data(f'#{playlist_id}')
                if playlist_div:
                    episode_items = playlist_div('.listitem a')
                    for episode in episode_items.items():
                        episode_url = self._normalize_url(episode.attr('href'))
                        episode_name = episode.text().strip()
                        if episode_url and episode_name:
                            episode_links.append(f"{episode_name}${episode_url}")
                
                if episode_links:
                    play_from_list.append(from_name)
                    play_url_list.append('#'.join(episode_links))
            
            # ---------- 3. 组装返回数据 ----------
            vod = {
                'vod_id': first_id,
                'vod_name': title,
                'vod_pic': pic,
                'vod_content': content,
                'vod_year': year,
                'vod_area': area,
                'vod_remarks': remarks,
                'vod_actor': actor,
                'vod_director': director
            }
            
            if play_from_list and play_url_list:
                vod['vod_play_from'] = '$$$'.join(play_from_list)
                vod['vod_play_url'] = '$$$'.join(play_url_list)
            else:
                vod['vod_play_from'] = '枝枝资源'
                vod['vod_play_url'] = f"播放${first_id}"
            
            return {'list': [vod]}
            
        except Exception as e:
            return {'list': []}
    
    def searchContent(self, key, quick, pg="1"):
        """搜索功能"""
        try:
            search_url = f"{self.host}/vodsearch/-------------.html?wd={key}"
            if pg != "1":
                search_url += f"&page={pg}"
            
            html = self.fetch(search_url, headers=self.headers).text
            data = self.getpq(html)
            results = self._get_video_list(data)
            
            filtered = self._filter_search_results(results, key)
            return {'list': filtered, 'page': int(pg)}
        except Exception as e:
            return {'list': [], 'page': int(pg)}
    
    def _filter_search_results(self, results, key):
        """过滤和排序搜索结果"""
        if not results or not key:
            return results
        key_lower = key.lower()
        scored = []
        for result in results:
            title = result.get('vod_name', '').lower()
            if key_lower in title:
                scored.append((title.startswith(key_lower), -title.find(key_lower), result))
        scored.sort(reverse=True)
        return [r for _, _, r in scored]
    
    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        try:
            html = self.fetch(id, headers=self.headers).text
            data = self.getpq(html)
            
            # 尝试找播放器iframe
            iframe = data('iframe.video, .player iframe, iframe[src*="play"], iframe[src*="m3u8"], iframe[src*="blob"]').attr('src')
            if iframe:
                return {'parse': 1, 'url': self._normalize_url(iframe), 'header': self.headers}
            
            # 尝试找video直链
            video_src = data('video source').attr('src') or data('video').attr('src')
            if video_src:
                return {'parse': 0, 'url': self._normalize_url(video_src), 'header': self.headers}
            
            # 回退：走通用解析
            return {'parse': 1, 'url': id, 'header': self.headers}
        except Exception as e:
            return {'parse': 1, 'url': id, 'header': self.headers}
    
    def localProxy(self, param):
        pass
    
    def liveContent(self, url):
        pass
    
    # ------------------------- 擴展功能 - 全部空方法 -------------------------
    def filterByType(self, video_list, type_id):
        return video_list
    
    def filterByYear(self, video_list, year):
        return video_list
    
    def filterByArea(self, video_list, area):
        return video_list
    
    def filterByLang(self, video_list, lang):
        return video_list
    
    def sortByHits(self, video_list, reverse=True):
        return video_list
    
    def sortByScore(self, video_list, reverse=True):
        return video_list
    
    def sortByTime(self, video_list, reverse=True):
        return video_list
    
    def getFilterOptions(self, tid):
        return {}