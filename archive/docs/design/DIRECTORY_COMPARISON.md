# 新旧目录结构对比

**最后更新**: 2026-02-12  
**目的**: 对比新旧目录结构，明确改进点

---

## 📊 结构对比

### 旧结构（当前）

```
data/projects/project_001/
├── meta.json
├── raw/                           # 原始文件
│   ├── novel/
│   └── srt/
├── processed/                     # 预处理结果（混乱）
│   ├── novel/
│   └── script/
├── processing/                    # ❌ 与analysis重复
│   ├── novel/
│   └── script/
├── analysis/                      # 工具输出
│   ├── novel/
│   ├── script/
│   └── alignment/
└── reports/
```

**问题**：
- ❌ `processing/` 和 `analysis/` 职责重叠
- ❌ 目录命名不统一（小写）
- ❌ 与前端步骤不对应
- ❌ 数据流不清晰

---

### 新结构（推荐）⭐

```
data/projects/project_001/
├── meta.json
│
├── Raw/                           # 🔵 Level 1: 原始数据
│   ├── novel/
│   └── script/
│
├── Analyst/                       # 🟢 Level 1: Phase I
│   │
│   ├── Import/                    # 📁 Step 1: Import
│   │   ├── novel/
│   │   │   ├── standardized.txt
│   │   │   ├── metadata.json
│   │   │   └── chapters.json
│   │   └── script/
│   │       ├── ep01.json
│   │       ├── ep01-imported.md
│   │       └── episodes.json
│   │
│   ├── ScriptAnalysis/            # 📁 Step 2: Script Analysis
│   │   ├── ep01_segmentation_latest.json
│   │   ├── ep01_hook_latest.json
│   │   └── history/
│   │
│   ├── NovelAnalysis/             # 📁 Step 3: Novel Analysis
│   │   ├── chapter_001_segmentation_latest.json
│   │   ├── chapter_001_annotation_latest.json
│   │   └── history/
│   │
│   └── Alignment/                 # 📁 Step 4: Alignment
│       ├── chapter_001_ep01_alignment_latest.json
│       └── history/
│
└── Reports/                       # 📝 人类可读报告
```

**优势**：
- ✅ 与前端步骤1:1对应
- ✅ 目录命名统一（大写）
- ✅ 数据流清晰（Raw → Import → Analysis → Alignment）
- ✅ 删除冗余目录（processing/）
- ✅ 支持未来扩展（可添加其他Phase）

---

## 🔄 路径映射表

### 文件迁移对照

| 旧路径 | 新路径 | 说明 |
|--------|--------|------|
| `raw/` | `Raw/` | 改为大写 |
| `processed/novel/` | `Analyst/Import/novel/` | 预处理结果 |
| `processed/script/` | `Analyst/Import/script/` | 预处理结果 |
| `processing/novel/` | ❌ 删除，合并到 `Analyst/NovelAnalysis/` | 冗余目录 |
| `processing/script/` | ❌ 删除，合并到 `Analyst/ScriptAnalysis/` | 冗余目录 |
| `analysis/novel/` | `Analyst/NovelAnalysis/` | 改名+移动 |
| `analysis/script/` | `Analyst/ScriptAnalysis/` | 改名+移动 |
| `analysis/alignment/` | `Analyst/Alignment/` | 改名+移动 |
| `reports/` | `Reports/` | 改为大写 |

---

## 📋 数据流对比

### 旧数据流

```
用户上传
    ↓
raw/
    ↓
processed/ (预处理)
    ↓
processing/ (❌ 混乱)  ←→  analysis/ (❌ 职责不清)
    ↓
reports/
```

**问题**：
- processing/ 和 analysis/ 界限不清
- 不知道最新结果在哪里

---

### 新数据流 ⭐

```
用户上传
    ↓
Raw/ (原始文件)
    ↓
Analyst/Import/ (Step 1: 预处理)
    ↓
    ┌─────────────────────┬─────────────────────┐
    ↓                     ↓                     ↓
ScriptAnalysis/     NovelAnalysis/        (可并行)
(Step 2)            (Step 3)
    └─────────────────────┴─────────────────────┘
                          ↓
                    Alignment/
                    (Step 4)
                          ↓
                    Reports/
```

**优势**：
- ✅ 每一步位置明确
- ✅ 数据流向清晰
- ✅ 与前端步骤对应

---

## 🎯 前端步骤与目录对应

### 前端 UI

```typescript
// 前端路由
/project/{id}/workflow/step_1_import      → Analyst/Import/
/project/{id}/workflow/step_2_script      → Analyst/ScriptAnalysis/
/project/{id}/workflow/step_3_novel       → Analyst/NovelAnalysis/
/project/{id}/workflow/step_4_alignment   → Analyst/Alignment/
```

### API 端点

```python
# 旧API（混乱）
GET /api/v2/projects/{id}/processed/novel/metadata.json
GET /api/v2/projects/{id}/analysis/novel/chapter_001.json

# 新API（清晰）⭐
GET /api/v2/projects/{id}/analyst/import/novel/metadata.json
GET /api/v2/projects/{id}/analyst/novel-analysis/chapter_001_segmentation_latest.json
```

---

## 📂 具体文件对比

### Novel处理结果

#### 旧结构
```
processed/novel/
├── standardized.txt
├── metadata.json
└── chapters.json

processing/novel/
├── step4_segmentation/
│   └── chapter_001.json
└── step5_annotation/
    └── chapter_001.json

analysis/novel/
├── chapter_001_segmentation_latest.json
└── chapter_001_annotation_latest.json
```

**问题**：
- 分段结果在3个地方（processing/, analysis/）
- 命名不统一（step4_segmentation vs chapter_001_segmentation）

#### 新结构 ⭐
```
Analyst/
├── Import/novel/                          # Step 1输出
│   ├── standardized.txt
│   ├── metadata.json
│   └── chapters.json
│
└── NovelAnalysis/                         # Step 3输出
    ├── chapter_001_segmentation_latest.json
    ├── chapter_001_annotation_latest.json
    └── history/
        ├── chapter_001_segmentation_v20260212_180000.json
        └── chapter_001_annotation_v20260212_180100.json
```

**优势**：
- ✅ 所有结果在一个地方
- ✅ 命名统一
- ✅ 版本化管理

---

### Script处理结果

#### 旧结构
```
processed/script/
├── ep01.json
├── ep01-imported.md
└── episodes.json

processing/script/
└── ep01_segmentation.json

analysis/script/
├── ep01_segmentation_latest.json
└── ep01_hook_latest.json
```

**问题**：
- 分段结果在2个地方（processing/, analysis/）
- 命名不一致

#### 新结构 ⭐
```
Analyst/
├── Import/script/                         # Step 1输出
│   ├── ep01.json
│   ├── ep01-imported.md
│   └── episodes.json
│
└── ScriptAnalysis/                        # Step 2输出
    ├── ep01_segmentation_latest.json
    ├── ep01_hook_latest.json
    ├── ep01_validation_latest.json
    └── history/
        └── ...
```

**优势**：
- ✅ 清晰分层：预处理 vs 深度分析
- ✅ 所有深度分析结果在一起
- ✅ 版本化管理

---

## 🔧 代码更新对比

### 读取文件路径

#### 旧代码
```python
# ❌ 路径混乱
novel_meta = load_json(f"{project_dir}/processed/novel/metadata.json")
chapters = load_json(f"{project_dir}/processed/novel/chapters.json")
segmentation = load_json(f"{project_dir}/processing/novel/step4_segmentation/chapter_001.json")
# 或
segmentation = load_json(f"{project_dir}/analysis/novel/chapter_001_segmentation_latest.json")
```

#### 新代码 ⭐
```python
# ✅ 路径清晰
novel_meta = load_json(f"{project_dir}/Analyst/Import/novel/metadata.json")
chapters = load_json(f"{project_dir}/Analyst/Import/novel/chapters.json")

# 使用 ArtifactManager
segmentation = artifact_manager.load_latest_artifact(
    artifact_type="chapter_001_segmentation",
    base_dir=f"{project_dir}/Analyst/NovelAnalysis"
)
```

---

### 保存文件路径

#### 旧代码
```python
# ❌ 不清楚该保存到哪里
output_dir = f"{project_dir}/processing/novel/step4_segmentation"
# 或
output_dir = f"{project_dir}/analysis/novel"

with open(f"{output_dir}/chapter_001.json", 'w') as f:
    json.dump(result, f)
```

#### 新代码 ⭐
```python
# ✅ 使用 ArtifactManager，自动版本化
artifact_manager.save_artifact(
    content=result,
    artifact_type="chapter_001_segmentation",
    base_dir=f"{project_dir}/Analyst/NovelAnalysis"
)
# 自动生成:
# - Analyst/NovelAnalysis/chapter_001_segmentation_latest.json
# - Analyst/NovelAnalysis/history/chapter_001_segmentation_v{timestamp}.json
```

---

## 📊 改进总结

| 方面 | 旧结构 | 新结构 | 改进 |
|------|--------|--------|------|
| **目录层级** | 4层（raw, processed, processing, analysis） | 3层（Raw, Analyst/{Step}, history） | -25% |
| **与前端对应** | ❌ 不对应 | ✅ 1:1对应 | +100% |
| **数据流清晰度** | 3/10 | 9/10 | +200% |
| **命名统一性** | 5/10 | 10/10 | +100% |
| **版本管理** | ❌ 手动 | ✅ 自动（ArtifactManager） | +100% |
| **冗余目录** | 1个（processing/） | 0个 | -100% |
| **开发者理解难度** | 7/10 | 3/10 | -57% |

---

## 🚀 迁移收益

### 对开发者

1. **更容易理解**：目录结构与前端步骤一致
2. **减少错误**：明确知道该读/写哪个目录
3. **版本管理**：ArtifactManager自动处理版本

### 对用户

1. **状态清晰**：每个步骤的结果都有明确位置
2. **可追溯**：可以看到数据如何从Raw流向最终结果
3. **可回滚**：保留历史版本，支持回滚

### 对项目

1. **易于扩展**：可以轻松添加新的Phase或Step
2. **易于维护**：结构清晰，减少技术债务
3. **易于测试**：每个步骤独立，便于单元测试

---

## 📋 迁移检查清单

### Phase 1: 目录迁移
- [ ] 创建新目录结构（Raw/, Analyst/, Reports/）
- [ ] 迁移 raw/ → Raw/
- [ ] 迁移 processed/ → Analyst/Import/
- [ ] 合并 processing/ + analysis/ → Analyst/{Step}/
- [ ] 迁移 reports/ → Reports/
- [ ] 备份旧目录

### Phase 2: 代码更新
- [ ] 更新 ProjectManagerV2.create_project()
- [ ] 更新所有 Workflow 的保存路径
- [ ] 更新所有读取路径
- [ ] 搜索替换 "processed/" → "Analyst/Import/"
- [ ] 搜索替换 "analysis/" → "Analyst/{Step}/"

### Phase 3: API更新
- [ ] 更新 API 路由
- [ ] 更新 API 文档
- [ ] 前端路径更新

### Phase 4: 测试验证
- [ ] 单元测试
- [ ] 集成测试
- [ ] 手动验证前端功能
- [ ] 性能测试

---

**最后更新**: 2026-02-12  
**建议执行**: 本周或下周  
**预计工期**: 5-6天
