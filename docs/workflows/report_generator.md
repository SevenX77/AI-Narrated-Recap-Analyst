# Report Generator (报告生成器)

## 职责 (Responsibility)
`ReportGenerator` 是 `NovelProcessingWorkflow` 的配套模块，负责将分析过程中的结构化数据转换为人类可读的报告（Markdown）和可视化页面（HTML）。

## 接口 (Interface)

该模块提供了一系列独立的生成函数，由主工作流在各个步骤完成后调用。

### 主要函数

#### 步骤报告 (Markdown)
- `output_step1_report(import_result, processing_dir)`: 导入报告
- `output_step2_report(metadata, processing_dir)`: 元数据报告
- `output_step3_report(chapters, processing_dir)`: 章节检测报告
- `output_step4_report(segmentation_results, processing_dir)`: 分段质量分析报告 ⭐
- `output_step5_report(annotation_results, processing_dir)`: 标注统计报告
- `output_step67_report(catalog, updates, tracking, processing_dir)`: 系统分析报告
- `output_step8_report(validation_report, processing_dir)`: 最终验证报告

#### 内容生成 (Markdown)
- `generate_metadata_markdown(metadata, project_name)`: 生成 `novel/metadata.md`
- `generate_chapters_index_markdown(chapters, project_name)`: 生成 `novel/chapters_index.md`
- `generate_chapter_markdown(segmentation_results, chapters, project_name)`: 生成 `novel/chapter_XXX.md`

#### 可视化 (HTML)
- `generate_comprehensive_html(result, project_name, novel_title)`: 生成交互式 HTML 仪表板

## 实现逻辑 (Implementation Logic)

### 1. 质量评分 (Step 4 Report)
在 `output_step4_report` 中实现了严格的分段质量评分逻辑：
- **ABC分布检查**: A类(设定) < 3% 或 > 40% 会扣分。
- **分段粒度检查**: 段落数 < 3 (分段不足) 或 > 25 (过度分段) 会扣分。
- **文本还原率**: 检查分段后的文本是否完整还原了原文。

### 2. HTML 可视化
使用 `templates/comprehensive_visualization_template.html` 模板，将 JSON 数据注入到 HTML 中，利用前端 JS 实现交互式查看（如折叠/展开段落、筛选事件类型）。

## 依赖 (Dependencies)
- **Schemas**: `src.core.schemas_novel.*`
- **Templates**: `templates/comprehensive_visualization_template.html`

## 示例代码 (Code Example)

```python
from src.workflows.report_generator import output_step4_report

# 在工作流 Step 4 完成后调用
output_step4_report(
    segmentation_results=step4_results,
    processing_dir=self.processing_dir
)
```
