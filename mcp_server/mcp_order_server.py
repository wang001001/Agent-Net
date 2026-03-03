"""MCP Order Server – FastAPI service for order data.

提供：
- MySQL 连接（使用 Config）
- 可选 `user_id` 过滤的 orders 查询
- JSON 响应使用 MySQLJSONEncoder
- `create_order_mcp_server` 启动 FastAPI（端口 6003）
"""

from __future__ import annotations

import os, sys, json
from typing import List, Optional, Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import mysql.connector

# 将项目根加入路径以便导入 Config 与 utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from utils.format import MySQLJSONEncoder

app = FastAPI(title="MCP Order Server", version="1.0")
_conf = Config()

class OrderService:
    """业务层：查询 `orders` 表。"""
    _conf = Config()

    @staticmethod
    def _get_connection():
        try:
            return mysql.connector.connect(
                host=OrderService._conf.host,
                user=OrderService._conf.user,
                password=OrderService._conf.password,
                database=OrderService._conf.database,
                charset="utf8mb4",
            )
        except mysql.connector.Error as err:
            raise HTTPException(status_code=500, detail=f"Database connection error: {err}")

    @classmethod
    def query(cls, user_id: Optional[int] = None) -> List[dict]:
        sql = "SELECT * FROM orders WHERE 1=1"
        params: List[Any] = []
        if user_id is not None:
            sql += " AND user_id = %s"
            params.append(user_id)
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

@app.get("/order")
def get_order(user_id: Optional[int] = Query(None, description="User ID to filter orders")):
    data = OrderService.query(user_id=user_id)
    json_str = json.dumps(data, cls=MySQLJSONEncoder)
    return Response(content=json_str, media_type="application/json")

def create_order_mcp_server():
    """启动 Order MCP 服务器（仅 FastAPI，端口 6003）。"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6003)
