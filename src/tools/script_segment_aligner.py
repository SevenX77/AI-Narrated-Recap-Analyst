"""
Script Segment Aligner Tool
Script段落对齐工具

将Script的每一段精确对齐到小说分段分析，分析改编手法和浓缩策略。
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI

from src.core.interfaces import BaseTool
from src.core.config import config
from src.core.schemas_segmentation import (
    AlignmentResult,
    ScriptToNovelAlignment,
    ScriptSegmentInfo,
    NovelSourceInfo,
    AlignmentAnalysis,
    AlignmentOverallStats,
    ChapterAnalysis
)
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class ScriptSegmentAligner(BaseTool):
    """
    Script段落对齐工具
    
    将Script的每一段与小说分段分析进行精确对齐，输出：
    1. 对应关系（segment_id映射）
    2. 浓缩比例分析
    3. 改编技巧识别
    4. 质量评估
    
    全程使用LLM进行语义理解和对齐。
    """
    
    name = "script_segment_aligner"
    description = "Align script segments to novel analysis with adaptation analysis"
    
    def __init__(self):
        """初始化对齐器"""
        self.prompt_config = load_prompts("script_alignment_analysis")
        self.llm_client = OpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url
        )
        logger.info(f"Initialized {self.name} with model: {config.llm.model}")
    
    def execute(
        self,
        script_text: str,
        novel_analyses: List[ChapterAnalysis],
        episode_id: str
    ) -> AlignmentResult:
        """
        执行Script-Novel对齐
        
        Args:
            script_text: Script原文（markdown格式）
            novel_analyses: 小说分段分析结果列表
            episode_id: 集数ID（如 "ep01"）
        
        Returns:
            AlignmentResult: 完整对齐结果
        
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当LLM调用失败时
        """
        if not script_text.strip():
            raise ValueError("script_text cannot be empty")
        
        if not novel_analyses:
            raise ValueError("novel_analyses cannot be empty")
        
        logger.info(f"Starting alignment for {episode_id}")
        
        # 1. 解析Script段落
        script_segments = self._parse_script_segments(script_text)
        logger.info(f"Parsed {len(script_segments)} script segments")
        
        # 2. 准备小说分析数据
        novel_data = self._prepare_novel_data(novel_analyses)
        
        # 3. 逐段对齐分析
        alignments = []
        for i, script_seg in enumerate(script_segments):
            logger.info(f"Aligning segment {i+1}/{len(script_segments)}: {script_seg['time_range']}")
            try:
                alignment = self._align_single_segment(script_seg, novel_data)
                alignments.append(alignment)
            except Exception as e:
                logger.error(f"Failed to align segment {i+1}: {e}")
                # 创建一个空的对齐结果
                alignments.append(self._create_fallback_alignment(script_seg))
        
        # 4. 计算整体统计
        overall_stats = self._calculate_overall_stats(alignments, novel_analyses)
        
        # 5. 构建完整结果
        result = AlignmentResult(
            episode_id=episode_id,
            alignments=alignments,
            overall_stats=overall_stats
        )
        
        logger.info(f"Alignment completed for {episode_id}: {len(alignments)} segments aligned")
        return result
    
    def _parse_script_segments(self, script_text: str) -> List[Dict[str, Any]]:
        """解析Script段落"""
        segments = []
        
        # 按 ## [时间范围] 分割
        pattern = r'## \[([\d:,\s\-]+)\]\s*\n\n(.*?)(?=\n\n## \[|$)'
        matches = re.findall(pattern, script_text, re.DOTALL)
        
        for time_range, content in matches:
            # 判断段落类型
            segment_type = "Hook" if time_range.startswith("00:00:00") and len(segments) == 0 else "Body"
            
            segments.append({
                "time_range": time_range.strip(),
                "text": content.strip(),
                "segment_type": segment_type,
                "word_count": len(content.strip())
            })
        
        return segments
    
    def _prepare_novel_data(self, novel_analyses: List[ChapterAnalysis]) -> str:
        """准备小说分析数据（JSON格式）"""
        # 简化小说分析数据，只保留关键信息
        simplified_data = []
        
        for chapter in novel_analyses:
            chapter_data = {
                "chapter_id": chapter.chapter_id,
                "chapter_title": chapter.chapter_title,
                "segments": []
            }
            
            for seg in chapter.segments:
                seg_data = {
                    "segment_id": seg.segment_id,
                    "text": seg.text[:200] + "..." if len(seg.text) > 200 else seg.text,  # 截断长文本
                    "tags": {
                        "narrative_function": seg.tags.narrative_function,
                        "structure": seg.tags.structure,
                        "character": seg.tags.character,
                        "priority": seg.tags.priority,
                        "location": seg.tags.location,
                        "time": seg.tags.time
                    },
                    "metadata": {
                        "is_first_appearance": seg.metadata.is_first_appearance,
                        "repetition_count": seg.metadata.repetition_count,
                        "condensation_suggestion": seg.metadata.condensation_suggestion,
                        "word_count": seg.metadata.word_count
                    }
                }
                chapter_data["segments"].append(seg_data)
            
            simplified_data.append(chapter_data)
        
        return json.dumps(simplified_data, ensure_ascii=False, indent=2)
    
    def _align_single_segment(
        self,
        script_seg: Dict[str, Any],
        novel_data: str
    ) -> ScriptToNovelAlignment:
        """对齐单个Script段落"""
        # 1. 准备提示词
        prompt = self._prepare_alignment_prompt(script_seg, novel_data)
        
        # 2. 调用LLM
        result = self._call_llm(prompt)
        
        # 3. 解析结果
        alignment = self._parse_alignment_result(result)
        
        return alignment
    
    def _prepare_alignment_prompt(
        self,
        script_seg: Dict[str, Any],
        novel_data: str
    ) -> str:
        """准备对齐提示词"""
        user_prompt_template = self.prompt_config["script_alignment_analysis"]["user"]
        
        user_prompt = user_prompt_template.format(
            time_range=script_seg["time_range"],
            segment_type=script_seg["segment_type"],
            script_text=script_seg["text"],
            novel_analysis_json=novel_data
        )
        
        return user_prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM进行对齐分析"""
        system_prompt = self.prompt_config["script_alignment_analysis"]["system"]
        temperature = self.prompt_config["script_alignment_analysis"].get("temperature", 0.3)
        max_tokens = self.prompt_config["script_alignment_analysis"].get("max_tokens", 4000)
        
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
        
        # 移除markdown标记
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        
        return result.strip()
    
    def _parse_alignment_result(self, raw_result: str) -> ScriptToNovelAlignment:
        """解析对齐结果"""
        try:
            data = json.loads(raw_result)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise ValueError(f"Invalid JSON from LLM: {e}")
        
        # 解析ScriptSegmentInfo
        script_data = data.get("script_segment", {})
        script_segment = ScriptSegmentInfo(
            time_range=script_data.get("time_range", "unknown"),
            text=script_data.get("text", ""),
            segment_type=script_data.get("segment_type", "Body"),
            word_count=script_data.get("word_count", 0)
        )
        
        # 解析NovelSourceInfo
        source_data = data.get("novel_source", {})
        novel_source = NovelSourceInfo(
            segments=source_data.get("segments", []),
            condensation_ratio=source_data.get("condensation_ratio", 0.0),
            retained_tags=source_data.get("retained_tags", []),
            omitted_tags=source_data.get("omitted_tags", []),
            transformation=source_data.get("transformation", {})
        )
        
        # 解析AlignmentAnalysis
        analysis_data = data.get("analysis", {})
        analysis = AlignmentAnalysis(
            alignment_confidence=analysis_data.get("alignment_confidence", 1.0),
            key_info_preserved=analysis_data.get("key_info_preserved", []),
            key_info_omitted=analysis_data.get("key_info_omitted", []),
            quality_score=analysis_data.get("quality_score"),
            notes=analysis_data.get("notes")
        )
        
        return ScriptToNovelAlignment(
            script_segment=script_segment,
            novel_source=novel_source,
            analysis=analysis
        )
    
    def _create_fallback_alignment(self, script_seg: Dict[str, Any]) -> ScriptToNovelAlignment:
        """创建备用对齐结果（当LLM失败时）"""
        return ScriptToNovelAlignment(
            script_segment=ScriptSegmentInfo(
                time_range=script_seg["time_range"],
                text=script_seg["text"],
                segment_type=script_seg["segment_type"],
                word_count=script_seg["word_count"]
            ),
            novel_source=NovelSourceInfo(
                segments=[],
                condensation_ratio=0.0,
                retained_tags=[],
                omitted_tags=[],
                transformation={"method": "unknown", "techniques": []}
            ),
            analysis=AlignmentAnalysis(
                alignment_confidence=0.0,
                key_info_preserved=[],
                key_info_omitted=[],
                quality_score=0.0,
                notes="Alignment failed"
            )
        )
    
    def _calculate_overall_stats(
        self,
        alignments: List[ScriptToNovelAlignment],
        novel_analyses: List[ChapterAnalysis]
    ) -> AlignmentOverallStats:
        """计算整体统计"""
        total_script_segments = len(alignments)
        total_novel_segments = sum(len(ch.segments) for ch in novel_analyses)
        
        # 计算整体浓缩比例
        total_script_words = sum(a.script_segment.word_count for a in alignments)
        total_novel_words = sum(
            sum(seg.metadata.word_count for seg in ch.segments)
            for ch in novel_analyses
        )
        condensation_ratio = total_script_words / total_novel_words if total_novel_words > 0 else 0.0
        
        # 计算P0/P1/P2保留率
        def count_priority_segments(priority: str) -> int:
            return sum(
                1 for ch in novel_analyses
                for seg in ch.segments
                if seg.tags.priority == priority
            )
        
        def count_retained_priority(priority: str) -> int:
            count = 0
            for alignment in alignments:
                for tag in alignment.novel_source.retained_tags:
                    if tag == priority:
                        count += 1
            return count
        
        total_p0 = count_priority_segments("P0-骨架")
        total_p1 = count_priority_segments("P1-血肉")
        total_p2 = count_priority_segments("P2-皮肤")
        
        retained_p0 = count_retained_priority("P0-骨架")
        retained_p1 = count_retained_priority("P1-血肉")
        retained_p2 = count_retained_priority("P2-皮肤")
        
        p0_retention_rate = retained_p0 / total_p0 if total_p0 > 0 else 0.0
        p1_retention_rate = retained_p1 / total_p1 if total_p1 > 0 else 0.0
        p2_retention_rate = retained_p2 / total_p2 if total_p2 > 0 else 0.0
        
        # 计算平均对齐置信度
        avg_confidence = sum(a.analysis.alignment_confidence for a in alignments) / len(alignments)
        
        return AlignmentOverallStats(
            total_script_segments=total_script_segments,
            total_novel_segments=total_novel_segments,
            condensation_ratio=condensation_ratio,
            p0_retention_rate=p0_retention_rate,
            p1_retention_rate=p1_retention_rate,
            p2_retention_rate=p2_retention_rate,
            avg_alignment_confidence=avg_confidence
        )
    
    def validate_inputs(
        self,
        script_text: str,
        novel_analyses: List[ChapterAnalysis],
        episode_id: str,
        **kwargs
    ) -> bool:
        """验证输入参数"""
        if not script_text or not script_text.strip():
            logger.error("script_text is empty")
            return False
        
        if not novel_analyses:
            logger.error("novel_analyses is empty")
            return False
        
        if not episode_id or not episode_id.strip():
            logger.error("episode_id is empty")
            return False
        
        return True


# 导出
__all__ = ["ScriptSegmentAligner"]
