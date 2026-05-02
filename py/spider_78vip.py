# coding=utf-8
import re
import json
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup


class Spider(Spider):
    """78vip.cfd - 猎奇伦理"""

    def getName(self):
        return "78vip"

    def init(self, extend=""):
        self.host = "https://78vip.cfd"

    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host,
        }

    def regUrl(self, url):
        """规范化 URL"""
        if not url:
            return ""
        if url.startswith('//'):
            return "https:" + url
        if url.startswith('/'):
            return self.host + url
        return url

    def _parse_list(self, soup):
        """解析 ul.img-list-data li 列表，返回 [video_item]"""
        items = soup.select('ul.img-list-data li')
        videos = []
        for li in items:
            a = li.find('a', class_='tupian-pic')
            if not a:
                continue
            vod_id = a.get('href', '')
            vod_name = a.get('title', '')
            if not vod_name:
                h3 = li.find('h3', class_='text-ellipsis')
                if h3:
                    vod_name = h3.get('title', h3.text.strip())
            img = li.find('img', class_='content-img')
            vod_pic = img.get('data-original', img.get('src', '')) if img else ''
            date_elem = li.find('p', class_='date-text-bg')
            vod_remarks = date_elem.text.strip() if date_elem else ''

            if vod_id and vod_name:
                videos.append({
                    "vod_id": self.regUrl(vod_id),
                    "vod_name": vod_name,
                    "vod_pic": self.regUrl(vod_pic),
                    "vod_remarks": vod_remarks,
                })
        return videos

    def homeContent(self, filter):
        """首页 — 返回分类列表"""
        result = {"class": [], "filter": {}}
        try:
            rsp = self.fetch(self.host, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')

            # 提取分类：取第一个 row-item 中的分类列表
            classes = []
            first_row = soup.select_one('div.row-item')
            if first_row:
                for a in first_row.select('ul.row-item-content li.item a'):
                    name = a.text.strip()
                    href = a.get('href', '')
                    tid_match = re.search(r'/id/(\d+)', href)
                    tid = tid_match.group(1) if tid_match else name
                    classes.append({"type_name": name, "type_id": tid})

            result["class"] = classes
        except Exception as e:
            pass
        return result

    def homeVideoContent(self):
        """首页 — 返回推荐视频列表"""
        try:
            rsp = self.fetch(self.host, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = self._parse_list(soup)
            return {"list": videos}
        except Exception as e:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        """分类页 — 返回分页视频列表"""
        pg = int(pg)
        if pg > 1:
            url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
        else:
            url = f"{self.host}/index.php/vod/type/id/{tid}.html"

        try:
            rsp = self.fetch(url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = self._parse_list(soup)

            # 分页
            page_text = rsp.text
            page_match = re.search(r'/(\d+)页', page_text)
            pagecount = int(page_match.group(1)) if page_match else pg

            return {
                "list": videos,
                "page": pg,
                "pagecount": pagecount,
                "limit": len(videos),
                "total": pagecount * len(videos) if pagecount > 0 else len(videos),
            }
        except Exception as e:
            return {"list": [], "page": pg, "pagecount": pg, "limit": 0, "total": 0}

    def searchContent(self, key, quick, pg=1):
        """搜索 — 返回搜索结果列表"""
        pg = int(pg)
        encoded = urllib.parse.quote(key)
        if pg > 1:
            url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{encoded}.html"
        else:
            url = f"{self.host}/index.php/vod/search.html?wd={encoded}"

        try:
            rsp = self.fetch(url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')
            videos = self._parse_list(soup)

            page_text = rsp.text
            page_match = re.search(r'/(\d+)页', page_text)
            pagecount = int(page_match.group(1)) if page_match else pg

            return {
                "list": videos,
                "page": pg,
                "pagecount": pagecount,
                "limit": len(videos),
                "total": pagecount * len(videos) if pagecount > 0 else len(videos),
            }
        except Exception as e:
            return {"list": [], "page": pg, "pagecount": pg}

    def detailContent(self, ids):
        """详情 — 返回视频详情和播放线路"""
        # ids 可能是数组或逗号分隔字符串
        if isinstance(ids, list):
            vid = ids[0] if ids else ""
        else:
            vid = ids.split(',')[0].strip() if ids else ""

        # 如果传入的是完整 URL，提取数字 ID
        id_match = re.search(r'/id/(\d+)', vid)
        if id_match:
            vid = id_match.group(1)

        url = f"{self.host}/index.php/vod/detail/id/{vid}.html"

        try:
            rsp = self.fetch(url, headers=self.header())
            soup = BeautifulSoup(rsp.text, 'html.parser')

            # 标题
            vod_name = ""
            h2 = soup.select_one('h2.c_pink')
            if h2:
                vod_name = h2.text.strip()

            # 封面
            vod_pic = ""
            img_elem = soup.select_one('div.pull-left img.lazy')
            if img_elem:
                style = img_elem.get('style', '')
                bg_match = re.search(r'url\((.+?)\)', style)
                if bg_match:
                    vod_pic = bg_match.group(1)

            # 类型 & 更新
            type_name = ""
            vod_year = ""
            for p in soup.select('div.film_info p'):
                text = p.text.strip()
                if '類型' in text or '类型' in text:
                    type_name = text.split('：')[-1].strip() if '：' in text else ''
                if '更新' in text:
                    vod_year = text.split('：')[-1].strip() if '：' in text else ''

            # 播放线路：div.play-btn-group .item.line a
            play_from = []
            play_url = []
            for a in soup.select('div.play-btn-group .item.line a'):
                line_name = a.get('title', a.text.strip())
                line_href = a.get('href', '')
                if line_name and line_href:
                    play_from.append(line_name)
                    play_url.append(line_href)

            video = {
                "vod_id": vid,
                "vod_name": vod_name,
                "vod_pic": self.regUrl(vod_pic),
                "type_name": type_name,
                "vod_year": vod_year,
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_url),
            }
            return {"list": [video]}
        except Exception as e:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        """播放 — 从播放页提取 m3u8 直链"""
        url = self.regUrl(id)
        result = {"parse": 1, "url": url, "header": self.header()}

        try:
            rsp = self.fetch(url, headers=self.header())
            html = rsp.text

            # 匹配 var player_aaaa={"url":"..."}
            match = re.search(r'var player_aaaa\s*=\s*(\{[^}]+\})', html)
            if match:
                try:
                    obj = json.loads(match.group(1))
                    m3u8 = obj.get('url', '')
                    if m3u8:
                        result["parse"] = 0
                        result["url"] = m3u8
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            pass

        return result