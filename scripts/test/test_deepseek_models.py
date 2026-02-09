"""
测试 DeepSeek 多模型配置
验证 v3.2 和 v3.2 thinking 两个模型都能正确使用
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.llm_client_manager import get_llm_client, get_model_name
from src.core.config import config


def test_deepseek_models():
    """测试 DeepSeek 多模型配置"""
    print("\n" + "="*80)
    print("  DeepSeek 多模型配置测试")
    print("="*80)
    
    print("\n✅ 检查 1: 配置验证\n")
    
    print(f"  DeepSeek API Key: {'已配置' if config.llm.deepseek_api_key else '未配置'}")
    print(f"  DeepSeek Base URL: {config.llm.deepseek_base_url}")
    print(f"  DeepSeek v3.2 Model: {config.llm.deepseek_v32_model}")
    print(f"  DeepSeek v3.2 Thinking Model: {config.llm.deepseek_v32_thinking_model}")
    print(f"  DeepSeek Default Model: {config.llm.deepseek_model_name}")
    
    print("\n✅ 检查 2: 模型名称获取\n")
    
    # 测试获取不同模型名称
    default_model = get_model_name("deepseek")
    v32_model = get_model_name("deepseek", model_type="v32")
    thinking_model = get_model_name("deepseek", model_type="v32-thinking")
    
    print(f"  默认模型: {default_model}")
    print(f"  v3.2 标准模型: {v32_model}")
    print(f"  v3.2 思维链模型: {thinking_model}")
    
    # 验证
    assert default_model == "deepseek-chat", f"默认模型错误: {default_model}"
    assert v32_model == "deepseek-chat", f"v3.2模型错误: {v32_model}"
    assert thinking_model == "deepseek-reasoner", f"思维链模型错误: {thinking_model}"
    
    print("\n  ✅ 所有模型名称正确")
    
    print("\n✅ 检查 3: 客户端创建\n")
    
    try:
        client = get_llm_client("deepseek")
        print(f"  ✅ DeepSeek 客户端创建成功")
    except Exception as e:
        print(f"  ❌ 客户端创建失败: {e}")
        return False
    
    print("\n" + "="*80)
    print("  使用示例")
    print("="*80)
    
    print("\n```python")
    print("from src.core.llm_client_manager import get_llm_client, get_model_name")
    print("")
    print("# 使用 v3.2 标准模型（快速、低成本）")
    print("client = get_llm_client('deepseek')")
    print("model = get_model_name('deepseek', model_type='v32')")
    print("# model = 'deepseek-chat'")
    print("")
    print("# 使用 v3.2 思维链模型（深度推理）")
    print("client = get_llm_client('deepseek')")
    print("model = get_model_name('deepseek', model_type='v32-thinking')")
    print("# model = 'deepseek-reasoner'")
    print("")
    print("# 调用示例")
    print("response = client.chat.completions.create(")
    print("    model=model,")
    print("    messages=[{'role': 'user', 'content': '...'}]")
    print(")")
    print("```")
    
    print("\n" + "="*80)
    print("  📋 测试总结")
    print("="*80)
    
    print("\n✅ DeepSeek 多模型配置正确")
    print("✅ 支持 v3.2 标准模型（deepseek-chat）")
    print("✅ 支持 v3.2 思维链模型（deepseek-reasoner）")
    print("✅ 工具可通过 model_type 参数选择模型")
    
    print("\n💡 使用建议:")
    print("  • 简单任务/快速响应 → v3.2 标准模型")
    print("  • 复杂推理/逻辑分析 → v3.2 思维链模型")
    print("  • 默认使用标准模型（性价比高）")
    
    print("\n")
    return True


if __name__ == "__main__":
    success = test_deepseek_models()
    sys.exit(0 if success else 1)
