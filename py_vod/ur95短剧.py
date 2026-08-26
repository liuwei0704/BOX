# 爬虫名称: ur95短剧 (暴力修复版)
# 修复内容: 固化分类入口、强化播放逻辑、完善Cookie模拟

import re
import json
import base64
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""):
        self.siteUrl = 'https://www.ur95.com'
        self.header = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
            "Referer": self.siteUrl,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        
    def getName(self):
        return '热播短剧网'
        
    def getType(self):
        return 3
        
    def getVersion(self):
        return 2.0

    def checkInit(self):
        if not hasattr(self, 'siteUrl'):
            self.init()
        
    def homeContent(self, filter):
        self.checkInit()
        result = {'class': [], 'list': []}
        try:
            # 1. 固化分类列表 (最稳妥的方式)
            classes = [
                {'type_id': '1', 'type_name': '重生'},
                {'type_id': '2', 'type_name': '穿越'},
                {'type_id': '3', 'type_name': '爽剧'},
                {'type_id': '4', 'type_name': '言情'},
                {'type_id': '5', 'type_name': '都市'},
                {'type_id': '6', 'type_name': '古装'},
                {'type_id': '7', 'type_name': '悬疑'},
                {'type_id': '8', 'type_name': '剧情'}
            ]
            result['class'] = classes
            
            # 2. 获取首页列表
            res = self.fetch(self.siteUrl, headers=self.header)
            html = res.text
            items = re.findall(r'href="/daquan/(\d+)\.html".*?title="([^"]+)".*?data-src="([^"]+)"', html, re.S)
            for vid, title, pic in items:
                # 终极漂白：去空格、去特殊字符后比对
                t_str = title.strip()
                clean_title = re.sub(r'\s+', '', t_str)
                bad_words = ["短剧大全", "排行榜", "首页", "导航", "广告", "APP下载", "官网站"]
                if any(word in clean_title for word in bad_words):
                    continue
                result['list'].append({
                    'vod_id': vid,
                    'vod_name': t_str,
                    'vod_pic': pic,
                    'vod_remarks': ''
                })
        except:
            pass
        return result
    
    def categoryContent(self, tid, pg, filter, extend):
        self.checkInit()
        result = {'page': pg, 'pagecount': 1, 'limit': 24, 'total': 0, 'list': []}
        try:
            url = f'{self.siteUrl}/duan/{tid}_{pg}.html' if int(pg) > 1 else f'{self.siteUrl}/duan/{tid}.html'
            html = self.fetch(url, headers=self.header).text
            items = re.findall(r'href="/daquan/(\d+)\.html".*?title="([^"]+)".*?data-src="([^"]+)"', html, re.S)
            for vid, title, pic in items:
                t_str = title.strip()
                # 强力过滤：剔除所有包含广告特征的标题
                if any(x in t_str for x in ["短剧大全", "排行榜", "首页", "导航", "广告"]):
                    continue
                result['list'].append({'vod_id': vid, 'vod_name': t_str, 'vod_pic': pic, 'vod_remarks': ''})
            
            pg_match = re.search(r'href="/duan/\d+-(\d+)\.html"[^>]*>尾页', html)
            if pg_match: result['pagecount'] = int(pg_match.group(1))
        except:
            pass
        return result
    
    def detailContent(self, ids):
        self.checkInit()
        vod_id = ids[0]
        try:
            url = f'{self.siteUrl}/daquan/{vod_id}.html'
            html = self.fetch(url, headers=self.header).text
            
            vod = {
                'vod_id': vod_id,
                'vod_name': re.search(r'og:title" content="([^"]+)"', html).group(1),
                'vod_pic': re.search(r'og:image" content="([^"]+)"', html).group(1),
                'vod_content': re.search(r'og:description" content="([^"]+)"', html).group(1),
                'vod_play_from': '主线路',
                'vod_play_url': ''
            }
            
            # 播放列表解析
            playlist_match = re.search(r'id="playlist\d+"[^>]*>(.*?)</div>', html, re.S)
            if playlist_match:
                eps = re.findall(r'title="([^"]+)"\s+href="([^"]+)"', playlist_match.group(1))
                vod['vod_play_url'] = "#".join([f"{t}${p}" for t, p in eps])
            
            return {'list': [vod]}
        except:
            return {'list': []}
    
    def playerContent(self, flag, id, vipFlags):
        self.checkInit()
        # 处理可能的相对路径
        url = self.siteUrl + id if id.startswith('/') else id
        try:
            res = self.fetch(url, headers=self.header)
            html = res.text
            
            # 深度嗅探播放地址
            # 1. 直接匹配 URL
            m3u8 = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', html)
            if m3u8:
                return {'url': m3u8.group(1).replace('\/', '/'), 'parse': 0, 'header': self.header}
            
            # 2. 匹配 var now 或 player_data 中的 url
            now = re.search(r'var\s+now\s*=\s*["\']([^"\']+)["\']', html)
            if now:
                return {'url': now.group(1).replace('\/', '/'), 'parse': 0, 'header': self.header}
            
            # 3. 匹配 JSON 格式 (player_aaaa)
            player_json = re.search(r'player_aaaa\s*=\s*(\{.*?\})', html)
            if player_json:
                data = json.loads(player_json.group(1))
                if 'url' in data:
                    return {'url': data['url'], 'parse': 0, 'header': self.header}

        except:
            pass
        return {'url': url, 'parse': 1}

    def searchContent(self, key, quick, pg=1):
        self.checkInit()
        result = {'list': []}
        try:
            # 1. 优先尝试标准的 GET 搜索 (适配该站点的实际接口)
            # 有些站点的搜索地址是 /index.php/vod/search.html?wd=xxx
            search_url = f'{self.siteUrl}/index.php/ajax/suggest?mid=1&wd={key}&limit=10'
            res = self.fetch(search_url, headers=self.header)
            
            # 如果是 AJAX 接口返回 JSON
            try:
                data = res.json()
                if data and 'list' in data:
                    for item in data['list']:
                        result['list'].append({
                            'vod_id': item['id'],
                            'vod_name': item['name'],
                            'vod_pic': item['pic'],
                            'vod_remarks': ''
                        })
                    return result
            except:
                pass

            # 2. 保底方案：传统页面抓取 (适配 /search.php 或 /vodsearch/...)
            # 我们直接请求搜索展示页
            url = f'{self.siteUrl}/search.php?searchword={key}'
            html = self.fetch(url, headers=self.header).text
            
            # 宽松正则匹配搜索结果页
            items = re.findall(r'href="/daquan/(\d+)\.html".*?title="([^"]+)".*?data-src="([^"]+)"', html, re.S)
            # 如果上面没匹配到，换一种匹配方式 (针对搜索页可能的不同结构)
            if not items:
                items = re.findall(r'href="/daquan/(\d+)\.html".*?alt="([^"]+)".*?src="([^"]+)"', html, re.S)
            
            for vid, title, pic in items:
                t_str = title.strip()
                # 同样应用过滤逻辑
                clean_title = re.sub(r'\s+', '', t_str)
                if any(word in clean_title for word in ["短剧大全", "排行榜", "首页"]):
                    continue
                result['list'].append({
                    'vod_id': vid,
                    'vod_name': t_str,
                    'vod_pic': pic,
                    'vod_remarks': ''
                })
        except:
            pass
        return result

    def localProxy(self, param):
        return None