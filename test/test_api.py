import requests
import gzip
import json

# 配置 (使用自己的密钥)
API_KEY = "89fde05dc05e4ab98f480a9cb8762cfe"
url = "https://mq5b65rnwf.re.qweatherapi.com/v7/weather/30d?location=101010100"  # 北京30天预报
headers = {
    "X-QW-Api-Key": API_KEY,
    "Accept-Encoding": "gzip"  # 请求gzip 但不强制
}

try:
    print("正在请求API...")
    response = requests.get(url, headers=headers, timeout=10)
    data = response.text
    parsed_data = json.loads(data)
    print("直接解析成功！")
    print(parsed_data)
except requests.RequestException as e:
    print(f"直接解析失败哦: {e}")
