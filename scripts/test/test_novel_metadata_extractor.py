"""
Test Script for NovelMetadataExtractor Tool
测试 NovelMetadataExtractor 工具并输出临时文件供检查

测试内容：
1. 从导入的小说文件提取元数据
2. 验证标题、作者、标签提取
3. 验证简介智能过滤（LLM + 规则）
4. 输出临时文件供人工检查
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_metadata_extractor import NovelMetadataExtractor
from test_helpers import TestOutputManager, print_section, format_file_size

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_novel_metadata_extractor():
    """测试 NovelMetadataExtractor 并输出临时文件"""
    
    print_section("🔧 NovelMetadataExtractor 工具测试", "=")
    
    # 1. 初始化
    print("📝 初始化工具...")
    output = TestOutputManager("02_metadata_extractor")
    extractor = NovelMetadataExtractor(use_llm=True)
    
    # 2. 查找测试文件（使用 NovelImporter 导入的文件）
    test_file = project_root / "data/projects/末哥超凡公路_test/raw/novel.txt"
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        print("💡 请先运行 test_novel_importer.py 导入小说文件")
        return None
    
    print(f"📖 测试文件: {test_file.name}")
    print(f"📊 文件大小: {format_file_size(test_file.stat().st_size)}")
    
    # 3. 执行元数据提取
    print("\n🚀 执行元数据提取...")
    try:
        metadata = extractor.execute(novel_file=test_file)
        print("✅ 提取成功！")
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        logger.exception("Metadata extraction failed")
        return None
    
    # 4. 保存检查文件
    print("\n💾 保存检查文件...")
    
    # 4.1 完整的元数据
    metadata_dict = {
        "title": metadata.title,
        "author": metadata.author,
        "tags": metadata.tags,
        "tag_count": len(metadata.tags),
        "introduction": metadata.introduction,
        "introduction_length": len(metadata.introduction),
        "chapter_count": metadata.chapter_count
    }
    output.save_json("metadata.json", metadata_dict)
    
    # 4.2 提取的标签列表
    tags_data = {
        "count": len(metadata.tags),
        "tags": metadata.tags
    }
    output.save_json("tags.json", tags_data)
    
    # 4.3 过滤后的简介
    output.save_text("filtered_introduction.txt", metadata.introduction)
    
    # 4.4 读取原始文件对比（提取原始简介）
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取原始简介用于对比
    lines = content.split('\n')
    raw_intro_lines = []
    in_intro = False
    for line in lines:
        if line.strip() == '简介:':
            in_intro = True
            continue
        if in_intro:
            if '====' in line or line.startswith('=== 第'):
                break
            if line.strip():
                raw_intro_lines.append(line.strip())
    
    raw_introduction = '\n'.join(raw_intro_lines)
    output.save_text("raw_introduction.txt", raw_introduction)
    
    # 4.5 生成对比报告
    comparison = f"""# 简介过滤对比报告

## 原始简介
**长度**: {len(raw_introduction)} 字符
**行数**: {len(raw_intro_lines)} 行

```
{raw_introduction}
```

## 过滤后简介
**长度**: {len(metadata.introduction)} 字符
**压缩率**: {(1 - len(metadata.introduction) / len(raw_introduction)) * 100:.1f}%

```
{metadata.introduction}
```

## 移除的内容
**移除字符数**: {len(raw_introduction) - len(metadata.introduction)}

"""
    output.save_text("comparison.md", comparison)
    
    # 5. 打印摘要
    print_section("📊 测试结果摘要", "-")
    
    print(f"✅ 提取状态: 成功")
    print(f"📖 标题: {metadata.title}")
    print(f"✍️  作者: {metadata.author}")
    print(f"🏷️  标签数: {len(metadata.tags)}")
    print(f"🏷️  标签: {', '.join(metadata.tags[:5])}")
    if len(metadata.tags) > 5:
        print(f"         ... 及其他 {len(metadata.tags) - 5} 个")
    
    print(f"\n📝 简介信息:")
    print(f"   - 原始长度: {len(raw_introduction)} 字符")
    print(f"   - 过滤后长度: {len(metadata.introduction)} 字符")
    print(f"   - 压缩率: {(1 - len(metadata.introduction) / len(raw_introduction)) * 100:.1f}%")
    
    # 显示简介前200字
    intro_preview = metadata.introduction[:200]
    if len(metadata.introduction) > 200:
        intro_preview += "..."
    print(f"\n📄 简介预览:")
    for line in intro_preview.split('\n'):
        print(f"   {line}")
    
    print(f"\n📁 临时输出: {output.get_path()}")
    print(f"💡 快速查看:")
    print(f"   - 元数据: cat {output.get_path()}/metadata.json")
    print(f"   - 对比报告: cat {output.get_path()}/comparison.md")
    print(f"   - 过滤后简介: cat {output.get_path()}/filtered_introduction.txt")
    
    print_section("", "-")
    
    return metadata


def test_edge_cases():
    """测试边界情况"""
    
    print_section("🧪 边界情况测试", "=")
    
    extractor = NovelMetadataExtractor()
    
    # 测试1: 文件不存在
    print("Test 1: 文件不存在")
    try:
        extractor.execute(novel_file="nonexistent_file.txt")
        print("  ❌ 应该抛出 FileNotFoundError")
    except FileNotFoundError as e:
        print(f"  ✅ 正确捕获异常: {type(e).__name__}")
    
    print_section("", "-")


def test_llm_vs_rules():
    """对比 LLM 过滤和规则过滤"""
    
    print_section("🔬 LLM vs 规则过滤对比", "=")
    
    test_file = project_root / "data/projects/末哥超凡公路_test/raw/novel.txt"
    
    if not test_file.exists():
        print("❌ 测试文件不存在，跳过对比测试")
        return
    
    # 测试 LLM 过滤
    print("\n1️⃣ 使用 LLM 过滤...")
    extractor_llm = NovelMetadataExtractor(use_llm=True)
    try:
        metadata_llm = extractor_llm.execute(test_file, use_llm=True)
        print(f"   ✅ LLM 过滤成功")
        print(f"   📝 简介长度: {len(metadata_llm.introduction)} 字符")
    except Exception as e:
        print(f"   ⚠️  LLM 过滤失败: {e}")
        metadata_llm = None
    
    # 测试规则过滤
    print("\n2️⃣ 使用规则过滤...")
    extractor_rules = NovelMetadataExtractor(use_llm=False)
    metadata_rules = extractor_rules.execute(test_file, use_llm=False)
    print(f"   ✅ 规则过滤成功")
    print(f"   📝 简介长度: {len(metadata_rules.introduction)} 字符")
    
    # 对比结果
    if metadata_llm:
        print("\n📊 对比结果:")
        print(f"   LLM 简介长度: {len(metadata_llm.introduction)} 字符")
        print(f"   规则简介长度: {len(metadata_rules.introduction)} 字符")
        diff = len(metadata_llm.introduction) - len(metadata_rules.introduction)
        print(f"   差异: {abs(diff)} 字符 ({'LLM更短' if diff < 0 else 'LLM更长'})")
    
    print_section("", "-")


def main():
    """主测试函数"""
    
    print("\n" + "="*60)
    print("  NovelMetadataExtractor 工具测试套件")
    print("="*60 + "\n")
    
    # 运行主测试
    metadata = test_novel_metadata_extractor()
    
    if metadata:
        print("\n✅ 主测试完成！\n")
        
        # 可选：运行对比测试
        test_llm_vs_rules()
        
        # 可选：运行边界测试
        test_edge_cases()
    else:
        print("\n❌ 主测试失败，请检查错误信息。\n")
    
    return metadata


if __name__ == "__main__":
    main()
