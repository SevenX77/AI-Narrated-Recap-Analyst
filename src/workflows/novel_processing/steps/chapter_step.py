import logging
from typing import List, Optional
from src.core.schemas_novel import ChapterInfo
from src.workflows.novel_processing.base import NovelProcessingWorkflowBase

logger = logging.getLogger(__name__)

async def step3_detect_chapters(
    workflow: NovelProcessingWorkflowBase,
    novel_path: str,
    chapter_range: Optional[tuple],
    processing_dir: str
) -> List[ChapterInfo]:
    """Step 3: 检测章节边界"""
    logger.info("\n" + "=" * 60)
    logger.info("📖 Step 3: 检测章节边界")
    logger.info("=" * 60)
    
    all_chapters = workflow.chapter_detector.execute(novel_file=novel_path)
    
    # 应用章节范围过滤
    if chapter_range:
        start, end = chapter_range
        chapters = [ch for ch in all_chapters if start <= ch.number <= end]
        logger.info(f"📌 应用章节范围过滤: {start}-{end}")
    else:
        chapters = all_chapters
    
    # 保存中间结果
    workflow._save_intermediate_result(
        {"all_chapters": len(all_chapters), "filtered_chapters": chapters},
        "step3_chapters",
        processing_dir
    )
    
    logger.info(f"✅ 章节检测完成: 共{len(all_chapters)}章, 处理{len(chapters)}章")
    
    return chapters
