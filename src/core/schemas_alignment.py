"""
Novel-Script Alignment Data Schemas
Novel与Script对齐数据结构定义

基于实验结果（test_alignment_with_annotation.py）设计
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime


class EventAlignment(BaseModel):
    """事件对齐信息"""
    event_id: str = Field(
        ...,
        description="Novel事件ID，格式：000100001B"
    )
    match_type: Literal["exact", "paraphrase", "summarize", "expand", "none"] = Field(
        ...,
        description="对应关系类型：exact-原文 | paraphrase-改写 | summarize-压缩 | expand-扩写 | none-无对应"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="匹配置信度（0-1）"
    )
    explanation: str = Field(
        default="",
        description="对应关系说明"
    )


class SettingAlignment(BaseModel):
    """设定对齐信息"""
    setting_id: str = Field(
        ...,
        description="Novel设定ID，格式：S00010001"
    )
    match_type: Literal["exact", "paraphrase", "summarize", "expand", "none"] = Field(
        ...,
        description="对应关系类型：exact-原文 | paraphrase-改写 | summarize-压缩 | expand-扩写 | none-无对应"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="匹配置信度（0-1）"
    )
    explanation: str = Field(
        default="",
        description="对应关系说明"
    )


class SkippedContent(BaseModel):
    """跳过的内容信息"""
    content_type: Literal["event", "setting"] = Field(
        ...,
        description="跳过内容类型：event-事件 | setting-设定"
    )
    content_id: str = Field(
        ...,
        description="跳过的事件/设定ID"
    )
    reason: str = Field(
        default="",
        description="跳过原因说明"
    )


class ScriptFragmentAlignment(BaseModel):
    """Script片段对齐结果"""
    fragment_index: int = Field(
        ...,
        description="片段序号（从1开始）"
    )
    time_range: str = Field(
        ...,
        description="时间范围，格式：00:00:00,000 --> 00:00:30,000"
    )
    content: str = Field(
        ...,
        description="Script片段内容（完整文本）"
    )
    content_preview: str = Field(
        default="",
        description="Script片段预览（前100字）"
    )
    matched_events: List[EventAlignment] = Field(
        default_factory=list,
        description="匹配的Novel事件列表"
    )
    matched_settings: List[SettingAlignment] = Field(
        default_factory=list,
        description="匹配的Novel设定列表"
    )
    skipped_content: List[SkippedContent] = Field(
        default_factory=list,
        description="Script中提到但Novel未出现的内容"
    )


class CoverageStatistics(BaseModel):
    """覆盖率统计"""
    total_events: int = Field(
        ...,
        description="Novel事件总数"
    )
    matched_events: int = Field(
        ...,
        description="已匹配的事件数"
    )
    event_coverage: float = Field(
        ...,
        description="事件覆盖率（0-1）"
    )
    total_settings: int = Field(
        ...,
        description="Novel设定总数"
    )
    matched_settings: int = Field(
        ...,
        description="已匹配的设定数"
    )
    setting_coverage: float = Field(
        ...,
        description="设定覆盖率（0-1）"
    )
    matched_event_ids: List[str] = Field(
        default_factory=list,
        description="已匹配的事件ID列表"
    )
    matched_setting_ids: List[str] = Field(
        default_factory=list,
        description="已匹配的设定ID列表"
    )
    unmatched_event_ids: List[str] = Field(
        default_factory=list,
        description="未匹配的事件ID列表"
    )
    unmatched_setting_ids: List[str] = Field(
        default_factory=list,
        description="未匹配的设定ID列表"
    )


class RewriteStrategyStatistics(BaseModel):
    """改写策略统计"""
    exact_count: int = Field(
        default=0,
        description="原文保留数量"
    )
    paraphrase_count: int = Field(
        default=0,
        description="改写数量"
    )
    summarize_count: int = Field(
        default=0,
        description="压缩数量"
    )
    expand_count: int = Field(
        default=0,
        description="扩写数量"
    )
    none_count: int = Field(
        default=0,
        description="无对应数量"
    )
    dominant_strategy: str = Field(
        default="",
        description="主要改写策略"
    )


class AlignmentResult(BaseModel):
    """Novel-Script对齐完整结果"""
    project_name: str = Field(
        ...,
        description="项目名称"
    )
    novel_chapter_id: str = Field(
        ...,
        description="Novel章节ID，格式：chpt_0001"
    )
    script_episode_id: str = Field(
        ...,
        description="Script集数ID，格式：ep01"
    )
    alignments: List[ScriptFragmentAlignment] = Field(
        default_factory=list,
        description="Script片段对齐结果列表"
    )
    coverage_stats: CoverageStatistics = Field(
        ...,
        description="覆盖率统计"
    )
    rewrite_stats: RewriteStrategyStatistics = Field(
        default_factory=RewriteStrategyStatistics,
        description="改写策略统计"
    )
    total_fragments: int = Field(
        default=0,
        description="Script片段总数"
    )
    aligned_at: datetime = Field(
        default_factory=datetime.now,
        description="对齐时间"
    )
    llm_provider: str = Field(
        default="",
        description="使用的LLM提供商"
    )
    llm_model: str = Field(
        default="",
        description="使用的LLM模型"
    )


class AlignmentQualityMetrics(BaseModel):
    """对齐质量指标"""
    avg_confidence: float = Field(
        ...,
        description="平均置信度"
    )
    high_confidence_count: int = Field(
        default=0,
        description="高置信度（>0.9）匹配数"
    )
    medium_confidence_count: int = Field(
        default=0,
        description="中等置信度（0.7-0.9）匹配数"
    )
    low_confidence_count: int = Field(
        default=0,
        description="低置信度（<0.7）匹配数"
    )
    empty_alignment_count: int = Field(
        default=0,
        description="无匹配的片段数"
    )


class AlignmentReport(BaseModel):
    """对齐分析报告"""
    alignment_result: AlignmentResult = Field(
        ...,
        description="对齐结果"
    )
    quality_metrics: AlignmentQualityMetrics = Field(
        ...,
        description="质量指标"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="改进建议列表"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="报告生成时间"
    )
