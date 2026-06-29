import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table
from rich.tree import Tree

from .react_agent import ReactAgent

console = Console()

def display_thinking_steps(steps):
    if not steps:
        console.print("[dim]（无思考过程）[/dim]")
        return
    
    console.print("\n[bold blue]🔍 思考过程[/bold blue]")
    console.print("-" * 60)
    
    for i, (thought, action, observation) in enumerate(steps, 1):
        console.print(f"\n[bold yellow]步骤 {i}:[/bold yellow]")
        
        console.print(f"[cyan]💡 Thought:[/cyan] {thought}")
        
        console.print(f"[green]🛠️ Action:[/green] {action}")
        
        if observation:
            console.print(f"[magenta]👀 Observation:[/magenta]")
            console.print(f"  {observation}")
    
    console.print("\n" + "-" * 60)

def main():
    load_dotenv()
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        console.print("[bold red]❌ 错误：[/bold red]未找到 DEEPSEEK_API_KEY 环境变量")
        console.print("[yellow]ℹ️ 请创建 .env 文件并添加 DEEPSEEK_API_KEY[/yellow]")
        sys.exit(1)
    
    working_dir = os.getcwd()
    
    console.print("\n" + "="*60)
    console.print("[bold green]🤖 AI Agent v0.1.0[/bold green]")
    console.print(f"[bold blue]📂 当前工作目录:[/bold blue] {working_dir}")
    console.print("="*60)
    console.print("[dim]提示：输入 'exit' 或 'quit' 退出[/dim]\n")
    
    try:
        agent = ReactAgent(working_dir=working_dir)
    except Exception as e:
        console.print(f"[bold red]❌ Agent 初始化失败:[/bold red] {str(e)}")
        sys.exit(1)
    
    while True:
        try:
            user_input = Prompt.ask("[bold cyan]你[/bold cyan]")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print("\n[bold green]👋 再见！[/bold green]")
                break
            
            if not user_input.strip():
                continue
            
            with console.status("[bold yellow]思考中...[/bold yellow]"):
                result = agent.run(user_input)
            
            thinking_steps = agent.get_thinking_steps()
            display_thinking_steps(thinking_steps)
            
            console.print(Panel(Markdown(result), title="🤖 AI 回复", border_style="blue"))
        
        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]⚠️ 已中断[/bold yellow]")
            break
        except EOFError:
            console.print("\n\n[bold green]👋 再见！[/bold green]")
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ 错误:[/bold red] {str(e)}")

if __name__ == "__main__":
    main()
