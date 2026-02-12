"""
自动拆分 schemas_novel.py 的脚本

将 1824 行的 schemas_novel.py 拆分成 5 个功能模块
"""
import re
from pathlib import Path
import os

# 切换到项目根目录
os.chdir('/Users/sevenx/Documents/coding/AI-Narrated Recap Analyst')

# 读取原文件
src_file = Path('src/core/schemas_novel.py')
with open(src_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取 header (imports)
imports = """from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
from datetime import datetime
"""

# 找到所有类定义
class_pattern = r'(class \w+\(BaseModel\):.*?)(?=\n\nclass |\Z)'
classes = {}
for match in re.finditer(class_pattern, content, re.DOTALL):
    class_text = match.group(1)
    class_name = re.search(r'class (\w+)\(BaseModel\):', class_text).group(1)
    classes[class_name] = class_text

# 分组定义
groups = {
    'basic.py': {
        'description': '基础导入和元数据',
        'classes': [
            'NovelImportResult',
            'NormalizedNovelText',
            'NovelMetadata',
            'ChapterInfo',
            'Paragraph',
            'NovelProcessingConfig'
        ]
    },
    'segmentation.py': {
        'description': '分段相关',
        'classes': [
            'ParagraphSegment',
            'ParagraphSegmentationResult',
            'ParagraphAnnotation',
            'AnnotatedParagraphResult',
            'SegmentationOutput'
        ]
    },
    'annotation.py': {
        'description': '标注相关（事件、设定、功能标签）',
        'classes': [
            'EventEntry',
            'EventTimeline',
            'SettingEntry',
            'SettingLibrary',
            'AnnotatedChapter',
            'ParagraphFunctionalTags',
            'FunctionalTagsLibrary',
            'ChapterTags',
            'NovelTaggingResult'
        ]
    },
    'system.py': {
        'description': '系统元素相关',
        'classes': [
            'SystemCategory',
            'SystemCatalog',
            'SystemElementUpdate',
            'SystemUpdateResult',
            'SystemChange',
            'SystemTrackingEntry',
            'SystemTrackingResult'
        ]
    },
    'validation.py': {
        'description': '验证和工作流结果',
        'classes': [
            'ValidationIssue',
            'NovelValidationReport',
            'ChapterProcessingError',
            'NovelProcessingResult'
        ]
    }
}

# 创建输出目录
output_dir = Path('src/core/schemas_novel')
output_dir.mkdir(exist_ok=True)

# 生成每个子模块
for filename, group_info in groups.items():
    file_path = output_dir / filename
    
    # 构建文件内容
    file_content = f'''"""
Novel Processing Schemas - {group_info['description']}
"""

{imports}

'''
    
    # 添加类定义
    for class_name in group_info['classes']:
        if class_name in classes:
            file_content += classes[class_name] + '\n\n'
        else:
            print(f"⚠️  警告: 类 {class_name} 未找到")
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(file_content)
    
    lines = file_content.count('\n')
    print(f"✅ 创建: {filename} ({len(group_info['classes'])} 个类, ~{lines} 行)")

# 生成 __init__.py
init_content = '''"""
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
'''

init_path = output_dir / '__init__.py'
with open(init_path, 'w', encoding='utf-8') as f:
    f.write(init_content)

print(f"✅ 创建: __init__.py")

print(f"\n🎉 拆分完成！")
print(f"   原文件: {src_file} (1824 行)")
print(f"   新目录: {output_dir}/ (6 个文件)")
