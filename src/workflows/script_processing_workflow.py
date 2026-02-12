"""
ScriptProcessingWorkflow - 脚本处理工作流

从原始SRT文件到完整的脚本分段数据，建立结构化的脚本知识库。

Workflow Steps:
    1. SRT导入与规范化
    2. 文本提取与智能修复
    3. Hook边界检测（仅ep01）
    4. Hook内容分析（可选）
    5. 脚本语义分段（ABC分类）
    6. 质量验证与报告生成

Author: AI-Narrated Recap Analyst Team
Created: 2026-02-10
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from src.core.interfaces import BaseWorkflow
from src.core.schemas_script import (
    ScriptProcessingConfig,
    ScriptProcessingResult,
    ScriptProcessingError,
    SrtImportResult,
    SrtEntry,
    SrtTextExtractionResult,
    HookDetectionResult,
    HookAnalysisResult,
    ScriptSegmentationResult,
    ScriptValidationReport
)
from src.tools.srt_importer import SrtImporter
from src.tools.srt_text_extractor import SrtTextExtractor
from src.tools.hook_detector import HookDetector
from src.tools.hook_content_analyzer import HookContentAnalyzer
from src.tools.script_segmenter import ScriptSegmenter
from src.tools.script_validator import ScriptValidator
from src.core.llm_rate_limiter import get_llm_manager

# Configure logging
logger = logging.getLogger(__name__)


class ScriptProcessingWorkflow(BaseWorkflow):
    """
    脚本处理工作流
    
    完整的SRT脚本处理pipeline，支持Hook检测、ABC分类和质量验证。
    
    Attributes:
        name (str): 工作流名称
        config (ScriptProcessingConfig): 工作流配置
        project_name (str): 项目名称
        episode_name (str): 集数名称
    
    Example:
        ```python
        workflow = ScriptProcessingWorkflow()
        result = await workflow.run(
            srt_path="path/to/ep01.srt",
            project_name="天命桃花_test",
            episode_name="ep01",
            config=ScriptProcessingConfig(
                enable_hook_detection=True,
                enable_abc_classification=True
            )
        )
        ```
    """
    
    name: str = "script_processing_workflow"
    
    def __init__(self):
        """初始化工作流"""
        super().__init__()
        
        # 初始化工具
        self.srt_importer = SrtImporter()
        self.text_extractor = SrtTextExtractor()
        self.hook_detector = HookDetector()
        self.hook_analyzer = HookContentAnalyzer()
        self.script_segmenter = ScriptSegmenter()
        self.script_validator = ScriptValidator()
        
        # 初始化LLM调用管理器
        self.llm_manager = get_llm_manager()
        
        # 统计信息
        self.llm_calls_count = 0
        self.total_cost = 0.0
        self.start_time = 0.0
        
        logger.info(f"✅ {self.name} 初始化完成")
    
    async def run(
        self,
        srt_path: str,
        project_name: str,
        episode_name: str,
        config: Optional[ScriptProcessingConfig] = None,
        novel_reference: Optional[str] = None,
        novel_intro: Optional[str] = None,
        novel_metadata: Optional[Dict[str, Any]] = None
    ) -> ScriptProcessingResult:
        """
        执行完整的脚本处理流程
        
        Args:
            srt_path: SRT文件路径
            project_name: 项目名称
            episode_name: 集数名称（如 "ep01"）
            config: 工作流配置（如不提供则使用默认配置）
            novel_reference: Novel文本参考（用于实体标准化，可选）
            novel_intro: Novel简介（用于Hook检测，可选）
            novel_metadata: Novel元数据（用于Hook分析，可选）
        
        Returns:
            ScriptProcessingResult: 完整的处理结果
        """
        logger.debug("run: 进入run方法")
        
        # 初始化配置
        if config is None:
            config = ScriptProcessingConfig()
        
        logger.debug("run: 配置初始化完成")
        
        # 记录开始时间
        self.start_time = time.time()
        
        # 初始化结果对象
        result = ScriptProcessingResult(
            project_name=project_name,
            episode_name=episode_name,
            config_used=config.model_dump()
        )
        
        logger.debug("run: 结果对象初始化完成")
        
        logger.info("=" * 80)
        logger.info(f"🚀 开始脚本处理工作流: {project_name} - {episode_name}")
        logger.info("=" * 80)
        
        logger.debug("run: 即将进入Phase 1")
        
        try:
            # ============================================================
            # Phase 1: SRT导入与规范化
            # ============================================================
            logger.info("\n" + "=" * 80)
            logger.info("Phase 1: SRT导入与规范化")
            logger.info("=" * 80)
            
            import_result = await self._phase1_srt_import(
                srt_path=srt_path,
                project_name=project_name,
                episode_name=episode_name
            )
            result.import_result = import_result
            
            if not import_result:
                raise ValueError("SRT导入失败")
            
            logger.info(f"✅ Phase 1 完成: 导入 {import_result.entry_count} 条SRT条目")
            logger.debug("Phase 1 完成，即将进入Phase 2")
            
            # ============================================================
            # Phase 2: 文本提取与智能修复
            # ============================================================
            logger.info("\n" + "=" * 80)
            logger.info("Phase 2: 文本提取与智能修复")
            logger.info("=" * 80)
            logger.debug("Phase 2: 即将调用_phase2_text_extraction")
            
            extraction_result = await self._phase2_text_extraction(
                srt_entries=import_result.entries,
                project_name=project_name,
                episode_name=episode_name,
                novel_reference=novel_reference,
                config=config
            )
            result.extraction_result = extraction_result
            
            if not extraction_result:
                raise ValueError("文本提取失败")
            
            logger.info(f"✅ Phase 2 完成: 提取 {extraction_result.processed_chars} 字符")
            
            # ============================================================
            # Phase 3: Hook边界检测（仅ep01）
            # ============================================================
            hook_detection_result = None
            if config.enable_hook_detection and episode_name.lower() == "ep01":
                logger.info("\n" + "=" * 80)
                logger.info("Phase 3: Hook边界检测")
                logger.info("=" * 80)
                
                # 先分段，然后检测Hook
                # 这里需要先做一次初步分段
                temp_segmentation = await self._temp_segmentation_for_hook(
                    extracted_text=extraction_result.processed_text,
                    srt_entries=import_result.entries,
                    config=config
                )
                
                hook_detection_result = await self._phase3_hook_detection(
                    segmented_script=temp_segmentation,
                    novel_intro=novel_intro,
                    config=config
                )
                result.hook_detection_result = hook_detection_result
                
                if hook_detection_result:
                    logger.info(f"✅ Phase 3 完成: Hook检测 - has_hook={hook_detection_result.has_hook}, confidence={hook_detection_result.confidence:.2f}")
                else:
                    logger.warning("⚠️ Phase 3: Hook检测失败，但继续处理")
            else:
                logger.info("\n" + "=" * 80)
                logger.info("Phase 3: Hook边界检测（已跳过）")
                if not config.enable_hook_detection:
                    logger.info("原因: 配置中禁用了Hook检测")
                else:
                    logger.info(f"原因: 非ep01集数（当前: {episode_name}）")
                logger.info("=" * 80)
            
            # ============================================================
            # Phase 4: Hook内容分析（可选）
            # ============================================================
            hook_analysis_result = None
            if (config.enable_hook_analysis and 
                hook_detection_result and 
                hook_detection_result.has_hook and 
                novel_intro and 
                novel_metadata):
                
                logger.info("\n" + "=" * 80)
                logger.info("Phase 4: Hook内容分析")
                logger.info("=" * 80)
                
                hook_analysis_result = await self._phase4_hook_analysis(
                    hook_detection_result=hook_detection_result,
                    segmented_script=temp_segmentation,
                    novel_intro=novel_intro,
                    novel_metadata=novel_metadata,
                    config=config
                )
                result.hook_analysis_result = hook_analysis_result
                
                if hook_analysis_result:
                    logger.info(f"✅ Phase 4 完成: 来源={hook_analysis_result.source_type}, 相似度={hook_analysis_result.similarity_score:.2f}")
                else:
                    logger.warning("⚠️ Phase 4: Hook内容分析失败，但继续处理")
            else:
                logger.info("\n" + "=" * 80)
                logger.info("Phase 4: Hook内容分析（已跳过）")
                if not config.enable_hook_analysis:
                    logger.info("原因: 配置中禁用了Hook分析")
                elif not hook_detection_result or not hook_detection_result.has_hook:
                    logger.info("原因: 未检测到Hook")
                elif not novel_intro or not novel_metadata:
                    logger.info("原因: 缺少Novel参考数据")
                logger.info("=" * 80)
            
            # ============================================================
            # Phase 5: 脚本语义分段（ABC分类）
            # ============================================================
            logger.info("\n" + "=" * 80)
            logger.info("Phase 5: 脚本语义分段（ABC分类）")
            logger.info("=" * 80)
            
            segmentation_result = await self._phase5_script_segmentation(
                extracted_text=extraction_result.processed_text,
                srt_entries=import_result.entries,
                project_name=project_name,
                episode_name=episode_name,
                config=config
            )
            result.segmentation_result = segmentation_result
            
            if not segmentation_result:
                raise ValueError("脚本分段失败")
            
            logger.info(f"✅ Phase 5 完成: 分成 {segmentation_result.total_segments} 个段落")
            
            # ============================================================
            # Phase 6: 质量验证与报告生成
            # ============================================================
            logger.info("\n" + "=" * 80)
            logger.info("Phase 6: 质量验证与报告生成")
            logger.info("=" * 80)
            
            validation_report = await self._phase6_quality_validation(
                srt_entries=import_result.entries,
                extraction_result=extraction_result,
                segmentation_result=segmentation_result,
                episode_name=episode_name
            )
            result.validation_report = validation_report
            
            logger.info(f"✅ Phase 6 完成: 质量评分 {validation_report.quality_score:.0f}/100")
            
            # 质量门禁检查
            if validation_report.quality_score < config.min_quality_score:
                logger.warning(f"⚠️ 质量警告: 评分 {validation_report.quality_score:.0f} 低于阈值 {config.min_quality_score}")
                for issue in validation_report.issues:
                    logger.warning(f"  - [{issue.severity}] {issue.description}")
            
            # ============================================================
            # 统计信息
            # ============================================================
            result.processing_time = time.time() - self.start_time
            result.llm_calls_count = self.llm_calls_count
            result.total_cost = self.total_cost
            result.success = True
            
            logger.info("\n" + "=" * 80)
            logger.info("🎉 脚本处理工作流完成")
            logger.info("=" * 80)
            logger.info(f"总耗时: {result.processing_time:.1f} 秒")
            logger.info(f"LLM调用次数: {result.llm_calls_count}")
            logger.info(f"总成本: ${result.total_cost:.4f} USD")
            logger.info(f"质量评分: {validation_report.quality_score:.0f}/100")
            logger.info("=" * 80)
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 工作流执行失败: {str(e)}", exc_info=True)
            
            # 记录错误
            error = ScriptProcessingError(
                step="workflow",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            result.errors.append(error)
            result.success = False
            
            # 记录统计信息
            result.processing_time = time.time() - self.start_time
            result.llm_calls_count = self.llm_calls_count
            result.total_cost = self.total_cost
            
            return result
    
    # ============================================================
    # Phase Implementation Methods
    # ============================================================
    
    async def _phase1_srt_import(
        self,
        srt_path: str,
        project_name: str,
        episode_name: str
    ) -> Optional[SrtImportResult]:
        """
        Phase 1: SRT导入与规范化
        
        Args:
            srt_path: SRT文件路径
            project_name: 项目名称
            episode_name: 集数名称
        
        Returns:
            SrtImportResult: 导入结果（包含SRT条目列表）
        """
        try:
            logger.debug("Phase 1: 进入_phase1_srt_import")
            logger.info(f"📥 开始导入SRT文件: {srt_path}")
            logger.debug("Phase 1: 即将调用srt_importer.execute")
            
            # 调用SrtImporter工具
            import_result = self.srt_importer.execute(
                source_file=srt_path,
                project_name=project_name,
                episode_name=episode_name
            )
            
            logger.debug("Phase 1: srt_importer.execute 返回")
            logger.info(f"✓ SRT导入成功:")
            logger.info(f"  - 文件编码: {import_result.encoding}")
            logger.info(f"  - 条目数量: {import_result.entry_count}")
            logger.info(f"  - 总时长: {import_result.total_duration}")
            logger.info(f"  - 应用的规范化: {', '.join(import_result.normalization_applied)}")
            
            return import_result
        
        except Exception as e:
            logger.debug(f"Phase 1: 发生异常: {str(e)}")
            logger.error(f"❌ SRT导入失败: {str(e)}", exc_info=True)
            return None
    
    async def _phase2_text_extraction(
        self,
        srt_entries: List[SrtEntry],
        project_name: str,
        episode_name: str,
        novel_reference: Optional[str],
        config: ScriptProcessingConfig
    ) -> Optional[SrtTextExtractionResult]:
        """
        Phase 2: 文本提取与智能修复
        
        Args:
            srt_entries: SRT条目列表
            project_name: 项目名称
            episode_name: 集数名称
            novel_reference: Novel文本参考（可选）
            config: 工作流配置
        
        Returns:
            SrtTextExtractionResult: 文本提取结果
        """
        try:
            logger.debug("Phase 2: 进入_phase2_text_extraction")
            logger.info("🔧 开始文本提取与智能修复...")
            
            # 选择处理模式
            processing_mode = "with_novel" if novel_reference else "without_novel"
            logger.info(f"  - 处理模式: {processing_mode}")
            logger.info(f"  - LLM Provider: {config.text_extraction_provider}")
            logger.debug("Phase 2: 即将调用text_extractor.execute")
            
            # 调用SrtTextExtractor工具（在线程池中运行同步代码）
            import asyncio
            extraction_result = await asyncio.to_thread(
                self.text_extractor.execute,
                srt_entries=srt_entries,
                project_name=project_name,
                episode_name=episode_name,
                novel_reference=novel_reference
            )
            logger.debug("Phase 2: text_extractor.execute 返回")
            
            # 更新统计
            self.llm_calls_count += 1
            # 估算成本（简化）
            cost_per_call = 0.03  # DeepSeek v3.2 约$0.02-0.04
            self.total_cost += cost_per_call
            
            logger.info(f"✓ 文本提取成功:")
            logger.info(f"  - 原始字符: {extraction_result.original_chars}")
            logger.info(f"  - 处理后字符: {extraction_result.processed_chars}")
            logger.info(f"  - 修正统计: {extraction_result.corrections}")
            logger.info(f"  - 处理耗时: {extraction_result.processing_time:.1f} 秒")
            
            return extraction_result
        
        except Exception as e:
            logger.error(f"❌ 文本提取失败: {str(e)}", exc_info=True)
            return None
    
    async def _temp_segmentation_for_hook(
        self,
        extracted_text: str,
        srt_entries: List[SrtEntry],
        config: ScriptProcessingConfig
    ) -> Optional[ScriptSegmentationResult]:
        """
        临时分段（用于Hook检测）
        
        在Hook检测前需要先进行简单分段，但不包含ABC分类。
        """
        try:
            logger.info("  - 执行初步分段（用于Hook检测）...")
            
            # 调用ScriptSegmenter进行初步分段
            # 注意：这里使用临时项目名，不保存到磁盘
            import asyncio
            temp_result = await asyncio.to_thread(
                self.script_segmenter.execute,
                processed_text=extracted_text,
                srt_entries=srt_entries,
                project_name="temp_hook_detection",
                episode_name="temp"
            )
            
            # 更新统计（Two-Pass分段）
            self.llm_calls_count += 2
            cost_per_pass = 0.03  # 约$0.02-0.04每次
            self.total_cost += cost_per_pass * 2
            
            return temp_result
        
        except Exception as e:
            logger.error(f"❌ 临时分段失败: {str(e)}", exc_info=True)
            return None
    
    async def _phase3_hook_detection(
        self,
        segmented_script: ScriptSegmentationResult,
        novel_intro: Optional[str],
        config: ScriptProcessingConfig
    ) -> Optional[HookDetectionResult]:
        """
        Phase 3: Hook边界检测
        
        Args:
            segmented_script: 分段后的脚本
            novel_intro: Novel简介（可选）
            config: 工作流配置
        
        Returns:
            HookDetectionResult: Hook检测结果
        """
        try:
            logger.info("🎣 开始Hook边界检测...")
            logger.info(f"  - LLM Provider: {config.hook_detection_provider}")
            
            # 调用HookDetector工具
            import asyncio
            hook_result = await asyncio.to_thread(
                self.hook_detector.execute,
                script_segmentation=segmented_script,
                novel_intro=novel_intro or "",
                novel_chapter1_preview=""  # 可选，如果有可以提供
            )
            
            # 更新统计
            self.llm_calls_count += 1
            cost_per_call = 0.02  # DeepSeek v3.2 约$0.01-0.03
            self.total_cost += cost_per_call
            
            logger.info(f"✓ Hook检测完成:")
            logger.info(f"  - 是否有Hook: {hook_result.has_hook}")
            if hook_result.has_hook:
                logger.info(f"  - Hook结束时间: {hook_result.hook_end_time}")
                logger.info(f"  - Body起点时间: {hook_result.body_start_time}")
            logger.info(f"  - 置信度: {hook_result.confidence:.2f}")
            logger.info(f"  - 判断理由: {hook_result.reasoning}")
            
            return hook_result
        
        except Exception as e:
            logger.error(f"❌ Hook检测失败: {str(e)}", exc_info=True)
            return None
    
    async def _phase4_hook_analysis(
        self,
        hook_detection_result: HookDetectionResult,
        segmented_script: ScriptSegmentationResult,
        novel_intro: str,
        novel_metadata: Dict[str, Any],
        config: ScriptProcessingConfig
    ) -> Optional[HookAnalysisResult]:
        """
        Phase 4: Hook内容分析
        
        Args:
            hook_detection_result: Hook检测结果
            segmented_script: 分段后的脚本
            novel_intro: Novel简介
            novel_metadata: Novel元数据
            config: 工作流配置
        
        Returns:
            HookAnalysisResult: Hook分析结果
        """
        try:
            logger.info("🔍 开始Hook内容分析...")
            
            # 提取Hook部分的段落
            hook_segments = [
                segmented_script.segments[i]
                for i in hook_detection_result.hook_segment_indices
            ]
            
            # 调用HookContentAnalyzer工具
            import asyncio
            analysis_result = await asyncio.to_thread(
                self.hook_analyzer.execute,
                hook_segments=hook_segments,
                novel_intro=novel_intro,
                novel_metadata=novel_metadata
            )
            
            # 更新统计
            self.llm_calls_count += 1
            cost_per_call = 0.03  # DeepSeek v3.2 约$0.02-0.04
            self.total_cost += cost_per_call
            
            logger.info(f"✓ Hook内容分析完成:")
            logger.info(f"  - 来源类型: {analysis_result.source_type}")
            logger.info(f"  - 相似度: {analysis_result.similarity_score:.2f}")
            logger.info(f"  - 建议策略: {analysis_result.alignment_strategy}")
            logger.info(f"  - 分层相似度: {analysis_result.layer_similarity}")
            
            return analysis_result
        
        except Exception as e:
            logger.error(f"❌ Hook内容分析失败: {str(e)}", exc_info=True)
            return None
    
    async def _phase5_script_segmentation(
        self,
        extracted_text: str,
        srt_entries: List[SrtEntry],
        project_name: str,
        episode_name: str,
        config: ScriptProcessingConfig
    ) -> Optional[ScriptSegmentationResult]:
        """
        Phase 5: 脚本语义分段（ABC分类）
        
        Args:
            extracted_text: 提取的文本
            srt_entries: SRT条目列表
            project_name: 项目名称
            episode_name: 集数名称
            config: 工作流配置
        
        Returns:
            ScriptSegmentationResult: 脚本分段结果
        """
        try:
            logger.info("✂️ 开始脚本语义分段...")
            logger.info(f"  - 使用Two-Pass分段 + ABC分类")
            
            # 调用ScriptSegmenter工具
            import asyncio
            segmentation_result = await asyncio.to_thread(
                self.script_segmenter.execute,
                processed_text=extracted_text,
                srt_entries=srt_entries,
                project_name=project_name,
                episode_name=episode_name
            )
            
            # 更新统计
            # ScriptSegmenter内部：Two-Pass分段 + ABC分类 = 3次LLM调用
            self.llm_calls_count += 3
            cost_per_call = 0.025  # DeepSeek v3.2 约$0.02-0.03每次
            self.total_cost += cost_per_call * 3
            
            logger.info(f"✓ 脚本分段完成:")
            logger.info(f"  - 总段落数: {segmentation_result.total_segments}")
            logger.info(f"  - 平均句子数: {segmentation_result.avg_sentence_count:.1f}")
            logger.info(f"  - 处理耗时: {segmentation_result.processing_time:.1f} 秒")
            
            # 统计ABC分类分布
            category_counts = {}
            for seg in segmentation_result.segments:
                cat = seg.category or "Unknown"
                category_counts[cat] = category_counts.get(cat, 0) + 1
            logger.info(f"  - ABC分类分布: {category_counts}")
            
            return segmentation_result
        
        except Exception as e:
            logger.error(f"❌ 脚本分段失败: {str(e)}", exc_info=True)
            return None
    
    async def _phase6_quality_validation(
        self,
        srt_entries: List[SrtEntry],
        extraction_result: SrtTextExtractionResult,
        segmentation_result: ScriptSegmentationResult,
        episode_name: str
    ) -> ScriptValidationReport:
        """
        Phase 6: 质量验证与报告生成
        
        Args:
            srt_entries: SRT条目列表
            extraction_result: 文本提取结果
            segmentation_result: 脚本分段结果
            episode_name: 集数名称
        
        Returns:
            ScriptValidationReport: 质量验证报告
        """
        try:
            logger.info("✅ 开始质量验证...")
            
            # 调用ScriptValidator工具
            import asyncio
            validation_report = await asyncio.to_thread(
                self.script_validator.execute,
                srt_entries=srt_entries,
                extraction_result=extraction_result,
                segmentation_result=segmentation_result,
                episode_name=episode_name
            )
            
            logger.info(f"✓ 质量验证完成:")
            logger.info(f"  - 总体评分: {validation_report.quality_score:.0f}/100")
            logger.info(f"  - 是否通过: {validation_report.is_valid}")
            logger.info(f"  - 问题数量: {len(validation_report.issues)}")
            logger.info(f"  - 警告数量: {len(validation_report.warnings)}")
            
            return validation_report
        
        except Exception as e:
            logger.error(f"❌ 质量验证失败: {str(e)}", exc_info=True)
            
            # 返回一个默认的失败报告
            return ScriptValidationReport(
                episode_name=episode_name,
                quality_score=0.0,
                is_valid=False,
                issues=[],
                warnings=[f"质量验证失败: {str(e)}"],
                recommendations=["检查工具实现和输入数据"]
            )
