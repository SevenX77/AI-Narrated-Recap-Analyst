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
- **Tool**: `NovelSegmentationTool` + `NovelChapterProcessor`
- **Input**: Raw novel text from `分析资料/`
- **Process**:
  1. Natural paragraph segmentation (LLM-assisted)
  2. Metadata extraction (title, author, tags)
  3. Introduction filtering (LLM-based, removes marketing content)
  4. Chapter splitting (10 chapters per file)
- **Output**: 
  - `raw/novel.txt`: Original text
  - `novel/chpt_0000.txt`: Filtered introduction
  - `novel/chpt_0001-0010.txt, chpt_0011-0020.txt, ...`: Chapter groups

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
*Last Updated: 2026-02-05 (v2.1)*
