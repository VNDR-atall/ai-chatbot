### 1. create a new repository on Github
### 2. create the project
```bash
mkdir ai-chatbot
cd ai-chatbot
git clone https://github.com/VNDR-atall/ai-chatbot.git
```

### 3. edit .gitignore
```bash
nano .gitignore
```

```text
.venv/
__pycache__/
*.pyc
.env
```
### 3. create virtual environment (.venv)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. install core dependencies
```bash
pip install langchain langchain-openai langchain-deepseek streamlit python-dotenv tiktoken chromadb duckduckgo-search numexpr
```

### 5. manage key
```bash
nano .env
```

```text
DEEPSEEK_API_KEY=sk-***
```

use the following in code:
```python
from dotenv import load_dotenv
load_dotenv()
```
Langchain will automatically read API key in environment variables.

### 6. verify installation
create `app.py`
```python
import streamlit as st
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()

st.title("Chatbot Demo (DeepSeek)")
llm = ChatDeepSeek(model="deepSeek-chat",temperature=0.7)

user_input = st.text_input("You:")
if user_input:
    response = llm.invoke(user_input)
	st.write(response.content)
```

```bash
streamlit run app.py
```

Open `http://localhost:8501` in the browser. If the Ask-Response is good, the environment good.

(In fact, it showed:)
```bash
(.venv) vndr@vndr-Legion-R9000P-ARX8:~/ai-chatbot$ streamlit run app.py

      👋 Welcome to Streamlit!

      If you'd like to receive helpful onboarding emails, news, offers, promotions,
      and the occasional swag, please enter your email address below. Otherwise,
      leave this field blank.

      Email: 15986655215@163.com

  You can find our privacy policy at https://streamlit.io/privacy-policy

  Summary:
  - This open source library collects usage statistics.
  - We cannot see and do not store information contained inside Streamlit apps,
    such as text, charts, images, etc.
  - Telemetry data is stored in servers in the United States.
  - If you'd like to opt out, add the following to ~/.streamlit/config.toml,
    creating that file if necessary:

    [browser]
    gatherUsageStats = false

2026-06-02 01:35:43.072 Uvicorn server started on 0.0.0.0:8501

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://172.20.10.2:8501

```
(And it opened the browser automatically.)
The result screen shot:
![[Pasted image 20260602013726.png]]
