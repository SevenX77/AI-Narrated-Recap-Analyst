"""
Novel Processing Schemas - 分段相关
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
from datetime import datetime


class ParagraphSegment(BaseModel):
    """
    段落分段模型（用于NovelSegmenter输出）
    
    用于描述基于A/B/C原则的叙事分段结果。
    - A类-设定：跳脱时间线的设定信息（世界观、规则）
    - B类-事件：现实时间线的事件（动作、场景）
    - C类-系统：次元空间事件（系统觉醒、系统交互）
    """
    index: int = Field(
        ...,
        description="段落索引（从1开始）",
        ge=1
    )
    type: Literal["A", "B", "C"] = Field(
        ...,
        description="段落类型：A-设定, B-事件, C-系统"
    )
    content: str = Field(
        ...,
        description="完整段落文本内容（可用于还原原文）"
    )
    start_char: int = Field(
        ...,
        description="段落开始字符位置（0-based，相对于章节内容）",
        ge=0
    )
    end_char: int = Field(
        ...,
        description="段落结束字符位置（0-based，不含，相对于章节内容）",
        ge=0
    )
    start_line: Optional[int] = Field(
        None,
        description="段落开始行号（0-based，辅助定位，可选）",
        ge=0
    )
    end_line: Optional[int] = Field(
        None,
        description="段落结束行号（0-based，不含，可选）",
        ge=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "index": 1,
                "type": "B",
                "content": "夜幕降临，车队露营。血月高悬...",
                "start_char": 0,
                "end_char": 234,
                "start_line": 0,
                "end_line": 5
            }
        }



class ParagraphAnnotation(BaseModel):
    """
    段落标注模型
    
    用于存储对段落的详细分析和标注信息。
    """
    summary: str = Field(
        ...,
        description="段落内容摘要"
    )
    tags: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="标签分类（如 {'人物': ['陈野'], '物品': ['二八大杠']}）"
    )
    events: List[str] = Field(
        default_factory=list,
        description="事件列表（按时间顺序）"
    )
    priority: str = Field(
        ...,
        description="段落优先级（P0-核心/P1-重要/P2-次要）"
    )
    notes: Optional[str] = Field(
        None,
        description="额外备注"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "夜晚车队露营，陈野煮泡面并警戒",
                "tags": {
                    "人物": ["陈野"],
                    "场景": ["夜晚露营", "血月"],
                    "物品": ["泡面", "血肠"]
                },
                "events": [
                    "车队露营",
                    "血月升起",
                    "陈野煮泡面",
                    "吃饭并警戒"
                ],
                "priority": "P1",
                "notes": None
            }
        }



class AnnotatedParagraph(ParagraphSegment):
    """
    带标注的段落模型
    
    继承自 ParagraphSegment，添加了标注信息。
    """
    annotations: ParagraphAnnotation = Field(
        ...,
        description="段落标注信息"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "index": 1,
                "type": "B",
                "content": "夜幕降临...",
                "start_char": 0,
                "end_char": 234,
                "annotations": {
                    "summary": "车队夜晚露营",
                    "tags": {"人物": ["陈野"]},
                    "events": ["车队露营"],
                    "priority": "P1"
                }
            }
        }





class ParagraphSegmentationResult(BaseModel):
    """
    章节分段结果模型
    
    由 NovelSegmenter 工具返回，包含完整的段落分段信息。
    """
    chapter_number: int = Field(
        ...,
        description="章节序号",
        ge=1
    )
    total_paragraphs: int = Field(
        ...,
        description="段落总数",
        ge=0
    )
    paragraphs: List[ParagraphSegment] = Field(
        default_factory=list,
        description="段落列表（按顺序排列，可拼接还原原文）"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="分段元数据（如类型分布、处理时间等）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "total_paragraphs": 11,
                "paragraphs": [
                    {
                        "index": 1,
                        "type": "B",
                        "content": "收音机播报...",
                        "start_char": 0,
                        "end_char": 100
                    }
                ],
                "metadata": {
                    "type_distribution": {"A": 3, "B": 7, "C": 1},
                    "processing_time": 27.34,
                    "model_used": "claude-sonnet-4-5-20250929"
                }
            }
        }



class AnnotatedParagraphResult(BaseModel):
    """
    带标注的章节分段结果模型
    
    由 NovelParagraphAnnotator 工具返回。
    """
    chapter_number: int = Field(
        ...,
        description="章节序号",
        ge=1
    )
    total_paragraphs: int = Field(
        ...,
        description="段落总数",
        ge=0
    )
    paragraphs: List[AnnotatedParagraph] = Field(
        default_factory=list,
        description="带标注的段落列表"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="分段和标注元数据"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "total_paragraphs": 11,
                "paragraphs": [
                    {
                        "index": 1,
                        "type": "B",
                        "content": "收音机播报...",
                        "start_char": 0,
                        "end_char": 100,
                        "annotations": {
                            "summary": "得知上沪沦陷",
                            "tags": {"事件": ["上沪沦陷"]},
                            "events": ["收音机播报"],
                            "priority": "P0"
                        }
                    }
                ],
                "metadata": {
                    "type_distribution": {"A": 3, "B": 7, "C": 1},
                    "annotation_time": 15.2,
                    "segmentation_time": 27.34
                }
            }
        }



class SegmentationOutput(BaseModel):
    """
    NovelSegmenter 工具的完整输出（v3）
    
    包含三种格式：
    - json_result: JSON格式（用于后续程序处理）
    - markdown_content: 简洁Markdown格式（用于用户查看）
    - llm_raw_output: LLM原始输出（可选，用于调试）
    """
    json_result: ParagraphSegmentationResult = Field(
        ...,
        description="JSON格式的分段结果（用于后续程序处理）"
    )
    markdown_content: str = Field(
        ...,
        description="简洁Markdown格式（只含分段原文和类型，用于用户查看）"
    )
    llm_raw_output: Optional[str] = Field(
        None,
        description="LLM原始输出（Markdown格式，可选，用于调试）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "json_result": {
                    "chapter_number": 1,
                    "total_paragraphs": 11,
                    "paragraphs": [...],
                    "metadata": {}
                },
                "markdown_content": "# 第1章：车队第一铁律\n\n---\n\n## 段落 1 [B类-事件]\n\n（完整段落内容）\n\n---\n...",
                "llm_raw_output": "- **段落1（B类-事件）**：...\n  行号：1-5"
            }
        }


# ============================================================================
# 小说标注工具数据模型 (v4, 2026-02-09)
# NovelAnnotator - 事件时间线 + 设定知识库
# ============================================================================



