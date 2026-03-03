"""
Weather spider – 30‑day QWeather forecast → MySQL `weather_data` table.

Features
--------
* timezone‑aware handling (Asia/Shanghai)
* incremental update (skip if latest < 24 h)
* ON DUPLICATE KEY UPDATE to keep data fresh
* unified logger (project logger)
* simple schedule interface (run daily at 01:00 Shanghai time)
"""

import os
import sys
import json
import time
import logging
import schedule
import requests
import mysql.connector
import pytz
from datetime import datetime, timedelta

# --------------------------------------------------------------
# 项目根路径 & 配置
# --------------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config

conf = Config()
logger = logging.getLogger("spider_weather")  # 项目统一 logger

# --------------------------------------------------------------
# 常量 & 配置
# --------------------------------------------------------------
API_KEY = "89fde05dc05e4ab98f480a9cb8762cfe"
BASE_URL = "https://mq5b65rnwf.re.qweatherapi.com/v7/weather/30d"
TZ = pytz.timezone("Asia/Shanghai")

city_codes = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "深圳": "101280601",
}

# --------------------------------------------------------------
# DB 辅助
# --------------------------------------------------------------
def connect_db():
    """返回 MySQL 连接（使用 Config 中的 DB 参数）。"""
    return mysql.connector.connect(
        host=conf.host,
        user=conf.user,
        password=conf.password,
        database=conf.database,
        charset="utf8mb4",
    )

def get_latest_update_time(cursor, city: str):
    """查询 `weather_data` 中 city 最近的 update_time。返回 None 或 datetime（naive）。"""
    cursor.execute(
        "SELECT MAX(update_time) FROM weather_data WHERE city = %s",
        (city,),
    )
    latest = cursor.fetchone()[0]
    return latest

def should_update_data(latest_dt, *, force: bool = False, interval_hours: int = 24) -> bool:
    """判断是否需要重新抓取数据。"""
    if force:
        return True
    if not latest_dt:
        return True
    # DB 中的 datetime 为 naive，视为上海时区
    if latest_dt.tzinfo is None:
        latest_dt = TZ.localize(latest_dt)
    now = datetime.now(TZ)
    return (now - latest_dt).total_seconds() >= interval_hours * 3600

# --------------------------------------------------------------
# API 抓取
# --------------------------------------------------------------
def fetch_weather_data(city: str, location: str) -> dict | None:
    """请求单个城市的 30 天天气，返回解析后的 JSON。"""
    url = f"{BASE_URL}?location={location}"
    headers = {
        "X-QW-Api-Key": API_KEY,
        "Accept-Encoding": "gzip",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()  # requests 已自动解压 gzip
    except (requests.RequestException, json.JSONDecodeError) as exc:
        logger.error("Fetch failed for %s (%s): %s", city, location, exc)
        return None

# --------------------------------------------------------------
# DB 写入
# --------------------------------------------------------------
def store_weather_data(conn, cursor, city: str, payload: dict) -> None:
    """把单城市天气写入 `weather_data`（支持冲突更新）。"""
    if not payload or payload.get("code") != "200":
        logger.warning("%s 数据无效或返回错误码，跳过写入", city)
        return

    daily = payload.get("daily", [])
    # QWeather 返回的更新时间是 ISO 带时区字符串
    update_time = datetime.fromisoformat(
        payload["updateTime"].replace("Z", "+00:00")
    ).astimezone(TZ)

    insert_sql = """
        INSERT INTO weather_data (
            city, fx_date, sunrise, sunset, moonrise, moonset,
            moon_phase, moon_phase_icon, temp_max, temp_min,
            icon_day, text_day, icon_night, text_night,
            wind360_day, wind_dir_day, wind_scale_day, wind_speed_day,
            wind360_night, wind_dir_night, wind_scale_night, wind_speed_night,
            precip, uv_index, humidity, pressure, vis, cloud,
            update_time
        ) VALUES (
            %(city)s, %(fx_date)s, %(sunrise)s, %(sunset)s, %(moonrise)s, %(moonset)s,
            %(moon_phase)s, %(moon_phase_icon)s, %(temp_max)s, %(temp_min)s,
            %(icon_day)s, %(text_day)s, %(icon_night)s, %(text_night)s,
            %(wind360_day)s, %(wind_dir_day)s, %(wind_scale_day)s, %(wind_speed_day)s,
            %(wind360_night)s, %(wind_dir_night)s, %(wind_scale_night)s, %(wind_speed_night)s,
            %(precip)s, %(uv_index)s, %(humidity)s, %(pressure)s, %(vis)s, %(cloud)s,
            %(update_time)s
        )
        ON DUPLICATE KEY UPDATE
            sunrise=VALUES(sunrise), sunset=VALUES(sunset),
            moonrise=VALUES(moonrise), moonset=VALUES(moonset),
            moon_phase=VALUES(moon_phase), moon_phase_icon=VALUES(moon_phase_icon),
            temp_max=VALUES(temp_max), temp_min=VALUES(temp_min),
            icon_day=VALUES(icon_day), text_day=VALUES(text_day),
            icon_night=VALUES(icon_night), text_night=VALUES(text_night),
            wind360_day=VALUES(wind360_day), wind_dir_day=VALUES(wind_dir_day),
            wind_scale_day=VALUES(wind_scale_day), wind_speed_day=VALUES(wind_speed_day),
            wind360_night=VALUES(wind360_night), wind_dir_night=VALUES(wind_dir_night),
            wind_scale_night=VALUES(wind_scale_night), wind_speed_night=VALUES(wind_speed_night),
            precip=VALUES(precip), uv_index=VALUES(uv_index),
            humidity=VALUES(humidity), pressure=VALUES(pressure),
            vis=VALUES(vis), cloud=VALUES(cloud), update_time=VALUES(update_time);
    """

    try:
        for d in daily:
            values = {
                "city": city,
                "fx_date": datetime.strptime(d["fxDate"], "%Y-%m-%d").date(),
                "sunrise": d.get("sunrise"),
                "sunset": d.get("sunset"),
                "moonrise": d.get("moonrise"),
                "moonset": d.get("moonset"),
                "moon_phase": d.get("moonPhase"),
                "moon_phase_icon": d.get("moonPhaseIcon"),
                "temp_max": d.get("tempMax"),
                "temp_min": d.get("tempMin"),
                "icon_day": d.get("iconDay"),
                "text_day": d.get("textDay"),
                "icon_night": d.get("iconNight"),
                "text_night": d.get("textNight"),
                "wind360_day": d.get("wind360Day"),
                "wind_dir_day": d.get("windDirDay"),
                "wind_scale_day": d.get("windScaleDay"),
                "wind_speed_day": d.get("windSpeedDay"),
                "wind360_night": d.get("wind360Night"),
                "wind_dir_night": d.get("windDirNight"),
                "wind_scale_night": d.get("windScaleNight"),
                "wind_speed_night": d.get("windSpeedNight"),
                "precip": d.get("precip"),
                "uv_index": d.get("uvIndex"),
                "humidity": d.get("humidity"),
                "pressure": d.get("pressure"),
                "vis": d.get("vis"),
                "cloud": d.get("cloud"),
                "update_time": update_time,
            }
            cursor.execute(insert_sql, values)
        conn.commit()
        logger.info("%s 天气写入/更新成功（%d 条）", city, len(daily))
    except mysql.connector.Error as err:
        conn.rollback()
        logger.error("%s 写入异常: %s", city, err)

# --------------------------------------------------------------
# 主流程
# --------------------------------------------------------------
def update_weather(force: bool = False) -> None:
    """遍历所有城市，依据最新更新时间决定是否抓取并写库。"""
    with connect_db() as conn, conn.cursor() as cur:
        for city, loc in city_codes.items():
            latest = get_latest_update_time(cur, city)
            if should_update_data(latest, force=force):
                logger.info("开始更新 %s 天气数据", city)
                payload = fetch_weather_data(city, loc)
                if payload:
                    store_weather_data(conn, cur, city, payload)
            else:
                logger.debug("%s 数据已是最新（%s）", city, latest)

# --------------------------------------------------------------
# 调度（上海时间 01:00）
# --------------------------------------------------------------
def setup_scheduler() -> None:
    """每天上海时间 01:00 执行一次 `update_weather`。"""
    target = datetime.now(TZ).replace(hour=1, minute=0, second=0, microsecond=0)
    utc_time = target.astimezone(pytz.utc).time()
    schedule.every().day.at(utc_time.strftime("%H:%M")).do(update_weather)
    logger.info("天气爬虫调度已启动（每日 %s 北京时间）", target.strftime("%H:%M"))
    while True:
        schedule.run_pending()
        time.sleep(30)

# --------------------------------------------------------------
# 入口
# --------------------------------------------------------------
if __name__ == "__main__":
    # 防御性建表
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS weather_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city VARCHAR(50) NOT NULL,
        fx_date DATE NOT NULL,
        sunrise TIME, sunset TIME,
        moonrise TIME, moonset TIME,
        moon_phase VARCHAR(20), moon_phase_icon VARCHAR(10),
        temp_max INT, temp_min INT,
        icon_day VARCHAR(10), text_day VARCHAR(20),
        icon_night VARCHAR(10), text_night VARCHAR(20),
        wind360_day INT, wind_dir_day VARCHAR(20), wind_scale_day VARCHAR(10), wind_speed_day INT,
        wind360_night INT, wind_dir_night VARCHAR(20), wind_scale_night VARCHAR(10), wind_speed_night INT,
        precip DECIMAL(5,1), uv_index INT,
        humidity INT, pressure INT, vis INT, cloud INT,
        update_time DATETIME,
        UNIQUE KEY uq_city_date (city, fx_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    with connect_db() as conn, conn.cursor() as cur:
        cur.execute(create_table_sql)
        conn.commit()
        logger.info("weather_data 表已就绪")
    # 首次全量抓取（强制）
    update_weather(force=True)
    # 启动调度
    setup_scheduler()
