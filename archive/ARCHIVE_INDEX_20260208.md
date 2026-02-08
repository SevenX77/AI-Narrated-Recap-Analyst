# 项目归档索引 (2026-02-08)

## 归档原因
项目重构：保留writer和training核心流程，归档所有旧版本的素材处理、对齐分析相关代码。
从0开始重新构建，专注把每个工具做扎实。

---

## 归档内容清单

### 1. Workflows (v2_workflows_20260208/)
**归档文件**:
- `ingestion_workflow_v3.py` - Hook-Body分离架构的数据摄入工作流
- `migration_workflow.py` - 项目迁移工作流

**保留文件**:
- `training_workflow_v2.py` - 热度驱动训练工作流（继续使用）

**归档原因**: 素材处理流程需要重新设计，旧版workflow架构过于复杂

---

### 2. Tools (v2_tools_20260208/)
**归档的8个工具**:
1. `introduction_validator.py` - 简介验证工具
2. `key_info_extractor.py` - 关键信息提取
3. `novel_chapter_analyzer.py` - 章节分析器
4. `novel_chapter_processor.py` - 章节处理器
5. `novel_processor.py` - 小说处理器
6. `novel_segmentation_analyzer.py` - 分段分析器
7. `script_segment_aligner.py` - 脚本对齐器
8. `srt_processor.py` - SRT处理器

**保留内容**: src/tools/ 目录现在为空，等待新工具

**归档原因**: 这些工具属于writer和training之前的素材处理阶段，需要从头重新设计

---

### 3. Agents (v2_agents_20260208/)
**归档的4个agents**:
1. `analyst.py` - 分析代理
2. `comparative_evaluator.py` - 对比评估代理
3. `deepseek_analyst.py` - DeepSeek分析客户端
4. `feedback_agent.py` - 反馈代理

**保留的4个agents**:
1. `deepseek_writer.py` - DeepSeek写作代理（writer核心）
2. `writer.py` - 写作代理（writer核心）
3. `rule_extractor.py` - 规则提取代理（training核心）
4. `rule_validator.py` - 规则验证代理（training核心）

**归档原因**: 保留writer和training核心，其他分析类agents重新设计

---

### 4. Modules (v2_modules_20260208/)
**归档的完整模块**:
- `alignment/` - 对齐模块（6个文件）
  - `body_start_detector.py`
  - `hook_content_extractor.py`
  - `layered_alignment_engine.py`
  - `novel_preprocessor.py`
  - 其他对齐相关工具
- `optimization/` - 优化模块（5个文件）
  - 自反馈优化系统
  - Prompt优化引擎

**归档原因**: 整个alignment和optimization架构需要重新设计

---

### 5. Docs (v2_docs_20260208/)
**归档所有文档** (共32个文件):

**架构文档**:
- `architecture/LAYERED_ALIGNMENT_DESIGN.md`
- `architecture/logic_flows.md`
- `architecture/SRT_PROCESSING_DESIGN.md`

**教程和指南**:
- `AI_TRAINING_TUTORIAL.md`
- `CLAUDE_SETUP_GUIDE.md`
- `CURSORRULES_UNIVERSAL_GUIDE.md`
- `HOOK_BODY_QUICKSTART.md`
- `LAYERED_ALIGNMENT_QUICKSTART.md`
- `SRT_PROCESSING_QUICKSTART.md`
- `QUICK_START_CLAUDE.md`

**方法论文档**:
- `NOVEL_SEGMENTATION_METHODOLOGY.md`
- `NOVEL_SEGMENTATION_QUICKREF.md`
- `METHODOLOGY_SUMMARY.md`
- `R1_MANUAL_SEGMENTATION_DIFFERENCES.md`
- `R1_VS_MANUAL_COMPARISON.md`

**实施报告**:
- `V4_COMPLETE_IMPLEMENTATION_SUMMARY.md`
- `NOVEL_PROCESSING_WORKFLOW_COMPLETE.md`
- `HEAT_DRIVEN_TRAINING_SYSTEM.md`
- `PROJECT_STRUCTURE.md`

**对比分析**:
- `CLAUDE_ONECHATS_SUMMARY.md`
- `CLAUDE_VS_MANUAL_ANALYSIS_COMPARISON.md`

**维护文档** (maintenance/):
- `ingestion_optimization_deployment.md`
- `ingestion_optimization_progress.md`
- `NOVEL_CHAPTER_ANALYZER_IMPLEMENTATION.md`
- `PROJECT_MIGRATION_V2_SUMMARY.md`
- `PROJECT_OPTIMIZATION_V2.1.md`
- `REFACTORING_REPORT_V3.md`
- `SRT_PROCESSING_IMPLEMENTATION.md`
- `WORKFLOW_FIX_REPORT_20260208.md`

**标准文档** (保留):
- `DEV_STANDARDS.md` - 将在新版本中更新

**归档原因**: 旧文档对应旧架构，新架构需要新文档

---

### 6. Data (v2_data_20260208/)
**归档所有数据**:

**项目数据**:
- `projects/with_novel/` - 有小说的项目（3个）
  - 天命桃花
  - 末哥超凡公路
  - 永夜悔恨录
- `projects/without_novel/` - 无小说的项目（2个）
  - 末世寒潮
  - 超前崛起

**归档数据**:
- `projects_archive_20260205/` - 旧版本归档

**其他数据**:
- `alignment_optimization/` - 对齐优化标注数据
- `migration_report_20260205.json` - 迁移报告
- `project_index.json` - 项目索引

**归档原因**: 清空数据，从新项目开始积累

---

## 保留的项目结构

```
AI-Narrated-Recap-Analyst/
├── src/
│   ├── core/              # 核心配置和接口（保留）
│   ├── agents/            # 仅保留writer和training agents
│   │   ├── deepseek_writer.py
│   │   ├── writer.py
│   │   ├── rule_extractor.py
│   │   └── rule_validator.py
│   ├── tools/             # 空目录，等待新工具
│   ├── workflows/         # 仅保留training_workflow_v2.py
│   ├── prompts/           # Prompt配置（保留）
│   └── utils/             # 工具函数（保留）
├── data/                  # 空目录，等待新数据
├── docs/                  # 空目录，等待新文档
├── scripts/               # 脚本（保留）
├── logs/                  # 日志（保留）
└── archive/               # 归档目录
    ├── v2_workflows_20260208/
    ├── v2_tools_20260208/
    ├── v2_agents_20260208/
    ├── v2_modules_20260208/
    ├── v2_docs_20260208/
    ├── v2_data_20260208/
    └── ARCHIVE_INDEX_20260208.md
```

---

## 归档统计

| 类别 | 归档数量 | 保留数量 |
|------|---------|---------|
| Workflows | 2个 | 1个 |
| Tools | 8个 | 0个 |
| Agents | 4个 | 4个 |
| Modules | 2个完整目录 | 0个 |
| Docs | 32个文件 | 0个 |
| Data | 全部 | 0个 |

---

## 下一步计划

### Phase 1: 素材处理工具
专注构建扎实的基础工具：
1. Novel导入与分段工具
2. Script导入与处理工具
3. Hook检测工具
4. 基础验证工具

### Phase 2: 分析对齐工具
在Phase 1基础上构建：
1. 语义分析工具
2. 对齐匹配工具
3. 质量评估工具

### Phase 3: Workflow串联
工具扎实后再考虑workflow设计

---

## 恢复指南

如需恢复归档内容：
```bash
# 恢复某个工具
cp archive/v2_tools_20260208/novel_processor.py src/tools/

# 恢复某个workflow
cp archive/v2_workflows_20260208/ingestion_workflow_v3.py src/workflows/

# 恢复文档
cp archive/v2_docs_20260208/NOVEL_SEGMENTATION_METHODOLOGY.md docs/
```

---

## 备注

- 归档不是删除，所有代码和文档都完整保留
- 可以随时参考归档内容
- 新版本将吸取旧版本的经验教训
- 专注于把每个工具做扎实，而不是追求完整的workflow

**归档日期**: 2026-02-08  
**执行人**: AI Assistant  
**批准**: User (sevenx)
