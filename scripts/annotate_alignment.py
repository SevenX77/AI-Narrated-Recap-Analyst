#!/usr/bin/env python3
"""
对齐结果标注工具 - CLI入口

用法:
    python scripts/annotate_alignment.py \
        --project PROJ_002 \
        --episode ep01 \
        --alignment-file data/projects/PROJ_002/alignment/ep01_body_alignment.json \
        --annotator your_name
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.optimization.annotator import AlignmentAnnotator
from src.modules.optimization.heat_calculator import HeatCalculator
from src.utils.logger import logger


def main():
    parser = argparse.ArgumentParser(description="对齐结果标注工具")
    parser.add_argument("--project", required=True, help="项目ID")
    parser.add_argument("--episode", required=True, help="集数")
    parser.add_argument("--alignment-file", required=True, help="对齐结果文件路径")
    parser.add_argument("--annotator", default=None, help="标注人姓名")
    
    args = parser.parse_args()
    
    # 初始化
    annotator = AlignmentAnnotator()
    heat_calculator = HeatCalculator()
    
    # 标注
    logger.info(f"🎯 开始标注: {args.project}/{args.episode}")
    
    annotations = annotator.annotate_alignment_result(
        alignment_result_path=args.alignment_file,
        project_id=args.project,
        episode=args.episode,
        annotator_name=args.annotator
    )
    
    if not annotations:
        logger.warning("未生成任何标注")
        return
    
    # 计算Heat
    logger.info("🔥 计算Heat分数...")
    annotations_with_heat = heat_calculator.calculate_batch_heat(annotations)
    
    # 显示摘要
    summary = heat_calculator.get_heat_summary(annotations_with_heat)
    
    print("\n" + "="*60)
    print("  标注摘要")
    print("="*60)
    print(f"总标注数: {summary['total_count']}")
    print(f"总Heat分数: {summary['total_heat']}")
    print(f"平均Heat: {summary['avg_heat']}")
    print(f"高Heat问题(>=60): {summary['high_heat_count']}")
    print(f"中等Heat(30-60): {summary['medium_heat_count']}")
    print(f"低Heat(<30): {summary['low_heat_count']}")
    print("\n错误类型分布:")
    for error_type, count in summary['error_type_breakdown'].items():
        print(f"  {error_type}: {count}")
    print("="*60)
    
    logger.info("✅ 标注完成！")


if __name__ == "__main__":
    main()
