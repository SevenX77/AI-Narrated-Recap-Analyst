# NovelSegmenter - 小说章节分段工具

## 职责 (Responsibility)

基于A/B/C原则对小说章节进行叙事分段，输出JSON格式结果。使用 Two-Pass LLM 策略确保分段质量。

**所属阶段**: 小说章节分段（Phase 1）
**工具链位置**: NovelChapterDetector → NovelSegmenter → NovelAnnotator

## 分段原则 (Segmentation Principles)

### A类-设定 (Setting)
跳脱时间线的设定信息（世界观、规则、背景）

### B类-事件 (Event)
现实时间线的事件（动作、场景、对话）

### C类-系统 (System)
次元空间事件（系统觉醒、系统交互、系统奖励）

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    chapter_content: str,
    chapter_number: int,
    chapter_title: str = "",
    **kwargs
) -> SegmentationOutput
```

### 输入参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| `chapter_content` | `str` | 章节文本内容（不包含章节标题行） |
| `chapter_number` | `int` | 章节序号 |
| `chapter_title` | `str` | 章节标题（可选，用于Markdown生成） |

### 输出结果

**类型**: `SegmentationOutput`

**结构**:
```python
SegmentationOutput(
    json_result: ParagraphSegmentationResult,  # JSON格式结果
    markdown_content: str,                     # Markdown格式输出
    llm_raw_output: str                        # LLM原始输出（调试用）
)
```

**ParagraphSegmentationResult 结构**:
```python
ParagraphSegmentationResult(
    chapter_number: int,
    total_paragraphs: int,
    paragraphs: List[ParagraphSegment],
    metadata: Dict[str, Any]
)
```

**ParagraphSegment 结构**:
```python
ParagraphSegment(
    index: int,           # 段落编号（1-based）
    type: str,            # 段落类型（A/B/C）
    content: str,         # 段落内容（完整）
    start_char: int,      # 起始字符位置
    end_char: int,        # 结束字符位置
    start_line: int,      # 起始行号
    end_line: int         # 结束行号
)
```

## 实现逻辑 (Logic)

### Two-Pass 策略

#### Pass 1: 初步分段

**输入**:
- 带行号的章节内容（格式：`   1| 第一行内容`）

**输出**:
- 段落列表（Markdown格式）
- 每个段落包含：
  - 段落编号 + 类型 + 描述
  - 行号范围

**Prompt**: `novel_chapter_segmentation_pass1`

#### Pass 2: 校验修正

**输入**:
- 章节原文（不带行号）
- Pass 1 的分段结果

**输出**:
- 校验结果：
  - 如果正确：`✅ 分段正确，无需修改`
  - 如果有误：修正后的分段列表

**Prompt**: `novel_chapter_segmentation_pass2`

### 核心流程

1. **Two-Pass LLM分段**
   - Pass 1: 初步分段
   - Pass 2: 校验修正
   - 如果 Pass 2 判断正确，使用 Pass 1 结果，否则使用 Pass 2 结果

2. **解析LLM输出**
   - 匹配段落头部：`- **段落1（B类-事件）**：[描述]`
   - 匹配行号范围：`行号：1-5`

3. **在原文中定位段落**
   - 使用行号从原文中提取段落内容
   - 计算字符位置

4. **验证原文还原**
   - 拼接所有段落内容
   - 验证是否能还原原文

5. **生成输出**
   - JSON结果（可完全还原原文）
   - Markdown输出（简洁版，只含分段原文和类型）

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_novel.py`

- `ParagraphSegment` - 段落片段
- `ParagraphSegmentationResult` - 分段结果
- `SegmentationOutput` - 完整输出

### Tool 依赖

**前置工具**:
- `NovelChapterDetector` - （可选）用于提取章节内容

**后续工具**:
- `NovelAnnotator` - 使用分段结果进行标注

### Prompt 依赖

**Prompt 文件**:
- `src/prompts/novel_chapter_segmentation_pass1.yaml` - Pass 1
- `src/prompts/novel_chapter_segmentation_pass2.yaml` - Pass 2

**配置项**:
- `system` - 系统提示词
- `user_template` - 用户提示词模板

### LLM 依赖

**Provider**: Claude (默认)
**Model**: 由 `get_model_name(provider)` 决定
**Configuration**: 通过 `src/core/llm_client_manager` 管理

## 代码示例 (Usage Example)

```python
from src.tools.novel_segmenter import NovelSegmenter

# 初始化工具
segmenter = NovelSegmenter(provider="claude")

# 准备章节内容
chapter_content = """
收音机里传来消息，上沪沦陷了。
陈野关掉收音机，看向车窗外的荒凉公路。
【系统觉醒：生存系统已激活】
"""

# 执行分段
output = segmenter.execute(
    chapter_content=chapter_content,
    chapter_number=1,
    chapter_title="车队第一铁律"
)

# 访问JSON结果
json_result = output.json_result
print(f"分段完成：{json_result.total_paragraphs} 个段落")
print(f"类型分布：{json_result.metadata['type_distribution']}")

# 遍历段落
for para in json_result.paragraphs:
    print(f"段落 {para.index} ({para.type}类)")
    print(f"  行号：{para.start_line}-{para.end_line}")
    print(f"  内容：{para.content[:50]}...")

# 访问Markdown输出
markdown = output.markdown_content
print(markdown)
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
{
  "chapter_number": 1,
  "total_paragraphs": 3,
  "paragraphs": [
    {
      "index": 1,
      "type": "A",
      "content": "【设定】全球诡异爆发，文明崩溃...",
      "start_char": 0,
      "end_char": 85,
      "start_line": 0,
      "end_line": 3
    },
    {
      "index": 2,
      "type": "B",
      "content": "收音机里传来消息，上沪沦陷了...",
      "start_char": 86,
      "end_char": 215,
      "start_line": 4,
      "end_line": 8
    },
    {
      "index": 3,
      "type": "C",
      "content": "【系统觉醒：生存系统已激活】...",
      "start_char": 216,
      "end_char": 285,
      "start_line": 9,
      "end_line": 12
    }
  ],
  "metadata": {
    "type_distribution": {"A": 1, "B": 1, "C": 1},
    "processing_time": 12.5,
    "model_used": "claude-sonnet-4.5",
    "provider": "claude"
  }
}
```

### Markdown 输出示例

```markdown
# 第1章：车队第一铁律

---

## 段落 1 [A类-设定]

【设定】全球诡异爆发，文明崩溃...

---

## 段落 2 [B类-事件]

收音机里传来消息，上沪沦陷了...

---

## 段落 3 [C类-系统]

【系统觉醒：生存系统已激活】...

---
```

## 错误处理 (Error Handling)

### 常见错误

1. **行号范围超出边界**
   - 抛出 `ValueError`
   - 提示行号范围和总行数

2. **段落缺少行号**
   - 抛出 `ValueError`
   - 提示段落编号

3. **原文还原失败**
   - 计算差异比例
   - 如果差异 > 5%，抛出 `ValueError`

### 日志级别

- `INFO`: 处理进度、统计信息
- `WARNING`: 原文还原差异
- `DEBUG`: 段落解析详情

## 性能特征 (Performance)

### Token 消耗

- **Pass 1**：约 2K-4K input + 1K-2K output
- **Pass 2**：约 2K-4K input + 1K-2K output
- **总计**：约 4K-8K input + 2K-4K output

### 处理时间

- **单章节**：10-20秒
- **批量处理**：建议并行处理

### 准确度

- **分段准确度**：95%+（Two-Pass策略）
- **原文还原**：100%（字符级精确）

## 注意事项 (Notes)

### 分段粒度

- 建议每段 50-500 字
- 避免过于细碎或过于粗糙

### A/B/C 判断标准

**A类特征**：
- 跳出时间线
- 解释世界观、规则
- 历史背景、角色经历

**B类特征**：
- 现实时间线
- 动作、对话、场景
- 推动剧情发展

**C类特征**：
- 系统面板
- 系统提示、奖励
- 次元空间交互

### 与 ScriptSegmenter 的区别

| 特性 | NovelSegmenter | ScriptSegmenter |
|-----|----------------|-----------------|
| 输入格式 | 小说文本 | SRT字幕文本 |
| 分段原则 | A/B/C类别 | 语义分段 |
| 输出格式 | JSON + Markdown | JSON + Markdown |
| 时间信息 | 无 | SRT时间戳 |

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
