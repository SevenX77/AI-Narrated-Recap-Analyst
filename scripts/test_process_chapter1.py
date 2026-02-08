"""
测试脚本：只处理第1章
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_chapter_processor import MetadataExtractor
from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer
from src.core.artifact_manager import ArtifactManager


def main():
    """只处理第1章"""
    print("="*80)
    print("测试：处理第1章")
    print("="*80)
    
    # 配置路径
    project_root = Path(__file__).parent.parent
    project_dir = project_root / "data/projects/with_novel/末哥超凡公路"
    raw_novel = project_dir / "raw/novel.txt"
    novel_dir = project_dir / "novel"
    analysis_dir = novel_dir / "functional_analysis"
    
    # 读取原始小说
    print(f"\n📖 读取小说: {raw_novel}")
    with open(raw_novel, 'r', encoding='utf-8') as f:
        novel_text = f.read()
    
    print(f"   文件大小: {len(novel_text)} 字符")
    
    # 识别章节
    print("\n识别章节...")
    chapter_pattern = r'===\s*第\s*(\d+)\s*章\s*(.*)===\s*\n'
    matches = list(re.finditer(chapter_pattern, novel_text))
    print(f"✅ 识别到 {len(matches)} 个章节")
    
    # 只处理第1章
    match = matches[0]
    chapter_number = int(match.group(1))
    chapter_title = match.group(2).strip()
    
    # 提取章节内容
    start_pos = match.end()
    end_pos = matches[1].start()
    chapter_content = novel_text[start_pos:end_pos].strip()
    
    print(f"\n--- 分析 第{chapter_number}章: {chapter_title} ---")
    print(f"   字数: {len(chapter_content)}")
    
    # 功能段分析
    print("\n开始分析...")
    analyzer = NovelChapterAnalyzer()
    analysis = analyzer.execute(
        chapter_content=chapter_content,
        chapter_number=chapter_number,
        chapter_title=chapter_title
    )
    
    # 转换为字典
    analysis_dict = analysis.model_dump(mode='json')
    
    print(f"\n✅ 分析完成:")
    print(f"   功能段数: {len(analysis_dict['segments'])}")
    print(f"   P0段落: {analysis_dict['chapter_summary']['p0_count']}")
    print(f"   P1段落: {analysis_dict['chapter_summary']['p1_count']}")
    print(f"   P2段落: {analysis_dict['chapter_summary']['p2_count']}")
    
    # 显示前2个段落
    print("\n前2个功能段:")
    for i, seg in enumerate(analysis_dict['segments'][:2]):
        print(f"\n{i+1}. {seg['title']}")
        print(f"   ID: {seg['segment_id']}")
        print(f"   优先级: {seg['tags']['priority']}")
        print(f"   字数: {len(seg['content'])}")
        print(f"   内容预览: {seg['content'][:100]}...")
    
    # 保存JSON
    artifact_type = f"chpt_{chapter_number:04d}_functional_analysis"
    versioned_path = ArtifactManager.save_artifact(
        content=analysis_dict,
        artifact_type=artifact_type,
        project_id="末哥超凡公路",
        base_dir=str(analysis_dir),
        extension="json"
    )
    
    print(f"\n✅ 已保存: {Path(versioned_path).name}")
    
    # 保存 Markdown - 输出到 novel/ 目录
    md_content = _format_analysis_to_markdown(analysis_dict)
    md_file = novel_dir / f"第{chapter_number}章完整分段分析.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"   Markdown: {md_file.name}")
    
    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("="*80)


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
