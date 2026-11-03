import json
import time
import uuid
from fastapi import APIRouter,Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.graph.builder import  build_graph
from app.db.session import AsyncSessionLocal
from app.db.models import Trace,Session
from sqlalchemy import select

#实例化路由小组
router = APIRouter()

#定义基于BaseModel类的自动校验，将前端json字符串自动转为python对象的类
class ChatRequest(BaseModel):
    message: str
    session_id: str

#测试接口路由是否正常挂载
@router.get("/ping")
async def ping():
    return {"pong": True}

#异步AgentFlow流式回复
@router.post("/chat/stream")
async def chat_stream(req: ChatRequest,request:Request):
    #从 app.state 拿 checkpointer,动态构建带记忆的图
    checkpointer = request.app.state.checkpointer
    graph = build_graph(checkpointer=checkpointer)

    #定义事件生成器函数
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
                                                                # ensure_ascii=False中文原样输出

            # 【新增】监听 supervisor 节点的结束事件，精准提取大模型返回的 intent
            elif kind == "on_chain_end" and event.get("name") == "supervisor":
                supervisor_output = event["data"].get("output",None)

                # 防御性编程：确保拿到的字典里真的有 intent
                if isinstance(supervisor_output,dict) and "intent" in supervisor_output:
                    route_intent = supervisor_output["intent"]

            #跑图结束事件
            elif kind == "on_chain_end" and event.get("name") == "LangGraph":
                if not has_streamed_tokens:
                    final_state = event["data"].get("output",None)
                    messages = final_state.get("messages",[])
                    if messages:
                        final_output = messages[-1].content
                        if final_output:
                            yield {"event":"token","data":json.dumps({"content":final_output},ensure_ascii=False)}

            # 抓取大模型返回的 Token 消耗（流式响应通常在最末尾的 chunk 里带 usage )
            elif kind == "on_chat_model_end":
                output = event["data"].get("output", None)
                if output is None:
                    continue
                # 方式 1：尝试直接从 usage_metadata 获取（新版 LangChain）
                usage = getattr(output, "usage_metadata", None)

                # 方式 2：如果上面没拿到，尝试从 response_metadata 获取（旧版或某些兼容模型）
                if not usage:
                    response_metadata = getattr(output, "response_metadata", None)
                    if response_metadata:
                        usage = response_metadata.get("token_usage",{})

                # 拿到数据后累加
                if usage and isinstance(usage,dict):
                    # 兼容 input_tokens 和 prompt_tokens 两种键名
                    prompt_tokens += usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
                    completion_tokens += usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)


        #整张图都跑完了执行下面
        # ================= 新增：落库 =================
        latency_ms = int((time.time() - start_time) * 1000)
        async with AsyncSessionLocal() as db:
            stmt = select(Session).where(Session.id == req.session_id)
            existing_session = (await db.execute(stmt)).scalar_one_or_none()

            if not existing_session:
                #直接用前端ID当主键
                new_session = Session(id=req.session_id)
                db.add(new_session)
                await db.flush()#刷新一下，确保外键能关联
            # 简单估算一下成本（假设每百万 token 2块钱，仅作演示）
            cost = (prompt_tokens + completion_tokens) * 0.000002
            trace_id = str(uuid.uuid4())

            #落库Trace（并把session_id也存进Trace表）
            trace = Trace(
                id=trace_id,
                session_id=req.session_id,
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

        yield {"event":"done","data": json.dumps({"trace_id":trace_id,"latency_ms":latency_ms})}
    return EventSourceResponse(event_gen())


