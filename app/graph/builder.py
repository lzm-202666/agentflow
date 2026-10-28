#图构建，条件边
from langgraph.graph import StateGraph,START,END
from app.graph.state import AgentState
from app.graph.supervisor import supervisor_node
from app.graph.nodes import db_query_node,rag_node,general_node,fallback_node

#定义条件边根据supervisor_node函数的intent决定
def route_after_supervisor(state) -> str:
    """
    条件边：根据 intent 决定走哪个分支。
    :param state:
    :return:
    """
    return state.get("intent") or "general"
#定义条件边根据db_query是否返回error决定
def route_after_db_query(state) -> str:
    """判断 DB 查询后是否要重试"""
    if not state.get("error"):
        return "end"

    retry_count = state.get("retry_count",0)
    if retry_count < 2:
        return "db_query" #重试
    else:
        return "fallback" #兜底
#全局状态图构建
def build_graph(checkpointer=None):
    g = StateGraph(AgentState)

    g.add_node("supervisor",supervisor_node)
    g.add_node("db_query",db_query_node)
    g.add_node("rag",rag_node)
    g.add_node("general",general_node)
    g.add_node("fallback",fallback_node)
    g.add_edge(START,"supervisor")
    g.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "db_query":"db_query",
            "rag":"rag",
            "general":"general",
        },
    )
    #DB 节点的条件边：判断重试还是结束
    g.add_conditional_edges(
        "db_query",
        route_after_db_query,
        {
            "db_query":"db_query",
            "fallback":"fallback",
            "end":END
        }
    )

    g.add_edge("rag",END)
    g.add_edge("general",END)
    #编译时传入 checkpointer
    return g.compile(checkpointer=checkpointer)

#编译图：校验结构，做成可执行对象# 不要再全局实例化了，统一在 chat.py 里按需实例化并注入 checkpointer
# graph = build_graph()