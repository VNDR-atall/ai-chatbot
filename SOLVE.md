# AI Chatbot Agent 问题修复记录

本文档记录了 CLI Agent 开发过程中遇到的问题及其解决方案。

---

## 问题一：tiktoken 模块导入阻塞

### 问题现象
运行 `agent` 命令后，程序在启动阶段完全卡住，无任何输出，用户按 `Ctrl+C` 中断后显示如下错误：

```
File "/Users/vd/ai-chatbot/agent/utils/token_utils.py", line 4, in <module>
    tokenizer = tiktoken.get_encoding("cl100k_base")
  ...
  File "/opt/miniconda3/lib/python3.13/site-packages/tiktoken/load.py", line 17, in read_file
    resp = requests.get(blobpath)
 KeyboardInterrupt
```

### 问题原因
`tiktoken.get_encoding("cl100k_base")` 在**模块导入阶段**就立即执行，此时会尝试从 OpenAI 的 Azure Blob Storage 下载 tokenizer 数据文件（`https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken`）。在网络受限环境下（如防火墙、代理），此请求会一直阻塞直到超时，导致整个程序无法启动。

### 涉及模块
- `agent/utils/token_utils.py` — 第4行

### 修复方案
将 tokenizer 初始化改为**延迟加载**（lazy loading），只在实际需要时才初始化，并添加异常处理和 fallback 方案。

**修改前**：
```python
import tiktoken
from langchain_core.messages import BaseMessage, trim_messages

tokenizer = tiktoken.get_encoding("cl100k_base")  # 模块导入时立即下载

def count_tokens(messages: list[BaseMessage]) -> int:
    text = " ".join(msg.content for msg in messages if hasattr(msg, "content"))
    return len(tokenizer.encode(text))
```

**修改后**：
```python
import tiktoken
from langchain_core.messages import BaseMessage, trim_messages

_tokenizer = None

def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        try:
            _tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _tokenizer = None
    return _tokenizer

def count_tokens(messages: list[BaseMessage]) -> int:
    text = " ".join(msg.content for msg in messages if hasattr(msg, "content"))
    tokenizer = _get_tokenizer()
    if tokenizer:
        return len(tokenizer.encode(text))
    else:
        return len(text) // 4  # fallback 方案
```

### 修改文件
- `agent/utils/token_utils.py`

### 效果对比
| 状态 | 修改前 | 修改后 |
|------|--------|--------|
| 模块导入 | 阻塞，无法启动 | 秒级启动 |
| 网络问题 | 完全卡死 | 自动 fallback |
| Token 计算 | 精确 | 降级为估算（len//4） |

---

## 问题二：Rich Panel 字符串拼接错误

### 问题现象
运行 agent 并输入对话后，出现以下错误：

```
❌ 错误: can only concatenate str (not "Panel") to str
```

### 问题原因
在 `agent/cli.py` 第77行，尝试用 `+` 运算符拼接字符串和 Rich 的 `Panel` 对象：

```python
console.print("\n" + Panel(Markdown(result), title="🤖 AI 回复", border_style="blue"))
```

Python 的 `+` 运算符不支持将字符串与 Rich 的 `Panel` 对象直接拼接。

### 涉及模块
- `agent/cli.py` — 第77行

### 修复方案
直接传递 Panel 对象给 `console.print()`，Rich 会自动处理换行：

**修改前**：
```python
console.print("\n" + Panel(Markdown(result), title="🤖 AI 回复", border_style="blue"))
```

**修改后**：
```python
console.print(Panel(Markdown(result), title="🤖 AI 回复", border_style="blue"))
```

### 修改文件
- `agent/cli.py`

### 效果对比
| 状态 | 修改前 | 修改后 |
|------|--------|--------|
| 运行结果 | 抛出类型错误 | 正常显示 Panel |

---

## 问题三：Agent 不调用 web_search 工具，使用过时知识

### 问题现象
用户询问"广州今天天气"，Agent 直接使用训练数据中的过时信息（显示2025年7月天气），而不是调用 `web_search` 工具获取实时数据。

```
根据搜索结果，今天是 2025年7月1日（星期二），广州的天气情况如下：
天气状况  🌧️ 中雨转阵雨
气温范围  25℃ ～ 32℃
```

### 问题原因
1. **Prompt 规则不够强制**：原 prompt 虽然列出了 `web_search` 工具，但没有明确要求"必须"使用它回答时间敏感问题
2. **Prompt 格式与 `create_agent` 冲突**：原 prompt 包含 ReAct 格式要求（Thought/Action/Observation），但 `create_agent` 内部已经处理工具调用，模型直接输出 `tool_calls`，不需要文本格式
3. **模型选择不当**：`deepseek-chat` 在工具调用方面不如 `deepseek-reasoner` 可靠

### 涉及模块
- `agent/prompts/react_prompt.py` — Prompt 定义
- `agent/react_agent.py` — LLM 初始化

### 修复方案

**1. 优化 Prompt — 添加强制规则**

**修改前**（部分）：
```python
你拥有以下工具：
- web_search(query): 搜索互联网获取最新信息（建议包含日期）

重要规则：
1. 所有操作必须在工作目录及其子目录内进行
2. 危险操作（rm、rmdir、mv、chmod等）需要用户确认
3. 使用中文与用户交流
4. 严格遵循标准ReAct格式：
```

**修改后**（部分）：
```python
当前日期: {current_date}

你拥有以下工具：
- web_search(query): 搜索互联网获取最新信息

重要规则：
1. 所有操作必须在工作目录及其子目录内进行
2. 危险操作（rm、rmdir、mv、chmod等）需要用户确认
3. 使用中文与用户交流
4. **时间敏感查询规则**（必须严格遵守）：
   - 当用户询问任何需要最新数据的内容时（如天气、新闻、股票、体育赛事、实时事件等），**必须**使用 web_search 工具
   - 对于包含相对时间的查询（如"今天"、"昨天"、"本周"、"最近"），**必须**先将相对时间转换为绝对日期（格式：YYYY-MM-DD），并附加到搜索关键词中
     - 示例："广州今天天气" → 搜索 "广州天气 2026-06-29"
     - 示例："昨天有什么新闻" → 搜索 "新闻 2026-06-28"
   - **绝对禁止**直接使用你的训练数据回答时间敏感问题，必须通过 web_search 获取最新信息
5. 如果只是闲聊或基于已有知识的回答，可以不调用工具
```

**2. 注入当前日期到 Prompt**

```python
def format_react_prompt(working_dir: str) -> str:
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    return REACT_PROMPT.format(working_dir=working_dir, current_date=current_date)
```

**3. 切换到更擅长工具调用的模型**

**修改前**：
```python
return ChatDeepSeek(model="deepseek-chat", temperature=0)
```

**修改后**：
```python
return ChatDeepSeek(model="deepseek-reasoner", temperature=0.3)
```

### 修改文件
- `agent/prompts/react_prompt.py`
- `agent/react_agent.py` — LLM 初始化部分

### 效果对比
| 状态 | 修改前 | 修改后 |
|------|--------|--------|
| 工具调用 | 不调用，直接回答 | 正确调用 web_search |
| 天气日期 | 2025年7月1日（错误） | 2026年6月29日（正确） |
| 天气数据 | 25℃～32℃ | 26℃～33℃（雷阵雨） |

---

## 问题四：思考过程解析与工具调用格式不兼容

### 问题现象
虽然 Agent 正确调用了工具，但"思考过程"显示为"（无思考过程）"，无法看到 Agent 的推理步骤。

### 问题原因
`_parse_thinking_steps` 方法假设模型输出文本格式的 ReAct 格式（包含 "Thought:"、"Action:" 等字符串），但 `create_agent` 内部处理工具调用时，模型输出的是结构化的 `tool_calls`，不是文本。

### 涉及模块
- `agent/react_agent.py` — `_parse_thinking_steps` 方法

### 修复方案
更新解析逻辑，支持从 `AIMessage.tool_calls` 中提取工具调用信息：

**修改前**：
```python
def _parse_thinking_steps(self, messages: List[BaseMessage]):
    self.thinking_steps = []
    current_thought = ""
    current_action = ""

    for msg in messages:
        if isinstance(msg, AIMessage):
            content = msg.content or ""

            thought_start = content.find("Thought:")
            action_start = content.find("Action:")
            # ... 基于文本解析的逻辑

        elif hasattr(msg, "type") and msg.type == "tool":
            if self.thinking_steps:
                thought, action, _ = self.thinking_steps[-1]
                self.thinking_steps[-1] = (thought, action, msg.content)
```

**修改后**：
```python
def _parse_thinking_steps(self, messages: List[BaseMessage]):
    self.thinking_steps = []

    for msg in messages:
        if isinstance(msg, AIMessage):
            content = msg.content or ""

            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_name = tc.get('name', '未知')
                    tool_args = tc.get('args', {})
                    thought = content if content else f"需要调用 {tool_name} 工具获取信息"
                    action = f"{tool_name}({tool_args})"
                    self.thinking_steps.append((thought, action, ""))

        elif isinstance(msg, ToolMessage):
            if self.thinking_steps:
                thought, action, _ = self.thinking_steps[-1]
                obs = "已获取工具执行结果"
                self.thinking_steps[-1] = (thought, action, obs)
```

### 修改文件
- `agent/react_agent.py`

### 效果对比
| 状态 | 修改前 | 修改后 |
|------|--------|--------|
| 思考过程 | （无思考过程） | 正确显示步骤 |
| 工具名称 | 无法解析 | 正确显示 |
| 观察结果 | 无法解析 | "已获取工具执行结果" |

---

## 问题五：搜索结果包含无关内容（星座运势、广告等）

### 问题现象
Agent 搜索新闻或天气时，返回的原始结果中包含大量无关内容，如星座运势、广告推广、隐私政策等，严重影响输出质量。

```
【星座運勢/唐綺陽運勢週報：6/29-7/5 當心口舌是非...】
【2025年全球十大新聞（下）】星座運勢...
```

### 问题原因
`web_search` 工具直接返回 Tavily 搜索的原始结果，未做任何过滤。Tavily 的搜索结果来自整个互联网，包含各种类型的内容。

### 涉及模块
- `agent/tools/web_search.py`

### 修复方案
添加关键词过滤机制，移除包含无关内容的搜索结果：

```python
UNWANTED_KEYWORDS = [
    '星座', '运势', '算命', '塔罗', '占星', '生肖', '八字', '风水',
    '广告', '推广', '促销', '优惠', '打折', '团购',
    '色情', '赌博', '博彩',
    '免责声明', '版权声明', '隐私政策', '使用条款',
]

def filter_content(text: str) -> str:
    lines = text.split('\n')
    filtered_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(keyword in line for keyword in UNWANTED_KEYWORDS):
            continue
        if len(line) < 5:
            continue
        filtered_lines.append(line)
    return '\n'.join(filtered_lines)
```

在 `web_search` 函数中应用过滤：
```python
web_results = []
for r in results_list:
    title = r.get('title', '无标题')
    content = r.get('content', '无内容')

    if any(keyword in title for keyword in UNWANTED_KEYWORDS):
        continue

    content = filter_content(content)
    if not content:
        continue

    web_results.append(f"【{title}】\n{content}")
```

### 修改文件
- `agent/tools/web_search.py`

### 效果对比
| 状态 | 修改前 | 修改后 |
|------|--------|--------|
| 星座运势 | 显示 | 已过滤 |
| 广告推广 | 显示 | 已过滤 |
| 新闻内容 | 混杂无效信息 | 干净清晰 |

---

## 问题六：Observation 显示过多原始搜索内容

### 问题现象
思考过程中的 Observation 部分显示了过长的原始搜索结果（被截断为500字符），包含大量 HTML 标签、网页源码等无效信息，影响可读性。

```
👀 Observation:
  A Ukrainian high-ranking official was convicted of spying for Russia. Over 1,300 people died due to a heatwave in Europe. A Syrian
leader switched sides and became president after ending a civil war. 【国际新闻大事｜即时快讯、深度分析世界局势 - 香港01】card-header-icon 法国东北部小型跳伞飞机坠毁 　 11人全数罹难包括学员及教练 ...
```

### 问题原因
`_parse_thinking_steps` 中直接显示 `ToolMessage.content` 的原始内容，且未限制长度。

### 涉及模块
- `agent/react_agent.py` — `_parse_thinking_steps` 方法

### 修复方案
将 Observation 内容替换为简洁的提示信息：

**修改前**：
```python
elif isinstance(msg, ToolMessage):
    if self.thinking_steps:
        thought, action, _ = self.thinking_steps[-1]
        obs = str(msg.content)[:500] + "..." if len(str(msg.content)) > 500 else str(msg.content)
        self.thinking_steps[-1] = (thought, action, obs)
```

**修改后**：
```python
elif isinstance(msg, ToolMessage):
    if self.thinking_steps:
        thought, action, _ = self.thinking_steps[-1]
        obs = "已获取工具执行结果"
        self.thinking_steps[-1] = (thought, action, obs)
```

### 修改文件
- `agent/react_agent.py`

### 效果对比
| 状态 | 修改前 | 修改后 |
|------|--------|--------|
| Observation 长度 | 500+字符，含 HTML | 8字符，简洁提示 |
| 可读性 | 差，混杂无效信息 | 好，清晰简洁 |

---

## 问题七：搜索时间不准确（额外优化）

### 问题现象
Agent 有时会使用错误的日期进行搜索，例如模型训练数据的截止日期而非当前实际日期。

### 问题原因
模型依赖自身知识判断当前日期，而不是使用准确的实际日期。

### 涉及模块
- `agent/prompts/react_prompt.py`

### 修复方案
在系统 Prompt 中注入当前日期：

```python
REACT_PROMPT = """你是一个智能助手，可以在终端中操作。

当前工作目录: {working_dir}
当前日期: {current_date}
...
"""
```

```python
def format_react_prompt(working_dir: str) -> str:
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    return REACT_PROMPT.format(working_dir=working_dir, current_date=current_date)
```

### 修改文件
- `agent/prompts/react_prompt.py`

### 效果对比
| 状态 | 修改前 | 修改后 |
|------|--------|--------|
| 日期来源 | 模型猜测 | 系统注入 |
| 搜索关键词 | 可能过期 | 包含正确日期 |

---

## 最终效果示例

### 天气查询

```
🔍 思考过程
------------------------------------------------------------

步骤 1:
💡 Thought: 需要调用 web_search 工具获取信息
🛠️ Action: web_search({'query': '广州天气 2026-06-29'})
👀 Observation: 已获取工具执行结果

------------------------------------------------------------
╭───────────────────────────────────────────────────────────── 🤖 AI 回复 ──────────────────────────────────────────────────────────────╮
│ 🌤️ 广州今日天气（2026年6月29日）                                                                                                      │
│                                                                                                                                       │
│ 天气: 雷阵雨 | 气温: 26°C ~ 33°C | 湿度: 87% ~ 98%                                                                                  │
│                                                                                                                                       │
│ 建议：出门记得带伞☂️，穿着透气凉爽的衣物，注意防暑降温，多喝水                                                                         │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### 新闻查询

```
🔍 思考过程
------------------------------------------------------------

步骤 1:
💡 Thought: 需要调用 web_search 工具获取信息
🛠️ Action: web_search({'query': '2026年6月29日 全球重大新闻 今天大事'})

步骤 2:
💡 Thought: 需要调用 web_search 工具获取信息
🛠️ Action: web_search({'query': 'world news today June 29 2026'})
👀 Observation: 已获取工具执行结果

------------------------------------------------------------
╭───────────────────────────────────────────────────────────── 🤖 AI 回复 ──────────────────────────────────────────────────────────────╮
│ 🌍 今日国际大事速览                                                                                                                   │
│                                                                                                                                       │
│ 1️⃣ 美伊冲突持续升级                                                                                                                  │
│ 2️⃣ 欧洲遭遇史无前例热浪                                                                                                              │
│ 3️⃣ 韩国队世界杯出局                                                                                                                   │
│ ...                                                                                                                                   │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `agent/utils/token_utils.py` | tiktoken 延迟加载 + fallback |
| `agent/cli.py` | 移除多余的字符串拼接 |
| `agent/prompts/react_prompt.py` | 强化时间规则 + 注入当前日期 |
| `agent/react_agent.py` | 切换模型 + 重写思考过程解析 |
| `agent/tools/web_search.py` | 添加内容过滤 |
