import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.spider_weather import connect_db

def show():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT city, fx_date, update_time FROM weather_data ORDER BY city, fx_date LIMIT 5')
    rows = cur.fetchall()
    for r in rows:
        print(r)
    cur.close()
    conn.close()

if __name__ == '__main__':
    show()
