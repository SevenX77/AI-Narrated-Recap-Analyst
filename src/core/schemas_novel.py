"""
Novel Processing Data Schemas
小说处理工具的基础数据结构定义

这个模块定义了小说导入、元数据提取、章节检测等工具的输入输出数据模型。
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
from datetime import datetime


class NovelImportResult(BaseModel):
    """
    小说导入结果模型
    
    由 NovelImporter 工具返回，包含导入后的文件路径和元数据。
    """
    saved_path: str = Field(
        ...,
        description="导入后的文件保存路径（data/projects/xxx/raw/novel.txt）"
    )
    original_path: str = Field(
        ...,
        description="原始文件路径"
    )
    project_name: str = Field(
        ...,
        description="项目名称"
    )
    encoding: str = Field(
        ...,
        description="原始文件编码（如 'UTF-8', 'GBK', 'GB2312'）"
    )
    file_size: int = Field(
        ...,
        description="原始文件大小（字节）",
        ge=0
    )
    line_count: int = Field(
        ...,
        description="文本行数（按 \\n 分割）",
        ge=0
    )
    char_count: int = Field(
        ...,
        description="字符数（不含空白字符）",
        ge=0
    )
    has_bom: bool = Field(
        ...,
        description="原始文件是否包含 BOM 标记"
    )
    normalization_applied: List[str] = Field(
        default_factory=list,
        description="应用的规范化操作列表（如 ['removed_bom', 'unified_newlines']）"
    )
    content: Optional[str] = Field(
        None,
        description="文本内容（可选，用于 Workflow 内存传递）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "saved_path": "data/projects/末哥超凡公路/raw/novel.txt",
                "original_path": "分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生.txt",
                "project_name": "末哥超凡公路",
                "encoding": "GBK",
                "file_size": 512000,
                "line_count": 3420,
                "char_count": 245830,
                "has_bom": True,
                "normalization_applied": ["removed_bom", "unified_newlines"],
                "content": None
            }
        }


class NormalizedNovelText(BaseModel):
    """
    规范化的小说文本数据模型
    
    由 NovelImporter 工具返回，包含规范化后的文本内容及元数据。
    """
    content: str = Field(
        ...,
        description="规范化后的文本内容（UTF-8编码，统一换行符）"
    )
    encoding: str = Field(
        ...,
        description="原始文件编码（如 'UTF-8', 'GBK', 'GB2312'）"
    )
    file_size: int = Field(
        ...,
        description="原始文件大小（字节）",
        ge=0
    )
    line_count: int = Field(
        ...,
        description="文本行数（按 \\n 分割）",
        ge=0
    )
    char_count: int = Field(
        ...,
        description="字符数（不含空白字符）",
        ge=0
    )
    has_bom: bool = Field(
        ...,
        description="原始文件是否包含 BOM 标记"
    )
    normalization_applied: List[str] = Field(
        default_factory=list,
        description="应用的规范化操作列表（如 ['removed_bom', 'unified_newlines']）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Title: 超凡公路\nAuthor: 末哥\n\n简介:\n...",
                "encoding": "GBK",
                "file_size": 512000,
                "line_count": 3420,
                "char_count": 245830,
                "has_bom": True,
                "normalization_applied": ["removed_bom", "unified_newlines", "stripped_whitespace"]
            }
        }


class NovelMetadata(BaseModel):
    """
    小说元数据模型
    
    由 NovelMetadataExtractor 工具返回。
    """
    title: str = Field(
        ...,
        description="小说标题"
    )
    author: str = Field(
        ...,
        description="作者名"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="小说标签列表（如 ['题材新颖', '非无脑爽文']）"
    )
    introduction: str = Field(
        ...,
        description="小说简介（已过滤标签和元信息）"
    )
    chapter_count: Optional[int] = Field(
        None,
        description="总章节数（可选，由 NovelChapterDetector 填充）",
        ge=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "超凡公路",
                "author": "末哥",
                "tags": ["题材新颖", "非无脑爽文", "非无敌", "序列魔药"],
                "introduction": "末世降临，诡异横行...",
                "chapter_count": 10
            }
        }


class ChapterInfo(BaseModel):
    """
    章节信息模型
    
    由 NovelChapterDetector 工具返回，描述单个章节的位置和元数据。
    """
    number: int = Field(
        ...,
        description="章节序号（从1开始）",
        ge=1
    )
    title: str = Field(
        ...,
        description="章节标题"
    )
    start_line: int = Field(
        ...,
        description="章节开始行号（0-based）",
        ge=0
    )
    end_line: Optional[int] = Field(
        None,
        description="章节结束行号（0-based，不含），None表示到文件末尾",
        ge=0
    )
    start_char: int = Field(
        ...,
        description="章节开始字符位置（0-based）",
        ge=0
    )
    end_char: Optional[int] = Field(
        None,
        description="章节结束字符位置（0-based，不含），None表示到文件末尾",
        ge=0
    )
    word_count: Optional[int] = Field(
        None,
        description="章节字数",
        ge=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "number": 1,
                "title": "车队第一铁律",
                "start_line": 120,
                "end_line": 450,
                "start_char": 5430,
                "end_char": 18920,
                "word_count": 3500
            }
        }


class Paragraph(BaseModel):
    """
    段落模型
    
    由 NovelSegmenter 工具返回，描述单个自然段落。
    """
    index: int = Field(
        ...,
        description="段落索引（从0开始）",
        ge=0
    )
    content: str = Field(
        ...,
        description="段落文本内容"
    )
    paragraph_type: str = Field(
        ...,
        description="段落类型：dialogue（对话）、narrative（叙述）、description（描写）"
    )
    start_line: int = Field(
        ...,
        description="段落开始行号（0-based）",
        ge=0
    )
    end_line: int = Field(
        ...,
        description="段落结束行号（0-based，不含）",
        ge=0
    )
    char_count: int = Field(
        ...,
        description="段落字符数",
        ge=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "index": 0,
                "content": "夜幕降临，车队缓缓停下。",
                "paragraph_type": "narrative",
                "start_line": 150,
                "end_line": 152,
                "char_count": 15
            }
        }


# ============================================================================
# 新版分段工具数据模型 (v3, 2026-02-09)
# ============================================================================

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
