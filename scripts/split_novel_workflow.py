"""
自动拆分 novel_processing_workflow.py 的脚本

将 1828 行的工作流拆分成 4 个功能模块（使用 Mixin 模式）
"""
import re
from pathlib import Path
import os

os.chdir('/Users/sevenx/Documents/coding/AI-Narrated Recap Analyst')

# 读取原文件
src_file = Path('src/workflows/novel_processing_workflow.py')
with open(src_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取 imports 和 docstring
imports_match = re.search(r'^(""".*?"""\n\n)(.*?)(class NovelProcessingWorkflow)', content, re.DOTALL)
file_docstring = imports_match.group(1)
imports_block = imports_match.group(2)

# 提取类定义
class_match = re.search(r'(class NovelProcessingWorkflow.*?)(?=\n\n# |$)', content, re.DOTALL)
class_content = class_match.group(1)

# 提取所有方法
method_pattern = r'(    (?:async )?def \w+.*?)(?=\n    (?:async )?def |\n\nclass |\Z)'
methods = {}
for match in re.finditer(method_pattern, class_content, re.DOTALL):
    method_text = match.group(1)
    method_name_match = re.search(r'def (\w+)\(', method_text)
    if method_name_match:
        method_name = method_name_match.group(1)
        methods[method_name] = method_text

print(f"📊 提取了 {len(methods)} 个方法")

# 方法分组
groups = {
    'base_workflow.py': {
        'description': '基础工作流类和辅助方法',
        'methods': [
            '__init__',
            '_estimate_tokens',
            '_setup_processing_directory',
            '_save_intermediate_result',
            '_save_final_result',
            '_calculate_stats'
        ]
    },
    'core_steps.py': {
        'description': '核心处理步骤（Steps 1-8 + run）',
        'methods': [
            'run',
            '_step1_import_novel',
            '_step2_extract_metadata',
            '_step3_detect_chapters',
            '_step4_segment_chapters',
            '_step5_annotate_chapters',
            '_step6_analyze_system',
            '_step7_track_system',
            '_step8_validate_quality'
        ]
    },
    'processing_helpers.py': {
        'description': '批处理和单项处理辅助方法',
        'methods': [
            '_process_segmentation_batch',
            '_segment_single_chapter',
            '_process_annotation_batch',
            '_annotate_single_chapter',
            '_process_system_tracking_batch',
            '_track_single_chapter_system'
        ]
    },
    'report_generators.py': {
        'description': '报告和可视化生成方法',
        'methods': [
            '_output_step1_report',
            '_output_step2_report',
            '_output_step3_report',
            '_output_step4_report',
            '_output_step5_report',
            '_output_step67_report',
            '_output_step8_report',
            '_generate_metadata_markdown',
            '_generate_chapters_index_markdown',
            '_generate_chapter_markdown',
            '_generate_comprehensive_html',
            '_render_segmentation_html',
            '_render_annotation_html',
            '_render_system_html',
            '_render_quality_html'
        ]
    }
}

# 创建输出目录
output_dir = Path('src/workflows/novel_processing')
output_dir.mkdir(exist_ok=True)

# 提取类docstring和属性
class_header = '''class NovelProcessingWorkflow(BaseWorkflow):
    """
    小说处理工作流
    
    完整的小说处理pipeline，支持并行处理、错误恢复和断点续传。
    
    Attributes:
        name (str): 工作流名称
        config (NovelProcessingConfig): 工作流配置
        project_name (str): 项目名称
        processing_dir (str): 中间结果保存目录
    
    Example:
        ```python
        workflow = NovelProcessingWorkflow()
        result = await workflow.run(
            novel_path="path/to/novel.txt",
            project_name="末哥超凡公路_test",
            config=NovelProcessingConfig(
                chapter_range=(1, 10),
                enable_parallel=True
            )
        )
        ```
    """
    
    name: str = "novel_processing_workflow"
'''

# 生成 Mixin 类
for filename, group_info in groups.items():
    if filename == 'base_workflow.py':
        # 基础工作流包含主类定义
        file_content = f'''{file_docstring}{imports_block}

# Configure logging
logger = logging.getLogger(__name__)


{class_header}
'''
        # 添加方法
        for method_name in group_info['methods']:
            if method_name in methods:
                file_content += '\n' + methods[method_name] + '\n'
        
    else:
        # Mixin 类（方法集合）
        mixin_name = filename.replace('.py', '').replace('_', ' ').title().replace(' ', '')
        file_content = f'''"""
Novel Processing Workflow - {group_info['description']}

这是 NovelProcessingWorkflow 的 Mixin 类，包含{group_info['description']}。
"""


class {mixin_name}:
    """
    {group_info['description']} Mixin
    
    包含以下方法：
'''
        for method_name in group_info['methods']:
            file_content += f'    - {method_name}\n'
        
        file_content += '    """\n'
        
        # 添加方法
        for method_name in group_info['methods']:
            if method_name in methods:
                file_content += '\n' + methods[method_name] + '\n'
    
    # 写入文件
    file_path = output_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(file_content)
    
    lines = file_content.count('\n')
    print(f"✅ 创建: {filename} ({len(group_info['methods'])} 个方法, ~{lines} 行)")

# 生成 __init__.py（整合所有 Mixin）
init_content = f'''{file_docstring}{imports_block}

# 导入 Mixin 类
from .processing_helpers import ProcessingHelpers
from .report_generators import ReportGenerators
from .core_steps import CoreSteps

# Configure logging
logger = logging.getLogger(__name__)


{class_header}
'''

# 添加 __init__ 方法
if '__init__' in methods:
    init_content += '\n' + methods['__init__'] + '\n'

# 添加辅助方法
for method_name in ['_estimate_tokens', '_setup_processing_directory', '_save_intermediate_result', '_save_final_result', '_calculate_stats']:
    if method_name in methods:
        init_content += '\n' + methods[method_name] + '\n'

# 添加 Mixin 继承说明注释
init_content += '''

# 继承所有 Mixin 方法
# 通过多重继承实现功能模块化：
# - CoreSteps: 核心处理步骤
# - ProcessingHelpers: 批处理辅助方法
# - ReportGenerators: 报告生成方法

# 动态混入方法
for mixin in [CoreSteps, ProcessingHelpers, ReportGenerators]:
    for attr_name in dir(mixin):
        if not attr_name.startswith('_') or attr_name.startswith('_step') or attr_name.startswith('_process') or attr_name.startswith('_output') or attr_name.startswith('_generate') or attr_name.startswith('_render') or attr_name.startswith('_segment') or attr_name.startswith('_annotate') or attr_name.startswith('_track'):
            attr = getattr(mixin, attr_name)
            if callable(attr):
                setattr(NovelProcessingWorkflow, attr_name, attr)
'''

init_path = output_dir / '__init__.py'
with open(init_path, 'w', encoding='utf-8') as f:
    f.write(init_content)

print(f"✅ 创建: __init__.py (主工作流类)")

print(f"\n🎉 拆分完成！")
print(f"   原文件: {src_file} (1828 行)")
print(f"   新目录: {output_dir}/ (5 个文件)")
print(f"\n   📦 使用 Mixin 模式保持向后兼容")
