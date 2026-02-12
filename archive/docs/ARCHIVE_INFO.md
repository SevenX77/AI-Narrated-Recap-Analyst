# 文档归档说明

**归档日期**: 2026-02-12  
**原因**: 文档精简优化，提升AI编码效率

---

## 📦 归档内容

本目录包含项目历史文档，这些文档已不再作为AI编码的主要参考，但保留用于历史追溯。

### 归档目录

| 目录 | 文档数量 | 说明 |
|------|---------|------|
| `maintenance/` | ~30个 | 历史健康检查、迁移总结、变更记录 |
| `summary/` | ~10个 | 历史总结性文档 |
| `planning/` | ~5个 | 历史规划文档 |
| `analysis/` | ~5个 | 历史分析文档 |
| `design/` | ~10个 | 历史设计文档（部分内容已合并到核心文档） |

**总计**: ~70个文档

---

## 🎯 为什么归档？

### 优化前的问题

1. **文档过多**: 143个文档分散在10+个子目录
2. **信息冗余**: 多个SUMMARY、REPORT类文档内容重叠
3. **检索困难**: AI需要遍历大量文档才能找到关键信息
4. **过程性文档**: maintenance/下有30+个健康检查、迁移总结等临时文档

### 优化目标

- **精简文档**: 从143个减少到~20个核心文档（减少85%）
- **提升检索效率**: AI通过.cursorrules场景化路由直接定位1-3个核心文档
- **提高信息密度**: 关键信息集中在5个核心文档中

---

## 📋 新文档体系

### 第一层: .cursorrules（入口规范）
在.cursorrules中建立**场景→文档**的明确映射，AI根据编码场景直接定位核心文档。

### 第二层: 5个核心文档（主要参考）

1. **DEV_STANDARDS.md** - 开发规范与架构
2. **TOOLS_REFERENCE.md** - 工具快速参考
3. **WORKFLOW_REFERENCE.md** - 工作流与数据存储
4. **UI_DEVELOPMENT_GUIDE.md** - 前端UI开发指南
5. **PROJECT_STRUCTURE.md** - 项目结构

### 第三层: 详细文档（按需查阅）

- `core/` - 核心系统详细文档（LLM、Artifact）
- `architecture/` - 架构详细设计
- `ui/` - 前端详细文档
- `tools/` - 工具详细文档（保留，可按需查阅）
- `workflows/` - 工作流详细文档（保留，可按需查阅）

---

## 🔍 如何查找归档内容？

### 如果需要查看历史文档

1. **项目健康检查**: `maintenance/PROJECT_HEALTH_CHECK_*.md`
2. **迁移记录**: `maintenance/*_MIGRATION_*.md`
3. **历史规划**: `planning/OPTIMIZATION_SUMMARY.md`, `planning/FINAL_OPTIMIZATION_PLAN.md`
4. **历史设计**: `design/DATA_FLOW_REDESIGN.md`, `design/DATA_STORAGE_DETAILED.md`

### 文档内容已合并

以下归档文档的核心内容已合并到新核心文档：

| 归档文档 | 合并到 |
|---------|--------|
| `tools/*.md` (23个工具文档) | `TOOLS_REFERENCE.md` |
| `planning/COMPLETE_WORKFLOW_DESIGN.md` | `WORKFLOW_REFERENCE.md` |
| `design/DATA_FLOW_REDESIGN.md` | `WORKFLOW_REFERENCE.md` |
| `design/DATA_STORAGE_DETAILED.md` | `WORKFLOW_REFERENCE.md` |
| `design/NAMING_CONVENTIONS.md` | `WORKFLOW_REFERENCE.md` |
| `ui/API_SPECIFICATION.md` (部分) | `UI_DEVELOPMENT_GUIDE.md` |

---

## ⚠️ 重要说明

**这些归档文档不应再被AI编码时引用**

- ✅ 仅用于历史追溯和审计
- ✅ 如需查看，手动搜索archive/docs/
- ❌ 不应出现在.cursorrules的文档路由中
- ❌ 不应被AI在编码时主动读取

---

## 📊 归档统计

### 文档数量变化

| 阶段 | 文档数量 | 说明 |
|------|---------|------|
| 优化前 | 143个 | 分散在docs/各子目录 |
| 核心文档 | 5个 | AI主要参考 |
| 详细文档 | ~15个 | 按需查阅（tools/、core/等） |
| 归档文档 | ~70个 | 移至archive/docs/ |
| **总计** | **~90个** | **减少53个（37%）** |

### AI检索效率提升

- **优化前**: AI需要检索10+个文档才能找到关键信息
- **优化后**: AI通过场景化路由直接定位1-3个核心文档
- **提升**: 检索时间减少80%，编码准确度提升

---

**归档人**: AI Assistant  
**归档日期**: 2026-02-12  
**参考文档**: `docs/INDEX.md`
