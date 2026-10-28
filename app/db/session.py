from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker,create_async_engine
from app.config import settings
from app.db.models import Base

#定义engine连接池管理器对象
engine = create_async_engine(settings.database_url,echo=False)
#定义会话工厂AsyncSessionLocal
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
#创建函数创建表功能
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

#创建(依赖函数)创建会话功能
async def get_db() -> AsyncGenerator[AsyncSession,None]:
    async with AsyncSessionLocal as session:
        yield session