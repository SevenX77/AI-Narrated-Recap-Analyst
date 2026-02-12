# NovelScriptAligner - Novel与Script对齐工具

## 职责 (Responsibility)

Novel与Script的句子级语义对齐分析工具。基于NovelAnnotator的事件/设定标注结果和ScriptSegmenter的分段结果，识别Script片段与Novel事件/设定的对应关系、改写策略、覆盖率等关键信息。

**核心价值**：
1. **改写策略分析**: 识别exact、paraphrase、summarize、expand等改写类型
2. **覆盖率统计**: 计算Novel事件/设定在Script中的覆盖率
3. **质量评估**: 提供置信度、对齐质量等指标
4. **高效处理**: 基于Annotation结构，无需读取Novel全文

## 所属Phase

**Phase II: 内容分析与对齐** - 对齐匹配工具

## 在工具链中的位置

```
NovelAnnotator (事件+设定标注)
         ↓
         ├─→ Novel事件列表
         └─→ Novel设定列表
                  ↓
ScriptSegmenter (脚本分段)
         ↓
         └─→ Script片段列表
                  ↓
         [NovelScriptAligner] ← 本工具
                  ↓
         ┌────────┴────────┐
         ↓                 ↓
   AlignmentResult    AlignmentReport
   (对齐数据)         (质量报告)
```

## 接口定义 (Interface)

### 输入 (Input)

```python
def execute(
    self,
    novel_annotation: AnnotatedChapter,      # Novel章节标注结果
    script_result: ScriptSegmentationResult, # Script分段结果
    project_name: str,                       # 项目名称
    **kwargs
) -> AlignmentResult
```

**参数说明**：
- `novel_annotation` (AnnotatedChapter): 来自NovelAnnotator的标注结果
  - 必须包含事件时间线（event_timeline）
  - 必须包含设定库（setting_library）
- `script_result` (ScriptSegmentationResult): 来自ScriptSegmenter的分段结果
  - 包含所有Script片段
  - 每个片段有时间范围和内容
- `project_name` (str): 项目名称，用于结果标识
- `**kwargs`: 其他可选参数
  - `episode_id` (str): Script集数ID（如"ep01"）

### 输出 (Output)

```python
@dataclass
class AlignmentResult:
    project_name: str                             # 项目名称
    novel_chapter_id: str                         # Novel章节ID
    script_episode_id: str                        # Script集数ID
    alignments: List[ScriptFragmentAlignment]     # 片段对齐列表
    coverage_stats: CoverageStatistics            # 覆盖率统计
    rewrite_stats: RewriteStrategyStatistics      # 改写策略统计
    total_fragments: int                          # 片段总数
    aligned_at: datetime                          # 对齐时间
    llm_provider: str                             # LLM提供商
    llm_model: str                                # LLM模型
```

**关键字段**：
- `alignments`: 每个Script片段的详细对齐信息
  - `matched_events`: 匹配的Novel事件（ID、类型、置信度、说明）
  - `matched_settings`: 匹配的Novel设定（ID、类型、置信度、说明）
  - `skipped_content`: Script跳过的Novel内容
- `coverage_stats`: 覆盖率统计
  - `event_coverage`: 事件覆盖率（0-1）
  - `setting_coverage`: 设定覆盖率（0-1）
  - `matched_event_ids`: 已匹配的事件ID列表
  - `unmatched_event_ids`: 未匹配的事件ID列表
- `rewrite_stats`: 改写策略统计
  - `exact_count`: 原文保留数量
  - `paraphrase_count`: 改写数量
  - `summarize_count`: 压缩数量
  - `expand_count`: 扩写数量
  - `dominant_strategy`: 主要改写策略

### 异常 (Exceptions)

- `ValueError`: 输入参数不完整或格式错误
- `LLMClientError`: LLM调用失败
- `ParseError`: LLM输出解析失败

## 实现逻辑 (Implementation Logic)

### 核心流程

```
Step 1: 准备Novel数据
├─ 提取事件列表文本
├─ 提取设定列表文本
└─ 格式化为LLM可读文本

Step 2: 提取Script片段
├─ 从ScriptSegmentationResult提取所有片段
├─ 构建时间范围字符串
└─ 准备片段内容

Step 3: LLM对齐分析（对每个片段）
├─ 构建Prompt（Script片段 + Novel事件/设定）
├─ 调用LLM分析对应关系
├─ 解析LLM输出
│  ├─ 匹配的事件（ID、类型、置信度、说明）
│  ├─ 匹配的设定（ID、类型、置信度、说明）
│  └─ 跳过的内容（类型、ID、原因）
└─ 构建ScriptFragmentAlignment对象

Step 4: 统计分析
├─ 计算覆盖率统计
│  ├─ 事件覆盖率
│  ├─ 设定覆盖率
│  └─ 未匹配的ID列表
├─ 计算改写策略统计
│  ├─ 各类型数量统计
│  └─ 主要改写策略
└─ 构建AlignmentResult

Step 5: 生成报告（可选）
├─ 计算质量指标
│  ├─ 平均置信度
│  ├─ 高/中/低置信度分布
│  └─ 空对齐片段数
├─ 生成改进建议
│  ├─ 覆盖率建议
│  ├─ 质量建议
│  └─ 改写策略建议
└─ 保存报告（JSON + Markdown）
```

### 关键算法

**1. 对应关系识别**

LLM根据以下标准识别对应关系类型：
- **exact**: 几乎原文，仅删减少量细节
- **paraphrase**: 改写，换了表达方式但语义相同
- **summarize**: 总结压缩，Script大幅简化了Novel内容
- **expand**: 扩写，Script增加了Novel中没有的细节
- **none**: 无明确对应关系

**2. 置信度评估**

LLM根据对应程度给出0-1的置信度：
- 0.9-1.0: 明确对应，内容高度一致
- 0.7-0.9: 较强对应，可识别相关性
- 0.5-0.7: 中等对应，部分内容相关
- <0.5: 弱对应，关联性不明确

**3. 覆盖率计算**

```python
event_coverage = matched_events / total_events
setting_coverage = matched_settings / total_settings
```

**4. 改写策略统计**

统计所有对齐结果中各类型的数量，识别主要改写策略。

### LLM输出解析

**输出格式**（结构化文本，非JSON）：

```
### 1. 匹配的Novel事件

事件ID: 000100001B | 类型: summarize | 置信度: 0.9 | 说明: Script压缩了陈野骑二八大杠的描写
事件ID: 000100002B | 类型: expand | 置信度: 0.85 | 说明: Script扩写了系统觉醒的细节

### 2. 匹配的Novel设定

设定ID: S00010001 | 类型: paraphrase | 置信度: 0.95 | 说明: Script改写了诡异无法被杀死的设定

### 3. Script跳过的内容

跳过类型: event | ID: 000100003B | 原因: Script完全省略了收音机广播的具体内容
```

**解析逻辑**：
1. 按章节标记（### 1/2/3）分割文本
2. 使用正则表达式提取每行的字段
3. 构建EventAlignment、SettingAlignment、SkippedContent对象

## 依赖关系 (Dependencies)

### Schema

- `AnnotatedChapter` (src/core/schemas_novel.py): Novel标注结果
- `ScriptSegmentationResult` (src/core/schemas_script.py): Script分段结果
- `AlignmentResult` (src/core/schemas_alignment.py): 对齐结果
- `AlignmentReport` (src/core/schemas_alignment.py): 对齐报告

### Tools

- **前置工具**:
  - `NovelAnnotator`: 提供Novel事件/设定标注
  - `ScriptSegmenter`: 提供Script分段结果

- **后续工具**:
  - 对齐结果可用于改编质量评估、改写策略学习等

### Config

- `CLAUDE_API_KEY` / `DEEPSEEK_API_KEY`: LLM API密钥
- `CLAUDE_BASE_URL` / `DEEPSEEK_BASE_URL`: LLM API地址
- `CLAUDE_MODEL_NAME` / `DEEPSEEK_MODEL_NAME`: 使用的模型

### Prompts

- `novel_script_alignment.yaml`: 对齐分析Prompt

## 代码示例 (Code Example)

### 基本使用

```python
from pathlib import Path
from src.tools.novel_annotator import NovelAnnotator
from src.tools.script_segmenter import ScriptSegmenter
from src.tools.novel_script_aligner import NovelScriptAligner

# Step 1: 准备Novel标注结果（来自NovelAnnotator）
novel_annotator = NovelAnnotator(provider="claude")
novel_annotation = novel_annotator.execute(segmentation_result)

# Step 2: 准备Script分段结果（来自ScriptSegmenter）
script_segmenter = ScriptSegmenter(provider="deepseek")
script_result = script_segmenter.execute(
    srt_sentences=srt_sentences,
    project_name="末哥超凡公路",
    episode_name="ep01"
)

# Step 3: 执行对齐分析
aligner = NovelScriptAligner(provider="claude")
alignment_result = aligner.execute(
    novel_annotation=novel_annotation,
    script_result=script_result,
    project_name="末哥超凡公路",
    episode_id="ep01"
)

# Step 4: 查看覆盖率
print(f"事件覆盖率: {alignment_result.coverage_stats.event_coverage * 100:.1f}%")
print(f"设定覆盖率: {alignment_result.coverage_stats.setting_coverage * 100:.1f}%")

# Step 5: 生成质量报告
report = aligner.generate_report(
    alignment_result,
    output_path=Path("output/alignment_report")
)

print(f"平均置信度: {report.quality_metrics.avg_confidence:.3f}")
print(f"改进建议: {len(report.recommendations)} 条")
```

### 访问详细对齐信息

```python
# 遍历所有片段的对齐结果
for alignment in alignment_result.alignments:
    print(f"\n片段 {alignment.fragment_index}")
    print(f"时间: {alignment.time_range}")
    print(f"内容: {alignment.content_preview}...")
    
    # 匹配的事件
    for event in alignment.matched_events:
        print(f"  事件: {event.event_id} ({event.match_type}, {event.confidence})")
        print(f"    → {event.explanation}")
    
    # 匹配的设定
    for setting in alignment.matched_settings:
        print(f"  设定: {setting.setting_id} ({setting.match_type}, {setting.confidence})")
        print(f"    → {setting.explanation}")
```

### 查看改写策略统计

```python
stats = alignment_result.rewrite_stats

print(f"改写策略分布:")
print(f"  原文保留: {stats.exact_count}")
print(f"  改写: {stats.paraphrase_count}")
print(f"  压缩: {stats.summarize_count}")
print(f"  扩写: {stats.expand_count}")
print(f"  无对应: {stats.none_count}")
print(f"  主要策略: {stats.dominant_strategy}")
```

## 测试验证 (Testing)

### 测试脚本

位置: `scripts/test/test_novel_script_aligner.py`

### 测试数据

- Novel: 末哥超凡公路第1章（已标注）
- Script: ep01.md（已分段）
- 预期结果: 事件覆盖率>80%，设定覆盖率>70%

### 测试用例

1. **基本对齐测试**: 验证所有片段都能成功对齐
2. **覆盖率测试**: 验证覆盖率计算正确
3. **改写策略测试**: 验证改写类型识别准确
4. **质量报告测试**: 验证报告生成完整

## 性能与成本 (Performance & Cost)

### 处理性能

- **单章对齐**: 9个Script片段，约40-60秒
- **LLM调用**: 每个片段1次（可并行优化）
- **内存占用**: 低（只处理Annotation摘要）

### 成本分析

以Claude Sonnet 4为例：
- **Input**: ~800 tokens/片段（事件+设定列表+Script内容）
- **Output**: ~300 tokens/片段（对齐结果）
- **单章成本**: ~$0.10（9个片段）
- **百章成本**: ~$10

成本节省策略：
- 使用DeepSeek v3.2标准模型可降低成本至1/10
- 批量处理时使用缓存优化

## 实验结果 (Experimental Results)

**测试日期**: 2026-02-09

**测试数据**:
- Novel: 末哥超凡公路第1章（11个段落，5个事件，3个设定）
- Script: ep01前半部分（7个片段）

**对齐结果**:
- 事件覆盖率: 100% (5/5事件全部匹配)
- 设定覆盖率: 100% (3/3设定全部匹配)
- 平均置信度: 0.94
- 主要改写策略: paraphrase（改写）

**改写策略分布**:
- exact: 2次（原文保留）
- paraphrase: 4次（改写）
- summarize: 2次（压缩）
- expand: 1次（扩写）

**关键发现**:
1. ✅ Script第一段确实对应Novel简介（不是原创）
2. ✅ 对应关系是句子级而非段落级
3. ✅ Script保留了所有核心事件和设定
4. ✅ 改写策略多样化，以paraphrase为主

## 设计决策 (Design Decisions)

### 1. 为什么基于Annotation而非Novel原文？

**优势**:
- ✅ **Context高效**: 只需事件/设定摘要（~800 tokens），不需要全文（~16000 tokens）
- ✅ **结构化**: 事件/设定有清晰的边界和分类
- ✅ **覆盖率分析**: 可直接统计事件/设定覆盖率
- ✅ **可扩展**: 支持长篇Novel的对齐

**权衡**:
- 需要先运行NovelAnnotator
- 原文细节需要时可通过paragraph_indices回查

### 2. 为什么选择句子级对齐？

根据实验验证，Novel-Script的对应关系是：
- Novel段落（或多段） → Script句子（或多句）
- 不是段落级的一对一映射

句子级对齐可以：
- 识别压缩关系（Novel多段 → Script一句）
- 识别扩写关系（Novel一段 → Script多句）
- 提供更精细的改写策略分析

### 3. 为什么输出结构化文本而非JSON？

**LLM输出JSON的问题**:
- JSON格式难以解析（括号、引号、转义字符）
- 容易出错，导致解析失败

**结构化文本的优势**:
- 简洁易解析（正则表达式）
- LLM生成更稳定
- 人工可读性强

## 后续改进 (Future Improvements)

1. **并行处理**: 支持多片段并行对齐，提升速度
2. **缓存优化**: 缓存Novel事件/设定列表，避免重复准备
3. **增量对齐**: 支持增量更新，只对齐新增的Script片段
4. **可视化**: 生成对齐关系的可视化图表
5. **反向对齐**: 识别Script中Novel没有的原创内容

## 相关文档

- [NovelAnnotator](novel_annotator.md) - 前置工具：Novel标注
- [ScriptSegmenter](script_segmenter.md) - 前置工具：Script分段
- [DEV_STANDARDS.md](../DEV_STANDARDS.md) - 开发规范
- [schemas_alignment.py](../../src/core/schemas_alignment.py) - 对齐数据模型

---

**最后更新**: 2026-02-09  
**工具状态**: ✅ 已完成并测试验证
