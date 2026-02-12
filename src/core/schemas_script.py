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
    category: Optional[str] = Field(
        None,
        description="段落分类（A=Setting设定, B=Event事件, C=System系统）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "index": 1,
                "content": "夜幕降临，车队缓缓停下。队长走下车，警惕地环顾四周。",
                "start_time": "00:00:01,240",
                "end_time": "00:00:15,680",
                "sentence_count": 2,
                "char_count": 28,
                "category": "B"
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


# ============================================================================
# Script Validation Schemas (ScriptValidator)
# ============================================================================

class ScriptValidationIssue(BaseModel):
    """
    脚本验证问题模型
    
    表示质量验证中发现的单个问题。
    """
    severity: str = Field(
        ...,
        description="严重程度（error/warning/info）"
    )
    category: str = Field(
        ...,
        description="问题类别（timeline/text/segmentation）"
    )
    description: str = Field(
        ...,
        description="问题描述"
    )
    location: Optional[str] = Field(
        None,
        description="问题位置（如SRT序号、段落号）"
    )
    recommendation: Optional[str] = Field(
        None,
        description="改进建议"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "severity": "warning",
                "category": "timeline",
                "description": "时间轴存在间隔：00:05:23 到 00:05:26（3秒间隔）",
                "location": "srt_entry_125_126",
                "recommendation": "检查是否存在缺失字幕"
            }
        }


class ScriptValidationReport(BaseModel):
    """
    脚本处理质量验证报告
    
    由 ScriptValidator 工具返回，包含完整的质量评估结果。
    """
    episode_name: str = Field(
        ...,
        description="集数名称（如 ep01）"
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
    timeline_check: Dict[str, Any] = Field(
        default_factory=dict,
        description="时间轴连续性检查结果"
    )
    text_check: Dict[str, Any] = Field(
        default_factory=dict,
        description="文本完整性检查结果"
    )
    segmentation_check: Dict[str, Any] = Field(
        default_factory=dict,
        description="分段合理性检查结果"
    )
    
    # 问题与建议
    issues: List[ScriptValidationIssue] = Field(
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
                "episode_name": "ep01",
                "quality_score": 92.0,
                "is_valid": True,
                "timeline_check": {
                    "passed": True,
                    "total_entries": 850,
                    "gaps": [],
                    "overlaps": []
                },
                "text_check": {
                    "passed": True,
                    "coverage": 0.98,
                    "missing_chars": 150
                },
                "segmentation_check": {
                    "passed": True,
                    "total_segments": 15,
                    "avg_duration": "00:01:20"
                },
                "issues": [],
                "recommendations": ["脚本质量优秀，无需改进"]
            }
        }


# ============================================================================
# Hook Detection Schemas (HookDetector)
# ============================================================================

class HookDetectionResult(BaseModel):
    """
    Hook检测结果模型
    
    由 HookDetector 工具返回，包含Hook边界检测的完整信息。
    """
    has_hook: bool = Field(
        ...,
        description="是否存在Hook"
    )
    hook_end_time: Optional[str] = Field(
        None,
        description="Hook结束时间（SRT格式：HH:MM:SS,mmm）"
    )
    body_start_time: str = Field(
        ...,
        description="Body起点时间（SRT格式）"
    )
    confidence: float = Field(
        ...,
        description="检测置信度（0.0-1.0）",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        ...,
        description="判断理由"
    )
    hook_segment_indices: List[int] = Field(
        default_factory=list,
        description="Hook部分的段落索引列表"
    )
    body_segment_indices: List[int] = Field(
        default_factory=list,
        description="Body部分的段落索引列表"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "has_hook": True,
                "hook_end_time": "00:00:45,500",
                "body_start_time": "00:00:45,600",
                "confidence": 0.92,
                "reasoning": "前45秒为概括性预告，从45.6秒开始进入线性叙事",
                "hook_segment_indices": [0, 1, 2],
                "body_segment_indices": [3, 4, 5, 6, 7, 8, 9, 10],
                "metadata": {
                    "hook_duration": 45.5,
                    "processing_time": 5.2
                }
            }
        }


# ============================================================================
# Hook Content Analysis Schemas (HookContentAnalyzer)
# ============================================================================

class LayeredContent(BaseModel):
    """
    分层内容模型
    
    表示Hook或简介的分层提取结果。
    """
    world_building: List[str] = Field(
        default_factory=list,
        description="世界观设定列表"
    )
    game_mechanics: List[str] = Field(
        default_factory=list,
        description="系统机制列表"
    )
    items_equipment: List[str] = Field(
        default_factory=list,
        description="道具装备列表"
    )
    plot_events: List[str] = Field(
        default_factory=list,
        description="情节事件列表"
    )


class HookAnalysisResult(BaseModel):
    """
    Hook来源分析结果模型
    
    由 HookContentAnalyzer 工具返回，包含Hook内容来源分析。
    """
    source_type: str = Field(
        ...,
        description="来源类型：简介/章节/独立创作"
    )
    similarity_score: float = Field(
        ...,
        description="与Novel简介的相似度（0.0-1.0）",
        ge=0.0,
        le=1.0
    )
    matched_chapter: Optional[int] = Field(
        None,
        description="如果来源于章节，章节号"
    )
    hook_layers: LayeredContent = Field(
        ...,
        description="Hook的分层内容"
    )
    intro_layers: LayeredContent = Field(
        ...,
        description="简介的分层内容"
    )
    layer_similarity: Dict[str, float] = Field(
        default_factory=dict,
        description="各层的相似度"
    )
    alignment_strategy: str = Field(
        ...,
        description="建议的对齐策略：direct_intro/chapter_based/skip"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_type": "简介",
                "similarity_score": 0.87,
                "matched_chapter": None,
                "hook_layers": {
                    "world_building": ["末日世界", "诡异生物"],
                    "game_mechanics": ["序列超凡体系"],
                    "items_equipment": [],
                    "plot_events": ["江城沦陷"]
                },
                "intro_layers": {
                    "world_building": ["末日世界", "诡异生物"],
                    "game_mechanics": ["序列超凡体系"],
                    "items_equipment": [],
                    "plot_events": []
                },
                "layer_similarity": {
                    "world_building": 0.95,
                    "game_mechanics": 0.90,
                    "items_equipment": 0.0,
                    "plot_events": 0.5
                },
                "alignment_strategy": "direct_intro",
                "metadata": {
                    "processing_time": 8.3
                }
            }
        }


# ============================================================================
# Workflow Schemas (ScriptProcessingWorkflow)
# ============================================================================

class ScriptProcessingConfig(BaseModel):
    """
    脚本处理工作流配置
    
    控制功能开关、重试策略、LLM选择等参数。
    """
    # 功能开关
    enable_hook_detection: bool = Field(
        default=True,
        description="是否启用Hook检测（仅ep01）"
    )
    enable_hook_analysis: bool = Field(
        default=False,
        description="是否启用Hook内容分析（需要Novel参考）"
    )
    enable_abc_classification: bool = Field(
        default=True,
        description="是否启用ABC类分段（ScriptSegmenter Pass 3）"
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
        default=1.0,
        description="请求之间的延迟（秒），避免触发API限流",
        ge=0.0,
        le=10.0
    )
    
    # LLM配置
    text_extraction_provider: str = Field(
        default="deepseek",
        description="文本提取工具使用的LLM Provider（deepseek/claude）"
    )
    hook_detection_provider: str = Field(
        default="deepseek",
        description="Hook检测工具使用的LLM Provider（deepseek/claude）"
    )
    segmentation_provider: str = Field(
        default="deepseek",
        description="分段工具使用的LLM Provider（deepseek/claude）"
    )
    
    # 错误处理
    continue_on_error: bool = Field(
        default=False,
        description="某个步骤失败时是否继续后续步骤（通常为False）"
    )
    save_intermediate_results: bool = Field(
        default=True,
        description="是否保存中间结果（用于调试）"
    )
    
    # 输出配置
    output_markdown_reports: bool = Field(
        default=True,
        description="是否输出Markdown格式的报告"
    )
    
    # 质量门禁
    min_quality_score: int = Field(
        default=75,
        description="最低质量评分（0-100），低于此分数将发出警告",
        ge=0,
        le=100
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "enable_hook_detection": True,
                "enable_hook_analysis": False,
                "enable_abc_classification": True,
                "retry_on_error": True,
                "max_retries": 3,
                "retry_delay": 2.0,
                "request_delay": 1.0,
                "text_extraction_provider": "deepseek",
                "hook_detection_provider": "deepseek",
                "segmentation_provider": "deepseek",
                "continue_on_error": False,
                "save_intermediate_results": True,
                "output_markdown_reports": True,
                "min_quality_score": 75
            }
        }


class ScriptProcessingError(BaseModel):
    """
    脚本处理错误信息
    """
    step: str = Field(
        ...,
        description="失败的步骤（如 'srt_import', 'text_extraction'）"
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


class ScriptProcessingResult(BaseModel):
    """
    脚本处理完整结果
    
    包含从SRT导入到质量验证的所有处理结果。
    """
    project_name: str = Field(
        ...,
        description="项目名称"
    )
    episode_name: str = Field(
        ...,
        description="集数名称（如 ep01）"
    )
    success: bool = Field(
        default=True,
        description="处理是否成功"
    )
    
    # Phase 1: SRT导入
    import_result: Optional[SrtImportResult] = Field(
        None,
        description="SRT导入结果"
    )
    
    # Phase 2: 文本提取
    extraction_result: Optional[SrtTextExtractionResult] = Field(
        None,
        description="文本提取结果"
    )
    
    # Phase 3: Hook检测（可选，仅ep01）
    hook_detection_result: Optional[HookDetectionResult] = Field(
        None,
        description="Hook检测结果（仅ep01）"
    )
    
    # Phase 4: Hook内容分析（可选）
    hook_analysis_result: Optional[HookAnalysisResult] = Field(
        None,
        description="Hook内容分析结果（需要Novel参考）"
    )
    
    # Phase 5: 脚本分段
    segmentation_result: Optional[ScriptSegmentationResult] = Field(
        None,
        description="脚本分段结果"
    )
    
    # Phase 6: 质量验证
    validation_report: Optional[ScriptValidationReport] = Field(
        None,
        description="质量验证报告"
    )
    
    # 处理统计
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
    
    # 错误记录
    errors: List[ScriptProcessingError] = Field(
        default_factory=list,
        description="处理过程中的错误列表"
    )
    
    # 元数据
    config_used: Optional[Dict[str, Any]] = Field(
        None,
        description="使用的配置参数"
    )
    processing_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="处理时间戳"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "天命桃花_test",
                "episode_name": "ep01",
                "success": True,
                "import_result": {},
                "extraction_result": {},
                "hook_detection_result": {},
                "segmentation_result": {},
                "validation_report": {},
                "processing_time": 180.5,
                "llm_calls_count": 5,
                "total_cost": 0.15,
                "errors": []
            }
        }
