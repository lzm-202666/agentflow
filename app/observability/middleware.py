import time
import contextvars
from typing import Any
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from app.observability.metrics import TOKEN_USAGE, LLM_COST

# 使用 ContextVar 跨组件安全地传递统计数据
trace_context = contextvars.ContextVar("trace_context", default={})


class TokenCostTracker(AsyncCallbackHandler):
    def __init__(self):
        self.start_time = time.time()

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        try:
            # 终极兼容提取方案，覆盖所有大模型格式
            token_usage = {}
            if response.generations and response.generations[0]:
                gen = response.generations[0][0]
                # 方式1：LangChain 新版流式输出
                if hasattr(gen, "message") and hasattr(gen.message, "usage_metadata"):
                    usage = gen.message.usage_metadata
                    if usage:
                        token_usage = {
                            "prompt_tokens": usage.get("input_tokens", 0),
                            "completion_tokens": usage.get("output_tokens", 0)
                        }
                # 方式2：OpenAI 兼容格式
                if not token_usage and hasattr(gen, "message") and hasattr(gen.message, "response_metadata"):
                    token_usage = gen.message.response_metadata.get("token_usage", {})

            # 方式3：传统非流式格式
            if not token_usage and response.llm_output:
                token_usage = response.llm_output.get("token_usage", {})

            # 拿到数据后累加
            prompt_tokens = token_usage.get("prompt_tokens", 0) or token_usage.get("input_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0) or token_usage.get("output_tokens", 0)

            if prompt_tokens or completion_tokens:
                TOKEN_USAGE.labels(kind="prompt").inc(prompt_tokens)
                TOKEN_USAGE.labels(kind="completion").inc(completion_tokens)

                cost = (prompt_tokens + completion_tokens) * 0.000001
                LLM_COST.inc(cost)

                ctx = trace_context.get()
                if ctx is not None:
                    ctx["prompt_tokens"] = ctx.get("prompt_tokens", 0) + prompt_tokens
                    ctx["completion_tokens"] = ctx.get("completion_tokens", 0) + completion_tokens
                    ctx["cost_usd"] = ctx.get("cost_usd", 0) + cost

        except Exception as e:
            print(f"⚠️ 监控埋点异常: {e}")