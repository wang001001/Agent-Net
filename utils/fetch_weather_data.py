import requests
import gzip
import json
# Adjust import path for script execution
import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
# Direct constants (avoid importing spider_weather which pulls in MySQL)
API_KEY = "5ef0a47e161a4ea997227322317eae83"
BASE_URL = "https://m7487r6ych.re.qweatherapi.com/v7/weather/30d"
city_codes = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "深圳": "101280601",
}

def fetch_weather_data(city, location):
    """Fetch 30‑day weather forecast for a specific city.

    Parameters
    ----------
    city: str
        Human readable city name (used for logging).
    location: str
        City code required by the QWeather API.
    """
    headers = {
        "X-QW-Api-Key": API_KEY,
        "Accept-Encoding": "gzip",
    }
    url = f"{BASE_URL}?location={location}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        # QWeather may return gzip‑compressed payload. ``requests`` will not
        # automatically decompress when ``Accept-Encoding`` is set, so we
        # handle it manually.
        if response.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(response.content).decode("utf-8")
        else:
            data = response.text
        return json.loads(data)
    except requests.RequestException as e:
        print(f"请求 {city} 天气数据失败: {e}")
        return None
    except json.JSONDecodeError as e:
        # 报错时输出部分响应内容帮助排查
        print(
            f"{city} JSON 解析错误: {e}, 响应内容: {response.text[:500]}..."
        )
        return None
    except gzip.BadGzipFile:
        # 如果 gzip 解压失败，尝试直接解析原文本
        print(f"{city} 数据未正确解压 尝试直接解析: {response.text[:500]}...")
        return json.loads(response.text) if response.text else None

if __name__ == "__main__":
    weather_data = fetch_weather_data("北京", city_codes["北京"])
    print(weather_data)
    print("解析成功！")
