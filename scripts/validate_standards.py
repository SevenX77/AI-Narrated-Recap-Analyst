import ast
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"

def check_file_standards(file_path: Path) -> List[str]:
    errors = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
    except Exception as e:
        return [f"Could not parse file: {e}"]

    # 1. Check for print statements
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            errors.append(f"Line {node.lineno}: Found 'print()' statement. Use 'logging' instead.")

    # 2. Check for hardcoded long strings (potential prompts) in Agents
    if "agents" in str(file_path):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str) and len(node.value.value) > 100:
                    # Ignore docstrings (which are usually Expr, not Assign, but let's be safe)
                    errors.append(f"Line {node.lineno}: Found long string literal (>100 chars). Check if this is a hardcoded prompt.")

    # 3. Check imports
    # (Simple check: ensure we are not importing from 'src.agents' inside 'src.tools' - circular dependency prevention)
    if "tools" in str(file_path):
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "src.agents" in node.module:
                errors.append(f"Line {node.lineno}: Tool importing from Agent. Tools should be independent.")

    return errors

def check_documentation_sync():
    print(f"{YELLOW}Checking Documentation Sync...{RESET}")
    
    logic_docs = DOCS_DIR / "architecture" / "logic_flows.md"
    if not logic_docs.exists():
        print(f"{RED}[FAIL] Missing critical documentation: {logic_docs}{RESET}")
        return False

    # Check if core logic files are newer than documentation
    # We check src/workflows and src/agents
    critical_dirs = [SRC_DIR / "workflows", SRC_DIR / "agents"]
    doc_mtime = logic_docs.stat().st_mtime
    
    out_of_sync_files = []
    
    for d in critical_dirs:
        if not d.exists(): continue
        for f in d.rglob("*.py"):
            if f.name == "__init__.py": continue
            if f.stat().st_mtime > doc_mtime:
                # Allow a small buffer (e.g., 1 minute) to avoid false positives during rapid editing
                if f.stat().st_mtime - doc_mtime > 60:
                    out_of_sync_files.append(f)

    if out_of_sync_files:
        print(f"{RED}[FAIL] Documentation might be out of sync! The following files are newer than {logic_docs.name}:{RESET}")
        for f in out_of_sync_files:
            print(f"  - {f.relative_to(PROJECT_ROOT)}")
        print(f"{YELLOW}Action Required: Review {logic_docs.name} and update if necessary. Then `touch` the file to update timestamp.{RESET}")
        return False
    else:
        print(f"{GREEN}[PASS] Documentation seems up to date.{RESET}")
        return True

def validate_structure():
    print(f"{YELLOW}Starting Project Standards Validation...{RESET}")
    
    # 0. Check Documentation Sync (Highest Priority)
    doc_sync_pass = check_documentation_sync()

    # 1. Check Directory Structure
    required_dirs = [
        SRC_DIR / "core",
        SRC_DIR / "tools",
        SRC_DIR / "agents",
        SRC_DIR / "workflows",
        SRC_DIR / "prompts",
        PROJECT_ROOT / "docs" / "architecture"
    ]
    
    all_dirs_exist = True
    for d in required_dirs:
        if not d.exists():
            print(f"{RED}[FAIL] Missing directory: {d}{RESET}")
            all_dirs_exist = False
    
    if all_dirs_exist:
        print(f"{GREEN}[PASS] Directory structure valid.{RESET}")

    # 2. Check Code Standards
    files_to_check = list(SRC_DIR.rglob("*.py"))
    issues_found = False
    
    for file_path in files_to_check:
        # Skip __init__.py and this script
        if file_path.name == "__init__.py" or "validate_standards.py" in str(file_path):
            continue
            
        rel_path = file_path.relative_to(PROJECT_ROOT)
        errors = check_file_standards(file_path)
        
        if errors:
            issues_found = True
            print(f"\n{RED}[FAIL] {rel_path}:{RESET}")
            for err in errors:
                print(f"  - {err}")
    
    if not issues_found and doc_sync_pass:
        print(f"\n{GREEN}[PASS] All checks passed. Codebase is healthy.{RESET}")
    else:
        print(f"\n{YELLOW}Please fix the violations above.{RESET}")

if __name__ == "__main__":
    validate_structure()
