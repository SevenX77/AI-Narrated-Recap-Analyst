import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class LLMConfig:
    """
    LLM配置类，支持多个LLM提供商（DeepSeek、Claude等）
    通过环境变量 LLM_PROVIDER 控制当前使用的提供商
    """
    # LLM 提供商选择: deepseek | claude
    provider: str = os.getenv("LLM_PROVIDER", "deepseek")
    
    # DeepSeek 配置
    deepseek_api_key: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model_name: str = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
    
    # Claude 配置
    claude_api_key: Optional[str] = os.getenv("CLAUDE_API_KEY")
    claude_base_url: str = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com")
    claude_model_name: str = os.getenv("CLAUDE_MODEL_NAME", "claude-sonnet-4-5-20250929")
    claude_max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))
    claude_temperature: float = float(os.getenv("CLAUDE_TEMPERATURE", "1.0"))
    
    # 双模型支持（DeepSeek）：R1为主（阅读理解优先），V3 Fallback
    primary_model: str = "deepseek-reasoner"  # DeepSeek R1（主模型，用于阅读理解任务）
    fallback_model: str = "deepseek-chat"  # DeepSeek V3（备用，当R1不可用时）
    enable_fallback: bool = True  # 启用自动回退
    
    # Fallback 触发条件
    fallback_on_error: bool = True  # 遇到错误时回退
    fallback_on_validation_fail: bool = True  # 验证失败时回退
    
    @property
    def api_key(self) -> Optional[str]:
        """根据当前provider返回对应的API Key"""
        if self.provider == "claude":
            return self.claude_api_key
        return self.deepseek_api_key
    
    @property
    def base_url(self) -> str:
        """根据当前provider返回对应的Base URL"""
        if self.provider == "claude":
            return self.claude_base_url
        return self.deepseek_base_url
    
    @property
    def model_name(self) -> str:
        """根据当前provider返回对应的模型名称"""
        if self.provider == "claude":
            return self.claude_model_name
        return self.deepseek_model_name
    
    @property
    def model(self) -> str:
        """Alias for model_name for backward compatibility"""
        return self.model_name
    
    def get_provider_config(self) -> dict:
        """获取当前provider的完整配置"""
        if self.provider == "claude":
            return {
                "provider": "claude",
                "api_key": self.claude_api_key,
                "base_url": self.claude_base_url,
                "model_name": self.claude_model_name,
                "max_tokens": self.claude_max_tokens,
                "temperature": self.claude_temperature,
            }
        else:  # deepseek
            return {
                "provider": "deepseek",
                "api_key": self.deepseek_api_key,
                "base_url": self.deepseek_base_url,
                "model_name": self.deepseek_model_name,
                "primary_model": self.primary_model,
                "fallback_model": self.fallback_model,
                "enable_fallback": self.enable_fallback,
            }

@dataclass
class IngestionConfig:
    """
    数据摄入与对齐流程的配置
    """
    # 动态章节提取策略
    initial_chapter_multiplier: int = 2  # 初始提取章节数 = SRT数量 × 此倍数
    batch_size: int = 10  # 每批提取的章节数
    safety_buffer_chapters: int = 10  # 安全缓冲：最后再提取的章节数
    
    # 质量评估阈值
    quality_threshold: float = 70.0  # 对齐质量合格分数
    min_coverage_ratio: float = 0.8  # 最小整体覆盖率
    min_episode_coverage: float = 0.6  # 单集最小覆盖率
    
    # 并发控制
    max_concurrent_requests: int = 10  # 最大并发LLM请求数
    enable_concurrent: bool = True  # 是否启用并发

@dataclass
class AppConfig:
    llm: LLMConfig = LLMConfig()
    ingestion: IngestionConfig = IngestionConfig()
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Paths
    base_dir: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logs_dir: str = os.getenv("LOGS_DIR", os.path.join(base_dir, "logs"))
    data_dir: str = os.getenv("DATA_DIR", os.path.join(base_dir, "data"))
    analysis_source_dir: str = os.getenv("ANALYSIS_SOURCE_DIR", os.path.join(base_dir, "分析资料"))

# Global Config Instance
config = AppConfig()
