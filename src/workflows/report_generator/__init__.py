"""
Report Generator - 小说处理工作流的报告生成模块

从 NovelProcessingWorkflow 中提取的报告生成功能，包括：
- 步骤报告生成 (Steps 1-8)
- Markdown 文件生成
- HTML 可视化生成

这些功能作为独立函数提供，由主工作流调用。

Author: AI-Narrated Recap Analyst Team
Created: 2026-02-10
Refactored: 2026-02-13 (拆分为独立模块)
"""

# 导出所有报告生成函数
from .step_reports import (
    output_step1_report,
    output_step2_report,
    output_step3_report,
    output_step4_report,
    output_step5_report,
    output_step67_report,
    output_step8_report
)

from .markdown_generator import (
    generate_metadata_markdown,
    generate_chapters_index_markdown,
    generate_chapter_markdown
)

from .html_renderer import (
    generate_comprehensive_html,
    render_segmentation_html,
    render_annotation_html,
    render_system_html,
    render_quality_html
)

__all__ = [
    # Step Reports
    "output_step1_report",
    "output_step2_report",
    "output_step3_report",
    "output_step4_report",
    "output_step5_report",
    "output_step67_report",
    "output_step8_report",
    # Markdown Generators
    "generate_metadata_markdown",
    "generate_chapters_index_markdown",
    "generate_chapter_markdown",
    # HTML Renderers
    "generate_comprehensive_html",
    "render_segmentation_html",
    "render_annotation_html",
    "render_system_html",
    "render_quality_html",
]
