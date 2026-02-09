#!/bin/bash
# 运行所有 Novel 相关工具的测试
# 每个测试会生成独立的时间戳目录

set -e  # 遇到错误立即退出

PROJECT_ROOT="/Users/sevenx/Documents/coding/AI-Narrated Recap Analyst"
cd "$PROJECT_ROOT"

echo "========================================"
echo "🧪 开始测试所有 Novel 相关工具"
echo "========================================"
echo "📅 测试时间: $(date)"
echo ""

# 记录总体开始时间
OVERALL_START=$(date +%s)

# 1. NovelImporter
echo "📝 测试 1/4: NovelImporter（小说导入与规范化）"
echo "----------------------------------------"
TEST_START=$(date +%s)
PYTHONPATH="$PROJECT_ROOT" python3 scripts/test/test_novel_importer.py
TEST_END=$(date +%s)
TEST_DURATION=$((TEST_END - TEST_START))
echo "✅ 完成，耗时: ${TEST_DURATION}s"
echo ""

# 2. NovelMetadataExtractor
echo "📝 测试 2/4: NovelMetadataExtractor（元数据提取）"
echo "----------------------------------------"
TEST_START=$(date +%s)
PYTHONPATH="$PROJECT_ROOT" python3 scripts/test/test_novel_metadata_extractor.py
TEST_END=$(date +%s)
TEST_DURATION=$((TEST_END - TEST_START))
echo "✅ 完成，耗时: ${TEST_DURATION}s"
echo ""

# 3. NovelChapterDetector
echo "📝 测试 3/4: NovelChapterDetector（章节检测）"
echo "----------------------------------------"
TEST_START=$(date +%s)
PYTHONPATH="$PROJECT_ROOT" python3 scripts/test/test_novel_chapter_detector.py
TEST_END=$(date +%s)
TEST_DURATION=$((TEST_END - TEST_START))
echo "✅ 完成，耗时: ${TEST_DURATION}s"
echo ""

# 4. NovelSegmenter
echo "📝 测试 4/4: NovelSegmenter（叙事分段分析）"
echo "----------------------------------------"
echo "⚠️  注意：此测试会调用 Claude API，可能需要30-60秒"
TEST_START=$(date +%s)
PYTHONPATH="$PROJECT_ROOT" python3 scripts/test/test_novel_segmenter.py
TEST_END=$(date +%s)
TEST_DURATION=$((TEST_END - TEST_START))
echo "✅ 完成，耗时: ${TEST_DURATION}s"
echo ""

# 总结
OVERALL_END=$(date +%s)
OVERALL_DURATION=$((OVERALL_END - OVERALL_START))

echo "========================================"
echo "🎉 所有测试完成！"
echo "========================================"
echo "📊 总耗时: ${OVERALL_DURATION}s"
echo "📁 输出目录: output/temp/"
echo "💡 快速查看最新结果: ls -lht output/temp/ | head -10"
echo ""
echo "📋 工具测试结果："
echo "  ✅ 1. NovelImporter - 小说导入与规范化"
echo "  ✅ 2. NovelMetadataExtractor - 元数据提取"
echo "  ✅ 3. NovelChapterDetector - 章节检测"
echo "  ✅ 4. NovelSegmenter - 叙事分段分析"
echo ""
echo "🔍 查看最新输出："
echo "  cd output/temp/latest"
echo "========================================"
