"""
测试 NovelValidator 工具

验证小说处理质量验证功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_validator import NovelValidator
from src.tools.novel_importer import NovelImporter
from src.tools.novel_chapter_detector import NovelChapterDetector
from src.tools.novel_segmenter import NovelSegmenter
from src.tools.novel_annotator import NovelAnnotator

def test_novel_validator():
    """测试NovelValidator"""
    print("=" * 60)
    print("测试 NovelValidator - 小说处理质量验证")
    print("=" * 60)
    
    # 配置
    project_name = "末哥超凡公路_output_test"
    novel_path = f"data/projects/{project_name}/raw/novel.txt"
    
    # Step 1: 导入小说
    print("\n[Step 1] 导入小说...")
    importer = NovelImporter()
    import_result = importer.execute(
        source_file=novel_path,
        project_name=project_name
    )
    print(f"✅ 导入完成: {import_result.char_count} 字符")
    
    # Step 2: 检测章节
    print("\n[Step 2] 检测章节...")
    detector = NovelChapterDetector()
    chapter_infos = detector.execute(novel_file=novel_path)
    print(f"✅ 检测到 {len(chapter_infos)} 个章节")
    
    # Step 3: 基础验证（只验证导入和章节）
    print("\n[Step 3] 基础质量验证...")
    validator = NovelValidator()
    
    report = validator.execute(
        import_result=import_result,
        chapter_infos=chapter_infos
    )
    
    print(f"\n{'='*60}")
    print(f"验证报告")
    print(f"{'='*60}")
    print(f"项目名称: {report.project_name}")
    print(f"质量评分: {report.quality_score}/100")
    print(f"是否通过: {'✅ 通过' if report.is_valid else '❌ 未通过'}")
    
    print(f"\n编码检查: {'✅' if report.encoding_check['passed'] else '❌'}")
    print(f"  - 无效字符数: {report.encoding_check.get('invalid_chars_count', 0)}")
    
    print(f"\n章节检查: {'✅' if report.chapter_check['passed'] else '❌'}")
    print(f"  - 章节总数: {report.chapter_check['total_chapters']}")
    print(f"  - 缺失章节: {report.chapter_check.get('missing_chapters', [])}")
    
    if report.issues:
        print(f"\n⚠️  发现 {len(report.issues)} 个问题:")
        for issue in report.issues[:5]:
            print(f"  [{issue.severity}] {issue.description}")
    
    if report.warnings:
        print(f"\n⚠️  警告 ({len(report.warnings)} 条):")
        for warning in report.warnings[:5]:
            print(f"  - {warning}")
    
    if report.recommendations:
        print(f"\n💡 建议:")
        for rec in report.recommendations:
            print(f"  - {rec}")
    
    print(f"\n统计信息:")
    for key, value in report.statistics.items():
        print(f"  {key}: {value}")
    
    # Step 4: 完整验证（包含分段和标注）
    print(f"\n{'='*60}")
    print("[Step 4] 完整质量验证（包含分段和标注）")
    print(f"{'='*60}")
    print("⚠️  此步骤需要先运行分段和标注流程，跳过...")
    print("💡 提示: 运行 test_novel_segmenter.py 和 test_novel_annotator.py 后再测试")
    
    return report


if __name__ == "__main__":
    try:
        report = test_novel_validator()
        print(f"\n{'='*60}")
        print("✅ NovelValidator 测试完成")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
