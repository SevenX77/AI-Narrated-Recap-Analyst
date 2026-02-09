"""
Script Processing Data Schemas
脚本处理工具的基础数据结构定义

这个模块定义了SRT导入、文本提取、脚本分段等工具的输入输出数据模型。
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SrtEntry(BaseModel):
    """
    SRT字幕条目模型
    
    表示单个SRT字幕条目，包含序号、时间轴和文本内容。
    """
    index: int = Field(
        ...,
        description="SRT条目序号（从1开始）",
        ge=1
    )
    start_time: str = Field(
        ...,
        description="开始时间戳（格式：HH:MM:SS,mmm）"
    )
    end_time: str = Field(
        ...,
        description="结束时间戳（格式：HH:MM:SS,mmm）"
    )
    text: str = Field(
        ...,
        description="字幕文本内容"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "index": 1,
                "start_time": "00:00:01,240",
                "end_time": "00:00:04,380",
                "text": "夜幕降临，车队缓缓停下"
            }
        }


class SrtImportResult(BaseModel):
    """
    SRT导入结果模型
    
    由 SrtImporter 工具返回，包含导入后的文件路径和元数据。
    """
    saved_path: str = Field(
        ...,
        description="导入后的文件保存路径（data/projects/xxx/raw/ep01.srt）"
    )
    original_path: str = Field(
        ...,
        description="原始文件路径"
    )
    project_name: str = Field(
        ...,
        description="项目名称"
    )
    episode_name: str = Field(
        ...,
        description="集数名称（如 'ep01'）"
    )
    encoding: str = Field(
        ...,
        description="原始文件编码（如 'UTF-8', 'GBK'）"
    )
    entry_count: int = Field(
        ...,
        description="SRT条目数量",
        ge=0
    )
    total_duration: str = Field(
        ...,
        description="总时长（最后一条的结束时间）"
    )
    file_size: int = Field(
        ...,
        description="原始文件大小（字节）",
        ge=0
    )
    normalization_applied: List[str] = Field(
        default_factory=list,
        description="应用的规范化操作列表"
    )
    entries: Optional[List[SrtEntry]] = Field(
        None,
        description="SRT条目列表（可选，用于Workflow内存传递）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "saved_path": "data/projects/末哥超凡公路/raw/ep01.srt",
                "original_path": "分析资料/.../ep01.srt",
                "project_name": "末哥超凡公路",
                "episode_name": "ep01",
                "encoding": "UTF-8",
                "entry_count": 524,
                "total_duration": "00:05:42,360",
                "file_size": 28640,
                "normalization_applied": ["unified_newlines", "fixed_time_format"],
                "entries": None
            }
        }


class EntityStandardization(BaseModel):
    """
    实体标准化信息模型
    
    描述单个实体的标准形式及其变体。
    """
    standard_form: str = Field(
        ...,
        description="标准形式"
    )
    variants: List[str] = Field(
        default_factory=list,
        description="变体列表"
    )
    reasoning: str = Field(
        ...,
        description="选择标准形式的推理依据"
    )
    confidence: Optional[float] = Field(
        None,
        description="置信度（0-1）",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "standard_form": "上沪",
                "variants": ["上沪", "上户", "商户"],
                "reasoning": "指代上海，沪是上海简称",
                "confidence": 0.95
            }
        }


class SrtTextExtractionResult(BaseModel):
    """
    SRT文本提取结果模型
    
    由 SrtTextExtractor 工具返回，包含处理后的文本和元数据。
    """
    processed_text: str = Field(
        ...,
        description="处理后的连续文本（已添加标点，已修复实体）"
    )
    processing_mode: str = Field(
        ...,
        description="使用的处理模式：with_novel | without_novel | rule_based"
    )
    raw_text: str = Field(
        ...,
        description="原始文本（无标点，从SRT提取）"
    )
    entity_standardization: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="实体标准化信息 {category: {entity_name: EntityStandardization}}"
    )
    corrections: Dict[str, int] = Field(
        default_factory=dict,
        description="修正统计 {correction_type: count}"
    )
    processing_time: float = Field(
        ...,
        description="处理耗时（秒）",
        ge=0.0
    )
    original_chars: int = Field(
        ...,
        description="原始字符数",
        ge=0
    )
    processed_chars: int = Field(
        ...,
        description="处理后字符数",
        ge=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "processed_text": "夜幕降临，车队缓缓停下。队长走下车，警惕地环顾四周...",
                "processing_mode": "with_novel",
                "raw_text": "夜幕降临车队缓缓停下队长走下车警惕地环顾四周",
                "entity_standardization": {
                    "characters": {
                        "队长": {
                            "standard_form": "队长",
                            "variants": ["队长", "对长"],
                            "reasoning": "主要角色",
                            "confidence": 0.98
                        }
                    }
                },
                "corrections": {
                    "punctuation_added": 42,
                    "typo_fixed": 3,
                    "entity_unified": 5
                },
                "processing_time": 2.35,
                "original_chars": 1245,
                "processed_chars": 1287
            }
        }


class ScriptSegment(BaseModel):
    """
    脚本段落模型
    
    由 ScriptSegmenter 工具返回，描述单个语义段落。
    """
    index: int = Field(
        ...,
        description="段落索引（从1开始）",
        ge=1
    )
    content: str = Field(
        ...,
        description="段落文本内容"
    )
    start_time: str = Field(
        ...,
        description="开始时间戳（格式：HH:MM:SS,mmm）"
    )
    end_time: str = Field(
        ...,
        description="结束时间戳（格式：HH:MM:SS,mmm）"
    )
    sentence_count: int = Field(
        ...,
        description="句子数量",
        ge=0
    )
    char_count: int = Field(
        ...,
        description="字符数",
        ge=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "index": 1,
                "content": "夜幕降临，车队缓缓停下。队长走下车，警惕地环顾四周。",
                "start_time": "00:00:01,240",
                "end_time": "00:00:15,680",
                "sentence_count": 2,
                "char_count": 28
            }
        }


class ScriptSegmentationResult(BaseModel):
    """
    脚本分段结果模型
    
    由 ScriptSegmenter 工具返回，包含所有分段和统计信息。
    """
    segments: List[ScriptSegment] = Field(
        ...,
        description="分段列表"
    )
    total_segments: int = Field(
        ...,
        description="总段落数",
        ge=0
    )
    avg_sentence_count: float = Field(
        ...,
        description="平均每段句子数",
        ge=0.0
    )
    segmentation_mode: str = Field(
        ...,
        description="使用的分段模式：semantic（LLM语义分段）"
    )
    output_file: str = Field(
        ...,
        description="保存的 Markdown 文件路径"
    )
    processing_time: float = Field(
        ...,
        description="处理耗时（秒）",
        ge=0.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "segments": [],  # 示例省略
                "total_segments": 45,
                "avg_sentence_count": 5.2,
                "segmentation_mode": "semantic",
                "output_file": "data/projects/末哥超凡公路/script/ep01.md",
                "processing_time": 3.45
            }
        }
