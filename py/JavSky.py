import re
from base.spider import Spider

class Spider(Spider):
    host = "https://javsky.tv"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://javsky.tv/"
    }

    def getName(self):
        return "JavSky_Final"

    def init(self, extend=""):
        pass

    def homeContent(self, filter):
        classes = [
            {"type_id": "category/censored", "type_name": "Censored"},
            {"type_id": "category/uncensored", "type_name": "Uncensored"},
            {"type_id": "amateur", "type_name": "Amateur"},
            {"type_id": "category/chinese-sub", "type_name": "Chinese Sub"}
          ]
        res = self.fetch(self.host, headers=self.header)
        video_list = self.parse_video_list(res.text)
        return {"class": classes, "list": video_list}

    def categoryContent(self, tid, pg, filter, extend):
        base_tid = tid.strip('/')
        # 规范化分页 URL，兼容 /page/n/ 格式
        if int(pg) == 1:
            url = f"{self.host}/{base_tid}"
        else:
            url = f"{self.host}/{base_tid}/page/{pg}/"
        res = self.fetch(url, headers=self.header)
        video_list = self.parse_video_list(res.text)
        return {"page": pg, "pagecount": 999, "limit": len(video_list), "total": 999, "list": video_list}

    def parse_video_list(self, html):
        result = []
        # 更加鲁棒的正则：alt 属性可选，放宽匹配限制
        pattern = re.compile(r'<a href="([^"]+)"[^>]*>.*?<img[^>]*?(?:data-src|src)="([^"]+)"(?:[^>]*alt="([^"]*)")?', re.S)
        matches = pattern.findall(html)
        for link, img, title in matches:
            vod_id = link.replace(self.host, "").strip("/")
            result.append({"vod_id": vod_id, "vod_name": title.strip() or "未知标题", "vod_pic": img, "vod_remarks": ""})
        return result

    def detailContent(self, ids):
        vod_id = ids[0]
        url = f"{self.host}/{vod_id}"
        res = self.fetch(url, headers=self.header)
        html = res.text
        hash_match = re.search(r'iframe src="/player#([^"]+)"', html)
        if hash_match:
            # 只传 Hash，不传 URL，彻底解决 02 选集问题
            raw_hash = hash_match.group(1).strip()
            return {
                "list": [{
                    "vod_id": vod_id,
                    "vod_play_from": "JavSky",
                    "vod_play_url": f"播放正片${raw_hash}"
                }]
            }
        return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        # 在这里拼回完整地址，避开 APP 对 # 号的错误处理
        final_url = f"https://javsky.tv/player#{id}"
        return {
            "parse": 1,
            "url": final_url,
            "header": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Referer": "https://javsky.tv/"
            }
        }

    def searchContent(self, key, quick, pg="1"):
        url = f"{self.host}/?s={key}" if str(pg) == "1" else f"{self.host}/page/{pg}/?s={key}"
        res = self.fetch(url, headers=self.header)
        video_list = self.parse_video_list(res.text)
        return {"list": video_list}