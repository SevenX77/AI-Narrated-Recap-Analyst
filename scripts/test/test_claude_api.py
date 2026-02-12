"""
测试Claude API连通性
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm_client_manager import get_llm_client, get_model_name
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def test_claude_api():
    """测试Claude API是否正常工作"""
    print("=" * 80)
    print("🧪 测试Claude API连通性")
    print("=" * 80)
    
    # 检查环境变量
    api_key = os.getenv("CLAUDE_API_KEY")
    base_url = os.getenv("CLAUDE_BASE_URL")
    model_name = os.getenv("CLAUDE_MODEL_NAME")
    
    print(f"\n📋 环境变量检查:")
    print(f"  CLAUDE_API_KEY: {'✅ 已设置' if api_key else '❌ 未设置'}")
    print(f"  CLAUDE_BASE_URL: {base_url}")
    print(f"  CLAUDE_MODEL_NAME: {model_name}")
    
    if not api_key:
        print("\n❌ Claude API Key未设置！")
        return False
    
    try:
        # 获取Claude客户端
        print(f"\n🔌 连接Claude API...")
        client = get_llm_client("claude")
        model = get_model_name("claude")
        
        print(f"  ✅ 客户端初始化成功")
        print(f"  📦 使用模型: {model}")
        
        # 发送测试请求
        print(f"\n📤 发送测试请求...")
        response = client.chat.completions.create(
            model=model,
            max_tokens=50,
            messages=[
                {"role": "user", "content": "请用一句话回复：你好，这是一个API连通性测试。"}
            ]
        )
        
        # 提取响应
        reply = response.choices[0].message.content
        
        print(f"\n✅ API调用成功！")
        print(f"\n📨 响应内容:")
        print(f"  {reply}")
        
        # Token使用情况
        if hasattr(response, 'usage') and response.usage:
            print(f"\n📊 Token使用:")
            print(f"  输入: {response.usage.prompt_tokens}")
            print(f"  输出: {response.usage.completion_tokens}")
            print(f"  总计: {response.usage.total_tokens}")
        
        print("\n" + "=" * 80)
        print("✅ Claude API 工作正常！")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ API调用失败！")
        print(f"\n错误信息:")
        print(f"  {str(e)}")
        
        # 详细错误信息
        import traceback
        print(f"\n详细堆栈:")
        traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("❌ Claude API 调用失败")
        print("=" * 80)
        
        # 常见问题排查
        print("\n🔍 可能的原因:")
        error_msg = str(e).lower()
        
        if "403" in error_msg or "forbidden" in error_msg:
            print("  • API Key无效或权限不足")
            print("  • API配额已用完")
            print("  • IP被限制")
        elif "429" in error_msg or "rate limit" in error_msg:
            print("  • 触发API限流")
            print("  • 请求过于频繁")
        elif "timeout" in error_msg:
            print("  • 网络超时")
            print("  • Base URL不可达")
        elif "connection" in error_msg:
            print("  • 网络连接问题")
            print("  • 检查Base URL是否正确")
        else:
            print("  • 请查看上方详细错误信息")
        
        return False


if __name__ == "__main__":
    success = test_claude_api()
    exit(0 if success else 1)
