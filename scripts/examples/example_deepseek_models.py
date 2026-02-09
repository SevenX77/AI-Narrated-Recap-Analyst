"""
DeepSeek 多模型使用示例

展示如何在不同场景下选择合适的 DeepSeek 模型：
- v3.2 标准模型（deepseek-chat）：快速响应、低成本
- v3.2 思维链模型（deepseek-reasoner）：深度推理、复杂逻辑
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.llm_client_manager import get_llm_client, get_model_name


def example_simple_task():
    """
    示例 1: 简单任务使用 v3.2 标准模型
    适用于：格式转换、信息提取、简单问答
    """
    print("\n" + "="*80)
    print("  示例 1: 简单任务 - v3.2 标准模型")
    print("="*80)
    
    client = get_llm_client("deepseek")
    model = get_model_name("deepseek", model_type="v32")
    
    print(f"\n使用模型: {model}")
    print("任务类型: 信息提取")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "提取这段文字的关键信息：《三体》是刘慈欣创作的科幻小说，2006年首次出版。"}
        ],
        temperature=0.3  # 低温度保证准确性
    )
    
    print(f"\nAI 回复:")
    print(response.choices[0].message.content)
    print(f"\nToken 使用: {response.usage.total_tokens}")


def example_complex_reasoning():
    """
    示例 2: 复杂推理使用 v3.2 思维链模型
    适用于：逻辑分析、数学推理、策略规划
    """
    print("\n" + "="*80)
    print("  示例 2: 复杂推理 - v3.2 思维链模型")
    print("="*80)
    
    client = get_llm_client("deepseek")
    model = get_model_name("deepseek", model_type="v32-thinking")
    
    print(f"\n使用模型: {model}")
    print("任务类型: 逻辑推理")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "如果所有的A都是B，所有的B都是C，那么能否推断出所有的A都是C？请详细解释推理过程。"}
        ],
        temperature=0.7  # 适中温度保证推理多样性
    )
    
    print(f"\nAI 回复:")
    print(response.choices[0].message.content)
    print(f"\nToken 使用: {response.usage.total_tokens}")


def example_default_usage():
    """
    示例 3: 默认使用（不指定 model_type）
    默认使用 v3.2 标准模型，适合大多数场景
    """
    print("\n" + "="*80)
    print("  示例 3: 默认使用")
    print("="*80)
    
    client = get_llm_client("deepseek")
    model = get_model_name("deepseek")  # 不指定 model_type，使用默认
    
    print(f"\n使用模型: {model}")
    print("说明: 默认使用 v3.2 标准模型（性价比最高）")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "你好！"}
        ]
    )
    
    print(f"\nAI 回复:")
    print(response.choices[0].message.content)
    print(f"\nToken 使用: {response.usage.total_tokens}")


def print_usage_guide():
    """打印使用指南"""
    print("\n" + "="*80)
    print("  DeepSeek 多模型使用指南")
    print("="*80)
    
    print("\n📋 模型选择建议:")
    print("\n1️⃣  v3.2 标准模型 (deepseek-chat)")
    print("   • 适用场景: 信息提取、格式转换、简单问答、内容生成")
    print("   • 优势: 快速响应、成本低、性价比高")
    print("   • 代码: get_model_name('deepseek', model_type='v32')")
    
    print("\n2️⃣  v3.2 思维链模型 (deepseek-reasoner)")
    print("   • 适用场景: 复杂逻辑、数学推理、代码生成、策略分析")
    print("   • 优势: 深度推理、逻辑严密、准确度高")
    print("   • 代码: get_model_name('deepseek', model_type='v32-thinking')")
    
    print("\n3️⃣  默认模型（不指定 model_type）")
    print("   • 默认使用 v3.2 标准模型")
    print("   • 适合大多数场景")
    print("   • 代码: get_model_name('deepseek')")
    
    print("\n💡 选择建议:")
    print("   • 80% 的任务 → v3.2 标准模型（快速、便宜）")
    print("   • 20% 的复杂任务 → v3.2 思维链模型（深度、准确）")
    print("   • 拿不准时先用标准模型，不满意再用思维链模型")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  DeepSeek 多模型使用示例")
    print("="*80)
    
    try:
        # 打印使用指南
        print_usage_guide()
        
        # 示例 1: 简单任务
        example_simple_task()
        
        # 示例 2: 复杂推理
        example_complex_reasoning()
        
        # 示例 3: 默认使用
        example_default_usage()
        
        print("\n" + "="*80)
        print("  ✅ 所有示例执行完成")
        print("="*80)
        print()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
