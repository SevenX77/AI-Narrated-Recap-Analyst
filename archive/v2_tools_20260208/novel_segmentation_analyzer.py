"""
Novel Segmentation Analysis Tool
小说分段分析工具

使用LLM对小说章节进行深度分析，提取多维度标签和结构化信息。
"""

import json
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI

from src.core.interfaces import BaseTool
from src.core.config import config
from src.core.schemas_segmentation import (
    ChapterAnalysis,
    NovelSegment,
    SegmentTags,
    SegmentMetadata,
    ForeshadowingInfo,
    ChapterSummary
)
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class NovelSegmentationAnalyzer(BaseTool):
    """
    小说分段分析工具
    
    对小说章节进行细粒度分析，为每个自然段标注多维度标签。
    全程使用LLM进行语义理解，而非硬规则。
    
    输出结构化的ChapterAnalysis，用于指导Script改写。
    """
    
    name = "novel_segmentation_analyzer"
    description = "Analyze novel chapters with multi-dimensional tags using LLM"
    
    def __init__(self):
        """初始化分析器"""
        self.prompt_config = load_prompts("novel_segmentation_analysis")
        self.llm_client = OpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url
        )
        logger.info(f"Initialized {self.name} with model: {config.llm.model}")
    
    def execute(
        self,
        chapter_text: str,
        chapter_id: str,
        chapter_title: Optional[str] = None,
        character_list: Optional[List[str]] = None,
        world_settings: Optional[Dict[str, Any]] = None,
        previous_summary: Optional[str] = None
    ) -> ChapterAnalysis:
        """
        执行章节分析
        
        Args:
            chapter_text: 章节原文（已分段的自然段落）
            chapter_id: 章节ID（如 "chpt_0001"）
            chapter_title: 章节标题（可选）
            character_list: 已知角色列表（可选）
            world_settings: 世界观设定（可选）
            previous_summary: 上一章摘要（可选）
        
        Returns:
            ChapterAnalysis: 结构化的章节分析结果
        
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当LLM调用失败时
        """
        if not chapter_text.strip():
            raise ValueError("chapter_text cannot be empty")
        
        logger.info(f"Starting analysis for {chapter_id}")
        
        # 1. 准备提示词
        prompt = self._prepare_prompt(
            chapter_text=chapter_text,
            chapter_id=chapter_id,
            chapter_title=chapter_title or "未命名章节",
            character_list=character_list or [],
            world_settings=world_settings or {},
            previous_summary=previous_summary or "无"
        )
        
        # 2. 调用LLM分析
        try:
            analysis_result = self._call_llm(prompt)
        except Exception as e:
            logger.error(f"LLM call failed for {chapter_id}: {e}")
            raise RuntimeError(f"LLM analysis failed: {e}")
        
        # 3. 解析并验证结果
        try:
            chapter_analysis = self._parse_result(analysis_result)
            logger.info(f"Successfully analyzed {chapter_id}: {len(chapter_analysis.segments)} segments")
            return chapter_analysis
        except Exception as e:
            logger.error(f"Failed to parse LLM result for {chapter_id}: {e}")
            logger.debug(f"Raw LLM output: {analysis_result}")
            raise RuntimeError(f"Result parsing failed: {e}")
    
    def _prepare_prompt(
        self,
        chapter_text: str,
        chapter_id: str,
        chapter_title: str,
        character_list: List[str],
        world_settings: Dict[str, Any],
        previous_summary: str
    ) -> str:
        """准备完整的提示词"""
        user_prompt_template = self.prompt_config["novel_segmentation_analysis"]["user"]
        
        # 格式化上下文信息
        character_str = ", ".join(character_list) if character_list else "暂无"
        world_str = json.dumps(world_settings, ensure_ascii=False, indent=2) if world_settings else "暂无"
        
        # 填充模板
        user_prompt = user_prompt_template.format(
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            chapter_text=chapter_text,
            character_list=character_str,
            world_settings=world_str,
            previous_summary=previous_summary
        )
        
        return user_prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM进行分析"""
        system_prompt = self.prompt_config["novel_segmentation_analysis"]["system"]
        temperature = self.prompt_config["novel_segmentation_analysis"].get("temperature", 0.3)
        max_tokens = self.prompt_config["novel_segmentation_analysis"].get("max_tokens", 8000)
        
        logger.debug(f"Calling LLM with temperature={temperature}, max_tokens={max_tokens}")
        
        response = self.llm_client.chat.completions.create(
            model=config.llm.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        result = response.choices[0].message.content.strip()
        
        # 移除可能的markdown代码块标记
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        
        return result.strip()
    
    def _parse_result(self, raw_result: str) -> ChapterAnalysis:
        """解析LLM返回的JSON结果"""
        try:
            data = json.loads(raw_result)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.debug(f"Raw result: {raw_result[:500]}...")
            raise ValueError(f"Invalid JSON from LLM: {e}")
        
        # 解析segments
        segments = []
        for seg_data in data.get("segments", []):
            # 解析tags
            tags_data = seg_data.get("tags", {})
            tags = SegmentTags(
                narrative_function=tags_data.get("narrative_function", []),
                structure=tags_data.get("structure", []),
                character=tags_data.get("character", []),
                priority=tags_data.get("priority", "P1-血肉"),
                location=tags_data.get("location"),
                time=tags_data.get("time")
            )
            
            # 解析metadata
            meta_data = seg_data.get("metadata", {})
            foreshadowing_data = meta_data.get("foreshadowing")
            foreshadowing = None
            if foreshadowing_data and isinstance(foreshadowing_data, dict):
                # 只有当foreshadowing_data是有效字典且包含必要字段时才创建
                if foreshadowing_data.get("type") and foreshadowing_data.get("content"):
                    foreshadowing = ForeshadowingInfo(
                        type=foreshadowing_data.get("type", "埋设"),
                        content=foreshadowing_data.get("content", ""),
                        reference_id=foreshadowing_data.get("reference_id"),
                        resolution_chapter=foreshadowing_data.get("resolution_chapter")
                    )
            
            metadata = SegmentMetadata(
                is_first_appearance=meta_data.get("is_first_appearance", False),
                repetition_count=meta_data.get("repetition_count", 0),
                foreshadowing=foreshadowing,
                condensation_suggestion=meta_data.get("condensation_suggestion", ""),
                word_count=meta_data.get("word_count", len(seg_data.get("text", "")))
            )
            
            # 创建NovelSegment
            segment = NovelSegment(
                segment_id=seg_data.get("segment_id", f"seg_unknown_{len(segments)}"),
                text=seg_data.get("text", ""),
                tags=tags,
                metadata=metadata
            )
            segments.append(segment)
        
        # 解析chapter_summary
        summary_data = data.get("chapter_summary", {})
        chapter_summary = ChapterSummary(
            total_segments=summary_data.get("total_segments", len(segments)),
            p0_count=summary_data.get("p0_count", 0),
            p1_count=summary_data.get("p1_count", 0),
            p2_count=summary_data.get("p2_count", 0),
            key_events=summary_data.get("key_events", []),
            foreshadowing_planted=summary_data.get("foreshadowing_planted", []),
            foreshadowing_resolved=summary_data.get("foreshadowing_resolved", []),
            characters_introduced=summary_data.get("characters_introduced", []),
            condensed_version=summary_data.get("condensed_version")
        )
        
        # 创建ChapterAnalysis
        analysis = ChapterAnalysis(
            chapter_id=data.get("chapter_id", "unknown"),
            chapter_title=data.get("chapter_title"),
            segments=segments,
            chapter_summary=chapter_summary
        )
        
        return analysis
    
    def validate_inputs(
        self,
        chapter_text: str,
        chapter_id: str,
        **kwargs
    ) -> bool:
        """验证输入参数"""
        if not chapter_text or not chapter_text.strip():
            logger.error("chapter_text is empty")
            return False
        
        if not chapter_id or not chapter_id.strip():
            logger.error("chapter_id is empty")
            return False
        
        if len(chapter_text) > 50000:
            logger.warning(f"chapter_text is very long ({len(chapter_text)} chars), may exceed token limit")
        
        return True


# 导出
__all__ = ["NovelSegmentationAnalyzer"]
