# 工作流与数据存储参考

**最后更新**: 2026-02-12  
**目的**: 工作流设计、数据流转、存储结构的完整参考

---

## 📊 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Import   │→ │ Script   │→ │ Novel    │→ │Alignment │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                     Backend API (FastAPI)                        │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓ 调用
┌─────────────────────────────────────────────────────────────────┐
│                  Workflows & Tools (Python)                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ Import         │  │ Script         │  │ Novel          │    │
│  │ Service        │  │ Analysis       │  │ Analysis       │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓ 写入/读取
┌─────────────────────────────────────────────────────────────────┐
│            Data Storage (JSON Files) - Phase I                   │
│  ┌────────┐  ┌─────────┐  ┌──────────────┐  ┌────────────┐     │
│  │ raw/   │→ │ import/ │→ │script/novel  │→ │ alignment/ │     │
│  │        │  │         │  │  _analysis/  │  │            │     │
│  └────────┘  └─────────┘  └──────────────┘  └────────────┘     │
│                     analyst/ (所有Phase I数据)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 核心工作流

### Workflow 1: NovelProcessingWorkflow
**目标**: 从原始小说到完整章节分析

**文件路径**: `src/workflows/novel_processing_workflow.py`

**工具链**:
```
Novel.txt 
    ↓ NovelImporter
规范化文本
    ↓ NovelMetadataExtractor
元数据 (metadata.json)
    ↓ NovelChapterDetector
章节列表 (chapters.json)
    ↓ NovelSegmenter (并行处理各章节)
分段结果 (segmented/chapter_*.json)
    ↓ NovelAnnotator (并行处理各章节)
标注结果 (annotated/chapter_*.json)
    ↓ NovelSystemDetector (逐章处理)
系统目录 (system_catalog.json)
    ↓ NovelValidator
质量报告
```

**输入参数**:
```python
{
    "project_id": "project_001",
    "novel_path": "data/projects/project_001/raw/novel/novel.txt"
}
```

**输出数据**:
```
data/projects/project_001/analyst/
├── import/novel/
│   ├── novel-imported.md             # NovelImporter输出
│   ├── metadata.json                 # NovelMetadataExtractor输出
│   ├── chapters.json                 # NovelChapterDetector输出
│   └── intro.md                      # 小说简介
│
└── novel_analysis/
    ├── chapter_001_segmentation_latest.json    # NovelSegmenter输出
    ├── chapter_001_annotation_latest.json      # NovelAnnotator输出
    ├── system_catalog_latest.json              # NovelSystemDetector输出
    └── history/                                # 历史版本
```

**执行配置**:
```python
NovelProcessingConfig(
    use_llm=True,
    llm_provider_segmentation="claude",     # 分段必须用Claude
    llm_provider_annotation="claude",       # 标注必须用Claude
    llm_provider_system="claude",           # 系统检测必须用Claude
    parallel_chapters=True,                 # 并行处理章节
    max_workers=3                           # 最大并发数
)
```

**成本估算**:
- 分段: ~$0.06/章 (Two-Pass Claude)
- 标注: ~$0.08/章 (Two-Pass Claude)
- 系统检测: ~$0.02/章 (独立Pass Claude)
- **总计**: ~$0.16/章，50章约 $8

---

### Workflow 2: ScriptProcessingWorkflow
**目标**: 从SRT到结构化脚本分段

**文件路径**: `src/workflows/script_processing_workflow.py`

**工具链**:
```
SRT文件
    ↓ SrtImporter
SRT条目列表
    ↓ SrtTextExtractor
纯文本 + 标点修复
    ↓ HookDetector (仅ep01)
Hook信息
    ↓ ScriptSegmenter (ABC分类)
分段结果
    ↓ ScriptValidator
质量报告
```

**输入参数**:
```python
{
    "project_id": "project_001",
    "srt_files": [
        "data/projects/project_001/raw/script/ep01.srt",
        "data/projects/project_001/raw/script/ep02.srt"
    ]
}
```

**输出数据**:
```
data/projects/project_001/analyst/
├── import/script/
│   ├── episodes.json                 # 集数索引
│   ├── ep01.json                     # 集数元数据
│   ├── ep01-imported.md              # SrtTextExtractor输出
│   └── ep02-imported.md
│
└── script_analysis/
    ├── ep01_segmentation_latest.json # ScriptSegmenter输出
    ├── ep01_hook_latest.json         # HookDetector输出（仅ep01）
    └── history/                      # 历史版本
```

**执行配置**:
```python
ScriptProcessingConfig(
    use_llm=True,
    llm_provider="deepseek",            # Script处理用DeepSeek
    detect_hook_ep01=True,              # 仅ep01检测Hook
    parallel_episodes=True,             # 并行处理集数
    max_workers=3
)
```

**成本估算**:
- 文本提取: ~$0.02/集 (DeepSeek)
- Hook检测: ~$0.05 (仅ep01, Claude)
- 分段: ~$0.03/集 (DeepSeek)
- **总计**: ep01约$0.10，其他集约$0.05/集

---

### Workflow 3: ImportService (原PreprocessService) ⭐
**目标**: 文件上传后自动导入与标准化（后台异步任务）

**文件路径**: `src/workflows/import_service.py`

**触发方式**: 文件上传到raw/后自动触发

**处理流程**:
```python
# 伪代码
def auto_import(project_id, file_path):
    # 1. 识别文件类型
    file_type = detect_file_type(file_path)  # .txt → novel, .srt → script
    
    # 2. 根据类型执行导入与标准化
    if file_type == "novel":
        # 导入 → 元数据提取 → 章节检测
        # 输出到: analyst/import/novel/
        NovelImporter.execute(...)
        NovelMetadataExtractor.execute(...)
        NovelChapterDetector.execute(...)
        
    elif file_type == "script":
        # 导入 → 文本提取
        # 输出到: analyst/import/script/
        SrtImporter.execute(...)
        SrtTextExtractor.execute(...)
    
    # 3. 更新项目状态
    update_workflow_stage(project_id, "import", "completed")
```

**状态追踪**:
```json
{
  "project_id": "project_001",
  "preprocess_status": {
    "novel": {
      "status": "completed",
      "tasks": [
        {"name": "导入", "status": "completed", "progress": 100},
        {"name": "元数据提取", "status": "completed", "progress": 100},
        {"name": "章节检测", "status": "completed", "progress": 100}
      ]
    },
    "script": {
      "status": "running",
      "tasks": [
        {"name": "ep01.srt 导入", "status": "completed", "progress": 100},
        {"name": "ep01.srt 文本提取", "status": "running", "progress": 45}
      ]
    }
  }
}
```

**API集成**:
```typescript
// 前端轮询或WebSocket获取状态
const status = await fetch(`/api/v2/projects/${projectId}/preprocess-status`);
```

---

## 📁 数据存储结构

### 目录结构（Phase I Analyst Workflow）

```
data/projects/{project_id}/
│
├── meta.json                          # 项目元数据（包含workflow_stages）
│
├── raw/                               # 原始文件（用户上传）
│   ├── novel/
│   │   └── 序列公路求生.txt
│   └── script/                        # ⚠️ 从srt改名为script
│       ├── ep01.srt
│       └── ep02.srt
│
└── analyst/                           # 🌟 Phase I 所有分析数据
    │
    ├── import/                        # Step 1: 导入与标准化
    │   ├── novel/
    │   │   ├── metadata.json          # 小说元数据
    │   │   ├── chapters.json          # 章节列表
    │   │   ├── intro.md               # 小说简介
    │   │   └── novel-imported.md      # 标准化后的完整小说
    │   │
    │   └── script/
    │       ├── episodes.json          # 集数索引
    │       ├── ep01.json              # 集数元数据
    │       ├── ep01-imported.md       # 标准化后的脚本
    │       └── ep02-imported.md
    │
    ├── script_analysis/               # Step 2: 脚本分析
    │   ├── ep01_segmentation_latest.json
    │   ├── ep01_hook_latest.json      # 仅ep01有Hook
    │   ├── ep02_segmentation_latest.json
    │   └── history/                   # 历史版本
    │       ├── ep01_segmentation_v20260211_100000.json
    │       └── ...
    │
    ├── novel_analysis/                # Step 3: 小说分析
    │   ├── chapter_001_segmentation_latest.json
    │   ├── chapter_001_annotation_latest.json
    │   ├── chapter_002_segmentation_latest.json
    │   ├── chapter_002_annotation_latest.json
    │   ├── system_catalog_latest.json
    │   └── history/                   # 历史版本
    │       ├── chapter_001_segmentation_v20260211_100000.json
    │       └── ...
    │
    └── alignment/                     # Step 4: 对齐分析
        ├── chapter_001_ep01_alignment_latest.json
        ├── chapter_002_ep02_alignment_latest.json
        └── history/                   # 历史版本
            ├── chapter_001_ep01_alignment_v20260212_080000.json
            └── ...
```

---

### 项目元数据 (meta.json)

**位置**: `data/projects/{project_id}/meta.json`

**结构**:
```json
{
  "project_id": "project_001",
  "name": "序列公路求生",
  "description": "末日升级题材",
  "created_at": "2026-02-10T10:00:00Z",
  "updated_at": "2026-02-12T08:30:00Z",
  "status": "completed",
  
  "sources": {
    "has_novel": true,
    "has_script": true,
    "novel_files": ["序列公路求生.txt"],
    "script_files": ["ep01.srt", "ep02.srt"],
    "novel_chapters": 50,
    "script_episodes": 5
  },
  
  "workflow_stages": {
    "import": {
      "status": "completed",
      "updated_at": "2026-02-10T10:30:00Z"
    },
    "metadata": {
      "status": "completed",
      "updated_at": "2026-02-10T11:00:00Z"
    },
    "segmentation": {
      "status": "completed",
      "novel_progress": 50,
      "novel_total": 50,
      "script_progress": 5,
      "script_total": 5,
      "updated_at": "2026-02-11T14:00:00Z"
    },
    "annotation": {
      "status": "running",
      "novel_progress": 30,
      "novel_total": 50,
      "updated_at": "2026-02-12T08:30:00Z"
    },
    "alignment": {
      "status": "pending"
    }
  }
}
```

**Schema**: `src/core/schemas_project.py::ProjectV2`

---

### 章节数据 (chapters.json)

**位置**: `data/projects/{project_id}/analyst/import/novel/chapters.json`

**结构**:
```json
[
  {
    "id": "chapter_001",
    "index": 1,
    "title": "第一章 末日降临",
    "start_line": 1,
    "end_line": 150,
    "char_count": 3500,
    "has_segmentation": true,
    "has_annotation": true
  },
  {
    "id": "chapter_002",
    "index": 2,
    "title": "第二章 系统觉醒",
    "start_line": 151,
    "end_line": 300,
    "char_count": 3200,
    "has_segmentation": true,
    "has_annotation": false
  }
]
```

**Schema**: `src/core/schemas_novel/basic.py::ChapterInfo`

---

### 分段结果 (chapter_*_segmentation_latest.json)

**位置**: `data/projects/{project_id}/analyst/novel_analysis/chapter_001_segmentation_latest.json`

**结构**:
```json
{
  "chapter_id": "chapter_001",
  "chapter_title": "第一章 末日降临",
  "segmentation_version": "v3_twopass",
  "llm_provider": "claude-sonnet-4-5",
  "created_at": "2026-02-11T10:00:00Z",
  
  "paragraphs": [
    {
      "id": "p001",
      "index": 1,
      "class_type": "B",
      "title": "收音机播报上沪沦陷",
      "content": "沪市电台播音员...",
      "start_line": 1,
      "end_line": 5,
      "char_count": 120,
      "functional_tags": ["情节推进", "世界观构建"]
    },
    {
      "id": "p002",
      "index": 2,
      "class_type": "A",
      "title": "诡异爆发背景说明",
      "content": "三天前，全球爆发...",
      "start_line": 6,
      "end_line": 10,
      "char_count": 200,
      "functional_tags": ["世界观构建", "背景铺垫"]
    }
  ],
  
  "stats": {
    "total_paragraphs": 11,
    "class_distribution": {
      "A": 3,
      "B": 7,
      "C": 1
    }
  }
}
```

**Schema**: `src/core/schemas_novel/segmentation.py::SegmentationResult`

---

### 标注结果 (chapter_*_annotation_latest.json)

**位置**: `data/projects/{project_id}/analyst/novel_analysis/chapter_001_annotation_latest.json`

**结构**:
```json
{
  "chapter_id": "chapter_001",
  "segmentation_input": "chapter_001_v20260211_100000",
  "annotation_version": "v2_twopass",
  "llm_provider": "claude-sonnet-4-5",
  "created_at": "2026-02-11T12:00:00Z",
  
  "event_timeline": {
    "events": [
      {
        "id": "event_001",
        "event_summary": "主角听到收音机播报，得知上沪沦陷",
        "event_type": "信息获取",
        "participants": ["主角"],
        "location": "小出租屋",
        "time_description": "末日第三天早晨",
        "source_paragraphs": ["p001", "p002"],
        "importance": "high"
      }
    ]
  },
  
  "setting_correlation": {
    "settings": [
      {
        "paragraph_id": "p002",
        "setting_type": "世界观",
        "setting_content": "诡异爆发导致人类变异",
        "correlation_type": "BF",
        "related_events": ["event_001"]
      }
    ]
  },
  
  "knowledge_base": {
    "worldview": ["诡异爆发", "人类变异"],
    "characters": ["主角-林默"],
    "systems": ["生存系统"]
  }
}
```

**Schema**: `src/core/schemas_novel/annotation.py::AnnotatedChapter`

---

### 系统目录 (system_catalog_latest.json)

**位置**: `data/projects/{project_id}/analyst/novel_analysis/system_catalog_latest.json`

**结构**:
```json
{
  "project_id": "project_001",
  "version": "v1",
  "created_at": "2026-02-11T14:00:00Z",
  "updated_at": "2026-02-12T08:00:00Z",
  
  "categories": [
    {
      "id": "SC001",
      "name": "角色与生物",
      "description": "主角、配角、诡异生物",
      "elements": [
        {
          "id": "SC001-001",
          "name": "林默",
          "type": "主角",
          "first_appearance": "chapter_001",
          "description": "末日求生者，拥有生存系统"
        }
      ]
    },
    {
      "id": "SC002",
      "name": "物品与道具",
      "description": "关键物品、武器、消耗品",
      "elements": [
        {
          "id": "SC002-001",
          "name": "改装弩箭",
          "type": "武器",
          "first_appearance": "chapter_003",
          "description": "主角自制的远程武器"
        }
      ]
    }
  ]
}
```

**Schema**: `src/core/schemas_novel/system.py::SystemCatalog`

---

## 🔄 数据流转（Phase I Analyst Workflow）

### Step 1: Import 导入与标准化

```
外部文件上传
    ↓
raw/novel/novel.txt
raw/script/ep01.srt
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
analyst/script_analysis/ep01_hook_latest.json (仅ep01)
```

### Step 3: Novel Analysis 小说分析

```
analyst/import/novel/chapters.json (取文件)
analyst/import/novel/novel-imported.md (取文件)
    ↓ NovelSegmenter (并行处理各章节)
analyst/novel_analysis/chapter_001_segmentation_latest.json
    ↓ NovelAnnotator (并行处理各章节)
analyst/novel_analysis/chapter_001_annotation_latest.json
    ↓ NovelSystemDetector (逐章处理)
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

---

## 📝 命名规范

### 项目ID
- 格式: `project_{number}`
- 示例: `project_001`, `project_002`

### 章节ID
- 格式: `chapter_{number}`
- 示例: `chapter_001`, `chapter_050`

### 集数ID
- 格式: `ep{number}`
- 示例: `ep01`, `ep10`

### 段落ID
- 格式: `p{number}`
- 示例: `p001`, `p012`

### 事件ID
- 格式: `event_{number}`
- 示例: `event_001`, `event_030`

### 系统元素ID
- 格式: `{CategoryID}-{number}`
- 示例: `SC001-001`, `SC002-015`

---

## 🎯 工作流状态管理

### 状态值

| 状态 | 说明 |
|------|------|
| `pending` | 等待执行 |
| `running` | 执行中 |
| `completed` | 已完成 |
| `failed` | 执行失败 |
| `cancelled` | 已取消 |

### 更新机制

**后端更新**:
```python
from src.core.project_manager_v2 import ProjectManagerV2
pm = ProjectManagerV2()

# 更新工作流状态
pm.update_workflow_stage(
    project_id="project_001",
    stage="segmentation",
    status="running",
    metadata={
        "novel_progress": 10,
        "novel_total": 50
    }
)
```

**前端轮询**:
```typescript
// 每2秒轮询一次
setInterval(async () => {
  const status = await fetch(`/api/v2/projects/${projectId}/preprocess-status`);
  updateUI(status);
}, 2000);
```

---

## 🔧 错误恢复机制

### 自动重试

**配置**:
```python
RetryConfig(
    max_retries=3,
    retry_delay=5,  # 秒
    exponential_backoff=True
)
```

**重试策略**:
- LLM调用失败 → 自动重试3次
- 文件读取失败 → 立即失败（不重试）
- 网络超时 → 指数退避重试

### 断点续传

工作流支持断点续传：
```python
# 检查哪些章节已处理
completed_chapters = get_completed_chapters(project_id)

# 只处理未完成的章节
remaining_chapters = [ch for ch in all_chapters if ch not in completed_chapters]
```

---

## 📊 成本估算

### Novel处理成本（50章）

| 步骤 | LLM | 成本/章 | 总成本 |
|------|-----|---------|--------|
| 导入 | ❌ | $0 | $0 |
| 元数据提取 | DeepSeek | $0.01 | $0.50 |
| 章节检测 | ❌ | $0 | $0 |
| 分段 | Claude | $0.06 | $3.00 |
| 标注 | Claude | $0.08 | $4.00 |
| 系统检测 | Claude | $0.02 | $1.00 |
| **总计** | - | **$0.17** | **$8.50** |

### Script处理成本（5集）

| 步骤 | LLM | 成本/集 | 总成本 |
|------|-----|---------|--------|
| 导入 | ❌ | $0 | $0 |
| 文本提取 | DeepSeek | $0.02 | $0.10 |
| Hook检测 | Claude | $0.05 | $0.05 (仅ep01) |
| 分段 | DeepSeek | $0.03 | $0.15 |
| **总计** | - | **$0.05** | **$0.30** |

### 完整项目成本

- Novel: $8.50
- Script: $0.30
- Alignment: ~$2.00
- **项目总成本**: ~$11

---

**维护说明**: 
- 修改工作流时，请同步更新本文档
- 修改数据结构时，请更新对应Schema路径
- 新增工作流时，请添加完整说明

**最后更新**: 2026-02-13  
**工作流数量**: 3个核心工作流  
**重大变更**: 
- 数据存储统一到 `analyst/` 目录下
- `raw/srt/` 改名为 `raw/script/`
- 去除 `processed/` 和顶层 `alignment/` 文件夹
- 采用四步工作流: import → script_analysis → novel_analysis → alignment
