"""
Novel 处理脚本 V3 - 重构版本（使用现有工具）

遵循 .cursorrules 强制检查：
✅ Step 1: 找到 MetadataExtractor, NovelChapterProcessor, ArtifactManager
✅ Step 2: 找到工具文件路径
✅ Step 3: 正确调用现有工具，不重复实现

新流程:
1. 使用 MetadataExtractor 提取并过滤简介（LLM清理）
2. 使用 NovelChapterProcessor 拆分章节
3. 使用 NovelChapterAnalyzer 进行功能分析（R1模型）
4. 使用 ArtifactManager 管理版本
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_chapter_processor import MetadataExtractor, NovelChapterProcessor
from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer
from src.core.artifact_manager import ArtifactManager
from src.core.config import LLMConfig


def main():
    """主流程"""
    print("="*80)
    print("Novel 处理脚本 V3 - 重构版本")
    print("="*80)
    
    # 配置路径
    project_root = Path(__file__).parent.parent
    project_dir = project_root / "data/projects/with_novel/末哥超凡公路"
    raw_novel = project_dir / "raw/novel.txt"
    novel_dir = project_dir / "novel"
    analysis_dir = novel_dir / "functional_analysis"
    
    # 确保目录存在
    novel_dir.mkdir(exist_ok=True)
    analysis_dir.mkdir(exist_ok=True)
    
    # 读取原始小说
    print(f"\n📖 读取小说: {raw_novel}")
    with open(raw_novel, 'r', encoding='utf-8') as f:
        novel_text = f.read()
    
    # ====================================
    # Step 1: 使用 MetadataExtractor 提取简介（LLM过滤）
    # ====================================
    print("\n" + "="*80)
    print("Step 1: 提取并过滤简介（使用 MetadataExtractor + LLM）")
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
    # Step 2: 使用 NovelChapterProcessor 拆分章节
    # ====================================
    print("\n" + "="*80)
    print("Step 2: 拆分章节（使用 NovelChapterProcessor）")
    print("="*80)
    
    processor = NovelChapterProcessor(chapters_per_file=1)  # 每章一个文件
    result = processor.execute(
        novel_text=novel_text,
        output_dir=novel_dir,
        introduction_override=metadata['novel']['introduction']  # 使用已过滤的简介
    )
    
    print(f"✅ 章节拆分完成:")
    print(f"   总章节数: {result['total_chapters']}")
    print(f"   生成文件: {len(result['chapter_files'])} 个")
    
    # ====================================
    # Step 3: 使用 NovelChapterAnalyzer 进行功能分析（R1模型）
    # ====================================
    print("\n" + "="*80)
    print("Step 3: 功能分析（使用 NovelChapterAnalyzer + DeepSeek R1）")
    print("="*80)
    
    # 强制使用 R1 模型（阅读理解任务）
    llm_config = LLMConfig()
    analyzer = NovelChapterAnalyzer(
        model=llm_config.fallback_model,  # 使用 R1 模型
        enable_fallback=False  # R1已经是最强模型，不需要fallback
    )
    
    # 分析所有章节
    for i in range(1, result['total_chapters'] + 1):
        chapter_file = novel_dir / f"chpt_{i:04d}.md"
        
        if not chapter_file.exists():
            print(f"⚠️  跳过 第{i}章 (文件不存在)")
            continue
        
        print(f"\n--- 分析 第{i}章 ---")
        
        with open(chapter_file, 'r', encoding='utf-8') as f:
            chapter_content = f.read()
        
        try:
            # 执行功能分析
            analysis = analyzer.execute(chapter_content, chapter_id=i)
            
            # ====================================
            # Step 4: 使用 ArtifactManager 保存版本化结果
            # ====================================
            artifact_type = f"chpt_{i:04d}_functional_analysis"
            versioned_path = ArtifactManager.save_artifact(
                content=analysis,
                artifact_type=artifact_type,
                project_id="末哥超凡公路",
                base_dir=str(analysis_dir),
                extension="json"
            )
            
            print(f"✅ 第{i}章分析完成:")
            print(f"   功能段数: {analysis['segment_count']}")
            print(f"   已保存: {Path(versioned_path).name}")
            print(f"   Latest指针: {artifact_type}_latest.json")
            
            # 同时保存 Markdown 版本（用于人类阅读）
            md_content = _format_analysis_to_markdown(analysis)
            md_file = analysis_dir / f"第{i}章完整分段分析.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"   Markdown: {md_file.name}")
            
        except Exception as e:
            print(f"❌ 第{i}章分析失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "="*80)
    print("✅ 所有处理完成！")
    print("="*80)
    print(f"\n📂 输出目录:")
    print(f"   简介: {intro_file}")
    print(f"   章节: {novel_dir}/chpt_XXXX.md")
    print(f"   分析: {analysis_dir}/chpt_XXXX_functional_analysis_latest.json")
    print(f"   历史版本: {analysis_dir}/history/")


def _format_analysis_to_markdown(analysis: Dict) -> str:
    """将分析结果格式化为Markdown（用于人类阅读）"""
    lines = []
    
    lines.append(f"# 第{analysis['chapter_id']}章 - {analysis['chapter_title']}")
    lines.append("")
    lines.append(f"**功能段数**: {analysis['segment_count']}")
    lines.append(f"**总字数**: {analysis['total_chars']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for seg in analysis['segments']:
        seg_id = seg['segment_id']
        lines.append(f"## {seg_id}")
        lines.append("")
        lines.append(f"**功能**: {seg['metadata']['narrative_function']}")
        lines.append(f"**优先级**: {seg['metadata']['condensation_priority']}")
        lines.append("")
        
        # 标签
        if seg['metadata']['tags']:
            lines.append(f"**标签**: {' '.join(seg['metadata']['tags'])}")
            lines.append("")
        
        # 内容
        lines.append("### 内容")
        lines.append("")
        lines.append(seg['content'])
        lines.append("")
        
        # 分析
        lines.append("### 分析")
        lines.append("")
        lines.append(seg['metadata']['analysis'])
        lines.append("")
        
        # 浓缩建议
        if seg['metadata']['condensation_suggestion']:
            lines.append("### 浓缩建议")
            lines.append("")
            lines.append(seg['metadata']['condensation_suggestion'])
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # 章节级洞察
    if analysis.get('chapter_insights'):
        lines.append("## 📊 章节洞察")
        lines.append("")
        for key, value in analysis['chapter_insights'].items():
            lines.append(f"**{key}**: {value}")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    main()
