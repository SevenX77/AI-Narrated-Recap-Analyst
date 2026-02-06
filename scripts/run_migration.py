"""
Run Migration Script
执行项目迁移
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflows.migration_workflow import ProjectMigrationWorkflow


async def main():
    """执行迁移"""
    import sys
    
    print("\n" + "="*60)
    print("🚀 开始项目迁移")
    print("="*60)
    print()
    
    # 检查命令行参数或后台运行
    if len(sys.argv) > 1 and sys.argv[1] == '--use-llm':
        use_llm = True
        print("✅ 使用 LLM 辅助分段（命令行参数）")
    else:
        try:
            # 询问是否使用 LLM
            use_llm_input = input("是否使用 LLM 辅助分段? (y/n，默认 n): ").strip().lower()
            use_llm = use_llm_input == 'y'
        except EOFError:
            # 后台运行时默认使用LLM
            use_llm = True
            print("✅ 使用 LLM 辅助分段（后台自动模式）")
    
    if use_llm:
        print("✓ 将使用 LLM 辅助优化分段")
    else:
        print("✓ 仅使用规则引擎进行分段")
    
    print()
    
    # 创建工作流
    workflow = ProjectMigrationWorkflow(use_llm=use_llm, dry_run=False)
    
    try:
        # 执行迁移
        report = await workflow.run()
        
        # 打印摘要
        print("\n" + "="*60)
        print("📊 迁移完成摘要")
        print("="*60)
        print(f"✅ 项目迁移数量: {report['projects_migrated']}")
        print(f"📖 小说文件处理: {report['files_processed']['novels']}")
        print(f"📝 字幕文件复制: {report['files_processed']['srt_files']}")
        print(f"💾 总数据大小: {report['files_processed']['total_size_mb']:.2f} MB")
        
        if report.get("novel_processing"):
            print("\n📚 小说分段处理详情:")
            for project_name, stats in report["novel_processing"].items():
                print(f"\n  {project_name}:")
                print(f"    - 原始行数: {stats['original_lines']}")
                print(f"    - 生成段落: {stats['total_paragraphs']}")
                print(f"    - 平均段长: {stats['avg_paragraph_length']:.1f} 句")
                print(f"    - 规则处理: {stats['rule_processed']}")
                if use_llm:
                    print(f"    - LLM 优化: {stats['llm_refined']}")
        
        if report["errors"]:
            print(f"\n⚠️  错误数量: {len(report['errors'])}")
            for error in report["errors"]:
                print(f"  - {error}")
        else:
            print("\n✅ 迁移过程无错误")
        
        print("\n" + "="*60)
        print("✨ 迁移完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
