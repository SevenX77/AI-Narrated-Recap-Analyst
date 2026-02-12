"""
测试修复后的workflow（启用LLM）
"""

import asyncio
import sys
import os
from pathlib import Path

print("=" * 80, flush=True)
print("测试Workflow（启用LLM）", flush=True)
print("=" * 80, flush=True)

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
from src.core.schemas_script import ScriptProcessingConfig

async def test_with_llm():
    """测试启用LLM的workflow"""
    print("\n进入async函数", flush=True)
    
    # 使用小的测试SRT文件
    source_srt = "分析资料/有原小说/01_末哥超凡公路/srt/ep05.srt"
    print(f"\n使用测试SRT: {source_srt}", flush=True)
    
    if not os.path.exists(source_srt):
        print(f"❌ 文件不存在", flush=True)
        return
    
    # 查看文件大小
    file_size = os.path.getsize(source_srt)
    print(f"文件大小: {file_size/1024:.1f} KB", flush=True)
    
    # 查看行数
    with open(source_srt, 'r', encoding='utf-8') as f:
        lines = len(f.readlines())
    print(f"文件行数: {lines}", flush=True)
    
    # 创建配置（启用LLM，但禁用Hook检测节省时间）
    print("\n创建配置（启用LLM）", flush=True)
    config = ScriptProcessingConfig(
        enable_hook_detection=False,  # ep05不需要Hook检测
        enable_hook_analysis=False,
        enable_abc_classification=True,  # 启用ABC分类（需要LLM）
        save_intermediate_results=True,
        output_markdown_reports=True,
        text_extraction_provider="deepseek",
        segmentation_provider="deepseek"
    )
    print("✅ 配置创建成功", flush=True)
    print(f"  - 文本提取LLM: {config.text_extraction_provider}", flush=True)
    print(f"  - 分段LLM: {config.segmentation_provider}", flush=True)
    print(f"  - ABC分类: {config.enable_abc_classification}", flush=True)
    
    # 创建workflow
    print("\n创建workflow实例", flush=True)
    workflow = ScriptProcessingWorkflow()
    print("✅ workflow创建成功", flush=True)
    
    # 执行workflow
    print("\n开始执行workflow.run()...", flush=True)
    print("（这将调用真实的LLM API，请耐心等待）", flush=True)
    
    try:
        result = await workflow.run(
            srt_path=source_srt,
            project_name="test_llm_enabled",
            episode_name="ep05",
            config=config
        )
        
        print("\n" + "=" * 80, flush=True)
        print("✅ workflow.run()执行完成", flush=True)
        print("=" * 80, flush=True)
        
        print(f"\n📊 执行结果:", flush=True)
        print(f"  - 状态: {'✅ 成功' if result.success else '❌ 失败'}", flush=True)
        print(f"  - 总耗时: {result.processing_time:.1f} 秒", flush=True)
        print(f"  - LLM调用次数: {result.llm_calls_count}", flush=True)
        print(f"  - 总成本: ${result.total_cost:.4f}", flush=True)
        
        if result.import_result:
            print(f"\n📥 Phase 1: SRT导入", flush=True)
            print(f"  - 条目数: {result.import_result.entry_count}", flush=True)
            print(f"  - 总时长: {result.import_result.total_duration}", flush=True)
        
        if result.extraction_result:
            print(f"\n🔧 Phase 2: 文本提取", flush=True)
            print(f"  - 处理模式: {result.extraction_result.processing_mode}", flush=True)
            print(f"  - 原始字符: {result.extraction_result.original_chars}", flush=True)
            print(f"  - 处理后字符: {result.extraction_result.processed_chars}", flush=True)
            print(f"  - 处理耗时: {result.extraction_result.processing_time:.1f}s", flush=True)
        
        if result.segmentation_result:
            print(f"\n✂️ Phase 5: 脚本分段", flush=True)
            print(f"  - 总段落数: {result.segmentation_result.total_segments}", flush=True)
            print(f"  - 平均句子数: {result.segmentation_result.avg_sentence_count:.1f}", flush=True)
            
            # ABC分布
            category_counts = {}
            for seg in result.segmentation_result.segments:
                cat = seg.category or "Unknown"
                category_counts[cat] = category_counts.get(cat, 0) + 1
            print(f"  - ABC分布: {category_counts}", flush=True)
        
        if result.validation_report:
            print(f"\n✅ Phase 6: 质量验证", flush=True)
            print(f"  - 质量评分: {result.validation_report.quality_score:.0f}/100", flush=True)
            print(f"  - 是否通过: {result.validation_report.is_valid}", flush=True)
        
        if result.errors:
            print(f"\n⚠️ 错误:", flush=True)
            for err in result.errors:
                print(f"  - {err.phase}: {err.message[:80]}", flush=True)
        
        # 检查输出文件
        output_md = f"data/projects/test_llm_enabled/script/ep05.md"
        if os.path.exists(output_md):
            with open(output_md, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            print(f"\n📄 输出文件:", flush=True)
            print(f"  - 路径: {output_md}", flush=True)
            print(f"  - 行数: {len(lines)}", flush=True)
            print(f"  - 前10行:", flush=True)
            for line in lines[:10]:
                print(f"    {line.rstrip()}", flush=True)
        
        print("\n" + "=" * 80, flush=True)
        print("🎉 测试完成！", flush=True)
        print("=" * 80, flush=True)
        
    except Exception as e:
        print(f"\n❌ 执行出错: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()

print("\n创建asyncio事件循环", flush=True)
asyncio.run(test_with_llm())
