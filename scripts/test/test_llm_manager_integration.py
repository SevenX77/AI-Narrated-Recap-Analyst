"""
LLM调用管理器集成测试

演示如何在workflow中使用LLMCallManager
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm_rate_limiter import get_llm_manager, LLMRateLimitConfig


async def demo_basic_usage():
    """演示基本使用方法"""
    print("=" * 80)
    print("🧪 演示1: 基本使用")
    print("=" * 80)
    
    # 获取全局管理器
    manager = get_llm_manager()
    
    # 查看当前配置
    print("\n📋 当前配置:")
    for key, config in manager.configs.items():
        if key != "conservative":
            print(f"  {key}: QPM={config.requests_per_minute}, 并发={config.max_concurrent}")
    
    # 模拟LLM调用函数
    def mock_llm_call(prompt: str):
        """模拟LLM调用"""
        import time
        import random
        
        time.sleep(0.1)  # 模拟网络延迟
        
        # 5%概率触发限流
        if random.random() < 0.05:
            raise Exception("Error code: 403 - access forbidden")
        
        return {"content": f"Response to: {prompt}", "tokens": 100}
    
    # 使用管理器调用
    print("\n🔄 发起10次LLM调用（自动限流+重试）...")
    
    success_count = 0
    for i in range(10):
        try:
            result = await manager.call_with_rate_limit(
                func=mock_llm_call,
                provider="deepseek",
                model="deepseek-chat",
                estimated_tokens=100,
                prompt=f"Test prompt {i+1}"
            )
            success_count += 1
            print(f"  ✅ 请求{i+1}: {result['content'][:30]}...")
        except Exception as e:
            print(f"  ❌ 请求{i+1}失败: {e}")
    
    print(f"\n📊 成功率: {success_count}/10")
    
    # 查看统计信息
    print("\n📈 使用统计:")
    stats = manager.get_all_stats()
    for model, stat in stats.items():
        if stat['requests_last_minute'] > 0:
            print(f"  {model}:")
            print(f"    最近1分钟请求: {stat['requests_last_minute']}")
            print(f"    最近1分钟tokens: {stat['tokens_last_minute']}")
            print(f"    当前并发: {stat['current_concurrent']}")


async def demo_concurrent_calls():
    """演示并发调用（自动限流）"""
    print("\n" + "=" * 80)
    print("🧪 演示2: 并发调用（自动限流控制）")
    print("=" * 80)
    
    manager = get_llm_manager()
    
    def mock_llm_call(task_id: int):
        import time
        import random
        
        time.sleep(0.2)
        
        if random.random() < 0.05:
            raise Exception("Error code: 403 - rate limit")
        
        return {"task_id": task_id, "status": "success"}
    
    # 创建20个并发任务
    print("\n🚀 发起20个并发任务...")
    print("（管理器会自动限流，避免超过max_concurrent）")
    
    tasks = []
    for i in range(20):
        task = manager.call_with_rate_limit(
            func=mock_llm_call,
            provider="deepseek",
            model="deepseek-chat",
            estimated_tokens=100,
            task_id=i+1
        )
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success = sum(1 for r in results if not isinstance(r, Exception))
    failed = len(results) - success
    
    print(f"\n📊 结果:")
    print(f"  成功: {success}/20")
    print(f"  失败: {failed}/20")


async def demo_rate_limit_detection():
    """演示限流检测"""
    print("\n" + "=" * 80)
    print("🧪 演示3: 限流检测与智能重试")
    print("=" * 80)
    
    manager = get_llm_manager()
    
    def mock_llm_with_rate_limit(attempt: int):
        """模拟会触发限流的调用"""
        import time
        
        time.sleep(0.1)
        
        # 前2次必定触发限流，第3次成功
        if attempt < 2:
            raise Exception("Error code: 403 - access forbidden")
        
        return {"status": "success", "attempt": attempt}
    
    print("\n🔄 调用会触发限流的API...")
    print("（管理器会自动检测限流并延长重试间隔）")
    
    attempt_counter = [0]  # 使用列表来在闭包中修改
    
    def wrapped_call():
        attempt_counter[0] += 1
        return mock_llm_with_rate_limit(attempt_counter[0])
    
    try:
        result = await manager.call_with_rate_limit(
            func=wrapped_call,
            provider="deepseek",
            model="deepseek-chat",
            estimated_tokens=100
        )
        print(f"\n✅ 最终成功: {result}")
        print(f"   总尝试次数: {attempt_counter[0]}")
    except Exception as e:
        print(f"\n❌ 最终失败: {e}")


async def demo_config_update():
    """演示配置更新"""
    print("\n" + "=" * 80)
    print("🧪 演示4: 动态更新配置")
    print("=" * 80)
    
    manager = get_llm_manager()
    
    # 查看当前配置
    config = manager.get_config("deepseek", "deepseek-chat")
    print(f"\n📋 当前DeepSeek配置:")
    print(f"  QPM: {config.requests_per_minute}")
    print(f"  并发: {config.max_concurrent}")
    print(f"  重试次数: {config.max_retries}")
    
    # 更新配置
    print("\n🔧 更新配置...")
    manager.update_config(
        "deepseek_chat",
        requests_per_minute=100,  # 提高QPM
        max_concurrent=3,  # 提高并发
        is_tested=True,
        last_test_date="2026-02-10",
        test_notes="测试验证：可支持更高QPM"
    )
    
    # 查看更新后的配置
    config = manager.get_config("deepseek", "deepseek-chat")
    print(f"\n📋 更新后的配置:")
    print(f"  QPM: {config.requests_per_minute}")
    print(f"  并发: {config.max_concurrent}")
    print(f"  已测试: {config.is_tested}")
    print(f"  测试日期: {config.last_test_date}")
    print(f"  测试备注: {config.test_notes}")


async def main():
    """运行所有演示"""
    print("=" * 80)
    print("🚀 LLM调用管理器集成测试")
    print("=" * 80)
    
    # 演示1: 基本使用
    await demo_basic_usage()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 演示2: 并发调用
    await demo_concurrent_calls()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 演示3: 限流检测
    await demo_rate_limit_detection()
    
    # 演示4: 配置更新
    await demo_config_update()
    
    print("\n" + "=" * 80)
    print("✅ 所有演示完成！")
    print("=" * 80)
    print("\n💡 提示:")
    print("  - 配置已保存到: config/llm_configs.json")
    print("  - 可运行测试工具: python3 scripts/test/test_llm_rate_limits.py")
    print("  - 查看文档: docs/core/LLM_RATE_LIMIT_SYSTEM.md")


if __name__ == "__main__":
    asyncio.run(main())
