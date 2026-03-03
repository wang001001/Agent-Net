import os


class Config:
    """Central configuration holder for the project.

    Provides:
    * ``project_root`` – absolute path to the repository root.
    * ``log_file`` – path to the rotating log file under ``logs/``.
    * ``model`` – configuration for the large language model used by the
      application (name, temperature, max tokens, optional API key).
    * ``database`` – simple DB connection settings. Values are read from
      environment variables when available, otherwise sensible defaults are
      applied.
    """

    def __init__(self):
        # -----------------------------------------------------------------
        # Project‑wide paths
        # -----------------------------------------------------------------
        self.project_root = os.path.abspath(os.path.dirname(__file__))
        self.log_file = os.path.join(self.project_root, "logs", "app.log")

        # -----------------------------------------------------------------
        # Large‑model configuration
        # -----------------------------------------------------------------
        self.base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        self.api_key = 'sk-efe5b7e6d8384e86bdd50aa7066ab848'
        self.model_name = 'qwen-plus'

        # -----------------------------------------------------------------
        # Database configuration
        # -----------------------------------------------------------------
        # Supported via environment variables – useful for local SQLite or a
        # remote PostgreSQL/MySQL instance.
        #   * DB_ENGINE – "sqlite" (default) or other DBMS identifier.
        #   * DB_NAME – file name for SQLite or database name for others.
        #   * DB_HOST, DB_PORT, DB_USER, DB_PASSWORD – ignored for SQLite.
                # -----------------------------------------------------------------
        # Database configuration
        # -----------------------------------------------------------------
        self.host = 'localhost'
        self.user = 'root'
        self.password = 'root'
        self.database = 'travel_rag'

        # MySQL does not require local directory creation.
        # 如果需要使用 SQLAlchemy，可以通过以下属性获取连接 URL（示例）：
        # self.mysql_uri = f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}"
