#!/usr/bin/env python3
"""
标注工作流程Demo

展示完整的标注、Heat计算、Prompt优化流程
（自动化版本，用于演示）
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.schemas import AlignmentAnnotation
from src.modules.optimization.heat_calculator import HeatCalculator
from src.modules.optimization.prompt_optimizer import PromptOptimizer


def create_demo_annotations():
    """创建Demo标注数据（模拟用户标注）"""
    
    # 基于ep01的实际对齐结果，模拟3个标注
    annotations = [
        AlignmentAnnotation(
            annotation_id="demo_001",
            project_id="PROJ_002",
            episode="ep01",
            layer="world_building",
            script_node_id="world_building_script_2",
            novel_node_id="world_building_novel_3",
            script_content="人类只能依靠序列超凡者不停迁徙",
            novel_content="普通人类只能依靠觉醒序列的超凡者不停迁徙",
            system_similarity=0.75,
            system_confidence="high",
            is_correct_match=True,
            error_type=None,
            human_similarity=0.88,
            human_feedback="系统低估了相似度，两者核心意思完全一致",
            heat_score=0.0  # 将由HeatCalculator计算
        ),
        AlignmentAnnotation(
            annotation_id="demo_002",
            project_id="PROJ_002",
            episode="ep01",
            layer="world_building",
            script_node_id="world_building_script_5",
            novel_node_id="world_building_novel_8",
            script_content="车队第一铁律：不要掉队",
            novel_content="车队铁律第二条：尽可能多储备物资",
            system_similarity=0.65,
            system_confidence="medium",
            is_correct_match=False,
            error_type="wrong_match",
            human_similarity=0.15,
            human_feedback="完全错误的匹配！第一条铁律和第二条铁律是不同的规则",
            heat_score=0.0
        ),
        AlignmentAnnotation(
            annotation_id="demo_003",
            project_id="PROJ_002",
            episode="ep01",
            layer="items_equipment",
            script_node_id="items_equipment_script_1",
            novel_node_id="items_equipment_novel_1",
            script_content="我拥有一辆破旧的二八大杠，可升级",
            novel_content="陈野拥有一辆破旧的二八大杠自行车",
            system_similarity=0.82,
            system_confidence="high",
            is_correct_match=True,
            error_type=None,
            human_similarity=0.90,
            human_feedback="匹配正确，但Script提到'可升级'而Novel未提及，这是关键信息",
            heat_score=0.0
        )
    ]
    
    return annotations


async def demo_workflow():
    """演示完整的标注-优化工作流程"""
    
    print("="*80)
    print("  标注-优化工作流程 Demo")
    print("="*80)
    
    # Step 1: 创建Demo标注
    print("\n【Step 1】创建Demo标注数据...")
    annotations = create_demo_annotations()
    print(f"  ✅ 创建了 {len(annotations)} 条标注")
    
    for i, ann in enumerate(annotations, 1):
        print(f"\n  标注{i}:")
        print(f"    层级: {ann.layer}")
        print(f"    Script: {ann.script_content[:50]}...")
        print(f"    Novel:  {ann.novel_content[:50]}...")
        print(f"    系统相似度: {ann.system_similarity:.2f}")
        print(f"    是否正确: {'✅' if ann.is_correct_match else '❌'}")
        if ann.error_type:
            print(f"    错误类型: {ann.error_type}")
    
    # Step 2: 计算Heat分数
    print("\n" + "="*80)
    print("【Step 2】计算Heat分数...")
    
    heat_calculator = HeatCalculator()
    annotations_with_heat = heat_calculator.calculate_batch_heat(annotations)
    
    print(f"\n  Heat分数:")
    for ann in annotations_with_heat:
        print(f"    {ann.annotation_id}: {ann.heat_score:.1f} "
              f"({'HIGH' if ann.heat_score >= 60 else 'MEDIUM' if ann.heat_score >= 30 else 'LOW'})")
    
    # 统计摘要
    summary = heat_calculator.get_heat_summary(annotations_with_heat)
    print(f"\n  总Heat: {summary['total_heat']:.1f}")
    print(f"  平均Heat: {summary['avg_heat']:.1f}")
    print(f"  高Heat问题: {summary['high_heat_count']}个")
    
    # Step 3: 筛选高Heat问题
    print("\n" + "="*80)
    print("【Step 3】筛选高Heat问题...")
    
    high_heat = heat_calculator.filter_high_heat(annotations_with_heat, threshold=60)
    
    if high_heat:
        print(f"\n  发现 {len(high_heat)} 个高Heat问题:")
        for ann in high_heat:
            print(f"\n  {ann.annotation_id} (Heat: {ann.heat_score:.1f})")
            print(f"    错误类型: {ann.error_type}")
            print(f"    反馈: {ann.human_feedback}")
    else:
        print("\n  ℹ️  无高Heat问题（所有Heat < 60）")
        print("     使用中等Heat问题进行演示...")
        high_heat = [ann for ann in annotations_with_heat if ann.heat_score >= 30]
    
    # Step 4: Prompt优化（如果有高Heat问题）
    if high_heat:
        print("\n" + "="*80)
        print("【Step 4】Prompt优化（Demo - 不实际调用LLM）...")
        
        print("\n  优化策略:")
        print("    1. 聚合错误模式")
        print("    2. 分析错误原因")
        print("    3. LLM生成优化后的Prompt")
        print("    4. 保存新版本")
        
        # 分析错误模式
        error_types = {}
        for ann in high_heat:
            if ann.error_type:
                if ann.error_type not in error_types:
                    error_types[ann.error_type] = []
                error_types[ann.error_type].append(ann)
        
        print(f"\n  错误模式分析:")
        for error_type, anns in error_types.items():
            print(f"    {error_type}: {len(anns)}个案例")
            for ann in anns[:1]:  # 只显示第一个
                print(f"      示例: {ann.human_feedback[:60]}...")
        
        print("\n  ℹ️  实际Prompt优化需要调用LLM，此处仅演示流程")
        print("     使用方法: PromptOptimizer.optimize_prompt()")
    
    # Step 5: 保存标注数据
    print("\n" + "="*80)
    print("【Step 5】保存标注数据...")
    
    output_dir = Path("data/alignment_optimization/annotations/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"demo_annotations_{timestamp}.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for ann in annotations_with_heat:
            f.write(json.dumps(ann.dict(), ensure_ascii=False, default=str) + '\n')
    
    print(f"  ✅ 已保存到: {output_file}")
    
    # Step 6: 生成报告
    print("\n" + "="*80)
    print("【Step 6】生成标注报告...")
    
    report = {
        "project_id": "PROJ_002",
        "episode": "ep01",
        "annotation_count": len(annotations_with_heat),
        "error_count": len([a for a in annotations_with_heat if not a.is_correct_match]),
        "total_heat": summary['total_heat'],
        "avg_heat": summary['avg_heat'],
        "high_heat_count": summary['high_heat_count'],
        "error_breakdown": summary['error_type_breakdown'],
        "recommendations": [
            "优化world_building Prompt以提高规则匹配准确性",
            "降低items_equipment层的对齐阈值",
            "增强LLM相似度判断的上下文理解"
        ]
    }
    
    report_file = output_dir / f"demo_report_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ 报告已保存到: {report_file}")
    
    print("\n" + "="*80)
    print("  ✅ Demo工作流程完成！")
    print("="*80)
    
    print("\n📋 下一步:")
    print("  1. 使用真实CLI工具标注实际数据:")
    print("     python scripts/annotate_alignment.py \\")
    print("       --project PROJ_002 --episode ep01 \\")
    print("       --alignment-file data/projects/PROJ_002/alignment/ep01_body_alignment.json")
    print("\n  2. 分析标注结果并优化Prompt")
    print("\n  3. 运行A/B测试验证优化效果")


if __name__ == "__main__":
    asyncio.run(demo_workflow())
