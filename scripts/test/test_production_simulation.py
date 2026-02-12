"""
生产环境模拟测试
完整处理末哥超凡公路前10章
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
from src.core.schemas_novel import NovelProcessingConfig


async def production_simulation():
    """生产环境模拟：完整处理前10章"""
    print("=" * 80)
    print("🏭 生产环境模拟 - NovelProcessingWorkflow")
    print("=" * 80)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    novel_path = "分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    project_name = "末哥超凡公路_production_10ch"
    
    if not Path(novel_path).exists():
        print(f"❌ 文件不存在: {novel_path}")
        return
    
    # 完整配置
    config = NovelProcessingConfig(
        enable_parallel=True,  # 启用并行处理
        max_concurrent_chapters=3,  # 3章并发
        chapter_range=(1, 10),  # 处理前10章
        enable_functional_tags=False,  # 暂时关闭功能标签（节省时间）
        enable_system_analysis=True,  # 启用系统分析
        output_markdown_reports=True,  # 启用所有报告
        continue_on_error=True  # 遇到错误继续处理
    )
    
    print(f"📋 配置:")
    print(f"   - 章节范围: 1-10章")
    print(f"   - 并行模式: 启用 (最大{config.max_concurrent_chapters}章并发)")
    print(f"   - 系统分析: 启用")
    print(f"   - Markdown报告: 启用")
    print(f"   - HTML可视化: 启用")
    print(f"   - 遇错继续: 启用")
    print()
    
    workflow = NovelProcessingWorkflow()
    
    try:
        result = await workflow.run(
            novel_path=novel_path,
            project_name=project_name,
            config=config
        )
        
        print("\n" + "=" * 80)
        print("✅ 生产模拟完成！")
        print("=" * 80)
        
        # 详细统计
        print(f"\n📊 处理统计:")
        print(f"   - 完成步骤: {result.completed_steps}")
        print(f"   - 处理时间: {result.processing_time:.1f}秒 ({result.processing_time/60:.1f}分钟)")
        print(f"   - LLM调用: {result.llm_calls_count}次")
        print(f"   - 总成本: ${result.total_cost:.4f}" if result.total_cost else "   - 总成本: 未计算")
        
        # 章节统计
        if result.chapters:
            print(f"\n📚 章节处理:")
            print(f"   - 检测到: {len(result.chapters)}章")
        
        # 分段统计
        if result.segmentation_results:
            print(f"\n✂️ 分段结果:")
            print(f"   - 成功分段: {len(result.segmentation_results)}章")
            total_paras = sum(len(seg.paragraphs) for seg in result.segmentation_results.values())
            print(f"   - 总段落数: {total_paras}")
            
            # ABC分布
            a_count = sum(sum(1 for p in seg.paragraphs if p.type == "A") for seg in result.segmentation_results.values())
            b_count = sum(sum(1 for p in seg.paragraphs if p.type == "B") for seg in result.segmentation_results.values())
            c_count = sum(sum(1 for p in seg.paragraphs if p.type == "C") for seg in result.segmentation_results.values())
            print(f"   - A类: {a_count} ({a_count/total_paras*100:.1f}%)")
            print(f"   - B类: {b_count} ({b_count/total_paras*100:.1f}%)")
            print(f"   - C类: {c_count} ({c_count/total_paras*100:.1f}%)")
        
        # 标注统计
        if result.annotation_results:
            print(f"\n📝 标注结果:")
            print(f"   - 成功标注: {len(result.annotation_results)}章")
            total_events = sum(len(ann.event_timeline.events) for ann in result.annotation_results.values())
            total_settings = sum(len(ann.setting_library.settings) for ann in result.annotation_results.values())
            print(f"   - 总事件数: {total_events}")
            print(f"   - 总设定数: {total_settings}")
        
        # 系统分析
        if result.system_catalog:
            print(f"\n🔧 系统分析:")
            print(f"   - 系统类型: {result.system_catalog.system_type}")
            print(f"   - 识别元素: {len(result.system_catalog.elements)}个")
        
        # 质量评估
        if result.validation_report:
            print(f"\n⭐ 质量评分:")
            print(f"   - 总体评分: {result.validation_report.quality_score}/100")
            if hasattr(result.validation_report, 'issues') and result.validation_report.issues:
                print(f"   - 发现问题: {len(result.validation_report.issues)}个")
        
        # 错误统计
        if result.errors:
            print(f"\n⚠️ 错误记录:")
            for err in result.errors:
                print(f"   - 章节{err.chapter_number}: {err.error_type} - {err.error_message[:50]}...")
        
        # 生成文件路径
        print(f"\n📁 生成文件:")
        print(f"   - 结构化数据: data/projects/{project_name}/processing/structured/")
        print(f"   - 可读Markdown: data/projects/{project_name}/novel/")
        print(f"   - HTML可视化: data/projects/{project_name}/visualization/")
        print(f"   - 质量报告: data/projects/{project_name}/processing/reports/")
        print(f"   - 最终结果: data/projects/{project_name}/processing/final_result.json")
        
        # 快速查看链接
        viz_path = Path(f"data/projects/{project_name}/visualization/segmentation_viewer.html")
        if viz_path.exists():
            print(f"\n🌐 在浏览器中打开查看:")
            print(f"   file://{viz_path.absolute()}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 生产模拟失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    start = datetime.now()
    result = asyncio.run(production_simulation())
    end = datetime.now()
    
    print(f"\n⏰ 结束时间: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ 总耗时: {(end-start).total_seconds():.1f}秒 ({(end-start).total_seconds()/60:.1f}分钟)")
    
    exit(0 if result else 1)
