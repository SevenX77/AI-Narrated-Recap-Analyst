import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class LLMConfig:
    """
    LLM 配置类，支持多个 LLM 提供商（Claude、DeepSeek）
    
    注意：
    - 不再使用全局 LLM_PROVIDER 切换，工具层面按需选择 Provider
    - Temperature 等参数应在工具调用时设置，不做全局配置
    """
    # DeepSeek 配置
    deepseek_api_key: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    # DeepSeek 多模型支持
    deepseek_v32_model: str = os.getenv("DEEPSEEK_V32_MODEL", "deepseek-chat")  # v3.2 标准模型
    deepseek_v32_thinking_model: str = os.getenv("DEEPSEEK_V32_THINKING_MODEL", "deepseek-reasoner")  # v3.2 思维链模型
    deepseek_model_name: str = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")  # 默认使用 v3.2
    
    # Claude 配置
    claude_api_key: Optional[str] = os.getenv("CLAUDE_API_KEY")
    # 默认使用 OneChats 通用线路（全球加速、非流6000s超时）
    claude_base_url: str = os.getenv("CLAUDE_BASE_URL", "https://chatapi.onechats.ai/v1/")
    claude_model_name: str = os.getenv("CLAUDE_MODEL_NAME", "claude-sonnet-4-5-20250929")
    claude_max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

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
