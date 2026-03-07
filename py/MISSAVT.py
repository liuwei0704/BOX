# coding=utf-8
import re
import json
from base.spider import Spider

class Spider(Spider):
    host = "https://central.znfcqan.cc"
    
    def getName(self):
        return "MissAVt"

    def init(self, extend=""):
        print(f"MissAVt spider initialized, host: {self.host}")

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def homeContent(self, filter):
        result = {"class": [], "list": [], "filters": {}}
        
        response = self.fetch(self.host)
        if not response:
            return result
        
        if hasattr(response, 'text'):
            html_content = response.text
        elif isinstance(response, str):
            html_content = response
        else:
            html_content = str(response)
        
        root = self.html(html_content)
        
        # 提取分类菜单
        classes = []
        nav_links = root.xpath("//nav[@id='app-nav']//ul/li/a")
        for a in nav_links:
            type_name = a.xpath("string(.)").strip()
            href_list = a.xpath("./@href")
            if not href_list:
                continue
            type_id = href_list[0]
            if type_name and type_id and type_name not in ["首页", "登录", "注册"]:
                if "/category/" in type_id:
                    class_id = type_id.replace("/category/", "").replace("/", "")
                    if class_id:
                        classes.append({"type_id": class_id, "type_name": type_name})
        result["class"] = classes
        
        # 提取首页推荐视频
        videos = []
        all_links = root.xpath("//a[contains(@href, '/watch/')]")
        seen = set()
        
        for link in all_links:
            href_list = link.xpath("./@href")
            if not href_list:
                continue
            href = href_list[0]
            
            if href in seen:
                continue
            seen.add(href)
            
            text = link.xpath("string(.)").strip()
            
            pic = ""
            parent = link.xpath("..")
            if parent:
                parent = parent[0]
                img_list = parent.xpath(".//img")
                if img_list:
                    img = img_list[0]
                    data_src = img.xpath("./@data-src")
                    if data_src:
                        pic = data_src[0]
                    else:
                        src = img.xpath("./@src")
                        if src:
                            pic = src[0]
            
            if pic and pic.startswith("//"):
                pic = "https:" + pic
            
            vod_id = self.host + href if href.startswith("/") else href
            videos.append({
                "vod_id": vod_id,
                "vod_name": text,
                "vod_pic": pic,
                "vod_remarks": text
            })
        
        result["list"] = videos
        return result

    def homeVideoContent(self):
        return self.homeContent(False)

    def categoryContent(self, tid, pg, filter, extend):
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 24, "total": 0}
        
        url = f"{self.host}/category/{tid}/"
        if pg and int(pg) > 1:
            url += f"?page={pg}"
        
        response = self.fetch(url)
        if not response:
            return result
        
        if hasattr(response, 'text'):
            html_content = response.text
        elif isinstance(response, str):
            html_content = response
        else:
            html_content = str(response)
        
        root = self.html(html_content)
        
        items = root.xpath("//ul[contains(@class, 'video-items')]/li")
        if not items:
            items = root.xpath("//div[contains(@class, 'video-item')]")
        
        videos = []
        seen = set()
        
        for item in items:
            links = item.xpath(".//a[contains(@href, '/watch/')]")
            if not links:
                continue
            link = links[0]
            
            href_list = link.xpath("./@href")
            if not href_list:
                continue
    def categoryContent(self, tid, pg, filter, extend):
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 24, "total": 0}
        
        url = f"{self.host}/category/{tid}/"
        if pg and int(pg) > 1:
            url += f"?page={pg}"
        
        response = self.fetch(url)
        if not response:
            return result
        
        if hasattr(response, 'text'):
            html_content = response.text
        elif isinstance(response, str):
            html_content = response
        else:
            html_content = str(response)
        
        root = self.html(html_content)
        
        # 查找视频列表容器
        items = root.xpath("//ul[contains(@class, 'video-items')]/li")
        if not items:
            items = root.xpath("//div[contains(@class, 'video-item')]")
        
        videos = []
        seen = set()
        
        for item in items:
            # 获取时长链接
            link = item.xpath(".//a[contains(@href, '/watch/')]")
            if not link:
                continue
            link = link[0]
            
            href_list = link.xpath("./@href")
            if not href_list:
                continue
            href = href_list[0]
            
            if href in seen:
                continue
            seen.add(href)
            
            # 获取时长（链接文本）
            remark = link.xpath("string(.)").strip()
            
            # 获取标题 - 在链接后面的div中
            title = ""
            # 方法1: 查找line-clamp-2 div
            title_div = item.xpath(".//div[contains(@class, 'line-clamp-2')]")
            if title_div:
                title = title_div[0].xpath("string(.)").strip()
            else:
                # 方法2: 查找链接后面的兄弟元素
                parent = link.xpath("..")
                if parent:
                    parent = parent[0]
                    next_elements = parent.xpath("./following-sibling::*")
                    for elem in next_elements:
                        text = elem.xpath("string(.)").strip()
                        if text and len(text) > 10:
                            title = text
                            break
            
            # 如果还没找到，使用链接文本
            if not title:
                title = remark
            
            # 获取封面
            pic = ""
            img_list = item.xpath(".//img")
            if img_list:
                img = img_list[0]
                data_src = img.xpath("./@data-src")
                if data_src:
                    pic = data_src[0]
                else:
                    src = img.xpath("./@src")
                    if src:
                        pic = src[0]
            
            if pic and pic.startswith("//"):
                pic = "https:" + pic
            
            vod_id = self.host + href if href.startswith("/") else href
            videos.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        
        # 提取分页信息
        page_texts = root.xpath("//*[contains(text(), '第') and contains(text(), '页')]")
        for elem in page_texts:
            text = elem.xpath("string(.)")
            match = re.search(r'第\d+/(\d+) 页', text)
            if match:
                result["pagecount"] = int(match.group(1))
                break
        
        result["list"] = videos
        result["total"] = len(videos)
        return result

    def detailContent(self, ids):
        vod = {}
        vid = ids[0] if isinstance(ids, list) else ids
        if not vid.startswith("http"):
            vid = self.host + "/watch/" + vid + "/"
        
        response = self.fetch(vid)
        if not response:
            return {"list": [vod]}
        
        if hasattr(response, 'text'):
            html_content = response.text
        elif isinstance(response, str):
            html_content = response
        else:
            html_content = str(response)
        
        root = self.html(html_content)
        
        # 提取标题
        title = ""
        title_elems = root.xpath("//title")
        if title_elems:
            title = title_elems[0].xpath("string(.)").replace(" - MissAVt", "").strip()
        
        # 提取封面
        pic = ""
        pic_elems = root.xpath("//meta[@property='og:image']")
        if pic_elems:
            pic_content = pic_elems[0].xpath("./@content")
            if pic_content:
                pic = pic_content[0]
        
        # 提取简介
        content = ""
        desc_elems = root.xpath("//meta[@property='og:description']")
        if desc_elems:
            desc_content = desc_elems[0].xpath("./@content")
            if desc_content:
                content = desc_content[0]
        
        # 提取播放地址 - 从poster div的data-url属性
        play_url = ""
        # 方法1: 查找poster div
        posters = root.xpath("//div[contains(@class, 'poster')]")
        if posters:
            data_url = posters[0].xpath("./@data-url")
            if data_url:
                play_url = data_url[0]
        
        # 方法2: 如果没找到，查找视频容器
        if not play_url:
            video_containers = root.xpath("//div[contains(@class, 'video-js')] | //div[contains(@class, 'xgplayer')]")
            for container in video_containers:
                data_url = container.xpath("./@data-url")
                if data_url:
                    play_url = data_url[0]
                    break
        
        # 方法3: 查找嵌入页
        if not play_url:
            embed_elems = root.xpath("//iframe[contains(@src, '/embed/')]")
            if embed_elems:
                embed_src = embed_elems[0].xpath("./@src")
                if embed_src:
                    # 需要再请求嵌入页获取真实地址
                    embed_url = self.host + embed_src[0] if embed_src[0].startswith("/") else embed_src[0]
                    embed_response = self.fetch(embed_url)
                    if embed_response:
                        if hasattr(embed_response, 'text'):
                            embed_html = embed_response.text
                        else:
                            embed_html = str(embed_response)
                        embed_root = self.html(embed_html)
                        # 在嵌入页中查找播放地址
                        video_sources = embed_root.xpath("//video/src | //source")
                        for source in video_sources:
                            src = source.xpath("./@src")
                            if src:
                                play_url = src[0]
                                break
        
        if play_url:
            vod["vod_play_from"] = "MissAVt"
            vod["vod_play_url"] = f"播放${play_url}"
        else:
            vod["vod_play_from"] = ""
            vod["vod_play_url"] = ""
        
        vod["vod_id"] = vid
        vod["vod_name"] = title
        vod["vod_pic"] = pic
        vod["vod_content"] = content
        vod["vod_year"] = ""
        vod["vod_area"] = ""
        vod["vod_actor"] = ""
        vod["vod_director"] = ""
        vod["vod_remarks"] = ""
        
        return {"list": [vod]}
        url = f"{self.host}/search?q={key}"
        if pg and int(pg) > 1:
            url += f"&page={pg}"
        
        response = self.fetch(url)
        if not response:
            return result
        
        if hasattr(response, 'text'):
            html_content = response.text
        elif isinstance(response, str):
            html_content = response
        else:
            html_content = str(response)
        
        root = self.html(html_content)
        
        items = root.xpath("//ul[contains(@class, 'video-items')]/li")
        if not items:
            items = root.xpath("//div[contains(@class, 'video-item')]")
        
        videos = []
        seen = set()
        
        for item in items:
            links = item.xpath(".//a[contains(@href, '/watch/')]")
            if not links:
                continue
            link = links[0]
            
            href_list = link.xpath("./@href")
            if not href_list:
                continue
            href = href_list[0]
            
            if href in seen:
                continue
            seen.add(href)
            
            title = ""
            title_div = item.xpath(".//div[contains(@class, 'line-clamp-2')]")
            if title_div:
                title = title_div[0].xpath("string(.)").strip()
            else:
                title = link.xpath("string(.)").strip()
            
            remark = ""
            time_elem = item.xpath(".//div[contains(@class, 'bg-black') and contains(@class, 'text-sm')]")
            if time_elem:
                remark = time_elem[0].xpath("string(.)").strip()
            else:
                remark = link.xpath("string(.)").strip()
            
            pic = ""
            img_list = item.xpath(".//img")
            if img_list:
                img = img_list[0]
                data_src = img.xpath("./@data-src")
                if data_src:
                    pic = data_src[0]
                else:
                    src = img.xpath("./@src")
                    if src:
                        pic = src[0]
            
            if pic and pic.startswith("//"):
                pic = "https:" + pic
            
            vod_id = self.host + href if href.startswith("/") else href
            videos.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remark
            })
        
        result["list"] = videos
        return result

    def playerContent(self, flag, id, vipFlags):
        return {"parse": 0, "url": id, "header": {}}
