"""
规则验证Agent

验证提取的规则能否准确预测Ground Truth项目的热度
"""

import json
from typing import Dict, Any, List
from datetime import datetime

from src.core.schemas_feedback import RuleBook, ValidationResult
from src.core.interfaces import BaseAgent
from src.utils.logger import logger
from src.utils.prompt_loader import load_prompts


class RuleValidatorAgent(BaseAgent):
    """
    规则验证Agent
    
    负责验证规则库的有效性：
    1. 用规则对GT项目评分
    2. 比较评分与实际热度的相关性
    3. 分析各维度的重要性
    4. 提出优化建议
    """
    
    def __init__(self, client: Any, model_name: str = "deepseek-chat"):
        """
        初始化规则验证Agent
        
        Args:
            client: LLM客户端
            model_name: 模型名称
        """
        super().__init__(context={})
        self.client = client
        self.model_name = model_name
        self.prompts = load_prompts("rule_validation")
    
    def validate_rulebook(
        self,
        rulebook: RuleBook,
        gt_projects_data: Dict[str, Dict[str, Any]],
        actual_heat_scores: Dict[str, float]
    ) -> ValidationResult:
        """
        验证规则库
        
        Args:
            rulebook: 待验证的规则库
            gt_projects_data: GT项目数据
            actual_heat_scores: 实际热度值
            
        Returns:
            ValidationResult: 验证结果
        """
        logger.info(f"🔍 开始验证规则库 {rulebook.version}...")
        
        # 准备数据
        rulebook_json = rulebook.model_dump_json(indent=2)
        projects_summary = self._prepare_projects_summary(gt_projects_data)
        heat_scores_json = json.dumps(actual_heat_scores, indent=2, ensure_ascii=False)
        
        system_prompt = self.prompts["validate_rules"]["system"]
        user_prompt = self.prompts["validate_rules"]["user"].format(
            rulebook=rulebook_json,
            gt_projects_data=projects_summary,
            actual_heat_scores=heat_scores_json
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
            
            # 构建ValidationResult
            validation_result = ValidationResult(
                rulebook_version=rulebook.version,
                validated_at=datetime.now().isoformat(),
                project_scores=data.get("project_scores", {}),
                correlation=data.get("correlation", 0.0),
                is_valid=data.get("is_valid", False),
                dimension_importance=data.get("dimension_importance", {}),
                optimization_suggestions=data.get("optimization_suggestions", []),
                details=data
            )
            
            logger.info(f"✅ 规则验证完成:")
            logger.info(f"   - 相关性: {validation_result.correlation:.2f}")
            logger.info(f"   - 是否有效: {validation_result.is_valid}")
            logger.info(f"   - 优化建议数: {len(validation_result.optimization_suggestions)}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ 规则验证失败: {e}")
            raise
    
    def score_content_by_rules(
        self,
        rulebook: RuleBook,
        content_data: Dict[str, Any],
        content_type: str
    ) -> Dict[str, Any]:
        """
        用规则对内容评分
        
        Args:
            rulebook: 规则库
            content_data: 内容数据
            content_type: 内容类型 (hook/ep01/ep02_plus)
            
        Returns:
            评分结果
        """
        logger.info(f"📊 使用规则对 {content_type} 内容评分...")
        
        rulebook_json = rulebook.model_dump_json(indent=2)
        content_json = json.dumps(content_data, indent=2, ensure_ascii=False)
        
        system_prompt = self.prompts["score_content_by_rules"]["system"]
        user_prompt = self.prompts["score_content_by_rules"]["user"].format(
            rulebook=rulebook_json,
            content_data=content_json,
            content_type=content_type
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
            
            logger.info(f"✅ 评分完成: {data.get('total_score')}/{data.get('max_score')}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ 评分失败: {e}")
            raise
    
    def _prepare_projects_summary(
        self,
        projects_data: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        准备项目数据摘要
        
        Args:
            projects_data: 项目数据
            
        Returns:
            格式化的摘要字符串
        """
        summary_parts = []
        
        for project_id, data in projects_data.items():
            summary = f"""
【{project_id}】
- SRT内容: {data.get('srt_content', '')[:300]}...
- 事件数: {len(data.get('events', []))}
- Hook信息: {json.dumps(data.get('hook_info', {}), ensure_ascii=False)}
"""
            summary_parts.append(summary)
        
        return "\n".join(summary_parts)
    
    async def process(self, **kwargs) -> Any:
        """
        BaseAgent接口实现
        
        Args:
            **kwargs: 可能包含 rulebook, gt_projects_data, actual_heat_scores
            
        Returns:
            ValidationResult或评分结果
        """
        rulebook = kwargs.get('rulebook')
        gt_projects_data = kwargs.get('gt_projects_data')
        actual_heat_scores = kwargs.get('actual_heat_scores')
        content_data = kwargs.get('content_data')
        content_type = kwargs.get('content_type')
        
        if rulebook and gt_projects_data and actual_heat_scores:
            return self.validate_rulebook(rulebook, gt_projects_data, actual_heat_scores)
        elif rulebook and content_data and content_type:
            return self.score_content_by_rules(rulebook, content_data, content_type)
        
        raise ValueError("参数不足，无法执行验证或评分")
