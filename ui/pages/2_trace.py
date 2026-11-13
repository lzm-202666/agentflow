import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

st.header("📊 全局历史监控 (Trace)")
st.markdown("展示每一次 API 请求的意图路由、Token 消耗与耗时。")

# 注意：D6 切 Postgres 后，这里读取逻辑我们会改成用 SQLAlchemy 异步查
db_path = Path(__file__).resolve().parent.parent.parent / "agentflow.db"

if st.button("🔄 刷新数据"):
    pass

if db_path.exists():
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT created_at, route, input, prompt_tokens, completion_tokens, cost_usd, latency_ms FROM traces ORDER BY created_at DESC LIMIT 50",
            conn
        )
        conn.close()
        if not df.empty:

            # 企业级时区转换：先标记为 UTC，再转为上海时区，最后格式化
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['created_at'] = df['created_at'].dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')
            df['created_at'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

            df.columns = ["时间", "路由意图", "用户输入", "输入Token", "输出Token", "成本(USD)", "耗时(ms)"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无数据，请先去问答页发消息。")
    except Exception as e:
        st.error(f"读取失败: {e}")
else:
    st.warning("未找到数据库，请先启动后端。")