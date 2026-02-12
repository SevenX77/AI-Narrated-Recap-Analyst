"""
测试 NovelProcessingWorkflow

测试小说处理工作流的完整流程，使用末哥超凡公路项目。

Usage:
    python scripts/test/test_novel_processing_workflow.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
from src.core.schemas_novel import NovelProcessingConfig


async def test_novel_processing_workflow():
    """
    测试 NovelProcessingWorkflow 完整流程
    
    测试配置:
    - 项目: 末哥超凡公路_test
    - 章节范围: 1-10
    - 并行处理: 开启（并发数3）
    - 功能性标签: 关闭（节省成本）
    - 系统分析: 开启
    """
    print("=" * 80)
    print("🧪 测试 NovelProcessingWorkflow")
    print("=" * 80)
    
    # 配置参数
    novel_path = "分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    project_name = "末哥超凡公路_test"
    
    # 检查文件是否存在
    if not Path(novel_path).exists():
        print(f"❌ 小说文件不存在: {novel_path}")
        return
    
    # 创建 Workflow 配置
    config = NovelProcessingConfig(
        enable_parallel=True,
        max_concurrent_chapters=3,
        enable_functional_tags=False,  # 关闭功能性标签，节省时间和成本
        enable_system_analysis=True,
        chapter_range=(1, 10),  # 处理前10章
        continue_on_error=True,
        save_intermediate_results=True,
        segmentation_provider="claude",
        annotation_provider="claude",
        output_markdown_reports=True  # 输出Markdown报告
    )
    
    print(f"\n📋 测试配置:")
    print(f"   - 小说路径: {novel_path}")
    print(f"   - 项目名称: {project_name}")
    print(f"   - 章节范围: {config.chapter_range}")
    print(f"   - 并行处理: {config.enable_parallel}")
    print(f"   - 并发数: {config.max_concurrent_chapters}")
    print(f"   - 功能性标签: {config.enable_functional_tags}")
    print(f"   - 系统分析: {config.enable_system_analysis}")
    print(f"   - Markdown报告: {config.output_markdown_reports}")
    print()
    
    # 创建 Workflow 实例
    workflow = NovelProcessingWorkflow()
    
    try:
        # 执行 Workflow
        result = await workflow.run(
            novel_path=novel_path,
            project_name=project_name,
            config=config
        )
        
        # 输出结果摘要
        print("\n" + "=" * 80)
        print("📊 执行结果摘要")
        print("=" * 80)
        
        print(f"\n✅ 完成步骤: {result.completed_steps}")
        print(f"\n📈 处理统计:")
        print(f"   - 总章节数: {result.processing_stats['total_chapters']}")
        print(f"   - 成功处理: {result.processing_stats['successful_chapters']}")
        print(f"   - 失败处理: {result.processing_stats['failed_chapters']}")
        print(f"   - 总段落数: {result.processing_stats['total_paragraphs']}")
        print(f"   - 总事件数: {result.processing_stats['total_events']}")
        print(f"   - 总设定数: {result.processing_stats['total_settings']}")
        print(f"   - 平均段落/章: {result.processing_stats['avg_paragraphs_per_chapter']:.1f}")
        
        print(f"\n⏱️  性能指标:")
        print(f"   - 总耗时: {result.processing_time:.1f}秒 ({result.processing_time/60:.1f}分钟)")
        print(f"   - LLM调用: {result.llm_calls_count}次")
        print(f"   - 总成本: ${result.total_cost:.4f}")
        
        if result.validation_report:
            print(f"\n✅ 质量评分: {result.validation_report.overall_score}/100")
        
        if result.errors:
            print(f"\n⚠️  错误数量: {len(result.errors)}")
            for error in result.errors[:5]:  # 只显示前5个错误
                print(f"   - 章节{error.chapter_number} ({error.step}): {error.error_message}")
        
        print(f"\n📁 输出目录:")
        print(f"   - 中间结果: {result.intermediate_results_dir}")
        print(f"   - Markdown报告: {result.intermediate_results_dir}/reports/")
        
        print("\n" + "=" * 80)
        print("✅ 测试完成！")
        print("=" * 80)
        
        # 列出生成的 Markdown 报告
        reports_dir = Path(result.intermediate_results_dir) / "reports"
        if reports_dir.exists():
            print("\n📄 生成的报告文件:")
            for report_file in sorted(reports_dir.glob("*.md")):
                print(f"   - {report_file.name}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_partial_workflow():
    """
    测试部分流程执行（仅前3步）
    
    用于快速验证前端流程是否正常。
    """
    print("=" * 80)
    print("🧪 测试 NovelProcessingWorkflow (部分流程)")
    print("=" * 80)
    
    novel_path = "分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    project_name = "末哥超凡公路_test_partial"
    
    if not Path(novel_path).exists():
        print(f"❌ 小说文件不存在: {novel_path}")
        return
    
    config = NovelProcessingConfig(
        enable_parallel=False,  # 前3步无需并行
        chapter_range=(1, 3),  # 只处理3章
        enable_system_analysis=False,
        output_markdown_reports=True
    )
    
    print(f"\n📋 测试配置:")
    print(f"   - 章节范围: {config.chapter_range}")
    print(f"   - 系统分析: {config.enable_system_analysis}")
    print()
    
    workflow = NovelProcessingWorkflow()
    
    try:
        # 只执行前3步
        result = await workflow.run(
            novel_path=novel_path,
            project_name=project_name,
            config=config
        )
        
        print("\n" + "=" * 80)
        print("✅ 部分流程测试完成！")
        print(f"完成步骤: {result.completed_steps}")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 NovelProcessingWorkflow")
    parser.add_argument(
        "--mode",
        choices=["full", "partial"],
        default="full",
        help="测试模式: full=完整流程, partial=部分流程（前3步）"
    )
    
    args = parser.parse_args()
    
    if args.mode == "full":
        asyncio.run(test_novel_processing_workflow())
    else:
        asyncio.run(test_partial_workflow())


if __name__ == "__main__":
    main()
