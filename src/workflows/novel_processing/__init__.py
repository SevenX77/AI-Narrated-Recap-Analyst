import logging
import time
from pathlib import Path
from typing import Optional

from src.core.schemas_novel import (
    NovelProcessingConfig,
    NovelProcessingResult,
    ChapterProcessingError
)
from src.workflows import report_generator
from src.workflows.novel_processing.base import NovelProcessingWorkflowBase

# Import Steps
from src.workflows.novel_processing.steps.import_step import step1_import_novel
from src.workflows.novel_processing.steps.metadata_step import step2_extract_metadata
from src.workflows.novel_processing.steps.chapter_step import step3_detect_chapters
from src.workflows.novel_processing.steps.segmentation_step import step4_segment_chapters
from src.workflows.novel_processing.steps.annotation_step import step5_annotate_chapters
from src.workflows.novel_processing.steps.system_step import step6_analyze_system, step7_track_system
from src.workflows.novel_processing.steps.validation_step import step8_validate_quality

logger = logging.getLogger(__name__)

class NovelProcessingWorkflow(NovelProcessingWorkflowBase):
    """
    小说处理工作流
    
    完整的小说处理pipeline，支持并行处理、错误恢复和断点续传。
    
    Attributes:
        name (str): 工作流名称
        config (NovelProcessingConfig): 工作流配置
        project_name (str): 项目名称
        processing_dir (str): 中间结果保存目录
    """
    
    async def run(
        self,
        novel_path: str,
        project_name: str,
        config: Optional[NovelProcessingConfig] = None,
        resume_from_step: Optional[int] = None
    ) -> NovelProcessingResult:
        """
        执行完整的小说处理流程
        """
        self.start_time = time.time()
        workflow_config = config or NovelProcessingConfig()
        
        logger.info("=" * 80)
        logger.info(f"🚀 启动 NovelProcessingWorkflow")
        logger.info(f"📁 项目: {project_name}")
        logger.info(f"📖 小说: {novel_path}")
        logger.info(f"⚙️  配置: 并行={workflow_config.enable_parallel}, "
                   f"并发数={workflow_config.max_concurrent_chapters}, "
                   f"章节范围={workflow_config.chapter_range}")
        logger.info("=" * 80)
        
        # 创建处理目录
        processing_dir = self._setup_processing_directory(project_name)
        
        # 初始化结果对象
        result = NovelProcessingResult(
            project_name=project_name,
            import_result=None,  # 将在后续步骤填充
            metadata=None,
            chapters=[],
            intermediate_results_dir=processing_dir
        )
        
        try:
            # Step 1: 小说导入与规范化
            if not resume_from_step or resume_from_step <= 1:
                result.import_result = await step1_import_novel(
                    self, novel_path, project_name, processing_dir
                )
                result.completed_steps.append(1)
                if workflow_config.output_markdown_reports:
                    report_generator.output_step1_report(result.import_result, processing_dir)
            
            # Step 2: 提取小说元数据
            if not resume_from_step or resume_from_step <= 2:
                result.metadata = await step2_extract_metadata(
                    self, result.import_result.saved_path, processing_dir
                )
                result.completed_steps.append(2)
                
                # 生成元数据Markdown到novel文件夹
                report_generator.generate_metadata_markdown(result.metadata, project_name)
                
                if workflow_config.output_markdown_reports:
                    report_generator.output_step2_report(result.metadata, processing_dir)
            
            # Step 3: 检测章节边界
            if not resume_from_step or resume_from_step <= 3:
                result.chapters = await step3_detect_chapters(
                    self,
                    result.import_result.saved_path, 
                    workflow_config.chapter_range,
                    processing_dir
                )
                result.completed_steps.append(3)
                
                # 生成章节索引Markdown到novel文件夹
                report_generator.generate_chapters_index_markdown(result.chapters, project_name)
                
                if workflow_config.output_markdown_reports:
                    report_generator.output_step3_report(result.chapters, processing_dir)
            
            # Step 4: 章节并行分段
            if not resume_from_step or resume_from_step <= 4:
                result.segmentation_results = await step4_segment_chapters(
                    self,
                    result.import_result.saved_path,
                    result.chapters,
                    workflow_config,
                    processing_dir
                )
                result.completed_steps.append(4)
                
                # 生成每章分段Markdown到novel文件夹
                report_generator.generate_chapter_markdown(
                    result.segmentation_results,
                    result.chapters,
                    project_name
                )
                
                if workflow_config.output_markdown_reports:
                    report_generator.output_step4_report(result.segmentation_results, processing_dir)
            
            # Step 5: 章节并行标注
            if not resume_from_step or resume_from_step <= 5:
                result.annotation_results = await step5_annotate_chapters(
                    self,
                    result.segmentation_results,
                    workflow_config,
                    processing_dir
                )
                result.completed_steps.append(5)
                if workflow_config.output_markdown_reports:
                    report_generator.output_step5_report(result.annotation_results, processing_dir)
            
            # Step 6-7: 系统分析与追踪（可选）
            if workflow_config.enable_system_analysis:
                if not resume_from_step or resume_from_step <= 6:
                    result.system_catalog = await step6_analyze_system(
                        self,
                        result.import_result.saved_path,
                        result.chapters,
                        processing_dir
                    )
                    result.completed_steps.append(6)
                
                if not resume_from_step or resume_from_step <= 7:
                    system_results = await step7_track_system(
                        self,
                        result.annotation_results,
                        result.segmentation_results,
                        result.system_catalog,
                        workflow_config,
                        processing_dir
                    )
                    result.system_updates = system_results["updates"]
                    result.system_tracking = system_results["tracking"]
                    result.completed_steps.append(7)
                    
                    if workflow_config.output_markdown_reports:
                        report_generator.output_step67_report(
                            result.system_catalog,
                            result.system_updates,
                            result.system_tracking,
                            processing_dir
                        )
            
            # Step 8: 质量验证
            if not resume_from_step or resume_from_step <= 8:
                result.validation_report = await step8_validate_quality(
                    self,
                    result,
                    processing_dir
                )
                result.completed_steps.append(8)
                if workflow_config.output_markdown_reports:
                    report_generator.output_step8_report(result.validation_report, processing_dir)
            
            # 计算统计信息
            result.processing_time = time.time() - self.start_time
            result.llm_calls_count = self.llm_calls_count
            result.total_cost = self.total_cost
            result.processing_stats = self._calculate_stats(result)
            
            # 保存最终结果
            self._save_final_result(result, processing_dir)
            
            # 生成完整的HTML可视化
            novel_title = result.metadata.title if result.metadata else Path(novel_path).stem
            report_generator.generate_comprehensive_html(result, project_name, novel_title)
            
            # 输出LLM使用统计
            llm_stats = self.llm_manager.get_all_stats()
            if llm_stats:
                logger.info("\n📊 LLM使用统计:")
                for model, stats in llm_stats.items():
                    logger.info(f"  {model}:")
                    logger.info(f"    - 请求数(最近1分钟): {stats['requests_last_minute']}")
                    logger.info(f"    - Tokens(最近1分钟): {stats['tokens_last_minute']}")
            
            logger.info("=" * 80)
            logger.info(f"✅ NovelProcessingWorkflow 执行完成")
            logger.info(f"⏱️  总耗时: {result.processing_time:.1f}秒 ({result.processing_time/60:.1f}分钟)")
            logger.info(f"📊 LLM调用: {result.llm_calls_count}次")
            logger.info(f"💰 总成本: ${result.total_cost:.4f}")
            logger.info(f"📈 成功处理: {len(result.segmentation_results)}/{len(result.chapters)} 章节")
            if result.errors:
                logger.warning(f"⚠️  错误数量: {len(result.errors)}")
            logger.info("=" * 80)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Workflow执行失败: {e}", exc_info=True)
            result.errors.append(ChapterProcessingError(
                chapter_number=0,
                step="workflow",
                error_type=type(e).__name__,
                error_message=str(e)
            ))
            # 保存错误状态
            self._save_final_result(result, processing_dir)
            raise
