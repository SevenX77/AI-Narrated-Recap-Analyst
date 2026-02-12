"""
Novel Processing Schemas
小说处理工具的基础数据结构定义

这个包定义了小说导入、元数据提取、章节检测、分段、标注等工具的输入输出数据模型。
"""

# 基础导入和元数据
from .basic import (
    NovelImportResult,
    NormalizedNovelText,
    NovelMetadata,
    ChapterInfo,
    Paragraph,
    NovelProcessingConfig
)

# 分段相关
from .segmentation import (
    ParagraphSegment,
    ParagraphSegmentationResult,
    ParagraphAnnotation,
    AnnotatedParagraph,
    AnnotatedParagraphResult,
    SegmentationOutput
)

# 标注相关
from .annotation import (
    EventEntry,
    EventTimeline,
    SettingEntry,
    SettingLibrary,
    AnnotatedChapter,
    ParagraphFunctionalTags,
    FunctionalTagsLibrary,
    ChapterTags,
    NovelTaggingResult
)

# 系统元素相关
from .system import (
    SystemCategory,
    SystemCatalog,
    SystemElementUpdate,
    SystemUpdateResult,
    SystemChange,
    SystemTrackingEntry,
    SystemTrackingResult
)

# 验证和工作流结果
from .validation import (
    ValidationIssue,
    NovelValidationReport,
    ChapterProcessingError,
    NovelProcessingResult
)

__all__ = [
    # 基础
    "NovelImportResult",
    "NormalizedNovelText",
    "NovelMetadata",
    "ChapterInfo",
    "Paragraph",
    "NovelProcessingConfig",
    # 分段
    "ParagraphSegment",
    "ParagraphSegmentationResult",
    "ParagraphAnnotation",
    "AnnotatedParagraph",
    "AnnotatedParagraphResult",
    "SegmentationOutput",
    # 标注
    "EventEntry",
    "EventTimeline",
    "SettingEntry",
    "SettingLibrary",
    "AnnotatedChapter",
    "ParagraphFunctionalTags",
    "FunctionalTagsLibrary",
    "ChapterTags",
    "NovelTaggingResult",
    # 系统
    "SystemCategory",
    "SystemCatalog",
    "SystemElementUpdate",
    "SystemUpdateResult",
    "SystemChange",
    "SystemTrackingEntry",
    "SystemTrackingResult",
    # 验证
    "ValidationIssue",
    "NovelValidationReport",
    "ChapterProcessingError",
    "NovelProcessingResult",
]
