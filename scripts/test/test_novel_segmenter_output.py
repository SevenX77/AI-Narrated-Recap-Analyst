#!/usr/bin/env python3
"""
NovelSegmenter 完整输出测试脚本

测试 NovelSegmenter v3 的双格式输出功能：
1. JSON格式（用于程序处理）
2. 简洁Markdown格式（用于用户查看）
3. LLM原始输出（用于调试）
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
from src.tools.novel_segmenter import NovelSegmenter
from src.utils.novel_helpers import get_chapter_by_number
from scripts.test.test_helpers import TestOutputManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_novel_segmenter_complete_output():
    """测试NovelSegmenter的完整输出（JSON + Markdown + LLM原始输出）"""
    
    logger.info("\n" + "="*60)
    logger.info("  NovelSegmenter 完整输出测试")
    logger.info("="*60 + "\n")
    
    # 1. 准备测试数据
    test_novel_path = Path("分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt")
    project_name = "末哥超凡公路_output_test"
    
    if not test_novel_path.exists():
        logger.error(f"Test novel file not found: {test_novel_path}")
        logger.info("Please ensure the test file exists at the specified path")
        return False
    
    # 导入小说
    logger.info(f"Step 1: Importing novel from {test_novel_path}")
    importer = NovelImporter()
    import_result = importer.execute(
        source_file=test_novel_path,
        project_name=project_name
    )
    logger.info(f"✓ Novel imported to: {import_result.saved_path}")
    
    # 创建测试输出目录
    output_manager = TestOutputManager("novel_segmenter_output")
    output_dir = Path(output_manager.output_dir)
    
    # 2. 获取第1章内容
    logger.info("\nStep 2: Extracting chapter 1 content")
    novel_file = Path(import_result.saved_path)
    
    try:
        chapter_info, chapter_content = get_chapter_by_number(
            novel_file=novel_file,
            chapter_number=1
        )
        logger.info(f"✓ Chapter 1: {chapter_info.title}")
        logger.info(f"  Content length: {len(chapter_content)} chars")
        logger.info(f"  Word count: {chapter_info.word_count}")
    except Exception as e:
        logger.error(f"Failed to extract chapter: {e}")
        return False
    
    # 3. 执行分段
    logger.info("\nStep 3: Performing segmentation with NovelSegmenter")
    segmenter = NovelSegmenter(provider="claude")
    
    try:
        output = segmenter.execute(
            chapter_content=chapter_content,
            chapter_number=chapter_info.number,
            chapter_title=chapter_info.title
        )
        logger.info(f"✓ Segmentation complete!")
    except Exception as e:
        logger.error(f"Segmentation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 保存输出文件
    logger.info("\nStep 4: Saving output files")
    
    # 4.1 保存JSON
    json_file = output_dir / "chpt_0001_segmentation.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(
            output.json_result.model_dump(),
            f,
            indent=2,
            ensure_ascii=False
        )
    logger.info(f"✓ JSON saved: {json_file}")
    
    # 4.2 保存简洁Markdown
    markdown_file = output_dir / "chpt_0001_segmented.md"
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(output.markdown_content)
    logger.info(f"✓ Markdown saved: {markdown_file}")
    
    # 4.3 保存LLM原始输出（可选，调试用）
    llm_raw_file = output_dir / "chpt_0001_llm_raw.md"
    with open(llm_raw_file, 'w', encoding='utf-8') as f:
        f.write(output.llm_raw_output or "")
    logger.info(f"✓ LLM raw output saved: {llm_raw_file}")
    
    # 5. 生成测试报告
    logger.info("\nStep 5: Generating test report")
    
    report_lines = [
        "# NovelSegmenter 完整输出测试报告",
        "",
        f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**测试章节**: 第{chapter_info.number}章 - {chapter_info.title}",
        "",
        "## 输出文件",
        "",
        f"1. **JSON格式** (程序处理用): `{json_file.name}`",
        f"2. **简洁Markdown** (用户查看用): `{markdown_file.name}`",
        f"3. **LLM原始输出** (调试用): `{llm_raw_file.name}`",
        "",
        "## 分段结果统计",
        "",
        f"- **总段落数**: {output.json_result.total_paragraphs}",
        f"- **类型分布**: {output.json_result.metadata.get('type_distribution', {})}",
        f"- **处理时间**: {output.json_result.metadata.get('processing_time', 0):.2f}秒",
        f"- **使用模型**: {output.json_result.metadata.get('model_used', 'N/A')}",
        "",
        "## 段落列表",
        ""
    ]
    
    for para in output.json_result.paragraphs:
        type_name = {
            "A": "A类-设定",
            "B": "B类-事件",
            "C": "C类-系统"
        }.get(para.type, para.type)
        
        report_lines.append(f"### 段落 {para.index} [{type_name}]")
        report_lines.append(f"- **字符范围**: [{para.start_char}, {para.end_char})")
        report_lines.append(f"- **内容长度**: {len(para.content)} 字符")
        report_lines.append(f"- **开头**: {para.content[:50]}...")
        report_lines.append("")
    
    report_lines.extend([
        "---",
        "",
        "## 文件说明",
        "",
        "### 1. JSON格式 (chpt_0001_segmentation.json)",
        "**用途**: 后续程序处理（如语义分析、标签生成）",
        "**内容**: 完整的段落数据，包括类型、内容、位置信息、元数据等",
        "**优势**: 结构化、精确、可编程处理",
        "",
        "### 2. 简洁Markdown (chpt_0001_segmented.md)",
        "**用途**: 用户快速查看分段结果",
        "**内容**: 段落原文 + 段落类型标注",
        "**格式**: 简洁易读，支持Git diff",
        "",
        "### 3. LLM原始输出 (chpt_0001_llm_raw.md)",
        "**用途**: 调试和验证",
        "**内容**: LLM返回的原始markdown（包含行号范围和段落描述）",
        "**备注**: 可选文件，仅用于开发调试",
        ""
    ])
    
    report_file = output_dir / "test_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    logger.info(f"✓ Test report saved: {report_file}")
    
    # 6. 打印摘要
    logger.info("\n" + "="*60)
    logger.info("  测试完成！")
    logger.info("="*60)
    logger.info(f"\n输出目录: {output_dir}")
    logger.info(f"\n生成的文件:")
    logger.info(f"  1. {json_file.name} - JSON格式（程序处理）")
    logger.info(f"  2. {markdown_file.name} - 简洁Markdown（用户查看）")
    logger.info(f"  3. {llm_raw_file.name} - LLM原始输出（调试）")
    logger.info(f"  4. {report_file.name} - 测试报告")
    logger.info(f"\n分段统计:")
    logger.info(f"  总段落数: {output.json_result.total_paragraphs}")
    logger.info(f"  类型分布: {output.json_result.metadata.get('type_distribution', {})}")
    logger.info(f"  处理时间: {output.json_result.metadata.get('processing_time', 0):.2f}秒")
    logger.info("")
    
    return True


if __name__ == "__main__":
    success = test_novel_segmenter_complete_output()
    sys.exit(0 if success else 1)
