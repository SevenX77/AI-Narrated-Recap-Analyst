"""
LLM Client Manager
统一管理多个 LLM Provider 的客户端实例

职责：
1. 为不同的 Provider（Claude、DeepSeek）创建和管理 OpenAI 客户端
2. 单例模式：同一个 Provider 复用客户端实例
3. 使用统计：记录各 Provider 的调用次数和 Token 消耗
"""

import logging
from typing import Dict, Optional, Literal
from openai import OpenAI

from src.core.config import config

logger = logging.getLogger(__name__)

# Provider 类型定义
ProviderType = Literal["claude", "deepseek"]


class LLMClientManager:
    """
    LLM 客户端管理器（单例模式）
    
    Example:
        >>> from src.core.llm_client_manager import get_llm_client
        >>> 
        >>> # 获取 Claude 客户端
        >>> claude_client = get_llm_client("claude")
        >>> 
        >>> # 获取 DeepSeek 客户端
        >>> deepseek_client = get_llm_client("deepseek")
    """
    
    # 客户端缓存
    _clients: Dict[str, OpenAI] = {}
    
    # 使用统计
    _usage_stats: Dict[str, Dict[str, int]] = {}
    
    @classmethod
    def get_client(cls, provider: ProviderType) -> OpenAI:
        """
        获取指定 Provider 的 OpenAI 客户端
        
        Args:
            provider: LLM Provider 名称
                - "claude": 使用 Claude API
                - "deepseek": 使用 DeepSeek API
        
        Returns:
            OpenAI 客户端实例（兼容 OpenAI SDK）
        
        Raises:
            ValueError: 当 Provider 未知或 API Key 未配置时
        """
        # 检查缓存
        if provider in cls._clients:
            logger.debug(f"Reusing cached client for provider: {provider}")
            return cls._clients[provider]
        
        # 创建新客户端
        logger.info(f"Creating new LLM client for provider: {provider}")
        
        if provider == "claude":
            api_key = config.llm.claude_api_key
            base_url = config.llm.claude_base_url
            
            if not api_key:
                raise ValueError(
                    "Claude API Key not configured. "
                    "Please set CLAUDE_API_KEY in .env file"
                )
            
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            logger.info(f"✅ Claude client created (base_url: {base_url})")
            
        elif provider == "deepseek":
            api_key = config.llm.deepseek_api_key
            base_url = config.llm.deepseek_base_url
            
            if not api_key:
                raise ValueError(
                    "DeepSeek API Key not configured. "
                    "Please set DEEPSEEK_API_KEY in .env file"
                )
            
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            logger.info(f"✅ DeepSeek client created (base_url: {base_url})")
            
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: claude, deepseek"
            )
        
        # 缓存客户端
        cls._clients[provider] = client
        
        # 初始化使用统计
        cls._usage_stats[provider] = {
            "total_calls": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
        
        return client
    
    @classmethod
    def get_model_name(cls, provider: ProviderType) -> str:
        """
        获取指定 Provider 的默认模型名称
        
        Args:
            provider: LLM Provider 名称
        
        Returns:
            模型名称字符串
        """
        if provider == "claude":
            return config.llm.claude_model_name
        elif provider == "deepseek":
            return config.llm.deepseek_model_name
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @classmethod
    def record_usage(
        cls,
        provider: ProviderType,
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ):
        """
        记录 LLM 使用统计
        
        Args:
            provider: Provider 名称
            prompt_tokens: 输入 Token 数
            completion_tokens: 输出 Token 数
        """
        if provider not in cls._usage_stats:
            cls._usage_stats[provider] = {
                "total_calls": 0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0
            }
        
        stats = cls._usage_stats[provider]
        stats["total_calls"] += 1
        stats["prompt_tokens"] += prompt_tokens
        stats["completion_tokens"] += completion_tokens
        stats["total_tokens"] += (prompt_tokens + completion_tokens)
    
    @classmethod
    def get_usage_stats(cls, provider: Optional[ProviderType] = None) -> Dict:
        """
        获取使用统计
        
        Args:
            provider: 指定 Provider（None 则返回所有）
        
        Returns:
            使用统计字典
        """
        if provider:
            return cls._usage_stats.get(provider, {})
        return cls._usage_stats
    
    @classmethod
    def reset_stats(cls):
        """重置所有统计数据"""
        cls._usage_stats.clear()
        logger.info("Usage statistics reset")
    
    @classmethod
    def clear_cache(cls):
        """清除所有缓存的客户端"""
        cls._clients.clear()
        logger.info("Client cache cleared")


# ============================================================================
# 便捷函数
# ============================================================================

def get_llm_client(provider: ProviderType) -> OpenAI:
    """
    获取 LLM 客户端的快捷方式
    
    这是推荐的使用方式。
    
    Args:
        provider: "claude" | "deepseek"
    
    Returns:
        OpenAI 客户端实例
    
    Example:
        >>> from src.core.llm_client_manager import get_llm_client
        >>> client = get_llm_client("claude")
        >>> response = client.chat.completions.create(
        ...     model="claude-sonnet-4-5-20250929",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    return LLMClientManager.get_client(provider)


def get_model_name(provider: ProviderType) -> str:
    """
    获取指定 Provider 的默认模型名称
    
    Args:
        provider: "claude" | "deepseek"
    
    Returns:
        模型名称
    
    Example:
        >>> from src.core.llm_client_manager import get_model_name
        >>> model = get_model_name("claude")
        >>> print(model)  # "claude-sonnet-4-5-20250929"
    """
    return LLMClientManager.get_model_name(provider)


def record_llm_usage(
    provider: ProviderType,
    prompt_tokens: int = 0,
    completion_tokens: int = 0
):
    """
    记录 LLM 使用情况
    
    Args:
        provider: Provider 名称
        prompt_tokens: 输入 Token 数
        completion_tokens: 输出 Token 数
    """
    LLMClientManager.record_usage(provider, prompt_tokens, completion_tokens)
