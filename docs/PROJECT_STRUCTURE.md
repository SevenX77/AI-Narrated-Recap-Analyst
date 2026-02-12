# 项目结构说明

## 📁 目录组织

```
AI-Narrated-Recap-Analyst/
│
├── docs/                           # 📚 文档目录
│   ├── PROJECT_STRUCTURE.md        # 项目结构说明（本文件）
│   ├── DEV_STANDARDS.md            # 开发标准与规范
│   ├── FILE_PATH_MAPPING.md        # 文件路径映射说明
│   ├── FRONTEND_INTEGRATION_COMPLETE.md  # 前端集成完成文档
│   ├── README.md                   # 文档索引
│   │
│   ├── architecture/               # 架构设计文档
│   │   ├── AUTO_PREPROCESS_IMPLEMENTATION.md  # 自动预处理实现
│   │   ├── DATA_STORAGE_REDESIGN.md          # 数据存储重新设计
│   │   └── REDESIGN_PROGRESS.md              # 重新设计进度
│   │
│   ├── core/                       # Core模块文档
│   │   ├── README.md
│   │   ├── DUAL_LLM_SETUP.md       # 双LLM配置说明
│   │   ├── LLM_INTEGRATION_GUIDE.md
│   │   ├── LLM_RATE_LIMIT_SYSTEM.md
│   │   ├── LLM_SYSTEM_COMPLETE.md
│   │   └── README_LLM_SYSTEM.md
│   │
│   ├── tools/                      # Tools模块文档
│   │   ├── README.md
│   │   ├── ROADMAP.md              # 工具路线图
│   │   ├── functional_tags.md
│   │   ├── FUNCTIONAL_TAGS_UPDATE.md
│   │   ├── novel_*.md              # 小说相关工具文档
│   │   ├── script_*.md             # 脚本相关工具文档
│   │   ├── srt_*.md                # SRT相关工具文档
│   │   ├── hook_*.md               # Hook相关工具文档
│   │   └── system_*.md             # 系统相关文档
│   │
│   ├── workflows/                  # Workflows模块文档
│   │   ├── README.md
│   │   ├── ROADMAP.md
│   │   ├── novel_processing_workflow.md
│   │   ├── script_processing_workflow.md
│   │   ├── QUALITY_STANDARDS.md
│   │   ├── RETRY_MECHANISM.md
│   │   ├── BUGFIX_SUMMARY.md
│   │   └── LLM_ASYNC_FIX.md
│   │
│   ├── ui/                         # 前端UI文档
│   │   ├── README.md
│   │   ├── UI_ARCHITECTURE.md
│   │   ├── UI_DESIGN_GEEK_STYLE.md
│   │   ├── API_SPECIFICATION.md
│   │   ├── QUICKSTART.md
│   │   ├── IMPLEMENTATION_PLAN.md
│   │   ├── SHADCN_IMPLEMENTATION_SUMMARY.md
│   │   ├── UI_SYSTEM_SUMMARY.md
│   │   └── DOCKER_DEPLOYMENT.md
│   │
│   ├── maintenance/                # 维护性文档
│   │   ├── DOC_CODE_CONSISTENCY_REPORT.md
│   │   ├── DOC_UPDATE_SUMMARY_2026-02-10.md
│   │   ├── IMPROVEMENT_SUMMARY_2026-02-10.md
│   │   ├── INTEGRATION_SUMMARY.md
│   │   ├── LLM_SYSTEM_OVERVIEW.md
│   │   ├── MIGRATION_SUMMARY.md
│   │   ├── PROJECT_HEALTH_CHECK_2026-02-10.md
│   │   ├── TOOL_APPLICATION_SUMMARY_2026-02-10.md
│   │   └── WORKFLOW_SPLIT_SUMMARY_2026-02-10.md
│   │
│   └── archive/                    # 归档文档
│       └── docs/                   # 旧版本文档
│
├── src/                            # 💻 源代码
│   ├── api/                        # FastAPI后端服务 ⭐
│   │   ├── main.py                 # API入口
│   │   ├── routes/                 # API路由
│   │   │   ├── projects.py         # 项目管理API（V1，已废弃）
│   │   │   ├── projects_v2.py      # 项目管理API（V2，推荐）⭐
│   │   │   └── workflows.py        # 工作流API
│   │   ├── schemas/                # API数据模型
│   │   │   ├── projects.py
│   │   │   ├── projects_v2.py
│   │   │   └── workflows.py
│   │   ├── services/               # 业务服务层
│   │   └── middleware/             # 中间件
│   │
│   ├── core/                       # 核心组件
│   │   ├── interfaces.py           # 接口定义（BaseTool, BaseAgent, BaseWorkflow）
│   │   ├── config.py               # 配置管理
│   │   │
│   │   ├── schemas_novel/          # 小说相关数据模型（已拆分）⭐
│   │   │   ├── __init__.py
│   │   │   ├── basic.py            # 基础数据结构（Chapter, Paragraph等）
│   │   │   ├── segmentation.py     # 分段相关（SegmentedChapter等）
│   │   │   ├── annotation.py       # 标注相关（AnnotatedChapter, EventTimeline等）
│   │   │   ├── system.py           # 系统元素相关（SystemCatalog等）
│   │   │   └── validation.py       # 验证相关（ValidationResult等）
│   │   │
│   │   ├── schemas_script.py       # 脚本相关数据模型
│   │   ├── schemas_alignment.py    # 对齐相关数据模型
│   │   ├── schemas_project.py      # 项目相关数据模型
│   │   ├── schemas.py              # 通用数据模型
│   │   │
│   │   ├── project_manager.py      # 项目管理（V1，已弃用）❌
│   │   ├── project_manager_v2.py   # 项目管理（V2，当前使用）✅⭐
│   │   ├── llm_rate_limiter.py     # LLM速率限制
│   │   ├── two_pass_tool.py        # Two-Pass工具基类
│   │   └── exceptions.py           # 异常定义
│   │
│   ├── tools/                      # 独立工具库（无状态）
│   │   ├── __init__.py
│   │   │
│   │   ├── novel_importer.py       # 小说导入
│   │   ├── novel_metadata_extractor.py  # 元数据提取
│   │   ├── novel_chapter_detector.py    # 章节检测
│   │   ├── novel_segmenter.py      # 小说分段（Two-Pass）⭐
│   │   ├── novel_annotator.py      # 小说标注（Two-Pass）⭐
│   │   ├── novel_tagger.py         # 功能标签生成
│   │   ├── novel_validator.py      # 小说验证
│   │   │
│   │   ├── novel_system_detector.py     # 系统元素检测 ⭐
│   │   ├── novel_system_analyzer.py     # 系统元素分析
│   │   ├── novel_system_tracker.py      # 系统元素追踪
│   │   │
│   │   ├── srt_importer.py         # SRT导入
│   │   ├── srt_text_extractor.py   # SRT文本提取
│   │   ├── script_segmenter.py     # 脚本分段（Two-Pass）⭐
│   │   ├── script_validator.py     # 脚本验证
│   │   │
│   │   ├── novel_script_aligner.py # 小说-脚本对齐
│   │   │
│   │   ├── hook_detector.py        # Hook检测
│   │   └── hook_content_analyzer.py # Hook分析
│   │
│   ├── workflows/                  # 工作流编排
│   │   ├── novel_processing_workflow.py   # 小说处理工作流
│   │   ├── script_processing_workflow.py  # 脚本处理工作流
│   │   ├── preprocess_service.py          # 预处理服务（后台任务）⭐
│   │   ├── report_generator.py            # 报告生成
│   │   └── training_workflow_v2.py        # 训练工作流V2
│   │
│   ├── prompts/                    # 🎯 提示词管理
│   │   ├── novel_chapter_segmentation_pass1.yaml  # 小说分段Pass1 ⭐
│   │   ├── novel_chapter_segmentation_pass2.yaml  # 小说分段Pass2 ⭐
│   │   ├── novel_annotation_pass1.yaml            # 小说标注Pass1
│   │   ├── novel_annotation_pass2.yaml            # 小说标注Pass2
│   │   ├── novel_annotation_pass3_functional_tags.yaml  # 功能标签Pass3
│   │   ├── novel_tagging.yaml
│   │   ├── novel_system_detection.yaml
│   │   ├── novel_system_analysis.yaml
│   │   ├── novel_system_tracking.yaml
│   │   ├── novel_system_templates.yaml
│   │   ├── novel_script_alignment.yaml
│   │   ├── script_segmentation_abc_classification.yaml  # 脚本分段ABC分类
│   │   ├── hook_detection.yaml
│   │   └── hook_content_analysis.yaml
│   │
│   ├── utils/                      # 工具函数
│   │   ├── llm_output_parser.py    # LLM输出解析
│   │   └── novel_helpers.py        # 小说处理辅助函数
│   │
│   └── agents/                     # AI Agent实现（预留）
│
├── frontend-new/                   # 🎨 前端项目（当前使用）⭐
│   ├── src/
│   │   ├── components/             # UI组件（shadcn UI）
│   │   │   ├── ui/                 # shadcn基础组件
│   │   │   ├── app-sidebar.tsx     # 应用侧边栏
│   │   │   ├── site-header.tsx     # 站点头部
│   │   │   ├── chart-area-interactive.tsx  # 交互式图表
│   │   │   ├── data-table.tsx      # 数据表格
│   │   │   └── layout/             # 布局组件
│   │   │
│   │   ├── pages/                  # 页面组件
│   │   │   ├── Dashboard.tsx               # 项目列表
│   │   │   ├── ProjectDetailPage.tsx      # 项目详情 ⭐
│   │   │   ├── NovelViewerPage.tsx        # 小说查看器
│   │   │   ├── ScriptViewerPage.tsx       # 脚本查看器
│   │   │   ├── WorkflowPage.tsx           # 工作流页面
│   │   │   └── SettingsPage.tsx           # 设置页面
│   │   │
│   │   ├── api/                    # API客户端
│   │   │   ├── projectsV2.ts       # V2项目API ⭐
│   │   │   └── workflows.ts        # 工作流API
│   │   │
│   │   ├── types/                  # TypeScript类型定义
│   │   │   └── project.ts
│   │   │
│   │   ├── lib/                    # 工具库
│   │   │   ├── queryClient.ts      # React Query配置
│   │   │   └── utils.ts
│   │   │
│   │   ├── store/                  # 状态管理（Zustand）
│   │   ├── hooks/                  # 自定义Hooks
│   │   ├── App.tsx                 # 应用入口
│   │   ├── main.tsx                # 主入口
│   │   └── index.css               # 全局样式
│   │
│   ├── public/                     # 静态资源
│   ├── components.json             # shadcn配置
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── README.md
│
├── scripts/                        # 🔧 脚本工具
│   ├── test/                       # 测试脚本
│   │   ├── test_novel_*.py         # 小说相关测试
│   │   ├── test_script_*.py        # 脚本相关测试
│   │   ├── test_llm_*.py           # LLM相关测试
│   │   └── test_*.py               # 其他测试
│   │
│   ├── ui/                         # UI相关脚本
│   │   ├── init_ui_project.sh
│   │   └── start_backend.sh
│   │
│   ├── setup_claude.sh
│   ├── test_resume.sh
│   ├── migrate_raw_to_categories.py
│   └── split_*.py
│
├── data/                           # 📦 数据目录
│   ├── project_index.json          # 项目索引
│   └── projects/                   # 各项目数据
│       └── project_XXX/
│           ├── meta.json           # 项目元数据
│           ├── raw/                # 原始数据（用户上传）
│           │   ├── novel/          # 小说原始文件
│           │   └── script/         # 脚本原始文件（.srt）⚠️ 从srt/改名
│           │
│           └── analyst/            # ✨ Phase I Analyst 工作流数据
│               ├── import/         # Step 1: 导入与标准化
│               │   ├── novel/
│               │   │   ├── metadata.json        # 元数据
│               │   │   ├── chapters.json        # 章节列表
│               │   │   ├── intro.md             # 简介
│               │   │   └── novel-imported.md    # 标准化小说
│               │   └── script/
│               │       ├── episodes.json        # 集数索引
│               │       ├── ep01.json            # 集数元数据
│               │       └── ep01-imported.md     # 标准化脚本
│               │
│               ├── script_analysis/    # Step 2: 脚本分析
│               │   ├── ep01_segmentation_latest.json
│               │   ├── ep01_hook_latest.json
│               │   └── history/        # 历史版本
│               │
│               ├── novel_analysis/     # Step 3: 小说分析
│               │   ├── chapter_001_segmentation_latest.json
│               │   ├── chapter_001_annotation_latest.json
│               │   ├── system_catalog_latest.json
│               │   └── history/        # 历史版本
│               │
│               └── alignment/          # Step 4: 对齐分析
│                   ├── chapter_001_ep01_alignment_latest.json
│                   └── history/        # 历史版本
│
├── config/                         # ⚙️ 配置文件目录
├── output/                         # 📝 系统输出
│   └── operation_history.jsonl     # 操作历史日志
│
├── templates/                      # 📋 模板文件
├── requirements-api.txt            # API依赖
├── requirements.txt                # Python依赖
├── CHANGELOG.md                    # 变更日志
├── README.md                       # 项目说明
└── .gitignore                      # Git忽略规则
```

## 🎯 关键文件说明

### 后端服务

#### API路由
- **src/api/routes/projects_v2.py** ⭐ (推荐使用):
  - `GET /api/v2/projects` - 获取项目列表
  - `POST /api/v2/projects` - 创建项目
  - `GET /api/v2/projects/{id}` - 获取项目详情
  - `GET /api/v2/projects/{id}/meta` - 获取项目元数据
  - `POST /api/v2/projects/{id}/files` - 上传文件（支持自动预处理）
  - `GET /api/v2/projects/{id}/preprocess-status` - 获取预处理状态
  - `GET /api/v2/projects/{id}/chapters` - 获取章节列表
  - `GET /api/v2/projects/{id}/episodes` - 获取集数列表
  - `DELETE /api/v2/projects/{id}` - 删除项目

### 前端应用

#### 核心页面
- **frontend-new/src/pages/ProjectDetailPage.tsx**: 项目详情页
  - 项目信息展示
  - 文件上传（支持拖拽）
  - 原始文件列表
  - 预处理状态追踪（实时更新）
  - 章节/集数列表展示

### 配置文件

- **src/core/config.py**: 
  - 统一的配置管理
  - `ProjectConfig`: 项目配置
  - `LLMConfig`: LLM相关配置

### 数据模型

#### Schemas拆分（已模块化）⭐
- **src/core/schemas_novel/** (已拆分):
  - `basic.py`: Chapter, Paragraph, NovelMetadata
  - `segmentation.py`: SegmentedChapter, SegmentationResult
  - `annotation.py`: AnnotatedChapter, EventTimeline, SettingCorrelation
  - `system.py`: SystemCatalog, SystemElement, SystemCategory
  - `validation.py`: ValidationResult, ValidationIssue

- **src/core/schemas_script.py**:
  - `Episode`: 集数信息
  - `Segment`: 脚本段落
  - `ABCSegment`: ABC分类段落

- **src/core/schemas_alignment.py**:
  - `AlignmentResult`: 对齐结果
  - `AlignmentItem`: 对齐项

- **src/core/schemas_project.py**:
  - `ProjectV2`: 项目信息
  - `ProjectSources`: 源文件信息
  - `WorkflowStages`: 工作流阶段状态

### 工作流

- **src/workflows/novel_processing_workflow.py**:
  - 导入 → 元数据提取 → 章节检测 → 分段 → 标注 → 系统检测
  
- **src/workflows/script_processing_workflow.py**:
  - 导入 → 文本提取 → 分段 → 验证

- **src/workflows/preprocess_service.py** ⭐:
  - 自动识别文件类型
  - 异步执行预处理
  - 状态追踪和错误处理

### 提示词

所有提示词统一管理在 `src/prompts/*.yaml`，便于：
- 版本控制
- 快速迭代
- A/B测试

**核心Prompt**:
- `novel_chapter_segmentation_pass1.yaml` + `pass2.yaml`: Two-Pass小说分段 ⭐
- `novel_annotation_pass1.yaml` + `pass2.yaml` + `pass3_functional_tags.yaml`: 小说标注
- `script_segmentation_abc_classification.yaml`: 脚本ABC分类分段 ⭐

## 🔍 文件查找指南

### 想要修改...

| 需求 | 查看文件 |
|------|---------|
| **LLM配置** | `src/core/config.py` |
| **提示词** | `src/prompts/*.yaml` |
| **API路由** | `src/api/routes/*.py` |
| **数据模型（小说）** | `src/core/schemas_novel/*.py` ⭐ |
| **数据模型（脚本）** | `src/core/schemas_script.py` |
| **数据模型（项目）** | `src/core/schemas_project.py` |
| **工具实现** | `src/tools/*.py` |
| **工作流逻辑** | `src/workflows/*.py` |
| **前端页面** | `frontend-new/src/pages/*.tsx` |
| **前端API客户端** | `frontend-new/src/api/*.ts` |

### 想要了解...

| 问题 | 查看文档 |
|------|---------|
| **系统架构** | `docs/DEV_STANDARDS.md`, `docs/PROJECT_STRUCTURE.md` (本文件) |
| **代码规范** | `docs/DEV_STANDARDS.md` |
| **工具功能** | `docs/tools/*.md` |
| **工作流说明** | `docs/workflows/*.md` |
| **API规范** | `docs/ui/API_SPECIFICATION.md` |
| **前端架构** | `docs/ui/UI_ARCHITECTURE.md` |
| **LLM系统** | `docs/core/DUAL_LLM_SETUP.md`, `docs/core/LLM_INTEGRATION_GUIDE.md` |
| **功能优化** | `docs/maintenance/*.md` |

## 📝 命名规范

### 文件命名

- **Tools**: `{功能}_{操作}.py` (如 `novel_segmenter.py`)
- **Workflows**: `{功能}_workflow.py`
- **Schemas**: `schemas_{category}.py` 或 `schemas_{category}/` (目录)
- **API Routes**: `{资源}` 或 `{资源}_v2.py`
- **配置**: 统一在 `config.py`

### 文档放置规范

📍 **根目录应保持简洁，所有文档应放在 `docs/` 目录下**：

| 文档类型 | 放置位置 | 示例 | 说明 |
|---------|---------|------|------|
| **核心文档** | `docs/` | DEV_STANDARDS.md, PROJECT_STRUCTURE.md | 永久性、全局性的文档 |
| **架构设计** | `docs/architecture/` | AUTO_PREPROCESS_IMPLEMENTATION.md | 系统架构和设计文档 |
| **模块文档** | `docs/{module}/` | docs/tools/README.md | 各模块的技术参考 |
| **维护记录** | `docs/maintenance/` | DOC_UPDATE_SUMMARY.md | 清理报告、变更记录、迁移日志 |
| **归档文档** | `docs/archive/` | v2_architecture/ | 旧版本文档 |

⚠️ **严格禁止**：
- 在项目根目录创建任何 `.md` 或 `.txt` 文档文件（除 README.md, CHANGELOG.md）
- 在 `docs/` 根目录创建过程性/总结性文档（应放在 `maintenance/` 下）

### 数据文件

- **最新版本**: `{name}_latest.json` 或 `{name}.json` (指针文件)
- **历史版本**: `{name}_v{timestamp}.json`
- **示例**: 
  - `chapter_01.json` (最新版本)
  - `chapter_01_v20260211_102030.json` (历史版本)

## 🚫 不应提交的文件

已在 `.gitignore` 中配置：

- `.cursor/` - Cursor IDE配置
- `frontend/` - 旧版前端（已废弃）⚠️
- `frontend-new/node_modules/` - 前端依赖
- `__pycache__/` - Python缓存
- `data/projects/` - 项目数据（可选择性提交测试数据）
- `output/` - 运行输出
- `*.log` - 日志文件
- `.env` - 环境变量（敏感信息）
- `.debug/` - 调试文件
- `*.png`, `*.jpg` (根目录) - 截图应放在特定目录

## 🔄 数据流向（Phase I Analyst Workflow）

### Step 1: Import 导入与标准化

```
外部上传文件
    ↓
raw/novel/*.txt
raw/script/*.srt
    ↓ NovelImporter / SrtImporter
analyst/import/novel/novel-imported.md
analyst/import/script/ep01-imported.md
    ↓ NovelMetadataExtractor / NovelChapterDetector
analyst/import/novel/metadata.json
analyst/import/novel/chapters.json
analyst/import/script/episodes.json
```

### Step 2: Script Analysis 脚本分析

```
analyst/import/script/ep01-imported.md (取文件)
    ↓ ScriptSegmenter + HookDetector
analyst/script_analysis/ep01_segmentation_latest.json
analyst/script_analysis/ep01_hook_latest.json
```

### Step 3: Novel Analysis 小说分析

```
analyst/import/novel/chapters.json (取文件)
analyst/import/novel/novel-imported.md (取文件)
    ↓ NovelSegmenter (Two-Pass并行)
analyst/novel_analysis/chapter_001_segmentation_latest.json
    ↓ NovelAnnotator (Two-Pass并行)
analyst/novel_analysis/chapter_001_annotation_latest.json
    ↓ NovelSystemDetector (逐章)
analyst/novel_analysis/system_catalog_latest.json
```

### Step 4: Alignment 对齐分析

```
analyst/script_analysis/ep01_segmentation_latest.json (取文件)
+
analyst/novel_analysis/chapter_001_annotation_latest.json (取文件)
    ↓ NovelScriptAligner
analyst/alignment/chapter_001_ep01_alignment_latest.json
```

### API-前端交互流程

```
用户操作 (frontend-new)
    ↓ API Client (projectsV2.ts)
HTTP Request
    ↓ FastAPI Server (src/api/main.py)
API Routes (routes/projects_v2.py)
    ↓
ImportService (后台任务)
    ↓
Novel/Script Analysis Workflow
    ↓
数据保存 (analyst/)
    ↓
API Response
    ↓ React Query (自动刷新)
前端UI更新
```

## 🏗️ 架构分层

```
┌─────────────────────────────────────────┐
│         Frontend (React + Vite)         │
│    Pages → Components → API Client      │
└─────────────────┬───────────────────────┘
                  │ HTTP/JSON
┌─────────────────▼───────────────────────┐
│         Backend (FastAPI)                │
│    Routes → Services → Workflows        │
└─────────────────┬───────────────────────┘
                  │ Function Call
┌─────────────────▼───────────────────────┐
│         Workflows (Orchestration)        │
│    NovelProcessing / ScriptProcessing   │
└─────────────────┬───────────────────────┘
                  │ Tool Call
┌─────────────────▼───────────────────────┐
│         Tools (Stateless)                │
│    Importer / Extractor / Segmenter     │
└─────────────────┬───────────────────────┘
                  │ Data Access
┌─────────────────▼───────────────────────┐
│         Core (Schemas + Managers)        │
│    Schemas / ProjectManager / Config    │
└─────────────────┬───────────────────────┘
                  │ File I/O
┌─────────────────▼───────────────────────┐
│         Data Storage                     │
│    data/projects/ (JSON Files)          │
└─────────────────────────────────────────┘
```

---

**最后更新**: 2026-02-13  
**维护者**: Project Team  
**更新内容**: 
- 数据存储统一到 `analyst/` 目录
- `raw/srt/` 改名为 `raw/script/`
- 去除 `processed/` 和顶层 `alignment/` 文件夹
- 采用四步工作流: import → script_analysis → novel_analysis → alignment
