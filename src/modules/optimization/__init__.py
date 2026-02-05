"""
自反馈优化模块

包含：
- annotator: CLI标注工具
- heat_calculator: Heat分数计算器
- prompt_optimizer: Prompt自动优化器
- ab_tester: A/B测试框架
"""

from src.modules.optimization.heat_calculator import HeatCalculator
from src.modules.optimization.annotator import AlignmentAnnotator

__all__ = [
    "HeatCalculator",
    "AlignmentAnnotator",
]
