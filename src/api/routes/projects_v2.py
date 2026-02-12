"""
Projects API V2 - 使用新的数据存储架构
支持自动预处理功能
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import List, Optional
import os
import json
import shutil
from pathlib import Path
from pydantic import BaseModel

from src.api.schemas.project import ProjectResponse, ProjectList, ProjectStats, ProjectCreate, ProjectUpdate
from src.core.project_manager_v2 import project_manager_v2
from src.workflows.preprocess_service import preprocess_service
from src.core.schemas_project import ProjectMeta
from src.core.config import config
from src.utils.logger import logger

router = APIRouter()


# ============ Helper Functions ============

def _meta_to_response(meta: ProjectMeta) -> ProjectResponse:
    """将 ProjectMeta 转换为 API Response"""
    return ProjectResponse(
        id=meta.id,
        name=meta.name,
        description=meta.description,
        created_at=meta.created_at,
        updated_at=meta.updated_at,
        status=meta.status.value,
        sources=meta.sources.model_dump(),
        workflow_stages=meta.workflow_stages.model_dump(),
        stats=meta.stats.model_dump()
    )


# ============ Project CRUD ============

@router.get("", response_model=ProjectList)
async def list_projects():
    """获取所有项目列表"""
    try:
        projects = project_manager_v2.list_projects()
        return ProjectList(
            projects=[_meta_to_response(meta) for meta in projects],
            total=len(projects)
        )
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ProjectStats)
async def get_project_stats():
    """获取项目统计信息"""
    try:
        projects = project_manager_v2.list_projects()
        return ProjectStats(
            total_projects=len(projects),
            initialized=sum(1 for p in projects if p.status.value == 'ready'),
            discovered=sum(1 for p in projects if p.status.value == 'draft')
        )
    except Exception as e:
        logger.error(f"Failed to get project stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """获取项目详情"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return _meta_to_response(meta)


@router.get("/{project_id}/meta")
async def get_project_meta(project_id: str):
    """获取项目完整元数据"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return meta.to_dict()


@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """创建新项目"""
    try:
        meta = project_manager_v2.create_project(
            name=project.name,
            description=project.description
        )
        
        logger.info(f"Created new project: {meta.name} -> {meta.id}")
        
        return _meta_to_response(meta)
    
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project: ProjectUpdate):
    """更新项目"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project.model_dump(exclude_unset=True)
    updated_meta = project_manager_v2.update_project(project_id, **update_data)
    
    if not updated_meta:
        raise HTTPException(status_code=500, detail="Failed to update project")
        
    return _meta_to_response(updated_meta)


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    success = project_manager_v2.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    logger.info(f"Deleted project: {project_id}")
    return {"message": "Project deleted successfully"}


# ============ File Management ============

@router.get("/{project_id}/files/analyst/{path:path}")
async def get_analyst_file(project_id: str, path: str):
    """获取analyst目录下的文件（Phase I数据）"""
    from fastapi.responses import FileResponse, JSONResponse
    import os
    from src.core.config import config
    
    project_dir = os.path.join(config.data_dir, "projects", project_id)
    file_path = os.path.join(project_dir, "analyst", path)
    
    # 安全检查：确保路径在项目目录内
    if not os.path.abspath(file_path).startswith(os.path.abspath(project_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # 如果是目录，列出文件
    if os.path.isdir(file_path):
        files = []
        for item in os.listdir(file_path):
            item_path = os.path.join(file_path, item)
            files.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
            })
        return JSONResponse({"files": files})
    
    # 返回文件
    return FileResponse(file_path)


@router.get("/{project_id}/files")
async def get_project_files(project_id: str):
    """获取项目原始文件列表"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    files = project_manager_v2.get_raw_files(project_id)
    return {"files": files}


@router.get("/{project_id}/files/{filename}/view")
async def view_raw_file(project_id: str, filename: str, category: Optional[str] = None):
    """查看原始文件内容。category 为 novel 或 script 时从 raw/novel 或 raw/script 读取。"""
    from fastapi.responses import PlainTextResponse

    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")

    raw_base = os.path.join(config.data_dir, "projects", project_id, "raw")
    if category in ("novel", "script"):
        file_path = os.path.join(raw_base, category, filename)
    else:
        file_path = os.path.join(raw_base, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return PlainTextResponse(content)
    except Exception as e:
        logger.error(f"Failed to read file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}/files/{filename}")
async def delete_raw_file(project_id: str, filename: str, category: Optional[str] = None):
    """删除原始文件。category 为 novel 或 srt 时从对应子目录删除。"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")

    raw_base = os.path.join(config.data_dir, "projects", project_id, "raw")
    if category in ("novel", "srt"):
        file_path = os.path.join(raw_base, category, filename)
    else:
        file_path = os.path.join(raw_base, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        os.remove(file_path)
        logger.info(f"Deleted file: {filename} from project {project_id}")
        
        # 更新项目源文件信息
        project_manager_v2.update_sources_from_filesystem(project_id)
        
        return {"message": "File deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/upload")
async def upload_files(
    project_id: str,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    auto_preprocess: bool = True
):
    """
    上传项目文件
    
    Args:
        project_id: 项目ID
        files: 上传的文件列表
        auto_preprocess: 是否自动预处理（默认True）
    """
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = os.path.join(config.data_dir, "projects", project_id)
    raw_base = os.path.join(project_dir, "raw")
    raw_novel = os.path.join(raw_base, "novel")
    raw_srt = os.path.join(raw_base, "srt")
    os.makedirs(raw_novel, exist_ok=True)
    os.makedirs(raw_srt, exist_ok=True)

    uploaded_files = []

    try:
        for file in files:
            ext = Path(file.filename).suffix.lower()
            if ext not in ['.txt', '.srt', '.md', '.pdf']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file.filename}"
                )
            if ext == '.srt':
                target_dir = raw_srt
            else:
                target_dir = raw_novel
            target_path = os.path.join(target_dir, file.filename)
            content = await file.read()
            with open(target_path, "wb") as f:
                f.write(content)
            uploaded_files.append({
                "filename": file.filename,
                "size": len(content),
                "type": ext[1:],
            })
            logger.info(f"Uploaded file: {file.filename} to {target_path}")
        
        # 更新项目源文件信息
        project_manager_v2.update_sources_from_filesystem(project_id)
        
        # 如果启用自动预处理，添加后台任务
        if auto_preprocess:
            background_tasks.add_task(preprocess_service.preprocess_project, project_id)
            logger.info(f"Scheduled preprocess task for project {project_id}")
        
        return {
            "message": "Files uploaded successfully",
            "files": uploaded_files,
            "auto_preprocess": auto_preprocess
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Preprocess Endpoints ============

class PreprocessTrigger(BaseModel):
    filename: Optional[str] = None
    category: Optional[str] = None

@router.post("/{project_id}/preprocess")
async def trigger_preprocess(
    project_id: str, 
    background_tasks: BackgroundTasks,
    payload: Optional[PreprocessTrigger] = None
):
    """
    手动触发预处理
    """
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    filename = payload.filename if payload else None
    category = payload.category if payload else None
    
    # 添加后台任务
    background_tasks.add_task(preprocess_service.preprocess_project, project_id, filename, category)
    
    return {
        "message": "Preprocessing started",
        "project_id": project_id,
        "file": filename or "ALL",
        "category": category
    }


@router.get("/{project_id}/preprocess/status")
async def get_preprocess_status(project_id: str):
    """
    获取预处理状态
    """
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "project_id": project_id,
        "preprocess_stage": meta.workflow_stages.preprocess.model_dump()
    }


@router.post("/{project_id}/preprocess/cancel")
async def cancel_preprocess(project_id: str):
    """
    取消预处理任务
    
    注意：由于使用了后台任务，无法真正取消正在运行的任务。
    此API将状态标记为cancelled，但任务可能仍在后台运行。
    """
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 检查当前状态
    if meta.workflow_stages.preprocess.status.value != 'running':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel preprocess in status: {meta.workflow_stages.preprocess.status.value}"
        )
    
    # 标记为失败状态（取消）
    from src.core.schemas_project import WorkflowStageStatus
    project_manager_v2.update_workflow_stage(
        project_id, 
        "preprocess", 
        WorkflowStageStatus.FAILED,
        error_message="Cancelled by user"
    )
    
    logger.info(f"Preprocess cancelled for project {project_id}")
    
    return {
        "message": "Preprocess task marked as cancelled",
        "project_id": project_id,
        "note": "Background task may still be running"
    }


# ============ Processed Data Endpoints ============

@router.get("/{project_id}/chapters")
async def get_project_chapters(project_id: str):
    """获取小说章节列表"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chapters = project_manager_v2.get_chapters(project_id)
    return {
        "total_chapters": len(chapters),
        "chapters": chapters
    }


@router.get("/{project_id}/chapters/{chapter_number}")
async def get_chapter_content(project_id: str, chapter_number: int):
    """获取章节内容"""
    from fastapi.responses import PlainTextResponse
    
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 读取小说原文（从 raw/novel 或 raw 根目录）
    novel_file = None
    raw_base = os.path.join(config.data_dir, "projects", project_id, "raw")
    
    # 优先从 raw/novel/ 查找
    raw_novel = os.path.join(raw_base, "novel")
    if os.path.exists(raw_novel):
        for filename in os.listdir(raw_novel):
            if filename.lower().endswith('.txt'):
                novel_file = os.path.join(raw_novel, filename)
                break
    
    # 兼容：从 raw/ 根目录查找
    if not novel_file and os.path.exists(raw_base):
        for filename in os.listdir(raw_base):
            if filename.lower().endswith('.txt'):
                novel_file = os.path.join(raw_base, filename)
                break
    
    if not novel_file or not os.path.exists(novel_file):
        raise HTTPException(status_code=404, detail="Novel file not found")
    
    # 获取章节信息
    chapters = project_manager_v2.get_chapters(project_id)
    chapter = next((ch for ch in chapters if ch.get("chapter_number") == chapter_number), None)
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    try:
        with open(novel_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start_line = chapter.get("start_line", 0)
        end_line = chapter.get("end_line", len(lines))
        
        chapter_content = ''.join(lines[start_line:end_line])
        
        # 格式化为markdown
        formatted_content = f"# {chapter.get('title', f'Chapter {chapter_number}')}\n\n{chapter_content}"
        
        return PlainTextResponse(formatted_content)
    except Exception as e:
        logger.error(f"Failed to read chapter {chapter_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/episodes")
async def get_project_episodes(project_id: str):
    """获取脚本集数列表"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    episodes = project_manager_v2.get_episodes(project_id)
    return {
        "total_episodes": len(episodes),
        "episodes": episodes
    }


@router.get("/{project_id}/episodes/{episode_name}")
async def get_episode_detail(project_id: str, episode_name: str):
    """获取单个集数的详细信息"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 读取导入后的数据
    processed_file = os.path.join(
        config.data_dir, 
        "projects", 
        project_id, 
        "analyst/import/script",
        f"{episode_name}.json"
    )
    
    if not os.path.exists(processed_file):
        raise HTTPException(status_code=404, detail="Episode not found")
    
    with open(processed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data
