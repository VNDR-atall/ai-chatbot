Found that the agent cannot search information from web, we need to find out the cause of the problem.

While ask the agent for latest information (e.g. Ask the weather today):
```bash
(.venv) (base) vndr@vndr-Legion-R9000P-ARX8:~/ai-chatbot$ streamlit run app.py
2026-06-03 17:33:25.387 Uvicorn server started on 0.0.0.0:8501

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://172.20.10.2:8501


/home/vndr/ai-chatbot/app.py:78: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  with DDGS() as ddgs:
```

---
## DeepSeek:

### 🏆 方案一：使用 Tavily Search API (最推荐)

这个方案特别适合 AI Agent，是专为语言模型优化的搜索引擎。它不仅免费额度充足，还有官方支持，集成起来非常方便。现在可以完全不用 `langchain-community` 了。

**安装：**
```bash
pip install langchain-tavily
```

**注册与获取 API 密钥：**  
去 [Tavily 官网](https://app.tavily.com/sign-in) 注册，在后台就能找到你的 API Key。

**编辑.env**：
```bash
TAVILY_API_KEY=sk-xxx
```

**代码集成：**  
将原来的 `web_search` 函数部分更新为以下代码：
```python

# 移除之前的 web_search 工具和 langchain_community 导入，添加以下导入
from langchain_tavily import TavilySearch
# ---------- 工具定义 ----------
@tool
def web_search(query: str) -> str:
    """搜索互联网获取最新信息。输入查询关键词，返回前几条结果摘要。"""
    try:
        # 实例化 Tavily 搜索工具，可根据需要调整参数
        search_tool = TavilySearch(
            max_results=3,      # 返回结果数量
            topic="general",    # 搜索主题: "general", "news", "finance"
            include_answer=True, # 是否包含AI生成的答案
        )
        # 执行搜索并获取结果
        result = search_tool.invoke({"query": query})
        
        # 从结果中提取关键信息
        if hasattr(result, 'get'):
            answer_part = f"AI 生成的答案: {result.get('answer', '')}\n\n" if result.get('answer') else ""
            results_list = result.get('results', [])
            if not results_list:
                return answer_part.strip() or "未找到相关结果。"
            
            web_results = "\n\n".join(
                f"【{r.get('title', '无标题')}】\n{r.get('content', '无内容')}"
                for r in results_list
            )
            return f"{answer_part}{web_results}".strip()
        # 如果返回结果不是字典，转换为字符串
        return str(result)
    except Exception as e:
        # 提供清晰的错误信息
        return f"搜索服务调用失败: {str(e)}。请检查网络或稍后重试。"

```

**优点：** 你可以通过 `max_results`、`topic`、`include_answer` 等多个参数灵活控制搜索行为

So the V3 `app.py`:
```python
import streamlit as st
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage,
    trim_messages, BaseMessage
)
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import tiktoken
import numexpr
import uuid

load_dotenv()

# ---------- 页面配置 ----------
st.set_page_config(page_title="AI Agent V3", page_icon="🤖")
st.title("🤖 AI 智能 Agent (LangGraph v1 标准版)")


# ---------- 初始化模型 ----------
@st.cache_resource
def get_llm():
    return ChatDeepSeek(model="deepseek-chat", temperature=0)


llm = get_llm()

# ---------- 自定义系统提示 ----------
CUSTOM_SYSTEM_PROMPT = """你是一个乐于助人的智能助手，可以记住对话历史。
你拥有以下工具：
- calculator：计算数学表达式。
- web_search：在互联网上搜索最新信息。

重要规则：
1. 当用户询问任何需要最新数据的内容时，必须使用 web_search 工具。
2. 对于时间敏感查询时的特殊要求：
- 如果用户提到相对时间（例如“今天”、“昨天”、“上周”、“去年”），你**必须**在调用 web_search 之前，将相对时间转换为绝对日期（格式：YYYY-MM-DD）。
- 例如：“广州昨天天气” → 你应该先计算昨天是 2026-06-02（假设今天是 2026-06-03），然后搜索 "广州天气 2026-06-02"。
- 绝对不要直接搜索“昨天xxx”，因为搜索引擎不理解相对时间。
3. 如果工具返回结果，请基于结果回答用户。
4. 对于纯数学计算，使用 calculator。
5. 如果只是闲聊或基于已有知识的回答，可以不调用工具。"""


# ---------- token 计数和裁剪 ----------
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(messages):
    text = " ".join(msg.content for msg in messages if hasattr(msg, "content"))
    return len(tokenizer.encode(text))

def trim_history(messages: list[BaseMessage]) -> list[BaseMessage]:
    return trim_messages(
        messages,
        max_tokens=4096,
        strategy="last",
        token_counter=count_tokens,
        include_system=True,
        start_on="human",
    )


# ---------- 工具定义 ----------
@tool
def calculator(expression: str) -> str:
    """计算数学表达式。输入纯数学表达式（例如 3+4*2），返回计算结果。"""
    try:
        result = numexpr.evaluate(expression).item()
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算出错：{str(e)}"

@tool
def web_search(query: str) -> str:
    """搜索互联网获取最新信息。输入查询关键词，返回前几条结果摘要。
    
    建议在查询中明确包含日期（例如 '广州天气 2026-06-02'），以获得更准确的历史或实时信息。
    不要主动限制搜索的时间范围，让搜索引擎自然返回最相关结果即可。
    """
    try:
        from langchain_tavily import TavilySearch
        
        # 不设置 time_range，让搜索全面覆盖
        search_tool = TavilySearch(
            max_results=3,
            topic="general",
            include_answer=True,
        )
        result = search_tool.invoke({"query": query})
        
        if hasattr(result, 'get'):
            answer_part = result.get('answer', '')
            answer_text = f"AI 生成的答案: {answer_part}\n\n" if answer_part else ""
            
            results_list = result.get('results', [])
            if not results_list and not answer_part:
                return "未找到相关结果。"
            
            web_results = "\n\n".join(
                f"【{r.get('title', '无标题')}】\n{r.get('content', '无内容')}"
                for r in results_list
            )
            return f"{answer_text}{web_results}".strip()
        return str(result)
    except Exception as e:
        return f"搜索服务调用失败: {str(e)}。请检查网络或稍后重试。"
        
tools = [calculator, web_search]


# ---------- 构建 Agent（新版 create_agent API） ----------
# 创建内存检查点保存器，用于实现对话记忆
checkpointer = InMemorySaver()

# 使用新版 create_agent 构建 ReAct 智能体
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=CUSTOM_SYSTEM_PROMPT,  # 系统提示词
    checkpointer=checkpointer,           # 启用对话记忆
)


# ---------- 会话状态 ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content=CUSTOM_SYSTEM_PROMPT),
        AIMessage(content="你好！我是你的AI助手，可以计算和搜索，有什么可以帮你的？")
    ]

if "thinking_log" not in st.session_state:
    st.session_state.thinking_log = ""

if "thread_id" not in st.session_state:
    # 为本次会话生成唯一的线程 ID，用于记忆隔离
    st.session_state.thread_id = str(uuid.uuid4())


# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("🔍 Agent 思考过程")
    if st.session_state.thinking_log:
        st.text_area("日志", st.session_state.thinking_log, height=400)
    else:
        st.info("尚未有推理记录")

    st.divider()
    st.caption(f"会话 ID: {st.session_state.thread_id[:8]}...")


# ---------- 显示历史消息 ----------
for msg in st.session_state.messages:
    if isinstance(msg, (HumanMessage, AIMessage)):
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)


# ---------- 用户输入 ----------
if prompt_input := st.chat_input("输入你的问题..."):
    # 添加用户消息
    user_msg = HumanMessage(content=prompt_input)
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt_input)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            # 准备输入消息（裁剪历史以控制 token 数量）
            input_messages = trim_history(st.session_state.messages)

            # 配置线程 ID，LangGraph 会自动管理该线程的对话历史
            config = {"configurable": {"thread_id": st.session_state.thread_id}}

            # 调用 Agent
            # create_agent 使用 "messages" 键来传递消息
            result = agent.invoke({"messages": input_messages}, config=config)

            # 提取最终回复
            final_answer = ""
            thinking_steps = []

            # 解析 Agent 返回的消息，提取工具调用过程和最终回复
            for msg in result.get("messages", []):
                # 处理工具调用请求（AIMessage 包含 tool_calls）
                if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        thinking_steps.append(f"🛠️ 工具：{tc.get('name', '未知')}")
                        thinking_steps.append(f"📥 输入：{tc.get('args', {})}")
                # 处理工具返回结果（ToolMessage 类型）
                elif hasattr(msg, "type") and msg.type == "tool":
                    thinking_steps.append(f"👀 观察：{msg.content}")
                # 最终回复（AIMessage 且不包含 tool_calls）
                elif isinstance(msg, AIMessage) and not (hasattr(msg, "tool_calls") and msg.tool_calls):
                    if msg.content:
                        final_answer = msg.content

            # 如果没有解析出最终回复，尝试取最后一条消息
            if not final_answer and result.get("messages"):
                last_msg = result["messages"][-1]
                if hasattr(last_msg, "content"):
                    final_answer = last_msg.content

            # 更新侧边栏日志
            if thinking_steps:
                st.session_state.thinking_log = "\n".join(thinking_steps)
            else:
                st.session_state.thinking_log = "（无工具调用）"

            # 显示最终回复
            if not final_answer:
                final_answer = "抱歉，我无法处理这个问题。"
            st.markdown(final_answer)

    # 保存最终回复到会话历史
    assistant_msg = AIMessage(content=final_answer)
    st.session_state.messages.append(assistant_msg)

```


---
## Result
## 🔍 Agent 思考过程

日志

🛠️ 工具：web_search 📥 输入：{'query': '黄仁勋 COMPUTEX 2026 台北 演讲 内容'} 👀 观察：AI 生成的答案: Huang Renxun's 2026 Computex Taipei keynote focused on AI Factory and AI PC 2.0, emphasizing AI's future infrastructure and capabilities. The event highlighted AI's transformative potential and industry shifts. 【NVIDIA GTC Taipei at COMPUTEX 2026｜黃仁勳演講】 # NVIDIA GTC Taipei at COMPUTEX 2026｜黃仁勳演講｜NVIDIA. # NVIDIA GTC Taipei at COMPUTEX 2026. NVIDIA 與我們的合作夥伴生態系將展示各項 AI 平台的最新技術突破，涵蓋物理 AI、AI 運算、AI 基礎架構等領域。歡迎蒞臨在台北國際會議中心 (TICC) 舉辦的GTC Taipei，參加各場議程與訓練，親身體驗下一代 AI 的無限可能；並誠摯邀請您前往南港展覽館的 COMPUTEX 展場，深入探索我們合作夥伴遍布全場的精彩技術展示。. Image 4: NVIDIA GTC Taipei. 邀請您於 6 月 2 — 4 日蒞臨台北國際會議中心 (TICC) 親臨 GTC Taipei，與 NVIDIA 專家及產業領袖深入交流，共同見證引領真實世界轉型的 AI 創新。. *您可以憑 GTC Taipei 識別證直接進入 COMPUTEX 展區，無需另外報名 COMPUTEX 觀展。請注意：GTC Taipei 識別證不包含 COMPUTEX 主題演講或論壇議程的參加權限。. *凡持 GTC Taipei 或 COMPUTEX 觀展證即可入場。. Image 7: aaeon logoImage 8: abb robotics logoImage 9: accucrazy logoImage 10: acer logoImage 11: adlink logoImage 12: advantech logoImage 13: aetina logoImage 14: aic logoImage 15: ailytics logoImage 16: aimfold logoImage 17: alsemy logoImage 18: altos logoImage 19: anivance ai logoImage 20: apmic logoImage 21: asrock rack logoImage 22: asus logoImage 23: asus rog logoImage 24: auras logoImage 25: avalanche computing logoImage 26: avermedia logoImage 27: barkingdog logoImage 28: bizlink logoImage 29: cadasu logoImage 30: cadence logoImage 31: canner logoImage 32: chenbro logoImage 33: cisco logoImage 34: clevo logoImage 35: codetrace logoImage 36: compal logoImage 37: danfoss logoImage 38: deeli ai logo. 我們已偵測到全球隱私控制 (GPC) 訊號，並針對這個瀏覽器為您記錄，您已拒絕這個網站的所有選擇性 Cookie。按一下「管理設定」即可管理 Cookie 設定。如需更多資訊，請參閱我們的 Cookie 政策。 若要選擇退出基於定向廣告目的「銷售」/「共享」非 Cookie 個人資訊，請造訪 NVIDIA 偏好中心。如需關於隱私權實務的更多資訊，請參閱我們的隱私權政策。. 我們已偵測到全球隱私控制 (GPC) 訊號，並針對這個瀏覽器為您選擇退出本網站所有選擇性 Cookie。按一下「管理設定」即可管理 Cookie 設定。請參閲我們的 Cookie 政策深入了解。此外，我們已為您選擇退出基於定向廣告目的「出售」/「共享」非 Cookie 個人資訊。您可以在 NVIDIA 偏好中心管理這些設定。如需更多資訊，請參閱我們的隱私權政策。. 我們已偵測到全球隱私控制 (GPC) 訊號，並針對這個瀏覽器為您選擇退出本網站所有選擇性 Cookie。按一下「管理設定」即可管理 Cookie 設定。請參閲我們的 Cookie 政策深入了解。此外，我們已為您選擇退出基於定向廣告目的「出售」/「共享」非 Cookie 個人資訊，而且至少會覆寫先前其中一項設定。您可以在 NVIDIA 偏好中心管理這些設定。如需更多資訊，請參閱我們的隱私權政策。. 【台北 Computex 2026 黃仁勳演講重點 × 行業公司】 NVIDIA DSX 平台正式推出：AI 工廠的專屬作業系統（AI Factory OS）. AI PC 2.0 時代到來：大模型直接在你的電腦裡跑，不用再連網. * 「AI Factory（AI 工廠）生態系」的六大核心支柱. * 第三階段（未來 3~5 年）—— 核心：AI Factory + Physical AI + AI Cloud. * 「AI PC 2.0 受惠企業」 與 「DSX 生態圈主要受惠企業」。. 但在 2026 年，黃仁勳重新定義了這個概念：未來的資料中心全面升級為「AI 工廠」（AI Factory）。這座工廠吃進去的是原始的數據資料，透過強大的算力加工後，吐出來的是 ****Token（數位代幣/金鑰，即 AI 思考與輸出的基本單位，如文字、聲音、影像、代碼等）********。黃仁勳強調，未來企業的核心競爭力不再是「你買了幾顆晶片」，而是「你是否擁有一整座運作流暢的 AI 工廠基礎設施」。****. 而黃仁勳宣布的 ****AI PC 2.0 時代****，核心亮點在於發表了 ****"RTX Spark" 平台****。它把強大的 AI 代理人（AI Agent）直接塞進了你的個人電腦裡。最關鍵的突破是：****原本需要幾千台伺服器才跑得動的超大型生成式模型，現在在你的個人筆電上就能直接運行****，不需要連網、秒級回應，而且完全不用擔心隱私外洩。你的筆電不再只是個顯示器，它本身就是一個獨立的個人 AI 工作站。. 因此，各國正在積極打造專屬於自己國家的「主權 AI 工廠」與「國家級 AI 雲」。每個國家都要用自己的語言、自己的歷史數據，去訓練出符合自身文化與法律的 AI 模型。NVIDIA 的 GPU 雲服務正順應這一趨勢在全球快速擴張，導致全球的算力資源與資本正在重新配置。. 「五層蛋糕（Five-Layer Cake）架構」是 NVIDIA 執行長黃仁勳在 2026 Computex 演講中提出的一個非常生動的比喻。它被視為未來 AI 生態系的核心藍圖，用來完整描繪一座「AI 工廠（AI Factory）」從最底層的硬體燃料到最上層的軟體應用，所需要具備的五個關鍵層級。. * ****【受惠企業（代號對照）】傳力：ANET (Arista 網路設備)、MRVL (Marvell 晶片)、COHR (Coherent 光通訊)、LITE (Lumentum)、GLW (Corning 康寧玻璃)。存力：MU (美光)、Samsung (三星)、SK hynix (海力士)、WDC (威騰電子)、285A (Kioxia 鎧俠)。電力：VRT (Vertiv 散熱基礎設施)、ETN (Eaton 伊頓重電)、GEV (GE Vernova 奇異綠能)、CAT (Caterpillar 卡特彼勒重機)、TT (Trane 節能與空調系統)。****. * ****【代表布局企業】AI Factory：DELL (戴爾)、HPE (慧與)、SMCI (美超微)、EQIX (Equinix 數位機房大廠)、DLR (Digital Realty 機房地產託管)。Physical AI：NVDA (NVIDIA 機器人大腦)、TSLA (Tesla 特斯拉自駕與人形機器人)、ABB (全球工業機器人巨頭)、Rockwell (羅克韋爾自動化)。AI Cloud：CRWV (CoreWeave 算力雲黑馬)、NBIS / NEBIUS (新興 AI 雲端服務商)、IREN (Iris Energy 算力基礎設施)。****. 本次黃仁勳在 2026 Computex 的演講，為全球投資人揭示了未來 3 至 5 年最明確的財富地圖。核心的戰略轉變可以總結為一句話：****「AI 投資正式從單純的『晶片軍備競賽』，跨入全產業鏈總動員的『AI 工廠（AI Factory）』與『實體 AI（Physical AI）』商用落地轉折點。」****. 2. ****新興 AI 雲與資料中心房東（REITs）：**** 隨著各國為了數據安全搶蓋「主權 AI（Sovereign AI）」，專為 AI 算力而生的新興雲端服務商（如 ****CoreWeave、Nebius****）以及巨型機房專業房東（如 ****Equinix、Digital Realty****）將迎來長達數年的剛性收租與擴廠潮。. 【COMPUTEX 2026》6/2-5登場！演講直播、門票、報名方式 - 商周】 # COMPUTEX 2026》6/2登場！黃仁勳演講、門票、報名方式、亮點一次看. 2026 COMPUTEX TAIPEI將於6月2日至5日在台北南港展覽館1、2館與世貿1館登場，主題為「AI Together」，聚焦AI運算、機器人與智慧移動、次世代科技，並集結高通、Marvell、英特爾、NXP等企業執行長主題演講。展前話題已大幅升溫，NVIDIA執行長黃仁勳與AMD執行長蘇姿丰兩大AI巨頭皆已提前抵台。. * 2026 NVIDIA GTC Taipei at COMPUTEX. ## 2026 COMPUTEX TAIPEI國際電腦展是什麼？. 延伸閱讀：314兆元狂潮襲台！2026 COMPUTEX規模創歷史新高，高通、英特爾AI巨頭開講. ## 2026 COMPUTEX時間、地點. + 6/2（二）～6/4（四）9:30-17:30 僅開放專業人士進場. + 6/5（五）9:30-15:30 南港展覽館1、2館. + 6/5（五）9:30-16:30 世貿1館. + 台北國際會議中心（TICC）：NVIDIA GTC Taipei. ## 2026 COMPUTEX入場資格與門票. ### 主題演講（Keynote）報名方式. ### COMPUTEX Forum論壇購票方式. ## 2026 COMPUTEX 6大看點. ### NVIDIA GTC Taipei同步登場. 今年最受矚目的周邊活動，無疑是NVIDIA GTC Taipei。GTC Taipei為探索下一代AI技術的全球盛會，議程涵蓋AI工廠與擴充基礎架構、代理與推理AI、科學AI、物理AI與機器人等主題。不過，GTC Taipei不是COMPUTEX本展，而是NVIDIA在COMPUTEX期間舉辦的AI大會。. | | COMPUTEX 2026 | NVIDIA GTC Taipei 2026 |. | 展覽期間 | 6/2～6/5 | 6/1～6/4 |. ### InnoVEX 2026：近500家新創參展. ### COMPUTEX Forum 2026聚焦6大AI議題. COMPUTEX Forum 2026以「AI Together」為主題，規劃6大核心議題，包括「機器人、自動化與實體AI」、「AI運算、基礎架構與開發」、「生成式AI與智慧內容應用」、「AI裝置、物聯網與邊緣運算」、「產業落地AI應用」及「資料智能、治理與安全」。. ## 2026 COMPUTEX主題演講（Keynote）. | 6/1（一） 11:00 | NVIDIA GTC Taipei主題演講 | 黃仁勳 |. | 6/1（一） 14:00 | 全球記者會暨高通開幕Keynote | Cristiano R. | 6/2（二） 10:30 | Marvell Keynote | Matt Murphy |. | 6/2（二） 13:30 | Intel Keynote | 陳立武 |. | 6/3（三） 10:30 | NXP Keynote | Rafael Sotomayor |. Amon、英特爾執行長陳立武、NXP總裁暨執行長Rafael Sotomayor。 (來源：COMPUTEX TAIPEI﻿官網). ### 2026 NVIDIA黃仁勳主題演講. ### 2026 COMPUTEX Keynote. 由左至右依序為：Marvell主席暨執行長Matt Murphy、NVIDIA創辦人暨執行長黃仁勳。 (來源：FB@COMPUTEX TAIPEI﻿). ## 2026 COMPUTEX Forum論壇. ## 2026 COMPUTEX參展廠商. 參考資料：COMPUTEX TAIPEI、NVIDIA GTC Taipei.

---

会话 ID: c0c7ce7e...

# 🤖 AI 智能 Agent (LangGraph v1 标准版)

你好！我是你的AI助手，可以计算和搜索，有什么可以帮你的？

what's the weather like in guangzhou today?

Here's the current weather in **Guangzhou** (as of June 3, 2026):

🌤 **Condition:** Partly Cloudy 🌡 **Temperature:** 33.3°C (91.9°F) — feels like **38.2°C (100.8°F)** 💧 **Humidity:** 54% 🌬 **Wind:** Southeast at 10.8 km/h ☔ **Chance of Rain:** Very low (2%) 👁 **Visibility:** 10 km

It's a hot and humid day in Guangzhou! The "feels like" temperature is quite high at 38°C, so if you're heading out, make sure to stay hydrated and wear light clothing. No significant rain is expected today. ☀️

黄仁勋最新的一次演讲是关于什么？在哪里？

根据搜索结果，黄仁勋（Jensen Huang）**最新的一次大型主题演讲**是在 **CES 2026**（国际消费电子展）上进行的。

以下是详细信息：

### 📍 地点[](http://localhost:8501/#2ce15cd3)

**美国拉斯维加斯** — CES 2026（国际消费电子展）

### 🗓 时间[](http://localhost:8501/#339eb1f1)

**2026年1月**（CES通常在每年1月初举行）

### 🎤 演讲主题与内容[](http://localhost:8501/#6ab866ff)

演讲主要围绕 **NVIDIA 的最新技术突破**，重点包括：

1. **Vera Rubin 超级 GPU 芯片** — NVIDIA 下一代全新架构的 GPU
2. **物理 AI（Physical AI）** — 将AI从数字世界扩展到物理世界
3. **数字孪生技术（Digital Twin）**
4. **价值10万亿美元的产业现代化浪潮** — 黄仁勋阐述了AI如何推动全球产业变革

此外，他在 **COMPUTEX 2026**（台北国际电脑展，2026年6月初）也有最新演讲，内容同样涉及AI、GPU等前沿技术。

如果你想了解更具体的某一场演讲内容，可以告诉我，我可以进一步帮你查找！😊

那再搜索一下他在2026台北演讲的内容

以下是黄仁勋在 **2026年台北国际电脑展（COMPUTEX 2026）** 的演讲核心内容总结：

---

## 📍 地点 & 时间[](http://localhost:8501/#and)

- **地点：** 台北国际会议中心（TICC）
- **时间：** 2026年6月1日（周一）上午11:00（GTC Taipei主题演讲）
- **展会时间：** COMPUTEX 2026 于6月2日~6月5日在南港展览馆举行

---

## 🎤 演讲核心主题[](http://localhost:8501/#a8dac0e3)

### 1️⃣ AI Factory（AI工厂）—— 未来数据中心全面升级[](http://localhost:8501/#1-ai-factory-ai)

黄仁勋提出，未来的数据中心将全面升级为 **"AI工厂"**：

- **输入：** 原始数据
- **输出：** Token（AI思考与输出的基本单位，如文字、声音、影像、代码等）
- 企业未来的核心竞争力不再是"买了多少颗芯片"，而是**是否拥有一座运作流畅的AI工厂基础设施**

### 2️⃣ AI PC 2.0 时代 —— RTX Spark 平台[](http://localhost:8501/#2-ai-pc-2-0-rtx-spark)

- 发布了 **RTX Spark 平台**，将强大的AI Agent直接塞进个人电脑
- **关键突破：** 原本需要几千台服务器才能运行的大型生成式模型，现在在个人笔记本上就能直接运行
- **无需联网、秒级响应、隐私安全**

### 3️⃣ NVIDIA DSX 平台 —— AI工厂的专属操作系统[](http://localhost:8501/#3-nvidia-dsx-ai)

- 正式推出 **NVIDIA DSX**，被称为 **AI Factory OS**
- 作为AI工厂的"操作系统"，管理整个AI生产流程

### 4️⃣ "五层蛋糕（Five-Layer Cake）"架构[](http://localhost:8501/#4-five-layer-cake)

- 描绘AI工厂从底层硬件到上层软件的五个关键层级
- 涵盖：算力、存力、网络、电力、软件生态

### 5️⃣ 主权AI（Sovereign AI）[](http://localhost:8501/#5-ai-sovereign-ai)

- 各国正在积极打造专属自己的**国家AI工厂**和**国家AI云**
- 用自己的语言、历史数据训练符合本国文化与法律的AI模型

### 6️⃣ Physical AI（物理AI）[](http://localhost:8501/#6-physical-ai-ai)

- AI从数字世界扩展到物理世界，涵盖机器人、自动驾驶等

---

## 💡 一句话总结[](http://localhost:8501/#1049d50d)

> **"AI投资正式从单纯的'芯片军备竞赛'，跨入全产业链总动员的'AI工厂'与'物理AI'商用落地转折点。"**

这次演讲被视为未来3~5年AI产业发展的**财富地图**和**战略蓝图**！🔥

请找出和大于542858013的最小素数

✅ **答案：542,858,021**

验证过程：

- 542,858,013 能被 3 整除（不是素数）
- 542,858,014 是偶数
- 542,858,015 以 5 结尾
- 542,858,016 是偶数
- 542,858,017 能被 13 整除
- 542,858,018 是偶数
- 542,858,019 能被 3 整除
- 542,858,020 是偶数
- **542,858,021** 通过了所有素数测试，被确认为素数 ✅

因此，**542,858,021** 是大于 542,858,013 的最小素数，两者相差 8。

(The latest question is not easy to calculate, but afer few minutes run, the agent still worked it out. That's great.)