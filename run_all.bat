@echo off

:: Start WeatherQueryAssistant server in a separate window
start "Weather Server" cmd /c "python a2a_server\weather_server.py"

:: Optionally start other services (e.g., MCP servers) here
rem start "MCP Weather" cmd /c "uvicorn mcp_server.mcp_weather_server:app --port 8000"

:: Run the main CLI interface
python main.py
