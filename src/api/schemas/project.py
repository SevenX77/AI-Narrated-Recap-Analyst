from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str = Field(..., description="项目名称")

class ProjectCreate(ProjectBase):
    """创建项目请求"""
    description: Optional[str] = Field(None, description="项目描述")

class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")

class ProjectResponse(ProjectBase):
    """项目响应模型 - 支持 V1 和 V2"""
    id: str = Field(..., description="项目ID")
    description: Optional[str] = Field(None, description="项目描述")
    status: str = Field(..., description="项目状态")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    
    # V2 新增字段（可选）
    sources: Optional[Dict[str, Any]] = Field(None, description="源文件信息")
    workflow_stages: Optional[Dict[str, Any]] = Field(None, description="工作流阶段")
    stats: Optional[Dict[str, Any]] = Field(None, description="统计信息")
    
    # V1 旧字段（兼容）
    source_path: Optional[str] = Field(None, description="源文件路径 (V1)")
    initialized_at: Optional[str] = Field(None, description="初始化时间 (V1)")

    class Config:
        from_attributes = True

class ProjectList(BaseModel):
    """项目列表响应"""
    projects: List[ProjectResponse]
    total: int

class ProjectStats(BaseModel):
    """项目统计信息"""
    total_projects: int
    initialized: int
    discovered: int
