# -*- coding: utf-8 -*-
import re
import sys
import json
import time
import urllib.parse
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    def init(self, extend=""):
        pass

    def getName(self):
        return "2DZ影视"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    # ------------------------- 网站配置 -------------------------
    host = 'https://www.2dz.top'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
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
        elif url.startswith('./'):
            return f"{self.host}{url[1:]}"
        return url

    def _extract_video_basic(self, item):
        """从视频卡片提取基本信息"""
        try:
            card = item
            link = card.attr('onclick') or ''
            vod_id = ''
            
            # 提取vod_id from onclick属性
            if link:
                id_match = re.search(r"player\.php\?id=([^']+)", link)
                if id_match:
                    vod_id = id_match.group(1)
            
            # 如果没有找到onclick，尝试从href获取
            if not vod_id:
                href = card('a').attr('href')
                if href:
                    id_match = re.search(r"id=([^&]+)", href)
                    if id_match:
                        vod_id = id_match.group(1)
            
            if not vod_id:
                return None

            # 提取图片
            img = card('img').attr('src') or ''
            img = self._normalize_url(img)
            
            # 提取标题
            title = card('.video-title').text().strip() or card('img').attr('alt') or '未知标题'
            
            return {
                'vod_id': vod_id,
                'vod_name': title,
                'vod_pic': img,
                'vod_remarks': '',
                'vod_year': ''
            }
        except Exception as e:
            return None

    def getpq(self, text):
        """创建PyQuery对象"""
        try:
            return pq(text)
        except:
            try:
                return pq(text.encode('utf-8'))
            except:
                return pq('')

    # ------------------------- API接口方法 -------------------------
    def _fetch_api(self, url):
        """通用API请求方法"""
        try:
            response = self.fetch(url, headers=self.headers)
            if response and response.text:
                return json.loads(response.text)
        except:
            pass
        return None

    def _get_type_name(self, type_id):
        """获取分类名称"""
        try:
            url = f"{self.host}/api/get_type_name.php?id={type_id}"
            response = self.fetch(url, headers=self.headers)
            if response and response.text:
                return response.text.strip()
        except:
            pass
        return "分类视频"

    def _get_types(self):
        """获取所有分类 - 修复版"""
        types = []
        try:
            # 直接从API获取分类
            api_url = f"{self.host}/api/get_type_name.php?t={int(time.time()*1000)}"
            response = self.fetch(api_url, headers=self.headers)
            if response and response.text:
                text = response.text.strip()
                # 按行分割
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            tid = parts[0].strip()
                            name = parts[1].strip()
                            # 排除空值和首页
                            if tid and name and tid != '0':
                                types.append({
                                    'type_id': tid,
                                    'type_name': name
                                })
            
            # 调试输出
            print(f"获取到分类: {types}")
            
        except Exception as e:
            print(f"获取分类出错: {e}")
        
        # 如果API获取失败，返回默认分类
        if not types:
            types = [
                {'type_id': '1', 'type_name': '电影'},
                {'type_id': '2', 'type_name': '电视剧'},
                {'type_id': '3', 'type_name': '综艺'},
                {'type_id': '4', 'type_name': '动漫'},
                {'type_id': '5', 'type_name': '短剧'}
            ]
        
        return types

    def _get_timestamp(self):
        """获取时间戳"""
        return int(time.time() * 1000)

    # ------------------------- 主要功能方法 -------------------------
    def homeContent(self, filter):
        """首页：分类 + 推荐列表"""
        try:
            # 获取分类
            classes = self._get_types()

            # 获取首页推荐（最新视频）
            list_data = self._get_list_from_api(type_id=0, page=1)
            
            result = {
                'class': classes,
                'list': list_data
            }
            
            # 调试输出
            print(f"首页返回: class数量={len(classes)}, 视频数量={len(list_data)}")
            
            return result
        except Exception as e:
            print(f"首页出错: {e}")
            return {'class': [], 'list': []}

    def _get_list_from_api(self, type_id=0, page=1, keyword=''):
        """从API获取视频列表"""
        videos = []
        try:
            if keyword:
                # 搜索API
                url = f"{self.host}/api/search.php?keyword={keyword}&page={page}"
            else:
                # 列表API
                url = f"{self.host}/api/list.php?type_id={type_id}&page={page}"
            
            data = self._fetch_api(url)
            if data and 'data' in data:
                for item in data['data']:
                    video = {
                        'vod_id': str(item.get('vod_id', '')),
                        'vod_name': item.get('vod_name', '未知标题'),
                        'vod_pic': self._normalize_url(item.get('vod_pic', '')),
                        'vod_remarks': '',
                        'vod_year': ''
                    }
                    videos.append(video)
        except Exception as e:
            pass
        return videos

    def categoryContent(self, tid, pg, filter, extend):
        """分类页内容"""
        try:
            videos = self._get_list_from_api(type_id=tid, page=int(pg))
            
            # 获取总数（从API响应中提取）
            total = 999999
            try:
                url = f"{self.host}/api/list.php?type_id={tid}&page={pg}"
                data = self._fetch_api(url)
                if data:
                    if 'total' in data:
                        total = data['total']
                    elif 'count' in data:
                        total = data['count']
            except:
                pass

            # 计算总页数
            pagecount = (total + 29) // 30 if total < 999999 else 9999

            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 30,
                'total': total
            }
        except Exception as e:
            return {'list': [], 'page': int(pg), 'pagecount': 1, 'limit': 30, 'total': 0}

    def detailContent(self, ids):
        """详情页：提取视频详情和播放地址"""
        try:
            # 处理传入的ID
            vod_id = ids
            if isinstance(ids, dict) and 'ids' in ids:
                vod_id = ids['ids']
            elif hasattr(ids, '__iter__') and not isinstance(ids, str):
                vod_id = next(iter(ids))
            
            # 通过API获取视频详情
            api_url = f"{self.host}/api/random.php?vod_id={vod_id}"
            response = self.fetch(api_url, headers=self.headers)
            
            if not response or not response.text:
                return {'list': []}
            
            # 解析API返回的JSON数据
            vod_info = json.loads(response.text)
            
            if vod_info.get('error'):
                return {'list': []}
            
            # 提取基本信息
            vod_name = vod_info.get('vod_name', f'视频_{vod_id}')
            vod_pic = self._normalize_url(vod_info.get('vod_pic', ''))
            type_id = vod_info.get('type_id', 0)
            
            # 获取分类名称
            type_name = self._get_type_name(type_id)
            
            # 构建播放列表
            play_from = []
            play_urls = []
            
            # 处理多线路
            all_lines = vod_info.get('all_lines', [])
            if all_lines and len(all_lines) > 0:
                for line in all_lines:
                    line_name = line.get('line_name', '默认线路')
                    play_from.append(line_name)
                    
                    episodes = line.get('episodes', [])
                    episode_parts = []
                    for ep in episodes:
                        ep_title = ep.get('title', '第1集')
                        ep_url = ep.get('url', '')
                        if ep_url:
                            episode_parts.append(f"{ep_title}${ep_url}")
                    
                    if episode_parts:
                        play_urls.append('#'.join(episode_parts))
            
            # 如果没有线路信息，尝试直接使用play_url
            if not play_urls and vod_info.get('play_url'):
                play_from.append('默认播放源')
                play_urls.append(f"播放${vod_info['play_url']}")
            
            # 构建视频详情对象
            vod = {
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_content': f'类型：{type_name}',
                'vod_year': str(vod_info.get('vod_year', '')),
                'vod_area': str(vod_info.get('vod_area', '')),
                'vod_remarks': '',
                'vod_actor': '',
                'vod_director': ''
            }
            
            if play_urls:
                vod['vod_play_from'] = '$$$'.join(play_from)
                vod['vod_play_url'] = '$$$'.join(play_urls)
            else:
                # 如果没有播放地址，使用播放器页面
                player_url = f"{self.host}/player.php?id={vod_id}"
                vod['vod_play_from'] = '默认播放源'
                vod['vod_play_url'] = f"播放${player_url}"
            
            return {'list': [vod]}
            
        except Exception as e:
            # 出错时返回基本数据
            player_url = f"{self.host}/player.php?id={vod_id if 'vod_id' in locals() else ids}"
            vod = {
                'vod_id': vod_id if 'vod_id' in locals() else ids,
                'vod_name': '视频详情',
                'vod_pic': '',
                'vod_content': '',
                'vod_year': '',
                'vod_area': '',
                'vod_remarks': '',
                'vod_actor': '',
                'vod_director': '',
                'vod_play_from': '默认播放源',
                'vod_play_url': f"播放${player_url}"
            }
            return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        """搜索功能"""
        try:
            # URL编码关键词
            encoded_key = urllib.parse.quote(key)
            
            # 调用搜索API
            videos = self._get_list_from_api(keyword=encoded_key, page=int(pg))
            
            return {
                'list': videos,
                'page': int(pg)
            }
        except Exception as e:
            return {'list': [], 'page': int(pg)}

    def playerContent(self, flag, id, vipFlags):
        """解析播放地址"""
        try:
            # 判断是否是m3u8地址
            if '.m3u8' in id:
                return {
                    'parse': 0,
                    'url': id,
                    'header': self.headers
                }
            
            # 如果是页面地址，尝试提取真实播放地址
            response = self.fetch(id, headers=self.headers)
            if response and response.text:
                html_text = response.text
                
                # 查找m3u8地址
                m3u8_urls = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html_text)
                if m3u8_urls:
                    return {
                        'parse': 0,
                        'url': m3u8_urls[0],
                        'header': self.headers
                    }
                
                # 查找video标签
                data = self.getpq(html_text)
                video = data('video')
                if video:
                    src = video.attr('src')
                    if src:
                        return {
                            'parse': 0,
                            'url': self._normalize_url(src),
                            'header': self.headers
                        }
            
            # 如果都找不到，使用解析接口
            return {
                'parse': 1,
                'url': id,
                'header': self.headers
            }
            
        except Exception as e:
            return {
                'parse': 1,
                'url': id,
                'header': self.headers
            }

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        pass

    # ------------------------- 辅助方法 -------------------------
    def _extract_from_html(self, html):
        """从HTML页面提取视频列表（备用方法）"""
        videos = []
        try:
            data = self.getpq(html)
            cards = data('.video-card')
            for card in cards.items():
                video_info = self._extract_video_basic(card)
                if video_info:
                    videos.append(video_info)
        except:
            pass
        return videos