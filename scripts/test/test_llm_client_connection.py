"""
测试LLM client连接
验证API密钥配置和网络连接
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_llm_connection():
    """测试LLM client连接"""
    print("=" * 80)
    print("测试LLM Client连接")
    print("=" * 80)
    
    # 测试1: 导入配置
    print("\n[1/4] 导入配置...")
    try:
        from src.core.config import config
        print(f"✅ 配置导入成功")
        print(f"  - DeepSeek API Key: {config.llm.deepseek_api_key[:20]}...")
        print(f"  - DeepSeek Base URL: {config.llm.deepseek_base_url}")
        print(f"  - Claude API Key: {config.llm.claude_api_key[:20]}...")
        print(f"  - Claude Base URL: {config.llm.claude_base_url}")
    except Exception as e:
        print(f"❌ 配置导入失败: {e}")
        return
    
    # 测试2: 初始化LLM client
    print("\n[2/4] 初始化LLM client...")
    try:
        from src.core.llm_client_manager import get_llm_client, get_model_name
        
        # 初始化DeepSeek client
        deepseek_client = get_llm_client("deepseek")
        deepseek_model = get_model_name("deepseek")
        print(f"✅ DeepSeek client初始化成功")
        print(f"  - Model: {deepseek_model}")
    except Exception as e:
        print(f"❌ DeepSeek client初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试3: 简单API调用
    print("\n[3/4] 测试简单API调用...")
    try:
        response = deepseek_client.chat.completions.create(
            model=deepseek_model,
            messages=[
                {"role": "user", "content": "请用一句话回复：你好"}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        print(f"✅ API调用成功")
        print(f"  - 响应: {content}")
        print(f"  - Tokens: {response.usage.total_tokens if response.usage else 'N/A'}")
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试4: 验证SrtTextExtractor初始化
    print("\n[4/4] 测试SrtTextExtractor初始化...")
    try:
        from src.tools.srt_text_extractor import SrtTextExtractor
        
        extractor = SrtTextExtractor(use_llm=True, provider="deepseek")
        print(f"✅ SrtTextExtractor初始化成功")
        print(f"  - use_llm: {extractor.use_llm}")
        print(f"  - provider: {extractor.provider}")
        print(f"  - llm_client: {extractor.llm_client is not None}")
        print(f"  - model_name: {extractor.model_name}")
    except Exception as e:
        print(f"❌ SrtTextExtractor初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("🎉 所有测试通过！LLM连接正常")
    print("=" * 80)


if __name__ == "__main__":
    test_llm_connection()
