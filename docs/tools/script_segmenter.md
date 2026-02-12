# ScriptSegmenter - 脚本分段工具

## 职责 (Responsibility)

使用 Two-Pass LLM 将连续脚本文本按叙事逻辑进行语义分段，并匹配对应的SRT时间范围，输出JSON格式结果。

**所属阶段**: 脚本分段（Phase 1）
**工具链位置**: SrtTextExtractor → ScriptSegmenter → 脚本分析

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    processed_text: str,
    srt_entries: List[SrtEntry],
    project_name: str,
    episode_name: str
) -> ScriptSegmentationResult
```

### 输入参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| `processed_text` | `str` | 连续的脚本文本（从 SrtTextExtractor 输出） |
| `srt_entries` | `List[SrtEntry]` | SRT条目列表（用于匹配时间戳） |
| `project_name` | `str` | 项目名称 |
| `episode_name` | `str` | 集数名称 |

### 输出结果

**类型**: `ScriptSegmentationResult`

**结构**:
```python
ScriptSegmentationResult(
    segments: List[ScriptSegment],      # 分段列表
    total_segments: int,                 # 分段总数
    avg_sentence_count: float,           # 平均句子数
    segmentation_mode: str,              # 分段模式（"two_pass"）
    output_file: str,                    # Markdown输出文件路径
    processing_time: float               # 处理时间（秒）
)
```

**ScriptSegment 结构**:
```python
ScriptSegment(
    index: int,           # 段落编号（1-based）
    content: str,         # 段落内容
    start_time: str,      # 起始时间（SRT格式：HH:MM:SS,mmm）
    end_time: str,        # 结束时间（SRT格式）
    sentence_count: int,  # 句子数量
    char_count: int       # 字符数量
)
```

## 实现逻辑 (Logic)

### 分段原则

- **场景转换**：当故事场景、时间、地点发生明显变化时分段
- **情节转折**：当故事出现新的事件、冲突或转折时分段
- **对话切换**：当不同角色的对话结束，进入新的叙述时分段
- **因果关系**：保持因果关系紧密的句子在同一段

### Two-Pass 策略

#### Pass 1: 初步分段

**输入**:
- 带句子序号的脚本内容（格式：`   1. 第一句话。`）

**输出**:
- 段落列表（Markdown格式）
- 每个段落包含：
  - 段落编号 + 描述
  - 句子序号范围

**Prompt**: `script_segmentation_pass1`

#### Pass 2: 校验修正

**输入**:
- 带句子序号的脚本内容
- Pass 1 的分段结果

**输出**:
- 校验结果：
  - 如果正确：`✅ 分段正确，无需修改`
  - 如果有误：修正后的分段列表

**Prompt**: `script_segmentation_pass2`

### 核心流程

1. **Two-Pass LLM分段**
   - 将脚本按句子拆分（按 `。！？` 分割）
   - 添加句子序号
   - Pass 1: 初步分段
   - Pass 2: 校验修正

2. **解析LLM输出**
   - 匹配段落头部：`- **段落1**：[描述]`
   - 匹配句号范围：`句号：1-3`

3. **提取段落内容**
   - 根据句子序号从原文中提取段落内容
   - 计算字符位置

4. **匹配时间戳**
   - 根据字符位置比例映射到SRT条目
   - 获取起始和结束时间

5. **生成输出**
   - JSON结果
   - Markdown文件（保存到 `data/projects/{project_name}/script/{episode_name}.md`）

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_script.py`

- `SrtEntry` - SRT条目
- `ScriptSegment` - 脚本段落
- `ScriptSegmentationResult` - 分段结果

### Tool 依赖

**前置工具**:
- `SrtTextExtractor` - 提供处理后的脚本文本

**后续工具**:
- 脚本语义分析工具（待开发）

### Prompt 依赖

**Prompt 文件**:
- `src/prompts/script_segmentation_pass1.yaml` - Pass 1
- `src/prompts/script_segmentation_pass2.yaml` - Pass 2

**配置项**:
- `system` - 系统提示词
- `user_template` - 用户提示词模板

### LLM 依赖

**Provider**: DeepSeek (默认)
**Model**: 由 `get_model_name(provider)` 决定
**Configuration**: 通过 `src/core/llm_client_manager` 管理

## 代码示例 (Usage Example)

```python
from src.tools.script_segmenter import ScriptSegmenter
from src.core.schemas_script import SrtEntry

# 初始化工具
segmenter = ScriptSegmenter(provider="deepseek")

# 准备输入
processed_text = "收音机里传来消息，上沪沦陷了。陈野关掉收音机..."
srt_entries = [
    SrtEntry(index=1, start_time="00:00:01,000", end_time="00:00:03,500", text="..."),
    ...
]

# 执行分段
result = segmenter.execute(
    processed_text=processed_text,
    srt_entries=srt_entries,
    project_name="末哥超凡公路",
    episode_name="ep01"
)

# 访问结果
print(f"分段完成：{result.total_segments} 个段落")
print(f"平均句子数：{result.avg_sentence_count:.1f}")
print(f"输出文件：{result.output_file}")

# 遍历段落
for seg in result.segments:
    print(f"段落 {seg.index} [{seg.start_time} - {seg.end_time}]")
    print(f"  句子数：{seg.sentence_count}")
    print(f"  内容：{seg.content[:50]}...")
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
{
  "segments": [
    {
      "index": 1,
      "content": "收音机里传来消息，上沪沦陷了。陈野关掉收音机，看向车窗外的荒凉公路。",
      "start_time": "00:00:01,000",
      "end_time": "00:00:05,500",
      "sentence_count": 2,
      "char_count": 42
    },
    {
      "index": 2,
      "content": "车队停在公路旁的休息区。陈野下车，检查车辆状况。",
      "start_time": "00:00:05,500",
      "end_time": "00:00:10,000",
      "sentence_count": 2,
      "char_count": 28
    }
  ],
  "total_segments": 2,
  "avg_sentence_count": 2.0,
  "segmentation_mode": "two_pass",
  "output_file": "data/projects/末哥超凡公路/script/ep01.md",
  "processing_time": 8.5
}
```

### Markdown 输出示例

```markdown
# ep01

## [00:00:01,000 - 00:00:05,500]

收音机里传来消息，上沪沦陷了。陈野关掉收音机，看向车窗外的荒凉公路。

## [00:00:05,500 - 00:00:10,000]

车队停在公路旁的休息区。陈野下车，检查车辆状况。
```

## 错误处理 (Error Handling)

### 常见错误

1. **句子序号超出范围**
   - 抛出 `ValueError`
   - 提示句子范围和总句数

2. **段落缺少句号**
   - 抛出 `ValueError`
   - 提示段落编号

3. **时间戳匹配失败**
   - 使用边界检查
   - 记录警告日志

### 日志级别

- `INFO`: 处理进度、统计信息
- `WARNING`: 时间戳匹配异常
- `DEBUG`: 段落解析详情

## 性能特征 (Performance)

### Token 消耗

- **Pass 1**：约 2K-4K input + 1K-2K output
- **Pass 2**：约 2K-4K input + 1K-2K output
- **总计**：约 4K-8K input + 2K-4K output

### 处理时间

- **单集**：8-15秒
- **批量处理**：建议并行处理

### 准确度

- **分段准确度**：90%+（Two-Pass策略）
- **时间戳准确度**：85%+（基于字符比例映射）

## 注意事项 (Notes)

### 分段粒度

- 建议每段 2-5 句
- 避免过于细碎（影响理解）或过于粗糙（时间跨度过大）

### 时间戳映射策略

当前使用简单的字符比例映射：
- 计算段落在全文中的字符位置比例
- 映射到SRT条目索引
- 获取对应的时间戳

**改进方向**：
- 使用更精确的内容匹配
- 考虑SRT条目的文本相似度

### 与 NovelSegmenter 的区别

| 特性 | ScriptSegmenter | NovelSegmenter |
|-----|-----------------|----------------|
| 输入格式 | SRT字幕文本 | 小说文本 |
| 分段原则 | 语义分段 | A/B/C类别 |
| 句子拆分 | 按标点符号 | 按行号 |
| 时间信息 | SRT时间戳 | 无 |
| 输出位置 | `data/projects/{project}/script/` | 内存 |

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
