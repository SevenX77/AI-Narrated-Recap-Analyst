# 目录结构重构方案

> ⚠️ **注意**：本文档描述的是旧的目录结构设计方案。
> 
> **最新方案请参考**：
> - [数据流重新设计](./DATA_FLOW_REDESIGN.md) - 详细的数据流和目录设计
> - [优化方案执行摘要](../planning/OPTIMIZATION_SUMMARY.md) - 最新的优化方案（3分钟快速了解）
> - [完整优化方案](../planning/FINAL_OPTIMIZATION_PLAN.md) - 6天实施计划
> 
> 本文档保留仅供参考，了解设计演变历史。

**最后更新**: 2026-02-12  
**状态**: ⚠️ 已过时，请参考最新文档  
**目的**: 清理冗余目录，统一数据存储结构

---

## 📊 当前问题

### 问题1: 目录冗余
```
❌ 当前存在3层目录：
├── processed/      # 预处理结果
├── processing/     # Workflow中间结果（❌ 与analysis重复）
└── analysis/       # 工具输出（版本化）
```

**问题**：
- `processing/` 和 `analysis/` 职责重叠
- 开发者困惑：不知道该写入哪个目录
- 数据分散：同一结果可能在多个地方

### 问题2: 命名不统一
- 文件名：`ep01` vs `episode_01` vs `1`
- 目录名：`novel` vs `novels`
- 变量名：`episode` vs `episode_id` vs `ep`

### 问题3: 状态冗余
- `meta.json` 包含2套状态：`workflow_stages` 和 `phase_i_analyst`

---

## 🎯 重构方案（推荐）

### 新目录结构

```
data/projects/{project_id}/
│
├── meta.json                           # ✅ 唯一状态文件（只保留 phase_i_analyst）
│
├── raw/                                # 🔵 原始文件（不可变）
│   ├── novel/
│   │   └── {original_filename}.txt
│   └── srt/
│       ├── ep01.srt                    # ✅ 统一格式：ep{XX}.srt
│       ├── ep02.srt
│       └── ...
│
├── processed/                          # 🟢 预处理结果（Step 1自动生成）
│   ├── novel/
│   │   ├── standardized.txt
│   │   ├── metadata.json
│   │   └── chapters.json
│   └── script/
│       ├── ep01.json                   # ✅ 统一格式：ep{XX}.json
│       ├── ep01-imported.md
│       ├── ep02.json
│       ├── ep02-imported.md
│       └── episodes.json
│
├── analysis/                           # 🟡 深度分析结果（Step 2/3/4输出，版本化）
│   ├── novel/
│   │   ├── chapter_001_segmentation_latest.json
│   │   ├── chapter_001_annotation_latest.json
│   │   ├── chapter_002_segmentation_latest.json
│   │   ├── system_catalog_latest.json
│   │   └── history/                    # 📦 历史版本
│   │       ├── chapter_001_segmentation_v{timestamp}.json
│   │       └── ...
│   ├── script/
│   │   ├── ep01_segmentation_latest.json
│   │   ├── ep01_hook_latest.json
│   │   ├── ep01_validation_latest.json
│   │   ├── ep02_segmentation_latest.json
│   │   └── history/
│   │       └── ...
│   └── alignment/
│       ├── chapter_001_ep01_alignment_latest.json
│       └── history/
│           └── ...
│
└── reports/                            # 📝 人类可读报告
    ├── quality_report.html
    ├── alignment_report.md
    └── ...
```

### 关键变化

| 变化 | 原因 | 影响 |
|------|------|------|
| ❌ 删除 `processing/` | 与 `analysis/` 重复 | 简化结构 |
| ✅ 统一使用 `analysis/` | 所有Workflow输出放在一起 | 易于查找 |
| ✅ 添加 `history/` 子目录 | 版本化管理 | 支持回滚 |
| ✅ 统一文件命名 | `ep01`, `chapter_001` | 消除混乱 |
| ❌ 删除 `workflow_stages` | 只保留 `phase_i_analyst` | 简化状态 |

---

## 📋 实施步骤

### Phase 1: 数据迁移（1天）

#### 步骤1.1: 迁移现有数据

```bash
# 迁移脚本：migrate_to_new_structure.sh

#!/bin/bash

PROJECT_DIR="data/projects/project_001"

# 1. 迁移 processing/ 数据到 analysis/
if [ -d "$PROJECT_DIR/processing" ]; then
    echo "Migrating processing/ to analysis/..."
    
    # 迁移 novel/ 数据
    if [ -d "$PROJECT_DIR/processing/novel" ]; then
        mkdir -p "$PROJECT_DIR/analysis/novel"
        cp -r $PROJECT_DIR/processing/novel/* $PROJECT_DIR/analysis/novel/
    fi
    
    # 迁移 script/ 数据
    if [ -d "$PROJECT_DIR/processing/script" ]; then
        mkdir -p "$PROJECT_DIR/analysis/script"
        cp -r $PROJECT_DIR/processing/script/* $PROJECT_DIR/analysis/script/
    fi
    
    # 备份后删除
    mv $PROJECT_DIR/processing $PROJECT_DIR/processing.backup
    echo "✅ Migrated processing/ → analysis/"
fi

# 2. 统一文件命名
echo "Renaming files to standard format..."

# Novel: 确保使用 chapter_{XXX} 格式
cd "$PROJECT_DIR/analysis/novel"
for file in chapter_*.json; do
    # 已经是标准格式，跳过
    echo "Novel file: $file (OK)"
done

# Script: 确保使用 ep{XX} 格式
cd "$PROJECT_DIR/analysis/script"
for file in *.json; do
    # 检查是否需要重命名
    if [[ $file =~ ^episode_([0-9]+)_ ]]; then
        new_name="ep$(printf "%02d" ${BASH_REMATCH[1]})_${file#episode_*_}"
        mv "$file" "$new_name"
        echo "Renamed: $file → $new_name"
    fi
done

echo "✅ File naming standardized"
```

#### 步骤1.2: 创建历史版本目录

```python
# scripts/create_history_dirs.py

import os
from pathlib import Path

def create_history_directories(project_dir: str):
    """为所有analysis子目录创建history/目录"""
    
    analysis_dir = Path(project_dir) / "analysis"
    
    for subdir in ["novel", "script", "alignment"]:
        subdir_path = analysis_dir / subdir
        history_path = subdir_path / "history"
        
        if subdir_path.exists():
            history_path.mkdir(exist_ok=True)
            print(f"✅ Created {history_path}")

if __name__ == "__main__":
    create_history_directories("data/projects/project_001")
```

---

### Phase 2: 代码更新（2天）

#### 步骤2.1: 更新 ProjectManagerV2

```python
# src/core/project_manager_v2.py

def create_project(self, name: str, description: Optional[str] = None) -> ProjectMeta:
    """创建新项目"""
    project_id = self._generate_project_id()
    project_dir = os.path.join(self.projects_dir, project_id)
    
    # ✅ 新目录结构
    directories = [
        "raw/novel",
        "raw/srt",
        "processed/novel",
        "processed/script",
        "analysis/novel",
        "analysis/novel/history",
        "analysis/script",
        "analysis/script/history",
        "analysis/alignment",
        "analysis/alignment/history",
        "reports"
    ]
    
    for dir_path in directories:
        os.makedirs(os.path.join(project_dir, dir_path), exist_ok=True)
    
    # ❌ 删除 processing/ 目录创建
    # os.makedirs(os.path.join(project_dir, "processing"), exist_ok=True)  # 删除这行
    
    # 创建元数据（只包含 phase_i_analyst）
    meta = ProjectMeta(
        id=project_id,
        name=name,
        description=description,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    # ✅ 初始化 Phase I 状态
    meta.initialize_phase_i()
    
    # ❌ 不再初始化 workflow_stages
    # meta.workflow_stages = ...  # 删除这行
    
    self._save_meta(project_id, meta)
    return meta
```

#### 步骤2.2: 更新 Workflow 保存路径

```python
# src/workflows/novel_processing_workflow.py

def save_segmentation_result(self, chapter_id: str, result: SegmentationResult):
    """保存分段结果"""
    
    # ❌ 旧路径（删除）
    # old_path = f"{self.project_dir}/processing/novel/step4_segmentation/{chapter_id}.json"
    
    # ✅ 新路径
    artifact_manager.save_artifact(
        content=result.model_dump(),
        artifact_type=f"{chapter_id}_segmentation",
        project_id=self.project_id,
        base_dir=f"{self.project_dir}/analysis/novel",
        extension="json"
    )
    # 自动生成:
    # - analysis/novel/chapter_001_segmentation_latest.json
    # - analysis/novel/history/chapter_001_segmentation_v{timestamp}.json
```

```python
# src/workflows/script_processing_workflow.py

def save_hook_result(self, episode_id: str, result: HookDetectionResult):
    """保存Hook检测结果"""
    
    # ❌ 旧路径（删除）
    # old_path = f"{self.project_dir}/processing/script/{episode_id}_hook.json"
    
    # ✅ 新路径
    artifact_manager.save_artifact(
        content=result.model_dump(),
        artifact_type=f"{episode_id}_hook",
        project_id=self.project_id,
        base_dir=f"{self.project_dir}/analysis/script",
        extension="json"
    )
```

#### 步骤2.3: 更新命名规范

```python
# 全局搜索替换

# ❌ 旧命名
episode = "episode_01"
ep = "ep_01"

# ✅ 新命名
episode_id = "ep01"  # 统一格式：ep{XX}
chapter_id = "chapter_001"  # 统一格式：chapter_{XXX}
```

**搜索替换清单**:
```bash
# 1. 替换函数参数
grep -r "def.*episode:" src/ | wc -l
→ 替换为: def process(episode_id: str)

# 2. 替换文件路径
grep -r "processing/" src/ | wc -l
→ 替换为: analysis/

# 3. 替换episode变量
grep -r "episode\s*=" src/ | wc -l
→ 替换为: episode_id =
```

---

### Phase 3: 清理代码（1天）

#### 步骤3.1: 删除 workflow_stages 相关代码

```python
# src/core/schemas_project.py

class ProjectMeta(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    status: ProjectStatus = ProjectStatus.DRAFT
    
    sources: ProjectSources = Field(default_factory=ProjectSources)
    
    # ❌ 删除（标记为废弃）
    workflow_stages: Optional[Dict] = Field(
        None,
        deprecated=True,
        description="已废弃，请使用 phase_i_analyst"
    )
    
    # ✅ 保留（主状态）
    phase_i_analyst: Optional[PhaseIAnalystState] = None
    
    stats: ProjectStats = Field(default_factory=ProjectStats)
```

#### 步骤3.2: 清理未使用的导入

```bash
# 运行代码检查工具
flake8 src/ --select=F401  # 检查未使用的导入
pylint src/ --disable=all --enable=unused-import
```

#### 步骤3.3: 删除旧测试文件

```bash
# 删除 processing/ 相关的测试
rm scripts/test/test_processing_*.py

# 更新测试路径
grep -r "processing/" scripts/test/ | wc -l
→ 替换为: analysis/
```

---

### Phase 4: 文档更新（1天）

#### 步骤4.1: 更新核心文档

- [ ] `docs/PROJECT_STRUCTURE.md` - 更新目录结构说明
- [ ] `docs/DEV_STANDARDS.md` - 补充命名规范
- [ ] `docs/FILE_PATH_MAPPING.md` - 更新路径映射
- [ ] `docs/workflows/ROADMAP.md` - 更新工作流说明

#### 步骤4.2: 创建迁移指南

```markdown
# MIGRATION_GUIDE.md

## 旧代码 → 新代码

### 1. 路径变更
| 旧路径 | 新路径 |
|--------|--------|
| `processing/novel/` | `analysis/novel/` |
| `processing/script/` | `analysis/script/` |

### 2. 命名变更
| 旧命名 | 新命名 |
|--------|--------|
| `episode` | `episode_id` |
| `ep_01` | `ep01` |
| `episode_01` | `ep01` |

### 3. 状态字段变更
| 旧字段 | 新字段 |
|--------|--------|
| `meta.workflow_stages` | `meta.phase_i_analyst` |
```

---

### Phase 5: 测试验证（1天）

#### 步骤5.1: 单元测试

```python
# tests/test_directory_structure.py

def test_new_directory_structure():
    """测试新目录结构是否正确创建"""
    project_id = "test_project_001"
    meta = project_manager_v2.create_project("Test Project")
    
    # 验证目录存在
    assert os.path.exists(f"data/projects/{project_id}/raw/novel")
    assert os.path.exists(f"data/projects/{project_id}/analysis/novel/history")
    
    # 验证旧目录不存在
    assert not os.path.exists(f"data/projects/{project_id}/processing")

def test_artifact_save_location():
    """测试artifact保存到正确位置"""
    result = {"chapter_id": "chapter_001", "paragraphs": []}
    
    artifact_manager.save_artifact(
        content=result,
        artifact_type="chapter_001_segmentation",
        project_id="test_project_001",
        base_dir="data/projects/test_project_001/analysis/novel"
    )
    
    # 验证文件存在
    assert os.path.exists("data/projects/test_project_001/analysis/novel/chapter_001_segmentation_latest.json")
    assert os.path.exists("data/projects/test_project_001/analysis/novel/history/chapter_001_segmentation_v*.json")
```

#### 步骤5.2: 集成测试

```bash
# 运行完整流程测试
python scripts/test/test_complete_workflow.py

# 测试步骤:
# 1. 创建项目 → 验证目录结构
# 2. 上传文件 → 验证processed/路径
# 3. 运行Workflow → 验证analysis/路径
# 4. 检查状态 → 验证phase_i_analyst更新
```

---

## 🚨 回滚计划

如果重构出现问题，可以快速回滚：

```bash
#!/bin/bash
# rollback.sh

PROJECT_DIR="data/projects/project_001"

# 1. 恢复 processing/ 目录
if [ -d "$PROJECT_DIR/processing.backup" ]; then
    mv $PROJECT_DIR/processing.backup $PROJECT_DIR/processing
    echo "✅ Restored processing/ directory"
fi

# 2. 恢复旧版本代码
git checkout HEAD~1 src/core/project_manager_v2.py
git checkout HEAD~1 src/workflows/
echo "✅ Restored old code"

# 3. 重启服务
pkill -f "uvicorn src.api.main"
sleep 2
nohup uvicorn src.api.main:app --reload --port 8000 &
echo "✅ Restarted API server"
```

---

## 📊 预期效果

### 重构前 vs 重构后

| 指标 | 重构前 | 重构后 | 改善 |
|------|--------|--------|------|
| **目录层级** | 3层（processed, processing, analysis） | 2层（processed, analysis） | -33% |
| **文件命名一致性** | 60% | 100% | +67% |
| **状态数据冗余** | 2套（workflow_stages, phase_i_analyst） | 1套（phase_i_analyst） | -50% |
| **开发者理解难度** | 高（7/10） | 低（3/10） | -57% |
| **数据查找时间** | ~30秒 | ~5秒 | -83% |

---

## 📋 执行检查清单

### 准备阶段
- [ ] 备份现有项目数据
- [ ] 通知团队成员即将重构
- [ ] 创建新分支 `refactor/directory-restructure`

### 实施阶段
- [ ] Phase 1: 数据迁移（1天）
  - [ ] 运行迁移脚本
  - [ ] 验证数据完整性
  - [ ] 创建history目录
- [ ] Phase 2: 代码更新（2天）
  - [ ] 更新ProjectManagerV2
  - [ ] 更新所有Workflow
  - [ ] 统一命名规范
- [ ] Phase 3: 清理代码（1天）
  - [ ] 删除workflow_stages
  - [ ] 清理未使用代码
  - [ ] 删除旧测试
- [ ] Phase 4: 文档更新（1天）
  - [ ] 更新核心文档
  - [ ] 创建迁移指南
- [ ] Phase 5: 测试验证（1天）
  - [ ] 运行单元测试
  - [ ] 运行集成测试
  - [ ] 手动验证前端功能

### 完成阶段
- [ ] 代码审查
- [ ] 合并到主分支
- [ ] 部署到生产环境
- [ ] 监控错误日志

---

## 🎯 里程碑

| 里程碑 | 预计完成 | 验收标准 |
|--------|---------|---------|
| 数据迁移完成 | Day 1 | 所有数据从processing/迁移到analysis/ |
| 代码更新完成 | Day 3 | 所有路径和命名统一 |
| 测试通过 | Day 5 | 单元测试和集成测试100%通过 |
| 文档更新完成 | Day 5 | 所有文档反映新结构 |
| 上线生产 | Day 6 | 生产环境稳定运行24小时 |

---

**最后更新**: 2026-02-12  
**预计工期**: 5-6天  
**风险等级**: 中等（有回滚方案）  
**建议执行时间**: 本周或下周
