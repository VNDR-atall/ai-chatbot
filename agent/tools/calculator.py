from langchain_core.tools import tool
import numexpr

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。
    
    参数:
        expression: 纯数学表达式（例如 3+4*2、sin(3.14)、sqrt(16)）
    
    返回:
        计算结果字符串
    """
    try:
        result = numexpr.evaluate(expression).item()
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算出错：{str(e)}"
