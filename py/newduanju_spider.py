# 新短剧网 Spider (newduanju.com)
import re
import urllib.parse
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

class Spider:
    def __init__(self):
        self.site_url = "https://newduanju.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': self.site_url
        }
        
        # 分类列表
        self.categories = [
            {"type_id": "1", "type_name": "短剧", "url": "/duanju/duanju.html"},
            {"type_id": "2", "type_name": "漫剧", "url": "/manju/manju.html"},
            {"type_id": "3", "type_name": "重生民国", "url": "/duanju/chongsheng.html"},
            {"type_id": "4", "type_name": "穿越现代", "url": "/duanju/chuanyue.html"},
            {"type_id": "5", "type_name": "反转爽剧", "url": "/duanju/fanzhuan.html"},
            {"type_id": "6", "type_name": "言情总裁", "url": "/duanju/yanqing.html"},
            {"type_id": "7", "type_name": "现代都市", "url": "/duanju/dushi.html"},
            {"type_id": "8", "type_name": "古装仙侠", "url": "/duanju/guzhuang.html"},
            {"type_id": "9", "type_name": "悬疑烧脑", "url": "/duanju/xuanyi.html"},
            {"type_id": "10", "type_name": "恋爱漫剧", "url": "/manju/lianai.html"},
            {"type_id": "11", "type_name": "玄幻武侠", "url": "/manju/xuanhuan.html"},
            {"type_id": "12", "type_name": "末世重生", "url": "/manju/moshi.html"},
            {"type_id": "13", "type_name": "穿越漫剧", "url": "/manju/chuanyue.html"},
            {"type_id": "14", "type_name": "科幻未来", "url": "/manju/keihuan.html"},
            {"type_id": "15", "type_name": "惊悚恐怖", "url": "/manju/jingsong.html"},
            {"type_id": "16", "type_name": "系统脑洞", "url": "/manju/xitong.html"},
            {"type_id": "17", "type_name": "家庭伦理", "url": "/manju/jiating.html"},
        ]

    def init(self, cfg=None):
        pass

    def getDependence(self):
        return []

    def _fetch_direct(self, url):
        import urllib.request
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return None

    def _parse_html(self, html):
        try:
            return BeautifulSoup(html, 'html.parser')
        except:
            return None

    def fix_url(self, url):
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        return urljoin(self.site_url, url)

    def extract_vod_list(self, html):
        result = []
        seen = set()
        if not html:
            return result
        
        soup = self._parse_html(html)
        if soup:
            items = soup.select('.module-item, .module-items .module-item, .module-list .module-item')
        else:
            items = re.findall(r'<div[^>]*class="[^"]*module-item[^"]*"[^>]*>(.*?)</div>\s*(?=<div|<a|</section|</main)', html, re.DOTALL)
        
        for item in items:
            try:
                if hasattr(item, 'select_one'):
                    # BeautifulSoup对象
                    a_tag = item.select_one('a')
                    if not a_tag:
                        continue
                    url = self.fix_url(a_tag.get('href', ''))
                    title = a_tag.get('title', '') or a_tag.text.strip()
                    if not title:
                        title_tag = item.select_one('.module-item-title')
                        if title_tag:
                            title = title_tag.text.strip()
                    
                    img_tag = item.select_one('img')
                    pic = ''
                    if img_tag:
                        pic = img_tag.get('data-original') or img_tag.get('src', '')
                        pic = self.fix_url(pic) if pic else ''
                    
                    remark_tag = item.select_one('.module-item-text')
                    remark = remark_tag.text.strip() if remark_tag else ''
                else:
                    # 正则匹配
                    a_match = re.search(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>', item)
                    if not a_match:
                        continue
                    url = self.fix_url(a_match.group(1))
                    
                    title = ""
                    title_match = re.search(r'<a[^>]*title=["\']([^"\']+)["\']', item)
                    if title_match:
                        title = title_match.group(1).strip()
                    if not title:
                        title_match2 = re.search(r'class="[^"]*module-item-title[^"]*"[^>]*>(.*?)</a>', item, re.DOTALL)
                        if title_match2:
                            title = re.sub(r'<[^>]+>', '', title_match2.group(1)).strip()
                    
                    pic = ""
                    img_match = re.search(r'<img[^>]*data-original=["\']([^"\']+)["\']', item)
                    if img_match:
                        pic = self.fix_url(img_match.group(1))
                    if not pic:
                        img_match2 = re.search(r'<img[^>]*src=["\']([^"\']+)["\']', item)
                        if img_match2 and 'load.png' not in img_match2.group(1):
                            pic = self.fix_url(img_match2.group(1))
                    
                    remark = ""
                    remark_match = re.search(r'class="[^"]*module-item-text[^"]*"[^>]*>(.*?)</div>', item, re.DOTALL)
                    if remark_match:
                        remark = re.sub(r'<[^>]+>', '', remark_match.group(1)).strip()
                
                if not title or "测试" in title or "test" in title.lower():
                    continue
                if url in seen:
                    continue
                seen.add(url)
                
                result.append({
                    "vod_id": url,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_remarks": remark
                })
            except:
                continue
        return result

    def homeContent(self, filter=False):
        result = {"class": [], "list": []}
        for cat in self.categories:
            result["class"].append({
                "type_id": cat["type_id"],
                "type_name": cat["type_name"]
            })
        html = self._fetch_direct(self.site_url + "/")
        if html:
            result["list"] = self.extract_vod_list(html)
        return result

    def homeVideoContent(self):
        return self.homeContent(filter=False)

    def categoryContent(self, tid, pg=1, filter=False, extend={}):
        p = int(pg) if pg else 1
        
        url_path = ""
        for cat in self.categories:
            if cat["type_id"] == str(tid):
                url_path = cat["url"]
                break
        if not url_path:
            return {"list": []}
        
        # 构建分页URL
        if p > 1:
            url = self.site_url + url_path + "?page=" + str(p)
        else:
            url = self.site_url + url_path
        
        html = self._fetch_direct(url)
        if not html:
            return {"list": []}
        
        vod_list = self.extract_vod_list(html)
        
        # 提取总页数 - 从分页控件中解析
        pagecount = p
        soup = self._parse_html(html)
        if soup:
            # 查找所有分页数字
            page_items = soup.select('#page a, #page span, .page-number')
            for item in page_items:
                text = item.text.strip()
                if text.isdigit():
                    try:
                        num = int(text)
                        if num > pagecount:
                            pagecount = num
                    except:
                        pass
            # 如果还是没有，尝试从"尾页"链接提取
            if pagecount == p:
                last_link = soup.select_one('a[href*="page="]:contains("尾页")')
                if last_link:
                    href = last_link.get('href', '')
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        pagecount = int(match.group(1))
        
        return {
            "list": vod_list,
            "page": p,
            "pagecount": pagecount,
            "limit": 20,
            "total": pagecount * 20
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        
        url = ids[0]
        if not url.startswith("http"):
            url = self.fix_url(url)
        
        html = self._fetch_direct(url)
        if not html:
            return {"list": []}
        
        soup = self._parse_html(html) if html else None
        
        # 提取标题
        title = ""
        if soup:
            h1 = soup.select_one('h1.page-title')
            if h1:
                title = h1.text.strip()
        if not title:
            h1_match = re.search(r'<h1[^>]*class="[^"]*page-title[^"]*"[^>]*>(.*?)</h1>', html)
            if h1_match:
                title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
        if not title:
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
            if title_match:
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        
        # 提取封面
        pic = ""
        if soup:
            img = soup.select_one('img[data-original]')
            if img:
                pic = self.fix_url(img.get('data-original', ''))
        if not pic:
            img_match = re.search(r'<img[^>]*data-original=["\']([^"\']+)["\']', html)
            if img_match:
                pic = self.fix_url(img_match.group(1))
        
        # 提取简介
        desc = ""
        if soup:
            desc_tag = soup.select_one('.video-info-content, .vod-content, .module-desc')
            if desc_tag:
                desc = desc_tag.text.strip()
        if not desc:
            desc_match = re.search(r'<div[^>]*class="[^"]*video-info-content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            if desc_match:
                desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
                desc = re.sub(r'<a[^>]*>.*?</a>', '', desc).strip()
        
        # 从详情页URL提取视频ID
        vid_match = re.search(r'/(duanjuxq|manjuxq)/(\d+)', url)
        video_id = vid_match.group(2) if vid_match else None
        prefix = vid_match.group(1).replace('juxq', 'ju') if vid_match else 'duanju'
        
        # 提取总集数
        total_episodes = 80
        if soup:
            text = soup.text
        else:
            text = html
        total_match = re.search(r'(\d+)集', text)
        if total_match:
            total_episodes = int(total_match.group(1))
        else:
            remark_match = re.search(r'备注[：:]\s*(\d+)集', text)
            if remark_match:
                total_episodes = int(remark_match.group(1))
            else:
                ep_count_match = re.search(r'共(\d+)集', text)
                if ep_count_match:
                    total_episodes = int(ep_count_match.group(1))
        
        if total_episodes > 200:
            total_episodes = 80
        
        # 构造剧集列表
        episodes = []
        for i in range(1, total_episodes + 1):
            play_url = f"{self.site_url}/{prefix}/{video_id}/play-{i}-1.html"
            episodes.append({"name": f"第{i}集", "href": play_url})
        
        if not video_id or not episodes:
            episodes = []
            ep_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?<span>(第?\d+集?)</span>', html, re.DOTALL)
            for href, name in ep_links:
                ep_link = self.fix_url(href)
                if ep_link and ep_link != self.site_url and ep_link != self.site_url + "/":
                    episodes.append({"name": name.strip(), "href": ep_link})
        
        if not episodes:
            episodes = [{"name": "播放", "href": url}]
        
        play_url_parts = []
        for ep in episodes:
            play_url_parts.append(ep["name"] + "$" + ep["href"])
        
        return {"list": [{
            "vod_id": url,
            "vod_name": title or "未知片名",
            "vod_pic": pic,
            "vod_play_from": "新短剧网",
            "vod_play_url": "#".join(play_url_parts),
            "vod_content": desc or "暂无简介"
        }]}

    def searchContent(self, key, quick=False, pg=1):
        p = int(pg) if pg else 1
        encoded = urllib.parse.quote(key)
        url = self.site_url + "/search?wd=" + encoded + "&page=" + str(p)
        html = self._fetch_direct(url)
        if not html:
            return {"list": []}
        return {"list": self.extract_vod_list(html)}

    def playerContent(self, flag, id, vipFlags=[]):
        html = self._fetch_direct(id)
        if not html:
            return {"parse": 0, "playUrl": id}
        
        iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html)
        if iframe_match:
            iframe_src = iframe_match.group(1)
            if '/player.php' in iframe_src:
                url_param_match = re.search(r'url=([^&]+)', iframe_src)
                if url_param_match:
                    video_url = unquote(url_param_match.group(1))
                    if video_url.startswith('http'):
                        return {"parse": 0, "playUrl": video_url}
        
        data_play_match = re.search(r'data-play=["\']([^"\']+)["\']', html)
        if data_play_match:
            play_path = data_play_match.group(1)
            url_param_match = re.search(r'url=([^&]+)', play_path)
            if url_param_match:
                video_url = unquote(url_param_match.group(1))
                if video_url.startswith('http'):
                    return {"parse": 0, "playUrl": video_url}
        
        return {"parse": 1, "playUrl": id}