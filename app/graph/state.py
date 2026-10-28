from typing import Annotated,Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

#定义图状态类
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage],add_messages]
    intent: Literal["db_query","rag","general"] | None
    error: str |None
    retry_count: int #记录重试次数