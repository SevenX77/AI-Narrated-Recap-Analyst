"""
测试 NovelChapterAnalyzer - 功能段级别的小说章节分析

使用项目：末哥超凡公路
测试章节：第一章
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer


def print_section(title: str):
    """打印章节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_novel_chapter_analyzer():
    """测试NovelChapterAnalyzer"""
    print_section("测试 NovelChapterAnalyzer - 功能段分析")
    
    # 读取原始小说文件
    project_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路"
    novel_file = project_dir / "raw/novel.txt"
    
    if not novel_file.exists():
        print(f"❌ 文件不存在: {novel_file}")
        return None
    
    with open(novel_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取第一章内容
    import re
    chapter_pattern = r'===\s*第\s*(\d+)\s*章\s*(.*)===\s*\n'
    matches = list(re.finditer(chapter_pattern, content))
    
    if len(matches) < 1:
        print("❌ 无法解析章节")
        return None
    
    # 提取第一章
    start_match = matches[0]
    chapter_number = int(start_match.group(1))
    chapter_title = start_match.group(2).strip()
    
    start_pos = start_match.end()
    end_pos = matches[1].start() if len(matches) > 1 else len(content)
    chapter_content = content[start_pos:end_pos].strip()
    
    print(f"📖 章节信息:")
    print(f"  - 章节号: 第{chapter_number}章")
    print(f"  - 标题: {chapter_title}")
    print(f"  - 内容长度: {len(chapter_content)} 字符")
    print(f"  - 内容预览: {chapter_content[:200]}...\n")
    
    # 创建分析器
    analyzer = NovelChapterAnalyzer()
    
    print("🔄 正在调用LLM进行功能段分析...")
    print("⏳ 这可能需要30-60秒，请稍候...\n")
    
    try:
        # 执行分析
        result = analyzer.execute(
            chapter_content=chapter_content,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            novel_title="序列公路求生：我在末日升级物资",
            known_characters=["陈野"],
            known_world_settings={"setting": "末日世界", "system": "诡异规则"}
        )
        
        print("✅ 分析成功！\n")
        
        # 打印结果统计
        print(f"📊 分析结果统计:")
        print(f"  - 功能段总数: {result.chapter_summary.total_segments}")
        print(f"  - P0-骨架: {result.chapter_summary.p0_count}")
        print(f"  - P1-血肉: {result.chapter_summary.p1_count}")
        print(f"  - P2-皮肤: {result.chapter_summary.p2_count}")
        print(f"  - 关键事件: {', '.join(result.chapter_summary.key_events)}")
        if result.chapter_summary.foreshadowing_planted:
            print(f"  - 埋设伏笔: {len(result.chapter_summary.foreshadowing_planted)}处")
        
        # 打印前3个功能段
        print(f"\n📝 前{min(3, len(result.segments))}个功能段:")
        for i, seg in enumerate(result.segments[:3]):
            print(f"\n  【{seg.title}】")
            print(f"  ID: {seg.segment_id}")
            print(f"  内容: {seg.content[:80]}...")
            print(f"  叙事功能: {', '.join(seg.tags.narrative_function)}")
            print(f"  优先级: {seg.tags.priority}")
            print(f"  字数: {seg.metadata.word_count}")
        
        # 打印结构洞察
        if result.structure_insight.opening_style:
            print(f"\n🎯 章节结构洞察:")
            print(f"  - 开篇方式: {result.structure_insight.opening_style}")
            if result.structure_insight.turning_point:
                print(f"  - 转折点: {result.structure_insight.turning_point}")
            if result.structure_insight.ending_hook:
                print(f"  - 章节钩子: {result.structure_insight.ending_hook}")
        
        # 保存结果
        output_dir = project_dir / "novel/functional_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存Markdown
        md_file = output_dir / f"第{chapter_number}章完整分段分析.md"
        analyzer.save_markdown(result, md_file)
        print(f"\n💾 Markdown已保存到: {md_file}")
        
        # 保存JSON
        json_file = output_dir / f"chpt_{chapter_number:04d}_functional_analysis.json"
        analyzer.save_json(result, json_file)
        print(f"💾 JSON已保存到: {json_file}")
        
        return result
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主测试流程"""
    print("\n" + "🚀" * 40)
    print("  NovelChapterAnalyzer - 功能段分析测试")
    print("🚀" * 40)
    
    print("\n📌 测试说明:")
    print("  - 使用项目: 末哥超凡公路")
    print("  - 测试数据: 第一章（完整章节）")
    print("  - 分析方式: 100% LLM功能段分析")
    print("  - 输出格式: Markdown + JSON")
    print("  - 预计耗时: 30-60秒")
    
    # 测试功能段分析
    result = test_novel_chapter_analyzer()
    
    # 总结
    print_section("测试总结")
    
    if result:
        print("✅ NovelChapterAnalyzer 测试通过！")
        print(f"\n📊 分析质量:")
        print(f"  - 功能段数量: {result.chapter_summary.total_segments} (预期: 10-15个)")
        print(f"  - P0/P1/P2分布: {result.chapter_summary.p0_count}/{result.chapter_summary.p1_count}/{result.chapter_summary.p2_count}")
        print(f"  - 结构洞察: {'✅' if result.structure_insight.opening_style else '❌'}")
        print(f"  - 浓缩版本: {'✅' if result.chapter_summary.condensed_version else '❌'}")
        
        print("\n📁 输出文件:")
        print("  - Markdown: novel/functional_analysis/第1章完整分段分析.md")
        print("  - JSON: novel/functional_analysis/chpt_0001_functional_analysis.json")
        
        print("\n🎯 下一步:")
        print("  1. 查看生成的Markdown文件，验证分析质量")
        print("  2. 对比人工分析结果（分析资料/有原小说/01_末哥超凡公路/novel/第一章完整分段分析.md）")
        print("  3. 如果满意，批量处理第2-10章")
    else:
        print("❌ 测试失败，请检查错误信息")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
