import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.spider_weather import connect_db
import mysql.connector

def ensure_table():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT DATABASE()')
    print('Current DB:', cur.fetchone())
    create_sql = '''
    CREATE TABLE IF NOT EXISTS weather_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city VARCHAR(50),
        fx_date DATE,
        sunrise VARCHAR(10),
        sunset VARCHAR(10),
        moonrise VARCHAR(10),
        moonset VARCHAR(10),
        moon_phase VARCHAR(20),
        moon_phase_icon VARCHAR(10),
        temp_max VARCHAR(10),
        temp_min VARCHAR(10),
        icon_day VARCHAR(10),
        text_day VARCHAR(50),
        icon_night VARCHAR(10),
        text_night VARCHAR(50),
        wind360_day VARCHAR(10),
        wind_dir_day VARCHAR(20),
        wind_scale_day VARCHAR(10),
        wind_speed_day VARCHAR(10),
        wind360_night VARCHAR(10),
        wind_dir_night VARCHAR(20),
        wind_scale_night VARCHAR(10),
        wind_speed_night VARCHAR(10),
        precip VARCHAR(10),
        uv_index VARCHAR(10),
        humidity VARCHAR(10),
        pressure VARCHAR(10),
        vis VARCHAR(10),
        cloud VARCHAR(10),
        update_time DATETIME
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;''' 
    cur.execute(create_sql)
    conn.commit()
    print('weather_data table ensured')
    cur.close()
    conn.close()

if __name__ == '__main__':
    ensure_table()
