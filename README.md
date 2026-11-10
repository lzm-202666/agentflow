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

### 🚀 Week 4 核心突破：企业级 RAG 混合检索体系搭建

1. **依赖重构与环境兼容 (D1)**：
   - 更新 `requirements.txt`，引入 `chromadb`、`rank_bm25`、`jieba` 等 RAG 核心依赖。
   - **解决 Python 3.13 兼容问题**：废弃了在本地编译沉重的 `sentence-transformers`，改用阿里云 `DashScopeEmbeddings` 云端接口。通过 `numpy>=2.0` 配合新版 `chromadb`，彻底解决了旧版依赖在 3.13 环境下的编译死锁。
2. **离线文档向量化入库 (D1)**：
   - 编写 `rag/indexer.py`，使用 `RecursiveCharacterTextSplitter` 对业务文档进行细粒度切分，并增加了 `chunk_overlap` 防止语义截断。
   - 成功将业务数据（新能源供应链、财务报销制度）向量化并持久化至本地 Chroma 向量库。
3. **BM25 + 向量混合检索与 RRF 融合 (D2-D3)**：
   - 编写 `rag/retriever.py`，实现 `HybridRetriever` 核心类。
   - **关键词检索**：引入 `jieba` 分词与 `BM25Okapi` 算法，解决了向量检索对专有名词（如“T+60 天”）召回不准的痛点。
   - **RRF 倒数排名融合**：实现了 `rrf_fusion` 算法，将量纲不同的向量相似度与 BM25 得分进行排名级融合，输出高精度的 Top-K 检索结果。

### 🚀 Week 4 核心架构大重构：企业级 RAG 混合检索与评测闭环

在完成基础的 RAG 链路后，针对真实工程环境中的痛点，对检索层与工程配置进行了深度重构：

1. **依赖与运行环境调优（彻底解决版本冲突）**：
   - 废弃本地 `sentence-transformers`，全面接入阿里云 `DashScopeEmbeddings` 与 `qwen3-rerank`。
   - 解决了 Python 3.13 环境下旧版 `numpy` 与 `chromadb` 编译冲突的致命问题。
   - 全面引入 `Path` 绝对路径解析，彻底解决 PyCharm 跨目录运行脚本时找不到 `.env` 与 `chroma_data` 的相对路径痛点。
2. **自研混合检索器（HybridRetriever）**：
   - 引入 `jieba` 分词与 `BM25Okapi`，构建关键词精准匹配能力。
   - **手写 RRF（倒数排名融合）算法**：将量纲不同的向量相似度与 BM25 得分进行排名级融合。
   - 增加空库防呆拦截，解决了 BM25 初始化时的 `ZeroDivisionError`。
3. **云端重排容错架构（Reranker）**：
   - 针对云端重排 API 不返回原文的痛点，摒弃直接取 `item.document.text`，改为使用 `item.index` 结合本地 `documents` 列表进行引用映射，并透传原始 `metadata`。
   - **加入企业级降级策略**：使用 `try-except` 包裹网络请求，若第三方 API 宕机或超时，自动无缝降级返回混合检索的基础 Top-K 结果，保障业务永不中断。
4. **评测闭环与 Baseline 对比**：
   - 构建针对新能源车企的 10 条强干扰测试集，基于 `runner.py` 跑通纯向量检索、混合检索与重排后的 Recall 指标对比。