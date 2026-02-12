# 文档冲突分析与解决方案

**日期**: 2026-02-12  
**目的**: 识别文档之间的冲突并统一规范

---

## 🔴 发现的冲突

### 冲突1: 目录命名风格不统一 ⚠️ **最严重**

#### 问题描述
三份文档使用了不同的命名风格：

| 文档 | 命名风格 | 示例 |
|------|---------|------|
| **DATA_FLOW_REDESIGN.md** | 大写开头+驼峰 | `Raw/`, `Analyst/`, `Import/`, `ScriptAnalysis/` |
| **OPTIMIZATION_SUMMARY.md** | 小写+下划线 | `raw/`, `analyst/`, `import/`, `script_analysis/` |
| **FINAL_OPTIMIZATION_PLAN.md** | 小写+下划线 | `raw/`, `analyst/`, `import/`, `script_analysis/` |
| **DIRECTORY_RESTRUCTURE_PLAN.md** | 小写 | `raw/`, `processed/`, `analysis/` (旧方案) |

#### 影响
- 开发者不知道应该使用哪种命名
- 可能导致路径错误
- 代码和文档不一致

#### 用户决策（2026-02-12）
> "1. 和前端保持一致"  
> "2. 保持小写吧"

#### ✅ 解决方案
**统一使用：小写+下划线**

```
正确 ✅：
data/projects/{project_id}/
├── raw/
├── analyst/
│   ├── import/
│   ├── script_analysis/
│   ├── novel_analysis/
│   └── alignment/
└── reports/

错误 ❌：
data/projects/{project_id}/
├── Raw/
├── Analyst/
│   ├── Import/
│   ├── ScriptAnalysis/
│   ├── NovelAnalysis/
│   └── Alignment/
└── Reports/
```

---

### 冲突2: 多个目录设计方案并存 🟡

#### 问题描述
存在多个不同的目录结构设计：

**方案A - DIRECTORY_RESTRUCTURE_PLAN.md（旧方案）**
```
data/projects/{project_id}/
├── raw/
├── processed/          # Step 1输出
├── analysis/           # Step 2/3/4输出
└── reports/
```

**方案B - DATA_FLOW_REDESIGN.md（新方案，但命名错误）**
```
data/projects/{project_id}/
├── Raw/
├── Analyst/            # 包含所有Step
│   ├── Import/
│   ├── ScriptAnalysis/
│   ├── NovelAnalysis/
│   └── Alignment/
└── Reports/
```

**方案C - OPTIMIZATION_SUMMARY.md + FINAL_OPTIMIZATION_PLAN.md（最终方案）**
```
data/projects/{project_id}/
├── raw/
├── analyst/            # 包含所有Step
│   ├── import/
│   ├── script_analysis/
│   ├── novel_analysis/
│   └── alignment/
└── reports/
```

#### 影响
- 文档之间描述不一致
- 新手会困惑应该参考哪个

#### ✅ 解决方案
**采用方案C作为最终方案**

原因：
1. ✅ 与前端4步1:1对应
2. ✅ 命名符合用户要求（小写+下划线）
3. ✅ 在最新的优化文档中定义

**需要更新的文档**：
- ❌ `DATA_FLOW_REDESIGN.md` - 需要将所有大写改为小写
- ⚠️ `DIRECTORY_RESTRUCTURE_PLAN.md` - 标记为"旧方案"

---

### 冲突3: Markdown文件决策描述不一致 🟢 **已统一**

#### 检查结果
所有文档**一致**：
- ✅ 保留 `novel-imported.md`（NovelViewer需要）
- ❌ 删除 `ep01-imported.md`（前端用JSON）

**无冲突** ✅

---

### 冲突4: 文件命名规范（轻微） 🟢

#### 问题描述
- 集数命名：`ep01` vs `episode_01` vs `ep_01`
- 章节命名：`chapter_001` vs `chapter001` vs `ch001`

#### 现状
文档中已统一：
- ✅ 集数：`ep01`, `ep02`
- ✅ 章节：`chapter_001`, `chapter_002`

**无冲突** ✅

---

## 📋 需要修正的文档

### 1. DATA_FLOW_REDESIGN.md ⚠️ **必须修改**

**问题**：使用了大写+驼峰命名

**需要修改的地方**：
- `Raw/` → `raw/`
- `Analyst/` → `analyst/`
- `Import/` → `import/`
- `ScriptAnalysis/` → `script_analysis/`
- `NovelAnalysis/` → `novel_analysis/`
- `Alignment/` → `alignment/`
- `Reports/` → `reports/`

**修改范围**：全文（约30处）

---

### 2. DIRECTORY_RESTRUCTURE_PLAN.md ⚠️ **需要标注**

**问题**：使用旧的目录结构（`processed/`, `analysis/`）

**解决方案**：
在文档开头添加警告：

```markdown
> ⚠️ **注意**：本文档描述的是旧的目录结构设计方案。
> 
> **最新方案请参考**：
> - [数据流重新设计](./DATA_FLOW_REDESIGN.md)
> - [优化方案执行摘要](../planning/OPTIMIZATION_SUMMARY.md)
```

---

## ✅ 最终统一规范

### 目录结构（标准）

```
data/projects/{project_id}/
│
├── meta.json                           # 项目元数据
│
├── raw/                                # 原始文件
│   ├── novel/
│   └── script/
│
├── analyst/                            # Phase I分析
│   ├── import/                         # Step 1
│   │   ├── novel/
│   │   │   ├── standardized.txt
│   │   │   ├── metadata.json
│   │   │   ├── chapters.json
│   │   │   └── novel-imported.md      # ✅ 唯一保留的markdown
│   │   └── script/
│   │       ├── ep01.json
│   │       ├── ep02.json
│   │       └── episodes.json
│   │       # ❌ 不生成 ep01-imported.md
│   │
│   ├── script_analysis/                # Step 2
│   │   ├── ep01_segmentation_latest.json
│   │   ├── ep01_hook_latest.json
│   │   ├── ep01_validation_latest.json
│   │   └── history/
│   │
│   ├── novel_analysis/                 # Step 3
│   │   ├── chapter_001_segmentation_latest.json
│   │   ├── chapter_001_annotation_latest.json
│   │   ├── system_catalog_latest.json
│   │   └── history/
│   │
│   └── alignment/                      # Step 4
│       ├── chapter_001_ep01_alignment_latest.json
│       └── history/
│
└── reports/                            # 报告
```

### 命名规范（标准）

| 类型 | 格式 | 示例 | 说明 |
|------|------|------|------|
| **目录名** | 小写+下划线 | `script_analysis/` | 与前端保持一致 |
| **集数ID** | `ep{XX}` | `ep01`, `ep02` | 两位数字，补零 |
| **章节ID** | `chapter_{XXX}` | `chapter_001` | 三位数字，补零 |
| **JSON文件** | `{name}_latest.json` | `ep01_segmentation_latest.json` | Latest指针 |
| **历史文件** | `{name}_v{timestamp}.json` | `ep01_segmentation_v20260212_180000.json` | 时间戳版本 |
| **Markdown** | `{name}-imported.md` | `novel-imported.md` | 仅Novel保留 |

---

## 🔧 修复计划

### 立即执行（P0）

- [ ] 修改 `DATA_FLOW_REDESIGN.md`
  - 将所有大写目录名改为小写+下划线
  - 预计修改：30处
  - 耗时：10分钟

- [ ] 标注 `DIRECTORY_RESTRUCTURE_PLAN.md`
  - 添加"旧方案"警告
  - 指向最新文档
  - 耗时：2分钟

### 后续优化（P1）

- [ ] 创建 `NAMING_STANDARDS.md`（独立的命名规范文档）
- [ ] 在 `INDEX.md` 中标注文档版本和状态

---

## 📊 文档一致性检查表

| 文档 | 目录命名 | Markdown决策 | 文件命名 | 状态 |
|------|---------|-------------|---------|------|
| OPTIMIZATION_SUMMARY.md | ✅ 小写 | ✅ 正确 | ✅ 正确 | ✅ 最新 |
| FINAL_OPTIMIZATION_PLAN.md | ✅ 小写 | ✅ 正确 | ✅ 正确 | ✅ 最新 |
| DATA_FLOW_REDESIGN.md | ❌ 大写 | ✅ 正确 | ✅ 正确 | ⚠️ 需修改 |
| DIRECTORY_RESTRUCTURE_PLAN.md | ⚠️ 旧方案 | ✅ 正确 | ✅ 正确 | ⚠️ 旧版 |
| USER_NEEDS_AND_DATA_GAP.md | ✅ 小写 | ✅ 正确 | ✅ 正确 | ✅ 最新 |
| FRONTEND_MISSING_FEATURES.md | ✅ 小写 | ✅ 正确 | ✅ 正确 | ✅ 最新 |
| NAMING_CONVENTIONS.md | ✅ 小写 | ✅ 正确 | ✅ 正确 | ✅ 最新 |

---

## 🎯 修复后的文档体系

### 主要参考文档（优先级排序）

1. **[优化方案执行摘要](./planning/OPTIMIZATION_SUMMARY.md)** ⭐ - 快速了解（3分钟）
2. **[完整优化方案](./planning/FINAL_OPTIMIZATION_PLAN.md)** ⭐ - 6天实施计划
3. **[数据流重新设计](./design/DATA_FLOW_REDESIGN.md)** ⚠️ **（需修复命名）** - 详细数据流
4. **[命名规范](./design/NAMING_CONVENTIONS.md)** - 统一命名标准

### 旧文档（仅供参考）

- **[目录重构方案](./design/DIRECTORY_RESTRUCTURE_PLAN.md)** ⚠️ **（已过时）** - 旧的设计方案

---

## 📝 总结

### 核心冲突
1. 🔴 **目录命名风格**：大写 vs 小写（最严重）
2. 🟡 **多个目录方案**：旧方案 vs 新方案

### 解决方案
1. ✅ 统一使用：**小写+下划线**
2. ✅ 采用最新方案：**analyst/{step}/**
3. ⚠️ 修复 `DATA_FLOW_REDESIGN.md`
4. ⚠️ 标注 `DIRECTORY_RESTRUCTURE_PLAN.md` 为旧版

### 预期效果
- ✅ 所有文档使用统一的命名规范
- ✅ 清晰标注文档版本和状态
- ✅ 开发者不再困惑

---

**最后更新**: 2026-02-12  
**状态**: 待修复（2处文档需要更新）
