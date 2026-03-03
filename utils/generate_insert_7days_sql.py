import json, gzip, requests, os

# Configuration for the QWeather API (first‑tier cities)
API_KEY = "5ef0a47e161a4ea997227322317eae83"
BASE_URL = "https://m7487r6ych.re.qweatherapi.com/v7/weather/30d"
city_codes = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "深圳": "101280601",
}

SQL_FILE = os.path.abspath('D:/My_predict_to_AIAGENT/My_Agent_propreject_EricHang_OnePreject/utils/insert_7days.sql')

# Helper to safely escape values for SQL (basic single‑quote escaping)
def esc(v):
    if v is None:
        return 'NULL'
    return "'" + str(v).replace("'", "''") + "'"

header = "INSERT INTO weather_data (city, fx_date, sunrise, sunset, moonrise, moonset, moon_phase, moon_phase_icon, temp_max, temp_min, icon_day, text_day, icon_night, text_night, wind360_day, wind_dir_day, wind_scale_day, wind_speed_day, wind360_night, wind_dir_night, wind_scale_night, wind_speed_night, precip, uv_index, humidity, pressure, vis, cloud, update_time) VALUES\n"
rows = []

for city, code in city_codes.items():
    url = f"{BASE_URL}?location={code}"
    headers = {"X-QW-Api-Key": API_KEY, "Accept-Encoding": "gzip"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    # The API may return gzip‑compressed JSON; handle both cases.
    if resp.headers.get('Content-Encoding') == 'gzip':
        data = json.loads(gzip.decompress(resp.content).decode('utf-8'))
    else:
        data = resp.json()
    if data.get('code') != '200':
        print(f"Failed to fetch data for {city}: {data.get('code')}")
        continue
    daily = data.get('daily', [])[:7]
    update_time = data.get('updateTime', '').replace('T', ' ').split('+')[0]
    for d in daily:
        rows.append(
            '(' + ', '.join([
                esc(city),
                esc(d.get('fxDate')),
                esc(d.get('sunrise')),
                esc(d.get('sunset')),
                esc(d.get('moonrise')),
                esc(d.get('moonset')),
                esc(d.get('moonPhase')),
                esc(d.get('moonPhaseIcon')),
                esc(d.get('tempMax')),
                esc(d.get('tempMin')),
                esc(d.get('iconDay')),
                esc(d.get('textDay')),
                esc(d.get('iconNight')),
                esc(d.get('textNight')),
                esc(d.get('wind360Day')),
                esc(d.get('windDirDay')),
                esc(d.get('windScaleDay')),
                esc(d.get('windSpeedDay')),
                esc(d.get('wind360Night')),
                esc(d.get('windDirNight')),
                esc(d.get('windScaleNight')),
                esc(d.get('windSpeedNight')),
                esc(d.get('precip')),
                esc(d.get('uvIndex')),
                esc(d.get('humidity')),
                esc(d.get('pressure')),
                esc(d.get('vis')),
                esc(d.get('cloud')),
                esc(update_time),
            ]) + ')')
        )

sql = header + ',\n'.join(rows) + ';'

with open(SQL_FILE, 'w', encoding='utf-8') as f:
    f.write(sql)
print('SQL file generated at', SQL_FILE)
print('\n--- Sample statements (first 3 rows) ---')
for r in rows[:3]:
    print(r + ';')
