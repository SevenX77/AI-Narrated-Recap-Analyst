import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    api_key: Optional[str] = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model_name: str = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")

@dataclass
class AppConfig:
    llm: LLMConfig = LLMConfig()
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Paths
    base_dir: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir: str = os.getenv("OUTPUT_DIR", os.path.join(base_dir, "output"))
    data_dir: str = os.getenv("DATA_DIR", os.path.join(base_dir, "data"))
    analysis_source_dir: str = os.getenv("ANALYSIS_SOURCE_DIR", os.path.join(base_dir, "分析资料"))

# Global Config Instance
config = AppConfig()
