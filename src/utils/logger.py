import os
import json
import logging
from datetime import datetime
from typing import Optional, List
from src.core.config import config

# Ensure output directory exists for log file
os.makedirs(config.logs_dir, exist_ok=True)

# Standard logging setup
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(config.logs_dir, "app.log"))
    ]
)

logger = logging.getLogger("AI-Narrated-Recap")

class OperationLogger:
    def __init__(self):
        self.log_path = os.path.join(config.logs_dir, "operation_history.jsonl")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_operation(self, project_id: str, action: str, output_files: List[str], details: Optional[str] = None):
        """
        Log a major operation to the history file.
        
        Args:
            project_id: The project ID (e.g. PROJ_001)
            action: Description of the action (e.g. "Ingest Novel", "Generate Script")
            output_files: List of file paths generated (should be absolute or relative to workspace root)
            details: Optional extra details
        """
        # Ensure paths are absolute for traceability
        abs_output_files = [os.path.abspath(p) for p in output_files]
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "project_id": project_id,
            "action": action,
            "output_files": abs_output_files,
            "details": details
        }
        
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
            logger.info(f"Operation logged: [{project_id}] {action} -> {len(output_files)} files")
        except Exception as e:
            logger.error(f"Failed to write operation log: {e}")

op_logger = OperationLogger()
