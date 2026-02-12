import logging
from src.core.schemas_novel import NovelMetadata
from src.workflows.novel_processing.base import NovelProcessingWorkflowBase

logger = logging.getLogger(__name__)

async def step2_extract_metadata(
    workflow: NovelProcessingWorkflowBase,
    novel_path: str,
    processing_dir: str
) -> NovelMetadata:
    """Step 2: 提取小说元数据"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 Step 2: 提取小说元数据")
    logger.info("=" * 60)
    
    result = workflow.metadata_extractor.execute(novel_file=novel_path)
    workflow.llm_calls_count += 1  # metadata extraction uses 1 LLM call
    
    # 保存中间结果
    workflow._save_intermediate_result(result, "step2_metadata", processing_dir)
    
    logger.info(f"✅ 元数据提取完成")
    logger.info(f"   书名: {result.title}")
    logger.info(f"   作者: {result.author}")
    logger.info(f"   标签: {', '.join(result.tags)}")
    
    return result
