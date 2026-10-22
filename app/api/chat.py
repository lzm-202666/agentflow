import json
from turtledemo.clock import jump

from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.graph.builder import graph

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
        state = {"messages":[HumanMessage(content=req.message)]}
        async for event in graph.astream_events(state,version="v2"):
            kind = event["event"]
            #节点启动事件
            if kind == "on_chain_start" and event.get("name") in {"supervisor","db_query","rag","general"}:
                yield {"event":"node","data":json.dumps({"node":event["name"]})}
            #llm输出token事件
            elif kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield {"event":"token","data":json.dumps({"content":content},ensure_ascii=False),}
        yield {"event":"done","data": json.dumps({"trace_id":"week2-demo"})}
    return EventSourceResponse(event_gen())


