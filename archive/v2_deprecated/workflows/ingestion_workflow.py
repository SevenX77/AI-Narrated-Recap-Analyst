"""
Ingestion Workflow v2 - 基于新的三层数据模型和两级匹配策略

数据流：
1. SRT blocks → Sentences (句子还原)
2. Sentences → Semantic Blocks (意思块划分)
3. Semantic Blocks → Events (事件聚合)
4. Events (Script) vs Events (Novel) → Two-Level Matching

两级匹配：
- Level 1: Event级粗匹配（快速定位候选）
- Level 2: SemanticBlock链细验证（精确确认）
"""

import os
import re
import json
import asyncio
from typing import List, Dict, Tuple
from src.core.interfaces import BaseWorkflow
from src.core.project_manager import project_manager
from src.core.artifact_manager import artifact_manager
from src.core.config import config
from src.agents.deepseek_analyst import get_llm_client
from src.modules.alignment.deepseek_alignment_engine_v2 import DeepSeekAlignmentEngineV2
from src.core.schemas import Sentence, SemanticBlock, Event, EventAlignment
from src.utils.logger import logger, op_logger


class IngestionWorkflow(BaseWorkflow):
    """
    Ingestion Workflow v2
    
    使用新的三层数据模型和两级匹配策略
    """
    
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.paths = project_manager.get_project_paths(project_id)
        self.client = get_llm_client()
        self.aligner = DeepSeekAlignmentEngineV2(self.client)
        self.cfg = config.ingestion
    
    async def run(self, **kwargs):
        """
        执行数据摄入与对齐流程
        
        Args:
            **kwargs: 可选参数
                - max_chapters: 强制指定最大章节数
                - force_reprocess: 强制重新处理（忽略已有结果），默认False
        """
        self.force_reprocess = kwargs.get('force_reprocess', False)
        if self.force_reprocess:
            logger.warning("⚠️  强制重新处理模式：将忽略所有已有结果")
        
        logger.info(f"🚀 启动数据摄入与对齐流程 v2: {self.project_id}")
        
        novel_path = os.path.join(self.paths['raw'], "novel.txt")
        if not os.path.exists(novel_path):
            logger.error(f"Novel file not found: {novel_path}")
            return
        
        # 1. 读取小说并分章
        logger.info("=" * 60)
        logger.info("Step 1: 读取小说内容")
        logger.info("=" * 60)
        
        with open(novel_path, 'r', encoding='utf-8') as f:
            novel_text = f.read()
        
        all_chapters = self._split_chapters(novel_text)
        logger.info(f"✅ 小说共 {len(all_chapters)} 章\n")
        
        # 2. 获取SRT文件列表
        import glob
        srt_files = sorted(glob.glob(os.path.join(self.paths['raw'], "*.srt")))
        logger.info(f"✅ 找到 {len(srt_files)} 个SRT文件\n")
        
        if not srt_files:
            logger.error("未找到SRT文件")
            return
        
        # 3. 处理SRT文件 → Sentences → Semantic Blocks → Events
        logger.info("=" * 60)
        logger.info("Step 2: 处理SRT文件 (Script)")
        logger.info("=" * 60)
        logger.info("🔄 断点续传功能已启用：将自动跳过已处理的文件\n")
        
        script_events_by_episode = await self._process_srt_files(srt_files)
        
        # 4. 处理Novel → Sentences → Semantic Blocks → Events
        logger.info("\n" + "=" * 60)
        logger.info("Step 3: 处理小说章节 (Novel)")
        logger.info("=" * 60)
        
        # 确定要提取的章节数
        forced_max_chapters = kwargs.get('max_chapters')
        if forced_max_chapters:
            chapters_to_process = all_chapters[:forced_max_chapters]
            logger.info(f"使用强制指定的章节数: {forced_max_chapters}")
        else:
            # 简化版：先提取 srt_count * multiplier 章
            initial_chapters = min(
                len(srt_files) * self.cfg.initial_chapter_multiplier,
                len(all_chapters)
            )
            chapters_to_process = all_chapters[:initial_chapters]
            logger.info(f"初始提取策略: {initial_chapters} 章 "
                       f"(SRT数 {len(srt_files)} × 倍数 {self.cfg.initial_chapter_multiplier})")
        
        novel_events = await self._process_novel_chapters(chapters_to_process)
        
        # 5. 执行两级匹配
        logger.info("\n" + "=" * 60)
        logger.info("Step 4: 两级匹配 (Event级粗匹配 + Block链细验证)")
        logger.info("=" * 60)
        
        all_alignments = []
        for episode_name, script_events in script_events_by_episode.items():
            logger.info(f"\n处理集数: {episode_name}")
            logger.info(f"  Script Events: {len(script_events)}")
            logger.info(f"  Novel Events: {len(novel_events)}")
            
            alignments = await self.aligner.match_events_two_level_async(
                script_events,
                novel_events,
                episode_name
            )
            
            all_alignments.extend(alignments)
            logger.info(f"  ✅ 完成匹配: {len(alignments)} 个对齐")
            
            # 如果是ep01，保存Hook部分（如果有）
            if episode_name == "ep01" and hasattr(self.aligner, 'last_hook_result'):
                hook_result = self.aligner.last_hook_result
                if hook_result and hook_result.has_hook:
                    hook_data = {
                        "episode": episode_name,
                        "has_hook": hook_result.has_hook,
                        "hook_end_index": hook_result.hook_end_index,
                        "linear_start_index": hook_result.linear_start_index,
                        "confidence": hook_result.confidence,
                        "reasoning": hook_result.reasoning,
                        "hook_blocks": [
                            {
                                "block_id": block.block_id,
                                "theme": block.theme,
                                "summary": block.summary,
                                "time_range": {
                                    "start": block.time_range.start if block.time_range else None,
                                    "end": block.time_range.end if block.time_range else None
                                } if block.time_range else None
                            }
                            for block in hook_result.hook_blocks
                        ]
                    }
                    
                    # 保存Hook数据
                    artifact_manager.save_artifact(
                        hook_data,
                        f"{episode_name}_hook_detection",
                        self.project_id,
                        self.paths['alignment']
                    )
                    logger.info(f"  💾 保存Hook检测结果: {len(hook_result.hook_blocks)} 个意思块")
        
        # 6. 保存最终结果
        logger.info("\n" + "=" * 60)
        logger.info("Step 5: 保存最终对齐结果")
        logger.info("=" * 60)
        logger.info("(Script Events和Novel Events已在处理过程中增量保存)")
        
        # Save Alignments
        alignment_path = artifact_manager.save_artifact(
            [a.model_dump() for a in all_alignments],
            "alignment_v2",
            self.project_id,
            self.paths['alignment']
        )
        logger.info(f"✅ 保存: alignment_v2")
        
        # 7. 评估质量
        logger.info("\n" + "=" * 60)
        logger.info("Step 6: 质量评估")
        logger.info("=" * 60)
        
        quality_report = self.aligner.evaluate_alignment_quality(
            all_alignments,
            self.cfg.quality_threshold
        )
        
        logger.info(f"\n📊 对齐质量报告:")
        logger.info(f"  综合得分: {quality_report.overall_score:.2f}/100")
        logger.info(f"  平均置信度: {quality_report.avg_confidence:.2%}")
        logger.info(f"  是否合格: {'✅ 是' if quality_report.is_qualified else '❌ 否'}")
        logger.info(f"\n  详细信息:")
        for key, value in quality_report.details.items():
            logger.info(f"    - {key}: {value}")
        
        # Save quality report
        quality_report_path = artifact_manager.save_artifact(
            quality_report.model_dump(),
            "alignment_quality_report_v2",
            self.project_id,
            self.paths['alignment']
        )
        logger.info(f"\n✅ 保存: alignment_quality_report_v2")
        
        # Log operation
        op_logger.log_operation(
            project_id=self.project_id,
            action="Ingestion & Alignment v2 (Two-Level Matching)",
            output_files=[alignment_path, quality_report_path],
            details=f"Processed {len(srt_files)} SRT files, {len(chapters_to_process)} chapters, "
                   f"{len(all_alignments)} alignments, quality: {quality_report.overall_score:.1f}"
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 数据摄入与对齐完成！")
        logger.info("=" * 60 + "\n")
    
    # ==================== SRT处理流程 ====================
    
    async def _process_srt_files(
        self,
        srt_files: List[str]
    ) -> Dict[str, List[Event]]:
        """
        处理SRT文件：SRT blocks → Sentences → Semantic Blocks → Events
        
        Returns:
            Dict[str, List[Event]]: {episode_name: [Event, ...], ...}
        """
        script_events_by_episode = {}
        
        for idx, srt_path in enumerate(srt_files, 1):
            filename = os.path.basename(srt_path)
            episode_name = os.path.splitext(filename)[0]
            logger.info(f"\n{'━'*60}")
            logger.info(f"📺 处理SRT [{idx}/{len(srt_files)}]: {filename}")
            logger.info(f"{'━'*60}")
            
            # 🔄 断点续传：检查是否已处理
            existing_file = os.path.join(
                self.paths['alignment'], 
                f"{episode_name}_script_events_v2_latest.json"
            )
            if os.path.exists(existing_file) and not self.force_reprocess:
                logger.info(f"  ♻️  发现已存在的结果，跳过处理")
                try:
                    with open(existing_file, 'r', encoding='utf-8') as f:
                        events_data = json.load(f)
                    events = [Event(**e) for e in events_data]
                    script_events_by_episode[episode_name] = events
                    logger.info(f"  ✅ 加载已有结果: {len(events)} events\n")
                    continue
                except Exception as e:
                    logger.warning(f"  ⚠️  加载已有结果失败: {e}，将重新处理")
                    pass
            
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            logger.info(f"📄 SRT文件大小: {len(srt_content)} 字符")
            
            # Step 2.1: 解析SRT blocks
            srt_blocks = self._parse_srt_blocks(srt_content)
            logger.info(f"  ✓ 解析SRT: {len(srt_blocks)} blocks")
            
            # Step 2.2: SRT blocks → Sentences
            sentences = await self.aligner.restore_sentences_from_srt_async(srt_blocks)
            logger.info(f"  ✓ 句子还原: {len(sentences)} 句子")
            
            # Step 2.3: Sentences → Semantic Blocks
            semantic_blocks = await self.aligner.segment_semantic_blocks_async(
                sentences,
                source_type="script",
                context_info=f"Episode: {episode_name}"
            )
            logger.info(f"  ✓ 意思块划分: {len(semantic_blocks)} blocks")
            
            # Step 2.4: Semantic Blocks → Events
            events = await self.aligner.aggregate_events_async(
                semantic_blocks,
                source_type="script",
                context_info=f"Episode: {episode_name}"
            )
            logger.info(f"  ✓ 事件聚合: {len(events)} events")
            
            # 为每个event设置episode
            for event in events:
                event.episode = episode_name
            
            script_events_by_episode[episode_name] = events
            
            # 💾 增量保存：立即保存Script Events
            artifact_manager.save_artifact(
                [e.model_dump() for e in events],
                f"{episode_name}_script_events_v2",
                self.project_id,
                self.paths['alignment']
            )
            logger.info(f"  💾 已保存: {episode_name}_script_events_v2.json")
            logger.info(f"  ✅ 完成: {episode_name} ({len(events)} events)\n")
        
        return script_events_by_episode
    
    def _parse_srt_blocks(self, srt_content: str) -> List[Dict]:
        """
        解析SRT内容为blocks
        
        Returns:
            List[Dict]: [{"index": 1, "start": "00:00:00,000", "end": "00:00:02,000", "text": "..."}, ...]
        """
        blocks = srt_content.strip().split('\n\n')
        srt_blocks = []
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                try:
                    index = int(lines[0])
                    time_parts = lines[1].split(' --> ')
                    start = time_parts[0]
                    end = time_parts[1]
                    text = " ".join(lines[2:])
                    
                    srt_blocks.append({
                        "index": index,
                        "start": start,
                        "end": end,
                        "text": text
                    })
                except:
                    continue
        
        return srt_blocks
    
    # ==================== Novel处理流程 ====================
    
    async def _process_novel_chapters(
        self,
        chapters: List[Tuple[str, str]]
    ) -> List[Event]:
        """
        处理Novel章节：Text → Sentences → Semantic Blocks → Events
        
        Returns:
            List[Event]: Novel的事件列表
        """
        all_novel_events = []
        
        # 🔄 断点续传：检查是否有已处理的Novel Events
        existing_novel_file = os.path.join(
            self.paths['alignment'], 
            "novel_events_v2_latest.json"
        )
        start_chapter_idx = 0
        
        if os.path.exists(existing_novel_file) and not self.force_reprocess:
            logger.info(f"\n♻️  发现已存在的Novel Events文件，尝试加载...")
            try:
                with open(existing_novel_file, 'r', encoding='utf-8') as f:
                    events_data = json.load(f)
                all_novel_events = [Event(**e) for e in events_data]
                
                # 计算已处理到第几章
                if all_novel_events:
                    max_chapter = max(
                        e.chapter_range[1] if e.chapter_range else 0 
                        for e in all_novel_events
                    )
                    start_chapter_idx = max_chapter
                    logger.info(f"  ✅ 加载已有结果: {len(all_novel_events)} events (已处理到第 {max_chapter} 章)")
                    logger.info(f"  🔄 将从第 {start_chapter_idx + 1} 章继续处理...\n")
            except Exception as e:
                logger.warning(f"  ⚠️  加载已有结果失败: {e}，将从头开始处理")
                all_novel_events = []
                start_chapter_idx = 0
        
        # 只处理剩余的章节
        remaining_chapters = chapters[start_chapter_idx:]
        if not remaining_chapters:
            logger.info(f"\n✅ 所有章节已处理完成，共 {len(all_novel_events)} 个事件")
            return all_novel_events
        
        logger.info(f"\n📚 处理剩余 {len(remaining_chapters)} 个章节 (共 {len(chapters)} 章)...")
        
        for i, (chapter_title, chapter_content) in enumerate(remaining_chapters):
            actual_chapter_num = start_chapter_idx + i + 1
            logger.info(f"\n{'━'*60}")
            logger.info(f"📖 处理章节 [{actual_chapter_num}/{len(chapters)}]: {chapter_title}")
            logger.info(f"{'━'*60}")
            logger.info(f"📄 章节内容长度: {len(chapter_content)} 字符")
            
            # Step 3.1: Text → Sentences
            sentences = self.aligner.restore_sentences_from_novel(
                chapter_content,
                chapter_title
            )
            logger.info(f"  ✓ 句子分割: {len(sentences)} 句子")
            
            # Step 3.2: Sentences → Semantic Blocks
            semantic_blocks = await self.aligner.segment_semantic_blocks_async(
                sentences,
                source_type="novel",
                context_info=f"Chapter: {chapter_title}"
            )
            logger.info(f"  ✓ 意思块划分: {len(semantic_blocks)} blocks")
            
            # Step 3.3: Semantic Blocks → Events
            events = await self.aligner.aggregate_events_async(
                semantic_blocks,
                source_type="novel",
                context_info=f"Chapter: {chapter_title}"
            )
            logger.info(f"  ✓ 事件聚合: {len(events)} events")
            
            # 为每个event设置chapter_range（使用实际章节编号）
            for event in events:
                event.chapter_range = (actual_chapter_num, actual_chapter_num)
            
            all_novel_events.extend(events)
            
            # 💾 增量保存：每处理完一章就保存当前所有Novel Events
            artifact_manager.save_artifact(
                [e.model_dump() for e in all_novel_events],
                "novel_events_v2",
                self.project_id,
                self.paths['alignment']
            )
            logger.info(f"  💾 已保存: novel_events_v2.json (累计 {len(all_novel_events)} events)")
            logger.info(f"  ✅ 完成: {chapter_title} (本章 {len(events)} events)\n")
        
        logger.info(f"\n✅ Novel处理完成: 共 {len(all_novel_events)} 个事件 (已处理 {len(chapters)} 章)")
        return all_novel_events
    
    # ==================== 辅助方法 ====================
    
    def _split_chapters(self, novel_text: str) -> List[Tuple[str, str]]:
        """
        分割小说章节
        
        Returns:
            List[Tuple[str, str]]: [(章节标题, 章节内容), ...]
        """
        chapters = re.split(r"(第[0-9]+章\s+[^\n]+)", novel_text)
        parts = chapters
        if parts and not re.match(r"(第[0-9]+章\s+[^\n]+)", parts[0]):
            parts = parts[1:]
        
        result = []
        for i in range(0, len(parts), 2):
            if i+1 < len(parts):
                title = parts[i].strip()
                content = parts[i+1].strip()
                result.append((title, content))
        
        return result
