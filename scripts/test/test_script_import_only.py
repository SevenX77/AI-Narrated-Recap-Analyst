"""
测试Phase 1: SRT导入

只测试SRT导入功能，不调用LLM
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
from src.core.schemas_script import ScriptProcessingConfig

async def test_import_only():
    """
    测试SRT导入
    """
    print("=" * 80)
    print("测试Phase 1: SRT导入")
    print("=" * 80)
    
    # 原始SRT文件
    source_srt = "分析资料/有原小说/01_末哥超凡公路/srt/ep01.srt"
    
    print(f"\n原始SRT文件: {source_srt}")
    
    # 检查文件是否存在
    import os
    if not os.path.exists(source_srt):
        print(f"❌ 文件不存在: {source_srt}")
        return
    
    file_size = os.path.getsize(source_srt)
    print(f"文件大小: {file_size/1024:.1f} KB")
    
    # 配置：禁用所有LLM调用
    config = ScriptProcessingConfig(
        enable_hook_detection=False,
        enable_hook_analysis=False,
        enable_abc_classification=False,
        save_intermediate_results=True,
        output_markdown_reports=False
    )
    
    print("\n配置:")
    print(f"  - Hook检测: {config.enable_hook_detection}")
    print(f"  - ABC分类: {config.enable_abc_classification}")
    
    # 初始化workflow
    print("\n初始化workflow...")
    workflow = ScriptProcessingWorkflow()
    
    # 执行workflow
    print("\n开始执行workflow...")
    try:
        result = await workflow.run(
            srt_path=source_srt,
            project_name="test_import_only",
            episode_name="ep01",
            config=config
        )
        
        print("\n" + "=" * 80)
        print("执行结果")
        print("=" * 80)
        
        print(f"\n状态: {result.success}")
        print(f"耗时: {result.processing_time:.1f} 秒")
        print(f"LLM调用: {result.llm_calls_count} 次")
        print(f"成本: ${result.total_cost:.4f}")
        
        # Phase 1: 导入
        if result.import_result:
            print(f"\nPhase 1: SRT导入 ✅")
            print(f"  - 原始路径: {result.import_result.original_path}")
            print(f"  - 保存路径: {result.import_result.saved_path}")
            print(f"  - 条目数量: {result.import_result.entry_count}")
            print(f"  - 总时长: {result.import_result.total_duration}")
            
            # 查看导入后的文件
            import_path = result.import_result.saved_path
            if os.path.exists(import_path):
                with open(import_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                print(f"\n导入后文件:")
                print(f"  - 路径: {import_path}")
                print(f"  - 行数: {len(lines)}")
                print(f"  - 前10行:")
                for line in lines[:10]:
                    print(f"    {line.rstrip()}")
        else:
            print(f"\nPhase 1: SRT导入 ❌")
        
        # Phase 2: 文本提取
        if result.extraction_result:
            print(f"\nPhase 2: 文本提取 ✅")
            print(f"  - 原始字符: {result.extraction_result.original_chars}")
            print(f"  - 处理后字符: {result.extraction_result.processed_chars}")
        
        # 检查是否有错误
        if result.errors:
            print(f"\n错误:")
            for err in result.errors:
                print(f"  - {err.phase}: {err.message}")
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_import_only())
