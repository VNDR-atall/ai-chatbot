from langchain_core.tools import tool
import os

MAX_FILE_SIZE = 10 * 1024 * 1024

def validate_path(filepath: str) -> tuple[bool, str]:
    if ".." in filepath:
        return False, "❌ 不允许使用相对路径 '..' 访问上级目录"
    if not os.path.abspath(filepath).startswith(os.path.abspath(os.getcwd())):
        return False, f"❌ 文件路径 '{filepath}' 超出工作目录范围"
    return True, ""

@tool
def list_files(path: str = ".") -> str:
    """列出指定目录的内容。
    
    参数:
        path: 目录路径，默认为当前目录
    """
    valid, msg = validate_path(path)
    if not valid:
        return msg
    
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"❌ 路径不存在: {path}"
        if not os.path.isdir(abs_path):
            return f"❌ '{path}' 不是目录"
        
        files = os.listdir(abs_path)
        files.sort()
        
        result = []
        for f in files:
            f_path = os.path.join(abs_path, f)
            if os.path.isdir(f_path):
                result.append(f"📁 {f}/")
            else:
                size = os.path.getsize(f_path)
                result.append(f"📄 {f} ({size} bytes)")
        
        return "\n".join(result) if result else "📭 目录为空"
    
    except PermissionError:
        return f"❌ 权限不足，无法访问目录 '{path}'"
    except Exception as e:
        return f"❌ 列出目录失败: {str(e)}"

@tool
def read_file(filepath: str) -> str:
    """读取文件内容。
    
    参数:
        filepath: 文件路径
    """
    valid, msg = validate_path(filepath)
    if not valid:
        return msg
    
    try:
        abs_path = os.path.abspath(filepath)
        if not os.path.exists(abs_path):
            return f"❌ 文件不存在: {filepath}"
        if not os.path.isfile(abs_path):
            return f"❌ '{filepath}' 不是文件"
        
        size = os.path.getsize(abs_path)
        if size > MAX_FILE_SIZE:
            return f"❌ 文件过大（{size} bytes），最大允许 {MAX_FILE_SIZE} bytes"
        
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        return content
    
    except PermissionError:
        return f"❌ 权限不足，无法读取文件 '{filepath}'"
    except Exception as e:
        return f"❌ 读取文件失败: {str(e)}"

@tool
def write_file(filepath: str, content: str) -> str:
    """写入文件内容（覆盖）。
    
    参数:
        filepath: 文件路径
        content: 要写入的内容
    """
    valid, msg = validate_path(filepath)
    if not valid:
        return msg
    
    try:
        abs_path = os.path.abspath(filepath)
        directory = os.path.dirname(abs_path)
        
        if not os.path.exists(directory):
            return f"❌ 目录不存在: {directory}"
        
        if os.path.exists(abs_path):
            return f"⚠️ 文件已存在，需要用户确认是否覆盖: {filepath}"
        
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return f"✅ 文件写入成功: {filepath}"
    
    except PermissionError:
        return f"❌ 权限不足，无法写入文件 '{filepath}'"
    except Exception as e:
        return f"❌ 写入文件失败: {str(e)}"

@tool
def append_file(filepath: str, content: str) -> str:
    """追加内容到文件。
    
    参数:
        filepath: 文件路径
        content: 要追加的内容
    """
    valid, msg = validate_path(filepath)
    if not valid:
        return msg
    
    try:
        abs_path = os.path.abspath(filepath)
        if not os.path.exists(abs_path):
            return f"❌ 文件不存在: {filepath}"
        if not os.path.isfile(abs_path):
            return f"❌ '{filepath}' 不是文件"
        
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write(content)
        
        return f"✅ 内容追加成功: {filepath}"
    
    except PermissionError:
        return f"❌ 权限不足，无法追加文件 '{filepath}'"
    except Exception as e:
        return f"❌ 追加文件失败: {str(e)}"

@tool
def create_directory(path: str) -> str:
    """创建目录。
    
    参数:
        path: 要创建的目录路径
    """
    valid, msg = validate_path(path)
    if not valid:
        return msg
    
    try:
        abs_path = os.path.abspath(path)
        
        if os.path.exists(abs_path):
            if os.path.isdir(abs_path):
                return f"ℹ️ 目录已存在: {path}"
            else:
                return f"❌ 路径已存在且不是目录: {path}"
        
        os.makedirs(abs_path, exist_ok=True)
        return f"✅ 目录创建成功: {path}"
    
    except PermissionError:
        return f"❌ 权限不足，无法创建目录 '{path}'"
    except Exception as e:
        return f"❌ 创建目录失败: {str(e)}"
