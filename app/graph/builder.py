#图构建，条件边
from langgraph.graph import StateGraph,START,END

from app.graph.state import AgentState
from app.graph.supervisor import supervisor_node
from app.graph.nodes import db_query_node,rag_node,general_node

#定义条件边根据supervisor_node函数的intent决定
def route_after_supervisor(state) -> str:
    """
    条件边：根据 intent 决定走哪个分支。
    :param state:
    :return:
    """
    return state.get("intent") or "general"
#全局状态图构建
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("supervisor",supervisor_node)
    g.add_node("db_query",db_query_node)
    g.add_node("rag",rag_node)
    g.add_node("general",general_node)
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
    g.add_edge("db_query",END)
    g.add_edge("rag",END)
    g.add_edge("general",END)
    return g.compile()

#编译图：校验结构，做成可执行对象
graph = build_graph()