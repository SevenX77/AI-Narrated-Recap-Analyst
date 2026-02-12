import logging
from src.core.schemas_novel import NovelImportResult
from src.workflows.novel_processing.base import NovelProcessingWorkflowBase

logger = logging.getLogger(__name__)

async def step1_import_novel(
    workflow: NovelProcessingWorkflowBase,
    novel_path: str,
    project_name: str,
    processing_dir: str
) -> NovelImportResult:
    """Step 1: 小说导入与规范化"""
    logger.info("\n" + "=" * 60)
    logger.info("📥 Step 1: 小说导入与规范化")
    logger.info("=" * 60)
    
    result = workflow.novel_importer.execute(
        source_file=novel_path,
        project_name=project_name
    )
    
    # 保存中间结果
    workflow._save_intermediate_result(result, "step1_import", processing_dir)
    
    logger.info(f"✅ 导入完成: {result.char_count}字符, {result.line_count}行")
    logger.info(f"📁 保存位置: {result.saved_path}")
    
    return result
