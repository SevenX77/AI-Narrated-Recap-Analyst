"""
Novel Processing Schemas - 基础导入和元数据
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

class NovelProcessingConfig(BaseModel):
    """
    小说处理工作流配置
    
    控制并行处理、功能开关、章节范围等参数。
    """
    # 并行处理配置
    enable_parallel: bool = Field(
        default=True,
        description="是否启用并行处理（章节级别）"
    )
    max_concurrent_chapters: int = Field(
        default=2,
        description="最大并发章节数（建议1-2避免API限流）",
        ge=1,
        le=10
    )
    
    # 重试与限流控制
    retry_on_error: bool = Field(
        default=True,
        description="API调用失败时是否自动重试"
    )
    max_retries: int = Field(
        default=3,
        description="最大重试次数（每次调用）",
        ge=0,
        le=10
    )
    retry_delay: float = Field(
        default=2.0,
        description="重试基础延迟（秒），使用指数退避策略",
        ge=0.5,
        le=60.0
    )
    request_delay: float = Field(
        default=1.5,
        description="请求之间的延迟（秒），避免触发API限流",
        ge=0.0,
        le=10.0
    )
    
    # 功能开关
    enable_functional_tags: bool = Field(
        default=False,
        description="是否启用功能性标签标注（NovelAnnotator Pass 3）"
    )
    enable_system_analysis: bool = Field(
        default=True,
        description="是否启用系统元素分析与追踪"
    )
    
    # 章节处理范围
    chapter_range: Optional[tuple] = Field(
        default=None,
        description="处理指定章节范围，格式：(start, end)，如 (1, 10) 表示处理第1-10章"
    )
    
    # 错误处理
    continue_on_error: bool = Field(
        default=True,
        description="单个章节处理失败时是否继续处理其他章节"
    )
    save_intermediate_results: bool = Field(
        default=True,
        description="是否保存中间结果（用于断点续传）"
    )
    
    # LLM配置
    segmentation_provider: str = Field(
        default="claude",
        description="分段工具使用的LLM Provider（claude/deepseek）"
    )
    annotation_provider: str = Field(
        default="claude",
        description="标注工具使用的LLM Provider（claude/deepseek）"
    )
    
    # 输出配置
    output_markdown_reports: bool = Field(
        default=True,
        description="是否在关键节点输出Markdown报告"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "enable_parallel": True,
                "max_concurrent_chapters": 3,
                "enable_functional_tags": False,
                "enable_system_analysis": True,
                "chapter_range": [1, 10],
                "continue_on_error": True,
                "save_intermediate_results": True,
                "segmentation_provider": "claude",
                "annotation_provider": "claude",
                "output_markdown_reports": True
            }
        }


