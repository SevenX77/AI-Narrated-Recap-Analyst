"""
测试Hook-Body分离架构的完整流程

测试内容：
    - Phase 0: Novel预处理
    - Phase 1: Hook分析（ep01）
    - Phase 2: Body对齐（占位）
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.ingestion_workflow_v3 import IngestionWorkflowV3
from src.utils.logger import logger


async def test_phase_0():
    """测试Phase 0: Novel预处理"""
    print("\n" + "=" * 60)
    print("测试 Phase 0: Novel预处理")
    print("=" * 60)
    
    workflow = IngestionWorkflowV3("PROJ_002")
    result = await workflow.preprocess_novel()
    
    print("\n✅ Phase 0 测试完成")
    print(f"简介长度: {result['introduction_length']} 字符")
    print(f"总章节数: {result['total_chapters']}")
    
    return result


async def test_phase_1():
    """测试Phase 1: Hook分析"""
    print("\n" + "=" * 60)
    print("测试 Phase 1: Hook分析")
    print("=" * 60)
    
    workflow = IngestionWorkflowV3("PROJ_002")
    result = await workflow.analyze_hook("ep01")
    
    print("\n✅ Phase 1 测试完成")
    print(f"has_hook: {result['detection']['has_hook']}")
    print(f"body_start_time: {result['detection']['body_start_time']}")
    print(f"confidence: {result['detection']['confidence']}")
    print(f"intro_similarity: {result['intro_similarity']:.2f}")
    
    if result.get('hook_content'):
        hook_content = result['hook_content']
        layered = hook_content.get('layered_extraction', {})
        print("\nHook分层内容统计:")
        for layer, nodes in layered.items():
            print(f"  {layer}: {len(nodes)} 个节点")
    
    return result


async def test_phase_2():
    """测试Phase 2: Body对齐"""
    print("\n" + "=" * 60)
    print("测试 Phase 2: Body对齐")
    print("=" * 60)
    
    workflow = IngestionWorkflowV3("PROJ_002")
    result = await workflow.align_body("ep01")
    
    print("\n✅ Phase 2 测试完成")
    print(f"episode: {result['episode']}")
    print(f"status: {result['status']}")
    
    return result


async def test_full_workflow():
    """测试完整流程"""
    print("\n" + "=" * 60)
    print("测试完整流程（一键运行）")
    print("=" * 60)
    
    workflow = IngestionWorkflowV3("PROJ_002")
    result = await workflow.run(episodes=["ep01"])
    
    print("\n✅ 完整流程测试完成")
    print(f"episodes_processed: {result['episodes_processed']}")
    print(f"status: {result['status']}")
    
    return result


def verify_outputs():
    """验证输出文件是否生成"""
    print("\n" + "=" * 60)
    print("验证输出文件")
    print("=" * 60)
    
    base_dir = project_root / "data/projects/PROJ_002"
    
    files_to_check = [
        "preprocessing/novel_introduction_clean.txt",
        "preprocessing/novel_chapters_index.json",
        "hook_analysis/ep01_hook_analysis.json",
        "alignment/ep01_body_alignment.json",
    ]
    
    for file_path in files_to_check:
        full_path = base_dir / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        
        if exists:
            size = full_path.stat().st_size
            print(f"   大小: {size} bytes")


async def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("Hook-Body分离架构 - 完整测试")
    print("=" * 60)
    
    try:
        # 测试各个Phase
        print("\n【测试模式】分阶段执行")
        
        await test_phase_0()
        await test_phase_1()
        await test_phase_2()
        
        # 验证输出
        verify_outputs()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
