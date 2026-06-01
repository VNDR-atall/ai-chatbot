import streamlit as st
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()

st.title("Chatbot Demo (DeepSeek)")

# 使用 DeepSeek 聊天模型
llm = ChatDeepSeek(
    model="deepseek-chat",      # 或 "deepseek-reasoner"
    temperature=0.7,
    # API key 会自动从环境变量 DEEPSEEK_API_KEY 读取
)

user_input = st.text_input("You:")
if user_input:
    response = llm.invoke(user_input)
    st.write(response.content)
