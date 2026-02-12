# 架构重新设计 - 实施进展

## 📋 你提出的4个问题

### ✅ 问题 1: 数据存储结构
**问题**: "分析资料" 是外部文件夹，项目数据应该存储在 `data/`

**解决方案**:
- ✅ 创建了新的目录结构设计文档
- ✅ 实现了 `ProjectMeta` schema（包含完整的项目元数据）
- ✅ 实现了 `ProjectManagerV2`（支持新架构）
- ⏳ 需要更新 API 路由使用新的 Manager
- ⏳ 需要更新前端调用新的 API

**新的目录结构**:
```
data/projects/
└── project_001/
    ├── meta.json          # 项目元数据
    ├── raw/               # 原始文件
    ├── processed/         # 标准化处理后
    ├── analysis/          # 分析结果
    └── reports/           # 质量报告
```

### ✅ 问题 2: "有无原小说"应该是项目属性
**问题**: 不应该按"有无原小说"分类项目，而是作为项目的属性

**解决方案**:
- ✅ 在 `ProjectMeta` 中添加了 `sources` 字段:
  ```python
  class ProjectSources:
      has_novel: bool = False      # 是否有原小说
      has_script: bool = False     # 是否有脚本
      novel_chapters: int = 0      # 章节数
      script_episodes: int = 0     # 集数
  ```
- ✅ 项目可以同时有小说和脚本
- ⏳ 需要更新前端 UI 显示这些属性

### ⏳ 问题 3: 项目需要显示源文件和处理阶段
**问题**: 
- 需要在项目详情页查看小说章节和脚本集数
- 工作流需要拆分成多个阶段（导入 → 预处理 → 分析 → 对齐）

**解决方案（部分完成）**:
- ✅ 在 `ProjectMeta` 中添加了 `workflow_stages`:
  ```python
  class WorkflowStages:
      import_stage: WorkflowStageInfo        # 导入
      preprocess: WorkflowStageInfo          # 预处理
      novel_segmentation: WorkflowStageInfo  # 小说分段
      novel_annotation: WorkflowStageInfo    # 小说标注
      script_segmentation: WorkflowStageInfo # 脚本分段
      script_hooks: WorkflowStageInfo        # Hook检测
      alignment: WorkflowStageInfo           # 对齐
  ```
- ✅ `ProjectManagerV2` 实现了:
  - `get_chapters(project_id)` - 获取章节列表
  - `get_episodes(project_id)` - 获取集数列表
  - `get_raw_files(project_id)` - 获取原始文件列表
  - `update_workflow_stage()` - 更新阶段状态

- ⏳ **待实现**:
  - 添加新的 API 端点
  - 创建项目详情页面组件
  - 显示章节和集数列表
  - 实现阶段式工作流执行

### ⏳ 问题 4: 上传功能需要扩展
**问题**: 除了 novel 和 script，还需要支持其他类型文档

**解决方案（部分完成）**:
- ✅ `ProjectManagerV2.add_file()` 支持多种文件类型
- ✅ `_get_file_type()` 可识别: .txt, .srt, .md, .pdf
- ⏳ **待实现**:
  - 前端上传组件支持更多文件类型
  - 在项目详情页添加上传入口
  - 显示已上传文件列表并支持删除

---

## 🎯 下一步工作

### 优先级 1: 完成后端 API
1. 更新 `/api/projects` 路由使用 `ProjectManagerV2`
2. 添加新端点:
   - `GET /api/projects/{id}/meta` - 获取完整元数据
   - `GET /api/projects/{id}/chapters` - 章节列表
   - `GET /api/projects/{id}/episodes` - 集数列表
   - `GET /api/projects/{id}/files` - 原始文件列表
   - `POST /api/projects/{id}/files` - 上传文件（支持多种类型）

### 优先级 2: 创建项目详情页面
1. 创建 `ProjectDetailPage.tsx` 组件
2. 显示项目信息（名称、状态、源文件属性）
3. 显示原始文件列表（带上传功能）
4. 显示章节列表（如果有小说）
5. 显示集数列表（如果有脚本）
6. 显示工作流阶段状态

### 优先级 3: 重构工作流
1. 拆分工作流为独立阶段
2. 实现阶段式执行
3. 更新进度跟踪

---

## 📂 已创建的文件

### 后端
- ✅ `src/core/schemas_project.py` - 项目元数据 schema
- ✅ `src/core/project_manager_v2.py` - 新版项目管理器

### 文档
- ✅ `docs/architecture/DATA_STORAGE_REDESIGN.md` - 架构设计文档
- ✅ `docs/architecture/REDESIGN_PROGRESS.md` - 进展跟踪（本文档）

---

## 🤔 需要用户确认的问题

1. **数据迁移**: 
   - 现有的项目数据需要迁移到新结构吗？
   - 还是新旧系统并存？

2. **工作流拆分**:
   - 是否需要用户手动触发每个阶段？
   - 还是自动串联执行？

3. **数据库选择**:
   - 继续使用 JSON 文件？
   - 还是迁移到 SQLite？

---

## 📝 建议

基于你的需求，我建议按以下顺序继续开发：

1. **今天**: 完成后端 API 更新，创建项目详情页面基础框架
2. **明天**: 实现章节/集数列表显示，完善上传功能
3. **后续**: 重构工作流为阶段式执行

你希望我继续哪一部分？或者有其他优先级更高的需求？
