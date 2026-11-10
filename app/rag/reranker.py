import dashscope
from http import HTTPStatus
from app.config import settings


class CloudReranker:
    def __init__(self):
        dashscope.api_key = settings.dashscope_api_key

    def rerank(self, query: str, documents: list, top_k: int = 3):
        """调用阿里云 qwen3-rerank 接口进行重排"""
        if not documents:
            return []

        # 提取纯文本列表
        docs_text = [doc["page_content"] for doc in documents]

        # 【新增】企业级防线 1：最外层包一个 try-except，防止网络超时或接口宕机导致整个系统崩溃
        try:
            resp = dashscope.TextReRank.call(
                model="qwen3-rerank",
                query=query,
                documents=docs_text,
                top_n=top_k,
                return_documents=False  # 【修改】改成 False。不让接口返回原文，省网络带宽，我们自己本地取
            )

            if resp.status_code == HTTPStatus.OK:
                results = []
                for item in resp.output.results:
                    # 【新增】企业级防线 2：防越界。确保接口返回的 index 不会超出我们本地 documents 的长度
                    if 0 <= item.index < len(documents):
                        # 【修改】核心修复：去本地 documents 列表里根据 index 拿原文，不要用 item.document.text
                        original_doc = documents[item.index]

                        results.append({
                            # 【修改】用原文本替换掉报错的 item.document.text
                            "page_content": original_doc["page_content"],
                            # 【新增】透传 metadata，为后续引用溯源做准备
                            "metadata": original_doc.get("metadata", {}),
                            "relevance_score": item.relevance_score
                        })
                return results
            else:
                print(f"Rerank API 状态异常: {resp.message}")
                return documents[:top_k]  # 降级处理，返回原顺序

        # 【新增】企业级防线 3：捕获任何异常（包括网络断开、解析失败），触发降级兜底
        except Exception as e:
            print(f"⚠️ Rerank 发生异常，触发降级策略: {e}")
            return documents[:top_k]  # 降级处理：直接返回混合检索的 Top K，保证业务不断流