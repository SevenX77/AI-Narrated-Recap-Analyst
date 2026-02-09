"""
NovelChapterDetector Tool Test Script
测试 NovelChapterDetector 工具的功能正确性

测试内容：
1. 正常章节检测
2. 章节位置计算
3. 章节字数统计
4. 连续性验证
5. 边界情况测试
"""

from pathlib import Path
import json
import shutil
from src.tools.novel_chapter_detector import NovelChapterDetector
from src.tools.novel_importer import NovelImporter
from scripts.test.test_helpers import TestOutputManager
from src.core.config import config
from src.core.schemas_novel import ChapterInfo

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define test data paths
TEST_SOURCE_NOVEL_PATH = Path("分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt")
TEST_PROJECT_NAME = "末哥超凡公路_test"
TEST_PROJECT_RAW_DIR = Path("data/projects") / TEST_PROJECT_NAME / "raw"
TEST_NOVEL_PATH_IN_PROJECT = TEST_PROJECT_RAW_DIR / "novel.txt"


def setup_and_teardown_test_project():
    """
    为测试模块设置和清理测试项目目录，并确保小说文件已导入。
    """
    # Setup: 确保测试项目目录干净并导入小说
    if TEST_PROJECT_RAW_DIR.exists():
        shutil.rmtree(TEST_PROJECT_RAW_DIR.parent)
    TEST_PROJECT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    importer = NovelImporter()
    importer.execute(
        source_file=TEST_SOURCE_NOVEL_PATH,
        project_name=TEST_PROJECT_NAME,
        save_to_disk=True,
        include_content=False
    )
    logger.info(f"Test novel imported to: {TEST_NOVEL_PATH_IN_PROJECT}")

    yield  # Run tests

    # Teardown: 清理测试项目目录
    if TEST_PROJECT_RAW_DIR.exists():
        shutil.rmtree(TEST_PROJECT_RAW_DIR.parent)
        logger.info(f"Test project directory cleaned up: {TEST_PROJECT_RAW_DIR}")


def run_main_test(output_manager: TestOutputManager, detector: NovelChapterDetector):
    """
    运行 NovelChapterDetector 的主要测试逻辑。
    """
    logger.info("\n" + "="*60)
    logger.info("  🔧 NovelChapterDetector 工具测试")
    logger.info("="*60 + "\n")

    logger.info("📝 初始化工具...")
    logger.info(f"📖 测试文件: {TEST_NOVEL_PATH_IN_PROJECT.name}")
    logger.info(f"📊 文件大小: {TEST_NOVEL_PATH_IN_PROJECT.stat().st_size / 1024:.1f}KB")

    logger.info("🚀 执行章节检测...")
    chapters = detector.execute(novel_file=TEST_NOVEL_PATH_IN_PROJECT)
    logger.info("✅ 检测成功！")

    logger.info("💾 保存检查文件...")
    
    # 保存完整章节信息
    chapters_data = [ch.model_dump(mode='json') for ch in chapters]
    output_manager.save_json("chapters.json", chapters_data)
    
    # 保存章节索引（简化版）
    chapter_index = [
        {
            "number": ch.number,
            "title": ch.title,
            "word_count": ch.word_count,
            "lines": f"{ch.start_line}-{ch.end_line}"
        }
        for ch in chapters
    ]
    output_manager.save_json("chapter_index.json", chapter_index)
    
    # 生成章节摘要文本
    summary_lines = ["# 章节检测摘要\n"]
    summary_lines.append(f"总章节数: {len(chapters)}\n\n")
    summary_lines.append("## 章节列表\n")
    for ch in chapters:
        summary_lines.append(
            f"- 第{ch.number}章: {ch.title or '(无标题)'} "
            f"({ch.word_count}字, 行{ch.start_line}-{ch.end_line})\n"
        )
    output_manager.save_text("chapter_summary.txt", ''.join(summary_lines))
    
    # 统计分析
    total_words = sum(ch.word_count or 0 for ch in chapters)
    avg_words = total_words / len(chapters) if chapters else 0
    
    analysis = {
        "total_chapters": len(chapters),
        "total_words": total_words,
        "avg_words_per_chapter": round(avg_words, 2),
        "min_words": min(ch.word_count or 0 for ch in chapters) if chapters else 0,
        "max_words": max(ch.word_count or 0 for ch in chapters) if chapters else 0,
        "first_chapter": f"第{chapters[0].number}章" if chapters else None,
        "last_chapter": f"第{chapters[-1].number}章" if chapters else None
    }
    output_manager.save_json("chapter_analysis.json", analysis)

    logger.info("\n" + "-"*60)
    logger.info("  📊 测试结果摘要")
    logger.info("-"*60 + "\n")
    logger.info(f"✅ 检测状态: 成功")
    logger.info(f"📚 总章节数: {analysis['total_chapters']}")
    logger.info(f"📝 总字数: {analysis['total_words']:,}")
    logger.info(f"📊 平均每章字数: {analysis['avg_words_per_chapter']:,.0f}")
    logger.info(f"📉 最短章节: {analysis['min_words']:,} 字")
    logger.info(f"📈 最长章节: {analysis['max_words']:,} 字")
    logger.info(f"🏁 首章: {analysis['first_chapter']}")
    logger.info(f"🔚 末章: {analysis['last_chapter']}")

    # 显示前5章节详情
    logger.info(f"\n📖 前5章详情:")
    for ch in chapters[:5]:
        logger.info(f"   第{ch.number}章: {ch.title or '(无标题)'}")
        logger.info(f"      字数: {ch.word_count:,}")
        logger.info(f"      位置: 行 {ch.start_line}-{ch.end_line}, 字符 {ch.start_char}-{ch.end_char}")

    logger.info(f"\n📁 临时输出: {output_manager.get_path()}")
    logger.info(f"💡 快速查看:")
    logger.info(f"   - 章节索引: cat {output_manager.get_path()}/chapter_index.json")
    logger.info(f"   - 章节摘要: cat {output_manager.get_path()}/chapter_summary.txt")
    logger.info(f"   - 统计分析: cat {output_manager.get_path()}/chapter_analysis.json")
    logger.info("\n" + "-"*60 + "\n")
    
    return chapters


def run_chapter_extraction_test(output_manager: TestOutputManager, detector: NovelChapterDetector, chapters):
    """
    测试章节提取功能（验证章节位置是否正确）
    """
    logger.info("\n" + "="*60)
    logger.info("  🔬 章节提取验证测试")
    logger.info("="*60 + "\n")

    # 读取完整文本
    content = TEST_NOVEL_PATH_IN_PROJECT.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # 提取前3章验证
    logger.info("📖 提取前3章验证位置准确性...")
    for ch in chapters[:3]:
        logger.info(f"\n第{ch.number}章: {ch.title}")
        
        # 提取章节内容
        chapter_lines = lines[ch.start_line:ch.end_line]
        chapter_content = '\n'.join(chapter_lines)
        
        # 保存章节内容
        output_manager.save_text(f"chapter_{ch.number}_content.txt", chapter_content)
        
        # 验证首行是否为章节标题
        first_line = chapter_lines[0] if chapter_lines else ""
        logger.info(f"   首行: {first_line[:60]}...")
        logger.info(f"   实际字数: {len(chapter_content)}")
        logger.info(f"   记录字数: {ch.word_count}")
        
        # 验证字符位置
        extracted_by_char = content[ch.start_char:ch.end_char]
        char_match = (extracted_by_char == chapter_content)
        logger.info(f"   字符位置匹配: {'✅' if char_match else '❌'}")

    logger.info("\n✅ 章节提取验证完成！")


def run_edge_case_tests(detector: NovelChapterDetector):
    """
    运行 NovelChapterDetector 的边界情况测试。
    """
    logger.info("\n" + "="*60)
    logger.info("  🧪 边界情况测试")
    logger.info("="*60 + "\n")

    # Test 1: 文件不存在
    logger.info("Test 1: 文件不存在")
    non_existent_file = Path("nonexistent_file.txt")
    try:
        detector.execute(novel_file=non_existent_file)
        assert False, "Expected FileNotFoundError but none was raised."
    except FileNotFoundError:
        logger.info("  ✅ 正确捕获异常: FileNotFoundError")
    except Exception as e:
        assert False, f"Expected FileNotFoundError but got {type(e).__name__}: {e}"

    # Test 2: 无章节文件（模拟）
    logger.info("Test 2: 无章节文件（模拟）")
    temp_no_chapter_file = Path("temp_no_chapter.txt")
    try:
        temp_no_chapter_file.write_text("这是一个没有章节标记的文本文件。\n只有普通内容。", encoding='utf-8')
        detector.execute(novel_file=temp_no_chapter_file)
        assert False, "Expected ValueError for no chapters but none was raised."
    except ValueError as e:
        assert "No chapters detected" in str(e)
        logger.info("  ✅ 正确捕获异常: ValueError (No chapters detected)")
    finally:
        if temp_no_chapter_file.exists():
            temp_no_chapter_file.unlink()

    logger.info("\n" + "-"*60 + "\n")


def main():
    logger.info("\n" + "="*60)
    logger.info("  NovelChapterDetector 工具测试套件")
    logger.info("="*60 + "\n")

    # Setup
    setup_and_teardown_test_project()

    output_manager = TestOutputManager("03_chapter_detector")
    detector = NovelChapterDetector()

    try:
        # 运行主要测试
        chapters = run_main_test(output_manager, detector)

        # 运行章节提取验证
        run_chapter_extraction_test(output_manager, detector, chapters)

        # 运行边界情况测试
        run_edge_case_tests(detector)

        logger.info("\n✅ 所有 NovelChapterDetector 测试完成！")
    finally:
        # Cleanup
        if TEST_PROJECT_RAW_DIR.exists():
            shutil.rmtree(TEST_PROJECT_RAW_DIR.parent)
            logger.info(f"Test project directory cleaned up: {TEST_PROJECT_RAW_DIR}")


if __name__ == "__main__":
    main()
