#!/usr/bin/env python3
"""
NovelSegmenter JSON输出测试脚本

测试新版NovelSegmenter的功能：
1. Two-Pass LLM分段
2. JSON格式输出
3. 原文还原验证
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_importer import NovelImporter
from src.tools.novel_chapter_detector import NovelChapterDetector
from src.tools.novel_segmenter import NovelSegmenter
from scripts.test.test_helpers import TestOutputManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_novel_segmenter_json():
    """测试NovelSegmenter的JSON输出和原文还原"""
    
    logger.info("\n" + "="*60)
    logger.info("  NovelSegmenter JSON输出测试")
    logger.info("="*60 + "\n")
    
    # 1. 准备测试数据
    test_novel_path = Path("分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt")
    project_name = "末哥超凡公路_json_test"
    
    # 导入小说
    importer = NovelImporter()
    import_result = importer.execute(
        source_file=test_novel_path,
        project_name=project_name
    )
    logger.info(f"Test novel imported to: {import_result.saved_path}")
    
    # 创建测试输出目录
    output_manager = TestOutputManager("novel_segmenter_json")
    
    # 2. 获取第1章内容
    novel_file = Path(import_result.saved_path)
    chapter_detector = NovelChapterDetector()
    chapters = chapter_detector.execute(novel_file=novel_file)
    
    target_chapter_info = None
    for chapter_info in chapters:
        if chapter_info.number == 1:
            target_chapter_info = chapter_info
            break
    
    if not target_chapter_info:
        logger.error("Chapter 1 not found")
        return False
    
    full_text = novel_file.read_text(encoding='utf-8')
    chapter_content = full_text[target_chapter_info.start_char : target_chapter_info.end_char]
    
    # 移除章节标题行
    lines = chapter_content.split('\n')
    if lines and lines[0].strip().startswith(f"=== 第1章"):
        chapter_content = '\n'.join(lines[1:]).strip()
    
    logger.info(f"Chapter content: {len(chapter_content)} chars")
    
    # 3. 执行分段
    logger.info("\n" + "="*60)
    logger.info("  执行NovelSegmenter")
    logger.info("="*60)
    
    segmenter = NovelSegmenter(provider="claude")
    
    try:
        result = segmenter.execute(
            chapter_content=chapter_content,
            chapter_number=1
        )
        
        logger.info(f"\n✅ Segmentation complete!")
        logger.info(f"  Total paragraphs: {result.total_paragraphs}")
        logger.info(f"  Type distribution: {result.metadata['type_distribution']}")
        logger.info(f"  Processing time: {result.metadata['processing_time']}s")
        logger.info(f"  Model used: {result.metadata['model_used']}")
        
    except Exception as e:
        logger.error(f"❌ Segmentation failed: {e}", exc_info=True)
        return False
    
    # 4. 保存JSON输出
    logger.info("\n" + "="*60)
    logger.info("  保存JSON输出")
    logger.info("="*60)
    
    output_json = result.model_dump(mode='json')
    output_manager.save_json("segmentation_result.json", output_json)
    
    logger.info(f"✅ JSON saved: {output_manager.get_path() / 'segmentation_result.json'}")
    
    # 5. 验证原文还原
    logger.info("\n" + "="*60)
    logger.info("  验证原文还原")
    logger.info("="*60)
    
    restored_text = ''.join([p.content for p in result.paragraphs])
    original_stripped = chapter_content.rstrip()
    restored_stripped = restored_text.rstrip()
    
    if original_stripped == restored_stripped:
        logger.info("✅ Text restoration: PASSED")
        restoration_status = "PASSED"
    else:
        diff_chars = len(original_stripped) - len(restored_stripped)
        logger.warning(f"⚠️ Text restoration: FAILED")
        logger.warning(f"  Original length: {len(original_stripped)}")
        logger.warning(f"  Restored length: {len(restored_stripped)}")
        logger.warning(f"  Difference: {diff_chars} chars")
        restoration_status = "FAILED"
        
        # 保存对比文件
        output_manager.save_text("original_text.txt", original_stripped)
        output_manager.save_text("restored_text.txt", restored_stripped)
    
    # 6. 生成段落摘要（用于人工查看）
    logger.info("\n" + "="*60)
    logger.info("  生成段落摘要")
    logger.info("="*60)
    
    summary_lines = [
        f"# 第{result.chapter_number}章分段结果摘要\n",
        f"**总段落数**: {result.total_paragraphs}\n",
        f"**类型分布**: {result.metadata['type_distribution']}\n",
        f"**处理时间**: {result.metadata['processing_time']}秒\n",
        f"**原文还原**: {restoration_status}\n",
        "\n## 段落列表\n"
    ]
    
    for para in result.paragraphs:
        summary_lines.append(f"\n### 段落{para.index}（{para.type}类）\n")
        summary_lines.append(f"- **位置**: 字符 [{para.start_char}, {para.end_char})\n")
        summary_lines.append(f"- **长度**: {len(para.content)} 字符\n")
        summary_lines.append(f"- **开头**: {para.content[:50]}...\n")
    
    summary_text = ''.join(summary_lines)
    output_manager.save_text("segmentation_summary.md", summary_text)
    
    logger.info(f"✅ Summary saved: {output_manager.get_path() / 'segmentation_summary.md'}")
    
    # 7. 对比标准结果（可选）
    standard_paragraph_count = 11
    if result.total_paragraphs == standard_paragraph_count:
        logger.info(f"\n✅ Paragraph count matches standard: {standard_paragraph_count}")
    else:
        logger.warning(f"\n⚠️ Paragraph count mismatch: {result.total_paragraphs} vs standard {standard_paragraph_count}")
    
    # 8. 打印测试结果摘要
    print("\n" + "="*60)
    print("  📊 测试结果摘要")
    print("="*60 + "\n")
    print(f"✅ 分段完成: {result.total_paragraphs}个段落")
    print(f"  - A类（设定）: {result.metadata['type_distribution']['A']}个")
    print(f"  - B类（事件）: {result.metadata['type_distribution']['B']}个")
    print(f"  - C类（系统）: {result.metadata['type_distribution']['C']}个")
    print(f"\n{'✅' if restoration_status == 'PASSED' else '⚠️'} 原文还原: {restoration_status}")
    print(f"\n⏱️  处理时间: {result.metadata['processing_time']}秒")
    print(f"\n📁 输出目录: {output_manager.get_path()}")
    print(f"\n💡 查看结果:")
    print(f"  JSON: cat '{output_manager.get_path() / 'segmentation_result.json'}'")
    print(f"  摘要: cat '{output_manager.get_path() / 'segmentation_summary.md'}'")
    print("\n" + "="*60 + "\n")
    
    # 9. 清理测试数据
    import shutil
    test_project_dir = Path("data/projects") / project_name
    if test_project_dir.exists():
        shutil.rmtree(test_project_dir)
        logger.info(f"Test project cleaned up: {test_project_dir}")
    
    return restoration_status == "PASSED"


if __name__ == "__main__":
    try:
        success = test_novel_segmenter_json()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
