"""
PreprocessService - 自动预处理服务
上传 raw 文件后自动执行预处理流程

职责：
1. Novel 处理链:
   - NovelImporter: 编码检测 + 规范化 → raw/novel.txt
   - NovelChapterDetector: 检测章节边界
   - NovelMetadataExtractor: 提取标题、作者、标签、简介
   - 保存到 analyst/import/novel/ 目录 (Phase I Step 1)

2. Script 处理链:
   - SrtImporter: 编码检测 + 解析SRT → raw/epXX.srt
   - SrtTextExtractor: 提取文本 + LLM智能添加标点
   - 保存到 analyst/import/script/ 目录 (Phase I Step 1)
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.tools.novel_importer import NovelImporter
from src.tools.novel_chapter_detector import NovelChapterDetector
from src.tools.novel_metadata_extractor import NovelMetadataExtractor
from src.tools.srt_importer import SrtImporter
from src.tools.srt_text_extractor import SrtTextExtractor

from src.core.project_manager_v2 import project_manager_v2
from src.core.schemas_project import WorkflowStageStatus, PreprocessTask
from src.core.config import config

logger = logging.getLogger(__name__)


class PreprocessService:
    """自动预处理服务"""
    
    def __init__(self):
        self.novel_importer = NovelImporter()
        self.chapter_detector = NovelChapterDetector()
        self.metadata_extractor = NovelMetadataExtractor(use_llm=True, provider="deepseek")
        
        self.srt_importer = SrtImporter()
        self.text_extractor = SrtTextExtractor(use_llm=True, provider="deepseek")
    
    def preprocess_project(self, project_id: str, filename: Optional[str] = None, category: Optional[str] = None) -> Dict[str, any]:
        """
        预处理项目中的 raw 文件
        
        Args:
            project_id: 项目ID
            filename: 指定处理的文件名（可选）。如果提供，只处理该文件。
            category: 指定处理的类别（'novel', 'script'）。如果提供且无filename，处理该类别所有文件。
        
        Returns:
            Dict: 处理结果统计
        """
        logger.info(f"Starting preprocess for project: {project_id}, file: {filename}, category: {category}")
        
        result = {
            "success": True,
            "novel_processed": False,
            "script_episodes_processed": 0,
            "errors": []
        }
        
        try:
            project_dir = os.path.join(config.data_dir, "projects", project_id)
            raw_base = os.path.join(project_dir, "raw")
            raw_novel_dir = os.path.join(raw_base, "novel")
            raw_srt_dir = os.path.join(raw_base, "script")  # ⚠️ 从srt改为script

            if not os.path.exists(raw_base):
                raise ValueError(f"Raw directory not found: {raw_base}")

            # 确定要处理的文件列表
            tasks = []
            novel_dirs = []
            if os.path.isdir(raw_novel_dir):
                novel_dirs.append(raw_novel_dir)
            novel_dirs.append(raw_base)
            srt_dirs = []
            if os.path.isdir(raw_srt_dir):
                srt_dirs.append(raw_srt_dir)
            srt_dirs.append(raw_base)

            target_is_novel = False
            target_is_srt = False
            
            if filename:
                if filename.lower().endswith('.txt'):
                    target_is_novel = True
                elif filename.lower().endswith('.srt'):
                    target_is_srt = True
            elif category:
                if category == 'novel':
                    target_is_novel = True
                elif category == 'script':
                    target_is_srt = True
            else:
                target_is_novel = True
                target_is_srt = True

            # 生成任务列表
            if target_is_novel:
                novel_added = False
                for scan_dir in novel_dirs:
                    if not os.path.isdir(scan_dir) or novel_added:
                        continue
                    for f in os.listdir(scan_dir):
                        if f.lower().endswith('.txt'):
                            # 如果指定了文件名，只添加匹配的任务
                            if filename and f != filename:
                                continue
                                
                            tasks.append(PreprocessTask(
                                task_id="novel",
                                task_type="novel",
                                task_name=f"Novel: {f}",
                                status=WorkflowStageStatus.PENDING
                            ))
                            novel_added = True
                            break # 目前只支持一本小说
            
            if target_is_srt:
                srt_seen = set()
                for scan_dir in srt_dirs:
                    if not os.path.isdir(scan_dir):
                        continue
                    for f in sorted(os.listdir(scan_dir)):
                        if f.lower().endswith('.srt') and f not in srt_seen:
                            # 如果指定了文件名，只添加匹配的任务
                            if filename and f != filename:
                                continue
                                
                            srt_seen.add(f)
                            episode_name = Path(f).stem
                            tasks.append(PreprocessTask(
                                task_id=episode_name,
                                task_type="script",
                                task_name=f"Script: {f}",
                                status=WorkflowStageStatus.PENDING
                            ))

            # 合并现有的任务状态
            # 逻辑：保留不属于当前执行范围的任务
            current_meta = project_manager_v2.get_project(project_id)
            final_tasks = []
            
            if current_meta and current_meta.workflow_stages.preprocess.tasks:
                for t in current_meta.workflow_stages.preprocess.tasks:
                    should_keep = True
                    
                    # 检查任务是否在当前执行范围内
                    if filename:
                        # 范围：特定文件
                        # 简单判断：如果 task_name 包含文件名（不够严谨但目前够用，或者用 task_id）
                        # 对于 novel，task_id="novel"，对于 script，task_id=episode_name
                        if t.task_type == 'novel' and target_is_novel:
                             should_keep = False # 简单起见，如果处理novel文件，就替换掉 novel 任务
                        elif t.task_type == 'script' and target_is_srt:
                             # 检查是否是同一个 episode
                             if filename.startswith(t.task_id): # ep01.srt -> ep01
                                 should_keep = False
                    elif category == 'novel':
                        # 范围：所有 Novel
                        if t.task_type == 'novel':
                            should_keep = False
                    elif category == 'script':
                        # 范围：所有 Script
                        if t.task_type == 'script':
                            should_keep = False
                    else:
                        # 范围：所有
                        should_keep = False
                    
                    if should_keep:
                        final_tasks.append(t)
            
            # 添加新任务
            final_tasks.extend(tasks)

            project_manager_v2.update_workflow_stage(
                project_id, "preprocess", WorkflowStageStatus.RUNNING, tasks=final_tasks
            )

            # 执行处理
            if target_is_novel:
                novel_dirs_for_run = [d for d in novel_dirs if os.path.isdir(d)]
                # 检查是否有匹配的小说文件
                has_novel = False
                for d in novel_dirs_for_run:
                    for f in os.listdir(d):
                        if f.lower().endswith('.txt'):
                            if filename and f != filename:
                                continue
                            has_novel = True
                            break
                    if has_novel: break
                
                if has_novel:
                    self._update_task_status(
                        project_id, "novel", WorkflowStageStatus.RUNNING,
                        current_step="Detecting chapters"
                    )
                    novel_result = self._preprocess_novel(project_id, novel_dirs_for_run, target_filename=filename)
                    result["novel_processed"] = novel_result["success"]
                    if novel_result.get("error"):
                        result["errors"].append(novel_result["error"])
                        self._update_task_status(
                            project_id, "novel", WorkflowStageStatus.FAILED, 
                            error_message=novel_result["error"]
                        )
                    else:
                        self._update_task_status(
                            project_id, "novel", WorkflowStageStatus.COMPLETED,
                            progress=f"{novel_result.get('chapters', 0)} chapters detected"
                        )
            
            if target_is_srt:
                srt_dirs_for_run = [d for d in srt_dirs if os.path.isdir(d)]
                script_result = self._preprocess_scripts(project_id, srt_dirs_for_run, target_filename=filename)
                result["script_episodes_processed"] = script_result["episodes_processed"]
                if script_result.get("errors"):
                    result["errors"].extend(script_result["errors"])
            
            # 更新项目源文件信息
            project_manager_v2.update_sources_from_filesystem(project_id)
            
            # 更新工作流阶段状态
            # 检查是否所有任务都完成了
            all_tasks_completed = True
            has_failures = False
            
            updated_meta = project_manager_v2.get_project(project_id)
            if updated_meta and updated_meta.workflow_stages.preprocess.tasks:
                for t in updated_meta.workflow_stages.preprocess.tasks:
                    if t.status == WorkflowStageStatus.FAILED:
                        has_failures = True
                    if t.status in [WorkflowStageStatus.PENDING, WorkflowStageStatus.RUNNING]:
                        all_tasks_completed = False
            
            if has_failures:
                 if all_tasks_completed:
                    project_manager_v2.update_workflow_stage(
                        project_id, "preprocess", WorkflowStageStatus.FAILED,
                        error_message="Some tasks failed"
                    )
            elif all_tasks_completed:
                project_manager_v2.update_workflow_stage(
                    project_id, "preprocess", WorkflowStageStatus.COMPLETED
                )
            
            logger.info(f"Preprocess completed for project {project_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Preprocess failed for project {project_id}: {e}")
            result["success"] = False
            result["errors"].append(str(e))
            project_manager_v2.update_workflow_stage(
                project_id, "preprocess", WorkflowStageStatus.FAILED,
                error_message=str(e)
            )
            return result
    
    def _update_task_status(
        self, 
        project_id: str, 
        task_id: str, 
        status: WorkflowStageStatus,
        error_message: Optional[str] = None,
        current_step: Optional[str] = None,
        progress: Optional[str] = None
    ):
        """更新子任务状态"""
        meta = project_manager_v2.get_project(project_id)
        if not meta:
            return
        
        # 更新子任务状态
        for task in meta.workflow_stages.preprocess.tasks:
            if task.task_id == task_id:
                task.status = status
                if status == WorkflowStageStatus.RUNNING:
                    task.started_at = datetime.now().isoformat()
                elif status in [WorkflowStageStatus.COMPLETED, WorkflowStageStatus.FAILED]:
                    task.completed_at = datetime.now().isoformat()
                if error_message:
                    task.error_message = error_message
                if current_step:
                    task.current_step = current_step
                if progress:
                    task.progress = progress
                break
        
        # 保存更新
        project_manager_v2.save_project_meta(meta)
    
    def _preprocess_novel(self, project_id: str, raw_dirs: List[str], target_filename: Optional[str] = None) -> Dict:
        """
        预处理 Novel。在 raw_dirs（如 [raw/novel, raw]）中查找 .txt 文件。
        """
        result = {"success": False, "error": None}
        try:
            novel_file = None
            for raw_dir in raw_dirs:
                if not os.path.isdir(raw_dir):
                    continue
                for filename in os.listdir(raw_dir):
                    if filename.lower().endswith('.txt'):
                        if target_filename and filename != target_filename:
                            continue
                        novel_file = os.path.join(raw_dir, filename)
                        break
                if novel_file:
                    break
            if not novel_file:
                logger.info("No novel file found, skipping novel preprocessing")
                return result
            
            logger.info(f"Processing novel file: {novel_file}")
            
            # Step 1: 检测章节
            chapters = self.chapter_detector.execute(
                novel_file=novel_file,
                validate_continuity=True
            )
            logger.info(f"Detected {len(chapters)} chapters")
            result["chapters"] = len(chapters)
            
            # Step 2: 提取元数据
            metadata = self.metadata_extractor.execute(
                novel_file=novel_file
            )
            logger.info(f"Extracted metadata: {metadata.title} by {metadata.author}")
            
            # Step 3: 保存到 analyst/import/novel/ (Phase I Step 1)
            processed_dir = os.path.join(
                config.data_dir, "projects", project_id, "analyst/import/novel"
            )
            os.makedirs(processed_dir, exist_ok=True)
            
            # 保存章节索引
            chapters_data = {
                "total_chapters": len(chapters),
                "chapters": [
                    {
                        "chapter_number": ch.number,
                        "title": ch.title,
                        "start_line": ch.start_line,
                        "end_line": ch.end_line,
                        "word_count": ch.word_count
                    }
                    for ch in chapters
                ]
            }
            chapters_path = os.path.join(processed_dir, "chapters.json")
            with open(chapters_path, 'w', encoding='utf-8') as f:
                json.dump(chapters_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved chapters index to {chapters_path}")
            
            # 保存元数据
            metadata_path = os.path.join(processed_dir, "metadata.json")
            metadata_dict = metadata.model_dump() if hasattr(metadata, 'model_dump') else metadata.dict()
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_dict, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved metadata to {metadata_path}")
            
            # Step 4: 生成 intro.md (使用 metadata 中的 introduction)
            try:
                intro_path = os.path.join(processed_dir, "intro.md")
                intro_content = metadata_dict.get('introduction', '')
                with open(intro_path, 'w', encoding='utf-8') as f:
                    # 添加 Markdown 标题
                    f.write('# Introduction\n\n')
                    f.write(intro_content)
                logger.info(f"Generated intro.md from metadata")
            except Exception as e:
                logger.warning(f"Failed to generate intro.md: {e}")
            
            # Step 5: 生成 Markdown 版本 (novel-imported.md)
            try:
                with open(novel_file, 'r', encoding='utf-8') as f:
                    novel_content = f.read()
                self.novel_importer._save_imported_markdown(novel_content, project_id)
                logger.info("Generated novel-imported.md")
            except Exception as e:
                logger.warning(f"Failed to generate markdown: {e}")
            
            result["success"] = True
            return result
            
        except Exception as e:
            logger.error(f"Failed to preprocess novel: {e}")
            result["error"] = f"Novel preprocessing error: {str(e)}"
            return result
    
    def _preprocess_scripts(self, project_id: str, raw_dirs: List[str], target_filename: Optional[str] = None) -> Dict:
        """
        预处理 Scripts。在 raw_dirs（如 [raw/srt, raw]）中查找 .srt 文件。
        """
        result = {"episodes_processed": 0, "errors": []}
        try:
            srt_files = []
            seen = set()
            for raw_dir in raw_dirs:
                if not os.path.isdir(raw_dir):
                    continue
                for filename in sorted(os.listdir(raw_dir)):
                    if filename.lower().endswith('.srt') and filename not in seen:
                        if target_filename and filename != target_filename:
                            continue
                        seen.add(filename)
                        srt_files.append(os.path.join(raw_dir, filename))
            
            if not srt_files:
                logger.info("No script files found, skipping script preprocessing")
                return result
            
            logger.info(f"Found {len(srt_files)} script files")
            
            processed_dir = os.path.join(
                config.data_dir, "projects", project_id, "analyst/import/script"
            )
            os.makedirs(processed_dir, exist_ok=True)
            
            episodes_data = []
            
            for srt_file in srt_files:
                episode_name = Path(srt_file).stem
                try:
                    logger.info(f"Processing script: {episode_name}")
                    
                    # 更新任务状态为运行中 - 解析SRT
                    self._update_task_status(
                        project_id, episode_name, WorkflowStageStatus.RUNNING,
                        current_step="Parsing SRT"
                    )
                    
                    # 读取并解析 SRT
                    srt_result = self.srt_importer.execute(
                        source_file=srt_file,
                        project_name=project_id,
                        episode_name=episode_name,
                        save_to_disk=True,  # 保存规范化版本（不生成markdown，等处理后再生成）
                        include_entries=True
                    )
                    
                    # 更新任务状态 - 提取文本
                    self._update_task_status(
                        project_id, episode_name, WorkflowStageStatus.RUNNING,
                        current_step="Extracting text with LLM",
                        progress=f"{srt_result.entry_count} entries"
                    )
                    
                    # 提取文本 + 添加标点
                    text_result = self.text_extractor.execute(
                        srt_entries=srt_result.entries,
                        project_name=project_id,
                        episode_name=episode_name,
                        novel_reference=None  # TODO: 如果有小说，可以传入
                    )
                    
                    # 保存处理后的文本和SRT条目（用于前端显示时间戳）
                    episode_path = os.path.join(processed_dir, f"{episode_name}.json")
                    with open(episode_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            "episode_name": episode_name,
                            "original_entry_count": srt_result.entry_count,
                            "processed_text": text_result.processed_text,
                            "processing_mode": text_result.processing_mode,
                            "entity_standardization": text_result.entity_standardization,
                            "entries": [
                                {
                                    "index": entry.index,
                                    "start_time": entry.start_time,
                                    "end_time": entry.end_time,
                                    "text": entry.text
                                }
                                for entry in srt_result.entries
                            ]
                        }, f, ensure_ascii=False, indent=2)
                    logger.info(f"Saved processed script to {episode_path}")
                    
                    # ✅ 生成 Markdown（句子级时间标注，用户阅读友好）
                    # Reason: Markdown使用智能算法将LLM处理后的文本按句子分段并匹配时间戳
                    # 提供比原始SRT条目更好的阅读体验（句子完整、有标点）
                    # JSON的entries保留原始SRT数据供API使用
                    try:
                        self.srt_importer.save_processed_markdown(
                            processed_text=text_result.processed_text,
                            entries=srt_result.entries,
                            project_name=project_id,
                            episode_name=episode_name
                        )
                        logger.info(f"Generated markdown for {episode_name}")
                    except Exception as e:
                        logger.warning(f"Failed to generate markdown for {episode_name}: {e}")
                    
                    episodes_data.append({
                        "episode_name": episode_name,
                        "entry_count": srt_result.entry_count,
                        "word_count": len(text_result.processed_text)
                    })
                    
                    result["episodes_processed"] += 1
                    
                    # 更新任务状态为完成
                    self._update_task_status(
                        project_id, episode_name, WorkflowStageStatus.COMPLETED,
                        progress=f"{len(text_result.processed_text)} chars processed"
                    )
                    
                except Exception as e:
                    error_msg = f"Failed to process {Path(srt_file).name}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    # 更新任务状态为失败
                    self._update_task_status(
                        project_id, episode_name, WorkflowStageStatus.FAILED,
                        error_message=str(e)
                    )
            
            # 保存集数索引
            episodes_index_path = os.path.join(processed_dir, "episodes.json")
            with open(episodes_index_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "total_episodes": len(episodes_data),
                    "episodes": episodes_data
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved episodes index to {episodes_index_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to preprocess scripts: {e}")
            result["errors"].append(f"Script preprocessing error: {str(e)}")
            return result


# 全局实例
preprocess_service = PreprocessService()
