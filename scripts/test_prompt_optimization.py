"""
测试 Prompt 优化效果 - 对比优化前后的 DeepSeek 输出
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer


def extract_chapter_content(novel_file: Path, chapter_num: int):
    """提取指定章节内容"""
    with open(novel_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import re
    chapter_pattern = r'===\s*第\s*(\d+)\s*章\s*(.*)===\s*\n'
    matches = list(re.finditer(chapter_pattern, content))
    
    if len(matches) < chapter_num:
        return None, None
    
    start_match = matches[chapter_num - 1]
    chapter_number = int(start_match.group(1))
    chapter_title = start_match.group(2).strip()
    
    start_pos = start_match.end()
    end_pos = matches[chapter_num].start() if len(matches) > chapter_num else len(content)
    chapter_content = content[start_pos:end_pos].strip()
    
    return chapter_title, chapter_content


def main():
    """主测试流程"""
    print("\n" + "🎯" * 40)
    print("  Prompt 优化效果测试 - DeepSeek")
    print("🎯" * 40)
    print("\n📝 本次测试使用优化后的 prompt")
    print("📊 将与之前的稳定性测试结果对比\n")
    
    # 读取原始小说文件
    project_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路"
    novel_file = project_dir / "raw/novel.txt"
    
    chapter_title, chapter_content = extract_chapter_content(novel_file, 1)
    
    if not chapter_content:
        print("❌ 无法提取章节内容")
        return
    
    print(f"📖 章节: 第1章 - {chapter_title}")
    print(f"📝 内容长度: {len(chapter_content)} 字符\n")
    
    # 创建输出目录
    output_dir = project_dir / "novel/functional_analysis/prompt_optimization_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行3次测试
    print("="*80)
    print("  开始运行3次测试（优化后的 Prompt）")
    print("="*80)
    
    results = []
    for i in range(1, 4):
        print(f"\n{'─'*80}")
        print(f"  第 {i} 次运行（优化后）")
        print(f"{'─'*80}\n")
        
        # 创建分析器
        analyzer = NovelChapterAnalyzer()
        
        print("🔄 正在调用 DeepSeek...\n")
        
        try:
            # 执行分析
            result = analyzer.execute(
                chapter_content=chapter_content,
                chapter_number=1,
                chapter_title=chapter_title,
                novel_title="序列公路求生：我在末日升级物资"
            )
            
            # 保存Markdown
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            md_file = output_dir / f"optimized_run_{i}_{timestamp}.md"
            analyzer.save_markdown(result, md_file)
            
            # 提取段落1信息
            segment_1 = result.segments[0] if result.segments else None
            
            if segment_1:
                # 检查是否包含陈野反应
                has_chenye_reaction = "陈野" in segment_1.content
                has_convoy_emotion = "车队" in segment_1.content or "绝望" in segment_1.content
                
                print(f"✅ 分析完成！")
                print(f"\n【段落1 核心信息】")
                print(f"  标题: {segment_1.title}")
                print(f"  字数: {segment_1.metadata.word_count}")
                print(f"  包含陈野反应: {'✅' if has_chenye_reaction else '❌'}")
                print(f"  包含车队情绪: {'✅' if has_convoy_emotion else '❌'}")
                print(f"  优先级: {segment_1.tags.priority}")
                print(f"\n  内容预览:")
                preview = segment_1.content[:200]
                print(f"  {preview}...")
                
                # 判断是否正确
                is_correct = (
                    segment_1.metadata.word_count >= 150 and
                    has_chenye_reaction and
                    has_convoy_emotion
                )
                
                if is_correct:
                    print(f"\n  ✅ 判定：正确（包含完整情绪单元）")
                else:
                    print(f"\n  ❌ 判定：错误（缺少情绪单元）")
                    if segment_1.metadata.word_count < 150:
                        print(f"     原因：字数不足（{segment_1.metadata.word_count} < 150）")
                    if not has_chenye_reaction:
                        print(f"     原因：缺少陈野反应")
                    if not has_convoy_emotion:
                        print(f"     原因：缺少车队情绪")
                
                print(f"\n💾 已保存: {md_file.name}")
                
                results.append({
                    "run": i,
                    "timestamp": timestamp,
                    "title": segment_1.title,
                    "word_count": segment_1.metadata.word_count,
                    "has_chenye": has_chenye_reaction,
                    "has_convoy": has_convoy_emotion,
                    "is_correct": is_correct,
                    "total_segments": result.chapter_summary.total_segments
                })
            else:
                print("❌ 没有段落结果")
                
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            import traceback
            traceback.print_exc()
        
        if i < 3:
            print(f"\n⏳ 等待5秒...\n")
            import time
            time.sleep(5)
    
    # 生成对比报告
    print("\n" + "="*80)
    print("  📊 优化效果对比")
    print("="*80)
    
    if len(results) == 3:
        print(f"\n✅ 成功完成3次测试\n")
        
        # 统计正确率
        correct_count = sum(1 for r in results if r['is_correct'])
        accuracy = correct_count / 3 * 100
        
        print("### 📈 总体统计\n")
        print(f"✅ 正确次数: {correct_count}/3")
        print(f"📊 准确率: {accuracy:.1f}%")
        
        print("\n### 📋 详细结果\n")
        print("| 运行 | 标题 | 字数 | 陈野反应 | 车队情绪 | 判定 |")
        print("|-----|------|------|---------|---------|------|")
        for r in results:
            chenye_mark = "✅" if r['has_chenye'] else "❌"
            convoy_mark = "✅" if r['has_convoy'] else "❌"
            result_mark = "✅ 正确" if r['is_correct'] else "❌ 错误"
            print(f"| 第{r['run']}次 | {r['title'][:20]}... | {r['word_count']} | {chenye_mark} | {convoy_mark} | {result_mark} |")
        
        print("\n### 🔍 与优化前对比\n")
        print("**优化前**（之前的稳定性测试）：")
        print("  - 正确次数: 1/3")
        print("  - 准确率: 33.3%")
        print("  - 问题: 2次将广播和反应拆分")
        
        print(f"\n**优化后**（本次测试）：")
        print(f"  - 正确次数: {correct_count}/3")
        print(f"  - 准确率: {accuracy:.1f}%")
        
        improvement = accuracy - 33.3
        if improvement > 0:
            print(f"  - 📈 提升: +{improvement:.1f}%")
            if accuracy == 100:
                print(f"  - 🎉 完美！3次全部正确！")
            elif accuracy >= 66.7:
                print(f"  - ✅ 显著改善")
            else:
                print(f"  - 📊 有改善但仍不稳定")
        elif improvement == 0:
            print(f"  - ⚠️ 无明显改善")
        else:
            print(f"  - ⚠️ 反而下降了")
        
        # 保存报告
        report_file = output_dir / f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Prompt 优化效果报告\n\n")
            f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write("## 优化内容\n\n")
            f.write("1. 添加详细的「分段禁忌」说明（错误示例+正确示例）\n")
            f.write("2. 强化「黄金规则」（情绪连贯性 > 内容形式）\n")
            f.write("3. 提供正确的段落1示例（165字，包含完整情绪单元）\n")
            f.write("4. 添加分段决策流程图\n")
            f.write("5. 添加分段前自检清单\n")
            f.write("6. 添加输出前最后检查清单\n\n")
            f.write("---\n\n")
            f.write("## 测试结果\n\n")
            f.write(f"**正确率**: {accuracy:.1f}% ({correct_count}/3)\n\n")
            f.write("| 运行 | 字数 | 陈野反应 | 车队情绪 | 判定 |\n")
            f.write("|-----|------|---------|---------|------|\n")
            for r in results:
                chenye_mark = "✅" if r['has_chenye'] else "❌"
                convoy_mark = "✅" if r['has_convoy'] else "❌"
                result_mark = "✅" if r['is_correct'] else "❌"
                f.write(f"| 第{r['run']}次 | {r['word_count']} | {chenye_mark} | {convoy_mark} | {result_mark} |\n")
            
            f.write("\n## 对比分析\n\n")
            f.write(f"- **优化前准确率**: 33.3% (1/3)\n")
            f.write(f"- **优化后准确率**: {accuracy:.1f}% ({correct_count}/3)\n")
            f.write(f"- **提升幅度**: {improvement:+.1f}%\n\n")
            
            if accuracy == 100:
                f.write("## 结论\n\n")
                f.write("✅ **Prompt 优化非常成功！** DeepSeek 在新 prompt 下表现稳定，3次测试全部正确。\n\n")
                f.write("**建议**：可以使用优化后的 DeepSeek 进行批量分析。\n")
            elif accuracy >= 66.7:
                f.write("## 结论\n\n")
                f.write("✅ **Prompt 优化效果显著**，DeepSeek 的准确率有明显提升。\n\n")
                f.write("**建议**：可以谨慎使用，但建议添加后处理校验机制。\n")
            else:
                f.write("## 结论\n\n")
                f.write("⚠️ **Prompt 优化效果有限**，DeepSeek 仍不够稳定。\n\n")
                f.write("**建议**：考虑切换到 Claude API 或使用多次运行+投票机制。\n")
        
        print(f"\n📄 详细报告已保存: {report_file.name}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
