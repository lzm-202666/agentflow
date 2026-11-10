import json
import os
from pathlib import Path

from app.rag.indexer import ROOT_DIR

#找到根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def load_eval_dataset(filepath: str = None):

    # 【修改】如果没有传入路径，就默认去根目录的 evals/dataset.jsonl 找
    if filepath is None:
        filepath = str(ROOT_DIR / "evals" / "dataset.jsonl")

    if not os.path.exists(filepath):
        print(f"⚠️ 找不到测试集文件: {filepath}")
        return []

    dataset = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                dataset.append(json.loads(line))
    return dataset