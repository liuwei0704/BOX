import sys
import requests
import re
import json
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class Spider():
    def __init__(self):
        self.host = "https://wuu420.wunv.top"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': self.host,
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

    def getName(self):
        return "W女大王|wunv.top"

    def getDependence(self):
        return []

    def init(self, extend=""):
        try:
            self.session.get(self.host, headers=self.headers, timeout=5)
        except:
            pass

    def homeContent(self, filter):
        result = {'class': [], 'list': []}
        try:
            res = self.session.get(self.host, headers=self.headers)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 提取分类
            class_selectors = ['.row-item-content li a', '.menuInfo-row .item a']
            type_set = set()
            for selector in class_selectors:
                for a in soup.select(selector):
                    href = a.get('href', '')
                    name = a.text.strip()
                    if name and href:
                        match = re.search(r'/vodtype/(\d+)\.html', href)
                        if match:
                            type_id = match.group(1)
                            if name not in [c['type_name'] for c in result['class']]:
                                result['class'].append({"type_name": name, "type_id": type_id})
                                type_set.add(name)
            
            # 提取首页视频 - 通用方法
            result['list'] = self.parse_vod_links(soup)[:12]
                
        except Exception as e:
            print(f"homeContent error: {e}")
            if 'class' not in result:
                result['class'] = []
            if 'list' not in result:
                result['list'] = []
        
        return result

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.host}/vodtype/{tid}.html?page={pg}"
        v_list = []
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                res.encoding = 'utf-8'
                soup = BeautifulSoup(res.text, 'html.parser')
                v_list = self.parse_vod_links(soup)
        except Exception as e:
            print(f"categoryContent error: {e}")
        
        # 备用URL格式
        if not v_list:
            url2 = f"{self.host}/vodtype/{tid}-{pg}.html"
            try:
                res = self.session.get(url2, headers=self.headers, timeout=10)
                if res.status_code == 200:
                    res.encoding = 'utf-8'
                    soup = BeautifulSoup(res.text, 'html.parser')
                    v_list = self.parse_vod_links(soup)
            except:
                pass
        
        return {
            "list": v_list,
            "page": int(pg),
            "pagecount": 9999,
            "limit": len(v_list),
            "total": 999999
        }

    def parse_vod_links(self, soup):
        """通用视频链接解析 - 查找所有指向 /voddetail/ 的链接"""
        video_list = []
        seen_ids = set()
        
        # 查找所有包含 /voddetail/ 的 a 标签
        all_links = soup.find_all('a', href=re.compile(r'/voddetail/'))
        
        for a in all_links:
            try:
                href = a.get('href', '')
                if not href:
                    continue
                
                # 尝试获取标题
                title = a.get('title') or a.text.strip()
                if not title:
                    # 查找相邻的图片alt属性
                    img = a.find('img')
                    if img:
                        title = img.get('alt', '')
                
                title = self.clean_title(title)
                if not title or len(title) < 2:
                    continue
                
                # 查找图片 - 可能在a内部，也可能在父级
                img = a.find('img')
                if not img:
                    # 向上查找父级中的图片
                    parent = a.parent
                    for _ in range(3):
                        if parent:
                            img = parent.find('img')
                            if img:
                                break
                            parent = parent.parent
                
                pic = ''
                if img:
                    pic = img.get('data-original') or img.get('data-src') or img.get('src') or ''
                
                if pic and not pic.startswith('http'):
                    pic = urljoin(self.host, pic)
                
                # 查找备注
                remarks = ''
                parent_elem = a.parent
                for _ in range(3):
                    if parent_elem:
                        remark_elem = parent_elem.select_one('.remarks, .pic-text, .module-item-caption, .score, .hint, .duration')
                        if remark_elem:
                            remarks = remark_elem.text.strip()
                            break
                        parent_elem = parent_elem.parent
                
                vod_id = href
                if vod_id not in seen_ids:
                    seen_ids.add(vod_id)
                    video_list.append({
                        "vod_id": vod_id,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": remarks
                    })
            except:
                continue
        
        return video_list

    def clean_title(self, title):
        title = re.sub(r'(-|\||_)?(電影|剧集|动漫|綜藝|免费|高清|在线|观看|无码|中文字幕)?線上看.*', '', title)
        title = re.sub(r'\s+', ' ', title)
        return title.strip()

    def detailContent(self, ids):
        if isinstance(ids, list):
            vid = ids[0]
        else:
            vid = str(ids)
        
        if not vid.startswith('http'):
            if vid.startswith('/'):
                url = self.host + vid
            else:
                url = f"{self.host}/voddetail/{vid}.html"
        else:
            url = vid
        
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            title = ""
            if soup.title:
                title = soup.title.text.split('-')[0].strip()
            
            from_list = []
            url_list = []
            
            # 查找所有播放链接
            play_links = soup.find_all('a', href=re.compile(r'/vodplay/'))
            if play_links:
                links = []
                for a in play_links:
                    ep_name = a.text.strip() or "播放"
                    ep_href = a.get('href')
                    if ep_href:
                        if not ep_href.startswith('http'):
                            ep_href = urljoin(self.host, ep_href)
                        links.append(f"{ep_name}${ep_href}")
                if links:
                    from_list.append("默认线路")
                    url_list.append("#".join(links))
            
            vod_info = {
                "vod_id": vid,
                "vod_name": self.clean_title(title),
                "vod_play_from": "$$$".join(from_list) if from_list else "默认线路",
                "vod_play_url": "$$$".join(url_list) if url_list else "",
                "type_name": "",
                "vod_pic": "",
                "vod_area": "",
                "vod_lang": "",
                "vod_year": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
            }
            
            # 提取图片
            img = soup.find('img', src=re.compile(r'\.(jpg|png|jpeg)'))
            if img:
                pic = img.get('data-original') or img.get('src') or ''
                if pic and not pic.startswith('http'):
                    pic = urljoin(self.host, pic)
                vod_info['vod_pic'] = pic
            
            return {"list": [vod_info]}
            
        except Exception as e:
            print(f"detailContent error: {e}")
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        search_url = f"{self.host}/vodsearch/-------------.html?wd={key}&page={pg}"
        v_list = []
        try:
            res = self.session.get(search_url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                res.encoding = 'utf-8'
                soup = BeautifulSoup(res.text, 'html.parser')
                v_list = self.parse_vod_links(soup)
        except Exception as e:
            print(f"searchContent error: {e}")
        
        return {
            "list": v_list,
            "page": int(pg),
            "pagecount": 9999,
            "limit": len(v_list),
            "total": len(v_list) * 10 if v_list else 0
        }

    def playerContent(self, flag, id, vipFlags):
        try:
            if id.startswith('http') and ('.m3u8' in id or '.mp4' in id):
                return {"parse": 0, "url": id, "header": json.dumps(self.headers)}
            
            if not id.startswith('http'):
                if id.startswith('/'):
                    play_url = self.host + id
                else:
                    play_url = f"{self.host}/vodplay/{id}.html"
            else:
                play_url = id
            
            res = self.session.get(play_url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            
            # 搜索 m3u8/mp4
            m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', res.text)
            if m3u8_match:
                return {"parse": 0, "url": m3u8_match.group(0), "header": json.dumps(self.headers)}
            
            mp4_match = re.search(r'https?://[^\s"\']+\.mp4[^\s"\']*', res.text)
            if mp4_match:
                return {"parse": 0, "url": mp4_match.group(0), "header": json.dumps(self.headers)}
            
            return {"parse": 1, "url": play_url, "header": json.dumps(self.headers)}
            
        except Exception as e:
            print(f"playerContent error: {e}")
            return {"parse": 0, "url": "", "header": ""}

    def localProxy(self, param):
        return {"code": 404, "content": b""}