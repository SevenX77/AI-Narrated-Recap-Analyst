import os
import re
import json
from typing import List
from src.core.interfaces import BaseWorkflow
from src.core.project_manager import project_manager
from src.core.artifact_manager import artifact_manager
from src.agents.deepseek_analyst import DeepSeekAnalyst, get_llm_client
from src.modules.alignment.deepseek_alignment_engine import DeepSeekAlignmentEngine
from src.utils.logger import logger, op_logger

class IngestionWorkflow(BaseWorkflow):
    """
    Workflow 1: Ingestion & Alignment
    Executed once per project to prepare data.
    """
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.paths = project_manager.get_project_paths(project_id)
        self.client = get_llm_client()
        self.analyst = DeepSeekAnalyst(self.client)
        self.aligner = DeepSeekAlignmentEngine(self.client)

    async def run(self, **kwargs):
        logger.info(f"🚀 启动数据摄入与对齐流程: {self.project_id}")
        
        # 1. Initialize Project (Ensure paths exist and data is copied)
        # Assuming project is already initialized via CLI or ProjectManager, 
        # but we can double check or re-run initialization if needed.
        # For now, we assume raw data is present.
        
        novel_path = os.path.join(self.paths['raw'], "novel.txt")
        if not os.path.exists(novel_path):
            logger.error(f"Novel file not found: {novel_path}")
            return

        # 2. Novel Analysis (Extract Events)
        logger.info("1. 分析小说内容...")
        with open(novel_path, 'r', encoding='utf-8') as f:
            novel_text = f.read()
            
        # Simple chapter splitting (Same logic as before, can be moved to utils)
        chapters = re.split(r"(第[0-9]+章\s+[^\n]+)", novel_text)
        parts = chapters
        if parts and not re.match(r"(第[0-9]+章\s+[^\n]+)", parts[0]):
            parts = parts[1:] 
            
        novel_events_db = []
        for i in range(0, len(parts), 2):
            if i+1 < len(parts):
                title = parts[i].strip()
                content = parts[i+1].strip()
                logger.info(f"   - 处理 {title}...")
                events = self.analyst.extract_events(content, title)
                novel_events_db.append({"id": title, "events": [e.model_dump() for e in events]})
        
        # Save Novel Events Artifact
        artifact_manager.save_artifact(
            novel_events_db,
            "novel_events",
            self.project_id,
            self.paths['alignment']
        )
        
        # 3. Script Analysis & Alignment
        logger.info("2. 处理解说字幕...")
        import glob
        srt_files = sorted(glob.glob(os.path.join(self.paths['raw'], "*.srt")))
        
        all_alignment_results = []
        all_script_events = {}
        
        for srt_path in srt_files:
            filename = os.path.basename(srt_path)
            episode_name = os.path.splitext(filename)[0]  # e.g., "ep01"
            logger.info(f"   - 分析: {filename}")
            
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
                
            # Parse SRT (Simple grouping)
            blocks = srt_content.strip().split('\n\n')
            srt_chunks = []
            current_text = []
            start_time = ""
            
            for i, block in enumerate(blocks):
                lines = block.split('\n')
                if len(lines) >= 3:
                    if not start_time: start_time = lines[1].split(' --> ')[0]
                    current_text.append(" ".join(lines[2:]))
                    if (i+1) % 10 == 0:
                        srt_chunks.append({"time": start_time, "content": " ".join(current_text)})
                        current_text = []
                        start_time = ""
            if current_text:
                srt_chunks.append({"time": start_time, "content": " ".join(current_text)})
                
            # Extract SRT Events
            srt_events_data = []
            for chunk in srt_chunks:
                events = self.analyst.extract_events(chunk['content'], f"{filename} {chunk['time']}")
                srt_events_data.append({"time": chunk['time'], "events": [e.model_dump() for e in events]})
            
            # Save Script Events Artifact (per episode)
            script_events_path = artifact_manager.save_artifact(
                srt_events_data,
                f"{episode_name}_script_events",
                self.project_id,
                self.paths['alignment']
            )
            logger.info(f"   - 脚本事件已保存: {script_events_path}")
            all_script_events[episode_name] = srt_events_data
                
            # Align
            logger.info(f"   - 对齐: {filename}")
            alignment = self.aligner.align_script_with_novel(novel_events_db, srt_events_data)
            all_alignment_results.extend(alignment)

        # Save Alignment Artifact
        alignment_path = artifact_manager.save_artifact(
            [item.model_dump() for item in all_alignment_results],
            "alignment",
            self.project_id,
            self.paths['alignment']
        )
        
        # Collect all output files for logging
        output_files = [alignment_path]
        output_files.extend([
            os.path.join(self.paths['alignment'], f"{ep}_script_events_latest.json") 
            for ep in all_script_events.keys()
        ])
        
        op_logger.log_operation(
            project_id=self.project_id,
            action="Ingestion & Alignment",
            output_files=output_files,
            details=f"Processed {len(srt_files)} SRT files, extracted novel events and script events"
        )
        
        logger.info("✅ 数据摄入与对齐完成！")
        logger.info(f"   - Novel Events: novel_events_latest.json")
        logger.info(f"   - Script Events: {len(all_script_events)} episodes")
        logger.info(f"   - Alignment Results: alignment_latest.json")