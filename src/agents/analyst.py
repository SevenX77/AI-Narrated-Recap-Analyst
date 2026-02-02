from typing import List, Any, Dict, Optional
from src.core.schemas import SceneAnalysis, NarrativeEvent
from src.core.interfaces import BaseAgent, Context

# --- Base Agent Class ---

class AnalystAgent(BaseAgent):
    def __init__(self, client: Any, model_name: str = "deepseek-chat", config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.client = client
        self.model_name = model_name

    async def process(self, context: Context, **kwargs) -> Any:
        """
        Standard process method for BaseAgent compliance.
        """
        raise NotImplementedError("AnalystAgent does not implement generic process yet.")

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
