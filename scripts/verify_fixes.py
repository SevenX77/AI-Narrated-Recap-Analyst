"""
验证所有修复结果
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """验证所有修复"""
    print("="*80)
    print("验证所有修复结果")
    print("="*80)
    
    project_root = Path(__file__).parent.parent
    project_dir = project_root / "data/projects/with_novel/末哥超凡公路"
    novel_dir = project_dir / "novel"
    analysis_dir = novel_dir / "functional_analysis"
    
    all_passed = True
    
    # ============================================================
    # 验证1：简介是否清理干净
    # ============================================================
    print("\n" + "="*80)
    print("验证1：简介清理")
    print("="*80)
    
    intro_file = novel_dir / "chpt_0000_简介.md"
    if intro_file.exists():
        with open(intro_file, 'r', encoding='utf-8') as f:
            intro_content = f.read()
        
        issues = []
        if "又有书名" in intro_content:
            issues.append("包含'又有书名'")
        if "【" in intro_content and "】" in intro_content:
            issues.append("包含标签【】")
        if "Title:" in intro_content:
            issues.append("包含Title:")
        if "Author:" in intro_content:
            issues.append("包含Author:")
        if "[封面:" in intro_content:
            issues.append("包含封面链接")
        if "====" in intro_content:
            issues.append("包含分隔符====")
        
        if issues:
            print(f"❌ 简介仍有问题:")
            for issue in issues:
                print(f"   - {issue}")
            all_passed = False
        else:
            print(f"✅ 简介已完全清理")
            print(f"   文件: {intro_file.name}")
            print(f"   长度: {len(intro_content)} 字符")
    else:
        print(f"❌ 简介文件不存在: {intro_file}")
        all_passed = False
    
    # ============================================================
    # 验证2：旧版本是否归档
    # ============================================================
    print("\n" + "="*80)
    print("验证2：旧版本归档")
    print("="*80)
    
    old_intro = novel_dir / "chpt_0000.md"
    if old_intro.exists():
        print(f"❌ 旧版本简介仍在主目录: {old_intro}")
        all_passed = False
    else:
        print(f"✅ 旧版本简介已归档")
    
    archive_intro = novel_dir / "archive/v3_old_intro_20260208/chpt_0000.md"
    if archive_intro.exists():
        print(f"✅ 已归档到: {archive_intro}")
    else:
        print(f"⚠️  归档文件不存在（可能是首次处理）")
    
    # ============================================================
    # 验证3：版本管理是否正确
    # ============================================================
    print("\n" + "="*80)
    print("验证3：版本管理")
    print("="*80)
    
    # 检查主目录
    versioned_files = list(analysis_dir.glob("chpt_*_v*.json"))
    if versioned_files:
        print(f"❌ 主目录中仍有版本文件 ({len(versioned_files)}个):")
        for vf in versioned_files[:5]:  # 只显示前5个
            print(f"   - {vf.name}")
        if len(versioned_files) > 5:
            print(f"   ... 还有 {len(versioned_files) - 5} 个")
        all_passed = False
    else:
        print(f"✅ 主目录只有_latest.json文件")
    
    # 检查latest文件
    latest_files = list(analysis_dir.glob("chpt_*_latest.json"))
    print(f"✅ _latest.json文件数: {len(latest_files)}")
    expected_chapters = list(range(1, 11))
    for chap in expected_chapters:
        latest_file = analysis_dir / f"chpt_{chap:04d}_functional_analysis_latest.json"
        if latest_file.exists():
            print(f"   ✅ 第{chap}章")
        else:
            print(f"   ❌ 第{chap}章缺失")
            all_passed = False
    
    # 检查history目录
    history_dir = analysis_dir / "history"
    if history_dir.exists():
        history_files = list(history_dir.glob("*.json"))
        print(f"✅ history/目录存在，包含 {len(history_files)} 个版本文件")
    else:
        print(f"❌ history/目录不存在")
        all_passed = False
    
    # ============================================================
    # 验证4：Markdown分段文件是否存在
    # ============================================================
    print("\n" + "="*80)
    print("验证4：Markdown分段文件")
    print("="*80)
    
    for chapter_num in range(1, 11):
        md_file = analysis_dir / f"第{chapter_num}章完整分段分析.md"
        if md_file.exists():
            print(f"   ✅ 第{chapter_num}章 Markdown")
        else:
            print(f"   ❌ 第{chapter_num}章 Markdown 缺失")
            all_passed = False
    
    # ============================================================
    # 最终结果
    # ============================================================
    print("\n" + "="*80)
    if all_passed:
        print("✅ 所有验证通过！")
    else:
        print("❌ 部分验证失败，请检查上述问题")
    print("="*80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
