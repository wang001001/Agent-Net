import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import asyncio
import uuid
import streamlit as st
from python_a2a import AgentNetwork, Message, TextContent, MessageRole, Task
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain_openai.chat_models import ChatOpenAI
import json
from datetime import datetime
import pytz
import re  # 用于清理响应

from SmartVoyage.config import Config
from SmartVoyage.create_logger import logger
from SmartVoyage.main_prompts import SmartVoyagePrompts

conf = Config()

# 设置页面配置
st.set_page_config(page_title="基于A2A的SmartVoyage旅行助手系统", layout="wide", page_icon="🤖")

# 自定义 CSS 打造高端大气科技感 优化对比度
st.markdown("""
<style>
/* 聊天消息框样式 */
.stChatMessage {
    background-color: #2c3e50 !important;
    border-radius: 12px !important;
    padding: 15px !important;
    margin-bottom: 15px !important;
    box-shadow: 0 3px 6px rgba(0,0,0,0.2) !important;
}

/* 用户消息框稍亮 */
.stChatMessage.user {
    background-color: #34495e !important;
}

/* ✅ 核心：强制所有文字变为白色 (包括 markdown 内部) */
.stChatMessage .stMarkdown, 
.stChatMessage .stMarkdown p, 
.stChatMessage .stMarkdown span, 
.stChatMessage .stMarkdown div, 
.stChatMessage .stMarkdown strong, 
.stChatMessage .stMarkdown em, 
.stChatMessage .stMarkdown code {
    color: #ffffff !important; 
}

/* 如果你想让 emoji 图标更亮一点 */
.stChatMessage [data-testid="stChatMessageAvatarIcon"] {
    filter: brightness(1.2);
}
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_network" not in st.session_state:
    # 存储代理URL信息 便于查看
    st.session_state.agent_urls = {
        "WeatherQueryAssistant": "http://localhost:5005",
        "TicketQueryAssistant": "http://localhost:5006",
        "TicketOrderAssistant": "http://localhost:5007"
    }
    # 初始化网络
    network = AgentNetwork(name="Travel Assistant Network")
    network.add("WeatherQueryAssistant", "http://localhost:5005")
    network.add("TicketQueryAssistant", "http://localhost:5006")
    network.add("TicketOrderAssistant", "http://localhost:5007")
    st.session_state.agent_network = network
    # 加载配置并创建LLM
    st.session_state.llm = ChatOpenAI(
        model=conf.model_name,
        api_key=conf.api_key,
        base_url=conf.base_url,
        temperature=0.1,
    )
    # 存储对话历史用于意图识别
    st.session_state.conversation_history = ""

# 意图识别agent
def intent_agent(user_input):
    """使用 LLM 根据对话历史和当前查询识别用户意图"""
    chain = SmartVoyagePrompts.intent_prompt() | st.session_state.llm
    current_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
    intent_response = chain.invoke({
        "conversation_history": '\n'.join(st.session_state.conversation_history.split("\n")[-6:]),
        "query": user_input,
        "current_date": current_date
    }).content.strip()
    logger.info(f"意图识别原始响应: {intent_response}")
    # 清理响应：移除可能的 Markdown 代码块标记
    intent_response = re.sub(r'^```json\s*|\s*```$', '', intent_response).strip()
    logger.info(f"清理后响应: {intent_response}")
    intent_output = json.loads(intent_response)
    intents = intent_output.get("intents", [])
    user_queries = intent_output.get("user_queries", {})
    follow_up_message = intent_output.get("follow_up_message", "")
    logger.info(f"intents: {intents}||user_queries: {user_queries}||follow_up_message: {follow_up_message} ")
    return intents, user_queries, follow_up_message

# 主界面布局
st.title("🤖 基于A2A的SmartVoyage旅行智能助手")
st.markdown("欢迎体验智能对话！输入问题 系统将精准识别意图并提供服务 ")

# 两栏布局：左侧对话 右侧 Agent Card
col1, col2 = st.columns([2, 1])

# 左侧对话区域
with col1:
    st.subheader("💬 对话")
    # 显示历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 输入框
    if prompt := st.chat_input("请输入您的问题..."):
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.conversation_history += f"\nUser: {prompt}"

        # 获取 LLM 和当前日期
        llm = st.session_state.llm
        current_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')

        # 意图识别
        with st.spinner("正在分析您的意图..."):
            try:
                intents, user_queries, follow_up_message = intent_agent(prompt)
                if "out_of_scope" in intents:
                    response = follow_up_message
                    st.session_state.conversation_history += f"\nAssistant: {response}"
                elif follow_up_message != "":
                    response = follow_up_message
                    st.session_state.conversation_history += f"\nAssistant: {response}"
                else:
                    responses = []
                    routed_agents = []
                    for intent in intents:
                        logger.info(f"处理意图：{intent}")
                        if intent == "weather":
                            agent_name = "WeatherQueryAssistant"
                        elif intent in ["flight", "train", "concert"]:
                            agent_name = "TicketQueryAssistant"
                        elif intent == "order":
                            agent_name = "TicketOrderAssistant"
                        else:
                            agent_name = None

                        if intent == "attraction":
                            chain = SmartVoyagePrompts.attraction_prompt() | llm
                            rec_response = chain.invoke({"query": prompt}).content.strip()
                            responses.append(rec_response)
                        elif agent_name:
                            query_str = user_queries.get(intent, {})
                            logger.info(f"{agent_name} 查询：{query_str}")
                            try:
                                agent = st.session_state.agent_network.get_agent(agent_name)
                                chat_history = '\n'.join(st.session_state.conversation_history.split("\n")[-7:-1]) + f"\nUser: {query_str}"
                                message = Message(content=TextContent(text=chat_history), role=MessageRole.USER)
                                task = Task(id="task-" + str(uuid.uuid4()), message=message.to_dict())
                                raw_response = asyncio.run(agent.send_task_async(task))
                                logger.info(f"{agent_name} 原始响应: {raw_response}")
                                if raw_response.status.state == 'completed':
                                    agent_result = raw_response.artifacts[0]['parts'][0]['text']
                                else:
                                    agent_result = raw_response.status.message['content']['text']
                            except Exception as e:
                                logger.error(f"调用 {agent_name} 失败: {e}")
                                agent_result = f"调用 {agent_name} 失败，请检查服务是否启动。"

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
                    st.session_state.conversation_history += f"\nAssistant: {response}"

                # 显示助手响应
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except json.JSONDecodeError as json_err:
                logger.error("意图识别JSON解析失败")
                error_message = f"意图识别JSON解析失败：{str(json_err)} 请重试 "
                with st.chat_message("assistant"):
                    st.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                logger.error(f"处理异常: {str(e)}")
                error_message = f"处理失败：{str(e)} 请重试 "
                with st.chat_message("assistant"):
                    st.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# 右侧 Agent Card 区域
with col2:
    st.subheader("🛠️ AgentCard")
    for agent_name in st.session_state.agent_network.agents.keys():
        agent_card = st.session_state.agent_network.get_agent_card(agent_name)
        agent_url = st.session_state.agent_urls.get(agent_name, "未知地址")
        with st.expander(f"Agent: {agent_name}", expanded=False):
            st.markdown(f"<div class='card-title'>技能</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-content'>{agent_card.skills}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-title'>描述</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-content'>{agent_card.description}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-title'>地址</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-content'>{agent_url}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-title'>状态</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-content'>在线</div>", unsafe_allow_html=True)

# 页脚
st.markdown("---")
st.markdown('<div class="footer">Powered by 基于Agent2Agent的旅行助手系统 v2.0</div>', unsafe_allow_html=True)
