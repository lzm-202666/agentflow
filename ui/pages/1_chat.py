import streamlit as st
import httpx
import json
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/chat/stream")

st.header("💬 智能数据分析与检索")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("试试问：查一下上个月的销售额 / BMS 端口是多少？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        payload = {"message": prompt, "session_id": st.session_state.session_id}

        try:
            with httpx.stream("POST", API_URL, json=payload, timeout=60.0) as response:
                for line in response.iter_lines():
                    if line.startswith("data:"):
                        try:
                            data = json.loads(line[5:].strip())
                            if "content" in data:
                                full_response += data["content"]
                                placeholder.markdown(full_response + "▌")
                        except json.JSONDecodeError:
                            pass
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"连接失败: {e}")