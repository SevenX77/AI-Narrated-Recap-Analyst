"""
Novel 处理脚本 - 最终简化版本

遵循用户要求：
1. 不生成冗余的单章文件（chpt_0001.md等）
2. 直接从 raw/novel.txt 读取并分析
3. 功能段分析已包含分段，无需额外步骤

流程：
Step 1: 数据摄入（手动）→ raw/novel.txt
Step 2: 简介提取 + LLM过滤 → chpt_0000_简介.md
Step 3: 功能段分析（R1模型）→ functional_analysis/
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_chapter_processor import MetadataExtractor
from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer
from src.core.artifact_manager import ArtifactManager


def main():
    """主流程"""
    print("="*80)
    print("Novel 处理脚本 - 最终简化版")
    print("="*80)
    
    # 配置路径
    project_root = Path(__file__).parent.parent
    project_dir = project_root / "data/projects/with_novel/末哥超凡公路"
    raw_novel = project_dir / "raw/novel.txt"
    novel_dir = project_dir / "novel"
    analysis_dir = novel_dir / "functional_analysis"
    
    # 确保目录存在
    novel_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "history").mkdir(exist_ok=True)
    
    # 读取原始小说
    print(f"\n📖 读取小说: {raw_novel}")
    with open(raw_novel, 'r', encoding='utf-8') as f:
        novel_text = f.read()
    
    print(f"   文件大小: {len(novel_text)} 字符")
    
    # ====================================
    # Step 1: 简介提取 + LLM过滤
    # ====================================
    print("\n" + "="*80)
    print("Step 1: 简介提取（使用 MetadataExtractor + LLM）")
    print("="*80)
    
    extractor = MetadataExtractor(use_llm=True)
    metadata = extractor.execute(novel_text)
    
    # 保存简介
    intro_file = novel_dir / "chpt_0000_简介.md"
    with open(intro_file, 'w', encoding='utf-8') as f:
        f.write(f"# {metadata['novel']['title']}\n\n")
        f.write("## 简介\n\n")
        f.write(metadata['novel']['introduction'])
    
    print(f"✅ 简介已保存: {intro_file.name}")
    print(f"   作者: {metadata['novel']['author']}")
    print(f"   标签: {', '.join(metadata['novel']['tags'])}")
    print(f"   简介长度: {len(metadata['novel']['introduction'])} 字符")
    
    # ====================================
    # Step 2: 识别章节（不生成单章文件）
    # ====================================
    print("\n" + "="*80)
    print("Step 2: 识别章节边界")
    print("="*80)
    
    chapter_pattern = r'===\s*第\s*(\d+)\s*章\s*(.*)===\s*\n'
    matches = list(re.finditer(chapter_pattern, novel_text))
    
    print(f"✅ 识别到 {len(matches)} 个章节")
    
    # ====================================
    # Step 3: 逐章功能段分析（R1模型）
    # ====================================
    print("\n" + "="*80)
    print("Step 3: 功能段分析（使用 NovelChapterAnalyzer + DeepSeek R1）")
    print("="*80)
    
    analyzer = NovelChapterAnalyzer()
    
    for i, match in enumerate(matches[:10]):  # 只处理前10章
        chapter_number = int(match.group(1))
        chapter_title = match.group(2).strip()
        
        # 提取章节内容
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(novel_text)
        chapter_content = novel_text[start_pos:end_pos].strip()
        
        print(f"\n--- 分析 第{chapter_number}章: {chapter_title} ---")
        print(f"   字数: {len(chapter_content)}")
        
        try:
            # 功能段分析
            analysis = analyzer.execute(
                chapter_content=chapter_content,
                chapter_number=chapter_number,
                chapter_title=chapter_title
            )
            
            # 转换为字典（处理datetime）
            analysis_dict = analysis.model_dump(mode='json')
            
            # 保存JSON（使用ArtifactManager）
            artifact_type = f"chpt_{chapter_number:04d}_functional_analysis"
            versioned_path = ArtifactManager.save_artifact(
                content=analysis_dict,
                artifact_type=artifact_type,
                project_id="末哥超凡公路",
                base_dir=str(analysis_dir),
                extension="json"
            )
            
            print(f"✅ 第{chapter_number}章分析完成:")
            print(f"   功能段数: {len(analysis_dict['segments'])}")
            print(f"   P0段落: {analysis_dict['chapter_summary']['p0_count']}")
            print(f"   P1段落: {analysis_dict['chapter_summary']['p1_count']}")
            print(f"   P2段落: {analysis_dict['chapter_summary']['p2_count']}")
            print(f"   已保存: {Path(versioned_path).name}")
            
            # 同时保存 Markdown 版本（人类阅读）- 输出到 novel/ 目录
            md_content = _format_analysis_to_markdown(analysis_dict)
            md_file = novel_dir / f"第{chapter_number}章完整分段分析.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"   Markdown: {md_file.name}")
            
        except Exception as e:
            print(f"❌ 第{chapter_number}章分析失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "="*80)
    print("✅ 所有处理完成！")
    print("="*80)
    print(f"\n📂 输出目录:")
    print(f"   简介: {intro_file}")
    print(f"   JSON分析: {analysis_dir}/chpt_XXXX_functional_analysis_latest.json")
    print(f"   Markdown: {novel_dir}/第X章完整分段分析.md")
    print(f"   历史版本: {analysis_dir}/history/")
    print(f"\n⚠️  注意: 不再生成单章文件（chpt_0001.md等），直接输出功能段分析")


def _format_analysis_to_markdown(analysis: dict) -> str:
    """将分析结果格式化为Markdown"""
    lines = []
    
    lines.append(f"# 第{analysis['chapter_number']}章 - {analysis['chapter_title']}")
    lines.append("")
    lines.append(f"**功能段数**: {analysis['chapter_summary']['total_segments']}")
    lines.append(f"**P0段落**: {analysis['chapter_summary']['p0_count']}")
    lines.append(f"**P1段落**: {analysis['chapter_summary']['p1_count']}")
    lines.append(f"**P2段落**: {analysis['chapter_summary']['p2_count']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for seg in analysis['segments']:
        lines.append(f"## {seg['title']}")
        lines.append("")
        lines.append(f"**ID**: `{seg['segment_id']}`")
        lines.append("")
        
        # 标签
        tags = seg['tags']
        if tags['narrative_function']:
            lines.append(f"**叙事功能**: {', '.join(tags['narrative_function'])}")
        if tags['structure']:
            lines.append(f"**叙事结构**: {', '.join(tags['structure'])}")
        if tags['character']:
            lines.append(f"**角色关系**: {', '.join(tags['character'])}")
        lines.append(f"**优先级**: {tags['priority']}")
        if tags.get('location'):
            lines.append(f"**地点**: {tags['location']}")
        if tags.get('time'):
            lines.append(f"**时间**: {tags['time']}")
        lines.append("")
        
        # 内容
        lines.append("### 📄 内容")
        lines.append("")
        lines.append(seg['content'])
        lines.append("")
        
        # 浓缩建议
        if seg.get('condensation_suggestion'):
            lines.append("### 💡 浓缩建议")
            lines.append("")
            lines.append(seg['condensation_suggestion'])
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    main()
