"""
批量重新生成章节分段Markdown - 第2-10章

遵循 .cursorrules 强制检查：
✅ Step 1: 找到 NovelChapterAnalyzer, ArtifactManager in docs
✅ Step 2: 找到工具文件
✅ Step 3: 正确调用工具，不重复实现
"""

import sys
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.artifact_manager import ArtifactManager


def format_analysis_to_markdown(analysis: dict) -> str:
    """将分析结果格式化为Markdown（用于人类阅读）"""
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
        seg_id = seg['segment_id']
        lines.append(f"## {seg['title']}")
        lines.append("")
        lines.append(f"**ID**: `{seg_id}`")
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
    
    # 章节级摘要
    if analysis.get('chapter_summary'):
        summary = analysis['chapter_summary']
        lines.append("## 📊 章节摘要")
        lines.append("")
        
        if summary.get('key_events'):
            lines.append("### 关键事件")
            lines.append("")
            for event in summary['key_events']:
                lines.append(f"- {event}")
            lines.append("")
        
        if summary.get('foreshadowing_planted'):
            lines.append("### 埋设伏笔")
            lines.append("")
            for f in summary['foreshadowing_planted']:
                lines.append(f"- {f}")
            lines.append("")
        
        if summary.get('foreshadowing_paid_off'):
            lines.append("### 回应伏笔")
            lines.append("")
            for f in summary['foreshadowing_paid_off']:
                lines.append(f"- {f}")
            lines.append("")
    
    # 结构洞察
    if analysis.get('structure_insight'):
        insight = analysis['structure_insight']
        lines.append("## 🔍 结构洞察")
        lines.append("")
        lines.append(f"**叙事节奏**: {insight.get('narrative_rhythm', 'N/A')}")
        lines.append(f"**情感曲线**: {insight.get('emotional_arc', 'N/A')}")
        lines.append("")
        
        if insight.get('turning_points'):
            lines.append("### 转折点")
            lines.append("")
            for tp in insight['turning_points']:
                lines.append(f"- {tp}")
            lines.append("")
    
    return "\n".join(lines)


def main():
    """批量重新生成第2-10章的Markdown分段"""
    print("="*80)
    print("批量重新生成章节分段Markdown（第2-10章）")
    print("="*80)
    
    # 配置路径
    project_root = Path(__file__).parent.parent
    project_dir = project_root / "data/projects/with_novel/末哥超凡公路"
    analysis_dir = project_dir / "novel/functional_analysis"
    
    # 处理第2-10章
    for chapter_num in range(2, 11):
        print(f"\n{'='*80}")
        print(f"处理第{chapter_num}章")
        print(f"{'='*80}")
        
        # 读取JSON分析结果
        artifact_type = f"chpt_{chapter_num:04d}_functional_analysis"
        latest_json = ArtifactManager.load_latest_artifact(
            artifact_type=artifact_type,
            base_dir=str(analysis_dir),
            extension="json"
        )
        
        if not latest_json:
            print(f"⚠️  第{chapter_num}章JSON不存在，跳过")
            continue
        
        print(f"✅ 已读取JSON分析: {artifact_type}_latest.json")
        print(f"   功能段数: {latest_json['chapter_summary']['total_segments']}")
        
        # 生成Markdown
        md_content = format_analysis_to_markdown(latest_json)
        md_file = analysis_dir / f"第{chapter_num}章完整分段分析.md"
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✅ 已生成Markdown: {md_file.name}")
    
    print("\n" + "="*80)
    print("✅ 批量生成完成！")
    print("="*80)
    print("\n生成的文件:")
    for chapter_num in range(2, 11):
        md_file = analysis_dir / f"第{chapter_num}章完整分段分析.md"
        if md_file.exists():
            print(f"  ✅ {md_file.name}")
        else:
            print(f"  ❌ {md_file.name} (不存在)")


if __name__ == "__main__":
    main()
