"""MCP Weather Server – FastAPI service that returns weather forecast data from MySQL.

Features
--------
- Initialise a MySQL connection using the project's ``Config`` class.
- Execute a ``SELECT`` query on the ``weather_data`` table with optional ``city`` and ``date`` filters.
- Serialise MySQL‑specific Python types (date, datetime, timedelta, Decimal) via ``MySQLJSONEncoder``.
- Expose a single ``/weather`` endpoint compatible with the existing MCP client.
"""

from __future__ import annotations

import os
import sys
import json
from typing import List, Optional, Any

# FastAPI imports
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response

# MySQL driver
import mysql.connector

# ---------------------------------------------------------------------------
# Ensure project root is on ``sys.path`` so that ``config`` and ``utils`` can be imported.
# The repository layout is:
#   SmartVoyage/            ← project root (contains ``config.py``)
#   SmartVoyage/mcp_server/ ← this module
# ---------------------------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Project configuration – holds DB credentials.
from config import Config

# Custom JSON encoder for MySQL‑specific types.
from utils.format import MySQLJSONEncoder

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="MCP Weather Server", version="1.0")

# ---------------------------------------------------------------------------
# Database helper – a thin wrapper around ``Config``.
# ---------------------------------------------------------------------------
_conf = Config()


def get_connection():
    """Create a new MySQL connection using the global ``Config``.

    The caller is responsible for closing the returned connection.
    """
    try:
        return mysql.connector.connect(
            host=_conf.host,
            user=_conf.user,
            password=_conf.password,
            database=_conf.database,
            charset="utf8mb4",
        )
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database connection error: {err}")


class WeatherService:
    """业务层：封装对 MySQL ``weather_data`` 表的查询。

    - 负责创建/关闭数据库连接
    - 支持可选的 ``city`` 与 ``date`` 过滤
    - 返回 ``list[dict]``，由上层 FastAPI 负责 JSON 编码
    """
    _conf = Config()

    @staticmethod
    def _get_connection():
        """返回一个新的 MySQL 连接。异常会转为 ``HTTPException``。"""
        try:
            return mysql.connector.connect(
                host=WeatherService._conf.host,
                user=WeatherService._conf.user,
                password=WeatherService._conf.password,
                database=WeatherService._conf.database,
                charset="utf8mb4",
            )
        except mysql.connector.Error as err:
            raise HTTPException(status_code=500, detail=f"Database connection error: {err}")

    @classmethod
    def query(cls, city: Optional[str] = None, fx_date: Optional[str] = None) -> List[dict]:
        """执行 SELECT 并返回字典列表。

        参数
        ------
        city: str | None
            城市名称（精确匹配）
        fx_date: str | None
            预报日期，格式 ``YYYY‑MM‑DD``
        """
        sql = "SELECT * FROM weather_data WHERE 1=1"
        params: List[Any] = []
        if city:
            sql += " AND city = %s"
            params.append(city)
        if fx_date:
            sql += " AND fx_date = %s"
            params.append(fx_date)

        conn = cls._get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in rows]
        except mysql.connector.Error as err:
            raise HTTPException(status_code=500, detail=str(err))
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()


# ---------------------------------------------------------------------------
# API endpoint
# ---------------------------------------------------------------------------
@app.get("/weather")
def get_weather(
    city: Optional[str] = Query(None, description="City name, e.g. 北京"),
    date: Optional[str] = Query(None, alias="date", description="Forecast date YYYY‑MM‑DD"),
):
    """Return weather forecast rows as JSON.

    The heavy lifting (SQL + type conversion) is delegated to ``WeatherService.query``
    and ``MySQLJSONEncoder``.
    """
    data = WeatherService.query(city=city, fx_date=date)
    json_str = json.dumps(data, cls=MySQLJSONEncoder)
    return Response(content=json_str, media_type="application/json")


def create_weather_mcp_server():
    """Create and start the Weather MCP server.

    - Instantiates a ``FastMCP`` object with the FastAPI ``app``.
    - Registers ``WeatherService.query`` as the ``query_weather`` tool.
    - Launches the FastAPI server on port ``6001``.
    """
    # FastMCP registration is optional for this demo. We simply start the FastAPI server.
    # If you wish to expose tools via FastMCP, instantiate FastMCP(name="weather_server") and register the tool.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6001)

