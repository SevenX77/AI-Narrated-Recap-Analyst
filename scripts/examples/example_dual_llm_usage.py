"""
双 LLM Provider 使用示例

展示如何在实际场景中使用 Claude 和 DeepSeek
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tools.novel_metadata_extractor import NovelMetadataExtractor
from src.tools.novel_segmenter import NovelSegmenter
from src.core.llm_client_manager import LLMClientManager


def example_1_metadata_extraction():
    """
    示例 1: 元数据提取（使用 DeepSeek）
    
    场景：提取小说的标题、作者、标签、简介
    策略：简单任务，使用 DeepSeek 节省成本
    """
    print("\n" + "="*80)
    print("  示例 1: 元数据提取（DeepSeek）")
    print("="*80)
    
    # 默认使用 DeepSeek
    extractor = NovelMetadataExtractor(use_llm=True, provider="deepseek")
    
    # 假设有小说文件
    # novel_file = "data/projects/xxx/raw/novel.txt"
    # metadata = extractor.execute(novel_file)
    # print(f"标题: {metadata.title}")
    # print(f"作者: {metadata.author}")
    
    print("\n✅ NovelMetadataExtractor 默认使用 DeepSeek")
    print("   原因: 元数据提取是简单任务，DeepSeek 性价比高")


def example_2_novel_segmentation():
    """
    示例 2: 小说分段分析（使用 Claude）
    
    场景：对小说章节进行叙事功能分段
    策略：复杂任务，使用 Claude 保证质量
    """
    print("\n" + "="*80)
    print("  示例 2: 小说分段分析（Claude）")
    print("="*80)
    
    # 默认使用 Claude
    segmenter = NovelSegmenter(provider="claude")
    
    # 假设有小说文件
    # novel_file = "data/projects/xxx/raw/novel.txt"
    # result = segmenter.execute(novel_file, chapter_number=1)
    
    print("\n✅ NovelSegmenter 默认使用 Claude")
    print("   原因: 小说分段需要深度理解叙事结构，Claude 质量更高")


def example_3_custom_llm_call():
    """
    示例 3: 自定义 LLM 调用
    
    场景：在自己的代码中直接调用 LLM
    策略：根据任务复杂度选择合适的 Provider
    """
    print("\n" + "="*80)
    print("  示例 3: 自定义 LLM 调用")
    print("="*80)
    
    from src.core.llm_client_manager import get_llm_client, get_model_name
    
    # 简单任务：使用 DeepSeek
    print("\n【简单任务示例】提取关键词")
    deepseek_client = get_llm_client("deepseek")
    deepseek_model = get_model_name("deepseek")
    
    print(f"  使用: DeepSeek ({deepseek_model})")
    print(f"  任务: 从文本中提取关键词（简单提取）")
    
    # response = deepseek_client.chat.completions.create(
    #     model=deepseek_model,
    #     messages=[{"role": "user", "content": "从以下文本提取关键词..."}]
    # )
    
    # 复杂任务：使用 Claude
    print("\n【复杂任务示例】创意文案生成")
    claude_client = get_llm_client("claude")
    claude_model = get_model_name("claude")
    
    print(f"  使用: Claude ({claude_model})")
    print(f"  任务: 基于小说生成吸引人的宣传文案（需要创意和理解）")
    
    # response = claude_client.chat.completions.create(
    #     model=claude_model,
    #     messages=[{"role": "user", "content": "为以下小说生成宣传文案..."}]
    # )


def example_4_mixed_workflow():
    """
    示例 4: 混合工作流
    
    场景：一个完整的分析流程，混用两个 Provider
    策略：根据每个步骤的复杂度选择最优 Provider
    """
    print("\n" + "="*80)
    print("  示例 4: 混合工作流")
    print("="*80)
    
    print("\n📝 完整分析流程:")
    print("\n步骤 1: 提取元数据")
    print("  → 使用 DeepSeek（简单提取）")
    # metadata = NovelMetadataExtractor(provider="deepseek").execute(novel_file)
    
    print("\n步骤 2: 章节分段分析")
    print("  → 使用 Claude（复杂分析）")
    # segments = NovelSegmenter(provider="claude").execute(novel_file, chapter_number=1)
    
    print("\n步骤 3: 关键信息提取")
    print("  → 使用 DeepSeek（简单提取）")
    # key_info = extract_with_deepseek(segments)
    
    print("\n步骤 4: 改编建议生成")
    print("  → 使用 Claude（需要创意）")
    # suggestions = generate_with_claude(key_info)
    
    print("\n✅ 混合策略：简单步骤用 DeepSeek，复杂步骤用 Claude")
    print("   效果：平衡成本和质量")


def example_5_usage_monitoring():
    """
    示例 5: 使用统计监控
    
    场景：查看当前会话的 LLM 使用情况
    策略：定期监控成本，优化使用策略
    """
    print("\n" + "="*80)
    print("  示例 5: 使用统计监控")
    print("="*80)
    
    # 获取使用统计
    stats = LLMClientManager.get_usage_stats()
    
    print("\n📊 当前会话使用统计:\n")
    
    for provider, data in stats.items():
        print(f"【{provider.upper()}】")
        print(f"  调用次数: {data.get('total_calls', 0)}")
        print(f"  总 Token: {data.get('total_tokens', 0)}")
        print(f"  输入 Token: {data.get('prompt_tokens', 0)}")
        print(f"  输出 Token: {data.get('completion_tokens', 0)}")
        print()
    
    # 估算成本（示例价格）
    print("💰 成本估算（假设价格）:")
    print("  Claude: $0.015/1K tokens (输入) + $0.075/1K tokens (输出)")
    print("  DeepSeek: $0.001/1K tokens (输入) + $0.002/1K tokens (输出)")
    print("\n  提示：实际价格以官方为准")


def main():
    """主函数：运行所有示例"""
    print("\n" + "📚" * 40)
    print("  双 LLM Provider 使用示例")
    print("📚" * 40)
    
    print("\n本示例展示:")
    print("  1. 如何在不同场景选择合适的 Provider")
    print("  2. 如何平衡成本和质量")
    print("  3. 如何监控 LLM 使用情况")
    
    # 运行示例
    example_1_metadata_extraction()
    example_2_novel_segmentation()
    example_3_custom_llm_call()
    example_4_mixed_workflow()
    example_5_usage_monitoring()
    
    # 总结
    print("\n" + "="*80)
    print("  📋 使用建议总结")
    print("="*80)
    
    print("\n✅ 推荐策略:")
    print("  • 元数据提取、格式转换 → DeepSeek")
    print("  • 小说分析、改编建议 → Claude")
    print("  • 规则提取、逻辑推理 → DeepSeek R1")
    print("  • 质量评估、创意生成 → Claude")
    
    print("\n💡 成本优化技巧:")
    print("  • 优先使用 DeepSeek，除非明确需要 Claude")
    print("  • 定期查看使用统计，识别高成本环节")
    print("  • 批量处理相同任务，减少重复调用")
    print("  • 缓存常用结果，避免重复计算")
    
    print("\n🔍 更多信息:")
    print("  • 配置指南: docs/core/DUAL_LLM_SETUP.md")
    print("  • API 文档: src/core/llm_client_manager.py")
    print("  • 测试脚本: scripts/test/test_dual_llm_providers.py")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
