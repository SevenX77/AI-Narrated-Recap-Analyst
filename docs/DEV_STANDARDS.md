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

3.  **DRY 原则 (Don't Repeat Yourself)**:
    - 相同的逻辑只写一次，通过函数/类复用
    - 禁止在多处重复实现相同的分析、转换或验证逻辑
    - 重复的代码必须提取为工具函数或独立工具类

4.  **单一数据源 (Single Source of Truth)**:
    - 每个数据只有一个计算来源，其他地方通过引用获取
    - 禁止在多处重新计算相同的数据
    - 工具的输出结果应该被保存和复用，而不是重新计算

5.  **计算顺序原则 (Correct Processing Order)**:
    - 先收集所有输入 → 验证数据 → 一次性处理 → 返回结果
    - 禁止"处理-修改-重新处理"模式
    - 避免中途修改已计算的数据

## 2. 目录结构 (Directory Structure)

```text
src/
├── api/            # FastAPI后端服务
│   ├── main.py               # API入口
│   ├── routes/               # API路由
│   │   ├── projects.py       # 项目管理API（V1）
│   │   ├── projects_v2.py    # 项目管理API（V2）⭐ 推荐
│   │   └── workflows.py      # 工作流API
│   ├── schemas/              # API数据模型
│   └── services/             # 业务服务层
├── core/           # 核心抽象层 (Base Classes, Interfaces, Config, Schemas)
│   ├── schemas_novel/        # 小说相关数据模型（已拆分）⭐
│   │   ├── basic.py          # 基础数据结构
│   │   ├── segmentation.py   # 分段相关
│   │   ├── annotation.py     # 标注相关
│   │   ├── system.py         # 系统元素相关
│   │   └── validation.py     # 验证相关
│   ├── schemas_script.py     # 脚本相关数据模型
│   ├── schemas_alignment.py  # 对齐相关数据模型
│   ├── schemas_project.py    # 项目相关数据模型
│   └── ...
├── tools/          # 独立工具库 (Stateless, Reusable)
├── agents/         # 智能体实现 (Stateful, LLM-driven)
├── workflows/      # 业务流程编排 (Orchestration)
│   ├── novel_processing_workflow.py   # 小说处理工作流
│   ├── script_processing_workflow.py  # 脚本处理工作流
│   └── preprocess_service.py          # 预处理服务⭐
├── modules/        # 业务逻辑模块 (Alignment, etc.)
├── utils/          # 通用辅助函数 (Logging, Config)
├── prompts/        # Prompt 模板 (YAML/JSON)
└── main.py         # 入口文件
docs/
├── architecture/   # 架构设计与逻辑文档 (必须与代码同步)
├── maintenance/    # 维护性文档 (清理报告、变更记录、迁移日志)
├── ui/             # 前端UI文档
└── api/            # 自动生成的 API 文档 (可选)
root/
├── frontend-new/   # 前端项目（React + Vite + shadcn UI）⭐ 当前使用
├── data/           # 项目数据存储 (Projects, Raw Data, Artifacts)
├── output/         # 系统输出 (Logs, Operation History)
├── config/         # 配置文件目录
└── scripts/        # 运维脚本 (Validation, Migration)
```

### 📍 文档管理规范

**保持根目录简洁是强制要求！**

| 文档类型 | 必须放置位置 | 示例 | 说明 |
|---------|------------|------|------|
| 核心文档 | `docs/` 根目录 | DEV_STANDARDS.md, PROJECT_STRUCTURE.md | 永久性、全局性的文档 |
| 版本变更 | `CHANGELOG.md`（根目录） | - | 版本发布记录，遵循 Keep a Changelog 规范 |
| 模块文档 | `docs/{module}/` | docs/core/README.md | 各模块的技术参考文档 |
| 归档文档 | `archive/docs/` | archive/docs/v2_architecture/ | 旧版本文档归档 |

**❌ 严格禁止**：
- ❌ 在根目录创建过程性/总结性文档（如 PROJECT_RESET_SUMMARY.md, MIGRATION_SUMMARY.md）
- ❌ 在根目录创建任何除 CHANGELOG.md 外的 `.md` 或 `.txt` 文档
- ❌ 在 `docs/` 创建"使用教程"类文档
- ❌ 在根目录创建临时测试文件

### 📝 文档内容规范

**文档目的**: 文档是代码的技术参考，不是使用教程。

**必须包含**：
1. **接口定义**: 输入输出参数、类型、格式
2. **实现逻辑**: 核心算法、处理流程、设计思路
3. **依赖关系**: 调用了哪些工具/模块/Agent
4. **数据模型**: 使用的Schema定义

**禁止包含**：
- ❌ "如何使用"教程式内容
- ❌ "运行步骤"操作指南
- ❌ 过程性记录（"我做了什么"）
- ❌ 总结性报告

**文档示例结构**：
```markdown
# ToolName

## 职责 (Responsibility)
简述该工具的单一职责

## 接口 (Interface)
### 输入 (Input)
- 参数1: 类型, 说明
- 参数2: 类型, 说明

### 输出 (Output)
返回值类型和结构说明

## 实现逻辑 (Implementation Logic)
1. 步骤1: 做什么，为什么
2. 步骤2: 调用哪个工具/函数
3. 步骤3: 如何处理结果

## 依赖 (Dependencies)
- Schema: 使用的数据模型
- Tools: 依赖的其他工具
- Config: 需要的配置项

## 示例代码 (Code Example)
```python
# 仅展示接口调用，不是完整使用流程
tool = ToolName(config)
result = tool.execute(input_data)
```
```

### 📋 CHANGELOG 管理规范

**格式**: 遵循 [Keep a Changelog](https://keepachangelog.com/) 规范

**何时更新**:
- ✅ 发布新版本时（必须）
- ✅ 新增重要功能（Added）
- ✅ 修改破坏性接口（Changed）
- ✅ 废弃功能（Deprecated）
- ✅ 移除功能（Removed）
- ✅ 修复Bug（Fixed）

**版本号规则**: 遵循 [Semantic Versioning](https://semver.org/)
- 主版本号: 不兼容的 API 修改
- 次版本号: 向下兼容的功能新增
- 修订号: 向下兼容的Bug修复

**不应记录**:
- ❌ 每次代码提交
- ❌ 内部重构（除非影响API）
- ❌ 文档更新（除非是重大文档结构变更）
- ❌ 配置调整

## 2.1 前端目录 (Frontend Directory)

```text
frontend-new/                # 当前使用的前端项目（React + Vite + shadcn UI）
├── src/
│   ├── components/          # UI组件（shadcn）
│   ├── pages/               # 页面组件
│   │   ├── Dashboard.tsx           # 项目列表
│   │   ├── ProjectDetailPage.tsx  # 项目详情
│   │   ├── NovelViewerPage.tsx    # 小说查看器
│   │   ├── ScriptViewerPage.tsx   # 脚本查看器
│   │   ├── WorkflowPage.tsx       # 工作流页面
│   │   └── SettingsPage.tsx       # 设置页面
│   ├── api/                 # API客户端
│   │   ├── projectsV2.ts    # V2项目API
│   │   └── workflows.ts     # 工作流API
│   ├── types/               # TypeScript类型定义
│   └── lib/                 # 工具函数
├── public/                  # 静态资源
└── package.json
```

**注意**: 
- ✅ 当前使用 `frontend-new/` 目录
- ⚠️ 旧的 `frontend/` 目录已废弃，可以删除

## 3. 模块定义规范 (Module Specifications)

### 3.1 Tools (工具)
- 继承自 `src.core.interfaces.BaseTool`。
- 必须实现 `execute` 方法。
- 输入输出必须强类型 (Type Hinting)。
- **禁止** 在 Tool 内部直接调用 Agent。

**现有工具**:

**小说处理工具**:
- `NovelImporter`: 小说导入与规范化（编码检测、格式清理）
- `NovelMetadataExtractor`: 元数据提取（标题、作者、标签、简介）**[支持双LLM]** 默认 DeepSeek v3.2 标准
- `NovelChapterDetector`: 章节边界检测与信息提取
- `NovelSegmenter`: 小说叙事功能分段分析（纯LLM驱动，Two-Pass）**[支持双LLM]** 默认 Claude ⭐ **推荐使用**
- `NovelAnnotator`: 小说章节标注（事件提取、设定关联、功能标签）**[Two-Pass]** ⭐
- `NovelTagger`: 功能标签生成（在NovelAnnotator基础上增强标签）
- `NovelValidator`: 小说数据验证（结构、完整性、质量检查）

**小说系统元素工具**:
- `NovelSystemDetector`: 系统元素检测（从标注结果中识别新元素）⭐
- `NovelSystemAnalyzer`: 系统元素分析（深度分析系统特性）
- `NovelSystemTracker`: 系统元素追踪（跨章节追踪系统元素变化）

**脚本处理工具**:
- `SrtImporter`: SRT字幕文件导入
- `SrtTextExtractor`: SRT文本提取与合并 **[支持双LLM]** 默认 DeepSeek v3.2 标准
- `ScriptSegmenter`: 脚本语义分段（ABC分类法，Two-Pass）**[支持双LLM]** 默认 DeepSeek v3.2 标准 ⭐
- `ScriptValidator`: 脚本数据验证

**小说-脚本对齐工具**:
- `NovelScriptAligner`: 小说与脚本对齐（改编分析）

**Hook检测工具**:
- `HookDetector`: Hook检测（开头爆点识别）
- `HookContentAnalyzer`: Hook内容分析（详细分析Hook特性）

**归档工具**:
- *(归档)* `NovelChapterProcessor`: 小说章节拆分与简介提取
- *(归档)* `IntroductionValidator`: 简介质量验证
- *(归档)* `SrtScriptProcessor`: SRT字幕处理（支持有/无小说参考两种模式）
- *(归档)* `NovelChapterAnalyzer`: 小说章节功能段分析（功能段级别）
- *(归档)* `NovelSegmentationAnalyzer`: 小说分段深度分析（自然段级别）
- *(归档)* `ScriptSegmentAligner`: Script-Novel精确对齐与改编分析
- *(归档)* `KeyInfoExtractor`: 关键信息提取与汇总
- ~~`NovelSegmentationTool`~~: 已废弃（规则分段，质量不达标）→ 归档到 `archive/v2_deprecated/`

### 3.2 Agents (智能体)
- 继承自 `src.core.interfaces.BaseAgent`。
- 拥有 `context` (上下文)。
- 通过 `process` 方法处理任务。

### 3.3 Workflows (工作流)
- 继承自 `src.core.interfaces.BaseWorkflow`。
- 定义明确的 `steps` (步骤)。
- 负责错误处理和全局状态管理。

### 3.4 API (后端服务)
- 存放于 `src/api/`。
- 基于 FastAPI 构建的 RESTful API。
- **路由结构**:
  - `routes/projects.py`: 项目管理（V1，已废弃）
  - `routes/projects_v2.py`: 项目管理（V2，推荐使用）⭐
    - 支持自动预处理
    - 完整的项目生命周期管理
    - 文件上传和状态追踪
  - `routes/workflows.py`: 工作流执行API
- **Schema定义**: 使用 Pydantic 模型定义请求/响应格式
- **错误处理**: 统一的异常处理和错误响应
- **CORS配置**: 允许前端跨域访问

**API示例**:
```
GET  /api/v2/projects           - 获取项目列表
POST /api/v2/projects           - 创建新项目
GET  /api/v2/projects/{id}      - 获取项目详情
POST /api/v2/projects/{id}/files - 上传文件
GET  /api/v2/projects/{id}/preprocess-status - 获取预处理状态
```

### 3.5 Modules (业务模块)
- 存放于 `src/modules/`。
- 负责特定的业务逻辑或算法实现（如 Alignment, Ingestion）。
- 可以包含复杂的逻辑，但不应像 Agent 那样具有自主决策性。
- 应尽量保持无状态或仅依赖输入数据。
- 必须定义清晰的输入输出 Schema。

### 3.5 Core (核心层)
- 存放于 `src/core/`。
- 仅包含：
    - **Interfaces**: 抽象基类 (Base Classes)。
    - **Config**: 配置定义与加载。
    - **Schemas**: Pydantic 数据模型。
    - **Managers**: 资源管理器（如 LLMClientManager, ArtifactManager）。
- **禁止** 包含具体的业务逻辑实现。

**Schemas 拆分规范** ⭐:
- `schemas_novel/`: 小说相关数据模型（已拆分为多个文件）
  - `basic.py`: 基础数据结构（Chapter, Paragraph等）
  - `segmentation.py`: 分段相关（SegmentedChapter, SegmentationResult等）
  - `annotation.py`: 标注相关（AnnotatedChapter, EventTimeline等）
  - `system.py`: 系统元素相关（SystemCatalog, SystemElement等）
  - `validation.py`: 验证相关（ValidationResult等）
- `schemas_script.py`: 脚本相关数据模型（Episode, Segment等）
- `schemas_alignment.py`: 对齐相关数据模型
- `schemas_project.py`: 项目相关数据模型

**核心管理器**:
- `LLMClientManager`: LLM 客户端统一管理
    - 支持多 Provider（Claude、DeepSeek）
    - DeepSeek 多模型支持（v3.2 标准 + v3.2 思维链）
    - 单例模式管理客户端实例
    - 自动记录使用统计（Token 消耗、调用次数）
    - 工具级别灵活指定 Provider 和模型类型
    - 位置：`src/core/llm_client_manager.py`
    - 文档：`docs/core/DUAL_LLM_SETUP.md`
- `ArtifactManager`: 工件版本管理
    - 自动版本化保存工具输出
    - 支持指针文件（_latest）
    - 位置：`src/core/artifact_manager.py`
- `ProjectManager`: 项目数据管理（V1，已有）
- `ProjectManagerV2`: 项目数据管理（V2，推荐使用）⭐
    - 完整的项目生命周期管理
    - 自动目录结构创建
    - 元数据管理
    - 位置：`src/core/project_manager_v2.py`

### 3.6 Workflows (工作流层)
- 存放于 `src/workflows/`。
- 负责编排多个工具完成完整业务流程。

#### 双工作流系统说明 (Dual Workflow Systems)

项目中存在两个独立的工作流跟踪系统，服务于不同目的：

| 系统 | 字段 | 用途 | API | 前端 |
|------|------|------|-----|------|
| **通用工作流** | `workflow_stages` | 预处理、分段、标注等通用流程 | `/api/v2/projects` | Dashboard |
| **Phase I Analyst** | `phase_i_analyst` | 深度分析、对齐等专门工作流 | `/api/v2/projects/{id}/workflow` | ProjectWorkflowPage |

**重要提示**:
- 两个系统**互相独立**，不应混用
- `phase_i_analyst` 是**可选字段**（Optional），需检查是否存在后再访问
- 新项目默认只使用 `workflow_stages`，除非明确启用 Phase I 工作流

**代码示例**:
```python
# ✅ 正确：检查 phase_i_analyst 是否存在
if meta.phase_i_analyst:
    meta.phase_i_analyst.step_1_import.novel_imported = True

# ❌ 错误：直接访问可能为 None
meta.phase_i_analyst.step_1_import.novel_imported = True  # AttributeError!
```

- **现有工作流**:
  - `novel_processing_workflow.py`: 小说完整处理流程
    - 导入 → 元数据提取 → 章节检测 → 分段 → 标注 → 系统检测
  - `script_processing_workflow.py`: 脚本完整处理流程
    - 导入 → 文本提取 → 分段 → 验证
  - `preprocess_service.py`: 预处理服务（后台任务）⭐
    - 自动识别文件类型
    - 异步执行预处理
    - 状态追踪
    - 错误恢复

### 3.7 Utils (工具库)
- 存放于 `src/utils/`。
- 必须是纯函数 (Pure Functions) 或通用 Helper 类。
- **禁止** 包含业务状态或特定业务逻辑。
- **禁止** 循环依赖 Core 或 Modules。

**现有工具**:
- `llm_output_parser.py`: LLM输出解析工具
- `novel_helpers.py`: 小说处理辅助函数

## 4. 工作流与逻辑同步 (Workflow & Logic Sync)

任何时候修改 `src/workflows` 或核心算法时，必须同步更新 `docs/architecture/logic_flows.md`。

## 5. 配置与密钥管理 (Configuration & Secrets)

- **单一数据源**: 所有配置（API Keys, Model Names, Paths）必须通过 `src/core/config.py` 统一管理，禁止在业务代码中硬编码默认值。
- **环境变量**: 敏感信息必须通过 `.env` 文件加载，使用 `pydantic-settings` 或 `os.environ` 读取。
- **禁止提交**: `.env` 文件必须包含在 `.gitignore` 中。

### 5.1 LLM Provider 配置

项目支持多个 LLM Provider 同时使用，通过 `LLMClientManager` 统一管理。

**环境变量配置**：
```bash
# Claude 配置
CLAUDE_API_KEY=sk-xxx
CLAUDE_BASE_URL=https://chatapi.onechats.ai/v1/  # OneChats 通用线路
CLAUDE_MODEL_NAME=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=16000

# DeepSeek 配置
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# DeepSeek 多模型支持
DEEPSEEK_V32_MODEL=deepseek-chat              # v3.2 标准模型（快速、低成本）
DEEPSEEK_V32_THINKING_MODEL=deepseek-reasoner # v3.2 思维链模型（深度推理）
DEEPSEEK_MODEL_NAME=deepseek-chat             # 默认模型
```

**使用方式**：
```python
from src.core.llm_client_manager import get_llm_client, get_model_name

# 获取客户端
client = get_llm_client("claude")  # 或 "deepseek"

# 获取模型名称
claude_model = get_model_name("claude")
deepseek_v32 = get_model_name("deepseek", model_type="v32")           # 标准模型
deepseek_thinking = get_model_name("deepseek", model_type="v32-thinking")  # 思维链模型
deepseek_default = get_model_name("deepseek")  # 默认使用标准模型
```

**功能分工策略**：
- **简单任务**（元数据提取、格式处理）→ DeepSeek v3.2 标准（速度快、成本低）
- **复杂任务**（小说分段、改编分析）→ Claude（质量高、理解强）
- **深度推理**（复杂逻辑、数学推理、代码生成）→ DeepSeek v3.2 思维链（专用推理模型）

**模型选择建议**：
- 80% 的任务 → DeepSeek v3.2 标准模型（快速、便宜）
- 15% 的任务 → Claude（复杂分析）
- 5% 的任务 → DeepSeek v3.2 思维链（深度推理）

详细配置：参见 `docs/core/DUAL_LLM_SETUP.md`

## 6. Prompt 工程规范 (Prompt Engineering)

### 6.1 基础规范

- **Prompt 分离**: 禁止将长 Prompt 字符串硬编码在 Python 函数内部。
- **存储位置**: 将 Prompt 提取到 `src/prompts/` 目录下的 YAML/JSON 文件中。
- **版本控制**: Prompt 的变更应视为代码变更，需进行版本管理。

### 6.2 ⚠️ 避免过拟合 (Anti-Overfitting Rules)

**核心原则**：**不要用数量规定来约束LLM输出，使用逻辑判断规则！**

**❌ 错误示例**：
```yaml
system: |
  你的任务是将章节分段。
  - 段落数量通常在8-12个之间
  - 每个段落应包含3-5句话
  - 标签数量不超过10个
```

**问题**：LLM 会为了凑数而强行分段/合并/添加标签，导致输出质量下降，违背真实的语义结构。

**✅ 正确示例**：
```yaml
system: |
  你的任务是将章节按**叙事功能变化**分段。
  
  分段判断逻辑：
  - 是否跨越了时空（时间/地点变化）？ → 是 → 分段
  - 是否是不同的设定类型？ → 是 → 分段
  - 是否是不同的叙事事件？ → 是 → 分段
  - 只是场景内的细节变化？ → 否 → 不分段，合并
  
  不要为了凑数量而分段！段落数量由实际结构决定。
```

**适用场景**：
- ❌ "段落数量8-12个"
- ❌ "每个标题不超过15个字"
- ❌ "提取5-10个关键词"
- ❌ "生成3个主要冲突"
- ✅ "按时空变化分段"
- ✅ "标题需概括核心功能，长度自然"
- ✅ "提取所有关键信息（不限数量）"
- ✅ "识别所有主要冲突"

**调试原则**：
- 如果输出质量不对，**先优化逻辑规则**，而不是添加数量限制
- 数量限制是最后的手段，且应该是**宽松的范围提示**（如"通常不少于3个"），而非硬性规定

### 6.3 现有Prompt配置

- `introduction_extraction.yaml`: 小说简介智能过滤
- **`novel_chapter_segmentation_pass1.yaml` + `novel_chapter_segmentation_pass2.yaml`**: **小说章节叙事分段（Two-Pass）** ⭐ **推荐使用**
  - 遵循"避免过拟合"原则：用逻辑判断代替数量规定
  - **Two-Pass 策略**：
    * **Pass 1（~90行）**：极简Prompt，初步分段，输出A/B/C分类
    * **Pass 2（~100行）**：用相同原则校验修正，输出最终分段
  - **A/B/C 三类判断法**：
    * **A类-设定**：跳脱时间线（世界观、规则）→ 必须独立
    * **B类-事件**：现实时间线（动作、场景）→ 按时空分段
    * **C类-系统**：次元空间（系统觉醒、系统交互）→ 必须独立
  - **关键区分点**：即使设定被包装成"回忆""思考"，本质仍是设定（A类）
  - **测试数据**（2026-02-09）：
    * Pass 1: 10个段落（基本正确）
    * Pass 2: 11个段落（完全匹配标准）
    * 准确率：100%，解决了原版过度分段问题（14个→11个）
- `novel_chapter_segmentation.yaml`: 旧版单Pass（286行，已废弃，存在过度分段问题）
- `novel_chapter_functional_analysis.yaml`: 小说章节功能段分析（叙事功能级别）
- `novel_segmentation_analysis.yaml`: 小说分段深度分析（自然段级别）
- `srt_script_processing_with_novel.yaml`: SRT处理（有小说参考）
- `srt_script_processing_without_novel.yaml`: SRT处理（无小说参考，智能实体识别）
- `layered_extraction.yaml`: 分层对齐的情节节点提取
- `script_alignment_analysis.yaml`: Script-Novel对齐与改编分析
- 其他分析和对齐相关prompts...

### 6.4 Two-Pass LLM调用原则 (强制) ⭐

**核心原则**：所有LLM任务必须使用Two-Pass策略，确保输出准确性。

#### 6.4.1 什么是Two-Pass？

Two-Pass策略将复杂的LLM任务拆分为两个独立的LLM调用：

1. **Pass 1（初步处理）**：
   - 使用简化的Prompt
   - 专注于单一任务（如分段、分类）
   - 输出结构化结果

2. **Pass 2（校验修正）**：
   - 使用相同的判断原则
   - 检查Pass 1的输出是否符合规则
   - 修正错误，或确认无需修改

#### 6.4.2 为什么使用Two-Pass？

**问题**：复杂的单Pass Prompt容易导致：
- 过度分段/合并（为了凑数量）
- 规则理解不准确（Prompt过长）
- 输出质量不稳定

**解决**：Two-Pass策略的优势：
- ✅ 每个Pass的Prompt更简洁（<100行）
- ✅ 任务明确（Pass 1生成，Pass 2校验）
- ✅ 准确度提升（100% vs 78%）
- ✅ Prompt易维护（两个简单Prompt vs 一个复杂Prompt）

#### 6.4.3 何时使用Two-Pass？

**必须使用Two-Pass的任务**：
- ✅ 复杂的结构化分段任务（小说章节分段、脚本分段）
- ✅ 需要严格规则约束的分类任务
- ✅ 输出结果需要与明确标准对比验证的任务

**可以单次调用的任务**：
- ⚠️ 简单的信息提取（元数据、标签）
- ⚠️ 格式转换和文本处理
- ⚠️ 创意生成和总结任务

**注意**：即使是简单任务，如果准确性要求高，也建议使用Two-Pass。

#### 6.4.4 Two-Pass实现模式

**Prompt文件结构**：
```
src/prompts/
├── task_name_pass1.yaml  # Pass 1: 初步处理
└── task_name_pass2.yaml  # Pass 2: 校验修正
```

**代码实现模式**：
```python
def _twopass_processing(self, input_data):
    # Pass 1: 初步处理
    prompt_pass1 = load_prompts("task_name_pass1")
    result_pass1 = llm_client.call(
        prompt=prompt_pass1,
        input=input_data
    )
    
    # Pass 2: 校验修正
    prompt_pass2 = load_prompts("task_name_pass2")
    result_pass2 = llm_client.call(
        prompt=prompt_pass2,
        input={
            "original_data": input_data,
            "pass1_result": result_pass1
        }
    )
    
    # 判断是否需要修正
    if "无需修改" in result_pass2:
        return result_pass1
    else:
        return result_pass2
```

#### 6.4.5 LLM输出格式规范

**禁止让LLM直接输出JSON**！
- ❌ 问题：JSON格式难以解析，容易出错（括号、引号、转义字符）
- ✅ 解决：LLM输出结构化文本，代码解析生成JSON

**推荐的LLM输出格式**：

**方案1：行号范围（推荐）** ⭐
```markdown
- **段落1（B类-事件）**：收音机播报上沪沦陷
  行号：1-5

- **段落2（A类-设定）**：诡异爆发背景
  行号：6-10
```

**优势**：
- 简洁易解析
- 避免文本匹配问题
- 可精确定位段落边界

**代码解析示例**：
```python
# 正则匹配段落头部
paragraph_pattern = r'^\- \*\*段落(\d+)（([ABC])类.*?）\*\*：(.+?)$'
line_range_pattern = r'^\s*行号[：:]\s*(\d+)-(\d+)'

# 解析后根据行号从原文提取内容
chapter_lines = chapter_content.split('\n')
paragraph_content = '\n'.join(chapter_lines[start_line-1:end_line])
```

**方案2：标记列表（备选）**
```markdown
1. **类型：B** | 描述：收音机播报 | 优先级：P0
2. **类型：A** | 描述：诡异爆发背景 | 优先级：P1
```

#### 6.4.6 设计原则

1. **Prompt分离**：Pass 1和Pass 2使用独立的Prompt文件
2. **原则一致**：Pass 2使用与Pass 1**相同的分类/判断原则**
3. **明确职责**：Pass 1专注生成，Pass 2专注校验
4. **结果验证**：Pass 2必须输出修正说明或"无需修改"
5. **输出格式**：LLM输出结构化文本，代码解析生成JSON

#### 6.4.7 成本与性能

**性能对比（实测数据）**：

| 方案 | LLM调用次数 | Token消耗 | 准确度 | Prompt维护性 |
|-----|-----------|----------|--------|------------|
| 单Pass（286行） | 1次 | ~16000 | 78% | 难 |
| Two-Pass（90+100行） | 2次 | ~16000 | 100% | 易 |

**结论**：
- 虽然调用2次，但每次Prompt更简洁，总Token消耗相当
- 准确度显著提升（78% → 100%）
- Prompt维护性大幅提升（两个简单Prompt vs 一个复杂Prompt）

#### 6.4.8 现有Two-Pass实现

- ✅ **NovelSegmenter**（小说章节分段）
  - 文件：`novel_chapter_segmentation_pass1.yaml` + `pass2.yaml`
  - 准确率：100%（11个段落，完全匹配标准）
  
- 🚧 **待改造的工具**（按优先级）：
  1. ScriptSegmenter（脚本分段）
  2. NovelMetadataExtractor（元数据提取）
  3. SrtTextExtractor（字幕文本提取）

### 6.5 避免Prompt污染：独立Pass策略 (Anti-Prompt-Pollution) ⭐⭐⭐

**核心原则**：**当需要在现有工具上添加新任务时，优先使用独立的新Pass，而非集成到现有Pass中。**

#### 6.5.1 什么是Prompt污染？

**Prompt污染**是指在一个已经稳定的Prompt中添加新任务，导致：
- ❌ 原有任务的质量下降
- ❌ LLM注意力分散，顾此失彼
- ❌ 输出格式复杂化，解析困难
- ❌ 破坏已验证的工具稳定性

**典型场景**：
```python
# ❌ 错误做法：在Pass 2中添加系统检测任务
Pass 2 (设定关联):
  - 任务1: 关联A类设定到事件（BF/BT/AF）
  - 任务2: 构建累积知识库
  - 任务3: 检测新系统元素 ← 新增任务，污染了Pass 2
```

#### 6.5.2 何时应该使用独立Pass？

**强制使用独立Pass的场景**：

1. **现有工具已验证稳定**
   - 工具已通过测试，输出质量稳定
   - 修改会破坏已有的验证结果

2. **新任务与现有任务逻辑独立**
   - 新任务不依赖现有任务的中间结果
   - 新任务的输出不影响现有任务的输出

3. **现有Prompt已经复杂**
   - Prompt超过80行
   - 包含多个子任务或复杂规则

4. **新任务的输出格式不同**
   - 需要解析不同的输出结构
   - 会增加解析逻辑的复杂度

#### 6.5.3 独立Pass vs 集成Pass：成本对比

**案例：NovelAnnotator + 系统元素检测**

**方案A：集成到Pass 2**
```
NovelAnnotator:
  - Pass 1: 事件聚合
  - Pass 2: 设定关联 + 系统检测 ← 污染
  
成本：
  - LLM调用：2次
  - 单章成本：$0.06
  - 风险：⚠️ 破坏设定关联质量
```

**方案B：独立Pass 3** ✅
```
NovelAnnotator:
  - Pass 1: 事件聚合
  - Pass 2: 设定关联
  
NovelSystemDetector (新工具):
  - Pass 3: 系统检测（独立）
  
成本：
  - LLM调用：3次
  - 单章成本：$0.08 (+$0.02)
  - 风险：✅ 保护原有工具稳定性
```

**结论**：
- 成本增加：$0.02/章（100章仅$2）
- 质量保证：NovelAnnotator保持100%准确率
- 架构清晰：符合Single Responsibility原则

#### 6.5.4 独立Pass设计要点

**1. 输入最小化**
```python
# ✅ 只提取必要的输入信息
def execute(self, annotated_chapter: AnnotatedChapter, system_catalog: SystemCatalog):
    # 提取事件摘要（不需要完整内容）
    events_summary = [e.event_summary for e in annotated_chapter.event_timeline.events]
    
    # 提取C类段落（系统交互场景）
    c_class_paragraphs = [p for p in segmentation if p.class_type == "C"]
```

**2. Prompt简洁化**
```yaml
# ✅ Pass 3的Prompt应该<50行
system: |
  你是系统元素识别专家。根据已有系统目录，识别新元素。

user_template: |
  【系统目录】{system_catalog_summary}
  【本章事件】{events_summary}
  【C类段落】{c_class_paragraphs}
  
  任务：识别未在目录中的新元素。
  输出格式：
  新元素 → SC00X（归类到：类别名）
```

**3. 输出结构化**
```python
# ✅ 输出简单、易解析
class SystemUpdateResult(BaseModel):
    new_elements: List[str]  # ["弩箭 → SC003", "干粮 → SC002"]
    catalog_updated: bool
```

#### 6.5.5 决策流程图

```
新需求：添加XX功能
        ↓
  现有工具是否稳定？
    ├─ YES → 是否逻辑独立？
    │         ├─ YES → ✅ 使用独立Pass（新工具）
    │         └─ NO  → 评估集成可行性
    │                   ├─ 复杂度低 → ⚠️ 可集成，需充分测试
    │                   └─ 复杂度高 → ✅ 使用独立Pass
    └─ NO  → 可以集成到现有Pass
```

#### 6.5.6 实施案例

**✅ 正确案例：NovelSystemDetector**
```python
# 系统检测作为独立工具
class NovelSystemDetector(BaseTool):
    def execute(self, annotated_chapter, system_catalog):
        # Pass 3: 独立的系统元素检测
        return SystemUpdateResult(...)
```

**❌ 错误案例：污染NovelAnnotator**
```python
# ❌ 不要这样做
class NovelAnnotator(BaseTool):
    def _pass2_setting_correlation(self, ...):
        # Pass 2: 设定关联
        # 同时做系统检测 ← 污染！
```

#### 6.5.7 成本权衡原则

**何时可以接受集成**：
- 成本增加显著（>$0.10/章）
- 新任务极其简单（<5行Prompt）
- 输出格式完全一致

**何时必须独立**：
- 成本增加可控（<$0.05/章）✅
- 现有工具已验证稳定 ✅
- 符合Single Responsibility原则 ✅

**黄金法则**：
> 当成本增加<$0.05/章时，优先选择独立Pass以保证架构清晰和质量稳定。

#### 6.5.8 现有独立Pass实现

- ✅ **NovelSystemDetector**（系统元素检测，2026-02-09）
  - 输入：AnnotatedChapter + SystemCatalog
  - 输出：SystemUpdateResult（新元素列表）
  - 成本：+$0.02/章
  - 设计理由：避免污染NovelAnnotator的Pass 2

## 7. 错误处理与日志 (Error Handling & Logging)

### 7.1 基础规范

- **禁止 Print**: 生产环境代码禁止使用 `print()`，必须使用 `logging` 模块。
- **结构化日志**: 日志应包含 `timestamp`, `module`, `level`, `message`。
- **操作日志 (Operation Log)**:
    - 关键的文件生成操作必须记录到 `output/operation_history.jsonl`。
    - 格式: `[Time] [ProjectID] [Action] -> [Output File]`。
- **重试机制**: 对于 LLM 调用和网络请求，必须实现指数退避 (Exponential Backoff) 的重试机制。

### 7.2 错误处理规范

**核心原则**：所有可能失败的操作必须有错误处理机制。

#### 7.2.1 LLM 调用错误处理

```python
# ✅ 正确：完整的错误处理
try:
    result = llm_client.call(prompt=prompt, input=data)
except TimeoutError as e:
    logging.error(f"LLM调用超时: {e}")
    # 使用重试机制
    result = retry_manager.retry(llm_client.call, ...)
except APIError as e:
    logging.error(f"API错误: {e}")
    # 记录错误并抛出
    raise ProcessingError(f"LLM调用失败: {e}")
```

#### 7.2.2 数据验证

```python
# ✅ 所有工具必须验证输入
class BaseTool:
    def execute(self, **kwargs):
        # 1. 验证输入
        self._validate_input(kwargs)
        
        # 2. 执行处理
        result = self._process(**kwargs)
        
        # 3. 验证输出
        self._validate_output(result)
        
        return result
    
    def _validate_input(self, kwargs):
        """验证输入参数的完整性和有效性"""
        required_fields = self.get_required_fields()
        for field in required_fields:
            if field not in kwargs:
                raise ValueError(f"缺少必需参数: {field}")
    
    def _validate_output(self, result):
        """验证输出结果的格式和内容"""
        if not result:
            raise ValueError("处理结果为空")
```

#### 7.2.3 配置项默认值

```python
# ❌ 错误：可能导致 NaN 或异常
rate = config.rate / 100

# ✅ 正确：提供默认值
rate = (config.rate if config.rate is not None else 80) / 100

# ✅ 更好：使用 ?? 运算符（Python 3.8+）
rate = (config.rate ?? 80) / 100

# ✅ Pydantic 模型中定义默认值
class Config(BaseModel):
    rate: float = 80.0  # 默认值
    max_tokens: int = 16000
```

## 8. 数据契约 (Data Contracts)

- **Schema 定义**: 模块间传递的数据结构（如 `SceneAnalysis`, `NarrativeEvent`）应定义为 Pydantic Models。
- **统一位置**: 统一放置在 `src/core/schemas.py` 中，禁止散落在各个 Agent 文件里。

## 9. 代码组织与文件大小规范 (Code Organization & File Size)

### 9.1 文件大小限制

**核心规则**：所有文件超过 **200 行**时必须考虑拆分

#### 拆分策略

```
按功能职责进行模块化：
- schemas.py → schemas_novel.py, schemas_script.py, schemas_alignment.py ✅ (已实施)
- 大型工具类 → 拆分为多个子模块或提取辅助函数到 utils
```

#### 当前需要优化的文件（体检发现）

**高优先级（>800行）**：
- `schemas_novel.py`: 1824 行 ❌ **需要拆分**
- `novel_processing_workflow.py`: 1828 行 ❌ **需要拆分**
- `novel_annotator.py`: 888 行 ❌ **需要拆分**
- `schemas_script.py`: 846 行 ⚠️ **接近阈值**

**中优先级（500-800行）**：
- `novel_script_aligner.py`: 714 行 ⚠️ **需要关注**
- `script_processing_workflow.py`: 711 行 ⚠️ **需要关注**
- `script_segmenter.py`: 550 行 ⚠️ **需要关注**

#### 拆分建议

**schemas_novel.py（1824行）** → 拆分为：
```
src/core/schemas_novel/
├── __init__.py
├── basic.py          # 基础数据结构
├── segmentation.py   # 分段相关
├── annotation.py     # 标注相关
└── analysis.py       # 分析相关
```

**novel_processing_workflow.py（1828行）** → 拆分为：
```
src/workflows/novel_processing/
├── __init__.py
├── base.py           # 基础工作流
├── preprocessing.py  # 预处理步骤
├── segmentation.py   # 分段步骤
└── annotation.py     # 标注步骤
```

### 9.2 组件风格

- ✅ 优先使用**函数式编程**风格（纯函数）
- ✅ 将复杂逻辑提取为**独立函数**
- ✅ 避免大段重复代码，高效使用工具函数

## 10. 代码质量保证 (Quality Assurance)

### 10.1 防止 Bug 的措施（优先级排序）

| 措施 | 自动化程度 | 强制执行 | 维护成本 | 推荐度 |
|------|-----------|---------|---------|--------|
| **工具类封装** | ⭐⭐⭐⭐⭐ | ✅ 强制 | 低 | ⭐⭐⭐⭐⭐ |
| **运行时验证** | ⭐⭐⭐⭐⭐ | ✅ 强制 | 低 | ⭐⭐⭐⭐⭐ |
| **TypeScript/Pydantic 类型** | ⭐⭐⭐⭐⭐ | ✅ 强制 | 低 | ⭐⭐⭐⭐⭐ |
| **Pre-commit Hook** | ⭐⭐⭐⭐ | ✅ 强制 | 中 | ⭐⭐⭐⭐ |
| **单元测试** | ⭐⭐⭐ | ⚠️ 可跳过 | 高 | ⭐⭐⭐ |
| **Code Review** | ⭐ | ❌ 不强制 | 高 | ⭐⭐ |

### 10.2 代码审查清单 (Code Review Checklist)

#### 提交前自查

- [ ] **没有重复的计算逻辑**
  - 相同的处理逻辑只出现一次
  - 通过函数/工具类复用处理逻辑

- [ ] **没有"处理-修改-重新处理"模式**
  - 不存在先处理后修改的情况
  - 所有处理都在确定输入后一次性完成

- [ ] **处理顺序正确**
  - 先收集输入 → 再处理 → 最后输出
  - 没有循环依赖

- [ ] **数据依赖清晰**
  - 依赖的数据已全部确定
  - 没有使用未初始化的值

#### LLM 工具专项检查

- [ ] **配置项有默认值**
  - 所有配置中的值都有 fallback
  - 使用 Pydantic 默认值防止 `None`

- [ ] **LLM 调用有错误处理**
  - 所有 LLM 调用都在 try-except 中
  - 使用重试机制处理暂时性失败

- [ ] **输出格式验证**
  - 验证 LLM 输出是否符合预期格式
  - 检查必需字段是否存在

#### 工作流专项检查

- [ ] **工具调用不重复**
  - 相同输入不多次调用相同工具
  - 中间结果保存到 ArtifactManager

- [ ] **状态管理清晰**
  - 工作流状态明确
  - 错误状态有明确处理

- [ ] **日志记录完整**
  - 关键步骤有日志记录
  - 错误信息详细可追溯

## 11. 版本管理规范 (Version Control)

### 11.1 语义化版本规则

```
v主版本号.次版本号.修订号
```

| 变更类型 | 更新规则 | 示例 |
|---------|---------|------|
| **重大更新** | 主版本号 +1 | `1.0.0` → `2.0.0` |
| 不兼容的修改、架构重构 | 次版本号和修订号归零 | |
| **功能新增** | 次版本号 +1 | `1.0.0` → `1.1.0` |
| 向下兼容的新功能 | 修订号归零 | |
| **问题修复** | 修订号 +1 | `1.0.0` → `1.0.1` |
| Bug 修复、小优化 | | |

### 11.2 Git 提交规范

**提交信息格式**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `refactor`: 代码重构（不改变功能）
- `test`: 测试相关
- `chore`: 构建/工具链更新

**示例**：
```
feat(novel-segmenter): 实现 Two-Pass 分段策略

- 添加 Pass 1: 初步分段
- 添加 Pass 2: 校验修正
- 准确率提升至 100%

Closes #123
```

---
*Last Updated: 2026-02-11*
*Updated: 目录结构、工具列表、API架构、前端路径、Schemas拆分*
