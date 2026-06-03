## before update

As `langgraph` is a more modern choise (the official has migrate the `create_react-agent` to `langgraph.prebuilt`), we introduce the package.
```bash
source .venv/bin/activate
pip install langgraph
```
so the updated `app.py` will be based on `langgraph`.

(In fact, you'd better verify that them are all be udapted to the latest version.)
```bash
pip install -U langgraph langchain
```

and for web search, the `ddgs` is needed:
```bash 
pip install -U ddgs
```

---
## update `app.py`
```python
import streamlit as st
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage,
    trim_messages, BaseMessage
)
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain_core.tools import tool
import tiktoken
import numexpr
import uuid

load_dotenv()

# ---------- 页面配置 ----------
st.set_page_config(page_title="AI Agent V3", page_icon="🤖")
st.title("🤖 AI 智能 Agent (LangGraph v1 标准版)")


# ---------- 初始化模型 ----------
@st.cache_resource
def get_llm():
    return ChatDeepSeek(model="deepseek-chat", temperature=0)


llm = get_llm()

# ---------- 自定义系统提示 ----------
CUSTOM_SYSTEM_PROMPT = """你是一个乐于助人的智能助手，可以记住对话历史。
你拥有以下工具：
- calculator：计算数学表达式。
- web_search：在互联网上搜索最新信息。

重要规则：
- 当用户询问任何需要最新数据、实时信息、新闻、天气等时，必须使用 web_search 工具。
- 绝对不要声称"无法联网"或"搜索功能不可用"。你确实可以搜索，请直接使用工具。
- 如果工具返回结果，请基于结果回答用户。
- 对于纯数学计算，使用 calculator。
- 如果只是闲聊或基于已有知识的回答，可以不调用工具。
- 使用中文与用户交流。"""


# ---------- token 计数和裁剪 ----------
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(messages):
    text = " ".join(msg.content for msg in messages if hasattr(msg, "content"))
    return len(tokenizer.encode(text))

def trim_history(messages: list[BaseMessage]) -> list[BaseMessage]:
    return trim_messages(
        messages,
        max_tokens=4096,
        strategy="last",
        token_counter=count_tokens,
        include_system=True,
        start_on="human",
    )


# ---------- 工具定义 ----------
@tool
def calculator(expression: str) -> str:
    """计算数学表达式。输入纯数学表达式（例如 3+4*2），返回计算结果。"""
    try:
        result = numexpr.evaluate(expression).item()
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算出错：{str(e)}"

@tool
def web_search(query: str) -> str:
    """搜索互联网获取最新信息。输入查询关键词，返回前几条结果摘要。"""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return "未找到相关结果。"
        return "\n\n".join(
            f"【{r['title']}】{r['body']}" for r in results
        )
    except Exception as e:
        return f"搜索出错：{str(e)}"

tools = [calculator, web_search]


# ---------- 构建 Agent（新版 create_agent API） ----------
# 创建内存检查点保存器，用于实现对话记忆
checkpointer = InMemorySaver()

# 使用新版 create_agent 构建 ReAct 智能体
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=CUSTOM_SYSTEM_PROMPT,  # 系统提示词
    checkpointer=checkpointer,           # 启用对话记忆
)


# ---------- 会话状态 ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content=CUSTOM_SYSTEM_PROMPT),
        AIMessage(content="你好！我是你的AI助手，可以计算和搜索，有什么可以帮你的？")
    ]

if "thinking_log" not in st.session_state:
    st.session_state.thinking_log = ""

if "thread_id" not in st.session_state:
    # 为本次会话生成唯一的线程 ID，用于记忆隔离
    st.session_state.thread_id = str(uuid.uuid4())


# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("🔍 Agent 思考过程")
    if st.session_state.thinking_log:
        st.text_area("日志", st.session_state.thinking_log, height=400)
    else:
        st.info("尚未有推理记录")

    st.divider()
    st.caption(f"会话 ID: {st.session_state.thread_id[:8]}...")


# ---------- 显示历史消息 ----------
for msg in st.session_state.messages:
    if isinstance(msg, (HumanMessage, AIMessage)):
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)


# ---------- 用户输入 ----------
if prompt_input := st.chat_input("输入你的问题..."):
    # 添加用户消息
    user_msg = HumanMessage(content=prompt_input)
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt_input)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            # 准备输入消息（裁剪历史以控制 token 数量）
            input_messages = trim_history(st.session_state.messages)

            # 配置线程 ID，LangGraph 会自动管理该线程的对话历史
            config = {"configurable": {"thread_id": st.session_state.thread_id}}

            # 调用 Agent
            # create_agent 使用 "messages" 键来传递消息
            result = agent.invoke({"messages": input_messages}, config=config)

            # 提取最终回复
            final_answer = ""
            thinking_steps = []

            # 解析 Agent 返回的消息，提取工具调用过程和最终回复
            for msg in result.get("messages", []):
                # 处理工具调用请求（AIMessage 包含 tool_calls）
                if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        thinking_steps.append(f"🛠️ 工具：{tc.get('name', '未知')}")
                        thinking_steps.append(f"📥 输入：{tc.get('args', {})}")
                # 处理工具返回结果（ToolMessage 类型）
                elif hasattr(msg, "type") and msg.type == "tool":
                    thinking_steps.append(f"👀 观察：{msg.content}")
                # 最终回复（AIMessage 且不包含 tool_calls）
                elif isinstance(msg, AIMessage) and not (hasattr(msg, "tool_calls") and msg.tool_calls):
                    if msg.content:
                        final_answer = msg.content

            # 如果没有解析出最终回复，尝试取最后一条消息
            if not final_answer and result.get("messages"):
                last_msg = result["messages"][-1]
                if hasattr(last_msg, "content"):
                    final_answer = last_msg.content

            # 更新侧边栏日志
            if thinking_steps:
                st.session_state.thinking_log = "\n".join(thinking_steps)
            else:
                st.session_state.thinking_log = "（无工具调用）"

            # 显示最终回复
            if not final_answer:
                final_answer = "抱歉，我无法处理这个问题。"
            st.markdown(final_answer)

    # 保存最终回复到会话历史
    assistant_msg = AIMessage(content=final_answer)
    st.session_state.messages.append(assistant_msg)