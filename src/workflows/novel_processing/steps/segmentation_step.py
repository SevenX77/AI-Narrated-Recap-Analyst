import logging
import asyncio
from typing import List, Dict
from src.core.schemas_novel import (
    ChapterInfo,
    ParagraphSegmentationResult,
    NovelProcessingConfig
)
from src.workflows.novel_processing.base import NovelProcessingWorkflowBase

logger = logging.getLogger(__name__)

async def step4_segment_chapters(
    workflow: NovelProcessingWorkflowBase,
    novel_path: str,
    chapters: List[ChapterInfo],
    workflow_config: NovelProcessingConfig,
    processing_dir: str
) -> Dict[int, ParagraphSegmentationResult]:
    """Step 4: 章节并行分段"""
    logger.info("\n" + "=" * 60)
    logger.info("✂️ Step 4: 章节并行分段 (Two-Pass)")
    logger.info("=" * 60)
    
    # 读取小说内容
    with open(novel_path, 'r', encoding='utf-8') as f:
        novel_content = f.read()
    
    segmentation_results = {}
    
    if workflow_config.enable_parallel:
        # 并行处理
        logger.info(f"🔀 并行处理模式: 并发数={workflow_config.max_concurrent_chapters}")
        
        # 分批处理
        for i in range(0, len(chapters), workflow_config.max_concurrent_chapters):
            batch = chapters[i:i + workflow_config.max_concurrent_chapters]
            batch_results = await _process_segmentation_batch(
                workflow, batch, novel_content, workflow_config, processing_dir
            )
            segmentation_results.update(batch_results)
    else:
        # 串行处理
        logger.info("📝 串行处理模式")
        for chapter in chapters:
            try:
                result = await _segment_single_chapter(
                    workflow, chapter, novel_content, workflow_config
                )
                segmentation_results[chapter.number] = result
                workflow._save_intermediate_result(
                    result,
                    f"step4_segmentation/chapter_{chapter.number:03d}",
                    processing_dir
                )
            except Exception as e:
                logger.error(f"❌ 章节{chapter.number}分段失败: {e}")
                if not workflow_config.continue_on_error:
                    raise
    
    logger.info(f"✅ 分段完成: {len(segmentation_results)}/{len(chapters)} 章节")
    return segmentation_results

async def _process_segmentation_batch(
    workflow: NovelProcessingWorkflowBase,
    batch: List[ChapterInfo],
    novel_content: str,
    workflow_config: NovelProcessingConfig,
    processing_dir: str
) -> Dict[int, ParagraphSegmentationResult]:
    """并行处理一批章节的分段"""
    tasks = [
        _segment_single_chapter(workflow, chapter, novel_content, workflow_config)
        for chapter in batch
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    batch_results = {}
    for chapter, result in zip(batch, results):
        if isinstance(result, Exception):
            logger.error(f"❌ 章节{chapter.number}分段失败: {result}")
            if not workflow_config.continue_on_error:
                raise result
        else:
            batch_results[chapter.number] = result
            workflow._save_intermediate_result(
                result,
                f"step4_segmentation/chapter_{chapter.number:03d}",
                processing_dir
            )
    
    return batch_results

async def _segment_single_chapter(
    workflow: NovelProcessingWorkflowBase,
    chapter: ChapterInfo,
    novel_content: str,
    workflow_config: NovelProcessingConfig
) -> ParagraphSegmentationResult:
    """分段单个章节（使用LLM管理器）"""
    logger.info(f"   处理章节 {chapter.number}: {chapter.title}")
    
    # 提取章节内容
    lines = novel_content.split('\n')
    end_line = chapter.end_line if chapter.end_line is not None else len(lines)
    chapter_content = '\n'.join(lines[chapter.start_line:end_line])
    
    # 使用LLM管理器调用（自动限流+重试）
    seg_output = await workflow.llm_manager.call_with_rate_limit(
        func=workflow.novel_segmenter.execute,
        provider=workflow_config.segmentation_provider,
        model="claude-sonnet-4-5-20250929" if workflow_config.segmentation_provider == "claude" else "deepseek-chat",
        estimated_tokens=workflow._estimate_tokens(chapter_content),
        chapter_content=chapter_content,
        chapter_number=chapter.number,
        chapter_title=chapter.title
    )
    
    workflow.llm_calls_count += 2  # Two-Pass
    
    # 提取 json_result（ParagraphSegmentationResult）
    result = seg_output.json_result
    logger.info(f"   ✅ 章节{chapter.number}: {len(result.paragraphs)}个段落")
    
    return result
