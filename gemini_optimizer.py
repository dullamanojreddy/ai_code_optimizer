import os
import ast
import time
import timeit
import mccabe
from google import genai
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- RICH IMPORTS ---
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

# Initialize Rich Console
console = Console()

# 🔑 API KEY ROTATION LIST (5 Unique Projects)
API_KEYS = [
    "AIzaSyBvstVAFinCqbZsvpTnggG8uavVd6o0dos",
    "AIzaSyAif6OUvOaV7q3A7Vk2cPJKOewbtfJzqTM",
    "AIzaSyDX3JmFKtd0At5ij1NkuVbHmwFh76igqaI",
    "AIzaSyCjgId1MQyrqh1f-Yp7z0JrEQ4AX8ygru4",
    "AIzaSyBmnDIVyrtaf1JGPyV-v8cMrxmR3W3Kykg"
]

class KeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.current_index = 0
        self.total_tokens_session = 0
        self.client = genai.Client(api_key=self.keys[self.current_index])

    def rotate_key(self):
        """Switches to the next available API key in the list"""
        if self.current_index < len(self.keys) - 1:
            self.current_index += 1
            self.client = genai.Client(api_key=self.keys[self.current_index])
            console.print(f"\n[bold magenta]🔄 Quota limit reached. Switching to Key #{self.current_index + 1}...[/bold magenta]")
            return True
        return False

# Initialize the manager
key_manager = KeyManager(API_KEYS)

class PDFReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "AI Code Optimization & Performance Report", 
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(10)

def get_complexity(code):
    try:
        tree = ast.parse(code)
        visitor = mccabe.PathGraphingAstVisitor()
        visitor.preorder(tree, visitor)
        complexities = [graph.complexity() for graph in visitor.graphs.values()]
        return max(complexities) if complexities else 1
    except: return 1

def print_rich_comparison(original, optimized, filename):
    table = Table(title=f"Comparison: {filename}", show_header=True, header_style="bold magenta")
    table.add_column("ORIGINAL CODE", style="dim")
    table.add_column("OPTIMIZED CODE", style="bold green")
    orig_syntax = Syntax(original, "python", theme="monokai", line_numbers=True)
    opt_syntax = Syntax(optimized, "python", theme="monokai", line_numbers=True)
    table.add_row(orig_syntax, opt_syntax)
    console.print(table)

def run_full_process():
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    
    # Header Setup
    pdf.cell(50, 10, "File Name", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
    pdf.cell(45, 10, "Complexity (O/N)", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
    pdf.cell(45, 10, "Speedup", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
    pdf.cell(50, 10, "Status", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', fill=True)

    if not os.path.exists("optimized_files"): os.makedirs("optimized_files")
    files = [f for f in os.listdir() if f.endswith('.py') and f.startswith('test')]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        
        overall_task = progress.add_task("[yellow]Optimizing project...", total=len(files))

        for filename in files:
            progress.update(overall_task, description=f"[cyan]Processing {filename}...")
            
            with open(filename, "r", encoding="utf-8") as f:
                old_code = f.read()

            success = False
            while not success:
                try:
                    response = key_manager.client.models.generate_content(
                        model="gemini-3-flash-preview", 
                        contents=f"Optimize this Python code. Return ONLY code:\n\n{old_code}"
                    )
                    usage = response.usage_metadata
                    key_manager.total_tokens_session += usage.total_token_count
                    
                    console.print(Panel(
                        f"File: {filename} | Used Key #{key_manager.current_index + 1}\n"
                        f"Tokens: {usage.total_token_count} (Session Total: {key_manager.total_tokens_session})",
                        title="API Usage Metadata", expand=False, style="blue"
                    ))
                    
                    new_code = response.text.replace("```python", "").replace("```", "").strip()
                    print_rich_comparison(old_code, new_code, filename)
                    
                    # Benchmarking
                    c_old, c_new = get_complexity(old_code), get_complexity(new_code)
                    t_old = timeit.timeit(lambda: exec(old_code, {}), number=10)
                    t_new = timeit.timeit(lambda: exec(new_code, {}), number=10)
                    gain = t_old / t_new if t_new > 0 else 1

                    # PDF Log
                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(50, 10, filename, 1, new_x=XPos.RIGHT)
                    pdf.cell(45, 10, f"{c_old} -> {c_new}", 1, new_x=XPos.RIGHT, align='C')
                    pdf.cell(45, 10, f"{gain:.1f}x", 1, new_x=XPos.RIGHT, align='C')
                    pdf.cell(50, 10, "SUCCESS", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

                    with open(f"optimized_files/opt_{filename}", "w", encoding="utf-8") as f:
                        f.write(new_code)
                    
                    success = True

                except Exception as e:
                    if "429" in str(e):
                        if not key_manager.rotate_key():
                            console.print("[bold red]❌ All 5 API keys exhausted for today![/bold red]")
                            pdf.cell(190, 10, f"FAILED: {filename} (Quota Exhausted)", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                            success = True 
                    else:
                        console.print(f"[bold red]❌ Error in {filename}: {e}[/bold red]")
                        success = True

            progress.advance(overall_task)
            time.sleep(2)

    pdf.output("Optimization_Report.pdf")
    console.print(f"\n[bold gold1]🎉 Batch complete! Total Session Tokens: {key_manager.total_tokens_session}[/bold gold1]")

if __name__ == "__main__":
    run_full_process()