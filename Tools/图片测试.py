import requests
import base64
import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# 目标图片 URL
url = "https://pic.zdpxxq.cn/upload_01/upload/20251114/2025111420430054690.jpeg"

# 你从 crypto_image.js 中提取的 Key 和 IV
# 16 字节的字符串，对应 AES-128-CBC
KEY = b'f5d965df75336270'
IV = b'97b60394abc2fbe1'

# 模拟常规浏览器请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def check_image_header(data):
    """通过文件头幻数判断图片真实格式"""
    if data.startswith(b'\xff\xd8'):
        return "jpeg"
    elif data.startswith(b'\x89PNG'):
        return "png"
    elif data.startswith(b'GIF8'):
        return "gif"
    elif data.startswith(b'RIFF') and b'WEBP' in data[8:12]:
        return "webp"
    return None

def decrypt_aes_cbc(ciphertext, key, iv):
    """执行 AES-CBC 解密并尝试去除 PKCS7 填充"""
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        try:
            # 网页端前端加密通常默认采用 PKCS7 填充，在此尝试去填充
            decrypted = unpad(decrypted, AES.block_size)
        except Exception:
            # 如果去填充失败（可能前端没用标准填充），则保留原样输出
            pass
        return decrypted
    except Exception as e:
        print(f"[-] AES 核心解密失败: {e}")
        return None

def main():
    print(f"[*] 正在拉取加密图片流:\n    {url}")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        raw_content = response.content
        print(f"[+] 下载完成，文件大小: {len(raw_content)} 字节")
    except Exception as e:
        print(f"[-] 下载失败，请检查网络或 URL 是否有效: {e}")
        sys.exit(1)

    if not raw_content:
        print("[-] 错误：下载的数据为空。")
        sys.exit(1)

    decrypted_data = None
    img_ext = "jpg"  # 默认缺省后缀

    # ---------------- 方案 A: 假设下载的文件就是纯二进制密文 ----------------
    print("[*] 尝试方案 A: 将输入视为原始二进制密文进行解密...")
    result_a = decrypt_aes_cbc(raw_content, KEY, IV)
    if result_a:
        fmt = check_image_header(result_a)
        if fmt:
            print(f"[+] 方案 A 成功！识别到有效的图片格式: {fmt.upper()}")
            decrypted_data = result_a
            img_ext = fmt

    # ---------------- 方案 B: 假设文件内部是 Base64 编码的文本密文 ----------------
    if not decrypted_data:
        print("[*] 方案 A 未能识别出图片头。尝试方案 B: 将输入视为 Base64 文本...")
        try:
            # 剔除可能存在的首尾引号或空格
            clean_content = raw_content.strip(b'"\' \n\r')
            decoded_ciphertext = base64.b64decode(clean_content)
            print(f"[+] Base64 解码成功，得到真实密文大小: {len(decoded_ciphertext)} 字节")
            
            result_b = decrypt_aes_cbc(decoded_ciphertext, KEY, IV)
            if result_b:
                fmt = check_image_header(result_b)
                if fmt:
                    print(f"[+] 方案 B 成功！识别到有效的图片格式: {fmt.upper()}")
                    img_ext = fmt
                else:
                    print("[!] 警告：方案 B 解密成功但未识别出标准图片头，将强制保存。")
                decrypted_data = result_b
        except Exception as e:
            print(f"[-] Base64 方案解析失败: {e}")

    # ---------------- 结果落盘 ----------------
    if decrypted_data:
        out_filename = f"decrypted_image.{img_ext}"
        with open(out_filename, "wb") as f:
            f.write(decrypted_data)
        print(f"[+] 解密文件已成功保存为: {out_filename}")
        print(f"[*] 明文前 16 字节 (Hex): {decrypted_data[:16].hex()}")
    else:
        print("[-] 抱歉，未能成功还原图片。请确认 crypto_image.js 中的 Key 和 IV 是否有动态导出的逻辑。")

if __name__ == "__main__":
    main()
