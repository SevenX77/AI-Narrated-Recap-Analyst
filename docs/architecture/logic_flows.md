# System Architecture & Logic Flows

## Overview
This document serves as the single source of truth for the system's logic and data flow.

## Core Components

### 1. Project Management
- **Project Index**: `data/project_index.json` maps source folders to unique IDs (e.g., `PROJ_001`).
- **Source Data**: Located in `分析资料/` (Analysis Data), organized by Novel Name.
- **Project Data**: Located in `data/projects/PROJ_XXX/`. Stores all persistent artifacts including raw text, alignment maps, analysis results, and generated scripts.
- **System Output**: Located in `output/`. Stores system logs (`app.log`) and operation history (`operation_history.jsonl`).

### 2. Agent Responsibilities
- **Analyst (`src.agents.deepseek_analyst`)**: 
  - **Role**: Understanding & Extraction.
  - **Input**: Raw Text (Novel or Script).
  - **Output**: Structured Events (SVO), Characters, Scenes.
  - **Note**: Does NOT know about alignment or script generation logic.
  - **Prompts**: Managed in `src/prompts/analyst.yaml`.
- **Writer (`src.agents.deepseek_writer`)**: 
  - **Role**: Creative Writing.
  - **Input**: Novel Context (Chapter-level), Analysis Data.
  - **Output**: Recap Script (JSON/Markdown).
- **Alignment Engine v2 (`src.modules.alignment.deepseek_alignment_engine_v2`)**: 
  - **Role**: 三层数据模型转换 + 两级匹配策略.
  - **Input**: Raw SRT/Novel Text.
  - **Output**: EventAlignment (Event级匹配 + Block链验证) + Quality Report.
  - **核心特性**: 
    - **三层数据模型**: `Sentence` → `SemanticBlock` → `Event`
    - **两级匹配策略**:
      - Level 1: Event级粗匹配（快速定位候选）
      - Level 2: SemanticBlock链细验证（精确确认）
    - **Hook检测器**: 独立模块检测ep01的Hook边界
    - **并发优化**: 支持异步LLM调用
  - **主要方法**:
    - `restore_sentences_from_srt_async`: SRT blocks → Sentences
    - `segment_semantic_blocks_async`: Sentences → Semantic Blocks
    - `aggregate_events_async`: Semantic Blocks → Events
    - `match_events_two_level_async`: 两级匹配主流程
  - **Prompts**: Managed in `src/prompts/alignment.yaml`.
- **Hook Detector (`src.modules.alignment.hook_detector`)**:
  - **Role**: 独立的Hook边界检测.
  - **Input**: Script开头的Semantic Blocks + Novel开头的Semantic Blocks.
  - **Output**: HookDetectionResult (has_hook, linear_start_index, confidence).
  - **特征**: 基于5个特征识别Hook（独立语义、非具象描述、后文连贯、匹配小说开头、匹配序言）.
- **Feedback Agent (`src.agents.feedback_agent`)**:
  - **Role**: Evaluation & Methodology Extraction.
  - **Input**: Alignment Results.
  - **Output**: Feedback Report & Methodology Update.
  - **Prompts**: Managed in `src/prompts/feedback.yaml`.

### 3. 三层数据模型 (v2)

**架构哲学**: 从"事件级"匹配升级到"情节级"匹配，通过层次化的数据结构提升匹配准确性和效率。

#### 3.1 三层结构

```
┌─────────────────────────────────────────────────────────┐
│  Event (事件) - 故事情节级                              │  ← 最高层
│  例如："超市中与剪刀女战斗"                            │
│  - 完整的冲突/情节单元                                  │
│  - 可能跨越多章（Novel）或多个时间段（Script）         │
│  - 包含多个意思块 ↓                                    │
└─────────────────────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────────────────────┐
│  SemanticBlock (意思块) - 情节步骤级                    │  ← 匹配核心
│  例如："发现敌人"、"准备逃跑"、"序列出现对抗"         │
│  - 围绕单一主题的语义连贯段落                          │
│  - 包含1-N个句子                                        │
│  - 提取关键维度：角色、地点、时间                      │
│  - Novel的意思块数量 >= Script的意思块数量             │
│  - 包含多个句子 ↓                                      │
└─────────────────────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────────────────────┐
│  Sentence (句子) - 最小文本单元                         │  ← 最底层
│  例如："我在货架后发现了她"、"她手里握着巨大的剪刀"   │
│  - SRT: 从碎片化文本还原而来（带标点）                 │
│  - Novel: 按标点符号分割                               │
└─────────────────────────────────────────────────────────┘
```

#### 3.2 核心数据模型

定义在 `src/core/schemas.py`:

**Sentence**: 最小文本单元
```python
{
    "text": str,              # 完整句子文本
    "time_range": {           # SRT时间范围（仅Script有）
        "start": "00:00:00,000",
        "end": "00:00:02,000"
    },
    "index": int              # 在原文中的位置
}
```

**SemanticBlock**: 意思块（匹配的核心单元）
```python
{
    "block_id": str,          # 如 "block_ep01_001"
    "theme": str,             # 主题，如 "发现敌人"
    "sentences": [Sentence],  # 包含的句子列表
    "characters": [str],      # 涉及的角色
    "location": str,          # 地点（只提取实际发生的，忽略假设）
    "time_context": str,      # 时间（只提取实际发生的，忽略假设）
    "summary": str,           # 简短概括（50字内）
    "time_range": TimeRange   # SRT时间范围（仅Script有）
}
```

**Event**: 事件（高层情节单元）
```python
{
    "event_id": str,          # 如 "event_ep01_001"
    "title": str,             # 事件标题，如 "超市中与剪刀女战斗"
    "semantic_blocks": [SemanticBlock],  # 意思块链（按顺序）
    "characters": [str],      # 主要角色
    "location": str,          # 主要地点
    "time_context": str,      # 时间背景
    "chapter_range": (int, int),  # 章节范围（仅Novel有）
    "time_range": TimeRange,  # 视频时间范围（仅Script有）
    "episode": str            # 所属集数（仅Script有）
}
```

#### 3.3 两级匹配策略

**Level 1: Event级粗匹配**
- **目标**: 快速定位Novel中的候选Event
- **方法**: 基于title、角色、地点、时间的语义相似度
- **策略**: 顺序匹配（从上次匹配位置往后搜索）
- **输出**: 1-3个候选Event，匹配分数 > 0.6 进入Level 2

**Level 2: SemanticBlock链细验证**
- **目标**: 精确确认Script Event对应的Novel Event
- **方法**: 验证"意思块链"的顺序一致性和覆盖率
- **关键原理**:
  - 同一个Event标题可能重复（如"与剪刀女战斗"发生2次）
  - 但意思块链是唯一的（第1次:"发现→逃跑"；第2次:"路遇→对抗"）
  - Script链的每个block应在Novel链中按顺序找到
  - Novel链的block数量 >= Script链的block数量（Novel更详细）
- **评分标准**:
  - 覆盖率 = 匹配的Script block数 / Script block总数
  - 顺序一致性 = 匹配索引对是否严格递增
  - 验证分数 = 覆盖率×0.6 + 顺序一致性×0.4

**最终置信度**:
```
final_confidence = event_match_score × 0.4 + validation_score × 0.6
```

#### 3.4 关键特性

1. **意思块链的唯一性**: 解决重复Event的区分问题
2. **维度提取准确性**: 只提取"实际发生"的时间/地点，忽略假设性描述
3. **Novel更详细**: 同一主题的意思块，Novel包含更多句子和细节
4. **顺序匹配优化**: 利用Script源于Novel的天然顺序性，减少搜索空间

### 4. Data Versioning Strategy
- **Principle**: "Latest Pointer + Timestamped Versions".
- **Implementation**: `src.core.artifact_manager.ArtifactManager`.
- **Structure**:
  ```text
  data/projects/PROJ_001/alignment/
  ├── novel_events_v20260203_1000.json       # Novel Events (Historical)
  ├── novel_events_latest.json               # Novel Events (Pointer)
  ├── ep01_script_events_v20260203_1000.json # Script Events EP01 (Historical)
  ├── ep01_script_events_latest.json         # Script Events EP01 (Pointer)
  ├── ep02_script_events_v20260203_1000.json # Script Events EP02 (Historical)
  ├── ep02_script_events_latest.json         # Script Events EP02 (Pointer)
  ├── alignment_v20260203_1000.json          # Alignment Map (Historical)
  ├── alignment_v20260203_1200.json          # Alignment Map (Latest Version)
  └── alignment_latest.json                  # Alignment Map (Pointer)
  ```
- **Usage**: Downstream modules (Writer, Training) read `*_latest.json` by default, ensuring stability while preserving history.
- **Purpose**: Script events are now persisted for debugging, analysis optimization, and alignment verification.

## Workflows

### Workflow 1: Ingestion & Alignment v2 (三层数据模型 + 两级匹配)
*Executed when a new project is added.*

**核心特性**：
- ✅ 三层数据模型：Sentence → SemanticBlock → Event
- ✅ 两级匹配策略：Event级粗匹配 + Block链细验证
- ✅ Hook检测独立化：专门模块处理ep01的Hook边界
- ✅ 并发优化：支持异步LLM调用，大幅减少总耗时
- ✅ 维度准确提取：只提取实际发生的时间/地点，忽略假设

**执行流程**：

1.  **Project Registration**:
    - Scan `分析资料/`.
    - Assign `PROJ_XXX` ID.
    - Create entry in `project_index.json`.
    - **Ingestion**: Copy raw data to `data/projects/PROJ_XXX/raw/`.

2.  **Script Processing** (三层转换):
    - **Step 2.1**: 解析SRT blocks (index, start, end, text)
    - **Step 2.2**: SRT blocks → Sentences (句子还原 + 标点)
      - 使用 `restore_sentences_from_srt_async()`
      - 合并碎片化文本，添加标点符号
    - **Step 2.3**: Sentences → Semantic Blocks (意思块划分)
      - 使用 `segment_semantic_blocks_async()`
      - 识别语义边界，提取关键维度（角色、地点、时间）
    - **Step 2.4**: Semantic Blocks → Events (事件聚合)
      - 使用 `aggregate_events_async()`
      - 将连续的、围绕同一情节的意思块聚合为事件
    - **Output**: `alignment/epXX_script_events_v2_latest.json` (one file per episode)

3.  **Novel Processing** (三层转换):
    - **初始策略**: 提取 `SRT数量 × 2` 章（可配置）
    - **Step 3.1**: Novel Text → Sentences (句子分割)
      - 按标点符号（。！？）分割
    - **Step 3.2**: Sentences → Semantic Blocks (意思块划分)
      - 同Script处理逻辑
    - **Step 3.3**: Semantic Blocks → Events (事件聚合)
      - 同Script处理逻辑
    - **Output**: `alignment/novel_events_v2_latest.json`

4.  **Two-Level Matching** (两级匹配):
    - **Hook Detection** (仅ep01):
      - 使用 `HookDetector.detect_hook_boundary()`
      - 识别Hook结束位置和线性叙事起点
      - 从线性起点开始匹配
    - **Level 1: Event级粗匹配**:
      - 使用 `_match_event_level_async()`
      - 基于title、角色、地点、时间匹配
      - 从上次匹配位置往后搜索（顺序匹配）
      - 输出1-3个候选，分数 > 0.6 进入Level 2
    - **Level 2: Block链细验证**:
      - 使用 `_validate_block_chain_async()`
      - 验证Script链和Novel链的顺序一致性
      - 计算覆盖率和验证分数
    - **最终置信度**:
      - `final_confidence = event_match × 0.4 + validation × 0.6`
    - **Output**: 
      - `alignment/alignment_v2_latest.json` - EventAlignment列表
      - 每个EventAlignment包含：script_event, novel_event, 匹配分数, Block链验证结果

5.  **Quality Evaluation**:
    - 使用 `evaluate_alignment_quality()`
    - **Metrics**:
      - 平均置信度 (final_confidence的平均值)
      - 综合得分 (avg_confidence × 100)
      - 详细信息（匹配数量、Event匹配分数、验证分数）
    - **Output**: `alignment/alignment_quality_report_v2_latest.json`

**配置参数** (`src/core/config.py`):
```python
initial_chapter_multiplier: 2  # 初始章节倍数
batch_size: 10  # 每批提取章节数
safety_buffer_chapters: 10  # 安全缓冲章节数
quality_threshold: 70.0  # 合格分数
min_coverage_ratio: 0.8  # 最小覆盖率
max_concurrent_requests: 10  # 最大并发数
enable_concurrent: True  # 启用并发
```

### Workflow 2: Heat-Driven Training Workflow V2 (`src.workflows.training_workflow_v2.py`)
*基于真实热度数据的规则学习和内容评估系统*

**核心理念**：
- 从多个Ground Truth项目中提取爆款规则
- 用真实热度数据驱动规则优化
- 预测新生成内容的潜在热度

**三大阶段**：

#### 阶段1: 规则提取 (Rule Extraction)
**目标**：从多个不同热度的GT项目中提取爆款规则

**输入**：
- 多个GT项目的SRT、事件数据
- 各项目的真实热度值（0-10分，存储在`project_index.json`）

**处理流程**：
1. 加载所有标记为`is_ground_truth=true`的项目
2. 对比分析高热度vs低热度项目的差异特征
3. 提取规则（Hook强度、信息密度、节奏、时长、爽点频率等）
4. 为每条规则分配权重（基于与热度的相关性）

**输出**：
- `data/rule_books/rulebook_v1.0_latest.json`
- 包含：
  - Hook规则（前30秒专用）
  - Ep01规则（第一集主体）
  - Ep02+规则（第二集及之后）
  - 时长Patterns
  - 段落Patterns

**关键Agent**：`RuleExtractorAgent` (`src.agents.rule_extractor.py`)

#### 阶段2: 规则验证 (Rule Validation)
**目标**：验证规则能否准确预测GT项目的热度

**输入**：
- 规则库（RuleBook）
- GT项目数据
- 实际热度值

**处理流程**：
1. 用规则对每个GT项目评分
2. 计算评分与实际热度的相关性
3. 分析各维度对热度的影响程度
4. 提出规则优化建议

**验证标准**：
- 相关性 ≥ 0.85 → 规则有效
- 相关性 < 0.85 → 需要优化权重或阈值

**输出**：
- `data/rule_books/validation_v1.0_YYYYMMDD_HHMMSS.json`
- 包含：
  - 各项目的预测分数vs实际热度
  - 相关性系数
  - 维度重要性排序
  - 优化建议

**关键Agent**：`RuleValidatorAgent` (`src.agents.rule_validator.py`)

#### 阶段3: 内容评估 (Content Evaluation)
**目标**：评估新生成的内容，预测潜在热度

**输入**：
- Generated内容（新生成的script）
- 规则库（已验证的RuleBook）
- 参考GT项目（用于对比）

**处理流程**：
1. 用规则对Generated内容逐条评分
2. 与参考GT项目进行详细对比
3. 找出具体差距并举例说明
4. 计算相似度指标
5. 预测潜在热度值

**评分标准**：
- 90-100分 → 预测热度 9-10分（爆款）
- 75-89分  → 预测热度 7-8分（高热）
- 60-74分  → 预测热度 5-6分（中等）
- <60分    → 预测热度 <5分（需改进）

**输出**：
- `data/projects/PROJ_XXX/training/reports/comparative_feedback_latest.json`
- 包含：
  - 总分及各维度得分
  - 与GT的分数差距
  - 预测热度值
  - 具体违规项（带GT对比示例）
  - 改进建议（具体到句子层面）
  - 相似度指标
  - 决策建议（pass/improve/rewrite）

**关键Agent**：`ComparativeEvaluatorAgent` (`src.agents.comparative_evaluator.py`)

**运行模式**：
```python
workflow = HeatDrivenTrainingWorkflow()

# 模式1: 仅提取规则
await workflow.run(mode="extract")

# 模式2: 仅验证规则
await workflow.run(mode="validate", rulebook_version="v1.0")

# 模式3: 仅评估内容
await workflow.run(mode="evaluate", project_id="PROJ_002")

# 模式4: 完整流程（提取→验证→评估）
await workflow.run(mode="full", eval_project_id="PROJ_002")
```

**数据结构**：
- 核心Schema定义在 `src/core/schemas_feedback.py`
- Prompt模板在 `src/prompts/rule_extraction.yaml`, `rule_validation.yaml`, `comparative_evaluation.yaml`

### Workflow 2 (Legacy): Training Workflow (`src.workflows.training_workflow.py`)
*旧版训练流程，已被V2取代*

1.  **Initialization**:
    - Inputs: Novel Path, SRT Folder, Workspace Directory.
    - Agents: Analyst, Alignment Engine, Feedback Agent.
2.  **Data Processing**:
    - **Novel**: Reads novel text -> Splits by chapter -> Extracts events (Cached).
    - **Script**: Reads SRTs -> Splits by time/block -> Extracts events.
3.  **Alignment**:
    - Aligns Script Events with Novel Events using `DeepSeekAlignmentEngine`.
4.  **Feedback & Optimization**:
    - `FeedbackAgent` analyzes the alignment.
    - Generates `feedback_report.json` (Score, Issues, Suggestions).
    - Updates `methodology_v1.txt` with extracted insights.

### Workflow 3: Production Generation
*Executed to generate scripts for new novels.*

1.  **Analysis**: Analyst extracts events and scene breakdown from new novel.
2.  **Planning**: Planner (Future) or Logic determines pacing.
3.  **Writing**: Writer generates script chunk by chunk.

---

## Performance Optimization

### Concurrent Execution
- **Analyst**: 提供 `extract_events_async()` 和 `analyze_async()` 异步方法
- **Workflow**: 使用 `asyncio.gather()` + `Semaphore` 实现并发控制
- **效果**: 
  - 串行: ~200次LLM调用 × 2秒 = ~7分钟
  - 并发(10): ~200次 / 10 × 2秒 = ~40秒 (理论加速 10倍)

### Quality-Driven Strategy
- 避免过度提取：根据质量评估动态停止
- 安全缓冲机制：防止遗漏更好的匹配
- 实时反馈：每轮显示质量得分和覆盖情况

---

## 系统版本历史

### v2.1 (2026-02-03)
**重大更新：热度驱动的训练系统**

**核心改进**:
1. **热度驱动规则学习**: 从多个GT项目的真实热度数据中提取爆款规则
2. **规则验证机制**: 验证规则能否准确预测热度，相关性驱动优化
3. **对比评估系统**: 将Generated内容与GT详细对比，给出具体改进建议
4. **热度预测**: 根据评分预测新内容的潜在市场表现

**解决的核心问题**:
- ❌ 旧版: 评分标准模糊，"85分"无法解释为什么
- ✅ 新版: 逐条规则评分，每个扣分都有GT对比示例
- ❌ 旧版: 无法判断Generated质量的绝对水平
- ✅ 新版: 基于真实热度数据，可预测潜在市场表现
- ❌ 旧版: 改进建议笼统，难以执行
- ✅ 新版: 具体到句子层面的对比和建议

**新增组件**:
- `src/core/schemas_feedback.py` - 热度驱动系统的数据模型
- `src/agents/rule_extractor.py` - 规则提取Agent
- `src/agents/rule_validator.py` - 规则验证Agent
- `src/agents/comparative_evaluator.py` - 对比评估Agent
- `src/workflows/training_workflow_v2.py` - 热度驱动训练工作流
- `src/prompts/rule_extraction.yaml` - 规则提取Prompts
- `src/prompts/rule_validation.yaml` - 规则验证Prompts
- `src/prompts/comparative_evaluation.yaml` - 对比评估Prompts

**数据结构变更**:
- `project_index.json` 新增字段:
  - `heat_score`: 项目热度值（0-10分）
  - `is_ground_truth`: 是否作为训练数据
  - `heat_score_definition`: 热度分级参考标准

### v2.0 (2026-02-03)
**重大更新：三层数据模型 + 两级匹配策略**

**核心改进**:
1. **数据模型升级**: 从"事件级"升级到"情节级"，引入三层结构（Sentence → SemanticBlock → Event）
2. **匹配策略重构**: Event级粗匹配 + SemanticBlock链细验证，解决重复Event的区分问题
3. **Hook检测独立化**: 专门模块处理Hook边界，只在ep01执行一次
4. **维度提取优化**: 准确区分"实际发生"vs"假设性描述"

**解决的核心问题**:
- ❌ 旧版: 大海捞针式匹配，每个event都搜索全部chapters，效率低且易错
- ✅ 新版: 顺序匹配 + 意思块链验证，利用Script源于Novel的天然顺序性
- ❌ 旧版: 同一Event重复出现时无法区分（如"与剪刀女战斗"发生2次）
- ✅ 新版: 通过意思块链的唯一性精确区分
- ❌ 旧版: Hook检测在每集都执行，导致大量误判
- ✅ 新版: Hook检测只在ep01执行一次，并从线性起点开始匹配

**文件变更**:
- 新增: `src/core/schemas.py` - Sentence, SemanticBlock, Event, EventAlignment, BlockChainValidation
- 新增: `src/modules/alignment/hook_detector.py` - HookDetector
- 新增: `src/modules/alignment/deepseek_alignment_engine_v2.py` - 两级匹配引擎
- 更新: `src/workflows/ingestion_workflow.py` - v2流程
- 更新: `src/prompts/alignment.yaml` - 新增5个prompts

### v1.0 (2026-02-01)
**初始版本：动态章节提取 + 并发优化**

---

## 热度驱动系统使用指南

### 1. 准备Ground Truth数据

在`data/project_index.json`中为GT项目填入热度值：

```json
{
  "projects": {
    "PROJ_002": {
      "name": "末哥超凡公路",
      "heat_score": 9.5,
      "is_ground_truth": true,
      "notes": "爆款案例"
    },
    "PROJ_001": {
      "name": "超前崛起",
      "heat_score": 6.0,
      "is_ground_truth": true
    }
  }
}
```

### 2. 提取规则

```python
from src.workflows.training_workflow_v2 import HeatDrivenTrainingWorkflow

workflow = HeatDrivenTrainingWorkflow()
rulebook = await workflow.run(mode="extract")
```

### 3. 验证规则

```python
validation_result = await workflow.run(mode="validate")
# 检查 validation_result.is_valid 和 validation_result.correlation
```

### 4. 评估新内容

```python
feedback = await workflow.run(
    mode="evaluate",
    project_id="PROJ_002",
    gt_reference_project="PROJ_002"  # 可选，默认使用热度最高的GT
)

print(f"得分: {feedback.total_score}/100")
print(f"预测热度: {feedback.predicted_heat_score}/10")
print(f"建议: {feedback.recommendation}")
```

### 5. 完整流程

```python
results = await workflow.run(
    mode="full",
    eval_project_id="PROJ_002"
)
```

---
*Last Updated: 2026-02-03 22:00*
