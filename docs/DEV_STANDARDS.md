# 开发规范与架构文档 (Development Standards & Architecture)

## 0. 最高优先级：文档同步 (Documentation Sync - HIGHEST PRIORITY)

**任何代码变更必须首先体现在文档中。**

- **代码即文档**: 核心逻辑变更必须同步更新 `docs/architecture/` 下的对应文档。
- **强制检查**: 自动化脚本会检查文档的更新时间。如果代码更新了但文档没更新，CI/CD 将会失败。
- **Docstrings**: 所有 Public Class 和 Function 必须包含 Google Style Docstrings。
- **架构图**: 复杂逻辑需在文档中通过 Mermaid 或文字描述清楚数据流向。

## 1. 核心原则 (Core Principles)

1.  **模块化 (Modularity)**: 
    - 系统由 **Tools (工具)**, **Agents (智能体)**, 和 **Workflows (工作流)** 组成。
    - **Tools** 必须是无状态、独立的原子操作（如：下载文件、切割文本）。
    - **Agents** 是有状态的，负责调用 LLM 进行决策或处理，并可以调用 Tools。
    - **Workflows** 是业务逻辑的编排者，负责串联 Agents 和 Tools。
    - 禁止循环依赖。

2.  **职责分离 (Separation of Concerns)**:
    - **Analyst (分析师)**: 唯一职责是 **"理解" (Understanding)**。
        - 输入: 文本 (小说或解说)。
        - 输出: 结构化数据 (Events, Characters)。
        - **禁止**: Analyst 不应知道 "Script" 或 "Alignment" 的存在。
    - **Alignment (对齐引擎)**: 唯一职责是 **"映射" (Mapping)**。
        - 输入: 两组结构化数据 (Novel Events, Script Events)。
        - 输出: 它们之间的关系 (Range/Mapping)。
        - **禁止**: Alignment 不应直接读取原始小说文本进行分析，只处理结构化数据。

## 2. 目录结构 (Directory Structure)

```text
src/
├── core/           # 核心抽象层 (Base Classes, Interfaces, Config, Schemas)
├── tools/          # 独立工具库 (Stateless, Reusable)
├── agents/         # 智能体实现 (Stateful, LLM-driven)
├── workflows/      # 业务流程编排 (Orchestration)
├── utils/          # 通用辅助函数 (Logging, Config)
├── prompts/        # Prompt 模板 (YAML/JSON)
└── main.py         # 入口文件
docs/
├── architecture/   # 架构设计与逻辑文档 (必须与代码同步)
└── api/            # 自动生成的 API 文档 (可选)
```

## 3. 模块定义规范 (Module Specifications)

### 3.1 Tools (工具)
- 继承自 `src.core.interfaces.BaseTool`。
- 必须实现 `execute` 方法。
- 输入输出必须强类型 (Type Hinting)。
- **禁止** 在 Tool 内部直接调用 Agent。

### 3.2 Agents (智能体)
- 继承自 `src.core.interfaces.BaseAgent`。
- 拥有 `context` (上下文)。
- 通过 `process` 方法处理任务。

### 3.3 Workflows (工作流)
- 继承自 `src.core.interfaces.BaseWorkflow`。
- 定义明确的 `steps` (步骤)。
- 负责错误处理和全局状态管理。

## 4. 工作流与逻辑同步 (Workflow & Logic Sync)

任何时候修改 `src/workflows` 或核心算法时，必须同步更新 `docs/architecture/logic_flows.md`。

## 5. 配置与密钥管理 (Configuration & Secrets)

- **单一数据源**: 所有配置（API Keys, Model Names, Paths）必须通过 `src/core/config.py` 统一管理，禁止在业务代码中硬编码默认值。
- **环境变量**: 敏感信息必须通过 `.env` 文件加载，使用 `pydantic-settings` 或 `os.environ` 读取。
- **禁止提交**: `.env` 文件必须包含在 `.gitignore` 中。

## 6. Prompt 工程规范 (Prompt Engineering)

- **Prompt 分离**: 禁止将长 Prompt 字符串硬编码在 Python 函数内部。
- **存储位置**: 将 Prompt 提取到 `src/prompts/` 目录下的 YAML/JSON 文件中。
- **版本控制**: Prompt 的变更应视为代码变更，需进行版本管理。

## 7. 错误处理与日志 (Error Handling & Logging)

- **禁止 Print**: 生产环境代码禁止使用 `print()`，必须使用 `logging` 模块。
- **结构化日志**: 日志应包含 `timestamp`, `module`, `level`, `message`。
- **操作日志 (Operation Log)**:
    - 关键的文件生成操作必须记录到 `output/operation_history.jsonl`。
    - 格式: `[Time] [ProjectID] [Action] -> [Output File]`。
- **重试机制**: 对于 LLM 调用和网络请求，必须实现指数退避 (Exponential Backoff) 的重试机制。

## 8. 数据契约 (Data Contracts)

- **Schema 定义**: 模块间传递的数据结构（如 `SceneAnalysis`, `NarrativeEvent`）应定义为 Pydantic Models。
- **统一位置**: 统一放置在 `src/core/schemas.py` 中，禁止散落在各个 Agent 文件里。

---
*Last Updated: 2026-02-03*
