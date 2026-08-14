import requests
import re
import time
import json
from urllib.parse import urlencode

# ============================ 🌟 用户配置 🌟 ============================
# 请替换为您自己的夸克网盘 Cookie
# 注意：整个Cookie应该写在一行，不要换行
COOKIE = ""#你的ck

SHARE_URL = "https://pan.quark.cn/s/67243ef26306"
# =======================================================================

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 quark-cloud-drive/3.2.0 Chrome/100.0.4896.160 Electron/18.3.5 Safari/537.36",
    "Referer": "https://drive.quark.cn/",
    "Cookie": COOKIE
})

# 缓存 stoken
stoken_cache = {}

def get_pwd_id(url):
    m = re.search(r"/s/([a-f0-9]{11,14})", url)
    return m.group(1) if m else None

def get_stoken(pwd_id):
    """获取夸克网盘 stoken (带缓存)"""
    if pwd_id in stoken_cache:
        return stoken_cache[pwd_id]

    token_url = "https://drive-pc.quark.cn/1/clouddrive/share/sharepage/token"
    data = {"pwd_id": pwd_id, "passcode": ""}

    r = session.post(token_url, json=data, params={"pr": "ucpro", "fr": "pc"})
    j = r.json()

    if j.get("code") != 0:
        raise Exception(f"获取stoken失败: {j.get('message')}")

    stoken = j["data"]["stoken"]
    stoken_cache[pwd_id] = stoken
    return stoken

def walk_quark_dir(pwd_id, stoken, pdir_fid="0", prefix_path="", video_files=[]):
    """递归遍历夸克网盘目录，获取所有视频文件"""
    detail_url = "https://drive-pc.quark.cn/1/clouddrive/share/sharepage/detail"
    params = {
        "pr": "ucpro", "fr": "pc",
        "pwd_id": pwd_id,
        "stoken": stoken,
        "pdir_fid": pdir_fid,
        "force": "0",
        "_page": 1,
        "_size": 200,
        "_sort": "file_name:asc"
    }

    r = session.get(detail_url, params=params)
    if r.status_code != 200:
        print(f"请求目录 {prefix_path} 失败: HTTP {r.status_code}")
        return

    data = r.json()
    if data.get("code") != 0:
        print(f"[错误] 获取文件列表失败: {data.get('message')}")
        return

    for f in data["data"].get("list", []):
        name = f["file_name"]

        # 路径名标准化：如果是根目录，不加前缀
        current_path = f"{prefix_path}/{name}" if prefix_path else name

        if f.get("dir"):
            # 递归进入子目录
            print(f"📁 发现文件夹: {current_path}")
            walk_quark_dir(pwd_id, stoken, f["fid"], current_path, video_files)
        else:
            # 检查是否为视频文件
            ext = name.lower().split(".")[-1]
            if ext in ["mp4", "mkv", "ts", "mov", "m2ts", "iso", "avi", "webm", "flv", "m4v"]:
                video_files.append({
                    'name': name,
                    'full_path': current_path,
                    'fid': f["fid"],
                    'size': f["size"],
                    'duration': f.get("duration", 0),
                    'share_token': f.get("share_fid_token", "")
                })

def get_quark_file_list(share_url):
    """主函数：获取夸克网盘分享链接中的所有视频文件列表 (递归)"""
    pwd_id = get_pwd_id(share_url)
    if not pwd_id:
        raise Exception("无法从链接中提取pwd_id")

    stoken = get_stoken(pwd_id)

    video_files = []
    # 从根目录 "0" 开始遍历
    walk_quark_dir(pwd_id, stoken, "0", "", video_files)

    return pwd_id, video_files

def clean_quark_file(fid):
    """清理转存的夸克网盘文件"""
    try:
        delete_url = "https://drive-pc.quark.cn/1/clouddrive/file/delete"
        data = {"action_type": 2, "filelist": [fid], "exclude_fids": []}
        session.post(delete_url, json=data, params={"pr": "ucpro", "fr": "pc"})
        print(f"   └─ 已自动清理转存文件，fid: {fid}")
    except Exception as e:
        print(f"   └─ 清理转存文件失败: {e}")

def process_quark_file(pwd_id, file_info):
    """转存文件，获取直链，并清理"""
    fid = file_info['fid']
    share_token = file_info['share_token']

    print(f"\n🎬 正在处理文件: {file_info['full_path']}")

    try:
        stoken = get_stoken(pwd_id)

        # 1. 转存文件
        save_url = "https://drive-pc.quark.cn/1/clouddrive/share/sharepage/save"
        save_data = {
            "fid_list": [fid],
            "fid_token_list": [share_token],
            "to_pdir_fid": "0",  # 转存到根目录
            "pwd_id": pwd_id,
            "stoken": stoken,
            "pdir_fid": "0",
            "scene": "link"
        }

        r = session.post(save_url, json=save_data, params={"pr": "ucpro", "fr": "pc"})
        j = r.json()
        if j.get("code") != 0:
            raise Exception(f"转存文件失败: {j.get('message')}")

        task_id = j["data"]["task_id"]
        print(f"   └─ 转存任务启动: {task_id}")

        # 2. 等待转存完成
        saved_fid = None
        for i in range(40):
            time.sleep(1)
            task_url = "https://drive-pc.quark.cn/1/clouddrive/task"
            task_params = {"pr": "ucpro", "fr": "pc", "task_id": task_id, "retry_index": 0}

            r = session.get(task_url, params=task_params)
            j = r.json()
            status = j["data"].get("status")

            if status == 2:  # 成功
                saved_fid = j["data"]["save_as"]["save_as_top_fids"][0]
                print(f"   └─ 转存成功，新 fid: {saved_fid}")
                break
            elif status in [3, 4]:  # 失败
                raise Exception("转存任务失败")
        else:
            raise Exception("转存超时")

        # 3. 获取下载直链
        download_url = "https://drive-pc.quark.cn/1/clouddrive/file/download"
        data = {"fids": [saved_fid]}

        r = session.post(download_url, json=data, params={"pr": "ucpro", "fr": "pc"})
        j = r.json()
        if not j.get("data"):
            raise Exception("获取下载链接失败")

        direct_url = j["data"][0]["download_url"]
        print("   └─ 获取直链成功！")

        # 4. 打印播放所需的 Headers
        print("\n🔥【播放信息 - 可直接用于播放器（如MXPlayer/VLC/TVBox）】")
        print(f"URL: {direct_url}")
        print("Headers:")
        print("   User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 quark-cloud-drive/3.2.0 Chrome/100.0.4896.160 Electron/18.3.5 Safari/537.36")
        print("   Referer: https://drive.quark.cn/")
        print(f"   Cookie: {COOKIE}")
        print("================================================================")

    except Exception as e:
        print(f"   └─ 处理失败: {e}")
        saved_fid = None
    finally:
        # 5. 清理转存的文件
        if saved_fid:
            clean_quark_file(saved_fid)

# ============================ 主程序执行 ============================
if __name__ == "__main__":
    print(f"正在测试夸克分享：{SHARE_URL}")
    print("----------------------------------------------------------------")

    try:
        # 步骤 1 & 2: 递归获取文件列表
        pwd_id, video_files = get_quark_file_list(SHARE_URL)

        if not video_files:
            print("\n❌ 错误：未在分享链接中找到任何视频文件。")
        else:
            print(f"\n✅ 成功找到 {len(video_files)} 个视频文件:")
            for i, f in enumerate(video_files):
                size_gb = f['size'] / (1024**3)
                print(f"   [{i+1}] {f['full_path']} ({size_gb:.2f} GB)")

            # 步骤 3, 4, 5, 6, 7: 处理第一个视频文件并获取直链
            print("\n----------------------------------------------------------------")
            print("▶️ 开始获取第一个视频文件的播放直链...")
            first_file = video_files[0]
            process_quark_file(pwd_id, first_file)

    except Exception as e:
        print(f"\n❌ 致命错误：{e}")
        print("请检查您的夸克网盘 Cookie 是否有效，或是否为超级会员。")