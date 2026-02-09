"""
快速测试 DeepSeek API 连通性
用于验证 API Key 是否有效，以及基本的对话功能
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from openai import OpenAI
from src.core.config import config


def test_api_connection():
    """测试 API 连通性"""
    print("\n" + "🔍" * 40)
    print("  DeepSeek API 快速连通性测试")
    print("🔍" * 40)
    
    # 1. 检查配置
    print("\n📋 步骤 1/3: 检查配置\n")
    
    api_key = config.llm.api_key
    base_url = config.llm.base_url
    model_name = config.llm.model_name
    provider = config.llm.provider
    
    print(f"  Provider: {provider}")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model_name}")
    
    if not api_key:
        print("\n❌ 错误：未找到 API Key")
        print("请在 .env 文件中设置：DEEPSEEK_API_KEY=sk-xxxxx")
        return False
    
    print(f"  API Key: {api_key[:10]}...{api_key[-4:]}")
    print("  ✅ 配置检查通过")
    
    # 2. 创建客户端
    print("\n📋 步骤 2/3: 创建 API 客户端\n")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        print("  ✅ 客户端创建成功")
    except Exception as e:
        print(f"  ❌ 客户端创建失败: {e}")
        return False
    
    # 3. 发送测试请求
    print("\n📋 步骤 3/3: 发送测试请求\n")
    print("  🔄 正在调用 DeepSeek API...\n")
    
    test_message = "你好！请用一句话介绍你自己，包括你的模型名称和主要能力。"
    
    try:
        start_time = datetime.now()
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": test_message}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 获取响应
        reply = response.choices[0].message.content
        
        # 显示结果
        print("  ✅ API 调用成功！\n")
        print("="*80)
        print("  📝 测试对话")
        print("="*80)
        print(f"\n【用户】: {test_message}\n")
        print(f"【AI】: {reply}\n")
        print("="*80)
        
        # 显示统计信息
        print(f"\n📊 调用统计:\n")
        print(f"  ⏱️  响应时间: {duration:.2f} 秒")
        
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"  📈 Token 使用:")
            print(f"     - Prompt Tokens: {usage.prompt_tokens}")
            print(f"     - Completion Tokens: {usage.completion_tokens}")
            print(f"     - Total Tokens: {usage.total_tokens}")
        
        print("\n✅ DeepSeek API 工作正常！")
        return True
        
    except Exception as e:
        print(f"  ❌ API 调用失败\n")
        print(f"错误信息: {e}")
        print("\n可能的原因:")
        print("  1. API Key 无效或已过期")
        print("  2. 网络连接问题")
        print("  3. API 额度不足")
        print("  4. Base URL 配置错误")
        
        import traceback
        print(f"\n详细错误信息:\n{traceback.format_exc()}")
        return False


def main():
    """主函数"""
    success = test_api_connection()
    
    print("\n" + "="*80)
    if success:
        print("  🎉 测试完成：API 连接正常")
        print("="*80)
        print("\n您现在可以:")
        print("  - 运行主程序进行完整的分析任务")
        print("  - 使用 test_deepseek_r1.py 测试推理能力")
        print("  - 使用 test_deepseek_stability.py 测试稳定性")
    else:
        print("  ❌ 测试失败：请检查配置")
        print("="*80)
        print("\n排查步骤:")
        print("  1. 检查 .env 文件中的 DEEPSEEK_API_KEY")
        print("  2. 确认 API Key 格式正确（以 sk- 开头）")
        print("  3. 访问 DeepSeek 官网确认账户状态")
        print("  4. 检查网络连接是否正常")
    
    print("\n")
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
