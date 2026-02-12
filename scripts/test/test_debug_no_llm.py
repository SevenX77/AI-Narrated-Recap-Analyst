"""
调试测试：完全不使用LLM
"""

import asyncio
import sys
from pathlib import Path

print("=" * 80, flush=True)
print("开始测试（完全不使用LLM）", flush=True)
print("=" * 80, flush=True)

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
from src.core.schemas_script import ScriptProcessingConfig

async def test_no_llm():
    """不使用LLM的测试"""
    print("\n进入async函数", flush=True)
    
    # 检查SRT文件
    source_srt = "分析资料/有原小说/01_末哥超凡公路/srt/ep01.srt"
    print(f"\n检查SRT文件: {source_srt}", flush=True)
    
    import os
    if not os.path.exists(source_srt):
        print(f"❌ 文件不存在", flush=True)
        return
    
    print(f"✅ 文件存在", flush=True)
    
    # 创建配置
    print("\n创建配置（禁用所有LLM）", flush=True)
    config = ScriptProcessingConfig(
        enable_hook_detection=False,
        enable_hook_analysis=False,
        enable_abc_classification=False,
        save_intermediate_results=False,
        output_markdown_reports=False
    )
    print("✅ 配置创建成功", flush=True)
    
    # 创建workflow
    print("\n创建workflow实例", flush=True)
    workflow = ScriptProcessingWorkflow()
    print("✅ workflow创建成功", flush=True)
    
    # 禁用text_extractor的LLM
    print("\n禁用text_extractor的LLM", flush=True)
    workflow.text_extractor.use_llm = False
    print("✅ text_extractor.use_llm = False", flush=True)
    
    # 执行workflow
    print("\n开始执行workflow.run()", flush=True)
    
    try:
        result = await workflow.run(
            srt_path=source_srt,
            project_name="test_no_llm",
            episode_name="ep01",
            config=config
        )
        
        print("\n✅ workflow.run()执行完成", flush=True)
        print(f"  - success: {result.success}", flush=True)
        print(f"  - processing_time: {result.processing_time:.1f}s", flush=True)
        print(f"  - llm_calls_count: {result.llm_calls_count}", flush=True)
        
        if result.import_result:
            print(f"  - import: 成功，{result.import_result.entry_count} 条", flush=True)
        
        if result.extraction_result:
            print(f"  - extraction: 成功，{result.extraction_result.processed_chars} 字符", flush=True)
            print(f"  - mode: {result.extraction_result.processing_mode}", flush=True)
        
        if result.segmentation_result:
            print(f"  - segmentation: 成功，{result.segmentation_result.total_segments} 段", flush=True)
        
        if result.validation_report:
            print(f"  - validation: 质量评分 {result.validation_report.quality_score}/100", flush=True)
        
        if result.errors:
            print(f"  - errors: {len(result.errors)} 个", flush=True)
            for err in result.errors:
                print(f"    - {err.phase}: {err.message[:80]}", flush=True)
        
    except Exception as e:
        print(f"\n❌ 执行出错: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()

print("\n创建asyncio事件循环", flush=True)
asyncio.run(test_no_llm())

print("\n" + "=" * 80, flush=True)
print("测试结束", flush=True)
print("=" * 80, flush=True)
