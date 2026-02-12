"""
测试NovelSystemTracker工具

测试目标：
1. 验证系统追踪功能
2. 生成系统追踪表
3. 测试完整Pipeline: Annotator → Detector → Tracker
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_system_tracker import NovelSystemTracker
from src.core.schemas_novel import (
    ParagraphSegmentationResult,
    SystemCatalog,
    AnnotatedChapter,
    SystemTrackingResult
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主测试流程"""
    logger.info("=== NovelSystemTracker 测试开始 ===")
    
    # 1. 加载测试数据
    logger.info("\n=== Step 1: 加载测试数据 ===")
    
    # 加载标注结果
    annotation_path = project_root / "output/temp/novel_annotation_test_20260209_195255/chpt_0001_annotation.json"
    if not annotation_path.exists():
        logger.error(f"Annotation file not found: {annotation_path}")
        return
    
    with open(annotation_path, 'r', encoding='utf-8') as f:
        annotation_data = json.load(f)
    annotated_chapter = AnnotatedChapter(**annotation_data)
    logger.info(f"Loaded annotation: Chapter {annotated_chapter.chapter_number}, {len(annotated_chapter.event_timeline.events)} events")
    
    # 加载更新后的系统目录
    catalog_path = project_root / "output/temp/novel_system_detector_test/system_catalog_updated.json"
    if not catalog_path.exists():
        logger.warning(f"Updated catalog not found, using original")
        catalog_path = project_root / "output/temp/novel_system_analysis/system_catalog.json"
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)
    system_catalog = SystemCatalog(**catalog_data)
    logger.info(f"Loaded system catalog: {len(system_catalog.categories)} categories, {catalog_data['metadata']['total_elements']} elements")
    
    # 2. 运行NovelSystemTracker
    logger.info("\n=== Step 2: 运行NovelSystemTracker ===")
    tracker = NovelSystemTracker(provider="claude")
    
    tracking_result = tracker.execute(
        annotated_chapter=annotated_chapter,
        system_catalog=system_catalog
    )
    
    # 3. 输出追踪结果
    logger.info("\n=== Step 3: 追踪结果 ===")
    logger.info(f"章节: {tracking_result.chapter_number}")
    logger.info(f"事件总数: {tracking_result.total_events}")
    logger.info(f"有变化的事件: {tracking_result.events_with_changes}")
    logger.info(f"处理时间: {tracking_result.metadata.get('processing_time', 0)}s")
    
    logger.info("\n事件追踪详情:")
    for entry in tracking_result.tracking_entries:
        status = "✅ 有变化" if entry.has_system_changes else "⚪ 无变化"
        logger.info(f"  {status} | {entry.event_id}: {entry.event_summary}")
        if entry.has_system_changes:
            for change in entry.system_changes:
                qty = f" ({change.quantity_change})" if change.quantity_change else ""
                stock = ""
                if change.quantity_before is not None or change.quantity_after is not None:
                    before = change.quantity_before if change.quantity_before else "?"
                    after = change.quantity_after if change.quantity_after else "?"
                    stock = f" [存量: {before}→{after}]"
                logger.info(f"      - {change.element_name}: {change.change_type}{qty}{stock}")
    
    # 4. 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / f"output/temp/novel_system_tracker_test_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存JSON
    json_path = output_dir / f"chpt_{annotated_chapter.chapter_number:04d}_tracking.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(tracking_result.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"\nSaved tracking result: {json_path}")
    
    # 生成Markdown报告
    md_path = output_dir / f"chpt_{annotated_chapter.chapter_number:04d}_tracking_report.md"
    md_content = generate_tracking_markdown(tracking_result)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    logger.info(f"Saved markdown report: {md_path}")
    
    # 生成系统追踪表（表格格式）
    table_path = output_dir / f"chpt_{annotated_chapter.chapter_number:04d}_tracking_table.md"
    table_content = generate_tracking_table(tracking_result)
    with open(table_path, 'w', encoding='utf-8') as f:
        f.write(table_content)
    logger.info(f"Saved tracking table: {table_path}")
    
    logger.info("\n=== 测试完成 ===")
    logger.info(f"输出目录: {output_dir}")


def generate_tracking_markdown(tracking: SystemTrackingResult) -> str:
    """生成追踪结果Markdown报告"""
    lines = [
        f"# 系统追踪报告 - 第{tracking.chapter_number}章",
        "",
        f"**处理时间**: {tracking.metadata.get('processing_time', 0)}s",
        f"**模型**: {tracking.metadata.get('model_used', 'unknown')}",
        "",
        "---",
        "",
        "## 追踪摘要",
        "",
        f"- **事件总数**: {tracking.total_events}",
        f"- **有变化的事件**: {tracking.events_with_changes}",
        f"- **无变化的事件**: {tracking.total_events - tracking.events_with_changes}",
        "",
        "---",
        ""
    ]
    
    # 逐事件展示
    lines.append("## 事件追踪详情")
    lines.append("")
    
    for i, entry in enumerate(tracking.tracking_entries, 1):
        status_icon = "✅" if entry.has_system_changes else "⚪"
        lines.append(f"### {status_icon} 事件{i}: {entry.event_id}")
        lines.append("")
        lines.append(f"**摘要**: {entry.event_summary}")
        lines.append("")
        
        if entry.has_system_changes:
            lines.append("**系统变化**:")
            lines.append("")
            for j, change in enumerate(entry.system_changes, 1):
                lines.append(f"#### 变化{j}: {change.element_name}")
                lines.append("")
                lines.append(f"- **类别**: {change.category_id}")
                lines.append(f"- **变化类型**: {change.change_type}")
                lines.append(f"- **描述**: {change.change_description}")
                if change.quantity_change:
                    lines.append(f"- **数量变化**: `{change.quantity_change}`")
                if change.quantity_before is not None or change.quantity_after is not None:
                    before = change.quantity_before if change.quantity_before else "未知"
                    after = change.quantity_after if change.quantity_after else "未知"
                    lines.append(f"- **存量变化**: `{before}` → `{after}`")
                lines.append("")
        else:
            lines.append("**系统变化**: 无")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)


def generate_tracking_table(tracking: SystemTrackingResult) -> str:
    """生成系统追踪表（表格格式）"""
    lines = [
        f"# 系统追踪表 - 第{tracking.chapter_number}章",
        "",
        "## 表格视图",
        "",
        "| 事件ID | 事件摘要 | 系统变化 | 元素 | 变化类型 | 数量变化 | 存量变化 | 变化描述 |",
        "|--------|---------|---------|------|---------|---------|---------|---------|"
    ]
    
    for entry in tracking.tracking_entries:
        if not entry.has_system_changes:
            # 无变化的事件
            lines.append(f"| {entry.event_id} | {entry.event_summary} | ⚪ 无 | - | - | - | - | - |")
        else:
            # 有变化的事件
            for i, change in enumerate(entry.system_changes):
                event_id = entry.event_id if i == 0 else ""
                event_summary = entry.event_summary if i == 0 else ""
                has_change = "✅ 有" if i == 0 else ""
                
                quantity = change.quantity_change if change.quantity_change else "-"
                
                # 存量变化
                stock = "-"
                if change.quantity_before is not None or change.quantity_after is not None:
                    before = change.quantity_before if change.quantity_before else "?"
                    after = change.quantity_after if change.quantity_after else "?"
                    stock = f"`{before}→{after}`"
                
                lines.append(f"| {event_id} | {event_summary} | {has_change} | {change.element_name} | {change.change_type} | `{quantity}` | {stock} | {change.change_description} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 统计信息")
    lines.append("")
    lines.append(f"- **事件总数**: {tracking.total_events}")
    lines.append(f"- **有变化的事件**: {tracking.events_with_changes} ({tracking.events_with_changes/tracking.total_events*100:.1f}%)")
    lines.append(f"- **无变化的事件**: {tracking.total_events - tracking.events_with_changes}")
    
    # 按类型统计变化
    change_type_count = {}
    for entry in tracking.tracking_entries:
        for change in entry.system_changes:
            change_type_count[change.change_type] = change_type_count.get(change.change_type, 0) + 1
    
    if change_type_count:
        lines.append("")
        lines.append("## 变化类型统计")
        lines.append("")
        for change_type, count in sorted(change_type_count.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{change_type}**: {count}次")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    main()
