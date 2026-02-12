# 工具快速参考

**最后更新**: 2026-02-12  
**目的**: 提供所有工具的快速查找表和复用指南

---

## 📋 工具总览

当前项目共有 **17个工具**，按功能分为4大类：

| 类别 | 工具数量 | 完成度 |
|------|---------|--------|
| Novel处理工具 | 8个 | ✅ 100% |
| Script处理工具 | 4个 | ✅ 100% |
| 对齐工具 | 1个 | ✅ 100% |
| Hook工具 | 2个 | ✅ 100% |

---

## 🔍 按场景查找工具

### 场景1: 处理小说文件
```
原始txt → NovelImporter → NovelMetadataExtractor → NovelChapterDetector 
          → NovelSegmenter → NovelAnnotator → NovelSystemDetector
```

### 场景2: 处理脚本文件
```
原始srt → SrtImporter → SrtTextExtractor → ScriptSegmenter → ScriptValidator
```

### 场景3: 小说-脚本对齐
```
Novel数据 + Script数据 → NovelScriptAligner → AlignmentReport
```

### 场景4: Hook检测（第一集开头）
```
Script ep01 → HookDetector → HookContentAnalyzer
```

---

## 📊 Novel工具链

### 1. NovelImporter - 小说导入工具
**职责**: 读取、规范化并导入小说文件

| 项目 | 内容 |
|------|------|
| **输入** | 原始小说文件路径 + 项目名称 |
| **输出** | `NovelImportResult` (保存路径、元数据) |
| **文件路径** | `src/tools/novel_importer.py` |
| **Schema** | `schemas_novel/basic.py` |
| **依赖** | 无 |
| **LLM** | ❌ 不使用 |

**核心功能**:
- 编码检测与统一（UTF-8）
- 换行符规范化
- 去除BOM标记
- 保存到 `data/projects/{project_id}/raw/novel/` 

---

### 2. NovelMetadataExtractor - 元数据提取工具
**职责**: 提取小说的基本信息

| 项目 | 内容 |
|------|------|
| **输入** | 规范化的小说文本 |
| **输出** | `NovelMetadata` (标题、作者、标签、简介) |
| **文件路径** | `src/tools/novel_metadata_extractor.py` |
| **Schema** | `schemas_novel/basic.py::NovelMetadata` |
| **依赖** | `NovelImporter` |
| **LLM** | ✅ DeepSeek v3.2 (可选) |
| **Prompt** | `introduction_extraction.yaml` |

**核心功能**:
- 提取标题、作者
- 提取标签/分类（从【标签】格式）
- 智能过滤简介（移除营销文案，保留世界观）

---

### 3. NovelChapterDetector - 章节检测工具
**职责**: 检测章节边界

| 项目 | 内容 |
|------|------|
| **输入** | 规范化的小说文本 |
| **输出** | `List[ChapterInfo]` (章节索引列表) |
| **文件路径** | `src/tools/novel_chapter_detector.py` |
| **Schema** | `schemas_novel/basic.py::ChapterInfo` |
| **依赖** | `NovelImporter` |
| **LLM** | ❌ 不使用（正则表达式） |

**核心功能**:
- 识别章节标题模式（第X章、ChapterX）
- 定位章节起始位置（行号、字符位置）
- 统计章节字数
- 生成章节索引

---

### 4. NovelSegmenter - 小说分段工具 ⭐
**职责**: 使用Two-Pass LLM对小说章节进行叙事分段

| 项目 | 内容 |
|------|------|
| **输入** | 规范化的小说文本 + 章节号 |
| **输出** | `SegmentationResult` (JSON格式) |
| **文件路径** | `src/tools/novel_segmenter.py` |
| **Schema** | `schemas_novel/segmentation.py` |
| **依赖** | `NovelImporter`, `NovelChapterDetector` |
| **LLM** | ✅ Claude Sonnet 4.5 (强制) |
| **Prompt** | `novel_chapter_segmentation_pass1.yaml` + `pass2.yaml` |
| **Two-Pass** | ✅ Pass 1初步分段 + Pass 2校验修正 |

**核心功能**:
- **ABC三类分段**：A类设定/B类事件/C类系统
- **行号定位**：LLM输出行号范围，代码提取内容
- **JSON输出**：结构化输出，可完全还原原文（99.63%）
- **准确率**：100%（vs 旧版78%）

**重要说明**: 此工具**不可使用DeepSeek**，复杂分段任务必须使用Claude

---

### 5. NovelAnnotator - 小说标注工具 ⭐
**职责**: 标注事件、设定关联、功能标签

| 项目 | 内容 |
|------|------|
| **输入** | `SegmentationResult` |
| **输出** | `AnnotatedChapter` |
| **文件路径** | `src/tools/novel_annotator.py` |
| **Schema** | `schemas_novel/annotation.py` |
| **依赖** | `NovelSegmenter` |
| **LLM** | ✅ Claude Sonnet 4.5 |
| **Prompt** | `novel_annotation_pass1.yaml` + `pass2.yaml` |
| **Two-Pass** | ✅ Pass 1事件聚合 + Pass 2设定关联 |

**核心功能**:
- **Pass 1**: 事件聚合（将B类段落聚合为事件）
- **Pass 2**: 设定关联（A类设定关联到事件：BF/BT/AF）
- 构建累积知识库（世界观、人物、系统）
- 输出事件时间线

---

### 6. NovelTagger - 功能标签生成工具
**职责**: 生成功能标签（在NovelAnnotator基础上增强）

| 项目 | 内容 |
|------|------|
| **输入** | `AnnotatedChapter` |
| **输出** | `TaggedChapter` |
| **文件路径** | `src/tools/novel_tagger.py` |
| **Schema** | `schemas_novel/annotation.py::FunctionalTag` |
| **依赖** | `NovelAnnotator` |
| **LLM** | ✅ DeepSeek v3.2 |
| **Prompt** | `novel_tagging.yaml` |

**核心功能**:
- 生成功能标签（世界观构建、冲突制造、伏笔埋设等）
- 标注叙事手法（对比、悬念、铺垫等）

---

### 7. NovelValidator - 小说验证工具
**职责**: 验证小说数据质量

| 项目 | 内容 |
|------|------|
| **输入** | `AnnotatedChapter` |
| **输出** | `ValidationResult` |
| **文件路径** | `src/tools/novel_validator.py` |
| **Schema** | `schemas_novel/validation.py` |
| **依赖** | `NovelAnnotator` |
| **LLM** | ❌ 不使用（规则验证） |

**核心功能**:
- 结构完整性检查
- 数据格式验证
- 质量评分

---

### 8. NovelSystemDetector - 系统元素检测工具 ⭐
**职责**: 从标注结果中识别新系统元素

| 项目 | 内容 |
|------|------|
| **输入** | `AnnotatedChapter` + `SystemCatalog` |
| **输出** | `SystemUpdateResult` |
| **文件路径** | `src/tools/novel_system_detector.py` |
| **Schema** | `schemas_novel/system.py` |
| **依赖** | `NovelAnnotator` |
| **LLM** | ✅ Claude Sonnet 4.5 |
| **Prompt** | `novel_system_detection.yaml` |
| **独立Pass** | ✅ Pass 3（避免污染NovelAnnotator） |

**核心功能**:
- 识别新系统元素（从C类段落和事件中）
- 自动分类到系统目录（SC001-角色、SC002-物品等）
- 避免重复检测

**设计理由**: 独立Pass而非集成到NovelAnnotator，成本增加$0.02/章，但保护NovelAnnotator稳定性

---

## 📊 Script工具链

### 9. SrtImporter - SRT导入工具
**职责**: 读取并规范化SRT文件

| 项目 | 内容 |
|------|------|
| **输入** | 原始SRT文件路径 |
| **输出** | `SrtImportResult` |
| **文件路径** | `src/tools/srt_importer.py` |
| **Schema** | `schemas_script.py::SrtEntry` |
| **依赖** | 无 |
| **LLM** | ❌ 不使用 |

**核心功能**:
- 解析SRT格式（序号、时间轴、文本）
- 编码检测与统一
- 时间轴验证
- 保存到 `data/projects/{project_id}/raw/srt/`

---

### 10. SrtTextExtractor - SRT文本提取工具
**职责**: 提取纯文本并修正

| 项目 | 内容 |
|------|------|
| **输入** | `List[SrtEntry]` |
| **输出** | 纯文本 (Markdown格式) |
| **文件路径** | `src/tools/srt_text_extractor.py` |
| **Schema** | `schemas_script.py` |
| **依赖** | `SrtImporter` |
| **LLM** | ✅ DeepSeek v3.2 (可选) |
| **Prompt** | 内置（标点修复） |

**核心功能**:
- 提取纯文本
- LLM添加标点符号
- 修正错别字
- 智能实体识别（无小说参考时）

**成本**: ~$0.02-0.04 / 集（仅标点修复）

---

### 11. ScriptSegmenter - 脚本分段工具 ⭐
**职责**: 使用Two-Pass ABC分类法对脚本分段

| 项目 | 内容 |
|------|------|
| **输入** | Script文本 |
| **输出** | `SegmentationResult` (ABC分类) |
| **文件路径** | `src/tools/script_segmenter.py` |
| **Schema** | `schemas_script.py::ABCSegment` |
| **依赖** | `SrtTextExtractor` |
| **LLM** | ✅ DeepSeek v3.2 标准 |
| **Prompt** | `script_segmentation_abc_classification.yaml` |
| **Two-Pass** | 🚧 **待改造**（当前单Pass） |

**核心功能**:
- **ABC三类分段**：A类设定/B类事件/C类系统
- 与NovelSegmenter使用相同分类原则
- 为对齐工具提供结构化输入

**待优化**: 改造为Two-Pass以提高准确率

---

### 12. ScriptValidator - 脚本验证工具
**职责**: 验证脚本数据质量

| 项目 | 内容 |
|------|------|
| **输入** | `SegmentationResult` |
| **输出** | `ValidationResult` |
| **文件路径** | `src/tools/script_validator.py` |
| **Schema** | `schemas_novel/validation.py` |
| **依赖** | `ScriptSegmenter` |
| **LLM** | ❌ 不使用（规则验证） |

**核心功能**:
- 结构完整性检查
- 时间轴连续性验证
- 质量评分

---

## 📊 对齐工具

### 13. NovelScriptAligner - 小说-脚本对齐工具
**职责**: 小说与脚本对齐（改编分析）

| 项目 | 内容 |
|------|------|
| **输入** | `AnnotatedChapter` + `SegmentationResult` (Script) |
| **输出** | `AlignmentResult` |
| **文件路径** | `src/tools/novel_script_aligner.py` |
| **Schema** | `schemas_alignment.py` |
| **依赖** | `NovelAnnotator`, `ScriptSegmenter` |
| **LLM** | ✅ Claude Sonnet 4.5 |
| **Prompt** | `novel_script_alignment.yaml` |

**核心功能**:
- 句子级对齐
- 改编类型分析（原样、简化、扩展、删除、新增）
- 对齐质量评分

---

## 📊 Hook工具

### 14. HookDetector - Hook检测工具
**职责**: 检测脚本开头Hook（ep01前3分钟）

| 项目 | 内容 |
|------|------|
| **输入** | Script ep01前180秒 |
| **输出** | `HookDetectionResult` |
| **文件路径** | `src/tools/hook_detector.py` |
| **Schema** | 自定义 |
| **依赖** | `SrtTextExtractor` |
| **LLM** | ✅ Claude Sonnet 4.5 |
| **Prompt** | `hook_detection.yaml` |

**核心功能**:
- 识别Hook类型（冲突、悬念、反差等）
- 定位Hook时间段
- Hook强度评分

---

### 15. HookContentAnalyzer - Hook内容分析工具
**职责**: 深度分析Hook特性

| 项目 | 内容 |
|------|------|
| **输入** | `HookDetectionResult` + Hook文本 |
| **输出** | `HookAnalysisResult` |
| **文件路径** | `src/tools/hook_content_analyzer.py` |
| **Schema** | 自定义 |
| **依赖** | `HookDetector` |
| **LLM** | ✅ Claude Sonnet 4.5 |
| **Prompt** | `hook_content_analysis.yaml` |

**核心功能**:
- Hook叙事手法分析
- Hook效果预测
- Hook优化建议

---

## 🔧 复用指南

### 编写新功能前必读

在编写任何新功能前，**必须**检查以下Manager和工具是否已实现相关功能：

### 核心Manager（必须优先使用）

| Manager | 功能 | 文件路径 |
|---------|------|----------|
| **ArtifactManager** | 文件版本管理、自动版本化保存 | `src/core/artifact_manager.py` |
| **ProjectManagerV2** | 项目元数据管理、目录结构创建 | `src/core/project_manager_v2.py` |
| **LLMClientManager** | LLM客户端统一管理（Claude/DeepSeek） | `src/core/llm_client_manager.py` |

**示例 - 保存工具输出**:
```python
# ❌ 错误：手动保存JSON
with open(f"{project_path}/output.json", "w") as f:
    json.dump(result, f)

# ✅ 正确：使用ArtifactManager
from src.core.artifact_manager import ArtifactManager
artifact_manager = ArtifactManager()
artifact_manager.save_artifact(
    project_id=project_id,
    artifact_type="novel_segmentation",
    chapter_id="chapter_01",
    data=result
)
```

**示例 - LLM调用**:
```python
# ❌ 错误：直接创建客户端
import anthropic
client = anthropic.Anthropic(api_key="xxx")

# ✅ 正确：使用LLMClientManager
from src.core.llm_client_manager import get_llm_client, get_model_name
client = get_llm_client("claude")  # 或 "deepseek"
model = get_model_name("deepseek", model_type="v32")  # v32 或 v32-thinking
```

---

## 📈 工具状态追踪

### 已完成工具 (17/17) ✅

| 工具 | 状态 | Two-Pass | LLM | 测试 |
|------|------|----------|-----|------|
| NovelImporter | ✅ | - | ❌ | ✅ |
| NovelMetadataExtractor | ✅ | ❌ | DeepSeek | ✅ |
| NovelChapterDetector | ✅ | - | ❌ | ✅ |
| NovelSegmenter | ✅ | ✅ | Claude | ✅ |
| NovelAnnotator | ✅ | ✅ | Claude | ✅ |
| NovelTagger | ✅ | ❌ | DeepSeek | ✅ |
| NovelValidator | ✅ | - | ❌ | ✅ |
| NovelSystemDetector | ✅ | ❌ | Claude | ✅ |
| SrtImporter | ✅ | - | ❌ | ✅ |
| SrtTextExtractor | ✅ | ❌ | DeepSeek | ✅ |
| ScriptSegmenter | ✅ | ⚠️ 待改造 | DeepSeek | ✅ |
| ScriptValidator | ✅ | - | ❌ | ✅ |
| NovelScriptAligner | ✅ | ❌ | Claude | ✅ |
| HookDetector | ✅ | ❌ | Claude | ✅ |
| HookContentAnalyzer | ✅ | ❌ | Claude | ✅ |

### 待优化工具

1. **ScriptSegmenter**: 改造为Two-Pass（提高准确率）
2. **NovelMetadataExtractor**: 可选Two-Pass改造（提高简介过滤质量）

---

## 🎯 Two-Pass工具设计原则

### 何时使用Two-Pass？

**必须使用Two-Pass的场景**:
- ✅ 复杂的结构化分段任务（NovelSegmenter, ScriptSegmenter）
- ✅ 需要严格规则约束的分类任务
- ✅ 输出结果需要与明确标准对比验证的任务

**可以单次调用的场景**:
- ⚠️ 简单的信息提取（元数据、标签）
- ⚠️ 格式转换和文本处理
- ⚠️ 创意生成和总结任务

### Two-Pass vs 独立Pass

**独立Pass原则**（避免Prompt污染）:
- 当需要在现有工具上添加新任务时，**优先使用独立的新Pass**
- 成本增加<$0.05/章时，**必须使用独立Pass**
- 现有工具已验证稳定，**禁止修改现有Pass**

**案例**: NovelSystemDetector作为独立Pass 3，而非集成到NovelAnnotator的Pass 2

---

## 📊 LLM选择指南

| 任务类型 | 推荐LLM | 原因 |
|---------|---------|------|
| **简单信息提取** | DeepSeek v3.2 标准 | 速度快、成本低 |
| **复杂分段任务** | Claude Sonnet 4.5 | 质量高、理解强 |
| **深度推理** | DeepSeek v3.2 思维链 | 专用推理模型 |
| **格式转换** | DeepSeek v3.2 标准 | 足够使用 |
| **对齐分析** | Claude Sonnet 4.5 | 需要深度理解 |

**成本对比**:
- DeepSeek v3.2: ~$0.02/章
- Claude Sonnet 4.5: ~$0.06/章
- DeepSeek v3.2 思维链: ~$0.08/章

**黄金法则**: 80%任务用DeepSeek，15%用Claude，5%用DeepSeek思维链

---

## 📝 快速查找表

### 按输入类型查找

| 输入 | 使用工具 |
|------|---------|
| 原始txt文件 | NovelImporter |
| 原始srt文件 | SrtImporter |
| 规范化小说文本 | NovelMetadataExtractor, NovelChapterDetector |
| 章节文本 | NovelSegmenter |
| 分段结果（Novel） | NovelAnnotator |
| 标注结果（Novel） | NovelTagger, NovelValidator, NovelSystemDetector |
| SRT条目列表 | SrtTextExtractor |
| Script文本 | ScriptSegmenter |
| 分段结果（Script） | ScriptValidator |
| Novel + Script | NovelScriptAligner |

### 按输出类型查找

| 需要输出 | 使用工具 |
|---------|---------|
| 元数据（标题、作者） | NovelMetadataExtractor |
| 章节列表 | NovelChapterDetector |
| 分段结果（ABC分类） | NovelSegmenter, ScriptSegmenter |
| 事件时间线 | NovelAnnotator |
| 功能标签 | NovelTagger |
| 系统目录 | NovelSystemDetector |
| 对齐关系 | NovelScriptAligner |
| Hook信息 | HookDetector, HookContentAnalyzer |
| 质量报告 | NovelValidator, ScriptValidator |

---

**维护说明**: 
- 新增工具时，请同步更新本文档
- 修改工具接口时，请更新对应表格
- 每次重大更新后，请在顶部更新日期

**最后更新**: 2026-02-12  
**工具总数**: 17个 (100%完成)
