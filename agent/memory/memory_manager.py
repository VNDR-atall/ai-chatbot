from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from typing import List, Optional
import uuid

class MemoryManager:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversation_history: List[BaseMessage] = []
        self.thread_id = str(uuid.uuid4())
    
    def add_message(self, message: BaseMessage):
        self.conversation_history.append(message)
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]
    
    def get_history(self) -> List[BaseMessage]:
        return self.conversation_history.copy()
    
    def get_last_n_messages(self, n: int) -> List[BaseMessage]:
        return self.conversation_history[-n:]
    
    def add_user_message(self, content: str):
        self.add_message(HumanMessage(content=content))
    
    def add_ai_message(self, content: str):
        self.add_message(AIMessage(content=content))
    
    def clear_history(self):
        self.conversation_history = []
        self.thread_id = str(uuid.uuid4())
    
    def get_thread_id(self) -> str:
        return self.thread_id
    
    def set_thread_id(self, thread_id: str):
        self.thread_id = thread_id
    
    def get_message_count(self) -> int:
        return len(self.conversation_history)
