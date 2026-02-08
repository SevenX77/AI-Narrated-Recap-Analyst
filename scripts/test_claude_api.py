#!/usr/bin/env python3
"""
Claude API 测试脚本
用途：测试 Claude Sonnet 4.5 Thinking 模型的连接性和响应质量
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from openai import OpenAI
import json
from datetime import datetime

# 加载环境变量
load_dotenv()

def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量（粗略估计：1 token ≈ 4 字符）
    """
    return len(text) // 4

def calculate_cost(input_tokens: int, output_tokens: int) -> dict:
    """
    计算 Claude Sonnet 4.5 的费用
    价格：输入 $3/M tokens，输出 $15/M tokens
    """
    input_cost = (input_tokens / 1_000_000) * 3
    output_cost = (output_tokens / 1_000_000) * 15
    total_cost = input_cost + output_cost
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
        "total_cost_cny": round(total_cost * 7.2, 4),  # 假设汇率 1 USD = 7.2 CNY
    }

def test_basic_connection():
    """测试基础连接"""
    print("\n" + "="*60)
    print("🔍 测试 1: 基础连接测试")
    print("="*60)
    
    api_key = os.getenv("CLAUDE_API_KEY")
    base_url = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")
    model = os.getenv("CLAUDE_MODEL_NAME", "claude-sonnet-4-5-20250929")
    
    if not api_key:
        print("❌ 错误: CLAUDE_API_KEY 未设置")
        print("请在 .env 文件中配置 CLAUDE_API_KEY")
        return False
    
    print(f"📋 配置信息:")
    print(f"   API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    
    try:
        # OneChats 使用 OpenAI 兼容的 API
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        test_prompt = "请用一句话介绍你自己。"
        
        print(f"\n📤 发送测试请求...")
        print(f"   提示词: {test_prompt}")
        
        response = client.chat.completions.create(
            model=model,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": test_prompt
            }]
        )
        
        print(f"\n✅ 连接成功!")
        print(f"   响应: {response.choices[0].message.content}")
        
        # 计算费用
        cost_info = calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )
        
        print(f"\n💰 费用统计:")
        print(f"   输入 tokens: {cost_info['input_tokens']}")
        print(f"   输出 tokens: {cost_info['output_tokens']}")
        print(f"   本次费用: ${cost_info['total_cost_usd']} (≈ ¥{cost_info['total_cost_cny']})")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 连接失败: {str(e)}")
        return False

def test_thinking_mode():
    """测试 Thinking 模式（较长推理任务）"""
    print("\n" + "="*60)
    print("🧠 测试 2: Thinking 模式测试")
    print("="*60)
    
    api_key = os.getenv("CLAUDE_API_KEY")
    base_url = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")
    model = os.getenv("CLAUDE_MODEL_NAME", "claude-sonnet-4-5-20250929")
    max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))
    
    try:
        # OneChats 使用 OpenAI 兼容的 API
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 使用一个需要推理的问题
        test_prompt = """
请分析以下小说片段的叙事功能：

"张明推开门，屋内一片漆黑。他摸索着找到开关，灯光亮起的瞬间，他看到了桌上那封信。"

请从以下角度分析：
1. 情节推进作用
2. 氛围营造
3. 人物塑造
"""
        
        print(f"📤 发送推理任务...")
        print(f"   任务: 叙事功能分析")
        print(f"   最大 tokens: {max_tokens}")
        
        start_time = datetime.now()
        
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{
                "role": "user",
                "content": test_prompt
            }]
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ 推理完成!")
        print(f"   耗时: {duration:.2f} 秒")
        print(f"\n📊 响应内容:")
        print("-" * 60)
        print(response.choices[0].message.content)
        print("-" * 60)
        
        # 计算费用
        cost_info = calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )
        
        print(f"\n💰 费用统计:")
        print(f"   输入 tokens: {cost_info['input_tokens']}")
        print(f"   输出 tokens: {cost_info['output_tokens']}")
        print(f"   本次费用: ${cost_info['total_cost_usd']} (≈ ¥{cost_info['total_cost_cny']})")
        print(f"   平均速度: {cost_info['output_tokens']/duration:.1f} tokens/秒")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False

def test_with_project_config():
    """测试使用项目配置"""
    print("\n" + "="*60)
    print("⚙️  测试 3: 项目配置集成测试")
    print("="*60)
    
    try:
        from src.core.config import config
        
        print(f"📋 当前配置:")
        print(f"   LLM Provider: {config.llm.provider}")
        print(f"   Model: {config.llm.model_name}")
        print(f"   Base URL: {config.llm.base_url}")
        
        if config.llm.provider != "claude":
            print(f"\n⚠️  注意: 当前 LLM_PROVIDER 设置为 '{config.llm.provider}'")
            print(f"   如需测试 Claude，请在 .env 中设置: LLM_PROVIDER=claude")
            return False
        
        provider_config = config.llm.get_provider_config()
        
        print(f"\n📦 完整配置:")
        print(json.dumps(
            {k: v for k, v in provider_config.items() if k != "api_key"},
            indent=2,
            ensure_ascii=False
        ))
        
        print(f"\n✅ 配置加载成功!")
        print(f"   您可以在代码中直接使用 config.llm 来访问 Claude 配置")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 配置加载失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 Claude Sonnet 4.5 Thinking 模型测试")
    print("="*60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查环境变量
    if not os.path.exists(project_root / ".env"):
        print("\n⚠️  警告: .env 文件不存在")
        print("请按以下步骤创建:")
        print("1. 复制 .env.example 为 .env")
        print("2. 确保 CLAUDE_API_KEY 已正确配置")
        print("3. 设置 LLM_PROVIDER=claude")
        return
    
    results = []
    
    # 测试 1: 基础连接
    results.append(("基础连接", test_basic_connection()))
    
    # 测试 2: Thinking 模式
    if results[0][1]:  # 只有连接成功才继续
        results.append(("Thinking 模式", test_thinking_mode()))
    
    # 测试 3: 项目配置
    results.append(("项目配置集成", test_with_project_config()))
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！Claude 配置成功！")
        print("\n📝 下一步:")
        print("   1. 在 .env 中设置 LLM_PROVIDER=claude 启用 Claude")
        print("   2. 运行您的主程序，系统将自动使用 Claude")
        print("   3. 随时可切换回 DeepSeek (LLM_PROVIDER=deepseek)")
    else:
        print("\n⚠️  部分测试未通过，请检查配置")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
