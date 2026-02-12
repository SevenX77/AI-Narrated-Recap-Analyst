"""
Step Reports - 小说处理工作流的步骤报告生成

生成每个处理步骤的详细报告（Steps 1-8）。

Author: AI-Narrated Recap Analyst Team
Created: 2026-02-13 (Refactored from report_generator.py)
"""

import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from src.core.schemas_novel import (
    NovelImportResult,
    NovelMetadata,
    ChapterInfo,
    ParagraphSegmentationResult,
    AnnotatedChapter,
    SystemCatalog,
    SystemUpdateResult,
    SystemTrackingResult,
    NovelValidationReport,
    ChapterProcessingError
)

logger = logging.getLogger(__name__)


def output_step1_report(import_result: NovelImportResult, processing_dir: str):
    """输出Step 1报告"""
    report_path = Path(processing_dir) / "reports" / "step1_import_report.md"
    
    content = f"""# Step 1: 小说导入报告

## 基本信息
- **项目名称**: {import_result.project_name}
- **原始路径**: {import_result.original_path}
- **保存路径**: {import_result.saved_path}

## 文件信息
- **编码**: {import_result.encoding}
- **文件大小**: {import_result.file_size} 字节 ({import_result.file_size/1024:.2f} KB)
- **字符数**: {import_result.char_count}
- **行数**: {import_result.line_count}
- **包含BOM**: {'是' if import_result.has_bom else '否'}

## 规范化操作
{chr(10).join(f'- {op}' for op in import_result.normalization_applied)}

---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📄 Step 1 报告: {report_path}")


def output_step2_report(metadata: NovelMetadata, processing_dir: str):
    """输出Step 2报告"""
    report_path = Path(processing_dir) / "reports" / "step2_metadata_report.md"
    
    content = f"""# Step 2: 小说元数据报告

## 基本信息
- **书名**: {metadata.title}
- **作者**: {metadata.author}

## 标签
{chr(10).join(f'- {tag}' for tag in metadata.tags)}

## 简介
{metadata.introduction}

---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📄 Step 2 报告: {report_path}")


def output_step3_report(chapters: List[ChapterInfo], processing_dir: str):
    """输出Step 3报告"""
    report_path = Path(processing_dir) / "reports" / "step3_chapters_report.md"
    
    content = f"""# Step 3: 章节检测报告

## 概览
- **总章节数**: {len(chapters)}
- **总字数**: {sum((ch.word_count or 0) for ch in chapters)}

## 章节列表

| 章节号 | 标题 | 字数 | 起始行 | 结束行 |
|-------|------|------|--------|--------|
"""
    
    for ch in chapters:
        content += f"| {ch.number} | {ch.title} | {ch.word_count or 'N/A'} | {ch.start_line} | {ch.end_line or 'N/A'} |\n"
    
    content += f"""
---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📄 Step 3 报告: {report_path}")


def output_step4_report(
    segmentation_results: Dict[int, ParagraphSegmentationResult],
    processing_dir: str
):
    """输出Step 4质量分析报告（严格评分）"""
    report_path = Path(processing_dir) / "reports" / "step4_segmentation_quality.md"
    
    if not segmentation_results:
        return
    
    # 统计信息
    total_paragraphs = sum(len(seg.paragraphs) for seg in segmentation_results.values())
    a_count = sum(sum(1 for p in seg.paragraphs if p.type == "A") for seg in segmentation_results.values())
    b_count = sum(sum(1 for p in seg.paragraphs if p.type == "B") for seg in segmentation_results.values())
    c_count = sum(sum(1 for p in seg.paragraphs if p.type == "C") for seg in segmentation_results.values())
    
    avg_para = total_paragraphs/len(segmentation_results)
    a_pct = a_count/total_paragraphs*100 if total_paragraphs else 0
    b_pct = b_count/total_paragraphs*100 if total_paragraphs else 0
    c_pct = c_count/total_paragraphs*100 if total_paragraphs else 0
    
    # 质量评分（严格标准）
    quality_score = 100
    issues = []
    warnings = []
    
    # 1. ABC分布检查
    if a_pct > 40:
        issues.append(f"A类占比过高({a_pct:.1f}%)，可能存在过度识别")
        quality_score -= 15
    elif a_pct < 3 and len(segmentation_results) <= 5:
        warnings.append(f"开篇A类占比偏低({a_pct:.1f}%)，可能遗漏设定")
        quality_score -= 5
    
    if b_pct < 50:
        issues.append(f"B类占比过低({b_pct:.1f}%)，事件主线不明显")
        quality_score -= 15
    
    if c_pct > 20:
        issues.append(f"C类占比过高({c_pct:.1f}%)，可能存在误判")
        quality_score -= 10
    
    # 2. 分段粒度检查
    abnormal_chapters = []
    for chapter_num, seg in segmentation_results.items():
        para_count = len(seg.paragraphs)
        if para_count < 3:
            abnormal_chapters.append(f"第{chapter_num}章仅{para_count}段（分段不足）")
            quality_score -= 5
        elif para_count > 25:
            abnormal_chapters.append(f"第{chapter_num}章有{para_count}段（过度分段）")
            quality_score -= 3
    
    # 3. 文本还原率检查
    restoration_issues = []
    for chapter_num, seg in segmentation_results.items():
        restoration_rate = seg.metadata.get("text_restoration_rate", 100)
        if restoration_rate < 95:
            restoration_issues.append(f"第{chapter_num}章还原率{restoration_rate:.2f}%")
            quality_score -= 10
        elif restoration_rate < 99:
            warnings.append(f"第{chapter_num}章还原率{restoration_rate:.2f}%")
            quality_score -= 2
    
    # 确定等级
    if quality_score >= 90:
        grade = "A 优秀"
    elif quality_score >= 80:
        grade = "B 良好"
    elif quality_score >= 70:
        grade = "C 及格"
    elif quality_score >= 60:
        grade = "D 勉强"
    else:
        grade = "F 不合格"
    
    # 生成报告
    content = f"""# Step 4: 章节分段质量分析 ⭐

## 📊 质量评分

**{quality_score}/100 ({grade})**

---

## 整体分段统计

### 数量指标
- **处理章节数**: {len(segmentation_results)}
- **总段落数**: {total_paragraphs}
- **平均段落/章**: {avg_para:.1f}

### ABC类型分布
- **A类（设定）**: {a_count}个 ({a_pct:.1f}%)
- **B类（事件）**: {b_count}个 ({b_pct:.1f}%)
- **C类（系统）**: {c_count}个 ({c_pct:.1f}%)

---

## 🎯 分段质量分析

### 1. ABC分布合理性

"""
    
    if not issues and a_pct >= 3 and b_pct >= 50:
        content += "✅ **通过**：ABC分布符合预期\n"
    else:
        content += "⚠️ **存在问题**：\n\n"
        for issue in issues:
            content += f"- 🔴 {issue}\n"
        for warning in warnings:
            content += f"- 🟡 {warning}\n"
    
    content += "\n### 2. 各章分段详情\n\n| 章节号 | 段落数 | A类 | B类 | C类 | 评价 |\n|-------|--------|-----|-----|-----|------|\n"
    
    for chapter_num in sorted(segmentation_results.keys()):
        seg = segmentation_results[chapter_num]
        para_count = len(seg.paragraphs)
        a = sum(1 for p in seg.paragraphs if p.type == "A")
        b = sum(1 for p in seg.paragraphs if p.type == "B")
        c = sum(1 for p in seg.paragraphs if p.type == "C")
        
        # 评价
        if para_count < 3:
            eval_text = "⚠️ 分段不足"
        elif para_count > 25:
            eval_text = "⚠️ 过度分段"
        elif a == 0 and chapter_num <= 5:
            eval_text = "⚠️ 开篇缺A类"
        else:
            eval_text = "✓"
        
        content += f"| {chapter_num} | {para_count} | {a} | {b} | {c} | {eval_text} |\n"
    
    content += f"""\n### 3. 异常章节\n\n"""
    
    if abnormal_chapters:
        for abnormal in abnormal_chapters:
            content += f"- 🔴 {abnormal}\n"
    else:
        content += "✅ 无异常章节\n"
    
    content += "\n### 4. 文本还原率\n\n"
    
    if restoration_issues:
        content += "⚠️ **存在还原问题**：\n\n"
        for issue in restoration_issues:
            content += f"- 🔴 {issue}\n"
    else:
        content += "✅ **无还原问题**（所有章节还原率>99%）\n"
    
    content += "\n---\n\n## 💡 改进建议\n\n### 优先级P0（必须改进）\n"
    
    p0_suggestions = []
    if restoration_issues:
        p0_suggestions.append("修正文本还原率低的章节")
    if a_pct > 40 or (a_pct < 3 and len(segmentation_results) <= 5):
        p0_suggestions.append(f"人工抽检A类分类准确性（当前{a_pct:.1f}%）")
    
    if p0_suggestions:
        for i, sug in enumerate(p0_suggestions, 1):
            content += f"{i}. {sug}\n"
    else:
        content += "无\n"
    
    content += "\n### 优先级P1（建议改进）\n"
    
    if abnormal_chapters:
        for i, abnormal in enumerate(abnormal_chapters[:3], 1):
            content += f"{i}. {abnormal}\n"
    else:
        content += "无\n"
    
    content += f"""\n---\n\n## ✅ 总体评价\n\n**质量等级：{grade}**\n\n"""
    
    if quality_score >= 90:
        content += "- 分段粒度优秀\n- ABC分类准确\n- 可直接用于标注步骤\n"
    elif quality_score >= 80:
        content += "- 分段粒度良好\n- 存在轻微问题\n- 建议修正后进入标注步骤\n"
    elif quality_score >= 70:
        content += "- 分段粒度可接受\n- 存在明显问题\n- 必须修正关键问题后使用\n"
    else:
        content += "- 🚨 分段质量不合格\n- 建议重新处理\n"
    
    content += f"""\n---\n*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*\n*评分依据: docs/workflows/QUALITY_STANDARDS.md*\n"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📄 Step 4 质量报告: {report_path}")
    logger.info(f"   质量评分: {quality_score}/100 ({grade})")


def output_step5_report(
    annotation_results: Dict[int, AnnotatedChapter],
    processing_dir: str
):
    """输出Step 5报告"""
    report_path = Path(processing_dir) / "reports" / "step5_annotation_report.md"
    
    if not annotation_results:
        return
    
    total_events = sum(len(ann.event_timeline.events) for ann in annotation_results.values())
    total_settings = sum(len(ann.setting_library.settings) for ann in annotation_results.values())
    avg_events = total_events/len(annotation_results) if annotation_results else 0
    avg_settings = total_settings/len(annotation_results) if annotation_results else 0
    
    content = f"""# Step 5: 章节标注报告

## 概览
- **处理章节数**: {len(annotation_results)}
- **总事件数**: {total_events}
- **总设定数**: {total_settings}
- **平均事件数/章**: {avg_events:.1f}
- **平均设定数/章**: {avg_settings:.1f}

## 各章详情

| 章节号 | 事件数 | 设定数 | 时间线起点 | 时间线终点 |
|-------|--------|--------|-----------|-----------|
"""
    
    for chapter_num in sorted(annotation_results.keys()):
        ann = annotation_results[chapter_num]
        timeline = ann.event_timeline
        
        # 计算时间线范围（从events中提取）
        timeline_start = "N/A"
        timeline_end = "N/A"
        if timeline.events:
            # 获取第一个和最后一个事件的时间信息
            first_event = timeline.events[0]
            last_event = timeline.events[-1]
            if hasattr(first_event, 'time_info') and first_event.time_info:
                timeline_start = first_event.time_info
            if hasattr(last_event, 'time_info') and last_event.time_info:
                timeline_end = last_event.time_info
        
        content += (f"| {chapter_num} | {len(timeline.events)} | "
                   f"{len(ann.setting_library.settings)} | "
                   f"{timeline_start} | "
                   f"{timeline_end} |\n")
    
    content += f"""
---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📄 Step 5 报告: {report_path}")


def output_step67_report(
    system_catalog: SystemCatalog,
    system_updates: Dict[int, SystemUpdateResult],
    system_tracking: Dict[int, SystemTrackingResult],
    processing_dir: str
):
    """输出Step 6-7报告"""
    report_path = Path(processing_dir) / "reports" / "step67_system_report.md"
    
    total_new_elements = sum(len(update.new_elements) for update in system_updates.values())
    total_changes = sum(len(tracking.tracking_entries) for tracking in system_tracking.values())
    
    content = f"""# Step 6-7: 系统分析与追踪报告

## 系统目录概览（Step 6）
- **小说类型**: {system_catalog.novel_type}
- **系统类别数**: {len(system_catalog.categories)}

### 系统类别
"""
    
    for cat in system_catalog.categories:
        cat_id = cat.category_id
        cat_name = getattr(cat, 'category_name', '未命名')
        strategy = getattr(cat, 'tracking_strategy', 'state_change')
        elem_count = len(getattr(cat, 'elements', []))
        content += f"""
#### {cat_id}: {cat_name}
- **追踪策略**: {strategy}
- **元素数量**: {elem_count}
"""
    
    content += f"""
## 系统追踪概览（Step 7）
- **处理章节数**: {len(system_tracking)}
- **新增元素总数**: {total_new_elements}
- **变化记录总数**: {total_changes}

## 各章详情

| 章节号 | 新增元素 | 变化记录 |
|-------|---------|---------|
"""
    
    for chapter_num in sorted(system_tracking.keys()):
        # 安全获取new_elements计数
        update_result = system_updates.get(chapter_num)
        new_count = len(update_result.new_elements) if update_result else 0
        change_count = len(system_tracking[chapter_num].tracking_entries)
        content += f"| {chapter_num} | {new_count} | {change_count} |\n"
    
    content += f"""
---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📄 Step 6-7 报告: {report_path}")


def output_step8_report(
    validation_report: NovelValidationReport,
    processing_dir: str
):
    """输出Step 8报告"""
    report_path = Path(processing_dir) / "reports" / "step8_validation_report.md"
    
    content = f"""# Step 8: 质量验证报告

## 总体评分
**{validation_report.quality_score}/100**

## 问题列表
"""
    
    if validation_report.issues:
        for issue in validation_report.issues:
            content += f"""
### {issue.get('severity', 'info').upper()}: {issue.get('category', 'General')}
- **描述**: {issue.get('description', '')}
- **章节**: {issue.get('chapter', 'N/A')}
"""
    else:
        content += "\n✅ 未发现任何问题\n"
    
    content += f"""
## 改进建议
"""
    
    if validation_report.recommendations:
        for recommendation in validation_report.recommendations:
            content += f"- {recommendation}\n"
    else:
        content += "\n无改进建议\n"
    
    content += f"""
---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"📄 Step 8 报告: {report_path}")
