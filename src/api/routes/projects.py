from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import os
import shutil
from src.api.schemas.project import ProjectResponse, ProjectList, ProjectStats, ProjectCreate
from src.core.project_manager import project_manager
from src.core.config import config
from src.utils.logger import logger

router = APIRouter()

@router.get("", response_model=ProjectList)
async def list_projects():
    """获取所有项目列表"""
    try:
        projects = project_manager.list_projects()
        return ProjectList(
            projects=[ProjectResponse(**proj) for proj in projects],
            total=len(projects)
        )
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=ProjectStats)
async def get_project_stats():
    """获取项目统计信息"""
    try:
        projects = project_manager.list_projects()
        return ProjectStats(
            total_projects=len(projects),
            initialized=sum(1 for p in projects if p.get('status') == 'initialized'),
            discovered=sum(1 for p in projects if p.get('status') == 'discovered')
        )
    except Exception as e:
        logger.error(f"Failed to get project stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """获取项目详情"""
    project = project_manager.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(id=project_id, **project)

@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """创建新项目"""
    try:
        # 生成新的项目ID
        new_id = f"PROJ_{project_manager.next_id:03d}"
        project_manager.next_id += 1
        
        # 创建项目目录
        project_source_path = os.path.join(config.analysis_source_dir, project.name)
        os.makedirs(project_source_path, exist_ok=True)
        os.makedirs(os.path.join(project_source_path, "novel"), exist_ok=True)
        os.makedirs(os.path.join(project_source_path, "srt"), exist_ok=True)
        
        # 添加到项目索引
        from datetime import datetime
        project_manager.projects[new_id] = {
            "name": project.name,
            "source_path": project_source_path,
            "created_at": datetime.now().isoformat(),
            "status": "discovered"
        }
        project_manager._save_index()
        
        logger.info(f"Created new project: {project.name} -> {new_id}")
        
        return ProjectResponse(id=new_id, **project_manager.projects[new_id])
    
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/upload")
async def upload_files(project_id: str, files: List[UploadFile] = File(...)):
    """上传项目文件"""
    project = project_manager.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    source_path = project['source_path']
    uploaded_files = []
    
    try:
        for file in files:
            # 根据文件类型保存到不同目录
            if file.filename.endswith('.txt'):
                target_dir = os.path.join(source_path, "novel")
                target_path = os.path.join(target_dir, file.filename)
            elif file.filename.endswith('.srt'):
                target_dir = os.path.join(source_path, "srt")
                target_path = os.path.join(target_dir, file.filename)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
            
            os.makedirs(target_dir, exist_ok=True)
            
            # 保存文件
            with open(target_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            uploaded_files.append(file.filename)
            logger.info(f"Uploaded file: {file.filename} to {target_path}")
        
        return {
            "message": "Files uploaded successfully",
            "files": uploaded_files
        }
    
    except Exception as e:
        logger.error(f"Failed to upload files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/initialize")
async def initialize_project(project_id: str):
    """初始化项目"""
    success = project_manager.initialize_project(project_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to initialize project")
    
    project = project_manager.projects.get(project_id)
    return ProjectResponse(id=project_id, **project)

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    project = project_manager.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # 删除源目录
        if os.path.exists(project['source_path']):
            shutil.rmtree(project['source_path'])
        
        # 删除数据目录
        project_data_path = os.path.join(config.data_dir, "projects", project_id)
        if os.path.exists(project_data_path):
            shutil.rmtree(project_data_path)
        
        # 从索引中移除
        del project_manager.projects[project_id]
        project_manager._save_index()
        
        logger.info(f"Deleted project: {project_id}")
        
        return {"message": "Project deleted successfully"}
    
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
