"""
Novel 处理脚本 V3 - 重新设计的处理流程

新流程:
1. 拆分简介 (chpt_0000.md → chpt_0000_简介.md)
2. 拆分章节 (raw/novel.txt → chpt_XXXX.md 单章)
3. 功能分析 (使用 R1/V3 → chpt_XXXX_functional_analysis.json)
4. 版本管理 (_latest.json 指针 + 时间戳版本)
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer


def extract_introduction(novel_file: Path) -> str:
    """提取简介部分"""
    with open(novel_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取第一个===之前的内容作为简介
    first_chapter = re.search(r'===\s*第\s*\d+\s*章', content)
    if first_chapter:
        intro = content[:first_chapter.start()].strip()
        return intro
    return ""


def extract_all_chapters(novel_file: Path) -> List[Dict]:
    """提取所有章节"""
    with open(novel_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
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
            'content': chapter_content,
            'word_count': len(chapter_content)
        })
    
    return chapters


def save_introduction(intro: str, output_dir: Path):
    """保存简介"""
    intro_file = output_dir / "chpt_0000_简介.md"
    with open(intro_file, 'w', encoding='utf-8') as f:
        f.write("# 序列公路求生：我在末日升级物资\n\n")
        f.write("## 简介\n\n")
        f.write(intro)
    print(f"✅ 简介已保存: {intro_file.name}")


def save_chapter_markdown(chapter: Dict, output_dir: Path):
    """保存单章分段markdown"""
    chapter_file = output_dir / f"chpt_{chapter['number']:04d}.md"
    
    with open(chapter_file, 'w', encoding='utf-8') as f:
        f.write(f"# 第{chapter['number']}章 - {chapter['title']}\n\n")
        f.write(f"> **字数**: {chapter['word_count']}\n\n")
        f.write("---\n\n")
        f.write(chapter['content'])
    
    print(f"✅ 章节已保存: {chapter_file.name} ({chapter['word_count']}字)")


def save_functional_analysis_with_version(
    analysis,
    chapter_number: int,
    output_dir: Path
) -> Tuple[Path, Path]:
    """
    保存功能分析结果（版本化）
    
    Returns:
        Tuple[versioned_file, latest_file]
    """
    # 时间戳版本
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_file = output_dir / f"chpt_{chapter_number:04d}_functional_analysis_v{timestamp}.json"
    
    # _latest 指针
    latest_file = output_dir / f"chpt_{chapter_number:04d}_functional_analysis_latest.json"
    
    # 保存时间戳版本
    with open(versioned_file, 'w', encoding='utf-8') as f:
        json.dump(analysis.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
    
    # 更新 _latest 指针
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(analysis.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
    
    return versioned_file, latest_file


def main():
    """主处理流程"""
    print("\n" + "📚" * 40)
    print("  Novel 处理 V3 - 重新设计的流程")
    print("📚" * 40)
    print("\n📋 流程:")
    print("  1. 拆分简介")
    print("  2. 拆分章节 (单章md)")
    print("  3. 功能分析 (R1/V3 + fallback)")
    print("  4. 版本管理 (_latest.json + 时间戳)\n")
    
    # 路径设置
    project_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路"
    novel_file = project_dir / "raw/novel.txt"
    novel_dir = project_dir / "novel"
    analysis_dir = novel_dir / "functional_analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: 提取并保存简介
    print("="*80)
    print("  Step 1: 提取简介")
    print("="*80)
    intro = extract_introduction(novel_file)
    if intro:
        save_introduction(intro, novel_dir)
    else:
        print("⚠️ 未找到简介")
    
    # Step 2: 提取所有章节
    print("\n" + "="*80)
    print("  Step 2: 提取章节")
    print("="*80)
    chapters = extract_all_chapters(novel_file)
    print(f"✅ 成功提取 {len(chapters)} 章\n")
    
    # Step 3: 保存单章markdown
    print("="*80)
    print("  Step 3: 保存单章 Markdown")
    print("="*80)
    for chapter in chapters[:10]:  # 先处理前10章
        save_chapter_markdown(chapter, novel_dir)
    
    # Step 4: 功能分析（使用 R1/V3 + fallback）
    print("\n" + "="*80)
    print("  Step 4: 功能分析 (R1/V3 + Fallback)")
    print("="*80)
    print("⚙️ 配置: 主模型=V3, Fallback模型=R1")
    print("🔍 Fallback触发条件:")
    print("  - V3 API错误")
    print("  - 段落1字数 < 120 (只有广播没有反应)")
    print("  - 段落1字数 > 400 (过度聚合)\n")
    
    analyzer = NovelChapterAnalyzer()
    
    success_count = 0
    failed_chapters = []
    
    for i, chapter in enumerate(chapters[:10], 1):  # 先处理前10章
        print(f"\n{'─'*80}")
        print(f"  [{i}/10] 第{chapter['number']}章 - {chapter['title']}")
        print(f"{'─'*80}\n")
        
        try:
            # 执行分析
            result = analyzer.execute(
                chapter_content=chapter['content'],
                chapter_number=chapter['number'],
                chapter_title=chapter['title'],
                novel_title="序列公路求生：我在末日升级物资"
            )
            
            # 版本化保存
            versioned_file, latest_file = save_functional_analysis_with_version(
                result,
                chapter['number'],
                analysis_dir
            )
            
            # 统计信息
            seg_1 = result.segments[0] if result.segments else None
            
            print(f"✅ 分析完成")
            print(f"  - 功能段: {result.chapter_summary.total_segments}")
            print(f"  - P0: {result.chapter_summary.p0_count}")
            print(f"  - P1: {result.chapter_summary.p1_count}")
            print(f"  - P2: {result.chapter_summary.p2_count}")
            if seg_1:
                print(f"  - 段落1字数: {seg_1.metadata.word_count}")
            print(f"\n💾 已保存:")
            print(f"  - {versioned_file.name}")
            print(f"  - {latest_file.name}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            failed_chapters.append(chapter['number'])
            import traceback
            traceback.print_exc()
        
        # 进度提示
        if i < 10:
            print(f"\n⏳ 等待3秒...")
            import time
            time.sleep(3)
    
    # 生成处理报告
    print("\n" + "="*80)
    print("  📊 处理完成")
    print("="*80)
    
    print(f"\n✅ 成功: {success_count}/10")
    if failed_chapters:
        print(f"❌ 失败章节: {failed_chapters}")
    
    # 保存汇总报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_chapters": len(chapters),
        "processed_chapters": 10,
        "success_count": success_count,
        "failed_chapters": failed_chapters,
        "version": "v3",
        "model_config": {
            "primary_model": "deepseek-chat",
            "fallback_model": "deepseek-reasoner",
            "enable_fallback": True
        }
    }
    
    report_file = analysis_dir / f"processing_report_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 处理报告: {report_file.name}")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
