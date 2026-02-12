from fastapi import APIRouter, HTTPException
from src.api.schemas.workflow import (
    WorkflowExecuteRequest,
    WorkflowResponse,
    WorkflowStatus,
    WorkflowType
)
from src.core.project_manager import project_manager
from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
from src.core.config import config
from src.utils.logger import logger
import asyncio
import uuid
from typing import Dict
from datetime import datetime

router = APIRouter()

# 存储任务状态（内存中，生产环境应使用数据库）
tasks: Dict[str, dict] = {}

@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowExecuteRequest):
    """执行工作流"""
    # 验证项目存在
    project = project_manager.projects.get(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 如果项目未初始化，先初始化
    if project.get('status') != 'initialized':
        success = project_manager.initialize_project(request.project_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to initialize project")
    
    # 生成任务ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    # 创建任务记录
    tasks[task_id] = {
        "task_id": task_id,
        "status": WorkflowStatus.PENDING,
        "workflow_type": request.workflow_type.value,
        "project_id": request.project_id,
        "progress": 0.0,
        "message": "Task created",
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat()
    }
    
    # 异步执行工作流
    asyncio.create_task(_execute_workflow_async(
        task_id,
        request.workflow_type,
        request.project_id,
        request.config
    ))
    
    logger.info(f"Created workflow task: {task_id} for project {request.project_id}")
    
    return WorkflowResponse(**tasks[task_id])

async def _execute_workflow_async(
    task_id: str,
    workflow_type: WorkflowType,
    project_id: str,
    workflow_config
):
    """异步执行工作流"""
    try:
        # 更新状态为运行中
        tasks[task_id]["status"] = WorkflowStatus.RUNNING
        tasks[task_id]["message"] = "Workflow started"
        
        # 获取项目路径
        project_paths = project_manager.get_project_paths(project_id)
        
        # 根据工作流类型选择不同的工作流
        if workflow_type == WorkflowType.NOVEL_PROCESSING:
            workflow = NovelProcessingWorkflow(
                input_folder=project_paths["root"],
                output_folder=project_paths["root"]
            )
            
            # 设置配置（如果提供）
            if workflow_config:
                config.llm_provider = workflow_config.llm_provider
                config.max_concurrency = workflow_config.max_concurrency
            
            # 执行工作流（在线程池中运行，避免阻塞）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, workflow.run)
            
            tasks[task_id]["status"] = WorkflowStatus.COMPLETED
            tasks[task_id]["progress"] = 1.0
            tasks[task_id]["message"] = "Novel processing completed"
            tasks[task_id]["result"] = {
                "chapters_processed": len(result.get("results", {})),
                "output_path": project_paths["root"]
            }
            
        elif workflow_type == WorkflowType.SCRIPT_PROCESSING:
            workflow = ScriptProcessingWorkflow(
                input_folder=project_paths["root"],
                output_folder=project_paths["root"]
            )
            
            if workflow_config:
                config.llm_provider = workflow_config.llm_provider
                config.max_concurrency = workflow_config.max_concurrency
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, workflow.run)
            
            tasks[task_id]["status"] = WorkflowStatus.COMPLETED
            tasks[task_id]["progress"] = 1.0
            tasks[task_id]["message"] = "Script processing completed"
            tasks[task_id]["result"] = {
                "episodes_processed": len(result.get("results", {})),
                "output_path": project_paths["root"]
            }
        
        else:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")
        
        logger.info(f"Workflow task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Workflow task {task_id} failed: {e}")
        tasks[task_id]["status"] = WorkflowStatus.FAILED
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["message"] = f"Workflow failed: {str(e)}"

@router.get("/{task_id}", response_model=WorkflowResponse)
async def get_workflow_status(task_id: str):
    """获取工作流状态"""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return WorkflowResponse(**task)

@router.get("", response_model=list[WorkflowResponse])
async def list_workflows():
    """列出所有工作流任务"""
    return [WorkflowResponse(**task) for task in tasks.values()]

@router.post("/{task_id}/cancel")
async def cancel_workflow(task_id: str):
    """取消工作流（TODO: 实现取消逻辑）"""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Task already finished")
    
    tasks[task_id]["status"] = WorkflowStatus.CANCELLED
    tasks[task_id]["message"] = "Task cancelled by user"
    
    return {"message": "Task cancelled"}
