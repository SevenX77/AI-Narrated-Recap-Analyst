import json
from typing import List, Dict, Tuple
from src.core.schemas import AlignmentItem
from .alignment_engine import AlignmentEngine

class DeepSeekAlignmentEngine(AlignmentEngine):
    
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
        system_prompt = """
        你是一个专业的剧情结构分析师。
        任务：分析解说文案的结构，找出“钩子(Hook)”与“正文(Body)”的分界点。
        
        【判断依据】
        1. 钩子(Hook)：通常是倒叙（来自未来的高潮片段）、世界观概括、或者悬念前置。它与小说第一章的开头往往在时间线上不连续。
        2. 正文(Body)：开始按照小说第一章的顺序进行线性叙事。
        
        【输入】
        - 解说开头片段
        - 小说第一章片段
        
        【输出】
        JSON格式：
        {
            "has_hook": true/false,
            "body_start_time": "00:45", // 正文开始的时间点
            "hook_summary": "...", // 钩子内容的概括
            "reason": "..." // 判断理由
        }
        """
        
        user_prompt = f"""
        【小说第一章 (Novel Start)】
        {novel_start_context}
        
        【解说文案开头 (Script Start)】
        {script_context}
        """
        
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
            print(f"Error detecting hook: {e}")
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
        
        print(f"Hook Detection Result: {hook_info}")
        
        # 3. Phase 2: Alignment
        # 将 Hook 信息注入到 System Prompt 中，指导模型进行分段匹配
        
        system_prompt = f"""
        你是一个专业的剧情逻辑分析师。
        你的任务是对比“解说文案事件流”和“小说原文事件流”，找出解说文案对应的原小说章节。
        
        【结构提示】
        根据分析，该解说文案的结构如下：
        - 是否有钩子(Hook): {hook_info.get('has_hook')}
        - 正文开始时间: {hook_info.get('body_start_time', '00:00')}
        - 钩子内容概括: {hook_info.get('hook_summary', '无')}
        
        【匹配策略】
        1. 对于“钩子”部分（正文开始时间之前）：
           - 尝试匹配小说中的“高潮/倒叙”片段，或者标记为“设定/预告”。
           - 如果在第一章找不到对应，不要强行匹配，可以标记为 matched_novel_chapter="Hook/Flashback"。
           
        2. 对于“正文”部分（正文开始时间之后）：
           - 严格按照小说章节顺序进行线性匹配。
           - 利用新增的 [时间] [地点] [手段] 信息来区分相似事件。
           
        请直接返回 JSON 数组。
        """

        user_prompt = f"""
        【小说事件流 (Novel Events)】
        {novel_context}
        
        【解说事件流 (Script Events)】
        {script_context}
        
        【输出要求】
        请以 JSON 格式输出匹配结果列表。字段如下：
        - script_time: 解说时间点
        - script_event: 解说事件概括
        - matched_novel_chapter: 匹配的小说章节 (若无匹配填 "None", 若是钩子填 "Hook/Flashback")
        - matched_novel_event: 匹配的小说事件概括
        - match_reason: 匹配理由
        - confidence: 高/中/低
        """
        
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
            print(f"Error aligning events: {e}")
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
