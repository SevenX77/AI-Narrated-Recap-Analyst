"""
测试重试机制和API限流控制
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
from src.core.schemas_novel import NovelProcessingConfig


async def test_retry_with_low_concurrency():
    """测试重试机制：降低并发，增加重试"""
    print("=" * 80)
    print("🧪 测试：重试机制 + API限流控制")
    print("=" * 80)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    novel_path = "分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    project_name = "末哥超凡公路_retry_test"
    
    if not Path(novel_path).exists():
        print(f"❌ 文件不存在: {novel_path}")
        return
    
    # 优化配置：降低并发+启用重试
    config = NovelProcessingConfig(
        enable_parallel=True,
        max_concurrent_chapters=1,  # 降至1，避免并发触发限流
        chapter_range=(1, 5),  # 只处理前5章
        enable_functional_tags=False,
        enable_system_analysis=False,
        output_markdown_reports=True,
        continue_on_error=True,
        
        # 重试配置
        retry_on_error=True,  # 启用重试
        max_retries=3,  # 最多重试3次
        retry_delay=3.0,  # 基础延迟3秒
        request_delay=2.0  # 请求间延迟2秒
    )
    
    print(f"📋 配置:")
    print(f"   - 章节范围: 1-5章")
    print(f"   - 并发模式: 启用 (并发数=1，串行化)")
    print(f"   - 重试机制: 启用 (最多3次，基础延迟3秒)")
    print(f"   - 请求延迟: 2秒")
    print(f"   - API限流检测: 启用")
    print()
    
    workflow = NovelProcessingWorkflow()
    
    try:
        result = await workflow.run(
            novel_path=novel_path,
            project_name=project_name,
            config=config
        )
        
        print("\n" + "=" * 80)
        print("✅ 测试完成！")
        print("=" * 80)
        
        print(f"\n📊 处理统计:")
        print(f"   - 完成步骤: {result.completed_steps}")
        print(f"   - 处理时间: {result.processing_time:.1f}秒")
        print(f"   - LLM调用: {result.llm_calls_count}次")
        
        if result.segmentation_results:
            print(f"\n✂️ 分段结果:")
            print(f"   - 成功分段: {len(result.segmentation_results)}章")
        
        if result.annotation_results:
            print(f"\n📝 标注结果:")
            print(f"   - 成功标注: {len(result.annotation_results)}章")
        
        if result.errors:
            print(f"\n⚠️ 错误记录: {len(result.errors)}个")
            for err in result.errors[:3]:  # 只显示前3个
                print(f"   - 章节{err.chapter_number}: {err.error_type}")
        
        print(f"\n📁 生成文件:")
        print(f"   - Markdown: data/projects/{project_name}/novel/")
        print(f"   - HTML可视化: data/projects/{project_name}/visualization/")
        print(f"   - 质量报告: data/projects/{project_name}/processing/reports/")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    start = datetime.now()
    result = asyncio.run(test_retry_with_low_concurrency())
    end = datetime.now()
    
    print(f"\n⏰ 结束时间: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ 总耗时: {(end-start).total_seconds():.1f}秒")
    
    exit(0 if result else 1)
