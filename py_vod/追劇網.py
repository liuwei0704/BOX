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
            res = self.fetch(self.host)
            if not res or res.status_code != 200:
                return result
            html = res.text
            result['list'] = self._parse_videos(html, limit=30)
        except Exception as e:
            pass
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

            res = self.fetch(url)
            if not res or res.status_code != 200:
                return result

            html = res.text
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
            pass
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
                # 处理各种URL格式
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

            print(f"详情页URL: {detail_url}")
            res = self.fetch(detail_url)
            if not res or res.status_code != 200:
                return result

            soup = BeautifulSoup(res.text, 'html.parser')

            # 获取标题
            vod_name = ""
            h1 = soup.select_one('h1')
            if h1:
                vod_name = h1.get_text(strip=True)
            if not vod_name:
                title_tag = soup.find('title')
                if title_tag:
                    vod_name = title_tag.get_text(strip=True).split(' - ')[0].split('|')[0].strip()

            # 获取图片
            vod_pic = ""
            img = soup.select_one('img.lazyload')
            if img:
                vod_pic = img.get('data-original') or img.get('src')
            if not vod_pic:
                meta_img = soup.find('meta', property='og:image')
                if meta_img:
                    vod_pic = meta_img.get('content')
            if vod_pic and not vod_pic.startswith('http'):
                if vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
                elif vod_pic.startswith('/'):
                    vod_pic = self.host + vod_pic

            # 获取简介
            vod_content = ""
            content_div = soup.select_one('.play_content, .vod_content, .desc')
            if content_div:
                vod_content = content_div.get_text(strip=True)

            # 提取播放线路和剧集
            play_from_list = []
            play_url_list = []

            # 方法1：从页面中提取线路
            line_tabs = soup.select('#NumTab a, .tabs a, .play-source-tab a')
            if not line_tabs:
                line_tabs = soup.select('a[href*="vodplay"]')

            line_data = {}
            for tab in line_tabs:
                href = tab.get('href', '')
                name = tab.get_text(strip=True)
                if not name or len(name) > 20:
                    continue

                # 提取线路ID
                line_match = re.search(r'/vodplay/(\d+)-(\d+)-\d+\.html', href)
                if line_match:
                    vid = line_match.group(1)
                    line_id = line_match.group(2)
                    if line_id not in line_data:
                        line_data[line_id] = {'name': name, 'vid': vid, 'episodes': []}

            # 如果没找到线路，创建默认
            if not line_data:
                play_links = soup.select('a[href*="/vodplay/"]')
                for link in play_links:
                    href = link.get('href', '')
                    match = re.search(r'/vodplay/(\d+)-(\d+)-\d+\.html', href)
                    if match:
                        vid = match.group(1)
                        line_id = match.group(2)
                        if line_id not in line_data:
                            line_data[line_id] = {'name': f"線路{line_id}", 'vid': vid, 'episodes': []}
                        text = link.get_text(strip=True)
                        if text:
                            line_data[line_id]['episodes'].append((text, href))

            # 如果没有找到任何数据，尝试从播放器页面获取
            if not line_data:
                # 从vod_id构建播放页
                play_url = f"{self.host}/vodplay/{vod_id}-1-1.html"
                play_res = self.fetch(play_url)
                if play_res and play_res.status_code == 200:
                    play_soup = BeautifulSoup(play_res.text, 'html.parser')
                    play_tabs = play_soup.select('#NumTab a, .tabs a')
                    for tab in play_tabs:
                        href = tab.get('href', '')
                        name = tab.get_text(strip=True)
                        match = re.search(r'/vodplay/(\d+)-(\d+)-\d+\.html', href)
                        if match:
                            vid = match.group(1)
                            line_id = match.group(2)
                            if line_id not in line_data:
                                line_data[line_id] = {'name': name, 'vid': vid, 'episodes': []}

            # 为每个线路获取剧集
            for line_id, data in line_data.items():
                if data['episodes']:
                    episodes = data['episodes']
                else:
                    episodes = []
                    container = soup.select_one(f'#playlist_{line_id}, .playlist_{line_id}, div[data-id="{line_id}"]')
                    if container:
                        ep_links = container.select('a[href*="vodplay"]')
                        for link in ep_links:
                            href = link.get('href', '')
                            text = link.get_text(strip=True)
                            if href:
                                episodes.append((text, href))

                if not episodes:
                    episodes = [("第1集", f"/vodplay/{data['vid']}-{line_id}-1.html")]

                # 按集数排序
                def get_ep_num(item):
                    match = re.search(r'第(\d+)集', item[0])
                    if match:
                        return int(match.group(1))
                    return 999

                episodes.sort(key=get_ep_num)

                ep_urls = []
                for text, href in episodes:
                    if not href.startswith('http'):
                        if href.startswith('//'):
                            href = 'https:' + href
                        elif href.startswith('/'):
                            href = self.host + href
                        else:
                            href = self.host + '/' + href
                    ep_urls.append(f"{text}${href}")

                if ep_urls:
                    play_from_list.append(data['name'])
                    play_url_list.append("#".join(ep_urls))

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

            # 使用 requests 直接请求，不通过 session
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
                result["url"] = url
                result["header"] = self.headers
                return result

            html = resp.text
            
            # 参考永乐视频的方式：匹配 player_aaaa
            match = re.search(r'var\s+player_aaaa\s*=\s*({.*?});', html, re.S | re.I)
            if match:
                try:
                    config_text = match.group(1)
                    # 清理换行和注释
                    config_text = config_text.replace('\n', '').replace('\r', '').replace('\t', '')
                    config_text = re.sub(r'//.*?$', '', config_text, flags=re.M)
                    player_data = json.loads(config_text)
                    play_url = player_data.get('url', '')
                    if play_url:
                        play_url = play_url.replace('\\/', '/')
                        # 处理相对路径
                        if not play_url.startswith('http'):
                            if play_url.startswith('//'):
                                play_url = 'https:' + play_url
                            else:
                                play_url = self.host + play_url
                        result["parse"] = 0
                        result["url"] = play_url
                        result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
                        return result
                except Exception as e:
                    pass

            # 直接匹配 m3u8
            m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html, re.S | re.I)
            if m3u8_match:
                result["parse"] = 0
                result["url"] = m3u8_match.group(1)
                result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
                return result

            # 降级到 WebView 嗅探
            result["parse"] = 1
            result["url"] = url
            result["header"] = {"User-Agent": self.headers['User-Agent'], "Referer": self.host}
        except Exception as e:
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
        soup = BeautifulSoup(html, 'html.parser')

        # 查找视频项目
        items = soup.select('.vodlist_item')
        if not items:
            items = soup.select('li.vodlist_item')

        for item in items:
            # 获取链接
            a_tag = item.select_one('a.vodlist_thumb')
            if not a_tag:
                a_tag = item.select_one('a[href*="/voddetail/"]')
            if not a_tag:
                continue

            href = a_tag.get('href', '')
            # 提取ID
            vod_id = href
            if not vod_id.startswith('http'):
                if vod_id.startswith('//'):
                    vod_id = 'https:' + vod_id
                elif vod_id.startswith('/'):
                    vod_id = self.host + vod_id
                else:
                    vod_id = self.host + '/' + vod_id

            # 获取图片
            vod_pic = a_tag.get('data-original') or a_tag.get('src', '')
            if vod_pic and not vod_pic.startswith('http'):
                if vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
                elif vod_pic.startswith('/'):
                    vod_pic = self.host + vod_pic

            # 获取标题
            vod_name = ""
            title_elem = item.select_one('.vodlist_title, .title, .name')
            if title_elem:
                title_link = title_elem.select_one('a')
                if title_link:
                    vod_name = title_link.get_text(strip=True)
                else:
                    vod_name = title_elem.get_text(strip=True)

            if not vod_name:
                vod_name = a_tag.get('title', '')

            # 获取备注
            vod_remarks = ""
            pic_text = item.select_one('.pic_text, .remarks, .note')
            if pic_text:
                vod_remarks = pic_text.get_text(strip=True)

            if vod_id:
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })

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