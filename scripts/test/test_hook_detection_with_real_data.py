"""
使用真实SRT数据测试Hook检测和分离

用于验证：
1. Hook检测是否正确识别Hook部分
2. Hook是否正确分离
3. ep01执行Hook检测，其他集数不执行

Author: AI-Narrated Recap Analyst Team
Created: 2026-02-10
"""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
from src.core.schemas_script import ScriptProcessingConfig


async def test_with_real_srt():
    """
    使用真实SRT数据测试
    """
    print("=" * 80)
    print("🎬 使用真实SRT数据测试Hook检测")
    print("=" * 80)
    
    # ============================================================
    # 配置真实数据路径
    # ============================================================
    
    # 请提供真实的项目数据
    # 示例：天命桃花项目
    real_project_name = "天命桃花_test"  # 修改为你的项目名
    
    # 真实SRT文件路径（请根据实际情况修改）
    test_cases = [
        {
            "episode_name": "ep01",
            "srt_path": f"data/projects/{real_project_name}/raw/ep01.srt",
            "novel_intro": "末日降临，诡异横行。江城沦陷，上沪告急..."  # 可选
        },
        {
            "episode_name": "ep02",
            "srt_path": f"data/projects/{real_project_name}/raw/ep02.srt",
            "novel_intro": None  # ep02不需要
        }
    ]
    
    # 检查文件是否存在
    available_cases = []
    for case in test_cases:
        if os.path.exists(case["srt_path"]):
            available_cases.append(case)
            print(f"✓ 找到文件: {case['srt_path']}")
        else:
            print(f"✗ 文件不存在: {case['srt_path']}")
    
    if not available_cases:
        print("\n❌ 没有找到可用的SRT文件")
        print("\n请提供真实的SRT文件路径，例如：")
        print("  - data/projects/天命桃花_test/raw/ep01.srt")
        print("  - data/projects/末哥超凡公路_test/raw/ep01.srt")
        print("\n或者修改脚本中的 real_project_name 变量")
        return
    
    # ============================================================
    # 执行测试
    # ============================================================
    
    config = ScriptProcessingConfig(
        enable_hook_detection=True,
        enable_hook_analysis=False,
        enable_abc_classification=True,
        min_quality_score=70  # 稍微宽松
    )
    
    workflow = ScriptProcessingWorkflow()
    results = {}
    
    print(f"\n开始处理 {len(available_cases)} 个集数...")
    
    for case in available_cases:
        print(f"\n{'=' * 80}")
        print(f"处理: {case['episode_name']}")
        print(f"{'=' * 80}")
        
        result = await workflow.run(
            srt_path=case["srt_path"],
            project_name=f"{real_project_name}_hook_test",
            episode_name=case["episode_name"],
            config=config,
            novel_intro=case.get("novel_intro")
        )
        
        results[case["episode_name"]] = result
        
        # 输出结果
        print(f"\n📊 {case['episode_name']} 处理结果:")
        print(f"  - 状态: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"  - 耗时: {result.processing_time:.1f} 秒")
        print(f"  - 成本: ${result.total_cost:.4f}")
        
        # Hook检测结果
        if result.hook_detection_result:
            print(f"\n  🎣 Hook检测:")
            print(f"    - 已执行: ✅")
            print(f"    - 是否有Hook: {result.hook_detection_result.has_hook}")
            print(f"    - 置信度: {result.hook_detection_result.confidence:.2f}")
            
            if result.hook_detection_result.has_hook:
                print(f"    - Hook结束时间: {result.hook_detection_result.hook_end_time}")
                print(f"    - Body起点时间: {result.hook_detection_result.body_start_time}")
                print(f"    - Hook段落数: {len(result.hook_detection_result.hook_segment_indices)}")
                print(f"    - Body段落数: {len(result.hook_detection_result.body_segment_indices)}")
            
            print(f"    - 判断理由: {result.hook_detection_result.reasoning[:100]}...")
        else:
            print(f"\n  🎣 Hook检测: ⏭️ 未执行（预期行为）")
        
        # 分段结果
        if result.segmentation_result:
            print(f"\n  ✂️ 分段结果:")
            print(f"    - 总段落数: {result.segmentation_result.total_segments}")
            
            # ABC分布
            category_counts = {}
            for seg in result.segmentation_result.segments:
                cat = seg.category or "Unknown"
                category_counts[cat] = category_counts.get(cat, 0) + 1
            print(f"    - ABC分布: {category_counts}")
            
            # 显示前3个段落
            print(f"\n  前3个段落:")
            for seg in result.segmentation_result.segments[:3]:
                print(f"    - [{seg.start_time}-{seg.end_time}] [{seg.category}]")
                print(f"      {seg.content[:50]}...")
        
        # 质量评分
        if result.validation_report:
            print(f"\n  ✅ 质量评分: {result.validation_report.quality_score:.0f}/100")
    
    # ============================================================
    # 总结
    # ============================================================
    
    print("\n" + "=" * 80)
    print("📈 测试总结")
    print("=" * 80)
    
    hook_detected_count = sum(
        1 for r in results.values() 
        if r.hook_detection_result is not None
    )
    
    has_hook_count = sum(
        1 for r in results.values()
        if r.hook_detection_result and r.hook_detection_result.has_hook
    )
    
    print(f"\n统计:")
    print(f"  - 处理集数: {len(results)}")
    print(f"  - Hook检测执行次数: {hook_detected_count}")
    print(f"  - 实际检测到Hook: {has_hook_count}")
    
    print(f"\n验证:")
    if hook_detected_count == 1:
        print(f"  ✅ Hook检测仅在ep01执行")
    else:
        print(f"  ❌ Hook检测执行次数异常: {hook_detected_count}")
    
    # 查看生成的Markdown文件
    print(f"\n生成的文件:")
    for ep_name in results.keys():
        md_path = f"data/projects/{real_project_name}_hook_test/script/{ep_name}.md"
        if os.path.exists(md_path):
            print(f"  ✓ {md_path}")
            
            # 读取前10行预览
            with open(md_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
            print(f"    预览（前10行）:")
            for line in lines:
                print(f"      {line.rstrip()}")
        else:
            print(f"  ✗ {md_path} (未找到)")
    
    print(f"\n{'=' * 80}")


async def main():
    """
    主函数
    """
    await test_with_real_srt()


if __name__ == "__main__":
    asyncio.run(main())
