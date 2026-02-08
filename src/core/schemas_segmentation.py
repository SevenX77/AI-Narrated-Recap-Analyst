"""
Novel Segmentation Analysis Schemas
小说分段分析数据模型

用于新的细粒度分段分析系统，支持多维度标签和Script-Novel精确对齐。
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class SegmentTags(BaseModel):
    """
    段落标签（多维度）
    
    Attributes:
        narrative_function: 叙事功能标签
            - "故事推进", "核心故事设定", "核心故事设定(首次)", 
            - "关键信息", "关键道具", "关键道具(首次)", "关键道具(升级)",
            - "背景交代"
        structure: 叙事结构标签
            - "钩子-悬念制造", "钩子-悬念释放", "伏笔", "回应伏笔", "重复强调"
        character: 角色与关系标签
            - "人物塑造-{角色名}", "对立关系-{角色A}-{角色B}", 
            - "同盟关系-{角色A}-{角色B}"
        priority: 浓缩优先级（单选）
            - "P0-骨架": 核心情节，必须保留
            - "P1-血肉": 重要细节，选择性保留
            - "P2-皮肤": 氛围渲染，可大量删减
        location: 地点标签（可选）
        time: 时间标签（可选）
    """
    narrative_function: List[str] = Field(default_factory=list)
    structure: List[str] = Field(default_factory=list)
    character: List[str] = Field(default_factory=list)
    priority: str = Field(..., description="P0-骨架 | P1-血肉 | P2-皮肤")
    location: Optional[str] = None
    time: Optional[str] = None


class ForeshadowingInfo(BaseModel):
    """
    伏笔信息
    
    Attributes:
        type: 伏笔类型 - "埋设" | "回应" | "强化" | "回收"
        content: 伏笔内容简述
        reference_id: 关联的伏笔ID（回应时使用）
        resolution_chapter: 回收章节（埋设时预测）
    """
    type: str = Field(..., description="埋设 | 回应 | 强化 | 回收")
    content: str
    reference_id: Optional[str] = None
    resolution_chapter: Optional[str] = None


class SegmentMetadata(BaseModel):
    """
    段落元数据
    
    Attributes:
        is_first_appearance: 是否首次出现（设定/道具/角色）
        repetition_count: 重复强调次数（0表示非重复）
        foreshadowing: 伏笔信息（可选）
        condensation_suggestion: 浓缩建议（供人类或Agent参考）
        word_count: 字数统计
    """
    is_first_appearance: bool = False
    repetition_count: int = 0
    foreshadowing: Optional[ForeshadowingInfo] = None
    condensation_suggestion: str = ""
    word_count: int = 0


class NovelSegment(BaseModel):
    """
    小说段落（分析单元）
    
    这是分段分析的最小单位，对应小说中的一个自然段。
    
    Attributes:
        segment_id: 段落唯一ID，格式: seg_{chapter_id}_{seq}
        text: 原文段落内容
        tags: 多维度标签
        metadata: 元数据和分析建议
    """
    segment_id: str
    text: str
    tags: SegmentTags
    metadata: SegmentMetadata


class ChapterSummary(BaseModel):
    """
    章节摘要统计
    
    Attributes:
        total_segments: 总段落数
        p0_count: P0段落数量
        p1_count: P1段落数量
        p2_count: P2段落数量
        key_events: 关键事件列表
        foreshadowing_planted: 本章埋设的伏笔
        foreshadowing_resolved: 本章回收的伏笔
        characters_introduced: 本章首次登场的角色
        condensed_version: 500字浓缩版（可选）
    """
    total_segments: int
    p0_count: int
    p1_count: int
    p2_count: int
    key_events: List[str] = Field(default_factory=list)
    foreshadowing_planted: List[str] = Field(default_factory=list)
    foreshadowing_resolved: List[str] = Field(default_factory=list)
    characters_introduced: List[str] = Field(default_factory=list)
    condensed_version: Optional[str] = None


class ChapterAnalysis(BaseModel):
    """
    章节完整分析结果
    
    Attributes:
        chapter_id: 章节ID（如 "chpt_0001"）
        chapter_title: 章节标题
        segments: 段落分析列表
        chapter_summary: 章节摘要
        version: 版本号（时间戳）
        analyzed_at: 分析时间
    """
    chapter_id: str
    chapter_title: Optional[str] = None
    segments: List[NovelSegment]
    chapter_summary: ChapterSummary
    version: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    analyzed_at: datetime = Field(default_factory=datetime.now)


class NovelKeyInfo(BaseModel):
    """
    小说关键信息汇总
    
    从多个章节分析中提取的关键信息，用于指导Script改写。
    
    Attributes:
        scope: 范围标识（如 "ep01", "chpt_0001-0010"）
        p0_skeleton: P0骨架信息（必须保留）
        p1_flesh: P1血肉信息（选择性保留）
        p2_skin: P2皮肤信息（可删减）
        foreshadowing_map: 伏笔映射表
        character_arcs: 角色弧光
        condensation_guidelines: 浓缩指导原则
    """
    scope: str
    p0_skeleton: List[Dict[str, Any]] = Field(default_factory=list)
    p1_flesh: List[Dict[str, Any]] = Field(default_factory=list)
    p2_skin: List[Dict[str, Any]] = Field(default_factory=list)
    foreshadowing_map: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    character_arcs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    condensation_guidelines: Dict[str, List[str]] = Field(default_factory=dict)


class ScriptSegmentInfo(BaseModel):
    """
    Script段落信息
    
    Attributes:
        time_range: 时间范围（SRT格式）
        text: Script文本内容
        segment_type: 段落类型 - "Hook" | "Body" | "Transition"
        word_count: 字数统计
    """
    time_range: str
    text: str
    segment_type: str = "Body"
    word_count: int = 0


class NovelSourceInfo(BaseModel):
    """
    Script对应的小说来源信息
    
    Attributes:
        segments: 对应的小说段落ID列表
        condensation_ratio: 浓缩比例（Script长度 / 小说长度）
        retained_tags: 保留的标签列表
        omitted_tags: 省略的标签列表
        transformation: 改编技巧描述
    """
    segments: List[str] = Field(default_factory=list)
    condensation_ratio: float = 0.0
    retained_tags: List[str] = Field(default_factory=list)
    omitted_tags: List[str] = Field(default_factory=list)
    transformation: Dict[str, Any] = Field(default_factory=dict)


class AlignmentAnalysis(BaseModel):
    """
    对齐分析详情
    
    Attributes:
        alignment_confidence: 对齐置信度（0-1）
        key_info_preserved: 保留的关键信息列表
        key_info_omitted: 省略的关键信息列表
        quality_score: 质量评分（0-100）
        notes: 分析备注
    """
    alignment_confidence: float = 1.0
    key_info_preserved: List[str] = Field(default_factory=list)
    key_info_omitted: List[str] = Field(default_factory=list)
    quality_score: Optional[float] = None
    notes: Optional[str] = None


class ScriptToNovelAlignment(BaseModel):
    """
    Script段落与小说的对应关系
    
    Attributes:
        script_segment: Script段落信息
        novel_source: 小说来源信息
        analysis: 对齐分析
    """
    script_segment: ScriptSegmentInfo
    novel_source: NovelSourceInfo
    analysis: AlignmentAnalysis


class AlignmentOverallStats(BaseModel):
    """
    对齐结果整体统计
    
    Attributes:
        total_script_segments: Script总段落数
        total_novel_segments: 小说总段落数
        condensation_ratio: 整体浓缩比例
        p0_retention_rate: P0内容保留率
        p1_retention_rate: P1内容保留率
        p2_retention_rate: P2内容保留率
        avg_alignment_confidence: 平均对齐置信度
    """
    total_script_segments: int
    total_novel_segments: int
    condensation_ratio: float
    p0_retention_rate: float
    p1_retention_rate: float
    p2_retention_rate: float
    avg_alignment_confidence: float


class AlignmentResult(BaseModel):
    """
    完整对齐结果
    
    Attributes:
        episode_id: 集数ID（如 "ep01"）
        alignments: 对齐关系列表
        overall_stats: 整体统计
        version: 版本号
        analyzed_at: 分析时间
    """
    episode_id: str
    alignments: List[ScriptToNovelAlignment]
    overall_stats: AlignmentOverallStats
    version: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    analyzed_at: datetime = Field(default_factory=datetime.now)


class AdaptationPattern(BaseModel):
    """
    改编手法模式
    
    从GT项目中提取的改编规律。
    
    Attributes:
        pattern_type: 模式类型 - "hook" | "condensation" | "rhythm" | "language"
        description: 模式描述
        examples: 示例列表
        success_rate: 成功率（基于热度相关性）
        applicable_scenarios: 适用场景
    """
    pattern_type: str
    description: str
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    success_rate: Optional[float] = None
    applicable_scenarios: List[str] = Field(default_factory=list)


class PatternLibrary(BaseModel):
    """
    改编规律库
    
    从多个GT项目中提取的爆款规律集合。
    
    Attributes:
        patterns: 按类型分组的模式字典
        success_factors: 成功因素列表
        source_projects: 来源项目列表
        validated: 是否已验证
        correlation: 与热度的相关性（验证后填充）
        version: 版本号
        created_at: 创建时间
    """
    patterns: Dict[str, List[AdaptationPattern]] = Field(default_factory=dict)
    success_factors: List[str] = Field(default_factory=list)
    source_projects: List[str] = Field(default_factory=list)
    validated: bool = False
    correlation: Optional[float] = None
    version: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    created_at: datetime = Field(default_factory=datetime.now)


class WritingContext(BaseModel):
    """
    Writer改写上下文
    
    提供给Writer Agent的完整上下文信息。
    
    Attributes:
        novel_analysis: 小说分析结果
        key_info: 关键信息汇总
        pattern_library: 改编规律库
        gt_reference: GT参考项目（可选）
        target_length: 目标长度（秒/字数）
        constraints: 约束条件
    """
    novel_analysis: ChapterAnalysis
    key_info: NovelKeyInfo
    pattern_library: PatternLibrary
    gt_reference: Optional[Dict[str, Any]] = None
    target_length: Optional[int] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)


# 导出所有模型
__all__ = [
    "SegmentTags",
    "ForeshadowingInfo",
    "SegmentMetadata",
    "NovelSegment",
    "ChapterSummary",
    "ChapterAnalysis",
    "NovelKeyInfo",
    "ScriptSegmentInfo",
    "NovelSourceInfo",
    "AlignmentAnalysis",
    "ScriptToNovelAlignment",
    "AlignmentOverallStats",
    "AlignmentResult",
    "AdaptationPattern",
    "PatternLibrary",
    "WritingContext",
]
