# -*- coding: utf-8 -*-
import requests
import re
import json
from bs4 import BeautifulSoup

BASE_URL = "https://hmgyy.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

TYPE_MAP = {"dy": "1", "dsj": "2", "zy": "3", "dj": "4", "dm": "5"}


def get_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = 'utf-8'
        return r.text
    except Exception as e:
        print(f"fetch err: {url}, {e}")
        return ""


def parse_video_list(html):
    soup = BeautifulSoup(html, 'html.parser')
    videos = []
    for a in soup.select('a.video'):
        href = a.get('href', '')
        vod_id = href.replace('/details/', '').strip('/')
        img_box = a.select_one('.img-box')
        vod_pic = ''
        if img_box:
            vod_pic = img_box.get('data', '')
            if not vod_pic:
                style = img_box.get('style', '')
                m = re.search(r'url\(["\']?([^"\')\s]+)', style)
                if m:
                    vod_pic = m.group(1)
        if vod_pic and not vod_pic.startswith('http'):
            vod_pic = BASE_URL + vod_pic
        vod_name = ''
        title_el = a.select_one('.title p')
        if title_el:
            vod_name = title_el.text.strip()
        vod_remarks = ''
        desc_el = a.select_one('.desc .desc')
        if not desc_el:
            desc_el = a.select_one('.desc')
        if desc_el:
            vod_remarks = desc_el.text.strip()
            if vod_remarks and vod_name and vod_remarks.startswith(vod_name):
                vod_remarks = vod_remarks[len(vod_name):].strip()
        if vod_id and vod_name:
            videos.append({
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_remarks": vod_remarks,
            })
    return videos


class Spider:

    def __init__(self):
        self.name = "hmgyy"

    def init(self, extend=""):
        pass

    def getDependence(self):
        return []

    def homeContent(self, filter):
        html = get_html(BASE_URL)
        return {
            "class": [
                {"type_id": "1", "type_name": "電影"},
                {"type_id": "2", "type_name": "劇集"},
                {"type_id": "3", "type_name": "綜藝"},
                {"type_id": "4", "type_name": "短劇"},
                {"type_id": "5", "type_name": "動漫"},
            ],
            "list": parse_video_list(html)[:24],
        }

    def homeVideoContent(self):
        return {"list": parse_video_list(get_html(BASE_URL))}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if pg else 1
        type_path = "dy"
        for k, v in TYPE_MAP.items():
            if v == str(tid):
                type_path = k
                break
        url = f"{BASE_URL}/type/{type_path}"
        if pg > 1:
            url += f"?page={pg}"
        videos = parse_video_list(get_html(url))
        return {
            "list": videos,
            "page": pg,
            "pagecount": 999,
            "limit": len(videos),
            "total": len(videos) * 999,
        }

    def detailContent(self, ids):
        vod_id = ids[0] if ids else ""
        html = get_html(f"{BASE_URL}/details/{vod_id}")
        soup = BeautifulSoup(html, 'html.parser')

        vod_name = ""
        vod_pic = ""
        vod_content = ""
        vod_remarks = ""
        vod_year = ""

        h1 = soup.select_one('.details h1')
        if h1:
            vod_name = h1.text.strip()

        img = soup.select_one('.details-img')
        if img:
            vod_pic = img.get('src', '')
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = BASE_URL + vod_pic

        for item in soup.select('.info'):
            text = item.text.strip()
            if 'jianjie' in text or '\u7b80\u4ecb' in text:
                vod_content = text.split(':', 1)[-1].strip()
            elif 'year' in text.lower() or '\u5e74\u4efd' in text:
                vod_year = text.split(':', 1)[-1].strip()
            elif 'status' in text.lower() or '\u72b6\u6001' in text:
                vod_remarks = text.split(':', 1)[-1].strip()

        play_from = []
        play_url = []

        m = re.search(r'episodesData\s*=\s*(\{.*?\});', html, re.DOTALL)
        if m:
            try:
                s = m.group(1)
                s = re.sub(r'//[^\n]*', '', s)
                s = s.replace('\\/', '/')
                s = re.sub(r'([\{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', s)
                s = re.sub(r',\s*\}', '}', s)
                s = re.sub(r',\s*\]', ']', s)
                ep = json.loads(s)
                for ln, eps in ep.items():
                    play_from.append(ln)
                    parts = []
                    for e in eps:
                        pn = e.get('name', '')
                        pp = e.get('path', '')
                        rm = re.search(r'/player/(\d+)/(\d+)', pp)
                        if rm:
                            parts.append(f"{pn}${rm.group(1)}-{rm.group(2)}")
                    if parts:
                        play_url.append("#".join(parts))
            except Exception as ex:
                print(f"episodesData parse err: {ex}")

        if not play_from:
            play_from = ["line1"]
            play_url = [f"play${vod_id}-1"]

        return {"list": [{
            "vod_id": vod_id,
            "vod_name": vod_name,
            "vod_pic": vod_pic,
            "vod_content": vod_content,
            "vod_remarks": vod_remarks,
            "vod_year": vod_year,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url),
        }]}

    def searchContent(self, key, quick, pg=1):
        pg = int(pg) if pg else 1
        url = f"{BASE_URL}/search?kw={key}"
        if pg > 1:
            url += f"&page={pg}"
        return {"list": parse_video_list(get_html(url))}

    def playerContent(self, flag, id, vipFlags):
        parts = id.split('-')
        vod_id = parts[0]
        ep = parts[1] if len(parts) > 1 else "1"
        html = get_html(f"{BASE_URL}/player/{vod_id}/{ep}")

        m3u8 = re.search(r'["\'](https?://[^"\']*\.m3u8[^"\']*)', html)
        if m3u8:
            return {"parse": 0, "url": m3u8.group(1)}
        mp4 = re.search(r'["\'](https?://[^"\']*\.mp4[^"\']*)', html)
        if mp4:
            return {"parse": 0, "url": mp4.group(1)}
        iframe = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html)
        if iframe:
            src = iframe.group(1)
            if '.m3u8' in src or '.mp4' in src:
                return {"parse": 0, "url": src}
            return {"parse": 1, "url": src}
        video = re.search(r'<video[^>]*src=["\']([^"\']+)["\']', html)
        if video:
            return {"parse": 0, "url": video.group(1)}
        return {"parse": 1, "url": f"{BASE_URL}/player/{vod_id}/{ep}"}


def getClassName():
    return Spider