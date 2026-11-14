from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.config import settings

# 注意：LangGraph 的 PostgresSaver 需要同步的驱动字符串（psycopg），但底层会异步处理
# 所以这里要把 asyncpg 的标识去掉，直接用 postgresql://
db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

# 注意：这仍然是一个 context manager，在 main.py 的 lifespan 中启动
checkpointer_cm = AsyncPostgresSaver.from_conn_string(db_url)