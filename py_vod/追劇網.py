# coding=utf-8
# 追劇網 - TVBox/FongMi 爬虫
# 站点: https://ztv.tw/
import sys
import re
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup

# 禁用SSL证书验证警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "追劇網"

    def init(self, extend=""):
        self.host = "https://ztv.tw"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update(self.headers)
        # 添加从浏览器复制的关键Cookie
        self.session.cookies.set('server_session_c903ae07', 'cb57a57d9ae2ceca86c25ea3732f539f', domain='ztv.tw')
    def fetch(self, url, timeout=15, retry=2):
        for attempt in range(retry + 1):
            try:
                # 每次请求更新Cookie
                if not hasattr(self, 'session'):
                    self.session = requests.Session()
                    self.session.verify = False
                    self.session.headers.update(self.headers)
                
                # 添加随机延迟避免频率限制
                if attempt > 0:
                    import time
                    time.sleep(0.5 * attempt)
                
                response = self.session.get(url, timeout=timeout, verify=False)
                if response.status_code == 403 and attempt < retry:
                    # 403时更新Cookie并重试
                    self.session.cookies.clear()
                    self.session.headers.update({'Cache-Control': 'no-cache'})
                    continue
                response.encoding = response.apparent_encoding or 'utf-8'
                return response
            except Exception as e:
                if attempt == retry:
                    return None
                continue
        return None
    def homeContent(self, filter):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {
            "class": [
                {"type_id": "1", "type_name": "電影"},
                {"type_id": "2", "type_name": "劇集"},
                {"type_id": "3", "type_name": "綜藝"},
                {"type_id": "4", "type_name": "動漫"},
                {"type_id": "27", "type_name": "福利"}
            ],
            "filters": self._get_filters(),
            "list": []
        }
        # 加载首页推荐
        home_data = self.homeVideoContent()
        result['list'] = home_data.get('list', [])
        return result

    def getHomeContent(self):
        """TVBox/FongMi 兼容方法"""
        return self.homeContent(False)

    def homeVideoContent(self):
        result = {"list": []}
        try:
            import requests as req
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.host + '/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
            }
            resp = req.get(self.host, headers=headers, timeout=15, verify=False)
            if resp.status_code != 200:
                return result
            html = resp.text
            
            # 使用正则提取首页推荐视频
            # 匹配格式：<a class="vodlist_thumb" href="/voddetail/数字.html" title="标题" data-original="图片">
            pattern = r'<a[^>]*class="[^"]*vodlist_thumb[^"]*"[^>]*href="(/voddetail/(\d+)\.html)"[^>]*title="([^"]*)"[^>]*(?:data-original="([^"]*)"|data-src="([^"]*)"|src="([^"]*)"|lazy-src="([^"]*)"|style="[^"]*url\(([^)]+)\)")[^>]*>'
            matches = re.findall(pattern, html, re.S | re.I)
            
            for match in matches:
                href = match[0]
                vid = match[1]
                title = match[2].strip()
                pic = match[3] or match[4] or match[5] or match[6] or match[7] or ""
                if pic:
                    pic = pic.strip()
                    if pic.startswith('//'):
                        pic = 'https:' + pic
                    elif pic.startswith('/'):
                        pic = self.host + pic
                
                # 提取备注
                remark = ""
                remark_match = re.search(r'<span[^>]*class="[^"]*pic_text[^"]*"[^>]*>([^<]+)</span>', html[html.find(href):html.find(href)+600] if href in html else "", re.S)
                if remark_match:
                    remark = remark_match.group(1).strip()
                
                if vid and title:
                    result['list'].append({
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": remark
                    })
                    if len(result['list']) >= 30:
                        break
        except Exception as e:
            print(f"homeVideoContent错误: {e}")
        return result
    def categoryContent(self, tid, pg, filter, extend):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}
        try:
            page_num = int(pg) if pg else 1
            if page_num > 1:
                url = f"{self.host}/vodtype/{tid}-{page_num}.html"
            else:
                url = f"{self.host}/vodtype/{tid}.html"

            # 尝试使用 requests 直接请求（不通过 session）
            import requests as req
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.host + '/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            resp = req.get(url, headers=headers, timeout=15, verify=False)
            if resp.status_code != 200:
                return result

            html = resp.text
            result['list'] = self._parse_videos(html)

            # 解析总页数
            pagecount = 1
            page_links = re.findall(rf'/vodtype/{tid}-(\d+)\.html', html)
            if page_links:
                max_page = max([int(p) for p in page_links])
                pagecount = max_page if max_page > 1 else 1
            result['pagecount'] = pagecount
            result['total'] = pagecount * 20
        except Exception as e:
            print(f"categoryContent错误: {e}")
        return result
    def searchContent(self, key, quick, pg=1):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}
        try:
            search_key = urllib.parse.quote(key)
            page_num = int(pg) if pg else 1
            url = f"{self.host}/vodsearch/{search_key}----------{page_num}---.html"

            res = self.fetch(url)
            if not res or res.status_code != 200:
                return result

            html = res.text
            result['list'] = self._parse_search_results(html)

            # 解析总数和总页数
            total_match = re.search(r'相關的<em[^>]*>(\d+)</em>條結果', html)
            if total_match:
                result['total'] = int(total_match.group(1))
            page_match = re.search(r'總共\s*(\d+)\s*頁', html)
            if page_match:
                result['pagecount'] = int(page_match.group(1))
        except Exception as e:
            pass
        return result

    def detailContent(self, ids):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {"list": []}
        try:
            vod_id = ids[0]
            # 如果传入的是纯数字ID，直接构建详情URL
            if vod_id.isdigit():
                detail_url = f"{self.host}/voddetail/{vod_id}.html"
            else:
                if '/voddetail/' in vod_id:
                    detail_url = vod_id
                elif '/vodplay/' in vod_id:
                    match = re.search(r'/vodplay/(\d+)-\d+-\d+\.html', vod_id)
                    if match:
                        detail_id = match.group(1)
                        detail_url = f"{self.host}/voddetail/{detail_id}.html"
                    else:
                        detail_url = vod_id
                else:
                    detail_url = f"{self.host}/voddetail/{vod_id}.html"

            if not detail_url.startswith('http'):
                if detail_url.startswith('/'):
                    detail_url = self.host + detail_url
                else:
                    detail_url = self.host + '/' + detail_url

            # 使用 requests 直接请求
            import requests as req
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.host + '/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            resp = req.get(detail_url, headers=headers, timeout=15, verify=False)
            if resp.status_code != 200:
                return result

            html = resp.text

            # 提取标题
            vod_name = ""
            title_match = re.search(r'<title>([^<]+)</title>', html, re.S | re.I)
            if title_match:
                title = title_match.group(1).strip()
                vod_name = re.sub(r'\s*[-|]\s*追劇網.*$', '', title).strip()
                vod_name = re.sub(r'線上看$', '', vod_name).strip()
            if not vod_name:
                meta_title = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html, re.S | re.I)
                if meta_title:
                    vod_name = meta_title.group(1).strip()

            # 提取图片
            vod_pic = ""
            meta_img = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html, re.S | re.I)
            if meta_img:
                vod_pic = meta_img.group(1).strip()
            if not vod_pic:
                img_match = re.search(r'<img[^>]*data-original="([^"]+)"', html, re.S | re.I)
                if img_match:
                    vod_pic = img_match.group(1).strip()
            if not vod_pic:
                img_match2 = re.search(r'<img[^>]*src="([^"]*\.(?:jpg|jpeg|png|webp))"', html, re.S | re.I)
                if img_match2:
                    vod_pic = img_match2.group(1).strip()
            if vod_pic and not vod_pic.startswith('http'):
                if vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
                elif vod_pic.startswith('/'):
                    vod_pic = self.host + vod_pic

            # 提取简介
            vod_content = ""
            desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html, re.S | re.I)
            if desc_match:
                vod_content = desc_match.group(1).strip()

            # 提取线路和剧集 - 更精确的匹配
            play_from_list = []
            play_url_list = []

            # 查找所有线路标签，匹配格式: <a href="/vodplay/..."><i class="iconfont">&#xe62f;</i>&nbsp;线路名</a>
            line_pattern = r'<a[^>]*href="(/vodplay/\d+-\d+-\d+\.html)"[^>]*>.*?<i[^>]*>[^<]*</i>\s*([^<]+)</a>'
            line_matches = re.findall(line_pattern, html, re.S | re.I)

            if line_matches:
                # 按线路分组
                line_data = {}
                for href, name in line_matches:
                    # 清理线路名称
                    name = name.replace('&nbsp;', '').replace('&amp;', '&').strip()
                    if not name:
                        continue
                    # 提取线路ID
                    match = re.search(r'/vodplay/(\d+)-(\d+)-\d+\.html', href)
                    if match:
                        vid = match.group(1)
                        line_id = match.group(2)
                        if line_id not in line_data:
                            line_data[line_id] = {'name': name, 'vid': vid, 'episodes': []}
                        # 从href提取剧集名称
                        ep_name = name
                        # 检查是否已有剧集名
                        if '第' in ep_name:
                            line_data[line_id]['episodes'].append((ep_name, href))
                        else:
                            # 尝试从href提取集数
                            ep_match = re.search(r'/vodplay/\d+-\d+-(\d+)\.html', href)
                            if ep_match:
                                ep_name = f"第{ep_match.group(1)}集"
                            line_data[line_id]['episodes'].append((ep_name, href))

                for line_id, data in line_data.items():
                    if data['episodes']:
                        play_from_list.append(data['name'])
                        ep_urls = []
                        for ep_name, ep_href in data['episodes']:
                            if not ep_href.startswith('http'):
                                if ep_href.startswith('/'):
                                    ep_href = self.host + ep_href
                                else:
                                    ep_href = self.host + '/' + ep_href
                            ep_urls.append(f"{ep_name}${ep_href}")
                        play_url_list.append("#".join(ep_urls))

            # 如果没有找到线路，尝试从播放列表容器提取
            if not play_from_list:
                # 查找播放列表中的剧集链接
                ep_pattern = r'<a[^>]*href="(/vodplay/\d+-\d+-\d+\.html)"[^>]*>([^<]+)</a>'
                ep_matches = re.findall(ep_pattern, html, re.S | re.I)
                if ep_matches:
                    play_from_list = ["追劇網線路"]
                    ep_urls = []
                    for href, name in ep_matches:
                        name = name.replace('&nbsp;', '').strip()
                        if not name:
                            match = re.search(r'/vodplay/\d+-\d+-(\d+)\.html', href)
                            if match:
                                name = f"第{match.group(1)}集"
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                href = self.host + href
                            else:
                                href = self.host + '/' + href
                        ep_urls.append(f"{name}${href}")
                    if ep_urls:
                        play_url_list.append("#".join(ep_urls))

            # 如果还是没有，使用默认
            if not play_from_list:
                play_from_list = ["追劇網線路"]
                play_url_list = [f"第1集${self.host}/vodplay/{vod_id}-1-1.html"]

            vod = {
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_remarks": "",
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }
            result['list'] = [vod]
        except Exception as e:
            print(f"详情解析错误: {e}")
        return result
    def playerContent(self, flag, id, vipFlags):
        # 确保初始化
        if not hasattr(self, 'host'):
            self.init()
        result = {"parse": 1, "playUrl": "", "url": ""}
        try:
            # 处理传入的id
            if id.startswith('http'):
                url = id
            else:
                if id.startswith('/'):
                    url = self.host + id
                else:
                    url = self.host + '/' + id

            # 使用独立的 requests 请求
            import requests as req
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.host + '/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            print(f"请求URL: {url}")
            resp = req.get(url, headers=headers, timeout=15, verify=False)
            print(f"状态码: {resp.status_code}")
            
            if resp.status_code != 200:
                result["url"] = url
                result["header"] = self.headers
                return result

            html = resp.text
            print(f"页面长度: {len(html)}")
            
            # 直接提取 url 字段
            url_match = re.search(r'"url"\s*:\s*"([^"]+)"', html, re.S | re.I)
            if url_match:
                play_url = url_match.group(1)
                play_url = play_url.replace('\\/', '/')
                print(f"提取到url: {play_url}")
                if play_url and ('.m3u8' in play_url or '.mp4' in play_url):
                    result["parse"] = 0
                    result["url"] = play_url
                    result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
                    return result

            # 直接匹配 m3u8
            m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html, re.S | re.I)
            if m3u8_match:
                print(f"提取到m3u8: {m3u8_match.group(1)}")
                result["parse"] = 0
                result["url"] = m3u8_match.group(1)
                result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
                return result

            print("未找到直链，降级到WebView嗅探")
            result["parse"] = 1
            result["url"] = url
            result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
        except Exception as e:
            print(f"playerContent错误: {e}")
            result["parse"] = 1
            result["url"] = id
            result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
        return result
    def _get_filters(self):
        return {
            "1": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}],
            "2": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}],
            "3": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}],
            "4": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}],
            "27": [{"key": "class", "name": "类型", "value": [{"n": "全部", "v": ""}]}]
        }

    def _parse_videos(self, html, limit=0):
        videos = []
        try:
            # 方法1：使用正则表达式匹配视频列表项
            # 匹配格式：<a class="vodlist_thumb" href="/voddetail/数字.html" title="标题" data-original="图片">
            pattern = r'<a[^>]*class="[^"]*vodlist_thumb[^"]*"[^>]*href="(/voddetail/(\d+)\.html)"[^>]*title="([^"]*)"[^>]*(?:data-original="([^"]*)"|data-src="([^"]*)"|src="([^"]*)")[^>]*>'
            matches = re.findall(pattern, html, re.S | re.I)
            
            for match in matches:
                href = match[0]
                vid = match[1]
                title = match[2].strip()
                # 图片地址可能在 data-original、data-src 或 src 中
                pic = match[3] or match[4] or match[5] or ""
                if pic and not pic.startswith('http'):
                    if pic.startswith('//'):
                        pic = 'https:' + pic
                    elif pic.startswith('/'):
                        pic = self.host + pic
                
                # 获取备注（从 <span class="pic_text"> 中提取）
                remark = ""
                remark_match = re.search(r'<span[^>]*class="[^"]*pic_text[^"]*"[^>]*>([^<]+)</span>', html[html.find(href):html.find(href)+500] if href in html else "", re.S)
                if remark_match:
                    remark = remark_match.group(1).strip()
                
                if vid and title:
                    videos.append({
                        "vod_id": f"{self.host}/voddetail/{vid}.html",
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": remark
                    })
            
            # 方法2：如果正则没有匹配到，尝试使用BeautifulSoup
            if not videos:
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.select('.vodlist_item, li.vodlist_item')
                for item in items:
                    a_tag = item.select_one('a.vodlist_thumb, a[href*="/voddetail/"]')
                    if not a_tag:
                        continue
                    href = a_tag.get('href', '')
                    vid_match = re.search(r'/voddetail/(\d+)\.html', href)
                    if not vid_match:
                        continue
                    vid = vid_match.group(1)
                    title = a_tag.get('title', '') or a_tag.get('alt', '')
                    if not title:
                        title_elem = item.select_one('.vodlist_title, .title')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                    pic = a_tag.get('data-original') or a_tag.get('data-src') or a_tag.get('src', '')
                    if pic and not pic.startswith('http'):
                        if pic.startswith('//'):
                            pic = 'https:' + pic
                        elif pic.startswith('/'):
                            pic = self.host + pic
                    remark = ""
                    remark_elem = item.select_one('.pic_text')
                    if remark_elem:
                        remark = remark_elem.get_text(strip=True)
                    if vid and title:
                        videos.append({
                            "vod_id": f"{self.host}/voddetail/{vid}.html",
                            "vod_name": title,
                            "vod_pic": pic,
                            "vod_remarks": remark
                        })
        except Exception as e:
            print(f"_parse_videos 错误: {e}")
        
        if limit and len(videos) > limit:
            return videos[:limit]
        return videos
    def _parse_search_results(self, html):
        videos = []
        soup = BeautifulSoup(html, 'html.parser')

        items = soup.select('.searchlist_item')
        for item in items:
            img_div = item.select_one('.searchlist_img')
            if img_div:
                a_tag = img_div.select_one('a.vodlist_thumb')
            else:
                a_tag = item.select_one('a[href*="/voddetail/"]')

            if not a_tag:
                continue

            href = a_tag.get('href', '')
            vod_id = href
            if not vod_id.startswith('http'):
                if vod_id.startswith('//'):
                    vod_id = 'https:' + vod_id
                elif vod_id.startswith('/'):
                    vod_id = self.host + vod_id
                else:
                    vod_id = self.host + '/' + vod_id

            vod_pic = a_tag.get('data-original') or a_tag.get('src', '')
            if vod_pic and not vod_pic.startswith('http'):
                if vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
                elif vod_pic.startswith('/'):
                    vod_pic = self.host + vod_pic

            title_div = item.select_one('.searchlist_titbox')
            vod_name = ""
            if title_div:
                title_a = title_div.select_one('h4 .vodlist_title a, .title a')
                if title_a:
                    vod_name = title_a.get_text(strip=True)

            if not vod_name:
                vod_name = a_tag.get('title', '')

            vod_remarks = ""
            pic_text = a_tag.select_one('.pic_text')
            if pic_text:
                vod_remarks = pic_text.get_text(strip=True)

            videos.append({
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_remarks": vod_remarks
            })

        return videos