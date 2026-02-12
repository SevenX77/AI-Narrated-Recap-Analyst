"""
Analyst Results API Routes
Phase I 分析结果查询接口

提供Step 2/3/4的分析结果查询功能
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pathlib import Path

from src.core.config import config
from src.core.project_manager_v2 import project_manager_v2

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/projects", tags=["analyst-results"])


# ============ Helper Functions ============

def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_project_data_dir(project_id: str) -> Path:
    """获取项目数据目录"""
    meta = project_manager_v2.get_project(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return Path(config.data_dir) / "projects" / project_id


# ============ Step 2: Script Analysis APIs ============

@router.get("/{project_id}/analyst/script_analysis/{episode_id}/segmentation")
async def get_script_segmentation(project_id: str, episode_id: str):
    """
    获取Script分段结果
    
    Returns:
        {
            "episode_id": "ep01",
            "total_segments": 12,
            "segments": [...],
            "abc_distribution": {"A": 2, "B": 9, "C": 1}
        }
    """
    project_dir = get_project_data_dir(project_id)
    file_path = project_dir / "analyst" / "script_analysis" / f"{episode_id}_segmentation_latest.json"
    
    return load_json_file(str(file_path))


@router.get("/{project_id}/analyst/script_analysis/{episode_id}/hook")
async def get_script_hook(project_id: str, episode_id: str):
    """
    获取Hook检测结果（仅ep01）
    
    Returns:
        {
            "episode_id": "ep01",
            "has_hook": true,
            "hook_end_time": 45.6,
            "confidence": 0.92,
            "hook_segments": [...]
        }
    """
    project_dir = get_project_data_dir(project_id)
    file_path = project_dir / "analyst" / "script_analysis" / f"{episode_id}_hook_latest.json"
    
    return load_json_file(str(file_path))


@router.get("/{project_id}/analyst/script_analysis/{episode_id}/validation")
async def get_script_validation(project_id: str, episode_id: str):
    """
    获取质量报告
    
    Returns:
        {
            "episode_id": "ep01",
            "quality_score": 85,
            "issues": ["..."],
            "suggestions": ["..."]
        }
    """
    project_dir = get_project_data_dir(project_id)
    file_path = project_dir / "analyst" / "script_analysis" / f"{episode_id}_validation_latest.json"
    
    return load_json_file(str(file_path))


@router.get("/{project_id}/analyst/script_analysis/summary")
async def get_script_analysis_summary(project_id: str):
    """
    获取Script分析汇总统计
    
    Returns:
        {
            "total_episodes": 5,
            "total_segments": 120,
            "abc_distribution": {"A": 12, "B": 102, "C": 6},
            "average_quality_score": 85,
            "total_cost": 2.8
        }
    """
    project_dir = get_project_data_dir(project_id)
    script_analysis_dir = project_dir / "analyst" / "script_analysis"
    
    if not script_analysis_dir.exists():
        return {
            "total_episodes": 0,
            "total_segments": 0,
            "abc_distribution": {"A": 0, "B": 0, "C": 0},
            "average_quality_score": 0,
            "total_cost": 0
        }
    
    # 统计所有集数
    total_segments = 0
    abc_total = {"A": 0, "B": 0, "C": 0}
    quality_scores = []
    total_cost = 0.0
    episode_count = 0
    
    # 遍历所有segmentation文件
    for file_path in script_analysis_dir.glob("*_segmentation_latest.json"):
        try:
            data = load_json_file(str(file_path))
            episode_count += 1
            total_segments += data.get("total_segments", 0)
            
            # ABC分布
            abc_dist = data.get("abc_distribution", {})
            for category in ["A", "B", "C"]:
                abc_total[category] += abc_dist.get(category, 0)
            
            # 质量和成本
            if "quality_score" in data:
                quality_scores.append(data["quality_score"])
            if "metadata" in data and "total_cost" in data["metadata"]:
                total_cost += data["metadata"]["total_cost"]
                
        except Exception as e:
            logger.warning(f"Failed to process {file_path}: {e}")
            continue
    
    return {
        "total_episodes": episode_count,
        "total_segments": total_segments,
        "abc_distribution": abc_total,
        "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
        "total_cost": round(total_cost, 3)
    }


# ============ Step 3: Novel Analysis APIs ============

@router.get("/{project_id}/analyst/novel_analysis/chapters")
async def get_novel_analysis_chapters(project_id: str):
    """
    获取章节列表及状态
    
    Returns:
        {
            "chapters": [
                {
                    "chapter_id": "chapter_001",
                    "chapter_title": "第一章 末日降临",
                    "status": "completed",
                    "quality_score": 88,
                    "total_paragraphs": 50,
                    "total_events": 15,
                    "processed_at": "2026-02-12T20:00:00"
                }
            ]
        }
    """
    project_dir = get_project_data_dir(project_id)
    novel_analysis_dir = project_dir / "analyst" / "novel_analysis"
    
    if not novel_analysis_dir.exists():
        return {"chapters": []}
    
    chapters = []
    
    # 遍历所有segmentation文件
    for file_path in sorted(novel_analysis_dir.glob("chapter_*_segmentation_latest.json")):
        try:
            data = load_json_file(str(file_path))
            chapter_id = data.get("chapter_id", file_path.stem.replace("_segmentation_latest", ""))
            
            # 尝试读取validation数据
            validation_path = novel_analysis_dir / f"{chapter_id}_validation_latest.json"
            quality_score = None
            if validation_path.exists():
                validation_data = load_json_file(str(validation_path))
                quality_score = validation_data.get("quality_score")
            
            # 尝试读取annotation数据
            annotation_path = novel_analysis_dir / f"{chapter_id}_annotation_latest.json"
            total_events = 0
            if annotation_path.exists():
                annotation_data = load_json_file(str(annotation_path))
                total_events = len(annotation_data.get("event_timeline", []))
            
            chapters.append({
                "chapter_id": chapter_id,
                "chapter_title": data.get("chapter_title", f"Chapter {chapter_id}"),
                "status": "completed",  # TODO: 从meta.json读取实际状态
                "quality_score": quality_score,
                "total_paragraphs": data.get("total_paragraphs", 0),
                "total_events": total_events,
                "processed_at": data.get("metadata", {}).get("timestamp")
            })
            
        except Exception as e:
            logger.warning(f"Failed to process {file_path}: {e}")
            continue
    
    return {"chapters": chapters}


@router.get("/{project_id}/analyst/novel_analysis/{chapter_id}/segmentation")
async def get_novel_segmentation(project_id: str, chapter_id: str):
    """
    获取单章分段结果
    
    Returns:
        {
            "chapter_id": "chapter_001",
            "chapter_title": "第一章 末日降临",
            "total_paragraphs": 50,
            "paragraphs": [...],
            "category_distribution": {"narrative": 40, "dialogue": 8, ...}
        }
    """
    project_dir = get_project_data_dir(project_id)
    file_path = project_dir / "analyst" / "novel_analysis" / f"{chapter_id}_segmentation_latest.json"
    
    data = load_json_file(str(file_path))
    
    # 计算category分布
    category_dist = {}
    for paragraph in data.get("paragraphs", []):
        category = paragraph.get("category", "unknown")
        category_dist[category] = category_dist.get(category, 0) + 1
    
    data["category_distribution"] = category_dist
    return data


@router.get("/{project_id}/analyst/novel_analysis/{chapter_id}/annotation")
async def get_novel_annotation(project_id: str, chapter_id: str):
    """
    获取单章标注结果（事件时间线+设定库）
    
    Returns:
        {
            "chapter_id": "chapter_001",
            "event_timeline": [...],
            "setting_library": [...]
        }
    """
    project_dir = get_project_data_dir(project_id)
    file_path = project_dir / "analyst" / "novel_analysis" / f"{chapter_id}_annotation_latest.json"
    
    return load_json_file(str(file_path))


@router.get("/{project_id}/analyst/novel_analysis/system_catalog")
async def get_system_catalog(project_id: str):
    """
    获取系统元素目录
    
    Returns:
        {
            "system_name": "序列公路求生系统",
            "categories": {
                "player_stats": [...],
                "items": [...],
                "skills": [...]
            }
        }
    """
    project_dir = get_project_data_dir(project_id)
    file_path = project_dir / "analyst" / "novel_analysis" / "system_catalog_latest.json"
    
    return load_json_file(str(file_path))


@router.get("/{project_id}/analyst/novel_analysis/{chapter_id}/validation")
async def get_novel_validation(project_id: str, chapter_id: str):
    """
    获取质量报告
    
    Returns:
        {
            "chapter_id": "chapter_001",
            "quality_score": 88,
            "issues": [...],
            "suggestions": [...]
        }
    """
    project_dir = get_project_data_dir(project_id)
    file_path = project_dir / "analyst" / "novel_analysis" / f"{chapter_id}_validation_latest.json"
    
    return load_json_file(str(file_path))


# ============ Step 4: Alignment APIs ============

@router.get("/{project_id}/analyst/alignment/pairs")
async def get_alignment_pairs(project_id: str):
    """
    获取所有对齐对列表
    
    Returns:
        {
            "pairs": [
                {
                    "chapter_id": "chapter_001",
                    "episode_id": "ep01",
                    "status": "completed",
                    "quality_score": 90
                }
            ]
        }
    """
    project_dir = get_project_data_dir(project_id)
    alignment_dir = project_dir / "analyst" / "alignment"
    
    if not alignment_dir.exists():
        return {"pairs": []}
    
    pairs = []
    
    # 遍历所有alignment文件
    for file_path in sorted(alignment_dir.glob("*_alignment_latest.json")):
        try:
            data = load_json_file(str(file_path))
            
            pairs.append({
                "chapter_id": data.get("chapter_id"),
                "episode_id": data.get("episode_id"),
                "status": "completed",
                "quality_score": data.get("quality_score")
            })
            
        except Exception as e:
            logger.warning(f"Failed to process {file_path}: {e}")
            continue
    
    return {"pairs": pairs}


@router.get("/{project_id}/analyst/alignment/{chapter_id}/{episode_id}")
async def get_alignment_result(project_id: str, chapter_id: str, episode_id: str):
    """
    获取单对的对齐详情
    
    Returns:
        {
            "chapter_id": "chapter_001",
            "episode_id": "ep01",
            "alignments": [...],
            "coverage": {...},
            "type_matching": {...}
        }
    """
    project_dir = get_project_data_dir(project_id)
    file_path = project_dir / "analyst" / "alignment" / f"{chapter_id}_{episode_id}_alignment_latest.json"
    
    return load_json_file(str(file_path))
