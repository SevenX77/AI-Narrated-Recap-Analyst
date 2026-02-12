# NovelValidator

## 职责 (Responsibility)

**单一职责**: 验证小说处理的各个环节质量，确保数据准确性和合理性，生成质量评分和改进建议。

NovelValidator 是 NovelProcessingWorkflow 的最后一个步骤（Step 8），负责对整个处理流程的输出进行全面质量检查，确保：
1. 文件编码正确无乱码
2. 章节检测完整无遗漏
3. 分段结果合理（ABC类分布、段落数量）
4. 标注结果合理（事件数量、设定数量）

---

## 接口 (Interface)

### 输入 (Input)

```python
def execute(
    import_result: NovelImportResult,                        # 必需，导入结果
    chapter_infos: List[ChapterInfo],                        # 必需，章节信息
    segmentation_results: List[ParagraphSegmentationResult], # 可选，分段结果
    annotation_results: List[AnnotatedChapter]               # 可选，标注结果
) -> NovelValidationReport
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `import_result` | `NovelImportResult` | ✅ | 小说导入结果，包含项目名、文件路径、编码等 |
| `chapter_infos` | `List[ChapterInfo]` | ✅ | 章节信息列表，包含章节号、标题、行号范围 |
| `segmentation_results` | `List[ParagraphSegmentationResult]` | ❌ | 分段结果列表，包含ABC类段落分类 |
| `annotation_results` | `List[AnnotatedChapter]` | ❌ | 标注结果列表，包含事件和设定信息 |

### 输出 (Output)

```python
class NovelValidationReport(BaseModel):
    project_name: str                      # 项目名称
    validation_time: datetime              # 验证时间
    quality_score: float                   # 总体质量评分 (0-100)
    is_valid: bool                         # 是否通过验证 (>=70分)
    
    # 检查结果
    encoding_check: Dict[str, Any]         # 编码检查结果
    chapter_check: Dict[str, Any]          # 章节检查结果
    segmentation_check: Dict[str, Any]     # 分段检查结果
    annotation_check: Dict[str, Any]       # 标注检查结果
    
    # 问题与建议
    issues: List[ValidationIssue]          # 发现的问题列表
    warnings: List[str]                    # 警告列表
    recommendations: List[str]             # 改进建议列表
    
    # 统计信息
    statistics: Dict[str, Any]             # 统计信息
```

**质量评分标准**:
- **≥90分**: 优秀，无明显问题
- **70-89分**: 良好，有轻微问题但可接受
- **<70分**: 不合格，需要重新处理

---

## 实现逻辑 (Implementation)

### 1. 编码正确性检查 (`_check_encoding`)

**目的**: 检测文件是否包含乱码字符

**检查项**:
- 读取已保存的文件内容
- 统计乱码字符数量（`�`, `\ufffd`）
- 记录原始文件编码

**评分规则**:
- 无乱码: 100分
- 有乱码: 0分（生成error级别issue）

**输出格式**:
```python
{
    "passed": bool,              # 是否通过
    "invalid_chars_count": int,  # 乱码字符数量
    "encoding": str              # 文件编码
}
```

---

### 2. 章节完整性检查 (`_check_chapters`)

**目的**: 验证章节检测的完整性和准确性

**检查项**:
- 章节数量是否为0
- 章节编号是否连续（1, 2, 3, ...）
- 是否存在重复章节

**评分规则**:
- 完整且无重复: 100分
- 有缺失或重复: 50分（生成error级别issue）

**输出格式**:
```python
{
    "passed": bool,                    # 是否通过
    "total_chapters": int,             # 章节总数
    "missing_chapters": List[int],     # 缺失的章节号
    "duplicate_chapters": List[int]    # 重复的章节号
}
```

---

### 3. 分段合理性检查 (`_check_segmentation`)

**目的**: 验证ABC类分段的合理性

**检查项**:
- ABC类分布比例是否合理
- 平均每章段落数是否合理
- 是否存在过度分段（>50段）

**正常范围标准**:
| 类型 | 正常比例 | 说明 |
|-----|---------|------|
| A类 | 10-30% | 设定类段落 |
| B类 | 60-80% | 事件类段落 |
| C类 | 0-10% | 系统类段落 |

| 指标 | 正常范围 | 说明 |
|-----|---------|------|
| 平均段落数 | 8-15段/章 | 过少(<8)或过多(>15)都可能有问题 |
| 单章最大段落数 | ≤50段 | 超过50段可能是过度分段 |

**评分规则**:
- 分布合理且段落数适中: 100分
- 分布异常或过度分段: 70分（生成warning）

**输出格式**:
```python
{
    "passed": bool,                        # 是否通过
    "total_paragraphs": int,               # 总段落数
    "avg_paragraphs_per_chapter": float,   # 平均每章段落数
    "max_paragraphs": int,                 # 单章最大段落数
    "abc_distribution": {                  # ABC类分布比例
        "A": float,  # 0.0-1.0
        "B": float,
        "C": float
    }
}
```

---

### 4. 标注合理性检查 (`_check_annotation`)

**目的**: 验证事件和设定标注的合理性

**检查项**:
- 平均每章事件数是否合理
- 平均每章设定数是否合理

**正常范围标准**:
| 指标 | 正常范围 | 说明 |
|-----|---------|------|
| 平均事件数 | 3-15个/章 | 过少(<3)可能是聚合过度，过多(>15)可能是过度拆分 |
| 平均设定数 | ≥1个/章 | 每章至少应该有1个设定 |

**评分规则**:
- 事件和设定数量合理: 100分
- 事件数量异常或设定过少: 70分（生成warning）

**输出格式**:
```python
{
    "passed": bool,                       # 是否通过
    "total_events": int,                  # 总事件数
    "total_settings": int,                # 总设定数
    "avg_events_per_chapter": float,      # 平均每章事件数
    "avg_settings_per_chapter": float     # 平均每章设定数
}
```

---

### 5. 质量评分计算 (`_calculate_quality_score`)

**计算方法**: 加权平均

**权重分配**:
```python
{
    "encoding": 0.2,       # 编码正确性 (20%)
    "chapter": 0.25,       # 章节完整性 (25%)
    "segmentation": 0.3,   # 分段合理性 (30%)
    "annotation": 0.25     # 标注合理性 (25%)
}
```

**计算公式**:
```
总分 = Σ (各项得分 × 权重)
```

**特殊情况**:
- 如果某项检查未执行（如无分段结果），该项按100分计算（不扣分）
- 未通过的检查项给予部分分数（如章节检查50分，分段/标注检查70分）

---

## 依赖关系 (Dependencies)

### Schema

#### 输入Schema
- `NovelImportResult` - 小说导入结果
- `ChapterInfo` - 章节信息
- `ParagraphSegmentationResult` - 分段结果
- `AnnotatedChapter` - 标注结果

#### 输出Schema
- `NovelValidationReport` - 验证报告
- `ValidationIssue` - 问题条目

### Tools

无直接依赖其他工具，但验证的对象是其他工具的输出：
- Step 1: `NovelImporter`
- Step 3: `NovelChapterDetector`
- Step 4: `NovelSegmenter`
- Step 5: `NovelAnnotator`

### 外部依赖

无LLM调用，无外部API依赖，纯本地计算。

---

## 数据模型 (Data Models)

### ValidationIssue

```python
class ValidationIssue(BaseModel):
    severity: Literal["error", "warning"]  # 严重程度
    category: str                          # 问题类别
    description: str                       # 问题描述
    location: Optional[str]                # 问题位置
    recommendation: Optional[str]          # 改进建议
```

### NovelValidationReport

详见"接口-输出"部分。

---

## 使用示例 (Usage Example)

### 在Workflow中使用

```python
from src.tools.novel_validator import NovelValidator

# 初始化验证器
validator = NovelValidator()

# 执行验证（在Step 8调用）
validation_report = validator.execute(
    import_result=import_result,
    chapter_infos=chapters,
    segmentation_results=list(segmentation_results.values()),
    annotation_results=list(annotation_results.values())
)

# 检查验证结果
if validation_report.is_valid:
    logger.info(f"✅ 质量验证通过: {validation_report.quality_score}/100")
else:
    logger.warning(f"⚠️ 质量不达标: {validation_report.quality_score}/100")
    logger.warning(f"   问题数: {len(validation_report.issues)}")
```

### 验证报告示例

```python
NovelValidationReport(
    project_name="末哥超凡公路",
    quality_score=85.5,
    is_valid=True,
    
    encoding_check={
        "passed": True,
        "invalid_chars_count": 0,
        "encoding": "UTF-8"
    },
    
    chapter_check={
        "passed": True,
        "total_chapters": 50,
        "missing_chapters": [],
        "duplicate_chapters": []
    },
    
    segmentation_check={
        "passed": True,
        "total_paragraphs": 625,
        "avg_paragraphs_per_chapter": 12.5,
        "max_paragraphs": 18,
        "abc_distribution": {"A": 0.15, "B": 0.75, "C": 0.10}
    },
    
    annotation_check={
        "passed": True,
        "total_events": 375,
        "total_settings": 125,
        "avg_events_per_chapter": 7.5,
        "avg_settings_per_chapter": 2.5
    },
    
    issues=[],
    warnings=[],
    recommendations=["分段质量优秀，建议保持当前策略"]
)
```

---

## 质量标准 (Quality Standards)

### 通过标准

验证通过需要满足：
1. **质量评分 ≥ 70分**
2. **无error级别的issue**
3. **编码检查通过**（无乱码）
4. **章节检查通过**（无缺失或重复）

### 优秀标准

验证优秀需要满足：
1. **质量评分 ≥ 90分**
2. **无任何issue或warning**
3. **ABC类分布在正常范围内**
4. **事件和设定数量合理**

### 常见问题处理

#### 问题1: 编码检查失败（有乱码）

**原因**:
- 原始文件编码错误
- 导入时编码检测失败

**解决方案**:
1. 检查原始文件，确认正确编码
2. 重新导入，指定正确编码
3. 如需要，手动转换文件编码为UTF-8

#### 问题2: ABC类分布异常

**原因**:
- A类过少(<10%): 分段Prompt过于保守，很多设定被归为B类
- A类过多(>30%): 分段Prompt过于激进，很多叙述被归为A类
- B类过少(<60%): 同上
- C类过多(>10%): 系统类小说，但Prompt过于激进

**解决方案**:
1. Review分段Prompt，调整A/B/C类的判断标准
2. 抽查具体章节，分析分类错误原因
3. 如需要，重新运行分段步骤

#### 问题3: 事件数量异常

**原因**:
- 过少(<3/章): 事件聚合过度，或章节内容过于简单
- 过多(>15/章): 事件聚合不足，应合并的事件被拆分

**解决方案**:
1. Review标注Prompt，调整事件聚合粒度
2. 检查事件聚合逻辑
3. 如需要，重新运行标注步骤

---

## 性能指标 (Performance)

- **执行时间**: < 5秒（取决于章节数量）
- **内存占用**: < 100MB（取决于文件大小）
- **无LLM调用**: 纯本地计算，无API费用

---

## 注意事项 (Notes)

1. **可选参数**: `segmentation_results` 和 `annotation_results` 是可选的
   - 如果只执行到Step 3（章节检测），只传 `import_result` 和 `chapter_infos`
   - 如果执行完整流程，传递所有参数

2. **评分公平性**: 未执行的步骤不会拉低总分
   - 如果没有分段结果，分段检查按100分计算
   - 这样可以在不同阶段使用验证器

3. **问题记录**: 所有问题都会记录在 `issues` 列表中
   - `severity="error"`: 严重问题，必须修复
   - `severity="warning"`: 轻微问题，建议改进

4. **改进建议**: `recommendations` 列表包含自动生成的改进建议
   - 基于检查结果自动生成
   - 可直接用于报告展示

---

## 相关文档 (Related Docs)

- [NovelProcessingWorkflow](../workflows/novel_processing_workflow.md) - Step 8使用本工具
- [QUALITY_STANDARDS](../workflows/QUALITY_STANDARDS.md) - 质量标准详细说明
- [schemas_novel.py](../../src/core/schemas_novel.py) - 相关Schema定义

---

**最后更新**: 2026-02-10  
**维护者**: AI Assistant
