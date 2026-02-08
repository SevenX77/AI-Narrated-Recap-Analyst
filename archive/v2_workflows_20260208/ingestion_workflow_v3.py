"""
Ingestion Workflow V3 - Hook-Body分离架构

实现Phase分割：
    Phase 0: Novel预处理（一次性）
    Phase 1: Hook分析（仅ep01）
    Phase 2: Body对齐（所有集数）
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from src.core.interfaces import BaseWorkflow
from src.core.project_manager import project_manager
from src.core.config import config
from src.agents.deepseek_analyst import get_llm_client
from src.modules.alignment.novel_preprocessor import NovelPreprocessor, preprocess_novel_file
from src.modules.alignment.body_start_detector import BodyStartDetector
from src.modules.alignment.hook_content_extractor import HookContentExtractor
from src.modules.alignment.layered_alignment_engine import LayeredAlignmentEngine
from src.utils.logger import logger

logger = logging.getLogger(__name__)


class IngestionWorkflowV3(BaseWorkflow):
    """
    Ingestion Workflow V3 - Hook-Body分离架构
    
    核心改进：
        1. 完全抛弃 Sentence → SemanticBlock → Event 中间层
        2. Hook与Body完全分离处理
        3. 支持独立执行各Phase
        4. 直接从原始文本提取Plot Nodes
    """
    
    def __init__(self, project_id: str):
        """
        初始化Workflow
        
        Args:
            project_id: 项目ID（如 "PROJ_002"）
        """
        super().__init__()
        self.project_id = project_id
        self.paths = project_manager.get_project_paths(project_id)
        self.client = get_llm_client()
        
        # 初始化模块
        self.novel_preprocessor = NovelPreprocessor()
        self.body_detector = BodyStartDetector(self.client)
        self.hook_extractor = HookContentExtractor(self.client)
        self.layered_aligner = LayeredAlignmentEngine(self.client)
        
        logger.info(f"✅ IngestionWorkflowV3 初始化完成: {project_id}")
    
    # ═══════════════════════════════════════════════════════════
    # Phase 0: Novel预处理（一次性，全局）
    # ═══════════════════════════════════════════════════════════
    
    async def preprocess_novel(self) -> Dict:
        """
        预处理Novel：提取简介和章节索引
        
        输出文件：
            - preprocessing/novel_introduction_clean.txt
            - preprocessing/novel_chapters_index.json
        
        Returns:
            预处理结果摘要
        """
        logger.info("=" * 60)
        logger.info("Phase 0: Novel预处理")
        logger.info("=" * 60)
        
        novel_path = os.path.join(self.paths['raw'], 'novel.txt')
        
        if not os.path.exists(novel_path):
            raise FileNotFoundError(f"Novel文件不存在: {novel_path}")
        
        # 创建preprocessing目录
        preprocessing_dir = os.path.join(
            os.path.dirname(self.paths['raw']),
            'preprocessing'
        )
        os.makedirs(preprocessing_dir, exist_ok=True)
        
        # 输出路径
        output_intro = os.path.join(preprocessing_dir, 'novel_introduction_clean.txt')
        output_index = os.path.join(preprocessing_dir, 'novel_chapters_index.json')
        
        # 执行预处理
        result = preprocess_novel_file(
            novel_path=novel_path,
            output_intro_path=output_intro,
            output_index_path=output_index
        )
        
        logger.info("✅ Phase 0 完成")
        return result
    
    # ═══════════════════════════════════════════════════════════
    # Phase 1: Hook分析（仅ep01，独立流程）
    # ═══════════════════════════════════════════════════════════
    
    async def analyze_hook(self, episode: str = "ep01") -> Dict:
        """
        分析Hook：检测边界 + 提取内容 + 计算相似度
        
        前置条件：
            - preprocessing/novel_introduction_clean.txt 已存在
            - raw/{episode}.srt 已存在
        
        输出文件：
            - hook_analysis/{episode}_hook_analysis.json
        
        Returns:
            Hook分析结果
        """
        logger.info("=" * 60)
        logger.info(f"Phase 1: Hook分析 - {episode}")
        logger.info("=" * 60)
        
        # Step 1: 检查前置条件
        srt_path = os.path.join(self.paths['raw'], f'{episode}.srt')
        intro_path = os.path.join(
            os.path.dirname(self.paths['raw']),
            'preprocessing/novel_introduction_clean.txt'
        )
        
        if not os.path.exists(srt_path):
            raise FileNotFoundError(f"SRT文件不存在: {srt_path}")
        
        if not os.path.exists(intro_path):
            logger.warning("简介文件不存在，先执行preprocess_novel")
            await self.preprocess_novel()
        
        # Step 2: 读取文件
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_text = f.read()
        
        with open(intro_path, 'r', encoding='utf-8') as f:
            intro_text = f.read()
        
        # Step 3: 读取Novel前5章（用于参考）
        novel_path = os.path.join(self.paths['raw'], 'novel.txt')
        with open(novel_path, 'r', encoding='utf-8') as f:
            novel_text = f.read()
        
        # 简单提取前5000字作为章节概要
        novel_preview = novel_text[:5000]
        
        # Step 4: 检测Body起点
        logger.info("Step 1.1: 检测Body起点...")
        body_detection = self.body_detector.detect_body_start(
            script_srt_text=srt_text,
            novel_chapters_text=novel_preview,
            max_check_duration=90
        )
        
        # Step 5: 提取Hook内容（如果存在）
        hook_content = None
        intro_similarity = 0.0
        
        if body_detection.has_hook:
            logger.info("Step 1.2: 提取Hook内容...")
            
            # 分离Hook部分
            hook_srt = self.body_detector.filter_srt_by_time(
                srt_text=srt_text,
                start_time=None,
                end_time=body_detection.body_start_time
            )
            
            # 提取Hook分层内容
            hook_content_obj = self.hook_extractor.extract_hook_content(
                hook_srt_text=hook_srt,
                hook_time_range=f"00:00:00,000 - {body_detection.body_start_time}"
            )
            
            # 提取简介分层内容
            intro_content_obj = self.hook_extractor.extract_hook_content(
                hook_srt_text=intro_text,  # 简介文本当作"伪SRT"处理
                hook_time_range="introduction"
            )
            
            # 计算相似度
            logger.info("Step 1.3: 计算与简介的相似度...")
            intro_similarity = self.hook_extractor.calculate_intro_similarity(
                hook_content=hook_content_obj,
                intro_content=intro_content_obj
            )
            
            hook_content = hook_content_obj.to_dict()
        else:
            logger.info("未检测到Hook，跳过Hook内容提取")
        
        # Step 6: 组装结果
        hook_analysis = {
            "episode": episode,
            "detection": body_detection.to_dict(),
            "hook_content": hook_content,
            "intro_similarity": intro_similarity,
            "source_analysis": {
                "inferred_source": "简介" if intro_similarity > 0.7 else "独立内容/前N章",
                "note": f"Hook与简介相似度: {intro_similarity:.2f}"
            },
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
        # Step 7: 保存结果
        hook_analysis_dir = os.path.join(
            os.path.dirname(self.paths['raw']),
            'hook_analysis'
        )
        os.makedirs(hook_analysis_dir, exist_ok=True)
        
        output_path = os.path.join(hook_analysis_dir, f'{episode}_hook_analysis.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(hook_analysis, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Phase 1 完成，结果已保存: {output_path}")
        
        return hook_analysis
    
    # ═══════════════════════════════════════════════════════════
    # Phase 2: Body对齐（所有集数，独立流程）
    # ═══════════════════════════════════════════════════════════
    
    async def align_body(self, episode: str) -> Dict:
        """
        Body部分的分层提取与对齐
        
        前置条件：
            - preprocessing/novel_chapters_index.json 已存在
            - 如果episode="ep01": hook_analysis/ep01_hook_analysis.json 已存在
        
        输出文件：
            - alignment/{episode}_body_alignment.json
        
        Returns:
            Body对齐结果
        """
        logger.info("=" * 60)
        logger.info(f"Phase 2: Body对齐 - {episode}")
        logger.info("=" * 60)
        
        # Step 1: 读取SRT
        srt_path = os.path.join(self.paths['raw'], f'{episode}.srt')
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_text = f.read()
        
        # Step 2: 如果是ep01，从body_start_time开始；否则使用完整SRT
        if episode == "ep01":
            hook_analysis_path = os.path.join(
                os.path.dirname(self.paths['raw']),
                'hook_analysis/ep01_hook_analysis.json'
            )
            
            if os.path.exists(hook_analysis_path):
                with open(hook_analysis_path, 'r', encoding='utf-8') as f:
                    hook_analysis = json.load(f)
                
                body_start_time = hook_analysis['detection']['body_start_time']
                
                # 过滤SRT
                srt_text = self.body_detector.filter_srt_by_time(
                    srt_text=srt_text,
                    start_time=body_start_time,
                    end_time=None
                )
                
                logger.info(f"  ep01: 从 {body_start_time} 开始提取Body")
            else:
                logger.warning(f"未找到Hook分析结果: {hook_analysis_path}")
                logger.warning("使用完整SRT（建议先运行 analyze_hook）")
        else:
            logger.info(f"  {episode}: 使用完整SRT")
        
        # Step 3: 读取Novel章节文本（移除简介）
        novel_path = os.path.join(self.paths['raw'], 'novel.txt')
        with open(novel_path, 'r', encoding='utf-8') as f:
            novel_full_text = f.read()
        
        # 定位第1章后的内容
        intro_path = os.path.join(
            os.path.dirname(self.paths['raw']),
            'preprocessing/novel_chapters_index.json'
        )
        
        if os.path.exists(intro_path):
            with open(intro_path, 'r', encoding='utf-8') as f:
                chapters_index = json.load(f)
            
            if chapters_index:
                first_chapter_line = chapters_index[0]['start_line']
                novel_lines = novel_full_text.split('\n')
                novel_chapters_text = '\n'.join(novel_lines[first_chapter_line:])
            else:
                novel_chapters_text = novel_full_text
        else:
            logger.warning("未找到章节索引，使用完整Novel文本")
            novel_chapters_text = novel_full_text
        
        # Step 4: 分层提取与对齐
        logger.info("Step 2.1: 执行分层对齐...")
        
        # 计算Script时间范围
        script_time_range = "00:00:00,000 - End"
        if episode == "ep01" and os.path.exists(hook_analysis_path):
            with open(hook_analysis_path, 'r', encoding='utf-8') as f:
                hook_analysis = json.load(f)
            body_start = hook_analysis['detection']['body_start_time']
            script_time_range = f"{body_start} - End"
        
        alignment_result = await self.layered_aligner.align(
            script_srt_text=srt_text,
            novel_chapters_text=novel_chapters_text,
            episode=episode,
            script_time_range=script_time_range
        )
        
        body_alignment = alignment_result.to_dict()
        
        # Step 4: 保存结果
        output_path = os.path.join(
            self.paths['alignment'],
            f'{episode}_body_alignment.json'
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(body_alignment, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Phase 2 完成，结果已保存: {output_path}")
        
        return body_alignment
    
    # ═══════════════════════════════════════════════════════════
    # 便捷方法：一键运行完整流程
    # ═══════════════════════════════════════════════════════════
    
    async def run(self, episodes: Optional[List[str]] = None, **kwargs):
        """
        运行完整的Ingestion流程
        
        Args:
            episodes: 待处理的集数列表，如 ["ep01", "ep02"]
                     如果为None，自动检测raw目录中的所有SRT文件
            **kwargs: 其他参数（保留用于扩展）
        
        流程：
            Phase 0: 预处理Novel
            Phase 1: 分析ep01 Hook（如果ep01在episodes中）
            Phase 2: 对齐所有episodes的Body
        """
        logger.info("=" * 60)
        logger.info(f"开始完整Ingestion流程: {self.project_id}")
        logger.info("=" * 60)
        
        # 自动检测episodes
        if episodes is None:
            import glob
            srt_files = sorted(glob.glob(os.path.join(self.paths['raw'], "*.srt")))
            episodes = [os.path.basename(f).replace('.srt', '') for f in srt_files]
            logger.info(f"自动检测到 {len(episodes)} 个集数: {episodes}")
        
        logger.info(f"待处理集数: {episodes}")
        
        # Phase 0: 预处理Novel
        logger.info("\n" + "=" * 60)
        await self.preprocess_novel()
        
        # Phase 1: 分析Hook（仅ep01）
        if "ep01" in episodes:
            logger.info("\n" + "=" * 60)
            await self.analyze_hook("ep01")
        
        # Phase 2: 对齐Body（所有集数）
        for episode in episodes:
            logger.info("\n" + "=" * 60)
            await self.align_body(episode)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 完整Ingestion流程完成")
        logger.info("=" * 60)
        
        return {
            "project_id": self.project_id,
            "episodes_processed": episodes,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    
    # ═══════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════
    
    def _create_directory(self, dir_path: str):
        """创建目录（如果不存在）"""
        Path(dir_path).mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# 使用示例
# ═══════════════════════════════════════════════════════════

async def main():
    """
    使用示例
    """
    workflow = IngestionWorkflowV3("PROJ_002")
    
    # 方式1: 一键运行完整流程
    await workflow.run(episodes=["ep01", "ep02", "ep03"])
    
    # 方式2: 分阶段运行
    # await workflow.preprocess_novel()
    # await workflow.analyze_hook("ep01")
    # await workflow.align_body("ep01")
    # await workflow.align_body("ep02")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
