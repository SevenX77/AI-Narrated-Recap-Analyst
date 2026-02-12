# NovelSystemDetector - 章节系统元素检测工具

## 职责 (Responsibility)

基于章节标注结果和全局系统目录，检测本章中新出现的系统元素，并更新系统目录。是小说分析工具链的 Phase 2。

**所属阶段**: 小说系统检测（Phase 2）
**工具链位置**: NovelAnnotator → NovelSystemDetector → NovelSystemTracker

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    annotated_chapter: AnnotatedChapter,
    segmentation_result: ParagraphSegmentationResult,
    system_catalog: SystemCatalog,
    **kwargs
) -> tuple[SystemUpdateResult, SystemCatalog]
```

### 输入参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| `annotated_chapter` | `AnnotatedChapter` | 章节标注结果 |
| `segmentation_result` | `ParagraphSegmentationResult` | 章节分段结果（用于获取C类段落） |
| `system_catalog` | `SystemCatalog` | 当前系统目录 |

### 输出结果

**类型**: `tuple[SystemUpdateResult, SystemCatalog]`

**SystemUpdateResult 结构**:
```python
SystemUpdateResult(
    chapter_number: int,                          # 章节号
    has_new_elements: bool,                       # 是否有新元素
    new_elements: List[SystemElementUpdate],      # 新元素列表
    catalog_updated: bool,                        # 目录是否已更新
    metadata: Dict[str, Any]                      # 元数据
)
```

**SystemElementUpdate 结构**:
```python
SystemElementUpdate(
    element_name: str,        # 元素名称
    category_id: str,         # 类别ID（SC001, SC002...）
    category_name: str,       # 类别名称
    chapter_number: int,      # 首次出现的章节号
    confidence: str           # 置信度（high/medium/low）
)
```

**更新后的 SystemCatalog**:
- 在对应类别的 `elements` 列表中添加新元素
- 更新 `metadata.total_elements`
- 更新 `metadata.last_updated_chapter`

## 实现逻辑 (Logic)

### 核心流程

1. **准备输入数据**
   - 格式化系统目录摘要（每类前10个元素）
   - 格式化事件摘要（event_id + event_summary）
   - 提取C类段落内容（完整内容）

2. **LLM系统检测**
   - 调用 `novel_system_detection` prompt
   - 输入：章节号 + 系统目录摘要 + 事件摘要 + C类段落
   - 输出：Markdown格式的检测结果
   - Temperature: 0.2
   - Max tokens: 1000

3. **解析检测结果**
   - 检测是否有新元素（匹配"无新元素"）
   - 匹配元素块：`### 1. [元素名称]`
   - 匹配归类：`**归类**：SC001 - [类别名称]`
   - 匹配置信度：`**置信度**：high/medium/low`

4. **更新系统目录**
   - 按类别分组新元素
   - 在对应类别中添加元素（去重）
   - 更新元数据

### 设计理念

- **独立Pass 3**：避免污染 NovelAnnotator
- **轻量级LLM调用**：输入控制在 2K tokens 以内
- **简洁输出格式**：易于解析

### 性能特征

- **Token消耗**：约 1.5K-2K input + 500-1K output
- **处理时间**：约 3-5秒/章节
- **准确度**：依赖于C类段落质量和系统目录完整性

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_novel.py`

- `AnnotatedChapter` - 章节标注结果
- `ParagraphSegmentationResult` - 章节分段结果
- `SystemCatalog` - 系统目录
- `SystemCategory` - 系统类别
- `SystemElementUpdate` - 元素更新
- `SystemUpdateResult` - 更新结果

### Tool 依赖

**前置工具**:
- `NovelSegmenter` - 提供分段结果
- `NovelAnnotator` - 提供标注结果
- `NovelSystemAnalyzer` - 提供初始系统目录

**后续工具**:
- `NovelSystemTracker` - 使用更新后的系统目录

### Prompt 依赖

**Prompt 文件**: `src/prompts/novel_system_detection.yaml`

**配置项**:
- `system` - 系统提示词
- `user_template` - 用户提示词模板

### LLM 依赖

**Provider**: Claude (默认)
**Model**: 由 `get_model_name(provider)` 决定
**配置**: 通过 `src/core/llm_client_manager` 管理

## 代码示例 (Usage Example)

```python
from src.tools.novel_system_detector import NovelSystemDetector
from src.core.schemas_novel import (
    AnnotatedChapter,
    ParagraphSegmentationResult,
    SystemCatalog
)

# 初始化工具
detector = NovelSystemDetector(provider="claude")

# 准备输入
annotated_chapter = AnnotatedChapter(...)      # 来自 NovelAnnotator
segmentation_result = ParagraphSegmentationResult(...)  # 来自 NovelSegmenter
system_catalog = SystemCatalog(...)            # 初始系统目录

# 执行检测
update_result, updated_catalog = detector.execute(
    annotated_chapter=annotated_chapter,
    segmentation_result=segmentation_result,
    system_catalog=system_catalog
)

# 访问结果
if update_result.has_new_elements:
    print(f"发现 {len(update_result.new_elements)} 个新元素")
    for elem in update_result.new_elements:
        print(f"  - {elem.element_name} ({elem.category_id}) [置信度: {elem.confidence}]")

# 使用更新后的目录
print(f"目录总元素数：{updated_catalog.metadata['total_elements']}")
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
{
  "chapter_number": 1,
  "has_new_elements": true,
  "new_elements": [
    {
      "element_name": "轻型枪械",
      "category_id": "SC002",
      "category_name": "装备道具",
      "chapter_number": 1,
      "confidence": "high"
    },
    {
      "element_name": "强化手套",
      "category_id": "SC002",
      "category_name": "装备道具",
      "chapter_number": 1,
      "confidence": "medium"
    }
  ],
  "catalog_updated": true,
  "metadata": {
    "processing_time": 4.2,
    "model_used": "claude-sonnet-4.5",
    "provider": "claude"
  }
}
```

### 更新后的系统目录

```json
{
  "novel_type": "末世求生",
  "novel_name": "超凡公路",
  "analyzed_chapters": "1-50",
  "categories": [
    {
      "category_id": "SC002",
      "category_name": "装备道具",
      "category_desc": "角色装备的武器、护具、道具",
      "importance": "critical",
      "elements": ["轻型枪械", "强化手套", ...],
      "tracking_strategy": "quantity"
    }
  ],
  "metadata": {
    "total_elements": 52,
    "category_count": 5,
    "last_updated_chapter": 1
  }
}
```

## 错误处理 (Error Handling)

### 常见错误

1. **未检测到新元素**
   - 返回空列表
   - `has_new_elements` 设为 `false`
   - 不更新系统目录

2. **类别不匹配**
   - 使用 `SC999 - 未分类` 作为默认类别
   - 记录警告日志

3. **元素重复**
   - 自动去重
   - 记录日志

### 日志级别

- `INFO`: 处理进度、新元素数量
- `WARNING`: 类别不匹配、元素重复
- `DEBUG`: 详细的解析过程

## 性能优化 (Performance)

### Token 优化

1. **系统目录摘要**：每个类别只显示前10个元素
2. **事件摘要**：只包含 event_id + event_summary
3. **C类段落**：完整内容（通常较短）
4. **输出长度限制**：Max tokens 设为 1000

### 处理速度

- **单章节**：3-5秒
- **批量处理**：建议串行处理（确保目录一致性）

## 注意事项 (Notes)

### 何时使用

- 每章处理后都应运行检测
- 确保系统目录实时更新

### 与 NovelSystemAnalyzer 的区别

| 特性 | NovelSystemAnalyzer | NovelSystemDetector |
|-----|---------------------|---------------------|
| 运行时机 | 全书开始前（分析前50章） | 每章处理后 |
| 输入来源 | 原始小说文本 | 章节标注结果 + C类段落 |
| 输出结果 | 初始系统目录 | 新元素 + 更新目录 |
| Token消耗 | 高（10K-20K） | 低（2K-3K） |

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
