from typing import Any
from src.core.interfaces import BaseAgent, Context
from src.core.schemas import SceneAnalysis
from src.core.schemas_writer import Script

class WriterAgent(BaseAgent):
    """
    Base Writer Agent defining the interface for script generation.
    """
    def __init__(self, client: Any = None, model_name: str = "deepseek-chat"):
        super().__init__()
        self.client = client
        self.model_name = model_name

    async def process(self, context: Context, **kwargs) -> Any:
        # Default implementation or routing logic
        pass

    def generate_script(self, analysis: SceneAnalysis, style: str = "first_person") -> Script:
        """
        Generate a script based on scene analysis.
        """
        raise NotImplementedError
