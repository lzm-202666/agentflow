from pydantic_settings import BaseSettings,SettingsConfigDict

#定义全局变量Settings类
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    app_name: str = "AgentFlow",
    log_level: str = "INFO",
    database_url: str = "sqlite+aiosqlite:///./agentflow.db"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

settings = Settings()