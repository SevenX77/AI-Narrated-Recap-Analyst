# V4架构清理计划

**清理目标**: 移除旧架构（V1.0/V2.0）的代码和数据文件  
**当前架构**: V4.0 - Hook-Body分离架构  
**清理日期**: 2026-02-04

---

## 📋 待清理文件清单

### 1. 旧版Workflows（src/workflows/）

#### ❌ 需要删除（7个）

```
src/workflows/
├── ingestion_workflow_old_backup.py    ← V1.0备份
├── ingestion_workflow_v1_backup.py     ← V1.0备份
├── ingestion_workflow_v1_old.py        ← V1.0旧版本
├── ingestion_workflow_v2_new.py        ← V2.0开发版
├── ingestion_workflow_v2.py            ← V2.0正式版（已被V3替代）
├── ingestion_workflow.py               ← V2.0别名（已被V3替代）
└── ingestion_workflow.py.bak           ← 备份文件
```

**删除理由**: 
- 使用旧的 Sentence→SemanticBlock→Event 架构
- 已被 `ingestion_workflow_v3.py` 完全替代
- Hook与Body混合处理，已过时

#### ✅ 保留

```
src/workflows/
├── ingestion_workflow_v3.py            ← ✅ V4.0当前版本
├── training_workflow.py                ← ✅ 训练流程（待验证是否使用）
└── training_workflow_v2.py             ← ⚠️  待确认是否使用
```

---

### 2. 旧版Alignment Engines（src/modules/alignment/）

#### ❌ 需要删除（4个）

```
src/modules/alignment/
├── deepseek_alignment_engine.py        ← V1.0引擎
├── deepseek_alignment_engine_v2.py     ← V2.0引擎（Sentence→Block→Event）
├── hook_detector.py                    ← 旧Hook检测（已被body_start_detector替代）
└── alignment_engine.py                 ← 旧接口定义
```

**删除理由**:
- 基于旧的三层数据模型
- 已被新的分层对齐引擎完全替代

#### ✅ 保留（V4.0新架构）

```
src/modules/alignment/
├── body_start_detector.py              ← ✅ Body起点检测器
├── hook_content_extractor.py           ← ✅ Hook内容提取器
├── layered_alignment_engine.py         ← ✅ 分层对齐引擎
└── novel_preprocessor.py               ← ✅ Novel预处理器
```

---

### 3. 旧版对齐数据（data/projects/PROJ_002/alignment/）

#### ❌ 需要清理/归档

**旧架构生成的文件（基于Event模型）**:
```
alignment/
├── alignment_quality_report_v2_latest.json          ← V2.0质量报告
├── alignment_v2_latest.json                         ← V2.0对齐结果
├── novel_events_v2_latest.json                      ← V2.0 Novel Events
├── novel_events_v2_latest_before_merge.json         ← V2.0中间文件
├── ep01_script_events_v2_latest.json                ← V2.0 Script Events
├── ep01_script_events_v2_latest_before_merge.json   ← V2.0中间文件
├── ep02_script_events_v2_latest.json
├── ep02_script_events_v2_latest_before_merge.json
├── ep03_script_events_v2_latest.json
├── ep03_script_events_v2_latest_before_merge.json
├── ep04_script_events_v2_latest.json
├── ep04_script_events_v2_latest_before_merge.json
├── ep05_script_events_v2_latest.json
├── ep05_script_events_v2_latest_before_merge.json
└── ep01_hook_detection_latest.json                  ← V2.0 Hook检测（已被新版替代）
```

**备份目录（已有备份）**:
```
alignment/
├── _backup/       ← 16个旧JSON文件
├── history/       ← 21个历史JSON文件
└── versions/      ← 版本文件夹
```

#### ✅ 保留（V4.0新架构生成）

```
alignment/
└── ep01_body_alignment.json            ← ✅ V4.0 Body对齐结果

preprocessing/（新目录）
├── novel_introduction_clean.txt        ← ✅ V4.0 简介
└── novel_chapters_index.json           ← ✅ V4.0 章节索引

hook_analysis/（新目录）
└── ep01_hook_analysis.json             ← ✅ V4.0 Hook分析结果
```

---

### 4. 其他弃用文件

#### ❌ 可清理

```
logs/output/                            ← 重复的日志目录（logs/已有）
  ├── app.log
  └── operation_history.jsonl
```

---

## 🎯 清理方案

### 方案A：完全删除（不推荐）

```bash
# 直接删除所有旧文件
rm -rf src/workflows/ingestion_workflow*.py（除v3外）
rm -rf src/modules/alignment/deepseek_*.py
```

**风险**: 无法回滚，丢失历史记录

---

### 方案B：归档备份（推荐）⭐

```bash
# 创建归档目录
mkdir -p archive/v2_deprecated

# 归档旧代码
mv src/workflows/ingestion_workflow_old_backup.py archive/v2_deprecated/
mv src/workflows/ingestion_workflow_v1*.py archive/v2_deprecated/
mv src/workflows/ingestion_workflow_v2*.py archive/v2_deprecated/
mv src/workflows/ingestion_workflow.py archive/v2_deprecated/
mv src/workflows/ingestion_workflow.py.bak archive/v2_deprecated/

mv src/modules/alignment/deepseek_alignment_engine*.py archive/v2_deprecated/
mv src/modules/alignment/hook_detector.py archive/v2_deprecated/
mv src/modules/alignment/alignment_engine.py archive/v2_deprecated/

# 归档旧数据
mkdir -p archive/v2_deprecated/alignment_data
mv data/projects/PROJ_002/alignment/*_v2_*.json archive/v2_deprecated/alignment_data/
mv data/projects/PROJ_002/alignment/ep01_hook_detection_latest.json archive/v2_deprecated/alignment_data/

# 归档备份目录
mv data/projects/PROJ_002/alignment/_backup archive/v2_deprecated/alignment_data/
mv data/projects/PROJ_002/alignment/history archive/v2_deprecated/alignment_data/
mv data/projects/PROJ_002/alignment/versions archive/v2_deprecated/alignment_data/

# 删除重复日志
rm -rf logs/output/
```

**优点**: 
- 保留历史记录
- 可随时查阅
- 降低风险

---

### 方案C：Git归档（最优）⭐⭐⭐

```bash
# 1. 先提交当前状态
git add .
git commit -m "feat: V4.0 Hook-Body分离架构完整实施"
git tag v4.0-release

# 2. 创建archive分支保存旧代码
git checkout -b archive/v2-deprecated
# 将旧文件commit到archive分支
git checkout main

# 3. 在main分支删除旧文件
git rm src/workflows/ingestion_workflow_old_backup.py
git rm src/workflows/ingestion_workflow_v1*.py
git rm src/workflows/ingestion_workflow_v2*.py
...
git commit -m "chore: 清理V2.0旧架构文件"

# 4. 旧数据文件添加到.gitignore（不提交到Git）
echo "*_v2_*.json" >> data/.gitignore
echo "_backup/" >> data/.gitignore
echo "history/" >> data/.gitignore
```

**优点**:
- Git历史完整保留
- 可通过tag/branch回滚
- 工作目录清爽
- 最佳实践

---

## 📊 预期清理效果

### 清理前

```
代码文件: 11个workflow + 4个engine = 15个文件
数据文件: ~60个JSON文件（含备份）
磁盘占用: ~50MB
```

### 清理后

```
代码文件: 1个workflow(V3) + 4个engine(V4) = 5个文件
数据文件: ~10个JSON文件（V4.0生成）
磁盘占用: ~10MB
节省: 40MB + 清晰的代码结构
```

---

## ✅ 推荐执行步骤

**建议使用方案C（Git归档）**:

```bash
# Step 1: 确认当前在main分支且无未提交修改
git status

# Step 2: 提交V4.0完整实施
git add .
git commit -m "feat: V4.0 Hook-Body分离架构完整实施

- ✅ Phase 0: Novel预处理
- ✅ Phase 1: Hook分析（Body起点检测+分层提取）
- ✅ Phase 2: Body对齐（LayeredAlignmentEngine）
- ✅ 完整测试通过
- ✅ 文档完善
"
git tag -a v4.0.0 -m "V4.0 Hook-Body分离架构正式发布"

# Step 3: 删除旧文件（保留在Git历史中）
# 旧workflows
git rm src/workflows/ingestion_workflow_old_backup.py
git rm src/workflows/ingestion_workflow_v1_backup.py
git rm src/workflows/ingestion_workflow_v1_old.py
git rm src/workflows/ingestion_workflow_v2_new.py
git rm src/workflows/ingestion_workflow_v2.py
git rm src/workflows/ingestion_workflow.py
git rm src/workflows/ingestion_workflow.py.bak

# 旧engines
git rm src/modules/alignment/deepseek_alignment_engine.py
git rm src/modules/alignment/deepseek_alignment_engine_v2.py
git rm src/modules/alignment/hook_detector.py
git rm src/modules/alignment/alignment_engine.py

git commit -m "chore: 清理V2.0旧架构代码文件"

# Step 4: 清理旧数据文件（不提交到Git）
# 这些文件已在.gitignore中，直接删除或归档
mkdir -p archive/v2_data
mv data/projects/PROJ_002/alignment/*_v2_*.json archive/v2_data/
mv data/projects/PROJ_002/alignment/ep01_hook_detection_latest.json archive/v2_data/
mv data/projects/PROJ_002/alignment/_backup archive/v2_data/
mv data/projects/PROJ_002/alignment/history archive/v2_data/
mv data/projects/PROJ_002/alignment/versions archive/v2_data/

# Step 5: 删除重复日志
rm -rf logs/output/

# Step 6: 验证清理结果
ls -la src/workflows/
ls -la src/modules/alignment/
ls -la data/projects/PROJ_002/alignment/

echo "✅ 清理完成！"
```

---

## 🔍 清理后验证

### 检查清理效果

```bash
# 1. 验证代码文件
echo "=== Workflows ==="
ls src/workflows/

echo "=== Alignment Modules ==="
ls src/modules/alignment/

echo "=== Alignment Data ==="
ls data/projects/PROJ_002/alignment/

# 2. 运行测试确保功能正常
python3 scripts/test_hook_body_workflow.py

# 3. 查看Git历史
git log --oneline --graph -10
git tag
```

### 预期输出

```
=== Workflows ===
ingestion_workflow_v3.py    ← ✅ 唯一的workflow
training_workflow.py
training_workflow_v2.py

=== Alignment Modules ===
body_start_detector.py      ← ✅ V4.0
hook_content_extractor.py   ← ✅ V4.0
layered_alignment_engine.py ← ✅ V4.0
novel_preprocessor.py       ← ✅ V4.0

=== Alignment Data ===
ep01_body_alignment.json    ← ✅ V4.0生成

Git Tags:
v4.0.0                      ← ✅ 当前版本
```

---

## 📝 注意事项

### ⚠️ 清理前备份

```bash
# 在清理前创建完整备份
tar -czf backup_before_cleanup_$(date +%Y%m%d).tar.gz \
    src/workflows/ \
    src/modules/alignment/ \
    data/projects/PROJ_002/alignment/
```

### ⚠️ 确认依赖

```bash
# 检查是否有其他文件import旧模块
grep -r "from src.workflows.ingestion_workflow_v2" src/
grep -r "from src.modules.alignment.deepseek_alignment_engine" src/
grep -r "from src.modules.alignment.hook_detector" src/
```

### ⚠️ 测试清理后功能

```bash
# 运行完整测试套件
python3 scripts/test_hook_body_workflow.py

# 验证V4.0功能
python3 -c "
from src.workflows.ingestion_workflow_v3 import IngestionWorkflowV3
print('✅ V4.0 Workflow可正常导入')
"
```

---

## 🎯 总结

**推荐方案**: 方案C（Git归档）

**清理后保留**:
- ✅ 1个workflow（ingestion_workflow_v3.py）
- ✅ 4个alignment模块（V4.0新架构）
- ✅ V4.0生成的数据文件
- ✅ 完整的Git历史记录

**清理收益**:
- 代码文件减少66%（15个→5个）
- 数据文件减少80%（60个→10个）
- 磁盘空间节省40MB
- 代码结构清晰，易于维护

---

**文档创建**: 2026-02-04  
**适用版本**: V4.0  
**状态**: 待执行
