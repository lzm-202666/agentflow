from langchain_core.messages import AIMessage,SystemMessage
from app.llm import get_llm

#定义数据库查询函数db_query_node，知识库检索函数rag_node，通用问答函数general_node
async def db_query_node(state) -> dict:
    #第三周换为真实 db_tool + SQL 生成
    mock = "[mock DB] 已识别为数据库查询。第 3 周介入真是MySQL工具。"
    return {"messages":[AIMessage(content=mock)]}
async def rag_node(state) -> dict:
    # 第 4 周替换为真实 retriever + reranker
    mock = "[mock RAG] 已识别为知识库检索。第 4 周接入混合检索。"
    return {"messages":[AIMessage(content=mock)]}
async def general_node(state) -> dict:
    llm = get_llm(temperature=0.3)
    resp = await llm.ainvoke([SystemMessage(content="你是AgentFlow 助手，简洁回答。"),*state["messages"],])
    return {"messages":[resp]}