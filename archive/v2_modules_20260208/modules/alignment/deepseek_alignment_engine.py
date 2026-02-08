import json
import re
from typing import List, Dict, Tuple, Optional
from src.core.schemas import AlignmentItem, AlignmentQualityReport, EpisodeCoverage
from src.utils.logger import logger
from src.utils.prompt_loader import load_prompts
from .alignment_engine import AlignmentEngine

class DeepSeekAlignmentEngine(AlignmentEngine):
    def __init__(self, client=None, model_name: str = "deepseek-chat"):
        super().__init__(client, model_name)
        self.prompts = load_prompts("alignment")
    
    def _format_events(self, events_data: List[Dict]) -> str:
        """Helper to format event lists into readable text"""
        context = ""
        for item in events_data:
            # 兼容小说章节ID 或 脚本时间戳
            header = item.get('id') or f"时间 {item.get('time')}"
            events_list = item.get('events', [])
            
            formatted_events = []
            if isinstance(events_list, list):
                for e in events_list:
                    if isinstance(e, dict):
                        # 使用新字段：Location, Method, Time
                        parts = [
                            f"[{e.get('time_context', '')}]" if e.get('time_context') else "",
                            f"在{e.get('location', '')}" if e.get('location') else "",
                            e.get('subject', ''),
                            f"[{e.get('method', '')}]" if e.get('method') else "",
                            e.get('action', ''),
                            e.get('outcome', '')
                        ]
                        # 过滤空字符串并拼接
                        line = " ".join([p for p in parts if p])
                        formatted_events.append(f"- {line}")
                    else:
                        # Pydantic object
                        parts = [
                            f"[{getattr(e, 'time_context', '')}]" if getattr(e, 'time_context', None) else "",
                            f"在{getattr(e, 'location', '')}" if getattr(e, 'location', None) else "",
                            e.subject,
                            f"[{getattr(e, 'method', '')}]" if getattr(e, 'method', None) else "",
                            e.action,
                            e.outcome
                        ]
                        line = " ".join([p for p in parts if p])
                        formatted_events.append(f"- {line}")
            else:
                formatted_events.append(str(events_list))
                
            context += f"【{header}】:\n" + "\n".join(formatted_events) + "\n\n"
        return context

    def _detect_hook_boundary(self, script_context: str, novel_start_context: str) -> Dict:
        """
        Phase 1: 分析解说结构，寻找钩子与正文的分界点
        核心逻辑：寻找解说中与小说第一章线性叙事接轨的时间点
        """
        system_prompt = self.prompts["detect_hook"]["system"]
        user_prompt = self.prompts["detect_hook"]["user"].format(
            novel_start_context=novel_start_context,
            script_context=script_context
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error detecting hook: {e}")
            return {"has_hook": False, "body_start_time": "00:00"}

    def align_script_with_novel(self, novel_events_data: List[Dict], script_events_data: List[Dict]) -> List[AlignmentItem]:
        """
        对齐解说文案和小说原文 (Two-Phase Approach)
        """
        # 1. Format Contexts
        novel_context = self._format_events(novel_events_data)
        script_context = self._format_events(script_events_data)
        
        # 2. Phase 1: Hook Detection
        # 取前3个小说章节作为参照
        novel_start_preview = self._format_events(novel_events_data[:3])
        # 取前10个解说事件作为参照
        script_start_preview = self._format_events(script_events_data[:10])
        
        hook_info = self._detect_hook_boundary(script_start_preview, novel_start_preview)
        
        logger.info(f"Hook Detection Result: {hook_info}")
        
        # 3. Phase 2: Alignment
        # 将 Hook 信息注入到 System Prompt 中，指导模型进行分段匹配
        
        system_prompt = self.prompts["align_events"]["system"].format(
            has_hook=hook_info.get('has_hook'),
            body_start_time=hook_info.get('body_start_time', '00:00'),
            hook_summary=hook_info.get('hook_summary', '无')
        )

        user_prompt = self.prompts["align_events"]["user"].format(
            novel_context=novel_context,
            script_context=script_context
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            items_list = []
            if isinstance(data, list):
                items_list = data
            elif isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list):
                        items_list = val
                        break
                        
            return [AlignmentItem(**item) for item in items_list]

        except Exception as e:
            logger.error(f"Error aligning events: {e}")
            return []

    def aggregate_context(self, alignment_results: List[AlignmentItem], novel_chapters: Dict[str, str]) -> Dict[str, str]:
        """
        根据对齐结果，聚合每一段解说对应的完整小说章节文本。
        
        Args:
            alignment_results: align_script_with_novel 的输出
            novel_chapters: 字典，Key为章节名(如"第1章")，Value为章节全文
            
        Returns:
            字典，Key为解说时间点(script_time)，Value为该时间点对应的聚合小说文本
        """
        context_map = {}
        
        # Group by script time
        time_to_chapters = {}
        for item in alignment_results:
            if item.matched_novel_chapter and item.matched_novel_chapter not in ["None", "Hook/Flashback"]:
                if item.script_time not in time_to_chapters:
                    time_to_chapters[item.script_time] = set()
                time_to_chapters[item.script_time].add(item.matched_novel_chapter)
        
        # Build context
        for time_point, chapters in time_to_chapters.items():
            # Sort chapters to maintain narrative order
            # This assumes chapter names are comparable or we accept lexicographical order
            sorted_chapters = sorted(list(chapters))
            
            full_text = []
            for chap in sorted_chapters:
                if chap in novel_chapters:
                    full_text.append(f"【{chap}】\n{novel_chapters[chap]}")
            
            if full_text:
                context_map[time_point] = "\n\n".join(full_text)
            
        return context_map
    
    def evaluate_alignment_quality(
        self, 
        alignment_results: List[AlignmentItem],
        quality_threshold: float = 70.0
    ) -> AlignmentQualityReport:
        """
        评估对齐结果的质量
        
        Args:
            alignment_results: 对齐结果列表
            quality_threshold: 合格阈值 (默认 70.0)
            
        Returns:
            AlignmentQualityReport: 质量评估报告
        """
        if not alignment_results:
            return AlignmentQualityReport(
                overall_score=0.0,
                avg_confidence=0.0,
                coverage_ratio=0.0,
                continuity_score=0.0,
                episode_coverage=[],
                is_qualified=False,
                needs_more_chapters=True,
                details={}
            )
        
        # 1. 按集数分组
        episodes_data = {}
        for item in alignment_results:
            # 从 script_time 提取 episode（假设格式：ep01/00:00:12）
            episode_match = re.search(r'(ep\d+)', item.script_time)
            if episode_match:
                episode_name = episode_match.group(1)
            else:
                episode_name = "unknown"
            
            if episode_name not in episodes_data:
                episodes_data[episode_name] = []
            episodes_data[episode_name].append(item)
        
        # 2. 计算各集的覆盖情况
        episode_coverages = []
        total_confidence_sum = 0
        total_matched = 0
        total_events = 0
        
        confidence_map = {"高": 1.0, "中": 0.6, "低": 0.3}
        
        for episode_name, items in episodes_data.items():
            matched_items = [
                item for item in items 
                if item.matched_novel_chapter not in ["None", "Hook/Flashback"]
            ]
            
            matched_count = len(matched_items)
            total_count = len(items)
            coverage_ratio = matched_count / total_count if total_count > 0 else 0.0
            
            # 提取最小和最大章节
            chapter_numbers = []
            for item in matched_items:
                chapter_match = re.search(r'第(\d+)章', item.matched_novel_chapter)
                if chapter_match:
                    chapter_numbers.append(int(chapter_match.group(1)))
            
            min_chapter = f"第{min(chapter_numbers)}章" if chapter_numbers else None
            max_chapter = f"第{max(chapter_numbers)}章" if chapter_numbers else None
            
            episode_coverages.append(EpisodeCoverage(
                episode_name=episode_name,
                total_events=total_count,
                matched_events=matched_count,
                coverage_ratio=coverage_ratio,
                min_matched_chapter=min_chapter,
                max_matched_chapter=max_chapter
            ))
            
            # 累计统计
            total_events += total_count
            total_matched += matched_count
            total_confidence_sum += sum(
                confidence_map.get(item.confidence, 0.3) for item in items
            )
        
        # 3. 计算平均置信度
        avg_confidence = total_confidence_sum / len(alignment_results) if alignment_results else 0.0
        
        # 4. 计算整体覆盖率
        overall_coverage = total_matched / total_events if total_events > 0 else 0.0
        
        # 5. 计算章节连续性得分
        continuity_score = self._calculate_continuity(alignment_results)
        
        # 6. 计算综合得分
        overall_score = (
            avg_confidence * 0.4 +
            overall_coverage * 0.4 +
            continuity_score * 0.2
        ) * 100
        
        # 7. 判断是否合格和是否需要更多章节
        is_qualified = overall_score >= quality_threshold
        
        # 需要更多章节的条件：
        # - 整体覆盖率低于 80%
        # - 或有任何一集的覆盖率低于 60%
        needs_more_chapters = (
            overall_coverage < 0.8 or
            any(ep.coverage_ratio < 0.6 for ep in episode_coverages)
        )
        
        return AlignmentQualityReport(
            overall_score=overall_score,
            avg_confidence=avg_confidence,
            coverage_ratio=overall_coverage,
            continuity_score=continuity_score,
            episode_coverage=episode_coverages,
            is_qualified=is_qualified,
            needs_more_chapters=needs_more_chapters,
            details={
                "total_events": total_events,
                "total_matched": total_matched,
                "episode_count": len(episodes_data),
                "quality_threshold": quality_threshold
            }
        )
    
    def _calculate_continuity(self, alignment_results: List[AlignmentItem]) -> float:
        """
        计算章节连续性得分
        
        连续性越好，得分越高。主要检测章节跳跃程度。
        
        Args:
            alignment_results: 对齐结果列表
            
        Returns:
            float: 连续性得分 (0.0-1.0)
        """
        # 提取所有有效匹配的章节编号
        chapter_numbers = []
        for item in alignment_results:
            if item.matched_novel_chapter not in ["None", "Hook/Flashback"]:
                match = re.search(r'第(\d+)章', item.matched_novel_chapter)
                if match:
                    chapter_numbers.append(int(match.group(1)))
        
        if len(chapter_numbers) < 2:
            return 1.0  # 样本太少，默认连续
        
        # 计算章节跳跃
        chapter_numbers_sorted = sorted(set(chapter_numbers))
        jumps = []
        for i in range(1, len(chapter_numbers_sorted)):
            jump = chapter_numbers_sorted[i] - chapter_numbers_sorted[i-1]
            if jump > 1:  # 跳过了章节
                jumps.append(jump - 1)
        
        # 计算跳跃惩罚
        if not jumps:
            return 1.0  # 完全连续
        
        avg_jump = sum(jumps) / len(jumps)
        
        # 跳跃越大，得分越低
        # avg_jump=1 -> 0.9, avg_jump=2 -> 0.8, avg_jump=5 -> 0.5
        continuity_score = max(0.0, 1.0 - (avg_jump * 0.1))
        
        return continuity_score