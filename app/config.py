from pydantic_settings import BaseSettings,SettingsConfigDict
from pathlib import Path

# 获取项目根目录的绝对路径（config.py 在 app 下，所以 parent.parent 就是根目录）
ROOT_DIR = Path(__file__).resolve().parent.parent

#定义全局变量Settings类
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    app_name: str = "AgentFlow"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./agentflow.db"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    dashscope_api_key: str = ""

settings = Settings()