import os
import re
import json
import asyncio
from typing import List, Dict, Tuple
from src.core.interfaces import BaseWorkflow
from src.core.project_manager import project_manager
from src.core.artifact_manager import artifact_manager
from src.core.config import config
from src.agents.deepseek_analyst import DeepSeekAnalyst, get_llm_client
from src.modules.alignment.deepseek_alignment_engine import DeepSeekAlignmentEngine
from src.utils.logger import logger, op_logger

class IngestionWorkflow(BaseWorkflow):
    """
    Workflow 1: Ingestion & Alignment (动态章节提取)
    
    实现策略：
    1. 根据SRT数量预估初始章节数
    2. 批量提取并评估对齐质量
    3. 根据覆盖率和质量动态决定是否继续提取
    4. 最后添加安全缓冲，防止遗漏更好的匹配
    """
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.paths = project_manager.get_project_paths(project_id)
        self.client = get_llm_client()
        self.analyst = DeepSeekAnalyst(self.client)
        self.aligner = DeepSeekAlignmentEngine(self.client)
        self.cfg = config.ingestion

    async def run(self, **kwargs):
        """
        执行数据摄入与对齐流程
        
        Args:
            **kwargs: 可选参数
                - max_chapters: 强制指定最大章节数（覆盖动态策略）
        """
        logger.info(f"🚀 启动数据摄入与对齐流程: {self.project_id}")
        
        novel_path = os.path.join(self.paths['raw'], "novel.txt")
        if not os.path.exists(novel_path):
            logger.error(f"Novel file not found: {novel_path}")
            return

        # 1. 读取小说并分章
        logger.info("1. 读取小说内容...")
        with open(novel_path, 'r', encoding='utf-8') as f:
            novel_text = f.read()
        
        all_chapters = self._split_chapters(novel_text)
        logger.info(f"   - 小说共 {len(all_chapters)} 章")
        
        # 2. 获取SRT文件列表
        import glob
        srt_files = sorted(glob.glob(os.path.join(self.paths['raw'], "*.srt")))
        logger.info(f"   - 找到 {len(srt_files)} 个SRT文件")
        
        if not srt_files:
            logger.error("未找到SRT文件")
            return
        
        # 3. 解析所有SRT事件（一次性完成）
        logger.info("2. 解析解说字幕...")
        all_srt_events = await self._parse_all_srt_files(srt_files)
        
        # 4. 动态章节提取与对齐
        logger.info("3. 动态章节提取与对齐...")
        
        # 检查是否有强制指定的最大章节数
        forced_max_chapters = kwargs.get('max_chapters')
        
        if forced_max_chapters:
            logger.info(f"   - 使用强制指定的章节数: {forced_max_chapters}")
            novel_events_db = await self._extract_chapters(
                all_chapters[:forced_max_chapters]
            )
        else:
            novel_events_db = await self._adaptive_chapter_extraction(
                all_chapters,
                all_srt_events,
                len(srt_files)
            )
        
        # 5. 保存结果
        logger.info("4. 保存数据...")
        
        # Save Novel Events
        artifact_manager.save_artifact(
            novel_events_db,
            "novel_events",
            self.project_id,
            self.paths['alignment']
        )
        
        # Save Script Events (per episode)
        for episode_name, srt_events_data in all_srt_events.items():
            artifact_manager.save_artifact(
                srt_events_data,
                f"{episode_name}_script_events",
                self.project_id,
                self.paths['alignment']
            )
        
        # Final alignment with all extracted chapters
        logger.info("5. 执行最终对齐...")
        final_alignment = await self._align_all_episodes(
            novel_events_db,
            all_srt_events
        )
        
        # Save Alignment
        alignment_path = artifact_manager.save_artifact(
            [item.model_dump() for item in final_alignment],
            "alignment",
            self.project_id,
            self.paths['alignment']
        )
        
        # Evaluate final quality
        quality_report = self.aligner.evaluate_alignment_quality(
            final_alignment,
            self.cfg.quality_threshold
        )
        
        logger.info("\n" + "="*60)
        logger.info("📊 最终对齐质量报告")
        logger.info("="*60)
        logger.info(f"   综合得分: {quality_report.overall_score:.2f}/100")
        logger.info(f"   平均置信度: {quality_report.avg_confidence:.2%}")
        logger.info(f"   整体覆盖率: {quality_report.coverage_ratio:.2%}")
        logger.info(f"   章节连续性: {quality_report.continuity_score:.2%}")
        logger.info(f"   是否合格: {'✅ 是' if quality_report.is_qualified else '❌ 否'}")
        logger.info("\n   各集覆盖情况:")
        for ep_cov in quality_report.episode_coverage:
            logger.info(f"     - {ep_cov.episode_name}: "
                       f"{ep_cov.matched_events}/{ep_cov.total_events} "
                       f"({ep_cov.coverage_ratio:.1%}) "
                       f"[{ep_cov.min_matched_chapter} - {ep_cov.max_matched_chapter}]")
        logger.info("="*60 + "\n")
        
        # Save quality report
        quality_report_path = artifact_manager.save_artifact(
            quality_report.model_dump(),
            "alignment_quality_report",
            self.project_id,
            self.paths['alignment']
        )
        
        # Log operation
        output_files = [alignment_path, quality_report_path]
        op_logger.log_operation(
            project_id=self.project_id,
            action="Ingestion & Alignment (Adaptive)",
            output_files=output_files,
            details=f"Processed {len(srt_files)} SRT files, extracted {len(novel_events_db)} chapters, quality score: {quality_report.overall_score:.1f}"
        )
        
        logger.info("✅ 数据摄入与对齐完成！")

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

    async def _parse_all_srt_files(self, srt_files: List[str]) -> Dict[str, List[Dict]]:
        """
        解析所有SRT文件，提取事件流
        
        Returns:
            Dict[str, List[Dict]]: {episode_name: srt_events_data, ...}
        """
        all_srt_events = {}
        
        for srt_path in srt_files:
            filename = os.path.basename(srt_path)
            episode_name = os.path.splitext(filename)[0]
            logger.info(f"   - 解析: {filename}")
            
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # Parse SRT into chunks
            srt_chunks = self._parse_srt_content(srt_content)
            
            # Extract events concurrently
            if self.cfg.enable_concurrent:
                srt_events_data = await self._extract_srt_chunks_concurrent(
                    srt_chunks, filename
                )
            else:
                srt_events_data = []
                for chunk in srt_chunks:
                    events = self.analyst.extract_events(
                        chunk['content'], 
                        f"{filename} {chunk['time']}"
                    )
                    srt_events_data.append({
                        "time": chunk['time'], 
                        "events": [e.model_dump() for e in events]
                    })
            
            all_srt_events[episode_name] = srt_events_data
        
        return all_srt_events

    def _parse_srt_content(self, srt_content: str) -> List[Dict]:
        """
        解析SRT内容为chunks
        
        Returns:
            List[Dict]: [{"time": "00:00:12", "content": "..."}, ...]
        """
        blocks = srt_content.strip().split('\n\n')
        srt_chunks = []
        current_text = []
        start_time = ""
        
        for i, block in enumerate(blocks):
            lines = block.split('\n')
            if len(lines) >= 3:
                if not start_time:
                    start_time = lines[1].split(' --> ')[0]
                current_text.append(" ".join(lines[2:]))
                if (i+1) % 10 == 0:
                    srt_chunks.append({
                        "time": start_time, 
                        "content": " ".join(current_text)
                    })
                    current_text = []
                    start_time = ""
        
        if current_text:
            srt_chunks.append({
                "time": start_time, 
                "content": " ".join(current_text)
            })
        
        return srt_chunks

    async def _adaptive_chapter_extraction(
        self,
        all_chapters: List[Tuple[str, str]],
        all_srt_events: Dict[str, List[Dict]],
        srt_count: int
    ) -> List[Dict]:
        """
        动态适应式章节提取
        
        策略：
        1. 初始提取 srt_count * multiplier 章
        2. 对齐并评估质量
        3. 如果覆盖率不足，继续提取
        4. 如果质量合格，再提取安全缓冲
        
        Returns:
            List[Dict]: novel_events_db
        """
        # 计算初始章节数
        initial_chapters = min(
            srt_count * self.cfg.initial_chapter_multiplier,
            len(all_chapters)
        )
        
        logger.info(f"   - 初始策略: 提取前 {initial_chapters} 章 "
                   f"(SRT数 {srt_count} × 倍数 {self.cfg.initial_chapter_multiplier})")
        
        extracted_chapters = []
        current_index = 0
        iteration = 1
        
        while current_index < len(all_chapters):
            # 确定本批次提取的章节范围
            if iteration == 1:
                batch_end = initial_chapters
            else:
                batch_end = min(
                    current_index + self.cfg.batch_size,
                    len(all_chapters)
                )
            
            # 提取本批次章节
            batch_chapters = all_chapters[current_index:batch_end]
            logger.info(f"\n   📖 第 {iteration} 轮提取: 章节 {current_index+1}-{batch_end}")
            
            batch_events = await self._extract_chapters(batch_chapters)
            extracted_chapters.extend(batch_events)
            
            # 对齐并评估
            logger.info(f"   🔗 执行对齐评估...")
            alignment = await self._align_all_episodes(
                extracted_chapters,
                all_srt_events
            )
            
            quality_report = self.aligner.evaluate_alignment_quality(
                alignment,
                self.cfg.quality_threshold
            )
            
            logger.info(f"   📊 质量评估:")
            logger.info(f"      - 综合得分: {quality_report.overall_score:.1f}/100")
            logger.info(f"      - 覆盖率: {quality_report.coverage_ratio:.1%}")
            logger.info(f"      - 是否合格: {'✅' if quality_report.is_qualified else '❌'}")
            logger.info(f"      - 需要更多章节: {'是' if quality_report.needs_more_chapters else '否'}")
            
            # 判断是否继续
            if not quality_report.needs_more_chapters:
                # 质量合格且覆盖充分，添加安全缓冲后退出
                logger.info(f"\n   ✅ 对齐质量合格，添加安全缓冲...")
                
                buffer_start = batch_end
                buffer_end = min(
                    buffer_start + self.cfg.safety_buffer_chapters,
                    len(all_chapters)
                )
                
                if buffer_start < len(all_chapters):
                    logger.info(f"   📖 安全缓冲: 章节 {buffer_start+1}-{buffer_end}")
                    buffer_chapters = all_chapters[buffer_start:buffer_end]
                    buffer_events = await self._extract_chapters(buffer_chapters)
                    extracted_chapters.extend(buffer_events)
                
                break
            
            # 更新索引，继续下一轮
            current_index = batch_end
            iteration += 1
            
            if current_index >= len(all_chapters):
                logger.info(f"\n   ⚠️  已提取所有章节，但质量仍未达标")
                break
        
        logger.info(f"\n   ✅ 章节提取完成: 共提取 {len(extracted_chapters)} 章")
        return extracted_chapters

    async def _extract_chapters(
        self,
        chapters: List[Tuple[str, str]]
    ) -> List[Dict]:
        """
        并发提取章节事件
        
        使用 asyncio.Semaphore 限制并发数，避免 API rate limit。
        
        Args:
            chapters: [(title, content), ...]
            
        Returns:
            List[Dict]: [{"id": title, "events": [...]}, ...]
        """
        if not self.cfg.enable_concurrent or len(chapters) == 1:
            # 单章节或禁用并发时使用串行
            novel_events = []
            for title, content in chapters:
                logger.info(f"      - 分析: {title}")
                events = self.analyst.extract_events(content, title)
                novel_events.append({
                    "id": title,
                    "events": [e.model_dump() for e in events]
                })
            return novel_events
        
        # 并发提取
        logger.info(f"      - 并发分析 {len(chapters)} 章 (最大并发: {self.cfg.max_concurrent_requests})")
        
        semaphore = asyncio.Semaphore(self.cfg.max_concurrent_requests)
        
        async def extract_with_limit(title: str, content: str) -> Tuple[str, List]:
            async with semaphore:
                logger.info(f"        → 开始: {title}")
                events = await self.analyst.extract_events_async(content, title)
                logger.info(f"        ✓ 完成: {title}")
                return (title, events)
        
        # 创建所有任务
        tasks = [extract_with_limit(title, content) for title, content in chapters]
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        novel_events = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                title = chapters[i][0]
                logger.error(f"      ✗ 提取失败: {title} - {result}")
                # 添加空事件列表
                novel_events.append({"id": title, "events": []})
            else:
                title, events = result
                novel_events.append({
                    "id": title,
                    "events": [e.model_dump() for e in events]
                })
        
        return novel_events
    
    async def _extract_srt_chunks_concurrent(
        self,
        srt_chunks: List[Dict],
        filename: str
    ) -> List[Dict]:
        """
        并发提取SRT chunks的事件
        
        Args:
            srt_chunks: [{"time": "00:00:12", "content": "..."}, ...]
            filename: SRT文件名
            
        Returns:
            List[Dict]: [{"time": "...", "events": [...]}, ...]
        """
        if len(srt_chunks) == 1:
            # 单chunk时直接调用
            chunk = srt_chunks[0]
            events = self.analyst.extract_events(
                chunk['content'],
                f"{filename} {chunk['time']}"
            )
            return [{"time": chunk['time'], "events": [e.model_dump() for e in events]}]
        
        semaphore = asyncio.Semaphore(self.cfg.max_concurrent_requests)
        
        async def extract_chunk_with_limit(chunk: Dict) -> Tuple[str, List]:
            async with semaphore:
                events = await self.analyst.extract_events_async(
                    chunk['content'],
                    f"{filename} {chunk['time']}"
                )
                return (chunk['time'], events)
        
        # 并发执行
        tasks = [extract_chunk_with_limit(chunk) for chunk in srt_chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        srt_events_data = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"      ✗ SRT chunk提取失败: {srt_chunks[i]['time']} - {result}")
                srt_events_data.append({
                    "time": srt_chunks[i]['time'],
                    "events": []
                })
            else:
                time_point, events = result
                srt_events_data.append({
                    "time": time_point,
                    "events": [e.model_dump() for e in events]
                })
        
        return srt_events_data

    async def _align_all_episodes(
        self,
        novel_events_db: List[Dict],
        all_srt_events: Dict[str, List[Dict]]
    ) -> List:
        """
        对所有episode执行对齐
        
        Returns:
            List[AlignmentItem]
        """
        all_alignment_results = []
        
        for episode_name, srt_events_data in all_srt_events.items():
            alignment = self.aligner.align_script_with_novel(
                novel_events_db,
                srt_events_data
            )
            all_alignment_results.extend(alignment)
        
        return all_alignment_results
