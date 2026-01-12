from base.spider import Spider
import re, sys, json, time, hashlib
sys.path.append('..')

class Spider(Spider):
    api_host = 'https://minidrama.contentchina.com'
    origin = 'https://minidrama.contentchina.com'
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        'accept-language': "zh-CN,zh;q=0.9",
        'cache-control': "no-cache",
        'origin': origin,
        'referer': origin + '/',
        'sec-ch-ua': "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': "\"Windows\"",
        'sec-fetch-dest': "empty",
        'sec-fetch-mode': "cors",
        'sec-fetch-site': "same-site"
    }

    def __init__(self):
        super().__init__()
        # 提取初始数据中的配置信息
        self.home_data = None
        self.init_data()

    def init_data(self):
        """初始化，获取网站配置数据"""
        try:
            response = self.fetch(self.origin, headers=self.headers)
            html = response.text
            
            # 查找Nuxt.js初始状态数据
            pattern = r'window\.__NUXT__\s*=\s*(.*?);</script>'
            match = re.search(pattern, html, re.DOTALL)
            
            if match:
                nuxt_data = match.group(1)
                try:
                    self.home_data = json.loads(nuxt_data)
                    print(f"成功获取网站初始数据")
                except json.JSONDecodeError:
                    print(f"解析Nuxt数据失败")
        except Exception as e:
            print(f"初始化失败: {e}")

    def homeContent(self, filter):
        """返回分类列表"""
        try:
            if self.home_data and 'state' in self.home_data:
                state = self.home_data['state']
                
                # 尝试获取分类数据
                categories = []
                if 'allCategory' in state and state['allCategory']:
                    for cat in state['allCategory']:
                        categories.append({
                            'type_id': str(cat.get('id', '')),
                            'type_name': cat.get('name', '')
                        })
                
                # 如果没有分类数据，使用默认分类
                if not categories:
                    categories = [
                        {'type_id': '1', 'type_name': '情感关系'},
                        {'type_id': '2', 'type_name': '成长逆袭'},
                        {'type_id': '3', 'type_name': '奇幻异能'},
                        {'type_id': '4', 'type_name': '战斗热血'},
                        {'type_id': '5', 'type_name': '伦理现实'},
                        {'type_id': '6', 'type_name': '时空穿越'},
                        {'type_id': '7', 'type_name': '权谋身份'}
                    ]
                
                return {'class': categories}
        except Exception as e:
            print(f"获取分类失败: {e}")
        
        # 默认返回分类
        return {'class': [
            {'type_id': '1', 'type_name': '热门推荐'},
            {'type_id': '2', 'type_name': '情感剧场'},
            {'type_id': '3', 'type_name': '逆袭成长'},
            {'type_id': '4', 'type_name': '奇幻玄幻'},
            {'type_id': '5', 'type_name': '都市现实'},
            {'type_id': '6', 'type_name': '古装权谋'}
        ]}

    def homeVideoContent(self):
        """首页推荐视频"""
        try:
            # 获取首页数据
            response = self.fetch(self.origin, headers=self.headers)
            html = response.text
            
            # 查找视频数据
            videos = []
            
            # 方法1: 尝试从JavaScript数据中提取
            pattern = r'hotList\s*:\s*(\[.*?\])'
            match = re.search(pattern, html)
            if match:
                try:
                    hot_list = json.loads(match.group(1))
                    for item in hot_list:
                        videos.append({
                            'vod_id': str(item.get('id', item.get('vod_id', ''))),
                            'vod_name': item.get('name', item.get('title', item.get('vod_name', ''))),
                            'vod_pic': self.fix_url(item.get('cover', item.get('pic', item.get('vod_pic', '')))),
                            'vod_remarks': item.get('total', item.get('vod_total', '0')) + '集',
                            'vod_score': str(item.get('score', item.get('vod_score', '')))
                        })
                except:
                    pass
            
            # 方法2: 如果方法1失败，尝试其他API
            if not videos:
                api_url = f"{self.api_host}/api/v1/video/hot"
                try:
                    resp = self.fetch(api_url, headers=self.headers)
                    data = resp.json()
                    if 'data' in data:
                        for item in data['data']:
                            videos.append({
                                'vod_id': str(item.get('id', '')),
                                'vod_name': item.get('title', ''),
                                'vod_pic': self.fix_url(item.get('cover', '')),
                                'vod_remarks': item.get('total', '0') + '集',
                                'vod_score': str(item.get('score', ''))
                            })
                except:
                    pass
            
            # 方法3: 如果还是失败，从HTML中提取可见内容
            if not videos:
                # 尝试提取可能的视频卡片
                card_pattern = r'<a[^>]*href=["\']/video/(\d+)["\'][^>]*>.*?<img[^>]*src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']+)["\']'
                matches = re.findall(card_pattern, html, re.DOTALL)
                for vid, img, title in matches[:20]:  # 限制数量
                    videos.append({
                        'vod_id': vid,
                        'vod_name': title,
                        'vod_pic': self.fix_url(img),
                        'vod_remarks': '点击查看',
                        'vod_score': ''
                    })
            
            return {'list': videos[:24]}  # 限制24个
            
        except Exception as e:
            print(f"获取首页视频失败: {e}")
            return {'list': []}

    def detailContent(self, ids):
        """视频详情"""
        try:
            video_id = ids[0]
            # 尝试多种API路径
            api_paths = [
                f"/api/v1/video/{video_id}",
                f"/api/video/detail/{video_id}",
                f"/api/detail/{video_id}"
            ]
            
            for api_path in api_paths:
                try:
                    url = f"{self.api_host}{api_path}"
                    response = self.fetch(url, headers=self.headers)
                    data = response.json()
                    
                    if 'data' in data and data['data']:
                        video_data = data['data']
                        
                        # 获取播放列表
                        play_list = self.get_play_list(video_id, video_data)
                        
                        vod = {
                            'vod_id': video_id,
                            'vod_name': video_data.get('title', video_data.get('name', '')),
                            'vod_content': video_data.get('description', video_data.get('intro', '')),
                            'vod_pic': self.fix_url(video_data.get('cover', video_data.get('pic', ''))),
                            'vod_remarks': '集数：' + str(video_data.get('total', video_data.get('vod_total', '0'))),
                            "vod_director": video_data.get('director', ''),
                            "vod_actor": video_data.get('actor', ''),
                            'vod_year': video_data.get('year', ''),
                            'vod_area': video_data.get('area', ''),
                            'vod_play_from': '喜福短剧',
                            'vod_play_url': play_list
                        }
                        return {'list': [vod]}
                except:
                    continue
            
            # 如果API失败，尝试从页面获取
            page_url = f"{self.origin}/video/{video_id}"
            response = self.fetch(page_url, headers=self.headers)
            html = response.text
            
            # 提取标题
            title_match = re.search(r'<title>([^<]+)</title>', html)
            title = title_match.group(1).replace('_免费短剧高清在线观看', '').strip() if title_match else ''
            
            # 提取描述
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html)
            desc = desc_match.group(1) if desc_match else ''
            
            # 提取封面
            img_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
            img = self.fix_url(img_match.group(1)) if img_match else ''
            
            # 获取播放列表
            play_list = self.extract_play_list_from_html(html, video_id)
            
            vod = {
                'vod_id': video_id,
                'vod_name': title,
                'vod_content': desc,
                'vod_pic': img,
                'vod_remarks': '请查看播放列表',
                "vod_director": '',
                "vod_actor": '',
                'vod_year': '',
                'vod_area': '',
                'vod_play_from': '喜福短剧',
                'vod_play_url': play_list
            }
            return {'list': [vod]}
            
        except Exception as e:
            print(f"获取详情失败: {e}")
            return {'list': []}

    def get_play_list(self, video_id, video_data):
        """获取播放列表"""
        play_list = ''
        
        # 尝试多种方式获取播放数据
        play_sources = [
            video_data.get('player', {}),
            video_data.get('play_list', {}),
            video_data.get('episodes', {})
        ]
        
        for source in play_sources:
            if isinstance(source, dict) and source:
                for name, url in source.items():
                    if isinstance(url, str) and url:
                        play_list += f'{name}${url}#'
                break
        
        # 如果没有播放数据，尝试从其他字段获取
        if not play_list and 'play_url' in video_data:
            play_list = f'正片${video_data["play_url"]}#'
        
        # 如果还是没有，尝试API获取播放列表
        if not play_list:
            try:
                api_url = f"{self.api_host}/api/v1/video/{video_id}/playlist"
                response = self.fetch(api_url, headers=self.headers)
                data = response.json()
                if 'data' in data and isinstance(data['data'], dict):
                    for name, url in data['data'].items():
                        play_list += f'{name}${url}#'
            except:
                pass
        
        return play_list.rstrip('#')

    def extract_play_list_from_html(self, html, video_id):
        """从HTML中提取播放列表"""
        play_list = ''
        
        # 查找播放数据
        patterns = [
            r'playList\s*:\s*(\[.*?\])',
            r'episodes\s*:\s*(\[.*?\])',
            r'videoList\s*:\s*(\[.*?\])',
            r'var\s+playData\s*=\s*(\{.*?\});'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data_str = match.group(1)
                    data = json.loads(data_str)
                    
                    if isinstance(data, list):
                        for i, item in enumerate(data, 1):
                            if isinstance(item, dict):
                                url = item.get('url', item.get('play_url', ''))
                                title = item.get('title', f'第{i}集')
                            else:
                                url = str(item)
                                title = f'第{i}集'
                            
                            if url:
                                play_list += f'{title}${url}#'
                    elif isinstance(data, dict):
                        for name, url in data.items():
                            play_list += f'{name}${url}#'
                except:
                    continue
        
        return play_list.rstrip('#')

    def searchContent(self, key, quick, pg="1"):
        """搜索内容"""
        try:
            # 尝试搜索API
            api_urls = [
                f"{self.api_host}/api/v1/search",
                f"{self.api_host}/api/search"
            ]
            
            for api_url in api_urls:
                try:
                    payload = {
                        "keyword": key,
                        "page": int(pg),
                        "limit": 24
                    }
                    
                    headers = self.headers.copy()
                    headers['Content-Type'] = 'application/json'
                    
                    response = self.post(api_url, data=json.dumps(payload), headers=headers)
                    data = response.json()
                    
                    if 'data' in data:
                        result_data = data['data']
                        videos = []
                        
                        if isinstance(result_data, dict) and 'list' in result_data:
                            items = result_data['list']
                        elif isinstance(result_data, list):
                            items = result_data
                        else:
                            continue
                        
                        for item in items:
                            videos.append({
                                "vod_id": str(item.get('id', '')),
                                "vod_name": item.get('title', item.get('name', '')),
                                "vod_pic": self.fix_url(item.get('cover', item.get('pic', ''))),
                                'vod_year': item.get('year', ''),
                                "vod_remarks": str(item.get('total', '0')) + '集'
                            })
                        
                        return {
                            'list': videos,
                            'page': pg,
                            'total': result_data.get('total', len(videos)) if isinstance(result_data, dict) else len(videos),
                            'limit': 24
                        }
                except:
                    continue
            
            # 如果API搜索失败，返回空结果
            return {'list': [], 'page': pg, 'total': 0, 'limit': 24}
            
        except Exception as e:
            print(f"搜索失败: {e}")
            return {'list': [], 'page': pg, 'total': 0, 'limit': 24}

    def categoryContent(self, tid, pg, filter, extend):
        """分类内容"""
        try:
            # 构建API请求
            api_url = f"{self.api_host}/api/v1/video/list"
            
            payload = {
                "category_id": tid,
                "page": int(pg),
                "limit": 24
            }
            
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/json'
            
            response = self.post(api_url, data=json.dumps(payload), headers=headers)
            data = response.json()
            
            if 'data' in data:
                videos = []
                items = data['data'].get('list', []) if isinstance(data['data'], dict) else data['data']
                
                for item in items:
                    videos.append({
                        'vod_id': str(item.get('id', '')),
                        'vod_name': item.get('title', item.get('name', '')),
                        'vod_pic': self.fix_url(item.get('cover', item.get('pic', ''))),
                        'vod_remarks': str(item.get('total', '0')) + '集',
                        'vod_year': item.get('year', ''),
                        'vod_score': str(item.get('score', ''))
                    })
                
                return {'list': videos}
            
        except Exception as e:
            print(f"获取分类内容失败: {e}")
        
        return {'list': []}

    def playerContent(self, flag, id, vipflags):
        """播放地址解析"""
        parse = 0
        header = self.headers.copy()
        url = id
        
        try:
            # 如果已经是视频链接，直接返回
            if self.isVideoFormat(id):
                return {'parse': parse, 'url': url, 'header': header}
            
            # 尝试从页面提取视频
            response = self.fetch(id, headers=header)
            html = response.text
            
            # 查找视频源
            patterns = [
                r'src="(https?://[^"]+\.(?:mp4|m3u8|flv|avi|mkv|mov|wmv|webm)[^"]*)"',
                r"src='(https?://[^']+\.(?:mp4|m3u8|flv|avi|mkv|mov|wmv|webm)[^']*)'",
                r'video-src="([^"]+)"',
                r"video-src='([^']+)'",
                r'url\s*:\s*["\'](https?://[^"\']+)["\']',
                r'let\s+url\s*=\s*["\'](https?://[^"\']+)["\']'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    found_url = match.group(1)
                    if self.isVideoFormat(found_url):
                        url = found_url
                        break
            
            # 如果不是视频格式，需要解析
            if not self.isVideoFormat(url):
                parse = 1
            
        except Exception as e:
            print(f"解析播放地址失败: {e}")
            parse = 1
        
        return {'parse': parse, 'url': url, 'header': header}

    def fix_url(self, url):
        """修复URL"""
        if not url:
            return ''
        
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return self.origin + url
        elif not url.startswith(('http://', 'https://')):
            return self.origin + '/' + url
        
        return url

    def isVideoFormat(self, url):
        """检查是否为视频格式"""
        if not url:
            return False
        
        video_extensions = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.mov', '.wmv', '.webm']
        url_lower = url.lower()
        
        # 检查扩展名
        if any(url_lower.endswith(ext) for ext in video_extensions):
            return True
        
        # 检查是否包含视频关键字
        video_keywords = ['video/', 'play/', 'stream/', 'm3u8', 'mp4']
        if any(keyword in url_lower for keyword in video_keywords):
            return True
        
        return False

    def init(self, extend=''):
        """初始化"""
        pass

    def getName(self):
        """返回爬虫名称"""
        return "喜福短剧"

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    def localProxy(self, param):
        pass