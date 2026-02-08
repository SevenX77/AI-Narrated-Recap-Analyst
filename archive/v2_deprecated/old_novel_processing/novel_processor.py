"""
Novel Processing Tools
处理小说文本的工具集：分段、格式化等
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from openai import OpenAI

from src.core.interfaces import BaseTool
from src.core.config import config
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


@dataclass
class SegmentationResult:
    """分段结果数据结构"""
    paragraphs: List[str]
    stats: Dict[str, Any]
    processing_log: List[Dict[str, Any]]


class NovelSegmentationTool(BaseTool):
    """
    小说自然段处理工具
    
    使用混合模式：规则引擎（80%）+ LLM 辅助（20%）
    将单句一行的文本处理成自然段落格式
    """
    
    name = "novel_segmentation"
    description = "Process novel text into natural paragraphs"
    
    # 关键词库
    TIME_KEYWORDS = [
        "夜幕降临", "清晨", "几天后", "一刻钟后", "此时", "现在", "当时",
        "第二天", "傍晚", "深夜", "黎明", "午后", "转眼间", "片刻后",
        "许久之后", "不久", "随后", "接着", "然后", "后来", "从前",
        "过了", "天后", "小时后", "分钟后", "之前", "之后"
    ]
    
    LOCATION_KEYWORDS = [
        "车队", "营地", "城市", "基地", "房间", "屋内", "屋外", "街道",
        "广场", "森林", "山上", "河边", "这里", "那里", "远处", "附近"
    ]
    
    SCENE_TRANSITION_MARKERS = [
        "……", "---", "***", "===", "———"
    ]
    
    def __init__(self, use_llm: bool = True, llm_threshold: float = 0.5):
        """
        Args:
            use_llm: 是否启用 LLM 辅助优化
            llm_threshold: 规则引擎置信度低于此值时调用 LLM
        """
        self.use_llm = use_llm
        self.llm_threshold = llm_threshold
        self.prompt_config = load_prompts("novel_segmentation")
        
        if self.use_llm:
            self.llm_client = OpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url
            )
    
    def execute(self, 
                text: str, 
                preserve_metadata: bool = True) -> SegmentationResult:
        """
        执行小说分段处理
        
        Args:
            text: 原始小说文本（逐行格式）
            preserve_metadata: 是否保留元数据（章节标题、作者信息等）
        
        Returns:
            SegmentationResult: 分段结果
        """
        logger.info(f"Starting novel segmentation, use_llm={self.use_llm}")
        
        # 1. 预处理
        lines = self._preprocess(text)
        logger.info(f"Preprocessed {len(lines)} lines")
        
        # 2. 分离元数据和正文
        if preserve_metadata:
            metadata_lines, content_lines = self._separate_metadata(lines)
        else:
            metadata_lines = []
            content_lines = lines
        
        # 3. 规则引擎分段
        segments = self._segment_by_rules(content_lines)
        logger.info(f"Rule-based segmentation: {len(segments)} segments")
        
        # 4. LLM 辅助优化（如果启用）
        processing_log = []
        if self.use_llm:
            segments, llm_log = self._refine_with_llm(segments, content_lines)
            processing_log.extend(llm_log)
            logger.info(f"LLM refined: {len(llm_log)} uncertain boundaries")
        
        # 5. 格式化段落
        paragraphs = self._format_paragraphs(segments)
        
        # 6. 添加元数据
        if metadata_lines:
            final_text = "\n".join(metadata_lines) + "\n\n" + "\n\n".join(paragraphs)
        else:
            final_text = "\n\n".join(paragraphs)
        
        # 7. 统计信息
        stats = self._calculate_stats(lines, segments, processing_log)
        
        return SegmentationResult(
            paragraphs=[final_text],
            stats=stats,
            processing_log=processing_log
        )
    
    def _preprocess(self, text: str) -> List[str]:
        """预处理：清理空行、规范化"""
        lines = text.split("\n")
        processed = []
        
        for line in lines:
            line = line.strip()
            if line:  # 保留非空行
                processed.append(line)
        
        return processed
    
    def _separate_metadata(self, lines: List[str]) -> Tuple[List[str], List[str]]:
        """分离元数据（封面、标题、作者、简介）和正文"""
        metadata = []
        content_start_idx = 0
        
        for i, line in enumerate(lines):
            # 元数据标记
            if any(marker in line for marker in ["[封面:", "Title:", "Author:", "简介:", "====="]):
                metadata.append(line)
            elif line.startswith("=== 第") and "章" in line:
                # 遇到第一章，元数据结束
                content_start_idx = i
                break
            elif i < 30:  # 前30行可能是元数据
                metadata.append(line)
            else:
                content_start_idx = i
                break
        
        return metadata, lines[content_start_idx:]
    
    def _segment_by_rules(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        规则引擎分段
        
        Returns:
            List of segments: [
                {
                    "start": 0,
                    "end": 10,
                    "lines": [...],
                    "confidence": 0.9,
                    "method": "rule",
                    "reason": "chapter_title"
                }
            ]
        """
        segments = []
        current_segment = {
            "start": 0,
            "lines": [],
            "confidence": 1.0,
            "method": "rule"
        }
        
        for i, line in enumerate(lines):
            # 规则 1: 章节标题强制分段
            if self._is_chapter_title(line):
                if current_segment["lines"]:
                    current_segment["end"] = i - 1
                    segments.append(current_segment)
                
                # 章节标题单独成段
                segments.append({
                    "start": i,
                    "end": i,
                    "lines": [line],
                    "confidence": 1.0,
                    "method": "rule",
                    "reason": "chapter_title"
                })
                
                current_segment = {
                    "start": i + 1,
                    "lines": [],
                    "confidence": 1.0,
                    "method": "rule"
                }
                continue
            
            # 添加当前行到段落
            current_segment["lines"].append(line)
            
            # 规则 2: 检测分段边界
            should_break, confidence, reason = self._detect_boundary(
                current_segment["lines"],
                line,
                lines[i+1] if i+1 < len(lines) else None
            )
            
            if should_break:
                current_segment["end"] = i
                current_segment["confidence"] = confidence
                current_segment["reason"] = reason
                segments.append(current_segment)
                
                current_segment = {
                    "start": i + 1,
                    "lines": [],
                    "confidence": 1.0,
                    "method": "rule"
                }
        
        # 添加最后一个段落
        if current_segment["lines"]:
            current_segment["end"] = len(lines) - 1
            segments.append(current_segment)
        
        return segments
    
    def _is_chapter_title(self, line: str) -> bool:
        """检测是否为章节标题"""
        patterns = [
            r"^===\s*第\s*\d+\s*章",  # === 第1章 ===
            r"^第\s*[零一二三四五六七八九十百千万\d]+\s*章",  # 第一章
        ]
        return any(re.match(p, line) for p in patterns)
    
    def _detect_boundary(self, 
                        current_lines: List[str],
                        current_line: str,
                        next_line: Optional[str]) -> Tuple[bool, float, str]:
        """
        检测段落边界
        
        Returns:
            (should_break, confidence, reason)
        """
        if not next_line:
            return False, 1.0, ""
        
        # 规则 1: 场景转换标记
        if any(marker in current_line for marker in self.SCENE_TRANSITION_MARKERS):
            return True, 1.0, "scene_transition_marker"
        
        # 规则 2: 时间变化
        time_in_current = any(kw in current_line for kw in self.TIME_KEYWORDS)
        time_in_next = any(kw in next_line for kw in self.TIME_KEYWORDS)
        if time_in_next and not time_in_current:
            return True, 0.85, "time_change"
        
        # 规则 3: 地点变化
        location_in_current = any(kw in current_line for kw in self.LOCATION_KEYWORDS)
        location_in_next = any(kw in next_line for kw in self.LOCATION_KEYWORDS)
        if location_in_next and not location_in_current:
            return True, 0.75, "location_change"
        
        # 规则 4: 对话与叙述模式切换
        is_current_dialogue = self._is_dialogue(current_line)
        is_next_dialogue = self._is_dialogue(next_line)
        
        if is_current_dialogue != is_next_dialogue:
            # 对话段连续性：连续对话不分段
            if is_current_dialogue and len(current_lines) > 1:
                # 检查当前段是否全是对话
                all_dialogue = all(self._is_dialogue(l) for l in current_lines[-3:])
                if all_dialogue:
                    return False, 0.5, "continuous_dialogue"
            return True, 0.70, "narrative_mode_change"
        
        # 规则 5: 段落长度控制
        para_length = len(current_lines)
        if para_length >= 15:
            return True, 0.60, "paragraph_too_long"
        
        if para_length < 3:
            return False, 0.50, "paragraph_too_short"
        
        # 规则 6: 主语/主题变化
        subject_current = self._extract_subject(current_line)
        subject_next = self._extract_subject(next_line)
        
        if subject_current and subject_next and subject_current != subject_next:
            if para_length >= 5:
                return True, 0.55, "subject_change"
        
        # 默认：不分段
        return False, 0.80, "continue"
    
    def _is_dialogue(self, line: str) -> bool:
        """检测是否为对话"""
        dialogue_markers = ['"', '"', '"', '\'', '\'']
        return any(marker in line for marker in dialogue_markers)
    
    def _extract_subject(self, line: str) -> Optional[str]:
        """提取主语（简单实现：检测人名）"""
        # 简单模式：检测常见人名模式
        # 中文姓名：2-4个字，出现在句首
        match = re.match(r'^([^，。！？"""\'\s]{2,4})', line)
        if match:
            return match.group(1)
        return None
    
    def _refine_with_llm(self, 
                         segments: List[Dict[str, Any]],
                         all_lines: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict]]:
        """
        LLM 辅助优化不确定的边界
        
        Args:
            segments: 规则引擎生成的段落
            all_lines: 全部文本行
        
        Returns:
            (refined_segments, processing_log)
        """
        refined_segments = []
        processing_log = []
        
        for i, seg in enumerate(segments):
            # 只处理置信度低的段落
            if seg.get("confidence", 1.0) < self.llm_threshold:
                # 获取上下文
                context_lines = self._get_context(seg, all_lines, context_size=10)
                
                # 调用 LLM
                try:
                    decision = self._query_llm_for_boundary(
                        context_lines,
                        seg["end"]
                    )
                    
                    # 更新段落信息
                    seg["llm_decision"] = decision
                    seg["confidence"] = decision.get("confidence", seg["confidence"])
                    seg["method"] = "llm_refined"
                    
                    processing_log.append({
                        "segment_index": i,
                        "line_number": seg["end"],
                        "rule_confidence": seg.get("confidence", 0.0),
                        "llm_decision": decision,
                        "action": "refined"
                    })
                    
                    logger.info(f"LLM refined segment {i}: {decision}")
                
                except Exception as e:
                    logger.warning(f"LLM refinement failed for segment {i}: {e}")
                    seg["method"] = "rule_fallback"
            
            refined_segments.append(seg)
        
        return refined_segments, processing_log
    
    def _get_context(self, 
                     segment: Dict[str, Any],
                     all_lines: List[str],
                     context_size: int = 10) -> str:
        """获取段落边界的上下文"""
        start = max(0, segment["start"] - context_size)
        end = min(len(all_lines), segment["end"] + context_size + 1)
        
        context = []
        for i in range(start, end):
            marker = ">>>" if i == segment["end"] else "   "
            context.append(f"{marker} Line {i+1}: {all_lines[i]}")
        
        return "\n".join(context)
    
    def _query_llm_for_boundary(self, context: str, line_number: int) -> Dict[str, Any]:
        """
        查询 LLM 判断边界
        
        Args:
            context: 上下文文本
            line_number: 待判断的行号
        
        Returns:
            {"should_break": bool, "reason": str, "confidence": float}
        """
        user_prompt = self.prompt_config["user_template"].format(
            context_lines=context,
            line_number=line_number
        )
        
        response = self.llm_client.chat.completions.create(
            model=self.prompt_config.get("settings", {}).get("model", "deepseek-chat"),
            messages=[
                {"role": "system", "content": self.prompt_config["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.prompt_config.get("settings", {}).get("temperature", 0.3),
            max_tokens=self.prompt_config.get("settings", {}).get("max_tokens", 200)
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 解析 JSON 响应
        try:
            # 尝试提取 JSON（可能包含额外文字）
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(result_text)
            
            return {
                "should_break": result.get("should_break", False),
                "reason": result.get("reason", ""),
                "confidence": float(result.get("confidence", 0.5))
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {result_text}, error: {e}")
            return {
                "should_break": False,
                "reason": "parse_error",
                "confidence": 0.3
            }
    
    def _format_paragraphs(self, segments: List[Dict[str, Any]]) -> List[str]:
        """
        格式化段落：段内连续，段间双空行
        
        Args:
            segments: 分段结果
        
        Returns:
            List of formatted paragraph strings
        """
        paragraphs = []
        
        for seg in segments:
            # 将段落中的所有句子合并成一个连续字符串
            paragraph_text = "".join(seg["lines"])
            paragraphs.append(paragraph_text)
        
        return paragraphs
    
    def _calculate_stats(self,
                        original_lines: List[str],
                        segments: List[Dict[str, Any]],
                        llm_log: List[Dict]) -> Dict[str, Any]:
        """计算统计信息"""
        rule_processed = sum(1 for s in segments if s.get("method") == "rule")
        llm_refined = sum(1 for s in segments if s.get("method") == "llm_refined")
        
        paragraph_lengths = [len(s["lines"]) for s in segments]
        avg_length = sum(paragraph_lengths) / len(paragraph_lengths) if paragraph_lengths else 0
        
        return {
            "original_lines": len(original_lines),
            "total_paragraphs": len(segments),
            "avg_paragraph_length": round(avg_length, 2),
            "min_paragraph_length": min(paragraph_lengths) if paragraph_lengths else 0,
            "max_paragraph_length": max(paragraph_lengths) if paragraph_lengths else 0,
            "rule_processed": rule_processed,
            "llm_refined": llm_refined,
            "llm_calls": len(llm_log)
        }
