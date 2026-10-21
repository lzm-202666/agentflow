import asyncio
import json
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

#实例化路由小组
router = APIRouter()

#定义基于BaseModel类的自动校验，将前端json字符串自动转为python对象的类
class ChatResponse(BaseModel):
    message: str

#测试接口路由是否正常挂载
@router.get("/ping")
async def ping():
    return {"pong": True}
#异步AgentFlow流式回复
@router.post("/chat/stream")
async def chat_stream(req: ChatResponse):
    async def event_gen():
        text = f"你说的是：{req.message}。这是AgentFlow的流式回复演习"
        for ch in text:
            yield {
                "event": "token",
                "data": json.dumps({"content": ch},ensure_ascii=False),
            }
            await asyncio.sleep(0.03)
        yield {"event": "done","data": json.dumps({"trace_id":"demo"})}
    return EventSourceResponse(event_gen())


