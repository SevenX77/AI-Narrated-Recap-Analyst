"""
测试Novel-to-Script智能改编系统的新工具

测试内容：
1. NovelSegmentationAnalyzer - 小说分段深度分析
2. KeyInfoExtractor - 关键信息提取
3. ScriptSegmentAligner - Script-Novel精确对齐

使用项目：末哥超凡公路（PROJ_002）
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_segmentation_analyzer import NovelSegmentationAnalyzer
from src.tools.key_info_extractor import KeyInfoExtractor
from src.tools.script_segment_aligner import ScriptSegmentAligner


def print_section(title: str):
    """打印章节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_novel_segmentation_analyzer():
    """测试NovelSegmentationAnalyzer"""
    print_section("测试 1: NovelSegmentationAnalyzer - 小说分段深度分析")
    
    # 读取章节内容（第一章）
    project_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路"
    novel_file = project_dir / "novel/chpt_0001-0010.md"
    
    if not novel_file.exists():
        print(f"❌ 文件不存在: {novel_file}")
        return None
    
    with open(novel_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取第一章内容（简单分割）
    chapters = content.split("=== 第")[1:]  # 跳过简介
    if not chapters:
        print("❌ 无法解析章节")
        return None
    
    first_chapter = "=== 第" + chapters[0].split("=== 第")[0]
    
    # 截取前1000字符用于测试（避免超长文本）
    first_chapter = first_chapter[:1000]
    
    print(f"📖 章节内容长度: {len(first_chapter)} 字符")
    print(f"📖 章节内容预览:\n{first_chapter[:200]}...\n")
    
    # 创建分析器
    analyzer = NovelSegmentationAnalyzer()
    
    print("🔄 正在调用LLM进行分段分析...")
    print("⏳ 这可能需要10-20秒，请稍候...\n")
    
    try:
        # 执行分析
        result = analyzer.execute(
            chapter_text=first_chapter,
            chapter_id="chpt_0001",
            chapter_title="第一章",
            character_list=["陈野"],
            world_settings={"setting": "末日世界", "system": "升级系统"}
        )
        
        print("✅ 分析成功！\n")
        
        # 打印结果统计
        print(f"📊 分析结果统计:")
        print(f"  - 总段落数: {result.chapter_summary.total_segments}")
        print(f"  - P0-骨架: {result.chapter_summary.p0_count}")
        print(f"  - P1-血肉: {result.chapter_summary.p1_count}")
        print(f"  - P2-皮肤: {result.chapter_summary.p2_count}")
        print(f"  - 关键事件: {', '.join(result.chapter_summary.key_events)}")
        print(f"  - 埋设伏笔: {', '.join(result.chapter_summary.foreshadowing_planted)}")
        
        # 打印前3个段落的详细信息
        print(f"\n📝 前3个段落详细信息:")
        for i, seg in enumerate(result.segments[:3]):
            print(f"\n  【段落 {i+1}】 {seg.segment_id}")
            print(f"  原文: {seg.text[:50]}...")
            print(f"  标签:")
            print(f"    - 叙事功能: {', '.join(seg.tags.narrative_function)}")
            print(f"    - 叙事结构: {', '.join(seg.tags.structure)}")
            print(f"    - 优先级: {seg.tags.priority}")
            print(f"  浓缩建议: {seg.metadata.condensation_suggestion[:50]}...")
        
        # 保存结果到文件
        output_dir = project_dir / "novel/segmentation_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{result.chapter_id}_analysis_test.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_key_info_extractor(chapter_analysis):
    """测试KeyInfoExtractor"""
    print_section("测试 2: KeyInfoExtractor - 关键信息提取")
    
    if not chapter_analysis:
        print("⚠️  跳过测试（需要先完成测试1）")
        return None
    
    # 创建提取器
    extractor = KeyInfoExtractor()
    
    print("🔄 正在提取关键信息...")
    
    try:
        # 执行提取
        key_info = extractor.execute(
            chapter_analyses=[chapter_analysis],
            scope="test_chapter_1"
        )
        
        print("✅ 提取成功！\n")
        
        # 打印结果统计
        print(f"📊 关键信息统计:")
        print(f"  - P0骨架: {len(key_info.p0_skeleton)} 项")
        print(f"  - P1血肉: {len(key_info.p1_flesh)} 项")
        print(f"  - P2皮肤: {len(key_info.p2_skin)} 项")
        print(f"  - 角色数量: {len(key_info.character_arcs)}")
        
        # 打印P0信息
        if key_info.p0_skeleton:
            print(f"\n📌 P0骨架信息（前3项）:")
            for i, info in enumerate(key_info.p0_skeleton[:3]):
                print(f"  {i+1}. {info['segment_id']}")
                print(f"     内容: {info['content'][:40]}...")
                print(f"     重要性: {info['importance']}")
        
        # 打印伏笔信息
        planted = key_info.foreshadowing_map.get("planted", [])
        if planted:
            print(f"\n🎣 埋设的伏笔:")
            for fh in planted:
                print(f"  - {fh['content']} (章节: {fh['chapter_id']})")
        
        # 打印浓缩指导
        print(f"\n📋 浓缩指导原则:")
        print(f"  必须保留: {', '.join(key_info.condensation_guidelines.get('must_retain', [])[:3])}")
        print(f"  可以简化: {', '.join(key_info.condensation_guidelines.get('can_simplify', [])[:3])}")
        print(f"  可以省略: {', '.join(key_info.condensation_guidelines.get('can_omit', [])[:3])}")
        
        # 保存结果
        project_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路"
        output_dir = project_dir / "analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "key_info_test.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(key_info.model_dump(), f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_file}")
        
        return key_info
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_script_segment_aligner(chapter_analysis):
    """测试ScriptSegmentAligner"""
    print_section("测试 3: ScriptSegmentAligner - Script-Novel精确对齐")
    
    if not chapter_analysis:
        print("⚠️  跳过测试（需要先完成测试1）")
        return None
    
    # 读取Script
    project_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路"
    script_file = project_dir / "script/ep01.md"
    
    if not script_file.exists():
        print(f"❌ Script文件不存在: {script_file}")
        return None
    
    with open(script_file, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    print(f"📜 Script长度: {len(script_content)} 字符")
    print(f"📜 Script预览:\n{script_content[:200]}...\n")
    
    # 创建对齐器
    aligner = ScriptSegmentAligner()
    
    print("🔄 正在执行Script-Novel对齐...")
    print("⏳ 这可能需要1-2分钟（每段Script需要调用LLM），请稍候...\n")
    
    try:
        # 执行对齐
        result = aligner.execute(
            script_text=script_content,
            novel_analyses=[chapter_analysis],
            episode_id="ep01_test"
        )
        
        print("✅ 对齐成功！\n")
        
        # 打印整体统计
        stats = result.overall_stats
        print(f"📊 对齐结果统计:")
        print(f"  - Script段落数: {stats.total_script_segments}")
        print(f"  - 小说段落数: {stats.total_novel_segments}")
        print(f"  - 浓缩比例: {stats.condensation_ratio:.2%}")
        print(f"  - P0保留率: {stats.p0_retention_rate:.2%}")
        print(f"  - P1保留率: {stats.p1_retention_rate:.2%}")
        print(f"  - P2保留率: {stats.p2_retention_rate:.2%}")
        print(f"  - 平均对齐置信度: {stats.avg_alignment_confidence:.2%}")
        
        # 打印前3个对齐结果
        print(f"\n📝 前3个对齐结果:")
        for i, alignment in enumerate(result.alignments[:3]):
            print(f"\n  【对齐 {i+1}】")
            print(f"  Script时间: {alignment.script_segment.time_range}")
            print(f"  Script类型: {alignment.script_segment.segment_type}")
            print(f"  Script内容: {alignment.script_segment.text[:50]}...")
            print(f"  对应小说段落: {', '.join(alignment.novel_source.segments[:3])}")
            print(f"  浓缩比例: {alignment.novel_source.condensation_ratio:.2%}")
            print(f"  保留标签: {', '.join(alignment.novel_source.retained_tags[:3])}")
            print(f"  改编技巧: {', '.join(alignment.novel_source.transformation.get('techniques', [])[:2])}")
            print(f"  对齐置信度: {alignment.analysis.alignment_confidence:.2%}")
        
        # 保存结果
        output_dir = project_dir / "script/alignment_to_novel"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{result.episode_id}_mapping_test.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"❌ 对齐失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主测试流程"""
    print("\n" + "🚀" * 40)
    print("  Novel-to-Script 智能改编系统 - 工具测试")
    print("🚀" * 40)
    
    print("\n📌 测试说明:")
    print("  - 使用项目: 末哥超凡公路（PROJ_002）")
    print("  - 测试数据: 第一章（部分内容）")
    print("  - LLM模型: DeepSeek V3")
    print("  - 预计耗时: 2-3分钟")
    
    input("\n按Enter键开始测试...")
    
    # 测试1: 小说分段分析
    chapter_analysis = test_novel_segmentation_analyzer()
    
    if not chapter_analysis:
        print("\n❌ 测试1失败，无法继续后续测试")
        return
    
    input("\n按Enter键继续测试2...")
    
    # 测试2: 关键信息提取
    key_info = test_key_info_extractor(chapter_analysis)
    
    input("\n按Enter键继续测试3...")
    
    # 测试3: Script-Novel对齐
    alignment_result = test_script_segment_aligner(chapter_analysis)
    
    # 总结
    print_section("测试总结")
    
    results = {
        "NovelSegmentationAnalyzer": "✅" if chapter_analysis else "❌",
        "KeyInfoExtractor": "✅" if key_info else "❌",
        "ScriptSegmentAligner": "✅" if alignment_result else "❌"
    }
    
    print("测试结果:")
    for tool, status in results.items():
        print(f"  {status} {tool}")
    
    if all(r == "✅" for r in results.values()):
        print("\n🎉 所有测试通过！工具运行正常。")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")
    
    print("\n📁 输出文件位置:")
    print("  - 分段分析: data/projects/with_novel/末哥超凡公路/novel/segmentation_analysis/")
    print("  - 关键信息: data/projects/with_novel/末哥超凡公路/analysis/")
    print("  - 对齐结果: data/projects/with_novel/末哥超凡公路/script/alignment_to_novel/")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
