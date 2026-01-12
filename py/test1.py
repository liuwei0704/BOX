from base.spider import Spider
import re, sys, json
sys.path.append('..')

class Spider(Spider):
    api_host = 'https://minidrama.contentchina.com'
    origin = 'https://minidrama.contentchina.com'
    api_path = '/api/search'
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        'Content-Type': "application/json",
        'accept-language': "zh-CN,zh;q=0.9",
        'cache-control': "no-cache",
        'origin': origin,
        'pragma': "no-cache",
        'priority': "u=1, i",
        'referer': origin+'/',
        'sec-ch-ua': "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': "\"Windows\"",
        'sec-fetch-dest': "empty",
        'sec-fetch-mode': "cors",
        'sec-fetch-site': "same-site"
    }

    def homeContent(self, filter):
        # 这里需要根据实际网站的分类进行调整
        return {'class': [
            {'type_id': 1, 'type_name': '情感关系'},
            {'type_id': 2, 'type_name': '成长逆袭'},
            {'type_id': 3, 'type_name': '奇幻异能'},
            {'type_id': 4, 'type_name': '战斗热血'},
            {'type_id': 5, 'type_name': '伦理现实'},
            {'type_id': 6, 'type_name': '时空穿越'},
            {'type_id': 7, 'type_name': '权谋身份'}
        ]}

    def homeVideoContent(self):
        payload = {
            "page": 1,
            "limit": 24,
            "type_id": "",
            "year": "",
            "keyword": ""
        }
        try:
            response = self.post(f"{self.api_host}{self.api_path}", data=json.dumps(payload), headers=self.headers).json()
            data = response.get('data', {})
            videos = []
            for i in data.get('list', []):
                videos.append({
                    'vod_id': i.get('vod_id', ''),
                    'vod_name': i.get('vod_name', ''),
                    'vod_class': i.get('vod_class', ''),
                    'vod_pic': i.get('vod_pic', ''),
                    'vod_year': i.get('vod_year', ''),
                    'vod_remarks': i.get('vod_total', '0') + '集',
                    'vod_score': i.get('vod_score', '')
                })
            return {'list': videos}
        except Exception as e:
            print(f"获取首页视频失败: {e}")
            return {'list': []}

    def detailContent(self, ids):
        try:
            response = self.post(f'{self.api_host}/api/detail/{ids[0]}', data=json.dumps({}), headers=self.headers).json()
            data = response.get('data', {})
            videos = []
            vod_play_url = ''
            
            # 检查是否有播放数据
            if 'player' in data and isinstance(data['player'], dict):
                for name, url in data['player'].items():
                    vod_play_url += f'{name}${url}#'
                vod_play_url = vod_play_url.rstrip('#')
            
            videos.append({
                'vod_id': data.get('vod_id', ''),
                'vod_name': data.get('vod_name', ''),
                'vod_content': data.get('vod_blurb', ''),
                'vod_remarks': '集数：' + data.get('vod_total', '0'),
                "vod_director": data.get('vod_director', ''),
                "vod_actor": data.get('vod_actor', ''),
                'vod_year': data.get('vod_year', ''),
                'vod_area': data.get('vod_area', ''),
                'vod_play_from': 'MiniDrama',
                'vod_play_url': vod_play_url
            })
            return {'list': videos}
        except Exception as e:
            print(f"获取详情失败: {e}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        payload = {
            "page": int(pg),
            "limit": 24,
            "type_id": "",
            "keyword": key
        }
        try:
            response = self.post(f'{self.api_host}{self.api_path}', data=json.dumps(payload), headers=self.headers).json()
            data = response.get('data', {})
            videos = []
            for i in data.get('list', []):
                videos.append({
                    "vod_id": i.get('vod_id', ''),
                    "vod_name": i.get('vod_name', ''),
                    "vod_class": i.get('vod_class', ''),
                    "vod_pic": i.get('vod_pic', ''),
                    'vod_year': i.get('vod_year', ''),
                    "vod_remarks": i.get('vod_total', '0') + '集'
                })
            return {
                'list': videos, 
                'page': pg, 
                'total': data.get('total', 0), 
                'limit': 24
            }
        except Exception as e:
            print(f"搜索失败: {e}")
            return {'list': [], 'page': pg, 'total': 0, 'limit': 24}

    def categoryContent(self, tid, pg, filter, extend):
        payload = {
            "page": int(pg),
            "limit": 24,
            "type_id": tid,
            "year": "",
            "keyword": ""
        }
        try:
            response = self.post(f'{self.api_host}{self.api_path}', data=json.dumps(payload), headers=self.headers).json()
            data = response.get('data', {})
            videos = []
            for i in data.get('list', []):
                videos.append({
                    'vod_id': i.get('vod_id', ''),
                    'vod_name': i.get('vod_name', ''),
                    'vod_class': i.get('vod_class', ''),
                    'vod_pic': i.get('vod_pic', ''),
                    'vod_remarks': i.get('vod_total', '0') + '集',
                    'vod_year': i.get('vod_year', ''),
                    'vod_score': i.get('vod_score', '')
                })
            return {'list': videos}
        except Exception as e:
            print(f"获取分类内容失败: {e}")
            return {'list': []}

    def playerContent(self, flag, id, vipflags):
        parse = 0
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        try:
            response = self.fetch(id, headers=self.headers).text
            # 尝试多种可能的视频URL提取方式
            patterns = [
                r'let\s+data\s*=\s*(\{[^}]*http[^}]*\});',
                r'var\s+data\s*=\s*(\{[^}]*http[^}]*\});',
                r'url\s*[:=]\s*[\'\"](https?://[^\'\"]+)[\'\"]',
                r'src\s*[:=]\s*[\'\"](https?://[^\'\"]+)[\'\"]'
            ]
            
            url = id  # 默认使用原始ID
            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    if pattern.startswith(('let', 'var')):
                        try:
                            data = match.group(1)
                            data2 = json.loads(data)
                            url = data2.get('url', id)
                        except:
                            continue
                    else:
                        url = match.group(1)
                    break
                    
            # 检查是否是视频格式
            if not self.isVideoFormat(url):
                parse = 1
                
        except Exception as e:
            print(f"解析播放地址失败: {e}")
            url, parse = id, 1
            
        return {'parse': parse, 'url': url, 'header': header}

    def isVideoFormat(self, url):
        """检查URL是否为视频格式"""
        video_extensions = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.mov', '.wmv', '.webm']
        return any(url.lower().endswith(ext) for ext in video_extensions)

    def init(self, extend=''):
        pass

    def getName(self):
        return "MiniDrama短剧"

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    def localProxy(self, param):
        pass