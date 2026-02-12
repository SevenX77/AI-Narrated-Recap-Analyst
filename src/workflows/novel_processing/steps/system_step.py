import logging
import asyncio
from typing import List, Dict, Tuple
from src.core.schemas_novel import (
    ChapterInfo,
    SystemCatalog,
    AnnotatedChapter,
    ParagraphSegmentationResult,
    SystemUpdateResult,
    SystemTrackingResult,
    NovelProcessingConfig
)
from src.workflows.novel_processing.base import NovelProcessingWorkflowBase

logger = logging.getLogger(__name__)

async def step6_analyze_system(
    workflow: NovelProcessingWorkflowBase,
    novel_path: str,
    chapters: List[ChapterInfo],
    processing_dir: str
) -> SystemCatalog:
    """Step 6: 全书系统元素分析"""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 Step 6: 全书系统元素分析")
    logger.info("=" * 60)
    
    # 分析前50章（或全部章节）
    analysis_chapters = min(50, len(chapters))
    logger.info(f"📊 分析前 {analysis_chapters} 章")
    
    result = workflow.system_analyzer.execute(
        novel_path=novel_path,  # 传递文件路径，不是内容
        max_chapters=analysis_chapters
    )
    
    workflow.llm_calls_count += 1
    workflow._save_intermediate_result(result, "step6_system_catalog", processing_dir)
    
    logger.info(f"✅ 系统分析完成: {len(result.categories)}个类别")
    return result

async def step7_track_system(
    workflow: NovelProcessingWorkflowBase,
    annotation_results: Dict[int, AnnotatedChapter],
    segmentation_results: Dict[int, ParagraphSegmentationResult],
    system_catalog: SystemCatalog,
    workflow_config: NovelProcessingConfig,
    processing_dir: str
) -> Dict[str, Dict]:
    """Step 7: 章节系统元素检测与追踪"""
    logger.info("\n" + "=" * 60)
    logger.info("🔬 Step 7: 章节系统元素检测与追踪")
    logger.info("=" * 60)
    
    system_updates = {}
    system_tracking = {}
    chapters = list(annotation_results.keys())
    
    if workflow_config.enable_parallel:
        # 并行处理
        logger.info(f"🔀 并行处理模式: 并发数={workflow_config.max_concurrent_chapters}")
        
        for i in range(0, len(chapters), workflow_config.max_concurrent_chapters):
            batch_chapters = chapters[i:i + workflow_config.max_concurrent_chapters]
            batch_results = await _process_system_tracking_batch(
                workflow,
                batch_chapters,
                annotation_results,
                segmentation_results,
                system_catalog,
                workflow_config,
                processing_dir
            )
            system_updates.update(batch_results["updates"])
            system_tracking.update(batch_results["tracking"])
    else:
        # 串行处理
        for chapter_num in chapters:
            try:
                update, tracking = await _track_single_chapter_system(
                    workflow,
                    chapter_num,
                    annotation_results[chapter_num],
                    segmentation_results[chapter_num],
                    system_catalog
                )
                system_updates[chapter_num] = update
                system_tracking[chapter_num] = tracking
                
                workflow._save_intermediate_result(
                    {"update": update, "tracking": tracking},
                    f"step7_system_tracking/chapter_{chapter_num:03d}",
                    processing_dir
                )
            except Exception as e:
                logger.error(f"❌ 章节{chapter_num}系统追踪失败: {e}")
                if not workflow_config.continue_on_error:
                    raise
    
    logger.info(f"✅ 系统追踪完成: {len(system_tracking)}/{len(chapters)} 章节")
    return {"updates": system_updates, "tracking": system_tracking}

async def _process_system_tracking_batch(
    workflow: NovelProcessingWorkflowBase,
    batch_chapters: List[int],
    annotation_results: Dict[int, AnnotatedChapter],
    segmentation_results: Dict[int, ParagraphSegmentationResult],
    system_catalog: SystemCatalog,
    workflow_config: NovelProcessingConfig,
    processing_dir: str
) -> Dict[str, Dict]:
    """并行处理一批章节的系统追踪"""
    tasks = [
        _track_single_chapter_system(
            workflow,
            chapter_num,
            annotation_results[chapter_num],
            segmentation_results[chapter_num],
            system_catalog
        )
        for chapter_num in batch_chapters
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    batch_updates = {}
    batch_tracking = {}
    
    for chapter_num, result in zip(batch_chapters, results):
        if isinstance(result, Exception):
            logger.error(f"❌ 章节{chapter_num}系统追踪失败: {result}")
            if not workflow_config.continue_on_error:
                raise result
        else:
            update, tracking = result
            batch_updates[chapter_num] = update
            batch_tracking[chapter_num] = tracking
            
            workflow._save_intermediate_result(
                {"update": update, "tracking": tracking},
                f"step7_system_tracking/chapter_{chapter_num:03d}",
                processing_dir
            )
    
    return {"updates": batch_updates, "tracking": batch_tracking}

async def _track_single_chapter_system(
    workflow: NovelProcessingWorkflowBase,
    chapter_num: int,
    annotated_chapter: AnnotatedChapter,
    segmentation_result: ParagraphSegmentationResult,
    system_catalog: SystemCatalog
) -> Tuple[SystemUpdateResult, SystemTrackingResult]:
    """追踪单个章节的系统元素"""
    logger.info(f"   处理章节 {chapter_num}")
    
    # 检测新系统元素（返回tuple: (update_result, updated_catalog)）
    detector_result = workflow.system_detector.execute(
        annotated_chapter=annotated_chapter,
        segmentation_result=segmentation_result,
        system_catalog=system_catalog
    )
    
    # 解包tuple
    if isinstance(detector_result, tuple):
        update_result, updated_catalog = detector_result
    else:
        # 如果不是tuple，假设只返回update_result
        update_result = detector_result
        updated_catalog = system_catalog
    
    # 追踪系统元素变化
    tracking_result = workflow.system_tracker.execute(
        annotated_chapter=annotated_chapter,
        system_catalog=system_catalog
    )
    
    workflow.llm_calls_count += 2  # detector + tracker
    
    logger.info(f"   ✅ 章节{chapter_num}: {len(update_result.new_elements)}个新元素, "
               f"{len(tracking_result.tracking_entries)}个追踪记录")
    
    return update_result, tracking_result
