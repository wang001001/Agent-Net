# SmartVoyage 🚀

**SmartVoyage** is a Python‑based, Agent‑to‑Agent (A2A) travel assistant that can answer travel‑related queries such as weather forecasts, ticket information, and order processing. It provides two entry points:

- **Streamlit UI** (`SmartVoyage/app.py`) – an interactive web interface.
- **Console driver** (`SmartVoyage/main.py`) – a CLI version that mimics the UI workflow.

The system is built on top of:

- **python‑a2a** – for constructing and routing agents.
- **LangChain + OpenAI** – LLM for intent detection, prompt templating and summarisation.
- **FastAPI** – micro‑services (MCP) that expose weather/ticket data.
- **MySQL** – persistence layer for scraped weather data.
- **Streamlit** – front‑end UI.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Deploying to GitHub](#deploying-to-github)
- [Known Issues & TODOs](#known-issues--todos)

---

## Project Structure
```
SmartVoyage/
├─ app.py                 # Streamlit UI entry point
├─ main.py                # Console entry point (same logic)
├─ config.py              # Central configuration (model, DB, credentials)
├─ create_logger.py       # Logger factory (console + rotating file)
├─ main_prompts.py        # LangChain prompt templates
│
├─ a2a_server/            # A2A agents
│   ├─ weather_server.py # Fully implemented weather agent
│   ├─ ticket_server.py  # TODO – ticket query agent (placeholder)
│   └─ order_server.py   # TODO – order processing agent (placeholder)
│
├─ mcp_server/            # FastAPI micro‑services (MCP)
│   ├─ mcp_weather_server.py
│   ├─ mcp_ticket_server.py
│   └─ mcp_order_server.py   # Syntax error – needs fixing
│
├─ utils/                 # Helper scripts and data processing
│   ├─ format.py
│   ├─ fetch_weather_data.py
│   ├─ spider_weather.py
│   ├─ insert_7days.py
│   ├─ get_latest_update_time.py
│   └─ generate_insert_7days_sql.py   # Syntax error – needs fixing
│
├─ test/                  # Pytest suite
│   ├─ test_api.py
│   ├─ test_intent_and_process.py
│   ├─ test_mcp_weather_server.py
│   └─ test_spider_weather.py
│
└─ requirements.txt       # All Python dependencies (generated via `pip freeze`)
```

---

## Prerequisites

- **Python 3.13** (tested with the Anaconda environment `tmf`).
- **MySQL** server (local or remote). Create a database named `smart_voyage` (or any name you prefer) and run the `sql/create_table.sql` script to initialise tables.
- **OpenAI / Anthropic API key** (or any compatible LLM endpoint) – used by `langchain-openai`.
- **Git** (optional, for pushing to GitHub).

---

## Setup & Installation

1. **Clone the repository** (or copy the folder to your machine).
2. **Create a new conda environment** (optional, but recommended):
   ```bash
   conda create -n smartvoyage python=3.13
   conda activate smartvoyage
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up environment variables** – you should **never** commit secret values. Create a file called `.env` in the project root:
   ```dotenv
   MODEL_NAME=your-model-name
   API_KEY=your-openai-or-anthropic-key
   BASE_URL=your-api-base-url   # e.g. https://api.openai.com/v1
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=your-db-user
   DB_PASSWORD=your-db-password
   DB_NAME=smart_voyage
   ```
   The `SmartVoyage/config.py` automatically reads these variables via `os.getenv`.
5. **Initialise the MySQL schema** (run once):
   ```bash
   mysql -u $DB_USER -p$DB_PASSWORD -h $DB_HOST $DB_NAME < sql/create_table.sql
   ```

---

## Configuration

All configurable values live in `SmartVoyage/config.py`. After adding the `.env` file you can adjust:

- `model_name`, `api_key`, `base_url` – LLM connection.
- Database connection details.
- Any additional flags such as `temperature`.

---

## Running the Application

### 1️⃣ Start the MCP services (FastAPI)
```bash
# In separate terminals:
uvicorn mcp_server.mcp_weather_server:app --reload --port 8000
uvicorn mcp_server.mcp_ticket_server:app  --reload --port 8001
# (Fix the syntax error in `mcp_order_server.py` before starting it.)
```
These expose the `/weather`, `/ticket` and `/order` endpoints used by the agents.

### 2️⃣ Start the A2A agents (optional, but recommended for full functionality)
```bash
python -m a2a_server.weather_server   # runs the weather A2A agent on port 5005
# Implement and start ticket_server & order_server when they are ready.
```

### 3️⃣ Launch the UI
```bash
streamlit run SmartVoyage/app.py
```
Open the URL printed by Streamlit (usually http://localhost:8501) in a browser. You can now chat with the assistant.

### 4️⃣ CLI version (quick test without UI)
```bash
python SmartVoyage/main.py
```
It will initialise the system and wait for input via `stdin`.

---

## Testing

Run the full pytest suite:
```bash
pytest -q
```
All existing tests pass for the weather flow. After implementing the ticket and order agents you should add corresponding tests.

---

## Deploying to GitHub

To push the project to a **GitHub repository** you will need:

1. **A remote repository URL** – e.g. `https://github.com/yourusername/SmartVoyage.git` (or an SSH URL).
2. **Write access** – either a personal access token (PAT) with `repo` scope for HTTPS pushes, **or** an SSH key that is added to your GitHub account.
3. (Optional) **Git configuration** – set your name/email if not already configured:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```

Typical workflow:
```bash
# Initialise a git repo if not already present
git init
git add .
git commit -m "Initial commit – SmartVoyage implementation"
# Add the remote (replace with your URL)
git remote add origin https://github.com/yourusername/SmartVoyage.git
# Push the main branch
git push -u origin master
```
If you use a PAT, you can embed it in the URL like:
```
https://<PAT>@github.com/yourusername/SmartVoyage.git
```
**Never commit the PAT** – use it only for the push command or configure a credential helper.

If you need help creating a repository or generating a PAT, let me know and I can guide you through the steps.

---

## Known Issues & TODOs

- **Syntax errors** in `mcp_server/mcp_order_server.py` and `utils/generate_insert_7days_sql.py` – fix before production.
- **Ticket & Order agents** are placeholders; implement the same pattern as the weather agent.
- **Hard‑coded secrets** – moved to `.env` in this README, but make sure the original `config.py` reads from env variables.
- **Linter warnings** – e.g., attribute `get` on strings in `weather_server.py`; they are harmless at runtime but can be cleaned up.
- **Package structure** – adding `__init__.py` files would make imports more robust.
- **Documentation** – extend the README with API specs if you expose the services to external callers.

---

## License

This project is provided under the **MIT License** (see `LICENSE` if added). Feel free to modify and redistribute.

---

*Enjoy building your travel assistant!*