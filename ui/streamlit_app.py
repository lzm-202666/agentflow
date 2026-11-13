import streamlit as st
import uuid

# 必须是第一个 st 命令
st.set_page_config(page_title="AgentFlow 企业级中枢", page_icon="🤖", layout="wide")

# 使用 st.navigation 实现高级路由 (Streamlit 1.36+ 新特性，极度企业级)
# 如果你版本较低，Streamlit 会自动识别 pages 文件夹并在左侧生成导航
pg = st.navigation([
    st.Page("pages/1_chat.py", title="💬 智能问答", default=True),
    st.Page("pages/2_trace.py", title="📊 监控追踪"),
    st.Page("pages/3_eval.py", title="🎯 评测跑分"),
])

# 侧边栏 - 全局状态管理
with st.sidebar:
    st.title("🤖 AgentFlow")
    st.caption("企业级多Agent工作流平台")
    st.divider()

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    st.info(f"会话 ID:\n`{st.session_state.session_id[:8]}...`")

    if st.button("🔄 开启新会话", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# 运行选中的页面
pg.run()