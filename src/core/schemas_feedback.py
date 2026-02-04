"""
热度驱动的反馈评估系统数据模型

这个模块定义了基于真实热度数据的规则学习和内容评估系统所需的所有数据结构。
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DurationPattern(BaseModel):
    """
    时长Pattern (从Ground Truth中提取)
    """
    min_duration: float = Field(..., description="最小时长（秒）")
    max_duration: float = Field(..., description="最大时长（秒）")
    optimal_duration: float = Field(..., description="最优时长（秒）")
    
    
class SegmentPattern(BaseModel):
    """
    段落Pattern（不同类型段落的时长特征）
    """
    segment_type: str = Field(..., description="段落类型：opening_impact, world_intro, conflict, transition, ending_hook")
    duration_pattern: DurationPattern = Field(..., description="该类型段落的时长Pattern")
    info_density: Optional[float] = Field(None, description="信息密度（个关键点/秒）")
    

class ContentRule(BaseModel):
    """
    单条爆款规则
    
    从Ground Truth项目中提取的具体规则，带有权重和证据支持
    """
    rule_id: str = Field(..., description="规则ID，如 'HOOK_001', 'EP01_002'")
    category: str = Field(..., description="规则类别：hook（前30秒）, ep01_body（第一集）, ep02_plus（第二集及以后）")
    dimension: str = Field(..., description="评分维度：hook_strength, information_density, pacing, duration, climax_frequency 等")
    rule_text: str = Field(..., description="规则描述，清晰说明评判标准")
    
    weight: float = Field(..., description="权重 (0-10)，表示该规则对热度的影响程度")
    threshold: Optional[Dict[str, Any]] = Field(None, description="阈值或判断标准，如 {'min': 1.0, 'optimal': 1.2}")
    
    evidence: Dict[str, Any] = Field(
        default_factory=dict, 
        description="证据：从不同热度项目中提取的数据，如 {'PROJ_002': {'value': 1.2, 'heat_score': 9.5}}"
    )
    
    confidence: float = Field(default=0.8, description="规则置信度 (0.0-1.0)")


class RuleBook(BaseModel):
    """
    爆款规则库
    
    包含从多个Ground Truth项目中提取和优化的所有规则
    """
    version: str = Field(..., description="规则库版本，如 'v1.0', 'v2.3'")
    created_at: str = Field(..., description="创建时间")
    
    extracted_from_projects: List[str] = Field(..., description="提取规则的源项目列表，如 ['PROJ_002', 'PROJ_003']")
    project_heat_scores: Dict[str, float] = Field(..., description="各项目的热度值，如 {'PROJ_002': 9.5}")
    
    # 分类别的规则集
    hook_rules: List[ContentRule] = Field(default_factory=list, description="Hook（前30秒）专用规则")
    ep01_rules: List[ContentRule] = Field(default_factory=list, description="第一集规则")
    ep02_plus_rules: List[ContentRule] = Field(default_factory=list, description="第二集及之后规则")
    
    # 时长Patterns
    duration_patterns: Dict[str, DurationPattern] = Field(
        default_factory=dict,
        description="时长模式，如 {'hook': {...}, 'ep01': {...}}"
    )
    segment_patterns: List[SegmentPattern] = Field(default_factory=list, description="段落时长模式")
    
    # 优化历史
    optimization_iterations: int = Field(default=0, description="优化迭代次数")
    heat_prediction_accuracy: float = Field(default=0.0, description="热度预测准确率 (0.0-1.0)")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="其他元数据")


class RuleViolation(BaseModel):
    """
    规则违反详情
    
    记录Generated内容违反某条规则的具体情况，并提供Ground Truth对比
    """
    rule_id: str = Field(..., description="违反的规则ID")
    rule_text: str = Field(..., description="规则描述")
    dimension: str = Field(..., description="所属维度")
    
    severity: str = Field(..., description="严重程度：critical（致命）, major（重要）, minor（轻微）")
    deduction: float = Field(..., description="扣分")
    
    comparison: Dict[str, Any] = Field(
        ...,
        description="""对比详情，包含：
        - ground_truth_example: GT中的优秀示例
        - generated_example: 生成内容的对应部分
        - issue: 具体问题描述
        - suggestion: 具体改进建议
        """
    )


class DimensionScore(BaseModel):
    """
    单维度评分
    
    某个评分维度的详细得分情况
    """
    dimension: str = Field(..., description="维度名称，如 'hook_strength', 'pacing', 'information_density'")
    score: float = Field(..., description="该维度得分")
    max_score: float = Field(..., description="该维度满分")
    weight: float = Field(..., description="该维度在总分中的权重")
    
    violations: List[RuleViolation] = Field(default_factory=list, description="违规项列表")
    highlights: List[str] = Field(default_factory=list, description="做得好的地方")
    
    gt_baseline: Optional[float] = Field(None, description="Ground Truth在该维度的基准分")


class SimilarityMetrics(BaseModel):
    """
    相似度指标
    
    Generated内容与Ground Truth的相似度对比
    """
    length_ratio: float = Field(..., description="长度比例（Generated/GT），1.0为完全一致")
    pacing_similarity: float = Field(..., description="节奏相似度 (0.0-1.0)")
    keyword_overlap: float = Field(..., description="关键词重叠度 (0.0-1.0)")
    info_density_ratio: float = Field(..., description="信息密度比例（Generated/GT）")
    
    details: Dict[str, Any] = Field(default_factory=dict, description="详细指标数据")


class ComparativeFeedback(BaseModel):
    """
    基于规则对比的Feedback报告
    
    对Generated内容的详细评估报告，包含与Ground Truth的对比
    """
    content_type: str = Field(..., description="内容类型：hook, ep01, ep02_plus")
    
    # 评分
    total_score: float = Field(..., description="总分")
    max_score: float = Field(default=100.0, description="满分")
    predicted_heat_score: float = Field(..., description="预测的热度值 (0-10)")
    
    # Ground Truth基准
    gt_project_id: Optional[str] = Field(None, description="参考的Ground Truth项目ID")
    gt_total_score: Optional[float] = Field(None, description="Ground Truth的总分（基准分）")
    gt_heat_score: Optional[float] = Field(None, description="Ground Truth的实际热度值")
    score_gap: Optional[float] = Field(None, description="与GT的分数差距")
    
    # 各维度评分
    dimension_scores: List[DimensionScore] = Field(default_factory=list, description="各维度详细评分")
    
    # 总体评价
    critical_issues: List[RuleViolation] = Field(default_factory=list, description="致命问题列表（扣分>5）")
    major_improvements: List[str] = Field(default_factory=list, description="主要改进建议")
    strengths: List[str] = Field(default_factory=list, description="亮点/优势")
    
    # 相似度分析
    similarity_metrics: Optional[SimilarityMetrics] = Field(None, description="与GT的相似度指标")
    
    # 决策建议
    pass_threshold: float = Field(default=80.0, description="通过阈值")
    is_passed: bool = Field(..., description="是否通过评估")
    recommendation: str = Field(..., description="总体建议：pass（通过）, improve（需改进）, rewrite（需重写）")
    
    # 元数据
    evaluated_at: str = Field(..., description="评估时间")
    rulebook_version: str = Field(..., description="使用的规则库版本")


class ValidationResult(BaseModel):
    """
    规则验证结果
    
    验证规则库能否准确预测Ground Truth项目的热度
    """
    rulebook_version: str = Field(..., description="被验证的规则库版本")
    validated_at: str = Field(..., description="验证时间")
    
    # 各项目的评分与实际热度
    project_scores: Dict[str, Dict[str, float]] = Field(
        ...,
        description="""各项目的评分与热度，格式：
        {
            'PROJ_002': {'predicted_score': 92, 'actual_heat': 9.5},
            'PROJ_003': {'predicted_score': 72, 'actual_heat': 6.0}
        }
        """
    )
    
    # 相关性分析
    correlation: float = Field(..., description="评分与热度的相关系数 (-1.0 到 1.0)")
    is_valid: bool = Field(..., description="是否通过验证（相关性>0.85）")
    
    # 各维度的重要性分析
    dimension_importance: Dict[str, float] = Field(
        default_factory=dict,
        description="各维度对热度的影响程度"
    )
    
    # 优化建议
    optimization_suggestions: List[str] = Field(
        default_factory=list,
        description="规则优化建议"
    )
    
    details: Dict[str, Any] = Field(default_factory=dict, description="详细验证数据")


class RuleExtractionResult(BaseModel):
    """
    规则提取结果
    
    从单个或多个Ground Truth项目中提取规则的结果
    """
    extracted_at: str = Field(..., description="提取时间")
    source_projects: List[str] = Field(..., description="源项目列表")
    
    extracted_rules: List[ContentRule] = Field(..., description="提取的规则列表")
    duration_patterns: Dict[str, DurationPattern] = Field(..., description="提取的时长模式")
    segment_patterns: List[SegmentPattern] = Field(..., description="提取的段落模式")
    
    extraction_method: str = Field(default="llm_analysis", description="提取方法")
    confidence: float = Field(default=0.8, description="提取结果的置信度")
    
    notes: List[str] = Field(default_factory=list, description="提取过程中的注意事项")
