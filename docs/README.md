# 项目文档中心

> 🚀 **快速导航**: 查看 **[INDEX.md](./INDEX.md)** 获取完整的文档索引和快速查找入口

本目录包含项目的技术参考文档，结构与代码目录对应。

**文档目的**: 技术参考，非使用教程。用于：
1. 查找工具/模块的接口定义
2. 理解代码实现逻辑
3. 查看依赖关系和数据模型
4. 代码混乱时快速定位和修正

---

## 📚 核心文档（必读）

- **[INDEX.md](./INDEX.md)** 📖 - **完整文档索引**（80+文档导航）
- **[DEV_STANDARDS.md](./DEV_STANDARDS.md)** 🔧 - 开发规范（所有开发者必读）
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** 🏗️ - 项目架构说明

---

## 🎯 2026-02-12 最新优化方案

**快速了解**（3分钟）:
- 📊 [优化方案执行摘要](./planning/OPTIMIZATION_SUMMARY.md) - 关键决策和预期效果
- 🚀 [6天实施计划](./planning/FINAL_OPTIMIZATION_PLAN.md) - 完整的优化方案和代码变更清单

**详细分析**:
- 🔍 [用户需求与数据Gap](./analysis/USER_NEEDS_AND_DATA_GAP.md) - 从用户视角分析需求
- 🎨 [前端缺失功能清单](./analysis/FRONTEND_MISSING_FEATURES.md) - 11个API设计和组件设计

---

## 📁 目录结构

```
docs/
├── INDEX.md                         # 📚 完整文档索引（80+文档导航）
├── README.md                        # 本文件：文档中心入口
├── DEV_STANDARDS.md                 # 开发规范（必读）
├── PROJECT_STRUCTURE.md             # 项目结构说明
│
├── planning/                        # 📋 规划文档
│   ├── OPTIMIZATION_SUMMARY.md      # ⭐ 优化方案执行摘要
│   ├── FINAL_OPTIMIZATION_PLAN.md   # 🚀 6天实施计划
│   └── COMPLETE_WORKFLOW_DESIGN.md  # 完整工作流设计
│
├── analysis/                        # 🔍 分析文档
│   ├── USER_NEEDS_AND_DATA_GAP.md   # 用户需求与数据Gap分析
│   └── FRONTEND_MISSING_FEATURES.md # 前端缺失功能清单
│
├── design/                          # 🏗️ 设计文档
│   ├── DATA_FLOW_REDESIGN.md        # 数据流重新设计
│   ├── DATA_STORAGE_DETAILED.md     # 数据存储详情
│   ├── NAMING_CONVENTIONS.md        # 命名规范
│   └── ...
│
├── summary/                         # 📊 总结文档
│   ├── MIGRATION_SUMMARY_*.md       # 迁移总结
│   └── FRONTEND_INTEGRATION_*.md    # 集成总结
│
├── core/                            # 🔧 核心系统指南
│   ├── ARTIFACT_MANAGER_GUIDE.md    # Artifact版本管理
│   ├── LLM_SYSTEM_COMPLETE.md       # LLM系统完整设计
│   └── ...
│
├── tools/                           # 🛠️ 工具文档
│   ├── ROADMAP.md                   # 工具路线图
│   ├── novel_*.md                   # Novel工具链
│   ├── script_*.md                  # Script工具链
│   └── ...
│
├── workflows/                       # 🔄 工作流文档
│   ├── PHASE_I_COMPLETE_GUIDE.md    # Phase I完整指南
│   ├── novel_processing_workflow.md # 小说处理工作流
│   └── ...
│
├── ui/                              # 📱 前端UI文档
│   ├── WORKFLOW_EXECUTION_GUIDE.md  # 工作流执行指南
│   └── ...
│
├── architecture/                    # 🏛️ 架构文档
│   └── logic_flows.md               # 逻辑流程图
│
└── maintenance/                     # 📊 维护与健康检查
    ├── PROJECT_HEALTH_CHECK_*.md    # 项目健康检查
    └── ...
```

## 📚 文档分类

### 核心文档（根目录）
- **DEV_STANDARDS.md**: 开发规范，所有开发者必读
- **PROJECT_STRUCTURE.md**: 项目整体结构说明
- **TOOLS_ROADMAP.md**: 工具开发路线图和优先级

### 开发指南（guides/）
- 快速开始教程
- 开发规范详解
- 最佳实践

### 模块文档（与代码对应）
每个代码模块都有对应的文档目录：
- `docs/core/` ↔ `src/core/`
- `docs/tools/` ↔ `src/tools/`
- `docs/agents/` ↔ `src/agents/`
- `docs/workflows/` ↔ `src/workflows/`
- `docs/prompts/` ↔ `src/prompts/`
- `docs/utils/` ↔ `src/utils/`

### 归档文档（archive/）
旧版本的文档，仅供参考，不再维护

## 📋 文档规范

### 文档必须包含
1. **职责定义**: 模块/工具的单一职责
2. **接口定义**: 输入输出的类型和格式
3. **实现逻辑**: 核心算法和处理流程
4. **依赖关系**: 使用的Schema、工具、配置

### 文档禁止包含
- ❌ "如何使用"的教程式内容
- ❌ "运行步骤"的操作指南
- ❌ 过程性记录和总结报告

### 文档更新规则
- ✅ 代码变更时必须同步更新对应文档
- ✅ 接口变更必须在文档中体现
- ✅ 新增工具/模块必须先写文档后写代码
- ✅ 重大变更记录在 `CHANGELOG.md`

## 🔍 快速查找

> 💡 **提示**: 使用 [INDEX.md](./INDEX.md) 可以快速定位任何文档！

### 我想了解...

#### 项目整体
- 项目结构和概念 → [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)
- 开发规范 → [DEV_STANDARDS.md](./DEV_STANDARDS.md)
- 完整文档索引 → [INDEX.md](./INDEX.md)

#### 最新优化方案（2026-02-12）
- 快速了解（3分钟）→ [优化方案执行摘要](./planning/OPTIMIZATION_SUMMARY.md) ⭐
- 详细实施计划 → [6天实施计划](./planning/FINAL_OPTIMIZATION_PLAN.md) ⭐
- 用户需求分析 → [用户需求与数据Gap](./analysis/USER_NEEDS_AND_DATA_GAP.md)
- 前端缺失功能 → [前端缺失功能清单](./analysis/FRONTEND_MISSING_FEATURES.md)

#### 数据存储
- 数据流设计 → [数据流重新设计](./design/DATA_FLOW_REDESIGN.md)
- 存储详情 → [数据存储详情](./design/DATA_STORAGE_DETAILED.md)
- 版本管理 → [Artifact管理指南](./core/ARTIFACT_MANAGER_GUIDE.md)
- 命名规范 → [命名规范](./design/NAMING_CONVENTIONS.md)

#### 工作流
- 完整工作流设计 → [完整工作流设计](./planning/COMPLETE_WORKFLOW_DESIGN.md)
- Phase I指南 → [Phase I完整指南](./workflows/PHASE_I_COMPLETE_GUIDE.md)
- 小说处理 → [小说处理工作流](./workflows/novel_processing_workflow.md)
- 脚本处理 → [脚本处理工作流](./workflows/script_processing_workflow.md)

#### 工具使用
- 工具路线图 → [工具路线图](./tools/ROADMAP.md)
- Novel工具 → 查看 [INDEX.md - Novel工具链](./INDEX.md#novel工具链)
- Script工具 → 查看 [INDEX.md - Script工具链](./INDEX.md#script工具链)

#### 前端开发
- 工作流UI → [工作流执行指南](./ui/WORKFLOW_EXECUTION_GUIDE.md)
- 实现总结 → [工作流实现总结](./ui/WORKFLOW_IMPLEMENTATION_SUMMARY.md)
- 缺失功能 → [前端缺失功能](./analysis/FRONTEND_MISSING_FEATURES.md)

#### LLM系统
- 完整设计 → [LLM系统完整设计](./core/LLM_SYSTEM_COMPLETE.md)
- 集成指南 → [LLM集成指南](./core/LLM_INTEGRATION_GUIDE.md)
- 速率限制 → [LLM速率限制系统](./core/LLM_RATE_LIMIT_SYSTEM.md)

## 📝 贡献文档

欢迎改进文档！请遵循：
1. 保持与代码结构一致
2. 使用清晰的标题和格式
3. 提供代码示例
4. 及时更新索引

---

## 📊 文档统计

- **文档总数**: 80+
- **核心文档**: 4个（根目录）
- **规划文档**: 3个
- **分析文档**: 2个
- **设计文档**: 6个
- **工具文档**: 20+个
- **工作流文档**: 15+个
- **维护文档**: 15+个

---

**最后更新**: 2026-02-12  
**维护者**: Project Team  
**文档索引**: [INDEX.md](./INDEX.md)
