import streamlit as st
import pandas as pd
import os
import psycopg  # 企业级：Psycopg 3
from dotenv import load_dotenv # 引入 dotenv

# 加载 .env 文件（本地开发时用到，Docker里直接用环境变量）

load_dotenv()
st.header("📊 全局历史监控 (Trace)")
st.markdown("展示每一次 API 请求的意图路由、Token 消耗与耗时。")

# 从环境变量读取 DB 地址
DB_URL = os.getenv("DATABASE_URL_SYNC")
if not DB_URL:
    st.error("❌ 致命错误：未配置 DATABASE_URL_SYNC 环境变量，请检查 .env 文件！")
    st.stop() # 停止执行

if st.button("🔄 刷新数据"):
    pass

try:
    # 使用 Psycopg 3 直连 Postgres
    with psycopg.connect(DB_URL) as conn:
        df = pd.read_sql_query(
            "SELECT created_at, route, input, prompt_tokens, completion_tokens, cost_usd, latency_ms FROM traces ORDER BY created_at DESC LIMIT 50",
            conn
        )

    if not df.empty:
        # 企业级时区转换：先标记为 UTC，再转为上海时区
        df['created_at'] = pd.to_datetime(df['created_at'])
        # 注意：如果数据库返回的时间已经带了时区（Postgres的timestamptz），直接 tz_convert 即可
        if df['created_at'].dt.tz is None:
            df['created_at'] = df['created_at'].dt.tz_localize('UTC')
        df['created_at'] = df['created_at'].dt.tz_convert('Asia/Shanghai')
        df['created_at'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

        df.columns = ["时间", "路由意图", "用户输入", "输入Token", "输出Token", "成本(USD)", "耗时(ms)"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无数据，请先去问答页发消息。")

except Exception as e:
    st.error(f"数据库读取失败: {e}")
    st.info("提示：如果你在本地直接跑 Streamlit，请确保 Docker 里的 Postgres 容器已经启动。")