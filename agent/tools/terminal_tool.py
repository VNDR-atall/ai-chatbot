from langchain_core.tools import tool
import subprocess
import os

DANGEROUS_COMMANDS = ["rm", "rmdir", "mv", "chmod", "git reset", "git clean"]
COMMAND_TIMEOUT = 30

def is_dangerous_command(command: str) -> bool:
    return any(dangerous in command.lower() for dangerous in DANGEROUS_COMMANDS)

def check_path_sandbox(cwd: str, working_dir: str) -> bool:
    abs_cwd = os.path.abspath(cwd)
    abs_working_dir = os.path.abspath(working_dir)
    return abs_cwd.startswith(abs_working_dir)

@tool
def terminal(command: str, cwd: str = ".") -> str:
    """在指定目录下执行终端命令。
    
    参数:
        command: 要执行的shell命令（如 'ls -la'）
        cwd: 执行命令的工作目录，默认为当前目录
    """
    if not command.strip():
        return "❌ 命令不能为空"
    
    if ".." in cwd:
        return "❌ 不允许使用相对路径 '..' 访问上级目录"
    
    working_dir = os.getcwd()
    
    if not check_path_sandbox(cwd, working_dir):
        return f"❌ 工作目录 '{cwd}' 超出允许范围（当前工作目录: {working_dir}）"
    
    dangerous = is_dangerous_command(command)
    
    if dangerous:
        return f"⚠️ 危险操作确认：{command}\n请在CLI中确认是否继续执行"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT
        )
        
        output_lines = []
        if result.stdout:
            output_lines.append("stdout:")
            output_lines.append(result.stdout.strip())
        if result.stderr:
            output_lines.append("\nstderr:")
            output_lines.append(result.stderr.strip())
        output_lines.append(f"\n退出码: {result.returncode}")
        
        return "\n".join(output_lines)
    
    except subprocess.TimeoutExpired:
        return f"⏱️ 命令 '{command}' 执行超时（{COMMAND_TIMEOUT}秒）"
    except FileNotFoundError:
        return f"❌ 命令 '{command.split()[0]}' 未找到"
    except PermissionError:
        return f"❌ 权限不足，无法执行命令 '{command}'"
    except Exception as e:
        return f"❌ 执行出错: {str(e)}"
