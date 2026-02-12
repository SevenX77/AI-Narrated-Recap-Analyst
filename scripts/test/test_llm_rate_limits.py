"""
LLM限流规则测试工具

自动测试各个LLM提供商的实际限流规则，并更新配置。
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm_rate_limiter import LLMCallManager, LLMRateLimitConfig


class LLMRateLimitTester:
    """LLM限流规则测试器"""
    
    def __init__(self):
        self.manager = LLMCallManager()
        self.test_results: Dict[str, Dict] = {}
    
    async def test_provider(
        self,
        provider: str,
        model: str,
        test_func,
        test_duration: int = 60,
        ramp_up_delay: float = 1.0
    ) -> Dict:
        """
        测试单个提供商的限流规则
        
        Args:
            provider: 提供商名称
            model: 模型名称
            test_func: 测试用的API调用函数
            test_duration: 测试时长（秒）
            ramp_up_delay: 初始延迟（秒），逐渐减少
        
        Returns:
            测试结果字典
        """
        print("=" * 80)
        print(f"🧪 测试 {provider}/{model}")
        print("=" * 80)
        
        start_time = time.time()
        success_count = 0
        rate_limit_count = 0
        error_count = 0
        last_success_time = start_time
        
        # 记录请求时间戳
        request_times: List[float] = []
        
        # 测试逻辑：逐渐加快请求频率，直到触发限流
        current_delay = ramp_up_delay
        
        while time.time() - start_time < test_duration:
            try:
                # 记录请求时间
                request_time = time.time()
                request_times.append(request_time)
                
                # 调用API
                print(f"📞 发起请求（延迟={current_delay:.2f}s）...", end=" ")
                result = test_func()
                
                # 成功
                success_count += 1
                last_success_time = request_time
                print(f"✅ 成功（总计{success_count}次）")
                
                # 逐渐缩短延迟
                current_delay = max(0.1, current_delay * 0.9)
                
            except Exception as e:
                error_msg = str(e)
                
                # 判断错误类型
                is_rate_limit = any(
                    code in error_msg
                    for code in ["403", "429", "rate limit", "too many requests"]
                )
                
                if is_rate_limit:
                    rate_limit_count += 1
                    print(f"🚫 触发限流（总计{rate_limit_count}次）")
                    
                    # 触发限流后延长延迟
                    current_delay = min(10.0, current_delay * 2)
                else:
                    error_count += 1
                    print(f"❌ 其他错误: {error_msg[:50]}")
            
            # 等待
            await asyncio.sleep(current_delay)
        
        # 分析结果
        elapsed = time.time() - start_time
        
        # 计算QPM（基于最近1分钟的成功请求）
        recent_requests = [t for t in request_times if t > last_success_time - 60]
        estimated_qpm = len(recent_requests) if recent_requests else success_count
        
        result = {
            "provider": provider,
            "model": model,
            "test_date": datetime.now().isoformat(),
            "test_duration_seconds": int(elapsed),
            "total_requests": success_count + rate_limit_count + error_count,
            "successful_requests": success_count,
            "rate_limited_requests": rate_limit_count,
            "other_errors": error_count,
            "estimated_qpm": estimated_qpm,
            "average_delay": elapsed / success_count if success_count > 0 else 0,
            "notes": ""
        }
        
        # 添加建议配置
        if rate_limit_count > 0:
            # 触发了限流，使用保守估计
            suggested_qpm = int(estimated_qpm * 0.8)  # 留20%余量
            result["suggested_qpm"] = suggested_qpm
            result["notes"] = f"触发{rate_limit_count}次限流，建议QPM设置为{suggested_qpm}"
        else:
            # 未触发限流，可以更激进
            result["suggested_qpm"] = estimated_qpm
            result["notes"] = f"未触发限流，可设置QPM为{estimated_qpm}或更高"
        
        self.test_results[f"{provider}_{model}"] = result
        
        print("\n" + "=" * 80)
        print("📊 测试结果")
        print("=" * 80)
        print(f"测试时长: {elapsed:.1f}秒")
        print(f"成功请求: {success_count}")
        print(f"限流次数: {rate_limit_count}")
        print(f"其他错误: {error_count}")
        print(f"估算QPM: {estimated_qpm}")
        print(f"建议QPM: {result['suggested_qpm']}")
        print(f"备注: {result['notes']}")
        print("=" * 80)
        print()
        
        return result
    
    async def quick_test_all(self):
        """快速测试所有已配置的提供商"""
        print("🚀 开始快速测试所有LLM提供商")
        print()
        
        # 这里需要实际的API调用函数
        # 暂时使用mock函数演示
        def mock_api_call():
            """模拟API调用"""
            import random
            time.sleep(0.1)  # 模拟网络延迟
            
            # 10%概率触发限流
            if random.random() < 0.1:
                raise Exception("Error code: 403 - access forbidden")
            
            return {"status": "success"}
        
        # 测试所有提供商
        for key, config in self.manager.configs.items():
            if key == "conservative":
                continue  # 跳过保守配置
            
            try:
                await self.test_provider(
                    provider=config.provider,
                    model=config.model,
                    test_func=mock_api_call,
                    test_duration=30,  # 快速测试30秒
                    ramp_up_delay=2.0
                )
            except KeyboardInterrupt:
                print("\n⚠️ 用户中断测试")
                break
            except Exception as e:
                print(f"❌ 测试{key}时出错: {e}")
                continue
        
        # 保存测试结果
        self._save_test_results()
    
    def _save_test_results(self):
        """保存测试结果"""
        import json
        
        results_file = Path("data/llm_rate_limit_test_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 测试结果已保存到: {results_file}")
    
    def update_configs_from_test(self):
        """根据测试结果更新配置"""
        print("\n🔧 根据测试结果更新配置")
        
        for key, result in self.test_results.items():
            suggested_qpm = result.get("suggested_qpm")
            if suggested_qpm:
                self.manager.update_config(
                    key,
                    requests_per_minute=suggested_qpm,
                    is_tested=True,
                    last_test_date=result["test_date"],
                    test_notes=result["notes"]
                )
                print(f"✅ 更新{key}: QPM={suggested_qpm}")
        
        print("✅ 配置更新完成")


async def interactive_test():
    """交互式测试"""
    tester = LLMRateLimitTester()
    
    print("=" * 80)
    print("🧪 LLM限流规则测试工具")
    print("=" * 80)
    print()
    print("选择测试模式:")
    print("1. 快速测试所有提供商（使用mock数据）")
    print("2. 测试单个提供商（需要实际API）")
    print("3. 查看当前配置")
    print("4. 退出")
    print()
    
    choice = input("请选择 (1-4): ").strip()
    
    if choice == "1":
        await tester.quick_test_all()
        
        # 询问是否更新配置
        update = input("\n是否根据测试结果更新配置？(y/n): ").strip().lower()
        if update == 'y':
            tester.update_configs_from_test()
    
    elif choice == "2":
        print("\n⚠️ 需要实际API才能测试，请自行实现test_func")
    
    elif choice == "3":
        print("\n📋 当前配置:")
        print("=" * 80)
        for key, config in tester.manager.configs.items():
            print(f"\n{key}:")
            print(f"  提供商: {config.provider}")
            print(f"  模型: {config.model}")
            print(f"  QPM: {config.requests_per_minute}")
            print(f"  QPD: {config.requests_per_day}")
            print(f"  最大并发: {config.max_concurrent}")
            print(f"  已测试: {config.is_tested}")
            if config.last_test_date:
                print(f"  测试日期: {config.last_test_date}")
            if config.test_notes:
                print(f"  备注: {config.test_notes}")
        print("=" * 80)
    
    elif choice == "4":
        print("👋 退出")
        return


if __name__ == "__main__":
    asyncio.run(interactive_test())
