# 🤖 AI Chatbot

一个基于 LangChain、LangGraph 的智能聊天机器人，支持标准 ReAct 工作流。用户可以在终端中进入任意目录后，通过 `agent` 命令启动 Agent，进行自然语言交互，Agent 会在工作目录内自主规划、思考、工具调用并返回结果。

## ✨ 特性

- **ReAct 工作流**: 标准的思考-行动-观察-回答循环
- **终端交互**: 类似 Claude Code 的命令行体验
- **文件操作**: 支持目录浏览、文件读写
- **命令执行**: 在工作目录内安全执行终端命令
- **数学计算**: 支持复杂数学表达式计算
- **网络搜索**: 集成 Tavily Search 获取最新信息，支持实时天气、新闻等
- **智能时间处理**: 自动将相对时间转换为绝对日期，确保搜索结果时效性
- **对话记忆**: 记住对话历史
- **安全机制**: 路径沙箱、危险操作确认、超时控制
- **双界面**: CLI 和 Streamlit Web 界面
- **健壮性**: 网络问题自动 fallback，错误优雅处理

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/yourname/ai-chatbot.git
cd ai-chatbot

# 安装依赖（开发模式）
pip install -e .

# 添加PATH（首次需要，或添加到~/.bashrc）
export PATH="/home/user/.local/bin:$PATH"
```

### 配置

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑.env，填入你的DeepSeek API Key
# DEEPSEEK_API_KEY=your-api-key-here
```

### 使用

**CLI 模式**（推荐）:
```bash
# 进入任意工作目录
cd /path/to/your/project

# 启动Agent
agent
```

**Web 模式**:
```bash
streamlit run app.py
```

## 📖 使用示例

```bash
🤖 AI Agent v0.1.0
📂 当前工作目录: /home/user/projects/myproject
============================================================
提示：输入 'exit' 或 'quit' 退出

你: 帮我查看当前目录下有哪些文件

🔍 思考过程
------------------------------------------------------------

步骤 1:
💡 Thought: 用户需要查看目录内容，我应该使用 list_files 工具。
🛠️ Action: list_files(path=".")
👀 Observation: 已获取工具执行结果

------------------------------------------------------------

🤖 AI 回复
当前目录包含以下文件和目录：
- src/ - 源代码目录
- README.md - 项目说明文档
- requirements.txt - 依赖列表

你: 广州今天天气怎么样？

🔍 思考过程
------------------------------------------------------------

步骤 1:
💡 Thought: 需要调用 web_search 工具获取信息
🛠️ Action: web_search({'query': '广州天气 2026-06-29'})
👀 Observation: 已获取工具执行结果

------------------------------------------------------------

🌤️ 广州今日天气（2026年6月29日）
天气: 雷阵雨 | 气温: 26°C ~ 33°C | 湿度: 87% ~ 98%

建议：出门记得带伞☂️，穿着透气凉爽的衣物，注意防暑降温
```

## 🛠️ 工具列表

| 工具 | 功能 |
|------|------|
| `terminal(command, cwd)` | 执行终端命令（带安全检查） |
| `list_files(path)` | 列出目录内容 |
| `read_file(filepath)` | 读取文件内容 |
| `write_file(filepath, content)` | 写入文件内容（覆盖） |
| `append_file(filepath, content)` | 追加内容到文件 |
| `create_directory(path)` | 创建目录 |
| `calculator(expression)` | 计算数学表达式 |
| `web_search(query)` | 搜索互联网获取最新信息 |

## 🔒 安全机制

- **路径沙箱**: 所有操作限制在当前工作目录及其子目录
- **危险操作确认**: rm、rmdir、mv、chmod 等命令需要用户确认
- **命令超时**: 终端命令执行超时时间 30 秒
- **文件大小限制**: 读取文件最大 10MB
- **路径遍历防护**: 禁止 `..` 路径访问

## 📁 项目结构

```
ai-chatbot/
├── pyproject.toml           # 包配置
├── .env.example             # 环境变量示例
├── .gitignore               # Git忽略规则
├── app.py                   # Streamlit Web界面
├── agent/
│   ├── cli.py               # CLI主入口
│   ├── react_agent.py       # ReAct Agent核心类
│   ├── tools/               # 工具模块
│   │   ├── terminal_tool.py    # 终端命令工具
│   │   ├── file_tool.py        # 文件系统工具
│   │   ├── calculator.py       # 计算器工具
│   │   └── web_search.py       # 网络搜索工具
│   ├── prompts/             # 提示词模板
│   │   └── react_prompt.py     # ReAct提示词模板
│   ├── memory/              # 记忆管理
│   │   └── memory_manager.py   # 对话记忆管理
│   └── utils/               # 工具函数
│       └── token_utils.py      # Token计数与裁剪
```

## 📦 依赖

**必需依赖**:
- langchain >= 1.3.0
- langgraph >= 1.2.0
- langchain-deepseek >= 1.0.0
- python-dotenv >= 1.0.0
- rich >= 15.0.0
- prompt_toolkit >= 3.0.0
- tiktoken >= 0.13.0
- numexpr >= 2.14.0
- langchain-tavily >= 0.2.0 (网络搜索)

**可选依赖**:
- streamlit >= 1.50.0 (Web界面)

## 🛡️ 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系

如有问题或建议，请通过 GitHub Issues 联系。
