import yaml
from pathlib import Path
from typing import Dict, Any

def load_prompts(module_name: str) -> Dict[str, Any]:
    """
    Load prompts from a YAML file in the src/prompts directory.
    """
    # Assuming this file is in src/utils/
    base_path = Path(__file__).parent.parent / "prompts"
    file_path = base_path / f"{module_name}.yaml"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
