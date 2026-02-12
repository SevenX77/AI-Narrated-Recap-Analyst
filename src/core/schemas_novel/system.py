"""
Novel Processing Schemas - 系统元素相关
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
from datetime import datetime


class SystemCategory(BaseModel):
    """
    系统元素类别
    
    对小说中的系统元素进行分类管理。
    """
    category_id: str = Field(
        ...,
        description="类别编号（如: SC001）"
    )
    category_name: str = Field(
        ...,
        description="类别名称（如：'生存资源'、'系统货币'）"
    )
    category_desc: str = Field(
        ...,
        description="类别描述"
    )
    importance: Literal["critical", "important", "minor"] = Field(
        ...,
        description="重要程度：critical-核心/important-重要/minor-次要"
    )
    elements: List[str] = Field(
        default_factory=list,
        description="该类别下的元素列表"
    )
    tracking_strategy: str = Field(
        default="state_change",
        description="追踪策略：state_change-状态变化/quantity-数量变化/ownership-持有关系"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "category_id": "SC001",
                "category_name": "生存资源",
                "category_desc": "末世生存所需的物资和资源",
                "importance": "critical",
                "elements": ["水", "食物", "燃料", "药品"],
                "tracking_strategy": "quantity"
            }
        }


class SystemCatalog(BaseModel):
    """
    系统目录（全局）
    
    由 NovelSystemAnalyzer 工具返回，包含小说的核心系统元素分类。
    """
    novel_type: str = Field(
        ...,
        description="小说类型（如：apocalypse_survival_system、cultivation、game_world）"
    )
    novel_name: str = Field(
        default="",
        description="小说名称"
    )
    analyzed_chapters: str = Field(
        default="1-50",
        description="分析的章节范围"
    )
    categories: List[SystemCategory] = Field(
        default_factory=list,
        description="系统元素类别列表"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（如分析时间、模型信息等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "novel_type": "apocalypse_survival_system",
                "novel_name": "超凡公路",
                "analyzed_chapters": "1-50",
                "categories": [
                    {
                        "category_id": "SC001",
                        "category_name": "生存资源",
                        "importance": "critical",
                        "elements": ["水", "食物", "燃料"]
                    }
                ],
                "metadata": {
                    "processing_time": 45.2,
                    "total_elements": 15
                }
            }
        }


class SystemElementUpdate(BaseModel):
    """
    单个系统元素更新
    
    用于记录检测到的新系统元素及其归类。
    """
    element_name: str = Field(
        ...,
        description="元素名称（如：'弩箭'、'干粮'）"
    )
    category_id: str = Field(
        ...,
        description="归类的类别ID（如：'SC003'）"
    )
    category_name: str = Field(
        ...,
        description="归类的类别名称（如：'武器装备'）"
    )
    chapter_number: int = Field(
        ...,
        description="首次出现的章节号",
        ge=1
    )
    confidence: str = Field(
        default="high",
        description="归类置信度：high-高/medium-中/low-低"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "element_name": "弩箭",
                "category_id": "SC003",
                "category_name": "武器装备",
                "chapter_number": 5,
                "confidence": "high"
            }
        }


class SystemUpdateResult(BaseModel):
    """
    系统元素检测结果
    
    由 NovelSystemDetector 工具返回，包含本章新发现的系统元素。
    """
    chapter_number: int = Field(
        ...,
        description="章节号",
        ge=1
    )
    has_new_elements: bool = Field(
        default=False,
        description="是否发现新元素"
    )
    new_elements: List[SystemElementUpdate] = Field(
        default_factory=list,
        description="新发现的元素列表"
    )
    catalog_updated: bool = Field(
        default=False,
        description="系统目录是否已更新"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（如处理时间等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 5,
                "has_new_elements": True,
                "new_elements": [
                    {
                        "element_name": "弩箭",
                        "category_id": "SC003",
                        "category_name": "武器装备",
                        "chapter_number": 5,
                        "confidence": "high"
                    }
                ],
                "catalog_updated": True,
                "metadata": {
                    "processing_time": 3.2
                }
            }
        }


# ============================================================================
# 系统追踪工具数据模型 (Phase 3 - 系统追踪, 2026-02-09)
# NovelSystemTracker - 追踪每个事件中的系统元素变化
# ============================================================================

class SystemChange(BaseModel):
    """
    单个系统元素的变化记录
    
    记录某个系统元素在事件中的状态/数量变化。
    """
    element_name: str = Field(
        ...,
        description="元素名称（如：'积分'、'手弩'）"
    )
    category_id: str = Field(
        ...,
        description="所属类别ID（如：'SC001'）"
    )
    change_type: Literal["获得", "消耗", "升级", "遭遇", "状态变化"] = Field(
        ...,
        description="变化类型"
    )
    change_description: str = Field(
        ...,
        description="变化描述（如：'+50积分'、'获得手弩'、'等级1→2'）"
    )
    quantity_change: Optional[str] = Field(
        default=None,
        description="数量变化（如：'+50'、'-10'、'1→2'）"
    )
    quantity_before: Optional[str] = Field(
        default=None,
        description="变化前存量（如：'100'、'0'）"
    )
    quantity_after: Optional[str] = Field(
        default=None,
        description="变化后存量（如：'150'、'90'）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "element_name": "积分",
                "category_id": "SC001",
                "change_type": "获得",
                "change_description": "击杀丧尸获得50积分",
                "quantity_change": "+50",
                "quantity_before": "100",
                "quantity_after": "150"
            }
        }


class SystemTrackingEntry(BaseModel):
    """
    单个事件的系统追踪记录
    
    记录某个事件中涉及的所有系统元素变化。
    """
    event_id: str = Field(
        ...,
        description="事件编号（如：'000100001B'）"
    )
    event_summary: str = Field(
        ...,
        description="事件摘要"
    )
    has_system_changes: bool = Field(
        default=False,
        description="是否有系统元素变化"
    )
    system_changes: List[SystemChange] = Field(
        default_factory=list,
        description="系统元素变化列表"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "000100001B",
                "event_summary": "陈野逃离江城",
                "has_system_changes": True,
                "system_changes": [
                    {
                        "element_name": "积分",
                        "category_id": "SC001",
                        "change_type": "获得",
                        "change_description": "初始获得100积分",
                        "quantity_change": "+100"
                    }
                ]
            }
        }


class SystemTrackingResult(BaseModel):
    """
    章节系统追踪结果
    
    由 NovelSystemTracker 工具返回，包含本章所有事件的系统追踪。
    """
    chapter_number: int = Field(
        ...,
        description="章节号",
        ge=1
    )
    total_events: int = Field(
        ...,
        description="事件总数",
        ge=0
    )
    events_with_changes: int = Field(
        default=0,
        description="有系统变化的事件数",
        ge=0
    )
    tracking_entries: List[SystemTrackingEntry] = Field(
        default_factory=list,
        description="系统追踪记录列表"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（如处理时间等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "total_events": 5,
                "events_with_changes": 3,
                "tracking_entries": [
                    {
                        "event_id": "000100001B",
                        "event_summary": "陈野逃离江城",
                        "has_system_changes": True,
                        "system_changes": [...]
                    }
                ],
                "metadata": {
                    "processing_time": 15.3
                }
            }
        }


# ============================================================================
# Novel Validation Schemas (NovelValidator)
# ============================================================================

