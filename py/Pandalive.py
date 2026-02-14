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
        return "M3U8在线播放器"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    # ------------------------- 网站配置 -------------------------
    host = 'https://5721004.xyz'  # 根据实际域名调整
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://5721004.xyz/'
    }

    # 代理服务器列表（从原网站JS中提取）
    proxy_servers = [
        "https://pol.515355.xyz/proxy/",
        "https://f00.515355.xyz/proxy/",
        "https://flank.515355.xyz/proxy/",
        "https://ce2.515355.xyz/proxy/?",
        "https://uae2.515355.xyz/proxy/",
        "https://hubu.515355.xyz/proxy/?"
    ]

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

    def _extract_stream_info(self, item):
        """从列表项提取直播流信息"""
        try:
            # 从mdui-list-item中提取信息
            name = item('.mdui-list-item-content').text().strip()
            # 获取点击事件中的URL信息（需要从HTML属性中提取）
            onclick_attr = item.attr('onclick')
            url = None
            if onclick_attr and 'changelive' in onclick_attr:
                # 提取changelive函数中的URL参数
                url_match = re.search(r"changelive\(['\"]([^'\"]+)['\"]", onclick_attr)
                if url_match:
                    url = url_match.group(1)
            
            if not url:
                return None
                
            return {
                'vod_id': url,
                'vod_name': name,
                'vod_pic': 'https://tupian.li/images/2024/03/30/660769b1ba623.png',  # 默认图标
                'vod_remarks': '直播',
                'vod_year': '',
                'vod_area': 'Pandalive',
                'type_name': '直播'
            }
        except:
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

    def _fetch_m3u_list(self):
        """获取list.m3u文件内容"""
        try:
            m3u_url = f"{self.host}/player/list.m3u"
            response = self.fetch(m3u_url, headers=self.headers)
            return response.text
        except:
            return ""

    def _parse_m3u_content(self, m3u_text):
        """解析M3U格式的直播列表"""
        streams = []
        lines = m3u_text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXTINF:'):
                # 解析EXTINF行，格式：#EXTINF:0,名字,额外信息
                parts = line.split(',', 2)
                if len(parts) >= 3:
                    name = parts[1].strip()
                    name_info = parts[2].strip()
                else:
                    name = parts[1].strip() if len(parts) > 1 else "未知"
                    name_info = name
                
                # 下一行应该是URL
                if i + 1 < len(lines):
                    url_line = lines[i + 1].strip()
                    if url_line.startswith('http'):
                        streams.append({
                            'vod_id': url_line,
                            'vod_name': name_info,
                            'vod_pic': 'https://tupian.li/images/2024/03/30/660769b1ba623.png',
                            'vod_remarks': '直播',
                            'vod_year': '',
                            'vod_area': 'Pandalive',
                            'type_name': '直播',
                            'vod_actor': name
                        })
                    i += 1
            elif line.startswith('#列表说明'):
                # 提取更新说明
                parts = line.split(',', 1)
                if len(parts) > 1:
                    update_info = parts[1].strip()
                    # 可以保存更新时间信息
            i += 1
        return streams

    # ------------------------- 主要功能方法 -------------------------
    def homeContent(self, filter):
        """首页：分类 + 推荐列表"""
        try:
            # 由于这是一个单一功能的播放器页面，我们返回固定分类
            classes = [
                {'type_name': '直播', 'type_id': 'live'}
            ]
            
            # 获取直播列表
            m3u_content = self._fetch_m3u_list()
            if m3u_content:
                videos = self._parse_m3u_content(m3u_content)
            else:
                videos = []
            
            return {'class': classes, 'list': videos[:20]}  # 首页只显示20个
        except Exception as e:
            return {'class': [], 'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        """分类页内容"""
        try:
            videos = []
            
            if tid == 'live':
                # 获取直播列表
                m3u_content = self._fetch_m3u_list()
                if m3u_content:
                    videos = self._parse_m3u_content(m3u_content)
            elif tid == 'sports':
                # 体育频道 - 可以从sports.html页面提取
                sports_url = f"{self.host}/player/sports.html"
                # 这里可以添加解析体育频道的逻辑
                pass
            elif tid == 'short':
                # 随机短视频
                short_url = f"{self.host}/player/short.html"
                # 这里可以添加解析短视频的逻辑
                pass
            
            # 分页处理
            page_size = 30
            start = (int(pg) - 1) * page_size
            end = start + page_size
            page_videos = videos[start:end] if start < len(videos) else []
            
            return {
                'list': page_videos,
                'page': int(pg),
                'pagecount': (len(videos) + page_size - 1) // page_size,
                'limit': page_size,
                'total': len(videos)
            }
        except Exception as e:
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}

    def detailContent(self, ids):
        """详情页：直播流详情"""
        try:
            first_id = next(iter(ids)) if hasattr(ids, '__iter__') and not isinstance(ids, str) else ids
            
            # 从URL中提取流信息
            vod = {
                'vod_id': first_id,
                'vod_name': '直播流',
                'vod_pic': 'https://tupian.li/images/2024/03/30/660769b1ba623.png',
                'vod_content': 'M3U8直播流，可使用代理播放',
                'vod_year': '',
                'vod_area': 'Pandalive',
                'vod_remarks': '直播',
                'vod_actor': '',
                'vod_director': ''
            }
            
            # 添加播放链接，使用不同的代理
            play_links = []
            
            # 原始链接
            #play_links.append(f"直连${first_id}")
            
            # 添加代理链接
            for i, proxy in enumerate(self.proxy_servers, 1):
                proxy_url = proxy + first_id
                play_links.append(f"代理{i}${proxy_url}")
            
            vod['vod_play_from'] = '默认播放源'
            vod['vod_play_url'] = '#'.join(play_links)

            return {'list': [vod]}
        except Exception as e:
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        """搜索功能"""
        try:
            # 从直播列表中搜索
            m3u_content = self._fetch_m3u_list()
            if not m3u_content:
                return {'list': [], 'page': int(pg)}
            
            all_streams = self._parse_m3u_content(m3u_content)
            
            # 过滤搜索结果
            results = []
            key_lower = key.lower()
            for stream in all_streams:
                name = stream.get('vod_name', '').lower()
                actor = stream.get('vod_actor', '').lower()
                if key_lower in name or key_lower in actor:
                    results.append(stream)
            
            # 搜索结果排序
            results = self._filter_search_results(results, key)
            
            return {'list': results, 'page': int(pg)}
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
            actor = result.get('vod_actor', '').lower()
            if key_lower in title or key_lower in actor:
                # 计算匹配度：标题匹配优先于演员匹配
                title_match = key_lower in title
                score = (title_match, -title.find(key_lower) if title_match else -actor.find(key_lower))
                scored.append((score, result))
        scored.sort(reverse=True)
        return [r for _, r in scored]

    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        try:
            # 对于直播流，直接返回解析结果
            # 判断是否为代理URL
            is_proxy = any(proxy in id for proxy in self.proxy_servers)
            
            return {
                'parse': 0,  # 0表示直接播放
                'url': id,
                'header': {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': self.host
                }
            }
        except Exception as e:
            return {'parse': 1, 'url': id, 'header': self.headers}

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        """处理直播内容"""
        try:
            if url == 'live':
                m3u_content = self._fetch_m3u_list()
                if m3u_content:
                    streams = self._parse_m3u_content(m3u_content)
                    # 转换为TVBox直播格式
                    groups = {}
                    for stream in streams:
                        group = stream.get('vod_area', '直播')
                        if group not in groups:
                            groups[group] = []
                        name = stream.get('vod_name', '未知')
                        url = stream.get('vod_id', '')
                        groups[group].append(f"{name},{url}")
                    
                    result = []
                    for group_name, channels in groups.items():
                        result.append(f"{group_name}," + "#".join(channels))
                    
                    return "\n".join(result)
            return ""
        except:
            return ""

    # ------------------------- 扩展功能 -------------------------
    def get_random_proxy(self):
        """随机获取一个代理服务器"""
        import random
        return random.choice(self.proxy_servers)

    def filter_live_only(self, video_list):
        """过滤仅保留直播"""
        return [v for v in video_list if 'live' in v.get('vod_id', '') or v.get('type_name') == '直播']