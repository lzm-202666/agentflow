import pytest
from httpx import ASGITransport,AsyncClient
from app.main import app

#把下面的函数标记成夹具：自动生成，自动收尾，自动释放资源，不用写一堆anext->因为 ac = await anext(client())
@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport,base_url="http://test") as ac:
        yield ac