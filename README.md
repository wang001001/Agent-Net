# 🚀 SmartVoyage — AI 驱动的旅行助手

<p align="center">
  <img src="https://via.placeholder.com/500x200?text=SmartVoyage" alt="SmartVoyage Banner" width="500"/>
</p>

<p align="center">
  <a href="https://github.com/wang001001/Agent-Net/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/wang001001/Agent-Net/ci.yml?branch=main&style=for-the-badge" alt="CI Status"/></a>
  <a href="https://github.com/wang001001/Agent-Net/releases"><img src="https://img.shields.io/github/v/release/wang001001/Agent-Net?style=for-the-badge" alt="Release"/></a>
  <a href="https://github.com/wang001001/Agent-Net/blob/main/LICENSE"><img src="https://img.shields.io/github/license/wang001001/Agent-Net?style=for-the-badge" alt="License"/></a>
</p>

---

## 🗺️ 项目概览

**SmartVoyage** 通过 **Agent‑to‑Agent (A2A)** 架构与 **FastAPI** 微服务，提供一个可交互的旅行助理。用户可在 **CLI** 或 **Streamlit** 界面输入自然语言请求，系统将完成以下步骤：

1. **意图解析** – 使用 LLM（如 OpenAI、Anthropic）把自然语言转化为具体业务意图（天气、票务、订单等）。
2. **代理调度** – 根据意图启动相应的 Python‑A2A 代理（Weather、Ticket、Order）。
3. **MCP 通信** – 代理通过 HTTP 与 FastAPI **MCP**（Micro‑Context‑Protocol）服务交互，查询 MySQL 数据库获取真实信息。
4. **结果呈现** – 将结构化数据进行汇总、格式化后返回给用户。

该闭环实现了 **自然语言 → 意图解析 → 多代理协作 → 微服务 → 持久化**，可作为 AI 助手或企业内部知识服务的示例项目。

---

## ✨ 主要特性

- **模块化**：天气、票务、订单等业务划分为独立 A2A 代理，新增功能只需实现新代理。
- **统一协议**：使用 **FastAPI** 实现的 **MCP** 为代理与微服务之间提供统一的 HTTP 接口，解耦业务逻辑。
- **完整示例**：从前端 UI、CLI、意图识别、代理调度、MCP 交互到 MySQL 持久化，一站式参考。
- **多语言支持**：项目文档、代码注释均采用中英文双语，降低学习门槛。

---

## 🚀 快速开始 (TL;DR)

```bash
# 1. 克隆仓库（已在本地，下面直接说明）
# git clone https://github.com/wang001001/Agent-Net.git
# cd Agent-Net

# 2. 创建并激活虚拟环境（推荐 conda）
conda create -n smartvoyage python=3.13 -y
conda activate smartvoyage

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 .env（请勿提交）
cat > .env <<EOF
MODEL_NAME=gpt-4o-mini
API_KEY=your-llm-api-key
BASE_URL=https://api.openai.com/v1
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-pass
DB_NAME=smart_voyage
EOF

# 5. 初始化数据库
mysql -u $DB_USER -p$DB_PASSWORD -h $DB_HOST $DB_NAME < sql/create_table.sql

# 6. 启动 MCP 微服务（每个业务一个端口）
uvicorn mcp_server.mcp_weather_server:app --reload --port 6001 &
uvicorn mcp_server.mcp_ticket_server:app --reload --port 6002 &
uvicorn mcp_server.mcp_order_server:app --reload --port 6003 &

# 7. 启动 A2A 代理
python -m a2a_server.weather_server &
python -m a2a_server.ticket_server &
python -m a2a_server.order_server &

# 8. 运行交互界面
# a) CLI
python main.py
# b) Streamlit UI
streamlit run app.py
```

---

## 🏗️ 项目结构

```
SmartVoyage/
├─ app.py                 # Streamlit 前端入口
├─ main.py                # CLI 主入口
├─ config.py              # 配置文件（模型、数据库、API Key）
├─ create_logger.py       # 日志工厂（Console + Rotating File）
├─ main_prompts.py        # LangChain Prompt 模板
│
├─ a2a_server/           # Python‑A2A 代理实现
│   ├─ weather_server.py  # 天气查询代理（5005）
│   ├─ ticket_server.py   # 票务查询代理（5006）
│   └─ order_server.py   # 订单查询代理（5007）
│
├─ mcp_server/           # FastAPI 微服务（MCP）
│   ├─ mcp_weather_server.py
│   ├─ mcp_ticket_server.py
│   └─ mcp_order_server.py
│
├─ utils/                # 数据抓取、格式化、SQL 生成等工具
│   ├─ spider_weather.py
│   ├─ fetch_weather_data.py
│   ├─ format.py
│   └─ generate_insert_7days_sql.py
│
├─ sql/                  # MySQL schema 与初始化脚本
│   ├─ create_table.sql
│   └─ create_weather_data.sql
│
├─ test/                 # Pytest 单元/集成测试
│   ├─ test_intent_and_process.py
│   ├─ test_mcp_weather_server.py
│   └─ test_spider_weather.py
│
├─ requirements.txt       # 项目依赖
└─ README.md              # 本文档（已更新）
```

---

## 🧪 测试

项目自带 **pytest** 测试套件，覆盖意图识别、MCP 接口以及爬虫。

```bash
pytest -q
```

> 运行前请确保所有 MCP 与 A2A 代理已启动，否则部分测试会因网络错误而失败。

---

## 🙋 常见问题 (FAQ)

| 问题 | 解决方案 |
|------|----------|
| **代理无法连接** | 确认对应 `python -m a2a_server.*` 已在端口（5005/5006/5007）运行；使用 `curl http://127.0.0.1:5005/a2a/tasks/send` 检查响应。 |
| **MCP 返回 500** | 检查 MySQL 配置及 `sql/create_table.sql` 是否已导入；查看 `mcp_server/*.py` 中的异常日志。 |
| **LLM 报 `input_required`** | 为模型提供完整信息，例如 `2025-07-30 北京的天气如何`。 |
| **中文乱码** | 设置环境变量 `PYTHONUTF8=1` 与 `PYTHONIOENCODING=utf-8`，或在 Windows 使用 `chcp 65001`。 |
| **Git 推送失败** | 确认 SSH 公钥已添加到 GitHub，或改用 HTTPS + PAT。 |

---

## 🤝 项目贡献

1. Fork 本仓库。
2. 在本地新建 `feature/xxx` 分支进行开发。
3. 完成代码、单元测试后提交 Pull Request。
4. 请遵循 **PEP8** 编码规范，确保 `flake8` 与 `black` 能通过。

---

## 📄 许可证

本项目采用 **MIT License**，详情请参阅根目录下的 `LICENSE` 文件。

---

## 🙏 致谢

- **python‑a2a**：提供完整的 A2A 协议实现与 AgentNetwork 管理。
- **LangChain**：简化 LLM Prompt 与链式调用构建。
- **FastAPI**：为 MCP 微服务提供轻量级、高性能的 HTTP 接口。
- **Streamlit**：快速搭建交互式网页 UI。

如有任何问题或改进建议，欢迎在 **Issues** 区提问或提交 **Pull Request**。祝您使用愉快！

---

*Enjoy building your travel assistant!*