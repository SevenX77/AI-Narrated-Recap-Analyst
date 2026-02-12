"""
HookDetector - Hook边界检测工具

检测视频解说第一集中Hook（开场钩子）的结束位置。
"""

import logging
import json
import time
from typing import List, Optional
from pathlib import Path

from src.core.interfaces import BaseTool
from src.core.schemas_script import ScriptSegment, ScriptSegmentationResult, HookDetectionResult
from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class HookDetector(BaseTool):
    """
    Hook边界检测工具
    
    职责 (Responsibility):
        基于5个特征识别Hook与Body的边界：
        1. 独立语义的段落
        2. 非具象的当下描述（更像总结/预告）
        3. Hook后的文字连贯性更强（进入线性叙事）
        4. Hook后的文字能在小说开头匹配到
        5. Hook可能与小说序言/简介匹配度高
    
    接口 (Interface):
        输入:
            - script_segmentation: ScriptSegmentationResult (Script分段结果)
            - novel_intro: str (Novel简介)
            - novel_chapter1_preview: str (Novel第一章预览)
            - check_count: int (检查前N段，默认10)
        
        输出:
            - HookDetectionResult: Hook检测结果
    
    依赖 (Dependencies):
        - Schema: HookDetectionResult (schemas_script.py)
        - Tool: ScriptSegmenter (前置工具)
        - Prompt: hook_detection.yaml
        - LLM: DeepSeek v3.2 或 Claude
    """
    
    name = "hook_detector"
    description = "检测Hook边界"
    
    def __init__(self, provider: str = "deepseek"):
        """
        初始化Hook检测器
        
        Args:
            provider: LLM Provider（"deepseek" 或 "claude"）
        """
        super().__init__()
        self.provider = provider
        self.llm_client = get_llm_client(provider)
        self.model_name = get_model_name(provider)
        self.prompts = load_prompts("hook_detection")
    
    def execute(
        self,
        script_segmentation: ScriptSegmentationResult,
        novel_intro: str,
        novel_chapter1_preview: str,
        check_count: int = 10,
        **kwargs
    ) -> HookDetectionResult:
        """
        检测Hook的边界
        
        Args:
            script_segmentation: Script分段结果
            novel_intro: Novel简介文本
            novel_chapter1_preview: Novel第一章预览（前800字）
            check_count: 检查前N段（默认10）
        
        Returns:
            HookDetectionResult: Hook检测结果
        """
        logger.info(f"🔍 开始Hook边界检测...")
        start_time = time.time()
        
        # 提取前N段Script
        script_segments = script_segmentation.segments[:check_count]
        
        # 格式化Script段落
        script_text = self._format_script_segments(script_segments)
        
        # 构造Prompt
        system_prompt = self.prompts.get("system", "")
        user_prompt = self.prompts.get("user_template", "").format(
            script_segment_count=len(script_segments),
            script_segments=script_text,
            novel_intro=novel_intro,
            novel_preview_length=len(novel_chapter1_preview),
            novel_chapter1_preview=novel_chapter1_preview
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(f"   → 调用LLM进行Hook检测 (检查前{len(script_segments)}段)...")
        
        # 调用LLM
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # 解析结果
            has_hook = result_json.get("has_hook", False)
            hook_end_index = result_json.get("hook_end_index", -1)
            body_start_index = result_json.get("body_start_index", 0)
            confidence = result_json.get("confidence", 0.0)
            reasoning = result_json.get("reasoning", "")
            
            # 提取时间戳
            hook_end_time = None
            body_start_time = "00:00:00,000"
            hook_segment_indices = []
            body_segment_indices = []
            
            if has_hook and hook_end_index >= 0:
                hook_end_time = script_segments[hook_end_index].end_time
                hook_segment_indices = list(range(0, hook_end_index + 1))
            
            if body_start_index < len(script_segments):
                body_start_time = script_segments[body_start_index].start_time
                body_segment_indices = list(range(body_start_index, len(script_segmentation.segments)))
            
            processing_time = time.time() - start_time
            
            result = HookDetectionResult(
                has_hook=has_hook,
                hook_end_time=hook_end_time,
                body_start_time=body_start_time,
                confidence=confidence,
                reasoning=reasoning,
                hook_segment_indices=hook_segment_indices,
                body_segment_indices=body_segment_indices,
                metadata={
                    "hook_duration": self._parse_duration(hook_end_time) if hook_end_time else 0.0,
                    "processing_time": round(processing_time, 2),
                    "model_used": self.model_name,
                    "provider": self.provider
                }
            )
            
            logger.info(f"✅ Hook检测完成: has_hook={has_hook}")
            if has_hook:
                logger.info(f"   Hook时长: {result.metadata['hook_duration']:.1f}秒")
                logger.info(f"   Body起点: {body_start_time}")
            logger.info(f"   推理: {reasoning}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Hook检测失败: {e}")
            # 返回默认结果（假设没有Hook）
            return HookDetectionResult(
                has_hook=False,
                hook_end_time=None,
                body_start_time="00:00:00,000",
                confidence=0.0,
                reasoning=f"检测失败: {str(e)}",
                hook_segment_indices=[],
                body_segment_indices=list(range(len(script_segmentation.segments))),
                metadata={"error": str(e)}
            )
    
    def _format_script_segments(self, segments: List[ScriptSegment]) -> str:
        """格式化Script段落为可读文本"""
        lines = []
        for seg in segments:
            lines.append(f"【段落{seg.index}】({seg.start_time} - {seg.end_time})")
            lines.append(f"{seg.content}")
            lines.append("")
        return "\n".join(lines)
    
    def _parse_duration(self, time_str: str) -> float:
        """解析时间戳为秒数"""
        if not time_str:
            return 0.0
        
        # 格式: HH:MM:SS,mmm
        try:
            parts = time_str.replace(',', ':').split(':')
            hours, minutes, seconds, milliseconds = map(int, parts)
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            return total_seconds
        except Exception as e:
            logger.warning(f"解析时间失败: {time_str}, {e}")
            return 0.0
