from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """集中式配置：全部通过环境变量 / .env 注入，代码里不再散落魔法值。"""

    # ---------- 数据库 ----------
    DATABASE_URL: str

    # ---------- JWT ----------
    JWT_SECRET_KEY: str
    JWT_EXPIRE_HOURS: int = 24
    JWT_ALGORITHM: str = "HS256"

    # ---------- 大模型（OpenAI 兼容协议）----------
    DEEPSEEK_KEY: str = ""
    DEEPSEEK_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ---------- Agent ----------
    AGENT_MAX_STEPS: int = 5  # ReAct 最大工具调用步数，防止死循环
    AGENT_HISTORY_LIMIT: int = 12  # 送入模型的最近消息条数

    # ---------- RAG ----------
    RAG_TOP_K: int = 4
    RAG_MIN_SCORE: float = 0.35
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"

    # ---------- 日志 ----------
    LOG_LEVEL: str = "INFO"

    # ---------- CORS（逗号分隔，便于按环境覆盖）----------
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 允许 .env 里存在历史遗留字段，不因多余键而崩溃
    )


setting = Settings()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
}
