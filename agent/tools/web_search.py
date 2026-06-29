from langchain_core.tools import tool

UNWANTED_KEYWORDS = [
    '星座', '运势', '算命', '塔罗', '占星', '生肖', '八字', '风水',
    '广告', '推广', '促销', '优惠', '打折', '团购',
    '色情', '赌博', '博彩',
    '免责声明', '版权声明', '隐私政策', '使用条款',
]

def filter_content(text: str) -> str:
    lines = text.split('\n')
    filtered_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(keyword in line for keyword in UNWANTED_KEYWORDS):
            continue
        if len(line) < 5:
            continue
        filtered_lines.append(line)
    return '\n'.join(filtered_lines)

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
            search_depth="advanced",
        )
        result = search_tool.invoke({"query": query})
        
        if hasattr(result, 'get'):
            answer_part = result.get('answer', '')
            answer_text = f"{answer_part}\n\n" if answer_part else ""
            
            results_list = result.get('results', [])
            if not results_list and not answer_part:
                return "未找到相关结果。"
            
            web_results = []
            for r in results_list:
                title = r.get('title', '无标题')
                content = r.get('content', '无内容')
                
                if any(keyword in title for keyword in UNWANTED_KEYWORDS):
                    continue
                
                content = filter_content(content)
                if not content:
                    continue
                
                web_results.append(f"【{title}】\n{content}")
            
            if not web_results and answer_part:
                return answer_text.strip()
            elif not web_results:
                return "未找到相关结果。"
            
            return f"{answer_text}{'\n\n'.join(web_results)}".strip()
        return str(result)
    except ImportError:
        return "❌ 未安装 langchain-tavily，请运行 'pip install langchain-tavily' 安装"
    except Exception as e:
        return f"搜索服务调用失败: {str(e)}。请检查网络或稍后重试。"