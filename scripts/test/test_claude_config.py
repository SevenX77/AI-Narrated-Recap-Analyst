"""
测试Claude配置是否正确加载
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm_rate_limiter import get_llm_manager


def test_claude_config():
    """测试Claude配置"""
    print("=" * 80)
    print("🧪 测试Claude配置")
    print("=" * 80)
    
    manager = get_llm_manager()
    
    # 测试不同的查找方式
    test_cases = [
        ("claude", "claude-sonnet-4-5-20250929"),
        ("anthropic", "claude-3-5-sonnet-20241022"),
        ("deepseek", "deepseek-chat"),
    ]
    
    print("\n📋 配置文件中的所有配置:")
    for key, config in manager.configs.items():
        print(f"  {key}:")
        print(f"    provider: {config.provider}")
        print(f"    model: {config.model}")
        print(f"    QPM: {config.requests_per_minute}")
        print(f"    并发: {config.max_concurrent}")
        print()
    
    print("\n🔍 测试配置查找:")
    for provider, model in test_cases:
        print(f"\n查找: provider={provider}, model={model}")
        config = manager.get_config(provider, model)
        print(f"  ✅ 找到配置:")
        print(f"    provider: {config.provider}")
        print(f"    model: {config.model}")
        print(f"    QPM: {config.requests_per_minute}")
        print(f"    并发: {config.max_concurrent}")
        print(f"    重试: {config.max_retries}次")
        print(f"    备注: {config.test_notes}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_claude_config()
