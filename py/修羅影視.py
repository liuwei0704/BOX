from base.spider import Spider
import re
import urllib.parse

class Spider(Spider):
    def init(self, extend=""):
        self.host = "https://www.xlys02.com"
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        self.headers = {
            "User-Agent": self.ua,
            "Referer": self.host + "/"
        }

    def homeContent(self, filter):
        self.init()
        res = self.fetch(self.host, headers=self.headers)
        root = self.html(res.text)
        classes = []
        seen_names = set()
        for nav in root.xpath("//a[contains(@href,'/s/')]"):
            name = "".join(nav.xpath(".//text()")).strip()
            if name and name not in seen_names and 1 < len(name) < 5:
                href = nav.xpath("./@href")[0].split(';')[0]
                classes.append({"type_id": href, "type_name": name})
                seen_names.add(name)
        return {"class": classes[:12], "list": self.parse_list(res.text)}

    def categoryContent(self, tid, pg, filter, extend):
        self.init()
        url = self.host + tid if tid.startswith('/') else f"{self.host}{tid}"
        if int(pg) > 1:
            url += f"&page={pg}" if "?" in url else f"?page={pg}"
        res = self.fetch(url.split(';')[0], headers=self.headers)
        return {"list": self.parse_list(res.text), "page": pg, "pagecount": 99}

    def parse_list(self, html_str):
        root = self.html(html_str)
        vids = []
        seen_ids = set()
        items = root.xpath("//div[contains(@class,'card')] | //div[contains(@class,'col-')] | //li[contains(@class,'media')] | //div[contains(@class,'item')]")
        for item in items:
            links = item.xpath(".//a[contains(@href, '.htm') and not(contains(@href, '/play/'))]/@href")
            if not links: continue
            href = links[0].split(';')[0]
            if any(x in href for x in ["/user/", "/topic", "/message"]): continue
            
            name_nodes = item.xpath(".//h3/text() | .//h4/text() | .//a[contains(@class,'title')]/text() | .//@title")
            title = name_nodes[0].strip() if name_nodes else ""
            img = item.xpath(".//img/@src | .//img/@data-src | .//img/@data-original")
            
            if title and href not in seen_ids:
                full_href = href if href.startswith('/') else f"/{href}"
                full_img = img[0] if img else ""
                if full_img.startswith('//'): full_img = "https:" + full_img
                vids.append({"vod_id": full_href, "vod_name": title, "vod_pic": full_img, "vod_remarks": ""})
                seen_ids.add(href)
        return vids

    def detailContent(self, ids):
        self.init()
        clean_id = ids[0].split(';')[0]
        full_url = self.host + (clean_id if clean_id.startswith('/') else f"/{clean_id}")
        res = self.fetch(full_url, headers=self.headers)
        html_source = res.text
        root = self.html(html_source)
        name = (root.xpath("//h1/text() | //h2/text() | //title/text()") or ["未知"])[0].strip().split(' - ')[0]
        play_list, down_list = [], []
        for p in root.xpath("//a[contains(@href, '/play/')]"):
            p_text = "".join(p.xpath(".//text()")).strip()
            p_href = p.xpath('./@href')[0].split(';')[0]
            if p_text and len(p_text) < 15: play_list.append(f"{p_text}${p_href}")
        raw_links = re.findall(r'(?:ed2k://|magnet:\?xt=)[^\s\'"<>]+', html_source)
        for i, link in enumerate(list(dict.fromkeys(raw_links))):
            down_list.append(f"磁力線路 {i+1}${link}")
        return {"list": [{"vod_id": clean_id, "vod_name": name, "vod_play_from": "在線播放$$$磁力下載", "vod_play_url": "#".join(play_list) + "$$$" + "#".join(down_list)}]}

    def searchContent(self, key, quick, pg="1"):
        self.init()
        # 模擬 POST 搜尋，這通常是解決搜尋失效的關鍵
        search_path = "/index.php?m=vod-search"
        payload = f"wd={urllib.parse.quote(key)}&submit=search"
        headers = self.headers.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        # 嘗試 POST 請求
        res = self.post(self.host + search_path, data=payload, headers=headers)
        
        # 如果 POST 沒結果，降級使用 GET (帶 submit 參數)
        if not self.parse_list(res.text):
            res = self.fetch(f"{self.host}/search?wd={urllib.parse.quote(key)}&submit=", headers=self.headers)
            
        return {"list": self.parse_list(res.text)}

    def playerContent(self, flag, id, vipFlags):
        url = id.split(';')[0]
        if any(url.startswith(p) for p in ["ed2k", "magnet", "thunder"]): return {"parse": 0, "url": url}
        play_page = self.host + url if url.startswith('/') else f"{self.host}/{url}"
        return {"parse": 1, "url": play_page, "header": {"User-Agent": self.ua, "Referer": play_page}, "jx": "1"}