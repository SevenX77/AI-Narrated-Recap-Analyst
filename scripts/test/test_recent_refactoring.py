"""
测试最近的代码重构
- script_processing_workflow.py (移除print语句)
- report_generator 模块拆分

Created: 2026-02-13
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_script_workflow_import():
    """测试 script_processing_workflow 模块导入"""
    logger.info("\n" + "="*60)
    logger.info("测试 1: script_processing_workflow 模块导入")
    logger.info("="*60)
    
    try:
        from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
        logger.info("✅ ScriptProcessingWorkflow 导入成功")
        
        # 检查类是否有必要的方法
        required_methods = ['run', '_phase1_srt_import', '_phase2_text_extraction']
        for method in required_methods:
            if hasattr(ScriptProcessingWorkflow, method):
                logger.info(f"✅ 方法 {method} 存在")
            else:
                logger.error(f"❌ 方法 {method} 不存在")
                return False
        
        return True
    except Exception as e:
        logger.error(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generator_import():
    """测试 report_generator 模块导入"""
    logger.info("\n" + "="*60)
    logger.info("测试 2: report_generator 模块导入")
    logger.info("="*60)
    
    try:
        from src.workflows import report_generator
        logger.info("✅ report_generator 模块导入成功")
        
        # 检查导出的函数
        expected_functions = [
            # Step Reports
            'output_step1_report',
            'output_step2_report',
            'output_step3_report',
            'output_step4_report',
            'output_step5_report',
            'output_step67_report',
            'output_step8_report',
            # Markdown Generators
            'generate_metadata_markdown',
            'generate_chapters_index_markdown',
            'generate_chapter_markdown',
            # HTML Renderers
            'generate_comprehensive_html',
            'render_segmentation_html',
            'render_annotation_html',
            'render_system_html',
            'render_quality_html',
        ]
        
        missing_functions = []
        for func_name in expected_functions:
            if hasattr(report_generator, func_name):
                logger.info(f"✅ 函数 {func_name} 存在")
            else:
                logger.error(f"❌ 函数 {func_name} 不存在")
                missing_functions.append(func_name)
        
        if missing_functions:
            logger.error(f"缺失函数: {missing_functions}")
            return False
        
        logger.info(f"\n📊 总计: {len(expected_functions)} 个函数全部可用")
        return True
        
    except Exception as e:
        logger.error(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generator_submodules():
    """测试 report_generator 子模块"""
    logger.info("\n" + "="*60)
    logger.info("测试 3: report_generator 子模块")
    logger.info("="*60)
    
    try:
        # 测试子模块导入
        from src.workflows.report_generator import step_reports
        logger.info("✅ step_reports 子模块导入成功")
        
        from src.workflows.report_generator import markdown_generator
        logger.info("✅ markdown_generator 子模块导入成功")
        
        from src.workflows.report_generator import html_renderer
        logger.info("✅ html_renderer 子模块导入成功")
        
        # 检查模块的 logger
        if hasattr(step_reports, 'logger'):
            logger.info("✅ step_reports 有 logger")
        if hasattr(markdown_generator, 'logger'):
            logger.info("✅ markdown_generator 有 logger")
        if hasattr(html_renderer, 'logger'):
            logger.info("✅ html_renderer 有 logger")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 子模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_novel_workflow_integration():
    """测试 novel_processing_workflow 与 report_generator 的集成"""
    logger.info("\n" + "="*60)
    logger.info("测试 4: novel_workflow 与 report_generator 集成")
    logger.info("="*60)
    
    try:
        from src.workflows.novel_processing import NovelProcessingWorkflow
        logger.info("✅ NovelProcessingWorkflow 导入成功")
        
        # 检查 report_generator 在 novel_workflow 中的导入
        import src.workflows.novel_processing as novel_module
        source_file = Path(novel_module.__file__).parent / "__init__.py"
        
        if source_file.exists():
            content = source_file.read_text()
            if "from src.workflows import report_generator" in content:
                logger.info("✅ novel_workflow 正确导入 report_generator")
            else:
                logger.warning("⚠️ novel_workflow 可能使用了不同的导入方式")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_print_statements():
    """测试是否还有 print() 语句（排除 docstring）"""
    logger.info("\n" + "="*60)
    logger.info("测试 5: 检查 print() 语句")
    logger.info("="*60)
    
    try:
        workflow_file = Path("src/workflows/script_processing_workflow.py")
        
        if not workflow_file.exists():
            logger.error(f"❌ 文件不存在: {workflow_file}")
            return False
        
        content = workflow_file.read_text()
        lines = content.split('\n')
        
        print_found = []
        in_docstring = False
        
        for i, line in enumerate(lines, 1):
            # 跳过文档字符串
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
                continue
            
            if in_docstring:
                continue
            
            # 检查 print() 语句（排除注释和字符串）
            stripped = line.strip()
            if stripped.startswith('print(') and not stripped.startswith('#'):
                # 检查是否在字符串中
                if 'print(' in line and not line.strip().startswith('"') and not line.strip().startswith("'"):
                    print_found.append((i, line))
        
        if print_found:
            logger.error(f"❌ 发现 {len(print_found)} 个 print() 语句:")
            for line_num, line_content in print_found:
                logger.error(f"   行 {line_num}: {line_content.strip()}")
            return False
        else:
            logger.info("✅ 未发现 print() 语句")
            return True
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """测试文件结构"""
    logger.info("\n" + "="*60)
    logger.info("测试 6: 文件结构检查")
    logger.info("="*60)
    
    try:
        # 检查旧文件是否已删除
        old_file = Path("src/workflows/report_generator.py")
        if old_file.exists():
            logger.error("❌ 旧文件 report_generator.py 仍然存在")
            return False
        else:
            logger.info("✅ 旧文件 report_generator.py 已删除")
        
        # 检查新目录结构
        new_dir = Path("src/workflows/report_generator")
        if not new_dir.exists() or not new_dir.is_dir():
            logger.error("❌ 新目录 report_generator/ 不存在")
            return False
        else:
            logger.info("✅ 新目录 report_generator/ 存在")
        
        # 检查必要的文件
        required_files = [
            "__init__.py",
            "step_reports.py",
            "markdown_generator.py",
            "html_renderer.py"
        ]
        
        for filename in required_files:
            filepath = new_dir / filename
            if filepath.exists():
                file_size = filepath.stat().st_size
                line_count = len(filepath.read_text().split('\n'))
                logger.info(f"✅ {filename} 存在 ({line_count} 行, {file_size} 字节)")
                
                # 检查文件行数是否合理
                if line_count > 800:
                    logger.warning(f"⚠️ {filename} 超过800行 ({line_count}行)")
            else:
                logger.error(f"❌ {filename} 不存在")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文件结构检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    logger.info("\n" + "🧪 " + "="*58)
    logger.info("🧪   开始测试最近的代码重构")
    logger.info("🧪 " + "="*58)
    
    tests = [
        ("script_processing_workflow 导入", test_script_workflow_import),
        ("report_generator 模块导入", test_report_generator_import),
        ("report_generator 子模块", test_report_generator_submodules),
        ("novel_workflow 集成", test_novel_workflow_integration),
        ("print() 语句检查", test_no_print_statements),
        ("文件结构检查", test_file_structure),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 '{test_name}' 执行异常: {e}")
            results.append((test_name, False))
    
    # 输出总结
    logger.info("\n" + "="*60)
    logger.info("📊 测试总结")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {test_name}")
    
    logger.info("="*60)
    logger.info(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！代码重构成功！")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
