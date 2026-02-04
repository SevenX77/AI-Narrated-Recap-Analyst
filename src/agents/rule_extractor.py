"""
规则提取Agent

从多个Ground Truth项目中提取爆款规则，基于真实热度数据驱动
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.schemas_feedback import (
    ContentRule, RuleBook, DurationPattern, SegmentPattern,
    RuleExtractionResult
)
from src.core.interfaces import BaseAgent
from src.utils.logger import logger
from src.utils.prompt_loader import load_prompts


class RuleExtractorAgent(BaseAgent):
    """
    规则提取Agent
    
    负责从Ground Truth项目中提取爆款规则，包括：
    1. 内容特征规则（Hook强度、信息密度、节奏等）
    2. 时长Pattern
    3. 段落Pattern
    """
    
    def __init__(self, client: Any, model_name: str = "deepseek-chat"):
        """
        初始化规则提取Agent
        
        Args:
            client: LLM客户端
            model_name: 模型名称
        """
        super().__init__(context={})
        self.client = client
        self.model_name = model_name
        self.prompts = load_prompts("rule_extraction")
        
    def extract_rules_from_projects(
        self,
        projects_data: Dict[str, Dict[str, Any]],
        heat_scores: Dict[str, float],
        explosive_flags: Optional[Dict[str, bool]] = None
    ) -> RuleBook:
        """
        从多个项目中提取规则
        
        Args:
            projects_data: 各项目的数据，格式：
                {
                    'PROJ_002': {
                        'srt_content': '...',
                        'events': [...],
                        'hook_info': {...}
                    }
                }
            heat_scores: 各项目的热度值，格式：{'PROJ_002': 9.5, 'PROJ_003': 6.0}
            explosive_flags: 爆款标记，格式：{'PROJ_002': True, 'PROJ_003': False}
            
        Returns:
            RuleBook: 提取的规则库
        """
        logger.info(f"🔍 开始从 {len(projects_data)} 个项目中提取规则...")
        
        if explosive_flags is None:
            explosive_flags = {}
        
        # 准备prompt数据
        projects_summary = self._prepare_projects_summary(projects_data, heat_scores, explosive_flags)
        
        # 准备热度和爆款信息
        heat_info = {}
        for project_id in heat_scores.keys():
            heat_info[project_id] = {
                "heat_score": heat_scores.get(project_id, 0.0),
                "is_explosive": explosive_flags.get(project_id, False),
                "confidence_level": "高可信度（爆款验证）" if explosive_flags.get(project_id, False) else "标准可信度"
            }
        heat_scores_str = json.dumps(heat_info, indent=2, ensure_ascii=False)
        
        system_prompt = self.prompts["extract_rules_from_multi_projects"]["system"]
        user_prompt = self.prompts["extract_rules_from_multi_projects"]["user"].format(
            projects_data=projects_summary,
            heat_scores=heat_scores_str
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result_json = response.choices[0].message.content
            data = json.loads(result_json)
            
            # 解析规则
            rules = [ContentRule(**rule_data) for rule_data in data.get("rules", [])]
            
            # 解析时长patterns
            duration_patterns = {}
            for key, pattern_data in data.get("duration_patterns", {}).items():
                duration_patterns[key] = DurationPattern(**pattern_data)
            
            # 解析段落patterns
            segment_patterns = [
                SegmentPattern(**sp_data) 
                for sp_data in data.get("segment_patterns", [])
            ]
            
            # 分类规则
            hook_rules = [r for r in rules if r.category == "hook"]
            ep01_rules = [r for r in rules if r.category == "ep01_body"]
            ep02_plus_rules = [r for r in rules if r.category == "ep02_plus"]
            
            # 构建RuleBook
            rulebook = RuleBook(
                version="v1.0",
                created_at=datetime.now().isoformat(),
                extracted_from_projects=list(projects_data.keys()),
                project_heat_scores=heat_scores,
                hook_rules=hook_rules,
                ep01_rules=ep01_rules,
                ep02_plus_rules=ep02_plus_rules,
                duration_patterns=duration_patterns,
                segment_patterns=segment_patterns,
                metadata={
                    "extraction_notes": data.get("extraction_notes", []),
                    "explosive_projects": [pid for pid, is_exp in explosive_flags.items() if is_exp],
                    "explosive_count": sum(1 for is_exp in explosive_flags.values() if is_exp),
                    "total_projects": len(projects_data)
                }
            )
            
            logger.info(f"✅ 规则提取完成:")
            logger.info(f"   - Hook规则: {len(hook_rules)}条")
            logger.info(f"   - Ep01规则: {len(ep01_rules)}条")
            logger.info(f"   - Ep02+规则: {len(ep02_plus_rules)}条")
            logger.info(f"   - 时长Patterns: {len(duration_patterns)}个")
            logger.info(f"   - 段落Patterns: {len(segment_patterns)}个")
            
            return rulebook
            
        except Exception as e:
            logger.error(f"❌ 规则提取失败: {e}")
            raise
    
    def extract_duration_patterns(
        self,
        srt_content: str,
        hook_detection_result: Optional[Dict] = None,
        events: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        从单个SRT文件中提取时长Pattern
        
        Args:
            srt_content: SRT字幕内容
            hook_detection_result: Hook检测结果
            events: 事件列表
            
        Returns:
            时长Pattern数据
        """
        logger.info("📏 提取时长Pattern...")
        
        system_prompt = self.prompts["extract_duration_patterns"]["system"]
        user_prompt = self.prompts["extract_duration_patterns"]["user"].format(
            srt_content=srt_content[:2000],  # 限制长度
            hook_detection_result=json.dumps(hook_detection_result or {}, ensure_ascii=False),
            events=json.dumps(events[:20] if events else [], ensure_ascii=False)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result_json = response.choices[0].message.content
            data = json.loads(result_json)
            
            logger.info(f"✅ 时长Pattern提取完成:")
            logger.info(f"   - 总时长: {data.get('total_duration')}秒")
            logger.info(f"   - Hook时长: {data.get('hook_duration')}秒")
            logger.info(f"   - 平均句长: {data.get('sentence_stats', {}).get('avg_length')}秒")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ 时长Pattern提取失败: {e}")
            return {}
    
    def _prepare_projects_summary(
        self,
        projects_data: Dict[str, Dict[str, Any]],
        heat_scores: Dict[str, float],
        explosive_flags: Optional[Dict[str, bool]] = None
    ) -> str:
        """
        准备项目数据摘要用于prompt
        
        Args:
            projects_data: 项目数据
            heat_scores: 热度值
            explosive_flags: 爆款标记
            
        Returns:
            格式化的项目摘要字符串
        """
        if explosive_flags is None:
            explosive_flags = {}
        
        summary_parts = []
        
        for project_id, data in projects_data.items():
            heat = heat_scores.get(project_id, 0.0)
            is_explosive = explosive_flags.get(project_id, False)
            
            # 提取关键统计信息
            srt_content = data.get('srt_content', '')
            events = data.get('events', [])
            hook_info = data.get('hook_info', {})
            
            # 简单统计（实际应该更精确）
            total_duration = self._estimate_duration(srt_content)
            hook_duration = hook_info.get('duration', 30)
            sentence_count = srt_content.count('\n\n') if srt_content else 0
            
            # 添加爆款标记说明
            explosive_tag = " 🔥 [已验证爆款]" if is_explosive else ""
            confidence_note = "\n- **可信度**: 高（在热度榜持续多天，已验证为爆款）" if is_explosive else "\n- **可信度**: 标准"
            
            summary = f"""
【{project_id}】热度值: {heat}{explosive_tag}{confidence_note}
- 总时长: 约{total_duration}秒
- Hook时长: 约{hook_duration}秒
- 句子数: 约{sentence_count}句
- 事件数: {len(events)}个
- SRT开头片段:
{srt_content[:500] if srt_content else '(无数据)'}
...
"""
            summary_parts.append(summary)
        
        return "\n".join(summary_parts)
    
    def _estimate_duration(self, srt_content: str) -> float:
        """
        从SRT内容估算总时长
        
        Args:
            srt_content: SRT内容
            
        Returns:
            估算的总时长（秒）
        """
        if not srt_content:
            return 0.0
        
        # 简单实现：查找最后一个时间戳
        lines = srt_content.strip().split('\n')
        for line in reversed(lines):
            if '-->' in line:
                # 格式: 00:00:59,600 --> 00:01:00,633
                try:
                    end_time = line.split('-->')[1].strip()
                    # 解析时间
                    time_parts = end_time.replace(',', ':').split(':')
                    if len(time_parts) == 4:
                        hours, minutes, seconds, milliseconds = map(int, time_parts)
                        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
                        return total_seconds
                except:
                    continue
        
        return 0.0
    
    async def process(self, **kwargs) -> Any:
        """
        BaseAgent接口实现
        
        Args:
            **kwargs: 可能包含 projects_data, heat_scores
            
        Returns:
            RuleBook或其他处理结果
        """
        projects_data = kwargs.get('projects_data')
        heat_scores = kwargs.get('heat_scores')
        
        if projects_data and heat_scores:
            return self.extract_rules_from_projects(projects_data, heat_scores)
        
        raise ValueError("需要提供 projects_data 和 heat_scores 参数")
