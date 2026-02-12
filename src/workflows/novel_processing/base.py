import logging
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.core.interfaces import BaseWorkflow
from src.core.schemas_novel import (
    NovelProcessingConfig,
    NovelProcessingResult,
    ChapterProcessingError
)
from src.core.llm_rate_limiter import get_llm_manager
from src.workflows import report_generator

# Tools
from src.tools.novel_importer import NovelImporter
from src.tools.novel_metadata_extractor import NovelMetadataExtractor
from src.tools.novel_chapter_detector import NovelChapterDetector
from src.tools.novel_segmenter import NovelSegmenter
from src.tools.novel_annotator import NovelAnnotator
from src.tools.novel_system_analyzer import NovelSystemAnalyzer
from src.tools.novel_system_detector import NovelSystemDetector
from src.tools.novel_system_tracker import NovelSystemTracker
from src.tools.novel_validator import NovelValidator

logger = logging.getLogger(__name__)

class NovelProcessingWorkflowBase(BaseWorkflow):
    """
    小说处理工作流基类
    包含初始化、状态管理和辅助方法
    """
    
    name: str = "novel_processing_workflow"
    
    def __init__(self):
        super().__init__()
        
        # 初始化工具
        self.novel_importer = NovelImporter()
        self.metadata_extractor = NovelMetadataExtractor()
        self.chapter_detector = NovelChapterDetector()
        self.novel_segmenter = NovelSegmenter()
        self.novel_annotator = NovelAnnotator()
        self.system_analyzer = NovelSystemAnalyzer()
        self.system_detector = NovelSystemDetector()
        self.system_tracker = NovelSystemTracker()
        self.novel_validator = NovelValidator()
        
        # 初始化LLM调用管理器
        self.llm_manager = get_llm_manager()
        
        # 统计信息
        self.llm_calls_count = 0
        self.total_cost = 0.0
        self.start_time = 0.0
        
        logger.info(f"✅ {self.name} 初始化完成")

    def _estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        中文: 1字 ≈ 1.5 tokens
        英文: 1词 ≈ 1.3 tokens
        输出: 假设为输入的20%
        """
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        other_chars = len(text) - chinese_chars
        
        input_tokens = int(chinese_chars * 1.5 + other_chars * 0.3)
        output_tokens = int(input_tokens * 0.2)
        
        return input_tokens + output_tokens

    def _setup_processing_directory(self, project_name: str) -> str:
        """创建处理目录"""
        base_dir = Path("data") / "projects" / project_name / "processing"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (base_dir / "structured").mkdir(exist_ok=True)
        (base_dir / "structured" / "step4_segmentation").mkdir(exist_ok=True)
        (base_dir / "structured" / "step5_annotation").mkdir(exist_ok=True)
        (base_dir / "structured" / "step7_system_tracking").mkdir(exist_ok=True)
        (base_dir / "reports").mkdir(exist_ok=True)
        
        # 创建novel文件夹（存放可读Markdown）
        novel_dir = Path("data") / "projects" / project_name / "novel"
        novel_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建visualization文件夹（存放HTML查看器）
        viz_dir = Path("data") / "projects" / project_name / "visualization"
        viz_dir.mkdir(parents=True, exist_ok=True)
        
        return str(base_dir)

    def _save_intermediate_result(
        self,
        data: Any,
        filename: str,
        processing_dir: str
    ):
        """保存中间结果到structured子目录"""
        # 统一保存到structured子目录
        if not filename.startswith("structured/"):
            if filename.startswith("step"):
                filepath = Path(processing_dir) / "structured" / f"{filename}.json"
            else:
                filepath = Path(processing_dir) / f"{filename}.json"
        else:
            filepath = Path(processing_dir) / f"{filename}.json"
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if hasattr(data, 'model_dump'):
                json.dump(data.model_dump(), f, indent=2, ensure_ascii=False, default=str)
            else:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def _save_final_result(self, result: NovelProcessingResult, processing_dir: str):
        """
        保存最终结果（使用文件引用代替内容嵌入）
        """
        filepath = Path(processing_dir) / "final_result.json"
        
        # 构建轻量级结果（使用文件引用）
        lightweight_result = {
            "project_name": result.project_name,
            "workflow_version": result.workflow_version,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "completed_steps": result.completed_steps,
            
            # 元数据（体积小，内嵌）
            "import_result": result.import_result.model_dump() if result.import_result else None,
            "metadata": result.metadata.model_dump() if result.metadata else None,
            "chapters": [ch.model_dump() for ch in result.chapters],
            
            # 大体积数据使用引用
            "segmentation_results": {
                chapter_num: f"structured/step4_segmentation/chapter_{chapter_num:03d}.json"
                for chapter_num in result.segmentation_results.keys()
            },
            "annotation_results": {
                chapter_num: f"structured/step5_annotation/chapter_{chapter_num:03d}.json"
                for chapter_num in result.annotation_results.keys()
            },
            "system_catalog": "structured/step6_system_catalog.json" if result.system_catalog else None,
            "system_updates": {
                chapter_num: f"structured/step7_system_tracking/chapter_{chapter_num:03d}.json"
                for chapter_num in result.system_updates.keys()
            },
            "system_tracking": {
                chapter_num: f"structured/step7_system_tracking/chapter_{chapter_num:03d}.json"
                for chapter_num in result.system_tracking.keys()
            },
            "validation_report": "structured/step8_validation_report.json" if result.validation_report else None,
            
            # 统计信息（内嵌）
            "processing_stats": result.processing_stats,
            "processing_time": result.processing_time,
            "llm_calls_count": result.llm_calls_count,
            "total_cost": result.total_cost,
            "errors": [err.model_dump() for err in result.errors],
            
            # 辅助信息
            "intermediate_results_dir": result.intermediate_results_dir,
            "novel_markdown_dir": f"data/projects/{result.project_name}/novel",
            "visualization_dir": f"data/projects/{result.project_name}/visualization"
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(lightweight_result, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 最终结果已保存（引用方式）: {filepath}")

    def _calculate_stats(self, result: NovelProcessingResult) -> Dict[str, Any]:
        """计算统计信息"""
        return {
            "total_chapters": len(result.chapters),
            "successful_chapters": len(result.segmentation_results),
            "failed_chapters": len(result.chapters) - len(result.segmentation_results),
            "total_paragraphs": sum(
                len(seg.paragraphs) for seg in result.segmentation_results.values()
            ),
            "total_events": sum(
                len(ann.event_timeline.events) for ann in result.annotation_results.values()
            ),
            "total_settings": sum(
                len(ann.setting_library.settings) for ann in result.annotation_results.values()
            ),
            "avg_paragraphs_per_chapter": (
                sum(len(seg.paragraphs) for seg in result.segmentation_results.values()) /
                len(result.segmentation_results)
            ) if result.segmentation_results else 0
        }
