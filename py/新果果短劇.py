import json
import re
import requests
from urllib.parse import quote, unquote
from lxml import etree

class Spider():
    def getName(self):
        return "果果新短劇"

    def init(self, extend=""):
        self.siteUrl = "https://www.ggduanju.com"
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.siteUrl
        }

    def getDependence(self):
        return []

    def isVideoCanPlay(self):
        return ""

    def isVideoStatus(self, vod_id, name, cnt):
        return True

    def homeContent(self, filter):
        classes = [
            {"type_name": "推薦榜", "type_id": "推荐榜"},
            {"type_name": "熱門榜", "type_id": "热门榜"},
            {"type_name": "新劇榜", "type_id": "新剧榜"},
            {"type_name": "完結榜", "type_id": "完结榜"}
        ]
        return {"class": classes}

    def homeVideoContent(self):
        return self.categoryContent("推荐榜", 1, {}, {})

    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'siteUrl'):
            self.init()
        import urllib.parse
        curr_pg = int(pg)
        encoded_tid = urllib.parse.quote(tid)
    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'siteUrl'):
            self.init()
        import urllib.parse
        curr_pg = int(pg)
        
        # 使用你提供的 URL 結構：直接在 /duanju/ 後接參數
        url = f"{self.siteUrl}/duanju/?cat={tid}&page={curr_pg}&load_more=true"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': f"{self.siteUrl}/duanju/",
            'Accept': 'text/html, */*; q=0.01'
        }

        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            content = res.text
            
            # 如果帶 load_more 沒數據，嘗試普通分頁格式
            if "recordView" not in content:
                url_backup = f"{self.siteUrl}/duanju/index.php?cat={urllib.parse.quote(tid)}&page={curr_pg}"
                res = requests.get(url_backup, headers=headers, timeout=10)
                res.encoding = 'utf-8'
                content = res.text

            vod_list = []
            pattern = r"recordView\('(.+?)',\s*'(.+?)',\s*'(.+?)',\s*'(.+?)',\s*'(.+?)'\)"
            matches = re.findall(pattern, content)
            
            for m in matches:
                name, pic, time_str, episode, bookid = m
                vod_list.append({
                    "vod_id": f"/duanju/detail.php?bookid={bookid}",
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": f"{episode} | {time_str}"
                })

            has_next = "loadMoreBtn" in content and len(vod_list) > 0
            return {
                "list": vod_list,
                "page": curr_pg,
                "pagecount": curr_pg + 1 if has_next else curr_pg,
                "limit": 20,
                "total": 999
            }
        except:
            return {"list": []}
            return {"list": []}

    def detailContent(self, ids):
        if not hasattr(self, 'siteUrl'):
            self.init()
        tid = ids[0]
        url = self.siteUrl + tid if tid.startswith('/') else f"{self.siteUrl}/duanju/{tid}"
        
        try:
            res = requests.get(url, timeout=10, headers=self.header)
            res.encoding = 'utf-8'
            html = etree.HTML(res.text)
            
            name = self.xpathText(html, '//h2[@class="info-title"]/text()') or self.xpathText(html, '//div[@class="header-title-text"]/text()')
            pic = self.xpath(html, '//img[@class="detail-poster"]/@src')
            desc = self.xpathText(html, '//p[@class="info-desc"]/text()')
            
            vod = {
                "vod_id": tid,
                "vod_name": name.strip() if name else "未知新劇",
                "vod_pic": pic,
                "type_name": "新短劇",
                "vod_content": desc.strip() if desc else "無簡介"
            }
            
            play_url = []
            ep_nodes = html.xpath('//div[@id="episodeGrid"]//a')
            for a in ep_nodes:
                ep_name = "".join(a.xpath('./text()')).strip().replace('✓', '')
                ep_href = a.xpath('./@href')[0]
                if "player.php" in ep_href:
                    ep_href = "/duanju/" + ep_href
                play_url.append(f"{ep_name}${ep_href}")
            
            vod["vod_play_from"] = "幼稚線路"
            vod["vod_play_url"] = "#".join(play_url)
            return {"list": [vod]}
        except:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        if not hasattr(self, 'siteUrl'):
            self.init()
        playUrl = self.siteUrl + id if id.startswith('/') else f"{self.siteUrl}/duanju/{id}"
        return {"parse": 1, "url": playUrl, "header": ""}

    def searchContent(self, key, quick, pg="1"):
        if not hasattr(self, 'siteUrl'):
            self.init()
        import urllib.parse
        curr_pg = int(pg)
        session = requests.Session()
        headers = {'User-Agent': self.header['User-Agent'], 'Referer': f"{self.siteUrl}/duanju/"}
        
        try:
            session.get(f"{self.siteUrl}/duanju/", headers=headers, timeout=5)
            encoded_key = urllib.parse.quote(key)
            url = f"{self.siteUrl}/duanju/index.php?keyword={encoded_key}&page={curr_pg}"
            res = session.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            content = res.text

            vod_list = []
            pattern = r"recordView\('(.+?)',\s*'(.+?)',\s*'(.+?)',\s*'(.+?)',\s*'(.+?)'\)"
            matches = re.findall(pattern, content)
            for m in matches:
                name, pic, time, episode, bookid = m
                vod_list.append({
                    "vod_id": f"/duanju/detail.php?bookid={bookid}",
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": f"{time} / {episode}"
                })
            return {"list": vod_list}
        except:
            return {"list": []}

    def xpathText(self, node, path):
        res = node.xpath(path)
        return res[0] if res else ""
        
    def xpath(self, node, path):
        res = node.xpath(path)
        return res[0] if res else ""