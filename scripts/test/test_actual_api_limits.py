"""
实际API限流测试工具

用于测试真实API的限流规则，并更新配置。
⚠️ 警告：此测试会消耗实际API配额！
"""

import asyncio
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Callable

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm_rate_limiter import LLMCallManager, LLMRateLimitConfig


class ActualAPITester:
    """实际API限流测试器"""
    
    def __init__(self):
        self.manager = LLMCallManager()
        self.test_results: Dict[str, Dict] = {}
    
    def create_deepseek_caller(self) -> Optional[Callable]:
        """创建DeepSeek API调用函数"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("⚠️ 未找到DEEPSEEK_API_KEY环境变量")
            return None
        
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            
            def call_deepseek():
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "user", "content": "请用一句话回复：你好"}
                    ],
                    max_tokens=50,
                    temperature=0.0
                )
                return {
                    "content": response.choices[0].message.content,
                    "tokens": response.usage.total_tokens
                }
            
            return call_deepseek
        
        except ImportError:
            print("❌ 未安装openai库: pip install openai")
            return None
        except Exception as e:
            print(f"❌ DeepSeek初始化失败: {e}")
            return None
    
    def create_anthropic_caller(self) -> Optional[Callable]:
        """创建Anthropic API调用函数"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️ 未找到ANTHROPIC_API_KEY环境变量")
            return None
        
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=api_key)
            
            def call_anthropic():
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=50,
                    messages=[
                        {"role": "user", "content": "请用一句话回复：你好"}
                    ]
                )
                return {
                    "content": response.content[0].text,
                    "tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            
            return call_anthropic
        
        except ImportError:
            print("❌ 未安装anthropic库: pip install anthropic")
            return None
        except Exception as e:
            print(f"❌ Anthropic初始化失败: {e}")
            return None
    
    async def test_api_limits(
        self,
        provider: str,
        model: str,
        api_caller: Callable,
        test_duration: int = 120,
        initial_delay: float = 3.0
    ) -> Dict:
        """
        测试API实际限流规则
        
        Args:
            provider: 提供商名称
            model: 模型名称
            api_caller: API调用函数
            test_duration: 测试时长（秒）
            initial_delay: 初始延迟（秒）
        
        Returns:
            测试结果
        """
        print("=" * 80)
        print(f"🧪 测试 {provider}/{model} 实际API限流")
        print("=" * 80)
        print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
        print(f"⏱️ 测试时长: {test_duration}秒")
        print(f"⚠️ 警告：此测试会消耗实际API配额！")
        print()
        
        start_time = time.time()
        success_count = 0
        rate_limit_count = 0
        error_count = 0
        
        request_times = []
        token_usage = []
        
        current_delay = initial_delay
        
        while time.time() - start_time < test_duration:
            elapsed = time.time() - start_time
            print(f"\r⏳ 进度: {elapsed:.0f}/{test_duration}s | 成功:{success_count} 限流:{rate_limit_count} 错误:{error_count}", end="")
            
            try:
                request_time = time.time()
                
                # 调用实际API
                result = api_caller()
                
                # 记录成功
                success_count += 1
                request_times.append(request_time)
                token_usage.append(result.get("tokens", 0))
                
                # 逐渐缩短延迟（探测限流阈值）
                current_delay = max(0.5, current_delay * 0.95)
                
            except Exception as e:
                error_msg = str(e)
                
                # 判断错误类型
                is_rate_limit = any(
                    code in error_msg
                    for code in ["403", "429", "rate", "limit", "quota"]
                )
                
                if is_rate_limit:
                    rate_limit_count += 1
                    # 触发限流后延长延迟
                    current_delay = min(30.0, current_delay * 2)
                else:
                    error_count += 1
                    print(f"\n❌ 其他错误: {error_msg[:80]}")
            
            # 等待
            await asyncio.sleep(current_delay)
        
        print()  # 换行
        
        # 分析结果
        total_elapsed = time.time() - start_time
        
        # 计算QPM（基于成功请求）
        if success_count > 0:
            estimated_qpm = int(success_count / total_elapsed * 60)
        else:
            estimated_qpm = 0
        
        # 计算TPM（基于token使用）
        if token_usage:
            total_tokens = sum(token_usage)
            estimated_tpm = int(total_tokens / total_elapsed * 60)
        else:
            estimated_tpm = 0
        
        # 建议配置
        if rate_limit_count > 0:
            # 触发了限流，使用保守估计
            suggested_qpm = max(10, int(estimated_qpm * 0.7))  # 留30%余量
            suggested_concurrent = 1
            notes = f"触发{rate_limit_count}次限流，建议保守配置"
        else:
            # 未触发限流，可以更激进
            suggested_qpm = estimated_qpm
            suggested_concurrent = 2
            notes = f"未触发限流，可以更高配置"
        
        result = {
            "provider": provider,
            "model": model,
            "test_date": datetime.now().isoformat(),
            "test_duration_seconds": int(total_elapsed),
            "total_attempts": success_count + rate_limit_count + error_count,
            "successful_requests": success_count,
            "rate_limited_requests": rate_limit_count,
            "other_errors": error_count,
            "estimated_qpm": estimated_qpm,
            "estimated_tpm": estimated_tpm,
            "suggested_qpm": suggested_qpm,
            "suggested_concurrent": suggested_concurrent,
            "notes": notes
        }
        
        # 输出结果
        print("\n" + "=" * 80)
        print("📊 测试结果")
        print("=" * 80)
        print(f"测试时长: {total_elapsed:.1f}秒")
        print(f"成功请求: {success_count}")
        print(f"限流次数: {rate_limit_count}")
        print(f"其他错误: {error_count}")
        print(f"估算QPM: {estimated_qpm}")
        print(f"估算TPM: {estimated_tpm}")
        print(f"\n💡 建议配置:")
        print(f"  QPM: {suggested_qpm}")
        print(f"  max_concurrent: {suggested_concurrent}")
        print(f"  备注: {notes}")
        print("=" * 80)
        
        self.test_results[f"{provider}_{model}"] = result
        
        return result
    
    def save_results(self):
        """保存测试结果"""
        import json
        
        results_file = Path("output/llm_rate_limit_test_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载已有结果
        existing_results = {}
        if results_file.exists():
            with open(results_file, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        
        # 合并结果
        existing_results.update(self.test_results)
        
        # 保存
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(existing_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 测试结果已保存到: {results_file}")
    
    def update_configs(self):
        """根据测试结果更新配置"""
        print("\n🔧 根据测试结果更新配置")
        
        for key, result in self.test_results.items():
            suggested_qpm = result.get("suggested_qpm")
            suggested_concurrent = result.get("suggested_concurrent", 1)
            
            if suggested_qpm:
                self.manager.update_config(
                    key,
                    requests_per_minute=suggested_qpm,
                    max_concurrent=suggested_concurrent,
                    is_tested=True,
                    last_test_date=result["test_date"],
                    test_notes=result["notes"]
                )
                print(f"✅ 更新{key}: QPM={suggested_qpm}, 并发={suggested_concurrent}")
        
        print("✅ 配置更新完成")


async def main():
    """主测试流程"""
    print("=" * 80)
    print("🧪 实际API限流测试工具")
    print("=" * 80)
    print()
    print("⚠️ 警告：此测试会消耗实际API配额！")
    print()
    print("请选择要测试的API:")
    print("1. DeepSeek (deepseek-chat)")
    print("2. Anthropic Claude (claude-3-5-sonnet)")
    print("3. 退出")
    print()
    
    choice = input("请选择 (1-3): ").strip()
    
    tester = ActualAPITester()
    
    if choice == "1":
        print("\n🔍 检查DeepSeek API...")
        api_caller = tester.create_deepseek_caller()
        
        if api_caller:
            confirm = input("\n确认开始测试？(y/n): ").strip().lower()
            if confirm == 'y':
                result = await tester.test_api_limits(
                    provider="deepseek",
                    model="deepseek-chat",
                    api_caller=api_caller,
                    test_duration=120,  # 测试2分钟
                    initial_delay=3.0
                )
                
                # 保存结果
                tester.save_results()
                
                # 询问是否更新配置
                update = input("\n是否根据测试结果更新配置？(y/n): ").strip().lower()
                if update == 'y':
                    tester.update_configs()
    
    elif choice == "2":
        print("\n🔍 检查Anthropic API...")
        api_caller = tester.create_anthropic_caller()
        
        if api_caller:
            confirm = input("\n确认开始测试？(y/n): ").strip().lower()
            if confirm == 'y':
                result = await tester.test_api_limits(
                    provider="anthropic",
                    model="claude-3-5-sonnet-20241022",
                    api_caller=api_caller,
                    test_duration=120,
                    initial_delay=2.0
                )
                
                tester.save_results()
                
                update = input("\n是否根据测试结果更新配置？(y/n): ").strip().lower()
                if update == 'y':
                    tester.update_configs()
    
    elif choice == "3":
        print("👋 退出")
        return
    
    print("\n✅ 测试完成！")
    print("\n📂 查看结果:")
    print("  - 配置文件: config/llm_configs.json")
    print("  - 测试结果: output/llm_rate_limit_test_results.json")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
        print("部分结果可能已保存")
