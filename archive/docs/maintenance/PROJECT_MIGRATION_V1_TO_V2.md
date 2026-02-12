# 项目管理系统迁移：V1 → V2

**迁移时间**: 2026-02-11  
**状态**: ✅ 完成

---

## 📋 迁移摘要

将项目管理从 V1（`ProjectManager` + `project_index.json`）迁移到 V2（`ProjectManagerV2` + `meta.json`）。

---

## 🔍 V1 vs V2 对比

| 特性 | V1 (ProjectManager) | V2 (ProjectManagerV2) |
|------|---------------------|----------------------|
| **索引方式** | 中心化索引 `project_index.json` | 分布式 `meta.json` 每个项目 |
| **自动扫描** | ✅ 自动扫描 `分析资料/` 目录 | ❌ 不自动扫描 |
| **项目状态** | `draft`, `ready`, `discovered` | `draft`, `ready`, `processing`, `completed` |
| **工作流跟踪** | 基础的 `workflow_stages` | 完整的 Phase I-IV 状态 |
| **API 路径** | `/api/projects` | `/api/v2/projects` |
| **推荐使用** | ❌ 已弃用 | ✅ 推荐 |

---

## ⚠️ V1 的问题

### 1. **自动扫描机制**

```python
# src/core/project_manager.py
def __init__(self):
    self._load_index()
    self._scan_and_update()  # ⚠️ 每次初始化都扫描 分析资料/
```

**副作用**：
- 自动创建 `status: "discovered"` 的项目
- 删除后会自动恢复（如果源文件夹还在）
- 索引和实际数据不一致

### 2. **中心化索引**

所有项目元数据存储在一个文件中，不利于：
- 并发修改
- 分布式存储
- 版本控制

### 3. **缺少详细状态**

V1 的 `workflow_stages` 只有基础状态，无法支持新的 Phase I-IV 工作流。

---

## 🚀 迁移步骤

### Step 1: 运行迁移脚本

```bash
cd /Users/sevenx/Documents/coding/AI-Narrated\ Recap\ Analyst
python3 scripts/migrate_v1_to_v2.py
```

**迁移结果**（2026-02-11）：
```
✅ 成功迁移: 1 个项目 (PROJ_001 - 末哥超凡公路)
⏭️  已跳过: 2 个项目 (PROJ_006, PROJ_007 - 无实际目录)
🗑️  已清理: 2 个自动发现的项目 (从索引中移除)
```

### Step 2: 禁用 V1 自动扫描

修改 `src/core/project_manager.py`:

```python
def __init__(self):
    self.index_path = os.path.join(config.data_dir, "project_index.json")
    self.projects = {}
    self.next_id = 1
    self._load_index()
    # ⚠️ 已禁用自动扫描（迁移到 V2）
    # self._scan_and_update()
```

### Step 3: 验证迁移

```bash
# 测试 V2 API
curl http://localhost:8000/api/v2/projects

# 查看生成的 meta.json
cat data/projects/PROJ_001/meta.json
```

### Step 4: 前端验证

访问 `http://localhost:5173`，确认项目列表正常显示。

---

## 📁 迁移后的目录结构

```
data/
├── projects/
│   └── PROJ_001/
│       ├── meta.json           ✨ 新增：V2 元数据
│       ├── raw/
│       │   └── srt/
│       │       ├── ep01.srt
│       │       ├── ep02.srt
│       │       └── ep03.srt
│       ├── processed/
│       ├── analysis/
│       └── reports/
│
└── project_index.json          💾 保留：V1 兼容性
```

---

## 🔄 V2 meta.json 格式

```json
{
  "id": "PROJ_001",
  "name": "末哥超凡公路",
  "description": "从 V1 迁移的项目",
  "status": "ready",
  "created_at": "2026-02-10T18:37:00",
  "updated_at": "2026-02-11T15:30:32",
  
  "sources": {
    "has_novel": false,
    "has_script": true,
    "novel_chapters": 0,
    "script_episodes": 3
  },
  
  "phase_i_analyst": {
    "overall_status": "pending",
    "overall_progress": 0.0,
    "step_1_import": {...},
    "step_2_script": {...},
    "step_3_novel": {...},
    "step_4_alignment": {...}
  },
  
  "workflow_stages": {...},
  "stats": {...}
}
```

---

## 🎯 前端适配

前端已使用 V2 API（`/api/v2/projects`），无需修改：

```typescript
// frontend-new/src/api/projectsV2.ts
export const projectsApiV2 = {
  async list(): Promise<ProjectListResponse> {
    const response = await apiClient.get('/api/v2/projects')
    return response.data
  },
  // ...
}
```

---

## ✅ 迁移验证清单

- [x] 运行迁移脚本
- [x] 生成 `meta.json`
- [x] 清理自动发现的项目
- [x] 禁用 V1 自动扫描
- [x] V2 API 返回项目列表
- [x] 前端显示项目
- [x] Phase I 状态初始化
- [x] 保留 V1 兼容性

---

## 🔒 回退方案

如果需要回退到 V1：

1. **恢复自动扫描**：
   ```python
   # src/core/project_manager.py
   def __init__(self):
       # ...
       self._scan_and_update()  # 取消注释
   ```

2. **V1 数据未删除**：
   - `project_index.json` 仍然存在
   - V1 API (`/api/projects`) 仍然可用

3. **删除 meta.json**（可选）：
   ```bash
   rm data/projects/*/meta.json
   ```

---

## 📚 相关文档

- [数据存储重新设计](../architecture/DATA_STORAGE_REDESIGN.md)
- [Phase I 工作流实施](../workflows/PHASE_I_COMPLETE_GUIDE.md)
- [项目结构说明](../PROJECT_STRUCTURE.md)

---

## 🎉 迁移成功标志

1. ✅ V2 API 返回项目列表
2. ✅ 前端页面显示项目
3. ✅ 不再自动创建 "discovered" 项目
4. ✅ Phase I 工作流状态可用

---

**最后更新**: 2026-02-11 15:30  
**状态**: ✅ 迁移完成，V2 正常运行
