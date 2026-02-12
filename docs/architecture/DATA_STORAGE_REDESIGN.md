# 数据存储架构 - Analyst 目录结构

## 设计原则

1. **与 Phase I 工作流对应** - 目录结构完全匹配前端的4步流程
2. **职责清晰** - 每个目录对应明确的工作流阶段
3. **可追溯性** - 使用 ArtifactManager 进行版本化管理
4. **可扩展性** - 支持未来的 Phase II, Phase III 扩展

## Analyst 目录结构

```
data/
├── projects/                    # 项目数据（主要存储）
│   ├── project_001/
│   │   ├── meta.json           # 项目元数据（workflow_stages状态）
│   │   ├── raw/                # 原始上传文件
│   │   │   ├── novel/          # 小说原文
│   │   │   │   └── novel.txt
│   │   │   └── srt/            # 脚本SRT文件
│   │   │       ├── ep01.srt
│   │   │       ├── ep02.srt
│   │   │       └── ...
│   │   │
│   │   ├── analyst/            # ✨ Phase I Analyst 工作流数据
│   │   │   ├── import/         # 📁 Step 1: Import（预处理结果）
│   │   │   │   ├── novel/
│   │   │   │   │   ├── chapters.json      # 章节索引
│   │   │   │   │   ├── metadata.json      # 小说元数据
│   │   │   │   │   ├── intro.md           # 简介
│   │   │   │   │   └── novel-imported.md  # 完整小说（Markdown）
│   │   │   │   └── script/
│   │   │   │       ├── episodes.json      # 集数索引
│   │   │   │       ├── ep01.json          # 集数数据（JSON）
│   │   │   │       ├── ep01-imported.md   # 集数内容（Markdown）
│   │   │   │       └── ...
│   │   │   │
│   │   │   ├── script_analysis/    # 📁 Step 2: Script Analysis
│   │   │   │   ├── ep01_segmentation_latest.json
│   │   │   │   ├── ep01_hook_latest.json
│   │   │   │   ├── ep01_validation_latest.json
│   │   │   │   └── history/        # 历史版本（ArtifactManager）
│   │   │   │
│   │   │   ├── novel_analysis/     # 📁 Step 3: Novel Analysis
│   │   │   │   ├── chapter_001_segmentation_latest.json
│   │   │   │   ├── chapter_001_annotation_latest.json
│   │   │   │   ├── chapter_001_validation_latest.json
│   │   │   │   ├── system_catalog_latest.json
│   │   │   │   └── history/        # 历史版本（ArtifactManager）
│   │   │   │
│   │   │   └── alignment/          # 📁 Step 4: Alignment
│   │   │       ├── chapter_001_ep01_alignment_latest.json
│   │   │       └── history/        # 历史版本（ArtifactManager）
│   │   │
│   │   └── reports/            # 质量报告（跨阶段汇总）
│   │
│   └── project_002/
│       └── ...
│
├── project_index.json          # 项目索引（轻量级数据库）
└── llm_configs.json           # LLM 配置

# 外部文件夹（不在 git 中）
分析资料/                        # 用户自己管理的源文件
├── 末哥超凡公路/
│   ├── novel/
│   └── srt/
└── ...
```

## 项目元数据结构

```json
{
  "id": "project_001",
  "name": "末哥超凡公路",
  "description": "项目描述",
  "created_at": "2026-02-10T10:00:00Z",
  "updated_at": "2026-02-10T12:00:00Z",
  "status": "ready",  // draft, ready, processing, completed
  
  "sources": {
    "has_novel": true,        // 是否有原小说
    "has_script": true,       // 是否有脚本
    "novel_chapters": 10,     // 小说章节数
    "script_episodes": 3      // 脚本集数
  },
  
  "workflow_stages": {
    "import": {              // 阶段1: 导入
      "status": "completed",
      "completed_at": "2026-02-10T10:30:00Z"
    },
    "preprocessing": {       // 阶段2: 预处理
      "status": "completed",
      "completed_at": "2026-02-10T11:00:00Z"
    },
    "analysis": {            // 阶段3: 分析
      "novel_segmentation": "completed",
      "novel_annotation": "completed",
      "script_segmentation": "completed",
      "script_hooks": "completed"
    },
    "alignment": {           // 阶段4: 对齐
      "status": "pending"
    }
  },
  
  "stats": {
    "total_size": 1024000,
    "last_processed": "2026-02-10T12:00:00Z"
  }
}
```

## 数据库选择

### 方案 A: JSON 文件 + 索引（当前使用）
- ✅ 简单、无依赖
- ✅ 适合小规模数据
- ❌ 并发性能差
- ❌ 查询能力有限

### 方案 B: SQLite（推荐）
- ✅ 轻量级、无服务器
- ✅ SQL 查询能力
- ✅ 事务支持
- ✅ 并发处理好
- ✅ Python 原生支持

### 方案 C: PostgreSQL/MySQL
- ✅ 功能强大
- ❌ 需要额外服务
- ❌ 过于重量级

**建议：当前使用 JSON，后续迁移到 SQLite**

## Phase I Analyst 工作流阶段

### Step 1: Import（导入 + 预处理）
**目录**: `analyst/import/`

**职责**:
- 上传文件到 `raw/`
- 自动运行 PreprocessService
- 解析原始文件，转换为标准格式
- 保存到 `analyst/import/`

**输出文件**:
- Novel: `chapters.json`, `metadata.json`, `intro.md`, `novel-imported.md`
- Script: `episodes.json`, `ep01.json`, `ep01-imported.md`

---

### Step 2: Script Analysis（脚本分析）
**目录**: `analyst/script_analysis/`

**职责**:
- 脚本分段（ABC分类）
- Hook检测（仅ep01）
- 质量验证

**输出文件** (使用 ArtifactManager):
- `ep01_segmentation_latest.json`
- `ep01_hook_latest.json`
- `ep01_validation_latest.json`
- `history/` 目录（历史版本）

---

### Step 3: Novel Analysis（小说分析）
**目录**: `analyst/novel_analysis/`

**职责**:
- 小说分段（段落分类）
- 事件标注
- 系统元素检测
- 质量验证

**输出文件** (使用 ArtifactManager):
- `chapter_001_segmentation_latest.json`
- `chapter_001_annotation_latest.json`
- `system_catalog_latest.json`
- `chapter_001_validation_latest.json`
- `history/` 目录（历史版本）

---

### Step 4: Alignment（对齐分析）
**目录**: `analyst/alignment/`

**职责**:
- 小说-脚本对齐
- 生成对齐报告

**输出文件** (使用 ArtifactManager):
- `chapter_001_ep01_alignment_latest.json`
- `history/` 目录（历史版本）

## API 设计

### V2 API (Analyst Results)

所有分析结果的API都使用 `/api/v2/projects/{project_id}/analyst/` 前缀：

**Step 2 (Script Analysis)**:
- `GET /api/v2/projects/{id}/analyst/script_analysis/{episode_id}/segmentation`
- `GET /api/v2/projects/{id}/analyst/script_analysis/{episode_id}/hook`
- `GET /api/v2/projects/{id}/analyst/script_analysis/{episode_id}/validation`
- `GET /api/v2/projects/{id}/analyst/script_analysis/summary`

**Step 3 (Novel Analysis)**:
- `GET /api/v2/projects/{id}/analyst/novel_analysis/chapters`
- `GET /api/v2/projects/{id}/analyst/novel_analysis/{chapter_id}/segmentation`
- `GET /api/v2/projects/{id}/analyst/novel_analysis/{chapter_id}/annotation`
- `GET /api/v2/projects/{id}/analyst/novel_analysis/system_catalog`
- `GET /api/v2/projects/{id}/analyst/novel_analysis/{chapter_id}/validation`

**Step 4 (Alignment)**:
- `GET /api/v2/projects/{id}/analyst/alignment/pairs`
- `GET /api/v2/projects/{id}/analyst/alignment/{chapter_id}/{episode_id}`

## 与前端对应关系

| 前端页面 | 后端目录 | 说明 |
|---------|---------|------|
| Dashboard | - | 项目列表（读取 `meta.json`） |
| Step 1: Import | `analyst/import/` | 预处理结果（chapters, episodes） |
| Step 2: Script Analysis | `analyst/script_analysis/` | 分段、Hook、验证 |
| Step 3: Novel Analysis | `analyst/novel_analysis/` | 分段、标注、系统目录 |
| Step 4: Alignment | `analyst/alignment/` | 对齐结果 |
| Novel Viewer | `analyst/import/novel/` | 显示原文（intro.md, novel-imported.md） |
| Script Viewer | `analyst/import/script/` | 显示脚本（ep01-imported.md） |

---

## 版本化管理（ArtifactManager）

所有分析结果使用 **Latest Pointer + Timestamped Versions** 策略：

```
analyst/script_analysis/
├── ep01_segmentation_latest.json              # ⭐ 最新版本
└── history/
    ├── ep01_segmentation_v20260212_180000.json
    ├── ep01_segmentation_v20260212_190000.json
    └── ...
```

**优势**:
- ✅ 始终知道最新版本是哪个
- ✅ 保留历史版本，支持回滚
- ✅ 可对比不同LLM provider的结果
- ✅ 自动时间戳命名

---

## 实施状态

| 组件 | 状态 | 说明 |
|------|------|------|
| ProjectManagerV2 | ✅ 已完成 | 创建 `analyst/` 目录结构 |
| PreprocessService | ✅ 已完成 | 保存到 `analyst/import/` |
| analyst_results.py | ✅ 已完成 | API 读取 `analyst/` 路径 |
| 前端 API Client | ✅ 已完成 | 调用新的 API |
| ArtifactManager | ✅ 已完成 | 版本化管理工具 |
| 数据迁移脚本 | ⏳ 待完成 | 迁移现有项目数据 |
