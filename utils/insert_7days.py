import mysql.connector
from config import Config
from fetch_weather_data import fetch_weather_data, city_codes


def connect_db():
    cfg = Config()
    return mysql.connector.connect(
        host=cfg.host,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        charset="utf8mb4",
    )

def insert_7days():
    conn = connect_db()
    cursor = conn.cursor()
    insert_sql = (
        "INSERT INTO weather_data (city, fx_date, sunrise, sunset, moonrise, moonset, moon_phase, "
        "moon_phase_icon, temp_max, temp_min, icon_day, text_day, icon_night, text_night, "
        "wind360_day, wind_dir_day, wind_scale_day, wind_speed_day, wind360_night, "
        "wind_dir_night, wind_scale_night, wind_speed_night, precip, uv_index, humidity, "
        "pressure, vis, cloud, update_time) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )

    for city, code in city_codes.items():
        data = fetch_weather_data(city, code)
        if not data or data.get('code') != '200':
            print(f"Failed to get data for {city}")
            continue
        daily = data.get('daily', [])[:7]
        for day in daily:
            values = (
                city,
                day.get('fxDate'),
                day.get('sunrise'),
                day.get('sunset'),
                day.get('moonrise'),
                day.get('moonset'),
                day.get('moonPhase'),
                day.get('moonPhaseIcon'),
                day.get('tempMax'),
                day.get('tempMin'),
                day.get('iconDay'),
                day.get('textDay'),
                day.get('iconNight'),
                day.get('textNight'),
                day.get('wind360Day'),
                day.get('windDirDay'),
                day.get('windScaleDay'),
                day.get('windSpeedDay'),
                day.get('wind360Night'),
                day.get('windDirNight'),
                day.get('windScaleNight'),
                day.get('windSpeedNight'),
                day.get('precip'),
                day.get('uvIndex'),
                day.get('humidity'),
                day.get('pressure'),
                day.get('vis'),
                day.get('cloud'),
                # use the API's updateTime as our record update_time
                data.get('updateTime').replace('T', ' ').split('+')[0],
            )
            cursor.execute(insert_sql, values)
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    insert_7days()
    print("Inserted 7‑day forecast for first‑tier cities.")
