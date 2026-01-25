# coding=utf-8
import sys
import os
import re
import json
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup

class Spider(Spider):
    def getName(self):
        return "貝貝影院"

    def init(self, extend=""):
        self.host = "https://www.beibei133.com"
        pass

    def header(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
            'Referer': self.host
        }

    def homeContent(self, filter):
        result = {}
        classes = [
            {"type_name": "電影", "type_id": "/mianfei/dianying/"},
            {"type_name": "電視劇", "type_id": "/mianfei/lianxuju/"},
            {"type_name": "動漫", "type_id": "/mianfei/dongman/"},
            {"type_name": "綜藝", "type_id": "/mianfei/zongyi/"}
        ]
        result["class"] = classes
        return result

    def homeVideoContent(self):
        rsp = self.fetch(self.host, headers=self.header())
        root = BeautifulSoup(rsp.text, 'html.parser')
        videos = []
        
        items = root.select('ul.img-list li')
        for item in items:
            a = item.find('a')
            if not a:
                continue
                
            img = item.find('img')
            if not img or 'src' not in img.attrs:
                continue
                
            vod_name = a.get('title', '')
            if not vod_name and a.find('h2'):
                vod_name = a.find('h2').text
            
            vod_pic = img['src']
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
            
            vod_remarks = item.find('i').text if item.find('i') else ""
            
            vod_id = a.get('href', '')
            if vod_id and not vod_id.startswith('http'):
                vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
            
            videos.append({
                "vod_id": vod_id,
                "vod_name": vod_name.strip(),
                "vod_pic": vod_pic,
                "vod_remarks": vod_remarks
            })
        return {"list": videos}

    def categoryContent(self, tid, pg, filter, extend):
        if int(pg) > 1:
            url = f"{self.host}{tid}index_{pg}.html"
        else:
            url = f"{self.host}{tid}"
            
        try:
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            items = root.select('ul.img-list li')
            for item in items:
                a = item.find('a')
                if not a:
                    continue
                    
                img = item.find('img')
                if not img or 'src' not in img.attrs:
                    continue
                
                vod_name = a.get('title', '')
                if not vod_name:
                    h2 = a.find('h2')
                    if h2:
                        vod_name = h2.text
                    else:
                        vod_name = a.text.strip()
                
                vod_pic = img['src']
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
                
                vod_remarks = item.find('i').text if item.find('i') else ""
                
                vod_id = a.get('href', '')
                if vod_id and not vod_id.startswith('http'):
                    vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name.strip(),
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })
            
            # 尝试获取总页数
            pagecount = 999
            page_div = root.find('div', class_='page')
            if page_div:
                page_links = page_div.find_all('a')
                if page_links:
                    last_page = 1
                    for link in page_links:
                        try:
                            num = int(link.text.strip())
                            if num > last_page:
                                last_page = num
                        except:
                            pass
                    pagecount = last_page
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 20,
                "total": 9999
            }
        except Exception as e:
            print(f"分类页面解析错误: {e}")
            return {
                "list": [],
                "page": int(pg),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }

    def detailContent(self, ids):
        try:
            vod_id = ids[0]
            if not vod_id.startswith('http'):
                if vod_id.startswith('/'):
                    url = self.host + vod_id
                else:
                    url = self.host + '/' + vod_id
            else:
                url = vod_id
            
            rsp = self.fetch(url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 获取影片名称
            vod_name = "未知"
            h1_tag = root.find('h1')
            if h1_tag:
                vod_name = h1_tag.text.strip()
            
            # 获取影片图片
            vod_pic = ""
            detail_pic = root.find('div', class_='detail-pic')
            if detail_pic:
                img_tag = detail_pic.find('img')
                if img_tag and 'src' in img_tag.attrs:
                    vod_pic = img_tag['src']
                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
            
            # 获取影片描述（剧情介绍）
            vod_content = ""
            desc_div = root.find('div', class_='tjuqing')
            if desc_div:
                p_tag = desc_div.find('p')
                if p_tag:
                    vod_content = p_tag.text.strip()
            
            # 获取年份、主演等信息
            vod_year = ""
            vod_actor = ""
            vod_director = ""
            vod_area = ""
            
            info_div = root.find('div', class_='detail-info')
            if info_div:
                # 查找所有dl标签
                dl_tags = info_div.find_all('dl')
                for dl in dl_tags:
                    dt = dl.find('dt')
                    dd = dl.find('dd')
                    if dt and dd:
                        label = dt.text.strip()
                        value = dd.text.strip()
                        if '年份' in label:
                            vod_year = value
                        elif '主演' in label:
                            vod_actor = value
                        elif '导演' in label:
                            vod_director = value
                        elif '类型' in label or '地区' in label:
                            vod_area = value
            
            # 解析播放源和播放列表
            play_sections = root.find_all('div', class_='down-title')
            
            play_from_list = []
            play_url_list = []
            
            # 优先查找"貝貝影院-電影資源2"这条线路
            default_source = "貝貝影院-電影資源2"
            found_default = False
            
            for section in play_sections:
                h2 = section.find('h2')
                if not h2:
                    continue
                    
                play_source_name = h2.text.strip()
                # 清理播放源名称
                if "永久免费" in play_source_name:
                    play_source_name = play_source_name.split("-永久免费")[0].strip()
                
                # 檢查是否是默認線路
                is_default = False
                if "電影資源2" in play_source_name or "电影资源2" in play_source_name:
                    play_source_name = "貝貝影院-電影資源2"
                    is_default = True
                
                # 查找下一个video_list div
                next_elem = section.find_next_sibling()
                video_list_div = None
                
                # 查找下一个video_list div，最多查找5个兄弟元素
                for _ in range(5):
                    if next_elem and hasattr(next_elem, 'get') and next_elem.get('class'):
                        if 'video_list' in next_elem.get('class'):
                            video_list_div = next_elem
                            break
                    if next_elem:
                        next_elem = next_elem.find_next_sibling()
                    else:
                        break
                
                if not video_list_div:
                    continue
                
                # 收集所有播放链接
                episode_links = []
                for a_tag in video_list_div.find_all('a'):
                    href = a_tag.get('href', '')
                    title = a_tag.text.strip()
                    
                    if href and title:
                        # 确保是完整的URL
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                href = self.host + href
                            else:
                                href = self.host + '/' + href
                        
                        # 清理标题中的特殊字符
                        title = title.replace('$', '').replace('#', '')
                        episode_links.append(f"{title}${href}")
                
                if episode_links:
                    # 如果是默认线路，放在第一位
                    if is_default:
                        play_from_list.insert(0, play_source_name)
                        play_url_list.insert(0, "#".join(episode_links))
                        found_default = True
                    else:
                        play_from_list.append(play_source_name)
                        play_url_list.append("#".join(episode_links))
            
            # 如果没有找到默认线路，尝试查找其他线路作为备用
            if not found_default:
                # 重新查找所有播放源，优先使用"貝貝影院"开头的线路
                temp_from_list = []
                temp_url_list = []
                
                for section in root.find_all('div', class_='down-title'):
                    h2 = section.find('h2')
                    if not h2:
                        continue
                    
                    play_source_name = h2.text.strip()
                    if "永久免费" in play_source_name:
                        play_source_name = play_source_name.split("-永久免费")[0].strip()
                    
                    # 查找播放列表
                    video_list_div = None
                    next_elem = section.find_next_sibling()
                    for _ in range(5):
                        if next_elem and hasattr(next_elem, 'get') and next_elem.get('class'):
                            if 'video_list' in next_elem.get('class'):
                                video_list_div = next_elem
                                break
                        if next_elem:
                            next_elem = next_elem.find_next_sibling()
                        else:
                            break
                    
                    if not video_list_div:
                        continue
                    
                    # 收集播放链接
                    episode_links = []
                    for a_tag in video_list_div.find_all('a'):
                        href = a_tag.get('href', '')
                        title = a_tag.text.strip()
                        
                        if href and title:
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = self.host + href
                                else:
                                    href = self.host + '/' + href
                            
                            title = title.replace('$', '').replace('#', '')
                            episode_links.append(f"{title}${href}")
                    
                    if episode_links:
                        # 优先使用"貝貝影院"开头的线路
                        if play_source_name.startswith("貝貝影院"):
                            temp_from_list.insert(0, play_source_name)
                            temp_url_list.insert(0, "#".join(episode_links))
                        else:
                            temp_from_list.append(play_source_name)
                            temp_url_list.append("#".join(episode_links))
                
                if temp_from_list:
                    play_from_list = temp_from_list
                    play_url_list = temp_url_list
            
            # 如果没有找到播放源，尝试其他方式
            if not play_from_list:
                # 尝试查找所有播放链接
                all_play_links = root.find_all('a', href=re.compile(r'/index\.php/vod/play/'))
                if all_play_links:
                    episode_links = []
                    for a_tag in all_play_links[:20]:  # 只取前20个
                        href = a_tag.get('href', '')
                        title = a_tag.text.strip()
                        
                        if href and title:
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = self.host + href
                                else:
                                    href = self.host + '/' + href
                            
                            title = title.replace('$', '').replace('#', '')
                            if not title:
                                title = f"第{len(episode_links)+1}集"
                            
                            episode_links.append(f"{title}${href}")
                    
                    if episode_links:
                        play_from_list = ["貝貝影院"]
                        play_url_list = ["#".join(episode_links)]
            
            # 如果还是没有找到播放源，添加默认的
            if not play_from_list:
                play_from_list = ["貝貝影院"]
                play_url_list = [f"第1集${url}"]
            
            # 构建完整的影片信息
            video = {
                "vod_id": ids[0],
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_content": vod_content,
                "vod_year": vod_year,
                "vod_actor": vod_actor,
                "vod_director": vod_director,
                "vod_area": vod_area,
                "vod_play_from": "$$$".join(play_from_list),
                "vod_play_url": "$$$".join(play_url_list)
            }
            
            print(f"播放线路: {play_from_list}")
            return {"list": [video]}
            
        except Exception as e:
            print(f"详情页解析错误: {e}")
            # 返回一个基本的视频信息
            video = {
                "vod_id": ids[0],
                "vod_name": "影片详情加载失败",
                "vod_pic": "",
                "vod_content": "",
                "vod_play_from": "貝貝影院",
                "vod_play_url": f"第1集${self.host}"
            }
            return {"list": [video]}

    def searchContent(self, key, quick, pg=1):
        try:
            # 编码搜索关键词
            encoded_key = urllib.parse.quote(key)
            search_url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{encoded_key}.html"
            
            print(f"搜索URL: {search_url}")
            rsp = self.fetch(search_url, headers=self.header())
            root = BeautifulSoup(rsp.text, 'html.parser')
            videos = []
            
            # 根据HTML结构，搜索结果在 ul.show-list 中
            show_list = root.find('ul', class_='show-list')
            if show_list:
                items = show_list.find_all('li')
                for item in items:
                    # 获取链接和图片
                    a_tag = item.find('a', class_='play-img')
                    if not a_tag:
                        continue
                    
                    vod_id = a_tag.get('href', '')
                    if vod_id and not vod_id.startswith('http'):
                        vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                    
                    # 获取图片
                    img_tag = a_tag.find('img')
                    vod_pic = ""
                    if img_tag and 'src' in img_tag.attrs:
                        vod_pic = img_tag['src']
                        if vod_pic and not vod_pic.startswith('http'):
                            vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
                    
                    # 获取标题
                    h2_tag = item.find('h2')
                    vod_name = ""
                    if h2_tag:
                        title_a = h2_tag.find('a')
                        if title_a:
                            vod_name = title_a.text.strip()
                        else:
                            vod_name = h2_tag.text.strip()
                    
                    # 获取备注信息（更新状态）
                    vod_remarks = ""
                    play_txt = item.find('div', class_='play-txt')
                    if play_txt:
                        dl_tags = play_txt.find_all('dl')
                        for dl in dl_tags:
                            dt = dl.find('dt')
                            if dt and '资源/剧集' in dt.text:
                                dd = dl.find('dd')
                                if dd:
                                    vod_remarks = dd.text.strip()
                                    break
                    
                    # 获取年份和类型信息
                    vod_year = ""
                    vod_area = ""
                    if play_txt:
                        for dl in play_txt.find_all('dl'):
                            dt = dl.find('dt')
                            if dt and '类型' in dt.text:
                                dd = dl.find('dd')
                                if dd:
                                    type_text = dd.text.strip()
                                    # 解析类型、地区和年份
                                    parts = type_text.split('/')
                                    if len(parts) >= 3:
                                        vod_area = parts[1].strip() if len(parts) > 1 else ""
                                        vod_year = parts[2].strip() if len(parts) > 2 else ""
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic,
                        "vod_remarks": vod_remarks,
                        "vod_year": vod_year,
                        "vod_area": vod_area
                    })
            
            # 如果上面的方式没找到，尝试其他方式
            if not videos:
                # 尝试查找所有包含视频的li元素
                all_li = root.find_all('li')
                for li in all_li:
                    a_tag = li.find('a')
                    if a_tag and a_tag.get('href') and '/mianfei/' in a_tag['href']:
                        vod_id = a_tag['href']
                        if not vod_id.startswith('http'):
                            vod_id = self.host + vod_id if vod_id.startswith('/') else vod_id
                        
                        img_tag = a_tag.find('img')
                        vod_pic = ""
                        if img_tag and 'src' in img_tag.attrs:
                            vod_pic = img_tag['src']
                            if vod_pic and not vod_pic.startswith('http'):
                                vod_pic = self.host + vod_pic if vod_pic.startswith('/') else 'https:' + vod_pic
                        
                        h2_tag = li.find('h2')
                        vod_name = ""
                        if h2_tag:
                            title_a = h2_tag.find('a')
                            if title_a:
                                vod_name = title_a.text.strip()
                            else:
                                vod_name = h2_tag.text.strip()
                        
                        if vod_name and vod_id:
                            videos.append({
                                "vod_id": vod_id,
                                "vod_name": vod_name,
                                "vod_pic": vod_pic,
                                "vod_remarks": ""
                            })
            
            # 尝试获取总页数
            pagecount = 1
            page_tip = root.find('div', class_='page_tip')
            if page_tip:
                tip_text = page_tip.text.strip()
                # 解析 "当前1/1570页"
                match = re.search(r'当前\d+/(\d+)页', tip_text)
                if match:
                    pagecount = int(match.group(1))
            
            # 如果没有找到分页信息，尝试从分页链接获取
            if pagecount == 1:
                page_links = root.find_all('a', class_='page_link')
                if page_links:
                    max_page = 1
                    for link in page_links:
                        href = link.get('href', '')
                        if href and '/page/' in href:
                            try:
                                # 从URL中提取页码
                                match = re.search(r'/page/(\d+)/', href)
                                if match:
                                    page_num = int(match.group(1))
                                    if page_num > max_page:
                                        max_page = page_num
                            except:
                                pass
                    pagecount = max_page if max_page > 1 else 1
            
            # 计算总数
            total = pagecount * 10  # 每页大约10个结果
            
            print(f"搜索到 {len(videos)} 个结果，共 {pagecount} 页")
            
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": 10,
                "total": total
            }
            
        except Exception as e:
            print(f"搜索页面解析错误: {e}")
            import traceback
            traceback.print_exc()
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        # 解析播放页面，获取真实播放地址
        result = {}
        
        try:
            # 首先尝试直接访问播放页面
            if not id.startswith('http'):
                if id.startswith('/'):
                    play_url = self.host + id
                else:
                    play_url = self.host + '/' + id
            else:
                play_url = id
            
            print(f"播放页面URL: {play_url}")
            rsp = self.fetch(play_url, headers=self.header())
            
            # 尝试解析iframe中的真实地址
            root = BeautifulSoup(rsp.text, 'html.parser')
            
            # 查找iframe
            iframe = root.find('iframe')
            if iframe and iframe.get('src'):
                # 获取iframe的src
                iframe_src = iframe['src']
                if iframe_src:
                    result["parse"] = 0  # 不解析，直接播放
                    result["url"] = iframe_src
                    result["header"] = self.header()
                    return result
            
            # 尝试查找video标签
            video_tag = root.find('video')
            if video_tag and video_tag.get('src'):
                result["parse"] = 0
                result["url"] = video_tag['src']
                result["header"] = self.header()
                return result
            
            # 尝试查找source标签
            source_tag = root.find('source')
            if source_tag and source_tag.get('src'):
                result["parse"] = 0
                result["url"] = source_tag['src']
                result["header"] = self.header()
                return result
            
            # 如果没有找到具体的播放地址，使用TVBox内置解析
            result["parse"] = 1
            result["url"] = play_url
            result["header"] = self.header()
            result["ua"] = "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"
            
        except Exception as e:
            print(f"播放页面解析错误: {e}")
            result["parse"] = 1
            result["url"] = id
            result["header"] = self.header()
        
        return result

    def isVideoFormat(self, url):
        # 判断URL是否为视频格式
        video_formats = ['.m3u8', '.mp4', '.avi', '.mkv', '.flv', '.ts', '.webm']
        for fmt in video_formats:
            if fmt in url.lower():
                return True
        return False

    def localProxy(self, params):
        # 本地代理功能（如果需要）
        return [200, "video/MP2T", ""]