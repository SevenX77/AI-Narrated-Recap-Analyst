#!/usr/bin/env python3
"""
V4.1 深入分析脚本

对ep01/02/03的对齐结果进行深入分析，识别：
1. 高质量匹配案例
2. 低质量匹配案例
3. 各层特征分析
4. 优化建议
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def analyze_alignment_quality(alignment_data: dict, episode: str):
    """分析单集的对齐质量"""
    
    print(f"\n{'='*80}")
    print(f"  {episode} 深入分析")
    print(f"{'='*80}")
    
    layered = alignment_data.get('layered_alignment', {})
    quality = alignment_data.get('alignment_quality', {})
    
    # 总体概况
    print(f"\n【总体概况】")
    print(f"  Overall Score: {quality.get('overall_score', 0):.3f}")
    print(f"  Layer Scores:")
    for layer, score in quality.get('layer_scores', {}).items():
        print(f"    {layer}: {score:.3f}")
    
    # 各层详细分析
    for layer_name in ['world_building', 'game_mechanics', 'items_equipment', 'plot_events']:
        analyze_layer(layered.get(layer_name, {}), layer_name)
    
    return layered


def analyze_layer(layer_data: dict, layer_name: str):
    """分析单层的对齐结果"""
    
    print(f"\n{'='*80}")
    print(f"  {layer_name}层 分析")
    print(f"{'='*80}")
    
    alignments = layer_data.get('alignments', [])
    
    if not alignments:
        print(f"  ⚠️  无对齐数据")
        return
    
    # 统计
    similarities = [a.get('similarity', 0) for a in alignments]
    avg_sim = sum(similarities) / len(similarities) if similarities else 0
    
    high_quality = [a for a in alignments if a.get('similarity', 0) >= 0.8]
    medium_quality = [a for a in alignments if 0.5 <= a.get('similarity', 0) < 0.8]
    low_quality = [a for a in alignments if a.get('similarity', 0) < 0.5]
    
    print(f"\n  统计:")
    print(f"    总对齐数: {len(alignments)}")
    print(f"    平均相似度: {avg_sim:.3f}")
    print(f"    高质量(≥0.8): {len(high_quality)}个 ({len(high_quality)/len(alignments)*100:.1f}%)")
    print(f"    中等质量(0.5-0.8): {len(medium_quality)}个 ({len(medium_quality)/len(alignments)*100:.1f}%)")
    print(f"    低质量(<0.5): {len(low_quality)}个 ({len(low_quality)/len(alignments)*100:.1f}%)")
    
    # 高质量案例
    if high_quality:
        print(f"\n  ✅ 高质量匹配案例（相似度≥0.8）:")
        for i, align in enumerate(sorted(high_quality, key=lambda x: x.get('similarity', 0), reverse=True)[:3], 1):
            print(f"\n    案例{i}: 相似度 {align.get('similarity', 0):.3f}")
            script = align.get('script_node', {}).get('content', '')[:50]
            novel = align.get('novel_node', {}).get('content', '')[:50]
            print(f"      Script: {script}...")
            print(f"      Novel:  {novel}...")
            if 'reasoning' in align:
                reasoning = align['reasoning'][:80]
                print(f"      理由: {reasoning}...")
    
    # 低质量案例
    if low_quality:
        print(f"\n  ⚠️  低质量匹配案例（相似度<0.5）:")
        for i, align in enumerate(sorted(low_quality, key=lambda x: x.get('similarity', 0))[:3], 1):
            print(f"\n    案例{i}: 相似度 {align.get('similarity', 0):.3f}")
            script = align.get('script_node', {}).get('content', '')[:50]
            novel = align.get('novel_node', {}).get('content', '')[:50]
            print(f"      Script: {script}...")
            print(f"      Novel:  {novel}...")
            if 'reasoning' in align:
                reasoning = align['reasoning'][:80]
                print(f"      理由: {reasoning}...")


def cross_episode_analysis(all_data: dict):
    """跨集数分析"""
    
    print(f"\n{'='*80}")
    print(f"  跨集数分析")
    print(f"{'='*80}")
    
    # 各层覆盖率趋势
    print(f"\n【各层Coverage Score趋势】")
    print(f"{'集数':<10} {'设定':<10} {'系统':<10} {'道具':<10} {'情节':<10}")
    print(f"{'-'*50}")
    
    for ep, data in sorted(all_data.items()):
        quality = data.get('alignment_quality', {})
        layer_scores = quality.get('layer_scores', {})
        print(f"{ep:<10} "
              f"{layer_scores.get('world_building', 0):<10.3f} "
              f"{layer_scores.get('game_mechanics', 0):<10.3f} "
              f"{layer_scores.get('items_equipment', 0):<10.3f} "
              f"{layer_scores.get('plot_events', 0):<10.3f}")
    
    # 相似度分布分析
    print(f"\n【相似度分布分析】")
    
    all_similarities = defaultdict(list)
    
    for ep, data in all_data.items():
        layered = data.get('layered_alignment', {})
        for layer_name in ['world_building', 'game_mechanics', 'items_equipment', 'plot_events']:
            layer_data = layered.get(layer_name, {})
            for align in layer_data.get('alignments', []):
                sim = align.get('similarity', 0)
                all_similarities[layer_name].append(sim)
    
    for layer_name, sims in all_similarities.items():
        if sims:
            avg = sum(sims) / len(sims)
            high = len([s for s in sims if s >= 0.8])
            print(f"\n  {layer_name}:")
            print(f"    总匹配数: {len(sims)}")
            print(f"    平均相似度: {avg:.3f}")
            print(f"    高质量数: {high} ({high/len(sims)*100:.1f}%)")


def generate_optimization_recommendations(all_data: dict):
    """生成优化建议"""
    
    print(f"\n{'='*80}")
    print(f"  优化建议")
    print(f"{'='*80}")
    
    # 分析各层的问题
    layer_issues = defaultdict(list)
    
    for ep, data in all_data.items():
        layered = data.get('layered_alignment', {})
        quality = data.get('alignment_quality', {})
        layer_scores = quality.get('layer_scores', {})
        
        for layer_name in ['world_building', 'game_mechanics', 'items_equipment', 'plot_events']:
            score = layer_scores.get(layer_name, 0)
            layer_data = layered.get(layer_name, {})
            alignments = layer_data.get('alignments', [])
            
            if score < 0.3:
                layer_issues[layer_name].append({
                    'episode': ep,
                    'score': score,
                    'alignment_count': len(alignments)
                })
    
    # 生成建议
    recommendations = []
    
    for layer_name, issues in layer_issues.items():
        if len(issues) >= 2:  # 多集都有问题
            avg_score = sum(i['score'] for i in issues) / len(issues)
            recommendations.append({
                'priority': 'HIGH',
                'layer': layer_name,
                'issue': f'覆盖率持续低于30%（平均{avg_score:.3f}）',
                'action': [
                    f'1. 优化{layer_name} Prompt，增强提取能力',
                    f'2. 降低对齐阈值（当前可能过高）',
                    f'3. 增加正反例示例到Prompt'
                ]
            })
    
    # 显示建议
    print(f"\n  ⚠️  发现 {len(recommendations)} 个需要优先处理的问题\n")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"  【建议{i}】{rec['priority']}")
        print(f"  层级: {rec['layer']}")
        print(f"  问题: {rec['issue']}")
        print(f"  行动:")
        for action in rec['action']:
            print(f"    {action}")
        print()
    
    # 通用建议
    print(f"  【通用建议】")
    print(f"  1. 使用CLI工具标注错误案例")
    print(f"  2. 运行PromptOptimizer优化高Heat问题")
    print(f"  3. 使用ABTester验证优化效果")
    print(f"  4. 迭代5轮后生成最终报告")


def main():
    """主函数"""
    
    print("="*80)
    print("  V4.1 深入分析报告")
    print("="*80)
    
    # 加载数据
    episodes = ['ep01', 'ep02', 'ep03']
    all_data = {}
    
    for ep in episodes:
        filepath = f'data/projects/PROJ_002/alignment/{ep}_body_alignment.json'
        if Path(filepath).exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                all_data[ep] = json.load(f)
    
    # 单集分析
    for ep, data in sorted(all_data.items()):
        analyze_alignment_quality(data, ep)
    
    # 跨集分析
    cross_episode_analysis(all_data)
    
    # 优化建议
    generate_optimization_recommendations(all_data)
    
    print(f"\n{'='*80}")
    print(f"  ✅ 深入分析完成")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
