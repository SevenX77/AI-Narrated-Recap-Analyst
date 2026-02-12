"""
NovelProcessingWorkflow 最小测试
仅处理1章，快速定位问题
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
from src.core.schemas_novel import NovelProcessingConfig


async def mini_test():
    """最小测试：只处理第1章"""
    print("=" * 80)
    print("🧪 NovelProcessingWorkflow 最小测试（1章）")
    print("=" * 80)
    
    novel_path = "分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    project_name = "末哥超凡公路_mini_test"
    
    if not Path(novel_path).exists():
        print(f"❌ 文件不存在: {novel_path}")
        return
    
    config = NovelProcessingConfig(
        enable_parallel=False,  # 串行处理，便于调试
        chapter_range=(1, 1),   # 只处理第1章
        enable_functional_tags=False,
        enable_system_analysis=False,  # 暂时关闭系统分析
        output_markdown_reports=True  # 启用新的质量报告
    )
    
    print(f"\n📋 配置: 章节范围=(1, 1), 串行处理")
    print()
    
    workflow = NovelProcessingWorkflow()
    
    try:
        result = await workflow.run(
            novel_path=novel_path,
            project_name=project_name,
            config=config
        )
        
        print("\n" + "=" * 80)
        print("✅ 测试成功！")
        print("=" * 80)
        print(f"\n完成步骤: {result.completed_steps}")
        print(f"耗时: {result.processing_time:.1f}秒")
        print(f"LLM调用: {result.llm_calls_count}次")
        
        if result.segmentation_results:
            seg = result.segmentation_results.get(1)
            if seg:
                print(f"\n章节1分段结果:")
                print(f"  - 段落数: {len(seg.paragraphs) if hasattr(seg, 'paragraphs') else 'N/A'}")
        
        if result.annotation_results:
            ann = result.annotation_results.get(1)
            if ann:
                print(f"\n章节1标注结果:")
                print(f"  - 事件数: {len(ann.event_timeline.events)}")
                print(f"  - 设定数: {len(ann.setting_library.settings)}")
        
        print(f"\n📁 报告目录: {result.intermediate_results_dir}/reports/")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(mini_test())
