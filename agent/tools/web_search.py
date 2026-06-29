from langchain_core.tools import tool

@tool
def web_search(query: str) -> str:
    """搜索互联网获取最新信息。
    
    参数:
        query: 查询关键词，建议包含日期（例如 '广州天气 2026-06-02'）
    
    返回:
        搜索结果摘要，包含AI生成答案和相关网页摘要
    """
    try:
        from langchain_tavily import TavilySearch
        
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
    except ImportError:
        return "❌ 未安装 langchain-tavily，请运行 'pip install langchain-tavily' 安装"
    except Exception as e:
        return f"搜索服务调用失败: {str(e)}。请检查网络或稍后重试。"
