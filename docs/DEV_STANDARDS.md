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
├── modules/        # 业务逻辑模块 (Alignment, etc.)
├── utils/          # 通用辅助函数 (Logging, Config)
├── prompts/        # Prompt 模板 (YAML/JSON)
└── main.py         # 入口文件
docs/
├── architecture/   # 架构设计与逻辑文档 (必须与代码同步)
├── maintenance/    # 维护性文档 (清理报告、变更记录、迁移日志)
└── api/            # 自动生成的 API 文档 (可选)
root/
├── data/           # 项目数据存储 (Projects, Raw Data, Artifacts)
├── output/         # 系统输出 (Logs, Operation History)
├── logs/           # 运行日志 (Deprecated, moved to output/)
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

## 3. 模块定义规范 (Module Specifications)

### 3.1 Tools (工具)
- 继承自 `src.core.interfaces.BaseTool`。
- 必须实现 `execute` 方法。
- 输入输出必须强类型 (Type Hinting)。
- **禁止** 在 Tool 内部直接调用 Agent。

**现有工具**:
- `NovelImporter`: 小说导入与规范化（编码检测、格式清理）
- `NovelMetadataExtractor`: 元数据提取（标题、作者、标签、简介）**[支持双LLM]** 默认 DeepSeek v3.2 标准
- `NovelChapterDetector`: 章节边界检测与信息提取
- `NovelSegmenter`: 小说叙事功能分段分析（纯LLM驱动）**[支持双LLM]** 默认 Claude ⭐ **推荐使用**
- `SrtTextExtractor`: SRT文本提取与合并 **[支持双LLM]** 默认 DeepSeek v3.2 标准
- `ScriptSegmenter`: 脚本语义分段 **[支持双LLM]** 默认 DeepSeek v3.2 标准
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

### 3.4 Modules (业务模块)
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

**核心管理器**:
- `LLMClientManager`: LLM 客户端统一管理
    - 支持多 Provider（Claude、DeepSeek）
    - DeepSeek 多模型支持（v3.2 标准 + v3.2 思维链）
    - 单例模式管理客户端实例
    - 自动记录使用统计（Token 消耗、调用次数）
    - 工具级别灵活指定 Provider 和模型类型
    - 位置：`src/core/llm_client_manager.py`
    - 文档：`docs/core/DUAL_LLM_SETUP.md`
- `ArtifactManager`: 工件版本管理（已有）
- `ProjectManager`: 项目数据管理（已有）

### 3.6 Utils (工具库)
- 存放于 `src/utils/`。
- 必须是纯函数 (Pure Functions) 或通用 Helper 类。
- **禁止** 包含业务状态或特定业务逻辑。
- **禁止** 循环依赖 Core 或 Modules。

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
*Last Updated: 2026-02-09*
