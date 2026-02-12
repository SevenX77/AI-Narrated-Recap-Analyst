"""
HTML Renderer - 小说处理工作流的HTML可视化生成

生成交互式HTML可视化页面，展示分段、标注、系统分析和质量报告。

Author: AI-Narrated Recap Analyst Team
Created: 2026-02-13 (Refactored from report_generator.py)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.core.schemas_novel import (
    ParagraphSegmentationResult,
    AnnotatedChapter,
    SystemCatalog,
    NovelValidationReport,
    ChapterProcessingError,
    NovelProcessingResult
)

logger = logging.getLogger(__name__)


def generate_comprehensive_html(
    result: NovelProcessingResult,
    project_name: str,
    novel_title: str = "未命名小说"
):
    """
    生成完整的HTML可视化文件
    
    Args:
        result: 完整的处理结果
        project_name: 项目名称
        novel_title: 小说标题
    """
    viz_dir = Path("data") / "projects" / project_name / "visualization"
    viz_dir.mkdir(parents=True, exist_ok=True)
    
    template_path = Path("templates") / "comprehensive_visualization_template.html"
    
    if not template_path.exists():
        logger.warning(f"HTML模板不存在: {template_path}，跳过可视化生成")
        return
    
    # 读取模板
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 生成分段内容HTML
    segmentation_html = render_segmentation_html(result.segmentation_results)
    
    # 生成标注内容HTML
    annotation_html = render_annotation_html(result.annotation_results)
    
    # 生成系统分析HTML
    system_html = render_system_html(result.system_catalog)
    
    # 生成质量报告HTML
    quality_html = render_quality_html(result.validation_report, result.errors)
    
    # 生成JSON内容
    json_content = json.dumps(result.dict(), ensure_ascii=False, indent=2, default=str)
    
    # 计算统计信息
    chapter_start = min(result.chapters, key=lambda c: c.number).number if result.chapters else 1
    chapter_end = max(result.chapters, key=lambda c: c.number).number if result.chapters else 1
    
    # 替换模板变量
    html_content = template.replace("{{novel_title}}", novel_title)
    html_content = html_content.replace("{{project_name}}", project_name)
    html_content = html_content.replace("{{chapter_start}}", str(chapter_start))
    html_content = html_content.replace("{{chapter_end}}", str(chapter_end))
    html_content = html_content.replace("{{processing_time}}", f"{result.processing_time:.1f}秒")
    html_content = html_content.replace("{{llm_calls}}", str(result.llm_calls_count))
    html_content = html_content.replace("{{segmentation_content}}", segmentation_html)
    html_content = html_content.replace("{{annotation_content}}", annotation_html)
    html_content = html_content.replace("{{system_content}}", system_html)
    html_content = html_content.replace("{{quality_content}}", quality_html)
    html_content = html_content.replace("{{json_content}}", json_content)
    
    # 保存HTML
    output_path = viz_dir / "comprehensive_viewer.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"🌐 完整HTML可视化: {output_path}")


def render_segmentation_html(segmentation_results: Dict[int, ParagraphSegmentationResult]) -> str:
    """渲染分段结果HTML"""
    if not segmentation_results:
        return '<div class="empty-state"><div class="empty-state-icon">📄</div><div class="empty-state-text">暂无分段数据</div></div>'
    
    html = ""
    for chapter_num in sorted(segmentation_results.keys()):
        seg_result = segmentation_results[chapter_num]
        
        # 统计ABC分布
        type_counts = {"A": 0, "B": 0, "C": 0}
        for p in seg_result.paragraphs:
            type_counts[p.type] = type_counts.get(p.type, 0) + 1
        
        # 获取使用的模型
        model_used = seg_result.metadata.get("model_used", "未知")
        model_class = "claude" if "claude" in model_used.lower() else "deepseek"
        
        html += f'''
        <div class="chapter-card">
            <div class="chapter-header">
                <div class="chapter-title">第{chapter_num}章</div>
                <div class="chapter-stats">
                    <span class="stat-badge">A类: {type_counts["A"]}</span>
                    <span class="stat-badge">B类: {type_counts["B"]}</span>
                    <span class="stat-badge">C类: {type_counts["C"]}</span>
                    <span class="model-badge {model_class}">🤖 {model_used}</span>
                </div>
            </div>
        '''
        
        for para in seg_result.paragraphs:
            html += f'''
            <div class="paragraph type-{para.type}">
                <div class="para-header">
                    <span class="para-type {para.type}">{para.type}类</span>
                    <span class="para-index">#{para.index}</span>
                </div>
                <div class="para-content">{para.content}</div>
            </div>
            '''
        
        html += "</div>"
    
    return html


def render_annotation_html(annotation_results: Dict[int, AnnotatedChapter]) -> str:
    """渲染标注结果HTML"""
    if not annotation_results:
        return '<div class="empty-state"><div class="empty-state-icon">🏷️</div><div class="empty-state-text">暂无标注数据</div></div>'
    
    html = ""
    for chapter_num in sorted(annotation_results.keys()):
        ann_result = annotation_results[chapter_num]
        
        # 获取使用的模型
        model_used = ann_result.metadata.get("model_used", "未知")
        model_class = "claude" if "claude" in model_used.lower() else "deepseek"
        
        html += f'''
        <div class="chapter-card">
            <div class="chapter-header">
                <div class="chapter-title">第{chapter_num}章</div>
                <div class="chapter-stats">
                    <span class="stat-badge">事件: {len(ann_result.event_timeline.events)}</span>
                    <span class="stat-badge">设定: {len(ann_result.setting_library.settings)}</span>
                    <span class="model-badge {model_class}">🤖 {model_used}</span>
                </div>
            </div>
            
            <h4 style="margin: 20px 0 10px 0; font-size: 16px; color: #4ecdc4;">📅 事件时间线</h4>
        '''
        
        for event in ann_result.event_timeline.events:
            # 获取时间信息
            time_info = event.time_info if hasattr(event, 'time_info') else {}
            time_str = time_info.get('time_point', '未知时间') if time_info else '未知时间'
            
            html += f'''
            <div class="event-card">
                <div class="event-header">
                    <div class="event-title">{event.event_summary}</div>
                    <div class="event-time">{time_str}</div>
                </div>
                <div class="event-description">{getattr(event, 'description', '')}</div>
            </div>
            '''
        
        html += '<h4 style="margin: 30px 0 10px 0; font-size: 16px; color: #ff6b6b;">📚 设定库</h4>'
        
        for setting in ann_result.setting_library.settings:
            html += f'''
            <div class="setting-card">
                <div class="setting-category">{setting.setting_title}</div>
                <div class="setting-content">{setting.setting_summary}</div>
            </div>
            '''
        
        html += "</div>"
    
    return html


def render_system_html(system_catalog: Optional[SystemCatalog]) -> str:
    """渲染系统分析HTML"""
    if not system_catalog:
        return '<div class="empty-state"><div class="empty-state-icon">🔧</div><div class="empty-state-text">暂无系统分析数据</div></div>'
    
    # 获取使用的模型
    model_used = system_catalog.metadata.get("model_used", "未知")
    model_class = "claude" if "claude" in model_used.lower() else "deepseek"
    
    html = f'''
    <div class="stats-grid">
        <div class="stat-card">
            <div class="value">{system_catalog.novel_type}</div>
            <div class="label">小说类型</div>
        </div>
        <div class="stat-card">
            <div class="value">{len(system_catalog.categories)}</div>
            <div class="label">系统类别数</div>
        </div>
        <div class="stat-card">
            <div class="value">{system_catalog.analyzed_chapters}</div>
            <div class="label">分析章节</div>
        </div>
        <div class="stat-card">
            <div class="value"><span class="model-badge {model_class}">{model_used}</span></div>
            <div class="label">使用模型</div>
        </div>
    </div>
    '''
    
    for category in system_catalog.categories:
        html += f'''
        <div class="system-category">
            <div class="system-category-title">
                {category.category_name}
                <span style="font-size: 14px; color: #999; font-weight: normal; margin-left: 10px;">
                    ({len(category.elements)}个元素)
                </span>
            </div>
            <div class="system-elements">
        '''
        
        # elements是List[str]，直接使用
        for element in category.elements:
            html += f'<div class="system-element">{element}</div>'
        
        html += '''
            </div>
        </div>
        '''
    
    return html


def render_quality_html(validation_report: Optional[NovelValidationReport], errors: List[ChapterProcessingError]) -> str:
    """渲染质量报告HTML"""
    if not validation_report:
        return '<div class="empty-state"><div class="empty-state-icon">⭐</div><div class="empty-state-text">暂无质量报告</div></div>'
    
    html = f'''
    <div class="quality-score">
        <div class="score">{validation_report.quality_score}</div>
        <div class="label">质量评分 / 100</div>
    </div>
    '''
    
    # 步骤报告
    if hasattr(validation_report, 'step_reports') and validation_report.step_reports:
        for step_name, report_content in validation_report.step_reports.items():
            html += f'''
            <div class="report-section">
                <h3>{step_name}</h3>
                <div class="report-content">{report_content}</div>
            </div>
            '''
    
    # 问题列表
    if hasattr(validation_report, 'issues') and validation_report.issues:
        html += '''
        <div class="report-section">
            <h3>⚠️ 发现的问题</h3>
            <div class="report-content">
        '''
        for issue in validation_report.issues:
            html += f"• {issue}<br>"
        html += '''
            </div>
        </div>
        '''
    
    # 错误列表
    if errors:
        html += f'''
        <div class="report-section">
            <h3>❌ 处理错误 ({len(errors)}个)</h3>
            <div class="report-content">
        '''
        for error in errors:
            html += f"• 章节{error.chapter_number}: [{error.error_type}] {error.error_message}<br>"
        html += '''
            </div>
        </div>
        '''
    
    return html
