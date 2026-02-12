"""
Novel Processing Schemas - 标注相关（事件、设定、功能标签）
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
from datetime import datetime


class EventEntry(BaseModel):
    """
    单个事件条目（事件时间线表）
    
    事件是多个连续段落的聚合，按故事时间线顺序排列。
    - 一个事件可以包含1个或多个B/C类段落
    - 事件编号格式: [章节4位][序号5位][类型1位]
    - 例: 000100001B (第1章第1个事件，B类)
    """
    event_id: str = Field(
        ...,
        description="事件编号 (如: 000100001B, 格式: 章节4位+序号5位+类型1位)"
    )
    event_summary: str = Field(
        ...,
        description="事件概括（简短描述，如：'陈野从江城逃出来，和一众幸存者组成车队'）"
    )
    event_type: Literal["B", "C"] = Field(
        ...,
        description="事件主类型：B-现实事件, C-系统事件"
    )
    paragraph_indices: List[int] = Field(
        ...,
        description="包含的段落索引列表（按时间线顺序，如: [3, 4]）"
    )
    paragraph_contents: List[str] = Field(
        ...,
        description="完整段落内容列表（包含段落标题，按时间线顺序）"
    )
    location: str = Field(
        ...,
        description="事件发生地点（如: '江城', '公路｜车队', '营地'）"
    )
    location_change: str = Field(
        ...,
        description="相对上一事件的地点变化（如: '江城——>公路｜车队', '不变'）"
    )
    time: str = Field(
        ...,
        description="事件发生时间（如: '白天', '晚上', '2030年10月13日'）"
    )
    time_change: str = Field(
        ...,
        description="相对上一事件的时间变化（如: '白天——>晚上', '不变'）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "000100001B",
                "event_summary": "陈野从江城逃出来，和一众幸存者组成车队",
                "event_type": "B",
                "paragraph_indices": [3, 4],
                "paragraph_contents": [
                    "## 段落 3 [B类-事件]\n\n陈野从江城逃出来...",
                    "## 段落 4 [B类-事件]\n\n这个车队组成很是杂乱..."
                ],
                "location": "公路｜车队",
                "location_change": "江城——>公路｜车队",
                "time": "白天",
                "time_change": "不变"
            }
        }


class EventTimeline(BaseModel):
    """
    事件时间线表
    
    由 NovelAnnotator 工具返回，包含按时间线排序的事件列表（B类+C类）。
    """
    chapter_number: int = Field(
        ...,
        description="章节序号",
        ge=1
    )
    total_events: int = Field(
        ...,
        description="事件总数",
        ge=0
    )
    events: List[EventEntry] = Field(
        default_factory=list,
        description="事件列表（按故事时间线顺序排列）"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（如处理时间、类型分布等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "total_events": 5,
                "events": [
                    {
                        "event_id": "000100001B",
                        "event_summary": "陈野从江城逃出来...",
                        "event_type": "B",
                        "paragraph_indices": [3, 4],
                        "location": "公路｜车队",
                        "time": "白天"
                    }
                ],
                "metadata": {
                    "type_distribution": {"B": 4, "C": 1},
                    "processing_time": 35.2
                }
            }
        }


class SettingEntry(BaseModel):
    """
    单个设定条目（设定知识库）
    
    从A类段落提取的设定知识点，关联到事件时间线。
    - 设定编号格式: S + 章节4位 + 序号4位
    - 例: S00010001 (第1章第1个设定)
    - 获得时间点: BF_000100001B (在事件000100001B之前获得)
    """
    setting_id: str = Field(
        ...,
        description="设定唯一编号 (如: S00010001, 格式: S+章节4位+序号4位)"
    )
    setting_title: str = Field(
        ...,
        description="设定标题（简短概括，如：'全球诡异爆发'）"
    )
    setting_summary: str = Field(
        ...,
        description="设定核心知识点（简洁提炼，如：'全球诡异爆发。只用了很短的时间...'）"
    )
    paragraph_index: int = Field(
        ...,
        description="对应的A类段落索引",
        ge=1
    )
    paragraph_content: str = Field(
        ...,
        description="完整A类段落内容（包含段落标题）"
    )
    acquisition_time: str = Field(
        ...,
        description="获得时间点 (如: BF_000100001B, 格式: [时间位置]_[事件ID])"
    )
    related_event_id: str = Field(
        ...,
        description="关联的事件编号（如: 000100001B）"
    )
    time_position: Literal["BF", "BT", "AF"] = Field(
        ...,
        description="相对事件的时间位置：BF-之前, BT-之间, AF-之后"
    )
    accumulated_knowledge: List[str] = Field(
        default_factory=list,
        description="累积的知识库（按顺序包含所有已出现的设定编号，如：['S00010001', 'S00010002']）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "setting_id": "S00010001",
                "setting_title": "全球诡异爆发",
                "setting_summary": "全球诡异爆发。只用了很短的时间，一些小的国家直接沦为人类禁区...",
                "paragraph_index": 2,
                "paragraph_content": "## 段落 2 [A类-设定]\n\n几个月前，全球诡异爆发...",
                "acquisition_time": "BF_000100001B",
                "related_event_id": "000100001B",
                "time_position": "BF",
                "accumulated_knowledge": ["S00010001"]
            }
        }


class SettingLibrary(BaseModel):
    """
    设定知识库
    
    由 NovelAnnotator 工具返回，包含所有A类设定的结构化信息。
    """
    chapter_number: int = Field(
        ...,
        description="章节序号",
        ge=1
    )
    total_settings: int = Field(
        ...,
        description="设定总数",
        ge=0
    )
    settings: List[SettingEntry] = Field(
        default_factory=list,
        description="设定列表（按出现顺序排列）"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（如处理时间、BF/BT/AF分布等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "total_settings": 3,
                "settings": [
                    {
                        "setting_id": "BF000100001B",
                        "setting_summary": "全球诡异爆发...",
                        "paragraph_index": 2,
                        "related_event_id": "000100001B",
                        "time_position": "BF"
                    }
                ],
                "metadata": {
                    "position_distribution": {"BF": 2, "BT": 1, "AF": 0},
                    "processing_time": 18.5
                }
            }
        }


class AnnotatedChapter(BaseModel):
    """
    完整章节标注结果
    
    由 NovelAnnotator 工具返回，包含：
    - 事件时间线表（Pass 1）
    - 设定知识库（Pass 2）
    - 功能性标签库（Pass 3）
    """
    chapter_number: int = Field(
        ...,
        description="章节序号",
        ge=1
    )
    event_timeline: EventTimeline = Field(
        ...,
        description="事件时间线表（B类+C类事件）"
    )
    setting_library: SettingLibrary = Field(
        ...,
        description="设定知识库（A类设定）"
    )
    functional_tags: Optional['FunctionalTagsLibrary'] = Field(
        None,
        description="功能性标签库（可选，由Pass 3生成）"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="整体元数据（如总处理时间、模型信息等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "event_timeline": {
                    "total_events": 5,
                    "events": [...]
                },
                "setting_library": {
                    "total_settings": 3,
                    "settings": [...]
                },
                "metadata": {
                    "total_processing_time": 53.7,
                    "model_used": "claude-sonnet-4-5-20250929",
                    "provider": "claude"
                }
            }
        }


# ============================================================================
# 系统追踪工具数据模型 (Phase 1 - 全局系统检测, 2026-02-09)
# NovelSystemAnalyzer - 识别小说核心系统元素
# ============================================================================

class ParagraphFunctionalTags(BaseModel):
    """
    段落功能性标签
    
    基于 NOVEL_SEGMENTATION_METHODOLOGY，为每个段落标注功能性标签。
    由 NovelAnnotator Pass 3 生成。
    """
    paragraph_index: int = Field(
        ...,
        description="段落索引",
        ge=1
    )
    
    # 维度1：叙事功能
    narrative_functions: List[str] = Field(
        default_factory=list,
        description="叙事功能标签（如：'故事推进', '核心故事设定（首次）', '关键道具'）"
    )
    
    # 维度2：叙事结构
    narrative_structures: List[str] = Field(
        default_factory=list,
        description="叙事结构标签（如：'钩子-悬念制造', '伏笔（明确）', '重复强调x3'）"
    )
    
    # 维度3：角色与关系
    character_tags: List[str] = Field(
        default_factory=list,
        description="角色与关系标签（如：'人物登场：佳佳', '对立关系：陈野 vs 佳佳'）"
    )
    
    # 维度4：浓缩优先级 ⭐ 最重要
    priority: str = Field(
        ...,
        description="浓缩优先级（'P0-骨架' / 'P1-血肉' / 'P2-皮肤'）"
    )
    priority_reason: str = Field(
        ...,
        description="优先级判断理由（简短说明，如：'主角关键决策'）"
    )
    
    # 维度5：其他标记
    emotional_tone: Optional[str] = Field(
        None,
        description="情绪基调（如：'紧张', '绝望', '希望', '平静'）"
    )
    is_first_occurrence: bool = Field(
        default=False,
        description="是否为首次信息（与重复信息区分）"
    )
    repetition_count: Optional[int] = Field(
        None,
        description="重复强调次数（如：'不要掉队'重复3次）",
        ge=2
    )
    
    # 浓缩建议
    condensation_advice: Optional[str] = Field(
        None,
        description="浓缩改编建议（如：'保留核心对话，删减环境描写'）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "paragraph_index": 5,
                "narrative_functions": ["核心故事设定（首次）", "关键信息"],
                "narrative_structures": ["伏笔", "重复强调x3"],
                "character_tags": [],
                "priority": "P0-骨架",
                "priority_reason": "车队生存铁律，删除后故事无法理解",
                "emotional_tone": "紧张",
                "is_first_occurrence": True,
                "repetition_count": 3,
                "condensation_advice": "保留：不要掉队铁律（必须重复强调）。删除：物资细节"
            }
        }


class FunctionalTagsLibrary(BaseModel):
    """
    章节功能性标签库
    
    包含章节所有段落的功能性标签，由 NovelAnnotator Pass 3 生成。
    """
    chapter_number: int = Field(
        ...,
        description="章节序号",
        ge=1
    )
    total_paragraphs: int = Field(
        ...,
        description="总段落数",
        ge=0
    )
    paragraph_tags: List[ParagraphFunctionalTags] = Field(
        default_factory=list,
        description="段落功能性标签列表"
    )
    
    # 统计信息
    priority_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="优先级分布统计（如：{'P0-骨架': 5, 'P1-血肉': 8, 'P2-皮肤': 10}）"
    )
    first_occurrence_count: int = Field(
        default=0,
        description="首次信息数量",
        ge=0
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（如处理时间等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "total_paragraphs": 11,
                "paragraph_tags": [],
                "priority_distribution": {
                    "P0-骨架": 5,
                    "P1-血肉": 4,
                    "P2-皮肤": 2
                },
                "first_occurrence_count": 8,
                "metadata": {
                    "processing_time": 12.3
                }
            }
        }


# ==================== NovelProcessingWorkflow Schemas ====================

class ChapterTags(BaseModel):
    """
    章节叙事特征标签
    
    由 NovelTagger 工具返回，描述章节的叙事特征。
    """
    chapter_number: int = Field(
        ...,
        description="章节号",
        ge=1
    )
    
    # 叙事特征
    narrative_perspective: str = Field(
        ...,
        description="叙事视角（第一人称/第三人称全知/第三人称限制）"
    )
    time_structure: str = Field(
        ...,
        description="时间结构（线性/倒叙/插叙/平行）"
    )
    pacing: str = Field(
        ...,
        description="叙事节奏（快节奏/中速/慢节奏）"
    )
    tone: str = Field(
        ...,
        description="情感基调（紧张/轻松/悬疑/幽默/压抑/热血）"
    )
    
    # 内容特征
    key_themes: List[str] = Field(
        default_factory=list,
        description="关键主题（如：生存、成长、复仇、友情）"
    )
    genre_tags: List[str] = Field(
        default_factory=list,
        description="类型标签（如：动作、悬疑、日常、战斗、心理）"
    )
    
    # 叙事技巧
    narrative_techniques: List[str] = Field(
        default_factory=list,
        description="叙事技巧（如：闪回、伏笔、对比、悬念）"
    )
    
    # 元数据
    confidence: float = Field(
        default=1.0,
        description="标注置信度（0.0-1.0）",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "narrative_perspective": "第三人称限制",
                "time_structure": "线性",
                "pacing": "快节奏",
                "tone": "紧张",
                "key_themes": ["生存", "逃亡"],
                "genre_tags": ["动作", "悬疑"],
                "narrative_techniques": ["悬念", "环境渲染"],
                "confidence": 0.95
            }
        }


class NovelTaggingResult(BaseModel):
    """
    Novel标注结果
    
    由 NovelTagger 工具返回，包含所有章节的叙事特征标签。
    """
    project_name: str = Field(
        ...,
        description="项目名称"
    )
    total_chapters: int = Field(
        ...,
        description="总章节数",
        ge=0
    )
    chapter_tags: List[ChapterTags] = Field(
        default_factory=list,
        description="章节标签列表"
    )
    
    # 整体特征统计
    overall_perspective: str = Field(
        ...,
        description="整体叙事视角（主导视角）"
    )
    dominant_tone: str = Field(
        ...,
        description="主导基调"
    )
    common_themes: List[str] = Field(
        default_factory=list,
        description="常见主题"
    )
    
    # 元数据
    processing_time: float = Field(
        ...,
        description="处理时长（秒）",
        ge=0.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "超凡公路",
                "total_chapters": 50,
                "chapter_tags": [],
                "overall_perspective": "第三人称限制",
                "dominant_tone": "紧张",
                "common_themes": ["生存", "成长", "系统"],
                "processing_time": 120.5
            }
        }


# ==================== 功能性标签体系 (Functional Tagging System) ====================

