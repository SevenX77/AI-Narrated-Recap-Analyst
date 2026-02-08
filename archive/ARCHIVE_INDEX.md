# 归档文件索引

> **最后更新**: 2026-02-07

本目录存放已废弃或过时的代码和文档，仅供历史参考。

---

## 📁 归档目录结构

### `v1_legacy_workflows/`
**归档日期**: 2026-02-07  
**原因**: 已被v2版本替代

**内容**:
- `training_workflow.py` - 旧版训练工作流，已被`training_workflow_v2.py`（热度驱动系统）替代

---

### `v2_deprecated/`
**归档日期**: 2026-02-05（历史归档）  
**原因**: v2对齐方法已被v4分层对齐替代

**内容**:
- `alignment_data/` - v2对齐结果数据
- `alignment_modules/` - v2对齐引擎代码
  - `alignment_engine.py`
  - `deepseek_alignment_engine_v2.py`
  - `hook_detector.py`
- `workflows/` - 旧版ingestion工作流

---

### `v3_maintenance_docs/`
**归档日期**: 2026-02-07  
**原因**: 一次性实施报告和问题修复文档，不再需要日常参考

**内容**:
- `CLEANUP_*.md` - 项目清理报告（v4相关）
- `DIAGNOSIS_REPORT.md` - 问题诊断报告
- `ERROR_ANALYSIS_REPORT.md` - 错误分析
- `V4*.md` - v4版本实施和问题修复文档
- `LLM_FILTER_*.md` - LLM过滤测试结果
- `PHASE2_IMPLEMENTATION.md` - 阶段2实施报告
- 其他一次性实施文档

---

## 🔄 当前活跃系统

### Alignment System
- **当前版本**: v4.0 - Layered Alignment Engine
- **位置**: `src/modules/alignment/layered_alignment_engine.py`
- **文档**: `docs/architecture/logic_flows.md` (Section 3)

### Training System
- **当前版本**: v2.0 - Heat-Driven Training Workflow
- **位置**: `src/workflows/training_workflow_v2.py`
- **文档**: `docs/architecture/logic_flows.md` (Workflow 2)

### Novel Processing
- **当前版本**: v2.2 - Functional Segment Analysis
- **工具**: `NovelChapterAnalyzer` (功能段分析), `NovelChapterProcessor` (简介拆分)
- **废弃工具**: `NovelSegmentationTool` (规则分段，质量不达标) → 归档到 `v2_deprecated/old_novel_processing/`
- **文档**: `docs/architecture/logic_flows.md` (Section 九、十)

---

## ⚠️ 注意事项

1. **不要删除归档文件**，它们可能包含重要的设计思路和历史决策
2. **新的废弃内容**应继续归档到此目录
3. **归档前**确保相关功能已有新版本替代
4. **更新此索引**当有新文件归档时

---

*维护者: 开发团队*
