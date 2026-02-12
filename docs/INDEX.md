# 文档索引

**最后更新**: 2026-02-13  
**优化说明**: docs/根目录精简至5个顶层文档，模块文档移至对应文件夹

---

## 🎯 顶层文档（5个 - 根目录）

### 1. DEV_STANDARDS.md ⭐
**开发规范与架构文档**（最高优先级）

**何时阅读**:
- 编写任何新代码前
- 修改架构时
- 不确定编码规范时

**核心内容**:
- 架构设计原则（Tools/Agents/Workflows）
- 编码标准（Config、Schemas、Prompts）
- Two-Pass工具设计原则
- 避免Prompt污染原则
- LLM选择指南

---

### 2. PROJECT_STRUCTURE.md
**项目结构说明**

**何时阅读**:
- 初次了解项目时
- 不确定文件应该放在哪里时
- 查找特定文件时

**核心内容**:
- 目录组织（src/、docs/、data/）
- 文件查找指南
- 命名规范
- 数据流向

---

### 3. QUICK_START.md
**快速开始指南**

**何时阅读**:
- 初次搭建项目时
- 运行项目时
- 配置环境时

---

### 4. INDEX.md
**文档索引**（本文件）

**核心内容**:
- 完整文档导航
- 场景化快速查找

---

### 5. README.md
**文档中心入口**

---

## 📚 模块文档（按需查阅）

### Tools 模块 - `docs/tools/`

#### tools/README.md ⭐
**工具完整参考**

**何时阅读**:
- 编写新工具前（检查是否已有类似工具）
- 调用现有工具时
- 不确定工具功能时

**核心内容**:
- 17个工具完整列表（Novel/Script/对齐/Hook）
- 工具输入输出、依赖关系、LLM配置
- 复用指南（ArtifactManager、ProjectManager、LLMClientManager）
- 按场景查找工具

---

### Workflows 模块 - `docs/workflows/`

#### workflows/README.md ⭐
**工作流与数据存储完整参考**

**何时阅读**:
- 修改工作流逻辑时
- 调整数据存储结构时
- 不确定数据流转路径时

**核心内容**:
- 3个核心工作流（Novel/Script/Preprocess）
- 数据存储结构（目录设计、命名规范）
- 数据流转路径
- 项目元数据结构（meta.json、chapters.json等）
- 成本估算

---

### UI 模块 - `docs/ui/`

#### ui/UX_PRINCIPLES.md ⭐⭐⭐
**前端用户体验设计原则**（前端开发必读）

**何时阅读**:
- 开发任何前端功能前（必读）
- 设计用户交互时
- Code Review前端代码时

**核心内容**:
- 三大核心原则（操作反馈、认知负担、后悔药）
- 实施检查清单（Toast、错误处理、进度显示）
- 组件设计模式
- 性能和可访问性原则

#### ui/DEVELOPMENT_GUIDE.md
**前端UI开发技术指南**

**何时阅读**:
- 开发前端功能时
- 调用后端API时
- 添加新组件时

**核心内容**:
- 技术栈（React + Vite + shadcn/ui）
- 核心页面设计（Dashboard、ProjectDetailPage等）
- API集成（projectsV2.ts）
- shadcn/ui组件使用
- TypeScript类型定义

---

## 📖 详细文档（按需查阅）

### LLM系统
- `core/LLM_INTEGRATION_GUIDE.md` - LLM集成指南
- `core/LLM_RATE_LIMIT_SYSTEM.md` - 速率限制系统
- `core/ARTIFACT_MANAGER_GUIDE.md` - Artifact版本管理

### 架构设计
- `architecture/logic_flows.md` - 逻辑流程图

### API规范
- `ui/API_SPECIFICATION.md` - API接口详细规范

---

## 🔍 快速查找

### 我需要...

| 需求 | 查看文档 |
|------|---------|
| **编写新工具** | 1. `DEV_STANDARDS.md` (架构规范) <br> 2. `tools/README.md` (检查现有工具) |
| **修改工作流** | 1. `workflows/README.md` (工作流设计) <br> 2. `DEV_STANDARDS.md` (编码规范) |
| **前端开发** | 1. `ui/UX_PRINCIPLES.md` (UX原则) ⭐⭐⭐ <br> 2. `ui/DEVELOPMENT_GUIDE.md` (技术实现) <br> 3. `tools/README.md` (API对接) |
| **调整数据存储** | 1. `workflows/README.md` (存储结构) <br> 2. `core/ARTIFACT_MANAGER_GUIDE.md` (版本管理) |
| **LLM集成** | 1. `DEV_STANDARDS.md` (LLM选择) <br> 2. `core/LLM_INTEGRATION_GUIDE.md` (详细配置) |
| **了解项目** | 1. `PROJECT_STRUCTURE.md` (项目结构) <br> 2. `DEV_STANDARDS.md` (架构原则) |

---

## 📂 文档目录结构

```
docs/
├── 📋 顶层文档（5个 - 根目录）⭐
│   ├── DEV_STANDARDS.md           # 开发规范与架构（最高优先级）
│   ├── PROJECT_STRUCTURE.md       # 项目结构说明
│   ├── QUICK_START.md             # 快速开始指南
│   ├── INDEX.md                   # 文档索引（本文件）
│   └── README.md                  # 文档中心入口
│
├── 📁 模块文档（按模块组织）
│   ├── tools/                     # 工具模块（20+个文档）
│   │   ├── README.md              # 工具完整参考 ⭐
│   │   ├── ROADMAP.md
│   │   ├── novel_*.md             # 小说工具文档
│   │   ├── script_*.md            # 脚本工具文档
│   │   └── ...
│   │
│   ├── workflows/                 # 工作流模块（10个文档）
│   │   ├── README.md              # 工作流与数据存储参考 ⭐
│   │   ├── PHASE_I_COMPLETE_GUIDE.md
│   │   ├── novel_processing_workflow.md
│   │   ├── script_processing_workflow.md
│   │   └── ...
│   │
│   ├── ui/                        # 前端UI模块（8个文档）
│   │   ├── UX_PRINCIPLES.md       # UX设计原则 ⭐⭐⭐（前端必读）
│   │   ├── DEVELOPMENT_GUIDE.md   # 技术开发指南 ⭐
│   │   ├── API_SPECIFICATION.md
│   │   ├── UI_ARCHITECTURE.md
│   │   └── ...
│   │
│   ├── core/                      # 核心系统（7个文档）
│   │   ├── LLM_INTEGRATION_GUIDE.md
│   │   ├── LLM_RATE_LIMIT_SYSTEM.md
│   │   ├── ARTIFACT_MANAGER_GUIDE.md
│   │   └── ...
│   │
│   └── architecture/              # 架构设计
│       └── logic_flows.md
│
└── 📦 归档（archive/docs/ - 84个）
    ├── analysis/                  # 历史分析文档
    ├── summary/                   # 历史总结文档
    ├── planning/                  # 历史规划文档
    └── maintenance/               # 历史维护文档
```

---

## 🎯 文档优化说明（2026-02-12）

### 优化前
- **文档总数**: 143个
- **核心文档**: 无明确定义
- **AI检索效率**: 低（需遍历大量文档）
- **信息密度**: 低（关键信息分散）

### 优化后（2026-02-13）
- **顶层文档**: 5个（仅根目录，全局性文档）
- **模块文档**: 
  - tools/ → README.md（工具参考）
  - workflows/ → README.md（工作流参考）
  - ui/ → UX_PRINCIPLES.md + DEVELOPMENT_GUIDE.md
  - core/ → 7个详细指南
- **归档文档**: 84个（移至archive/）
- **AI检索效率**: 极高（.cursorrules精确路由）
- **文档层次**: 清晰（顶层 → 模块 → 详细）

### 优化方法
1. **场景化路由**: 在.cursorrules中建立"场景→文档"映射
2. **三层文档体系**:
   - 第一层: .cursorrules（入口规范）
   - 第二层: 5个核心文档（主要参考）
   - 第三层: 详细文档（按需查阅）
3. **合并重复内容**: 将多个文档合并为1个核心文档
4. **归档过程性文档**: maintenance/、summary/等移至archive/

---

## 📝 维护规则

### 更新核心文档时
1. **同步更新本INDEX.md**: 如果文档职责变化
2. **同步更新.cursorrules**: 如果场景化路由需要调整
3. **记录更新日期**: 在文档顶部更新"最后更新"

### 创建新文档时
- ❌ **禁止创建新核心文档**（保持5个）
- ✅ 如有必要，添加到`core/`或`ui/`作为详细文档
- ✅ 更新本INDEX.md添加链接

### 删除文档时
- ✅ 移动到`archive/docs/`而非直接删除
- ✅ 更新本INDEX.md移除链接

---

**最后更新**: 2026-02-13  
**顶层文档数量**: 5个（根目录）  
**模块文档数量**: 45+个（tools/workflows/ui/core/）  
**归档文档数量**: 84个
