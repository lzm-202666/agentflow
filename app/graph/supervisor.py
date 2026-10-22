from typing import Literal
from pydantic import BaseModel,Field
from langchain_core.messages import SystemMessage
from app.llm import get_llm

#定义llm结构化输出规范
# {"intent": "rag",
#  "reason": "用户询问制度流程，属于知识库内容"}

class RouteDecision(BaseModel):
    intent: Literal["db_query","rag","general"] = Field(
        description="用户意图：数据库查询 / 知识库检索 / 通用问答"
    )
    reason: str = Field(description="一句话说明路由理由")
#实例化带结构规范的llm对象
_router = get_llm().with_structured_output(RouteDecision)

#创建supervisor专家函数 -> 判断去哪里只输出intent的三个其中之一
async def supervisor_node(state) -> dict:
    decision = await _router.ainvoke([
        SystemMessage(content=(
"你是意图路由器。只判断用户意图，不要回答问题。\n"
"- db_query: 涉及数据、统计、销售额、订单、报表\n"
"- rag: 涉及制度、流程、手册、文档、规定\n"
"- general: 寒暄、常识、闲聊、其他\n"
"只输出结构化结果。"
)),
        *state["messages"],
    ])
    return {"intent":decision.intent}
