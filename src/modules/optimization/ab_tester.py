"""
A/B测试框架 (A/B Tester)

用于对比新旧Prompt的性能：
1. 使用旧Prompt运行对齐 → 结果A
2. 使用新Prompt运行对齐 → 结果B
3. 对比结果A和结果B
4. 决策是否采用新Prompt
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from src.core.schemas import PromptVersion, OptimizationRound, AlignmentAnnotation
from src.modules.optimization.heat_calculator import HeatCalculator

logger = logging.getLogger(__name__)


@dataclass
class ABTestResult:
    """A/B测试结果"""
    old_version: str
    new_version: str
    
    # 对齐结果路径
    old_alignment_path: str
    new_alignment_path: str
    
    # 性能指标
    old_overall_score: float
    new_overall_score: float
    old_layer_scores: Dict[str, float]
    new_layer_scores: Dict[str, float]
    
    # 标注数据（如果有）
    old_annotations: Optional[List[AlignmentAnnotation]] = None
    new_annotations: Optional[List[AlignmentAnnotation]] = None
    old_total_heat: Optional[float] = None
    new_total_heat: Optional[float] = None
    
    # 决策
    is_better: bool = False
    improvement_percentage: float = 0.0
    adoption_reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "old_alignment_path": self.old_alignment_path,
            "new_alignment_path": self.new_alignment_path,
            "performance": {
                "old": {
                    "overall_score": self.old_overall_score,
                    "layer_scores": self.old_layer_scores,
                    "total_heat": self.old_total_heat
                },
                "new": {
                    "overall_score": self.new_overall_score,
                    "layer_scores": self.new_layer_scores,
                    "total_heat": self.new_total_heat
                }
            },
            "decision": {
                "is_better": self.is_better,
                "improvement_percentage": self.improvement_percentage,
                "adoption_reason": self.adoption_reason
            }
        }


class ABTester:
    """
    A/B测试框架
    
    工作流程：
        1. 加载旧Prompt和新Prompt
        2. 分别运行对齐
        3. 对比性能指标
        4. 决策是否采用新Prompt
    """
    
    def __init__(
        self,
        layered_aligner,
        heat_calculator: Optional[HeatCalculator] = None,
        output_dir: str = "data/alignment_optimization/ab_tests"
    ):
        """
        初始化A/B测试器
        
        Args:
            layered_aligner: LayeredAlignmentEngine实例
            heat_calculator: HeatCalculator实例（可选）
            output_dir: A/B测试结果输出目录
        """
        self.layered_aligner = layered_aligner
        self.heat_calculator = heat_calculator or HeatCalculator()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ ABTester 初始化完成")
    
    async def run_ab_test(
        self,
        project_id: str,
        episode: str,
        script_text: str,
        novel_text: str,
        script_time_range: str,
        old_prompt_version: str,
        new_prompt_version: str,
        layer: str
    ) -> ABTestResult:
        """
        运行A/B测试
        
        Args:
            project_id: 项目ID
            episode: 集数
            script_text: Script文本
            novel_text: Novel文本
            script_time_range: Script时间范围
            old_prompt_version: 旧Prompt版本
            new_prompt_version: 新Prompt版本
            layer: 测试的层级
        
        Returns:
            ABTestResult
        """
        logger.info(f"🧪 开始A/B测试: {project_id}/{episode} - {layer}")
        logger.info(f"   旧版本: {old_prompt_version}")
        logger.info(f"   新版本: {new_prompt_version}")
        
        # Step 1: 使用旧Prompt运行对齐
        logger.info("   → 使用旧Prompt运行对齐...")
        self._load_prompt_version(layer, old_prompt_version)
        
        old_result = await self.layered_aligner.align(
            episode=episode,
            script_text=script_text,
            novel_text=novel_text,
            script_time_range=script_time_range
        )
        
        old_alignment_path = self._save_alignment_result(
            old_result,
            project_id,
            episode,
            f"old_{old_prompt_version}"
        )
        
        logger.info(f"     Old Overall Score: {old_result.overall_score:.3f}")
        
        # Step 2: 使用新Prompt运行对齐
        logger.info("   → 使用新Prompt运行对齐...")
        self._load_prompt_version(layer, new_prompt_version)
        
        new_result = await self.layered_aligner.align(
            episode=episode,
            script_text=script_text,
            novel_text=novel_text,
            script_time_range=script_time_range
        )
        
        new_alignment_path = self._save_alignment_result(
            new_result,
            project_id,
            episode,
            f"new_{new_prompt_version}"
        )
        
        logger.info(f"     New Overall Score: {new_result.overall_score:.3f}")
        
        # Step 3: 对比性能
        is_better, improvement, reason = self._compare_results(
            old_result,
            new_result,
            layer
        )
        
        # Step 4: 创建测试结果
        ab_result = ABTestResult(
            old_version=old_prompt_version,
            new_version=new_prompt_version,
            old_alignment_path=old_alignment_path,
            new_alignment_path=new_alignment_path,
            old_overall_score=old_result.overall_score,
            new_overall_score=new_result.overall_score,
            old_layer_scores=old_result.layer_scores,
            new_layer_scores=new_result.layer_scores,
            is_better=is_better,
            improvement_percentage=improvement,
            adoption_reason=reason
        )
        
        # Step 5: 保存测试结果
        self._save_ab_result(ab_result, project_id, episode, layer)
        
        logger.info(f"✅ A/B测试完成: {'✅ 采用新版本' if is_better else '❌ 保留旧版本'}")
        logger.info(f"   改进幅度: {improvement:+.2f}%")
        logger.info(f"   理由: {reason}")
        
        return ab_result
    
    def _load_prompt_version(self, layer: str, version: str):
        """加载指定版本的Prompt"""
        # TODO: 实现Prompt版本切换逻辑
        # 这需要修改prompts的加载机制
        logger.debug(f"   加载Prompt: {layer}/{version}")
        pass
    
    def _save_alignment_result(
        self,
        result,
        project_id: str,
        episode: str,
        suffix: str
    ) -> str:
        """保存对齐结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{project_id}_{episode}_{suffix}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.debug(f"   已保存对齐结果: {filepath}")
        return str(filepath)
    
    def _compare_results(
        self,
        old_result,
        new_result,
        layer: str
    ) -> tuple[bool, float, str]:
        """
        对比新旧结果
        
        Returns:
            (is_better, improvement_percentage, reason)
        """
        # 对比Overall Score
        old_score = old_result.overall_score
        new_score = new_result.overall_score
        
        if old_score == 0:
            improvement = 100.0 if new_score > 0 else 0.0
        else:
            improvement = ((new_score - old_score) / old_score) * 100
        
        # 对比特定层的Score
        old_layer_score = old_result.layer_scores.get(layer, 0)
        new_layer_score = new_result.layer_scores.get(layer, 0)
        
        if old_layer_score == 0:
            layer_improvement = 100.0 if new_layer_score > 0 else 0.0
        else:
            layer_improvement = ((new_layer_score - old_layer_score) / old_layer_score) * 100
        
        # 决策逻辑
        is_better = False
        reason = ""
        
        if new_score > old_score * 1.05:  # 改进超过5%
            is_better = True
            reason = f"Overall Score提升{improvement:.2f}%，显著改进"
        elif new_score > old_score and new_layer_score > old_layer_score * 1.10:
            is_better = True
            reason = f"{layer}层Score提升{layer_improvement:.2f}%，目标层改进显著"
        elif new_score >= old_score * 0.95:  # 下降小于5%
            if new_layer_score > old_layer_score:
                is_better = True
                reason = f"{layer}层Score提升，Overall Score变化可接受"
            else:
                is_better = False
                reason = f"Overall Score下降{-improvement:.2f}%或持平，不采用"
        else:
            is_better = False
            reason = f"Overall Score下降{-improvement:.2f}%，拒绝新版本"
        
        return is_better, improvement, reason
    
    def _save_ab_result(
        self,
        ab_result: ABTestResult,
        project_id: str,
        episode: str,
        layer: str
    ):
        """保存A/B测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ab_test_{project_id}_{episode}_{layer}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(ab_result.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"   A/B测试结果已保存: {filepath}")
    
    async def run_optimization_round(
        self,
        project_id: str,
        episode: str,
        script_text: str,
        novel_text: str,
        script_time_range: str,
        annotations: List[AlignmentAnnotation],
        round_number: int
    ) -> OptimizationRound:
        """
        运行完整的优化轮次
        
        Args:
            project_id: 项目ID
            episode: 集数
            script_text: Script文本
            novel_text: Novel文本
            script_time_range: Script时间范围
            annotations: 标注数据
            round_number: 轮次编号
        
        Returns:
            OptimizationRound
        """
        logger.info(f"🔄 开始优化轮次 {round_number}...")
        
        # 计算Heat
        annotations_with_heat = self.heat_calculator.calculate_batch_heat(annotations)
        summary = self.heat_calculator.get_heat_summary(annotations_with_heat)
        
        logger.info(f"   标注数据: {len(annotations)}条")
        logger.info(f"   错误数量: {len([a for a in annotations if not a.is_correct_match])}个")
        logger.info(f"   总Heat: {summary['total_heat']:.1f}")
        
        # 运行对齐（当前版本）
        current_result = await self.layered_aligner.align(
            episode=episode,
            script_text=script_text,
            novel_text=novel_text,
            script_time_range=script_time_range
        )
        
        current_alignment_path = self._save_alignment_result(
            current_result,
            project_id,
            episode,
            f"round_{round_number}"
        )
        
        # 创建OptimizationRound
        round_data = OptimizationRound(
            round_number=round_number,
            project_id=project_id,
            episode=episode,
            prompt_versions={
                "world_building": "v1.0",  # TODO: 动态获取
                "game_mechanics": "v1.0",
                "items_equipment": "v1.0",
                "plot_events": "v1.0"
            },
            alignment_result_path=current_alignment_path,
            overall_score=current_result.overall_score,
            layer_scores=current_result.layer_scores,
            annotations=annotations_with_heat,
            total_annotations=len(annotations_with_heat),
            error_count=len([a for a in annotations_with_heat if not a.is_correct_match]),
            total_heat=summary['total_heat'],
            avg_heat=summary['avg_heat'],
            adopted=False,  # 默认为False，A/B测试后更新
            adoption_reason=None
        )
        
        logger.info(f"✅ 优化轮次 {round_number} 完成")
        logger.info(f"   Overall Score: {current_result.overall_score:.3f}")
        
        return round_data
