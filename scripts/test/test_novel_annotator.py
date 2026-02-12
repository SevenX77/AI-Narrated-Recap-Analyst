"""
测试NovelAnnotator工具

测试目标：
1. 读取NovelSegmenter的输出JSON
2. 调用NovelAnnotator进行标注
3. 输出事件时间线表和设定知识库
4. 保存JSON和Markdown格式
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_annotator import NovelAnnotator
from src.core.schemas_novel import ParagraphSegmentationResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_segmentation_result(json_path: Path) -> ParagraphSegmentationResult:
    """加载NovelSegmenter的JSON输出"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return ParagraphSegmentationResult(**data)


def save_annotation_result(
    annotated_chapter,
    output_dir: Path,
    chapter_number: int
):
    """保存标注结果"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 保存完整JSON
    json_path = output_dir / f"chpt_{chapter_number:04d}_annotation.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(annotated_chapter.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"Saved JSON: {json_path}")
    
    # 2. 保存事件表（Markdown）
    event_md_path = output_dir / f"chpt_{chapter_number:04d}_events.md"
    event_md = generate_event_markdown(annotated_chapter.event_timeline)
    with open(event_md_path, 'w', encoding='utf-8') as f:
        f.write(event_md)
    logger.info(f"Saved event table: {event_md_path}")
    
    # 3. 保存设定表（Markdown）
    setting_md_path = output_dir / f"chpt_{chapter_number:04d}_settings.md"
    setting_md = generate_setting_markdown(annotated_chapter.setting_library)
    with open(setting_md_path, 'w', encoding='utf-8') as f:
        f.write(setting_md)
    logger.info(f"Saved setting table: {setting_md_path}")
    
    # 4. 保存功能性标签表（Markdown）
    if annotated_chapter.functional_tags:
        functional_tags_md_path = output_dir / f"chpt_{chapter_number:04d}_functional_tags.md"
        functional_tags_md = generate_functional_tags_markdown(annotated_chapter.functional_tags)
        with open(functional_tags_md_path, 'w', encoding='utf-8') as f:
            f.write(functional_tags_md)
        logger.info(f"Saved functional tags table: {functional_tags_md_path}")


def generate_event_markdown(event_timeline) -> str:
    """生成事件表Markdown"""
    lines = [
        f"# 第{event_timeline.chapter_number}章 - 事件时间线表",
        "",
        f"**总事件数**: {event_timeline.total_events}",
        f"**类型分布**: {event_timeline.metadata.get('type_distribution', {})}",
        "",
        "---",
        ""
    ]
    
    for event in event_timeline.events:
        lines.append(f"## 事件 {event.event_id}")
        lines.append("")
        lines.append(f"**概括**: {event.event_summary}")
        lines.append(f"**类型**: {event.event_type}类")
        lines.append(f"**包含段落**: {event.paragraph_indices}")
        lines.append(f"**地点**: {event.location}")
        lines.append(f"**地点变化**: {event.location_change}")
        lines.append(f"**时间**: {event.time}")
        lines.append(f"**时间变化**: {event.time_change}")
        lines.append("")
        
        # 显示段落内容（折叠）
        lines.append("<details>")
        lines.append("<summary>查看段落内容</summary>")
        lines.append("")
        for content in event.paragraph_contents:
            lines.append(content)
            lines.append("")
        lines.append("</details>")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)


def generate_setting_markdown(setting_library) -> str:
    """生成设定表Markdown"""
    lines = [
        f"# 第{setting_library.chapter_number}章 - 设定知识库",
        "",
        f"**总设定数**: {setting_library.total_settings}",
        f"**时间位置分布**: {setting_library.metadata.get('position_distribution', {})}",
        "",
        "---",
        ""
    ]
    
    for setting in setting_library.settings:
        lines.append(f"## 设定 {setting.setting_id}: {setting.setting_title}")
        lines.append("")
        lines.append(f"**段落索引**: {setting.paragraph_index}")
        lines.append(f"**获得时间点**: {setting.acquisition_time}")
        lines.append(f"**关联事件**: {setting.related_event_id}")
        lines.append(f"**时间位置**: {setting.time_position}")
        lines.append("")
        lines.append("**核心知识点**:")
        lines.append(f"> {setting.setting_summary}")
        lines.append("")
        lines.append("**累积知识库（设定编号）**:")
        for i, knowledge_id in enumerate(setting.accumulated_knowledge, 1):
            lines.append(f"{i}. {knowledge_id}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)


def generate_functional_tags_markdown(functional_tags_library) -> str:
    """生成功能性标签表Markdown"""
    lines = [
        f"# 第{functional_tags_library.chapter_number}章 - 功能性标签库",
        "",
        f"**总段落数**: {functional_tags_library.total_paragraphs}",
        f"**优先级分布**: {functional_tags_library.priority_distribution}",
        f"**首次信息数量**: {functional_tags_library.first_occurrence_count}",
        "",
        "---",
        ""
    ]
    
    # 统计表格
    lines.append("## 📊 优先级统计")
    lines.append("")
    total = functional_tags_library.total_paragraphs
    for priority, count in functional_tags_library.priority_distribution.items():
        percentage = (count / total * 100) if total > 0 else 0
        lines.append(f"- **{priority}**: {count}段 ({percentage:.1f}%)")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 段落详细标签
    lines.append("## 📝 段落功能性标签")
    lines.append("")
    
    for tags in functional_tags_library.paragraph_tags:
        lines.append(f"### 段落 {tags.paragraph_index}")
        lines.append("")
        
        # 叙事功能
        if tags.narrative_functions:
            lines.append("**叙事功能**:")
            for func in tags.narrative_functions:
                lines.append(f"- {func}")
            lines.append("")
        
        # 叙事结构
        if tags.narrative_structures:
            lines.append("**叙事结构**:")
            for struct in tags.narrative_structures:
                lines.append(f"- {struct}")
            lines.append("")
        
        # 角色关系
        if tags.character_tags:
            lines.append("**角色与关系**:")
            for char_tag in tags.character_tags:
                lines.append(f"- {char_tag}")
            lines.append("")
        
        # 优先级
        lines.append(f"**浓缩优先级**: `{tags.priority}`")
        lines.append(f"**理由**: {tags.priority_reason}")
        lines.append("")
        
        # 其他标记
        if tags.emotional_tone:
            lines.append(f"**情绪基调**: {tags.emotional_tone}")
        if tags.is_first_occurrence:
            lines.append(f"**首次信息**: ✅ 是")
        if tags.repetition_count:
            lines.append(f"**重复强调**: {tags.repetition_count}次")
        lines.append("")
        
        # 浓缩建议
        if tags.condensation_advice:
            lines.append("**浓缩建议**:")
            lines.append(f"> {tags.condensation_advice}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)


def main():
    """主测试流程"""
    logger.info("=== NovelAnnotator 测试开始 ===")
    
    # 1. 配置路径
    # 这里使用NovelSegmenter的测试输出作为输入
    segmentation_json = project_root / "output/temp/20260209_103214/novel_segmenter_output/chpt_0001_segmentation.json"
    
    if not segmentation_json.exists():
        logger.error(f"Segmentation JSON not found: {segmentation_json}")
        logger.info("请先运行test_novel_segmenter.py生成分段结果")
        return
    
    # 2. 加载分段结果
    logger.info(f"Loading segmentation result from: {segmentation_json}")
    segmentation_result = load_segmentation_result(segmentation_json)
    logger.info(f"Loaded chapter {segmentation_result.chapter_number} with {segmentation_result.total_paragraphs} paragraphs")
    
    # 3. 初始化NovelAnnotator
    logger.info("Initializing NovelAnnotator...")
    annotator = NovelAnnotator(provider="claude")
    
    # 4. 执行标注
    logger.info("Starting annotation...")
    annotated_chapter = annotator.execute(segmentation_result)
    
    # 5. 打印结果摘要
    logger.info("\n=== 标注结果摘要 ===")
    logger.info(f"章节: {annotated_chapter.chapter_number}")
    logger.info(f"事件数: {annotated_chapter.event_timeline.total_events}")
    logger.info(f"设定数: {annotated_chapter.setting_library.total_settings}")
    
    if annotated_chapter.functional_tags:
        logger.info(f"功能性标签: {annotated_chapter.functional_tags.total_paragraphs}段")
        logger.info(f"优先级分布: {annotated_chapter.functional_tags.priority_distribution}")
        logger.info(f"首次信息数: {annotated_chapter.functional_tags.first_occurrence_count}")
    
    logger.info(f"总处理时间: {annotated_chapter.metadata['total_processing_time']}s")
    
    logger.info("\n事件列表:")
    for event in annotated_chapter.event_timeline.events:
        logger.info(f"  - {event.event_id}: {event.event_summary}")
    
    logger.info("\n设定列表:")
    for setting in annotated_chapter.setting_library.settings:
        logger.info(f"  - {setting.setting_id} ({setting.setting_title}): {setting.setting_summary[:50]}...")
    
    if annotated_chapter.functional_tags:
        logger.info("\n功能性标签示例（前3段）:")
        for tags in annotated_chapter.functional_tags.paragraph_tags[:3]:
            logger.info(f"  - 段落{tags.paragraph_index}: {tags.priority} | {tags.priority_reason}")
    
    # 6. 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / "output/temp" / f"novel_annotation_test_{timestamp}"
    
    logger.info(f"\nSaving results to: {output_dir}")
    save_annotation_result(
        annotated_chapter,
        output_dir,
        annotated_chapter.chapter_number
    )
    
    logger.info("\n=== 测试完成 ===")
    logger.info(f"输出目录: {output_dir}")


if __name__ == "__main__":
    main()
