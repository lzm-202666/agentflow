# AgentFlow
轻量级 Agent 工作流与评测平台（开发中）。

## 当前进度
- [x] Week 1: FastAPI 基础骨架、SSE 流式接口、SQLite、Prometheus、pytest
- [x] Week 2: LangGraph 意图路由、LLM 工厂、基于 Pydantic 的结构化输出
- [x] Week 3: 真实 DB 工具调用、SqliteSaver 多轮记忆、死循环重试兜底、Trace 监控与 Token 成本落库
- [x] Week 4: 企业级 RAG 混合检索（BM25+向量）、qwen3-rerank 重排、评测闭环与 Agent 节点接入
- [x] Week 5 (进行中): 全局 Token 成本无侵入监控、Prometheus 指标打点、Streamlit 可视化管理平台

## 更新日志 (Changelog)

### 🚀 Week 3 核心架构重构与全链路闭环
本次更新对系统的三大核心模块进行了生产级重构，彻底解决了早期版本的稳定性与体验痛点：
1. **`supervisor.py` 路由节点防御性重构**：强制设定 `temperature=0.0` 确保确定性；构建“原生结构化 -> 纯文本 JSON 解析 -> 默认 General 兜底”的三级降级链路；彻底杜绝大模型抽风导致的崩溃。
2. **`nodes.py` 业务节点真实工具接入**：移除 Mock 逻辑，接入真实查库工具；实现“参数提取”与“回复生成”双 LLM 解耦，优化前端流式体验；打通“失败重试 -> 兜底”的容错闭环。
3. **`chat.py` 全链路监控与长连接优化**：修复 `astream_events` 导致的记忆丢失；修复非流式节点前端无输出的 Bug；解决流式响应 Token 统计为 0 的痛点；打通 Session 与 Trace 表外键关联。
4. **路由意图精准追踪**：改为监听 `supervisor` 节点的 `on_chain_end` 事件，从 State 中提取大模型预测的原始 `intent`。实现“用户真实意图”与“系统执行路径”的解耦。

### 🚀 Week 4 核心突破：企业级 RAG 混合检索与评测闭环
在完成基础的 RAG 链路后，针对真实工程环境中的痛点，对检索层与工程配置进行了深度重构：

1. **依赖与环境调优（解决 Python 3.13 兼容死锁）**：
   - 废弃本地 `sentence-transformers`，全面接入阿里云 `DashScopeEmbeddings` 与 `qwen3-rerank` 云端接口。
   - 通过 `numpy>=2.0` 配合新版 `chromadb`，彻底解决了旧版依赖在 3.13 环境下的编译冲突问题。
   - 全面引入 `Path` 绝对路径解析，解决跨目录运行脚本时找不到 `.env` 与 `chroma_data` 的相对路径痛点。
2. **自研混合检索器（HybridRetriever）**：
   - 编写 `rag/indexer.py`，使用递归切分与重叠（overlap）技术完成文档细粒度入库。
   - 引入 `jieba` 分词与 `BM25Okapi`，解决向量检索对专有名词（如报错码、具体参数）召回不准的痛点。
   - **手写 RRF（倒数排名融合）算法**：将量纲不同的向量相似度与 BM25 得分进行排名级融合，并增加空库防呆拦截。
3. **云端重排与溯源架构（Reranker）**：
   - 针对重排 API 不返回原文的痛点，摒弃直接取 `item.document.text`，改为使用 `item.index` 结合本地列表映射，并透传原始 `metadata` 为后续溯源做准备。
   - **加入企业级降级策略**：使用 `try-except` 包裹网络请求，第三方 API 宕机时自动无缝降级返回混合检索的 Top-K 结果。
4. **评测闭环与 Agent 节点接入**：
   - 构建针对新能源车企的强干扰测试集，跑通纯向量 vs 混合检索 vs 重排的 Recall 指标对比。
   - **重写真实 `rag_node`**：将混合检索与重排逻辑正式接入 LangGraph 状态机。配合 Prompt 防幻觉约束，成功实现“查询专属知识（BMS端口）”走 RAG，“查销售额”走 DB，“问食堂”走 General 的完美多路分流。

   
### 📊 Week 5 核心升级：无侵入式可观测架构与全局监控
在不侵入业务代码的前提下，实现了生产级的成本与性能监控：
1. **重构 Token 统计逻辑**：废弃在 API 路由层手动解析事件流的笨重做法，引入 LangChain `AsyncCallbackHandler`。
2. **全局监控与上下文隔离**：结合 Python `ContextVar` 实现并发请求下的监控数据隔离，精准捕获输入/输出 Token 与 API 成本，并全局打点至 Prometheus 指标。
3. **接口性能追踪**：加入全局请求延迟 Histogram 与请求数 Counter，支撑后续 Grafana 监控大盘的接入。