 # AgentFlow
轻量级 Agent 工作流与评测平台（开发中）。

## 当前进度
- [x] Week 1: FastAPI 基础骨架、SSE 流式接口、SQLite、Prometheus、pytest
- [x] Week 2: LangGraph 意图路由、LLM 工厂、基于 Pydantic 的结构化输出
- [x] Week 3: 真实 DB 工具调用、SqliteSaver 多轮记忆、死循环重试兜底、Trace 监控与 Token 成本落库

## 更新日志 (Changelog)

### 🚀 Week 3 核心架构重构与全链路闭环
本次更新对系统的三大核心模块进行了生产级重构，彻底解决了早期版本的稳定性与体验痛点：

1. **`supervisor.py` 路由节点防御性重构**：
   - 强制设定 `temperature=0.0` 确保路由确定性。
   - 构建“原生结构化 -> 纯文本 JSON 解析 -> 默认 General 兜底”的三级降级链路。
   - 加入 `None` 值防御与代码块清理，彻底杜绝大模型抽风导致的崩溃。

2. **`nodes.py` 业务节点真实工具接入**：
   - 移除 Mock 逻辑，接入真实查库工具。
   - 实现“参数提取”与“回复生成”双 LLM 解耦，优化前端流式体验。
   - 完善异常捕获与 `retry_count` 累加，打通“失败重试 -> 兜底”的容错闭环。

3. **`chat.py` 全链路监控与长连接优化**：
   - 修复 `astream_events` 未传 `config` 导致的记忆丢失问题，并加入 `recursion_limit` 防止死循环。
   - 修复非流式节点前端无输出的 Bug，实现 `on_chain_end` 终态兜底推送。
   - 增强 Token 抓取鲁棒性，解决流式响应 Token 统计为 0 的痛点。
   - 打通 Session 与 Trace 表外键关联，实现完整的调用链路审计。

4. **路由意图精准追踪**：
   - 修正了 `route_intent` 的获取逻辑。不再偷懒使用 `event["name"]`（实际执行节点名）进行反推。
   - 改为监听 `supervisor` 节点的 `on_chain_end` 事件，直接从 LangGraph 的 State 返回值中提取大模型预测的原始 `intent`。
   - **价值**：实现了“用户真实意图”与“系统实际执行路径”的解耦。即使系统因异常触发 `fallback` 降级，Trace 审计日志依然能精准记录用户的原始诉求，为后续的模型调优和数据分析提供准确依据。