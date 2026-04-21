import sys, requests, re, json, base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, quote

class Spider():
    def __init__(self):
        self.host = "https://186416.xyz"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': self.host,
        }

    def getName(self):
        return "18CM视频站"

    # --- 依赖声明 ---
    def getDependence(self):
        return []

    def init(self, extend=""):
        try: 
            self.session.get(self.host, headers=self.headers, timeout=5)
        except: 
            pass

    # --- 首页内容：分类 + 推荐视频 ---
    def homeContent(self, filter):
        result = {
            'class': [
                {"type_name": "全部", "type_id": ""},
                {"type_name": "国产", "type_id": "%e5%9c%8b%e7%94%a2av/"},
                {"type_name": "网红", "type_id": "%e9%a1%94%e5%80%bc%e7%b6%b2%e7%b4%85/"},
                {"type_name": "探花", "type_id": "%e6%8e%a2%e8%8a%b1%e7%b4%84%e7%82%ae/"},
                {"type_name": "日韩", "type_id": "%e6%97%a5%e9%9f%93%e8%a6%96%e9%a0%bb/"},
                {"type_name": "中字", "type_id": "%e4%b8%ad%e6%96%87%e5%ad%97%e5%b9%95/"},
                {"type_name": "主播", "type_id": "%e4%b8%bb%e6%92%ad%e7%9b%b4%e6%92%ad/"},
                {"type_name": "FC2", "type_id": "fc2/"},
                {"type_name": "动漫", "type_id": "%e5%8b%95%e6%bc%ab/"},
                {"type_name": "嫩妹", "type_id": "%e5%ab%a9%e5%a6%b9/"},
                {"type_name": "欧美", "type_id": "%e6%ad%90%e7%be%8e/"},
            ]
        }
        # 获取首页推荐视频
        try:
            res = self.session.get(self.host, headers=self.headers)
            res.encoding = 'utf-8'
            v_list = self.parseHomeList(res.text)
            result['list'] = v_list
        except:
            result['list'] = []
        return result

    def homeVideoContent(self):
        return self.homeContent(False)

    # --- 解析首页视频列表 ---
    def parseHomeList(self, html):
        video_list = []
        soup = BeautifulSoup(html, 'html.parser')
        # 首页视频在 article.post 容器中
        items = soup.select('article.post')
        for item in items:
            try:
                a = item.find('a', href=True)
                if not a: 
                    continue
                title_elem = item.select_one('.entry-title a') or a
                raw_name = title_elem.get('title') or title_elem.text.strip()
                name = re.sub(r'[-|_\s]*(18CM|18cm|免费|高清|在线|观看|完整版|无码).*$', '', raw_name, flags=re.I).strip()
                
                img = item.find('img')
                pic = img.get('data-src') or img.get('src') or ''
                if pic and not pic.startswith('http'):
                    pic = urljoin(self.host, pic)
                
                # 获取播放次数/备注
                views_elem = item.select_one('.views, .meta-views, .entry-meta span')
                remarks = views_elem.text.strip() if views_elem else ''
                
                video_list.append({
                    "vod_id": a['href'],
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": remarks
                })
            except:
                continue
        
        # 去重
        seen = set()
        res_list = []
        for v in video_list:
            if v['vod_id'] not in seen:
                res_list.append(v)
                seen.add(v['vod_id'])
        return res_list

    # --- 分类列表 ---
    def categoryContent(self, tid, pg, filter, extend):
        # tid 为分类ID，pg 为页码
        if tid:
            url = urljoin(self.host, f"/{tid}page/{pg}/")
        else:
            url = urljoin(self.host, f"/page/{pg}/")
        
        try:
            res = self.session.get(url, headers=self.headers)
            res.encoding = 'utf-8'
            v_list = self.parseCategoryList(res.text)
            return {
                "list": v_list,
                "page": int(pg),
                "pagecount": 99,
                "limit": len(v_list),
                "total": 999
            }
        except Exception as e:
            return {"list": [], "page": int(pg)}

    def parseCategoryList(self, html):
        video_list = []
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('article.post')
        for item in items:
            try:
                a = item.find('a', href=True)
                if not a:
                    continue
                title_elem = item.select_one('.entry-title a') or a
                raw_name = title_elem.get('title') or title_elem.text.strip()
                name = re.sub(r'[-|_\s]*(18CM|18cm|免费|高清|在线|观看|完整版|无码).*$', '', raw_name, flags=re.I).strip()
                
                img = item.find('img')
                pic = img.get('data-src') or img.get('src') or ''
                if pic and not pic.startswith('http'):
                    pic = urljoin(self.host, pic)
                
                video_list.append({
                    "vod_id": a['href'],
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": ""
                })
            except:
                continue
        
        seen = set()
        res_list = []
        for v in video_list:
            if v['vod_id'] not in seen:
                res_list.append(v)
                seen.add(v['vod_id'])
        return res_list

    # --- 搜索 ---
    def searchContent(self, key, quick, pg=1):
        search_url = urljoin(self.host, f"/?s={quote(key)}")
        try:
            res = self.session.get(search_url, headers=self.headers)
            res.encoding = 'utf-8'
            v_list = self.parseCategoryList(res.text)
            return {"list": v_list}
        except:
            return {"list": []}

    # --- 详情页 ---
    def detailContent(self, ids):
        url = ids[0] if ids[0].startswith('http') else urljoin(self.host, ids[0])
        try:
            res = self.session.get(url, headers=self.headers)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 标题
            title_elem = soup.select_one('.entry-title')
            vod_name = title_elem.text.strip() if title_elem else "未知标题"
            
            # 封面
            img = soup.select_one('.post-thumbnail img, .entry-content img')
            vod_pic = img.get('src') or img.get('data-src') or ''
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = urljoin(self.host, vod_pic)
            
            # 描述
            desc_elem = soup.select_one('.entry-content p, .video-description')
            vod_content = desc_elem.text.strip() if desc_elem else ""
            
            # 播放源解析：从iframe的q参数中提取真实地址
            play_url = ""
            iframe = soup.select_one('.video-player iframe')
            if iframe:
                iframe_src = iframe.get('src', '')
                # 提取q参数
                q_match = re.search(r'q=([^&]+)', iframe_src)
                if q_match:
                    try:
                        q_value = q_match.group(1)
                        decoded = base64.b64decode(q_value).decode('utf-8')
                        from urllib.parse import unquote
                        video_html = unquote(decoded)
                        # 从video HTML中提取src
                        src_match = re.search(r'src="([^"]+)"', video_html)
                        if src_match:
                            play_url = src_match.group(1)
                    except:
                        pass
            
            # 演员/分类信息
            tags = [t.text.strip() for t in soup.select('.entry-tags a, .tags-links a')]
            vod_actor = ','.join(tags[:5]) if tags else ""
            
            vod_list = [{
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_actor": vod_actor,
                "vod_play_from": "18CM",
                "vod_play_url": f"正片${play_url}" if play_url else "正片$"
            }]
            return {"list": vod_list}
        except Exception as e:
            return {"list": []}

    # --- 播放地址解析 ---
    def playerContent(self, flag, id, vipFlags):
        # id 为播放地址 URL
        if id.startswith('http'):
            return {"url": id}
        return {"url": urljoin(self.host, id)}