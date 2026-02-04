import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    api_key: Optional[str] = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model_name: str = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")

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
