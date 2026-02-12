"""
ProjectManager V2 - 支持新的数据存储架构
- 使用 meta.json 存储项目元数据
- 清晰的目录结构（raw, processed, analysis, reports）
- 项目属性（has_novel, has_script）
- 工作流阶段跟踪
"""
import os
import json
import shutil
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path

from src.core.schemas_project import (
    ProjectMeta,
    ProjectStatus,
    ProjectSources,
    WorkflowStages,
    WorkflowStageInfo,
    WorkflowStageStatus,
    ProjectStats
)
from src.core.config import config
from src.utils.logger import logger

class ProjectManagerV2:
    """项目管理器 V2"""
    
    def __init__(self):
        self.projects_dir = os.path.join(config.data_dir, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)
    
    def create_project(self, name: str, description: Optional[str] = None) -> ProjectMeta:
        """创建新项目"""
        # 生成项目ID
        project_id = self._generate_project_id()
        
        # 创建项目目录结构（analyst/ 符合 Phase I 的4步工作流）
        project_dir = os.path.join(self.projects_dir, project_id)
        os.makedirs(os.path.join(project_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "raw/novel"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "raw/script"), exist_ok=True)  # ⚠️ 从srt改为script
        # Phase I Analyst 目录结构
        os.makedirs(os.path.join(project_dir, "analyst/import/novel"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "analyst/import/script"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "analyst/script_analysis"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "analyst/script_analysis/history"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "analyst/novel_analysis"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "analyst/novel_analysis/history"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "analyst/alignment"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "analyst/alignment/history"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "reports"), exist_ok=True)
        
        # 创建项目元数据
        meta = ProjectMeta(
            id=project_id,
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status=ProjectStatus.DRAFT
        )
        
        # 保存元数据
        self._save_meta(project_id, meta)
        
        logger.info(f"Created project: {project_id} ({name})")
        return meta
    
    def get_project(self, project_id: str) -> Optional[ProjectMeta]:
        """获取项目元数据"""
        meta_path = self._get_meta_path(project_id)
        if not os.path.exists(meta_path):
            return None
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return ProjectMeta.from_dict(data)
    
    def list_projects(self) -> List[ProjectMeta]:
        """列出所有项目"""
        projects = []
        
        if not os.path.exists(self.projects_dir):
            return projects
        
        for item in os.listdir(self.projects_dir):
            project_dir = os.path.join(self.projects_dir, item)
            if os.path.isdir(project_dir):
                meta = self.get_project(item)
                if meta:
                    projects.append(meta)
        
        # 按更新时间排序
        projects.sort(key=lambda x: x.updated_at, reverse=True)
        return projects
    
    def update_project(self, project_id: str, **kwargs) -> Optional[ProjectMeta]:
        """更新项目元数据"""
        meta = self.get_project(project_id)
        if not meta:
            return None
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(meta, key):
                setattr(meta, key, value)
        
        meta.updated_at = datetime.now().isoformat()
        
        # 保存
        self._save_meta(project_id, meta)
        return meta
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        project_dir = os.path.join(self.projects_dir, project_id)
        if not os.path.exists(project_dir):
            return False
        
        try:
            shutil.rmtree(project_dir)
            logger.info(f"Deleted project: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False
    
    def add_file(self, project_id: str, file_path: str, file_type: str) -> bool:
        """添加文件到项目"""
        meta = self.get_project(project_id)
        if not meta:
            return False
        
        # 复制文件到 raw 下的分类目录
        filename = os.path.basename(file_path)
        raw_base = os.path.join(self.projects_dir, project_id, "raw")
        subdir = "novel" if file_type in ("novel", "document", "pdf") else "script" if file_type == "script" else None
        if subdir:
            raw_dir = os.path.join(raw_base, subdir)
            os.makedirs(raw_dir, exist_ok=True)
        else:
            raw_dir = raw_base
            os.makedirs(raw_dir, exist_ok=True)
        target_path = os.path.join(raw_dir, filename)
        
        try:
            shutil.copy2(file_path, target_path)
            
            # 更新源文件信息
            if file_type == "novel":
                meta.sources.has_novel = True
            elif file_type == "script":
                meta.sources.has_script = True
            
            # 更新统计
            meta.stats.raw_files_count += 1
            meta.stats.total_size += os.path.getsize(target_path)
            meta.status = ProjectStatus.READY
            
            self._save_meta(project_id, meta)
            logger.info(f"Added file {filename} to project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add file to project {project_id}: {e}")
            return False
    
    def get_chapters(self, project_id: str) -> List[Dict]:
        """获取小说章节列表"""
        chapters_index_path = os.path.join(
            self.projects_dir, project_id, "analyst/import/novel/chapters.json"
        )
        
        if not os.path.exists(chapters_index_path):
            return []
        
        with open(chapters_index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("chapters", [])
    
    def get_episodes(self, project_id: str) -> List[Dict]:
        """获取脚本集数列表"""
        episodes_index_path = os.path.join(
            self.projects_dir, project_id, "analyst/import/script/episodes.json"
        )
        
        if not os.path.exists(episodes_index_path):
            return []
        
        with open(episodes_index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("episodes", [])
    
    def get_raw_files(self, project_id: str) -> List[Dict]:
        """获取原始文件列表，从 raw/novel 与 raw/script 分类目录汇总，并带 category 字段"""
        raw_base = os.path.join(self.projects_dir, project_id, "raw")
        if not os.path.exists(raw_base):
            return []

        files = []
        for category, exts in [("novel", (".txt", ".md", ".pdf")), ("script", (".srt",))]:
            cat_dir = os.path.join(raw_base, category)
            if not os.path.isdir(cat_dir):
                continue
            for filename in os.listdir(cat_dir):
                file_path = os.path.join(cat_dir, filename)
                if os.path.isfile(file_path) and any(filename.lower().endswith(e) for e in exts):
                    stat = os.stat(file_path)
                    files.append({
                        "name": filename,
                        "size": stat.st_size,
                        "type": self._get_file_type(filename),
                        "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "category": category,
                    })
        # 兼容：根 raw 下直接放文件（不设 category，查看/删除时用 raw/filename）
        for filename in os.listdir(raw_base):
            if filename in ("novel", "srt"):
                continue
            file_path = os.path.join(raw_base, filename)
            if os.path.isfile(file_path):
                ft = self._get_file_type(filename)
                if ft in ("novel", "script", "document", "pdf"):
                    stat = os.stat(file_path)
                    files.append({
                        "name": filename,
                        "size": stat.st_size,
                        "type": ft,
                        "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
        return files
    
    def update_sources_from_filesystem(self, project_id: str) -> bool:
        """
        根据文件系统状态自动更新项目源文件信息
        - has_novel: 检查 raw/novel/ 中是否有 .txt 文件
        - has_script: 检查 raw/script/ 中是否有 .srt 文件
        - novel_chapters: 从 analyst/import/novel/chapters.json 读取
        - script_episodes: 从 analyst/import/script/episodes.json 读取
        """
        meta = self.get_project(project_id)
        if not meta:
            return False
        
        raw_base = os.path.join(self.projects_dir, project_id, "raw")
        novel_dir = os.path.join(raw_base, "novel")
        script_dir = os.path.join(raw_base, "script")  # ⚠️ 从srt_dir改为script_dir

        has_novel = False
        if os.path.isdir(novel_dir):
            for filename in os.listdir(novel_dir):
                if filename.lower().endswith(('.txt', '.md', '.pdf')):
                    has_novel = True
                    break
        if not has_novel and os.path.exists(raw_base):
            for filename in os.listdir(raw_base):
                if os.path.isfile(os.path.join(raw_base, filename)) and filename.lower().endswith('.txt'):
                    has_novel = True
                    break

        has_script = False
        if os.path.isdir(script_dir):
            for filename in os.listdir(script_dir):
                if filename.lower().endswith('.srt'):
                    has_script = True
                    break
        if not has_script and os.path.exists(raw_base):
            for filename in os.listdir(raw_base):
                if os.path.isfile(os.path.join(raw_base, filename)) and filename.lower().endswith('.srt'):
                    has_script = True
                    break
        
        # 获取章节数
        chapters = self.get_chapters(project_id)
        novel_chapters = len(chapters)
        
        # 获取集数
        episodes = self.get_episodes(project_id)
        script_episodes = len(episodes)
        
        # 更新 meta
        meta.sources.has_novel = has_novel
        meta.sources.has_script = has_script
        meta.sources.novel_chapters = novel_chapters
        meta.sources.script_episodes = script_episodes
        
        # 同步更新 Phase I 状态
        if meta.phase_i_analyst:
            meta.phase_i_analyst.step_1_import.novel_imported = has_novel
            meta.phase_i_analyst.step_1_import.script_imported = has_script
            meta.phase_i_analyst.step_1_import.novel_chapter_count = novel_chapters
            
            # 安全地处理 script episodes
            script_ep_names = []
            script_total = 0
            if episodes:
                for e in episodes:
                    if isinstance(e, dict):
                        script_ep_names.append(e.get('episode_name', 'unknown'))
                        script_total += e.get('entry_count', 0)
            
            meta.phase_i_analyst.step_1_import.script_episodes = script_ep_names
            meta.phase_i_analyst.step_1_import.script_total_entries = script_total
        
        # 更新项目状态
        if has_novel or has_script:
            if meta.status == ProjectStatus.DRAFT:
                meta.status = ProjectStatus.READY
        
        self._save_meta(project_id, meta)
        logger.info(f"Updated sources for project {project_id}: has_novel={has_novel}, has_script={has_script}")
        return True
    
    def update_workflow_stage(
        self, 
        project_id: str,
        stage_name: str,
        status: WorkflowStageStatus,
        error_message: Optional[str] = None,
        tasks: Optional[List] = None
    ) -> bool:
        """更新工作流阶段状态"""
        meta = self.get_project(project_id)
        if not meta:
            return False
        
        stage_info = getattr(meta.workflow_stages, stage_name, None)
        if not stage_info:
            logger.error(f"Invalid stage name: {stage_name}")
            return False
        
        stage_info.status = status
        
        if status == WorkflowStageStatus.RUNNING:
            stage_info.started_at = datetime.now().isoformat()
        elif status in [WorkflowStageStatus.COMPLETED, WorkflowStageStatus.FAILED]:
            stage_info.completed_at = datetime.now().isoformat()
        
        if error_message:
            stage_info.error_message = error_message
        
        # 更新子任务列表
        if tasks is not None:
            stage_info.tasks = tasks
        
        self._save_meta(project_id, meta)
        return True
    
    def save_project_meta(self, meta):
        """保存项目元数据（供外部使用）"""
        self._save_meta(meta.id, meta)
    
    def _generate_project_id(self) -> str:
        """生成项目ID"""
        existing_ids = [
            d for d in os.listdir(self.projects_dir)
            if os.path.isdir(os.path.join(self.projects_dir, d))
        ]
        
        # 提取数字后缀
        max_num = 0
        for pid in existing_ids:
            if pid.startswith("project_"):
                try:
                    num = int(pid.split("_")[1])
                    max_num = max(max_num, num)
                except:
                    continue
        
        return f"project_{max_num + 1:03d}"
    
    def _get_meta_path(self, project_id: str) -> str:
        """获取元数据文件路径"""
        return os.path.join(self.projects_dir, project_id, "meta.json")
    
    def _save_meta(self, project_id: str, meta: ProjectMeta):
        """保存元数据（原子写入，防止损坏）"""
        meta_path = self._get_meta_path(project_id)
        temp_path = meta_path + '.tmp'
        
        try:
            # 1. 序列化数据（先验证能否成功序列化）
            data_dict = meta.to_dict()
            json_str = json.dumps(data_dict, ensure_ascii=False, indent=2)
            
            # 2. 写入临时文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
                f.flush()  # 确保写入磁盘
                os.fsync(f.fileno())  # 强制同步到磁盘
            
            # 3. 验证临时文件可读且JSON有效
            with open(temp_path, 'r', encoding='utf-8') as f:
                json.load(f)  # 验证JSON格式
            
            # 4. 原子替换（rename是原子操作）
            os.replace(temp_path, meta_path)
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.error(f"Failed to save meta for {project_id}: {e}")
            raise
    
    def _get_file_type(self, filename: str) -> str:
        """根据文件名判断类型"""
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.txt':
            return 'novel'
        elif ext == '.srt':
            return 'script'
        elif ext in ['.md', '.markdown']:
            return 'document'
        elif ext in ['.pdf']:
            return 'pdf'
        else:
            return 'other'

# 全局实例
project_manager_v2 = ProjectManagerV2()
