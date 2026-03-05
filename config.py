# -*- coding: utf-8 -*-
"""
安全的配置文件 – 读取所有敏感信息自环境变量 (.env)

- 大模型配置：BASE_URL、API_KEY、MODEL_NAME
- 数据库配置：DB_HOST、DB_USER、DB_PASSWORD、DB_NAME
- 日志文件路径：默认放在项目根目录下的 logs 目录

在项目根目录创建 .env 并写入对应键值，
示例（请勿提交到仓库）：

    MODEL_NAME=qwen-plus
    API_KEY=your-llm-api-key
    BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
    DB_HOST=localhost
    DB_USER=root
    DB_PASSWORD=root
    DB_NAME=travel_rag
    LOG_DIR=logs

程序会自动读取上述变量，若未设置将使用安全的默认值。
"""

import os
from pathlib import Path

# 项目根目录（相对于本文件的上级目录）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---- 大模型配置 ----
BASE_URL = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
API_KEY = os.getenv("API_KEY", "")  # 必须在 .env 中提供
MODEL_NAME = os.getenv("MODEL_NAME", "qwen-plus")

# ---- 数据库配置 ----
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # 必须在 .env 中提供
DB_NAME = os.getenv("DB_NAME", "travel_rag")

# ---- 日志配置 ----
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_PATH = PROJECT_ROOT / LOG_DIR / "app.log"

# 将路径转为字符串，保持与原来代码兼容
log_file = str(LOG_PATH)


class Config:
    """兼容旧代码的包装类 – 所有属性在实例化时读取环境变量"""

    def __init__(self):
        # 大模型配置
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.model_name = MODEL_NAME

        # 数据库配置
        self.host = DB_HOST
        self.user = DB_USER
        self.password = DB_PASSWORD
        self.database = DB_NAME

        # 日志配置
        self.log_file = log_file


if __name__ == "__main__":
    # 简单打印用于调试
    cfg = Config()
    print("Base URL:", cfg.base_url)
    print("Model:", cfg.model_name)
    print("DB Host:", cfg.host)
    print("Log file:", cfg.log_file)
