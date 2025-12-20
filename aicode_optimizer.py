import os
import time
import timeit
import ast
import mccabe
from google import genai
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console(width=120)

API_KEYS = [
    "API_KEY1",
    "API_KEY2",
    "API_KEY3",
    "API_KEY4"
]

class KeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.idx = 0
        self.total_tokens = 0
        self.keys_used = set()
        self.client = genai.Client(api_key=self.keys[self.idx])

    def rotate(self):
        if self.idx < len(self.keys) - 1:
            self.idx += 1
            self.client = genai.Client(api_key=self.keys[self.idx])
            console.print(f"[yellow]🔄 Switched to API Key {self.idx + 1}[/yellow]")
            return True
        return False

key_manager = KeyManager(API_KEYS)

os.makedirs("reports", exist_ok=True)
os.makedirs("optimized_files", exist_ok=True)

class PDFReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(
            0, 10,
            "AI Code Optimization Report",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="C"
        )
        self.ln(5)

def sanitize_llm_code(text):
    lines = [l for l in text.splitlines() if not l.strip().startswith("```")]
    if lines and lines[0].strip().lower() in ("python", "c", "c++", "java"):
        lines = lines[1:]
    return "\n".join(lines).strip()

def cyclomatic_complexity(code):
    try:
        tree = ast.parse(code)
        visitor = mccabe.PathGraphingAstVisitor()
        visitor.preorder(tree, visitor)
        return max((g.complexity() for g in visitor.graphs.values()), default=1)
    except:
        return "-"

def safe_exec_time(code):
    try:
        return timeit.timeit(lambda: exec(code, {}), number=3)
    except:
        return "-"

def fix_java_class_name(code, filename):
    class_name = os.path.splitext(filename)[0]
    import re
    code = re.sub(r'public\s+class\s+\w+', f'public class {class_name}', code)
    return code

def print_comparison(old, new, fname, lang="python"):
    table = Table(
        title=f"Comparison: {fname}",
        show_header=True,
        header_style="bold magenta",
        width=110
    )
    table.add_column("ORIGINAL", ratio=1)
    table.add_column("OPTIMIZED", ratio=1)

    if lang.lower() == "python":
        table.add_row(
            Syntax(old, "python", line_numbers=True, word_wrap=True),
            Syntax(new, "python", line_numbers=True, word_wrap=True)
        )
    else:
        table.add_row(old, new)

    console.print(table)

def run():
    SKIP_FILES = [os.path.basename(__file__)]
    files = sorted(
        f for f in os.listdir()
        if f.endswith((".py", ".c", ".cpp", ".java")) and f not in SKIP_FILES
    )

    optimized_count = 0
    skipped_count = 0
    processed_files = 0
    pdf_created = False
    pdf = PDFReport()

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:

        task = progress.add_task("Optimizing source files...", total=len(files))

        for fname in files:
            processed_files += 1
            progress.update(task, description=f"{fname}")

            if fname.endswith(".java"):
                opt_path = f"optimized_files/{fname}"
            else:
                opt_path = f"optimized_files/opt_{fname}"

            if os.path.exists(opt_path):
                skipped_count += 1
                console.print(
                    Panel(
                        f"{fname} already optimized\nKey Used: NONE\nTokens: 0",
                        title="SKIPPED",
                        style="green"
                    )
                )
                progress.advance(task)
                continue

            with open(fname, "r", encoding="utf-8") as f:
                old_code = f.read()

            lang = (
                "python" if fname.endswith(".py")
                else "c" if fname.endswith(".c")
                else "cpp" if fname.endswith(".cpp")
                else "java"
            )

            while True:
                try:
                    prompt = f"Optimize this {lang.upper()} code professionally. Return ONLY code:\n\n{old_code}"
                    response = key_manager.client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=prompt
                    )

                    tokens = response.usage_metadata.total_token_count
                    key_manager.total_tokens += tokens
                    key_manager.keys_used.add(key_manager.idx + 1)

                    new_code = sanitize_llm_code(response.text)

                    if lang == "java":
                        new_code = fix_java_class_name(new_code, fname)

                    print_comparison(old_code, new_code, fname, lang)

                    c_old = cyclomatic_complexity(old_code) if lang == "python" else "-"
                    c_new = cyclomatic_complexity(new_code) if lang == "python" else "-"
                    t_old = safe_exec_time(old_code) if lang == "python" else "-"
                    t_new = safe_exec_time(new_code) if lang == "python" else "-"
                    speedup = round(t_old / t_new, 2) if t_old != "-" and t_new != "-" else "-"

                    with open(opt_path, "w", encoding="utf-8") as f:
                        f.write(new_code)

                    if not pdf_created:
                        pdf.add_page()
                        pdf.set_font("Helvetica", "B", 10)
                        pdf.cell(40, 10, "File", 1)
                        pdf.cell(40, 10, "Complexity", 1)
                        pdf.cell(40, 10, "Speedup", 1)
                        pdf.cell(40, 10, "Status", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                        pdf_created = True

                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(40, 10, fname, 1)
                    pdf.cell(40, 10, f"{c_old}->{c_new}", 1)
                    pdf.cell(40, 10, f"{speedup}x", 1)
                    pdf.cell(40, 10, "SUCCESS", 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                    optimized_count += 1

                    console.print(
                        Panel(
                            f"File: {fname}\n"
                            f"API Key Used: {key_manager.idx + 1}\n"
                            f"Tokens Used: {tokens}\n"
                            f"Total Tokens: {key_manager.total_tokens}",
                            title="OPTIMIZATION METRICS",
                            style="blue"
                        )
                    )
                    break

                except Exception as e:
                    if "429" in str(e) and key_manager.rotate():
                        continue
                    console.print(f"[red]❌ Error processing {fname}: {e}[/red]")
                    break

            progress.advance(task)
            time.sleep(0.1)

    if pdf_created:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        pdf_file = f"reports/Optimization_Report_{timestamp}.pdf"
        pdf.output(pdf_file)
        report_msg = f"Saved PDF: {pdf_file}"
    else:
        report_msg = "No files optimized → PDF report not generated"

    console.print(
        Panel(
            f"Files Processed: {processed_files}\n"
            f"Optimized: {optimized_count}\n"
            f"Skipped: {skipped_count}\n"
            f"Keys Used: {sorted(key_manager.keys_used) if key_manager.keys_used else 'NONE'}\n"
            f"Total Tokens Used: {key_manager.total_tokens}\n\n"
            f"{report_msg}",
            title="SESSION SUMMARY",
            style="bold green"
        )
    )

if __name__ == "__main__":
    run()
