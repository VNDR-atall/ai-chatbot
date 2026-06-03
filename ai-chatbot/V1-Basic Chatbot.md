### update `app.py`
```python 
import streamlit as st
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()

# 页面设置
st.set_page_config(page_title="AI 问答机器人", page_icon="🤖")
st.title("🤖 AI 智能问答机器人 (DeepSeek)")

# 初始化模型（可以放在缓存里）
@st.cache_resource
def get_llm():
    return ChatDeepSeek(
        model="deepseek-chat",
        temperature=0.7,
    )

llm = get_llm()

# 初始化消息历史（保存在会话状态中）
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个乐于助人的智能助手。"}
    ]
    # 可选：添加一条欢迎消息
    st.session_state.messages.append({
        "role": "assistant",
        "content": "你好！我是你的AI助手，有什么可以帮你的？"
    })

# 显示历史消息（跳过system消息）
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 接收用户输入
if prompt := st.chat_input("输入你的问题..."):
    # 添加用户消息到历史
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 生成回复
    with st.chat_message("assistant"):
        # 将历史消息转换为 LangChain 可以理解的格式（列表即可）
        # ChatDeepSeek.invoke 接受消息列表，每个是 {"role": ..., "content": ...}
        # 直接传 st.session_state.messages 即可
        response = llm.invoke(st.session_state.messages)
        reply = response.content
        st.markdown(reply)

    # 添加助手回复到历史
    st.session_state.messages.append({"role": "assistant", "content": reply})
```

你给出的新 `app.py` 在原来“极简版”的基础上，增加了**多轮对话记忆、聊天界面美化、状态持久化、模型缓存、角色设定**等关键能力。下面逐点说明新增了哪些东西，以及背后的原理。

---

### 1. 页面美化与元信息设置
```python
st.set_page_config(page_title="AI 问答机器人", page_icon="🤖")
```
- **新增功能**：定义浏览器标签页的标题和图标，提升应用的专业感。
- **原理**：`st.set_page_config` 必须在任何 Streamlit 命令前调用，它会设置 HTML 的 `<title>` 和 favicon，是一次性的页面级配置。

---

### 2. 模型实例缓存
```python
@st.cache_resource
def get_llm():
    return ChatDeepSeek(model="deepseek-chat", temperature=0.7)
llm = get_llm()
```
- **新增功能**：通过 `@st.cache_resource` 缓存 `ChatDeepSeek` 对象。
- **原理**：Streamlit 每次用户交互都会**重新执行整个脚本**。如果不缓存，每次都会重新创建 LLM 实例（包括初始化 HTTP 客户端、加载 token 计算器等），浪费资源且可能变慢。  
  `@st.cache_resource` 会检查函数参数是否改变，若无变化则直接返回第一次创建的实例，从而让 LLM 对象在多次 rerun 间复用，提升性能。

---

### 3. 多轮对话记忆（会话状态）
```python
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个乐于助人的智能助手。"},
        {"role": "assistant", "content": "你好！我是你的AI助手，有什么可以帮你的？"}
    ]
```
- **新增功能**：  
  - 使用 `st.session_state` 保存完整的对话历史，使得每次用户输入后，之前的交流记录不会丢失。  
  - 添加了 `system` 消息来设定助手的角色（“乐于助人的智能助手”）。  
  - 添加了一条初始的 `assistant` 欢迎消息，让对话开始得更自然。
- **原理**：`st.session_state` 是 Streamlit 的**服务端会话字典**，它跨脚本重执行而持久存在（每个用户浏览器会话独立）。  
  这里把所有消息按 OpenAI 格式的字典 `{"role": "...", "content": "..."}` 存储，为后续的上下文传递和界面渲染提供统一数据源。

---

### 4. 历史消息的聊天式渲染
```python
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
```
- **新增功能**：每次脚本重执行时，都把历史对话以**聊天气泡**的形式显示出来，并跳过 `system` 消息（不展示给用户）。
- **原理**：`st.chat_message(role)` 会创建一个带有角色头像和样式的消息容器，`role` 为 `"user"` 或 `"assistant"` 时，自动匹配不同的图标和气泡对齐方式。`with` 块内可以放置任意 Streamlit 元素（这里用 `st.markdown` 渲染文本）。  
  这种方式比原来简单的 `st.write` 更接近现代聊天 UI，且因为脚本每次重执行都会重新绘制整个页面，因此历史记录会完整保留在屏幕上。

---

### 5. 聊天专用输入框
```python
if prompt := st.chat_input("输入你的问题..."):
```
- **新增功能**：用 `st.chat_input` 替换了原来的 `st.text_input`。它直接在聊天界面底部显示一个输入框，带有发送按钮，回车即可提交。
- **原理**：`st.chat_input` 是 Streamlit 为聊天应用专门设计的组件，外观与 `st.chat_message` 风格统一，输入后返回字符串，行为与 `st.text_input` 类似，但更符合对话场景的交互习惯（固定在底部，不会在历史消息上方重复出现）。

---

### 6. 带上下文的 LLM 调用
```python
response = llm.invoke(st.session_state.messages)
```
- **新增功能**：传递给模型的**不再是单个用户输入字符串**，而是**完整的消息列表**（包括 system、历史 user/assistant 消息，以及刚追加的新 user 消息）。
- **原理**：`ChatDeepSeek.invoke()` 能够接收一个消息列表，每个元素是 `{"role": "...", "content": "..."}` 的字典，它会自动序列化为符合 DeepSeek API 的请求体。  
  这样模型就能“记住”之前所有对话内容，实现真正的多轮上下文理解。这是从“一次性问答”到“连贯对话”的核心转变。

---

### 7. 消息的双向追加与即时显示
```python
# 添加用户消息并显示
st.session_state.messages.append({"role": "user", "content": prompt})
with st.chat_message("user"):
    st.markdown(prompt)

# 生成并显示助手回复
with st.chat_message("assistant"):
    response = llm.invoke(st.session_state.messages)
    reply = response.content
    st.markdown(reply)

# 将助手回复存入历史
st.session_state.messages.append({"role": "assistant", "content": reply})
```
- **新增功能**：  
  - 用户消息被立刻添加到 `st.session_state.messages` 并渲染。  
  - 助手的回复在生成后同样被即时渲染并存入历史。  
  - 这样整个对话流的状态就完整、有序地维护在了 `st.session_state.messages` 中。
- **原理**：利用 Streamlit 的执行流程——每次交互后脚本从头运行：  
  1. 旧消息被重绘（步骤 4）。  
  2. 新的用户消息通过 `st.chat_input` 触发条件块，追加到 `messages` 并显示。  
  3. LLM 被调用后，将返回的新 `assistant` 消息追加并显示。  
  最终形成一个**完整且可滚动的聊天界面**。

---

### 总结：从“单次问答”到“智能会话”的升级
新代码在极简版基础上，利用 Streamlit 的 **缓存机制、会话状态、聊天专用组件**，以及 LangChain 的 **消息列表传递**，实现了一个：
- 具备上下文记忆的多轮对话机器人  
- 美观的聊天气泡式 UI  
- 可自定义角色设定  
- 性能优化（模型实例缓存）  
- 开箱即用的专业聊天体验  

每一处新增都精准对应了 Streamlit 或 LangChain 暴露出的**高层抽象**，让你几乎不用处理 Web 开发或状态管理的底层细节，就能快速构建出一个功能完备的 AI 聊天应用。