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
        return len(text) // 4

def trim_messages(messages: list[BaseMessage], max_tokens: int = 4096) -> list[BaseMessage]:
    return trim_messages(
        messages,
        max_tokens=max_tokens,
        strategy="last",
        token_counter=count_tokens,
        include_system=True,
        start_on="human",
    )
