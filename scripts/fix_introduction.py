"""
修复简介提取问题 - 使用 MetadataExtractor（LLM过滤）

遵循 .cursorrules 强制检查：
✅ Step 1: 找到 MetadataExtractor in docs/DEV_STANDARDS.md
✅ Step 2: 找到工具文件 src/tools/novel_chapter_processor.py
✅ Step 3: 正确调用 MetadataExtractor，不重复实现
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_chapter_processor import MetadataExtractor


def main():
    """修复简介提取"""
    print("="*80)
    print("修复简介提取（使用 MetadataExtractor + LLM过滤）")
    print("="*80)
    
    # 配置路径
    project_root = Path(__file__).parent.parent
    project_dir = project_root / "data/projects/with_novel/末哥超凡公路"
    raw_novel = project_dir / "raw/novel.txt"
    novel_dir = project_dir / "novel"
    
    # 读取原始小说
    print(f"\n📖 读取小说: {raw_novel}")
    with open(raw_novel, 'r', encoding='utf-8') as f:
        novel_text = f.read()
    
    # 使用 MetadataExtractor 提取简介（LLM过滤）
    print("\n" + "="*80)
    print("Step 1: 使用 MetadataExtractor（LLM过滤）")
    print("="*80)
    
    extractor = MetadataExtractor(use_llm=True)
    metadata = extractor.execute(novel_text)
    
    print(f"\n✅ 简介提取完成:")
    print(f"   作者: {metadata['novel']['author']}")
    print(f"   标签: {', '.join(metadata['novel']['tags'])}")
    print(f"   简介长度: {len(metadata['novel']['introduction'])} 字符")
    
    # 检查是否清理干净
    intro = metadata['novel']['introduction']
    issues = []
    if "又有书名" in intro:
        issues.append("包含'又有书名'")
    if "【" in intro and "】" in intro:
        issues.append("包含标签【】")
    if "Title:" in intro:
        issues.append("包含Title:")
    if "Author:" in intro:
        issues.append("包含Author:")
    if "[封面:" in intro:
        issues.append("包含封面链接")
    if "====" in intro:
        issues.append("包含分隔符====")
    
    if issues:
        print(f"\n   ⚠️  简介仍有问题: {', '.join(issues)}")
    else:
        print(f"   ✅ 简介已完全清理")
    
    # 保存干净的简介
    print("\n" + "="*80)
    print("Step 2: 保存干净简介")
    print("="*80)
    
    intro_file = novel_dir / "chpt_0000_简介.md"
    
    # 先备份旧文件
    if intro_file.exists():
        backup_file = novel_dir / "archive/v3_old_intro_20260208/chpt_0000_简介_old.md"
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(intro_file, backup_file)
        print(f"✅ 旧简介已备份: {backup_file.name}")
    
    # 写入新简介
    with open(intro_file, 'w', encoding='utf-8') as f:
        f.write(f"# {metadata['novel']['title']}\n\n")
        f.write("## 简介\n\n")
        f.write(metadata['novel']['introduction'])
    
    print(f"✅ 新简介已保存: {intro_file.name}")
    
    # 显示简介内容
    print("\n" + "="*80)
    print("简介内容预览:")
    print("="*80)
    print(metadata['novel']['introduction'][:200] + "..." if len(metadata['novel']['introduction']) > 200 else metadata['novel']['introduction'])
    
    print("\n" + "="*80)
    print("✅ 简介修复完成！")
    print("="*80)


if __name__ == "__main__":
    main()
