"""
测试NovelScriptAligner工具

测试Novel-Script对齐功能，验证：
1. 基本对齐功能
2. 覆盖率统计
3. 改写策略识别
4. 质量报告生成
"""

import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_script_aligner import NovelScriptAligner
from src.core.schemas_novel import AnnotatedChapter
from src.core.schemas_script import ScriptSegmentationResult
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_data():
    """加载测试数据"""
    logger.info("=" * 80)
    logger.info("加载测试数据")
    logger.info("=" * 80)
    
    # 1. 加载Novel Annotation
    annotation_file = project_root / "output/temp/novel_annotation_test_20260209_195255/chpt_0001_annotation.json"
    logger.info(f"加载Novel Annotation: {annotation_file.name}")
    
    with open(annotation_file, 'r', encoding='utf-8') as f:
        annotation_data = json.load(f)
    
    novel_annotation = AnnotatedChapter(**annotation_data)
    logger.info(f"  ✅ Novel章节: {novel_annotation.chapter_number}")
    logger.info(f"  ✅ 事件数: {novel_annotation.event_timeline.total_events}")
    logger.info(f"  ✅ 设定数: {novel_annotation.setting_library.total_settings}")
    
    # 2. 加载Script Segmentation Result
    # 查找最新的测试结果
    temp_dir = project_root / "output/temp"
    script_test_dirs = sorted(temp_dir.glob("script_segmenter_test_*"), reverse=True)
    
    if not script_test_dirs:
        raise FileNotFoundError("未找到Script分段测试结果")
    
    script_result_file = script_test_dirs[0] / "ep01_segmentation.json"
    logger.info(f"\n加载Script分段结果: {script_result_file.parent.name}/{script_result_file.name}")
    
    with open(script_result_file, 'r', encoding='utf-8') as f:
        script_data = json.load(f)
    
    script_result = ScriptSegmentationResult(**script_data)
    logger.info(f"  ✅ 段落数: {script_result.total_segments}")
    logger.info(f"  ✅ 平均句子数: {script_result.avg_sentence_count}")
    
    return novel_annotation, script_result


def test_alignment():
    """测试对齐功能"""
    logger.info("\n" + "=" * 80)
    logger.info("测试1: 基本对齐功能")
    logger.info("=" * 80)
    
    # 加载测试数据
    novel_annotation, script_result = load_test_data()
    
    # 创建对齐工具
    aligner = NovelScriptAligner(provider="claude")
    
    # 执行对齐
    logger.info("\n开始执行对齐分析...")
    alignment_result = aligner.execute(
        novel_annotation=novel_annotation,
        script_result=script_result,
        project_name="末哥超凡公路_test",
        episode_id="ep01"
    )
    
    # 验证结果
    logger.info("\n" + "=" * 80)
    logger.info("对齐结果验证")
    logger.info("=" * 80)
    
    assert alignment_result.total_fragments == script_result.total_segments, \
        f"片段数不匹配: {alignment_result.total_fragments} != {script_result.total_segments}"
    logger.info(f"✅ 片段数匹配: {alignment_result.total_fragments}")
    
    assert len(alignment_result.alignments) == script_result.total_segments, \
        f"对齐结果数不匹配: {len(alignment_result.alignments)} != {script_result.total_segments}"
    logger.info(f"✅ 对齐结果数匹配: {len(alignment_result.alignments)}")
    
    # 验证覆盖率
    logger.info(f"\n覆盖率统计:")
    logger.info(f"  事件覆盖率: {alignment_result.coverage_stats.event_coverage * 100:.1f}%")
    logger.info(f"  设定覆盖率: {alignment_result.coverage_stats.setting_coverage * 100:.1f}%")
    
    # 验证改写策略
    logger.info(f"\n改写策略统计:")
    logger.info(f"  原文保留: {alignment_result.rewrite_stats.exact_count}")
    logger.info(f"  改写: {alignment_result.rewrite_stats.paraphrase_count}")
    logger.info(f"  压缩: {alignment_result.rewrite_stats.summarize_count}")
    logger.info(f"  扩写: {alignment_result.rewrite_stats.expand_count}")
    logger.info(f"  无对应: {alignment_result.rewrite_stats.none_count}")
    logger.info(f"  主要策略: {alignment_result.rewrite_stats.dominant_strategy}")
    
    return alignment_result, aligner


def test_report_generation(alignment_result, aligner):
    """测试报告生成"""
    logger.info("\n" + "=" * 80)
    logger.info("测试2: 质量报告生成")
    logger.info("=" * 80)
    
    # 准备输出目录
    output_dir = project_root / "output/temp/novel_script_alignment_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"alignment_report_{timestamp}"
    
    # 生成报告
    logger.info(f"\n生成质量报告: {report_path.name}")
    report = aligner.generate_report(
        alignment_result,
        output_path=report_path
    )
    
    # 验证报告
    logger.info(f"\n报告质量指标:")
    logger.info(f"  平均置信度: {report.quality_metrics.avg_confidence:.3f}")
    logger.info(f"  高置信度匹配: {report.quality_metrics.high_confidence_count}")
    logger.info(f"  中等置信度匹配: {report.quality_metrics.medium_confidence_count}")
    logger.info(f"  低置信度匹配: {report.quality_metrics.low_confidence_count}")
    logger.info(f"  空对齐片段: {report.quality_metrics.empty_alignment_count}")
    
    logger.info(f"\n改进建议:")
    for idx, rec in enumerate(report.recommendations, 1):
        logger.info(f"  {idx}. {rec}")
    
    # 验证文件存在
    json_file = report_path.with_suffix('.json')
    md_file = report_path.with_suffix('.md')
    
    assert json_file.exists(), f"JSON报告未生成: {json_file}"
    assert md_file.exists(), f"Markdown报告未生成: {md_file}"
    
    logger.info(f"\n✅ 报告生成成功:")
    logger.info(f"  JSON: {json_file}")
    logger.info(f"  Markdown: {md_file}")
    
    return report


def test_detailed_alignment(alignment_result):
    """测试详细对齐信息"""
    logger.info("\n" + "=" * 80)
    logger.info("测试3: 详细对齐信息")
    logger.info("=" * 80)
    
    # 显示前3个片段的详细对齐信息
    for i in range(min(3, len(alignment_result.alignments))):
        alignment = alignment_result.alignments[i]
        
        logger.info(f"\n--- 片段 {alignment.fragment_index} ---")
        logger.info(f"时间: {alignment.time_range}")
        logger.info(f"内容: {alignment.content_preview}...")
        
        if alignment.matched_events:
            logger.info(f"匹配事件 ({len(alignment.matched_events)}):")
            for event in alignment.matched_events:
                logger.info(f"  - {event.event_id} ({event.match_type}, {event.confidence})")
                logger.info(f"    → {event.explanation}")
        
        if alignment.matched_settings:
            logger.info(f"匹配设定 ({len(alignment.matched_settings)}):")
            for setting in alignment.matched_settings:
                logger.info(f"  - {setting.setting_id} ({setting.match_type}, {setting.confidence})")
                logger.info(f"    → {setting.explanation}")
        
        if alignment.skipped_content:
            logger.info(f"跳过内容 ({len(alignment.skipped_content)}):")
            for skip in alignment.skipped_content:
                logger.info(f"  - {skip.content_type}: {skip.content_id} - {skip.reason}")
    
    logger.info("\n✅ 详细对齐信息验证完成")


def test_coverage_analysis(alignment_result, novel_annotation):
    """测试覆盖率分析"""
    logger.info("\n" + "=" * 80)
    logger.info("测试4: 覆盖率分析")
    logger.info("=" * 80)
    
    coverage = alignment_result.coverage_stats
    
    # 显示匹配的事件
    logger.info(f"\n已匹配事件 ({coverage.matched_events}/{coverage.total_events}):")
    for event_id in coverage.matched_event_ids:
        event = next(e for e in novel_annotation.event_timeline.events if e.event_id == event_id)
        logger.info(f"  ✅ {event_id}: {event.event_summary[:50]}...")
    
    # 显示未匹配的事件
    if coverage.unmatched_event_ids:
        logger.info(f"\n未匹配事件 ({len(coverage.unmatched_event_ids)}):")
        for event_id in coverage.unmatched_event_ids:
            event = next(e for e in novel_annotation.event_timeline.events if e.event_id == event_id)
            logger.info(f"  ❌ {event_id}: {event.event_summary[:50]}...")
    else:
        logger.info(f"\n✅ 所有事件都已匹配！")
    
    # 显示匹配的设定
    logger.info(f"\n已匹配设定 ({coverage.matched_settings}/{coverage.total_settings}):")
    for setting_id in coverage.matched_setting_ids:
        setting = next(s for s in novel_annotation.setting_library.settings if s.setting_id == setting_id)
        logger.info(f"  ✅ {setting_id}: {setting.setting_title}")
    
    # 显示未匹配的设定
    if coverage.unmatched_setting_ids:
        logger.info(f"\n未匹配设定 ({len(coverage.unmatched_setting_ids)}):")
        for setting_id in coverage.unmatched_setting_ids:
            setting = next(s for s in novel_annotation.setting_library.settings if s.setting_id == setting_id)
            logger.info(f"  ❌ {setting_id}: {setting.setting_title}")
    else:
        logger.info(f"\n✅ 所有设定都已匹配！")
    
    logger.info("\n✅ 覆盖率分析完成")


def main():
    """主测试流程"""
    logger.info("\n" + "=" * 80)
    logger.info("NovelScriptAligner 工具测试")
    logger.info("=" * 80)
    
    try:
        # 测试1: 基本对齐功能
        alignment_result, aligner = test_alignment()
        
        # 测试2: 报告生成
        report = test_report_generation(alignment_result, aligner)
        
        # 测试3: 详细对齐信息
        test_detailed_alignment(alignment_result)
        
        # 测试4: 覆盖率分析
        novel_annotation, _ = load_test_data()
        test_coverage_analysis(alignment_result, novel_annotation)
        
        # 最终总结
        logger.info("\n" + "=" * 80)
        logger.info("✅ 所有测试通过！")
        logger.info("=" * 80)
        logger.info(f"\n测试总结:")
        logger.info(f"  片段数: {alignment_result.total_fragments}")
        logger.info(f"  事件覆盖率: {alignment_result.coverage_stats.event_coverage * 100:.1f}%")
        logger.info(f"  设定覆盖率: {alignment_result.coverage_stats.setting_coverage * 100:.1f}%")
        logger.info(f"  平均置信度: {report.quality_metrics.avg_confidence:.3f}")
        logger.info(f"  主要改写策略: {alignment_result.rewrite_stats.dominant_strategy}")
        logger.info(f"\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
