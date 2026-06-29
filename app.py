import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

from agent.react_agent import ReactAgent

st.set_page_config(page_title="AI Agent", page_icon="🤖")
st.title("🤖 AI 智能 Agent")

if "agent" not in st.session_state:
    working_dir = os.getcwd()
    try:
        st.session_state.agent = ReactAgent(working_dir=working_dir)
        st.success(f"Agent 初始化成功！工作目录: {working_dir}")
    except Exception as e:
        st.error(f"Agent 初始化失败: {str(e)}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thinking_log" not in st.session_state:
    st.session_state.thinking_log = ""

with st.sidebar:
    st.header("🔍 Agent 思考过程")
    if st.session_state.thinking_log:
        st.text_area("日志", st.session_state.thinking_log, height=400)
    else:
        st.info("尚未有推理记录")
    
    st.divider()
    st.caption(f"会话 ID: {st.session_state.agent.memory.get_thread_id()[:8]}...")

for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(msg["content"])

if prompt_input := st.chat_input("输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt_input})
    with st.chat_message("user"):
        st.markdown(prompt_input)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            result = st.session_state.agent.run(prompt_input)
            
            thinking_steps = st.session_state.agent.get_thinking_steps()
            
            thinking_log_lines = []
            if thinking_steps:
                for i, (thought, action, observation) in enumerate(thinking_steps, 1):
                    thinking_log_lines.append(f"步骤 {i}:")
                    thinking_log_lines.append(f"💡 Thought: {thought}")
                    thinking_log_lines.append(f"🛠️ Action: {action}")
                    if observation:
                        thinking_log_lines.append(f"👀 Observation: {observation}")
                    thinking_log_lines.append("")
                st.session_state.thinking_log = "\n".join(thinking_log_lines)
            else:
                st.session_state.thinking_log = "（无工具调用）"
            
            if not result:
                result = "抱歉，我无法处理这个问题。"
            st.markdown(result)

    st.session_state.messages.append({"role": "assistant", "content": result})
