# Tools模块技术参考

Tools模块包含所有无状态、原子性的功能工具。每个工具专注做好一件事。

**本文档目的**: 技术参考，用于查找工具接口、理解实现逻辑、便于代码调用。

## 📁 文档组织

```
docs/tools/
├── README.md                    # 本文件：Tools概述
│
├── phase1_novel/                # Phase I: Novel处理工具
│   ├── README.md
│   ├── novel_importer.md       # 小说导入
│   ├── novel_metadata_extractor.md
│   ├── novel_chapter_detector.md
│   ├── novel_segmenter.md
│   ├── novel_chapter_splitter.md
│   └── novel_validator.md
│
├── phase1_script/               # Phase I: Script处理工具
│   ├── README.md
│   ├── srt_importer.md
│   ├── srt_text_extractor.md
│   ├── script_segmenter.md
│   └── script_validator.md
│
└── phase2_analysis/             # Phase II: 分析对齐工具
    ├── README.md
    ├── hook_detector.md
    ├── hook_content_analyzer.md
    ├── novel_semantic_analyzer.md
    ├── script_semantic_analyzer.md
    ├── semantic_matcher.md
    ├── alignment_validator.md
    ├── novel_tagger.md
    └── script_tagger.md
```

## 🎯 工具设计原则

### 1. 单一职责
每个工具只做一件事，做好一件事。

### 2. 无状态
工具不保存状态，每次调用独立。

### 3. 原子性
工具执行要么成功，要么失败，不会有中间状态。

### 4. 可测试
每个工具都有对应的测试脚本。

### 5. 文档完整
每个工具都有详细的文档和使用示例。

## 🔄 重要更新 (2026-02-11)

**Schemas 拆分**: 小说相关的数据模型已从 `src/core/schemas.py` 拆分到 `src/core/schemas_novel/` 目录：
- `schemas_novel/basic.py`: 基础数据结构（Chapter, Paragraph等）
- `schemas_novel/segmentation.py`: 分段相关（SegmentedChapter等）
- `schemas_novel/annotation.py`: 标注相关（AnnotatedChapter, EventTimeline等）
- `schemas_novel/system.py`: 系统元素相关（SystemCatalog等）
- `schemas_novel/validation.py`: 验证相关（ValidationResult等）

**导入示例**:
```python
# 新的导入方式
from src.core.schemas_novel.basic import Chapter, Paragraph
from src.core.schemas_novel.segmentation import SegmentedChapter
from src.core.schemas_novel.annotation import AnnotatedChapter
```

**影响范围**: 所有 Novel 相关工具的数据模型引用。工具代码已更新，文档中的示例代码可能仍引用旧路径，但不影响理解。

## 📊 工具完整列表 (已实现: 18个)

### Novel处理工具 (9个)

| 工具 | 文档 | 职责 | LLM |
|-----|------|------|-----|
| `NovelImporter` | [novel_importer.md](./novel_importer.md) | 小说导入与规范化 | ❌ |
| `NovelMetadataExtractor` | [novel_metadata_extractor.md](./novel_metadata_extractor.md) | 提取元数据（标题/作者/简介） | ✅ |
| `NovelChapterDetector` | [novel_chapter_detector.md](./novel_chapter_detector.md) | 检测章节边界 | ❌ |
| `NovelSegmenter` | [novel_segmenter.md](./novel_segmenter.md) | 章节ABC分段（Two-Pass） | ✅ |
| `NovelAnnotator` | [novel_annotator.md](./novel_annotator.md) | 事件+设定标注（Three-Pass） | ✅ |
| `NovelSystemAnalyzer` | [novel_system_analyzer.md](./novel_system_analyzer.md) | 全书系统分析 | ✅ |
| `NovelSystemDetector` | [novel_system_detector.md](./novel_system_detector.md) | 章节系统元素检测 | ✅ |
| `NovelSystemTracker` | [novel_system_tracker.md](./novel_system_tracker.md) | 章节系统元素追踪 | ✅ |
| `NovelValidator` | [novel_validator.md](./novel_validator.md) | Novel质量验证 | ❌ |
| `NovelTagger` | [novel_tagger.md](./novel_tagger.md) | Novel叙事特征标注 | ✅ |

### Script处理工具 (5个)

| 工具 | 文档 | 职责 | LLM |
|-----|------|------|-----|
| `SrtImporter` | [srt_importer.md](./srt_importer.md) | SRT字幕导入 | ❌ |
| `SrtTextExtractor` | [srt_text_extractor.md](./srt_text_extractor.md) | SRT文本提取与清洗 | ❌ |
| `ScriptSegmenter` | [script_segmenter.md](./script_segmenter.md) | Script分段（ABC分类） | ✅ |
| `ScriptValidator` | [script_validator.md](./script_validator.md) | Script质量验证 | ❌ |

### Hook分析工具 (2个)

| 工具 | 文档 | 职责 | LLM |
|-----|------|------|-----|
| `HookDetector` | [hook_detector.md](./hook_detector.md) | 检测Hook边界 | ✅ |
| `HookContentAnalyzer` | [hook_content_analyzer.md](./hook_content_analyzer.md) | Hook内容来源分析 | ✅ |

### 对齐工具 (1个)

| 工具 | 文档 | 职责 | LLM |
|-----|------|------|-----|
| `NovelScriptAligner` | [novel_script_aligner.md](./novel_script_aligner.md) | Novel与Script对齐 | ✅ |

**统计**: 
- 总计: **18个工具**
- 文档覆盖率: **100%** (18/18)
- LLM工具: 11个
- 非LLM工具: 7个

---

## 📊 工具开发路线图

详见：[ROADMAP.md](ROADMAP.md)

### ✅ Phase I: 素材标准化（已完成）
- **Novel处理**: 10个工具 ✅
- **Script处理**: 5个工具 ✅
- **验证工具**: 2个工具 ✅

### ⏳ Phase II: 内容分析（进行中）
- **Hook分析**: 2个工具 ✅
- **对齐匹配**: 1个工具 ✅

## 📋 工具技术规范

### 接口定义
所有工具必须继承 `BaseTool` (定义于 `src/core/interfaces.py`)

**基类接口**:
```python
class BaseTool(ABC):
    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """执行工具核心功能"""
        pass
```

### 实现规范
```python
from src.core.interfaces import BaseTool
from typing import Any

class MyTool(BaseTool):
    """
    [工具名称]
    
    职责 (Responsibility):
        单一职责描述
    
    接口 (Interface):
        输入: Type - 说明
        输出: Type - 说明
    
    依赖 (Dependencies):
        - Schema: 使用的数据模型
        - Tools: 依赖的其他工具
        - Config: 需要的配置项
    
    实现逻辑 (Logic):
        1. 步骤1
        2. 步骤2
        3. 步骤3
    """
    
    def __init__(self, config_param: Any = None):
        super().__init__()
        self.config_param = config_param
    
    def execute(self, input_data: Any) -> Any:
        """核心执行逻辑"""
        # 实现
        return result
```

## 📝 工具文档模板

每个工具文档 (`docs/tools/{phase}/{tool_name}.md`) 必须包含：

### 1. 职责定义
- 单一职责描述
- 所属Phase
- 在工具链中的位置

### 2. 接口定义
```python
# 函数签名
def execute(self, input: InputType) -> OutputType
```
- 输入参数: 类型、格式、约束
- 输出结果: 类型、结构、字段说明
- 异常: 可能抛出的异常类型

### 3. 实现逻辑
- 核心算法步骤
- 调用的子工具/函数
- 关键决策逻辑

### 4. 依赖关系
- Schema: `src/core/schemas.py` 中使用的模型
- Tools: 依赖的其他工具（文件路径）
- Config: `src/core/config.py` 中需要的配置项

### 5. 代码示例
```python
# 仅展示接口调用，不是完整流程
tool = ToolName(config)
result = tool.execute(input_data)
# result.field1, result.field2
```

## 🔧 开发新工具流程

### Step 1: 设计与文档
1. 在 `docs/tools/{phase}/` 创建工具文档
2. 定义：职责、接口、实现逻辑、依赖
3. 确认设计无误后开始编码

### Step 2: 实现代码
1. 在 `src/tools/` 创建工具文件
2. 继承 `BaseTool`，实现 `execute()`
3. Docstring 必须与文档一致
4. 添加类型注解

### Step 3: 验证
1. 创建测试脚本 `scripts/test/{tool_name}_test.py`
2. 验证功能正确性和边界情况
3. 记录测试结果

### Step 4: 集成
1. 更新 `docs/tools/README.md` 工具列表
2. 如有新Schema，更新 `docs/core/schemas.md`
3. 提交代码和文档

## 📚 开发参考

### 归档工具参考
可以参考但不要直接复制：
- `archive/v2_tools_20260208/novel_processor.py`
- `archive/v2_tools_20260208/srt_processor.py`

### 相关文档
- [ROADMAP.md](ROADMAP.md) - 工具路线图
- [DEV_STANDARDS.md](../DEV_STANDARDS.md) - 开发规范
- [interfaces.md](../core/interfaces.md) - 接口定义

## 📚 已完成工具文档 (更新: 2026-02-10)

### Novel处理工具 (10个) ✅

#### 基础处理
- [**NovelImporter**](novel_importer.md) - 小说导入与规范化
- [**NovelMetadataExtractor**](novel_metadata_extractor.md) - 元数据提取（标题/作者/简介）
- [**NovelChapterDetector**](novel_chapter_detector.md) - 章节边界检测

#### 核心分析
- [**NovelSegmenter**](novel_segmenter.md) - 章节ABC分段（Two-Pass）
- [**NovelAnnotator**](novel_annotator.md) - 事件+设定标注（Three-Pass）

#### 系统分析
- [**NovelSystemAnalyzer**](novel_system_analyzer.md) - 全书系统元素分析
- [**NovelSystemDetector**](novel_system_detector.md) - 章节系统元素检测
- [**NovelSystemTracker**](novel_system_tracker.md) - 章节系统元素追踪

#### 特征与验证
- [**NovelTagger**](novel_tagger.md) - 叙事特征标注 **[新增: 2026-02-10]**
- [**NovelValidator**](novel_validator.md) - Novel质量验证 **[新增: 2026-02-10]**

---

### Script处理工具 (5个) ✅

#### 基础处理
- [**SrtImporter**](srt_importer.md) - SRT字幕导入
- [**SrtTextExtractor**](srt_text_extractor.md) - SRT文本提取与清洗
- [**ScriptSegmenter**](script_segmenter.md) - Script分段（ABC分类）

#### 特征与验证
- [**ScriptValidator**](script_validator.md) - Script质量验证 **[新增: 2026-02-10]**

---

### Hook分析工具 (2个) ✅

- [**HookDetector**](hook_detector.md) - Hook边界检测 **[新增: 2026-02-10]**
- [**HookContentAnalyzer**](hook_content_analyzer.md) - Hook内容来源分析 **[新增: 2026-02-10]**

---

### 对齐工具 (1个) ✅

- [**NovelScriptAligner**](novel_script_aligner.md) - Novel与Script智能对齐

## 📈 进度追踪

查看 [ROADMAP.md](ROADMAP.md) 了解：
- 已完成工具列表
- 进行中的工具
- 待开发工具
- 优先级排序

---

## 📈 进度追踪

**最后更新**: 2026-02-10  
**当前进度**: 18/18 核心工具完成 (100%) 🎉

### ✅ 已完成 (18个)

**Novel处理** (10个):
- NovelImporter, NovelMetadataExtractor, NovelChapterDetector
- NovelSegmenter, NovelAnnotator
- NovelSystemAnalyzer, NovelSystemDetector, NovelSystemTracker
- NovelTagger, NovelValidator

**Script处理** (5个):
- SrtImporter, SrtTextExtractor, ScriptSegmenter
- ScriptValidator

**Hook分析** (2个):
- HookDetector, HookContentAnalyzer

**对齐工具** (1个):
- NovelScriptAligner

### 📊 文档覆盖率

| 类别 | 代码文件 | 文档文件 | 覆盖率 |
|-----|---------|---------|--------|
| Novel工具 | 10 | 10 | **100%** ✅ |
| Script工具 | 5 | 5 | **100%** ✅ |
| Hook工具 | 2 | 2 | **100%** ✅ |
| 对齐工具 | 1 | 1 | **100%** ✅ |
| **总计** | **18** | **18** | **100%** ✅ |

### 🎯 最新更新 (2026-02-10)

**本次更新**: 补充5个缺失的工具文档
1. ✅ `novel_validator.md` - Novel质量验证
2. ✅ `hook_detector.md` - Hook边界检测
3. ✅ `hook_content_analyzer.md` - Hook内容分析
4. ✅ `novel_tagger.md` - Novel叙事特征标注
5. ✅ `script_validator.md` - Script质量验证

**文档质量**: 所有文档符合DEV_STANDARDS规范
