import tiktoken
from langchain_core.messages import BaseMessage, trim_messages

tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(messages: list[BaseMessage]) -> int:
    text = " ".join(msg.content for msg in messages if hasattr(msg, "content"))
    return len(tokenizer.encode(text))

def trim_messages(messages: list[BaseMessage], max_tokens: int = 4096) -> list[BaseMessage]:
    return trim_messages(
        messages,
        max_tokens=max_tokens,
        strategy="last",
        token_counter=count_tokens,
        include_system=True,
        start_on="human",
    )
