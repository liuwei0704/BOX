# coding=utf-8
import sys
import requests
import json
import re
import urllib.parse

class Spider():
    def __init__(self):
        self.api_url = "http://zhangqun1818.serv00.net/yt/yt001.php"

    def getName(self):
        return "YouTube_PHP_Fix"

    # 1. 修復之前報錯的 getDependence
    def getDependence(self):
        return []

    def init(self, extend=""):
        pass

    # 2. 修正 homeVideoContent 報錯 (首頁推薦)
    # 直接回傳空，或調用 Trending 數據
    def homeVideoContent(self):
        return self.categoryContent("Trending")

    def homeContent(self, filter):
        result = {}
        # 這裡建議使用英文 ID，在請求 PHP 時再處理
        cateManual = {
            "蒼穹動漫社": "@DragonAnimationClub",
            "桃桃爱漫画": "@桃桃爱漫画",
            "阿星推文": "@阿星推文",
            "AI动漫频道": "@AI动漫频道",
            "漫剧不打烊": "@漫剧不打烊",
            "盛世劇集": "@ShengshiDrama",
            "王者短劇": "@王者短劇堂KingDramaHub"
        }
        classes = []
        for k in cateManual:
            classes.append({'type_name': k, 'type_id': cateManual[k]})
        result['class'] = classes
        return result

    def categoryContent(self, tid, pg=1, filter=True, extend={}):
        result = {}
        encoded_tid = urllib.parse.quote(tid)
        # 假設 PHP 支持 t 參數獲取頻道或分類內容
        url = f"{self.api_url}?t={encoded_tid}&pg={pg}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            # 兼容 PHP 返回 {"list": []} 或直接返回 [] 的情況
            vod_list = data.get('list', data) if isinstance(data, dict) else data
            result['list'] = self.format_list(vod_list)
            result['page'] = pg
            result['pagecount'] = 99
            result['limit'] = 20
            result['total'] = 999
        except:
            result['list'] = []
        return result

    def searchContent(self, key, quick, pg=1):
        result = {'list': []}
        import urllib.parse
        encoded_key = urllib.parse.quote(key)
        
        # 2026 最新：嘗試多個可能參數 (wd, q, keyword)
        params_list = [f"wd={encoded_key}", f"q={encoded_key}", f"keyword={encoded_key}"]
        
        for p in params_list:
            url = f"{self.api_url}?{p}&pg={pg}"
            try:
                res = requests.get(url, timeout=10)
                res.encoding = 'utf-8' # 強制編碼，防止中文亂碼
                
                # 情況 A：如果 PHP 返回的是 JSON 數組
                try:
                    data = res.json()
                    # 如果返回的是 {"list": [...]}
                    if isinstance(data, dict) and "list" in data:
                        result['list'] = self.format_list(data['list'])
                    # 如果返回的是 [...] 直接數組
                    elif isinstance(data, list):
                        result['list'] = self.format_list(data)
                    
                    if len(result['list']) > 0:
                        return result
                except:
                    pass
                
                # 情況 B：如果 PHP 返回的是 HTML 或 原始 YouTube JSON (暴力正則匹配)
                # 2026 年 YouTube 搜索結果的通用特徵：videoId 與 label/text
                content = res.text
                items = re.findall(r'"videoId":"([^"]{11})".*?"text":"([^"]+)"', content)
                
                temp_list = []
                seen = set()
                for vid, title in items:
                    if vid in seen or len(title) < 2: continue
                    # 過濾掉 UI 常見詞 (首頁, 訂閱, 播放等)
                    if any(x in title for x in ["YouTube", "Shorts", "訂閱", "Home", "Library"]): continue
                    
                    seen.add(vid)
                    temp_list.append({
                        "vod_id": vid,
                        "vod_name": title.replace('\\n', '').strip(),
                        "vod_pic": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                        "vod_remarks": "搜尋結果"
                    })
                
                if len(temp_list) > 0:
                    result['list'] = temp_list
                    return result
                    
            except Exception as e:
                continue
                
        return result

    def format_list(self, raw_list):
        items = []
        if not isinstance(raw_list, list):
            return items
        for item in raw_list:
            # 2026 年 YouTube API 鍵名適配
            vid = item.get('vod_id', item.get('videoId', ''))
            
            # 獲取標題：優先找 vod_name，再找 title，最後找 runs 結構
            name = item.get('vod_name', item.get('title', ''))
            if isinstance(name, dict):
                name = name.get('runs', [{}])[0].get('text', name.get('simpleText', ''))
            
            if vid and name and len(str(name)) > 1:
                items.append({
                    "vod_id": vid,
                    "vod_name": str(name),
                    "vod_pic": item.get('vod_pic', f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"),
                    "vod_remarks": item.get('vod_remarks', '2026.04')
                })
        return items

    def playerContent(self, flag, id, vipFlags):
        # 這裡返回 YouTube 標準播放頁，Fongmi 會嘗試解析
        result = {
            "parse": 1, 
            "url": f"https://www.youtube.com/watch?v={id}", 
            "header": {"User-Agent": "Mozilla/5.0"}
        }
        return result

    def format_list(self, raw_list):
        items = []
        if not isinstance(raw_list, list):
            return items
        for item in raw_list:
            vid = item.get('vod_id', item.get('videoId', ''))
            name = item.get('vod_name', item.get('title', ''))
            if vid and name:
                items.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": item.get('vod_pic', f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"),
                    "vod_remarks": item.get('vod_remarks', '2026_Fix')
                })
        return items

# 測試區塊（盒子環境不調用）
if __name__ == '__main__':
    spider = Spider()
    print(spider.homeVideoContent())