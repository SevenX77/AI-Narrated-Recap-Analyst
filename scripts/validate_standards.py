import ast
import os
import sys
import re
from pathlib import Path
from typing import List, Set

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"

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

def check_architecture_integrity() -> List[str]:
    """Checks if components defined in logic_flows.md exist in code."""
    errors = []
    logic_docs = DOCS_DIR / "architecture" / "logic_flows.md"
    
    if not logic_docs.exists():
        return ["Missing logic_flows.md"]
        
    with open(logic_docs, "r", encoding="utf-8") as f:
        doc_content = f.read()
        
    # Extract expected components using regex (looking for `src.xxx.ClassName`)
    # Pattern: `src.agents.analyst.AnalystAgent` or just `AnalystAgent` mentioned in context
    # Simplified: Look for ClassNames mentioned in "Agent Responsibilities" or "Workflows"
    
    # 1. Check Workflows
    # We expect IngestionWorkflow, TrainingWorkflow in src/workflows
    workflow_classes = get_defined_classes(SRC_DIR / "workflows")
    required_workflows = ["IngestionWorkflow", "TrainingWorkflow"]
    
    for wf in required_workflows:
        if wf not in workflow_classes:
            # Check if it's mentioned in docs first (to be fair)
            if wf in doc_content:
                errors.append(f"Missing Workflow implementation: {wf} (defined in docs, missing in src/workflows)")

    # 2. Check Modules/Engines
    # We expect AlignmentEngine/DeepSeekAlignmentEngine
    module_classes = get_defined_classes(SRC_DIR / "modules")
    if "DeepSeekAlignmentEngine" in doc_content and "DeepSeekAlignmentEngine" not in module_classes:
         errors.append("Missing Module implementation: DeepSeekAlignmentEngine")

    return errors

def check_core_mechanisms(file_path: Path) -> List[str]:
    """Checks if core business files use logging and artifact management."""
    errors = []
    # Only check workflows and main.py
    if "workflows" not in str(file_path) and "main.py" not in str(file_path):
        return errors
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Check for Operation Logger
        if "op_logger.log_operation" not in content:
             errors.append(f"Line 0: Core business file must log operations using 'op_logger.log_operation'")
             
        # Check for Artifact Manager (except Ingestion which might just save, but usually yes)
        # We relax this for main.py if it's just a CLI entry, but run_production_pipeline should have it.
        if "artifact_manager.save_artifact" not in content and "save_artifact" not in content:
             # Might be using a wrapper, but warn
             errors.append(f"Line 0: Core business file should save results using 'artifact_manager.save_artifact'")
             
    except Exception:
        pass
    return errors

def check_path_hygiene(file_path: Path) -> List[str]:
    """Checks for hardcoded output/data paths."""
    errors = []
    # Skip config and logger
    if "config.py" in str(file_path) or "logger.py" in str(file_path):
        return errors
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value
                # Check for "output/" or "data/" at start of string or in path join
                if (val.startswith("output/") or val.startswith("data/")) and "operation_history" not in val:
                    errors.append(f"Line {node.lineno}: Found hardcoded path '{val}'. Use config.logs_dir or config.data_dir.")
    except Exception:
        pass
    return errors

def check_module_boundaries(file_path: Path) -> List[str]:
    """Checks for forbidden dependencies."""
    errors = []
    
    # Rule: Analyst cannot import Script schemas
    if "agents/analyst.py" in str(file_path) or "agents/deepseek_analyst.py" in str(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and "schemas_writer" in node.module:
                        errors.append(f"Line {node.lineno}: Analyst forbidden from importing 'schemas_writer'. Violation of Separation of Concerns.")
        except Exception:
            pass
            
    return errors

def validate_standards():
    print(f"{YELLOW}Starting Enhanced Project Standards Validation...{RESET}")
    all_passed = True
    
    # 1. Architecture Integrity
    print(f"{YELLOW}Checking Architecture Integrity...{RESET}")
    arch_errors = check_architecture_integrity()
    if arch_errors:
        all_passed = False
        for err in arch_errors:
            print(f"{RED}[FAIL] {err}{RESET}")
    else:
        print(f"{GREEN}[PASS] Architecture matches documentation.{RESET}")

    # 2. Code Scans
    print(f"{YELLOW}Scanning Codebase...{RESET}")
    files_to_check = list(SRC_DIR.rglob("*.py")) + [PROJECT_ROOT / "main.py"]
    
    for file_path in files_to_check:
        if not file_path.exists(): continue
        if file_path.name == "__init__.py": continue
        
        rel_path = file_path.relative_to(PROJECT_ROOT)
        file_errors = []
        
        # Standard Checks
        file_errors.extend(check_path_hygiene(file_path))
        file_errors.extend(check_module_boundaries(file_path))
        file_errors.extend(check_core_mechanisms(file_path))
        
        # Print errors
        if file_errors:
            all_passed = False
            print(f"\n{RED}[FAIL] {rel_path}:{RESET}")
            for err in file_errors:
                print(f"  - {err}")

    if all_passed:
        print(f"\n{GREEN}[PASS] All checks passed. System is healthy.{RESET}")
    else:
        print(f"\n{YELLOW}Please fix the violations above.{RESET}")

if __name__ == "__main__":
    validate_standards()
