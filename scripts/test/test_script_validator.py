"""
测试 ScriptValidator 工具

验证脚本处理质量验证功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.script_validator import ScriptValidator
from src.tools.srt_importer import SrtImporter
from src.tools.srt_text_extractor import SrtTextExtractor
from src.tools.script_segmenter import ScriptSegmenter

def test_script_validator():
    """测试ScriptValidator"""
    print("=" * 60)
    print("测试 ScriptValidator - 脚本处理质量验证")
    print("=" * 60)
    
    # 配置
    project_name = "天命桃花_test"
    episode_name = "ep01"
    srt_path = "分析资料/有原小说/02_天命桃花/srt/ep01.srt"
    
    # Step 1: 导入SRT
    print("\n[Step 1] 导入SRT...")
    importer = SrtImporter()
    import_result = importer.execute(
        source_file=srt_path,
        project_name=project_name,
        episode_name=episode_name
    )
    srt_entries = import_result.entries if hasattr(import_result, 'entries') and import_result.entries else []
    print(f"✅ 导入完成: {len(srt_entries)} 条字幕")
    
    # Step 2: 基础验证（只验证时间轴）
    print("\n[Step 2] 基础质量验证（时间轴）...")
    validator = ScriptValidator()
    
    report = validator.execute(
        srt_entries=srt_entries,
        episode_name=episode_name
    )
    
    print(f"\n{'='*60}")
    print(f"验证报告")
    print(f"{'='*60}")
    print(f"集数: {report.episode_name}")
    print(f"质量评分: {report.quality_score}/100")
    print(f"是否通过: {'✅ 通过' if report.is_valid else '❌ 未通过'}")
    
    print(f"\n时间轴检查: {'✅' if report.timeline_check['passed'] else '❌'}")
    print(f"  - 总条目数: {report.timeline_check['total_entries']}")
    print(f"  - 时间轴间隔: {len(report.timeline_check.get('gaps', []))} 处")
    print(f"  - 时间轴重叠: {len(report.timeline_check.get('overlaps', []))} 处")
    
    if report.issues:
        print(f"\n⚠️  发现 {len(report.issues)} 个问题:")
        for issue in report.issues[:5]:
            print(f"  [{issue.severity}] {issue.description}")
            if issue.location:
                print(f"      位置: {issue.location}")
    
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
    
    # Step 3: 完整验证（包含文本提取和分段）
    print(f"\n{'='*60}")
    print("[Step 3] 完整质量验证（包含文本提取和分段）")
    print(f"{'='*60}")
    print("⚠️  此步骤需要先运行文本提取和分段流程，跳过...")
    print("💡 提示: 运行 test_srt_text_extractor.py 和 test_script_segmenter.py 后再测试")
    
    return report


if __name__ == "__main__":
    try:
        report = test_script_validator()
        print(f"\n{'='*60}")
        print("✅ ScriptValidator 测试完成")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
