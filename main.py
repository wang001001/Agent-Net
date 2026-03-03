import asyncio
import json
import uuid
from datetime import datetime
import pytz
import re
from python_a2a import AgentNetwork, TextContent, Message, MessageRole, Task
from langchain_openai import ChatOpenAI

from SmartVoyage.config import Config
from SmartVoyage.create_logger import logger
from SmartVoyage.main_prompts import SmartVoyagePrompts

conf = Config()

# 初始化全局变量 用于模拟会话状态   这些变量替换了Streamlit的session_state
messages = []  # 存储对话历史消息列表 每个元素为字典{"role": "user/assistant", "content": "消息内容"}
agent_network = None  # 代理网络实例
llm = None  # 大语言模型实例
agent_urls = {}  # 存储代理的URL信息字典
conversation_history = ""  # 存储整个对话历史字符串 用于意图识别


def initialize_system():
    """
    初始化系统组件，包括代理网络、路由器、LLM和会话状态。
    核心逻辑：构建AgentNetwork，添加代理，创建路由器和LLM实例。
    """

    """
    初始化系统组件 包括代理网络、路由器、LLM和会话状态
    核心逻辑：构建AgentNetwork 添加代理 创建路由器和LLM
    """
    global agent_network, llm, agent_urls, conversation_history
    # 存储代理URL信息 便于查看
    agent_urls = {
        "WeatherQueryAssistant": "http://localhost:5005",  # 天气代理URL
        "TicketQueryAssistant": "http://localhost:5006",  # 票务代理URL
        "TicketOrderAssistant": "http://localhost:5007"  # 票务预定URL
    }
    # 创建代理网络
    network = AgentNetwork(name="旅行助手网络")
    network.add("WeatherQueryAssistant", "http://localhost:5005")
    network.add("TicketQueryAssistant", "http://localhost:5006")
    network.add("TicketOrderAssistant", "http://localhost:5007")
    agent_network = network

    # 加载配置并创建LLM
    llm = ChatOpenAI(
        model=conf.model_name,
        api_key=conf.api_key,
        base_url=conf.base_url,
        temperature=0.1,
    )

    # 初始化对话历史为空字符串
conversation_history = ""


def intent_agent(user_input):
    """意图识别 Agent

    作用：
    - 作为系统的大脑，分析用户查询意图。
    - 根据意图选择合适的子代理（如天气或票务代理），避免硬编码路由，提升系统的智能性和可扩展性。
    - 基于最近的对话历史对用户查询进行改写，使问题更明确，便于后续 Agent 处理。

    参数:
    - user_input: 当前用户的原始输入字符串。

    返回:
    - intents: 检测到的意图列表，例如 ["weather", "ticket"]。
    - user_queries: 改写后的用户查询字典，以意图为键。
    - follow_up_message: 如需进一步追问用户的提示信息。
    """
    global conversation_history, llm

    # 创建意图识别链：使用提示模板并接入 LLM
    chain = SmartVoyagePrompts.intent_prompt() | llm

    # 获取当前日期（Asia/Shanghai 时区），供 Prompt 使用
    current_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')

    # 只保留最近的几条对话，避免上下文过长
    recent_history = "\n".join(conversation_history.split("\n")[-6:])

    # 调用 LLM 进行意图识别
    intent_response = chain.invoke({
        "conversation_history": recent_history,
        "query": user_input,
        "current_date": current_date,
    }).content.strip()
    logger.info(f"意图识别原始响应: {intent_response}")

    # 清理响应：移除可能的 Markdown 代码块标记
    intent_response = re.sub(r'^```json\s*|\s*```$', '', intent_response).strip()
    logger.info(f"清理后响应: {intent_response}")

    # 将 JSON 字符串解析为对象
    intent_output = json.loads(intent_response)
    intents = intent_output.get("intents", [])
    user_queries = intent_output.get("user_queries", {})
    follow_up_message = intent_output.get("follow_up_message", "")
    logger.info(f"intents: {intents}||user_queries: {user_queries}||follow_up_message: {follow_up_message} ")

    return intents, user_queries, follow_up_message


def process_user_input(prompt):
    """处理用户输入：识别意图、调用代理、生成响应

    核心逻辑：使用 LLM 进行意图识别，根据意图路由到相应代理或直接生成内容。
    """
    global messages, conversation_history, llm, agent_network
    # 添加用户消息到历史
    messages.append({"role": "user", "content": prompt})
    conversation_history += f"\nUser: {prompt}"

    print("正在分析您的意图...")
    try:
        # 意图识别过程
        intents, user_queries, follow_up_message = intent_agent(prompt)

        # 根据意图输出生成响应
        if "out_of_scope" in intents:
            # 超出范围，直接返回大模型回复
            response = follow_up_message
            conversation_history += f"\nAssistant: {response}"
        elif follow_up_message != "":
            # 有追问消息，直接返回
            response = follow_up_message
            conversation_history += f"\nAssistant: {response}"
        else:
            responses = []
            routed_agents = []
            for intent in intents:
                logger.info(f"处理意图：{intent}")
                # 根据意图确定代理名称
                if intent == "weather":
                    agent_name = "WeatherQueryAssistant"
                elif intent in ["flight", "train", "concert"]:
                    agent_name = "TicketQueryAssistant"
                elif intent == "order":
                    agent_name = "TicketOrderAssistant"
                else:
                    agent_name = None

                if intent == "attraction":
                    # 景点推荐直接使用 LLM
                    chain = SmartVoyagePrompts.attraction_prompt() | llm
                    rec_response = chain.invoke({"query": prompt}).content.strip()
                    responses.append(rec_response)
                elif agent_name:
                    # 调用对应代理
                    query_str = user_queries.get(intent, {})
                    logger.info(f"{agent_name} 查询：{query_str}")
                    agent = agent_network.get_agent(agent_name)
                    chat_history = '\n'.join(conversation_history.split('\n')[-7:-1]) + f'\nUser: {query_str}'
                    message = Message(content=TextContent(text=chat_history), role=MessageRole.USER)
                    task = Task(id="task-" + str(uuid.uuid4()), message=message.to_dict())
                    raw_response = asyncio.run(agent.send_task_async(task))
                    logger.info(f"{agent_name} 原始响应: {raw_response}")
                    if raw_response.status.state == 'completed':
                        agent_result = raw_response.artifacts[0]['parts'][0]['text']
                    else:
                        agent_result = raw_response.status.message['content']['text']

                    # 根据代理类型汇总响应
                    if agent_name == "WeatherQueryAssistant":
                        chain = SmartVoyagePrompts.summarize_weather_prompt() | llm
                        final_response = chain.invoke({"query": query_str, "raw_response": agent_result}).content.strip()
                    elif agent_name == "TicketQueryAssistant":
                        chain = SmartVoyagePrompts.summarize_ticket_prompt() | llm
                        final_response = chain.invoke({"query": query_str, "raw_response": agent_result}).content.strip()
                    else:
                        final_response = agent_result

                    responses.append(final_response)
                    routed_agents.append(agent_name)
                else:
                    responses.append("暂不支持此意图 ")

            response = "\n\n".join(responses)
            if routed_agents:
                logger.info(f"路由到代理：{routed_agents}")
            conversation_history += f"\nAssistant: {response}"

        print(f"\n助手回复：\n{response}\n")
        messages.append({"role": "assistant", "content": response})
    except json.JSONDecodeError as json_err:
        logger.error("意图识别JSON解析失败")
        error_message = f"意图识别JSON解析失败：{str(json_err)} 请重试 "
        print(f"\n助手回复：\n{error_message}\n")
        messages.append({"role": "assistant", "content": error_message})
    except Exception as e:
        logger.error(f"处理异常: {str(e)}")
        error_message = f"处理失败：{str(e)} 请重试 "
        print(f"\n助手回复：\n{error_message}\n")
        messages.append({"role": "assistant", "content": error_message})


