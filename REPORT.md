# AI Chatbot 项目构建流程记录

## 项目概述

本项目是一个基于 LangChain、LangGraph 和 Streamlit 的智能聊天机器人，支持标准 ReAct 工作流。用户可以在终端中进入任意目录后，通过 `agent` 命令启动 Agent，进行自然语言交互，Agent 会在工作目录内自主规划、思考、工具调用并返回结果。

## 技术栈

- **核心框架**: LangChain v1.3+, LangGraph v1.2+
- **模型**: DeepSeek Chat API
- **界面**: Streamlit, Rich (CLI)
- **工具**: Terminal, File System, Calculator, Web Search
- **包管理**: pip (pyproject.toml)

---

## 阶段一：基础设施搭建

### 1.1 创建项目配置文件

**文件**: `pyproject.toml`

```toml
[project]
name = "ai-chatbot"
version = "0.1.0"
dependencies = [
    "langchain>=1.3.0",
    "langgraph>=1.2.0",
    "langchain-deepseek>=1.0.0",
    "python-dotenv>=1.0.0",
    "rich>=15.0.0",
    "prompt_toolkit>=3.0.0",
    "tiktoken>=0.13.0",
    "numexpr>=2.14.0",
]

[project.scripts]
agent = "agent.cli:main"
```

**关键点**:
- 使用 `[project.scripts]` 注册 `agent` 命令，实现全局调用
- 定义必需依赖和可选依赖（web、search）

### 1.2 创建环境变量示例

**文件**: `.env.example`

```bash
DEEPSEEK_API_KEY=your-api-key-here
```

**关键点**:
- 用户只需复制为 `.env` 并填入 API Key 即可使用
- 支持 GitHub 部署，他人无需修改代码

### 1.3 创建包初始化文件

**文件**: `agent/__init__.py`

```python
from .cli import main
from .react_agent import ReactAgent
__version__ = "0.1.0"
```

### 1.4 创建 CLI 主入口

**文件**: `agent/cli.py`

**核心功能**:
- 加载环境变量并验证 API Key
- 自动检测当前工作目录
- 使用 Rich 库实现彩色终端界面
- 交互式对话循环

**关键点**:
- 使用 `rich.console.Console` 和 `rich.prompt.Prompt`
- 支持 `exit`/`quit`/`bye` 退出命令
- 优雅处理 KeyboardInterrupt 和 EOFError

### 1.5 创建安全终端工具

**文件**: `agent/tools/terminal_tool.py`

**安全机制**:
- 危险命令检测（rm、rmdir、mv、chmod 等）
- 路径沙箱限制（只能在工作目录及其子目录操作）
- 命令超时控制（30秒）
- 结构化输出（stdout/stderr/returncode）

**危险命令列表**:
```python
DANGEROUS_COMMANDS = ["rm", "rmdir", "mv", "chmod", "git reset", "git clean"]
```

### 1.6 创建文件系统工具

**文件**: `agent/tools/file_tool.py`

**提供功能**:
- `list_files(path)` - 列出目录内容
- `read_file(filepath)` - 读取文件内容
- `write_file(filepath, content)` - 写入文件（覆盖）
- `append_file(filepath, content)` - 追加内容
- `create_directory(path)` - 创建目录

**安全机制**:
- 路径验证（防止 `..` 遍历攻击）
- 文件大小限制（最大 10MB）
- 路径沙箱限制

### 1.7 安装验证

```bash
pip install -e . --break-system-packages
export PATH="/home/vndr/.local/bin:$PATH"
agent
```

**验证结果**: ✅ Agent 成功启动，显示工作目录和交互提示

---

## 阶段二：ReAct 核心完善

### 2.1 创建 ReAct 提示词模板

**文件**: `agent/prompts/react_prompt.py`

**标准 ReAct 格式**:
```
Thought: [思考内容]
Action: [工具名]([参数])
Observation: [工具返回结果]
...
finalAnswer: [最终回答]
```

**提示词结构**:
- 工具列表（8个工具）
- 重要规则（路径限制、危险操作确认、中文交流）
- ReAct 格式说明
- 示例演示
- 工作流程说明

### 2.2 创建 Token 工具

**文件**: `agent/utils/token_utils.py`

**功能**:
- `count_tokens(messages)` - 计算消息 token 数量
- `trim_messages(messages, max_tokens)` - 裁剪超出限制的消息

**实现**:
```python
import tiktoken
tokenizer = tiktoken.get_encoding("cl100k_base")
```

### 2.3 创建记忆管理模块

**文件**: `agent/memory/memory_manager.py`

**功能**:
- 对话历史管理（最多 10 轮）
- 线程 ID 管理（会话隔离）
- 消息添加和获取

**关键点**:
- 使用 LangChain 的 BaseMessage 类型
- 自动清理超出限制的历史消息

### 2.4 重构 ReactAgent 核心类

**文件**: `agent/react_agent.py`

**核心改进**:
- 集成 ReAct 提示词模板
- 集成记忆管理模块
- 集成 Token 裁剪工具
- 思考过程解析（提取 Thought/Action/Observation）
- 最终答案提取（finalAnswer）

**思考过程解析逻辑**:
```python
def _parse_thinking_steps(self, messages):
    for msg in messages:
        if isinstance(msg, AIMessage):
            # 提取 Thought 和 Action
        elif msg.type == "tool":
            # 关联 Observation
```

### 2.5 增强 CLI 思考过程可视化

**文件**: `agent/cli.py`（更新）

**显示格式**:
```
🔍 思考过程
------------------------------------------------------------

步骤 1:
💡 Thought: 用户需要查看目录内容
🛠️ Action: list_files(path=".")
👀 Observation: ...

步骤 2:
💡 Thought: 用户需要读取文件
🛠️ Action: read_file(filepath="README.md")
👀 Observation: ...

------------------------------------------------------------

🤖 AI 回复
```

---

## 阶段三：工具整合

### 3.1 创建计算器工具

**文件**: `agent/tools/calculator.py`

**功能**:
- 使用 `numexpr` 库计算数学表达式
- 支持复杂表达式（如 `sin(3.14)`, `sqrt(16)`）

### 3.2 创建网络搜索工具

**文件**: `agent/tools/web_search.py`

**功能**:
- 使用 Tavily Search API
- 返回 AI 生成答案 + 网页摘要
- 优雅处理未安装依赖的情况

### 3.3 注册所有工具

**文件**: `agent/tools/__init__.py`（更新）

**完整工具列表**:
```python
__all__ = [
    "terminal", "list_files", "read_file", "write_file", 
    "append_file", "create_directory", "calculator", "web_search"
]
```

### 3.4 更新 ReactAgent

**文件**: `agent/react_agent.py`（更新）

**工具注册**:
```python
def _init_tools(self):
    return [terminal, list_files, read_file, write_file, 
            append_file, create_directory, calculator, web_search]
```

### 3.5 更新提示词模板

**文件**: `agent/prompts/react_prompt.py`（更新）

**添加新工具描述**:
```
- calculator(expression): 计算数学表达式（如 3+4*2）
- web_search(query): 搜索互联网获取最新信息（建议包含日期）
```

---

## 阶段四：界面完善

### 4.1 重构 Streamlit 界面

**文件**: `app.py`

**改进**:
- 集成模块化 ReactAgent
- 侧边栏显示思考过程
- 工作目录显示
- 会话 ID 显示

**核心代码**:
```python
from agent.react_agent import ReactAgent

if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent(working_dir=os.getcwd())
```

### 4.2 更新 Git 忽略规则

**文件**: `.gitignore`（更新）

**添加内容**:
```
.env.local
.DS_Store
*.egg-info/
dist/
build/
*.log
```

### 4.3 最终验证

**CLI 验证**: ✅ `agent` 命令启动成功

**Web 验证**: ✅ `streamlit run app.py` 启动成功

---

## 项目架构总结

```
ai-chatbot/
├── pyproject.toml           # 包配置
├── .env.example             # 环境变量示例
├── .gitignore               # Git忽略规则
├── app.py                   # Streamlit界面
├── agent/
│   ├── cli.py               # CLI入口
│   ├── react_agent.py       # ReAct Agent核心
│   ├── tools/               # 工具模块
│   │   ├── terminal_tool.py
│   │   ├── file_tool.py
│   │   ├── calculator.py
│   │   └── web_search.py
│   ├── prompts/             # 提示词模板
│   │   └── react_prompt.py
│   ├── memory/              # 记忆管理
│   │   └── memory_manager.py
│   └── utils/               # 工具函数
│       └── token_utils.py
```

---

## 功能清单

| 工具 | 功能 | 安全机制 |
|------|------|----------|
| terminal | 执行终端命令 | 危险命令检测、路径沙箱、超时控制 |
| list_files | 列出目录内容 | 路径验证 |
| read_file | 读取文件内容 | 路径验证、文件大小限制 |
| write_file | 写入文件 | 路径验证、覆盖确认 |
| append_file | 追加内容 | 路径验证 |
| create_directory | 创建目录 | 路径验证 |
| calculator | 数学计算 | 表达式解析 |
| web_search | 网络搜索 | API调用 |

---

## 使用流程

**开发模式**:
```bash
# 克隆项目
git clone <repo-url>
cd ai-chatbot

# 安装依赖
pip install -e .

# 配置API密钥
cp .env.example .env
# 编辑.env，填入DEEPSEEK_API_KEY

# 启动CLI（在任意目录）
agent

# 启动Web界面
streamlit run app.py
```

**用户使用**:
1. 进入目标目录
2. 运行 `agent` 命令
3. 自然语言交互
4. Agent 自动规划、调用工具、返回结果
5. 输出 finalAnswer

---

## 安全策略

1. **命令白名单**: 仅允许安全命令，危险命令需用户确认
2. **路径沙箱**: 所有操作限制在工作目录及其子目录
3. **超时控制**: 命令执行超时时间 30 秒
4. **文件大小限制**: 读取文件最大 10MB
5. **路径遍历防护**: 禁止 `..` 路径访问

---

## 未来扩展方向

1. **多模型支持**: 支持其他 LLM 模型
2. **RAG 集成**: 添加文档检索增强生成
3. **持久化记忆**: 使用数据库存储对话历史
4. **多会话管理**: 支持同时管理多个会话
5. **插件系统**: 支持动态加载工具插件
6. **任务规划**: 复杂任务分解和规划能力
