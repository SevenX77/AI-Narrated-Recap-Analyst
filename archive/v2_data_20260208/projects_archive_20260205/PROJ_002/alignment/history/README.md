# history/ - 版本管理目录

⚠️ **重要：请勿删除此目录！**

---

## 📂 目录用途

此目录是 **ArtifactManager 版本管理机制** 的核心组成部分。

### 版本管理策略

```
主目录 (alignment/)
├── artifact_latest.json     ← 指向最新版本（供系统读取）
└── history/                 ← 此目录
    ├── artifact_v20260204_123456.json
    ├── artifact_v20260204_150000.json
    └── artifact_v20260205_001234.json
```

**工作机制**：
1. 主目录只保留 `*_latest.json` 文件
2. 所有带时间戳的版本文件自动保存在此 `history/` 目录
3. 系统运行时会自动管理此目录

---

## 🔧 由以下模块使用

- `src/core/artifact_manager.py` - `ArtifactManager.save_artifact()`
- 所有使用版本管理的workflow（ingestion, training等）

---

## ⚠️ 重要提示

### ✅ 可以做：
- 查看历史版本文件
- 手动回滚到某个历史版本（复制到主目录并重命名为latest）
- 定期清理过旧的历史版本（如保留最近30天）

### ❌ 不要做：
- **不要删除此目录**（会破坏版本管理机制）
- **不要手动修改此目录中的文件**
- **不要将此目录添加到 .gitignore**

---

## 📊 历史版本管理

如需清理旧版本文件，建议保留策略：
```bash
# 示例：只保留最近30天的版本
find . -name "*_v*.json" -mtime +30 -delete
```

---

**系统设计文档**: `docs/architecture/logic_flows.md`  
**代码实现**: `src/core/artifact_manager.py`  
**最后更新**: 2026-02-05
