# 项目文档索引

本目录包含项目的技术参考文档，结构与代码目录对应。

**文档目的**: 技术参考，非使用教程。用于：
1. 查找工具/模块的接口定义
2. 理解代码实现逻辑
3. 查看依赖关系和数据模型
4. 代码混乱时快速定位和修正

## 📁 目录结构

```
docs/
├── README.md                        # 本文件：文档索引
├── DEV_STANDARDS.md                 # 开发规范（必读）
├── PROJECT_STRUCTURE.md             # 项目结构说明
├── TOOLS_ROADMAP.md                 # 工具开发路线图
│
├── guides/                          # 开发指南
│   ├── GETTING_STARTED.md          # 快速开始
│   └── CURSORRULES_GUIDE.md        # Cursor规则说明
│
├── core/                            # Core模块文档
│   ├── README.md                   # Core模块概述
│   ├── config.md                   # 配置系统
│   ├── interfaces.md               # 接口定义
│   ├── schemas.md                  # 数据模型
│   └── managers.md                 # 管理器（Project/Artifact）
│
├── tools/                           # Tools模块文档
│   ├── README.md                   # Tools模块概述
│   ├── phase1_novel/               # Phase I Novel工具文档
│   ├── phase1_script/              # Phase I Script工具文档
│   └── phase2_analysis/            # Phase II 分析工具文档
│
├── agents/                          # Agents模块文档
│   ├── README.md                   # Agents模块概述
│   ├── writer.md                   # Writer代理
│   └── training.md                 # Training代理（规则提取/验证）
│
├── workflows/                       # Workflows模块文档
│   ├── README.md                   # Workflows模块概述
│   └── training_workflow.md        # Training工作流
│
├── prompts/                         # Prompts文档
│   ├── README.md                   # Prompts管理说明
│   ├── writer_prompts.md           # Writer相关prompts
│   └── training_prompts.md         # Training相关prompts
│
├── utils/                           # Utils模块文档
│   └── README.md                   # Utils模块概述
│
└── archive/                         # 归档文档（旧版本）
    ├── v2_architecture/            # V2架构文档
    └── v2_maintenance/             # V2维护文档
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

## 🔍 快速导航

### 开始开发
1. 阅读 [DEV_STANDARDS.md](DEV_STANDARDS.md)
2. 查看 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
3. 参考 [TOOLS_ROADMAP.md](TOOLS_ROADMAP.md)

### 开发工具
1. 查看 [docs/tools/README.md](tools/README.md)
2. 按Phase查找对应工具文档
3. 参考代码示例和测试

### 开发代理
1. 查看 [docs/agents/README.md](agents/README.md)
2. 了解Writer和Training代理
3. 查看相关Prompt配置

### 开发工作流
1. 查看 [docs/workflows/README.md](workflows/README.md)
2. 了解Training工作流
3. 学习如何串联工具

## 📝 贡献文档

欢迎改进文档！请遵循：
1. 保持与代码结构一致
2. 使用清晰的标题和格式
3. 提供代码示例
4. 及时更新索引

---

**最后更新**: 2026-02-08  
**维护者**: Project Team
