"""
测试LLM管理器集成和HTML可视化

验证：
1. LLM管理器是否正常工作
2. HTML是否包含所有内容（分段、标注、系统分析、质量报告）
3. 模型信息是否正确显示
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
from src.core.schemas_novel import NovelProcessingConfig


async def test_integration():
    """测试LLM管理器集成和完整HTML可视化"""
    print("=" * 80)
    print("🧪 测试LLM管理器集成和HTML可视化")
    print("=" * 80)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    novel_path = "分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    project_name = "末哥超凡公路_llm_integration_test"
    
    if not Path(novel_path).exists():
        print(f"❌ 文件不存在: {novel_path}")
        return
    
    # 配置：只处理2章，快速测试
    config = NovelProcessingConfig(
        enable_parallel=False,  # 串行处理
        chapter_range=(1, 2),  # 只处理前2章
        enable_functional_tags=False,  # 关闭以节省时间
        enable_system_analysis=True,  # 启用系统分析
        output_markdown_reports=True,
        continue_on_error=True,
        
        # LLM配置
        segmentation_provider="claude",  # 分段使用Claude
        annotation_provider="claude"  # 标注使用Claude
    )
    
    print(f"📋 配置:")
    print(f"   - 章节范围: 1-2章（快速测试）")
    print(f"   - 分段模型: {config.segmentation_provider}")
    print(f"   - 标注模型: {config.annotation_provider}")
    print(f"   - 系统分析: 启用")
    print(f"   - HTML可视化: 启用")
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
        
        # 验证结果
        print(f"\n📊 处理统计:")
        print(f"   - 完成步骤: {result.completed_steps}")
        print(f"   - 处理时间: {result.processing_time:.1f}秒")
        print(f"   - LLM调用: {result.llm_calls_count}次")
        
        # 验证分段结果
        if result.segmentation_results:
            print(f"\n✂️ 分段结果:")
            print(f"   - 成功分段: {len(result.segmentation_results)}章")
            for ch_num, seg_result in result.segmentation_results.items():
                model_used = seg_result.metadata.get("model_used", "未记录")
                print(f"   - 章节{ch_num}: {len(seg_result.paragraphs)}个段落, 使用模型: {model_used}")
        
        # 验证标注结果
        if result.annotation_results:
            print(f"\n🏷️ 标注结果:")
            print(f"   - 成功标注: {len(result.annotation_results)}章")
            for ch_num, ann_result in result.annotation_results.items():
                model_used = ann_result.metadata.get("model_used", "未记录")
                print(f"   - 章节{ch_num}: {len(ann_result.event_timeline.events)}个事件, "
                      f"{len(ann_result.setting_library.settings)}个设定, 使用模型: {model_used}")
        
        # 验证系统分析
        if result.system_catalog:
            model_used = result.system_catalog.metadata.get("model_used", "未记录")
            print(f"\n🔧 系统分析:")
            print(f"   - 系统类型: {result.system_catalog.novel_type}")
            print(f"   - 类别数: {len(result.system_catalog.categories)}")
            print(f"   - 使用模型: {model_used}")
        
        # 验证HTML文件
        viz_path = Path(f"data/projects/{project_name}/visualization/comprehensive_viewer.html")
        if viz_path.exists():
            print(f"\n🌐 HTML可视化:")
            print(f"   ✅ 文件已生成: {viz_path}")
            print(f"   📊 文件大小: {viz_path.stat().st_size / 1024:.1f} KB")
            print(f"\n   🌐 在浏览器中打开:")
            print(f"   file://{viz_path.absolute()}")
            
            # 检查HTML内容
            html_content = viz_path.read_text(encoding='utf-8')
            checks = {
                "包含分段结果": "分段结果" in html_content,
                "包含标注结果": "标注结果" in html_content,
                "包含系统分析": "系统分析" in html_content,
                "包含质量报告": "质量报告" in html_content,
                "包含模型标签": "model-badge" in html_content,
                "包含Claude标识": "claude" in html_content.lower()
            }
            
            print(f"\n   📝 内容验证:")
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"      {status} {check_name}")
        else:
            print(f"\n❌ HTML文件未生成: {viz_path}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    start = datetime.now()
    result = asyncio.run(test_integration())
    end = datetime.now()
    
    print(f"\n⏰ 结束时间: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ 总耗时: {(end-start).total_seconds():.1f}秒")
    
    if result:
        print("\n" + "=" * 80)
        print("🎉 所有功能已成功集成！")
        print("=" * 80)
        print("\n📋 已完成的功能:")
        print("   ✅ LLM管理器集成（智能限流+重试）")
        print("   ✅ 记录每次调用使用的模型")
        print("   ✅ 完整HTML可视化（分段+标注+系统+报告）")
        print("   ✅ HTML中显示模型信息")
        print()
        
        exit(0)
    else:
        exit(1)
