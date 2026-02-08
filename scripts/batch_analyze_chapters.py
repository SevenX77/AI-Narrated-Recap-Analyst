"""
批量分析章节 - 使用优化后的 Prompt
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer


def extract_all_chapters(novel_file: Path):
    """提取所有章节"""
    with open(novel_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import re
    chapter_pattern = r'===\s*第\s*(\d+)\s*章\s*(.*)===\s*\n'
    matches = list(re.finditer(chapter_pattern, content))
    
    chapters = []
    for i, match in enumerate(matches):
        chapter_number = int(match.group(1))
        chapter_title = match.group(2).strip()
        
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        chapter_content = content[start_pos:end_pos].strip()
        
        chapters.append({
            'number': chapter_number,
            'title': chapter_title,
            'content': chapter_content
        })
    
    return chapters


def main():
    """批量分析章节"""
    print("\n" + "📚" * 40)
    print("  批量章节分析 - 优化后的 Prompt")
    print("📚" * 40)
    print("\n⚙️ 配置：DeepSeek + 优化后的 Prompt")
    print("📊 目标：第1-10章功能段分析\n")
    
    # 读取原始小说文件
    project_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路"
    novel_file = project_dir / "raw/novel.txt"
    output_dir = project_dir / "novel/functional_analysis"
    
    print(f"📖 读取小说文件: {novel_file.name}")
    chapters = extract_all_chapters(novel_file)
    
    # 只分析前10章
    chapters_to_analyze = [c for c in chapters if 1 <= c['number'] <= 10]
    
    print(f"✅ 成功提取 {len(chapters)} 章")
    print(f"🎯 本次分析：第1-10章（共 {len(chapters_to_analyze)} 章）\n")
    
    # 询问用户是否继续
    print("="*80)
    print("  开始批量分析")
    print("="*80)
    
    # 创建分析器
    analyzer = NovelChapterAnalyzer()
    
    results_summary = []
    
    for i, chapter in enumerate(chapters_to_analyze, 1):
        print(f"\n{'─'*80}")
        print(f"  [{i}/{len(chapters_to_analyze)}] 第{chapter['number']}章 - {chapter['title']}")
        print(f"{'─'*80}\n")
        
        print(f"📝 内容长度: {len(chapter['content'])} 字符")
        print(f"🔄 正在分析...\n")
        
        try:
            # 执行分析
            result = analyzer.execute(
                chapter_content=chapter['content'],
                chapter_number=chapter['number'],
                chapter_title=chapter['title'],
                novel_title="序列公路求生：我在末日升级物资"
            )
            
            # 保存文件
            # Markdown
            md_file = output_dir / f"第{chapter['number']}章完整分段分析.md"
            analyzer.save_markdown(result, md_file)
            
            # JSON
            json_file = output_dir / f"chpt_{chapter['number']:04d}_functional_analysis.json"
            analyzer.save_json(result, json_file)
            
            # 统计信息
            segment_1 = result.segments[0] if result.segments else None
            summary = {
                'chapter': chapter['number'],
                'title': chapter['title'],
                'total_segments': result.chapter_summary.total_segments,
                'p0_count': result.chapter_summary.p0_count,
                'p1_count': result.chapter_summary.p1_count,
                'p2_count': result.chapter_summary.p2_count,
                'segment_1_word_count': segment_1.metadata.word_count if segment_1 else 0,
                'md_file': md_file.name,
                'json_file': json_file.name
            }
            
            results_summary.append(summary)
            
            print(f"✅ 分析完成！")
            print(f"\n📊 统计：")
            print(f"  - 功能段总数: {result.chapter_summary.total_segments}")
            print(f"  - P0-骨架: {result.chapter_summary.p0_count}")
            print(f"  - P1-血肉: {result.chapter_summary.p1_count}")
            print(f"  - P2-皮肤: {result.chapter_summary.p2_count}")
            if segment_1:
                print(f"  - 段落1字数: {segment_1.metadata.word_count}")
            print(f"\n💾 已保存:")
            print(f"  - {md_file.name}")
            print(f"  - {json_file.name}")
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            import traceback
            traceback.print_exc()
            results_summary.append({
                'chapter': chapter['number'],
                'title': chapter['title'],
                'error': str(e)
            })
        
        # 进度提示
        if i < len(chapters_to_analyze):
            print(f"\n⏳ 等待3秒后继续...")
            import time
            time.sleep(3)
    
    # 生成总结报告
    print("\n" + "="*80)
    print("  📊 批量分析完成")
    print("="*80)
    
    success_count = len([r for r in results_summary if 'error' not in r])
    
    print(f"\n✅ 成功: {success_count}/{len(chapters_to_analyze)}")
    
    if success_count > 0:
        print(f"\n### 📋 章节统计\n")
        print("| 章节 | 标题 | 功能段 | P0 | P1 | P2 | 段落1字数 |")
        print("|-----|------|--------|----|----|----|---------| ")
        for r in results_summary:
            if 'error' not in r:
                print(f"| 第{r['chapter']}章 | {r['title'][:10]}... | {r['total_segments']} | {r['p0_count']} | {r['p1_count']} | {r['p2_count']} | {r['segment_1_word_count']} |")
    
    # 保存汇总报告
    report_file = output_dir / f"batch_analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_chapters': len(chapters_to_analyze),
            'success_count': success_count,
            'results': results_summary
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告: {report_file.name}")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
