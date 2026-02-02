from typing import List, Dict, Any
from src.core.schemas import AlignmentItem

class AlignmentEngine:
    def __init__(self, client: Any, model_name: str = "deepseek-chat"):
        self.client = client
        self.model_name = model_name

    def align_script_with_novel(self, novel_events: List[Dict], script_events: List[Dict]) -> List[AlignmentItem]:
        """
        对齐解说文案和小说原文
        """
        raise NotImplementedError
