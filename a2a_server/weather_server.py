"""A2A Weather Agent Server

该模块实现了一个天气查询代理，使用 LLM 自动生成 SQL，调用 MCP Weather Server 获取数据，
并把结果以友好的中文文本返回给客户端。
"""

# -*- coding: utf-8 -*-
import os, sys, json, asyncio
# 添加项目根路径，以便导入内部模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config
from create_logger import logger
from datetime import datetime
import pytz
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from python_a2a import (
    A2AServer,
    run_server,
    AgentCard,
    AgentSkill,
    TaskStatus,
    TaskState,
)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

conf = Config()

# ---------------------------------------------------------------------------
# 初始化 LLM（使用项目配置的模型）
# ---------------------------------------------------------------------------
llm = ChatOpenAI(
    model=conf.model_name,
    base_url=conf.base_url,
    api_key=conf.api_key,
    temperature=0.1,
)

# ---------------------------------------------------------------------------
# 数据库表 schema（用于 Prompt）
# ---------------------------------------------------------------------------
TABLE_SCHEMA = """CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(50) NOT NULL COMMENT '城市名称',
    fx_date DATE NOT NULL COMMENT '预报日期',
    sunrise TIME COMMENT '日出时间',
    sunset TIME COMMENT '日落时间',
    moonrise TIME COMMENT '月升时间',
    moonset TIME COMMENT '月落时间',
    moon_phase VARCHAR(20) COMMENT '月相名称',
    moon_phase_icon VARCHAR(10) COMMENT '月相图标代码',
    temp_max INT COMMENT '最高温度',
    temp_min INT COMMENT '最低温度',
    icon_day VARCHAR(10) COMMENT '白天天气图标代码',
    text_day VARCHAR(20) COMMENT '白天天气描述',
    icon_night VARCHAR(10) COMMENT '夜间天气图标代码',
    text_night VARCHAR(20) COMMENT '夜间天气描述',
    wind360_day INT COMMENT '白天风向360角度',
    wind_dir_day VARCHAR(20) COMMENT '白天风向',
    wind_scale_day VARCHAR(10) COMMENT '白天风力等级',
    wind_speed_day INT COMMENT '白天风速 (km/h)',
    wind360_night INT COMMENT '夜间风向360角度',
    wind_dir_night VARCHAR(20) COMMENT '夜间风向',
    wind_scale_night VARCHAR(10) COMMENT '夜间风力等级',
    wind_speed_night INT COMMENT '夜间风速 (km/h)',
    precip DECIMAL(5,1) COMMENT '降水量 (mm)',
    uv_index INT COMMENT '紫外线指数',
    humidity INT COMMENT '相对湿度 (%)',
    pressure INT COMMENT '大气压强 (hPa)',
    vis INT COMMENT '能见度 (km)',
    cloud INT COMMENT '云量 (%)',
    update_time DATETIME COMMENT '数据更新时间',
    UNIQUE KEY unique_city_date (city, fx_date)
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='天气数据表';"""

# ---------------------------------------------------------------------------
# LLM 生成 SQL 的 Prompt（示例中已对大括号进行转义）
# ---------------------------------------------------------------------------
SQL_PROMPT = ChatPromptTemplate.from_template(
    """
系统提示：你是一个专业的天气SQL生成器，需要从对话历史 (含用户的问题) 中提取关键信息，然后基于 `weather_data` 表生成对应的 SELECT 语句。
- 当用户想查询天气时，至少需要 **城市** 与 **日期** 信息。如果对话中缺少必要信息，请返回如下 JSON（示例），并在 `message` 中给出明确的追问。
  {{"status": "input_required", "message": "请提供具体的需要查询的日期，例如 '2025-07-30'"}}
- 若对话与天气无关，返回类似的 JSON 并提示需要天气相关查询。
- 当信息齐全时，仅返回纯 SQL（不含任何包装字符）。

示例：
- 对话: user: 北京 2025-07-30
  输出: SELECT city, fx_date, temp_max, temp_min, text_day, text_night, humidity, wind_dir_day, precip FROM weather_data WHERE city = '北京' AND fx_date = '2025-07-30'
- 对话: user: 上海未来3天的天气
  输出: SELECT city, fx_date, temp_max, temp_min, text_day, text_night, humidity, wind_dir_day, precip FROM weather_data WHERE city = '上海' AND fx_date BETWEEN '2025-07-30' AND '2025-08-01' ORDER BY fx_date
- 对话: user: 北京的天气
  输出: {{"status": "input_required", "message": "请提供具体的需要查询的日期，例如 '2025-07-30'"}}

weather_data 表结构：
{table_schema_string}

对话历史（最新的在最前）：
{conversation}

当前日期（Asia/Shanghai）: {current_date}
    """
)

# ---------------------------------------------------------------------------
# 辅助函数 – 通过 MCP 调用查询
# ---------------------------------------------------------------------------
async def get_weather(sql: str):
    """使用 MCP 的 streamable http 接口执行 `query_weather` 工具并返回原始响应。"""
    try:
        async with streamablehttp_client("http://127.0.0.1:8002/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("query_weather", {"sql": sql})
                # MCP 可能返回 JSON 字符串或对象
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except Exception:
                        pass
                return result
    except Exception as e:
        logger.error(f"MCP 查询出错: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# AgentCard 定义（描述本代理）
# ---------------------------------------------------------------------------
agent_card = AgentCard(
    name="WeatherQueryAssistant",
    description="基于 LLM 自动生成 SQL 并调用 MCP Weather Server 的天气查询智能体",
    url="http://localhost:5005",
    version="1.0.0",
    capabilities={"streaming": True, "memory": True},
    skills=[
        AgentSkill(
            name="execute weather query",
            description="执行天气查询，返回天气数据库结果，支持自然语言输入",
            examples=["北京 2025-07-30 天气", "上海未来5天", "今天天气如何"],
        )
    ],
)

# ---------------------------------------------------------------------------
# 主服务器类
# ---------------------------------------------------------------------------
class WeatherQueryServer(A2AServer):
    def __init__(self):
        super().__init__(agent_card=agent_card)
        self.llm = llm
        self.sql_prompt = SQL_PROMPT
        self.schema = TABLE_SCHEMA

    # -----------------------------------------------------------------------
    # 生成 SQL（或输入需求 JSON）
    # -----------------------------------------------------------------------
    def generate_sql_query(self, conversation: str) -> dict:
        try:
            chain = self.sql_prompt | self.llm
            current_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
            raw_output = chain.invoke({
                "conversation": conversation,
                "current_date": current_date,
                "table_schema_string": self.schema,
            })
            output = str(getattr(raw_output, "content", raw_output)).strip()
            logger.info(f"LLM 原始输出: {output}")
            if output.startswith('{'):
                return json.loads(output)
            return {"status": "sql", "sql": output}
        except Exception as e:
            logger.error(f"SQL 生成失败: {e}")
            return {"status": "input_required", "message": "查询无效，请提供城市和日期"}

    # -----------------------------------------------------------------------
    # 任务处理逻辑
    # -----------------------------------------------------------------------
    def handle_task(self, task):
        # 1️⃣ 提取用户输入文字（假设在 task.message.content.text）
        content = (task.message or {}).get("content", {})
        conversation = content.get("text", "") if isinstance(content, dict) else ""
        logger.info(f"收到对话: {conversation}")

        try:
            gen_res = self.generate_sql_query(conversation)
            if gen_res.get("status") == "input_required":
                # 需要追问
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={"role": "agent", "content": {"text": gen_res["message"]}},
                )
                return task

            sql = gen_res.get("sql")
            if not sql:
                task.status = TaskStatus(state=TaskState.FAILED,
                                          message={"role": "agent", "content": {"text": "未生成有效的 SQL"}})
                return task
            logger.info(f"生成的 SQL: {sql}")
            # 2️⃣ 调用 MCP（异步）
            mcp_result = asyncio.run(get_weather(sql))
            logger.info(f"MCP 返回: {mcp_result}")

            # 统一处理返回结构：若为 dict 按约定字段读取；若为 list 直接视为成功数据
            if isinstance(mcp_result, dict):
                status = mcp_result.get("status")
                if status == "success":
                    data = mcp_result.get("data", [])
                elif status == "no_data":
                    # 没有符合条件的天气数据（如查询日期过远）
                    msg = mcp_result.get("message", "暂无可用的天气数据，可能查询的日期超出预报范围。请尝试查询最近 10 天内的日期。")
                    task.status = TaskStatus(
                        state=TaskState.INPUT_REQUIRED,
                        message={"role": "agent", "content": {"text": msg}},
                    )
                    return task
                else:
                    msg = mcp_result.get("message", "查询失败，请稍后再试")
                    task.status = TaskStatus(
                        state=TaskState.FAILED,
                        message={"role": "agent", "content": {"text": msg}},
                    )
                    return task
            else:
                # 假设返回的是 List[dict], 直接使用
                data = mcp_result

            # 构造友好文本
            lines = []
            for row in data:
                line = (
                    f"{row.get('city')} {row.get('fx_date')}: {row.get('text_day')} (夜间 {row.get('text_night')}) "
                    f"温度 {row.get('temp_min')}-{row.get('temp_max')}°C 湿度 {row.get('humidity')}% "
                    f"风向 {row.get('wind_dir_day')} 降水 {row.get('precip')}mm"
                )
                lines.append(line)
            # 当返回空列表时给出更友好的提示
            if not lines:
                response_text = "未查询到对应日期的天气数据。该日期可能超出预报范围（通常为最近 7–15 天），请尝试查询更近的日期。"
            else:
                response_text = "\n".join(lines)
            task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            return task
        except Exception as e:
            logger.error(f"任务处理异常: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={"role": "agent", "content": {"text": f"查询失败: {e}"}},
            )
            return task

# ---------------------------------------------------------------------------
# 运行入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    server = WeatherQueryServer()
    print("=== 天气查询服务器信息 ===")
    print(f"名称: {server.agent_card.name}")
    print(f"描述: {server.agent_card.description}")
    print("技能:")
    for skill in server.agent_card.skills:
        print(f"- {skill.name}: {skill.description}")
    run_server(server, host="127.0.0.1", port=5005)
