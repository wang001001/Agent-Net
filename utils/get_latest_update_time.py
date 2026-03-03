import mysql.connector
from config import Config

def connect_db():
    """Create and return a MySQL connection using project Config."""
    cfg = Config()
    return mysql.connector.connect(
        host=cfg.host,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        charset="utf8mb4",
    )

def get_latest_update_time(cursor, city: str):
    """Return the most recent `update_time` for the given city in `weather_data`.

    Parameters
    ----------
    cursor : mysql.connector.cursor
        Active cursor from a MySQL connection.
    city : str
        城市名称，例如 "北京"。
    """
    sql = "SELECT MAX(update_time) FROM weather_data WHERE city = %s"
    cursor.execute(sql, (city,))
    result = cursor.fetchone()
    # result is a tuple like (datetime,) or (None,)
    return result[0] if result else None

if __name__ == "__main__":
    # 建立数据库连接
    conn = connect_db()
    cursor = conn.cursor()

    # 获取北京城市的最新更新的时间日期
    latest = get_latest_update_time(cursor, "北京")
    print("北京最新更新日期:", latest)

    # 关闭数据库连接
    cursor.close()
    conn.close()
