from fastapi.security import api_key
from langchain_openai import ChatOpenAI
from app.config import settings

#定义实例化llm函数
def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=temperature,
    )