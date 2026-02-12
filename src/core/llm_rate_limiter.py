"""
LLM调用限流管理器

提供统一的LLM调用限流、重试、并发控制机制。
支持不同模型的不同限流规则。
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LLMRateLimitConfig:
    """
    LLM提供商的限流配置
    
    Attributes:
        provider: 提供商名称（如 'anthropic', 'deepseek', 'openai'）
        model: 模型名称（如 'claude-3-5-sonnet-20241022'）
        
        # 限流规则
        requests_per_minute: 每分钟最大请求数（QPM）
        requests_per_day: 每天最大请求数（QPD）
        tokens_per_minute: 每分钟最大token数（TPM）
        tokens_per_day: 每天最大token数（TPD）
        
        # 并发控制
        max_concurrent: 最大并发请求数
        
        # 重试策略
        max_retries: 最大重试次数
        base_retry_delay: 基础重试延迟（秒）
        max_retry_delay: 最大重试延迟（秒）
        
        # 错误码识别
        rate_limit_errors: 识别为限流的错误码列表
    """
    provider: str
    model: str
    
    # 限流规则（None表示不限制）
    requests_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    tokens_per_day: Optional[int] = None
    
    # 并发控制
    max_concurrent: int = 1
    
    # 重试策略
    max_retries: int = 3
    base_retry_delay: float = 2.0
    max_retry_delay: float = 60.0
    
    # 错误码识别
    rate_limit_errors: list = field(default_factory=lambda: ["403", "429", "rate limit", "too many requests"])
    
    # 测试状态
    is_tested: bool = False
    last_test_date: Optional[str] = None
    test_notes: str = ""


# 预定义的LLM限流配置
DEFAULT_LLM_CONFIGS = {
    "anthropic_claude": LLMRateLimitConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        requests_per_minute=50,  # 需要测试验证
        requests_per_day=None,
        tokens_per_minute=40000,  # 需要测试验证
        max_concurrent=3,
        max_retries=3,
        base_retry_delay=2.0,
        is_tested=False,
        test_notes="默认配置，待测试验证"
    ),
    
    "deepseek_chat": LLMRateLimitConfig(
        provider="deepseek",
        model="deepseek-chat",
        requests_per_minute=60,  # 需要测试验证
        requests_per_day=None,
        tokens_per_minute=None,
        max_concurrent=2,
        max_retries=3,
        base_retry_delay=3.0,
        is_tested=False,
        test_notes="默认配置，待测试验证"
    ),
    
    "openai_gpt4": LLMRateLimitConfig(
        provider="openai",
        model="gpt-4",
        requests_per_minute=500,  # 付费账户
        requests_per_day=10000,
        tokens_per_minute=10000,
        max_concurrent=5,
        max_retries=3,
        base_retry_delay=1.0,
        is_tested=False,
        test_notes="付费账户配置"
    ),
    
    # 保守配置（用于未测试的模型）
    "conservative": LLMRateLimitConfig(
        provider="unknown",
        model="unknown",
        requests_per_minute=10,
        requests_per_day=None,
        tokens_per_minute=None,
        max_concurrent=1,
        max_retries=5,
        base_retry_delay=5.0,
        is_tested=False,
        test_notes="保守配置，用于未知模型"
    )
}


class RateLimiter:
    """
    限流器（滑动窗口算法）
    
    跟踪时间窗口内的请求数和token数，确保不超过限制。
    """
    
    def __init__(self, config: LLMRateLimitConfig):
        self.config = config
        
        # 请求时间戳队列（分钟级）
        self.minute_requests: deque = deque()
        
        # 请求时间戳队列（天级）
        self.day_requests: deque = deque()
        
        # Token使用记录
        self.minute_tokens: deque = deque()
        self.day_tokens: deque = deque()
        
        # 并发控制
        self.current_concurrent = 0
        self.concurrent_lock = asyncio.Lock()
    
    async def acquire(self, estimated_tokens: int = 1000) -> bool:
        """
        请求获取执行权限
        
        Args:
            estimated_tokens: 预估的token使用量
        
        Returns:
            是否获得执行权限
        """
        now = time.time()
        
        # 清理过期记录
        self._cleanup_old_records(now)
        
        # 检查并发限制
        if self.current_concurrent >= self.config.max_concurrent:
            logger.debug(f"并发数达到上限: {self.current_concurrent}/{self.config.max_concurrent}")
            return False
        
        # 检查QPM限制
        if self.config.requests_per_minute:
            if len(self.minute_requests) >= self.config.requests_per_minute:
                logger.debug(f"QPM限制: {len(self.minute_requests)}/{self.config.requests_per_minute}")
                return False
        
        # 检查QPD限制
        if self.config.requests_per_day:
            if len(self.day_requests) >= self.config.requests_per_day:
                logger.warning(f"QPD限制: {len(self.day_requests)}/{self.config.requests_per_day}")
                return False
        
        # 检查TPM限制
        if self.config.tokens_per_minute:
            current_minute_tokens = sum(tokens for _, tokens in self.minute_tokens)
            if current_minute_tokens + estimated_tokens > self.config.tokens_per_minute:
                logger.debug(f"TPM限制: {current_minute_tokens + estimated_tokens}/{self.config.tokens_per_minute}")
                return False
        
        # 检查TPD限制
        if self.config.tokens_per_day:
            current_day_tokens = sum(tokens for _, tokens in self.day_tokens)
            if current_day_tokens + estimated_tokens > self.config.tokens_per_day:
                logger.warning(f"TPD限制: {current_day_tokens + estimated_tokens}/{self.config.tokens_per_day}")
                return False
        
        # 记录请求
        self.minute_requests.append(now)
        self.day_requests.append(now)
        self.minute_tokens.append((now, estimated_tokens))
        self.day_tokens.append((now, estimated_tokens))
        
        # 增加并发计数
        async with self.concurrent_lock:
            self.current_concurrent += 1
        
        return True
    
    async def release(self):
        """释放执行权限"""
        async with self.concurrent_lock:
            self.current_concurrent = max(0, self.current_concurrent - 1)
    
    def _cleanup_old_records(self, now: float):
        """清理过期的记录"""
        # 清理分钟级记录（保留60秒内）
        minute_ago = now - 60
        while self.minute_requests and self.minute_requests[0] < minute_ago:
            self.minute_requests.popleft()
        while self.minute_tokens and self.minute_tokens[0][0] < minute_ago:
            self.minute_tokens.popleft()
        
        # 清理天级记录（保留24小时内）
        day_ago = now - 86400
        while self.day_requests and self.day_requests[0] < day_ago:
            self.day_requests.popleft()
        while self.day_tokens and self.day_tokens[0][0] < day_ago:
            self.day_tokens.popleft()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        now = time.time()
        self._cleanup_old_records(now)
        
        return {
            "current_concurrent": self.current_concurrent,
            "requests_last_minute": len(self.minute_requests),
            "requests_last_day": len(self.day_requests),
            "tokens_last_minute": sum(tokens for _, tokens in self.minute_tokens),
            "tokens_last_day": sum(tokens for _, tokens in self.day_tokens),
        }


class LLMCallManager:
    """
    LLM调用管理器
    
    统一管理所有LLM调用，提供限流、重试、并发控制。
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
        """
        self.config_file = config_file or "config/llm_configs.json"
        self.configs: Dict[str, LLMRateLimitConfig] = {}
        self.limiters: Dict[str, RateLimiter] = {}
        
        # 加载配置
        self._load_configs()
        
        # 初始化限流器
        for key, config in self.configs.items():
            self.limiters[key] = RateLimiter(config)
        
        logger.info(f"✅ LLMCallManager初始化完成，加载{len(self.configs)}个配置")
    
    def _load_configs(self):
        """加载配置文件"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for key, config_dict in data.items():
                    self.configs[key] = LLMRateLimitConfig(**config_dict)
                
                logger.info(f"📂 从{config_path}加载配置")
            except Exception as e:
                logger.warning(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
                self.configs = DEFAULT_LLM_CONFIGS.copy()
        else:
            logger.info("📂 配置文件不存在，使用默认配置")
            self.configs = DEFAULT_LLM_CONFIGS.copy()
            self._save_configs()
    
    def _save_configs(self):
        """保存配置到文件"""
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for key, config in self.configs.items():
            data[key] = {
                "provider": config.provider,
                "model": config.model,
                "requests_per_minute": config.requests_per_minute,
                "requests_per_day": config.requests_per_day,
                "tokens_per_minute": config.tokens_per_minute,
                "tokens_per_day": config.tokens_per_day,
                "max_concurrent": config.max_concurrent,
                "max_retries": config.max_retries,
                "base_retry_delay": config.base_retry_delay,
                "max_retry_delay": config.max_retry_delay,
                "rate_limit_errors": config.rate_limit_errors,
                "is_tested": config.is_tested,
                "last_test_date": config.last_test_date,
                "test_notes": config.test_notes
            }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 配置已保存到{config_path}")
    
    def get_config(self, provider: str, model: str) -> LLMRateLimitConfig:
        """
        获取指定模型的配置
        
        Args:
            provider: 提供商名称
            model: 模型名称
        
        Returns:
            限流配置
        """
        # 尝试精确匹配
        key = f"{provider}_{model}".replace("-", "_").replace(".", "_")
        if key in self.configs:
            return self.configs[key]
        
        # 尝试提供商匹配
        for config_key, config in self.configs.items():
            if config.provider == provider:
                logger.info(f"使用{provider}的通用配置")
                return config
        
        # 使用保守配置
        logger.warning(f"⚠️ 未找到{provider}/{model}的配置，使用保守配置")
        return self.configs.get("conservative", DEFAULT_LLM_CONFIGS["conservative"])
    
    async def call_with_rate_limit(
        self,
        func: Callable,
        provider: str,
        model: str,
        estimated_tokens: int = 1000,
        *args,
        **kwargs
    ) -> Any:
        """
        带限流控制的LLM调用
        
        Args:
            func: 要调用的函数
            provider: 提供商名称
            model: 模型名称
            estimated_tokens: 预估token使用量
            *args, **kwargs: 传递给func的参数
        
        Returns:
            函数执行结果
        """
        config = self.get_config(provider, model)
        limiter = self.limiters.get(
            f"{provider}_{model}".replace("-", "_").replace(".", "_"),
            RateLimiter(config)
        )
        
        # 等待获取执行权限
        while not await limiter.acquire(estimated_tokens):
            wait_time = min(5.0, config.base_retry_delay)
            logger.debug(f"⏳ 等待限流释放...{wait_time}秒")
            await asyncio.sleep(wait_time)
        
        try:
            # 执行函数（带重试）
            result = await self._execute_with_retry(
                func, config, *args, **kwargs
            )
            return result
        
        finally:
            # 释放执行权限
            await limiter.release()
    
    async def _execute_with_retry(
        self,
        func: Callable,
        config: LLMRateLimitConfig,
        *args,
        **kwargs
    ) -> Any:
        """
        带重试的执行
        
        Args:
            func: 要执行的函数
            config: 限流配置
            *args, **kwargs: 传递给func的参数
        
        Returns:
            函数执行结果
        """
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                # 执行函数
                result = func(*args, **kwargs)
                return result
            
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # 检测是否是限流错误
                is_rate_limit = any(
                    err_code in error_msg
                    for err_code in config.rate_limit_errors
                )
                
                if attempt < config.max_retries:
                    # 计算延迟（指数退避）
                    delay = min(
                        config.base_retry_delay * (2 ** attempt),
                        config.max_retry_delay
                    )
                    
                    # 如果是限流错误，增加额外延迟
                    if is_rate_limit:
                        delay *= 2
                        logger.warning(f"🚫 检测到API限流")
                    
                    logger.warning(
                        f"⚠️ 执行失败（第{attempt + 1}/{config.max_retries + 1}次尝试）: {error_msg[:100]}"
                    )
                    logger.info(f"⏳ 等待{delay:.1f}秒后重试...")
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ 重试{config.max_retries}次后仍然失败")
        
        raise last_exception
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有限流器的统计信息"""
        stats = {}
        for key, limiter in self.limiters.items():
            stats[key] = limiter.get_stats()
        return stats
    
    def update_config(self, key: str, **kwargs):
        """
        更新配置
        
        Args:
            key: 配置键
            **kwargs: 要更新的配置项
        """
        if key in self.configs:
            config = self.configs[key]
            for k, v in kwargs.items():
                if hasattr(config, k):
                    setattr(config, k, v)
            
            self._save_configs()
            logger.info(f"✅ 配置{key}已更新")
        else:
            logger.warning(f"⚠️ 配置{key}不存在")


# 全局单例
_global_manager: Optional[LLMCallManager] = None


def get_llm_manager() -> LLMCallManager:
    """获取全局LLM调用管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = LLMCallManager()
    return _global_manager
