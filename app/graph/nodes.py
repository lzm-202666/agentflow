import json
from langchain_core.messages import AIMessage,SystemMessage,HumanMessage
from app.llm import get_llm
from app.tools.db_tool import db_query_tool,DBQueryArgs

#定义数据库查询函数db_query_node，知识库检索函数rag_node，通用问答函数general_node
async def db_query_node(state) -> dict:

    # 必须按照 DBQueryArgs 这个图纸来输出，输出出来直接是 DBQueryArgs 的实例对象
    # 1.安检员，只负责提取月份参数
    extractor_llm = get_llm().with_structured_output(DBQueryArgs)
    try:
        user_msg = state["messages"][-1].content
        args = await extractor_llm.ainvoke(f"请提取用户想查询的月份：{user_msg}")
        result = await db_query_tool.execute(args.model_dump())
        if result["success"]:
            data = result["data"]
            if "error" in data:
                raise ValueError(data["error"])

            # 【关键修改点】：查到数据后，让大模型来生成最终回答
            # 2.客服，拿到数据，负责生成流畅的回复
            chat_llm = get_llm(temperature=0.3)
            final_resp = await chat_llm.ainvoke([
                SystemMessage(content="你是一个数据分析助手，请根据查到的数据，简洁地回答用户。"),
                HumanMessage(content=f"用户问：{user_msg}。查询结果：{data}")
            ])

                # 返回大模型的响应，这样前端就能拦截到流式输出了！
            return {"messages": [final_resp], "error": None}
        else:
            raise ValueError(result["error"])

    except Exception as e:
        # 加上这一行，把错误打印到控制台
        print(f"\n======== 数据库查询报错了: {str(e)} ========\n")
        # 发生异常，记录 error 并让状态流转到重试或兜底
        return {
            "messages":[AIMessage(content=f"查询失败，正在重试：{str(e)}")],
            "error":str(e),
            "retry_count":state.get("retry_count",0) + 1,#失败重试次数
        }

async def rag_node(state) -> dict:
    # 第 4 周替换为真实 retriever + reranker
    mock = "[mock RAG] 已识别为知识库检索。第 4 周接入混合检索。"
    return {"messages":[AIMessage(content=mock)]}

async def general_node(state) -> dict:
    llm = get_llm(temperature=0.3)
    resp = await llm.ainvoke([SystemMessage(content="你是AgentFlow 助手，简洁回答。"),*state["messages"],])
    return {"messages":[resp]}

async def fallback_node(state) -> dict:
    # 兜底节点：重试超过次数或彻底失败时触发
    msg = "抱歉，系统连续多次尝试均未能完成您的请求，请检查查询条件或稍后再试。"
    return {"messages": [AIMessage(content=msg)]}