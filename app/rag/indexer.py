import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import settings


def build_vector_db(data_dir: str = "data", persist_dir: str = "chroma_data"):
    """
    读取文本文件，切分，并存入 Chroma 向量数据库
    """
    print(f"📂 正在加载 {data_dir} 目录下的文档...")
    loader = DirectoryLoader(data_dir, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
    documents = loader.load()

    if not documents:
        print("⚠️ 没有找到任何文档，请检查 data 文件夹！")
        return

    # 文本切分
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✂️ 成功将文档切分为 {len(chunks)} 个片段。")

    # 初始化阿里云 DashScope 的 Embedding 模型
    print("🧠 正在初始化云端 Embedding (text-embedding-v2)...")
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v2",
        dashscope_api_key=settings.dashscope_api_key
    )

    # 存入 Chroma 向量数据库
    print("💾 正在写入 Chroma 向量数据库...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )

    print("✅ 向量数据库构建完成！")
    return vectorstore


if __name__ == "__main__":
    build_vector_db()

