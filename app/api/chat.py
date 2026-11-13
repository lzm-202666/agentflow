import json
import time
import uuid
from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.graph.builder import build_graph
from app.db.session import AsyncSessionLocal
from app.db.models import Trace, Session
from sqlalchemy import select
# 引入我们写的中间件和指标
from app.observability.middleware import TokenCostTracker, trace_context
from app.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str


@router.get("/ping")
async def ping():
    return {"pong": True}


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer=checkpointer)

    async def event_gen():
        # 初始化上下文与追踪器
        ctx = {}
        token_ctx = trace_context.set(ctx)
        tracker = TokenCostTracker()

        state = {"messages": [HumanMessage(content=req.message)]}
        config = {
            "configurable": {"thread_id": req.session_id},
            "recursion_limit": 25,
            "callbacks": [tracker]  # 关键：交给 Callback 处理
        }

        start_time = time.time()
        has_streamed_tokens = False
        final_output = ""
        route_intent = "unknown"
        trace_id = str(uuid.uuid4())

        # 监控整个接口的调用次数与耗时
        REQUEST_COUNT.labels(endpoint="/chat/stream", status="started").inc()

        try:
            async for event in graph.astream_events(state, config=config, version="v2"):
                kind = event["event"]
                # 过滤路由节点事件
                if kind == "on_chain_start" and event.get("name") in {"supervisor", "db_query", "rag", "general",
                                                                      "fallback"}:
                    yield {"event": "node", "data": json.dumps({"node": event["name"]})}

                # 处理流式输出
                elif kind == "on_chat_model_stream":
                    tags = event.get("tags", [])
                    if "supervisor" in tags:
                        continue
                    content = event["data"]["chunk"].content
                    if content:
                        has_streamed_tokens = True
                        final_output += content
                        yield {"event": "token", "data": json.dumps({"content": content}, ensure_ascii=False)}

                # 提取意图
                elif kind == "on_chain_end" and event.get("name") == "supervisor":
                    supervisor_output = event["data"].get("output", None)
                    if isinstance(supervisor_output, dict) and "intent" in supervisor_output:
                        route_intent = supervisor_output["intent"]

                # 处理无流式输出的节点兜底
                elif kind == "on_chain_end" and event.get("name") == "LangGraph":
                    if not has_streamed_tokens:
                        final_state = event["data"].get("output", None)
                        messages = final_state.get("messages", []) if final_state else []
                        if messages:
                            final_output = messages[-1].content
                            if final_output:
                                yield {"event": "token",
                                       "data": json.dumps({"content": final_output}, ensure_ascii=False)}

            # 图执行结束，记录耗时并落库
            latency_seconds = time.time() - start_time
            latency_ms = int(latency_seconds * 1000)
            REQUEST_LATENCY.labels(endpoint="/chat/stream").observe(latency_seconds)

            async with AsyncSessionLocal() as db:
                stmt = select(Session).where(Session.id == req.session_id)
                existing_session = (await db.execute(stmt)).scalar_one_or_none()

                if not existing_session:
                    db.add(Session(id=req.session_id))
                    await db.flush()

                # 直接从 Context 中拿 Token 数据
                trace = Trace(
                    id=trace_id,
                    session_id=req.session_id,
                    input=req.message,
                    output=final_output,
                    route=route_intent,
                    status="success",
                    prompt_tokens=ctx.get("prompt_tokens", 0),
                    completion_tokens=ctx.get("completion_tokens", 0),
                    cost_usd=ctx.get("cost_usd", 0.0),
                    latency_ms=latency_ms,
                )
                db.add(trace)
                await db.commit()

            yield {"event": "done", "data": json.dumps({"trace_id": trace_id, "latency_ms": latency_ms})}

        except Exception as e:
            print(f"\n[ERROR] 聊天流式接口发生报错: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

        finally:
            # 清理上下文
            trace_context.reset(token_ctx)

    return EventSourceResponse(event_gen())