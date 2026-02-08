# System Architecture & Logic Flows

## Overview
This document serves as the single source of truth for the system's logic and data flow.

## Core Components

### 1. Project Management
- **Project Index**: `data/project_index.json` maps source folders to unique IDs (e.g., `PROJ_001`).
- **Source Data**: Located in `分析资料/` (Analysis Data), organized by Novel Name.
- **Project Data**: Located in `data/projects/` with two categories:
  - `with_novel/`: Projects with novel reference (for alignment training)
  - `without_novel/`: Projects without novel (for script analysis only)
- **Project Structure**:
  - `raw/`: Original files (novel.txt, *.srt)
  - `novel/`: Processed novel chapters (chpt_0000.txt for intro, chpt_XXXX-YYYY.txt for chapter groups)
  - `script/`: Processed SRT scripts (ep01.txt, ep02.txt, ...)
  - `alignment/`: Alignment results
  - `analysis/`: Analysis artifacts
  - `ground_truth/`: Ground truth data
- **System Output**: Located in `output/`. Stores system logs (`app.log`) and operation history (`operation_history.jsonl`).

### 2. Data Processing Pipeline

#### 2.1 Novel Processing (with_novel projects)
- **Tools**: `NovelChapterProcessor` (简介拆分) + `NovelChapterAnalyzer` (功能段分析)
- **Input**: Raw novel text from `分析资料/`
- **Process**:
  1. **简介拆分** (`NovelChapterProcessor`):
     - Metadata extraction (title, author, tags)
     - Introduction filtering (LLM-based, removes marketing content)
     - Chapter splitting (10 chapters per file)
  2. **功能段分析** (`NovelChapterAnalyzer`):
     - 100% LLM驱动的叙事功能段分析
     - 多维度标签（叙事功能、结构、角色、优先级）
     - 浓缩建议与章节结构洞察
- **Output**: 
  - `raw/novel.txt`: Original text
  - `novel/chpt_0000.md`: Filtered introduction
  - `novel/functional_analysis/第X章完整分段分析.md`: 功能段分析（Markdown）
  - `novel/functional_analysis/chpt_XXXX_functional_analysis.json`: 功能段分析（JSON）
- **Note**: 旧的 `NovelSegmentationTool` (规则分段) 已废弃，归档到 `archive/v2_deprecated/old_novel_processing/`

#### 2.2 SRT Processing (all projects)
- **Tool**: `SrtScriptProcessor`
- **Input**: Raw SRT files from `分析资料/`
- **Processing Modes**:
  
  **Mode 1: With Novel Reference** (with_novel projects)
  - Extract standard entities from novel (characters, locations, items)
  - Use LLM to:
    - Add punctuation
    - Fix typos and homophones
    - Align entity names to novel standards
    - Fix missing characters (e.g., "到达上" → "到达上海")
  - Segment into natural paragraphs
  
  **Mode 2: Without Novel Reference** (without_novel projects)
  - Use LLM to intelligently:
    - Extract entities from SRT itself
    - Detect entity variants (e.g., "上沪", "上户", "上" all refer to same location)
    - Infer standard forms based on semantics (e.g., "上沪" for Shanghai, as 沪 is Shanghai's abbreviation)
    - Unify entity names across the script
    - Add punctuation and fix typos
    - Context-based completion (e.g., "到达商户" → "到达上沪" based on context)
  - Segment into natural paragraphs

- **Output**:
  - `raw/*.srt`: Original SRT files
  - `script/ep01.txt, ep02.txt, ...`: Processed readable scripts
  - `script/ep01_processing_report.json`: Processing metadata and entity standardization info

- **Prompts**: 
  - `src/prompts/srt_script_processing_with_novel.yaml`
  - `src/prompts/srt_script_processing_without_novel.yaml`

### 3. Agent Responsibilities
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
- **Layered Alignment Engine v4.0 (`src.modules.alignment.layered_alignment_engine`)**: 
  - **Role**: Hook-Body分离 + 4层分层对齐
  - **Input**: SRT (Body部分) / Novel Chapters
  - **Output**: 4层对齐结果 (Plot Nodes对齐) + Quality Report
  - **架构改进** (v4.0):
    - **Phase 0**: Novel预处理（提取纯净简介 + 章节索引）
    - **Phase 1**: Hook分析（仅ep01，Body起点检测 + Hook内容提取）
    - **Phase 2**: Body对齐（所有集数，4层分层对齐）
  - **4层对齐**:
    - Layer 1: `world_building` (世界观设定)
    - Layer 2: `game_mechanics` (系统机制)
    - Layer 3: `items_equipment` (道具装备)
    - Layer 4: `plot_events` (情节事件)
  - **核心特性**:
    - 直接从原始文本提取 Plot Nodes（无中间层）
    - Hook与Body独立处理（避免干扰）
    - 4层分别对齐（更精确的语义匹配）
    - 混合相似度引擎（TF-IDF + Embedding）
  - **主要模块**:
    - `layered_alignment_engine.py`: 主引擎
    - `body_start_detector.py`: Body起点检测
    - `hook_content_extractor.py`: Hook内容提取
    - `hybrid_similarity.py`: 混合相似度计算
    - `novel_preprocessor.py`: Novel预处理
  - **Prompts**: Managed in `src/prompts/layered_extraction.yaml`
  - **详细设计**: 见 `docs/architecture/LAYERED_ALIGNMENT_DESIGN.md`
- **Body Start Detector (`src.modules.alignment.body_start_detector`)**:
  - **Role**: 检测Script中Body部分的起点（Hook结束位置）
  - **Input**: Script SRT blocks
  - **Output**: BodyDetectionResult (has_hook, body_start_time, confidence, reasoning)
  - **检测依据**: 
    - 叙事模式转换（40%权重）：从概括→具体叙述
    - 连贯性变化（35%权重）：前后句子的因果关系
    - 时间锚点（15%权重）：明确的时间标记
    - 人称变化（10%权重）：从泛指→特定角色
  - **示例**: 识别"我从江城逃了出来"为Body起点
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

## 九、项目结构重构与数据迁移 (Project Restructuring & Migration)

### 概述

**日期**: 2026-02-05  
**版本**: v2.0  
**目标**: 重构项目数据结构，区分有无原小说的项目，实现小说自然分段处理

### 1. 新的项目目录结构

```
data/projects/
├── with_novel/              # 有原小说 → alignment & writer 训练
│   ├── 末哥超凡公路/
│   │   ├── raw/
│   │   │   ├── novel.txt              # 分段处理后的小说
│   │   │   ├── novel_original.txt     # 原始备份
│   │   │   ├── novel_processing_report.json
│   │   │   ├── ep01.srt ~ ep05.srt    # 字幕文件
│   │   │   └── metadata.json          # 项目元数据
│   │   ├── alignment/
│   │   ├── analysis/
│   │   └── ground_truth/
│   ├── 天命桃花/
│   └── 永夜悔恨录/
│
└── without_novel/           # 没有原小说 → script 分析 & 爆款规律
    ├── 超前崛起/
    │   ├── raw/
    │   │   ├── ep01.srt ~ ep09.srt
    │   │   └── metadata.json
    │   ├── analysis/
    │   └── ground_truth/
    └── 末世寒潮/
```

### 2. 项目分类

| 类别 | 用途 | 项目示例 |
|------|------|---------|
| **with_novel** | Alignment & Writer 训练 | 末哥超凡公路、天命桃花、永夜悔恨录 |
| **without_novel** | Script 分析、爆款规律提取 | 超前崛起、末世寒潮 |

### 3. 小说自然分段处理

#### 3.1 问题背景

原始小说文本格式：每句话单独一行，缺少自然段的概念
```
"滋滋……现在的时间是2030年10月13日上午10:23。"

"这或许是本电台最后一次广播！"

"上沪己经沦陷成为无人区！"
```

#### 3.2 处理目标

转换为自然段落格式：段内连续，段间双空行
```
"滋滋……现在的时间是2030年10月13日上午10:23。""这或许是本电台最后一次广播！""上沪己经沦陷成为无人区！""不要前往！不要前往！！！"

陈野听着收音机里的杂乱电流，只觉得浑身冰凉。整个车队弥漫一种绝望的窒息情绪。

几个月前，全球诡异爆发。只用了很短的时间，一些小的国家直接沦为人类禁区。
```

#### 3.3 分段算法：规则引擎 + LLM 辅助（混合模式）

##### 工具实现

**工具**: `src/tools/novel_processor.py::NovelSegmentationTool`
- **继承**: `BaseTool`
- **模式**: 可选纯规则或混合模式（规则 + LLM）
- **Prompt**: `src/prompts/novel_segmentation.yaml`

##### 规则引擎（覆盖 80%+ 场景）

**分段规则**:

| 规则 | 触发条件 | 置信度 | 说明 |
|------|---------|--------|------|
| 章节标题 | `=== 第X章 ===` | 1.0 | 强制分段 |
| 场景转换标记 | `……`、`---`、`***` | 1.0 | 强制分段 |
| 时间变化 | 出现时间关键词（几天后、清晨、夜幕降临） | 0.85 | 考虑分段 |
| 地点变化 | 出现地点关键词（车队、营地、城市） | 0.75 | 考虑分段 |
| 叙述模式切换 | 对话 ↔ 叙述 | 0.70 | 考虑分段 |
| 段落长度控制 | >15 句话 | 0.60 | 强制分段 |
| 主语变化 | 人物视角切换 | 0.55 | 考虑分段 |

**关键词库**:
- **时间**: `["夜幕降临", "清晨", "几天后", "一刻钟后", "此时", "现在", ...]`
- **地点**: `["车队", "营地", "城市", "基地", "房间", ...]`

##### LLM 辅助优化（处理 20% 疑难场景）

**触发条件**: 规则引擎置信度 < 0.5

**LLM 任务**:
```
输入: 待判断行的上下文（前后各10行）
输出: {"should_break": bool, "reason": str, "confidence": float}
模型: DeepSeek V3 (低成本、高质量)
温度: 0.3 (确保稳定性)
```

**Prompt 设计** (简化版):
```
分析以下文本，判断第 X 行后是否应该分段：
1. 前后句子主题是否一致？
2. 是否有时间/地点/视角变化？
3. 叙述模式是否变化（对话↔叙述）？

输出纯 JSON 格式。
```

#### 3.4 处理统计

| 项目 | 原始行数 | 生成段落数 | 平均段长 | 处理模式 |
|------|---------|-----------|---------|---------|
| 末哥超凡公路 | 5,507 | 1,643 | 3.3 句 | 纯规则 |
| 天命桃花 | 14,394 | 3,423 | 4.2 句 | 纯规则 |
| 永夜悔恨录 | 3,047 | 979 | 3.1 句 | 纯规则 |

### 4. 迁移工作流

**工作流**: `src/workflows/migration_workflow.py::ProjectMigrationWorkflow`

**执行步骤**:

```
步骤 1: 归档旧数据
  └─> data/projects → data/projects_archive_20260205/

步骤 2: 创建新目录结构
  ├─> data/projects/with_novel/
  └─> data/projects/without_novel/

步骤 3: 迁移 with_novel 项目
  ├─> 复制 SRT 文件
  ├─> 处理小说文本
  │   ├─> 保存原始备份 (novel_original.txt)
  │   ├─> 执行分段处理
  │   ├─> 保存处理结果 (novel.txt)
  │   └─> 生成处理报告 (novel_processing_report.json)
  └─> 创建元数据 (metadata.json)

步骤 4: 迁移 without_novel 项目
  ├─> 复制 SRT 文件
  └─> 创建元数据

步骤 5: 更新 project_index.json
  ├─> 版本升级: v1.0 → v2.0
  ├─> 添加 category 字段 (with_novel / without_novel)
  ├─> 添加 purpose 字段 (用途说明)
  └─> 添加 novel_processing 信息

步骤 6: 生成迁移报告
  └─> data/migration_report_20260205.json
```

### 5. 使用方式

#### 执行迁移

```bash
python3 scripts/run_migration.py
# 交互式选择是否使用 LLM 辅助
```

#### 代码调用

```python
from src.workflows.migration_workflow import ProjectMigrationWorkflow

# 纯规则模式（推荐，快速且成本低）
workflow = ProjectMigrationWorkflow(use_llm=False, dry_run=False)
report = await workflow.run()

# 混合模式（LLM 辅助，更高准确率）
workflow = ProjectMigrationWorkflow(use_llm=True, dry_run=False)
report = await workflow.run()
```

#### 单独使用小说分段工具

```python
from src.tools.novel_processor import NovelSegmentationTool

tool = NovelSegmentationTool(use_llm=False)
result = tool.execute(original_text, preserve_metadata=True)

print(f"段落数: {result.stats['total_paragraphs']}")
print(f"平均段长: {result.stats['avg_paragraph_length']}")
```

### 6. 更新的 project_index.json 结构

```json
{
  "version": "2.0",
  "updated_at": "2026-02-05T...",
  "projects": {
    "with_novel": {
      "末哥超凡公路": {
        "id": "PROJ_002",
        "category": "with_novel",
        "purpose": "alignment_writer_training",
        "episodes": ["ep01", "ep02", "ep03", "ep04", "ep05"],
        "novel_processing": {
          "method": "rule_only",
          "stats": {
            "original_lines": 5507,
            "total_paragraphs": 1643,
            "avg_paragraph_length": 3.34
          }
        }
      }
    },
    "without_novel": {
      "超前崛起": {
        "id": "PROJ_001",
        "category": "without_novel",
        "purpose": "script_analysis_hit_pattern",
        "episodes": ["ep01", ..., "ep09"]
      }
    }
  },
  "migration_history": {
    "v1_to_v2": {
      "date": "2026-02-05",
      "archived_to": "data/projects_archive_20260205",
      "reason": "重构项目结构，分离有无原小说项目，实现小说自然分段处理"
    }
  }
}
```

### 7. 相关文件

| 文件 | 说明 |
|------|------|
| `src/tools/novel_processor.py` | 小说分段工具 |
| `src/workflows/migration_workflow.py` | 迁移工作流 |
| `src/prompts/novel_segmentation.yaml` | LLM 分段提示词 |
| `scripts/run_migration.py` | 迁移执行脚本 |
| `data/migration_report_20260205.json` | 迁移报告 |
| `data/project_index.json` | 项目索引（v2.0） |

---

## 十、项目结构优化 v2.1 (Project Structure Optimization)

### 概述

**日期**: 2026-02-05  
**版本**: v2.1 (基于 v2.0)  
**目标**: 进一步优化目录结构和数据组织

### 优化内容

| 优化项 | v2.0 | v2.1 |
|--------|------|------|
| raw/novel.txt | 已分段处理 | **原始逐行格式** |
| 处理后的小说 | raw/ 目录 | **独立 novel/ 目录** |
| 章节组织 | 单一文件 | **按10章拆分** |
| 简介 | 混在正文中 | **独立 chpt_0000.txt** |
| 标签 | 无 | **提取到 metadata.json** |

### 最终目录结构

```
data/projects/with_novel/末哥超凡公路/
├── raw/                              # 原始文件（不可变）
│   ├── novel.txt                     # 原始小说（逐行格式）
│   └── ep*.srt                       # 原始字幕
│
├── novel/                            # 处理后的小说（可重新生成）
│   ├── chpt_0000.txt                 # 简介（仅正文）
│   ├── chpt_0001-0010.txt            # 第1-10章
│   ├── chpt_0011-0020.txt            # 第11-20章
│   ├── ...
│   └── processing_report.json        # 处理报告
│
├── metadata.json                     # 元数据（含标签）
├── alignment/
├── analysis/
└── ground_truth/
```

### 新增工具

| 工具 | 文件 | 功能 |
|------|------|------|
| **NovelChapterProcessor** | `src/tools/novel_chapter_processor.py` | 章节拆分、简介提取 |
| **MetadataExtractor** | `src/tools/novel_chapter_processor.py` | 标签提取、元数据解析 |

### metadata.json 增强

```json
{
  "project_name": "末哥超凡公路",
  "novel": {
    "title": "序列公路求生：我在末日升级物资",
    "author": "山海呼啸",
    "tags": [
      "题材新颖", "非无脑爽文", "非无敌",
      "序列魔药", "诡异", "公路求生",
      "升级物资", "心狠手辣"
    ],
    "introduction": "诡异降临，城市成了人类禁区...",
    "chapters": {
      "total": 50,
      "files": {
        "chpt_0000.txt": "简介",
        "chpt_0001-0010.txt": "第1-10章",
        ...
      }
    }
  }
}
```

### 章节文件命名规则

- **简介**: `chpt_0000.txt`
- **章节组**: `chpt_XXXX-YYYY.txt` (每10章一组)
  - 例如: `chpt_0001-0010.txt` (第1-10章)
  - 例如: `chpt_0081-0085.txt` (第81-85章，最后一组)

### 使用示例

#### 读取项目元数据

```python
import json
from pathlib import Path

project_dir = Path("data/projects/with_novel/末哥超凡公路")

# 读取元数据
with open(project_dir / "metadata.json") as f:
    metadata = json.load(f)

# 获取标签
tags = metadata["novel"]["tags"]
print(f"标签: {', '.join(tags)}")

# 读取简介
with open(project_dir / "novel/chpt_0000.txt") as f:
    intro = f.read()
```

#### 按需加载章节

```python
# 只读取前10章
with open(project_dir / "novel/chpt_0001-0010.txt") as f:
    first_chapters = f.read()

# 遍历所有章节
novel_dir = project_dir / "novel"
for chapter_file in sorted(novel_dir.glob("chpt_[0-9]*-[0-9]*.txt")):
    with open(chapter_file) as f:
        content = f.read()
        # 处理章节...
```

#### 根据标签筛选项目

```python
def find_projects_by_tag(tag: str) -> List[str]:
    """根据标签查找项目"""
    projects = []
    for project_dir in Path("data/projects/with_novel").iterdir():
        metadata_file = project_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
                if tag in metadata.get("novel", {}).get("tags", []):
                    projects.append(metadata["project_name"])
    return projects
```

### 处理统计

| 项目 | 总章节数 | 章节文件数 |
|------|---------|-----------|
| 末哥超凡公路 | 50 | 5 |
| 天命桃花 | 90 | 9 |
| 永夜悔恨录 | 76 | 8 |

---

## 十一、版本控制建议

### v2.0 版本提交

```bash
git add .
git commit -m "feat: 重构项目结构v2.0 - 分离有无原小说项目 + 实现小说自然分段处理

- 新增 with_novel / without_novel 分类
- 实现 NovelSegmentationTool (规则引擎 + LLM 辅助)
- 实现 ProjectMigrationWorkflow 自动化迁移
- 归档旧数据到 projects_archive_20260205
- 更新 project_index.json 到 v2.0
- 处理 3 个小说项目（共 22,948 行 → 6,045 段）
- 迁移 22 个字幕文件

See: docs/architecture/logic_flows.md - Section 九"

git tag -a v2.0.0 -m "Project Restructuring v2.0"
```

### v2.1 版本提交

```bash
git add .
git commit -m "feat: 优化项目结构v2.1 - 目录分离 + 章节拆分 + 标签提取

- raw/ 和 novel/ 目录分离（原始 vs 处理）
- 按10章拆分小说文件（chpt_0001-0010.txt）
- 简介独立为 chpt_0000.txt（仅正文）
- 标签提取到 metadata.json
- 新增 NovelChapterProcessor 工具
- 新增 MetadataExtractor 工具

See: docs/maintenance/PROJECT_OPTIMIZATION_V2.1.md"

git tag -a v2.1.0 -m "Project Structure Optimization v2.1"
```

---

## 十二、番茄小说自动下载系统 (Fanqie Novel Auto-Download System)

### 概述

**日期**: 2026-02-07  
**版本**: v1.0  
**目标**: 自动化爬取番茄小说榜单并批量下载小说内容，为 AI 分析提供素材

### 1. 系统架构

```
┌─────────────────────────────────────────────┐
│  Tools (工具层) - 原子操作                   │
├─────────────────────────────────────────────┤
│  • FanqieTextDecoder        文字解密        │
│  • FanqieBrowserController  浏览器控制      │
│  • FanqiePageScraper        页面元素提取    │
│  • FanqieNovelDownloader    小说下载        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Workflows (工作流层) - 业务编排             │
├─────────────────────────────────────────────┤
│  • RankingCrawlWorkflow     榜单爬取        │
│  • BatchNovelDownloadWorkflow 批量下载     │
└─────────────────────────────────────────────┘
```

### 2. 核心技术原理

#### 2.1 文字解密机制

番茄小说使用 **Unicode 私有区域字符映射** 来混淆文本内容，防止爬虫直接抓取。

**技术细节**:
- **混淆范围**: Unicode 58344-58715 (U+E408 - U+E57B)
- **映射表长度**: 372 个字符
- **映射内容**: 常用汉字和字母

**解密算法**:
```python
def decode_char(char_code):
    if 58344 <= char_code <= 58715:
        bias = char_code - 58344
        return CHARSET[bias]
    return chr(char_code)
```

**示例**:
```
混淆前: \uE408\uE409\uE40A  (Unicode 私有区域)
解密后: "D在主"              (正常文字)
```

#### 2.2 浏览器自动化策略

使用 **Playwright MCP 工具** 进行浏览器控制，而非传统的 Selenium。

**优势**:
- ✅ 更快的页面加载速度
- ✅ 更好的反检测能力
- ✅ 支持无头模式
- ✅ 更稳定的元素定位

**反检测措施**:
- 随机 User-Agent（Chrome/Edge/Firefox/Safari）
- 随机延迟（1-3 秒）
- 模拟人类滚动行为
- 禁用 WebDriver 标识

### 3. 数据模型

定义在 `src/core/schemas.py`:

#### 3.1 RankingNovelItem (榜单小说条目)

```python
{
    "novel_id": str,              # 小说唯一标识
    "title": str,                 # 小说标题
    "author": str,                # 作者
    "url": str,                   # 小说链接
    "rank": int,                  # 排名
    "ranking_type": str,          # 榜单类型（热销榜/完本榜等）
    "cover_url": str,             # 封面图链接
    "intro_snippet": str,         # 简介片段
    "crawled_at": str             # 爬取时间
}
```

#### 3.2 RankingData (榜单完整数据)

```python
{
    "ranking_type": str,          # 榜单类型
    "ranking_url": str,           # 榜单链接
    "crawled_at": str,            # 爬取时间
    "novels": [RankingNovelItem], # 小说列表
    "total_count": int            # 总数量
}
```

#### 3.3 FanqieChapter (章节信息)

```python
{
    "chapter_id": str,            # 章节 ID
    "chapter_num": int,           # 章节序号
    "title": str,                 # 章节标题
    "url": str,                   # 章节链接
    "is_vip": bool                # 是否付费章节
}
```

#### 3.4 FanqieNovelMetadata (小说元数据)

```python
{
    "novel_id": str,              # 小说 ID
    "title": str,                 # 标题
    "author": str,                # 作者
    "intro": str,                 # 简介
    "cover_url": str,             # 封面
    "total_chapters": int,        # 总章节数
    "chapters": [FanqieChapter],  # 章节列表
    "tags": [str]                 # 标签
}
```

#### 3.5 FanqieDownloadResult (下载结果)

```python
{
    "novel_id": str,              # 小说 ID
    "title": str,                 # 标题
    "success": bool,              # 是否成功
    "downloaded_chapters": int,   # 已下载章节数
    "failed_chapters": [int],     # 失败的章节列表
    "output_path": str,           # 输出文件路径
    "error_message": str          # 错误信息（如果有）
}
```

### 4. 工作流详解

#### Workflow 1: RankingCrawlWorkflow (榜单爬取)

**执行流程**:

```
阶段 1: 浏览器初始化
  ├─> 启动 Playwright 浏览器
  ├─> 配置反检测参数
  └─> 准备榜单 URL 列表

阶段 2: 榜单页面遍历
  For each 榜单:
    ├─> 导航到榜单页面
    ├─> 等待页面加载完成
    ├─> 识别小说列表元素
    │   ├─> 使用 CSS Selector 定位
    │   └─> 多候选策略（容错）
    ├─> 处理分页/滚动加载
    │   ├─> 检测页面类型（分页/无限滚动）
    │   ├─> 自动翻页或滚动
    │   └─> 等待新内容加载
    ├─> 提取小说元信息
    │   ├─> 标题、作者、封面
    │   ├─> 小说链接
    │   └─> 排名信息
    └─> 保存榜单数据
        └─> rankings/{榜单名称}_{时间戳}.json

阶段 3: 数据汇总与去重
  ├─> 合并所有榜单数据
  ├─> 按 novel_id 去重
  │   └─> 保留排名最高的记录
  ├─> 生成下载队列
  │   └─> download_queue.json
  └─> 关闭浏览器
```

**输出文件**:
- `data/fanqie/rankings/热销榜_20260207_143000.json` - 热销榜原始数据
- `data/fanqie/rankings/完本榜_20260207_143500.json` - 完本榜原始数据
- `data/fanqie/download_queue.json` - 合并去重后的下载队列

**关键配置** (`src/core/config.py`):
```python
FANQIE_RANKINGS = {
    "热销榜": {
        "url": "https://fanqienovel.com/ranking/hot",
        "selector": ".ranking-item",
        "type": "paginated"
    },
    "完本榜": {
        "url": "https://fanqienovel.com/ranking/finished",
        "selector": ".book-card",
        "type": "infinite_scroll"
    }
    # ... 更多榜单
}
```

#### Workflow 2: BatchNovelDownloadWorkflow (批量下载)

**执行流程**:

```
阶段 1: 加载下载队列
  ├─> 读取 download_queue.json
  ├─> 检查已下载记录（断点续传）
  └─> 过滤已存在的小说

阶段 2: 并行下载
  使用异步任务池（最大并发: 3）
  
  For each novel (并行):
    ├─> 步骤 2.1: 获取章节列表
    │   ├─> 访问小说主页
    │   ├─> 解析章节列表
    │   └─> 识别 VIP 章节
    │
    ├─> 步骤 2.2: 下载章节内容
    │   For each chapter:
    │     ├─> 发送 HTTP 请求
    │     ├─> 解析 HTML 内容
    │     ├─> 调用 FanqieTextDecoder 解密
    │     ├─> 提取图片链接（如果有）
    │     ├─> 保存到内存缓冲区
    │     └─> 延迟 0.5-2 秒（防封禁）
    │
    ├─> 步骤 2.3: 保存为文件
    │   ├─> 格式: TXT / Markdown / EPUB
    │   ├─> 路径: data/fanqie/novels/{榜单类型}/{书名}.txt
    │   └─> 包含元数据（标题、作者、简介）
    │
    └─> 步骤 2.4: 记录操作日志
        └─> output/operation_history.jsonl

阶段 3: 生成下载报告
  ├─> 统计总数、成功、失败、耗时
  ├─> 列出失败的小说和错误原因
  └─> 生成 Markdown 报告
      └─> data/fanqie/download_report_{时间戳}.md
```

**输出文件**:
- `data/fanqie/novels/热销榜/诡秘之主.txt` - 下载的小说
- `data/fanqie/download_report_20260207.md` - 下载报告
- `output/operation_history.jsonl` - 操作日志

**错误处理策略**:

| 错误类型 | 处理策略 |
|---------|---------|
| 网络超时 | 重试 3 次（指数退避：1s, 2s, 4s） |
| 验证码检测 | 暂停 5 分钟，记录日志，跳过该小说 |
| 元素未找到 | 尝试备用 Selector，失败则跳过 |
| VIP 章节 | 标记为"付费内容"，记录章节号，继续下载免费部分 |
| 单章失败 | 记录失败章节，继续下载其他章节 |
| 解密失败 | 保留原始混淆文本，标记警告 |

### 5. 工具层实现

#### Tool 1: FanqieTextDecoder (文字解密)

**职责**: 将混淆文字还原为正常文字

**接口**:
```python
class FanqieTextDecoder(BaseTool):
    name = "fanqie_text_decoder"
    
    def execute(self, text: str) -> str:
        """
        Args:
            text: 混淆的文本
        Returns:
            解密后的文本
        """
```

**实现要点**:
- charset 映射表从配置文件加载
- 支持动态更新映射表
- 处理未知字符（保持原样）

#### Tool 2: FanqieBrowserController (浏览器控制)

**职责**: 封装 Playwright MCP 工具调用

**接口**:
```python
class FanqieBrowserController(BaseTool):
    name = "fanqie_browser_controller"
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Args:
            action: 操作类型（navigate/snapshot/click/scroll/extract）
            **kwargs: 操作参数
        Returns:
            操作结果
        """
```

**支持的操作**:
- `navigate`: 导航到 URL
- `snapshot`: 获取页面快照
- `click`: 点击元素
- `scroll`: 滚动页面
- `extract`: 提取元素信息

#### Tool 3: FanqiePageScraper (页面元素提取)

**职责**: 从页面中提取小说信息

**接口**:
```python
class FanqiePageScraper(BaseTool):
    name = "fanqie_page_scraper"
    
    def execute(self, page_snapshot: str, selector: str) -> List[Dict]:
        """
        Args:
            page_snapshot: 页面快照（HTML 或结构化数据）
            selector: CSS 选择器
        Returns:
            提取的元素列表
        """
```

**提取逻辑**:
- 支持多候选 Selector（容错）
- 智能识别元素类型（标题/作者/链接）
- 数据清洗和标准化

#### Tool 4: FanqieNovelDownloader (小说下载)

**职责**: 下载单本小说的完整内容

**接口**:
```python
class FanqieNovelDownloader(BaseTool):
    name = "fanqie_novel_downloader"
    
    def __init__(self):
        self.decoder = FanqieTextDecoder()
    
    def execute(self, 
                novel_url: str,
                output_dir: Path,
                format: str = "txt",
                start_chapter: int = 1,
                end_chapter: Optional[int] = None) -> FanqieDownloadResult:
        """
        Args:
            novel_url: 小说 URL
            output_dir: 输出目录
            format: 保存格式 (txt/md/epub)
            start_chapter: 起始章节（支持断点续传）
            end_chapter: 结束章节（None = 全部）
        Returns:
            下载结果对象
        """
```

**关键特性**:
- ✅ 断点续传（检查已下载章节）
- ✅ VIP 章节识别（跳过付费内容）
- ✅ 图片下载（可选）
- ✅ 多格式输出（TXT/MD/EPUB）
- ✅ 速率限制（防封禁）

### 6. 配置管理

定义在 `src/core/config.py`:

```python
@dataclass
class FanqieConfig:
    """番茄小说下载配置"""
    
    # 字符解密
    charset: List[str] = field(default_factory=lambda: FANQIE_CHARSET)
    code_start: int = 58344
    code_end: int = 58715
    
    # 网络配置
    request_timeout: int = 30
    retry_times: int = 3
    rate_limit_delay: Tuple[float, float] = (0.5, 2.0)
    
    # 浏览器配置
    browser_headless: bool = True
    browser_timeout: int = 30
    
    # 榜单配置
    rankings: Dict[str, Dict] = field(default_factory=lambda: FANQIE_RANKINGS)
    max_novels_per_ranking: int = 100
    
    # 下载配置
    max_concurrent_downloads: int = 3
    download_format: str = "txt"
    save_images: bool = False
    
    # Cookie（可选）
    cookies: Optional[Dict[str, str]] = None

# 全局配置实例
config.fanqie = FanqieConfig()
```

### 7. 使用示例

#### 场景 1: 爬取单个榜单并下载

```python
from src.workflows.ranking_crawl_workflow import RankingCrawlWorkflow
from src.workflows.batch_novel_download_workflow import BatchNovelDownloadWorkflow

# 步骤 1: 爬取榜单
crawl_wf = RankingCrawlWorkflow()
queue = await crawl_wf.run(
    ranking_types=["热销榜"],
    max_per_ranking=50
)

# 步骤 2: 批量下载
download_wf = BatchNovelDownloadWorkflow()
result = await download_wf.run(
    queue_file="data/fanqie/download_queue.json",
    output_dir=Path("data/fanqie/novels"),
    format="txt"
)

print(f"成功下载: {result['success']} / {result['total']}")
```

#### 场景 2: 爬取所有榜单（自动下载）

```python
crawl_wf = RankingCrawlWorkflow()
result = await crawl_wf.run(
    ranking_types=["热销榜", "完本榜", "新书榜", "免费榜"],
    auto_download=True,        # 爬取后自动下载
    max_per_ranking=30,        # 每个榜单最多 30 本
    deduplicate=True           # 去重
)
```

#### 场景 3: 断点续传

```python
# 如果之前下载中断，可以继续
download_wf = BatchNovelDownloadWorkflow()
result = await download_wf.run(
    queue_file="data/fanqie/download_queue.json",
    resume=True  # 自动检测已下载的小说
)
```

### 8. 数据存储结构

```
data/fanqie/
├── rankings/                           # 榜单原始数据
│   ├── 热销榜_20260207_143000.json
│   ├── 完本榜_20260207_143500.json
│   └── 新书榜_20260207_144000.json
│
├── novels/                            # 下载的小说
│   ├── 热销榜/
│   │   ├── 诡秘之主.txt
│   │   ├── 诡秘之主_metadata.json
│   │   └── ...
│   ├── 完本榜/
│   └── 新书榜/
│
├── download_queue.json                # 下载队列
├── download_queue_completed.json      # 已完成队列
└── download_report_20260207.md        # 下载报告
```

### 9. 性能与合规

#### 性能指标

| 指标 | 估算值 |
|------|-------|
| 单本小说下载时间 | 5-15 分钟 |
| 批量下载 10 本 | 30-60 分钟（并发 3） |
| 榜单爬取时间 | 2-5 分钟/榜单 |
| 平均小说大小 | 2-10 MB |
| 并发下载数 | 3（可配置） |

#### 合规说明

⚠️ **重要提醒**:
- 此工具**仅供学习研究使用**
- 下载的内容受**版权保护**
- 不应用于**商业用途**或**大规模传播**
- 请遵守番茄小说的**服务条款**
- 建议控制下载频率，避免对服务器造成压力

### 10. 故障排查

#### 常见问题与解决方案

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 解密后文字乱码 | charset 映射表过期 | 更新 `FANQIE_CHARSET` 配置 |
| 浏览器启动失败 | Playwright 未安装 | 运行 `playwright install` |
| 元素未找到 | 页面结构变化 | 更新 CSS Selector |
| 下载速度慢 | 网络延迟或速率限制 | 调整 `rate_limit_delay` |
| 验证码频繁出现 | 请求过于频繁 | 降低并发数，增加延迟 |
| VIP 章节无法下载 | 需要付费 | 自动跳过，记录在 `failed_chapters` |

### 11. 维护与更新

#### 定期维护任务

- [ ] **每月检查** charset 映射表是否需要更新
- [ ] **每季度更新** 榜单配置（URL 和 Selector）
- [ ] **监控下载成功率**，低于 90% 需要检查
- [ ] **清理旧数据**，超过 3 个月的榜单数据可以归档

#### 版本更新记录

- **v1.0 (2026-02-07)**: 初始版本，支持榜单爬取和批量下载

---

## 十三、版本控制建议（更新）

### v3.0 版本提交

```bash
git add .
git commit -m "feat: 添加番茄小说自动下载系统 v1.0

- 实现榜单自动爬取（热销榜/完本榜/新书榜等）
- 实现文字解密算法（Unicode 私有区域映射）
- 实现批量下载工作流（支持并发和断点续传）
- 集成 Playwright MCP 浏览器控制
- 新增 4 个 Tools（Decoder/BrowserController/Scraper/Downloader）
- 新增 2 个 Workflows（RankingCrawl/BatchDownload）
- 新增数据模型（RankingNovelItem/FanqieChapter/FanqieDownloadResult等）
- 新增配置管理（FanqieConfig）

See: docs/architecture/logic_flows.md - Section 十二"

git tag -a v3.0.0 -m "Fanqie Novel Auto-Download System v1.0"
```

---

## 十三、Novel-to-Script 智能改编系统 (Novel-to-Script Intelligent Adaptation System)

### 概述

**日期**: 2026-02-07  
**版本**: v1.0  
**目标**: 构建模块化、可迭代的小说到解说Script的智能改编系统，支持训练和生产并存

### 1. 系统架构

```
📦 原子工具层 (Atomic Tools)
├── NovelSegmentationAnalyzer    小说分段深度分析（LLM驱动，多维度标签）
├── ScriptSegmentAligner          Script-Novel精确对齐与改编分析
└── KeyInfoExtractor              关键信息提取与汇总

         ↓ 调用

🤖 智能Agent层 (Intelligent Agents)
├── NovelAnalysisAgent            协调小说分析流程
├── AlignmentAnalysisAgent        执行Script-Novel精确对齐
├── PatternLearningAgent          从GT项目学习改编规律
├── EnhancedWriterAgent           融合式Script生成（模板+学习+迭代）
└── FeedbackLoopAgent             管理评估-改写循环

         ↓ 编排

🔄 工作流层 (Workflows)
├── NovelAnalysisWorkflow         小说分析流程（分段+标签+关键信息）
├── AlignmentWorkflow             对齐流程（GT项目Script-Novel对应关系）
├── TrainingWorkflow              训练流程（提取爆款规律+验证）
├── ProductionWorkflow            生产流程（为新小说生成Script）
└── ContinuousImprovementWorkflow 持续改进（生产→评估→反馈→训练闭环）

         ↓ 持续迭代

📊 版本化数据 (Versioned Data)
└── 所有中间产物都有版本号 + latest指针
```

### 2. 核心数据模型

定义在 `src/core/schemas_segmentation.py`:

#### 2.1 小说分段分析

**NovelSegment** (小说段落)
```python
{
    "segment_id": "seg_chpt_0001_001",
    "text": "段落原文",
    "tags": {
        "narrative_function": ["故事推进", "核心故事设定(首次)"],
        "structure": ["钩子-悬念制造"],
        "character": ["人物塑造-陈野"],
        "priority": "P0-骨架",  # P0-骨架 | P1-血肉 | P2-皮肤
        "location": "江城车队",
        "time": "末日爆发后数月"
    },
    "metadata": {
        "is_first_appearance": true,
        "repetition_count": 0,
        "foreshadowing": {
            "type": "埋设",
            "content": "升级系统",
            "resolution_chapter": "chpt_0003"
        },
        "condensation_suggestion": "必须保留，核心设定首次出现",
        "word_count": 150
    }
}
```

**ChapterAnalysis** (章节完整分析)
```python
{
    "chapter_id": "chpt_0001",
    "segments": [NovelSegment, ...],
    "chapter_summary": {
        "total_segments": 11,
        "p0_count": 5,
        "p1_count": 4,
        "p2_count": 2,
        "key_events": ["觉醒系统", "升级自行车"],
        "foreshadowing_planted": ["升级系统", "杀戮点债务"],
        "condensed_version": "500字浓缩版"
    }
}
```

#### 2.2 Script-Novel对齐

**ScriptToNovelAlignment** (对齐关系)
```python
{
    "script_segment": {
        "time_range": "00:00:00,000 - 00:00:35,666",
        "text": "Script文本",
        "segment_type": "Hook"
    },
    "novel_source": {
        "segments": ["seg_chpt_0001_001", "seg_chpt_0001_002"],
        "condensation_ratio": 0.25,
        "retained_tags": ["P0-骨架", "核心故事设定(首次)"],
        "omitted_tags": ["P2-皮肤", "心理描写"],
        "transformation": {
            "method": "高度浓缩+概括",
            "techniques": ["合并多段", "提炼核心设定"]
        }
    },
    "analysis": {
        "alignment_confidence": 0.95,
        "key_info_preserved": ["诡异无法被杀死", "序列超凡"],
        "quality_score": 90
    }
}
```

**AlignmentResult** (完整对齐结果)
```python
{
    "episode_id": "ep01",
    "alignments": [ScriptToNovelAlignment, ...],
    "overall_stats": {
        "total_script_segments": 15,
        "total_novel_segments": 45,
        "condensation_ratio": 0.33,
        "p0_retention_rate": 1.0,   # P0内容100%保留
        "p1_retention_rate": 0.6,
        "p2_retention_rate": 0.1
    }
}
```

#### 2.3 改编规律库

**PatternLibrary** (爆款规律库)
```python
{
    "patterns": {
        "hook": [AdaptationPattern, ...],
        "condensation": [AdaptationPattern, ...],
        "rhythm": [AdaptationPattern, ...],
        "language": [AdaptationPattern, ...]
    },
    "success_factors": ["Hook强度高", "节奏紧凑", "爽点密集"],
    "source_projects": ["PROJ_002", "PROJ_003"],
    "validated": true,
    "correlation": 0.92
}
```

### 3. 多维度标签体系

#### 3.1 叙事功能标签
- `故事推进`: 推动情节发展
- `核心故事设定(首次)`: 世界观规则首次出现
- `关键道具(首次)`: 重要物品初次登场
- `关键信息`: 重要线索、事实
- `背景交代`: 补充说明

#### 3.2 叙事结构标签
- `钩子-悬念制造`: 引起期待但不给答案
- `钩子-悬念释放`: 回应之前的悬念
- `伏笔`: 埋设未来情节线索
- `回应伏笔`: 回收之前的伏笔
- `重复强调`: 重要信息反复强调

#### 3.3 浓缩优先级标签
- `P0-骨架`: 核心情节，必须保留
- `P1-血肉`: 重要细节，选择性保留
- `P2-皮肤`: 氛围渲染，可大量删减

### 4. 工作流详解

#### Workflow 1: NovelAnalysisWorkflow (小说分析)

**目的**: 分析小说章节，输出结构化的多维度标签

**流程**:
```
Step 1: 章节分段分析
  └─> NovelSegmentationAnalyzer Tool
      ├─ 输入: 章节原文
      ├─ LLM分析: 语义理解+标签提取
      └─ 输出: ChapterAnalysis (版本化JSON)

Step 2: 关键信息汇总
  └─> KeyInfoExtractor Tool
      ├─ 输入: 所有章节分析
      ├─ 提取: P0/P1/P2分级+伏笔追踪+角色弧光
      └─ 输出: NovelKeyInfo

Step 3: 版本化存储
  └─> data/projects/{project}/novel/segmentation_analysis/
      ├─ chpt_0001_analysis_v20260207_120000.json
      └─ chpt_0001_analysis_latest.json (指针)
```

#### Workflow 2: AlignmentWorkflow (对齐分析)

**目的**: 分析GT项目的Script如何改编自小说

**流程**:
```
Step 1: 加载小说分析
  └─> 读取 segmentation_analysis/*.json

Step 2: 精确对齐
  └─> ScriptSegmentAligner Tool
      ├─ 逐段分析Script
      ├─ 找出对应的小说段落（segment_id）
      ├─ 计算浓缩比例
      └─ 识别改编技巧

Step 3: 输出对应关系
  └─> data/projects/{project}/script/alignment_to_novel/
      ├─ ep01_mapping_v20260207_120000.json
      └─ ep01_mapping_latest.json
```

#### Workflow 3: TrainingWorkflow (训练)

**目的**: 从多个GT项目提取爆款规律

**流程**:
```
Step 1: 验证GT数据完整性
  └─> 确保所有GT项目已完成分析和对齐

Step 2: 提取跨项目规律
  └─> PatternLearningAgent
      ├─ 分析多个GT的对齐结果
      ├─ 提取Hook模式、浓缩策略、节奏控制
      └─ 输出: PatternLibrary

Step 3: 验证规律有效性
  └─> 复用 training_workflow_v2.py
      ├─ 用规则对GT项目评分
      ├─ 计算与实际热度的相关性
      └─ 如果相关性 < 0.85，优化权重并重新训练

Step 4: 版本化存储
  └─> data/rule_books/
      ├─ pattern_library_v20260207_120000.json
      └─ pattern_library_latest.json
```

#### Workflow 4: ProductionWorkflow (生产)

**目的**: 为新小说生成高质量Script

**流程**:
```
Step 1: 分析新小说
  └─> NovelAnalysisWorkflow

Step 2: 加载规律库
  └─> pattern_library_latest.json

Step 3: 选择GT参考（可选）
  └─> 基于题材、风格匹配相似GT项目

Step 4: 生成Script（融合模式）
  └─> EnhancedWriterAgent
      ├─ 模式1: 基于模板（使用Pattern Library规则）
      ├─ 模式2: 对比学习（参考GT改编手法）
      └─> 输出初版Script

Step 5: 迭代优化
  └─> FeedbackLoopAgent
      ├─ Evaluator评分
      ├─ 如果 < 目标分数，提取改进建议
      ├─ Writer根据建议重写
      └─> 重复直到达标（最多3轮）

Step 6: 版本化输出
  └─> data/projects/{project}/production/scripts/
      ├─ ep01_v20260207_120000.md
      └─> ep01_latest.md
```

#### Workflow 5: ContinuousImprovementWorkflow (持续改进)

**目的**: 生产→评估→反馈→训练的闭环

**流程**:
```
后台持续运行:
  ├─ 检查新生产的Script
  ├─ 自动评估质量
  ├─ 如果达到爆款标准（score > 90）
  │   ├─ 用户确认后晋升为GT
  │   └─ 重新训练PatternLibrary
  └─> 循环迭代
```

### 5. 核心工具详解

#### Tool 1: NovelSegmentationAnalyzer

**功能**: 使用LLM对小说章节进行深度分析

**特点**:
- ✅ 全程LLM语义理解，无硬规则
- ✅ 多维度标签（叙事功能+结构+角色+优先级）
- ✅ 识别首次出现、重复强调、伏笔
- ✅ 提供浓缩建议

**Prompt**: `src/prompts/novel_segmentation_analysis.yaml`

**输出**: `ChapterAnalysis` (JSON)

#### Tool 2: ScriptSegmentAligner

**功能**: 将Script段落精确对齐到小说分段分析

**特点**:
- ✅ 逐段对齐分析
- ✅ 识别改编技巧（合并、删减、强调）
- ✅ 计算浓缩比例和保留率
- ✅ 质量评分

**Prompt**: `src/prompts/script_alignment_analysis.yaml`

**输出**: `AlignmentResult` (JSON)

#### Tool 3: KeyInfoExtractor

**功能**: 从章节分析中提取关键信息汇总

**特点**:
- ✅ P0/P1/P2分级信息提取
- ✅ 伏笔映射表构建
- ✅ 角色弧光追踪
- ✅ 浓缩指导原则生成

**输出**: `NovelKeyInfo` (JSON)

### 6. 数据存储结构

```
data/projects/with_novel/{project}/
├── novel/
│   ├── chpt_0001-0010.md              # 原始章节
│   └── segmentation_analysis/         # 🆕 分段分析结果
│       ├── chpt_0001_analysis_v20260207_120000.json
│       ├── chpt_0001_analysis_latest.json  # 指针
│       └── ...
│
├── script/
│   ├── ep01.md                        # 原始Script
│   └── alignment_to_novel/            # 🆕 Script-Novel对应关系
│       ├── ep01_mapping_v20260207_120000.json
│       ├── ep01_mapping_latest.json
│       └── ...
│
├── analysis/                          # 🆕 综合分析
│   ├── key_info_v20260207_120000.json    # P0/P1/P2信息汇总
│   ├── key_info_latest.json
│   ├── foreshadowing_tracking.json       # 伏笔追踪
│   └── condensation_guidelines.json      # 浓缩指导
│
├── training/
│   └── writer_context/                # 🆕 Writer改写上下文
│       ├── ep01_writing_context_v20260207_120000.json
│       └── ep01_writing_context_latest.json
│
└── production/
    └── scripts/
        ├── ep01_v20260207_120000.md
        └── ep01_latest.md
```

### 7. 与现有系统的关系

#### 7.1 归档的旧方法
- ✅ 旧的粗粒度对齐（v2 Event级对齐）已归档至 `archive/v2_deprecated/`
- ✅ 现在使用细粒度分段分析（段落级+多维度标签）

#### 7.2 保留的系统
- ✅ **LayeredAlignmentEngine v4.0**: 保留用于特定场景的分层对齐
- ✅ **Training Workflow v2**: 热度驱动训练系统，整合到新的TrainingWorkflow中

#### 7.3 新增的组件
- 🆕 3个新Tools（Analyzer, Aligner, Extractor）
- 🆕 5个新Agents（分析、对齐、学习、增强Writer、反馈循环）
- 🆕 5个新Workflows（分析、对齐、训练、生产、持续改进）
- 🆕 1个新Schema文件（schemas_segmentation.py）
- 🆕 2个新Prompt文件（分段分析、对齐分析）

### 8. 关键设计亮点

1. **模块化**: Tools独立可测试，Agents可组合，Workflows灵活编排
2. **版本管理**: 所有中间产物都有版本号+latest指针
3. **融合模式**: Writer同时使用模板、学习、迭代三种策略
4. **闭环优化**: 生产→评估→反馈→训练的自动化循环
5. **LLM驱动**: 分段分析全部使用语义理解，而非硬规则
6. **训练生产并存**: 支持持续训练和生产，不断优化

### 9. 使用示例

#### 分析新小说（训练模式）
```python
from src.workflows.novel_analysis_workflow import NovelAnalysisWorkflow

workflow = NovelAnalysisWorkflow()
result = await workflow.run(
    project_id="PROJ_002",
    chapters=["chpt_0001-0010"]
)
```

#### 对齐GT项目
```python
from src.workflows.alignment_workflow import AlignmentWorkflow

workflow = AlignmentWorkflow()
result = await workflow.run(
    project_id="PROJ_002",
    episode_id="ep01"
)
```

#### 训练规律库
```python
from src.workflows.training_workflow import TrainingWorkflow

workflow = TrainingWorkflow()
pattern_library = await workflow.run(
    gt_project_ids=["PROJ_002", "PROJ_003", "PROJ_005"]
)
```

#### 生产新Script
```python
from src.workflows.production_workflow import ProductionWorkflow

workflow = ProductionWorkflow()
result = await workflow.run(
    novel_path="data/projects/with_novel/新小说/novel/",
    target_episodes=1
)
```

### 10. 实施状态

**Phase 1: 基础工具开发** ✅ (已完成)
- [x] NovelSegmentationAnalyzer Tool
- [x] ScriptSegmentAligner Tool
- [x] KeyInfoExtractor Tool
- [x] Schemas定义
- [x] Prompt文件

**Phase 2: Agent开发** (待实施)
- [ ] NovelAnalysisAgent
- [ ] AlignmentAnalysisAgent
- [ ] PatternLearningAgent
- [ ] EnhancedWriterAgent
- [ ] FeedbackLoopAgent

**Phase 3: Workflow编排** (待实施)
- [ ] NovelAnalysisWorkflow
- [ ] AlignmentWorkflow
- [ ] TrainingWorkflow
- [ ] ProductionWorkflow

**Phase 4: 验证与优化** (待实施)
- [ ] 用GT项目测试完整流程
- [ ] 验证改进效果
- [ ] 性能优化

**Phase 5: 持续改进** (待实施)
- [ ] ContinuousImprovementWorkflow
- [ ] 监控面板

### 11. 版本控制建议

```bash
git add .
git commit -m "feat: Novel-to-Script智能改编系统 Phase 1 - 基础工具开发

- 新增 schemas_segmentation.py（数据模型）
- 新增 NovelSegmentationAnalyzer Tool（LLM驱动分段分析）
- 新增 ScriptSegmentAligner Tool（精确对齐与改编分析）
- 新增 KeyInfoExtractor Tool（关键信息汇总）
- 新增 2个Prompt配置（分段分析、对齐分析）
- 归档旧方法到 archive/（v1_legacy_workflows, v3_maintenance_docs）
- 更新文档（DEV_STANDARDS.md, logic_flows.md）

See: docs/architecture/logic_flows.md - Section 十三"

git tag -a v3.1.0 -m "Novel-to-Script System Phase 1"
```

---
*Last Updated: 2026-02-07 (v3.1)*
