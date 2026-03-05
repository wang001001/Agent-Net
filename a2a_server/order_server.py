"""A2A Order Server – Handles order queries via MCP.

Workflow:
1. Receive user query string.
2. Optionally parse an integer `user_id` from the query.
3. Call the Order MCP endpoint ``http://127.0.0.1:6003/order`` with the `user_id` parameter.
4. Return the JSON response (or error dict) to the caller.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import re
import urllib.parse, urllib.request
from python_a2a import (
    A2AServer,
    run_server,
    AgentCard,
    AgentSkill,
    TaskStatus,
    TaskState,
)
from config import Config
from datetime import datetime
import pytz
from create_logger import logger

conf = Config()

# 初始化 LLM – 与其他 Agent 保持统一结构
llm = ChatOpenAI(
    model=conf.model_name,
    base_url=conf.base_url,
    api_key=conf.api_key,  # type: ignore
    temperature=0.1,
)

# 简单的 Prompt（这里仅用作占位，实际业务可自行扩展）
sql_prompt = ChatPromptTemplate.from_template(
    """
系统提示：你是一个订单SQL生成器，需要从用户自然语言查询中提取可能的 user_id（整数），
如果用户未提供 user_id，则返回 "SELECT * FROM orders"，否则返回带过滤的 SELECT 语句。
示例：
- 用户: 查询用户 5 的订单
  输出: SELECT * FROM orders WHERE user_id = 5
- 用户: 查看所有订单
  输出: SELECT * FROM orders
"""
)


def get_order(query: str):
    """Call Order MCP endpoint.
    Parses an optional integer `user_id` from the query and performs an HTTP GET.
    Returns the decoded JSON (list of orders) or an error dict.
    """
    try:
        user_id = None
        # Very naive integer extraction – sufficient for demo purposes
        match = re.search(r"(\d+)", query)
        if match:
            user_id = int(match.group(1))
        params = {}
        if user_id is not None:
            params["user_id"] = user_id
        query_str = urllib.parse.urlencode(params)
        url = "http://127.0.0.1:6003/order"
        if query_str:
            url = f"{url}?{query_str}"
        with urllib.request.urlopen(url) as resp:
            data = resp.read().decode()
        return json.loads(data)
    except Exception as e:
        logger.error(f"Order query error: {e}")
        return {"status": "error", "message": str(e)}


agent_card = AgentCard(
    name="OrderQueryAssistant",
    description="查询订单信息的代理，通过 MCP 与 MySQL 交互",
    url="http://localhost:5007",
    version="1.0.0",
    capabilities={"streaming": True, "memory": True},
    skills=[
        AgentSkill(
            name="query orders",
            description="根据 user_id 查询 orders 表，返回列表",
            examples=["查询用户 3 的订单", "查看所有订单"],
        )
    ],
)


class OrderQueryServer(A2AServer):
    def __init__(self):
        super().__init__(agent_card=agent_card)
        self.llm = llm
        self.sql_prompt = sql_prompt

    def generate_sql_query(self, conversation: str) -> dict:
        """使用 LLM 生成 SQL（或直接返回查询关键字），保持与其他 Agent 的统一接口。"""
        try:
            chain = self.sql_prompt | self.llm
            current_date = datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
                "%Y-%m-%d"
            )
            result = chain.invoke(
                {"conversation": conversation, "current_date": current_date}
            )
            output = result.content if hasattr(result, "content") else str(result)
            output = str(output).strip()
            logger.info(f"Order LLM 输出: {output}")
            if output.startswith("SELECT"):
                return {"status": "sql", "sql": output}
            return {"status": "sql", "sql": output}
        except Exception as e:
            logger.error(f"Order SQL 生成错误: {e}")
            return {"status": "input_required", "message": "请提供有效的订单查询"}

    def handle_task(self, task):
        content = (task.message or {}).get("content", {})
        conversation = content.get("text", "") if isinstance(content, dict) else ""
        logger.info(f"Order Agent 收到查询: {conversation}")
        gen = self.generate_sql_query(conversation)
        if gen.get("status") == "input_required":
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"text": gen["message"]}},
            )
            return task
        sql = gen["sql"]
        # 直接调用 MCP（Order MCP 仅支持 user_id）
        result = get_order(sql)
        if isinstance(result, dict) and result.get("status") == "error":
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {"text": result.get("message", "查询失败")},
                },
            )
            return task
        # 正常返回 JSON 列表，直接转为文字展示
        text = json.dumps(result, ensure_ascii=False, indent=2)
        task.artifacts = [{"parts": [{"type": "text", "text": text}]}]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task


if __name__ == "__main__":
    server = OrderQueryServer()
    print("=== Order Query Server ===")
    run_server(server, host="127.0.0.1", port=5007)
