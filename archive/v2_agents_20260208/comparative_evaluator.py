"""
对比评估Agent

将Generated内容与Ground Truth对比，给出详细的差距分析和改进建议
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.schemas_feedback import (
    RuleBook, ComparativeFeedback, DimensionScore,
    RuleViolation, SimilarityMetrics
)
from src.core.interfaces import BaseAgent
from src.utils.logger import logger
from src.utils.prompt_loader import load_prompts


class ComparativeEvaluatorAgent(BaseAgent):
    """
    对比评估Agent
    
    负责：
    1. 将Generated内容与GT对比
    2. 找出具体差距并举例
    3. 计算相似度指标
    4. 给出详细改进建议
    """
    
    def __init__(self, client: Any, model_name: str = "deepseek-chat"):
        """
        初始化对比评估Agent
        
        Args:
            client: LLM客户端
            model_name: 模型名称
        """
        super().__init__(context={})
        self.client = client
        self.model_name = model_name
        self.prompts = load_prompts("comparative_evaluation")
    
    def compare_with_ground_truth(
        self,
        generated_content: Dict[str, Any],
        ground_truth_content: Dict[str, Any],
        gt_heat_score: float,
        rulebook: RuleBook,
        gt_project_id: str
    ) -> ComparativeFeedback:
        """
        将Generated内容与Ground Truth对比评估
        
        Args:
            generated_content: 生成的内容数据
            ground_truth_content: Ground Truth内容数据
            gt_heat_score: GT的实际热度值
            rulebook: 规则库
            gt_project_id: GT项目ID
            
        Returns:
            ComparativeFeedback: 详细的对比评估报告
        """
        logger.info(f"🔍 开始对比评估（参考GT: {gt_project_id}, 热度: {gt_heat_score}）...")
        
        # 准备数据
        gt_json = json.dumps(ground_truth_content, indent=2, ensure_ascii=False)
        generated_json = json.dumps(generated_content, indent=2, ensure_ascii=False)
        rulebook_json = rulebook.model_dump_json(indent=2)
        
        system_prompt = self.prompts["compare_with_ground_truth"]["system"]
        user_prompt = self.prompts["compare_with_ground_truth"]["user"].format(
            ground_truth_content=gt_json,
            gt_heat_score=gt_heat_score,
            generated_content=generated_json,
            rulebook=rulebook_json
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
            
            # 解析dimension_scores
            dimension_scores = []
            for dim_data in data.get("dimension_comparisons", []):
                violations = [
                    RuleViolation(**v) 
                    for comp in dim_data.get("detailed_comparison", [])
                    if comp.get("importance") in ["critical", "major"]
                    for v in [self._convert_comparison_to_violation(comp)]
                ]
                
                dimension_scores.append(DimensionScore(
                    dimension=dim_data.get("dimension"),
                    score=dim_data.get("generated_score", 0),
                    max_score=dim_data.get("gt_score", 100),
                    weight=1.0,  # 可以从rulebook中获取
                    violations=violations,
                    highlights=[],
                    gt_baseline=dim_data.get("gt_score")
                ))
            
            # 解析similarity_metrics
            similarity_data = data.get("similarity_metrics", {})
            similarity_metrics = SimilarityMetrics(
                length_ratio=similarity_data.get("length_ratio", 1.0),
                pacing_similarity=similarity_data.get("pacing_similarity", 0.0),
                keyword_overlap=similarity_data.get("keyword_overlap", 0.0),
                info_density_ratio=similarity_data.get("info_density_ratio", 1.0),
                details=similarity_data
            )
            
            # 构建ComparativeFeedback
            total_score = data.get("generated_total_score", 0)
            gt_total_score = data.get("gt_total_score", 100)
            predicted_heat = self._predict_heat_from_score(total_score)
            
            feedback = ComparativeFeedback(
                content_type=generated_content.get("type", "unknown"),
                total_score=total_score,
                max_score=100.0,
                predicted_heat_score=predicted_heat,
                gt_project_id=gt_project_id,
                gt_total_score=gt_total_score,
                gt_heat_score=gt_heat_score,
                score_gap=data.get("score_gap", 0),
                dimension_scores=dimension_scores,
                critical_issues=data.get("critical_issues", []),
                major_improvements=data.get("major_improvements", []),
                strengths=data.get("strengths", []),
                similarity_metrics=similarity_metrics,
                is_passed=total_score >= 80.0,
                recommendation=data.get("recommendation", "improve"),
                evaluated_at=datetime.now().isoformat(),
                rulebook_version=rulebook.version
            )
            
            logger.info(f"✅ 对比评估完成:")
            logger.info(f"   - Generated得分: {total_score}/{gt_total_score}")
            logger.info(f"   - 分数差距: {feedback.score_gap}")
            logger.info(f"   - 预测热度: {predicted_heat:.1f}")
            logger.info(f"   - 建议: {feedback.recommendation}")
            
            return feedback
            
        except Exception as e:
            logger.error(f"❌ 对比评估失败: {e}")
            raise
    
    def calculate_similarity(
        self,
        generated_content: Dict[str, Any],
        ground_truth_content: Dict[str, Any]
    ) -> SimilarityMetrics:
        """
        计算Generated与GT的相似度指标
        
        Args:
            generated_content: 生成的内容
            ground_truth_content: Ground Truth内容
            
        Returns:
            SimilarityMetrics: 相似度指标
        """
        logger.info("📊 计算相似度指标...")
        
        gt_json = json.dumps(ground_truth_content, indent=2, ensure_ascii=False)
        generated_json = json.dumps(generated_content, indent=2, ensure_ascii=False)
        
        system_prompt = self.prompts["calculate_similarity"]["system"]
        user_prompt = self.prompts["calculate_similarity"]["user"].format(
            ground_truth=gt_json,
            generated=generated_json
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
            
            similarity_metrics = SimilarityMetrics(
                length_ratio=data.get("length_ratio", 1.0),
                pacing_similarity=data.get("pacing_similarity", 0.0),
                keyword_overlap=data.get("keyword_overlap", 0.0),
                info_density_ratio=data.get("info_density_ratio", 1.0),
                details=data.get("details", {})
            )
            
            logger.info(f"✅ 相似度计算完成:")
            logger.info(f"   - 长度比例: {similarity_metrics.length_ratio:.2f}")
            logger.info(f"   - 节奏相似度: {similarity_metrics.pacing_similarity:.2f}")
            logger.info(f"   - 关键词重叠: {similarity_metrics.keyword_overlap:.2f}")
            
            return similarity_metrics
            
        except Exception as e:
            logger.error(f"❌ 相似度计算失败: {e}")
            raise
    
    def _convert_comparison_to_violation(self, comparison: Dict) -> RuleViolation:
        """
        将对比详情转换为RuleViolation对象
        
        Args:
            comparison: 对比详情
            
        Returns:
            RuleViolation
        """
        severity_map = {
            "critical": "critical",
            "major": "major",
            "minor": "minor"
        }
        
        return RuleViolation(
            rule_id=f"COMP_{comparison.get('aspect', 'unknown').upper()}",
            rule_text=comparison.get('aspect', ''),
            dimension="comparison",
            severity=severity_map.get(comparison.get('importance', 'minor'), 'minor'),
            deduction=8 if comparison.get('importance') == 'critical' else 5,
            comparison={
                "ground_truth_example": comparison.get('gt_example', ''),
                "generated_example": comparison.get('generated_example', ''),
                "issue": comparison.get('issue', ''),
                "suggestion": comparison.get('suggestion', '')
            }
        )
    
    def _predict_heat_from_score(self, score: float) -> float:
        """
        根据评分预测热度值
        
        Args:
            score: 评分 (0-100)
            
        Returns:
            预测的热度值 (0-10)
        """
        if score >= 90:
            return 9.0 + (score - 90) / 10
        elif score >= 75:
            return 7.0 + (score - 75) / 7.5
        elif score >= 60:
            return 5.0 + (score - 60) / 7.5
        elif score >= 45:
            return 3.0 + (score - 45) / 7.5
        else:
            return score / 22.5
    
    async def process(self, **kwargs) -> Any:
        """
        BaseAgent接口实现
        
        Args:
            **kwargs: 包含 generated_content, ground_truth_content, gt_heat_score, rulebook, gt_project_id
            
        Returns:
            ComparativeFeedback或SimilarityMetrics
        """
        generated_content = kwargs.get('generated_content')
        ground_truth_content = kwargs.get('ground_truth_content')
        gt_heat_score = kwargs.get('gt_heat_score')
        rulebook = kwargs.get('rulebook')
        gt_project_id = kwargs.get('gt_project_id')
        
        if all([generated_content, ground_truth_content, gt_heat_score, rulebook, gt_project_id]):
            return self.compare_with_ground_truth(
                generated_content,
                ground_truth_content,
                gt_heat_score,
                rulebook,
                gt_project_id
            )
        elif generated_content and ground_truth_content:
            return self.calculate_similarity(generated_content, ground_truth_content)
        
        raise ValueError("参数不足，无法执行对比评估")
