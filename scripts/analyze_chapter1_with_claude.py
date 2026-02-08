#!/usr/bin/env python3
"""
使用 Claude Sonnet 4.5 Thinking 分析第一章
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import config
from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer
from src.core.artifact_manager import ArtifactManager

def main():
    print("\n" + "="*80)
    print("🤖 使用 Claude Sonnet 4.5 Thinking 分析第一章")
    print("="*80)
    
    # 1. 检查配置
    print(f"\n📋 当前配置:")
    print(f"   LLM Provider: {config.llm.provider}")
    print(f"   Model: {config.llm.model_name}")
    print(f"   Base URL: {config.llm.base_url}")
    
    if config.llm.provider != "claude":
        print(f"\n❌ 错误: 当前 LLM_PROVIDER = '{config.llm.provider}'")
        print(f"   请在 .env 中设置: LLM_PROVIDER=claude")
        print(f"\n💡 提示:")
        print(f"   1. 打开 .env 文件")
        print(f"   2. 添加或修改: LLM_PROVIDER=claude")
        print(f"   3. 确保 CLAUDE_API_KEY 已配置")
        print(f"   4. 重新运行此脚本")
        return
    
    # 2. 读取第一章内容
    novel_dir = project_root / "data/projects/with_novel/末哥超凡公路"
    raw_novel_path = novel_dir / "raw/novel.txt"
    
    if not raw_novel_path.exists():
        print(f"❌ 错误: 找不到小说文件: {raw_novel_path}")
        return
    
    print(f"\n📖 读取小说...")
    with open(raw_novel_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()
    
    # 提取第一章（简单版本，假设章节格式为 "第X章"）
    import re
    chapter_pattern = re.compile(r'第(\d+|一|二|三|四|五|六|七|八|九|十)章[：:\s]*([^\n]+)')
    chapters = list(chapter_pattern.finditer(raw_content))
    
    if len(chapters) < 1:
        print(f"❌ 错误: 未找到章节")
        return
    
    # 第一章内容
    chapter1_start = chapters[0].start()
    chapter1_end = chapters[1].start() if len(chapters) > 1 else len(raw_content)
    chapter1_content = raw_content[chapter1_start:chapter1_end].strip()
    
    # 提取标题
    chapter1_match = chapters[0]
    chapter_title = chapter1_match.group(2).strip()
    
    print(f"   ✅ 第1章: {chapter_title}")
    print(f"   字数: {len(chapter1_content)}")
    
    # 3. 使用 Claude 分析
    print(f"\n🧠 开始 Claude 分析...")
    print(f"   模型: {config.llm.model_name}")
    print(f"   温度: {config.llm.claude_temperature}")
    print(f"   最大 tokens: {config.llm.claude_max_tokens}")
    
    analyzer = NovelChapterAnalyzer()
    
    start_time = datetime.now()
    
    try:
        analysis_result = analyzer.execute(
            chapter_content=chapter1_content,
            chapter_number=1,
            chapter_title=chapter_title,
            novel_title="末哥超凡公路"
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ 分析完成！")
        print(f"   耗时: {duration:.2f} 秒")
        print(f"   功能段数量: {len(analysis_result.segments)}")
        print(f"   总字数: {analysis_result.metadata.total_word_count}")
        
        # 4. 保存结果
        output_dir = novel_dir / "novel"
        analysis_dir = novel_dir / "novel/functional_analysis"
        output_dir.mkdir(exist_ok=True, parents=True)
        analysis_dir.mkdir(exist_ok=True, parents=True)
        
        # 保存 JSON（versioned）
        print(f"\n💾 保存分析结果...")
        artifact_type = "chpt_0001_functional_analysis_claude"
        ArtifactManager.save_artifact(
            content=analysis_result,
            artifact_type=artifact_type,
            project_id="末哥超凡公路",
            base_dir=str(analysis_dir),
            extension="json"
        )
        print(f"   ✅ JSON: {artifact_type}_latest.json")
        
        # 保存 Markdown
        md_output_path = output_dir / "第1章完整分段分析_Claude.md"
        analyzer.save_markdown(analysis_result, md_output_path)
        print(f"   ✅ Markdown: {md_output_path.name}")
        
        # 5. 显示概览
        print(f"\n" + "="*80)
        print(f"📊 分析概览")
        print(f"="*80)
        
        print(f"\n章节信息:")
        print(f"  标题: {analysis_result.chapter_title}")
        print(f"  功能段数: {len(analysis_result.segments)}")
        print(f"  总字数: {analysis_result.metadata.total_word_count}")
        
        print(f"\n前3个功能段:")
        for i, segment in enumerate(analysis_result.segments[:3], 1):
            print(f"\n  段落{i}: {segment.title}")
            print(f"    字数: {segment.metadata.word_count}")
            print(f"    叙事功能: {', '.join(segment.tags.narrative_function)}")
            print(f"    优先级: {segment.tags.condensation_priority}")
        
        if len(analysis_result.segments) > 3:
            print(f"\n  ... 还有 {len(analysis_result.segments) - 3} 个功能段")
        
        print(f"\n章节摘要:")
        print(f"  {analysis_result.chapter_summary.brief_summary}")
        
        print(f"\n" + "="*80)
        print(f"✅ 完成！请查看 Markdown 文件以获取完整分析")
        print(f"="*80)
        
        # 6. 费用估算（粗略）
        input_tokens = len(chapter1_content) // 4 + 1000  # 内容 + prompt
        output_tokens = len(str(analysis_result.model_dump_json())) // 4
        
        input_cost = (input_tokens / 1_000_000) * 3
        output_cost = (output_tokens / 1_000_000) * 15
        total_cost_usd = input_cost + output_cost
        total_cost_cny = total_cost_usd * 7.2
        
        print(f"\n💰 费用估算:")
        print(f"   输入 tokens: ~{input_tokens}")
        print(f"   输出 tokens: ~{output_tokens}")
        print(f"   本次费用: ~${total_cost_usd:.4f} (≈ ¥{total_cost_cny:.2f})")
        print(f"   预计10章总费用: ~${total_cost_usd*10:.2f} (≈ ¥{total_cost_cny*10:.1f})")
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
