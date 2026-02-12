# ScriptValidator

## 职责 (Responsibility)

**单一职责**: 验证脚本处理的各个环节质量，确保数据准确性和合理性，生成质量评分和改进建议。

ScriptValidator是ScriptProcessingWorkflow的质量保障步骤，负责验证：
1. SRT时间轴连续性（间隔、重叠）
2. 文本完整性（覆盖率）
3. 分段合理性（段落数量、时长）

---

## 接口 (Interface)

### 输入 (Input)

```python
def execute(
    srt_entries: List[SrtEntry],                       # 必需，SRT条目列表
    text_extraction: SrtTextExtractionResult = None,   # 可选，文本提取结果
    segmentation: ScriptSegmentationResult = None,     # 可选，分段结果
    episode_name: str = "ep01"                         # 集数名称
) -> ScriptValidationReport
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `srt_entries` | `List[SrtEntry]` | ✅ | SRT条目列表，由SrtImporter导入 |
| `text_extraction` | `SrtTextExtractionResult` | ❌ | 文本提取结果，由SrtTextExtractor生成 |
| `segmentation` | `ScriptSegmentationResult` | ❌ | 分段结果，由ScriptSegmenter生成 |
| `episode_name` | `str` | ❌ | 集数名称，默认"ep01" |

### 输出 (Output)

```python
class ScriptValidationReport(BaseModel):
    episode_name: str                  # 集数名称
    validation_time: datetime          # 验证时间
    quality_score: float               # 总体质量评分 (0-100)
    is_valid: bool                     # 是否通过验证 (>=70分)
    
    # 检查结果
    timeline_check: Dict[str, Any]     # 时间轴检查结果
    text_check: Dict[str, Any]         # 文本完整性检查结果
    segmentation_check: Dict[str, Any] # 分段合理性检查结果
    
    # 问题与建议
    issues: List[ScriptValidationIssue]  # 发现的问题列表
    warnings: List[str]                   # 警告列表
    recommendations: List[str]            # 改进建议列表
    
    # 统计信息
    statistics: Dict[str, Any]           # 统计信息
```

**质量评分标准**:
- **≥90分**: 优秀，无明显问题
- **70-89分**: 良好，有轻微问题但可接受
- **<70分**: 不合格，需要检查原始文件

---

## 实现逻辑 (Implementation)

### 1. 时间轴连续性检查 (`_check_timeline`)

**目的**: 检测SRT字幕时间轴是否连续

**检查项**:

#### (1) 时间间隔 (Gaps)
- **定义**: 前一条字幕结束到下一条字幕开始的间隔
- **正常范围**: ≤ 1秒
- **异常情况**: > 1秒（可能缺失字幕）

**示例**:
```
条目1: 00:00:10,000 → 00:00:12,000
条目2: 00:00:15,000 → 00:00:18,000
间隔: 3秒 ❌ 异常
```

#### (2) 时间重叠 (Overlaps)
- **定义**: 下一条字幕开始时间早于前一条结束时间
- **正常情况**: 无重叠
- **异常情况**: 有重叠（SRT文件错误）

**示例**:
```
条目1: 00:00:10,000 → 00:00:15,000
条目2: 00:00:14,000 → 00:00:18,000
重叠: 1秒 ❌ 异常
```

**评分规则**:
- 间隔≤5个且无重叠: 100分
- 间隔>5个或有重叠: 70分（生成warning/error）

**输出格式**:
```python
{
    "passed": bool,
    "total_entries": int,
    "gaps": [                      # 间隔列表
        {
            "entries": "10-11",
            "gap_seconds": 3.2,
            "time_range": "00:00:12,000 → 00:00:15,200"
        }
    ],
    "overlaps": [                  # 重叠列表
        {
            "entries": "20-21",
            "overlap_seconds": 1.5,
            "time_range": "00:00:45,000 → 00:00:46,500"
        }
    ]
}
```

---

### 2. 文本完整性检查 (`_check_text_completeness`)

**目的**: 验证文本提取的完整性

**检查项**:

#### 文本覆盖率
- **计算方法**: 提取后文本长度 / SRT原始文本总长度
- **正常范围**: ≥ 95%
- **异常情况**: < 95%（可能提取逻辑有问题）

**评分规则**:
- 覆盖率 ≥ 95%: 100分
- 覆盖率 < 95%: 按覆盖率计分（如90% = 90分）

**输出格式**:
```python
{
    "passed": bool,
    "coverage": float,              # 覆盖率 (0.0-1.0)
    "srt_text_length": int,         # SRT原始文本长度
    "extracted_text_length": int,   # 提取后文本长度
    "missing_chars": int            # 缺失字符数
}
```

---

### 3. 分段合理性检查 (`_check_segmentation`)

**目的**: 验证Script分段的合理性

**检查项**:

#### (1) 分段数量
- **正常范围**: 5-20段/集
- **异常情况**: 
  - < 5段: 分段过少，粒度太粗
  - > 20段: 分段过多，粒度太细

#### (2) 平均段落时长
- **计算方法**: 各段落时长的平均值
- **参考范围**: 30-120秒/段

#### (3) 异常时长检测
- **过短段落**: < 10秒（可能是误分）
- **过长段落**: > 180秒（3分钟，可能需要再拆分）

**评分规则**:
- 分段数量合理且无异常时长: 100分
- 分段数量异常或存在异常时长: 80分（生成warning）

**输出格式**:
```python
{
    "passed": bool,
    "total_segments": int,
    "avg_duration_seconds": float,
    "avg_sentence_count": float,
    "short_segments": List[int],    # 过短段落索引
    "long_segments": List[int]      # 过长段落索引
}
```

---

### 4. 质量评分计算 (`_calculate_quality_score`)

**计算方法**: 加权平均

**权重分配**:
```python
{
    "timeline": 0.3,       # 时间轴连续性 (30%)
    "text": 0.4,           # 文本完整性 (40%)
    "segmentation": 0.3    # 分段合理性 (30%)
}
```

**特殊情况**:
- 如果某项检查未执行（如无分段结果），该项按100分计算（不扣分）

---

## 依赖关系 (Dependencies)

### Schema

#### 输入Schema
- `SrtEntry` - SRT字幕条目
- `SrtTextExtractionResult` - 文本提取结果
- `ScriptSegmentationResult` - 分段结果

#### 输出Schema
- `ScriptValidationReport` - 验证报告
- `ScriptValidationIssue` - 问题条目

### Tools

验证的对象是其他工具的输出：
- `SrtImporter` - 导入SRT文件
- `SrtTextExtractor` - 提取纯文本
- `ScriptSegmenter` - 分段

### 外部依赖

- 无LLM调用
- 无外部API依赖
- 纯本地计算

---

## 数据模型 (Data Models)

### ScriptValidationIssue

```python
class ScriptValidationIssue(BaseModel):
    severity: Literal["error", "warning"]  # 严重程度
    category: str                          # 问题类别
    description: str                       # 问题描述
    location: Optional[str]                # 问题位置
    recommendation: Optional[str]          # 改进建议
```

### ScriptValidationReport

详见"接口-输出"部分。

---

## 使用示例 (Usage Example)

### 基本使用

```python
from src.tools.script_validator import ScriptValidator
from src.tools.srt_importer import SrtImporter
from src.tools.script_segmenter import ScriptSegmenter

# 1. 导入SRT
importer = SrtImporter()
srt_result = importer.execute(srt_path="data/ep01.srt")

# 2. 分段（可选）
segmenter = ScriptSegmenter(provider="deepseek")
seg_result = segmenter.execute(script_text=srt_result.processed_text)

# 3. 验证质量
validator = ScriptValidator()
validation_report = validator.execute(
    srt_entries=srt_result.entries,
    text_extraction=srt_result,
    segmentation=seg_result,
    episode_name="ep01"
)

# 4. 检查结果
if validation_report.is_valid:
    print(f"✅ 质量验证通过: {validation_report.quality_score}/100")
else:
    print(f"⚠️ 质量不达标: {validation_report.quality_score}/100")
    for issue in validation_report.issues:
        print(f"  - {issue.description}")
```

### 在Workflow中使用

```python
# ScriptProcessingWorkflow中的质量验证步骤
validation_report = self.script_validator.execute(
    srt_entries=srt_result.entries,
    text_extraction=text_extraction_result,
    segmentation=segmentation_result,
    episode_name=episode_name
)

# 保存验证报告
self._save_validation_report(validation_report)

# 根据验证结果决定是否继续
if not validation_report.is_valid:
    logger.warning("质量验证失败，建议检查原始文件")
    if not workflow_config.continue_on_error:
        raise ValidationError(f"质量评分不达标: {validation_report.quality_score}")
```

---

## 质量标准 (Quality Standards)

### 通过标准

验证通过需要满足：
1. **质量评分 ≥ 70分**
2. **无error级别的issue**
3. **时间轴无重叠**
4. **文本覆盖率 ≥ 95%**

### 优秀标准

验证优秀需要满足：
1. **质量评分 ≥ 90分**
2. **无任何issue或warning**
3. **时间轴间隔 ≤ 5处**
4. **文本覆盖率 ≥ 98%**
5. **分段数量在5-20段范围内**

---

## 常见问题处理

### 问题1: 时间轴间隔过多

**原因**:
- SRT文件本身有间隔（静音、画面切换）
- 字幕缺失

**解决方案**:
1. 检查原始视频是否有静音或画面切换
2. 如果是字幕缺失，补充字幕
3. 如果是正常间隔，可以接受（≤5处间隔是正常的）

### 问题2: 时间轴重叠

**原因**:
- SRT文件格式错误
- 字幕工具导出错误

**解决方案**:
1. 使用专业SRT编辑器（如Aegisub）修复
2. 重新导出SRT文件
3. 手动修正重叠的时间戳

### 问题3: 文本覆盖率低

**原因**:
- 文本提取时过滤了特殊字符
- 重复文本被去重

**解决方案**:
1. 检查 `SrtTextExtractor` 的去重逻辑
2. 如果覆盖率在90-95%之间，通常是正常的去重
3. 如果 < 90%，需要检查提取逻辑

### 问题4: 分段数量异常

**原因**:
- 分段过少(<5): ScriptSegmenter的LLM分段过于保守
- 分段过多(>20): ScriptSegmenter的LLM分段过于激进

**解决方案**:
1. Review分段Prompt，调整分段粒度
2. 调整 `min_segment_length` 参数
3. 人工review分段结果

---

## 性能指标 (Performance)

- **执行时间**: < 3秒
- **内存占用**: < 50MB
- **无LLM调用**: 纯本地计算，无API费用

---

## 注意事项 (Notes)

1. **可选参数**: `text_extraction` 和 `segmentation` 是可选的
   - 如果只导入SRT，只传 `srt_entries`
   - 如果执行完整流程，传递所有参数

2. **评分公平性**: 未执行的步骤不会拉低总分
   - 如果没有分段结果，分段检查按100分计算

3. **时间间隔容差**: 
   - 1秒以内的间隔是正常的（语句停顿）
   - 超过1秒的间隔才会被标记

4. **SRT格式**: 
   - 时间戳格式必须是 `HH:MM:SS,mmm`
   - 如果格式错误，会返回默认timedelta(0)

---

## 相关文档 (Related Docs)

- [SrtImporter](./srt_importer.md) - SRT导入工具
- [SrtTextExtractor](./srt_text_extractor.md) - 文本提取工具
- [ScriptSegmenter](./script_segmenter.md) - Script分段工具
- [ScriptProcessingWorkflow](../workflows/script_processing_workflow.md) - 完整流程

---

**最后更新**: 2026-02-10  
**维护者**: AI Assistant
