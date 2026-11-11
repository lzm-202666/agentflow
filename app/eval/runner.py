from app.rag.retriever import HybridRetriever
from app.rag.reranker import CloudReranker
from app.eval.dataset import load_eval_dataset


def calculate_recall(results: list, ground_truth: str):
    """判断检索出的结果里，是否包含 ground_truth 关键词"""
    for res in results:
        if ground_truth in res["page_content"]:
            return 1
    return 0


def run_eval():
    retriever = HybridRetriever()
    reranker = CloudReranker()
    dataset = load_eval_dataset()

    if not dataset:
        return

    vector_recall = 0
    hybrid_recall = 0
    hybrid_rerank_recall = 0
    total = len(dataset)

    print(f"🚀 开始跑分，共 {total} 条测试用例...\n")

    for i, item in enumerate(dataset):
        query = item["query"]
        gt = item["ground_truth"]

        # 1. 纯向量检索
        v_res = retriever.vector_search(query, top_k=2)
        v_res_formatted = [{"page_content": d.page_content} for d in v_res]
        v_hit = calculate_recall(v_res_formatted, gt)
        vector_recall += v_hit

        # 2. 混合检索 (BM25 + 向量 RRF)
        h_res = retriever.hybrid_search(query, top_k=2)
        h_hit = calculate_recall(h_res, gt)
        hybrid_recall += h_hit

        # 3. 混合检索 + 重排 (Rerank)
        hr_res = reranker.rerank(query, h_res, top_k=2)
        hr_hit = calculate_recall(hr_res, gt)
        hybrid_rerank_recall += hr_hit

        print(f"[{i + 1}/{total}] 问: {query}")
        print(f" -> 纯向量: {'✅' if v_hit else '❌'} | 混合: {'✅' if h_hit else '❌'} | 重排: {'✅' if hr_hit else '❌'}")

    print("\n" + "=" * 30)
    print("📊 最终 Baseline 对比结果 (Recall@5 / Recall@3):")
    print(f"1. 纯向量检索召回率: {vector_recall / total:.2%}")
    print(f"2. 混合检索(RRF)召回率: {hybrid_recall / total:.2%}")
    print(f"3. 混合+重排召回率: {hybrid_rerank_recall / total:.2%}")
    print("=" * 30)


if __name__ == "__main__":
    run_eval()