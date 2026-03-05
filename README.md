
# SmartVoyage A2A + MCP 旅行助手

## 项目简介
**SmartVoyage** 是一个基于 **Agent‑to‑Agent (A2A)** 协议和 **FastAPI** 微服务的旅行智能助手。用户通过 **CLI** 或 **Streamlit** 前端界面提交自然语言查询，系统会自动完成以下流程：

1. **意图识别** – 使用 LLM（OpenAI/Anthropic）将用户输入解析为意图（天气、票务、订单等）。
2. **路由至对应 A2A 代理** – 根据意图调用相应的 Python‑A2A 代理（Weather、Ticket、Order）。
3. **代理内部调用 MCP** – A2A 代理通过 HTTP 与 FastAPI MCP（Micro‑Context‑Protocol）服务交互，从 MySQL 数据库获取真实数据。
4. **结果汇总并返回** – 将 MCP 的返回结果进行摘要、格式化后返回给用户。

整个系统实现了 **自然语言 → 意图识别 → 多代理协作 → 微服务 → 数据持久化** 的完整闭环，适合作为 AI 助手、聊天机器人或企业内部知识服务的技术参考。

---

## 项目背景
随着大语言模型（LLM）的成熟，单一模型直接完成复杂业务的能力仍有限。**Agent‑to‑Agent（A2A）** 架构通过让多个专职代理协同工作，能够把 **LLM** 的自然语言理解能力与 **后端业务系统**（数据库、外部 API）相结合，实现更可靠、更可控的业务流程。

本项目的动机主要有三点：

- **模块化可扩展**：不同业务（天气、票务、订单）各自独立实现为 A2A 代理，后期只需新增代理即可扩展新功能。
- **统一协议 (MCP)**：使用 FastAPI 实现的 **Model‑Context‑Protocol**（MCP）在代理与微服务之间提供统一的 HTTP 接口，解耦业务逻辑。
- **完整示例**：提供从前端 UI、CLI、意图识别、Agent 调度、MCP 交互到 MySQL 持久化的一站式示例，帮助学习者快速上手 A2A + 微服务组合。

---

## 项目结构
```
SmartVoyage/
├─ app.py                 # Streamlit 前端入口
├─ main.py                # CLI 主入口（与 UI 逻辑相同）
├─ config.py              # 配置文件（模型、数据库、API Key）
├─ create_logger.py       # 日志工厂（Console + Rotating File）
├─ main_prompts.py        # LangChain Prompt 模板
│
├─ a2a_server/            # Python‑A2A 代理实现
│   ├─ weather_server.py  # 天气查询代理（5005）
│   ├─ ticket_server.py   # 票务查询代理（5006）
│   └─ order_server.py    # 订单查询代理（5007）
│
├─ mcp_server/            # FastAPI 微服务（MCP）
│   ├─ mcp_weather_server.py
│   ├─ mcp_ticket_server.py
│   └─ mcp_order_server.py
│
├─ utils/                 # 数据抓取、格式化、SQL 生成等工具
│   ├─ spider_weather.py  # 爬取天气数据的 spider
│   ├─ fetch_weather_data.py
│   ├─ format.py          # MySQLJSONEncoder，处理 datetime/Decimal 等
│   └─ generate_insert_7days_sql.py
│
├─ sql/                   # MySQL schema 与初始化脚本
│   ├─ create_table.sql
│   └─ create_weather_data.sql
│
├─ test/                  # Pytest 单元/集成测试
│   ├─ test_intent_and_process.py
│   ├─ test_mcp_weather_server.py
│   └─ test_spider_weather.py
│
├─ requirements.txt        # 项目依赖（python‑a2a、langchain‑openai、fastapi 等）
└─ README.md               # 本文档
```

---

## 环境准备与部署
### 1. 克隆仓库（已经在本地，下面直接说明）
```bash
# 若需要重新克隆
git clone https://github.com/wang001001/SmartVoyage_Agent_MCP.git
cd SmartVoyage_Agent_MCP
```

### 2. 创建虚拟环境（推荐使用 conda）
```bash
conda create -n smartvoyage python=3.13
conda activate smartvoyage
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
在项目根目录新建 `.env`（**不要**提交到仓库），示例内容如下：
```dotenv
# LLM 配置（这里示例使用阿里通义千问 / OpenAI）
MODEL_NAME=gpt-4o-mini
API_KEY=your-llm-api-key
BASE_URL=https://api.openai.com/v1   # 根据实际提供商修改

# MySQL 配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-pass
DB_NAME=smart_voyage
```
> **安全提示**：`.env` 已在 `.gitignore` 中，切勿提交到远程仓库。

### 5. 初始化数据库
```bash
# 需要先在本地或远程 MySQL 创建数据库 smart_voyage
mysql -u $DB_USER -p$DB_PASSWORD -h $DB_HOST $DB_NAME < sql/create_table.sql
```
（`create_table.sql` 包含 `weather_data`、`train_tickets`、`concert_tickets`、`flight_tickets`、`orders` 等表结构）

---

## 启动方式
### 1. 启动 MCP 微服务（可自行选择端口）
```bash
# 天气 MCP（端口 6001）
uvicorn mcp_server.mcp_weather_server:app --reload --port 6001
# 票务 MCP（端口 6002）
uvicorn mcp_server.mcp_ticket_server:app --reload --port 6002
# 订单 MCP（端口 6003）
uvicorn mcp_server.mcp_order_server:app --reload --port 6003
```
> 建议在不同终端窗口分别启动，确保所有服务均在运行状态。

### 2. 启动 A2A 代理（每个代理对应一个端口）
```bash
python -m a2a_server.weather_server   # 5005
python -m a2a_server.ticket_server    # 5006
python -m a2a_server.order_server     # 5007
```
> 这三个进程会在后台暴露 `/a2a` 接口，供 `main.py` / `app.py` 调用。

### 3. 运行交互界面
#### (a) CLI 交互
```bash
python main.py
```
按提示输入自然语言，例如 `北京今天的天气如何`，系统会完成意图识别 → 调用 WeatherAgent → 调用 MCP → 返回天气信息。

#### (b) Streamlit UI
```bash
streamlit run app.py
```
在浏览器打开 `http://localhost:8501`，即可使用图形化界面进行同样的查询。

---

## 测试
项目自带 **pytest** 测试套件，覆盖意图识别、MCP 接口以及爬虫。
```bash
pytest -q
```
> 运行前请确保所有 MCP 与 A2A 代理已启动，否则相应的测试会因网络错误而失败。

---

## 常见问题 (FAQ)
| 问题 | 解决方案 |
|------|----------|
| **代理无法连接** | 确认相应的 `python -m a2a_server.*` 已在对应端口（5005/5006/5007）运行；使用 `curl http://127.0.0.1:5005/a2a/tasks/send` 检查是否有响应。 |
| **MCP 返回 500** | 检查 MySQL 配置、数据库是否已创建并导入 `sql/create_table.sql`；查看 `mcp_server/*.py` 中的异常日志。 |
| **LLM 报 `input_required`** | LLM 认为缺少必要信息（比如日期），请在查询中提供更完整的描述，例如 `2025-07-30 北京的天气如何`。 |
| **中文乱码** | 确保环境变量 `PYTHONUTF8=1` 与 `PYTHONIOENCODING=utf-8` 已设置，或在 Windows 终端使用 `chcp 65001`。 |
| **Git 推送失败（SSH）** | 若使用 SSH，请确保本地私钥对应的公钥已添加到 GitHub，且私钥文件权限为 `600`（`chmod 600 id_rsa`）。若仍有问题，建议改用 HTTPS + PAT。 |

---

## 项目贡献
1. Fork 本仓库。
2. 在本地新建 `feature/xxx` 分支进行开发。
3. 完成代码、单元测试后提交 Pull Request。
4. 请遵循 **PEP8** 编码规范，确保 `flake8` 与 `black` 能通过。

---

## 许可证
本项目采用 **MIT License**，细节请查看根目录下的 `LICENSE` 文件。

---

## 致谢
- **python‑a2a**：提供了完整的 A2A 协议实现与 AgentNetwork 管理。 
- **LangChain**：简化了 LLM Prompt 与链式调用的构建。 
- **FastAPI**：为 MCP 微服务提供轻量级、高性能的 HTTP 接口。 
- **Streamlit**：快速搭建交互式网页 UI。 

如有任何问题或改进建议，欢迎在 **Issues** 区提问或提交 **Pull Request**。祝您使用愉快！

---

## License

This project is provided under the **MIT License** (see `LICENSE` if added). Feel free to modify and redistribute.

---

*Enjoy building your travel assistant!*
