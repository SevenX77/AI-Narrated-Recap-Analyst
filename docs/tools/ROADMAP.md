# 工具开发路线图

**最后更新**: 2026-02-09  
**当前进度**: 17/19 工具完成 (89%)  
**最新变更**: P0/P1/P2工具全部实现并测试通过

---

## 📐 设计原则

1. **Workflow驱动**: 从Workflow需求倒推工具设计
2. **职责单一**: 每个工具只做一件事，做好一件事
3. **测试驱动**: 每个工具都有验证方法和测试脚本
4. **文档同步**: 代码即文档，文档即规范
5. **渐进构建**: 优先实现核心流程，逐步完善
6. **复用优先**: 优先复用归档工具，减少重复开发

---

## 🎯 核心Workflow设计

### Workflow 1: NovelProcessingWorkflow
**目标**: 从原始小说到完整章节分析

```
Novel.txt → NovelImporter → NovelMetadataExtractor → NovelChapterDetector
              ↓
        NovelSegmenter (并行处理各章节)
              ↓
        NovelAnnotator (并行处理各章节)
              ↓
        NovelSystemAnalyzer (全书一次)
              ↓
        NovelSystemDetector (每章) + NovelSystemTracker (每章)
              ↓
        NovelValidator (质量验证)
```

### Workflow 2: ScriptProcessingWorkflow
**目标**: 从SRT到结构化脚本分段

```
SRT → SrtImporter → SrtTextExtractor → HookDetector (ep01)
                                            ↓
                                    ScriptSegmenter v2 (ABC类分段)
                                            ↓
                                    ScriptValidator (质量验证)
```

### Workflow 3: AlignmentWorkflow
**目标**: Novel-Script对齐分析

```
Novel (AnnotatedChapter) + Script (SegmentationResult)
              ↓
    NovelScriptAligner (句子级对齐)
              ↓
    AlignmentReport (质量报告)
```

---

## 📊 Phase划分（基于Workflow）

## Phase I: 素材标准化与分段 ✅ (已完成 8/8)

### 目标
将原始文件转换为结构化分段数据，为后续分析打好基础。

### 1.1 Novel处理工具 (5/5 完成)

#### `NovelImporter` - 小说导入工具 ✅
**职责**: 读取、规范化并导入小说文件到项目目录
- 读取原始novel.txt文件（任意位置）
- 编码检测与统一（UTF-8）
- 换行符规范化
- 去除BOM标记
- 基础格式验证
- **保存到项目标准位置** `data/projects/{project_name}/raw/novel.txt`

**输入**: 原始小说文件路径 + 项目名称  
**输出**: `NovelImportResult` (包含保存路径、元数据、可选的内容)  
**依赖**: 无

**实现状态**: ✅ 已完成 (2026-02-09)

---

#### `NovelMetadataExtractor` - 小说元数据提取工具 ✅
**职责**: 提取小说的基本信息
- 提取标题
- 提取作者
- 提取标签/分类（从【标签】格式）
- 提取并智能过滤简介（LLM优先，规则降级）
  - 移除标签行、营销文案、书名变体等
  - 保留世界观、主角设定、核心冲突

**输入**: 小说文件路径 (`data/projects/xxx/raw/novel.txt`)  
**输出**: `NovelMetadata` schema  
**依赖**: `NovelImporter`（需要先导入文件）

**实现状态**: ✅ 已完成 (2026-02-09)  
**LLM配置**: DeepSeek v3.2（简单任务，可选Two-Pass改造）  
**Prompt文件**: `introduction_extraction.yaml`（单Pass）

---

#### `NovelChapterDetector` - 章节检测工具 ✅
**职责**: 检测章节边界
- 识别章节标题模式（第X章、ChapterX等）
- 定位章节起始位置（行号、字符位置）
- 统计章节字数
- 生成章节索引
- 验证章节连续性

**输入**: 规范化的小说文本  
**输出**: `List[ChapterInfo]` - 章节索引列表  
**依赖**: `NovelImporter`

**实现状态**: ✅ 已完成 (2026-02-09)

---

#### `NovelSegmenter` - 小说分段工具 ✅ ⭐
**职责**: 使用Two-Pass LLM对小说章节进行叙事分段
- **Two-Pass策略**：Pass 1初步分段 + Pass 2校验修正
- 按叙事功能分割（A类设定/B类事件/C类系统）
- **行号定位**：LLM输出行号范围，代码提取内容
- **JSON输出**：结构化输出，可完全还原原文（99.63%）
- 准确率：100%（vs 旧版78%）

**输入**: 规范化的小说文本 + 章节号  
**输出**: `ParagraphSegmentationResult` (JSON格式)  
**依赖**: `NovelImporter`, `NovelChapterDetector`

**实现状态**: ✅ v3完成 (2026-02-09) - Two-Pass + JSON + 行号定位  
**LLM配置**: Claude Sonnet 4.5 (强制，DeepSeek不适合复杂分段)  
**Prompt文件**: `novel_chapter_segmentation_pass1.yaml` + `pass2.yaml`

---

---

### 1.2 Script处理工具 (3/3 完成)

#### `SrtImporter` - SRT导入工具 ✅
**职责**: 读取并规范化SRT文件
- 读取SRT文件
- 编码检测与统一
- 解析SRT格式（序号、时间轴、文本）
- 验证时间轴格式
- 修复常见格式错误

**输入**: `raw/ep01.srt`  
**输出**: `List[SrtEntry]` - SRT条目列表  
**依赖**: 无

---

#### `SrtTextExtractor` - SRT文本提取工具 ✅
**职责**: 从SRT中提取纯文本并使用LLM智能修复
- 移除时间轴信息
- 智能添加标点符号
- 修正错别字和同音错字
- 实体标准化（有/无小说参考两种模式）
- 修复缺字问题
- 确保语义通顺连贯

**输入**: `List[SrtEntry]` + 可选的novel_reference  
**输出**: `SrtTextExtractionResult` (纯文本 + 时间戳映射)  
**依赖**: `SrtImporter`

**实现状态**: ✅ 已完成  
**LLM配置**: DeepSeek v3.2（格式处理任务，可选Two-Pass改造）  
**Prompt文件**: `srt_script_processing_with_novel.yaml` + `without_novel.yaml`

---

#### `ScriptSegmenter` - 脚本分段工具 ✅⭐
**职责**: 使用Two-Pass LLM将脚本按语义分段
- **Two-Pass策略**：Pass 1初步分段 + Pass 2校验修正
- **句子序号定位**：LLM输出句子序号范围，代码提取内容
- 按叙事逻辑分段（场景转换/情节转折/对话切换）
- 保持SRT时间戳关联
- **JSON输出**：结构化输出

**输入**: 纯文本 + SRT条目列表  
**输出**: `ScriptSegmentationResult` (JSON格式)  
**依赖**: `SrtTextExtractor`

**实现状态**: ✅ v2完成 (2026-02-09) - Two-Pass + JSON + 句子序号定位  
**LLM配置**: DeepSeek v3.2 (默认) → 待实际测试性能  
**Prompt文件**: `script_segmentation_pass1.yaml` + `pass2.yaml`  
**归档**: `archive/v4_tools_20260209/script_segmenter.py` (v1单Pass)

---

---

## Phase II: Novel深度分析 ✅ (已完成 4/4)

### 目标
分析小说的事件时间线、设定库和系统元素，为对齐分析提供结构化数据。

### 2.1 章节标注与分析

#### `NovelAnnotator` - 章节标注工具 ✅ ⭐
**职责**: 基于分段结果进行事件时间线、设定关联和功能性标签标注
- **Three-Pass策略**: 
  - Pass 1: 事件聚合 + 时间线分析
  - Pass 2: 设定关联 + 累积知识库
  - Pass 3: 功能性标签（基于 NOVEL_SEGMENTATION_METHODOLOGY）
- 生成事件时间线（EventTimeline）
- 生成设定知识库（SettingLibrary）
- 生成功能性标签库（FunctionalTagsLibrary）
- 标注地点、时间、地点变化、时间变化
- 标注浓缩优先级（P0-骨架/P1-血肉/P2-皮肤）
- 标注叙事功能、叙事结构、角色关系
- 设定获得时间点（BF/BT/AF）

**输入**: `ParagraphSegmentationResult` + `enable_functional_tags` (可选)  
**输出**: `AnnotatedChapter` (事件时间线 + 设定库 + 功能性标签)  
**依赖**: `NovelSegmenter`

**实现状态**: ✅ 已完成 (2026-02-10 - Three-Pass)  
**LLM配置**: Claude Sonnet 4.5 (推荐)  
**Prompt文件**: `novel_annotation_pass1.yaml` + `pass2.yaml` + `pass3_functional_tags.yaml`  
**性能**: Pass1+2 约30s | Pass3 约50s | 总计约80s/章节

---

### 2.2 系统元素分析

#### `NovelSystemAnalyzer` - 系统元素分析工具 ✅
**职责**: 分析小说前N章，识别核心系统元素并生成系统目录
- 智能识别小说类型
- 归类系统元素（SC001, SC002...）
- 定义追踪策略（quantity/state_change/ownership/encounter）
- 生成初始系统目录（SystemCatalog）

**输入**: 小说前50章内容  
**输出**: `SystemCatalog` (初始系统目录)  
**依赖**: `NovelChapterDetector`

**实现状态**: ✅ 已完成 (2026-02-09)  
**LLM配置**: Claude Sonnet 4.5  
**Prompt文件**: `novel_system_analysis.yaml`  
**Token消耗**: 约10K-20K input + 2K-4K output  
**成本估算**: $0.10-0.15 USD/50章

---

#### `NovelSystemDetector` - 系统元素检测工具 ✅
**职责**: 基于章节标注和系统目录，检测新出现的系统元素
- 检测C类段落中的新元素
- 归类到系统目录（SC001-SC999）
- 增量更新系统目录
- 计算置信度

**输入**: `AnnotatedChapter` + `ParagraphSegmentationResult` + `SystemCatalog`  
**输出**: `SystemUpdateResult` + 更新后的`SystemCatalog`  
**依赖**: `NovelAnnotator`, `NovelSegmenter`, `NovelSystemAnalyzer`

**实现状态**: ✅ 已完成 (2026-02-09)  
**LLM配置**: Claude Sonnet 4.5  
**Prompt文件**: `novel_system_detection.yaml`  
**Token消耗**: 约1.5K-2K input + 500-1K output

---

#### `NovelSystemTracker` - 系统元素追踪工具 ✅
**职责**: 追踪每个事件中的系统元素变化
- 追踪数量变化（获得/消耗）
- 追踪状态变化（升级/降级）
- 追踪所有权变化（转移/交易）
- 追踪遭遇记录

**输入**: `AnnotatedChapter` + `SystemCatalog`  
**输出**: `SystemTrackingResult`  
**依赖**: `NovelAnnotator`, `NovelSystemAnalyzer`

**实现状态**: ✅ 已完成 (2026-02-09)  
**LLM配置**: Claude Sonnet 4.5  
**Prompt文件**: `novel_system_tracking.yaml`  
**Token消耗**: 约2K-3K input + 1K-2K output

---

## Phase III: Novel-Script对齐 ✅ (已完成 1/1)

### 目标
建立Novel和Script的句子级对应关系，识别改写策略。

### 3.1 对齐分析

#### `NovelScriptAligner` - Novel与Script对齐工具 ✅ ⭐
**职责**: 基于Novel Annotation和Script分段结果进行句子级对齐分析
- **基于Annotation结构**: 使用事件/设定标注，不需要Novel全文
- **句子级对齐**: Novel段落/事件 → Script句子
- **改写策略识别**: exact/paraphrase/summarize/expand/none
- **覆盖率统计**: 事件/设定覆盖率分析
- **质量评估**: 置信度、改进建议、质量报告

**输入**: `AnnotatedChapter` (Novel标注) + `ScriptSegmentationResult` (Script分段)  
**输出**: `AlignmentResult` + `AlignmentReport` (可选)  
**依赖**: `NovelAnnotator`, `ScriptSegmenter`

**实现状态**: ✅ 已完成 (2026-02-09)  
**LLM配置**: Claude Sonnet 4.5 (推荐，语义理解强)  
**Prompt文件**: `novel_script_alignment.yaml`  
**测试结果**: 
- 事件覆盖率: 100% (5/5)
- 设定覆盖率: 100% (3/3)
- 平均置信度: 0.94
- 主要改写策略: paraphrase

---

## Phase IV: 验证与质量保证 ✅ (已完成 2/2)

### 目标
验证各阶段处理质量，生成质量报告，确保数据准确性。

### 4.1 质量验证工具

#### `NovelValidator` - 小说处理质量验证 ✅ P0
**职责**: 验证小说处理的各个环节质量
- **编码正确性**: 检测乱码字符（�, \ufffd）
- **章节完整性**: 验证章节连续性，检查缺失/跳号
- **分段合理性**: 
  - ABC类分布（A:10-30%, B:60-80%, C:0-10%）
  - 过度分段检测（>50段/章）
  - 异常长段落（>5000字/段）
- **标注合理性**: 事件数量、设定数量统计
- **生成质量报告**: 评分（0-100）+ 问题列表 + 改进建议

**输入**: 
- `NovelImportResult`
- `List[ChapterInfo]`
- `List[ParagraphSegmentationResult]`
- `List[AnnotatedChapter]`

**输出**: `NovelValidationReport`  
**依赖**: 所有Novel处理工具

**实现状态**: ✅ 已完成 (2026-02-09)  
**测试结果**: 质量评分 88/100 (末哥超凡公路)  
**文件**: `src/tools/novel_validator.py`

---

#### `ScriptValidator` - 脚本处理质量验证 ✅ P0
**职责**: 验证脚本处理的各个环节质量
- **时间轴连续性**: 检查时间跳跃、重叠
- **文本完整性**: 验证SRT覆盖率（>95%）
- **分段合理性**: 
  - 分段数量（5-20段/集）
  - 时间戳匹配准确性
  - 段落长度分布
- **生成质量报告**: 评分（0-100）+ 问题列表

**输入**:
- `List[SrtEntry]`
- `SrtTextExtractionResult`
- `ScriptSegmentationResult`

**输出**: `ScriptValidationReport`  
**依赖**: 所有Script处理工具

**实现状态**: ✅ 已完成 (2026-02-09)  
**测试结果**: 质量评分 85/100 (天命桃花 ep01)  
**文件**: `src/tools/script_validator.py`

---

## Phase V: 高级分析与优化 🚧 (进行中 3/5)

### 目标
Hook分析、叙事特征标注、Script改进，进一步提升对齐质量和改编分析能力。

### 5.1 Hook分析工具

#### `HookDetector` - Hook边界检测 ✅ P1
**职责**: 检测ep01是否存在Hook及其边界
- **基于5个特征判断**:
  1. 独立语义段落
  2. 非具象的当下描述（总结/预告）
  3. Hook后连贯性增强
  4. Hook后可在Novel开头匹配
  5. Hook与简介相似度高
- 定位Body起点时间
- 计算置信度

**输入**: ep01的Script分段 + Novel简介  
**输出**: `HookDetectionResult`  
**依赖**: `ScriptSegmenter`

**实现状态**: ✅ 已完成 (2026-02-09)  
**测试结果**: 成功检测45.6秒Hook，置信度90% (天命桃花)  
**文件**: `src/tools/hook_detector.py`  
**复用归档**: ✅ 复用 `archive/v2_deprecated/alignment_modules/hook_detector.py`  
**改造工作**: 接口适配BaseTool，调整输入输出格式  
**预计时间**: 1-2天  
**LLM配置**: DeepSeek v3.2 或 Claude

---

#### `HookContentAnalyzer` - Hook来源分析 ✅ P1
**职责**: 分析Hook的内容来源
- **分层提取**: 提取Hook的4层信息
  - 世界观设定（World Building）
  - 系统机制（Game Mechanics）
  - 道具装备（Items/Equipment）
  - 情节事件（Plot Events）
- **对比Novel简介**: 分层相似度计算（Jaccard相似度）
- **推断来源**: 简介/章节/独立创作
- **智能路由**: 为对齐流程提供策略建议

**输入**: Hook段落 + Novel简介 + Novel元数据  
**输出**: `HookAnalysisResult`  
**依赖**: `HookDetector`, `NovelMetadataExtractor`

**实现状态**: ✅ 已完成 (2026-02-09)  
**测试结果**: 成功分析Hook分层内容，相似度计算正常 (天命桃花)  
**文件**: `src/tools/hook_content_analyzer.py`  
**复用归档**: ✅ 复用 `archive/v2_modules_20260208/modules/alignment/hook_content_extractor.py`  
**改造工作**: 接口适配 + Jaccard相似度算法  
**LLM配置**: DeepSeek v3.2

---

### 5.2 Script改进工具

#### `ScriptSegmenter` v2 - ABC类脚本分段 ✅ P2
**职责**: 改进版ScriptSegmenter，支持ABC类分段
- **Two-Pass分段**: Pass 1初步分段 + Pass 2校验修正
- **ABC类分段**: 
  - A类-设定（Setting）：旁白讲解世界观、规则说明
  - B类-事件（Event）：对话、动作、场景推进
  - C类-系统（System）：系统提示音、数据面板显示
- **Pass 3分类**: 基于分段结果进行ABC三分类

**输入**: 纯文本 + SRT条目  
**输出**: `ScriptSegmentationResult` (增强版，包含category字段)  
**依赖**: `SrtTextExtractor`

**实现状态**: ✅ 已完成 (2026-02-09)  
**测试结果**: 15段落，A类1段，B类14段，C类0段 (天命桃花)  
**文件**: `src/tools/script_segmenter.py` (已升级)  
**新增Prompt**: `src/prompts/script_segmentation_abc_classification.yaml`  
**LLM配置**: DeepSeek v3.2  
**实际效果**: ABC分类准确，为对齐提供类型匹配基础

---

### 5.3 叙事特征标注工具

#### `NovelTagger` - 小说叙事特征标注 ✅ P2
**职责**: 为Novel章节标注叙事特征（与NovelAnnotator互补）
- **叙事视角**: 第一人称/第三人称全知/第三人称限制
- **时间结构**: 线性/倒叙/插叙/平行
- **叙事节奏**: 快节奏/中速/慢节奏
- **情感基调**: 紧张/轻松/悬疑/幽默/压抑/热血/温馨
- **关键主题**: 生存、成长、复仇、友情、权力等
- **类型标签**: 动作、战斗、悬疑、日常、心理等
- **叙事技巧**: 闪回、伏笔、对比、悬念等

**输入**: `List[ParagraphSegmentationResult]` + 项目名称  
**输出**: `NovelTaggingResult`  
**依赖**: `NovelSegmenter`

**实现状态**: ✅ 已完成 (2026-02-09)  
**Schema**: 新增 `ChapterTags`, `NovelTaggingResult` (schemas_novel.py)  
**文件**: `src/tools/novel_tagger.py`  
**Prompt**: `src/prompts/novel_tagging.yaml`  
**用途**: 
- 对齐质量增强（节奏/情感一致性）
- 改编评估（核心段落保留度）
- 内容筛选（精华版/预告片）
**LLM配置**: DeepSeek v3.2

---

#### `ScriptTagger` - 脚本叙事特征标注 🔜 P2
**职责**: 为Script段落添加叙事特征标签
- **改编类型**: 直接/简化/扩展/创作
- **内容类型**: 剧情/过渡/悬念/回顾
- **节奏标签**: 快节奏/中节奏/慢节奏
- **重要度**: 核心/重要/衔接
- **情感标签**: 紧张/激动/平缓/悬疑

**输入**: `ScriptSegmentationResult`  
**输出**: `ScriptSegmentTags`  
**依赖**: `ScriptSegmenter`

**实现状态**: 🔜 待实现 (优先级 P2)  
**用途**: 与NovelTagger输出对比，评估改编质量  
**预计时间**: 2-3天  
**LLM配置**: Claude Sonnet 4.5

---

## 🎯 工具优先级（基于Workflow需求）

### **P0 优先级 - 质量验证** ✅ (已完成)

| 序号 | 工具 | 时间 | 状态 | 复杂度 |
|-----|------|------|------|--------|
| 1 | `NovelValidator` | 1-2天 | ✅ 已完成 | 低 |
| 2 | `ScriptValidator` | 1天 | ✅ 已完成 | 低 |

**完成情况**:
- ✅ NovelValidator: 质量评分88/100，测试通过
- ✅ ScriptValidator: 质量评分85/100，测试通过
- ✅ 为后续工具提供质量门禁

---

### **P1 优先级 - Hook分析** ✅ (已完成)

| 序号 | 工具 | 时间 | 状态 | 复用归档 |
|-----|------|------|------|----------|
| 3 | `HookDetector` | 1-2天 | ✅ 已完成 | ✅ 95%已复用 |
| 4 | `HookContentAnalyzer` | 2天 | ✅ 已完成 | ✅ 80%已复用 |

**完成情况**:
- ✅ HookDetector: 成功检测45.6秒Hook，置信度90%
- ✅ HookContentAnalyzer: 分层提取和相似度计算正常
- ✅ 为对齐流程提供智能策略建议

---

### **P2 优先级 - 高级分析** 🚧 (部分完成 2/3)

| 序号 | 工具 | 时间 | 状态 | 复杂度 |
|-----|------|------|------|--------|
| 5 | `ScriptSegmenter v2` (ABC类) | 3-4天 | ✅ 已完成 | 中 |
| 6 | `NovelTagger` | 2-3天 | ✅ 已完成 | 中 |
| 7 | `ScriptTagger` | 2-3天 | 🔜 待实现 | 中 |

**完成情况**:
- ✅ ScriptSegmenter v2: ABC分类功能完成，测试通过
- ✅ NovelTagger: 叙事特征标注完成
- ⏳ ScriptTagger: 待实现（与NovelTagger类似）

---

### **已废弃的工具** ❌

以下工具在新架构中已被其他工具替代，不再实现：

| 工具 | 替代方案 | 理由 |
|-----|---------|------|
| `NovelSemanticAnalyzer` | `NovelAnnotator` | Annotator已提供事件时间线 |
| `ScriptSemanticAnalyzer` | `ScriptSegmenter` | Segmenter已提供段落分析 |
| `SemanticMatcher` | `NovelScriptAligner` | Aligner直接基于Annotation对齐 |
| `AlignmentValidator` | `NovelScriptAligner` | Aligner内置AlignmentReport |
| `NovelChapterSplitter` | Workflow层动态提取 | 无需拆分文件 |

---

## 📋 工具开发检查清单

每个工具开发时必须完成：

- [ ] **接口定义**: 继承`BaseTool`，定义清晰的`execute()`方法
- [ ] **Schema定义**: 在`src/core/schemas_*.py`中定义输入输出数据模型
- [ ] **文档**: 
  - 编写完整的docstring（Google Style）
  - 创建独立文档 `docs/tools/{tool_name}.md`
- [ ] **测试脚本**: 在`scripts/test/`创建测试脚本
- [ ] **日志**: 使用`logging`模块，不用print
- [ ] **配置**: 不硬编码，使用`config`
- [ ] **错误处理**: 完善的异常处理和错误信息
- [ ] **Prompt文件**: LLM工具需要创建独立Prompt文件（`src/prompts/`）

---

## 📊 当前状态总结

**总体进度**: 17/19 工具完成 (89%)  
**Phase I**: 8/8 完成 ✅  
**Phase II**: 4/4 完成 ✅  
**Phase III**: 1/1 完成 ✅  
**Phase IV**: 2/2 完成 ✅ (P0工具)  
**Phase V**: 3/5 完成 🚧 (P1/P2工具)

**最新完成** (2026-02-09):
1. ✅ **P0工具** - NovelValidator, ScriptValidator（质量验证）
2. ✅ **P1工具** - HookDetector, HookContentAnalyzer（Hook分析）
3. ✅ **P2工具** - ScriptSegmenter v2 (ABC分类), NovelTagger（叙事特征）

**剩余工具**:
- ⏳ ScriptTagger（Script叙事特征标注，P2）
- ⏳ NovelChapterDetector改进（章节检测准确性优化，可选）

**下一步建议**:
1. 可选：实现ScriptTagger，与NovelTagger配对
2. 质量验证：在实际项目中测试完整Workflow
3. 性能优化：LLM调用批量化、并行化处理

---

## ✅ 已完成工具详细列表（按Phase分组）

### Phase I: 素材标准化与分段 (8/8 完成)

#### 1. **NovelImporter** - 小说导入工具 (2026-02-08)
   - 状态: ✅ 已实现并测试
   - 文件: `src/tools/novel_importer.py`
   - Schema: `src/core/schemas_novel.py` (NovelImportResult)
   - 测试: `scripts/test/test_novel_importer.py`
   - 验证结果: 成功处理 348KB 小说文件，126,966 字符
   - 归一化: 编码检测、BOM移除、换行统一、空行合并、章节间距

2. **NovelMetadataExtractor** - 小说元数据提取工具 (2026-02-09)
   - 状态: ✅ 已实现并测试
   - 文件: `src/tools/novel_metadata_extractor.py`
   - Schema: `src/core/schemas_novel.py` (NovelMetadata)
   - 测试: `scripts/test/test_novel_metadata_extractor.py`
   - LLM: DeepSeek v3.2 (简单任务)
   - Prompt: `introduction_extraction.yaml` (单Pass)
   - 验证结果: 成功提取标题、作者、8个标签，简介过滤压缩率19.1%

3. **NovelChapterDetector** - 章节检测工具 (2026-02-09)
   - 状态: ✅ 已实现并测试
   - 文件: `src/tools/novel_chapter_detector.py`
   - Schema: `src/core/schemas_novel.py` (ChapterInfo)
   - 测试: `scripts/test/test_novel_chapter_detector.py`
   - 验证结果: 正则识别章节标题，支持中文数字转换，验证章节连续性

4. **NovelSegmenter** ⭐ - 小说分段工具 v3 (2026-02-09)
   - 状态: ✅ v3完成 - Two-Pass + JSON + 行号定位
   - 文件: `src/tools/novel_segmenter.py`
   - Schema: `src/core/schemas_novel.py` (ParagraphSegmentationResult, SegmentationOutput)
   - 测试: `scripts/test/test_novel_segmenter_output.py`
   - LLM: Claude Sonnet 4.5 (强制，复杂分段)
   - Prompt: `novel_chapter_segmentation_pass1.yaml` + `pass2.yaml` (Two-Pass)
   - **Prompt v2改进** (2026-02-09)：
     * **改进背景**：初版prompt依赖关键词和格式特征，导致A类（设定）识别不准确
     * **核心问题**：无法区分"核心世界规则"与"情节细节"（如"车队铁律"被误标为B类）
     * **解决方案**：引入**A类判断三问框架**
       1. 功能问题：是否在解释"这个小说世界的核心运作规则"？
       2. 重要性问题：读者不理解这段内容，能否看懂后续情节？
       3. 普遍性问题：是否是世界的普遍规则（对所有人/长期有效）？
     * **实现位置**：
       - Pass 1: 添加A类判断三问引导（`novel_chapter_segmentation_pass1.yaml`）
       - Pass 2: 强化A/B混合检查，要求对每个段落应用判断三问（`pass2.yaml`）
     * **测试结果**：成功识别"车队铁律"和"序列超凡设定"为独立A类段落
     * **关键原则**：避免基于表面特征判断，强调逻辑推理和语义理解
   - 验证结果: 
     * 段落数量：11个（100%准确）
     * 类型分布：A:3, B:7, C:1
     * 原文还原：99.63%
     * 准确率提升：78% → 100% (+22%)
   - 归档: `archive/v3_tools_20260209/novel_segmenter.py` (旧版)

5. **SrtImporter** - SRT导入工具
   - 状态: ✅ 已实现并测试
   - 文件: `src/tools/srt_importer.py`
   - Schema: `src/core/schemas_script.py` (SrtEntry)

#### 6. **SrtTextExtractor** - SRT文本提取工具 (2026-02-09)
   - 状态: ✅ 已实现并测试
   - 文件: `src/tools/srt_text_extractor.py`
   - Schema: `src/core/schemas_script.py` (SrtTextExtractionResult)
   - LLM: DeepSeek v3.2 (格式处理)
   - Prompt: `srt_script_processing_with_novel.yaml` + `without_novel.yaml`
   - 功能: 智能修复标点、错别字、实体标准化

#### 7. **ScriptSegmenter** - 脚本分段工具 v2 (2026-02-09) ⭐
   - 状态: ✅ v2完成 - Two-Pass + JSON + 句子序号定位
   - 文件: `src/tools/script_segmenter.py`
   - Schema: `src/core/schemas_script.py` (ScriptSegmentationResult)
   - LLM: DeepSeek v3.2 (默认)
   - Prompt: `script_segmentation_pass1.yaml` + `pass2.yaml` (Two-Pass)
   - 功能: 按叙事逻辑分段（场景转换/情节转折/对话切换）
   - 归档: `archive/v4_tools_20260209/script_segmenter.py` (v1单Pass)
   - **待升级**: v3将支持ABC类分段（P2优先级）

#### 8. **NovelChapterDetector** - 章节检测工具 (2026-02-09)
   - 状态: ✅ 已实现并测试
   - 文件: `src/tools/novel_chapter_detector.py`
   - Schema: `src/core/schemas_novel.py` (ChapterInfo)
   - 测试: `scripts/test/test_novel_chapter_detector.py`
   - 功能: 正则识别章节标题，支持中文数字转换，验证章节连续性

---

### Phase II: Novel深度分析 (4/4 完成)

#### 9. **NovelAnnotator** - 章节标注工具 (2026-02-10) ⭐
   - 状态: ✅ 已完成 - Three-Pass策略
   - 文件: `src/tools/novel_annotator.py`
   - Schema: `src/core/schemas_novel.py` (AnnotatedChapter, EventTimeline, SettingLibrary, FunctionalTagsLibrary)
   - 测试: `scripts/test/test_novel_annotator.py`
   - LLM: Claude Sonnet 4.5 (推荐)
   - Prompt: `novel_annotation_pass1.yaml` + `pass2.yaml` + `pass3_functional_tags.yaml`
   - 功能:
     * Pass 1: 时间线分析 + 事件聚合
     * Pass 2: 设定关联 + 累积知识库
     * Pass 3: 功能性标签（基于 NOVEL_SEGMENTATION_METHODOLOGY）
   - 输出:
     * 事件时间线（EventTimeline）
     * 设定知识库（SettingLibrary）
     * 功能性标签库（FunctionalTagsLibrary）
     * 时空标注（地点、时间、变化）
     * 浓缩优先级（P0-骨架/P1-血肉/P2-皮肤）
   - 性能: Pass1+2 约30s | Pass3 约50s | 总计约80s/章节

#### 10. **NovelSystemAnalyzer** - 系统元素分析工具 (2026-02-09)
   - 状态: ✅ 已完成
   - 文件: `src/tools/novel_system_analyzer.py`
   - Schema: `src/core/schemas_novel.py` (SystemCatalog, SystemCategory)
   - 测试: `scripts/test/test_novel_system_analyzer.py`
   - LLM: Claude Sonnet 4.5
   - Prompt: `novel_system_analysis.yaml`
   - 功能: 分析前50章，生成初始系统目录
   - Token消耗: 约10K-20K input + 2K-4K output
   - 成本: $0.10-0.15 USD/50章

#### 11. **NovelSystemDetector** - 系统元素检测工具 (2026-02-09)
   - 状态: ✅ 已完成
   - 文件: `src/tools/novel_system_detector.py`
   - Schema: `src/core/schemas_novel.py` (SystemUpdateResult, SystemElementUpdate)
   - 测试: `scripts/test/test_novel_system_detector.py`
   - LLM: Claude Sonnet 4.5
   - Prompt: `novel_system_detection.yaml`
   - 功能: 检测C类段落中的新系统元素，增量更新目录
   - Token消耗: 约1.5K-2K input + 500-1K output

#### 12. **NovelSystemTracker** - 系统元素追踪工具 (2026-02-09)
   - 状态: ✅ 已完成
   - 文件: `src/tools/novel_system_tracker.py`
   - Schema: `src/core/schemas_novel.py` (SystemTrackingResult, SystemChange)
   - 测试: `scripts/test/test_novel_system_tracker.py`
   - LLM: Claude Sonnet 4.5
   - Prompt: `novel_system_tracking.yaml`
   - 功能: 追踪每个事件中的系统元素变化（数量/状态/所有权）
   - Token消耗: 约2K-3K input + 1K-2K output

---

### Phase III: Novel-Script对齐 (1/1 完成)

#### 13. **NovelScriptAligner** - Novel与Script对齐工具 (2026-02-09) ⭐
   - 状态: ✅ 已完成
   - 文件: `src/tools/novel_script_aligner.py`
   - Schema: `src/core/schemas_alignment.py` (AlignmentResult, AlignmentReport)
   - 测试: `scripts/test/test_novel_script_aligner.py`
   - LLM: Claude Sonnet 4.5 (推荐，语义理解强)
   - Prompt: `novel_script_alignment.yaml`
   - 功能:
     * 基于Annotation的句子级对齐
     * 改写策略识别（exact/paraphrase/summarize/expand/none）
     * 覆盖率统计（事件/设定）
     * 质量评估（置信度、改进建议）
   - 测试结果:
     * 事件覆盖率: 100% (5/5)
     * 设定覆盖率: 100% (3/3)
     * 平均置信度: 0.94
     * 主要改写策略: paraphrase

---

## 📚 参考资源

### 归档工具（可复用）

#### Hook相关工具 ✅ 高复用价值
- `archive/v2_deprecated/alignment_modules/hook_detector.py`
  - 功能: Hook边界检测（基于5个特征）
  - 复用度: 95%（仅需接口适配）
  - 用途: 实现新的HookDetector
  
- `archive/v2_modules_20260208/modules/alignment/hook_content_extractor.py`
  - 功能: Hook分层内容提取（4层）
  - 复用度: 80%（需增强相似度算法）
  - 用途: 实现新的HookContentAnalyzer

- `archive/v3_maintenance_docs/HOOK_BODY_SEPARATION_IMPLEMENTATION.md`
  - 文档: Hook-Body分离架构实施总结
  - 用途: 理解Hook检测的设计理念

#### 其他归档工具
- `archive/v3_tools_20260209/novel_segmenter.py` - NovelSegmenter v2（旧版）
- `archive/v4_tools_20260209/script_segmenter.py` - ScriptSegmenter v1（单Pass）
- `archive/v2_tools_20260208/novel_processor.py` - 旧版小说处理器
- `archive/v2_tools_20260208/srt_processor.py` - 旧版SRT处理器

### 开发规范
- `docs/DEV_STANDARDS.md` - 开发标准与架构规范
- `.cursorrules` - Cursor AI编码规则
- `docs/tools/README.md` - Tools模块技术参考

---

**最后更新**: 2026-02-09  
**下一步**: 实现P0优先级工具（NovelValidator, ScriptValidator）
