# coding=utf-8
import sys
import requests
import json

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    host = "https://bfzyapi.com/api.php/provide/vod/"
    
    def getName(self):
        return "暴风资源"

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        result = {}
        # 经过实测确认有内容的真实 ID
        result['class'] = [
            {"type_name": "动作片", "type_id": "20"},
            {"type_name": "喜剧片", "type_id": "21"},
            {"type_name": "爱情片", "type_id": "22"},
            {"type_name": "科幻片", "type_id": "24"},
            {"type_name": "恐怖片", "type_id": "23"},
            {"type_name": "剧情片", "type_id": "26"},
            {"type_name": "国产剧", "type_id": "31"},
            {"type_name": "欧美剧", "type_id": "32"},
            {"type_name": "韩国剧", "type_id": "34"},
            {"type_name": "日本剧", "type_id": "36"},
            {"type_name": "大陆综艺", "type_id": "46"},
            {"type_name": "日韩动漫", "type_id": "41"},
            {"type_name": "反转爽文", "type_id": "68"}
        ]
        try:
            url = f"{self.host}?ac=videolist"
            res = requests.get(url, timeout=10)
            result['list'] = self.parseJsonList(res.json())
        except:
            result['list'] = []
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        url = f"{self.host}?ac=videolist&t={tid}&pg={pg}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            result['list'] = self.parseJsonList(data)
            result['page'] = int(data.get('page', pg))
            result['pagecount'] = int(data.get('pagecount', 999))
            result['limit'] = int(data.get('limit', 20))
            result['total'] = int(data.get('total', 999))
        except:
            result['list'] = []
        return result

    def detailContent(self, ids):
        url = f"{self.host}?ac=detail&ids={ids[0]}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            item = data['list'][0]
            vod = {
                "vod_id": item['vod_id'],
                "vod_name": item['vod_name'],
                "vod_pic": item['vod_pic'],
                "vod_remarks": item['vod_remarks'],
                "vod_content": item.get('vod_content', ''),
                "vod_play_from": item['vod_play_from'],
                "vod_play_url": item['vod_play_url']
            }
            return {"list": [vod]}
        except:
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        url = f"{self.host}?ac=videolist&wd={key}&pg={pg}"
        try:
            res = requests.get(url, timeout=10)
            return {"list": self.parseJsonList(res.json())}
        except:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        return {"parse": 0, "url": id, "header": ""}

    def parseJsonList(self, data):
        vod_list = []
        for item in data.get('list', []):
            vod_list.append({
                "vod_id": item['vod_id'],
                "vod_name": item['vod_name'],
                "vod_pic": item['vod_pic'],
                "vod_remarks": item['vod_remarks']
            })
        return vod_list