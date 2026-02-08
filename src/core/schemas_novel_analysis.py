"""
Novel Chapter Functional Analysis Data Schemas
小说章节功能段分析的数据结构定义
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class FunctionalSegmentTags(BaseModel):
    """功能段标签"""
    narrative_function: List[str] = Field(
        default_factory=list,
        description="叙事功能：故事推进、核心故事设定(首次)、关键信息、关键道具(首次)、背景交代、人物塑造-XX"
    )
    structure: List[str] = Field(
        default_factory=list,
        description="叙事结构：钩子-悬念制造、钩子-悬念释放、伏笔、回应伏笔、重复强调"
    )
    character: List[str] = Field(
        default_factory=list,
        description="角色与关系：人物塑造-XX、对立关系、同盟关系"
    )
    priority: str = Field(
        ...,
        description="浓缩优先级：P0-骨架 | P1-血肉 | P2-皮肤"
    )
    location: Optional[str] = Field(
        None,
        description="地点"
    )
    time: Optional[str] = Field(
        None,
        description="时间"
    )


class FunctionalSegmentMetadata(BaseModel):
    """功能段元数据"""
    word_count: int = Field(
        ...,
        description="字数统计"
    )
    contains_first_appearance: bool = Field(
        default=False,
        description="是否包含首次出现的设定/道具"
    )
    repetition_items: List[str] = Field(
        default_factory=list,
        description="重复强调的内容列表"
    )
    foreshadowing: Optional[Dict[str, Optional[str]]] = Field(
        None,
        description="伏笔信息：{\"type\": \"埋设|回应|强化\", \"content\": \"...\", \"reference\": \"...或null\"}"
    )


class FunctionalSegment(BaseModel):
    """功能段（叙事功能聚合的段落组）"""
    segment_id: str = Field(
        ...,
        description="段落ID，格式：func_seg_chpt_XXXX_YY"
    )
    title: str = Field(
        ...,
        description="段落标题，例如：段落1：开篇钩子（广播）"
    )
    content: str = Field(
        ...,
        description="段落原文内容"
    )
    tags: FunctionalSegmentTags = Field(
        ...,
        description="多维度标签"
    )
    metadata: FunctionalSegmentMetadata = Field(
        ...,
        description="元数据"
    )
    condensation_suggestion: str = Field(
        ...,
        description="浓缩建议：保留什么、删除什么、如何简化"
    )


class ChapterSummary(BaseModel):
    """章节整体摘要"""
    total_segments: int = Field(
        ...,
        description="功能段总数"
    )
    p0_count: int = Field(
        default=0,
        description="P0-骨架段落数"
    )
    p1_count: int = Field(
        default=0,
        description="P1-血肉段落数"
    )
    p2_count: int = Field(
        default=0,
        description="P2-皮肤段落数"
    )
    key_events: List[str] = Field(
        default_factory=list,
        description="关键事件列表"
    )
    foreshadowing_planted: List[str] = Field(
        default_factory=list,
        description="埋设的伏笔列表"
    )
    foreshadowing_resolved: List[str] = Field(
        default_factory=list,
        description="回收的伏笔列表"
    )
    characters_introduced: List[str] = Field(
        default_factory=list,
        description="登场角色列表"
    )
    condensed_version: str = Field(
        default="",
        description="章节浓缩版本（500字）"
    )


class ChapterStructureInsight(BaseModel):
    """章节结构洞察"""
    opening_style: str = Field(
        default="",
        description="开篇方式：如双开篇、规则前置等"
    )
    turning_point: str = Field(
        default="",
        description="转折点位置和内容"
    )
    climax: str = Field(
        default="",
        description="高潮部分"
    )
    ending_hook: str = Field(
        default="",
        description="章节钩子（悬念）"
    )
    narrative_rhythm: str = Field(
        default="",
        description="叙事节奏描述"
    )


class ChapterFunctionalAnalysis(BaseModel):
    """章节功能段分析完整结果"""
    chapter_id: str = Field(
        ...,
        description="章节ID，格式：chpt_XXXX"
    )
    chapter_number: int = Field(
        ...,
        description="章节序号"
    )
    chapter_title: str = Field(
        ...,
        description="章节标题"
    )
    segments: List[FunctionalSegment] = Field(
        ...,
        description="功能段列表"
    )
    chapter_summary: ChapterSummary = Field(
        ...,
        description="章节摘要"
    )
    structure_insight: ChapterStructureInsight = Field(
        default_factory=ChapterStructureInsight,
        description="章节结构洞察"
    )
    methodology_notes: List[str] = Field(
        default_factory=list,
        description="方法论验证笔记"
    )
    version: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"),
        description="分析版本（时间戳）"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.now,
        description="分析时间"
    )


class NovelAnalysisProject(BaseModel):
    """小说分析项目"""
    novel_title: str = Field(
        ...,
        description="小说标题"
    )
    author: str = Field(
        default="",
        description="作者"
    )
    chapters: List[ChapterFunctionalAnalysis] = Field(
        default_factory=list,
        description="章节分析列表"
    )
    total_chapters_analyzed: int = Field(
        default=0,
        description="已分析章节数"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="更新时间"
    )
