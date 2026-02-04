# 项目结构说明

## 📁 目录组织

```
AI-Narrated-Recap-Analyst/
│
├── docs/                           # 📚 文档目录
│   ├── PROJECT_STRUCTURE.md        # 项目结构说明（本文件）
│   ├── DEV_STANDARDS.md            # 开发标准与规范
│   ├── architecture/               # 架构设计文档
│   │   └── logic_flows.md          # 系统架构与数据流
│   └── maintenance/                # 维护性文档（功能优化、清理报告、变更记录等）
│       ├── ingestion_optimization_deployment.md   # 摄入优化部署指南
│       ├── ingestion_optimization_progress.md     # 摄入优化实施进度
│       ├── CLEANUP_SUMMARY.md                     # 项目整理总结
│       └── PROJECT_CLEANUP_REPORT.txt             # 整理完成报告
│
├── src/                            # 💻 源代码
│   ├── agents/                     # AI Agent 实现
│   │   ├── analyst.py              # Analyst基类
│   │   ├── deepseek_analyst.py     # DeepSeek Analyst实现
│   │   ├── writer.py               # Writer基类
│   │   ├── deepseek_writer.py      # DeepSeek Writer实现
│   │   └── feedback_agent.py       # 反馈评估Agent
│   │
│   ├── workflows/                  # 工作流编排
│   │   ├── ingestion_workflow.py   # 数据摄入与对齐工作流
│   │   └── training_workflow.py    # 训练工作流
│   │
│   ├── modules/                    # 功能模块
│   │   └── alignment/
│   │       ├── alignment_engine.py        # 对齐引擎基类
│   │       └── deepseek_alignment_engine.py # DeepSeek对齐实现
│   │
│   ├── core/                       # 核心组件
│   │   ├── config.py               # 配置管理
│   │   ├── schemas.py              # 数据模型（Pydantic）
│   │   ├── schemas_writer.py       # Writer相关模型
│   │   ├── interfaces.py           # 接口定义
│   │   ├── project_manager.py      # 项目管理
│   │   └── artifact_manager.py     # 数据版本管理
│   │
│   ├── prompts/                    # 🎯 提示词管理
│   │   ├── analyst.yaml
│   │   ├── alignment.yaml
│   │   ├── writer.yaml
│   │   └── feedback.yaml
│   │
│   ├── utils/                      # 工具函数
│   │   ├── logger.py               # 日志工具
│   │   ├── prompt_loader.py        # 提示词加载
│   │   └── text_processing.py      # 文本处理
│   │
│   └── tools/                      # 独立工具（预留）
│
├── scripts/                        # 🔧 脚本工具
│   ├── examples/                   # 使用示例
│   │   └── generate_ep01_recap.py  # EP01生成示例
│   ├── validate_standards.py       # 代码标准验证
│   ├── migrate_artifacts.py        # 数据迁移脚本
│   └── debug_hook_detection.py     # 调试工具
│
├── data/                           # 📦 数据目录
│   ├── project_index.json          # 项目索引
│   └── projects/                   # 各项目数据
│       └── PROJ_XXX/
│           ├── raw/                # 原始数据
│           │   ├── novel.txt
│           │   └── *.srt
│           ├── alignment/          # 对齐数据
│           │   ├── novel_events_latest.json
│           │   ├── epXX_script_events_latest.json
│           │   └── alignment_latest.json
│           ├── analysis/           # 分析结果
│           ├── training/           # 训练数据
│           │   └── reports/
│           └── production/         # 生产输出
│               └── scripts/
│
├── logs/                           # 📝 日志目录
│   └── output/
│       ├── app.log
│       └── operation_history.jsonl
│
├── main.py                         # 🚀 主入口
├── requirements.txt                # Python依赖
├── README.md                       # 项目说明
└── .gitignore                      # Git忽略规则
```

## 🎯 关键文件说明

### 配置文件

- **src/core/config.py**: 
  - 统一的配置管理
  - `IngestionConfig`: 摄入工作流配置
  - `LLMConfig`: LLM相关配置

### 数据模型

- **src/core/schemas.py**:
  - `NarrativeEvent`: 叙事事件（SVO结构）
  - `SceneAnalysis`: 场景分析结果
  - `AlignmentItem`: 对齐项
  - `AlignmentQualityReport`: 质量评估报告
  - `EpisodeCoverage`: 单集覆盖情况

### 工作流

- **src/workflows/ingestion_workflow.py**:
  - 动态章节提取
  - 并发事件提取
  - 质量评估
  - 自适应对齐

### 提示词

所有提示词统一管理在 `src/prompts/*.yaml`，便于：
- 版本控制
- 快速迭代
- A/B测试

## 🔍 文件查找指南

### 想要修改...

| 需求 | 查看文件 |
|------|---------|
| **LLM配置** | `src/core/config.py` |
| **提示词** | `src/prompts/*.yaml` |
| **质量阈值** | `src/core/config.py` → `IngestionConfig` |
| **并发数** | `src/core/config.py` → `max_concurrent_requests` |
| **数据模型** | `src/core/schemas.py` |
| **对齐算法** | `src/modules/alignment/deepseek_alignment_engine.py` |
| **工作流逻辑** | `src/workflows/ingestion_workflow.py` |
| **日志配置** | `src/utils/logger.py` |

### 想要了解...

| 问题 | 查看文档 |
|------|---------|
| **系统架构** | `docs/architecture/logic_flows.md` |
| **代码规范** | `docs/DEV_STANDARDS.md` |
| **项目结构** | `docs/PROJECT_STRUCTURE.md` (本文件) |
| **功能优化详情** | `docs/maintenance/` 目录下的相关文档 |

## 📝 命名规范

### 文件命名

- **Agents**: `{provider}_{agent_type}.py` (如 `deepseek_analyst.py`)
- **Workflows**: `{workflow_name}_workflow.py`
- **Schemas**: `schemas_{category}.py` (如 `schemas_writer.py`)
- **配置**: 统一在 `config.py`

### 文档放置规范

📍 **根目录应保持简洁，所有文档应放在 `docs/` 目录下**：

| 文档类型 | 放置位置 | 示例 | 说明 |
|---------|---------|------|------|
| **核心文档** | `docs/` | DEV_STANDARDS.md, PROJECT_STRUCTURE.md | 永久性、全局性的文档 |
| **架构设计** | `docs/architecture/` | logic_flows.md | 系统架构和设计文档 |
| **功能优化** | `docs/maintenance/` | ingestion_optimization_*.md | 针对特定功能的优化文档 |
| **维护记录** | `docs/maintenance/` | CLEANUP_SUMMARY.md | 清理报告、变更记录、迁移日志 |

⚠️ **严格禁止**：
- 在 `docs/` 根目录创建针对特定功能的文档（应放在 `maintenance/` 下）
- 在项目根目录创建任何 `.md` 或 `.txt` 文档文件

### 数据文件

- **最新版本**: `{name}_latest.json` (指针文件)
- **历史版本**: `{name}_v{timestamp}.json`
- **示例**: 
  - `novel_events_latest.json`
  - `novel_events_v20260203_045226.json`

## 🚫 不应提交的文件

已在 `.gitignore` 中配置：

- `browser_data/` - 浏览器缓存
- `cookies.json` - 临时cookies
- `chapter_*.txt` - 临时文本文件
- `*.bak` - 备份文件
- `__pycache__/` - Python缓存
- `logs/` - 日志文件
- `data/projects/` - 项目数据

## 🔄 数据流向

```
原始数据 (raw/)
    ↓
Analyst 提取事件
    ↓
事件数据 (alignment/)
    ↓
Alignment Engine 对齐
    ↓
对齐结果 + 质量报告
    ↓
训练数据 (training/) 或 生产输出 (production/)
```

---

**最后更新**: 2026-02-03  
**维护者**: 开发团队
