"""
测试NovelSystemDetector工具

测试目标：
1. 验证系统元素检测功能
2. 验证系统目录动态更新
3. 测试完整流程：Annotator → Detector → Tracker
"""

import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_system_detector import NovelSystemDetector
from src.core.schemas_novel import ParagraphSegmentationResult, SystemCatalog, SystemUpdateResult, AnnotatedChapter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主测试流程"""
    logger.info("=== NovelSystemDetector 测试开始 ===")
    
    # 1. 加载测试数据
    logger.info("\n=== Step 1: 加载测试数据 ===")
    
    # 加载分段结果
    segmentation_path = project_root / "output/temp/20260209_103214/novel_segmenter_output/chpt_0001_segmentation.json"
    if not segmentation_path.exists():
        logger.error(f"Segmentation file not found: {segmentation_path}")
        return
    
    with open(segmentation_path, 'r', encoding='utf-8') as f:
        segmentation_data = json.load(f)
    segmentation_result = ParagraphSegmentationResult(**segmentation_data)
    logger.info(f"Loaded segmentation: {len(segmentation_result.paragraphs)} paragraphs")
    
    # 加载系统目录
    catalog_path = project_root / "output/temp/novel_system_analysis/system_catalog.json"
    if not catalog_path.exists():
        logger.error(f"System catalog not found: {catalog_path}")
        return
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)
    system_catalog = SystemCatalog(**catalog_data)
    logger.info(f"Loaded system catalog: {len(system_catalog.categories)} categories, {catalog_data['metadata']['total_elements']} elements")
    
    # 2. 加载标注结果（使用已有的）
    logger.info("\n=== Step 2: 加载标注结果 ===")
    annotation_path = project_root / "output/temp/novel_annotation_test_20260209_195255/chpt_0001_annotation.json"
    
    if not annotation_path.exists():
        logger.warning(f"Annotation file not found: {annotation_path}")
        logger.info("Running NovelAnnotator...")
        from src.tools.novel_annotator import NovelAnnotator
        from src.core.schemas_novel import AnnotatedChapter
        
        annotator = NovelAnnotator(provider="claude")
        annotated_chapter = annotator.execute(segmentation_result)
    else:
        logger.info(f"Loading annotation from: {annotation_path}")
        from src.core.schemas_novel import AnnotatedChapter
        
        with open(annotation_path, 'r', encoding='utf-8') as f:
            annotation_data = json.load(f)
        annotated_chapter = AnnotatedChapter(**annotation_data)
    
    logger.info(f"Annotated chapter {annotated_chapter.chapter_number}:")
    logger.info(f"  - Events: {len(annotated_chapter.event_timeline.events)}")
    logger.info(f"  - Settings: {len(annotated_chapter.setting_library.settings)}")
    
    # 3. 运行NovelSystemDetector
    logger.info("\n=== Step 3: 运行NovelSystemDetector ===")
    detector = NovelSystemDetector(provider="claude")
    
    detection_result, updated_catalog = detector.execute(
        annotated_chapter=annotated_chapter,
        segmentation_result=segmentation_result,
        system_catalog=system_catalog
    )
    
    # 4. 输出检测结果
    logger.info("\n=== Step 4: 检测结果 ===")
    logger.info(f"章节: {detection_result.chapter_number}")
    logger.info(f"发现新元素: {detection_result.has_new_elements}")
    logger.info(f"新元素数量: {len(detection_result.new_elements)}")
    logger.info(f"目录已更新: {detection_result.catalog_updated}")
    logger.info(f"处理时间: {detection_result.metadata.get('processing_time', 0)}s")
    
    if detection_result.has_new_elements:
        logger.info("\n新发现的元素:")
        for elem in detection_result.new_elements:
            logger.info(f"  - {elem.element_name} → {elem.category_id} ({elem.category_name}) [{elem.confidence}]")
    else:
        logger.info("\n本章无新元素")
    
    # 5. 对比目录变化
    logger.info("\n=== Step 5: 系统目录变化 ===")
    original_total = system_catalog.metadata.get('total_elements', 0)
    updated_total = updated_catalog.metadata.get('total_elements', 0)
    logger.info(f"原始元素总数: {original_total}")
    logger.info(f"更新后元素总数: {updated_total}")
    logger.info(f"新增元素数: {updated_total - original_total}")
    
    # 6. 保存结果
    output_dir = project_root / "output/temp/novel_system_detector_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存检测结果
    detection_json_path = output_dir / f"chpt_{annotated_chapter.chapter_number:04d}_detection.json"
    with open(detection_json_path, 'w', encoding='utf-8') as f:
        json.dump(detection_result.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"\nSaved detection result: {detection_json_path}")
    
    # 保存更新后的目录
    catalog_json_path = output_dir / "system_catalog_updated.json"
    with open(catalog_json_path, 'w', encoding='utf-8') as f:
        json.dump(updated_catalog.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"Saved updated catalog: {catalog_json_path}")
    
    # 生成Markdown报告
    md_path = output_dir / f"chpt_{annotated_chapter.chapter_number:04d}_detection_report.md"
    md_content = generate_detection_markdown(detection_result, system_catalog, updated_catalog)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    logger.info(f"Saved markdown report: {md_path}")
    
    logger.info("\n=== 测试完成 ===")


def generate_detection_markdown(
    detection: SystemUpdateResult,
    original_catalog: SystemCatalog,
    updated_catalog: SystemCatalog
) -> str:
    """生成检测结果Markdown报告"""
    lines = [
        f"# 系统元素检测报告 - 第{detection.chapter_number}章",
        "",
        f"**检测时间**: {detection.metadata.get('processing_time', 0)}s",
        f"**模型**: {detection.metadata.get('model_used', 'unknown')}",
        "",
        "---",
        ""
    ]
    
    # 检测结果摘要
    lines.append("## 检测结果摘要")
    lines.append("")
    lines.append(f"- **发现新元素**: {'是' if detection.has_new_elements else '否'}")
    lines.append(f"- **新元素数量**: {len(detection.new_elements)}")
    lines.append(f"- **目录已更新**: {'是' if detection.catalog_updated else '否'}")
    lines.append("")
    
    if detection.has_new_elements:
        lines.append("---")
        lines.append("")
        lines.append("## 新发现的元素")
        lines.append("")
        
        for i, elem in enumerate(detection.new_elements, 1):
            lines.append(f"### {i}. {elem.element_name}")
            lines.append("")
            lines.append(f"- **归类**: {elem.category_id} - {elem.category_name}")
            lines.append(f"- **首次出现**: 第{elem.chapter_number}章")
            lines.append(f"- **置信度**: {elem.confidence}")
            lines.append("")
    
    # 系统目录变化
    lines.append("---")
    lines.append("")
    lines.append("## 系统目录变化")
    lines.append("")
    
    original_total = original_catalog.metadata.get('total_elements', 0)
    updated_total = updated_catalog.metadata.get('total_elements', 0)
    
    lines.append(f"- **原始元素总数**: {original_total}")
    lines.append(f"- **更新后元素总数**: {updated_total}")
    lines.append(f"- **新增元素数**: {updated_total - original_total}")
    lines.append("")
    
    if detection.has_new_elements:
        lines.append("### 受影响的类别")
        lines.append("")
        
        # 找出变化的类别
        for orig_cat, upd_cat in zip(original_catalog.categories, updated_catalog.categories):
            if len(orig_cat.elements) != len(upd_cat.elements):
                new_elems = set(upd_cat.elements) - set(orig_cat.elements)
                lines.append(f"#### {upd_cat.category_id} - {upd_cat.category_name}")
                lines.append(f"- 原有元素: {len(orig_cat.elements)}")
                lines.append(f"- 更新后元素: {len(upd_cat.elements)}")
                lines.append(f"- 新增: {', '.join(new_elems)}")
                lines.append("")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    main()
