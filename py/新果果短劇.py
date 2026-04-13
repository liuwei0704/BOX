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
        # 新短劇板塊的固定分類
        classes = [
            {"type_name": "推薦榜", "type_id": "推荐榜"},
            {"type_name": "熱門榜", "type_id": "热门榜"},
            {"type_name": "新劇榜", "type_id": "新剧榜"},
            {"type_name": "完結榜", "type_id": "完结榜"}
        ]
        return {"class": classes}

    def homeVideoContent(self):
        # 預設加載推薦榜首頁
        return self.categoryContent("推荐榜", 1, {}, {})

    def categoryContent(self, tid, pg, filter, extend):
        curr_pg = int(pg)
        vod_list = []
        
        # 構造 URL
        cat_name = quote(tid)
        url = f"{self.siteUrl}/duanju/index.php?cat={cat_name}&page={curr_pg}"
        
        # 強化 Header，新短劇板塊有時會檢查 Referer
        headers = self.header.copy()
        headers['Referer'] = f"{self.siteUrl}/duanju/"
        
        try:
            res = requests.get(url, timeout=10, headers=headers)
            res.encoding = 'utf-8'
            content = res.text
            
            # 如果返回內容太短，可能是沒數據了
            if len(content) < 500:
                return {"list": [], "page": curr_pg, "pagecount": curr_pg}
                
            html = etree.HTML(content)
            nodes = html.xpath('//div[contains(@class, "movie-item")]')
            
            for node in nodes:
                try:
                    name_nodes = node.xpath('.//div[contains(@class, "movie-title")]/text()')
                    name = name_nodes[0].strip() if name_nodes else ""
                    
                    pic_nodes = node.xpath('.//img[contains(@class, "movie-poster")]/@src')
                    pic = pic_nodes[0] if pic_nodes else ""
                    
                    href_nodes = node.xpath('.//a/@href')
                    if not href_nodes: continue
                    href = href_nodes[0]
                    
                    vod_id = "/duanju/" + href if "detail.php" in href and not href.startswith("/") else href
                    remark = "".join(node.xpath('.//div[contains(@class, "movie-desc")]/text()')).strip()
                    
                    vod_list.append({
                        "vod_id": vod_id,
                        "vod_name": name,
                        "vod_pic": pic,
                        "vod_remarks": remark
                    })
                except: continue
            
            # 判斷是否有下一頁：
            # 1. 根據目前抓到的數量（通常一頁 12 或 18 個）
            # 2. 檢查頁面是否有 "下一页" 字眼的鏈接
            has_next = False
            next_nodes = html.xpath('//a[contains(text(), "下一页")]/@href')
            if next_nodes or len(vod_list) >= 10:
                has_next = True
                
            return {
                "list": vod_list, 
                "page": curr_pg, 
                "pagecount": curr_pg + 1 if has_next else curr_pg
            }
        except: return {"list": []}

    def detailContent(self, ids):
        tid = ids[0]
        # 確保 URL 正確拼接
        url = self.siteUrl + tid if tid.startswith('/') else f"{self.siteUrl}/duanju/{tid}"
        
        try:
            res = requests.get(url, timeout=10, headers=self.header)
            res.encoding = 'utf-8'
            html = etree.HTML(res.text)
            
            # 新版詳情頁解析
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
            
            # 解析播放列表 (episode-grid 結構)
            play_url = []
            ep_nodes = html.xpath('//div[@id="episodeGrid"]//a')
            for a in ep_nodes:
                ep_name = "".join(a.xpath('./text()')).strip().replace('✓', '')
                ep_href = a.xpath('./@href')[0]
                # 確保播放地址補全
                if "player.php" in ep_href:
                    ep_href = "/duanju/" + ep_href
                play_url.append(f"{ep_name}${ep_href}")
            
            vod["vod_play_from"] = "幼稚線路"
            vod["vod_play_url"] = "#".join(play_url)
            
            return {"list": [vod]}
        except: return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        # 拼接完整的播放頁網址
        playUrl = self.siteUrl + id if id.startswith('/') else f"{self.siteUrl}/duanju/{id}"
        return {"parse": 1, "url": playUrl, "header": ""}

    def searchContent(self, key, quick, pg="1"):
        import urllib.parse
        curr_pg = int(pg)
        # 1. 建立 Session 自動處理 Cookie
        session = requests.Session()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Referer': f"{self.siteUrl}/duanju/",
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        
        try:
            # 第一步：先訪問 /duanju/ 獲取基礎 Cookie
            session.get(f"{self.siteUrl}/duanju/", headers=headers, timeout=5)
            
            # 第二步：手動構造 URL，確保關鍵字被正確編碼 (UTF-8)
            encoded_key = urllib.parse.quote(key)
            url = f"{self.siteUrl}/duanju/index.php?keyword={encoded_key}&page={curr_pg}"
            
            # 第三步：發送搜尋請求
            res = session.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            content = res.text

            # 如果 content 裡面有 "正在跳转" 或 "验证" 字樣，說明被攔截了
            if 'movie-item' not in content and 'recordView' not in content:
                # 嘗試另一種 URL 格式 (有些 PHP 站點只認這種)
                url_alt = f"{self.siteUrl}/duanju/?keyword={encoded_key}"
                res = session.get(url_alt, headers=headers, timeout=10)
                res.encoding = 'utf-8'
                content = res.text

            vod_list = []
            
            # 暴力正則提取：針對 recordView 函數直接拿數據
            # 格式：recordView('標題', '圖片', '時間', '集數', 'ID')
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

            # 如果正則沒抓到，嘗試 XPath 保底
            if not vod_list:
                html = etree.HTML(content)
                nodes = html.xpath('//div[contains(@class, "movie-item")]')
                for node in nodes:
                    name = node.xpath('.//div[@class="movie-title"]/text()')[0].strip()
                    pic = node.xpath('.//img/@src')[0]
                    href = node.xpath('.//a/@href')[0]
                    vod_id = "/duanju/" + href if "detail.php" in href and not href.startswith("/") else href
                    vod_list.append({
                        "vod_id": vod_id,
                        "vod_name": name,
                        "vod_pic": pic,
                        "vod_remarks": ""
                    })

            return {"list": vod_list}
            
        except Exception as e:
            return {"list": []}

    # 輔助函數：提取文本
    def xpathText(self, node, path):
        res = node.xpath(path)
        return res[0] if res else ""
        
    # 輔助函數：提取屬性
    def xpath(self, node, path):
        res = node.xpath(path)
        return res[0] if res else ""