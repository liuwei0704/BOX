#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import json
import time
import requests
from datetime import datetime
from urllib.parse import quote, unquote
from hashlib import md5
from functools import reduce

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    def __init__(self):
        super().__init__()
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
            "Referer": "https://www.bilibili.com"
        }
        self.retry = 0
        self.extendDict = {}

    def getName(self):
        return "B站视频"

    def init(self, extend):
        try:
            self.extendDict = json.loads(extend)
        except:
            self.extendDict = {}

    def cleanText(self, text):
        # 移除不必要的字符
        return re.sub(r'[\x00-\x1F\x7F]', '', text).strip()

    def removeHtmlTags(self, text):
        return re.sub(r'<[^>]+>', '', text).strip()

    def formatDuration(self, seconds):
        # 将秒数转为 HH:MM:SS 或 MM:SS
        seconds = int(seconds)
        if seconds >= 3600:
            return time.strftime('%H:%M:%S', time.gmtime(seconds))
        else:
            return time.strftime('%M:%S', time.gmtime(seconds)).lstrip('0')

    def getCookieAndKeys(self):
        """统一获取 cookie 和 imgKey/subKey"""
        cookie_str = self.extendDict.get('cookie', '')
        
        if 'json' in self.extendDict:
            try:
                r = self.fetch(self.extendDict['json'], timeout=10)
                data = r.json()
                if 'cookie' in data:
                    cookie_str = data['cookie']
            except:
                pass
        
        if not cookie_str:
            cookie_str = '{}'
        elif isinstance(cookie_str, str) and cookie_str.startswith('http'):
            cookie_str = self.fetch(cookie_str, timeout=10).text.strip()
        
        try:
            if isinstance(cookie_str, dict):
                cookie_str = json.dumps(cookie_str, ensure_ascii=False)
        except:
            pass
        
        return self._parseCookie(cookie_str)

    def _parseCookie(self, cookie_str):
        if cookie_str.startswith('{') and cookie_str.endswith('}'):
            try:
                cookies = json.loads(cookie_str)
            except:
                cookies = {}
        else:
            cookies = {}
            for item in cookie_str.strip(';').split(';'):
                if '=' in item:
                    k, v = item.strip().split('=', 1)
                    cookies[k] = v
        
        # 尝试从缓存获取
        bblogin = self.getCache('bblogin')
        if bblogin:
            return cookies, bblogin.get('imgKey', ''), bblogin.get('subKey', '')
        
        # 请求接口获取
        try:
            r = requests.get(
                "http://api.bilibili.com/x/web-interface/nav",
                cookies=cookies,
                headers=self.header,
                timeout=10
            )
            data = r.json()
            if data.get("code") == 0:
                img_url = data['data']['wbi_img']['img_url']
                sub_url = data['data']['wbi_img']['sub_url']
                imgKey = img_url.rsplit('/', 1)[1].split('.')[0]
                subKey = sub_url.rsplit('/', 1)[1].split('.')[0]
                
                cache_data = {
                    'imgKey': imgKey,
                    'subKey': subKey,
                    'expiresAt': int(time.time()) + 1200
                }
                self.setCache('bblogin', cache_data)
                return cookies, imgKey, subKey
        except:
            pass
        
        # 兜底方案
        try:
            r = self.fetch("https://www.bilibili.com/", headers=self.header, timeout=5)
            cookies = r.cookies.get_dict()
        except:
            pass
        
        return cookies, '', ''

    def homeContent(self, filter):
        result = {
            'filters': {},
            'class': []
        }
        
        # 获取分类配置
        config_classes = []
        if 'json' in self.extendDict:
            try:
                r = self.fetch(self.extendDict['json'], timeout=10)
                params = r.json()
                if 'classes' in params:
                    config_classes = params['classes']
                if filter and 'filter' in params:
                    result['filters'] = params['filter']
            except:
                pass
        elif 'categories' in self.extendDict or 'type' in self.extendDict:
            cate_str = self.extendDict.get('categories') or self.extendDict.get('type', '')
            if cate_str:
                for cate in cate_str.split('#'):
                    config_classes.append({'type_name': cate, 'type_id': cate})
        
        result['class'].extend(config_classes)
        
        # 默认分类
        if not result['class']:
            default_cates = [
                {"type_name": "動態漫", "type_id": "動態漫"},
                {"type_name": "傻屌仙逆", "type_id": "沙雕仙逆"},
                {"type_name": "沙雕动画", "type_id": "沙雕动画"},
                {"type_name": "小姐姐", "type_id": "小姐姐"},
                {"type_name": "熱舞", "type_id": "熱舞"}
            ]
            result['class'] = default_cates
        
        return result

    def homeVideoContent(self):
        result = {'list': []}
        cookies, _, _ = self.getCookieAndKeys()
        
        try:
            url = 'https://api.bilibili.com/x/web-interface/index/top/feed/rcmd?ps=20'
            r = requests.get(url, cookies=cookies, headers=self.header, timeout=5)
            data = r.json()
            
            for vod in data.get('data', {}).get('item', []):
                try:
                    aid = str(vod['id']).strip()
                    title = self.removeHtmlTags(vod.get('title', '')).strip()
                    img = vod.get('pic', '').strip()
                    duration = vod.get('duration', 0)
                    
                    if duration <= 0:
                        continue
                    
                    remark = self.formatDuration(duration)
                    result['list'].append({
                        'vod_id': aid,
                        'vod_name': title,
                        'vod_pic': img,
                        'vod_remarks': remark
                    })
                except:
                    continue
        except:
            pass
        
        return result

    def categoryContent(self, cid, page, filter, ext):
        page = int(page)
        result = {
            'list': [],
            'page': page,
            'pagecount': page,
            'limit': 0,
            'total': 0
        }
        
        cookies, imgKey, subKey = self.getCookieAndKeys()
        
        # 分类处理
        if cid == '动态':
            return self._handleDynamic(cid, page, cookies, result)
        elif cid == '收藏夹':
            return self._handleFavoriteFolder(page, cookies, result)
        elif cid.startswith('fav&&&'):
            return self._handleFavoriteList(cid, page, cookies, result)
        elif cid.startswith('UP主&&&'):
            return self._handleUpVideos(cid, page, cookies, imgKey, subKey, result)
        elif cid == '历史记录':
            return self._handleHistory(page, cookies, result)
        else:
            return self._handleSearch(cid, page, ext, cookies, result)
        
        return result

    def _handleDynamic(self, cid, page, cookies, result):
        if page > 1:
            offset = self.getCache('offset') or ''
            url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?offset={offset}&page={page}'
        else:
            url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?page={page}'
        
        r = self.fetch(url, cookies=cookies, headers=self.header, timeout=5)
        data = r.json()
        
        if 'offset' in data.get('data', {}):
            self.setCache('offset', data['data']['offset'])
        
        has_more = data.get('data', {}).get('has_more', False)
        result['pagecount'] = page + 1 if has_more else page
        
        for vod in data.get('data', {}).get('items', []):
            if vod.get('type') != 'DYNAMIC_TYPE_AV':
                continue
            
            modules = vod.get('modules', {}).get('module_dynamic', {})
            archive = modules.get('major', {}).get('archive', {})
            
            vid = str(archive.get('aid', '')).strip()
            if not vid:
                continue
            
            title = self.removeHtmlTags(archive.get('title', '')).strip()
            img = archive.get('cover', '')
            remark = archive.get('duration_text', '').strip()
            
            result['list'].append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": img,
                "vod_remarks": remark
            })
        
        result['limit'] = result['total'] = len(result['list'])
        return result

    def _handleFavoriteFolder(self, page, cookies, result):
        userid = self._getUserId(cookies)
        if not userid:
            return result
        
        url = f'http://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid={userid}'
        r = self.fetch(url, cookies=cookies, headers=self.header, timeout=5)
        data = r.json()
        
        for vod in data.get('data', {}).get('list', []):
            vid = vod.get('id', '')
            title = vod.get('title', '').strip()
            remark = vod.get('media_count', 0)
            
            result['list'].append({
                "vod_id": f'fav&&&{vid}',
                "vod_name": title,
                "vod_pic": 'https://api-lmteam.koyeb.app/files/shoucang.png',
                "vod_tag": 'folder',
                "vod_remarks": str(remark)
            })
        
        result['limit'] = result['total'] = len(result['list'])
        return result

    def _handleFavoriteList(self, cid, page, cookies, result):
        media_id = cid[6:]
        url = f'http://api.bilibili.com/x/v3/fav/resource/list?media_id={media_id}&pn={page}&ps=20'
        r = self.fetch(url, cookies=cookies, headers=self.header, timeout=5)
        data = r.json()
        
        has_more = data.get('data', {}).get('has_more', False)
        result['pagecount'] = page + 1 if has_more else page
        
        for vod in data.get('data', {}).get('medias', []):
            vid = str(vod.get('id', '')).strip()
            title = self.removeHtmlTags(vod.get('title', '')).replace("&quot;", '"')
            img = vod.get('cover', '').strip()
            duration = vod.get('duration', 0)
            
            if duration <= 0:
                continue
            
            remark = self.formatDuration(duration)
            result['list'].append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": img,
                "vod_remarks": remark
            })
        
        result['limit'] = result['total'] = len(result['list'])
        return result

    def _handleUpVideos(self, cid, page, cookies, imgKey, subKey, result):
        mid = cid[6:]
        params = {'mid': mid, 'ps': 30, 'pn': page}
        
        if imgKey and subKey:
            params = self.encWbi(params, imgKey, subKey)
        
        url = 'https://api.bilibili.com/x/space/wbi/arc/search?'
        for key in params:
            url += f'&{key}={quote(str(params[key]))}'
        
        r = self.fetch(url, cookies=cookies, headers=self.header, timeout=5)
        data = r.json()
        
        page_data = data.get('data', {}).get('page', {})
        page_count = page_data.get('count', 1)
        result['pagecount'] = page + 1 if page < page_count else page
        
        # 第一页添加播放列表项
        if page == 1:
            result['list'].append({
                "vod_id": f'UP主&&&{mid}',
                "vod_name": '播放列表'
            })
        
        for vod in data.get('data', {}).get('list', {}).get('vlist', []):
            vid = str(vod.get('aid', '')).strip()
            title = self.removeHtmlTags(vod.get('title', '')).replace("&quot;", '"')
            img = vod.get('pic', '').strip()
            length = vod.get('length', '00:00')
            
            # 处理时长格式
            if ':' in length:
                parts = length.split(':')
                if len(parts) == 2:
                    minutes, seconds = parts
                    if minutes.isdigit() and int(minutes) >= 60:
                        hours = int(minutes) // 60
                        minutes = int(minutes) % 60
                        remark = f"{hours:02d}:{minutes:02d}:{seconds}"
                    else:
                        remark = f"{int(minutes):02d}:{seconds}"
                else:
                    remark = length
            else:
                remark = length
            
            result['list'].append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": img,
                "vod_remarks": remark
            })
        
        result['limit'] = result['total'] = len(result['list'])
        return result

    def _handleHistory(self, page, cookies, result):
        url = f'http://api.bilibili.com/x/v2/history?pn={page}'
        r = self.fetch(url, cookies=cookies, headers=self.header, timeout=5)
        data = r.json()
        
        items = data.get('data', [])
        if len(items) == 300:
            result['pagecount'] = page + 1
        else:
            result['pagecount'] = page
        
        for vod in items:
            duration = vod.get('duration', 0)
            progress = vod.get('progress', -1)
            
            if duration <= 0 or progress == -1:
                continue
            
            vid = str(vod.get("aid", "")).strip()
            img = vod.get("pic", "").strip()
            title = self.removeHtmlTags(vod.get("title", "")).replace("&quot;", '"')
            
            progress_str = self.formatDuration(progress)
            total_str = self.formatDuration(duration)
            remark = f"{progress_str}|{total_str}"
            
            result['list'].append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": img,
                "vod_remarks": remark
            })
        
        result['limit'] = result['total'] = len(result['list'])
        return result

    def _handleSearch(self, cid, page, ext, cookies, result):
        keyword = cid
        params = f'search_type=video&keyword={quote(keyword)}&page={page}'
        
        for key in ext:
            if key == 'tid':
                continue
            params += f'&{key}={ext[key]}'
        
        url = f'https://api.bilibili.com/x/web-interface/search/type?{params}'
        r = self.fetch(url, cookies=cookies, headers=self.header, timeout=5)
        data = r.json()
        
        result['pagecount'] = data.get('data', {}).get('numPages', 1)
        
        for vod in data.get('data', {}).get('result', []):
            if vod.get('type') != 'video':
                continue
            
            vid = str(vod.get('aid', '')).strip()
            title = self.removeHtmlTags(vod.get('title', ''))
            img = 'https:' + vod.get('pic', '').strip()
            duration_str = vod.get('duration', '0:00')
            
            # 处理时长
            if ':' in duration_str:
                parts = duration_str.split(':')
                if len(parts) == 2:
                    minutes, seconds = parts
                    minutes = int(minutes)
                    if minutes >= 60:
                        hours = minutes // 60
                        minutes = minutes % 60
                        remark = f"{hours:02d}:{minutes:02d}:{seconds}"
                    else:
                        remark = f"{minutes:02d}:{seconds}"
                elif len(parts) == 3:
                    remark = duration_str
                else:
                    remark = '00:00'
            else:
                remark = '00:00'
            
            result['list'].append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": img,
                "vod_remarks": remark
            })
        
        result['limit'] = result['total'] = len(result['list'])
        return result

    def detailContent(self, did):
        aid = did[0]
        
        # UP主播放列表处理
        if aid.startswith('UP主&&&'):
            bizId = aid[6:]
            url = f'https://api.bilibili.com/x/v2/medialist/resource/list?type=1&biz_id={bizId}&ps=100'
            r = self.fetch(url, headers=self.header, timeout=5)
            data = r.json()
            
            playUrl = ''
            for video in data.get('data', {}).get('media_list', []):
                duration = video.get('duration', 0)
                title = self.removeHtmlTags(video.get('title', '')).strip()
                bvid = video.get('bv_id', '')
                
                if not bvid:
                    continue
                
                remark = self.formatDuration(duration)
                name = title.replace("#", "-").replace('$', '*')
                playUrl += f"[{remark}]/{name}$bvid&&&{bvid}#"
            
            vod = {
                "vod_id": aid,
                "vod_name": '播放列表',
                'vod_play_from': 'B站视频',
                'vod_play_url': playUrl.strip('#')
            }
            return {'list': [vod]}
        
        # 普通视频处理
        url = f"https://api.bilibili.com/x/web-interface/view?aid={aid}"
        r = self.fetch(url, headers=self.header, timeout=10)
        data = r.json().get('data', {})
        
        # 导演信息（UP主）
        director = ''
        if "staff" in data:
            for staff in data['staff']:
                mid = staff.get('mid', '')
                name = staff.get('name', '')
                if mid and name:
                    director += f'[a=cr:{{"id":"UP主&&&{mid}","name":"{name}"}}/]{name}[/a],'
        else:
            owner = data.get('owner', {})
            mid = owner.get('mid', '')
            name = owner.get('name', '')
            if mid and name:
                director = f'[a=cr:{{"id":"UP主&&&{mid}","name":"{name}"}}/]{name}[/a]'
        
        # 基本信息
        vod = {
            "vod_id": aid,
            "vod_name": self.removeHtmlTags(data.get('title', '')),
            "vod_pic": data.get('pic', ''),
            "type_name": data.get('tname', ''),
            "vod_year": datetime.fromtimestamp(data.get('pubdate', 0)).strftime('%Y-%m-%d %H:%M:%S'),
            "vod_content": data.get('desc', '').replace('\xa0', ' ').replace('\n\n', '\n').strip(),
            "vod_director": director.rstrip(','),
            "vod_play_from": 'B站视频$$$相关视频'
        }
        
        # 主视频播放列表
        playUrl = ''
        pages = data.get('pages', [])
        for video in pages:
            duration = video.get('duration', 0)
            part = video.get('part', '')
            cid = video.get('cid', '')
            
            remark = self.formatDuration(duration)
            name = self.removeHtmlTags(part).strip().replace("#", "-").replace('$', '*')
            playUrl += f"[{remark}]/{name}${aid}_{cid}#"
        
        # 相关视频
        url = f'https://api.bilibili.com/x/web-interface/archive/related?aid={aid}'
        r = self.fetch(url, headers=self.header, timeout=5)
        related_data = r.json()
        
        playUrl = playUrl.strip('#') + '$$$'
        for video in related_data.get('data', []):
            duration = video.get('duration', 0)
            title = video.get('title', '')
            related_aid = video.get('aid', '')
            related_cid = video.get('cid', '')
            
            if not related_aid or not related_cid:
                continue
            
            remark = self.formatDuration(duration)
            name = self.removeHtmlTags(title).strip().replace("#", "-").replace('$', '*')
            playUrl += f'[{remark}]/{name}${related_aid}_{related_cid}#'
        
        vod['vod_play_url'] = playUrl.strip('#')
        return {'list': [vod]}

    def searchContent(self, key, quick):
        return self.searchContentPage(key, quick, '1')

    def searchContentPage(self, key, quick, page):
        if quick:
            return {'list': []}
        
        cookies, _, _ = self.getCookieAndKeys()
        url = f'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={quote(key)}&page={page}'
        
        try:
            r = self.fetch(url, headers=self.header, cookies=cookies, timeout=5)
            data = r.json()
        except:
            return {'list': []}
        
        videos = []
        for vod in data.get('data', {}).get('result', []):
            if vod.get('type') != 'video':
                continue
            
            aid = str(vod.get('aid', '')).strip()
            title = self.removeHtmlTags(vod.get('title', ''))
            img = 'https:' + vod.get('pic', '').strip()
            duration_str = vod.get('duration', '0:00')
            
            # 处理时长
            if ':' in duration_str:
                parts = duration_str.split(':')
                if len(parts) == 2:
                    minutes, seconds = parts
                    minutes = int(minutes)
                    if minutes >= 60:
                        hours = minutes // 60
                        minutes = minutes % 60
                        remark = f"{hours:02d}:{minutes:02d}:{seconds}"
                    else:
                        remark = f"{minutes:02d}:{seconds}"
                else:
                    remark = duration_str
            else:
                remark = '00:00'
            
            videos.append({
                "vod_id": aid,
                "vod_name": title,
                "vod_pic": img,
                "vod_remarks": remark
            })
        
        return {'list': videos}

    def playerContent(self, flag, pid, vipFlags):
        result = {
            "parse": 0,
            "playUrl": '',
            "header": self.header
        }
        
        # 解析视频ID
        if pid.startswith('bvid&&&'):
            bvid = pid[7:]
            url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            r = self.fetch(url, headers=self.header, timeout=10)
            data = r.json().get('data', {})
            aid = data.get('aid', '')
            cid = data.get('cid', '')
        else:
            parts = pid.split("_")
            aid = parts[0] if len(parts) > 0 else ''
            cid = parts[1] if len(parts) > 1 else ''
        
        if not aid or not cid:
            return result
        
        # 获取cookie
        cookies, _, _ = self.getCookieAndKeys()
        cookies_str = quote(json.dumps(cookies))
        
        # 构建代理URL
        thread = str(self.extendDict.get('thread', '0'))
        api_url = f'https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn=120&fnval=4048'
        proxy_url = f'http://127.0.0.1:9978/proxy?do=py&type=mpd&cookies={cookies_str}&url={quote(api_url)}&aid={aid}&cid={cid}&thread={thread}'
        
        result["url"] = proxy_url
        result["danmaku"] = f'https://api.bilibili.com/x/v1/dm/list.so?oid={cid}'
        result["format"] = 'application/dash+xml'
        
        return result

    def localProxy(self, params):
        if params.get('type') == "mpd":
            return self.proxyMpd(params)
        elif params.get('type') == "media":
            return self.proxyMedia(params)
        return None

    def proxyMpd(self, params):
        content, dashinfos, mediaType = self.getDash(params)
        
        if mediaType == 'mpd':
            return [200, "application/dash+xml", content]
        else:
            # 处理mp4直链
            url = content
            if dashinfos and 'durl' in dashinfos and dashinfos['durl']:
                durl = dashinfos['durl'][0]
                url_list = [durl.get('url', '')]
                if 'backup_url' in durl:
                    url_list.extend(durl['backup_url'])
                
                for u in url_list:
                    if 'mcdn.bilivideo.cn' not in u:
                        url = u
                        break
            
            header = self.header.copy()
            if 'range' in params:
                header['Range'] = params['range']
            
            if '127.0.0.1:7777' in url:
                header["Location"] = url
                return [302, "video/MP2T", None, header]
            
            r = requests.get(url, headers=header, stream=True, timeout=10)
            return [206, "application/octet-stream", r.content]

    def proxyMedia(self, params, forceRefresh=False):
        _, dashinfos, _ = self.getDash(params)
        
        # 确定是视频还是音频
        if 'videoid' in params:
            videoid = int(params['videoid'])
            if 'video' in dashinfos and videoid < len(dashinfos['video']):
                dashinfo = dashinfos['video'][videoid]
        elif 'audioid' in params:
            audioid = int(params['audioid'])
            if 'audio' in dashinfos and audioid < len(dashinfos['audio']):
                dashinfo = dashinfos['audio'][audioid]
        else:
            return [404, "text/plain", ""]
        
        # 选择最佳URL
        url_list = [dashinfo.get('baseUrl', '')]
        if 'backupUrl' in dashinfo:
            url_list.extend(dashinfo['backupUrl'])
        
        url = ''
        for u in url_list:
            if 'mcdn.bilivideo.cn' not in u:
                url = u
                break
        
        if not url:
            return [404, "text/plain", ""]
        
        header = self.header.copy()
        if 'range' in params:
            header['Range'] = params['range']
        
        r = requests.get(url, headers=header, stream=True, timeout=10)
        return [206, "application/octet-stream", r.content]

    def getDash(self, params, forceRefresh=False):
        aid = params.get('aid', '')
        cid = params.get('cid', '')
        url = unquote(params.get('url', ''))
        thread = params.get('thread', '0')
        
        cache_key = f'bilivdmpdcache_{aid}_{cid}'
        if not forceRefresh:
            cached = self.getCache(cache_key)
            if cached:
                return cached.get('content', ''), cached.get('dashinfos', {}), cached.get('type', '')
        
        # 获取cookie
        try:
            cookieDict = json.loads(params.get('cookies', '{}'))
        except:
            cookieDict = {}
        
        # 请求数据
        try:
            r = self.fetch(url, cookies=cookieDict, headers=self.header, timeout=5)
            data = r.json()
        except:
            return '', {}, ''
        
        if data.get('code') != 0:
            return '', {}, ''
        
        # 非dash格式（mp4直链）
        if 'dash' not in data.get('data', {}):
            durl = data['data'].get('durl', [])
            if not durl:
                return '', {}, ''
            
            purl = durl[0].get('url', '')
            if not purl:
                return '', {}, ''
            
            # 解析过期时间
            expiresAt = int(time.time()) + 600
            match = re.search(r'deadline=(\d+)', purl)
            if match:
                expiresAt = int(match.group(1)) - 60
            
            # 线程代理
            if thread != '0':
                try:
                    self.fetch('http://127.0.0.1:7777', timeout=2)
                except:
                    self.fetch('http://127.0.0.1:9978/go', timeout=2)
                purl = f'http://127.0.0.1:7777?url={quote(purl)}&thread={thread}'
            
            cache_data = {
                'content': purl,
                'type': 'mp4',
                'dashinfos': data['data'],
                'expiresAt': expiresAt
            }
            self.setCache(cache_key, cache_data)
            return purl, data['data'], 'mp4'
        
        # dash格式
        dashinfos = data['data']['dash']
        duration = dashinfos.get('duration', 0)
        minBufferTime = dashinfos.get('minBufferTime', '1')
        
        # 构建MPD
        video_reps = ''
        audio_reps = ''
        deadline_list = []
        
        # 视频轨
        for idx, video in enumerate(dashinfos.get('video', [])):
            # 过期时间
            deadline = int(time.time()) + 600
            match = re.search(r'deadline=(\d+)', video.get('baseUrl', ''))
            if match:
                deadline = int(match.group(1))
            deadline_list.append(deadline)
            
            # 代理URL
            baseUrl = f'http://127.0.0.1:9978/proxy?do=py&type=media&cookies={quote(json.dumps(cookieDict))}&url={quote(url)}&aid={aid}&cid={cid}&videoid={idx}'
            
            video_reps += f"""      <Representation bandwidth="{video.get('bandwidth', 0)}" codecs="{video.get('codecs', '')}" frameRate="{video.get('frameRate', '30')}" height="{video.get('height', 0)}" id="{video.get('id', '')}" width="{video.get('width', 0)}">
        <BaseURL>{baseUrl}</BaseURL>
        <SegmentBase indexRange="{video.get('SegmentBase', {}).get('indexRange', '')}">
          <Initialization range="{video.get('SegmentBase', {}).get('Initialization', '')}"/>
        </SegmentBase>
      </Representation>\n"""
        
        # 音轨
        for idx, audio in enumerate(dashinfos.get('audio', [])):
            # 过期时间
            deadline = int(time.time()) + 600
            match = re.search(r'deadline=(\d+)', audio.get('baseUrl', ''))
            if match:
                deadline = int(match.group(1))
            deadline_list.append(deadline)
            
            # 代理URL
            baseUrl = f'http://127.0.0.1:9978/proxy?do=py&type=media&cookies={quote(json.dumps(cookieDict))}&url={quote(url)}&aid={aid}&cid={cid}&audioid={idx}'
            
            audio_reps += f"""      <Representation audioSamplingRate="44100" bandwidth="{audio.get('bandwidth', 0)}" codecs="{audio.get('codecs', '')}" id="{audio.get('id', '')}">
        <BaseURL>{baseUrl}</BaseURL>
        <SegmentBase indexRange="{audio.get('SegmentBase', {}).get('indexRange', '')}">
          <Initialization range="{audio.get('SegmentBase', {}).get('Initialization', '')}"/>
        </SegmentBase>
      </Representation>\n"""
        
        # 构建完整MPD
        mpd = f"""<?xml version="1.0" encoding="UTF-8"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" profiles="urn:mpeg:dash:profile:isoff-on-demand:2011" type="static" mediaPresentationDuration="PT{duration}S" minBufferTime="PT{minBufferTime}S">
  <Period>
    <AdaptationSet mimeType="video/mp4" startWithSAP="1" scanType="progressive" segmentAlignment="true">
{video_reps.strip()}
    </AdaptationSet>
    <AdaptationSet mimeType="audio/mp4" startWithSAP="1" segmentAlignment="true" lang="und">
{audio_reps.strip()}
    </AdaptationSet>
  </Period>
</MPD>"""
        
        expiresAt = min(deadline_list) - 60 if deadline_list else int(time.time()) + 600
        cache_data = {
            'type': 'mpd',
            'content': mpd.replace('&', '&amp;'),
            'dashinfos': dashinfos,
            'expiresAt': expiresAt
        }
        self.setCache(cache_key, cache_data)
        
        return mpd.replace('&', '&amp;'), dashinfos, 'mpd'

    def _getUserId(self, cookies):
        """获取用户ID"""
        try:
            url = 'http://api.bilibili.com/x/space/myinfo'
            r = self.fetch(url, cookies=cookies, headers=self.header, timeout=5)
            data = r.json()
            if data.get('code') == 0:
                return data['data'].get('mid')
        except:
            return None
        return None

    def encWbi(self, params, imgKey, subKey):
        """WBI签名算法"""
        mixinKeyEncTab = [
            46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14,