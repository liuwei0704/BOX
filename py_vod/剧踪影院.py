import requests
from bs4 import BeautifulSoup
import re
from base.spider import Spider
import sys
import json
import base64
import urllib.parse

sys.path.append('..')

xurl = "https://www.juzong.me"
headerx = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36'
}

class Spider(Spider):
    global xurl
    global headerx

    def getName(self):
        return "剧踪影院"

    def init(self, extend):
        pass

    def isVideoFormat(self, url):
        pass

    def homeContent(self, filter):
        # 分类配置，匹配站点头部导航分类映射
        class_items = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "剧集"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"}
        ]
        
        # 筛选配置，适配站点筛选逻辑
        static_filters = {
            "1": [ 
                  {"key": "area",
                  "name": "地区",
                  "value": [{"n": "大陆", "v": "大陆"},
                            {"n": "香港", "v": "香港"},
                            {"n": "台湾", "v": "台湾"},
                            {"n": "美国", "v": "美国"},
                            {"n": "日本", "v": "日本"},
                            {"n": "韩国", "v": "韩国"},
                            {"n": "德国", "v": "德国"},
                            {"n": "泰国", "v": "泰国"},
                            {"n": "英国", "v": "英国"},
                            {"n": "法国", "v": "法国"},
                            {"n": "意大利", "v": "意大利"},
                            {"n": "西班牙", "v": "西班牙"}]},                                                     
                 {"key": "year",
                  "name": "年代",
                  "value": [{"n": "2026", "v": "2026"},
                            {"n": "2025", "v": "2025"},
                            {"n": "2024", "v": "2024"},
                            {"n": "2023", "v": "2023"},
                            {"n": "2022", "v": "2022"},
                            {"n": "2021", "v": "2021"},
                            {"n": "2020", "v": "2020"},
                            {"n": "2019", "v": "2019"},
                            {"n": "2018", "v": "2018"},
                            {"n": "2017", "v": "2017"},
                            {"n": "2016", "v": "2016"},
                            {"n": "2015", "v": "2015"},
                            {"n": "2014", "v": "2014"},
                            {"n": "2013", "v": "2013"},
                            {"n": "2012", "v": "2012"},
                            {"n": "2011", "v": "2011"},
                            {"n": "2010", "v": "2010"}]},
                {"key": "by",
                  "name": "排序",
                  "value": [{"n": "时间", "v": "time"},
                            {"n": "人气", "v": "hits"},
                            {"n": "评分", "v": "score"}]}
            ],
            "2": [
                  {"key": "area",
                  "name": "地区",
                  "value": [{"n": "内地", "v": "内地"},
                            {"n": "香港", "v": "香港"},
                            {"n": "台湾", "v": "台湾"},
                            {"n": "美国", "v": "美国"},
                            {"n": "日本", "v": "日本"},
                            {"n": "韩国", "v": "韩国"},
                            {"n": "德国", "v": "德国"},
                            {"n": "泰国", "v": "泰国"},
                            {"n": "英国", "v": "英国"},
                            {"n": "法国", "v": "法国"},
                            {"n": "新加坡", "v": "新加坡"},
                            {"n": "其他", "v": "其他"}]},                               
                 {"key": "year",
                  "name": "年代",
                  "value": [{"n": "2026", "v": "2026"},
                            {"n": "2025", "v": "2025"},
                            {"n": "2024", "v": "2024"},
                            {"n": "2023", "v": "2023"},
                            {"n": "2022", "v": "2022"},
                            {"n": "2021", "v": "2021"},
                            {"n": "2020", "v": "2020"},
                            {"n": "2019", "v": "2019"},
                            {"n": "2018", "v": "2018"},
                            {"n": "2017", "v": "2017"},
                            {"n": "2016", "v": "2016"},
                            {"n": "2015", "v": "2015"},
                            {"n": "2014", "v": "2014"},
                            {"n": "2013", "v": "2013"},
                            {"n": "2012", "v": "2012"},
                            {"n": "2011", "v": "2011"},
                            {"n": "2010", "v": "2010"}]},
                {"key": "by",
                  "name": "排序",
                  "value": [{"n": "时间", "v": "time"},
                            {"n": "人气", "v": "hits"},
                            {"n": "评分", "v": "score"}]}
            ],
            "3": [               
                  {"key": "area",
                  "name": "地区",
                  "value": [{"n": "内地", "v": "内地"},
                            {"n": "港台", "v": "港台"},
                            {"n": "欧美", "v": "欧美"},
                            {"n": "韩国", "v": "韩国"},
                            {"n": "其他", "v": "其他"}]},
                 {"key": "year",
                  "name": "年代",
                  "value": [{"n": "2026", "v": "2026"},
                            {"n": "2025", "v": "2025"},
                            {"n": "2024", "v": "2024"},
                            {"n": "2023", "v": "2023"},
                            {"n": "2022", "v": "2022"},
                            {"n": "2021", "v": "2021"},
                            {"n": "2020", "v": "2020"},
                            {"n": "2019", "v": "2019"},
                            {"n": "2018", "v": "2018"},
                            {"n": "2017", "v": "2017"},
                            {"n": "2016", "v": "2016"},
                            {"n": "2015", "v": "2015"},
                            {"n": "2014", "v": "2014"},
                            {"n": "2013", "v": "2013"},
                            {"n": "2012", "v": "2012"},
                            {"n": "2011", "v": "2011"},
                            {"n": "2010", "v": "2010"}]},
                 {"key": "by",
                  "name": "排序",
                  "value": [{"n": "时间", "v": "time"},
                            {"n": "人气", "v": "hits"},
                            {"n": "评分", "v": "score"}]}
            ],
            "4": [                
                  {"key": "area",
                  "name": "地区",
                  "value": [{"n": "国产", "v": "国产"},
                            {"n": "欧美", "v": "欧美"},
                            {"n": "日本", "v": "日本"},
                            {"n": "其他", "v": "其他"}]},
                 {"key": "year",
                  "name": "年代",
                  "value": [{"n": "2026", "v": "2026"},
                            {"n": "2025", "v": "2025"},
                            {"n": "2024", "v": "2024"},
                            {"n": "2023", "v": "2023"},
                            {"n": "2022", "v": "2022"},
                            {"n": "2021", "v": "2021"},
                            {"n": "2020", "v": "2020"},
                            {"n": "2019", "v": "2019"},
                            {"n": "2018", "v": "2018"},
                            {"n": "2017", "v": "2017"},
                            {"n": "2016", "v": "2016"},
                            {"n": "2015", "v": "2015"},
                            {"n": "2014", "v": "2014"},
                            {"n": "2013", "v": "2013"},
                            {"n": "2012", "v": "2012"},
                            {"n": "2011", "v": "2011"},
                            {"n": "2010", "v": "2010"}]},
                 {"key": "by",
                  "name": "排序",
                  "value": [{"n": "时间", "v": "time"},
                            {"n": "人气", "v": "hits"},
                            {"n": "评分", "v": "score"}]}
            ]
        }
        
        return {
            "class": class_items,
            "filters": static_filters
        }

    def homeVideoContent(self):
        # 适配首页stui-vodlist结构提取视频数据
        resp = requests.get(url=xurl, headers=headerx, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")
        
        # 查找首页所有视频卡片列表
        video_list = soup.select('.stui-vodlist__thumb.lazyload')
        
        videos = []
        for item in video_list:
            # 提取标题
            title = item.get('title', '')
            # 提取详情链接
            detail_url = item.get('href', '')
            # 提取封面
            pic = item.get('data-original', '')
            if not pic:
                pic = item.get('style', '')
                pic = re.search(r'url$"([^"]+)"$', pic).group(1) if pic else ''
            # 提取副标题（更新信息）
            subtitle_tag = item.select_one('.pic-text')
            subtitle = subtitle_tag.text.strip() if subtitle_tag else ''
            
            video = {
                "vod_id": detail_url,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": subtitle
            }
            videos.append(video)
                
        result = {'list': videos}
        return result

    def categoryContent(self, cid, pg, filter, ext):
        page = int(pg) if pg else 1
        cateId = ext.get('cateId', cid) if ext else cid
        class_ = ext.get('class_', '') if ext else ''        
        area = ext.get('area', '') if ext else ''
        year = ext.get('year', '') if ext else ''
        by = ext.get('by', '') if ext else ''
        
        # 适配站点分类页URL规则
        url = f"{xurl}/vodshow/{cateId}-{area}-{by}-{class_}-----{page}---{year}/"
        
        resp = requests.get(url, headers=headerx, timeout=10)
        soup = BeautifulSoup(resp.text, 'lxml')
        
        # 提取分类页视频列表
        video_list = soup.select('.stui-vodlist__thumb.lazyload')
        
        videos = []
        for item in video_list:
            # 提取标题
            title = item.get('title', '')
            # 提取详情链接
            detail_url = item.get('href', '')
            # 提取封面
            pic = item.get('data-original', '')
            if not pic:
                pic = item.get('style', '')
                pic = re.search(r'url$"([^"]+)"$', pic).group(1) if pic else ''
            # 提取副标题
            subtitle_tag = item.select_one('.pic-text')
            subtitle = subtitle_tag.text.strip() if subtitle_tag else ''
            
            video = {
                "vod_id": detail_url,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": subtitle
            }
            videos.append(video)
                
        result = {'list': videos}
        result['page'] = pg
        result['pagecount'] = 99
        result['limit'] = 30
        result['total'] = 9999
        return result

        # 详情
    def detailContent(self, ids): 
        did = ids[0]
        result = {}
        videos = []
        playurl = ''
        if 'http' not in did:
            did = xurl + did
        # 请求详情页
        源码 = BeautifulSoup(requests.get(url=did, headers=headerx).text, "lxml")
        
        # 初始化VOD字典
        vod = {}
        
        # ========== 提取视频基本信息 ==========
        #视频ID
        vod["vod_id"] = did
        
        # 标题
        vod["vod_name"] = 源码.select_one('h1').get_text()
                                        
        # 封面图
        vod["vod_pic"] = 源码.select_one('img').get('data-original', '').replace('', '').strip()
                
        # 导演
        tag = 源码.select_one('.data:-soup-contains(导演)')
        vod["vod_director"] = tag.get_text().replace('导演：', '').strip() if tag else ""
 
        
        # 演员
        tag = 源码.select_one('.data:-soup-contains(主演)')
        vod["vod_actor"] = tag.get_text().replace('主演：', '').strip() if tag else ""
        
        # 简介
        vod["vod_content"] = 源码.select_one('.detail-sketch').get_text().strip()
            
        # ========== 提取播放列表 ==========
        
        # 线路
        ktabs = []
        线路数组 = 源码.select('.stui-pannel__head h3.title')
        for XL in 线路数组:
            线路标题 = XL.get_text().strip()
            线路标题 = re.sub(r'<img.*?>', '', 线路标题).strip()
            ktabs.append(线路标题)
        vod["vod_play_from"] = '$$$'.join(ktabs)
  
        # 列表
        klists = []
        播放数组 = 源码.select('.stui-content__playlist')
        for BF in 播放数组:
            播放列表 = BF.select('li a')
            klist = []
            for LB in 播放列表:
                播放标题 = LB.get_text().strip()
                播放链接 = LB.get('href', '')
                剧集 = f'{播放标题}${播放链接}'
                klist.append(剧集)
            # 用#连接同一播放源的剧集
            klists.append('#'.join(klist))
        
        # 用$$$连接不同播放源
        vod["vod_play_url"] = '$$$'.join(klists)
        
        result = {'list': [vod]}
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {}       
        try:
            # 第一步：尝试提取直链播放
            resp = requests.get(url=xurl + id, headers=headerx, timeout=10)
            源码 = BeautifulSoup(resp.text, "lxml")
            url = re.search(r'var\s+now\s*=\s*"([^"]+)"', str(源码)).group(1)            
            # 正则提取成功，使用直链播放
            result["parse"] = 0
            result["playUrl"] = ''
            result["url"] = url
            result["header"] = headerx
            
        except (AttributeError, Exception):
            # 提取失败（正则未匹配到或请求异常），使用嗅探播放
            result["parse"] = 1
            result["playUrl"] = ''
            result["url"] = xurl + id
            result["header"] = headerx        
        return result

    def searchContentPage(self, key, quick, page):
        result = {}
        videos = []
        if not page:
            page = '1'
        if page == '1':
            url = f'{xurl}/vodsearch/-------------/?wd={urllib.parse.quote(key)}'
        else:
            url = f'{xurl}/vodsearch/{urllib.parse.quote(key)}----------{page}---/'       
        resp = requests.get(url=url, headers=headerx, timeout=10)
        源码 = BeautifulSoup(resp.text, "lxml")
        
        # 适配搜索页结构提取视频列表
        搜索卡片列表 = 源码.select('.v-thumb.stui-vodlist__thumb.lazyload')
        
        for 数组 in 搜索卡片列表:
            # 获取标题
            标题 = 数组.get('title', '')
            # 获取链接
            链接 = 数组.get('href', '')
            # 获取封面
            图片 = 数组.get('data-original', '')
            if not 图片:
                图片 = 数组.get('style', '')
                图片 = re.search(r'url$"([^"]+)"$', 图片).group(1) if 图片 else ''
            # 获取副标题
            副标题标签 = 数组.select_one('.pic-text')
            副标题 = 副标题标签.text.strip() if 副标题标签 else ""
            
            video = {
                      "vod_id": 链接,
                      "vod_name": 标题,
                      "vod_pic": 图片,
                      "vod_remarks": 副标题
                                 }
            videos.append(video)
            
        result = {'list': videos}
        result['page'] = page
        result['pagecount'] = 60
        result['limit'] = 30
        result['total'] = 999999
        return result

    def searchContent(self, key, quick, page='1'):
        return self.searchContentPage(key, quick, page)

    def localProxy(self, params):
        if params['type'] == "m3u8":
            return self.proxyM3u8(params)
        elif params['type'] == "media":
            return self.proxyMedia(params)
        elif params['type'] == "ts":
            return self.proxyTs(params)
        return None
        
        
if __name__ == "__main__":
    spider = Spider()
    spider.init("")

    # 调用首页视频内容测试
    #result = spider.homeVideoContent()
    #print("首页视频内容测试结果：")
    #print(result)

    # 调用分类内容测试
    #category_result = spider.categoryContent("13", "2", {}, {})
    #print("\n分类内容测试结果：")
    #print(category_result)

    # 调用详情内容测试
    #detail_result = spider.detailContent(["/voddetail/60361/"])
    #print("\n详情内容测试结果：")
    #print(detail_result)

    # 调用播放内容测试
    #player_result = spider.playerContent("m3u8", "/vodplay/60361-1-1/", {})
    #print("\n播放内容测试结果：")
    #print(player_result)

    # 调用搜索内容测试
    #search_result = spider.searchContent("你的", False)
    # print("\n搜索内容测试结果：")
    #print(search_result)
