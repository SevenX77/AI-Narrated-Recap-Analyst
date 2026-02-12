"""
Novel Processing Schemas - 验证和工作流结果
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
from datetime import datetime

# 跨模块导入 - 解决类依赖问题
from .basic import NovelImportResult, NovelMetadata, ChapterInfo
from .segmentation import ParagraphSegmentationResult
from .annotation import AnnotatedChapter
from .system import SystemCatalog, SystemUpdateResult, SystemTrackingResult


class ValidationIssue(BaseModel):
    """
    验证问题模型
    
    表示质量验证中发现的单个问题。
    """
    severity: str = Field(
        ...,
        description="严重程度（error/warning/info）"
    )
    category: str = Field(
        ...,
        description="问题类别（encoding/chapter/segmentation/annotation）"
    )
    description: str = Field(
        ...,
        description="问题描述"
    )
    location: Optional[str] = Field(
        None,
        description="问题位置（如章节号、段落号）"
    )
    recommendation: Optional[str] = Field(
        None,
        description="改进建议"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "severity": "warning",
                "category": "segmentation",
                "description": "第1章分段数量过多（53段），可能存在过度分段",
                "location": "chapter_1",
                "recommendation": "检查分段逻辑，考虑合并相似段落"
            }
        }


class NovelValidationReport(BaseModel):
    """
    小说处理质量验证报告
    
    由 NovelValidator 工具返回，包含完整的质量评估结果。
    """
    project_name: str = Field(
        ...,
        description="项目名称"
    )
    validation_time: datetime = Field(
        default_factory=datetime.now,
        description="验证时间"
    )
    quality_score: float = Field(
        ...,
        description="总体质量评分（0-100分）",
        ge=0,
        le=100
    )
    is_valid: bool = Field(
        ...,
        description="是否通过验证（质量评分>=70）"
    )
    
    # 检查结果
    encoding_check: Dict[str, Any] = Field(
        default_factory=dict,
        description="编码正确性检查结果"
    )
    chapter_check: Dict[str, Any] = Field(
        default_factory=dict,
        description="章节完整性检查结果"
    )
    segmentation_check: Dict[str, Any] = Field(
        default_factory=dict,
        description="分段合理性检查结果"
    )
    annotation_check: Dict[str, Any] = Field(
        default_factory=dict,
        description="标注合理性检查结果"
    )
    
    # 问题与建议
    issues: List[ValidationIssue] = Field(
        default_factory=list,
        description="发现的问题列表"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="警告列表"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="改进建议列表"
    )
    
    # 统计信息
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="统计信息"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "超凡公路",
                "quality_score": 85.5,
                "is_valid": True,
                "encoding_check": {
                    "passed": True,
                    "invalid_chars_count": 0
                },
                "chapter_check": {
                    "passed": True,
                    "total_chapters": 50,
                    "missing_chapters": []
                },
                "segmentation_check": {
                    "passed": True,
                    "avg_paragraphs_per_chapter": 12.5,
                    "abc_distribution": {"A": 0.15, "B": 0.75, "C": 0.10}
                },
                "issues": [],
                "recommendations": ["分段质量优秀，建议保持当前策略"]
            }
        }


# ============================================
# NovelTagger Schemas
# ============================================

class ChapterProcessingError(BaseModel):
    """
    章节处理错误信息
    """
    chapter_number: int = Field(
        ...,
        description="章节序号"
    )
    step: str = Field(
        ...,
        description="失败的步骤（如 'segmentation', 'annotation'）"
    )
    error_type: str = Field(
        ...,
        description="错误类型"
    )
    error_message: str = Field(
        ...,
        description="错误消息"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="错误发生时间"
    )


class NovelProcessingResult(BaseModel):
    """
    小说处理完整结果
    
    包含从导入到验证的所有处理结果。
    """
    project_name: str = Field(
        ...,
        description="项目名称"
    )
    
    # Step 1-3: 基础信息
    import_result: Optional[NovelImportResult] = Field(
        None,
        description="导入结果"
    )
    metadata: Optional[NovelMetadata] = Field(
        None,
        description="小说元数据"
    )
    chapters: List[ChapterInfo] = Field(
        ...,
        description="章节信息列表"
    )
    
    # Step 4-5: 核心分析
    segmentation_results: Dict[int, ParagraphSegmentationResult] = Field(
        default_factory=dict,
        description="分段结果，key=章节号"
    )
    annotation_results: Dict[int, AnnotatedChapter] = Field(
        default_factory=dict,
        description="标注结果，key=章节号"
    )
    
    # Step 6-7: 系统分析（可选）
    system_catalog: Optional[SystemCatalog] = Field(
        None,
        description="系统目录（如果启用系统分析）"
    )
    system_updates: Dict[int, SystemUpdateResult] = Field(
        default_factory=dict,
        description="系统元素更新结果，key=章节号"
    )
    system_tracking: Dict[int, SystemTrackingResult] = Field(
        default_factory=dict,
        description="系统元素追踪结果，key=章节号"
    )
    
    # Step 8: 质量报告
    validation_report: Optional[NovelValidationReport] = Field(
        None,
        description="质量验证报告"
    )
    
    # 处理统计
    processing_stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="处理统计信息"
    )
    processing_time: float = Field(
        default=0.0,
        description="总处理时间（秒）",
        ge=0
    )
    llm_calls_count: int = Field(
        default=0,
        description="LLM调用总次数",
        ge=0
    )
    total_cost: float = Field(
        default=0.0,
        description="总成本（USD）",
        ge=0
    )
    
    # 错误信息
    errors: List[ChapterProcessingError] = Field(
        default_factory=list,
        description="处理过程中的错误列表"
    )
    
    # 中间结果保存路径
    intermediate_results_dir: Optional[str] = Field(
        None,
        description="中间结果保存目录"
    )
    
    # 元数据
    workflow_version: str = Field(
        default="1.0.0",
        description="Workflow版本"
    )
    completed_steps: List[int] = Field(
        default_factory=list,
        description="已完成的步骤列表"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "末哥超凡公路_test",
                "import_result": {},
                "metadata": {},
                "chapters": [],
                "segmentation_results": {},
                "annotation_results": {},
                "system_catalog": None,
                "system_updates": {},
                "system_tracking": {},
                "validation_report": None,
                "processing_stats": {
                    "total_chapters": 10,
                    "successful_chapters": 10,
                    "failed_chapters": 0
                },
                "processing_time": 3900.5,
                "llm_calls_count": 50,
                "total_cost": 2.5,
                "errors": [],
                "intermediate_results_dir": "data/projects/xxx/processing",
                "workflow_version": "1.0.0",
                "completed_steps": [1, 2, 3, 4, 5, 6, 7, 8],
                "created_at": "2026-02-10T10:00:00"
            }
        }


