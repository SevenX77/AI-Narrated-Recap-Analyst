"""
测试 DeepSeek 稳定性 - 连续运行3次并记录结果
"""

import sys
import shutil
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


def run_single_test(run_num: int, output_dir: Path):
    """运行单次测试"""
    print(f"\n{'='*80}")
    print(f"  第 {run_num} 次运行")
    print(f"{'='*80}\n")
    
    # 读取原始小说文件
    project_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路"
    novel_file = project_dir / "raw/novel.txt"
    
    chapter_title, chapter_content = extract_chapter_content(novel_file, 1)
    
    if not chapter_content:
        print("❌ 无法提取章节内容")
        return None
    
    print(f"📖 章节: 第1章 - {chapter_title}")
    print(f"📝 内容长度: {len(chapter_content)} 字符\n")
    
    # 创建分析器
    analyzer = NovelChapterAnalyzer()
    
    print("🔄 正在调用 DeepSeek 进行分析...\n")
    
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
        md_file = output_dir / f"run_{run_num}_{timestamp}.md"
        analyzer.save_markdown(result, md_file)
        
        # 提取段落1信息
        segment_1 = result.segments[0] if result.segments else None
        
        if segment_1:
            print(f"✅ 分析完成！")
            print(f"📊 功能段总数: {result.chapter_summary.total_segments}")
            print(f"\n【段落1】")
            print(f"  标题: {segment_1.title}")
            print(f"  字数: {segment_1.metadata.word_count}")
            print(f"  内容预览: {segment_1.content[:100]}...")
            print(f"  优先级: {segment_1.tags.priority}")
            print(f"\n💾 已保存到: {md_file}")
            
            return {
                "run_num": run_num,
                "timestamp": timestamp,
                "file": md_file,
                "segment_1_title": segment_1.title,
                "segment_1_word_count": segment_1.metadata.word_count,
                "segment_1_content_preview": segment_1.content[:200],
                "total_segments": result.chapter_summary.total_segments,
                "p0_count": result.chapter_summary.p0_count,
                "p1_count": result.chapter_summary.p1_count,
                "p2_count": result.chapter_summary.p2_count
            }
        else:
            print("❌ 没有段落结果")
            return None
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主测试流程"""
    print("\n" + "🔬" * 40)
    print("  DeepSeek 稳定性测试 - 连续运行3次")
    print("🔬" * 40)
    
    # 创建输出目录
    output_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路/novel/functional_analysis/stability_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行3次测试
    results = []
    for i in range(1, 4):
        result = run_single_test(i, output_dir)
        if result:
            results.append(result)
        
        if i < 3:
            print(f"\n⏳ 等待5秒后进行下一次测试...\n")
            import time
            time.sleep(5)
    
    # 生成对比报告
    print("\n" + "="*80)
    print("  📊 对比报告")
    print("="*80)
    
    if len(results) == 3:
        print(f"\n✅ 成功完成3次测试\n")
        
        # 对比段落1
        print("### 段落1对比\n")
        for r in results:
            print(f"**第{r['run_num']}次运行** ({r['timestamp']}):")
            print(f"  - 标题: {r['segment_1_title']}")
            print(f"  - 字数: {r['segment_1_word_count']}")
            print(f"  - 内容: {r['segment_1_content_preview']}...")
            print()
        
        # 对比总体统计
        print("### 总体统计对比\n")
        print("| 运行次数 | 功能段总数 | P0 | P1 | P2 |")
        print("|---------|----------|----|----|----| ")
        for r in results:
            print(f"| 第{r['run_num']}次 | {r['total_segments']} | {r['p0_count']} | {r['p1_count']} | {r['p2_count']} |")
        
        # 判断一致性
        titles = [r['segment_1_title'] for r in results]
        word_counts = [r['segment_1_word_count'] for r in results]
        
        print(f"\n### 一致性分析\n")
        if len(set(titles)) == 1:
            print("✅ **段落1标题完全一致**")
        else:
            print("⚠️ **段落1标题不一致：**")
            for t in set(titles):
                count = titles.count(t)
                print(f"  - '{t}': {count}次")
        
        if len(set(word_counts)) == 1:
            print("✅ **段落1字数完全一致**")
        else:
            print("⚠️ **段落1字数不一致：**")
            for w in set(word_counts):
                count = word_counts.count(w)
                print(f"  - {w}字: {count}次")
        
        # 保存对比报告
        report_file = output_dir / f"stability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# DeepSeek 稳定性测试报告\n\n")
            f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write("## 段落1对比\n\n")
            for r in results:
                f.write(f"### 第{r['run_num']}次运行 ({r['timestamp']})\n\n")
                f.write(f"- **标题**: {r['segment_1_title']}\n")
                f.write(f"- **字数**: {r['segment_1_word_count']}\n")
                f.write(f"- **内容预览**: {r['segment_1_content_preview']}...\n")
                f.write(f"- **文件**: {r['file'].name}\n\n")
            
            f.write("## 总体统计\n\n")
            f.write("| 运行次数 | 功能段总数 | P0 | P1 | P2 |\n")
            f.write("|---------|----------|----|----|----|\n")
            for r in results:
                f.write(f"| 第{r['run_num']}次 | {r['total_segments']} | {r['p0_count']} | {r['p1_count']} | {r['p2_count']} |\n")
            
            f.write("\n## 结论\n\n")
            if len(set(titles)) == 1 and len(set(word_counts)) == 1:
                f.write("✅ **结果完全一致** - DeepSeek在此次测试中表现稳定\n")
            else:
                f.write("⚠️ **结果不一致** - DeepSeek存在随机性，不适合用于生产环境\n")
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
    else:
        print(f"\n⚠️ 只完成了{len(results)}次测试")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
