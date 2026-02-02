import os
import json
import shutil
from typing import Dict, Optional, List
from datetime import datetime
from src.core.config import config
from src.utils.logger import logger, op_logger

class ProjectManager:
    def __init__(self):
        self.index_path = os.path.join(config.data_dir, "project_index.json")
        self.projects = {}
        self.next_id = 1
        self._load_index()
        # Scan on init to ensure index is up to date with source folder
        self._scan_and_update()

    def _load_index(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.projects = data.get("projects", {})
                    self.next_id = data.get("next_id", 1)
            except Exception as e:
                logger.error(f"Error loading project index: {e}")
                self.projects = {}
                self.next_id = 1
        else:
            self.projects = {}
            self.next_id = 1

    def _save_index(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        data = {
            "projects": self.projects,
            "next_id": self.next_id
        }
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _scan_and_update(self):
        if not os.path.exists(config.analysis_source_dir):
            return

        existing_paths = {p['source_path']: pid for pid, p in self.projects.items()}
        
        for item in os.listdir(config.analysis_source_dir):
            item_path = os.path.join(config.analysis_source_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                if item_path not in existing_paths:
                    new_id = f"PROJ_{self.next_id:03d}"
                    self.projects[new_id] = {
                        "name": item,
                        "source_path": item_path,
                        "created_at": datetime.now().isoformat(),
                        "status": "discovered" # Not yet initialized
                    }
                    self.next_id += 1
                    logger.info(f"Discovered new project: {item} -> {new_id}")
        
        self._save_index()

    def get_project_paths(self, project_id: str) -> Dict[str, str]:
        """Get standardized paths for a project."""
        base = os.path.join(config.data_dir, "projects", project_id)
        return {
            "root": base,
            "raw": os.path.join(base, "raw"),
            "alignment": os.path.join(base, "alignment"),
            "ground_truth": os.path.join(base, "ground_truth"),
            "analysis": os.path.join(base, "analysis")
        }

    def initialize_project(self, project_id: str) -> bool:
        """
        Initialize project structure and ingest data (Copy Strategy).
        """
        project = self.projects.get(project_id)
        if not project:
            logger.error(f"Project {project_id} not found")
            return False

        paths = self.get_project_paths(project_id)
        
        # 1. Create Directories
        for p in paths.values():
            os.makedirs(p, exist_ok=True)

        # 2. Ingest Data (Copy from Source)
        source_path = project['source_path']
        files_copied = []
        
        try:
            # Copy Novel
            novel_src_dir = os.path.join(source_path, "novel")
            if os.path.exists(novel_src_dir):
                for f in os.listdir(novel_src_dir):
                    if f.endswith(".txt"):
                        shutil.copy2(os.path.join(novel_src_dir, f), os.path.join(paths['raw'], "novel.txt"))
                        files_copied.append("novel.txt")
                        break # Only take first txt
            
            # Copy SRTs
            srt_src_dir = os.path.join(source_path, "srt")
            if os.path.exists(srt_src_dir):
                for f in os.listdir(srt_src_dir):
                    if f.endswith(".srt"):
                        shutil.copy2(os.path.join(srt_src_dir, f), os.path.join(paths['raw'], f))
                        files_copied.append(f)

            # Update Status
            self.projects[project_id]['status'] = "initialized"
            self.projects[project_id]['initialized_at'] = datetime.now().isoformat()
            self._save_index()
            
            op_logger.log_operation(project_id, "Initialize Project", files_copied, "Ingested raw data")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize project {project_id}: {e}")
            return False

    def list_projects(self) -> List[Dict]:
        return [{"id": k, **v} for k, v in self.projects.items()]

project_manager = ProjectManager()
