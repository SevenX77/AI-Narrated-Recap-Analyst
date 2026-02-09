"""
NovelSegmenter Tool Test Script
测试 NovelSegmenter 工具的功能正确性

测试内容：
1. 第1章分段分析
2. 生成Markdown报告
3. 对比标准分析文件
4. 验证格式完整性
"""

from pathlib import Path
import shutil
from src.tools.novel_segmenter import NovelSegmenter
from src.tools.novel_importer import NovelImporter
from scripts.test.test_helpers import TestOutputManager

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define test data paths
TEST_SOURCE_NOVEL_PATH = Path("分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt")
TEST_PROJECT_NAME = "末哥超凡公路_test"
TEST_PROJECT_RAW_DIR = Path("data/projects") / TEST_PROJECT_NAME / "raw"
TEST_NOVEL_PATH_IN_PROJECT = TEST_PROJECT_RAW_DIR / "novel.txt"
TEST_ANALYSIS_DIR = Path("data/projects") / TEST_PROJECT_NAME / "analysis"

# 标准分析文件路径
STANDARD_ANALYSIS_PATH = Path("分析资料/有原小说/01_末哥超凡公路/novel/第一章完整分段分析.md")


def setup_test_project():
    """
    为测试设置项目目录并导入小说
    """
    # 清理旧的测试项目
    if TEST_PROJECT_RAW_DIR.exists():
        shutil.rmtree(TEST_PROJECT_RAW_DIR.parent)
    TEST_PROJECT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 导入小说
    importer = NovelImporter()
    importer.execute(
        source_file=TEST_SOURCE_NOVEL_PATH,
        project_name=TEST_PROJECT_NAME,
        save_to_disk=True,
        include_content=False
    )
    logger.info(f"Test novel imported to: {TEST_NOVEL_PATH_IN_PROJECT}")


def cleanup_test_project():
    """
    清理测试项目目录
    """
    if TEST_PROJECT_RAW_DIR.exists():
        shutil.rmtree(TEST_PROJECT_RAW_DIR.parent)
        logger.info(f"Test project directory cleaned up: {TEST_PROJECT_RAW_DIR}")


def run_main_test(output_manager: TestOutputManager, segmenter: NovelSegmenter):
    """
    运行 NovelSegmenter 的主要测试逻辑
    """
    logger.info("\n" + "="*60)
    logger.info("  🔧 NovelSegmenter 工具测试")
    logger.info("="*60 + "\n")

    logger.info("📝 初始化工具...")
    logger.info(f"📖 测试文件: {TEST_NOVEL_PATH_IN_PROJECT.name}")
    logger.info(f"📊 文件大小: {TEST_NOVEL_PATH_IN_PROJECT.stat().st_size / 1024:.1f}KB")
    logger.info(f"🎯 目标章节: 第1章")

    logger.info("🚀 执行章节分段分析...")
    logger.info("⏳ 调用 LLM 中，请耐心等待（可能需要30-60秒）...")
    
    analysis_path = segmenter.execute(
        novel_file=TEST_NOVEL_PATH_IN_PROJECT,
        chapter_number=1
    )
    
    logger.info("✅ 分析成功！")
    logger.info(f"📁 分析报告: {analysis_path}")

    # 验证文件是否存在
    assert analysis_path.exists(), f"Analysis file not found: {analysis_path}"
    
    # 读取生成的分析内容
    llm_analysis = analysis_path.read_text(encoding='utf-8')
    logger.info(f"📊 LLM分析长度: {len(llm_analysis)} 字符")
    
    # 复制到临时输出目录以便查看
    output_manager.save_text("第1章完整分段分析_LLM.md", llm_analysis)
    
    # 读取标准分析文件（如果存在）
    if STANDARD_ANALYSIS_PATH.exists():
        standard_analysis = STANDARD_ANALYSIS_PATH.read_text(encoding='utf-8')
        logger.info(f"📊 标准分析长度: {len(standard_analysis)} 字符")
        
        # 保存标准分析到临时输出
        output_manager.save_text("第1章完整分段分析_标准.md", standard_analysis)
        
        # 简单对比分析
        llm_paragraphs = llm_analysis.count("## 段落")
        standard_paragraphs = standard_analysis.count("## 段落")
        
        logger.info(f"\n📊 段落数量对比:")
        logger.info(f"   LLM分析: {llm_paragraphs} 个段落")
        logger.info(f"   标准分析: {standard_paragraphs} 个段落")
        logger.info(f"   差异: {abs(llm_paragraphs - standard_paragraphs)} 个")
        
        # 生成对比报告
        comparison_report = f"""# 第1章分段分析对比报告

## 基本统计

| 指标 | LLM分析 | 标准分析 | 差异 |
|------|---------|----------|------|
| 总字符数 | {len(llm_analysis)} | {len(standard_analysis)} | {len(llm_analysis) - len(standard_analysis)} |
| 段落数量 | {llm_paragraphs} | {standard_paragraphs} | {llm_paragraphs - standard_paragraphs} |

## 文件位置

- **LLM分析**: `{output_manager.get_path()}/第1章完整分段分析_LLM.md`
- **标准分析**: `{output_manager.get_path()}/第1章完整分段分析_标准.md`

## 手动对比建议

1. 打开两个文件进行逐段对比
2. 检查段落边界是否合理
3. 检查叙事功能标注是否准确
4. 检查整体分析部分是否完整

## 评估维度

- [ ] 段落数量是否接近（±2个可接受）
- [ ] 关键段落是否识别（段落4铁律、段落9系统觉醒）
- [ ] 叙事功能标注是否合理
- [ ] Markdown格式是否完整
- [ ] 整体分析部分是否包含所有必要内容
"""
        output_manager.save_text("comparison_report.md", comparison_report)
    else:
        logger.warning(f"⚠️  标准分析文件不存在: {STANDARD_ANALYSIS_PATH}")

    logger.info("\n" + "-"*60)
    logger.info("  📊 测试结果摘要")
    logger.info("-"*60 + "\n")
    logger.info(f"✅ 分析状态: 成功")
    logger.info(f"📁 分析文件: {analysis_path}")
    logger.info(f"📊 分析长度: {len(llm_analysis)} 字符")
    logger.info(f"📋 段落数量: {llm_analysis.count('## 段落')} 个")
    
    # 检查关键部分是否存在
    has_overall_analysis = "## 📊" in llm_analysis or "整体分析" in llm_analysis
    has_segmentation = "段落1" in llm_analysis
    has_condensation = "浓缩建议（500字版本）" in llm_analysis
    
    logger.info(f"\n📋 格式完整性检查:")
    logger.info(f"   段落分析: {'✅' if has_segmentation else '❌'}")
    logger.info(f"   整体分析: {'✅' if has_overall_analysis else '❌'}")
    logger.info(f"   浓缩建议: {'✅' if has_condensation else '❌'}")

    logger.info(f"\n📁 项目分析目录: {TEST_ANALYSIS_DIR}")
    logger.info(f"📁 临时输出: {output_manager.get_path()}")
    logger.info(f"💡 快速查看:")
    logger.info(f"   - LLM分析: cat '{output_manager.get_path()}/第1章完整分段分析_LLM.md'")
    if STANDARD_ANALYSIS_PATH.exists():
        logger.info(f"   - 对比报告: cat '{output_manager.get_path()}/comparison_report.md'")
    logger.info("\n" + "-"*60 + "\n")
    
    return analysis_path


def run_format_validation(analysis_path: Path):
    """
    验证Markdown格式
    """
    logger.info("\n" + "="*60)
    logger.info("  🔬 格式验证测试")
    logger.info("="*60 + "\n")

    content = analysis_path.read_text(encoding='utf-8')
    
    # 验证必要的section
    required_sections = [
        "# 第1章完整分段分析",
        "## 段落",
        "**[叙事功能]**",
        "**[浓缩优先级]**",
        "**[浓缩建议]**",
        "**[时空]**",
        "## 📊",
        "### 核心功能统计",
        "### 优先级分布",
        "### 浓缩建议（500字版本）"
    ]
    
    logger.info("检查必要的Markdown section...")
    all_present = True
    for section in required_sections:
        present = section in content
        status = "✅" if present else "❌"
        logger.info(f"  {status} {section}")
        if not present:
            all_present = False
    
    if all_present:
        logger.info("\n✅ 所有必要section都存在！")
    else:
        logger.warning("\n⚠️  部分section缺失，请检查LLM输出")
    
    logger.info("\n" + "-"*60 + "\n")


def main():
    logger.info("\n" + "="*60)
    logger.info("  NovelSegmenter 工具测试套件")
    logger.info("="*60 + "\n")

    # Setup
    setup_test_project()

    output_manager = TestOutputManager("04_novel_segmenter")
    segmenter = NovelSegmenter()

    try:
        # 运行主要测试
        analysis_path = run_main_test(output_manager, segmenter)

        # 运行格式验证
        run_format_validation(analysis_path)

        logger.info("\n✅ 所有 NovelSegmenter 测试完成！")
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        raise
    finally:
        # Cleanup
        cleanup_test_project()


if __name__ == "__main__":
    main()
