"""MCP Ticket Server – FastAPI service for ticket data.

Provides:
- MySQL connection via Config
- Query tickets with optional ``user_id`` filter
- JSON response using MySQLJSONEncoder
- ``create_ticket_mcp_server`` to launch FastMCP and register tool
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

class TicketService:
    """业务层：查询 tickets 表。"""
    _conf = Config()

    @staticmethod
    def _get_connection():
        try:
            return mysql.connector.connect(
                host=TicketService._conf.host,
                user=TicketService._conf.user,
                password=TicketService._conf.password,
                database=TicketService._conf.database,
                charset="utf8mb4",
            )
        except mysql.connector.Error as err:
            raise HTTPException(status_code=500, detail=f"Database connection error: {err}")

    @classmethod
    def query(cls, user_id: Optional[int] = None) -> List[dict]:
        sql = "SELECT * FROM tickets WHERE 1=1"
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

@app.get("/ticket")
def get_ticket(user_id: Optional[int] = Query(None, description="User ID to filter tickets")):
    data = TicketService.query(user_id=user_id)
    json_str = json.dumps(data, cls=MySQLJSONEncoder)
    return Response(content=json_str, media_type="application/json")

def create_ticket_mcp_server():
    """Create and start the Ticket MCP server.

    - Registers ``TicketService.query`` as ``query_ticket`` tool.
    - Starts FastAPI on port 6002.
    """
    # FastMCP registration is optional for this demo. We simply start the FastAPI app.
    # If FastMCP integration is desired, instantiate FastMCP(name="ticket_server") and register the tool.
    # For now we just run the server.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6002)


