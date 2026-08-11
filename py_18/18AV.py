# coding=utf-8
import json
import re
import sys
import html
import urllib.parse
import urllib3
import concurrent.futures
from bs4 import BeautifulSoup
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.append('..')
from base.spider import Spider

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Spider(Spider):
    def getName(self):
        return "18AV万能聚合-终极稳定版"

    def init(self, extend=""):
        self.domains = [
            "https://mjv012.com",
            "https://mjv007.com",
            "https://mjv003.com",
            "https://mjv004.com"
        ]
        self.base_url = self.domains[0]
        self.session = Session()
        
        retry = Retry(total=2, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "HEAD"])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.ua = "Mozilla/5.0 (Linux; Android 14; 22127RK46C Build/UKQ1.230804.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36"
        self.headers = {"User-Agent": self.ua, "Accept-Language": "zh-CN,zh;q=0.9", "Referer": self.base_url + "/zh/"}
        
        # 预加载全站免 18 岁拦截通行证
        self.session.cookies.set('javascript_cookie_AgreeTOS_save1', 'javascript_cookie_AgreeTOS_save2', domain='mjv012.com')
        self.session.cookies.set('YES_Eighteen', 'IamOverEighteenYearsOld', domain='mjv012.com')

        self.CONFIG_CATES = {
            "chinese": {"name": "💠 中文字幕AV", "val": "chinese_list/all", "kind": "video"},
            "censored": {"name": "💠 有碼AV", "val": "censored_list/all", "kind": "video"},
            "uncensored": {"name": "💠 無碼AV", "val": "uncensored_list/all", "kind": "video"},
            "amateurjav": {"name": "💠 素人AV", "val": "amateurjav_list/all", "kind": "video"},
            "reducing-mosaic": {"name": "💠 無碼破解", "val": "reducing-mosaic_list/all", "kind": "video"},
            "animation": {"name": "💠 H動畫", "val": "animation_list/all", "kind": "video"},
            "dt": {"name": "💠 國產自拍", "val": "dt_list/all", "kind": "video"},
            "18H": {"name": "💠 18H漫畫", "val": "18H_list/all", "kind": "comic"},
            "cg": {"name": "💠 寫真圖片", "val": "cg_list/all", "kind": "image"},
            "novel": {"name": "💠 激情小說", "val": "novel_list/all", "kind": "novel"}
        }

    def _fix_url(self, url):
        if not url: return ""
        url = str(url).replace("\\/", "/").replace("&amp;", "&").strip()
        if url.startswith("//"): return "https:" + url
        return url if url.startswith("http") else urllib.parse.urljoin(self.base_url + "/", url)

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", html.unescape(str(text or ""))).strip()

    def _clean_desc(self, text):
        if not text: return "暂无简介"
        text = re.sub(r"(?is)<script.*?>.*?</script>|<style.*?>.*?</style>", "", html.unescape(str(text)))
        text = re.sub(r"(?i)<br\s*/?>|</p\s*>", "\n", text)
        text = re.sub(r"\n{2,}", "\n\n", re.sub(r"<[^>]+>", "", text)).strip()
        return text or "暂无简介"

    def _req_html(self, url):
        if not hasattr(self, 'domains'):
            self.init("")
        for domain in self.domains:
            full_url = url if url.startswith("http") else domain + url
            try:
                res = self.session.get(full_url, headers={"User-Agent": self.ua, "Referer": domain + "/zh/"}, verify=False, timeout=10, allow_redirects=True)
                if "IamOverEighteenYearsOld" in res.text:
                    match = re.search(r'window\.location\s*=\s*["\']([^"\']+)["\']', res.text)
                    if match:
                        jump_url = self._fix_url(match.group(1))
                        self.session.get(jump_url, headers={"User-Agent": self.ua, "Referer": full_url}, verify=False)
                        res = self.session.get(full_url, headers={"User-Agent": self.ua, "Referer": domain + "/zh/"}, verify=False)
                if res.status_code == 200 and len(res.text) > 1000:
                    self.base_url = domain
                    res.encoding = 'utf-8'
                    return res.text
            except: 
                continue
        return ""

    def homeContent(self, filter):
        if not hasattr(self, 'CONFIG_CATES'):
            self.init("")
        classes = [{"type_name": v["name"], "type_id": k} for k, v in self.CONFIG_CATES.items()]
        filters = {
            "chinese": [{"key": "cate_id", "name": "排序", "value": [{"n": "最新", "v": "chinese_list/all"}, {"n": "随机", "v": "chinese_random/all"}]}],
            "censored": [{"key": "cate_id", "name": "排序", "value": [{"n": "最新", "v": "censored_list/all"}, {"n": "随机", "v": "censored_random/all"}]}],
            "amateurjav": [{"key": "cate_id", "name": "排序", "value": [{"n": "最新", "v": "amateurjav_list/all"}, {"n": "随机", "v": "amateurjav_random/all"}]}],
            "reducing-mosaic": [{"key": "cate_id", "name": "排序", "value": [{"n": "最新", "v": "reducing-mosaic_list/all"}, {"n": "随机", "v": "reducing-mosaic_random/all"}]}],
            "dt": [{"key": "cate_id", "name": "排序", "value": [{"n": "最新", "v": "dt_list/all"}, {"n": "随机", "v": "dt_random/all"}]}],
            "uncensored": [{"key": "cate_id", "name": "片商分类", "value": [{"n": "全部", "v": "uncensored_list/all"}, {"n": "一本道", "v": "uncensored_makersr/32/一本道(1pondo)"}, {"n": "加勒比", "v": "uncensored_makersr/30/カリビアンコム(Caribbeancom)"}, {"n": "加勒比PPV", "v": "uncensored_makersr/40/カリビアンコムPPV(Caribbeancompr)"}, {"n": "天然むすめ", "v": "uncensored_makersr/31/天然むすめ(10musume)"}, {"n": "HEYZO", "v": "uncensored_makersr/17/HEYZO"}, {"n": "东京热", "v": "uncensored_makersr/29/東京熱(Tokyo Hot)"}, {"n": "ガチん娘！", "v": "uncensored_makersr/35/ガチん娘！(Gachinco)"}, {"n": "パコパコママ", "v": "uncensored_makersr/36/パコパコママ(pacopacomama)"}, {"n": "エッチな4610", "v": "uncensored_makersr/34/エッチな4610"}, {"n": "人妻斩り0930", "v": "uncensored_makersr/38/人妻斬り0930"}, {"n": "エッチな0930", "v": "uncensored_makersr/39/エッチな0930"}, {"n": "XXX-AV", "v": "uncensored_makersr/126/トリプルエックス (XXX-AV)"}]}],
            "animation": [{"key": "cate_id", "name": "动画类型", "value": [{"n": "全部", "v": "animation_list/all"}, {"n": "H有码动画", "v": "CensoredAnimation_list/all"}, {"n": "H无码动画", "v": "UncensoredAnimation_list/all"}, {"n": "H_3D动画", "v": "tdAnimation_list/all"}]}],
            "18H": [{"key": "cate_id", "name": "漫画类型", "value": [{"n": "18H长篇", "v": "18H_list/all"}, {"n": "18H短篇、同人", "v": "doujin_list/all"}]}],
            "cg": [{"key": "cate_id", "name": "写真分类", "value": [{"n": "全部", "v": "cg_list/all"}, {"n": "国产写真", "v": "cwp_list/all"}, {"n": "Bejean On Line", "v": "cg_search/all/Bejean On Line"}, {"n": "Bomb.tv", "v": "cg_search/all/Bomb.tv"}, {"n": "DGC", "v": "cg_search/all/DGC"}, {"n": "Graphis Gals", "v": "cg_search/all/Graphis Gals"}, {"n": "Graphis Hatsunugi", "v": "cg_search/all/Graphis Hatsunugi"}, {"n": "image.tv", "v": "cg_search/all/image.tv"}, {"n": "Sabra.net", "v": "cg_search/all/Sabra.net"}, {"n": "S-Cute", "v": "cg_search/all/S-Cute"}, {"n": "X-City", "v": "cg_search/all/X-City"}, {"n": "YS Web", "v": "cg_search/all/YS Web"}, {"n": "3AGirl AAA女郎", "v": "cwp_search/all/3AGirl AAA女郎"}, {"n": "ROSI写真", "v": "cwp_search/all/ROSI寫真"}, {"n": "RU1MM 如壹写真", "v": "cwp_search/all/RU1MM 如壹寫真"}, {"n": "DISI第四印象", "v": "cwp_search/all/DISI第四印象"}]}],
            "novel": [{"key": "cate_id", "name": "小说题材", "value": [{"n": "全部", "v": "novel_list/all"}, {"n": "学生校园", "v": "novel_search/all/學生校園"}, {"n": "职场激情", "v": "novel_search/all/職場激情"}, {"n": "经验故事", "v": "novel_search/all/經驗故事"}, {"n": "暴力虐待", "v": "novel_search/all/暴力虐待"}, {"n": "不伦恋情", "v": "novel_search/all/不倫戀情"}, {"n": "群体换伴", "v": "novel_search/all/群體換伴"}, {"n": "人妻熟女", "v": "novel_search/all/人妻熟女"}, {"n": "科学幻想", "v": "novel_search/all/科學幻想"}, {"n": "其他故事", "v": "novel_search/all/其他故事"}, {"n": "玄幻仙侠", "v": "novel_search/all/玄幻仙俠"}, {"n": "动漫修改", "v": "novel_search/all/動漫修改"}, {"n": "长篇连载", "v": "novel_search/all/長篇連載"}]}]
        }
        return {"class": classes, "filters": filters}

    def homeVideoContent(self):
        return {"list": []}

    def _parse_pagecount(self, soup, pg):
        pagecount = int(pg)
        for a in soup.select('div[class*="page"] a, ul[class*="page"] a, .pagination a, .pages a, a.page-numbers'):
            text = self._clean_text(a.get_text())
            if text.isdigit():
                pagecount = max(pagecount, int(text))
        if pagecount <= int(pg) and soup.find('a', string=re.compile(r'下一[页頁]|Next|next|>')):
            pagecount = int(pg) + 1
        return pagecount

    def _parse_list(self, html_text, default_kind, pg=1):
        soup = BeautifulSoup(html_text, "html.parser")
        result = []
        for p in soup.select("div.posts div.post, div.post, article, .item, .vodbox"):
            a_tag = p.select_one("h3 a") or p.select_one("h2 a") or p.select_one(".entry-title a") or p.select_one("a[href]")
            if not a_tag: continue
            title = self._clean_text(a_tag.get("title") or a_tag.get_text())
            href = self._fix_url(a_tag.get("href", ""))
            if not title or not href or "/tag/" in href: continue
            img_tag = p.select_one("img.thumb") or p.select_one("img") or p.select_one("[data-src]")
            pic = self._fix_url(img_tag.get("data-src") or img_tag.get("src") or img_tag.get("data-original") or "") if img_tag else ""
            remark_node = p.select_one(".meta") or p.select_one(".post-meta") or p.select_one(".duration")
            remark = self._clean_text(remark_node.get_text()) if remark_node else ""
            kind = default_kind
            if "/novel_content/" in href: kind = "novel"
            elif "/cg_content/" in href or "/cwp_content/" in href: kind = "image"
            elif "/doujin_content/" in href or "/18H_content/" in href: kind = "comic"
            elif "_content/" in href: kind = "video"
            result.append({
                "vod_id": f"{kind}@@{href}",
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        return result, self._parse_pagecount(soup, pg)

    def categoryContent(self, tid, pg, filter, extend):
        if not hasattr(self, 'CONFIG_CATES'):
            self.init("")
        cate_config = self.CONFIG_CATES.get(tid, {})
        if not cate_config: return {"list": [], "page": int(pg), "pagecount": int(pg), "limit": 20, "total": 9999}
        target_id = cate_config.get("val")
        if isinstance(extend, dict) and "cate_id" in extend:
            target_id = extend["cate_id"]
        target_id = urllib.parse.quote(target_id, safe='/:()')
        html_text = self._req_html(f"/zh/{target_id}/{pg}.html")
        if not html_text: return {"list": [], "page": int(pg), "pagecount": int(pg)}
        items, pagecount = self._parse_list(html_text, cate_config.get("kind", "video"), pg)
        return {"list": items, "page": int(pg), "pagecount": max(pagecount, int(pg)), "limit": 20, "total": 9999}

    def _extract_images(self, html_text, soup):
        large_cgurls = re.findall(r'Large_cgurl\[\d+\]\s*=\s*["\']([^"\']+)["\']', html_text)
        if large_cgurls: return [self._fix_url(u) for u in large_cgurls]
        pics = []
        containers = soup.select("#show_cg_html, .content_18h_wpcg, .ut1_img_content_smallcg, .entry-content")
        img_tags = []
        if containers:
            for c in containers: img_tags.extend(c.select("img"))
        else:
            img_tags = soup.select("img")
        for img in img_tags:
            src = self._fix_url(img.get("data-src") or img.get("src") or "")
            if src and src not in pics:
                src_lower = src.lower()
                if not any(ad in src_lower for ad in ["adcg", "banner", "icon", "logo", "gifb", "nowprinting", "1v.jpg", "thumb"]):
                    if any(src_lower.split("?")[0].endswith(x) for x in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                        pics.append(src)
        return pics

    def _extract_images_from_text(self, text):
        out = []
        for x in re.findall(r'https?://[^"\'\s<>,\\]+?\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\'\s<>]*)?', text, re.I):
            x = self._fix_url(x)
            if x and x not in out and not any(ad in x.lower() for ad in ["adcg", "banner", "icon", "logo", "nowprinting", "1v.jpg", "thumb"]):
                out.append(x)
        return out

    def _extract_novel_text(self, html_text, soup):
        match = re.search(r'(?:id|class)=["\']novel_content_txtsize["\'][^>]*>([\s\S]*?)</div>', html_text, re.I)
        if match:
            raw_text = match.group(1)
        else:
            container = soup.select_one(".content_18h_wpcg") or soup.select_one(".content") or soup.select_one(".main") or soup.body
            if container:
                for tag in container(["script", "style"]): tag.extract()
                for br in container.find_all("br"): br.replace_with("\n")
                for p in container.find_all("p"): p.insert_after("\n")
                raw_text = container.get_text("\n", strip=True)
            else:
                raw_text = html_text
        text = html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<p[^>]*>|<br\s*/?>', '\n', raw_text, flags=re.I))).replace('\r', '\n')
        for prefix in ["行距：", "文字放大：", "自訂文字大小："]:
            if prefix in text: text = text.split(prefix)[-1]
        for word in ["傳送門", "隨機主題", "随机主题", "發佈頁網址", "发布页网址", "意見反應區", "意见反应区", "jmvbt.com", "18 USC 2257", "Home\n"]:
            if word in text: text = text.split(word)[0]
        return '\n'.join([line.strip() for line in text.split('\n') if line.strip()]).strip()

    def _decrypt_mvarr(self, html_text):
        try:
            import base64
            from collections import Counter
            from Crypto.Cipher import AES
            keys = list(set(re.findall(r"['\"]([a-fA-F0-9]{16}|[a-fA-F0-9]{32})['\"]", html_text)))
            if not keys: return ""
            for enc_str in re.findall(r"['\"]([0-9a-z]{1,12}(?:[a-z][0-9a-z]{1,12}){20,})['\"]", html_text, re.I):
                letters = [c for c in enc_str if c.isalpha()]
                if not letters: continue
                parts = [x for x in enc_str.split(Counter(letters).most_common(1)[0][0]) if x]
                for base in range(2, 37):
                    for xor_key in range(256):
                        try:
                            b64_str = "".join(chr(int(p, base) ^ xor_key) for p in parts)
                            ciphertext = base64.b64decode(b64_str + "=" * ((4 - len(b64_str) % 4) % 4), altchars=b'-_')
                            for k1 in keys:
                                for mode, k2 in [(AES.MODE_ECB, None)] + [(AES.MODE_CBC, k) for k in keys if k != k1]:
                                    try:
                                        cipher = AES.new(k1.encode('utf-8'), mode, k2.encode('utf-8')) if k2 else AES.new(k1.encode('utf-8'), mode)
                                        decrypted = cipher.decrypt(ciphertext)
                                        pad_len = decrypted[-1]
                                        text = decrypted[:-pad_len].decode('utf-8') if 1 <= pad_len <= 16 else decrypted.decode('utf-8')
                                        if len(text) > 15 and re.match(r'^[a-zA-Z0-9_-]+$', text): return text
                                    except: pass
                        except: pass
        except: pass
        return ""

    def _decrypt_play_url(self, url: str, encrypt_type: str) -> str:
        """播放 URL 解密工具 - 对应 encrypt: '1' / '2' 处理"""
        if not url:
            return url
        try:
            if encrypt_type == '1':
                return urllib.parse.unquote(url)
            elif encrypt_type == '2':
                import base64
                decoded = base64.b64decode(url).decode('utf-8')
                return urllib.parse.unquote(decoded)
        except Exception as e:
            self.log({"_decrypt_play_url": {"encrypt": encrypt_type, "error": str(e)}})
        return url

    def detailContent(self, ids):
        raw = ids[0]
        kind, vid = raw.split("@@", 1) if "@@" in raw else ("video", raw)
        html_text = self._req_html(vid)
        if not html_text: return {"list": []}
        soup = BeautifulSoup(html_text, "html.parser")
        title_node = soup.select_one("h1") or soup.select_one("h2") or soup.find("b") or soup.select_one("title")
        vod_name = self._clean_text(title_node.get_text()) if title_node else "未知"
        desc_node = soup.select_one(".entry-content") or soup.select_one(".post-content") or soup.select_one(".article-content") or soup.select_one("meta[name='description']")
        vod_content = self._clean_text(desc_node.get("content", "")) if desc_node and getattr(desc_node, "name", "") == "meta" else (self._clean_desc(desc_node.get_text("\n")) if desc_node else vod_name)
        og_img = soup.select_one("meta[property='og:image']")
        imgs = self._extract_images(html_text, soup)
        cover = self._fix_url(og_img.get("content", "")) if og_img else (imgs[0] if imgs else "")
        
        if kind in ["comic", "image"]:
            imgs = imgs or self._extract_images_from_text(html_text)
            play_from = "畫冊全集" if kind == "comic" else "寫真圖集"
            return {"list": [{"vod_id": raw, "vod_name": vod_name, "vod_pic": cover, "vod_content": vod_content, "vod_play_from": play_from, "vod_play_url": "全集$pics@@" + "&&".join(imgs)}]}
        if kind == "novel":
            return {"list": [{"vod_id": raw, "vod_name": vod_name, "vod_pic": cover, "vod_content": vod_content, "vod_play_from": "阅读", "vod_play_url": f"正文$novel@@{vod_name}@@{vid}"}]}
        
        # 提取播放页 URL（让 TVBox 嗅探处理）
        real_id = self._decrypt_mvarr(html_text)
        if not real_id:
            for iframe in soup.select("iframe"):
                src = iframe.get("data-src") or iframe.get("src") or ""
                if "play.php" in src.lower() or "player" in src.lower():
                    match_id = re.search(r'id=([a-zA-Z0-9_-]{15,})', src)
                    if match_id:
                        real_id = match_id.group(1)
                        break
        if not real_id:
            m_play = re.search(r'player/play\.php\?[^"\'<>]*id=([a-zA-Z0-9_-]{15,})', html_text)
            if m_play: real_id = m_play.group(1)
        
        if real_id:
            play_url = self._fix_url(f"/js/player/play.php?numresolution=1080&id={real_id}")
            return {"list": [{"vod_id": raw, "vod_name": vod_name, "vod_pic": cover, "vod_content": vod_content, "vod_play_from": "网页嗅探", "vod_play_url": f"播放$sniff@@{play_url}"}]}
        
        m3u8_list = re.findall(r'(https?://[^"\'\s<>,\\]+?\.m3u8(?:\?[^"\'\s<>]*)?)', html_text, re.I)
        if m3u8_list:
            return {"list": [{"vod_id": raw, "vod_name": vod_name, "vod_pic": cover, "vod_content": vod_content, "vod_play_from": "直链", "vod_play_url": f"播放${self._fix_url(m3u8_list[-1])}"}]}
        
        return {"list": [{"vod_id": raw, "vod_name": vod_name, "vod_pic": cover, "vod_content": vod_content, "vod_play_from": "网页嗅探", "vod_play_url": f"播放$sniff@@{vid}"}]}

    def searchContent(self, key, quick, pg="1"):
        if not key: return {"list": [], "page": int(pg)}
        q = urllib.parse.quote(self._clean_text(key))
        items, max_pagecount = [], int(pg)
        def fetch_type(stype, sname):
            html_text = self._req_html(f"/zh/{stype}_search/all/{q}/{pg}.html")
            if html_text:
                sub_items, pc = self._parse_list(html_text, "video", pg)
                for item in sub_items: item["vod_remarks"] = f"[{sname}] {item.get('vod_remarks', '')}"
                return sub_items, pc
            return [], int(pg)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(fetch_type, k, v) for k, v in {"fc": "视频", "novel": "小说", "doujin": "短篇漫画", "18H": "长篇漫画", "cg": "写真", "cwp": "国产写真"}.items()]
            for future in concurrent.futures.as_completed(futures):
                try:
                    sub_items, pc = future.result()
                    items.extend(sub_items)
                    max_pagecount = max(max_pagecount, pc)
                except: pass
        return {"list": items, "page": int(pg), "pagecount": max_pagecount}

    def _build_tvbox_url(self, play_url, referer):
        """构建 TVBox 播放 URL，header 策略：UA-Only"""
        if not hasattr(self, 'ua'):
            self.init("")
        cookies = self.session.cookies.get_dict()
        if 'YES_Eighteen' not in cookies: 
            cookies['YES_Eighteen'] = 'IamOverEighteenYearsOld'
        if 'javascript_cookie_AgreeTOS_save1' not in cookies: 
            cookies['javascript_cookie_AgreeTOS_save1'] = 'javascript_cookie_AgreeTOS_save2'
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        header_parts = [
            f"User-Agent@{self.ua}",
            f"Cookie@{cookie_str}"
        ]
        if '.m3u8' in play_url:
            header_parts.append(f"Referer@{referer}")
        ext_str = "&&".join(header_parts)
        return f"{play_url};{{{ext_str}}}"

    def playerContent(self, flag, id, vipFlags):
        if not hasattr(self, 'ua'):
            self.init("")
        if id.startswith("iframe_1080@@") or id.startswith("iframe_720@@"):
            url = id.split("@@", 1)[1]
            try:
                res = self.session.get(url, headers={"User-Agent": self.ua, "Referer": self.base_url + "/zh/"}, verify=False, timeout=10)
                if res.status_code == 200:
                    html = res.text
                    # 1. 提取 player_* JSON 配置（支持 encrypt 解密）
                    player_match = re.search(r'(?:var\s+)?player_.*?\s*=\s*({.*?})\s*;', html, re.DOTALL)
                    if player_match:
                        try:
                            config = json.loads(player_match.group(1))
                            play_url = config.get('url', '')
                            encrypt = config.get('encrypt', '0')
                            if play_url:
                                play_url = self._decrypt_play_url(play_url, str(encrypt))
                                if re.search(r'\.(m3u8|mp4)(\?|$)', play_url, re.I):
                                    # 通过 localProxy 代理
                                    proxy_url = f"http://127.0.0.1:9978/proxy?url={play_url}"
                                    return {"parse": 0, "url": proxy_url, "header": {"User-Agent": self.ua}}
                        except:
                            pass
                    # 2. 提取 videoSources 中的 m3u8
                    pattern = r"\{src:\s*['\"]([^'\"]+\.m3u8[^'\"]*)['\"],\s*type:\s*['\"][^'\"]+['\"],\s*size:\s*(\d+)\}"
                    matches = re.findall(pattern, html, re.I)
                    if matches:
                        m3u8_url = None
                        for src, size in matches:
                            if int(size) == 1080:
                                m3u8_url = src
                                break
                        if not m3u8_url:
                            m3u8_url = matches[-1][0]
                        m3u8_url = m3u8_url.replace("\\/", "/")
                        # 通过 localProxy 代理（解密）
                        proxy_url = f"http://127.0.0.1:9978/proxy?url={m3u8_url}"
                        return {"parse": 0, "url": proxy_url, "header": {"User-Agent": self.ua}}
                    # 3. 通用 m3u8 匹配
                    m3u8_list = re.findall(r'(https?://[^"\'\s<>,\\]+?\.m3u8(?:\?[^"\'\s<>]*)?)', html, re.I)
                    if m3u8_list:
                        proxy_url = f"http://127.0.0.1:9978/proxy?url={m3u8_list[-1]}"
                        return {"parse": 0, "url": proxy_url, "header": {"User-Agent": self.ua}}
            except Exception as e:
                self.log({"action": "playerContent_extract_fail", "error": str(e)})
            # 降级：parse:1 让 TVBox 嗅探
            return {"parse": 1, "url": url, "header": {"User-Agent": self.ua, "Referer": self.base_url + "/zh/"}}

        if id.startswith("novel@@"):
            parts = id.replace("novel@@", "", 1).split("@@", 1)
            name, url = parts[0] if len(parts) > 1 else "阅读", parts[1] if len(parts) > 1 else parts[0]
            try:
                html_text = self._req_html(url)
                soup = BeautifulSoup(html_text, "html.parser")
                content = self._extract_novel_text(html_text, soup)
            except Exception as e: 
                content = "内容加载失败: " + str(e)
            return {"parse": 0, "url": "novel://" + json.dumps({"title": name, "content": content}, ensure_ascii=False), "header": ""}

        if id.startswith("pics@@"): return {"parse": 0, "url": "pics://" + id.replace("pics@@", "", 1), "header": ""}
        if id.startswith("direct@@"): 
            m3u8_url = id.replace("direct@@", "", 1)
            proxy_url = f"http://127.0.0.1:9978/proxy?url={m3u8_url}"
            return {"parse": 0, "url": proxy_url, "header": {"User-Agent": self.ua}}
        if id.startswith("sniff@@"): return {"parse": 1, "url": id.replace("sniff@@", "", 1), "header": {"User-Agent": self.ua}}
        return {"parse": 0, "url": id, "header": {"User-Agent": self.ua}}
    def localProxy(self, param):
        """
        本地代理：完整解密方案
        1. m3u8 请求 → 解析并重写分片 URL，指向代理
        2. 密钥请求 → 返回 key.bin
        3. 分片请求 → AES-128 解密 .js → 返回 .ts
        """
        import base64
        from Crypto.Cipher import AES
        
        url = param.get("url", "")
        if not url:
            return [404, "text/plain", "Not Found"]
        
        # ========== 1. 处理密钥请求 ==========
        if "key.bin" in url or "aavv.vv" in url:
            try:
                resp = self.session.get(url, headers={"User-Agent": self.ua, "Referer": self.base_url + "/"}, verify=False, timeout=10)
                if resp.status_code == 200:
                    return [200, "application/octet-stream", resp.content]
            except Exception as e:
                self.log({"action": "localProxy_key_fail", "error": str(e)})
            return [404, "text/plain", "Key not found"]
        
        # ========== 2. 处理 .js 分片请求（解密） ==========
        if ".js" in url and ("_000" in url or "_001" in url or "_002" in url or "_00" in url):
            try:
                # 获取加密的分片数据
                resp = self.session.get(url, headers={"User-Agent": self.ua, "Referer": self.base_url + "/"}, verify=False, timeout=10)
                if resp.status_code != 200:
                    return [404, "text/plain", "Segment not found"]
                
                encrypted_data = resp.content
                
                # 从请求参数或路径中提取 IV
                # IV 在 m3u8 中定义，需要从原始 m3u8 获取
                # 这里通过解析 URL 中的路径信息生成 IV
                iv_str = self._get_iv_from_url(url)
                if iv_str:
                    iv = base64.b16decode(iv_str.upper(), True)
                else:
                    # 默认 IV (全零)
                    iv = b'\x00' * 16
                
                # 获取密钥 (从 session 缓存或请求)
                key = self._get_aes_key()
                if not key:
                    return [404, "text/plain", "Key not available"]
                
                # AES-128 CBC 解密
                cipher = AES.new(key, AES.MODE_CBC, iv)
                try:
                    decrypted = cipher.decrypt(encrypted_data)
                    # 去除 PKCS7 填充
                    pad_len = decrypted[-1]
                    if 1 <= pad_len <= 16:
                        decrypted = decrypted[:-pad_len]
                except Exception as e:
                    # 如果解密失败，返回原始数据（可能是未加密的分片）
                    self.log({"action": "localProxy_decrypt_fail", "error": str(e), "url": url})
                    decrypted = encrypted_data
                
                return [200, "video/MP2T", decrypted]
            except Exception as e:
                self.log({"action": "localProxy_js_fail", "error": str(e), "url": url})
                return [404, "text/plain", "Segment not found"]
        
        # ========== 3. 处理 m3u8 请求 ==========
        if ".m3u8" in url:
            try:
                resp = self.session.get(url, headers={"User-Agent": self.ua, "Referer": self.base_url + "/"}, verify=False, timeout=10)
                if resp.status_code != 200:
                    return [404, "text/plain", "m3u8 not found"]
                
                content = resp.text if hasattr(resp, 'text') else resp.content.decode('utf-8', errors='ignore')
                lines = content.split('\n')
                new_lines = []
                base_url = url.rsplit('/', 1)[0]
                
                # 缓存密钥 URI 和 IV
                key_uri = None
                iv = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 保留注释行，但修改 KEY 的 URI
                    if line.startswith('#'):
                        if line.startswith('#EXT-X-KEY'):
                            # 提取 URI 和 IV
                            uri_match = re.search(r'URI="([^"]+)"', line)
                            iv_match = re.search(r'IV=([^,\s]+)', line)
                            if uri_match:
                                key_uri = uri_match.group(1)
                                if not key_uri.startswith('http'):
                                    key_uri = self._fix_url(key_uri)
                                # 缓存密钥
                                self._cache_aes_key(key_uri)
                            if iv_match:
                                iv = iv_match.group(1)
                                # 缓存 IV
                                self._cache_iv(iv)
                            # 将 KEY URI 改为指向本地代理
                            if key_uri:
                                proxy_key_url = f"http://127.0.0.1:9978/proxy?url={key_uri}"
                                line = line.replace(uri_match.group(1), proxy_key_url)
                            new_lines.append(line)
                        else:
                            new_lines.append(line)
                    else:
                        # 处理分片 URL，改为指向本地代理
                        if not line.startswith('http'):
                            line = base_url + '/' + line
                        # 将 .js 分片改为指向代理
                        if '.js' in line:
                            proxy_url = f"http://127.0.0.1:9978/proxy?url={line}"
                            new_lines.append(proxy_url)
                        else:
                            new_lines.append(line)
                
                return [200, "application/vnd.apple.mpegurl", '\n'.join(new_lines)]
            except Exception as e:
                self.log({"action": "localProxy_m3u8_fail", "error": str(e)})
                return [404, "text/plain", "m3u8 proxy failed"]
        
        # ========== 4. 其他请求：直接代理 ==========
        try:
            resp = self.session.get(url, headers={"User-Agent": self.ua, "Referer": self.base_url + "/"}, verify=False, timeout=10)
            if resp.status_code == 200:
                return [200, "application/octet-stream", resp.content]
        except:
            pass
        
        return [404, "text/plain", "Not Found"]
    
    def _get_aes_key(self):
        """获取缓存的 AES 密钥"""
        if hasattr(self, '_aes_key'):
            return self._aes_key
        return None
    
    def _cache_aes_key(self, key_uri):
        """缓存 AES 密钥"""
        try:
            resp = self.session.get(key_uri, headers={"User-Agent": self.ua, "Referer": self.base_url + "/"}, verify=False, timeout=10)
            if resp.status_code == 200:
                self._aes_key = resp.content
                self.log({"action": "cache_aes_key", "status": "success", "size": len(resp.content)})
                return True
        except Exception as e:
            self.log({"action": "cache_aes_key", "error": str(e)})
        return False
    
    def _cache_iv(self, iv_str):
        """缓存 IV"""
        self._iv = iv_str
        self.log({"action": "cache_iv", "iv": iv_str})
    
    def _get_iv_from_url(self, url):
        """从 URL 中提取 IV"""
        # 优先使用缓存的 IV
        if hasattr(self, '_iv') and self._iv:
            return self._iv
        # 从 URL 路径中提取
        match = re.search(r'[^/]+_(\d+)\.js', url)
        if match:
            seq = int(match.group(1))
            # IV 为 16 字节的序列号
            return seq.to_bytes(16, 'big').hex()
        return None
    def isVideoFormat(self, url): pass
    def manualVideoCheck(self): pass
    def destroy(self):
        try: self.session.close()
        except: pass