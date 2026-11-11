from langchain_core.messages import AIMessage,SystemMessage,HumanMessage
from app.llm import get_llm
from app.tools.db_tool import db_query_tool,DBQueryArgs
from app.rag.retriever import HybridRetriever
from app.rag.reranker import CloudReranker

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

#【重写】真实的知识库检索节点
async def rag_node(state) -> dict:
    # 1. 拿到用户最新的问题
    user_query = state["messages"][-1].content

    try:
        # 2. 混合检索捞出 Top-5
        retriever = HybridRetriever()
        hybrid_results = retriever.hybrid_search(user_query, top_k=5)

        # 3. 重排筛选出 Top-2
        reranker = CloudReranker()
        final_results = reranker.rerank(user_query, hybrid_results, top_k=2)

        # 4. 把筛选出来的文档拼接成上下文
        context = "\n\n".join([doc["page_content"] for doc in final_results])

        # 5. 构造 Prompt 交给大模型生成回答（加入严格防幻觉指令）
        system_prompt = (
            "你是一个新能源车企的智能助手。请严格根据下面提供的【参考资料】回答用户的问题。\n"
            "如果参考资料中没有相关信息，请直接回答“根据现有知识库无法回答”，千万不要编造。\n\n"
            f"【参考资料】\n{context}"
        )

        llm = get_llm(temperature=0.1)  # 知识问答不需要太发散，温度调低
        resp = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ])

        return {"messages": [resp], "error": None}

    except Exception as e:
        print(f"\n======== RAG 检索报错了: {str(e)} ========\n")
        return {
            "messages": [AIMessage(content=f"知识库检索失败，请稍后再试。")],
            "error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }

async def general_node(state) -> dict:
    llm = get_llm(temperature=0.3)
    resp = await llm.ainvoke([SystemMessage(content="你是AgentFlow 助手，简洁回答。"),*state["messages"],])
    return {"messages":[resp]}

async def fallback_node(state) -> dict:
    # 兜底节点：重试超过次数或彻底失败时触发
    msg = "抱歉，系统连续多次尝试均未能完成您的请求，请检查查询条件或稍后再试。"
    return {"messages": [AIMessage(content=msg)]}