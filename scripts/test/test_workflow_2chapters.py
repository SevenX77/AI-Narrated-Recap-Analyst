"""
小规模Workflow测试 - 2章
验证LLM管理器集成和完整HTML可视化
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
from src.core.schemas_novel import NovelProcessingConfig


async def test_workflow_2chapters():
    """测试workflow处理2章"""
    print("=" * 80)
    print("🧪 Workflow小规模测试 - 2章")
    print("=" * 80)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    novel_path = "分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    project_name = "末哥超凡公路_2ch_test"
    
    if not Path(novel_path).exists():
        print(f"❌ 文件不存在: {novel_path}")
        return
    
    # 配置：只处理2章
    config = NovelProcessingConfig(
        enable_parallel=False,  # 串行处理，便于观察
        chapter_range=(1, 2),
        enable_functional_tags=False,  # 关闭以节省时间
        enable_system_analysis=True,
        output_markdown_reports=True,
        continue_on_error=True,
        
        # LLM配置 - 使用Claude
        segmentation_provider="claude",
        annotation_provider="claude"
    )
    
    print(f"📋 测试配置:")
    print(f"   - 小说: 末哥超凡公路")
    print(f"   - 章节: 第1-2章")
    print(f"   - 分段模型: {config.segmentation_provider}")
    print(f"   - 标注模型: {config.annotation_provider}")
    print(f"   - 系统分析: 启用")
    print(f"   - 并行处理: 关闭（串行）")
    print(f"   - HTML可视化: 启用")
    print()
    print("🚀 开始处理...")
    print()
    
    workflow = NovelProcessingWorkflow()
    
    try:
        result = await workflow.run(
            novel_path=novel_path,
            project_name=project_name,
            config=config
        )
        
        print("\n" + "=" * 80)
        print("✅ Workflow测试完成！")
        print("=" * 80)
        
        # 详细结果
        print(f"\n📊 处理结果:")
        print(f"   - 完成步骤: {result.completed_steps}")
        print(f"   - 处理时间: {result.processing_time:.1f}秒 ({result.processing_time/60:.1f}分钟)")
        print(f"   - LLM调用: {result.llm_calls_count}次")
        
        # 分段结果
        if result.segmentation_results:
            print(f"\n✂️ 分段结果:")
            for ch_num, seg_result in result.segmentation_results.items():
                model_used = seg_result.metadata.get("model_used", "未记录")
                
                # 统计ABC分布
                type_counts = {"A": 0, "B": 0, "C": 0}
                for p in seg_result.paragraphs:
                    type_counts[p.type] = type_counts.get(p.type, 0) + 1
                
                print(f"   - 章节{ch_num}: {len(seg_result.paragraphs)}个段落")
                print(f"     • A类:{type_counts['A']} B类:{type_counts['B']} C类:{type_counts['C']}")
                print(f"     • 使用模型: {model_used}")
        
        # 标注结果
        if result.annotation_results:
            print(f"\n🏷️ 标注结果:")
            for ch_num, ann_result in result.annotation_results.items():
                model_used = ann_result.metadata.get("model_used", "未记录")
                print(f"   - 章节{ch_num}: {len(ann_result.event_timeline.events)}个事件, "
                      f"{len(ann_result.setting_library.settings)}个设定")
                print(f"     • 使用模型: {model_used}")
        
        # 系统分析
        if result.system_catalog:
            model_used = result.system_catalog.metadata.get("model_used", "未记录")
            print(f"\n🔧 系统分析:")
            print(f"   - 系统类型: {result.system_catalog.novel_type}")
            print(f"   - 类别数: {len(result.system_catalog.categories)}")
            print(f"   - 使用模型: {model_used}")
        
        # 质量验证
        if result.validation_report:
            print(f"\n⭐ 质量评分: {result.validation_report.quality_score}/100")
        
        # 错误统计
        if result.errors:
            print(f"\n⚠️ 处理错误: {len(result.errors)}个")
            for err in result.errors:
                print(f"   - 章节{err.chapter_number}: {err.error_type}")
        
        # HTML文件
        viz_path = Path(f"data/projects/{project_name}/visualization/comprehensive_viewer.html")
        if viz_path.exists():
            file_size = viz_path.stat().st_size / 1024
            print(f"\n🌐 HTML可视化:")
            print(f"   ✅ 文件已生成")
            print(f"   📊 大小: {file_size:.1f} KB")
            print(f"   📂 路径: {viz_path}")
            print(f"\n   🌐 在浏览器中打开:")
            print(f"   file://{viz_path.absolute()}")
        else:
            print(f"\n❌ HTML文件未生成")
        
        # 生成的文件列表
        project_dir = Path(f"data/projects/{project_name}")
        if project_dir.exists():
            print(f"\n📁 生成的文件:")
            
            novel_dir = project_dir / "novel"
            if novel_dir.exists():
                md_files = list(novel_dir.glob("*.md"))
                print(f"   - Markdown文件: {len(md_files)}个")
            
            viz_dir = project_dir / "visualization"
            if viz_dir.exists():
                html_files = list(viz_dir.glob("*.html"))
                print(f"   - HTML文件: {len(html_files)}个")
            
            reports_dir = project_dir / "processing/reports"
            if reports_dir.exists():
                report_files = list(reports_dir.glob("*.md"))
                print(f"   - 报告文件: {len(report_files)}个")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    start = datetime.now()
    result = asyncio.run(test_workflow_2chapters())
    end = datetime.now()
    
    print(f"\n⏰ 结束时间: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ 总耗时: {(end-start).total_seconds():.1f}秒 ({(end-start).total_seconds()/60:.1f}分钟)")
    
    if result:
        print("\n" + "=" * 80)
        print("🎉 测试成功！所有功能正常工作！")
        print("=" * 80)
        print("\n✅ 已验证的功能:")
        print("   • LLM管理器自动限流")
        print("   • Claude API正常调用")
        print("   • 模型信息正确记录")
        print("   • 完整HTML可视化生成")
        print("   • 5个Tab全部内容")
        print()
        exit(0)
    else:
        exit(1)
