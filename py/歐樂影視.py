# coding=utf-8
#!/usr/bin/python
import sys
import os
sys.path.append("..")
import re
import json
import time
import hashlib
import random
import string
from base.spider import Spider
from urllib.parse import quote, unquote

class Spider(Spider):

    def getName(self):
        return "歐樂影院"

    def init(self, extend=""):
        self.host = "https://www.olehdtv.com"
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def action(self, action):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        result = {}
        
        # 只設置基本分類，不設置篩選器
        classes = [
            {"type_name": "電影", "type_id": "1"},
            {"type_name": "連續劇", "type_id": "2"},
            {"type_name": "綜藝", "type_id": "3"},
            {"type_name": "動漫", "type_id": "4"}
        ]
        
        result["class"] = classes
        return result

    def homeVideoContent(self):
        # 獲取首頁推薦視頻（最新電影）
        return self.categoryContent("1", 1, False, {})

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        videos = []
        
        try:
            # 簡單的URL構建，沒有篩選參數
            url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"
            
            html = self.fetch(url, headers=self.header()).text
            
            # 修復正則表達式：避免匹配到包含var vod_id的內容
            # 使用更精確的模式匹配
            pattern = r'<li\s+class="vodlist_item[^"]*">.*?<a\s+class="vodlist_thumb[^"]*"[^>]*dids="(\d+)"[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*data-original="([^"]*)"[^>]*>.*?<p\s+class="vodlist_title">.*?<a[^>]*>([^<]*)</a>.*?</p>.*?<p\s+class="vodlist_sub">([^<]*)</p>'
            matches = re.findall(pattern, html, re.S)
            
            for match in matches:
                vod_id = match[0]
                detail_url = match[1]
                title = match[2].strip()
                cover = match[3]
                title_html = match[4].strip()
                actors = match[5].strip()
                
                # 清理標題：移除var vod_id=xxxxx等JS代碼
                # 先嘗試從title_html提取，如果包含JS代碼則從title屬性提取
                title_clean = title_html
                
                # 檢查是否包含var vod_id=
                if 'var vod_id=' in title_clean:
                    # 使用title屬性作為備選
                    title_clean = title
                
                # 進一步清理：移除任何JS代碼
                title_clean = re.sub(r'var\s+vod_id\s*=\s*\d+;?\s*', '', title_clean)
                title_clean = re.sub(r'<script[^>]*>.*?</script>', '', title_clean, flags=re.S)
                title_clean = re.sub(r'javascript:.*?(;|$)', '', title_clean)
                title_clean = title_clean.strip()
                
                # 如果還是空的，使用title屬性
                if not title_clean:
                    title_clean = title
                
                # 從封面URL提取年份
                year = ""
                if "/vod/" in cover:
                    date_match = re.search(r'/vod/(\d{4})\d{2}', cover)
                    if date_match:
                        year = date_match.group(1)
                
                # 提取評分和熱度
                score = "0.0"
                
                # 嘗試從當前匹配的完整HTML塊中提取評分
                # 查找匹配的HTML片段
                item_pattern = r'<li\s+class="vodlist_item[^"]*"[^>]*dids="' + vod_id + r'"[^>]*>.*?<p\s+class="vodlist_sub">[^<]*</p>'
                item_match = re.search(item_pattern, html, re.S)
                
                if item_match:
                    item_text = item_match.group(0)
                    score_pattern = r'text_right\s+text_dy[^>]*>(\d+\.?\d*)<'
                    score_match = re.search(score_pattern, item_text)
                    if score_match:
                        score = score_match.group(1)
                
                # 提取視頻質量
                quality = "高清"
                if 'item_text' in locals():
                    quality_match = re.search(r'voddate\s+voddate_year">([^<]*)</em>', item_text)
                    if quality_match:
                        quality = quality_match.group(1)
                
                video = {
                    "vod_id": vod_id,
                    "vod_name": title_clean,
                    "vod_pic": cover,
                    "vod_year": year,
                    "vod_remarks": f"{quality}|評分:{score}",
                    "vod_content": f"主演：{actors[:100]}" if actors else "暫無主演信息"
                }
                videos.append(video)
            
            # 獲取總頁數
            total_page = 1
            page_match = re.search(r'共有\s*(\d+)\s*頁', html)
            if page_match:
                total_page = int(page_match.group(1))
            else:
                # 嘗試其他方式查找頁數
                page_patterns = [
                    r'<a[^>]*>(\d+)</a>\s*<a[^>]*>下一頁</a>',
                    r'page/(\d+)\.html">尾頁</a>',
                    r'共\s*(\d+)\s*頁'
                ]
                for pattern in page_patterns:
                    page_match = re.search(pattern, html)
                    if page_match:
                        total_page = int(page_match.group(1))
                        break
            
            # 獲取總視頻數
            total = len(videos)
            
            result["list"] = videos
            result["page"] = pg
            result["pagecount"] = total_page
            result["limit"] = len(videos) if videos else 60
            result["total"] = total
            
        except Exception as e:
            print(f"Error parsing category: {e}")
            import traceback
            traceback.print_exc()
            result["list"] = []
            result["page"] = pg
            result["pagecount"] = 1
            result["limit"] = 60
            result["total"] = 60
            
        return result

    def detailContent(self, ids):
        vod_id = ids[0]
        result = {}
        try:
            url = f"{self.host}/index.php/vod/detail/id/{vod_id}.html"
            html = self.fetch(url, headers=self.header()).text
            
            # 提取標題
            title_pattern = r'<title>(.*?)_'
            title_match = re.search(title_pattern, html)
            title = title_match.group(1).strip() if title_match else ""
            
            # 提取描述
            desc_pattern = r'<meta name="description" content="(.*?)"'
            desc_match = re.search(desc_pattern, html)
            description = desc_match.group(1) if desc_match else ""
            
            # 提取封面
            cover_pattern = r'data-original="(.*?)"'
            cover_match = re.search(cover_pattern, html)
            cover = cover_match.group(1) if cover_match else ""
            
            # 提取年份、地區、類型等信息
            year = ""
            area = ""
            lang = ""
            vod_type = ""
            status = ""
            
            # 從詳情數據中提取
            data_pattern = r'<li class="data">.*?<span.*?>年份：</span>.*?<a.*?>(.*?)</a>.*?</li>'
            year_match = re.search(data_pattern, html, re.S)
            if year_match:
                year = year_match.group(1).strip()
            
            area_pattern = r'<span.*?>地區：</span>.*?<a.*?>(.*?)</a>'
            area_match = re.search(area_pattern, html, re.S)
            if area_match:
                area = area_match.group(1).strip()
            
            # 提取類型
            type_pattern = r'<span.*?>類型：</span>(.*?)</li>'
            type_match = re.search(type_pattern, html, re.S)
            if type_match:
                vod_type = type_match.group(1).strip()
                vod_type = re.sub(r'<[^>]+>', '', vod_type)
            
            # 提取演員
            actors = []
            actor_pattern = r'<span>主演：</span>(.*?)</li>'
            actor_match = re.search(actor_pattern, html, re.S)
            if actor_match:
                actors_html = actor_match.group(1)
                actor_names = re.findall(r'<a.*?>(.*?)</a>', actors_html)
                actors = [name.strip() for name in actor_names if name.strip()]
            
            # 提取導演
            director = ""
            director_pattern = r'<span>導演：</span>.*?<a.*?>(.*?)</a>'
            director_match = re.search(director_pattern, html, re.S)
            if director_match:
                director = director_match.group(1).strip()
            
            # 提取評分
            score = "0.0"
            score_pattern = r'<span class="star_tips">(\d+\.?\d*)</span>'
            score_match = re.search(score_pattern, html)
            if score_match:
                score = score_match.group(1)
            
            # 提取狀態
            status = ""
            status_pattern = r'<span class="data_style">(.*?)</span>'
            status_match = re.search(status_pattern, html)
            if status_match:
                status = status_match.group(1)
            
            # 提取更新時間
            update_time = ""
            update_pattern = r'<em>(\d{2}-\d{2})</em>'
            update_match = re.search(update_pattern, html)
            if update_match:
                update_time = update_match.group(1)
            
            # 提取詳細描述
            desc_detail = ""
            desc_detail_pattern = r'<div class="content_desc.*?<span>(.*?)</span>'
            desc_detail_match = re.search(desc_detail_pattern, html, re.S)
            if desc_detail_match:
                desc_detail = desc_detail_match.group(1).strip()
            
            if not desc_detail and description:
                desc_detail = description
            
            # 解析播放列表
            play_from = []
            play_url = []
            
            # 查找播放源標籤
            play_source_pattern = r'<div class="play_source_tab.*?">(.*?)</div>'
            play_source_match = re.search(play_source_pattern, html, re.S)
            
            source_list = []
            if play_source_match:
                play_source_html = play_source_match.group(1)
                # 提取播放源名稱
                source_names = re.findall(r'<a.*?>(.*?)</a>', play_source_html)
                for source_name in source_names:
                    source_name_clean = re.sub(r'<.*?>', '', source_name).strip()
                    if source_name_clean and source_name_clean not in source_list:
                        source_list.append(source_name_clean)
            
            # 如果沒有找到播放源，添加默認播放源
            if not source_list:
                source_list = ["歐樂官方播放器", "VIP會員超清"]
            
            # 解析每個播放源的集數
            for source_name in source_list:
                # 查找對應的播放列表
                playlist_found = False
                
                # 查找播放列表區域
                play_list_pattern = r'<ul class="content_playlist.*?">(.*?)</ul>'
                play_list_matches = re.findall(play_list_pattern, html, re.S)
                
                for play_list_html in play_list_matches:
                    # 查找播放鏈接
                    play_links = re.findall(r'<a.*?href="(.*?)".*?>(.*?)</a>', play_list_html, re.S)
                    
                    if play_links:
                        play_from.append(source_name)
                        play_url_items = []
                        
                        for play_link in play_links:
                            play_url_path, play_name = play_link
                            play_name_clean = re.sub(r'<.*?>', '', play_name).strip()
                            
                            # 構建完整URL
                            if not play_url_path.startswith("http"):
                                if play_url_path.startswith("/"):
                                    full_url = f"{self.host}{play_url_path}"
                                else:
                                    full_url = f"{self.host}/{play_url_path}"
                            else:
                                full_url = play_url_path
                            
                            # 添加集數信息
                            if play_name_clean:
                                play_url_items.append(f"{play_name_clean}${full_url}")
                        
                        if play_url_items:
                            play_url.append("#".join(play_url_items))
                            playlist_found = True
                            break
                
                if not playlist_found:
                    # 如果沒有找到具體集數，添加默認播放地址
                    play_from.append(source_name)
                    play_url.append(f"立即播放${self.host}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html")
            
            # 如果以上都沒找到，使用通用播放地址
            if not play_from:
                play_from = ["歐樂官方播放器"]
                play_url = [f"立即播放${self.host}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"]
            
            # 構建視頻信息
            video = {
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": cover,
                "vod_year": year,
                "vod_area": area,
                "vod_lang": "",
                "vod_type": vod_type,
                "vod_remarks": f"{status}|評分:{score}|{update_time}",
                "vod_content": desc_detail,
                "vod_actor": " / ".join(actors) if actors else "",
                "vod_director": director,
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_url)
            }
            
            result["list"] = [video]
            
        except Exception as e:
            print(f"Error parsing detail: {e}")
            import traceback
            traceback.print_exc()
            # 返回默認信息
            video = {
                "vod_id": vod_id,
                "vod_name": "未知視頻",
                "vod_pic": "",
                "vod_year": "",
                "vod_area": "",
                "vod_remarks": "",
                "vod_content": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_play_from": "歐樂官方播放器",
                "vod_play_url": f"立即播放${self.host}/index.php/vod/play/id/{vod_id}/sid/1/nid/1.html"
            }
            result["list"] = [video]
            
        return result

    def searchContent(self, key, quick, pg=1):
        result = {}
        videos = []
        
        try:
            # URL編碼搜索關鍵詞
            encoded_key = quote(key)
            url = f"{self.host}/index.php/vod/search/wd/{encoded_key}/page/{pg}.html"
            
            html = self.fetch(url, headers=self.header()).text
            
            # 使用和分類頁相同的解析邏輯
            pattern = r'<li\s+class="vodlist_item[^"]*">.*?<a\s+class="vodlist_thumb[^"]*"[^>]*dids="(\d+)"[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*data-original="([^"]*)"[^>]*>.*?<p\s+class="vodlist_title">.*?<a[^>]*>([^<]*)</a>.*?</p>.*?<p\s+class="vodlist_sub">([^<]*)</p>'
            matches = re.findall(pattern, html, re.S)
            
            for match in matches:
                vod_id = match[0]
                detail_url = match[1]
                title = match[2].strip()
                cover = match[3]
                title_html = match[4].strip()
                actors = match[5].strip()
                
                # 清理標題：移除var vod_id=xxxxx等JS代碼
                title_clean = title_html
                
                # 檢查是否包含var vod_id=
                if 'var vod_id=' in title_clean:
                    # 使用title屬性作為備選
                    title_clean = title
                
                # 進一步清理：移除任何JS代碼
                title_clean = re.sub(r'var\s+vod_id\s*=\s*\d+;?\s*', '', title_clean)
                title_clean = re.sub(r'<script[^>]*>.*?</script>', '', title_clean, flags=re.S)
                title_clean = re.sub(r'javascript:.*?(;|$)', '', title_clean)
                title_clean = title_clean.strip()
                
                # 如果還是空的，使用title屬性
                if not title_clean:
                    title_clean = title
                
                # 提取評分
                score = "0.0"
                
                # 查找匹配的HTML片段
                item_pattern = r'<li\s+class="vodlist_item[^"]*"[^>]*dids="' + vod_id + r'"[^>]*>.*?<p\s+class="vodlist_sub">[^<]*</p>'
                item_match = re.search(item_pattern, html, re.S)
                
                if item_match:
                    item_text = item_match.group(0)
                    score_pattern = r'text_right\s+text_dy[^>]*>(\d+\.?\d*)<'
                    score_match = re.search(score_pattern, item_text)
                    if score_match:
                        score = score_match.group(1)
                
                video = {
                    "vod_id": vod_id,
                    "vod_name": title_clean,
                    "vod_pic": cover,
                    "vod_year": "",
                    "vod_remarks": f"評分:{score}",
                    "vod_content": f"主演：{actors[:50]}"
                }
                videos.append(video)
            
            # 獲取總頁數
            total_page = 1
            page_match = re.search(r'page/(\d+)\.html">尾頁</a>', html)
            if page_match:
                total_page = int(page_match.group(1))
            else:
                # 嘗試其他方式查找頁數
                page_patterns = [
                    r'<a[^>]*>(\d+)</a>\s*<a[^>]*>下一頁</a>',
                    r'共\s*(\d+)\s*頁'
                ]
                for pattern in page_patterns:
                    page_match = re.search(pattern, html)
                    if page_match:
                        total_page = int(page_match.group(1))
                        break
            
            result["list"] = videos
            result["page"] = pg
            result["pagecount"] = total_page
            result["limit"] = 20
            result["total"] = len(videos)
            
        except Exception as e:
            print(f"Error searching: {e}")
            import traceback
            traceback.print_exc()
            result["list"] = []
            result["page"] = pg
            result["pagecount"] = 1
            result["limit"] = 20
            result["total"] = 20
            
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {}
        
        # id可能是完整的播放地址或相對路徑
        if id.startswith("http"):
            url = id
        else:
            # 處理相對路徑
            if not id.startswith("/"):
                id = "/" + id
            url = f"{self.host}{id}"
        
        try:
            # 獲取播放頁面HTML
            html = self.fetch(url, headers=self.header()).text
            
            # 方法1：從JavaScript變量中提取視頻地址
            player_pattern = r'var player_aaaa\s*=\s*({.*?});'
            player_match = re.search(player_pattern, html, re.S)
            
            if player_match:
                player_json = player_match.group(1)
                # 清理JSON字符串
                player_json = player_json.replace('\n', '').replace('\r', '').replace('\t', '')
                
                try:
                    player_data = json.loads(player_json)
                    play_url = player_data.get("url", "")
                    
                    if play_url and ("m3u8" in play_url or "mp4" in play_url):
                        # 處理轉義字符
                        play_url = play_url.replace('\\/', '/')
                        result["parse"] = 0
                        result["url"] = play_url
                    else:
                        result["parse"] = 1
                        result["url"] = url
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    # 嘗試手動解析
                    url_match = re.search(r'"url"\s*:\s*"(.*?)"', player_json)
                    if url_match:
                        play_url = url_match.group(1).replace('\\/', '/')
                        result["parse"] = 0
                        result["url"] = play_url
                    else:
                        result["parse"] = 1
                        result["url"] = url
            else:
                # 方法2：嘗試查找直接嵌入的m3u8地址
                m3u8_pattern = r'"url"\s*:\s*"(https?://[^"]+\.(m3u8|mp4))"'
                m3u8_match = re.search(m3u8_pattern, html)
                
                if m3u8_match:
                    play_url = m3u8_match.group(1).replace('\\/', '/')
                    result["parse"] = 0
                    result["url"] = play_url
                else:
                    # 方法3：查找iframe
                    iframe_pattern = r'<iframe.*?src="(.*?)"'
                    iframe_match = re.search(iframe_pattern, html)
                    
                    if iframe_match:
                        iframe_url = iframe_match.group(1)
                        if not iframe_url.startswith("http"):
                            iframe_url = f"{self.host}{iframe_url}"
                        
                        # 遞歸解析iframe內容
                        return self.playerContent(flag, iframe_url, vipFlags)
                    else:
                        result["parse"] = 1
                        result["url"] = url
        
        except Exception as e:
            print(f"Error parsing player content: {e}")
            import traceback
            traceback.print_exc()
            result["parse"] = 1
            result["url"] = url
        
        # 添加請求頭
        result["header"] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.host,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Origin": self.host
        }
        
        # 如果是m3u8地址，添加額外的header
        if result.get("url", "").endswith(".m3u8"):
            result["header"].update({
                "Accept": "application/x-mpegURL, */*",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site"
            })
        
        return result

    def localProxy(self, param):
        try:
            action = {}
            if "do" in param:
                action["do"] = param["do"]
            if "type" in param:
                action["type"] = param["type"]
            if "url" in param:
                action["url"] = param["url"]
            
            if action.get("type") == "m3u8":
                # 處理m3u8代理
                m3u8_url = action["url"]
                
                # 獲取m3u8文件內容
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": self.host,
                    "Accept": "application/x-mpegURL, */*"
                }
                
                response = self.fetch(m3u8_url, headers=headers)
                content = response.text
                
                # 處理m3u8文件中的相對路徑
                lines = content.split('\n')
                processed_lines = []
                
                for line in lines:
                    if line and not line.startswith('#') and not line.startswith('http'):
                        # 修正相對路徑
                        if line.startswith('/'):
                            # 絕對路徑
                            base_domain = re.search(r'https?://[^/]+', m3u8_url).group(0)
                            line = base_domain + line
                        else:
                            # 相對路徑
                            base_url = m3u8_url[:m3u8_url.rfind('/') + 1]
                            line = base_url + line
                    processed_lines.append(line)
                
                content = '\n'.join(processed_lines)
                return [200, "application/vnd.apple.mpegurl", content]
            
            elif action.get("type") == "media":
                # 處理媒體文件代理
                media_url = action["url"]
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": self.host,
                    "Range": action.get("range", "")
                }
                
                response = self.fetch(media_url, headers=headers)
                content_type = response.headers.get("Content-Type", "video/mp4")
                
                return [200, content_type, response.content]
            
            else:
                return [404, "text/plain", "Not Found"]
                
        except Exception as e:
            print(f"Error in localProxy: {e}")
            import traceback
            traceback.print_exc()
            return [500, "text/plain", f"Server Error: {str(e)}"]

    def header(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": self.host,
            "Cache-Control": "max-age=0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1"
        }