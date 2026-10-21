import asyncio
from app.db.session import init_db

asyncio.run(init_db())
print("db ok")