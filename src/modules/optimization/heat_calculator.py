"""
Heat分数计算器 (Heat Calculator)

计算标注问题的严重程度（Heat Score）：
- Heat越高 = 问题越严重
- 用于优先级排序和Prompt优化
"""

import logging
from typing import List
from src.core.schemas import AlignmentAnnotation

logger = logging.getLogger(__name__)


class HeatCalculator:
    """
    Heat分数计算器
    
    计算公式：
        Heat = 基础分 + 相似度差距分 + 错误类型分
        
        基础分：
            - 错误匹配: 50分
            - 正确匹配: 0分
        
        相似度差距分：
            - |人类评分 - 系统评分| * 50
        
        错误类型分：
            - missing (缺失关键信息): 40分
            - incomplete (提取不完整): 30分
            - wrong_match (错误匹配): 20分
            - similarity_wrong (相似度错误): 10分
    
    最终Heat: 0-100分
    """
    
    # 错误类型权重
    ERROR_TYPE_WEIGHTS = {
        "missing": 40,       # 最严重：缺失关键信息
        "incomplete": 30,    # 严重：提取不完整
        "wrong_match": 20,   # 中等：错误匹配
        "similarity_wrong": 10  # 轻微：相似度评分错误
    }
    
    def calculate_heat(self, annotation: AlignmentAnnotation) -> float:
        """
        计算单个标注的Heat分数
        
        Args:
            annotation: 标注数据
        
        Returns:
            Heat分数（0-100）
        """
        heat = 0.0
        
        # 1. 基础分：是否错误匹配
        if not annotation.is_correct_match:
            heat += 50
            logger.debug(f"   基础分: +50 (错误匹配)")
        
        # 2. 相似度差距分
        if annotation.human_similarity is not None:
            gap = abs(annotation.human_similarity - annotation.system_similarity)
            sim_score = gap * 50
            heat += sim_score
            logger.debug(f"   相似度差距分: +{sim_score:.1f} (gap={gap:.2f})")
        
        # 3. 错误类型分
        if annotation.error_type:
            error_score = self.ERROR_TYPE_WEIGHTS.get(annotation.error_type, 0)
            heat += error_score
            logger.debug(f"   错误类型分: +{error_score} ({annotation.error_type})")
        
        # 限制在0-100范围
        heat = min(heat, 100.0)
        
        logger.debug(f"   最终Heat: {heat:.1f}")
        
        return heat
    
    def calculate_batch_heat(
        self,
        annotations: List[AlignmentAnnotation]
    ) -> List[AlignmentAnnotation]:
        """
        批量计算Heat分数
        
        Args:
            annotations: 标注列表
        
        Returns:
            更新Heat分数后的标注列表
        """
        logger.info(f"🔥 计算Heat分数: {len(annotations)}条标注")
        
        for annotation in annotations:
            annotation.heat_score = self.calculate_heat(annotation)
        
        # 排序（Heat从高到低）
        annotations_sorted = sorted(
            annotations,
            key=lambda x: x.heat_score,
            reverse=True
        )
        
        # 统计
        total_heat = sum(a.heat_score for a in annotations)
        avg_heat = total_heat / len(annotations) if annotations else 0.0
        high_heat_count = sum(1 for a in annotations if a.heat_score > 60)
        
        logger.info(f"   总Heat: {total_heat:.1f}")
        logger.info(f"   平均Heat: {avg_heat:.1f}")
        logger.info(f"   高Heat问题(>60): {high_heat_count}个")
        
        return annotations_sorted
    
    def filter_high_heat(
        self,
        annotations: List[AlignmentAnnotation],
        threshold: float = 60.0
    ) -> List[AlignmentAnnotation]:
        """
        筛选高Heat问题
        
        Args:
            annotations: 标注列表
            threshold: Heat阈值
        
        Returns:
            高Heat标注列表
        """
        high_heat = [a for a in annotations if a.heat_score >= threshold]
        
        logger.info(f"🔥 筛选高Heat问题（>={threshold}）: {len(high_heat)}/{len(annotations)}")
        
        return high_heat
    
    def get_heat_summary(self, annotations: List[AlignmentAnnotation]) -> dict:
        """
        获取Heat统计摘要
        
        Returns:
            统计字典
        """
        if not annotations:
            return {
                "total_count": 0,
                "total_heat": 0.0,
                "avg_heat": 0.0,
                "high_heat_count": 0,
                "medium_heat_count": 0,
                "low_heat_count": 0
            }
        
        total_heat = sum(a.heat_score for a in annotations)
        avg_heat = total_heat / len(annotations)
        
        high_heat_count = sum(1 for a in annotations if a.heat_score >= 60)
        medium_heat_count = sum(1 for a in annotations if 30 <= a.heat_score < 60)
        low_heat_count = sum(1 for a in annotations if a.heat_score < 30)
        
        return {
            "total_count": len(annotations),
            "total_heat": round(total_heat, 2),
            "avg_heat": round(avg_heat, 2),
            "high_heat_count": high_heat_count,
            "medium_heat_count": medium_heat_count,
            "low_heat_count": low_heat_count,
            "error_type_breakdown": self._get_error_type_breakdown(annotations)
        }
    
    def _get_error_type_breakdown(self, annotations: List[AlignmentAnnotation]) -> dict:
        """统计错误类型分布"""
        breakdown = {}
        
        for annotation in annotations:
            if annotation.error_type:
                breakdown[annotation.error_type] = breakdown.get(annotation.error_type, 0) + 1
        
        return breakdown
