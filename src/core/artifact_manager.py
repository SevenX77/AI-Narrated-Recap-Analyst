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
        
        策略：
        1. 主目录只保留 latest 文件
        2. 所有版本文件（包括新版本）保存在 history/ 目录
        
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
        
        # 主目录：只有 latest
        latest_path = os.path.join(base_dir, latest_filename)
        
        # history 目录：所有版本文件
        history_dir = os.path.join(base_dir, "history")
        version_path = os.path.join(history_dir, version_filename)
        
        try:
            # 0. 确保 history 目录存在
            os.makedirs(history_dir, exist_ok=True)
            
            # 1. 将主目录中的旧版本文件移动到 history/
            import glob
            pattern = os.path.join(base_dir, f"{artifact_type}_v*.{extension}")
            existing_versions_in_root = glob.glob(pattern)
            
            moved_count = 0
            for old_version in existing_versions_in_root:
                # 只移动主目录中的版本文件
                if os.path.dirname(old_version) == base_dir:
                    dest_path = os.path.join(history_dir, os.path.basename(old_version))
                    try:
                        shutil.move(old_version, dest_path)
                        moved_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to move old version {old_version}: {e}")
            
            if moved_count > 0:
                logger.debug(f"Moved {moved_count} old version(s) to history/")
            
            # 2. 保存新版本到 history/ 目录
            with open(version_path, 'w', encoding='utf-8') as f:
                if extension == "json":
                    json.dump(content, f, ensure_ascii=False, indent=2)
                else:
                    f.write(str(content))
            
            # 3. 更新主目录的 latest 文件
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
