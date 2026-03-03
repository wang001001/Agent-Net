@echo off
:: ==== 环境变量（可自行修改） ====
set MODEL_NAME=qwen-plus
set BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
set API_KEY=sk-sk-efe5b7e6d8384e86bdd50aa7066ab848
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root
set DB_PASSWORD=root
set DB_NAME=travel_rag

:: ==== 启动 MCP 服务 ====
start "MCP Weather" cmd /k uvicorn mcp_server.mcp_weather_server:app --reload --host 0.0.0.0 --port 8002
start "MCP Ticket"  cmd /k uvicorn mcp_server.mcp_ticket_server:app  --reload --host 0.0.0.0 --port 8003
start "MCP Order"   cmd /k uvicorn mcp_server.mcp_order_server:create_order_mcp_server --reload --host 0.0.0.0 --port 6003

:: ==== 启动 A2A Weather 代理 ====
start "Weather Agent" cmd /k python a2a_server/weather_server.py

:: ==== 启动 Streamlit 前端 ====
timeout /t 5 >nul
streamlit run app.py
