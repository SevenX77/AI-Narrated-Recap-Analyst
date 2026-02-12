# 数据流与目录结构重新设计

**最后更新**: 2026-02-12  
**设计原则**: 与前端步骤完全对应，数据流清晰可追溯

---

## 🎯 设计理念

### 核心原则

1. **与前端步骤1:1对应**：每个前端步骤对应一个数据目录
2. **按Phase分层**：第一级按Phase（Raw, Analyst, ...），第二级按Step
3. **输入输出明确**：每一步的输入来源和输出位置都清晰标注
4. **数据流可追溯**：可以清楚看到数据如何从Raw流向最终结果

---

## 📊 新目录结构

```
data/projects/{project_id}/
│
├── meta.json                           # 项目元数据和状态
│
├── raw/                                # 🔵 Level 1: 原始数据（用户上传）
│   ├── novel/
│   │   └── {original_filename}.txt
│   └── script/
│       ├── ep01.srt
│       ├── ep02.srt
│       └── ...
│
├── analyst/                            # 🟢 Level 1: Phase I Analyst Agent
│   │
│   ├── import/                         # 📁 Step 1: Import（预处理结果）
│   │   ├── novel/
│   │   │   ├── standardized.txt
│   │   │   ├── metadata.json
│   │   │   └── chapters.json
│   │   └── script/
│   │       ├── ep01.json
│   │       ├── ep01-imported.md
│   │       ├── ep02.json
│   │       ├── ep02-imported.md
│   │       └── episodes.json
│   │
│   ├── script_analysis/                 # 📁 Step 2: Script Analysis（深度分析）
│   │   ├── ep01_segmentation_latest.json
│   │   ├── ep01_hook_latest.json
│   │   ├── ep01_validation_latest.json
│   │   ├── ep02_segmentation_latest.json
│   │   └── history/
│   │       ├── ep01_segmentation_v20260212_180000.json
│   │       └── ...
│   │
│   ├── novel_analysis/                  # 📁 Step 3: Novel Analysis（深度分析）
│   │   ├── chapter_001_segmentation_latest.json
│   │   ├── chapter_001_annotation_latest.json
│   │   ├── chapter_002_segmentation_latest.json
│   │   ├── system_catalog_latest.json
│   │   └── history/
│   │       └── ...
│   │
│   └── alignment/                      # 📁 Step 4: Alignment（对齐分析）
│       ├── chapter_001_ep01_alignment_latest.json
│       ├── chapter_002_ep02_alignment_latest.json
│       └── history/
│           └── ...
│
└── reports/                            # 📝 人类可读报告
    ├── quality_report.html
    ├── alignment_report.md
    └── ...
```

---

## 🔄 数据流详解

### 整体数据流

```
用户上传
    ↓
raw/
    ↓
analyst/import/         (Step 1: 自动预处理)
    ↓
analyst/script_analysis/ (Step 2: 用户启动)
    ↓
analyst/novel_analysis/  (Step 3: 用户启动)
    ↓
analyst/alignment/      (Step 4: 用户启动)
    ↓
reports/
```

---

## 📋 Step 1: Import - 文件导入与标准化

### 输入准备

**用户操作**：上传文件

**输入文件**：
```
raw/
├── novel/
│   └── 序列公路求生：我在末日升级物资.txt    # ✅ 用户上传
└── script/
    ├── ep01.srt                              # ✅ 用户上传
    ├── ep02.srt
    └── ...
```

**如何获得**：
- 前端拖拽上传或点击选择
- API: `POST /api/v2/projects/{project_id}/files`
- 文件保存到 `raw/` 目录（按类型自动分类）

---

### 处理过程

**触发方式**：文件上传后**自动触发**

**后端服务**：`PreprocessService`（异步后台任务）

**处理流程**：

#### Novel预处理
```python
raw/novel/序列公路求生.txt
    ↓ NovelImporter
    ├─ 编码检测 (UTF-8)
    ├─ 文本规范化
    └─ 保存: analyst/import/novel/standardized.txt
    ↓ NovelMetadataExtractor
    ├─ 提取标题、作者、字数
    └─ 保存: analyst/import/novel/metadata.json
    ↓ NovelChapterDetector
    ├─ 章节边界检测
    ├─ 提取章节标题
    └─ 保存: analyst/import/novel/chapters.json
```

#### Script预处理
```python
raw/script/ep01.srt
    ↓ SrtImporter
    ├─ 解析SRT格式
    ├─ 验证时间轴
    └─ 保存: analyst/import/script/ep01.json
    ↓ SrtTextExtractor
    ├─ 提取纯文本
    ├─ LLM修复标点
    └─ 保存: analyst/import/script/ep01-imported.md
```

---

### 输出结果

**输出位置**：`analyst/import/`

**文件结构**：
```
analyst/import/
├── novel/
│   ├── standardized.txt              # ✅ 规范化文本（UTF-8）
│   │   末日降临的那一天，苏烈正驾驶着卡车...
│   │
│   ├── metadata.json                 # ✅ 元数据
│   │   {
│   │     "title": "序列公路求生：我在末日升级物资",
│   │     "author": "末哥超凡",
│   │     "total_chars": 500000,
│   │     "chapter_count": 50,
│   │     "encoding": "UTF-8",
│   │     "created_at": "2026-02-12T18:00:00"
│   │   }
│   │
│   └── chapters.json                 # ✅ 章节列表
│       [
│         {
│           "id": "chapter_001",
│           "title": "第一章 末日降临",
│           "start_line": 1,
│           "end_line": 150,
│           "char_count": 3500
│         },
│         ...
│       ]
│
└── script/
    ├── ep01.json                     # ✅ SRT解析结果
    │   {
    │     "episode_id": "ep01",
    │     "total_entries": 146,
    │     "total_duration": 180.5,
    │     "entries": [
    │       {
    │         "index": 1,
    │         "start_time": "00:00:00,000",
    │         "end_time": "00:00:02,500",
    │         "text": "末日降临公路求生"
    │       },
    │       ...
    │     ]
    │   }
    │
    ├── ep01-imported.md              # ✅ 提取的纯文本
    │   末日降临，公路求生。
    │   苏烈独自驾驶着一辆破旧的卡车...
    │
    ├── ep02.json
    ├── ep02-imported.md
    │
    └── episodes.json                 # ✅ 集数汇总
        [
          {
            "episode_id": "ep01",
            "name": "第一集",
            "srt_file": "ep01.srt",
            "total_entries": 146,
            "duration": 180.5,
            "status": "imported",
            "imported_at": "2026-02-12T18:00:00"
          },
          ...
        ]
```

---

### 状态更新

**meta.json 更新**：
```json
{
  "phase_i_analyst": {
    "step_1_import": {
      "status": "completed",
      "novel_imported": true,
      "novel_chapter_count": 50,
      "script_imported": true,
      "script_episodes": ["ep01", "ep02", "ep03", "ep04", "ep05"],
      "completed_at": "2026-02-12T18:01:30"
    }
  }
}
```

---

### 衔接到下一步

**Step 2 (Script Analysis) 需要**：
- ✅ `analyst/import/script/ep01.json` (SRT解析结果)
- ✅ `analyst/import/script/ep01-imported.md` (提取的文本)
- ✅ `analyst/import/novel/metadata.json` (可选，用于Hook检测)

**Step 3 (Novel Analysis) 需要**：
- ✅ `analyst/import/novel/standardized.txt` (规范化文本)
- ✅ `analyst/import/novel/chapters.json` (章节列表)

---

## 📋 Step 2: Script Analysis - 脚本深度分析

### 输入准备

**前置条件**：Step 1 已完成

**输入文件**：
```
analyst/import/script/
├── ep01.json                         # ✅ 来自 Step 1
├── ep01-imported.md                  # ✅ 来自 Step 1
├── ep02.json
├── ep02-imported.md
└── episodes.json

analyst/import/novel/
└── metadata.json                     # ✅ 可选，用于Hook检测
```

**如何获得**：
- 自动读取：`analyst/import/script/` 目录
- 代码示例：
  ```python
  srt_entries = load_json(f"analyst/import/script/{episode_id}.json")
  extracted_text = load_text(f"analyst/import/script/{episode_id}-imported.md")
  ```

---

### 处理过程

**触发方式**：用户点击 "Start Analysis"

**后端服务**：`ScriptProcessingWorkflow`

**处理流程**（单集）：
```python
读取 analyst/import/script/ep01.json
读取 analyst/import/script/ep01-imported.md
    ↓
Phase 1: Hook检测（仅ep01）
    └─ HookDetector.execute()
    └─ 保存: analyst/script_analysis/ep01_hook_latest.json
    ↓
Phase 2: 语义分段 + ABC分类
    └─ ScriptSegmenter.execute()
    └─ 保存: analyst/script_analysis/ep01_segmentation_latest.json
    ↓
Phase 3: 质量验证
    └─ ScriptValidator.execute()
    └─ 保存: analyst/script_analysis/ep01_validation_latest.json
```

---

### 输出结果

**输出位置**：`analyst/script_analysis/`

**文件结构**：
```
analyst/script_analysis/
├── ep01_hook_latest.json             # ✅ Hook检测（ep01专属）
│   {
│     "episode_id": "ep01",
│     "has_hook": true,
│     "hook_end_time": 45.6,
│     "body_start_index": 15,
│     "confidence": 0.92,
│     "hook_segments": [
│       {
│         "segment_id": "hook_001",
│         "content": "末日降临，公路求生...",
│         "start_time": 0.0,
│         "end_time": 10.5
│       }
│     ]
│   }
│
├── ep01_segmentation_latest.json     # ✅ 分段结果
│   {
│     "episode_id": "ep01",
│     "total_segments": 12,
│     "segments": [
│       {
│         "segment_id": "seg001",
│         "content": "末日降临，公路求生。",
│         "category": "A",           // A=设定, B=事件, C=系统
│         "start_time": 0.0,
│         "end_time": 2.5,
│         "srt_range": [1, 1]
│       },
│       {
│         "segment_id": "seg002",
│         "content": "苏烈独自驾驶着一辆破旧的卡车...",
│         "category": "B",
│         "start_time": 2.5,
│         "end_time": 6.8,
│         "srt_range": [2, 3]
│       }
│     ],
│     "metadata": {
│       "segmented_at": "2026-02-12T19:00:00",
│       "tool": "ScriptSegmenter",
│       "llm_provider": "deepseek",
│       "total_cost": 0.08
│     }
│   }
│
├── ep01_validation_latest.json       # ✅ 质量报告
│   {
│     "episode_id": "ep01",
│     "quality_score": 85,
│     "issues": [],
│     "suggestions": ["..."]
│   }
│
├── ep02_segmentation_latest.json
├── ep02_validation_latest.json
│
└── history/                          # 📦 版本历史
    ├── ep01_hook_v20260212_190000.json
    ├── ep01_segmentation_v20260212_190100.json
    └── ...
```

---

### 状态更新

**meta.json 更新**：
```json
{
  "phase_i_analyst": {
    "step_2_script": {
      "status": "completed",
      "total_episodes": 5,
      "completed_episodes": 5,
      "episodes_status": {
        "ep01": {
          "status": "completed",
          "has_hook": true,
          "quality_score": 85,
          "total_segments": 12,
          "processed_at": "2026-02-12T19:05:00"
        },
        "ep02": {
          "status": "completed",
          "has_hook": false,
          "quality_score": 82,
          "total_segments": 10
        }
      },
      "completed_at": "2026-02-12T19:30:00"
    }
  }
}
```

---

### 衔接到下一步

**Step 4 (Alignment) 需要**：
- ✅ `analyst/script_analysis/ep01_segmentation_latest.json`
- ✅ `analyst/script_analysis/ep01_hook_latest.json` (如果有Hook)

---

## 📋 Step 3: Novel Analysis - 小说深度分析

### 输入准备

**前置条件**：Step 1 已完成

**输入文件**：
```
analyst/import/novel/
├── standardized.txt                  # ✅ 来自 Step 1
└── chapters.json                     # ✅ 来自 Step 1
```

**如何获得**：
```python
standardized_text = load_text(f"analyst/import/novel/standardized.txt")
chapters = load_json(f"analyst/import/novel/chapters.json")

# 提取单章文本
chapter_text = extract_chapter_text(
    standardized_text,
    chapter["start_line"],
    chapter["end_line"]
)
```

---

### 处理过程

**触发方式**：用户点击 "Start Analysis"

**后端服务**：`NovelProcessingWorkflow`

**处理流程**（单章）：
```python
读取 analyst/import/novel/standardized.txt
读取 analyst/import/novel/chapters.json
提取章节文本
    ↓
Phase 1: 章节分段（Two-Pass）
    └─ NovelSegmenter.execute()
    └─ 保存: analyst/novel_analysis/chapter_001_segmentation_latest.json
    ↓
Phase 2: 章节标注（Three-Pass）
    └─ NovelAnnotator.execute()
    └─ 保存: analyst/novel_analysis/chapter_001_annotation_latest.json
    ↓
Phase 3: 质量验证
    └─ NovelValidator.execute()
    └─ 保存: analyst/novel_analysis/chapter_001_validation_latest.json
    ↓
[所有章节完成后]
Phase 4: 系统元素分析（全书一次）
    └─ NovelSystemAnalyzer.execute()
    └─ 保存: analyst/novel_analysis/system_catalog_latest.json
```

---

### 输出结果

**输出位置**：`analyst/novel_analysis/`

**文件结构**：
```
analyst/novel_analysis/
├── chapter_001_segmentation_latest.json    # ✅ 分段结果
│   {
│     "chapter_id": "chapter_001",
│     "chapter_title": "第一章 末日降临",
│     "total_paragraphs": 50,
│     "paragraphs": [
│       {
│         "paragraph_id": "p001",
│         "content": "末日降临的那一天，苏烈正驾驶着卡车...",
│         "category": "narrative",
│         "start_line": 1,
│         "end_line": 1
│       },
│       {
│         "paragraph_id": "p002",
│         "content": "【系统提示】序列公路系统激活...",
│         "category": "system",
│         "start_line": 2,
│         "end_line": 2
│       }
│     ],
│     "metadata": {
│       "segmented_at": "2026-02-12T20:00:00",
│       "tool": "NovelSegmenter",
│       "llm_provider": "claude",
│       "total_cost": 0.10
│     }
│   }
│
├── chapter_001_annotation_latest.json      # ✅ 标注结果
│   {
│     "chapter_id": "chapter_001",
│     "event_timeline": [
│       {
│         "event_id": "ev001",
│         "description": "苏烈驾车行驶在高速公路",
│         "timestamp": "Day 1, 10:00",
│         "location": "高速公路",
│         "participants": ["苏烈"],
│         "related_paragraphs": ["p001", "p003"]
│       }
│     ],
│     "setting_library": [
│       {
│         "setting_id": "set001",
│         "type": "world_rule",
│         "content": "序列公路系统规则",
│         "related_paragraphs": ["p002"]
│       }
│     ],
│     "metadata": {
│       "annotated_at": "2026-02-12T20:05:00",
│       "tool": "NovelAnnotator",
│       "llm_provider": "claude",
│       "total_cost": 0.12
│     }
│   }
│
├── chapter_001_validation_latest.json
│
├── chapter_002_segmentation_latest.json
├── chapter_002_annotation_latest.json
│
├── system_catalog_latest.json              # ✅ 系统目录（全书）
│   {
│     "system_name": "序列公路求生系统",
│     "categories": {
│       "player_stats": [
│         {
│           "name": "生命值",
│           "description": "玩家当前生命值",
│           "first_appearance": "chapter_001"
│         }
│       ],
│       "items": [...],
│       "skills": [...]
│     },
│     "metadata": {
│       "analyzed_at": "2026-02-12T20:30:00",
│       "total_chapters_analyzed": 10,
│       "tool": "NovelSystemAnalyzer"
│     }
│   }
│
└── history/                                # 📦 版本历史
    └── ...
```

---

### 状态更新

**meta.json 更新**：
```json
{
  "phase_i_analyst": {
    "step_3_novel": {
      "status": "completed",
      "total_chapters": 10,
      "completed_chapters": 10,
      "total_events": 150,
      "total_settings": 80,
      "total_system_elements": 45,
      "novel_steps": {
        "chapter_001": {
          "status": "completed",
          "quality_score": 88,
          "total_paragraphs": 50,
          "total_events": 15,
          "processed_at": "2026-02-12T20:05:00"
        }
      },
      "completed_at": "2026-02-12T21:00:00"
    }
  }
}
```

---

### 衔接到下一步

**Step 4 (Alignment) 需要**：
- ✅ `analyst/novel_analysis/chapter_001_annotation_latest.json`
- ✅ `analyst/novel_analysis/system_catalog_latest.json` (可选)

---

## 📋 Step 4: Alignment - 对齐分析

### 输入准备

**前置条件**：
- Step 2 (Script Analysis) 已完成
- Step 3 (Novel Analysis) 已完成

**输入文件**：
```
analyst/novel_analysis/
├── chapter_001_annotation_latest.json    # ✅ 来自 Step 3
└── system_catalog_latest.json            # ✅ 来自 Step 3

analyst/script_analysis/
├── ep01_segmentation_latest.json         # ✅ 来自 Step 2
└── ep01_hook_latest.json                 # ✅ 来自 Step 2（如果有）
```

**如何获得**：
```python
novel_annotation = artifact_manager.load_latest_artifact(
    artifact_type="chapter_001_annotation",
    base_dir="analyst/NovelAnalysis"
)

script_segmentation = artifact_manager.load_latest_artifact(
    artifact_type="ep01_segmentation",
    base_dir="analyst/ScriptAnalysis"
)
```

---

### 处理过程

**触发方式**：用户点击 "Start Alignment"

**后端服务**：`AlignmentWorkflow` 🚧

**处理流程**：
```python
读取 analyst/novel_analysis/chapter_001_annotation_latest.json
读取 analyst/script_analysis/ep01_segmentation_latest.json
读取 analyst/script_analysis/ep01_hook_latest.json (可选)
    ↓
Phase 1: 数据验证
    ├─ 检查数据完整性
    └─ 验证依赖关系
    ↓
Phase 2: Hook-Body分离（如果有Hook）
    ├─ Hook部分 → 与Novel简介对齐
    └─ Body部分 → 与Novel章节对齐
    ↓
Phase 3: 句子级对齐
    └─ NovelScriptAligner.execute()
    └─ 输出: 段落映射关系
    ↓
Phase 4: ABC类型匹配分析
    └─ 分析类型一致性
    ↓
Phase 5: 覆盖率分析
    └─ 计算事件/设定覆盖率
    ↓
保存: analyst/alignment/chapter_001_ep01_alignment_latest.json
```

---

### 输出结果

**输出位置**：`analyst/alignment/`

**文件结构**：
```
analyst/alignment/
├── chapter_001_ep01_alignment_latest.json    # ✅ 对齐结果
│   {
│     "chapter_id": "chapter_001",
│     "episode_id": "ep01",
│     "has_hook": true,
│     "alignments": [
│       {
│         "script_segment_id": "seg001",
│         "novel_paragraph_id": null,
│         "alignment_type": "hook",
│         "confidence": 0.0,
│         "note": "Hook部分，不对齐"
│       },
│       {
│         "script_segment_id": "seg002",
│         "novel_paragraph_id": "p001",
│         "alignment_type": "event",
│         "confidence": 0.92,
│         "rewrite_strategy": "paraphrase"
│       }
│     ],
│     "coverage": {
│       "event_coverage": 0.95,
│       "setting_coverage": 0.85,
│       "total_novel_paragraphs": 50,
│       "total_script_segments": 12,
│       "aligned_paragraphs": 47,
│       "aligned_segments": 11
│     },
│     "type_matching": {
│       "A_to_A": 2,
│       "B_to_B": 8,
│       "C_to_C": 1,
│       "mismatches": 0
│     },
│     "metadata": {
│       "aligned_at": "2026-02-12T22:00:00",
│       "tool": "NovelScriptAligner",
│       "llm_provider": "claude",
│       "total_cost": 0.10
│     }
│   }
│
├── chapter_002_ep02_alignment_latest.json
│
└── history/
    └── ...
```

---

### 状态更新

**meta.json 更新**：
```json
{
  "phase_i_analyst": {
    "step_4_alignment": {
      "status": "completed",
      "total_alignments": 10,
      "average_confidence": 0.89,
      "event_coverage_rate": 0.92,
      "setting_coverage_rate": 0.85,
      "alignment_pairs": [
        {
          "chapter_id": "chapter_001",
          "episode_id": "ep01",
          "quality_score": 90
        }
      ],
      "completed_at": "2026-02-12T23:00:00"
    },
    "overall_status": "completed",
    "overall_progress": 100.0,
    "completed_at": "2026-02-12T23:00:00"
  }
}
```

---

### 最终输出

**reports/ 目录**：
```
reports/
├── phase_i_summary.html              # Phase I 总结报告
├── quality_report.html               # 质量评分报告
├── alignment_report.html             # 对齐分析报告
└── system_catalog_report.md          # 系统元素报告
```

---

## 📊 完整数据流图

```
┌─────────────────────────────────────────────────────────────────┐
│ 用户操作：上传文件                                               │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ raw/ (原始文件)                                                  │
│  ├─ novel/序列公路求生.txt                                       │
│  └─ script/ep01.srt, ep02.srt, ...                             │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓ PreprocessService (自动)
┌─────────────────────────────────────────────────────────────────┐
│ analyst/import/ (Step 1输出)                                    │
│  ├─ novel/                                                       │
│  │   ├─ standardized.txt                                        │
│  │   ├─ metadata.json                                           │
│  │   └─ chapters.json                                           │
│  └─ script/                                                      │
│      ├─ ep01.json, ep01-imported.md                            │
│      └─ episodes.json                                           │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │ 用户点击 "Start Analysis"      │
        └───────────────┬───────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌───────────────────────┐   ┌───────────────────────┐
│ ScriptProcessing      │   │ NovelProcessing       │
│ Workflow              │   │ Workflow              │
└───────────┬───────────┘   └───────────┬───────────┘
            ↓                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ analyst/script_analysis/ (Step 2输出)                            │
│  ├─ ep01_hook_latest.json                                       │
│  ├─ ep01_segmentation_latest.json                               │
│  └─ ep01_validation_latest.json                                 │
└─────────────────────────────────────────────────────────────────┘
            │
┌─────────────────────────────────────────────────────────────────┐
│ analyst/novel_analysis/ (Step 3输出)                             │
│  ├─ chapter_001_segmentation_latest.json                        │
│  ├─ chapter_001_annotation_latest.json                          │
│  └─ system_catalog_latest.json                                  │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
        ┌───────────────────────────────┐
        │ 用户点击 "Start Alignment"     │
        └───────────────┬───────────────┘
                        ↓
        ┌───────────────────────────────┐
        │ AlignmentWorkflow             │
        └───────────────┬───────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ analyst/alignment/ (Step 4输出)                                 │
│  └─ chapter_001_ep01_alignment_latest.json                      │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ reports/ (人类可读报告)                                          │
│  ├─ phase_i_summary.html                                        │
│  ├─ quality_report.html                                         │
│  └─ alignment_report.html                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 数据衔接规则

### 规则1: 每个Step的输入来自上一个Step

| Step | 输入来源 | 输入文件 |
|------|---------|---------|
| Step 1 | raw/ | 用户上传的原始文件 |
| Step 2 | analyst/import/ | ep01.json, ep01-imported.md |
| Step 3 | analyst/import/ | standardized.txt, chapters.json |
| Step 4 | analyst/script_analysis/ + analyst/novel_analysis/ | 分段、标注结果 |

### 规则2: 文件命名与ID保持一致

```python
# Novel
chapter_id = "chapter_001"
→ analyst/import/novel/chapters.json (包含chapter_001)
→ analyst/novel_analysis/chapter_001_segmentation_latest.json
→ analyst/novel_analysis/chapter_001_annotation_latest.json
→ analyst/alignment/chapter_001_ep01_alignment_latest.json

# Script
episode_id = "ep01"
→ analyst/import/script/ep01.json
→ analyst/script_analysis/ep01_segmentation_latest.json
→ analyst/script_analysis/ep01_hook_latest.json
→ analyst/alignment/chapter_001_ep01_alignment_latest.json
```

### 规则3: 使用 ArtifactManager 管理版本

```python
# 保存（自动版本化）
artifact_manager.save_artifact(
    content=result,
    artifact_type="chapter_001_segmentation",
    base_dir="analyst/NovelAnalysis"
)
# 生成:
# - analyst/novel_analysis/chapter_001_segmentation_latest.json
# - analyst/novel_analysis/history/chapter_001_segmentation_v{timestamp}.json

# 读取（始终读取latest）
result = artifact_manager.load_latest_artifact(
    artifact_type="chapter_001_segmentation",
    base_dir="analyst/NovelAnalysis"
)
```

---

## 🔄 迁移计划

### 从旧结构迁移到新结构

```bash
# 迁移脚本
#!/bin/bash

PROJECT_DIR="data/projects/project_001"

# 1. 创建新目录结构
mkdir -p $PROJECT_DIR/analyst/import/novel
mkdir -p $PROJECT_DIR/analyst/import/script
mkdir -p $PROJECT_DIR/analyst/ScriptAnalysis
mkdir -p $PROJECT_DIR/analyst/NovelAnalysis
mkdir -p $PROJECT_DIR/analyst/Alignment

# 2. 迁移 processed/ → analyst/import/
if [ -d "$PROJECT_DIR/processed" ]; then
    cp -r $PROJECT_DIR/processed/novel/* $PROJECT_DIR/analyst/import/novel/
    cp -r $PROJECT_DIR/processed/script/* $PROJECT_DIR/analyst/import/script/
    mv $PROJECT_DIR/processed $PROJECT_DIR/processed.backup
fi

# 3. 迁移 analysis/ → analyst/{Step}/
if [ -d "$PROJECT_DIR/analysis" ]; then
    # 移动 script 相关文件到 script_analysis/
    cp -r $PROJECT_DIR/analysis/script/* $PROJECT_DIR/analyst/script_analysis/
    
    # 移动 novel 相关文件到 novel_analysis/
    cp -r $PROJECT_DIR/analysis/novel/* $PROJECT_DIR/analyst/novel_analysis/
    
    # 移动 alignment 文件到 alignment/
    cp -r $PROJECT_DIR/analysis/alignment/* $PROJECT_DIR/analyst/alignment/
    
    mv $PROJECT_DIR/analysis $PROJECT_DIR/analysis.backup
fi

# 4. 重命名 raw/ → raw/ (大写)
if [ -d "$PROJECT_DIR/raw" ]; then
    mv $PROJECT_DIR/raw $PROJECT_DIR/Raw
fi

# 5. 重命名 reports/ → reports/ (大写)
if [ -d "$PROJECT_DIR/reports" ]; then
    mv $PROJECT_DIR/reports $PROJECT_DIR/Reports
fi

echo "✅ Migration completed!"
```

---

## 📊 目录大小估算

| 目录 | 内容 | 大小估算（10章+10集） |
|------|------|---------------------|
| raw/ | 原始文件 | ~2MB (小说1.5MB + SRT 0.5MB) |
| analyst/import/ | 预处理结果 | ~3MB |
| analyst/script_analysis/ | 分段+Hook | ~1MB (含history ~5MB) |
| analyst/novel_analysis/ | 分段+标注 | ~5MB (含history ~25MB) |
| analyst/alignment/ | 对齐结果 | ~2MB (含history ~10MB) |
| reports/ | 报告 | ~1MB |
| **总计（不含history）** | | **~14MB** |
| **总计（含history）** | | **~54MB** |

---

## 📝 总结

### 新结构的优势

1. **与前端完全对应**：
   - raw/ → Step 1 → analyst/import/
   - Step 2 → analyst/script_analysis/
   - Step 3 → analyst/novel_analysis/
   - Step 4 → analyst/alignment/

2. **数据流清晰**：
   - 每一步的输入输出都有明确位置
   - 数据衔接规则简单明了

3. **易于扩展**：
   - 未来可以添加其他Phase（如 Generator/, Trainer/）
   - 每个Phase下可以添加更多Step

4. **版本化管理**：
   - 使用 ArtifactManager 统一管理
   - 保留历史版本，支持回滚

5. **命名统一**：
   - 大写目录名（raw/, analyst/, reports/）
   - 统一文件命名（chapter_001, ep01）

---

**最后更新**: 2026-02-12  
**下一步**: 实施目录迁移和代码更新
