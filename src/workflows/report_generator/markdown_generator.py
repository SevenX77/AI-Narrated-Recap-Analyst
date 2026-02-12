"""
Markdown Generator - 小说处理工作流的Markdown文件生成

生成小说元数据、章节索引和分段章节的Markdown文件。

Author: AI-Narrated Recap Analyst Team
Created: 2026-02-13 (Refactored from report_generator.py)
"""

import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from src.core.schemas_novel import (
    NovelMetadata,
    ChapterInfo,
    ParagraphSegmentationResult
)

logger = logging.getLogger(__name__)


def generate_metadata_markdown(metadata: NovelMetadata, project_name: str):
    """生成元数据Markdown到novel文件夹"""
    novel_dir = Path("data") / "projects" / project_name / "novel"
    novel_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = novel_dir / "metadata.md"
    
    content = f"""# {metadata.title}

> **作者**: {metadata.author}

## 标签
{chr(10).join(f'`{tag}`' for tag in metadata.tags)}

## 简介

{metadata.introduction}

---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*来源: NovelProcessingWorkflow Step 2*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📄 元数据Markdown: {filepath}")


def generate_chapters_index_markdown(chapters: List[ChapterInfo], project_name: str):
    """生成章节索引Markdown到novel文件夹"""
    novel_dir = Path("data") / "projects" / project_name / "novel"
    filepath = novel_dir / "chapters_index.md"
    
    total_words = sum((ch.word_count or 0) for ch in chapters)
    
    content = f"""# 章节索引

## 概览
- **总章节数**: {len(chapters)}
- **总字数**: {total_words:,}
- **平均字数/章**: {total_words/len(chapters):.0f}

## 章节列表

| 章节 | 标题 | 字数 | Markdown文件 |
|-----|------|------|-------------|
"""
    
    for ch in chapters:
        md_file = f"chapter_{ch.number:03d}_segmented.md"
        content += f"| {ch.number} | {ch.title} | {ch.word_count or 'N/A'} | [{md_file}](./{md_file}) |\n"
    
    content += f"""
---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*来源: NovelProcessingWorkflow Step 3*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📄 章节索引: {filepath}")


def generate_chapter_markdown(
    segmentation_results: Dict[int, ParagraphSegmentationResult],
    chapters: List[ChapterInfo],
    project_name: str
):
    """生成每章分段Markdown到novel文件夹"""
    novel_dir = Path("data") / "projects" / project_name / "novel"
    
    logger.info(f"📝 生成章节分段Markdown: {len(segmentation_results)}章")
    
    # 创建章节标题映射
    chapter_titles = {ch.number: ch.title for ch in chapters}
    
    for chapter_num, seg_result in segmentation_results.items():
        chapter_title = chapter_titles.get(chapter_num, f"第{chapter_num}章")
        filepath = novel_dir / f"chapter_{chapter_num:03d}_segmented.md"
        
        # 统计ABC分布
        a_count = sum(1 for p in seg_result.paragraphs if p.type == "A")
        b_count = sum(1 for p in seg_result.paragraphs if p.type == "B")
        c_count = sum(1 for p in seg_result.paragraphs if p.type == "C")
        
        content = f"""# {chapter_title}

## 分段概览
- **总段落数**: {seg_result.total_paragraphs}
- **A类（设定）**: {a_count}
- **B类（事件）**: {b_count}
- **C类（系统）**: {c_count}

---

"""
        
        # 输出每个段落
        for para in seg_result.paragraphs:
            type_label = {
                "A": "🔷 A类-设定",
                "B": "🔶 B类-事件",
                "C": "🔸 C类-系统"
            }.get(para.type, para.type)
            
            content += f"""## 段落 {para.index} {type_label}

{para.content}

---

"""
        
        content += f"""
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*来源: NovelProcessingWorkflow Step 4*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    logger.info(f"✅ 章节Markdown生成完成: {novel_dir}/chapter_*.md")
