# NovelAnnotator - 小说章节标注工具

## 职责 (Responsibility)

基于NovelSegmenter的分段结果，进行事件时间线分析、设定关联标注和功能性标签标注。使用 Three-Pass 策略完成复杂的语义分析任务。

**所属阶段**: 小说章节标注（Phase 2）
**工具链位置**: NovelSegmenter → NovelAnnotator → NovelSystemDetector

**Three-Pass 策略**:
- **Pass 1**: 事件时间线分析 + 事件聚合
- **Pass 2**: 设定关联 + 知识库构建
- **Pass 3**: 功能性标签标注（基于 NOVEL_SEGMENTATION_METHODOLOGY）

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    segmentation_result: ParagraphSegmentationResult,
    enable_functional_tags: bool = True,
    **kwargs
) -> AnnotatedChapter
```

### 输入参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| `segmentation_result` | `ParagraphSegmentationResult` | NovelSegmenter的分段结果 |
| `enable_functional_tags` | `bool` | 是否启用Pass 3功能性标签标注（默认True） |

### 输出结果

**类型**: `AnnotatedChapter`

**结构**:
```python
AnnotatedChapter(
    chapter_number: int,                        # 章节号
    event_timeline: EventTimeline,              # 事件时间线（Pass 1）
    setting_library: SettingLibrary,            # 设定知识库（Pass 2）
    functional_tags: FunctionalTagsLibrary,     # 功能性标签库（Pass 3，可选）
    metadata: Dict[str, Any]                    # 元数据
)
```

**EventTimeline 结构**:
```python
EventTimeline(
    chapter_number: int,
    total_events: int,
    events: List[EventEntry],
    metadata: Dict[str, Any]
)
```

**EventEntry 结构**:
```python
EventEntry(
    event_id: str,                    # 事件ID（9位：4位章节号+5位序号+1位类型）
    event_summary: str,               # 事件摘要
    event_type: str,                  # 事件类型（B/C）
    paragraph_indices: List[int],     # 包含的段落编号
    paragraph_contents: List[str],    # 段落内容
    location: str,                    # 地点
    location_change: str,             # 地点变化
    time: str,                        # 时间
    time_change: str                  # 时间变化
)
```

**SettingLibrary 结构**:
```python
SettingLibrary(
    chapter_number: int,
    total_settings: int,
    settings: List[SettingEntry],
    metadata: Dict[str, Any]
)
```

**SettingEntry 结构**:
```python
SettingEntry(
    setting_id: str,                  # 设定编号（S001, S002...）
    setting_title: str,               # 设定标题
    setting_summary: str,             # 设定摘要
    paragraph_index: int,             # 所在段落编号
    paragraph_content: str,           # 段落内容
    acquisition_time: str,            # 获得时间点（BF_/BT_/AF_+事件ID）
    related_event_id: str,            # 关联事件ID
    time_position: str,               # 时间位置（BF/BT/AF）
    accumulated_knowledge: List[str]  # 累积知识库（设定ID列表）
)
```

**FunctionalTagsLibrary 结构**:
```python
FunctionalTagsLibrary(
    chapter_number: int,              # 章节号
    total_paragraphs: int,            # 总段落数
    paragraph_tags: List[ParagraphFunctionalTags],  # 段落标签列表
    priority_distribution: Dict[str, int],  # 优先级分布（P0/P1/P2）
    first_occurrence_count: int,      # 首次信息数量
    metadata: Dict[str, Any]          # 元数据
)
```

**ParagraphFunctionalTags 结构**:
```python
ParagraphFunctionalTags(
    paragraph_index: int,             # 段落索引
    narrative_functions: List[str],   # 叙事功能（故事推进、核心设定等）
    narrative_structures: List[str],  # 叙事结构（钩子、伏笔等）
    character_tags: List[str],        # 角色关系（人物登场、对立关系等）
    priority: str,                    # 浓缩优先级（P0-骨架/P1-血肉/P2-皮肤）
    priority_reason: str,             # 优先级理由
    emotional_tone: str,              # 情绪基调（紧张、绝望等）
    is_first_occurrence: bool,        # 是否首次信息
    repetition_count: Optional[int],  # 重复强调次数
    condensation_advice: str          # 浓缩建议
)
```

## 实现逻辑 (Logic)

### Three-Pass 策略

#### Pass 1: 时间线分析 + 事件聚合

**输入**:
- 格式化的分段结果（段落编号 + 类型 + 内容）

**输出**:
- 事件列表（Markdown格式）
- 每个事件包含：
  - 事件摘要
  - 事件类型（B/C）
  - 包含的段落编号
  - 地点、地点变化
  - 时间、时间变化

**Prompt**: `novel_annotation_pass1`

#### Pass 2: 设定关联 + 校验

**输入**:
- Pass 1 的事件列表（完整）
- A类段落（完整内容）

**输出**:
- 设定列表（Markdown格式）
- 每个设定包含：
  - 设定编号（S001...）
  - 设定标题
  - 段落编号
  - 关联事件ID
  - 时间位置（BF/BT/AF）
  - 核心知识点
  - 累积知识库

**Prompt**: `novel_annotation_pass2`

#### Pass 3: 功能性标签标注（可选）

**输入**:
- 分段结果（所有段落）
- Pass 1 的事件列表（供参考）

**输出**:
- 功能性标签列表（Markdown格式）
- 每个段落包含：
  - 叙事功能（故事推进、核心设定、关键道具等）
  - 叙事结构（钩子、伏笔、重复强调等）
  - 角色关系（人物登场、对立关系等）
  - 浓缩优先级（P0-骨架 / P1-血肉 / P2-皮肤）
  - 优先级理由
  - 情绪基调、首次信息、重复次数
  - 浓缩建议

**Prompt**: `novel_annotation_pass3_functional_tags`

**设计依据**: 基于 `archive/docs/NOVEL_SEGMENTATION_METHODOLOGY.md` 的标签体系，为改编浓缩提供决策依据。

### 解析流程

1. **解析 Pass 1 输出（事件）**
   - 匹配事件头部：`## 事件1：[摘要]`
   - 匹配字段：
     - `**类型**：B类/C类`
     - `**包含段落**：[1, 2, 3]`
     - `**地点**：[地点]`
     - `**地点变化**：[变化]`
     - `**时间**：[时间]`
     - `**时间变化**：[变化]`

2. **构建 EventEntry**
   - 生成事件ID（格式：章节4位+序号5位+类型1位）
   - 从分段结果中获取段落内容

3. **解析 Pass 2 输出（设定）**
   - 匹配设定头部：`## 设定1：[标题]`
   - 匹配字段：
     - `**段落**：[编号]`
     - `**设定编号**：S001`
     - `**关联事件**：事件1 ([事件ID])`
     - `**时间位置**：BF/BT/AF`
     - `**获得时间点**：BF_000100001B`
     - `**核心知识点**：[知识点]`

4. **构建 SettingEntry**
   - 验证并修正事件ID格式
   - 构建获得时间点（time_position + event_id）
   - 累积知识库（设定ID列表）

### 性能特征

- **Token消耗**：
  - Pass 1: 约 2K-4K input + 2K-3K output
  - Pass 2: 约 1K-2K input + 2K-3K output
  - Pass 3: 约 3K-5K input + 4K-6K output
- **处理时间**：
  - Pass 1+2: 约 30秒/章节
  - Pass 3: 约 50秒/章节（可选）
  - 总计: 约 80秒/章节（启用Pass 3时）
- **准确度**：依赖于分段质量和LLM能力

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_novel.py`

- `ParagraphSegmentationResult` - 分段结果
- `EventEntry` - 事件条目
- `EventTimeline` - 事件时间线
- `SettingEntry` - 设定条目
- `SettingLibrary` - 设定知识库
- `ParagraphFunctionalTags` - 段落功能性标签
- `FunctionalTagsLibrary` - 功能性标签库
- `AnnotatedChapter` - 标注结果

### Tool 依赖

**前置工具**:
- `NovelSegmenter` - 提供分段结果

**后续工具**:
- `NovelSystemDetector` - 使用标注结果检测新元素
- `NovelSystemTracker` - 使用事件列表追踪系统变化

### Prompt 依赖

**Prompt 文件**:
- `src/prompts/novel_annotation_pass1.yaml` - Pass 1 提示词
- `src/prompts/novel_annotation_pass2.yaml` - Pass 2 提示词
- `src/prompts/novel_annotation_pass3_functional_tags.yaml` - Pass 3 提示词

**配置项**:
- `system` - 系统提示词
- `user_template` - 用户提示词模板

### LLM 依赖

**Provider**: Claude (默认)
**Model**: 由 `get_model_name(provider)` 决定
**Configuration**: 通过 `src/core/llm_client_manager` 管理

## 代码示例 (Usage Example)

```python
from src.tools.novel_annotator import NovelAnnotator
from src.core.schemas_novel import ParagraphSegmentationResult

# 初始化工具
annotator = NovelAnnotator(provider="claude")

# 准备输入
segmentation_result = ParagraphSegmentationResult(...)  # 来自 NovelSegmenter

# 执行标注
annotated_chapter = annotator.execute(
    segmentation_result=segmentation_result
)

# 访问事件时间线
print(f"事件总数：{annotated_chapter.event_timeline.total_events}")
for event in annotated_chapter.event_timeline.events:
    print(f"事件 {event.event_id}：{event.event_summary}")
    print(f"  类型：{event.event_type}")
    print(f"  地点：{event.location}")
    print(f"  包含段落：{event.paragraph_indices}")

# 访问设定知识库
print(f"设定总数：{annotated_chapter.setting_library.total_settings}")
for setting in annotated_chapter.setting_library.settings:
    print(f"设定 {setting.setting_id}：{setting.setting_title}")
    print(f"  时间位置：{setting.time_position}")
    print(f"  关联事件：{setting.related_event_id}")
    print(f"  累积知识：{len(setting.accumulated_knowledge)} 个设定")

# 访问功能性标签库（如果启用）
if annotated_chapter.functional_tags:
    print(f"功能性标签总数：{annotated_chapter.functional_tags.total_paragraphs}")
    print(f"优先级分布：{annotated_chapter.functional_tags.priority_distribution}")
    
    for tags in annotated_chapter.functional_tags.paragraph_tags:
        print(f"段落 {tags.paragraph_index}：{tags.priority}")
        print(f"  理由：{tags.priority_reason}")
        print(f"  叙事功能：{tags.narrative_functions}")
        print(f"  浓缩建议：{tags.condensation_advice}")
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
{
  "chapter_number": 1,
  "event_timeline": {
    "chapter_number": 1,
    "total_events": 3,
    "events": [
      {
        "event_id": "000100001B",
        "event_summary": "陈野从江城逃出来，和一众幸存者组成车队",
        "event_type": "B",
        "paragraph_indices": [2, 3, 4],
        "paragraph_contents": [...],
        "location": "江城 → 公路",
        "location_change": "从江城转移到公路",
        "time": "末日后第3天",
        "time_change": "持续1天"
      }
    ],
    "metadata": {
      "type_distribution": {"B": 2, "C": 1},
      "processing_time": 7.5
    }
  },
  "setting_library": {
    "chapter_number": 1,
    "total_settings": 2,
    "settings": [
      {
        "setting_id": "S001",
        "setting_title": "全球诡异爆发",
        "setting_summary": "全球爆发未知诡异现象...",
        "paragraph_index": 1,
        "paragraph_content": "...",
        "acquisition_time": "BF_000100001B",
        "related_event_id": "000100001B",
        "time_position": "BF",
        "accumulated_knowledge": ["S001"]
      }
    ],
    "metadata": {
      "position_distribution": {"BF": 1, "BT": 0, "AF": 1},
      "processing_time": 8.2
    }
  },
  "functional_tags": {
    "chapter_number": 1,
    "total_paragraphs": 11,
    "paragraph_tags": [
      {
        "paragraph_index": 1,
        "narrative_functions": ["故事推进", "核心故事设定（首次）"],
        "narrative_structures": ["钩子-悬念制造", "伏笔（明确）"],
        "character_tags": [],
        "priority": "P0-骨架",
        "priority_reason": "首次揭示世界观核心设定",
        "emotional_tone": "绝望",
        "is_first_occurrence": true,
        "repetition_count": 3,
        "condensation_advice": "保留：核心设定。删除：细节描写"
      }
    ],
    "priority_distribution": {
      "P0-骨架": 5,
      "P1-血肉": 4,
      "P2-皮肤": 2
    },
    "first_occurrence_count": 7,
    "metadata": {
      "processing_time": 50.9
    }
  },
  "metadata": {
    "total_processing_time": 78.56,
    "model_used": "claude-sonnet-4.5",
    "provider": "claude"
  }
}
```

## 错误处理 (Error Handling)

### 常见错误

1. **事件ID格式错误**
   - 自动重新构建标准格式
   - 记录警告日志

2. **段落编号不存在**
   - 跳过该段落
   - 记录警告日志

3. **时间位置缺失**
   - 使用默认值 `BF`
   - 记录警告日志

### 日志级别

- `INFO`: 处理进度、统计信息
- `WARNING`: 格式修正、缺失字段
- `DEBUG`: 详细的解析过程

## 性能优化 (Performance)

### Three-Pass 优势

1. **任务分解**：将复杂任务拆分为三个独立任务
2. **质量提升**：Pass 2 可以校验 Pass 1，Pass 3 可以参考 Pass 1 结果
3. **Context管理**：每个Pass的输入控制在合理范围
4. **灵活性**：Pass 3 可选，不影响 Pass 1+2 的基础功能

### Token 优化

- Pass 1: 只处理事件聚合，不涉及设定
- Pass 2: 只处理设定关联，复用 Pass 1 结果
- Pass 3: 只处理功能性标签，参考 Pass 1 的事件摘要

## 注意事项 (Notes)

### 时间位置说明

- **BF (Before)**：事件发生前获得的设定
- **BT (Between)**：事件进行中获得的设定
- **AF (After)**：事件发生后获得的设定

### 事件ID格式

- **格式**：`CCCCCEEEEET`
  - C: 章节号（4位）
  - E: 事件序号（5位）
  - T: 事件类型（1位，B或C）
- **示例**：`000100001B` = 第1章第1个B类事件

### 获得时间点格式

- **格式**：`{time_position}_{event_id}`
- **示例**：`BF_000100001B` = 事件000100001B发生前

### 功能性标签说明

#### 浓缩优先级

- **P0-骨架**：主线情节，删除后故事无法理解（占比应为20-30%）
- **P1-血肉**：重要设定或细节，删除会损失信息但主线仍可理解（占比40-50%）
- **P2-皮肤**：氛围渲染、情感细节，浓缩时可删（占比20-30%）

#### 首次信息

- 标记为 `true` 的段落包含首次出现的重要信息（设定、道具、人物）
- 首次信息必须保留，重复信息可以压缩

#### 重复强调

- 记录段落内重要信息的重复次数（如："不要掉队！不要掉队！不要掉队！" = 3次）
- 重复强调是刻意的叙事手法，浓缩时应保留1-2次

#### 浓缩建议

- 明确指出哪些内容必须保留、哪些可以删除
- 直接用于指导改编剧本的创作

---

**最后更新**: 2026-02-10
**实现状态**: ✅ 已完成并测试（Three-Pass）
