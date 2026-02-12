from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class WorkflowType(str, Enum):
    """工作流类型"""
    NOVEL_PROCESSING = "novel_processing"
    SCRIPT_PROCESSING = "script_processing"
    ALIGNMENT = "alignment"

class WorkflowConfig(BaseModel):
    """工作流配置"""
    llm_provider: str = Field("claude", description="LLM提供商")
    llm_model: str = Field("claude-3-5-sonnet-20241022", description="LLM模型")
    max_concurrency: int = Field(10, ge=1, le=50, description="最大并发数")
    enable_system_analysis: bool = Field(True, description="是否启用体系分析")
    enable_functional_tags: bool = Field(False, description="是否启用功能性标签")

class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求"""
    workflow_type: WorkflowType = Field(..., description="工作流类型")
    project_id: str = Field(..., description="项目ID")
    config: Optional[WorkflowConfig] = Field(None, description="工作流配置")

class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowResponse(BaseModel):
    """工作流响应"""
    task_id: str = Field(..., description="任务ID")
    status: WorkflowStatus = Field(..., description="任务状态")
    workflow_type: str = Field(..., description="工作流类型")
    project_id: str = Field(..., description="项目ID")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="进度(0-1)")
    message: Optional[str] = Field(None, description="状态消息")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
