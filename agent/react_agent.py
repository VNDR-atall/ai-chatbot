from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import os
from dotenv import load_dotenv
from typing import List, Tuple

from .tools.terminal_tool import terminal
from .tools.file_tool import list_files, read_file, write_file, append_file, create_directory
from .tools.calculator import calculator
from .tools.web_search import web_search
from .prompts.react_prompt import format_react_prompt
from .memory.memory_manager import MemoryManager
from .utils.token_utils import count_tokens, trim_messages

load_dotenv()

class ReactAgent:
    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)
        self.system_prompt = format_react_prompt(self.working_dir)
        self.memory = MemoryManager(max_history=10)
        self.llm = self._init_llm()
        self.tools = self._init_tools()
        self.agent = self._init_agent()
        self.thinking_steps: List[Tuple[str, str, str]] = []
    
    def _init_llm(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")
        return ChatDeepSeek(model="deepseek-reasoner", temperature=0.3)
    
    def _init_tools(self):
        return [terminal, list_files, read_file, write_file, append_file, create_directory, calculator, web_search]
    
    def _init_agent(self):
        checkpointer = InMemorySaver()
        return create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
            checkpointer=checkpointer,
        )
    
    def get_thinking_steps(self) -> List[Tuple[str, str, str]]:
        return self.thinking_steps.copy()
    
    def clear_thinking_steps(self):
        self.thinking_steps = []
    
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
                else:
                    if content:
                        thought_start = content.find("Thought:")
                        action_start = content.find("Action:")
                        if thought_start != -1 and action_start != -1:
                            current_thought = content[thought_start:action_start].replace("Thought:", "").strip()
                            current_action = content[action_start:].replace("Action:", "").strip()
                            self.thinking_steps.append((current_thought, current_action, ""))
            
            elif isinstance(msg, ToolMessage):
                if self.thinking_steps:
                    thought, action, _ = self.thinking_steps[-1]
                    obs = "已获取工具执行结果"
                    self.thinking_steps[-1] = (thought, action, obs)
    
    def run(self, user_input: str) -> str:
        self.clear_thinking_steps()
        
        self.memory.add_user_message(user_input)
        
        history = self.memory.get_history()
        input_messages = [SystemMessage(content=self.system_prompt)]
        input_messages.extend(history)
        input_messages.append(HumanMessage(content=user_input))
        
        if count_tokens(input_messages) > 4096:
            input_messages = trim_messages(input_messages, max_tokens=4096)
        
        config = {"configurable": {"thread_id": self.memory.get_thread_id()}}
        
        try:
            result = self.agent.invoke({"messages": input_messages}, config=config)
            
            self._parse_thinking_steps(result.get("messages", []))
            
            final_answer = ""
            for msg in result.get("messages", []):
                if isinstance(msg, AIMessage) and msg.content:
                    content = msg.content
                    final_start = content.find("finalAnswer:")
                    if final_start != -1:
                        final_answer = content[final_start:].replace("finalAnswer:", "").strip()
                    elif not msg.tool_calls:
                        final_answer = content
            
            if not final_answer and result.get("messages"):
                last_msg = result["messages"][-1]
                if hasattr(last_msg, "content"):
                    content = str(last_msg.content)
                    final_start = content.find("finalAnswer:")
                    if final_start != -1:
                        final_answer = content[final_start:].replace("finalAnswer:", "").strip()
                    else:
                        final_answer = content
            
            if final_answer:
                self.memory.add_ai_message(final_answer)
            
            return final_answer if final_answer else "抱歉，我无法处理这个问题。"
        
        except Exception as e:
            return f"❌ 执行出错: {str(e)}"
