from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging

# 导入统一异常（延迟导入避免循环依赖）
# from src.core.exceptions import ToolExecutionError, ValidationError

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Context:
    """
    Shared context object passed between Agents and Workflows.
    Stores global state, configuration, and intermediate results.
    """
    data: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

class BaseTool(ABC):
    """
    Abstract Base Class for Tools.
    Tools are stateless, atomic operations.
    """
    name: str = "base_tool"
    description: str = "Base tool description"

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool's main logic.
        """
        pass

    def validate_inputs(self, **kwargs) -> bool:
        """
        Optional: Validate inputs before execution.
        """
        return True

class BaseAgent(ABC):
    """
    Abstract Base Class for Agents.
    Agents are stateful entities that use LLMs or complex logic to make decisions.
    """
    name: str = "base_agent"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool):
        """Register a tool for the agent to use."""
        self.tools[tool.name] = tool
        logger.info(f"Agent {self.name} registered tool: {tool.name}")

    @abstractmethod
    async def process(self, context: Context, **kwargs) -> Any:
        """
        Main processing logic for the agent.
        """
        pass

class BaseWorkflow(ABC):
    """
    Abstract Base Class for Workflows.
    Workflows orchestrate the execution of Agents and Tools.
    """
    name: str = "base_workflow"

    def __init__(self):
        self.context = Context()
        self.agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        self.agents[agent.name] = agent

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """
        Entry point for the workflow.
        """
        pass
