"""
测试脚本：ScriptProcessingWorkflow 工作流测试

测试完整的脚本处理流程，从SRT导入到质量验证。

Author: AI-Narrated Recap Analyst Team
Created: 2026-02-10
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
from src.core.schemas_script import ScriptProcessingConfig


async def test_script_processing_workflow():
    """
    测试 ScriptProcessingWorkflow 完整流程
    """
    print("=" * 80)
    print("测试 ScriptProcessingWorkflow")
    print("=" * 80)
    
    # ============================================================
    # 配置参数
    # ============================================================
    
    # 项目信息
    project_name = "天命桃花_test_script"
    episode_name = "ep01"
    
    # SRT文件路径（请根据实际情况修改）
    srt_path = "data/projects/天命桃花_test/raw/ep01.srt"
    
    # 检查文件是否存在
    if not os.path.exists(srt_path):
        print(f"❌ SRT文件不存在: {srt_path}")
        print("请提供有效的SRT文件路径")
        return
    
    # Novel参考数据（可选）
    novel_reference = None  # 如果有Novel文本，可以提供
    novel_intro = None  # 如果有Novel简介，可以提供
    novel_metadata = None  # 如果有Novel元数据，可以提供
    
    # 工作流配置
    config = ScriptProcessingConfig(
        # 功能开关
        enable_hook_detection=True,  # 启用Hook检测（仅ep01）
        enable_hook_analysis=False,  # 不启用Hook分析（需要Novel数据）
        enable_abc_classification=True,  # 启用ABC分类
        
        # 重试配置
        retry_on_error=True,
        max_retries=3,
        retry_delay=2.0,
        request_delay=1.0,
        
        # LLM配置
        text_extraction_provider="deepseek",
        hook_detection_provider="deepseek",
        segmentation_provider="deepseek",
        
        # 错误处理
        continue_on_error=False,
        save_intermediate_results=True,
        
        # 输出配置
        output_markdown_reports=True,
        
        # 质量门禁
        min_quality_score=75
    )
    
    # ============================================================
    # 执行工作流
    # ============================================================
    
    print(f"\n📋 测试配置:")
    print(f"  - 项目名称: {project_name}")
    print(f"  - 集数: {episode_name}")
    print(f"  - SRT文件: {srt_path}")
    print(f"  - Hook检测: {config.enable_hook_detection}")
    print(f"  - Hook分析: {config.enable_hook_analysis}")
    print(f"  - ABC分类: {config.enable_abc_classification}")
    print(f"  - 最低质量评分: {config.min_quality_score}")
    print()
    
    # 初始化工作流
    workflow = ScriptProcessingWorkflow()
    
    # 执行工作流
    try:
        result = await workflow.run(
            srt_path=srt_path,
            project_name=project_name,
            episode_name=episode_name,
            config=config,
            novel_reference=novel_reference,
            novel_intro=novel_intro,
            novel_metadata=novel_metadata
        )
        
        # ============================================================
        # 输出结果
        # ============================================================
        
        print("\n" + "=" * 80)
        print("📊 处理结果汇总")
        print("=" * 80)
        
        if result.success:
            print("✅ 工作流执行成功！")
        else:
            print("❌ 工作流执行失败！")
        
        print(f"\n⏱️  处理统计:")
        print(f"  - 总耗时: {result.processing_time:.1f} 秒")
        print(f"  - LLM调用次数: {result.llm_calls_count}")
        print(f"  - 总成本: ${result.total_cost:.4f} USD")
        
        # Phase 1: SRT导入
        if result.import_result:
            print(f"\n📥 Phase 1: SRT导入")
            print(f"  - 条目数量: {result.import_result.entry_count}")
            print(f"  - 总时长: {result.import_result.total_duration}")
            print(f"  - 文件编码: {result.import_result.encoding}")
        
        # Phase 2: 文本提取
        if result.extraction_result:
            print(f"\n🔧 Phase 2: 文本提取")
            print(f"  - 原始字符: {result.extraction_result.original_chars}")
            print(f"  - 处理后字符: {result.extraction_result.processed_chars}")
            print(f"  - 处理模式: {result.extraction_result.processing_mode}")
            print(f"  - 修正统计: {result.extraction_result.corrections}")
        
        # Phase 3: Hook检测
        if result.hook_detection_result:
            print(f"\n🎣 Phase 3: Hook检测")
            print(f"  - 是否有Hook: {result.hook_detection_result.has_hook}")
            if result.hook_detection_result.has_hook:
                print(f"  - Hook结束时间: {result.hook_detection_result.hook_end_time}")
                print(f"  - Body起点时间: {result.hook_detection_result.body_start_time}")
            print(f"  - 置信度: {result.hook_detection_result.confidence:.2f}")
            print(f"  - 判断理由: {result.hook_detection_result.reasoning}")
        
        # Phase 4: Hook分析
        if result.hook_analysis_result:
            print(f"\n🔍 Phase 4: Hook内容分析")
            print(f"  - 来源类型: {result.hook_analysis_result.source_type}")
            print(f"  - 相似度: {result.hook_analysis_result.similarity_score:.2f}")
            print(f"  - 建议策略: {result.hook_analysis_result.alignment_strategy}")
        
        # Phase 5: 脚本分段
        if result.segmentation_result:
            print(f"\n✂️ Phase 5: 脚本分段")
            print(f"  - 总段落数: {result.segmentation_result.total_segments}")
            print(f"  - 平均句子数: {result.segmentation_result.avg_sentence_count:.1f}")
            
            # ABC分类统计
            category_counts = {}
            for seg in result.segmentation_result.segments:
                cat = seg.category or "Unknown"
                category_counts[cat] = category_counts.get(cat, 0) + 1
            print(f"  - ABC分类分布: {category_counts}")
        
        # Phase 6: 质量验证
        if result.validation_report:
            print(f"\n✅ Phase 6: 质量验证")
            print(f"  - 质量评分: {result.validation_report.quality_score:.0f}/100")
            print(f"  - 是否通过: {result.validation_report.is_valid}")
            print(f"  - 问题数量: {len(result.validation_report.issues)}")
            print(f"  - 警告数量: {len(result.validation_report.warnings)}")
            
            # 显示前5个问题
            if result.validation_report.issues:
                print(f"\n  前5个问题:")
                for issue in result.validation_report.issues[:5]:
                    print(f"    - [{issue.severity}] {issue.description}")
            
            # 显示建议
            if result.validation_report.recommendations:
                print(f"\n  改进建议:")
                for rec in result.validation_report.recommendations[:3]:
                    print(f"    - {rec}")
        
        # 错误信息
        if result.errors:
            print(f"\n❌ 错误列表:")
            for error in result.errors:
                print(f"  - [{error.step}] {error.error_type}: {error.error_message}")
        
        print("\n" + "=" * 80)
        print("测试完成!")
        print("=" * 80)
        
        return result
    
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_minimal_config():
    """
    测试最小配置（不启用Hook检测和分析）
    """
    print("\n" + "=" * 80)
    print("测试最小配置（不启用Hook检测）")
    print("=" * 80)
    
    project_name = "天命桃花_test_minimal"
    episode_name = "ep02"  # 非ep01
    srt_path = "data/projects/天命桃花_test/raw/ep02.srt"
    
    if not os.path.exists(srt_path):
        print(f"❌ SRT文件不存在: {srt_path}")
        print("跳过最小配置测试")
        return
    
    # 最小配置
    config = ScriptProcessingConfig(
        enable_hook_detection=False,  # 禁用Hook检测
        enable_hook_analysis=False,  # 禁用Hook分析
        enable_abc_classification=True,
        min_quality_score=70  # 更宽松的质量要求
    )
    
    workflow = ScriptProcessingWorkflow()
    
    result = await workflow.run(
        srt_path=srt_path,
        project_name=project_name,
        episode_name=episode_name,
        config=config
    )
    
    print(f"\n结果: {'成功' if result.success else '失败'}")
    print(f"总耗时: {result.processing_time:.1f} 秒")
    print(f"总成本: ${result.total_cost:.4f} USD")
    
    return result


async def main():
    """
    主测试函数
    """
    print("\n" + "=" * 80)
    print("ScriptProcessingWorkflow 工作流测试套件")
    print("=" * 80)
    
    # 测试1: 完整流程（包含Hook检测）
    print("\n[测试1] 完整流程测试（ep01）")
    result1 = await test_script_processing_workflow()
    
    # 测试2: 最小配置（不包含Hook检测）
    print("\n[测试2] 最小配置测试（ep02）")
    result2 = await test_minimal_config()
    
    print("\n" + "=" * 80)
    print("所有测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
