import logging
import asyncio
from typing import List, Dict
from src.core.schemas_novel import (
    ParagraphSegmentationResult,
    AnnotatedChapter,
    NovelProcessingConfig
)
from src.workflows.novel_processing.base import NovelProcessingWorkflowBase

logger = logging.getLogger(__name__)

async def step5_annotate_chapters(
    workflow: NovelProcessingWorkflowBase,
    segmentation_results: Dict[int, ParagraphSegmentationResult],
    workflow_config: NovelProcessingConfig,
    processing_dir: str
) -> Dict[int, AnnotatedChapter]:
    """Step 5: 章节并行标注"""
    logger.info("\n" + "=" * 60)
    logger.info("🏷️ Step 5: 章节并行标注 (Three-Pass)")
    logger.info("=" * 60)
    
    annotation_results = {}
    chapters = list(segmentation_results.keys())
    
    if workflow_config.enable_parallel:
        # 并行处理
        logger.info(f"🔀 并行处理模式: 并发数={workflow_config.max_concurrent_chapters}")
        
        for i in range(0, len(chapters), workflow_config.max_concurrent_chapters):
            batch_chapters = chapters[i:i + workflow_config.max_concurrent_chapters]
            batch_results = await _process_annotation_batch(
                workflow,
                batch_chapters,
                segmentation_results,
                workflow_config,
                processing_dir
            )
            annotation_results.update(batch_results)
    else:
        # 串行处理
        logger.info("📝 串行处理模式")
        for chapter_num in chapters:
            try:
                result = await _annotate_single_chapter(
                    workflow,
                    chapter_num,
                    segmentation_results[chapter_num],
                    workflow_config
                )
                annotation_results[chapter_num] = result
                workflow._save_intermediate_result(
                    result,
                    f"step5_annotation/chapter_{chapter_num:03d}",
                    processing_dir
                )
            except Exception as e:
                logger.error(f"❌ 章节{chapter_num}标注失败: {e}")
                if not workflow_config.continue_on_error:
                    raise
    
    logger.info(f"✅ 标注完成: {len(annotation_results)}/{len(chapters)} 章节")
    return annotation_results

async def _process_annotation_batch(
    workflow: NovelProcessingWorkflowBase,
    batch_chapters: List[int],
    segmentation_results: Dict[int, ParagraphSegmentationResult],
    workflow_config: NovelProcessingConfig,
    processing_dir: str
) -> Dict[int, AnnotatedChapter]:
    """并行处理一批章节的标注"""
    tasks = [
        _annotate_single_chapter(
            workflow,
            chapter_num,
            segmentation_results[chapter_num],
            workflow_config
        )
        for chapter_num in batch_chapters
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    batch_results = {}
    for chapter_num, result in zip(batch_chapters, results):
        if isinstance(result, Exception):
            logger.error(f"❌ 章节{chapter_num}标注失败: {result}")
            if not workflow_config.continue_on_error:
                raise result
        else:
            batch_results[chapter_num] = result
            workflow._save_intermediate_result(
                result,
                f"step5_annotation/chapter_{chapter_num:03d}",
                processing_dir
            )
    
    return batch_results

async def _annotate_single_chapter(
    workflow: NovelProcessingWorkflowBase,
    chapter_num: int,
    segmentation_result: ParagraphSegmentationResult,
    workflow_config: NovelProcessingConfig
) -> AnnotatedChapter:
    """标注单个章节（使用LLM管理器）"""
    logger.info(f"   处理章节 {chapter_num}")
    
    # 估算token数（基于段落内容）
    total_chars = sum(len(p.content) for p in segmentation_result.paragraphs)
    estimated_tokens = workflow._estimate_tokens("x" * total_chars)
    
    # 使用LLM管理器调用（自动限流+重试）
    result = await workflow.llm_manager.call_with_rate_limit(
        func=workflow.novel_annotator.execute,
        provider=workflow_config.annotation_provider,
        model="claude-sonnet-4-5-20250929" if workflow_config.annotation_provider == "claude" else "deepseek-chat",
        estimated_tokens=estimated_tokens,
        segmentation_result=segmentation_result,
        enable_functional_tags=workflow_config.enable_functional_tags
    )
    
    # LLM calls: Pass1 + Pass2 + (optional Pass3)
    llm_calls = 3 if workflow_config.enable_functional_tags else 2
    workflow.llm_calls_count += llm_calls
    
    event_count = len(result.event_timeline.events)
    setting_count = len(result.setting_library.settings)
    logger.info(f"   ✅ 章节{chapter_num}: {event_count}个事件, {setting_count}个设定")
    
    return result
