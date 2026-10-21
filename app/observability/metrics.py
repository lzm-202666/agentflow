from fastapi import Request,Response
from prometheus_client import CONTENT_TYPE_LATEST,Counter,Histogram,generate_latest

#定义指标实例对象
REQUEST_COUNT = Counter(
    "agentflow_requests_total",
    "Total HTTP requests",
    ["endpoint","status"],
)
REQUEST_LATENCY = Histogram(
    "agentflow_requests_latency_seconds",
    "HTTP latency",
    ["endpoint"],
)
TOKEN_USAGE = Counter(
    "agentflow_tokens_total",
    "LLM token usage",
    ["kind"],
)
LLM_COST = Counter(
    "agentflow_cost_usd_total",
    "LLM cost in USD",
)
#创建函数去全局注册表里取出指标实例对象，
# 读取实例里的元信息+当前统计数值，组装成Prometheus标准文本，
# 包装成Response返回给请求方（Prometheus服务）
async def metrics_endpoint(request: Request) -> Response:
    return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
