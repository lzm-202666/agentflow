import streamlit as st
import httpx
import json
import uuid

st.set_page_config(page_title="AgentFlow", page_icon="🤖", layout="wide")

# API 地址：支持通过环境变量配置，方便 Docker 内部通信
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/chat/stream")

with st.sidebar:
    st.title("🤖 AgentFlow")
    st.caption("企业级多Agent工作流与评测平台")
    st.divider()
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    st.info(f"当前会话 ID：\n`{st.session_state.session_id[:8]}...`")
    if st.button("🔄 开启新会话", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

st.header("💬 智能数据分析与检索")
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("输入你的问题，例如：查一下上个月的销售额 / BMS 端口是多少？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        payload = {"message": prompt, "session_id": st.session_state.session_id}

        try:
            with httpx.stream("POST", API_URL, json=payload, timeout=60.0) as response:
                if response.status_code != 200:
                    st.error(f"服务异常，状态码: {response.status_code}")
                else:
                    for line in response.iter_lines():
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            try:
                                data = json.loads(data_str)
                                if "content" in data:
                                    full_response += data["content"]
                                    # 加上光标模拟打字机
                                    placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                pass
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"连接后端失败，请检查后端是否启动。错误: {e}")