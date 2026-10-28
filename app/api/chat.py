import json
import time
import uuid
from fastapi import APIRouter,Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.graph.builder import  build_graph
from app.db.session import AsyncSessionLocal
from app.db.models import Trace

#实例化路由小组
router = APIRouter()

#定义基于BaseModel类的自动校验，将前端json字符串自动转为python对象的类
class ChatResponse(BaseModel):
    message: str
    session_id: str

#测试接口路由是否正常挂载
@router.get("/ping")
async def ping():
    return {"pong": True}

#异步AgentFlow流式回复
@router.post("/chat/stream")
async def chat_stream(req: ChatResponse,request:Request):
    #从 app.state 拿 checkpointer,动态构建带记忆的图
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer=checkpointer)

    async def event_gen():
        state = {"messages":[HumanMessage(content=req.message)]}
        config = {"configurable":{"thread_id":req.session_id},"recursion_limit":25}

        start_time = time.time()
        has_streamed_tokens = False
        final_output = ""
        route_intent = "unknown"

        #记录 token 使用情况
        prompt_tokens = 0
        completion_tokens = 0

        async for event in graph.astream_events(state,config=config,version="v2"):
            kind = event["event"]
            #节点启动事件
            if kind == "on_chain_start" and event.get("name") in {"supervisor","db_query","rag","general","fallback"}:
                if event["name"] != "supervisor" and route_intent == "unknown":
                    #记录最终走的分支
                    route_intent = event["name"]
                yield {"event":"node","data":json.dumps({"node":event["name"]})}
            #llm输出token事件
            elif kind == "on_chat_model_stream":
                # 过滤掉 supervisor 节点里的内部思考过程
                tags = event.get("tags", [])
                if "supervisor" in tags:
                    continue

                content = event["data"]["chunk"].content
                if content:
                    has_streamed_tokens = True
                    final_output += content
                    yield {"event":"token","data":json.dumps({"content":content},ensure_ascii=False),}

            elif kind == "on_chain_end" and event.get("name") == "LangGraph":
                if not has_streamed_tokens:
                    final_state = event["data"].get("output",{})
                    messages = final_state.get("messages",[])
                    if messages:
                        final_state = messages[-1].content
                        if final_output:
                            yield {"event":"token","data":json.dump({"content":final_output},ensure_ascii=False)}

            # 抓取大模型返回的 Token 消耗（流式响应通常在最末尾的 chunk 里带 usage )
            elif kind == "on_chat_model_end":
                output = event["data"].get("output", {})

                # 方式 1：尝试直接从 usage_metadata 获取（新版 LangChain）
                usage = getattr(output, "usage_metadata", None)

                # 方式 2：如果上面没拿到，尝试从 response_metadata 获取（旧版或某些兼容模型）
                if not usage and hasattr(output, "response_metadata"):
                    usage = output.response_metadata.get("token_usage", {})

                # 拿到数据后累加
                if usage:
                    # 兼容 input_tokens 和 prompt_tokens 两种键名
                    prompt_tokens += usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
                    completion_tokens += usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)

        # ================= 新增：落库 =================
        latency_ms = int((time.time() - start_time) * 1000)
        async with AsyncSessionLocal() as db:
            # 简单估算一下成本（假设每百万 token 2块钱，仅作演示）
            cost = (prompt_tokens + completion_tokens) * 0.000002

            trace = Trace(
                id=str(uuid.uuid4()),
                input=req.message,
                output=final_output,
                route=route_intent,
                status="success",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
            )
            db.add(trace)
            await db.commit()

        yield {"event":"done","data": json.dumps({"trace_id":trace.id,"latency_ms":latency_ms})}
    return EventSourceResponse(event_gen())


