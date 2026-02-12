import ast
import os
import sys
import re
from pathlib import Path
from typing import List, Set, Dict

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"

# Configuration
MAX_FILE_LINES_WARNING = 800
MAX_FILE_LINES_ERROR = 1000

def get_defined_classes(directory: Path) -> Set[str]:
    """Extracts all class names defined in python files within a directory."""
    classes = set()
    if not directory.exists():
        return classes
        
    for file_path in directory.rglob("*.py"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes.add(node.name)
        except Exception:
            pass
    return classes

def check_file_size(file_path: Path) -> List[str]:
    """Checks if file size exceeds limits."""
    errors = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            line_count = len(lines)
            
        if line_count > MAX_FILE_LINES_ERROR:
            errors.append(f"{RED}[ERROR] File too large: {line_count} lines (Limit: {MAX_FILE_LINES_ERROR}){RESET}")
        elif line_count > MAX_FILE_LINES_WARNING:
            errors.append(f"{YELLOW}[WARN] File growing too large: {line_count} lines (Limit: {MAX_FILE_LINES_WARNING}){RESET}")
    except Exception:
        pass
    return errors

def check_documentation_coverage() -> List[str]:
    """Checks if tools and workflows have corresponding documentation."""
    errors = []
    
    # 1. Check Tools
    tools_dir = SRC_DIR / "tools"
    docs_tools_dir = DOCS_DIR / "tools"
    if tools_dir.exists():
        for file_path in tools_dir.glob("*.py"):
            if file_path.name == "__init__.py": continue
            
            # Expected doc file: docs/tools/{filename}.md
            doc_name = file_path.stem + ".md"
            doc_path = docs_tools_dir / doc_name
            
            if not doc_path.exists():
                errors.append(f"{YELLOW}[WARN] Missing documentation for tool: {file_path.name} -> docs/tools/{doc_name}{RESET}")

    # 2. Check Workflows
    workflows_dir = SRC_DIR / "workflows"
    docs_workflows_dir = DOCS_DIR / "workflows"
    if workflows_dir.exists():
        for file_path in workflows_dir.glob("*.py"):
            if file_path.name == "__init__.py": continue
            
            # Expected doc file: docs/workflows/{filename}.md
            doc_name = file_path.stem + ".md"
            doc_path = docs_workflows_dir / doc_name
            
            if not doc_path.exists():
                errors.append(f"{YELLOW}[WARN] Missing documentation for workflow: {file_path.name} -> docs/workflows/{doc_name}{RESET}")
                
    return errors

def check_directory_structure() -> List[str]:
    """Checks for forbidden directories and files."""
    errors = []
    
    # 1. Check for empty directories in docs/tools
    docs_tools_dir = DOCS_DIR / "tools"
    if docs_tools_dir.exists():
        for item in docs_tools_dir.iterdir():
            if item.is_dir():
                # Check if empty
                if not any(item.iterdir()):
                     errors.append(f"{YELLOW}[WARN] Empty directory found: {item.relative_to(PROJECT_ROOT)}{RESET}")
                elif item.name.startswith("phase"):
                     errors.append(f"{YELLOW}[WARN] Deprecated directory structure found: {item.relative_to(PROJECT_ROOT)}{RESET}")

    # 2. Check for backup files
    for file_path in SRC_DIR.rglob("*.backup"):
        errors.append(f"{RED}[ERROR] Backup file found: {file_path.relative_to(PROJECT_ROOT)}{RESET}")
        
    return errors

def check_architecture_integrity() -> List[str]:
    """Checks if logic_flows.md exists."""
    errors = []
    logic_docs = DOCS_DIR / "architecture" / "logic_flows.md"
    
    if not logic_docs.exists():
        return [f"{RED}[ERROR] Missing logic_flows.md{RESET}"]
    return []

def validate_standards():
    print(f"{YELLOW}Starting Enhanced Project Standards Validation...{RESET}")
    all_passed = True
    
    # 1. Architecture Integrity
    print(f"\n{YELLOW}Checking Architecture Integrity...{RESET}")
    arch_errors = check_architecture_integrity()
    if arch_errors:
        all_passed = False
        for err in arch_errors:
            print(err)
    else:
        print(f"{GREEN}[PASS] Architecture documentation exists.{RESET}")

    # 2. Documentation Coverage
    print(f"\n{YELLOW}Checking Documentation Coverage...{RESET}")
    doc_errors = check_documentation_coverage()
    if doc_errors:
        # Warnings don't necessarily fail the build, but we print them
        for err in doc_errors:
            print(err)
    else:
        print(f"{GREEN}[PASS] All tools and workflows are documented.{RESET}")

    # 3. Directory Structure
    print(f"\n{YELLOW}Checking Directory Structure...{RESET}")
    dir_errors = check_directory_structure()
    if dir_errors:
        all_passed = False
        for err in dir_errors:
            print(err)
    else:
        print(f"{GREEN}[PASS] Directory structure is clean.{RESET}")

    # 4. Code Scans (File Size & Hygiene)
    print(f"\n{YELLOW}Scanning Codebase...{RESET}")
    files_to_check = list(SRC_DIR.rglob("*.py"))
    
    for file_path in files_to_check:
        if not file_path.exists(): continue
        if file_path.name == "__init__.py": continue
        
        rel_path = file_path.relative_to(PROJECT_ROOT)
        file_errors = []
        
        # Check File Size
        file_errors.extend(check_file_size(file_path))
        
        # Print errors for this file
        if file_errors:
            # If any error is RED, fail the build
            if any(RED in e for e in file_errors):
                all_passed = False
            
            print(f"{rel_path}:")
            for err in file_errors:
                print(f"  - {err}")

    if all_passed:
        print(f"\n{GREEN}[PASS] System is healthy.{RESET}")
    else:
        print(f"\n{RED}[FAIL] Please fix the violations above.{RESET}")

if __name__ == "__main__":
    validate_standards()
