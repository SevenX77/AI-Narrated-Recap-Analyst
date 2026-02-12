import logging
from src.core.schemas_novel import (
    NovelProcessingResult,
    NovelValidationReport
)
from src.workflows.novel_processing.base import NovelProcessingWorkflowBase

logger = logging.getLogger(__name__)

async def step8_validate_quality(
    workflow: NovelProcessingWorkflowBase,
    result: NovelProcessingResult,
    processing_dir: str
) -> NovelValidationReport:
    """Step 8: 质量验证"""
    logger.info("\n" + "=" * 60)
    logger.info("✅ Step 8: 质量验证")
    logger.info("=" * 60)
    
    validation_report = workflow.novel_validator.execute(
        import_result=result.import_result,
        chapter_infos=result.chapters,
        segmentation_results=list(result.segmentation_results.values()),
        annotation_results=list(result.annotation_results.values())
    )
    
    workflow._save_intermediate_result(
        validation_report,
        "step8_validation_report",
        processing_dir
    )
    
    logger.info(f"✅ 质量验证完成: 评分 {validation_report.quality_score}/100")
    if validation_report.issues:
        logger.warning(f"⚠️  发现 {len(validation_report.issues)} 个问题")
    
    return validation_report
