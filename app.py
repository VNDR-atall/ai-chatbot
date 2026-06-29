import os
os.environ["UVLOOP_DISABLE"] = "1"

import streamlit as st
from dotenv import load_dotenv
<<<<<<< HEAD
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage, AIMessageChunk,
    trim_messages, BaseMessage, ToolMessage
)
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import tiktoken
import numexpr
import uuid
import asyncio

load_dotenv()

st.set_page_config(page_title="AI Agent V4", page_icon="🤖")
st.title("🤖 AI 智能 Agent")

# 侧边栏参数
with st.sidebar:
    st.header("⚙️ 模型参数")
    model_name = st.selectbox("模型选择", ["deepseek-chat", "deepseek-reasoner"], index=0)
    temperature = st.slider("温度", 0.0, 1.0, 0.0, 0.05)
    max_tokens_trim = st.number_input("上下文最大 Token 数", 1024, 16384, 4096, 512)
    if st.button("🗑️ 清除对话记录", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

@st.cache_resource
def get_llm(model_name: str, temperature: float):
    return ChatDeepSeek(model=model_name, temperature=temperature)

CUSTOM_SYSTEM_PROMPT = """你是一个乐于助人的智能助手，可以记住对话历史。
你拥有以下工具：
- calculator：计算数学表达式。
- web_search：在互联网上搜索最新信息。

重要规则：
1. 当用户询问任何需要最新数据的内容时，必须使用 web_search 工具。
2. **处理时间敏感查询的特殊要求**：
   - 如果用户提到相对时间（例如“今天”、“昨天”、“上周”、“去年”），你**必须**在调用 web_search 之前，将相对时间转换为绝对日期（格式：YYYY-MM-DD），并附加到搜索关键词中。
   - 示例：
     * “广州昨天天气” → 先计算昨天日期（假设今天是2026-06-04，则昨天是2026-06-03），搜索 `广州天气 2026-06-03`。
     * “今天有什么新闻” → 搜索 `新闻 2026-06-04`。
   - 绝对不要直接搜索“昨天xxx”或“今天xxx”，因为搜索引擎不理解相对时间。
3. 如果搜索结果中包含明确的日期信息，优先使用该日期信息回答。如果搜索结果与用户询问的日期明显不符，指出可能的信息延迟并尝试重新搜索。
4. 如果工具返回结果，请基于结果回答用户。
5. 对于纯数学计算，使用 calculator。
6. 如果只是闲聊或基于已有知识的回答，可以不调用工具。
7. 始终保持回答的准确性和相关性。
"""

tokenizer = tiktoken.get_encoding("cl100k_base")
def count_tokens(messages):
    text = " ".join(msg.content for msg in messages if hasattr(msg, "content"))
    return len(tokenizer.encode(text))

def trim_history(messages: list[BaseMessage], max_tokens: int = 4096) -> list[BaseMessage]:
    return trim_messages(
        messages,
        max_tokens=max_tokens,
        strategy="last",
        token_counter=count_tokens,
        include_system=True,
        start_on="human",
    )

# 工具定义：显式提供 description 避免 docstring 问题
@tool(description="计算数学表达式。输入纯数学表达式（例如 3+4*2），返回计算结果。")
def calculator(expression: str) -> str:
=======
import os

load_dotenv()

from agent.react_agent import ReactAgent

st.set_page_config(page_title="AI Agent", page_icon="🤖")
st.title("🤖 AI 智能 Agent")

if "agent" not in st.session_state:
    working_dir = os.getcwd()
>>>>>>> 14b614d0ad2daaaca502ebcc0c2c2651b4072ea3
    try:
        st.session_state.agent = ReactAgent(working_dir=working_dir)
        st.success(f"Agent 初始化成功！工作目录: {working_dir}")
    except Exception as e:
        st.error(f"Agent 初始化失败: {str(e)}")
        st.stop()

<<<<<<< HEAD
@tool(description="搜索互联网获取最新信息。输入查询关键词，返回前几条结果摘要。建议在查询中明确包含日期，如YYYY-MM-DD")
def web_search(query: str) -> str:
    try:
        search_tool = TavilySearch(
            max_results=3,
            topic="general",
            include_answer=True,
            search_depth="advanced",   # 深度搜索，提高相关性
            # 不设置 time_range，让 Tavily 根据查询词中的日期智能返回
        )
        result = search_tool.invoke({"query": query})
        if hasattr(result, 'get'):
            answer_part = result.get('answer', '')
            answer_text = f"AI 生成的答案: {answer_part}\n\n" if answer_part else ""
            results_list = result.get('results', [])
            if not results_list and not answer_part:
                return "未找到相关结果。"
            web_results = "\n\n".join(
                f"【{r.get('title', '无标题')}】\n{r.get('content', '无内容')}"
                for r in results_list
            )
            return f"{answer_text}{web_results}".strip()
        return str(result)
    except Exception as e:
        return f"搜索服务调用失败: {str(e)}"

tools = [calculator, web_search]

# 关键修复：在缓存函数中，对不可哈希的参数加下划线前缀，让 Streamlit 忽略哈希
@st.cache_resource
def get_agent(llm, _tools, system_prompt, _checkpointer):
    return create_agent(
        model=llm,
        tools=_tools,
        system_prompt=system_prompt,
        checkpointer=_checkpointer,
    )

# 会话状态
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content=CUSTOM_SYSTEM_PROMPT),
        AIMessage(content="你好！我是你的AI助手，可以计算和搜索，有什么可以帮你的？")
    ]
if "thinking_log" not in st.session_state:
    st.session_state.thinking_log = ""
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

llm = get_llm(model_name, temperature)
checkpointer = InMemorySaver()
agent = get_agent(llm, tools, CUSTOM_SYSTEM_PROMPT, checkpointer)

# 显示历史消息
=======
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

>>>>>>> 14b614d0ad2daaaca502ebcc0c2c2651b4072ea3
for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(msg["content"])

<<<<<<< HEAD
# 侧边栏思考过程
with st.sidebar:
    st.header("🔍 Agent 思考过程")
    thinking_placeholder = st.empty()
    if st.session_state.thinking_log:
        thinking_placeholder.text_area("日志", st.session_state.thinking_log, height=400)
    else:
        thinking_placeholder.info("尚未有推理记录")

# 用户输入处理
if prompt_input := st.chat_input("输入你的问题..."):
    st.session_state.messages.append(HumanMessage(content=prompt_input))
=======
if prompt_input := st.chat_input("输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt_input})
>>>>>>> 14b614d0ad2daaaca502ebcc0c2c2651b4072ea3
    with st.chat_message("user"):
        st.markdown(prompt_input)

    input_messages = trim_history(st.session_state.messages, max_tokens_trim)
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.chat_message("assistant"):
<<<<<<< HEAD
        msg_placeholder = st.empty()
        state = {"full_response": "", "thinking_steps": []}

        async def stream_events():
            async for event in agent.astream_events(
                {"messages": input_messages},
                config=config,
                version="v1"
            ):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if isinstance(chunk, AIMessageChunk) and chunk.content:
                        state["full_response"] += chunk.content
                        msg_placeholder.markdown(state["full_response"] + "▌")
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    tool_input = event["data"].get("input", {})
                    step = f"🛠️ 工具：{tool_name}\n📥 输入：{tool_input}"
                    if step not in state["thinking_steps"]:
                        state["thinking_steps"].append(step)
                        thinking_placeholder.text_area("日志", "\n".join(state["thinking_steps"]), height=400)
                elif kind == "on_tool_end":
                    output = event["data"].get("output", "")
                    step = f"👀 观察：{str(output)[:200]}..." if len(str(output)) > 200 else f"👀 观察：{output}"
                    if step not in state["thinking_steps"]:
                        state["thinking_steps"].append(step)
                        thinking_placeholder.text_area("日志", "\n".join(state["thinking_steps"]), height=400)
            msg_placeholder.markdown(state["full_response"])
            st.session_state.thinking_log = "\n".join(state["thinking_steps"])
            return state["full_response"]

        # 获取或创建事件循环（兼容 Python 3.13）
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        import traceback
        try:
            final_response = loop.run_until_complete(stream_events())
        except Exception as e:
            st.error(f"❌ 处理出错：{str(e)}")
            # 将错误堆栈打印到终端
            print(traceback.format_exc())
            final_response = "抱歉，我遇到了一个错误，请稍后重试。"
            msg_placeholder.markdown(final_response)

    st.session_state.messages.append(AIMessage(content=final_response))
    st.rerun()
=======
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
>>>>>>> 14b614d0ad2daaaca502ebcc0c2c2651b4072ea3
