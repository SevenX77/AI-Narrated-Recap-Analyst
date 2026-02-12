# NovelTagger

## 职责 (Responsibility)

**单一职责**: 分析Novel章节的叙事特征，提供标准化的叙事标签（视角、节奏、基调、主题等）。

NovelTagger与NovelAnnotator互补：
- **NovelAnnotator**: 事实性标注（时间线、人物、地点、设定）
- **NovelTagger**: 叙事特征（视角、节奏、基调、主题）

---

## 接口 (Interface)

### 输入 (Input)

```python
def execute(
    segmentation_results: List[ParagraphSegmentationResult],  # 章节分段结果
    project_name: str,                                        # 项目名称
    preview_length: int = 1000                                # 章节预览长度（字符）
) -> NovelTaggingResult
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `segmentation_results` | `List[ParagraphSegmentationResult]` | ✅ | 章节分段结果列表 |
| `project_name` | `str` | ✅ | 项目名称 |
| `preview_length` | `int` | ❌ | 每章分析的字符数，默认1000字 |

### 输出 (Output)

```python
class NovelTaggingResult(BaseModel):
    project_name: str                   # 项目名称
    total_chapters: int                 # 总章节数
    chapter_tags: List[ChapterTags]     # 各章节标签
    overall_perspective: str            # 整体叙事视角
    dominant_tone: str                  # 主导基调
    common_themes: List[str]            # 常见主题（前5个）
    processing_time: float              # 处理时长（秒）
```

**ChapterTags结构**:
```python
class ChapterTags(BaseModel):
    chapter_number: int                      # 章节号
    narrative_perspective: str               # 叙事视角
    time_structure: str                      # 时间结构
    pacing: str                              # 节奏
    tone: str                                # 基调
    key_themes: List[str]                    # 关键主题
    genre_tags: List[str]                    # 类型标签
    narrative_techniques: List[str]          # 叙事技巧
    confidence: float                        # 置信度 (0.0-1.0)
```

**示例输出**:
```python
NovelTaggingResult(
    project_name="末哥超凡公路",
    total_chapters=10,
    overall_perspective="第三人称限制",
    dominant_tone="紧张",
    common_themes=["生存", "末世", "系统", "升级", "团队"],
    processing_time=25.8,
    
    chapter_tags=[
        ChapterTags(
            chapter_number=1,
            narrative_perspective="第三人称限制",
            time_structure="线性",
            pacing="快速",
            tone="紧张",
            key_themes=["末世", "逃亡", "系统"],
            genre_tags=["末世", "系统流"],
            narrative_techniques=["环境描写", "心理描写"],
            confidence=0.9
        ),
        ...
    ]
)
```

---

## 实现逻辑 (Implementation)

### 处理流程

```
章节分段结果 → 构建章节预览 → LLM提取特征 → 章节标签
                                                     ↓
                多章节标签 → 统计汇总 → 整体特征（视角/基调/主题）
```

### 1. 构建章节预览

从分段结果中提取前N个字符（默认1000字）：
- 按段落顺序拼接
- 达到长度限制后截断
- 添加"..."标记

### 2. LLM提取叙事特征

**模型**: DeepSeek v3.2 或 Claude  
**温度**: 0.1（需要稳定分类）  
**输出格式**: JSON

**提取的特征**:

#### (1) 叙事视角 (narrative_perspective)

| 类型 | 说明 | 示例 |
|-----|------|------|
| 第一人称 | "我"视角 | "我看到..." |
| 第三人称全知 | 可知所有人想法 | "他想到...她感到..." |
| 第三人称限制 | 只知主角想法 | "陈野想到..." |
| 第二人称 | "你"视角（罕见） | "你感到..." |

#### (2) 时间结构 (time_structure)

| 类型 | 说明 |
|-----|------|
| 线性 | 按时间顺序叙述 |
| 倒叙 | 从结局开始回溯 |
| 插叙 | 中间插入回忆 |
| 非线性 | 时间线跳跃 |

#### (3) 节奏 (pacing)

| 类型 | 说明 |
|-----|------|
| 缓慢 | 细致描写，节奏慢 |
| 中速 | 平衡叙述和动作 |
| 快速 | 快节奏，多动作 |
| 变化 | 节奏有变化 |

#### (4) 基调 (tone)

| 类型 | 说明 |
|-----|------|
| 紧张 | 压迫感、危机感 |
| 轻松 | 幽默、愉快 |
| 悲伤 | 沉重、忧郁 |
| 中性 | 平淡叙述 |
| 神秘 | 悬疑、未知 |

#### (5) 关键主题 (key_themes)

识别章节的核心主题，如：
- "生存"、"末世"、"系统"
- "友情"、"背叛"、"成长"
- "权力"、"复仇"、"救赎"

#### (6) 类型标签 (genre_tags)

小说类型特征，如：
- "末世"、"系统流"、"升级流"
- "修仙"、"玄幻"、"都市"
- "科幻"、"悬疑"、"爱情"

#### (7) 叙事技巧 (narrative_techniques)

使用的叙事手法，如：
- "环境描写"、"心理描写"
- "对话推进"、"动作描写"
- "铺垫"、"伏笔"、"悬念"

### 3. 汇总整体特征

**整体视角**: 统计最常见的叙事视角

**主导基调**: 统计最常见的基调

**常见主题**: 统计所有章节的主题，取前5个

---

## 依赖关系 (Dependencies)

### Schema

- **输入Schema**:
  - `ParagraphSegmentationResult` - 章节分段结果

- **输出Schema**:
  - `NovelTaggingResult` - 标注结果
  - `ChapterTags` - 章节标签

### Tools

- **前置工具**: `NovelSegmenter`
  - 必须先完成分段，才能提取叙事特征

- **互补工具**: `NovelAnnotator`
  - NovelTagger提供叙事特征
  - NovelAnnotator提供事实性标注

### 外部依赖

- **Prompt**: `src/prompts/novel_tagging.yaml`
- **LLM**: DeepSeek v3.2 或 Claude Sonnet
- **LLM调用次数**: N次（每章1次）

---

## 数据模型 (Data Models)

### ChapterTags

详见"接口-输出"部分。

### NovelTaggingResult

详见"接口-输出"部分。

---

## 使用示例 (Usage Example)

### 基本使用

```python
from src.tools.novel_tagger import NovelTagger

# 1. 假设已有分段结果
segmentation_results = [...]  # List[ParagraphSegmentationResult]

# 2. 标注叙事特征
tagger = NovelTagger(provider="deepseek")
tagging_result = tagger.execute(
    segmentation_results=segmentation_results,
    project_name="末哥超凡公路",
    preview_length=1000
)

# 3. 查看整体特征
print(f"整体视角: {tagging_result.overall_perspective}")
print(f"主导基调: {tagging_result.dominant_tone}")
print(f"常见主题: {', '.join(tagging_result.common_themes)}")

# 4. 查看各章节特征
for tags in tagging_result.chapter_tags:
    print(f"\n章节{tags.chapter_number}:")
    print(f"  视角: {tags.narrative_perspective}")
    print(f"  节奏: {tags.pacing}")
    print(f"  基调: {tags.tone}")
    print(f"  主题: {', '.join(tags.key_themes)}")
```

### 在Workflow中使用

```python
# NovelProcessingWorkflow中的可选步骤
if workflow_config.enable_tagging:
    tagging_result = self.novel_tagger.execute(
        segmentation_results=list(segmentation_results.values()),
        project_name=project_name
    )
    
    # 保存结果
    self._save_tagging_result(tagging_result)
    
    # 用于后续分析
    # 例如：根据基调选择配音风格
    if tagging_result.dominant_tone == "紧张":
        audio_config.pace = "fast"
        audio_config.intensity = "high"
```

---

## 标注标准 (Tagging Standards)

### 叙事视角判断

```python
# 第一人称示例
"我看到远处有一个人影..."

# 第三人称全知示例
"陈野想到逃跑的路线，而李明则担心着家人..."

# 第三人称限制示例
"陈野想到逃跑的路线。他不知道李明在想什么..."
```

### 节奏判断

| 指标 | 缓慢 | 中速 | 快速 |
|-----|------|------|------|
| 描写占比 | >50% | 30-50% | <30% |
| 动作密度 | 低 | 中 | 高 |
| 对话量 | 少 | 中 | 多 |

### 主题识别

主题应该是**抽象概念**，而非具体事件：
- ✅ "生存"、"成长"、"友情"
- ❌ "击杀丧尸"、"获得系统"（这是事件）

---

## 性能指标 (Performance)

- **LLM调用**: N次（N=章节数）
- **执行时间**: 2-4秒/章
- **预览长度**: 1000字/章（可配置）
- **准确率**: ~75%（叙事特征主观性较强）

---

## 注意事项 (Notes)

1. **预览长度**: 
   - 默认1000字，可根据章节长度调整
   - 过短(<500字)可能提取不准确
   - 过长(>2000字)增加LLM成本但提升有限

2. **主观性**: 
   - 叙事特征本身具有主观性
   - LLM判断可能与人工标注有差异
   - 建议作为辅助参考，不作为绝对标准

3. **置信度**: 
   - 每个章节标签都有置信度字段
   - 低置信度(<0.7)建议人工review

4. **批量处理**: 
   - 当前版本按章节串行处理
   - 如需加速，可改为并行调用LLM

5. **可选功能**: 
   - NovelTagger是可选工具
   - 如不需要叙事特征分析，可跳过

---

## 常见问题 (FAQ)

### Q1: 如何提高标注准确性？

**方法**:
1. 使用Claude模型（理解能力更强）
2. 增加 `preview_length` 到1500-2000字
3. 调整Prompt，增加示例
4. 人工review低置信度结果

### Q2: 叙事特征有什么实际用途？

**用途**:
1. **配音选择**: 根据基调选择配音风格
2. **配乐选择**: 根据节奏和基调选择BGM
3. **剪辑策略**: 快节奏章节可快速剪辑
4. **内容分类**: 按主题/类型组织内容
5. **质量分析**: 分析叙事一致性

### Q3: 为什么叙事视角全是"第三人称限制"？

**原因**: 
- 多数网络小说采用第三人称限制视角
- 如果所有章节视角一致，这是正常的
- 如果明显是第一人称却判断错误，需要检查Prompt

---

## 相关文档 (Related Docs)

- [NovelAnnotator](./novel_annotator.md) - 事实性标注工具（互补）
- [NovelSegmenter](./novel_segmenter.md) - 分段工具（前置）
- [NovelProcessingWorkflow](../workflows/novel_processing_workflow.md) - 完整流程

---

**最后更新**: 2026-02-10  
**维护者**: AI Assistant
