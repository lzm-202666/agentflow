import jieba
from rank_bm25 import BM25Okapi
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import settings
from pathlib import Path


#拿到项目根目录
ROOT_DIR=Path(__file__).resolve().parent.parent.parent


class HybridRetriever:
    def __init__(self, persist_dir: str = str(ROOT_DIR / "chroma_data")):
        # 1. 初始化向量库连接
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=settings.dashscope_api_key
        )
        self.vectorstore = Chroma(persist_directory=persist_dir, embedding_function=self.embeddings)

        # 2. 初始化 BM25 所需的数据
        # 从向量库中提取所有文本块，用于构建关键词索引
        data = self.vectorstore.get()
        self.documents = data["documents"]
        self.metadatas = data["metadatas"]

        # 防止数据库真的空了报 ZeroDivision 错
        if not self.documents:
            raise ValueError("❌ 向量数据库是空的！请先运行 indexer.py！")

        # 使用 jieba 分词构建 BM25
        tokenized_corpus = [list(jieba.cut(doc)) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)

    #返回document列表对象
    def vector_search(self, query: str, top_k: int = 5):
        """纯向量检索"""
        return self.vectorstore.similarity_search(query, k=top_k)

    def bm25_search(self, query: str, top_k: int = 5):
        """纯 BM25 关键词检索"""
        tokenized_query = list(jieba.cut(query))
        scores = self.bm25.get_scores(tokenized_query)
        # 获取分数最高的 top_k 个索引
        top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for i in top_n:
            if scores[i] > 0:  # 过滤掉完全不相关的
                results.append({
                    "page_content": self.documents[i],
                    "metadata": self.metadatas[i]
                })
        return results

    def rrf_fusion(self, vector_res: list, bm25_res: list, k: int = 60, top_k: int = 5):
        """RRF (Reciprocal Rank Fusion) 融合排序算法"""
        rrf_scores = {}
        doc_pool = {}  # 【新增】用于存放完整的文档对象信息

        # 计算向量检索的 RRF 分数
        for rank, doc in enumerate(vector_res):
            content = doc.page_content
            rrf_scores[content] = rrf_scores.get(content, 0) + 1 / (k + rank + 1)

            # 【新增】保存完整信息（包含 metadata）
            doc_pool[content] = {
                "page_content": content,
                "metadata": doc.metadata
            }


        # 计算 BM25 检索的 RRF 分数
        for rank, doc in enumerate(bm25_res):
            content = doc["page_content"]
            rrf_scores[content] = rrf_scores.get(content, 0) + 1 / (k + rank + 1)

            # 【新增】保存完整信息
            doc_pool[content] = {
                "page_content": content,
                "metadata": doc.get("metadata", {})
            }

        # 按融合分数降序排序sorted_docs是元组列表
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # 还原格式->字典列表
        fused_results = []
        for content, score in sorted_docs:
            fused_results.append({"page_content": content,
                                  "rrf_score": score,
                                  "metadata": doc_pool[content]["metadata"]})
        return fused_results

    def hybrid_search(self, query: str, top_k: int = 3):
        """混合检索入口"""
        vec_res = self.vector_search(query, top_k=top_k * 2)
        bm_res = self.bm25_search(query, top_k=top_k * 2)
        return self.rrf_fusion(vec_res, bm_res, top_k=top_k)