## update `app.py`
```python
import streamlit as st
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import trim_messages, SystemMessage, HumanMessage, AIMessage
import tiktoken

load_dotenv()

# ---------- 页面配置 ----------
st.set_page_config(page_title="AI 问答机器人 V2", page_icon="🤖")
st.title("🤖 AI 智能问答机器人（带记忆）")

# ---------- 初始化模型 ----------
@st.cache_resource
def get_llm():
    return ChatDeepSeek(model="deepseek-chat", temperature=0.7)

llm = get_llm()

# ---------- 系统提示 ----------
SYSTEM_PROMPT = "你是一个乐于助人的智能助手，可以记住对话历史。"

# ---------- 自定义 token 计数器（用 cl100k_base 近似） ----------
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(messages):
    """估算消息列表的总 token 数"""
    text = " ".join(msg.content for msg in messages if hasattr(msg, "content"))
    return len(tokenizer.encode(text))

# ---------- 记忆裁剪器 ----------
def trim_history(messages: list) -> list:
    """裁剪历史消息，保留最近 4096 token 的内容"""
    return trim_messages(
        messages,
        max_tokens=4096,
        strategy="last",
        token_counter=count_tokens,   # 使用自定义函数
        include_system=True,
        start_on="human",
    )

# ---------- 初始化消息历史 ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content=SYSTEM_PROMPT)
    ]
    st.session_state.messages.append(
        AIMessage(content="你好！我是你的AI助手，有什么可以帮你的？")
    )

# ---------- 显示所有非系统消息 ----------
for msg in st.session_state.messages:
    if isinstance(msg, (HumanMessage, AIMessage)):
        with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
            st.markdown(msg.content)

# ---------- 用户输入 ----------
if prompt_input := st.chat_input("输入你的问题..."):
    # 添加用户消息到历史
    user_msg = HumanMessage(content=prompt_input)
    st.session_state.messages.append(user_msg)

    with st.chat_message("user"):
        st.markdown(prompt_input)

    # 生成回复
    with st.chat_message("assistant"):
        trimmed = trim_history(st.session_state.messages)
        response = llm.invoke(trimmed)
        reply = response.content
        st.markdown(reply)

    # 添加助手回复到历史
    assistant_msg = AIMessage(content=reply)
    st.session_state.messages.append(assistant_msg)
```
![[Pasted image 20260602132632.png|689]]你给出的 **V2 版本**，相比 V1，核心增加了一套 **“智能记忆管理”机制**——这是把聊天机器人从“能记住对话”推进到“能稳定运行长对话”的关键一步。除此之外，还在代码规范性和可扩展性上做了优化。

下面逐一说明 V2 新增了哪些东西，以及为什么重要。

---

### 1. 消息对象标准化：从“字典”升级为 LangChain 原生消息类型
**V1 的做法**  
用普通字典 `{"role": "...", "content": "..."}` 表示一条消息。

**V2 的做法**  
```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
```
所有消息都用对应的类实例化：
- `SystemMessage(content=...)`  
- `HumanMessage(content=...)`  
- `AIMessage(content=...)`  

**新增价值**  
- **类型安全**：LangChain 的许多工具（如 `trim_messages`、消息管道）要求输入/输出是这些标准消息对象，而不是纯字典。V2 使用它们后，整个流水线可以无缝衔接。  
- **未来扩展**：如果你需要添加 `tool_calls`、`function_call` 等附加字段，这些对象自带属性，远比字典扩展性强。  
- **代码可读性**：看到 `isinstance(msg, HumanMessage)` 比检查 `msg["role"] == "user"` 更明确、更 Pythonic。

---

### 2. 记忆裁剪器：解决长对话的上下文超限问题
这是 **V2 最核心的新功能**。

**V1 的缺陷**  
V1 每次调用 LLM 时，都直接把 `st.session_state.messages` 完整传递过去。如果对话持续多轮，历史消息会越来越长，很快就会超过 DeepSeek 模型的上下文长度（例如 64k，但消耗的 token 会急剧增加，甚至可能触发 API 限制或报错）。

**V2 的解决方案**  
```python
from langchain_core.messages import trim_messages

def trim_history(messages: list) -> list:
    return trim_messages(
        messages,
        max_tokens=4096,          # 保留最近的 4096 token
        strategy="last",          # 保留最后的部分
        token_counter=count_tokens,
        include_system=True,      # 始终保留系统消息
        start_on="human",         # 裁剪后的消息序列以 human 开头
    )
```
在生成回复时：
```python
trimmed = trim_history(st.session_state.messages)
response = llm.invoke(trimmed)
```

**新增价值**  
- **自动防止上下文溢出**：无论聊多久，发送给模型的上下文始终被控制在 `4096` token 以内（这个值可根据模型上下文窗口调整）。  
- **策略可控**：`strategy="last"` 保留最新的对话，符合“滑动窗口”记忆模式；`include_system=True` 确保系统指令永不丢失；`start_on="human"` 保证对话结构合理（不会出现连续两条 assistant 消息的情况）。  
- **零侵入**：裁剪过程对用户透明，界面显示依然是完整历史，但模型只看到裁剪后的紧凑上下文。

---

### 3. 自定义 Token 计数器：精确、透明的 token 计算
**V1 的做法**  
没有 token 计数能力，完全依靠模型自身的上下文窗口，无法提前控制。

**V2 的做法**  
```python
import tiktoken

tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(messages):
    text = " ".join(msg.content for msg in messages if hasattr(msg, "content"))
    return len(tokenizer.encode(text))
```
然后将它传给 `trim_messages` 的 `token_counter` 参数。

**新增价值**  
- **精确估算**：使用 OpenAI 开源的 `tiktoken` 库，用 `cl100k_base` 编码（与 DeepSeek 使用的 tokenizer 类似）计算 token 数，远比简单按字符数或单词数估算准确。  
- **可定制**：如果未来换用其他模型或需要更精细的计算（例如计算 messages 的 JSON 开销），可以修改 `count_tokens` 函数，不影响裁剪逻辑。  
- **成本与性能优化**：精准控制 token 上限，避免因 token 浪费导致 API 费用飙升或响应变慢。

---

### 4. 系统提示常量化，代码结构更清晰
**V1**  
系统提示直接写在列表初始化里：
```python
{"role": "system", "content": "你是一个乐于助人的智能助手。"}
```

**V2**  
```python
SYSTEM_PROMPT = "你是一个乐于助人的智能助手，可以记住对话历史。"
...
SystemMessage(content=SYSTEM_PROMPT)
```
**新增价值**  
- 方便统一修改系统人设。  
- 提示内容可以轻松扩展为长文本甚至从文件加载，而不打乱主逻辑。

---

### 总结：V2 最大的跃升——“记忆管理从无到有”
| 维度 | V1 | V2 |
|------|----|----|
| 消息表示 | 普通字典 | LangChain 标准消息对象 |
| 长对话处理 | 无限制，易超上下文 | 自动裁剪至 4096 token |
| Token 计算 | 无 | 基于 tiktoken 的精确计数 |
| 系统提示 | 硬编码在列表里 | 提取为常量，用对象封装 |
| 可扩展性 | 仅能应付简单 Demo | 为多轮稳定对话和高级功能铺路 |

如果你把这个聊天机器人看作一辆车，那么 V0 是“能跑”，V1 是“能开且有仪表盘”，而 V2 给你装上了 **“智能变速箱”——它能自动根据油量（token 上限）换挡（裁剪历史），确保长时间行驶不熄火。**