"""MCP Ticket Server – FastAPI service for ticket data.

Provides:
- MySQL connection via Config
- Unified endpoint for three ticket categories (train, concert, flight)
- JSON response using MySQLJSONEncoder
"""

from __future__ import annotations

import os, sys, json
from typing import List, Optional, Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import mysql.connector

# Ensure project root is on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from utils.format import MySQLJSONEncoder

app = FastAPI(title="MCP Ticket Server", version="1.0")
_conf = Config()


# ---------- Base Service ----------
class BaseTicketService:
    """抽象基类，子类只需要实现 `table_name`（对应数据库表名）。"""

    _conf = Config()
    table_name: str = ""  # placeholder to satisfy type checkers

    @staticmethod
    def _get_connection():
        try:
            return mysql.connector.connect(
                host=BaseTicketService._conf.host,
                user=BaseTicketService._conf.user,
                password=BaseTicketService._conf.password,
                database=BaseTicketService._conf.database,
                charset="utf8mb4",
            )
        except mysql.connector.Error as err:
            raise HTTPException(
                status_code=500, detail=f"Database connection error: {err}"
            )

    @classmethod
    def query(cls, user_id: Optional[int] = None) -> List[dict]:
        sql = f"SELECT * FROM {cls.table_name} WHERE 1=1"
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
            columns = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )
            return [dict(zip(columns, row)) for row in rows]
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()


# ---------- Specific Services ----------
class TrainTicketService(BaseTicketService):
    table_name = "train_tickets"


class ConcertTicketService(BaseTicketService):
    table_name = "concert_tickets"


class FlightTicketService(BaseTicketService):
    table_name = "flight_tickets"


# ---------- API Endpoint ----------
@app.get("/ticket")
def get_ticket(
    user_id: Optional[int] = Query(None, description="User ID to filter tickets"),
    category: Optional[str] = Query(
        None,
        description="Ticket category: train | concert | flight",
        regex="^(train|concert|flight)$",
    ),
):
    """根据 category 动态查询对应票务表。若未提供 category 返回 400 错误。"""
    if not category:
        raise HTTPException(
            status_code=400, detail="Missing required query param: category"
        )
    service_map = {
        "train": TrainTicketService,
        "concert": ConcertTicketService,
        "flight": FlightTicketService,
    }
    svc = service_map[category]
    data = svc.query(user_id=user_id)
    json_str = json.dumps(data, cls=MySQLJSONEncoder, ensure_ascii=False)
    return Response(content=json_str, media_type="application/json")


# ---------- Run Helper ----------
def create_ticket_mcp_server():
    """启动 Ticket MCP（仅 FastAPI）"""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=6002)
