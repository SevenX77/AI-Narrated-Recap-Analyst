"""
双 LLM Provider 测试脚本
验证 Claude 和 DeepSeek 同时使用的功能

测试内容：
1. LLMClientManager 基本功能
2. Claude API 连接
3. DeepSeek API 连接
4. 使用统计功能
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.llm_client_manager import (
    get_llm_client,
    get_model_name,
    LLMClientManager
)


def test_client_creation():
    """测试客户端创建"""
    print("\n" + "="*80)
    print("  测试 1: 客户端创建")
    print("="*80)
    
    # 测试 Claude
    print("\n📝 测试 Claude 客户端...")
    try:
        claude_client = get_llm_client("claude")
        claude_model = get_model_name("claude")
        print(f"  ✅ Claude 客户端创建成功")
        print(f"     模型: {claude_model}")
    except Exception as e:
        print(f"  ❌ Claude 客户端创建失败: {e}")
        return False
    
    # 测试 DeepSeek
    print("\n📝 测试 DeepSeek 客户端...")
    try:
        deepseek_client = get_llm_client("deepseek")
        deepseek_model = get_model_name("deepseek")
        print(f"  ✅ DeepSeek 客户端创建成功")
        print(f"     模型: {deepseek_model}")
    except Exception as e:
        print(f"  ❌ DeepSeek 客户端创建失败: {e}")
        print(f"\n  ⚠️  提示: 请在 .env 文件中配置 DEEPSEEK_API_KEY")
        print(f"     DEEPSEEK_API_KEY=sk-你的API密钥")
        return False
    
    # 验证单例模式
    print("\n📝 测试单例模式...")
    claude_client_2 = get_llm_client("claude")
    if claude_client is claude_client_2:
        print("  ✅ 单例模式正常（同一 provider 返回相同实例）")
    else:
        print("  ⚠️  警告: 单例模式可能未生效")
    
    return True


def test_claude_api():
    """测试 Claude API 调用"""
    print("\n" + "="*80)
    print("  测试 2: Claude API 调用")
    print("="*80)
    
    try:
        client = get_llm_client("claude")
        model = get_model_name("claude")
        
        print(f"\n🔄 调用 Claude API...")
        print(f"   模型: {model}")
        
        start_time = datetime.now()
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "请用一句话介绍你自己（20字以内）"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        reply = response.choices[0].message.content
        
        print(f"\n  ✅ Claude 调用成功")
        print(f"\n【AI回复】: {reply}")
        print(f"\n📊 统计:")
        print(f"   响应时间: {duration:.2f} 秒")
        if hasattr(response, 'usage'):
            print(f"   Prompt Tokens: {response.usage.prompt_tokens}")
            print(f"   Completion Tokens: {response.usage.completion_tokens}")
            print(f"   Total Tokens: {response.usage.total_tokens}")
            
            # 记录使用统计
            LLMClientManager.record_usage(
                "claude",
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
        
        return True
        
    except Exception as e:
        print(f"\n  ❌ Claude 调用失败")
        print(f"     错误: {e}")
        import traceback
        print(f"\n{traceback.format_exc()}")
        return False


def test_deepseek_api():
    """测试 DeepSeek API 调用"""
    print("\n" + "="*80)
    print("  测试 3: DeepSeek API 调用")
    print("="*80)
    
    try:
        client = get_llm_client("deepseek")
        model = get_model_name("deepseek")
        
        print(f"\n🔄 调用 DeepSeek API...")
        print(f"   模型: {model}")
        
        start_time = datetime.now()
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "请用一句话介绍你自己（20字以内）"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        reply = response.choices[0].message.content
        
        print(f"\n  ✅ DeepSeek 调用成功")
        print(f"\n【AI回复】: {reply}")
        print(f"\n📊 统计:")
        print(f"   响应时间: {duration:.2f} 秒")
        if hasattr(response, 'usage'):
            print(f"   Prompt Tokens: {response.usage.prompt_tokens}")
            print(f"   Completion Tokens: {response.usage.completion_tokens}")
            print(f"   Total Tokens: {response.usage.total_tokens}")
            
            # 记录使用统计
            LLMClientManager.record_usage(
                "deepseek",
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
        
        return True
        
    except Exception as e:
        print(f"\n  ❌ DeepSeek 调用失败")
        print(f"     错误: {e}")
        
        if "API key" in str(e) or "401" in str(e):
            print(f"\n  💡 提示: DeepSeek API Key 未配置或无效")
            print(f"     请访问: https://platform.deepseek.com/api_keys")
            print(f"     创建 API Key 后，在 .env 文件中配置：")
            print(f"     DEEPSEEK_API_KEY=sk-你的API密钥")
        
        import traceback
        print(f"\n{traceback.format_exc()}")
        return False


def test_usage_stats():
    """测试使用统计"""
    print("\n" + "="*80)
    print("  测试 4: 使用统计")
    print("="*80)
    
    stats = LLMClientManager.get_usage_stats()
    
    print("\n📊 当前会话使用统计:\n")
    
    for provider, data in stats.items():
        print(f"【{provider.upper()}】")
        print(f"  调用次数: {data.get('total_calls', 0)}")
        print(f"  总 Token: {data.get('total_tokens', 0)}")
        print(f"  输入 Token: {data.get('prompt_tokens', 0)}")
        print(f"  输出 Token: {data.get('completion_tokens', 0)}")
        print()


def main():
    """主测试流程"""
    print("\n" + "🔍" * 40)
    print("  双 LLM Provider 功能测试")
    print("🔍" * 40)
    print("\n目标:")
    print("  1. 验证 LLMClientManager 正常工作")
    print("  2. 测试 Claude 和 DeepSeek 同时可用")
    print("  3. 验证使用统计功能")
    
    results = {
        "client_creation": False,
        "claude_api": False,
        "deepseek_api": False
    }
    
    # 测试 1: 客户端创建
    results["client_creation"] = test_client_creation()
    
    if not results["client_creation"]:
        print("\n❌ 客户端创建失败，后续测试跳过")
        return False
    
    # 测试 2: Claude API
    results["claude_api"] = test_claude_api()
    
    # 测试 3: DeepSeek API
    results["deepseek_api"] = test_deepseek_api()
    
    # 测试 4: 使用统计
    test_usage_stats()
    
    # 总结
    print("\n" + "="*80)
    print("  📋 测试总结")
    print("="*80)
    
    print("\n测试结果:")
    print(f"  ✅ 客户端创建: {'通过' if results['client_creation'] else '失败'}")
    print(f"  {'✅' if results['claude_api'] else '❌'} Claude API: {'通过' if results['claude_api'] else '失败'}")
    print(f"  {'✅' if results['deepseek_api'] else '❌'} DeepSeek API: {'通过' if results['deepseek_api'] else '失败'}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 所有测试通过！双 LLM Provider 功能正常")
        print("\n您现在可以:")
        print("  - 在工具中自由选择 provider: get_llm_client('claude') 或 get_llm_client('deepseek')")
        print("  - NovelMetadataExtractor 默认使用 DeepSeek（简单任务）")
        print("  - NovelSegmenter 默认使用 Claude（复杂任务）")
    else:
        print("\n⚠️  部分测试未通过")
        if not results["deepseek_api"]:
            print("\n🔧 DeepSeek 配置指南:")
            print("  1. 访问: https://platform.deepseek.com/api_keys")
            print("  2. 注册/登录账号")
            print("  3. 创建新的 API Key")
            print("  4. 复制 API Key（格式：sk-xxx）")
            print("  5. 在 .env 文件中添加：")
            print("     DEEPSEEK_API_KEY=sk-你的API密钥")
    
    print("\n" + "="*80)
    print()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
