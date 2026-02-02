from typing import List, Any
from src.core.schemas import SceneAnalysis, NarrativeEvent

# --- Base Agent Class ---

class AnalystAgent:
    def __init__(self, client: Any, model_name: str = "deepseek-chat"):
        self.client = client
        self.model_name = model_name

    def extract_events(self, text: str, context_id: str = "") -> List[NarrativeEvent]:
        """
        从文本中提取 SVO 事件流 (用于理解剧情)
        """
        raise NotImplementedError

    def analyze(self, text_chunk: str, previous_context: str = "") -> SceneAnalysis:
        """
        分析小说片段，提取生成解说所需的结构化信息
        """
        raise NotImplementedError
