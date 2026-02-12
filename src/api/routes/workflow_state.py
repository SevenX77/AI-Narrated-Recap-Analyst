"""
Workflow State Management API
管理 Phase I Analyst Agent 工作流状态
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional, Dict, List
import json
import asyncio
from datetime import datetime

from src.core.project_manager_v2 import project_manager_v2
from src.core.schemas_project import (
    ProjectMeta,
    PhaseIAnalystState,
    PhaseStepState,
    PhaseStatus,
    DependencyCheck
)
from src.utils.logger import logger

router = APIRouter()


# ============ WebSocket 连接管理 ============

class ConnectionManager:
    """WebSocket 连接管理器"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        """连接 WebSocket"""
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        logger.info(f"WebSocket connected for project {project_id}")
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        """断开 WebSocket"""
        if project_id in self.active_connections:
            self.active_connections[project_id].remove(websocket)
            logger.info(f"WebSocket disconnected for project {project_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict, project_id: str):
        """广播消息到项目的所有连接"""
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")


manager = ConnectionManager()


# ============ Helper Functions ============

def check_step_dependencies(step_id: str, meta: ProjectMeta) -> DependencyCheck:
    """检查步骤依赖"""
    if not meta.phase_i_analyst:
        return DependencyCheck(is_met=False, message="Phase I 未初始化")
    
    phase = meta.phase_i_analyst
    
    if step_id == "step_1_import":
        # 步骤 1 无依赖
        return DependencyCheck(is_met=True, message="无前置依赖")
    
    elif step_id == "step_2_script":
        # 依赖步骤 1 的 Script 导入
        if phase.step_1_import.script_imported:
            return DependencyCheck(is_met=True, message="Script 已导入")
        return DependencyCheck(
            is_met=False,
            missing_dependencies=["step_1_import.script"],
            message="需要先导入 Script 文件"
        )
    
    elif step_id == "step_3_novel":
        # 依赖步骤 1 的 Novel 导入
        if phase.step_1_import.novel_imported:
            return DependencyCheck(is_met=True, message="Novel 已导入")
        return DependencyCheck(
            is_met=False,
            missing_dependencies=["step_1_import.novel"],
            message="需要先导入 Novel 文件"
        )
    
    elif step_id == "step_4_alignment":
        # 依赖步骤 2 和 3
        step2_done = phase.step_2_script.status == PhaseStatus.COMPLETED
        step3_done = phase.step_3_novel.status == PhaseStatus.COMPLETED
        
        if step2_done and step3_done:
            return DependencyCheck(is_met=True, message="Script 和 Novel 分析已完成")
        
        missing = []
        if not step2_done:
            missing.append("step_2_script")
        if not step3_done:
            missing.append("step_3_novel")
        
        return DependencyCheck(
            is_met=False,
            missing_dependencies=missing,
            message="需要先完成 Script 和 Novel 分析"
        )
    
    return DependencyCheck(is_met=False, message="未知步骤")


def update_step_status_based_on_dependencies(meta: ProjectMeta):
    """根据依赖关系更新步骤状态（LOCKED/READY）"""
    if not meta.phase_i_analyst:
        meta.initialize_phase_i()
    
    phase = meta.phase_i_analyst
    
    # 更新每个步骤的依赖和状态
    for step in [phase.step_1_import, phase.step_2_script, phase.step_3_novel, phase.step_4_alignment]:
        if step.status in [PhaseStatus.LOCKED, PhaseStatus.READY]:
            dep_check = check_step_dependencies(step.step_id, meta)
            step.dependencies = dep_check
            
            if dep_check.is_met:
                step.status = PhaseStatus.READY
            else:
                step.status = PhaseStatus.LOCKED
    
    # 更新整体状态
    if any(s.status == PhaseStatus.RUNNING for s in [phase.step_1_import, phase.step_2_script, phase.step_3_novel, phase.step_4_alignment]):
        phase.overall_status = PhaseStatus.RUNNING
    elif all(s.status == PhaseStatus.COMPLETED for s in [phase.step_1_import, phase.step_2_script, phase.step_3_novel, phase.step_4_alignment]):
        phase.overall_status = PhaseStatus.COMPLETED
    elif any(s.status == PhaseStatus.FAILED for s in [phase.step_1_import, phase.step_2_script, phase.step_3_novel, phase.step_4_alignment]):
        phase.overall_status = PhaseStatus.FAILED
    else:
        phase.overall_status = PhaseStatus.LOCKED


# ============ Workflow State API ============

@router.get("/{project_id}/workflow-state")
async def get_workflow_state(project_id: str):
    """获取项目的 Phase I 工作流状态"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 初始化 Phase I 状态（如果未初始化）
    if not meta.phase_i_analyst:
        meta.initialize_phase_i()
        project_manager_v2.save_project_meta(meta)
    
    # 确保源文件状态是最新的
    project_manager_v2.update_sources_from_filesystem(project_id)
    
    # 重新获取最新的 meta
    meta = project_manager_v2.get_project(project_id)
    
    # 更新依赖状态
    update_step_status_based_on_dependencies(meta)
    project_manager_v2.save_project_meta(meta)
    
    return meta.phase_i_analyst.model_dump()


@router.post("/{project_id}/workflow/{step_id}/start")
async def start_workflow_step(project_id: str, step_id: str):
    """启动指定步骤"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not meta.phase_i_analyst:
        meta.initialize_phase_i()
    
    # 检查依赖
    dep_check = check_step_dependencies(step_id, meta)
    if not dep_check.is_met:
        raise HTTPException(
            status_code=400,
            detail=f"依赖未满足: {dep_check.message}"
        )
    
    # 获取步骤
    phase = meta.phase_i_analyst
    step_map = {
        "step_1_import": phase.step_1_import,
        "step_2_script": phase.step_2_script,
        "step_3_novel": phase.step_3_novel,
        "step_4_alignment": phase.step_4_alignment,
    }
    
    step = step_map.get(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")
    
    # 更新状态
    step.status = PhaseStatus.RUNNING
    step.started_at = datetime.now()
    step.last_updated = datetime.now()
    
    project_manager_v2.save_project_meta(meta)
    
    # 广播状态更新
    await manager.broadcast({
        "type": "step_started",
        "step_id": step_id,
        "step_name": step.step_name,
        "timestamp": datetime.now().isoformat()
    }, project_id)
    
    logger.info(f"Started step {step_id} for project {project_id}")
    
    # 在后台异步执行workflow并追踪task
    task_key = f"{project_id}:{step_id}"
    if step_id == "step_2_script":
        _running_tasks[task_key] = asyncio.create_task(_execute_script_workflow(project_id))
    elif step_id == "step_3_novel":
        _running_tasks[task_key] = asyncio.create_task(_execute_novel_workflow(project_id))
    elif step_id == "step_4_alignment":
        _running_tasks[task_key] = asyncio.create_task(_execute_alignment_workflow(project_id))
    
    return {"message": f"步骤 {step.step_name} 已启动", "step_id": step_id}


@router.post("/{project_id}/workflow/{step_id}/complete")
async def complete_workflow_step(
    project_id: str,
    step_id: str,
    quality_score: Optional[int] = None,
    result_path: Optional[str] = None
):
    """标记步骤为完成"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not meta.phase_i_analyst:
        raise HTTPException(status_code=400, detail="Phase I 未初始化")
    
    phase = meta.phase_i_analyst
    step_map = {
        "step_1_import": phase.step_1_import,
        "step_2_script": phase.step_2_script,
        "step_3_novel": phase.step_3_novel,
        "step_4_alignment": phase.step_4_alignment,
    }
    
    step = step_map.get(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")
    
    # 更新状态
    step.status = PhaseStatus.COMPLETED
    step.completed_at = datetime.now()
    step.last_updated = datetime.now()
    step.overall_progress = 100.0
    
    if quality_score is not None:
        step.quality_score = quality_score
    if result_path:
        step.result_path = result_path
    
    # 更新依赖状态（解锁后续步骤）
    update_step_status_based_on_dependencies(meta)
    
    project_manager_v2.save_project_meta(meta)
    
    # 广播状态更新
    await manager.broadcast({
        "type": "step_completed",
        "step_id": step_id,
        "step_name": step.step_name,
        "quality_score": quality_score,
        "timestamp": datetime.now().isoformat()
    }, project_id)
    
    logger.info(f"Completed step {step_id} for project {project_id}")
    
    return {"message": f"步骤 {step.step_name} 已完成", "step_id": step_id}


@router.post("/{project_id}/workflow/{step_id}/fail")
async def fail_workflow_step(
    project_id: str,
    step_id: str,
    error_message: str
):
    """标记步骤为失败"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not meta.phase_i_analyst:
        raise HTTPException(status_code=400, detail="Phase I 未初始化")
    
    phase = meta.phase_i_analyst
    step_map = {
        "step_1_import": phase.step_1_import,
        "step_2_script": phase.step_2_script,
        "step_3_novel": phase.step_3_novel,
        "step_4_alignment": phase.step_4_alignment,
    }
    
    step = step_map.get(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")
    
    # 更新状态
    step.status = PhaseStatus.FAILED
    step.completed_at = datetime.now()
    step.last_updated = datetime.now()
    step.error_message = error_message
    
    project_manager_v2.save_project_meta(meta)
    
    # 广播状态更新
    await manager.broadcast({
        "type": "step_failed",
        "step_id": step_id,
        "step_name": step.step_name,
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    }, project_id)
    
    logger.error(f"Step {step_id} failed for project {project_id}: {error_message}")
    
    return {"message": f"步骤 {step.step_name} 失败", "step_id": step_id}


@router.post("/{project_id}/workflow/{step_id}/stop")
async def stop_workflow_step(project_id: str, step_id: str):
    """停止正在运行的步骤"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 取消正在运行的任务
    task_key = f"{project_id}:{step_id}"
    if task_key in _running_tasks:
        task = _running_tasks[task_key]
        if not task.done():
            task.cancel()
            logger.info(f"Cancelled task {task_key}")
        del _running_tasks[task_key]
    
    # 更新状态为cancelled
    if not meta.phase_i_analyst:
        raise HTTPException(status_code=400, detail="Phase I 未初始化")
    
    phase = meta.phase_i_analyst
    step_map = {
        "step_1_import": phase.step_1_import,
        "step_2_script": phase.step_2_script,
        "step_3_novel": phase.step_3_novel,
        "step_4_alignment": phase.step_4_alignment,
    }
    
    step = step_map.get(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")
    
    step.status = PhaseStatus.CANCELLED
    step.completed_at = datetime.now()
    step.last_updated = datetime.now()
    step.error_message = "Stopped by user"
    
    project_manager_v2.save_project_meta(meta)
    
    # 广播状态更新
    await manager.broadcast({
        "type": "step_cancelled",
        "step_id": step_id,
        "step_name": step.step_name,
        "timestamp": datetime.now().isoformat()
    }, project_id)
    
    logger.info(f"Stopped step {step_id} for project {project_id}")
    
    return {"message": f"步骤 {step.step_name} 已停止", "step_id": step_id}


@router.post("/{project_id}/workflow/step_2_script/episode/{episode_id}/start")
async def start_episode_processing(project_id: str, episode_id: str):
    """启动单个episode的处理"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not meta.phase_i_analyst:
        raise HTTPException(status_code=400, detail="Phase I 未初始化")
    
    # 检查episode是否存在
    if episode_id not in meta.phase_i_analyst.step_2_script.episodes_status:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")
    
    # 启动单集处理
    task_key = f"{project_id}:step_2_script:{episode_id}"
    _running_tasks[task_key] = asyncio.create_task(_execute_single_episode(project_id, episode_id))
    
    logger.info(f"Started processing episode {episode_id} for project {project_id}")
    
    return {"message": f"Episode {episode_id} 处理已启动", "episode_id": episode_id}


@router.post("/{project_id}/workflow/step_2_script/episode/{episode_id}/stop")
async def stop_episode_processing(project_id: str, episode_id: str):
    """停止单个episode的处理"""
    task_key = f"{project_id}:step_2_script:{episode_id}"
    
    if task_key in _running_tasks:
        task = _running_tasks[task_key]
        if not task.done():
            task.cancel()
            logger.info(f"Cancelled episode task {task_key}")
        del _running_tasks[task_key]
        
        # 更新episode状态
        meta = project_manager_v2.get_project(project_id)
        if meta and meta.phase_i_analyst:
            if episode_id in meta.phase_i_analyst.step_2_script.episodes_status:
                meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["status"] = PhaseStatus.CANCELLED.value
                project_manager_v2.save_project_meta(meta)
        
        await manager.broadcast({
            "type": "episode_stopped",
            "step_id": "step_2_script",
            "episode_id": episode_id,
            "timestamp": datetime.now().isoformat()
        }, project_id)
        
        return {"message": f"Episode {episode_id} 已停止", "episode_id": episode_id}
    else:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} is not running")



@router.post("/{project_id}/workflow/{step_id}/progress")
async def update_step_progress(
    project_id: str,
    step_id: str,
    progress: float,
    current_task: Optional[str] = None
):
    """更新步骤进度"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not meta.phase_i_analyst:
        raise HTTPException(status_code=400, detail="Phase I 未初始化")
    
    phase = meta.phase_i_analyst
    step_map = {
        "step_1_import": phase.step_1_import,
        "step_2_script": phase.step_2_script,
        "step_3_novel": phase.step_3_novel,
        "step_4_alignment": phase.step_4_alignment,
    }
    
    step = step_map.get(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")
    
    # 更新进度
    step.overall_progress = min(100.0, max(0.0, progress))
    step.last_updated = datetime.now()
    
    project_manager_v2.save_project_meta(meta)
    
    # 广播进度更新
    await manager.broadcast({
        "type": "progress_update",
        "step_id": step_id,
        "progress": progress,
        "current_task": current_task,
        "timestamp": datetime.now().isoformat()
    }, project_id)
    
    return {"message": "进度已更新", "progress": progress}


# ============ WebSocket 实时连接 ============

@router.websocket("/{project_id}/ws")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket 连接用于实时日志推送和进度更新"""
    await manager.connect(websocket, project_id)
    
    try:
        # 发送欢迎消息
        await manager.send_personal_message({
            "type": "connected",
            "project_id": project_id,
            "message": "WebSocket 连接成功",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # 保持连接并接收消息
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息（如果需要）
            logger.info(f"Received message from client: {data}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
        logger.info(f"WebSocket disconnected for project {project_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, project_id)


# ============ Workflow执行后台任务 ============

# 全局任务追踪（用于取消）
_running_tasks: Dict[str, asyncio.Task] = {}

async def _execute_script_workflow(project_id: str):
    """执行Script处理workflow (分段+Hook检测+验证)"""
    from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
    from src.core.schemas_script import ScriptProcessingConfig
    from src.core.config import config
    import os
    
    try:
        meta = project_manager_v2.get_project(project_id)
        if not meta:
            logger.error(f"Project {project_id} not found")
            return
        
        project_dir = os.path.join(config.data_dir, "projects", project_id)
        raw_script_dir = os.path.join(project_dir, "raw", "script")
        
        # 如果raw/script不存在，尝试raw目录
        if not os.path.exists(raw_script_dir):
            raw_script_dir = os.path.join(project_dir, "raw")
        
        # 获取所有SRT文件
        srt_files = []
        if os.path.exists(raw_script_dir):
            srt_files = [f for f in os.listdir(raw_script_dir) if f.lower().endswith('.srt')]
        
        if not srt_files:
            error_msg = f"No SRT files found in {raw_script_dir}"
            logger.error(error_msg)
            
            meta.phase_i_analyst.step_2_script.status = PhaseStatus.FAILED
            meta.phase_i_analyst.step_2_script.error_message = error_msg
            project_manager_v2.save_project_meta(meta)
            
            await manager.broadcast({
                "type": "step_failed",
                "step_id": "step_2_script",
                "error_message": error_msg,
                "timestamp": datetime.now().isoformat()
            }, project_id)
            return
        
        # 按集数排序
        srt_files.sort()
        
        total_episodes = len(srt_files)
        completed_episodes = 0
        total_llm_calls = 0
        total_cost = 0.0
        
        logger.info(f"Found {total_episodes} SRT files in {raw_srt_dir}")
        
        # 初始化episodes_status
        meta.phase_i_analyst.step_2_script.total_episodes = total_episodes
        meta.phase_i_analyst.step_2_script.completed_episodes = 0
        meta.phase_i_analyst.step_2_script.episodes_status = {}
        
        for srt_file in srt_files:
            episode_name = srt_file.replace('.srt', '')
            meta.phase_i_analyst.step_2_script.episodes_status[episode_name] = {
                "status": PhaseStatus.READY.value,
                "phases": {
                    "phase_1": {"phase_id": "phase_1", "phase_name": "SRT Import", "status": PhaseStatus.READY.value},
                    "phase_2": {"phase_id": "phase_2", "phase_name": "Text Extraction", "status": PhaseStatus.LOCKED.value},
                    "phase_3": {"phase_id": "phase_3", "phase_name": "Hook Detection", "status": PhaseStatus.LOCKED.value},
                    "phase_4": {"phase_id": "phase_4", "phase_name": "Hook Analysis", "status": PhaseStatus.LOCKED.value},
                    "phase_5": {"phase_id": "phase_5", "phase_name": "Semantic Segmentation", "status": PhaseStatus.LOCKED.value},
                    "phase_6": {"phase_id": "phase_6", "phase_name": "ABC Classification", "status": PhaseStatus.LOCKED.value},
                    "phase_7": {"phase_id": "phase_7", "phase_name": "Quality Validation", "status": PhaseStatus.LOCKED.value},
                },
                "quality_score": 0,
                "llm_calls": 0,
                "cost": 0.0,
                "processing_time": 0.0
            }
        
        project_manager_v2.save_project_meta(meta)
        
        await manager.broadcast({
            "type": "progress_update",
            "step_id": "step_2_script",
            "progress": 0,
            "current_task": f"Initializing {total_episodes} episodes",
            "timestamp": datetime.now().isoformat()
        }, project_id)
        
        # 并发处理episodes（批量处理，避免API限流）
        max_concurrent = 2  # 建议并发数 ≤ 2，避免API限流
        logger.info(f"🔀 并发处理模式: 并发数={max_concurrent}")
        
        async def process_episode(idx: int, srt_file: str):
            """处理单个episode"""
            nonlocal completed_episodes, total_llm_calls, total_cost
            
            episode_name = srt_file.replace('.srt', '')
            srt_path = os.path.join(raw_srt_dir, srt_file)
            
            # 检查是否已经处理过（检查processed文件）
            processed_json = os.path.join(project_dir, "processed", "script", f"{episode_name}.json")
            if os.path.exists(processed_json):
                logger.info(f"⏭️ Skipping {episode_name} - already processed (found {processed_json})")
                
                # 标记为已完成
                meta = project_manager_v2.get_project(project_id)
                meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["status"] = PhaseStatus.COMPLETED.value
                for phase_id in meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["phases"]:
                    meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["phases"][phase_id]["status"] = PhaseStatus.COMPLETED.value
                meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["quality_score"] = 100
                meta.phase_i_analyst.step_2_script.completed_episodes = completed_episodes + 1
                project_manager_v2.save_project_meta(meta)
                
                completed_episodes += 1
                return None
            
            logger.info(f"Processing {episode_name} ({idx+1}/{total_episodes})")
            
            # 更新episode状态为running
            meta = project_manager_v2.get_project(project_id)
            meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["status"] = PhaseStatus.RUNNING.value
            meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["phases"]["phase_1"]["status"] = PhaseStatus.RUNNING.value
            project_manager_v2.save_project_meta(meta)
            
            await manager.broadcast({
                "type": "progress_update",
                "step_id": "step_2_script",
                "progress": (completed_episodes / total_episodes) * 100,
                "current_task": f"Processing {episode_name} ({idx+1}/{total_episodes})",
                "timestamp": datetime.now().isoformat()
            }, project_id)
            
            # 配置workflow（ep01启用Hook检测）
            workflow_config = ScriptProcessingConfig(
                enable_hook_detection=(episode_name == "ep01"),
                enable_hook_analysis=False,  # 暂不启用深度分析
                enable_abc_classification=True,
                segmentation_provider="deepseek",  # 使用DeepSeek降低成本
                min_quality_score=70
            )
            
            try:
                # 执行ScriptProcessingWorkflow
                workflow = ScriptProcessingWorkflow()
                result = await workflow.run(
                    srt_path=srt_path,
                    project_name=project_id,
                    episode_name=episode_name,
                    config=workflow_config
                )
                
                # 更新统计
                completed_episodes += 1
                total_llm_calls += result.llm_calls_count
                total_cost += result.total_cost
                
                # 更新episode完成状态
                meta = project_manager_v2.get_project(project_id)
                if result.success:
                    meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["status"] = PhaseStatus.COMPLETED.value
                    meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["quality_score"] = int(result.validation_report.quality_score) if result.validation_report else 0
                    # 标记所有phases为completed
                    for phase_id in meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["phases"]:
                        meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["phases"][phase_id]["status"] = PhaseStatus.COMPLETED.value
                else:
                    meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["status"] = PhaseStatus.FAILED.value
                
                meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["llm_calls"] = result.llm_calls_count
                meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["cost"] = result.total_cost
                meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["processing_time"] = result.processing_time
                meta.phase_i_analyst.step_2_script.completed_episodes = completed_episodes
                project_manager_v2.save_project_meta(meta)
                
                logger.info(f"✅ Completed {episode_name}: cost=${result.total_cost:.3f}, llm_calls={result.llm_calls_count}")
                
                return result
            
            except Exception as e:
                logger.error(f"❌ Failed to process {episode_name}: {str(e)}")
                
                # 标记失败
                meta = project_manager_v2.get_project(project_id)
                meta.phase_i_analyst.step_2_script.episodes_status[episode_name]["status"] = PhaseStatus.FAILED.value
                project_manager_v2.save_project_meta(meta)
                
                return None
        
        # 分批并发处理
        for i in range(0, len(srt_files), max_concurrent):
            batch = srt_files[i:i + max_concurrent]
            batch_indices = range(i, i + len(batch))
            
            logger.info(f"📦 Processing batch {i//max_concurrent + 1}: {[f.replace('.srt', '') for f in batch]}")
            
            # 并发处理当前批次
            tasks = [process_episode(idx, srt_file) for idx, srt_file in zip(batch_indices, batch)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查结果
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Batch processing error: {result}")
            
            logger.info(f"✅ Batch {i//max_concurrent + 1} completed")
        
        # 标记完成
        meta = project_manager_v2.get_project(project_id)
        meta.phase_i_analyst.step_2_script.status = PhaseStatus.COMPLETED
        meta.phase_i_analyst.step_2_script.completed_at = datetime.now()
        meta.phase_i_analyst.step_2_script.overall_progress = 100.0
        meta.phase_i_analyst.step_2_script.completed_episodes = completed_episodes
        meta.phase_i_analyst.step_2_script.total_episodes = total_episodes
        meta.phase_i_analyst.step_2_script.llm_calls_count = total_llm_calls
        meta.phase_i_analyst.step_2_script.total_cost = total_cost
        project_manager_v2.save_project_meta(meta)
        
        logger.info(f"🎉 Script workflow completed for {project_id}: {completed_episodes} episodes, ${total_cost:.2f}")
        
        await manager.broadcast({
            "type": "step_completed",
            "step_id": "step_2_script",
            "message": f"Completed {completed_episodes}/{total_episodes} episodes (${total_cost:.2f})",
            "timestamp": datetime.now().isoformat()
        }, project_id)
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Script workflow failed for project {project_id}: {e}\n{error_detail}")
        
        meta = project_manager_v2.get_project(project_id)
        if meta:
            meta.phase_i_analyst.step_2_script.status = PhaseStatus.FAILED
            meta.phase_i_analyst.step_2_script.error_message = str(e)
            project_manager_v2.save_project_meta(meta)
        
        await manager.broadcast({
            "type": "step_failed",
            "step_id": "step_2_script",
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }, project_id)


async def _execute_single_episode(project_id: str, episode_id: str):
    """执行单个episode的Script处理"""
    from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
    from src.core.schemas_script import ScriptProcessingConfig
    from src.core.config import config
    import os
    
    try:
        meta = project_manager_v2.get_project(project_id)
        if not meta:
            logger.error(f"Project {project_id} not found")
            return
        
        project_dir = os.path.join(config.data_dir, "projects", project_id)
        raw_srt_dir = os.path.join(project_dir, "raw", "srt")
        
        if not os.path.exists(raw_srt_dir):
            raw_srt_dir = os.path.join(project_dir, "raw")
        
        srt_path = os.path.join(raw_srt_dir, f"{episode_id}.srt")
        
        if not os.path.exists(srt_path):
            error_msg = f"SRT file not found: {srt_path}"
            logger.error(error_msg)
            
            meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["status"] = PhaseStatus.FAILED.value
            project_manager_v2.save_project_meta(meta)
            
            await manager.broadcast({
                "type": "episode_failed",
                "step_id": "step_2_script",
                "episode_id": episode_id,
                "error_message": error_msg,
                "timestamp": datetime.now().isoformat()
            }, project_id)
            return
        
        # 更新状态为running
        meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["status"] = PhaseStatus.RUNNING.value
        project_manager_v2.save_project_meta(meta)
        
        await manager.broadcast({
            "type": "episode_started",
            "step_id": "step_2_script",
            "episode_id": episode_id,
            "timestamp": datetime.now().isoformat()
        }, project_id)
        
        # 配置workflow
        workflow_config = ScriptProcessingConfig(
            enable_hook_detection=(episode_id == "ep01"),
            enable_hook_analysis=False,
            enable_abc_classification=True,
            segmentation_provider="deepseek",
            min_quality_score=70
        )
        
        # 执行workflow
        workflow = ScriptProcessingWorkflow()
        result = await workflow.run(
            srt_path=srt_path,
            project_name=project_id,
            episode_name=episode_id,
            config=workflow_config
        )
        
        # 更新完成状态
        meta = project_manager_v2.get_project(project_id)
        if result.success:
            meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["status"] = PhaseStatus.COMPLETED.value
            meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["quality_score"] = int(result.validation_report.quality_score) if result.validation_report else 0
            for phase_id in meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["phases"]:
                meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["phases"][phase_id]["status"] = PhaseStatus.COMPLETED.value
        else:
            meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["status"] = PhaseStatus.FAILED.value
        
        meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["llm_calls"] = result.llm_calls_count
        meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["cost"] = result.total_cost
        meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["processing_time"] = result.processing_time
        
        # 更新总统计
        meta.phase_i_analyst.step_2_script.completed_episodes = sum(
            1 for ep in meta.phase_i_analyst.step_2_script.episodes_status.values()
            if ep["status"] == PhaseStatus.COMPLETED.value
        )
        meta.phase_i_analyst.step_2_script.llm_calls_count += result.llm_calls_count
        meta.phase_i_analyst.step_2_script.total_cost += result.total_cost
        
        project_manager_v2.save_project_meta(meta)
        
        await manager.broadcast({
            "type": "episode_completed",
            "step_id": "step_2_script",
            "episode_id": episode_id,
            "quality_score": result.validation_report.quality_score if result.validation_report else 0,
            "cost": result.total_cost,
            "timestamp": datetime.now().isoformat()
        }, project_id)
        
        logger.info(f"✅ Completed episode {episode_id}: cost=${result.total_cost:.3f}")
        
    except asyncio.CancelledError:
        logger.info(f"Episode {episode_id} processing was cancelled")
        meta = project_manager_v2.get_project(project_id)
        if meta and meta.phase_i_analyst:
            meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["status"] = PhaseStatus.CANCELLED.value
            project_manager_v2.save_project_meta(meta)
        raise
    except Exception as e:
        logger.error(f"Failed to process episode {episode_id}: {str(e)}")
        meta = project_manager_v2.get_project(project_id)
        if meta and meta.phase_i_analyst:
            meta.phase_i_analyst.step_2_script.episodes_status[episode_id]["status"] = PhaseStatus.FAILED.value
            project_manager_v2.save_project_meta(meta)
        
        await manager.broadcast({
            "type": "episode_failed",
            "step_id": "step_2_script",
            "episode_id": episode_id,
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }, project_id)



async def _execute_novel_workflow(project_id: str):
    """执行Novel处理workflow (分段+标注+系统分析+验证)"""
    from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
    from src.core.schemas_novel import NovelProcessingConfig
    from src.core.config import config
    import os
    
    try:
        meta = project_manager_v2.get_project(project_id)
        if not meta:
            logger.error(f"Project {project_id} not found")
            return
        
        project_dir = os.path.join(config.data_dir, "projects", project_id)
        
        # 尝试多个可能的Novel文件路径
        possible_paths = [
            os.path.join(project_dir, "processed", "novel", "standardized.txt"),
            os.path.join(project_dir, "raw", "novel.txt"),
            os.path.join(project_dir, "raw", "novel", "novel.txt"),
        ]
        
        # 查找第一个存在的文件
        novel_path = None
        for path in possible_paths:
            if os.path.exists(path):
                novel_path = path
                break
        
        if not novel_path:
            error_msg = f"Novel file not found. Searched: {possible_paths}"
            logger.error(error_msg)
            
            meta.phase_i_analyst.step_3_novel.status = PhaseStatus.FAILED
            meta.phase_i_analyst.step_3_novel.error_message = error_msg
            project_manager_v2.save_project_meta(meta)
            
            await manager.broadcast({
                "type": "step_failed",
                "step_id": "step_3_novel",
                "error_message": error_msg,
                "timestamp": datetime.now().isoformat()
            }, project_id)
            return
        
        logger.info(f"Found novel file at: {novel_path}")
        
        # 获取章节数量（从meta中读取）
        chapter_count = meta.phase_i_analyst.step_1_import.novel_chapter_count or 50
        
        # 配置workflow（处理前10章用于测试，全书用于生产）
        workflow_config = NovelProcessingConfig(
            enable_parallel=True,
            max_concurrent_chapters=3,  # 并发处理3个章节
            chapter_range=(1, min(10, chapter_count)),  # 先处理前10章
            enable_functional_tags=False,  # 暂不启用功能标签
            enable_system_analysis=True,   # 启用系统分析
            segmentation_provider="claude",  # 使用Claude保证质量
            annotation_provider="claude",
            output_markdown_reports=True,
            continue_on_error=True,  # 单章失败继续处理
        )
        
        logger.info(f"Starting novel workflow with config: chapters 1-{workflow_config.chapter_range[1]}")
        
        # 定期更新进度
        async def progress_monitor():
            """监控进度并广播"""
            while True:
                await asyncio.sleep(10)
                # 这里可以从workflow读取实时进度
                # 暂时使用简单的心跳
                await manager.broadcast({
                    "type": "heartbeat",
                    "step_id": "step_3_novel",
                    "timestamp": datetime.now().isoformat()
                }, project_id)
        
        # 启动进度监控
        monitor_task = asyncio.create_task(progress_monitor())
        
        try:
            # 执行NovelProcessingWorkflow
            workflow = NovelProcessingWorkflow()
            result = await workflow.run(
                novel_path=novel_path,
                project_name=project_id,
                config=workflow_config
            )
            
            # 停止进度监控
            monitor_task.cancel()
            
            # 标记完成
            meta = project_manager_v2.get_project(project_id)
            meta.phase_i_analyst.step_3_novel.status = PhaseStatus.COMPLETED
            meta.phase_i_analyst.step_3_novel.completed_at = datetime.now()
            meta.phase_i_analyst.step_3_novel.overall_progress = 100.0
            meta.phase_i_analyst.step_3_novel.total_chapters = len(result.chapters)
            meta.phase_i_analyst.step_3_novel.llm_calls_count = result.llm_calls_count
            meta.phase_i_analyst.step_3_novel.total_cost = result.total_cost
            meta.phase_i_analyst.step_3_novel.processing_time = result.processing_time
            project_manager_v2.save_project_meta(meta)
            
            logger.info(f"🎉 Novel workflow completed for {project_id}: {len(result.chapters)} chapters, ${result.total_cost:.2f}")
            
            await manager.broadcast({
                "type": "step_completed",
                "step_id": "step_3_novel",
                "message": f"Completed {len(result.chapters)} chapters (${result.total_cost:.2f})",
                "timestamp": datetime.now().isoformat()
            }, project_id)
            
        except asyncio.CancelledError:
            monitor_task.cancel()
            raise
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Novel workflow failed for project {project_id}: {e}\n{error_detail}")
        
        meta = project_manager_v2.get_project(project_id)
        if meta:
            meta.phase_i_analyst.step_3_novel.status = PhaseStatus.FAILED
            meta.phase_i_analyst.step_3_novel.error_message = str(e)
            project_manager_v2.save_project_meta(meta)
        
        await manager.broadcast({
            "type": "step_failed",
            "step_id": "step_3_novel",
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }, project_id)


async def _execute_alignment_workflow(project_id: str):
    """执行对齐workflow"""
    # TODO: 实现对齐workflow
    logger.info(f"Alignment workflow not yet implemented for project {project_id}")
    await manager.broadcast({
        "type": "step_failed",
        "step_id": "step_4_alignment",
        "error_message": "Alignment workflow not yet implemented",
        "timestamp": datetime.now().isoformat()
    }, project_id)


# ============ 日志流式输出 API ============

@router.get("/{project_id}/logs/stream")
async def stream_logs(project_id: str, step_id: Optional[str] = None):
    """流式输出日志（Server-Sent Events）"""
    from fastapi.responses import StreamingResponse
    import asyncio
    
    async def event_generator():
        """生成日志事件"""
        # TODO: 实现实际的日志流式输出
        # 目前返回模拟数据
        for i in range(10):
            yield f"data: {json.dumps({'message': f'Log entry {i}', 'timestamp': datetime.now().isoformat()})}\n\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
