"""
测试NovelTagger工具

测试目标：
1. 读取NovelSegmenter的输出JSON
2. 调用NovelTagger进行叙事特征标注
3. 输出章节标签表和整体分析
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

from src.tools.novel_tagger import NovelTagger
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


def save_tagging_result(
    tagging_result,
    output_dir: Path
):
    """保存标注结果"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 保存完整JSON
    json_path = output_dir / "novel_tagging_result.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(tagging_result.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"Saved JSON: {json_path}")
    
    # 2. 保存章节标签表（Markdown）
    tags_md_path = output_dir / "chapter_tags.md"
    tags_md = generate_tags_markdown(tagging_result)
    with open(tags_md_path, 'w', encoding='utf-8') as f:
        f.write(tags_md)
    logger.info(f"Saved tags table: {tags_md_path}")
    
    # 3. 保存整体分析报告（Markdown）
    report_md_path = output_dir / "overall_analysis.md"
    report_md = generate_report_markdown(tagging_result)
    with open(report_md_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
    logger.info(f"Saved overall report: {report_md_path}")


def generate_tags_markdown(tagging_result) -> str:
    """生成章节标签表Markdown"""
    lines = [
        f"# {tagging_result.project_name} - 章节叙事特征标签",
        "",
        f"**总章节数**: {tagging_result.total_chapters}",
        f"**处理时间**: {tagging_result.processing_time}秒",
        "",
        "---",
        ""
    ]
    
    # 章节标签表格
    lines.append("## 章节标签一览表")
    lines.append("")
    lines.append("| 章节 | 叙事视角 | 时间结构 | 节奏 | 基调 | 关键主题 | 类型标签 | 置信度 |")
    lines.append("|------|----------|----------|------|------|----------|----------|--------|")
    
    for tag in tagging_result.chapter_tags:
        themes_str = "、".join(tag.key_themes[:3])
        genres_str = "、".join(tag.genre_tags[:3])
        lines.append(
            f"| {tag.chapter_number} | {tag.narrative_perspective} | {tag.time_structure} | "
            f"{tag.pacing} | {tag.tone} | {themes_str} | {genres_str} | {tag.confidence:.2f} |"
        )
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 每章详细标签
    lines.append("## 章节详细标签")
    lines.append("")
    
    for tag in tagging_result.chapter_tags:
        lines.append(f"### 第{tag.chapter_number}章")
        lines.append("")
        lines.append(f"**叙事视角**: {tag.narrative_perspective}")
        lines.append(f"**时间结构**: {tag.time_structure}")
        lines.append(f"**叙事节奏**: {tag.pacing}")
        lines.append(f"**情感基调**: {tag.tone}")
        lines.append("")
        lines.append(f"**关键主题**: {', '.join(tag.key_themes)}")
        lines.append(f"**类型标签**: {', '.join(tag.genre_tags)}")
        lines.append(f"**叙事技巧**: {', '.join(tag.narrative_techniques)}")
        lines.append("")
        lines.append(f"**置信度**: {tag.confidence:.2f}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)


def generate_report_markdown(tagging_result) -> str:
    """生成整体分析报告Markdown"""
    lines = [
        f"# {tagging_result.project_name} - 整体叙事分析报告",
        "",
        f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**总章节数**: {tagging_result.total_chapters}",
        f"**处理时长**: {tagging_result.processing_time}秒",
        "",
        "---",
        ""
    ]
    
    # 整体特征
    lines.append("## 📊 整体叙事特征")
    lines.append("")
    lines.append(f"### 叙事视角")
    lines.append(f"> **{tagging_result.overall_perspective}**")
    lines.append("")
    lines.append(f"### 情感基调")
    lines.append(f"> **{tagging_result.dominant_tone}**")
    lines.append("")
    lines.append(f"### 核心主题")
    for i, theme in enumerate(tagging_result.common_themes, 1):
        lines.append(f"{i}. {theme}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 特征分布统计
    lines.append("## 📈 特征分布统计")
    lines.append("")
    
    # 视角分布
    perspective_dist = {}
    for tag in tagging_result.chapter_tags:
        perspective = tag.narrative_perspective
        perspective_dist[perspective] = perspective_dist.get(perspective, 0) + 1
    
    lines.append("### 视角分布")
    for perspective, count in sorted(perspective_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = count / tagging_result.total_chapters * 100
        lines.append(f"- **{perspective}**: {count}章 ({percentage:.1f}%)")
    lines.append("")
    
    # 节奏分布
    pacing_dist = {}
    for tag in tagging_result.chapter_tags:
        pacing = tag.pacing
        pacing_dist[pacing] = pacing_dist.get(pacing, 0) + 1
    
    lines.append("### 节奏分布")
    for pacing, count in sorted(pacing_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = count / tagging_result.total_chapters * 100
        lines.append(f"- **{pacing}**: {count}章 ({percentage:.1f}%)")
    lines.append("")
    
    # 基调分布
    tone_dist = {}
    for tag in tagging_result.chapter_tags:
        tone = tag.tone
        tone_dist[tone] = tone_dist.get(tone, 0) + 1
    
    lines.append("### 基调分布")
    for tone, count in sorted(tone_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = count / tagging_result.total_chapters * 100
        lines.append(f"- **{tone}**: {count}章 ({percentage:.1f}%)")
    lines.append("")
    
    # 主题频次
    theme_freq = {}
    for tag in tagging_result.chapter_tags:
        for theme in tag.key_themes:
            theme_freq[theme] = theme_freq.get(theme, 0) + 1
    
    lines.append("### 主题频次")
    for theme, count in sorted(theme_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
        lines.append(f"- **{theme}**: {count}次")
    lines.append("")
    
    # 类型标签频次
    genre_freq = {}
    for tag in tagging_result.chapter_tags:
        for genre in tag.genre_tags:
            genre_freq[genre] = genre_freq.get(genre, 0) + 1
    
    lines.append("### 类型标签频次")
    for genre, count in sorted(genre_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
        lines.append(f"- **{genre}**: {count}次")
    lines.append("")
    
    # 叙事技巧频次
    technique_freq = {}
    for tag in tagging_result.chapter_tags:
        for technique in tag.narrative_techniques:
            technique_freq[technique] = technique_freq.get(technique, 0) + 1
    
    lines.append("### 叙事技巧频次")
    for technique, count in sorted(technique_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
        lines.append(f"- **{technique}**: {count}次")
    lines.append("")
    
    return '\n'.join(lines)


def main():
    """主测试流程"""
    logger.info("=== NovelTagger 测试开始 ===")
    
    # 1. 配置路径
    # 使用NovelSegmenter的测试输出作为输入
    segmentation_json = project_root / "output/temp/20260209_103214/novel_segmenter_output/chpt_0001_segmentation.json"
    
    if not segmentation_json.exists():
        logger.error(f"Segmentation JSON not found: {segmentation_json}")
        logger.info("请先运行test_novel_segmenter.py生成分段结果")
        return
    
    # 2. 加载分段结果
    logger.info(f"Loading segmentation result from: {segmentation_json}")
    segmentation_result = load_segmentation_result(segmentation_json)
    logger.info(f"Loaded chapter {segmentation_result.chapter_number} with {segmentation_result.total_paragraphs} paragraphs")
    
    # 3. 初始化NovelTagger
    logger.info("Initializing NovelTagger...")
    tagger = NovelTagger(provider="deepseek")  # 使用 DeepSeek，成本更低
    
    # 4. 执行标注（将单章结果放入列表）
    logger.info("Starting tagging...")
    tagging_result = tagger.execute(
        segmentation_results=[segmentation_result],
        project_name="天命桃花",
        preview_length=1000
    )
    
    # 5. 打印结果摘要
    logger.info("\n=== 标注结果摘要 ===")
    logger.info(f"项目: {tagging_result.project_name}")
    logger.info(f"总章节数: {tagging_result.total_chapters}")
    logger.info(f"整体视角: {tagging_result.overall_perspective}")
    logger.info(f"主导基调: {tagging_result.dominant_tone}")
    logger.info(f"常见主题: {', '.join(tagging_result.common_themes[:5])}")
    logger.info(f"总处理时间: {tagging_result.processing_time}s")
    
    logger.info("\n章节标签:")
    for tag in tagging_result.chapter_tags:
        logger.info(f"\n  第{tag.chapter_number}章:")
        logger.info(f"    - 视角: {tag.narrative_perspective}")
        logger.info(f"    - 节奏: {tag.pacing}")
        logger.info(f"    - 基调: {tag.tone}")
        logger.info(f"    - 主题: {', '.join(tag.key_themes)}")
        logger.info(f"    - 类型: {', '.join(tag.genre_tags)}")
        logger.info(f"    - 技巧: {', '.join(tag.narrative_techniques)}")
        logger.info(f"    - 置信度: {tag.confidence:.2f}")
    
    # 6. 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / "output/temp" / f"novel_tagger_test_{timestamp}"
    
    logger.info(f"\nSaving results to: {output_dir}")
    save_tagging_result(tagging_result, output_dir)
    
    logger.info("\n=== 测试完成 ===")
    logger.info(f"输出目录: {output_dir}")


if __name__ == "__main__":
    main()
