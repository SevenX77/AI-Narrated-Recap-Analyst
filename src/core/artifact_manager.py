import os
import json
import shutil
from datetime import datetime
from typing import Any, Optional
from src.utils.logger import logger

class ArtifactManager:
    """
    Manages versioned data artifacts (Analysis, Alignment, etc.)
    Strategy: "Latest Pointer + Timestamped Versions"
    """
    
    @staticmethod
    def save_artifact(content: Any, artifact_type: str, project_id: str, base_dir: str, extension: str = "json") -> str:
        """
        Save an artifact with versioning.
        
        Args:
            content: The data to save (dict/list for JSON, str for text)
            artifact_type: Name prefix (e.g. "novel_events", "alignment_map")
            project_id: Project ID
            base_dir: Directory to save in
            extension: File extension
            
        Returns:
            Path to the saved versioned file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_filename = f"{artifact_type}_v{timestamp}.{extension}"
        latest_filename = f"{artifact_type}_latest.{extension}"
        
        version_path = os.path.join(base_dir, version_filename)
        latest_path = os.path.join(base_dir, latest_filename)
        
        try:
            # 1. Save Versioned File
            with open(version_path, 'w', encoding='utf-8') as f:
                if extension == "json":
                    json.dump(content, f, ensure_ascii=False, indent=2)
                else:
                    f.write(str(content))
            
            # 2. Update Latest Pointer (Copy)
            # We use copy instead of symlink for better Windows compatibility and simplicity
            shutil.copy2(version_path, latest_path)
            
            logger.info(f"Saved artifact [{project_id}]: {version_filename} (updated latest)")
            return version_path
            
        except Exception as e:
            logger.error(f"Failed to save artifact {artifact_type}: {e}")
            raise e

    @staticmethod
    def load_latest_artifact(artifact_type: str, base_dir: str, extension: str = "json") -> Optional[Any]:
        """
        Load the latest version of an artifact.
        """
        latest_path = os.path.join(base_dir, f"{artifact_type}_latest.{extension}")
        
        if not os.path.exists(latest_path):
            return None
            
        try:
            with open(latest_path, 'r', encoding='utf-8') as f:
                if extension == "json":
                    return json.load(f)
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load artifact {latest_path}: {e}")
            return None

artifact_manager = ArtifactManager()
