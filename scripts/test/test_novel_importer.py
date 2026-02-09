"""
Test Script for NovelImporter Tool
测试 NovelImporter 工具并输出临时文件供检查

测试内容：
1. 读取并规范化小说文件
2. 验证编码检测
3. 验证规范化操作
4. 输出临时文件供人工检查
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_importer import NovelImporter
from test_helpers import TestOutputManager, print_section, format_file_size

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_novel_importer():
    """测试 NovelImporter 并输出临时文件"""
    
    print_section("🔧 NovelImporter 工具测试", "=")
    
    # 1. 初始化
    print("📝 初始化工具...")
    output = TestOutputManager("01_novel_importer")
    importer = NovelImporter()
    
    # 2. 查找测试文件
    test_file = project_root / "分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    project_name = "末哥超凡公路_test"
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        print("💡 请提供有效的小说文件路径")
        return None
    
    print(f"📖 测试文件: {test_file.name}")
    print(f"📊 文件大小: {format_file_size(test_file.stat().st_size)}")
    print(f"🎯 目标项目: {project_name}")
    
    # 3. 执行导入（保存到项目目录 + 获取内容）
    print("\n🚀 执行导入...")
    try:
        result = importer.execute(
            source_file=test_file,
            project_name=project_name,
            save_to_disk=True,
            include_content=True  # 获取内容用于临时输出
        )
        print("✅ 导入成功！")
        print(f"📁 已保存到: {result.saved_path}")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        logger.exception("Import failed")
        return None
    
    # 4. 验证文件已保存到项目目录
    print("\n🔍 验证文件保存...")
    saved_file = Path(result.saved_path)
    if saved_file.exists():
        print(f"✅ 文件已保存: {saved_file}")
        print(f"📊 保存文件大小: {format_file_size(saved_file.stat().st_size)}")
    else:
        print(f"❌ 文件未找到: {saved_file}")
    
    # 5. 保存检查文件到临时目录（供人工验证）
    print("\n💾 保存检查文件到临时目录...")
    
    # 5.1 完整的规范化文本
    if result.content:
        output.save_text("normalized_text.txt", result.content)
        
        # 5.2 元数据
        metadata = {
            "saved_path": result.saved_path,
            "original_path": result.original_path,
            "project_name": result.project_name,
            "encoding": result.encoding,
            "file_size": result.file_size,
            "file_size_readable": format_file_size(result.file_size),
            "line_count": result.line_count,
            "char_count": result.char_count,
            "has_bom": result.has_bom,
            "normalization_applied": result.normalization_applied
        }
        output.save_json("metadata.json", metadata)
        
        # 5.3 前100行预览
        lines = result.content.split('\n')
        preview_lines = lines[:100]
        output.save_lines("preview_first_100_lines.txt", preview_lines)
        
        # 5.4 统计分析
        # 计算非空行数
        non_empty_lines = [line for line in lines if line.strip()]
        avg_chars_per_line = result.char_count / len(non_empty_lines) if non_empty_lines else 0
        
        # 检测可能的章节标题（简单检测）
        chapter_markers = [
            line for line in lines 
            if any(marker in line for marker in ['第', '章', 'Chapter', 'CHAPTER'])
        ]
        
        stats = {
            "total_lines": result.line_count,
            "non_empty_lines": len(non_empty_lines),
            "empty_lines": result.line_count - len(non_empty_lines),
            "avg_chars_per_line": round(avg_chars_per_line, 2),
            "possible_chapter_markers": len(chapter_markers)
        }
        output.save_json("statistics.json", stats)
        
        # 5.5 章节标记预览（如果有）
        if chapter_markers:
            output.save_lines("possible_chapter_markers.txt", chapter_markers[:50])
    
    # 6. 打印摘要
    print_section("📊 测试结果摘要", "-")
    
    print(f"✅ 导入状态: 成功")
    print(f"📁 保存位置: {result.saved_path}")
    print(f"📄 原始编码: {result.encoding}")
    print(f"📊 文件大小: {format_file_size(result.file_size)}")
    print(f"📝 字符数: {result.char_count:,}")
    print(f"📋 总行数: {result.line_count:,}")
    
    if result.content:
        lines = result.content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        avg_chars_per_line = result.char_count / len(non_empty_lines) if non_empty_lines else 0
        chapter_markers = [
            line for line in lines 
            if any(marker in line for marker in ['第', '章', 'Chapter', 'CHAPTER'])
        ]
        
        print(f"📋 非空行数: {len(non_empty_lines):,}")
        print(f"💾 平均每行字符数: {avg_chars_per_line:.1f}")
        print(f"🔖 可能的章节标记: {len(chapter_markers)}")
    
    print(f"🔧 规范化操作: {', '.join(result.normalization_applied)}")
    print(f"⚠️  是否有BOM: {'是' if result.has_bom else '否'}")
    
    print(f"\n📁 项目目录: {result.saved_path}")
    print(f"📁 临时输出: {output.get_path()}")
    print(f"💡 快速查看:")
    print(f"   - 项目文件: cat {result.saved_path}")
    print(f"   - 元数据: cat {output.get_path()}/metadata.json")
    print(f"   - 预览: head -50 {output.get_path()}/preview_first_100_lines.txt")
    
    print_section("", "-")
    
    return result


def test_edge_cases():
    """测试边界情况"""
    
    print_section("🧪 边界情况测试", "=")
    
    importer = NovelImporter()
    
    # 测试1: 不存在的文件
    print("Test 1: 文件不存在")
    try:
        importer.execute(
            source_file="nonexistent_file.txt",
            project_name="test"
        )
        print("  ❌ 应该抛出 FileNotFoundError")
    except FileNotFoundError as e:
        print(f"  ✅ 正确捕获异常: {e}")
    
    # 测试2: 空文件（如果有的话）
    # 这里可以创建临时空文件测试
    
    print_section("", "-")


def main():
    """主测试函数"""
    import sys
    
    print("\n" + "="*60)
    print("  NovelImporter 工具测试套件")
    print("="*60 + "\n")
    
    # 运行主测试
    result = test_novel_importer()
    
    if result:
        print("\n✅ 测试完成！请检查输出文件验证结果。\n")
        
        # 可选：运行边界测试（仅在交互式环境）
        if sys.stdin.isatty():
            run_edge_tests = input("是否运行边界情况测试？(y/n): ").strip().lower()
            if run_edge_tests == 'y':
                test_edge_cases()
        else:
            print("ℹ️  非交互式环境，跳过边界测试")
    else:
        print("\n❌ 主测试失败，请检查错误信息。\n")
    
    return result


if __name__ == "__main__":
    main()
