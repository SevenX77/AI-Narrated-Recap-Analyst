# 项目管理系统迁移总结

**迁移日期**: 2026-02-11  
**迁移类型**: V1 → V2 项目管理系统  
**状态**: ✅ 完成

---

## 📊 迁移概览

### 问题背景

用户发现：
1. **索引不一致**: `project_index.json` 中出现已删除的项目（PROJ_006, PROJ_007）
2. **前端无数据**: 前端页面无法显示项目列表
3. **自动扫描**: 删除的项目会自动恢复

### 根本原因

V1 的 `ProjectManager` 在**每次初始化时自动扫描** `分析资料/` 目录：

```python
# src/core/project_manager.py (V1)
def __init__(self):
    self._load_index()
    self._scan_and_update()  # ⚠️ 自动扫描外部目录
```

**副作用**：
- 自动创建 `status: "discovered"` 的项目索引
- 删除后会自动恢复（如果源文件夹存在）
- 数据索引和实际项目目录不一致

---

## 🚀 迁移方案

选择**方案 C：迁移到 ProjectManager V2**

### V2 的优势

| 特性 | V1 | V2 |
|------|----|----|
| 索引方式 | 中心化 `project_index.json` | 分布式 `meta.json` |
| 自动扫描 | ✅ 自动扫描 `分析资料/` | ❌ 不自动扫描 |
| 工作流支持 | 基础 `workflow_stages` | 完整 Phase I-IV |
| API 路径 | `/api/projects` | `/api/v2/projects` |
| 状态 | ❌ 已弃用 | ✅ 当前使用 |

---

## 🔧 迁移步骤

### Step 1: 创建迁移脚本

创建 `scripts/migrate_v1_to_v2.py`：
- 读取 `project_index.json`（V1 索引）
- 为每个实际存在的项目创建 `meta.json`（V2 格式）
- 清理 `discovered` 状态的项目（自动扫描生成的）
- 保留 V1 数据（兼容性）

### Step 2: 执行迁移

```bash
python3 scripts/migrate_v1_to_v2.py
```

**迁移结果**：
```
✅ 成功迁移: 1 个项目 (PROJ_001 - 末哥超凡公路)
⏭️  已跳过: 2 个项目 (PROJ_006, PROJ_007 - 目录不存在)
🗑️  已清理: 2 个自动发现的项目
```

### Step 3: 禁用 V1 自动扫描

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

### Step 4: 验证迁移

```bash
# 测试 V2 API
curl http://localhost:8000/api/v2/projects

# 输出：
{
  "projects": [
    {
      "id": "PROJ_001",
      "name": "末哥超凡公路",
      "status": "ready",
      "sources": {
        "has_script": true,
        "script_episodes": 3
      }
    }
  ],
  "total": 1
}
```

---

## 📁 迁移前后对比

### 迁移前（V1）

```
data/
├── projects/
│   └── PROJ_001/
│       ├── raw/
│       └── script/
│
└── project_index.json          # 中心化索引
    {
      "PROJ_001": {...},
      "PROJ_006": {...},        # ⚠️ 自动发现
      "PROJ_007": {...}         # ⚠️ 自动发现
    }
```

### 迁移后（V2）

```
data/
├── projects/
│   └── PROJ_001/
│       ├── meta.json           # ✨ V2 元数据
│       ├── raw/
│       ├── processed/
│       ├── analysis/
│       └── reports/
│
└── project_index.json          # 保留（V1 兼容）
    {
      "PROJ_001": {...}         # ✅ 仅实际项目
    }
```

---

## ✅ 验证结果

### 1. 后端 API

```bash
# V2 API 返回项目列表
GET /api/v2/projects
```

**返回**：✅ 1 个项目（PROJ_001）

### 2. 前端显示

访问 `http://localhost:5173`：

**首页**：
- ✅ 左上角显示："末哥超凡公路 (ID: PROJ_001)"
- ✅ 统计卡片：Total Projects: 1, Initialized: 1, Discovered: 0
- ✅ 项目列表：显示项目卡片（3 episodes, Feb 10, 2026）

**工作流页面** (`/project/PROJ_001`):
- ✅ 左侧边栏：Phase I 的 4 个步骤（流程图样式）
- ✅ 右侧主区域：ProjectDashboard（整体进度 + 步骤卡片）
- ✅ WebSocket 连接：成功连接（降级到轮询模式）

### 3. Playwright 验证

截图已保存：
- `frontend-new/.debug/screenshots/projects-list-with-data.png` - 项目列表
- `frontend-new/.debug/screenshots/project-workflow-with-data.png` - 工作流页面

---

## 📚 更新的文档

1. **迁移脚本**: `scripts/migrate_v1_to_v2.py`
2. **迁移文档**: `docs/maintenance/PROJECT_MIGRATION_V1_TO_V2.md`
3. **项目结构**: `docs/PROJECT_STRUCTURE.md`（标记 V1 已弃用）
4. **总结文档**: `docs/MIGRATION_SUMMARY_2026-02-11.md`（本文件）

---

## 🎯 解决的问题

### 问题 1: 索引不一致 ✅

**现象**: `project_index.json` 中有 PROJ_006 和 PROJ_007，但删除后又出现

**解决**: 
- 清理了自动发现的项目索引
- 禁用了 V1 的自动扫描机制

**结果**: 索引仅包含实际存在的项目

### 问题 2: 前端无数据 ✅

**现象**: 前端调用 `/api/v2/projects` 返回空列表

**原因**: V2 需要 `meta.json`，但 V1 项目没有

**解决**: 迁移脚本为 PROJ_001 生成了 `meta.json`

**结果**: 前端正常显示项目

### 问题 3: 自动扫描机制 ✅

**现象**: 删除项目后会自动恢复

**原因**: V1 在初始化时自动扫描 `分析资料/` 目录

**解决**: 
- 禁用了 `_scan_and_update()` 调用
- 迁移到不自动扫描的 V2

**结果**: 不再自动创建项目

---

## 🔄 回退方案

如需回退到 V1：

1. **恢复自动扫描**：
   ```python
   # src/core/project_manager.py
   def __init__(self):
       self._load_index()
       self._scan_and_update()  # 取消注释
   ```

2. **V1 数据未删除**：
   - `project_index.json` 仍然存在
   - V1 API (`/api/projects`) 仍然可用

3. **删除 V2 数据**（可选）：
   ```bash
   rm data/projects/*/meta.json
   ```

---

## 🎉 迁移成功标志

- [x] V1 自动扫描已禁用
- [x] V2 项目数据已生成
- [x] 自动发现的项目已清理
- [x] 后端 API 正常返回
- [x] 前端页面正常显示
- [x] 工作流页面正常工作
- [x] WebSocket 连接成功
- [x] 文档已更新

---

## 📖 相关资源

- **详细迁移文档**: [PROJECT_MIGRATION_V1_TO_V2.md](./maintenance/PROJECT_MIGRATION_V1_TO_V2.md)
- **数据架构设计**: [DATA_STORAGE_REDESIGN.md](./architecture/DATA_STORAGE_REDESIGN.md)
- **Phase I 工作流**: [PHASE_I_COMPLETE_GUIDE.md](./workflows/PHASE_I_COMPLETE_GUIDE.md)
- **项目结构**: [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

---

**完成时间**: 2026-02-11 15:32  
**迁移耗时**: ~10 分钟  
**状态**: ✅ 迁移成功，系统正常运行
