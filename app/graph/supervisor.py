from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from app.llm import get_llm
import json


# 定义llm结构化输出规范
class RouteDecision(BaseModel):
    intent: Literal["db_query", "rag", "general"] = Field(
        description="用户意图：数据库查询 / 知识库检索 / 通用问答"
    )
    reason: str = Field(description="一句话说明路由理由")


# 创建supervisor专家函数 -> 判断去哪里只输出intent的三个其中之一
async def supervisor_node(state) -> dict:
    # 【修改点 1】强制 temperature=0.0，让模型不要乱发挥，严格按格式输出
    llm = get_llm(temperature=0.0)

    _SYSTEM = (
        "你是意图路由器。只判断用户意图，不要回答问题。\n"
        "- db_query: 涉及数据、统计、销售额、订单、报表\n"
        "- rag: 涉及制度、流程、手册、文档、规定\n"
        "- general: 寒暄、常识、闲聊、其他\n"
        "只输出结构化结果。"
    )

    # 【修改点 2】加上了 try-except 和 None 值判断的兜底逻辑
    try:
        _router = llm.with_structured_output(RouteDecision)
        decision = await _router.ainvoke([
            SystemMessage(content=_SYSTEM),
            *state["messages"],
        ])

        # 如果大模型抽风返回了 None，或者没返回 intent，做防御
        if decision is not None and hasattr(decision, "intent"):
            return {"intent": decision.intent}

    except Exception as e:
        print(f"⚠️ 原生结构化输出失败，正在尝试备用解析: {e}")

    # 【修改点 3】如果上面的结构化输出彻底挂了，走 JSON 文本解析的兜底方案
    try:
        sys_prompt = _SYSTEM + "\n请严格以 JSON 格式输出，例如：{\"intent\": \"db_query\", \"reason\": \"...\"}"
        resp = await llm.ainvoke([
            SystemMessage(content=sys_prompt),
            *state["messages"],
        ])
        content = resp.content.strip()

        # 清理 Markdown 代码块标记
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        data = json.loads(content)
        intent = data.get("intent", "general")
        if intent not in ["db_query", "rag", "general"]:
            intent = "general"
        return {"intent": intent}
    except Exception as e:
        print(f"❌ 备用解析也失败了，降级为 general: {e}")
        return {"intent": "general", "error": "route_failed"}